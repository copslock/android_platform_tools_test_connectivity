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
import shutil
import tempfile
import threading
import time

import background_job
import ssh_connection
import ssh_error
import ssh_formatter


class MasterSshConnection(ssh_connection.SshConnection):
    """An ssh connection that uses a master connection.

    Works similar to an ssh connection, however it will leave a master
    connection open while this object is alive. This allows multiple
    commands to be executed in a row without waiting for an ssh handshake.
    """

    @property
    def socket_path(self):
        """Returns: The os path to the master socket file."""
        return os.path.join(self._master_ssh_tempdir, 'socket')

    def __init__(self, settings, formatter=ssh_formatter.SshFormatter()):
        """
        Args:
            settings: The ssh settings to use.
            formatter: The formatter to use to construct commands.
        """
        super(MasterSshConnection, self).__init__(settings, formatter)
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
                                 'ControlPath': self.socket_path}

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
                    raise ssh_error.SshTimeoutError(
                        'Master ssh connection timed out.')

    def run(self,
            command,
            timeout_seconds=3600,
            env=None,
            stdout=None,
            stderr=None,
            stdin=None,
            master_connection_timeout=5):
        """See SshConnection.run for doc.

        Args:
            master_connection_timeout: How long to wait for the master ssh
                                       connection before reverting to normal
                                       ssh.
        """
        try:
            self.setup_master_ssh(master_connection_timeout)
        except ssh_error.SshError:
            logging.log('Failed to create master ssh connection, using normal'
                        'ssh connection.')
        return super(MasterSshConnection, self).run(command, timeout_seconds,
                                                    env, stdout, stderr, stdin)

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
