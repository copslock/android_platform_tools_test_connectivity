#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Python script for wrappers to various libraries.
"""

import cmd
"""Various Global Strings"""
CMD_LOG = "CMD {} result: {}"
FAILURE = "CMD {} threw exception: {}"


class CmdInput(cmd.Cmd):
    """Simple command processor for Bluetooth PTS Testing"""

    def setup_vars(self, android_devices, mac_addr, log):
        self.pri_dut = android_devices[0]
        if len(android_devices) > 1:
            self.sec_dut = android_devices[1]
            self.ter_dut = android_devices[2]
        self.mac_addr = mac_addr
        self.log = log

    def emptyline(self):
        pass

    def do_EOF(self, line):
        "End Script"
        return True
