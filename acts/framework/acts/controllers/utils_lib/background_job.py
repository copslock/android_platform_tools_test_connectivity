# Copyright 2016 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Classes and functions for running background jobs.

This module contains all needed functions and classes for running a
background job. The main class is BackgroundJob, which is a wrapper for running
a child process in the background.
"""

import enum
import io
import logging
import os
import re
import select
import signal
import subprocess
import sys
import time

from acts.controllers.utils_lib import shell_utils


class CmdError(Exception):
    """Indicates that a command failed, is fatal to the test unless caught."""

    def __init__(self, command, result_obj, additional_text=None):
        self._command = command
        self.result_obj = result_obj
        self.additional_text = additional_text

    def __str__(self):
        if self.result_obj.exit_status is None:
            msg = ('Command <%s> failed and is not responding to signals' %
                   self._command)
        else:
            msg = 'Command <%s> failed, rc=%d'
            msg %= (self._command, self.result_obj.exit_status)

        if self.additional_text:
            msg += ", %s" % self.additional_text
        msg += '\n' + repr(self.result_obj)
        return msg


class CmdTimeoutError(CmdError):
    """Thrown when a BackgroundJob times out on wait."""


class EventType(enum.IntEnum):
    """Represents what type of event has occured.

    Enum that represents the type of event that took place.
    NONE: No event took place, currently not used, but included for later used
          if needed.
    NEW_DATA: New I/O data was processed.
    DEAD: The program closed.
    TIMEOUT: The operation timed out.
    ALREADY_DEAD: The program has already given its DEAD event. This will be
                  given for all events after DEAD.
    """
    NONE = 0
    NEW_DATA = 1
    DEAD = 2
    TIMEOUT = 3
    ALREADY_DEAD = 4


class EventData(object):
    """Data about an event occuring inside a process.

    Whenever an event occurs within a process EventData will be given back.
    This data allows for an event type and misc data to be given.

    Attributes:
        event_type: An EventType enum that represents what type of event took
                    place.
        data: Data associated with the event.
    """

    def __init__(self, event_type, data):
        """
        Arguments:
            event_type: An EventType enum that represents the type of event.
            data: Data to assosiate with the event.
        """
        self.event_type = event_type
        self.data = data

    def __str__(self):
        return 'Event Data:\nType: %s\nData:\n%s' % (
            EventType.to_str(self.event_type), str(self.data))


class ProcessedData(object):
    """Container for new data processed by the job.

    IO data that is processed by a process will be stored in an object of this
    type.

    Attributes:
        new_stdout: Any new data that came from stdout. None if no data came.
        new_stderr: Any new data that came from stderr. None if no data came.
        new_stdin: Any new data that was written into stdin. None if no data
                   was written.
        did_close: True if the program has closed all input.
    """

    def __init__(self,
                 did_close,
                 new_stdout=None,
                 new_stderr=None,
                 new_stdin=None):
        self.new_stdout = new_stdout
        self.new_stderr = new_stderr
        self.new_stdin = new_stdin
        self.did_close = did_close

    def __str__(self):
        return 'stdout: %s\nstdin: %s\nstderr: %s\nclosed?: %s' % (
            self.new_stdout, self.new_stdin, self.new_stderr, self.did_close)


class CmdResult(object):
    """Command execution result.

    Contains information on a BackgroundJob once that BackgroundJob has closed.

    Attributes:
        command: An array containing the command and all arguments that was executed.
        exit_status: Integer exit code of the process.
        stdout_raw: The raw bytes output from standard out.
        stderr_raw: The raw bytes output from standard error
        duration: How long the process ran for.
        did_timeout: True if the program timedout and was killed for that reason.
    """

    @property
    def stdout(self):
        """String representation of standard output."""
        if not self._stdout_str:
            self._stdout_str = self.raw_stdout.decode(encoding=self._encoding)
        return self._stdout_str

    @property
    def stderr(self):
        """String representation of standard error."""
        if not self._stderr_str:
            self._stderr_str = self.raw_stderr.decode(encoding=self._encoding)
        return self._stderr_str

    def __init__(self,
                 command=[],
                 stdout=bytes(),
                 stderr=bytes(),
                 exit_status=None,
                 duration=0,
                 did_timeout=False,
                 encoding='utf-8'):
        """
        Args:
            command: The command that was run. This will be a list containing
                     the executed command and all args.
            stdout: The raw bytes that standard output gave.
            stderr: The raw bytes that standard error gave.
            exit_status: The exit status of the command.
            duration: How long the command ran.
            did_timeout: True if the command timed out.
            encoding: The encoding standard that the program uses.
        """
        self.command = command
        self.exit_status = exit_status
        self.raw_stdout = stdout
        self.raw_stderr = stderr
        self._stdout_str = None
        self._stderr_str = None
        self._encoding = encoding
        self.duration = duration
        self.did_timeout = did_timeout


class BackgroundJob(object):
    """A job to be executed in the background.

    Represents another command being executed on the background.
    """

    @property
    def command(self):
        """The command that this BackgroundJob is executing.

        An array containing the command and arguments of this BackgroundJob.

        Returns:
            The split command as an array.
        """
        return self._command

    @property
    def start_time(self):
        """Returns: The start time of this BackgroundJob."""
        return self._start_time

    @property
    def up_time(self):
        """
        Returns:
            The duration of time that this BackgroundJob has been running.
        """
        if self.is_alive:
            return time.time() - self._start_time
        else:
            return self._result.duration

    @property
    def result(self):
        """Gets the result of the job.

        Waits for the job to finish and then returns the result of the job.

        Returns:
            The results of the BackgroundJob.
        """
        self.wait()
        return self._result

    @property
    def is_alive(self):
        """Returns: True if the process is still running."""
        return self._sp.poll() is None

    def __init__(self,
                 command,
                 stdout_tee=None,
                 stderr_tee=None,
                 verbose=True,
                 stdin=None,
                 allow_send=False,
                 env=None,
                 extra_paths=None,
                 no_pipes=False,
                 use_shell=False,
                 io_encoding='utf-8'):
        """Create and start a new BackgroundJob.

        This constructor creates a new BackgroundJob, and uses Popen to start a
        new subprocess with given command. It returns without blocking on
        execution of the subprocess.

        After starting a BackgroundJob either use wait to wait for the job to
        finish, next_event to wait for the process to do something, or
        periodically check is_alive to see when the job dies.

        Note:
            When the job dies it will still be held as a zombie process by the
            os. Only once the BackgroundJob object is deleted will it cleanup
            system resources.

        Args:
            command: Name of the command to execute along with all arguments.
                     The command can either be a string as would be input in
                     the shell, or a list starting with the command to execute
                     and followed by all arguments. All strings will be treated
                     literally as if they were typed into the command line.
            stdout_tee: Optional additional stream that the process's stdout
                        stream output will be written to.
            stderr_tee: Same as stdout_tee, but for stderr.
            verbose: Boolean, make BackgroundJob logging more verbose.
            stdin: if stream object, will be passed to Popen as the new
                   process's stdin. If string, will be written into the
                   processes stdin when processing data.
            allow_send: if true, then the input stream will be kept open
                        event past when all data has been sent.
            env: Dict containing environment variables used in subprocess.
            extra_paths: Optional string list, to be prepended to the PATH
                         env variable in env (or os.environ dict if env is
                         not specified).
            no_pipes: When true, all io from this process will be ignored.
            use_shell: Execute the command using shell.

        Raises:
            ValueError: If an invalid input combination is given.
        """

        if no_pipes and allow_send:
            raise ValueError('allow_send cannot be true with no_pipes.')

        if no_pipes and (stdout_tee or stderr_tee or stdin):
            raise ValueError(
                'Extra i/o streams cannot be given when no_pipes is true.')

        if isinstance(command, str):
            command = shell_utils.split_command_line(command)

        # Use literal strings for all arguments.
        command = [s.encode('unicode_escape') for s in command]

        self._command = command
        self._result = CmdResult(command, encoding=io_encoding)
        self._keep_input_alive = allow_send
        self._start_time = time.time()

        self._encoding = io_encoding

        # Streams to hold the data internally.
        self._stdout_raw = io.BytesIO()
        self._stderr_raw = io.BytesIO()

        self._no_pipes = no_pipes
        if no_pipes:
            self._stdout = _NullStream()
            self._stderr = _NullStream()

            self._has_closed_stdout = True
            self._has_closed_stderr = True

            stdout_pipe = None
            stderr_pipe = None
        else:
            if stdout_tee is None:
                stdout_tee = _NullStream()

            if stderr_tee is None:
                stderr_tee = _NullStream()

            stdout_streams = [stdout_tee, self._stdout_raw]
            stderr_streams = [stderr_tee, self._stderr_raw]

            self._stdout = _MultiStream(stdout_streams)
            self._stderr = _MultiStream(stderr_streams)

            self._has_closed_stdout = False
            self._has_closed_stderr = False

            stdout_pipe = subprocess.PIPE
            stderr_pipe = subprocess.PIPE

        # allow for easy stdin input by string, we'll let subprocess create
        # a pipe for stdin input and we'll write to it in the wait loop
        if stdin is None:
            stdin = ''

        self._has_closed_input = False
        stdin_pipe = subprocess.PIPE
        if isinstance(stdin, str) and not no_pipes:
            self._string_stdin = stdin
            self._stream_stdin = None
            self._keep_input_alive = allow_send
        elif no_pipes:
            self._string_stdin = None
            self._stream_stdin = None
            stdin_pipe = None
            self._has_closed_input = True
        else:
            self._string_stdin = None
            self._stream_stdin = stdin
            self._keep_input_alive = True

        # Prepend extra_paths to env['PATH'] if necessary.
        if extra_paths:
            env = (os.environ if env is None else env).copy()
            oldpath = env.get('PATH')
            env['PATH'] = os.pathsep.join(extra_paths + ([oldpath]
                                                         if oldpath else []))

        if verbose:
            logging.debug("Running '%s'", command)

        self._sp = subprocess.Popen(command,
                                    shell=use_shell,
                                    close_fds=True,
                                    env=env,
                                    stdin=stdin_pipe,
                                    stdout=stdout_pipe,
                                    stderr=stderr_pipe)

        self._cleanup_called = False

    def __del__(self):
        # Kill the program when it becomes orphaned.
        if self.is_alive:
            logging.warning(
                "Running command '%s' was deleted before shutting down." %
                self._command)
            self.force_close()

        # Ensures that the program is removed from the os.
        self._cleanup()
        del self._sp

    def send(self, data, timeout=None):
        """Sends data to the process.

        Sends a piece of data to the process through its stdin.

        Args:
            data: A string of data to write to the process.
            timeout: The amount of time to wait on the input sending. <= 0 or
                     None will wait indefinetly.

        Returns:
            True if the data could send, otherwise false.
        """
        if self._no_pipes:
            logging.error('Trying to write to process %d '
                          "while no pipes have been activated." % self._sp.pid)
            return False
        if self._has_closed_input:
            logging.error('Trying to write to process %d '
                          'after its input pipe has been closed.' %
                          self._sp.pid)
            return False

        if self._string_stdin is None:
            logging.error(
                'Cannot write to process %d '
                'the process is reading from another input stream source')
            return False

        if not self._keep_input_alive:
            logging.warning(
                'Writing to process %d without forcing input to stay'
                'alive. This can result in'
                'race conditions' % self._sp.pid)

        if timeout is None:
            timeout = 0

        end_time = time.time() + timeout
        self._string_stdin += data
        while (time.time() < end_time or
               timeout <= 0) and len(self._string_stdin) > 0:
            self.__process_data()

        return True

    def sendline(self, line, timeout=None):
        """Writes a line to the process.

        Writes a line of data to the process. Works like send however a newline
        is added to the end.

        Args:
            line: The string to send as a line of data.
            timeout: The amount of time to wait on the input sending. <= 0 or
                     None will wait indefinetly.

        Returns:
            True if the data could be sent, otherwise false.
        """
        return self.send(line + '\n')

    def close_input(self):
        """Closes the standard input on the process.

        Closes the standard input on a process. If already closed then it does
        nothing.
        """
        if self._has_closed_input:
            return

        self._sp.stdin.close()
        self._has_closed_input = True

    def close(self, timeout=10):
        """Closes the program safely and waits for it to die.

        Signals the program with a set of different kill signals until it dies.
        Each signal waits for the timeout time to pass until the next signal
        is sent.

        Args:
            timeout: How long to wait on each signal.
        """
        kill_queue = [signal.SIGINT, signal.SIGTERM, signal.SIGKILL]
        for sig in kill_queue:
            self._signal(sig, timeout)
            if not self.is_alive:
                break

        self._cleanup()

    def wait(self, timeout=None):
        """Wait for the process to close.
        Args:
            timeout: The time to wait for the process to close. If <= 0 or None
                     never timeout.

        Raises:
            CmdTimeoutError: When the command times out.
        """
        if self._cleanup_called:
            return

        # Waiting for program to die so input is not needed anymore and can
        # close.
        self._keep_input_alive = False

        timeleft = timeout if timeout is not None else 0
        if timeleft <= 0:
            timeleft = None

        last_time = time.time()
        was_timeout = False
        while True:
            e = self.next_event(timeleft)
            e_type = e.event_type

            if e_type == EventType.DEAD or e_type == EventType.ALREADY_DEAD:
                break

            if timeout is not None:
                timeleft -= time.time() - last_time
                last_time = time.time()

                if e_type == EventType.TIMEOUT or timeleft <= 0:
                    was_timeout = True
                    break

        status = self._sp.poll()
        if status is None:
            logging.warning('run process timeout (%s) fired on: "%s"', timeout,
                            self._command)
            self.close()
        else:
            was_timeout = False

        self._cleanup()
        self._result.did_timeout = was_timeout

        if was_timeout:
            raise CmdTimeoutError(self._command, self._result)

    def next_event(self, timeout=None):
        """Waits for the next event on the process to occur.

        This method will wait until the process reports having done something
        and then return information about that event.

        Args:
            timeout: How long to wait for the next event before giving up.
            wait_period: How long to wait between checking for input again.

        Returns: EventData containing the event type and any data assosiated
                 with that event.
        """
        if self._cleanup_called:
            return EventData(EventType.ALREADY_DEAD, None)

        if timeout is None:
            timeout = 0
            end_time = None
        else:
            end_time = time.time() + timeout

        end_time = time.time() + timeout
        while timeout <= 0 or (time.time() < end_time):
            processed_data = self.__process_data()

            if (processed_data.new_stdout or processed_data.new_stderr or
                    processed_data.new_stdin):
                return EventData(EventType.NEW_DATA, processed_data)
            elif processed_data.did_close and not self.is_alive:
                return EventData(EventType.DEAD, None)

        return EventData(EventType.TIMEOUT, None)

    def __process_data(self):
        """ Processes data for this process.

        In order to control a processes various pieces of IO, the buffers must
        be wrote to and read from. This method will handler reading from the
        stdout and stderr and putting them into buffers for use. It will also
        handle writing data into stdin if an external stream is not in charge
        of that.

        Returns:
            A ProcessedData structure describing the new data processed.
        """

        # All pipes have closed, so no need to process.
        if (self._has_closed_input and self._has_closed_stdout and
                self._has_closed_stderr):
            return ProcessedData(True)

        # If the process is dead and output has been fully read then consider
        # everything closed. No need to write input to a dead process.
        if (not self.is_alive and self._has_closed_stdout and
                self._has_closed_stderr):
            self._has_closed_input = True
            return ProcessedData(True)

        read_list = []
        if not self._has_closed_stdout:
            read_list.append(self._sp.stdout)
        if not self._has_closed_stderr:
            read_list.append(self._sp.stderr)

        write_list = []
        if not self._has_closed_input:
            write_list = [self._sp.stdin]

        # When wait_period is zero select does not yield the process. This
        # is normally not a problem as the BackgroundJob waits on the pid status.
        # However there is a small window of time after a process dies where
        # the stdout buffer has not been flushed by the os. If our process
        # happens to poll during this window then it will see the buffers
        # as closed without data in them. Yielding for any amount of time
        # allows the os to flush the buffer.
        WAIT_PERIOD = 0.1
        r, w, _ = select.select(read_list, write_list, [], WAIT_PERIOD)

        processed_out = None
        processed_err = None
        for read_input in r:
            if read_input in read_list:
                if read_input is self._sp.stdout:
                    processed_out = _feed_to_stream(read_input, self._stdout)

                    if not processed_out:
                        self._sp.stdout.close()
                        self._has_closed_stdout = True

                elif read_input is self._sp.stderr:
                    processed_err = _feed_to_stream(read_input, self._stderr)

                    if not processed_err:
                        self._sp.stderr.close()
                        self._has_closed_stderr = True

        processed_in = None
        for write_output in w:
            if write_output in write_list and not self._has_closed_input:

                # we can write PIPE_BUF bytes without blocking
                # POSIX requires PIPE_BUF is >= 512
                if self._string_stdin is not None:
                    next_data = self._string_stdin[:512].encode(self._encoding)
                    self._string_stdin = self._string_stdin[512:]
                else:
                    # TODO: When encoding a different size than 1 byte per char
                    # more than 512 bytes can be written which can cause
                    # blocking.
                    next_data = self._stream_stdin.read(512)
                    if isinstance(next_data, str):
                        next_data = next_data.encode(self._encoding)

                if next_data is not None and len(next_data) > 0:
                    try:
                        write_output.write(next_data)
                        write_output.flush()
                        processed_in = next_data
                    except IOError:
                        self._has_closed_input = True
                        pass
                elif not self._keep_input_alive:
                    # No data left so close the write stream.
                    write_output.close()
                    self._has_closed_input = True

        return ProcessedData(False, processed_out, processed_err, processed_in)

    def _cleanup(self):
        """Clean up after BackgroundJob.

        Flush the stdout_tee and stderr_tee buffers, close the
        subprocess stdout and stderr buffers, and saves data from
        the configured stdout and stderr destination streams to
        self._result. Duplicate calls ignored with a warning.
        """
        if self._cleanup_called:
            return
        try:
            if self.is_alive:
                self.wait()

            if self._sp.stdout is not None:
                self._sp.stdout.close()
            if self._sp.stderr is not None:
                self._sp.stderr.close()
            if self._sp.stdin is not None:
                self._sp.stdin.close()
            self._result.raw_stdout = self._stdout_raw.getvalue()
            self._result.raw_stderr = self._stderr_raw.getvalue()
            self._result.exit_status = self._sp.poll()
            self._result.duration = time.time() - self._start_time
        finally:
            self._cleanup_called = True

    def _signal(self, sig, timeout=5):
        """Sends a signal to a process.

        Sends a termination signal to a process.

        Args:
            sig: The signal id to use (see linux man pages).
            timeout: How long to wait for the process to die.

        Returns:
            True if the process terminated after the tiemout period.
        """
        try:
            os.kill(self._sp.pid, sig)
        except OSError:
            # The process may have died before we could kill it.
            pass

        timeleft = timeout
        while timeleft > 0:
            if not self.is_alive:
                return True
            time.sleep(0.1)
            timeleft -= 0.1

        # The process is still alive
        return False


def _read_file(filename):
    """Reads the contents of a file.

    Reads the entire contents of a file.

    Returns:
        The contents of the file.
    """
    with open(filename) as f:
        return f.read()


def _feed_to_stream(src_file, dst, size=1024):
    """Feed a file to a stream.

    Takes data from a source file and pushes it to another stream.

    Args:
        src_file: A stream with a file descriptor to read from.
        dst: The destination stream to write to.
        size: How many bytes to read/write max.

    Returns:
        The pushed data, or None if no data was pushed.
    """
    try:
        # Some streams close without warning which can cause this to thrown
        # an exception.
        data = os.read(src_file.fileno(), size)
    except OSError:
        return None

    if len(data) <= 0:
        return None

    dst.write(data)

    return data


class _NullStream(object):
    """Helper for ignoring input to a stream, but still providing a stream
    interface
    """

    def write(self, data):
        pass

    def flush(self):
        pass


class _MultiStream(object):
    """Helper for writing data to multiple streams at once."""

    def __init__(self, streams):
        self.streams = streams

    def write(self, data):
        """Writes data to all streams."""
        str_value = None
        for stream in self.streams:
            write_data = data

            if isinstance(stream, io.TextIOBase):
                if str_value is None:
                    encoding = stream.encoding
                    if encoding is None:
                        encoding = 'UTF-8'
                    str_value = data.decode(encoding)
                write_data = str_value

            stream.write(write_data)

    def flush(self):
        """Flushes all stream."""
        for stream in self.streams:
            stream.flush()
