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

from acts.controllers.utils_lib import background_job
from acts.controllers.utils_lib.ssh import error
from acts.controllers.utils_lib.ssh import formatter


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

    def __init__(self, settings, formatter=formatter.SshFormatter()):
        """
        Args:
            settings: The ssh settings to use for this conneciton.
            formatter: The object that will handle formatting ssh command
                       for use with the background job.
        """
        self._settings = settings
        self._formatter = formatter
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
            SshTimeoutError: If the master ssh connection takes to long to
                             start then a timeout error will be thrown.
        """
        with self._lock:
            if self._background_job is not None:
                socket_path = self.socket_path
                if (not os.path.exists(socket_path) or
                        self._background_jobsp.poll() is not None):
                    logging.info('Master ssh connection to %s is down.',
                                 self.connection.construct_host_name())
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
                self._background_job = background_job.BackgroundJob(
                    master_cmd, no_pipes=True)

                end_time = time.time() + timeout_seconds

                while time.time() < end_time:
                    if os.path.exists(self.socket_path):
                        break
                    time.sleep(.2)
                else:
                    raise error.SshTimeoutError(
                        'Master ssh connection timed out.')

    def run(self,
            command,
            timeout_seconds=3600,
            env={},
            stdout=None,
            stderr=None,
            stdin=None,
            master_connection_timeout=5):
        """Run a remote command over ssh.

        Runs a remote command over ssh.

        Args:
            command: The command to execute over ssh. Can be either a string
                     or a list.
            timeout_seconds: How long to wait on the command before timing out.
            env: A dictonary of enviroment variables to setup on the remote
                 host.
            stdout: A stream to send stdout to.
            stderr: A stream to send stderr to.
            stdin: A string that contains the contents of stdin. A string may
                   also be used, however its contents are not gurenteed to
                   be sent to the ssh process.
            master_connection_timeout: The amount of time to wait for the
                                       master ssh connection to come up.

        Returns:
            The results of the ssh background job.

        Raises:
            CmdTimeoutError: When the remote command took to long to execute.
            SshTimeoutError: When the connection took to long to established.
            SshPermissionDeniedError: When permission is not allowed on the
                                      remote host.
        """
        try:
            self.setup_master_ssh(master_connection_timeout)
        except error.SshError:
            logging.warning('Failed to create master ssh connection, using '
                            'normal ssh connection.')

        extra_options = {'BatchMode': True}
        terminal_command = self._formatter.format_command(
            command, env,
            self._settings,
            extra_options=extra_options)

        dns_retry_count = 2
        while True:
            job = background_job.BackgroundJob(terminal_command,
                                               stdout_tee=stdout,
                                               stderr_tee=stderr,
                                               verbose=False,
                                               stdin=stdin)
            job.wait(timeout_seconds)
            result = job.result
            error_string = result.stderr

            dns_retry_count -= 1
            if (result and result.exit_status == 255 and re.search(
                    r'^ssh: .*: Name or service not known', error_string)):
                if dns_retry_count:
                    logging.debug('Retrying because of DNS failure')
                    continue
                logging.debug('Retry failed.')
            elif not dns_retry_count:
                logging.debug('Retry succeeded.')
            break

        # The error messages will show up in band (indistinguishable
        # from stuff sent through the SSH connection), so we have the
        # remote computer echo the message "Connected." before running
        # any command.  Since the following 2 errors have to do with
        # connecting, it's safe to do these checks.

        # This may not be true in acts?
        if result.exit_status == 255:
            if re.search(r'^ssh: connect to host .* port .*: '
                         r'Connection timed out\r$', error_string):
                raise error.SshTimeoutError('ssh timed out', result)
            if 'Permission denied' in error_string:
                msg = 'ssh permission denied'
                raise error.SshPermissionDeniedError(msg, result)
            if re.search(r'ssh: Could not resolve hostname .*: '
                         r'Name or service not known', error_string):
                raise error.SshUnknownHost('unknown host', result)

        return result

    def _cleanup_master_ssh(self):
        """
        Release all resources (process, temporary directory) used by an active
        master SSH connection.
        """
        # If a master SSH connection is running, kill it.
        if self._background_job is not None:
            logging.debug('Nuking master_ssh_job.')
            self._background_job.force_close()
            self._background_job = None

        # Remove the temporary directory for the master SSH socket.
        if self._master_ssh_tempdir is not None:
            logging.debug('Cleaning master_ssh_tempdir.')
            shutil.rmtree(self._master_ssh_tempdir)
            self._master_ssh_tempdir = None
