#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

from acts.libs.proc import job


class FastbootError(Exception):
    """Raised when there is an error in fastboot operations."""


class FastbootProxy():
    """Proxy class for fastboot.

    For syntactic reasons, the '-' in fastboot commands need to be replaced
    with '_'. Can directly execute fastboot commands on an object:
    >> fb = FastbootProxy(<serial>)
    >> fb.devices() # will return the console output of "fastboot devices".
    """

    def __init__(self, serial="", ssh_connection=None):
        self.serial = serial
        if serial:
            self.fastboot_str = "fastboot -s {}".format(serial)
        else:
            self.fastboot_str = "fastboot"
        self.ssh_connection = ssh_connection

    def _exec_fastboot_cmd(self, name, arg_str):
        command = ' '.join((self.fastboot_str, name, arg_str))
        if self.ssh_connection:
            return self.connection.run(command).stdout
        else:
            return job.run(command).stdout

    def args(self, *args):
        return job.run(' '.join((self.fastboot_str,) + args)).stdout

    def __getattr__(self, name):
        def fastboot_call(*args):
            clean_name = name.replace('_', '-')
            arg_str = ' '.join(str(elem) for elem in args)
            return self._exec_fastboot_cmd(clean_name, arg_str)

        return fastboot_call
