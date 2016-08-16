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
import re

import background_job
import ssh_error
import ssh_formatter


class SshConnection(object):
    """Provides a connection to a remote machine through ssh.

    Provides the ability to connect to a remote machine and execute a command
    on it.
    """

    def __init__(self, settings, formatter=ssh_formatter.SshFormatter()):
        """
            Args:
                settings: The ssh settings to use for this conneciton.
                formatter: The object that will handle formatting ssh command
                           for use with the background job.
        """
        self._settings = settings
        self._formatter = formatter

    def run(self,
            command,
            timeout_seconds=3600,
            env={},
            stdout=None,
            stderr=None,
            stdin=None):
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

        Returns:
            The results of the ssh background job.

        Raises:
            CmdTimeoutError: When the remote command took to long to execute.
            SshTimeoutError: When the connection took to long to established.
            SshPermissionDeniedError: When permission is not allowed on the
                                      remote host.
        """
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
                raise ssh_error.SshTimeoutError('ssh timed out', result)
            if 'Permission denied' in error_string:
                msg = 'ssh permission denied'
                raise ssh_error.SshPermissionDeniedError(msg, result)
            if re.search(r'ssh: Could not resolve hostname .*: '
                         r'Name or service not known', error_string):
                raise ssh_error.SshUnknownHost('unknown host', result)

        return result
