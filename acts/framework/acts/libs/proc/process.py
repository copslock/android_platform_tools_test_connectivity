#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import logging
import subprocess
from threading import Thread

import time


class Process(object):
    """A Process object used to run various commands.

    Attributes:
        _command: The initial command to run.
        _subprocess_kwargs: The kwargs to send to Popen for more control over
                            execution.
        _process: The subprocess.Popen object currently executing a process.
        _listening_thread: The thread that is listening for the process to stop.
        _redirection_thread: The thread that is redirecting process output.
        _on_output_callback: The callback to call when output is received.
        _on_terminate_callback: The callback to call when the process terminates
                                without stop() being called first.
        _started: Whether or not the Process is in the running state.
        _stopped: Whether or not stop() was called.
    """

    def __init__(self, command, **kwargs):
        """Creates a Process object.

        Note that this constructor does not begin the process. To start the
        process, use Process.start().
        """
        self._command = command
        self._subprocess_kwargs = kwargs
        self._process = None

        self._listening_thread = None
        self._redirection_thread = None
        self._on_output_callback = lambda *args, **kw: None
        self._on_terminate_callback = lambda *args, **kw: ''

        self._stopped = False

    def set_on_output_callback(self, on_output_callback):
        """Sets the on_output_callback function.

        Args:
            on_output_callback: The function to be called when output is sent to
                the output. The output callback has the following signature:

                >>> def on_output_callback(output_line):
                >>>     return None
        Returns:
            self
        """
        self._on_output_callback = on_output_callback
        return self

    def set_on_terminate_callback(self, on_terminate_callback):
        """Sets the on_self_terminate callback function.

        Args:
            on_terminate_callback: The function to be called when the process
                has terminated on its own. The callback has the following
                signature:

                >>> def on_self_terminate_callback(popen_process):
                >>>     return 'command to run' or None

                If a string is returned, the string returned will be the command
                line used to run the command again. If None is returned, the
                process will end without restarting.

        Returns:
            self
        """
        self._on_terminate_callback = on_terminate_callback
        return self

    def start(self):
        """Starts the process's execution."""
        self._process = None
        self._stopped = False

        self._listening_thread = Thread(target=self._exec_loop)
        self._listening_thread.start()

        time_up_at = time.time() + 1

        while self._process is None:
            if time.time() > time_up_at:
                raise OSError('Unable to open process!')

    @staticmethod
    def _get_timeout_left(timeout, start_time):
        return max(.1, timeout - (time.time() - start_time))

    def wait(self, kill_timeout=60.0):
        """Waits for the process to finish execution.

        If the process has reached the kill_timeout, the process will be killed
        instead.

        Args:
            kill_timeout: The amount of time to wait until killing the process.
        """
        start_time = time.time()

        try:
            self._process.wait(kill_timeout)
        except subprocess.TimeoutExpired:
            self._stopped = True
            self._process.kill()

        time_left = self._get_timeout_left(kill_timeout, start_time)

        if self._listening_thread is not None:
            self._listening_thread.join(timeout=time_left)
            self._listening_thread = None

        time_left = self._get_timeout_left(kill_timeout, start_time)

        if self._redirection_thread is not None:
            self._redirection_thread.join(timeout=time_left)
            self._redirection_thread = None

    def stop(self, timeout=60.0):
        """Stops the process.

        This command is effectively equivalent to kill, but gives time to clean
        up any related work on the process, such as output redirection.

        Note: the on_self_terminate callback will NOT be called when calling
        this function.

        Args:
            timeout: The amount of time to wait for the program output to finish
                     being handled.
        """
        self._stopped = True

        start_time = time.time()

        if self._process is not None and self._process.poll() is None:
            self._process.kill()
        self.wait(self._get_timeout_left(timeout, start_time))

    def _redirect_output(self):
        """Redirects the output from the command into the on_output_callback."""
        while True:
            line = self._process.stdout.readline().decode('utf-8',
                                                          errors='replace')

            if line == '':
                return
            else:
                # Output the line without trailing \n and whitespace.
                self._on_output_callback(line.rstrip())

    @staticmethod
    def __start_process(command, **kwargs):
        """A convenient wrapper function for starting the process."""
        acts_logger = logging.getLogger()
        acts_logger.debug(
            'Starting command "%s" with kwargs %s', command, kwargs)
        return subprocess.Popen(command, **kwargs)

    def _exec_loop(self):
        """Executes Popen in a loop.

        When Popen terminates without stop() being called,
        self._on_terminate_callback() will be called. The returned value from
        _on_terminate_callback will then be used to determine if the loop should
        continue and start up the process again. See set_on_terminate_callback()
        for more information.
        """
        command = self._command
        while True:
            self._process = self.__start_process(command,
                                                 stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT,
                                                 bufsize=1,
                                                 **self._subprocess_kwargs)
            self._redirection_thread = Thread(target=self._redirect_output)
            self._redirection_thread.start()
            self._process.wait()

            if self._stopped:
                break
            else:
                # Wait for all output to be processed before sending
                # _on_terminate_callback()
                self._redirection_thread.join()
                retry_value = self._on_terminate_callback(self._process)
                if retry_value:
                    command = retry_value
                else:
                    break
