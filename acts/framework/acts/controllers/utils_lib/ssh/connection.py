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

import logging
import os
import re
import shutil
import tempfile
import threading
import time
import uuid

from acts.libs.proc import job
from acts.controllers.utils_lib.ssh import formatter


class Error(Exception):
    """An error occured during an ssh operation."""


class CommandError(Exception):
    """An error occured with the command.

    Attributes:
        result: The results of the ssh command that had the error.
    """

    def __init__(self, result):
        """
        Args:
            result: The result of the ssh command that created the problem.
        """
        self.result = result

    def __str__(self):
        return 'cmd: %s\nstdout: %s\nstderr: %s' % (
            self.result.command, self.result.stdout, self.result.stderr)


class SshConnection(object):
    """Provides a connection to a remote machine through ssh.

    Provides the ability to connect to a remote machine and execute a command
    on it. The connection will try to establish a persistent connection When
    a command is run. If the persistent connection fails it will attempt
    to connect normally.
    """

    @property
    def socket_path(self):
        """Returns: The os path to the master socket file."""
        return os.path.join(self._master_ssh_tempdir, 'socket')

    def __init__(self, settings):
        """
        Args:
            settings: The ssh settings to use for this conneciton.
            formatter: The object that will handle formatting ssh command
                       for use with the background job.
        """
        self._settings = settings
        self._formatter = formatter.SshFormatter()
        self._lock = threading.Lock()
        self._background_job = None
        self._master_ssh_tempdir = None

    def __del__(self):
        self._cleanup_master_ssh()

    def setup_master_ssh(self, timeout_seconds=5):
        """Sets up the master ssh connection.

        Sets up the inital master ssh connection if it has not already been
        started.

        Args:
            timeout_seconds: The time to wait for the master ssh connection to be made.

        Raises:
            Error: When setting up the master ssh connection fails.
        """
        with self._lock:
            if self._background_job is not None:
                socket_path = self.socket_path
                if (not os.path.exists(socket_path) or
                        not self._background_job.is_alive):
                    logging.info('Master ssh connection to %s is down.',
                                 self._settings.hostname)
                    self._cleanup_master_ssh()

            if self._background_job is None:
                # Create a shared socket in a temp location.
                self._master_ssh_tempdir = tempfile.mkdtemp(
                    prefix='ssh-master')

                # Setup flags and options for running the master ssh
                # -N: Do not execute a remote command.
                # ControlMaster: Spawn a master connection.
                # ControlPath: The master connection socket path.
                extra_flags = {'-N': None}
                extra_options = {'ControlMaster': True,
                                 'ControlPath': self.socket_path,
                                 'BatchMode': True}

                # Construct the command and start it.
                master_cmd = self._formatter.format_ssh_local_command(
                    self._settings, extra_flags, extra_options)
                logging.info('Starting master ssh connection %s', master_cmd)
                self._background_job = job.BackgroundJob(master_cmd,
                                                         no_pipes=True)

                end_time = time.time() + timeout_seconds

                while time.time() < end_time:
                    if os.path.exists(self.socket_path):
                        break
                    time.sleep(.2)
                else:
                    self._background_job.close()
                    self._background_job = None
                    raise Error('Master ssh connection timed out.')

    def run(self,
            command,
            timeout_seconds=3600,
            env=None,
            stdout=None,
            stderr=None,
            stdin=None,
            connect_timeout=15):
        """Runs a remote command over ssh.

        Will ssh to a remote host and run a command. This method will
        block until the remote command is finished.

        Args:
            command: The command to execute over ssh. Can be either a string
                     or a list.
            env: A dictonary of enviroment variables to setup on the remote
                 host.
            stdout: A stream to send stdout to.
            stderr: A stream to send stderr to.
            stdin: A string that contains the contents of stdin. A string may
                   also be used, however its contents are not gurenteed to
                   be sent to the ssh process.
            connect_timeout: How long to wait for the connection confirmation.

        Returns:
            A job.Result containing the results of the ssh command.

        Raises:
            job.TimeoutError: When the remote command took to long to execute.
            Error: When the ssh connection failed to be created.
            CommandError: Ssh worked, but the command had an error executing.
        """
        if env is None:
            env = {}

        try:
            self.setup_master_ssh(connect_timeout)
        except Error:
            logging.warning('Failed to create master ssh connection, using '
                            'normal ssh connection.')

        extra_options = {'BatchMode': True}
        if self._background_job:
            extra_options['ControlPath'] = self.socket_path

        identifier = str(uuid.uuid4())
        full_command = 'echo "CONNECTED: %s"; %s' % (identifier, command)

        terminal_command = self._formatter.format_command(
            full_command,
            env, self._settings,
            extra_options=extra_options)

        dns_retry_count = 2
        while True:
            ssh_job = job.BackgroundJob(terminal_command,
                                        stdout_tee=stdout,
                                        stderr_tee=stderr,
                                        verbose=False,
                                        stdin=stdin)

            ssh_job.wait(timeout=timeout_seconds)
            result = ssh_job.result
            output = ssh_job.result.stdout

            # Check for a connected message to prevent false negatives.
            valid_connection = re.search('^CONNECTED: %s' % identifier,
                                         output,
                                         flags=re.MULTILINE)
            if valid_connection:
                # Remove the first line that contains the connect message.
                line_index = output.find('\n')
                real_output = output[line_index + 1:].encode(
                    encoding=result._encoding)
                result = job.Result(command=result.command,
                                    stdout=real_output,
                                    stderr=result.raw_stderr,
                                    exit_status=result.exit_status,
                                    duration=result.duration,
                                    did_timeout=result.did_timeout,
                                    encoding=result._encoding)

                if result.exit_status:
                    # Error out if the remote ssh command had a problem.
                    raise CommandError(result)

                return result

            error_string = result.stderr

            had_dns_failure = (result.exit_status == 255 and re.search(
                r'^ssh: .*: Name or service not known',
                error_string,
                flags=re.MULTILINE))
            if had_dns_failure:
                dns_retry_count -= 1
                if not dns_retry_count:
                    raise Error('DNS failed to find host.', result)
                logging.debug('Failed to connecto to host, retrying...')
            else:
                break

        had_timeout = re.search(r'^ssh: connect to host .* port .*: '
                                r'Connection timed out\r$',
                                error_string,
                                flags=re.MULTILINE)
        if had_timeout:
            raise Error('Ssh timed out.', result)

        permission_denied = 'Permission denied' in error_string
        if permission_denied:
            raise Error('Permission denied.', result)

        unknown_host = re.search(r'ssh: Could not resolve hostname .*: '
                                 r'Name or service not known',
                                 error_string,
                                 flags=re.MULTILINE)
        if unknown_host:
            raise Error('Unknown host.', result)

        raise Error('The job failed for unkown reasons.', result)

    def run_async(self, command, env=None, connect_timeout=5):
        """Starts up a background command over ssh.

        Will ssh to a remote host and startup a command. This method will
        block until there is confirmation that the remote command has started.

        Args:
            command: The command to execute over ssh. Can be either a string
                     or a list.
            env: A dictonary of enviroment variables to setup on the remote
                 host.
            connect_timeout: How long to wait for the connection confirmation.

        Returns:
            The result of the command to launch the background job.

        Raises:
            CmdTimeoutError: When the remote command took to long to execute.
            SshTimeoutError: When the connection took to long to established.
            SshPermissionDeniedError: When permission is not allowed on the
                                      remote host.
        """
        command = '(%s) < /dev/null > /dev/null 2>&1 & echo -n $!' % command
        result = self.run(command, env=env, connect_timeout=connect_timeout)

        return result

    def _cleanup_master_ssh(self):
        """
        Release all resources (process, temporary directory) used by an active
        master SSH connection.
        """
        # If a master SSH connection is running, kill it.
        if self._background_job is not None:
            logging.debug('Nuking master_ssh_job.')
            self._background_job.close()
            self._background_job = None

        # Remove the temporary directory for the master SSH socket.
        if self._master_ssh_tempdir is not None:
            logging.debug('Cleaning master_ssh_tempdir.')
            shutil.rmtree(self._master_ssh_tempdir)
            self._master_ssh_tempdir = None
