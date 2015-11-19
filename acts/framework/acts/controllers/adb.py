#!/usr/bin/python3.4
#
#   Copyright 2014 - The Android Open Source Project
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

import time

from acts.utils import exe_cmd

class AdbError(Exception):
    """Raised when there is an error in adb operations."""

SL4A_LAUNCH_CMD=("am start -a com.googlecode.android_scripting.action.LAUNCH_SERVER "
    "-n com.googlecode.android_scripting/.activity.ScriptingLayerServiceLauncher "
    "--ei com.googlecode.android_scripting.extra.USE_SERVICE_PORT {}")

def get_available_host_ports(num):
    """Gets available host port numbers for adb forward.

    Starting from 9999 and counting down, check if the port is already used by
    adb forward. If so, continue to the next number.

    Args:
        num: Number of port numbers needed.

    Returns:
        A list of integers each representing a port number available for adb
        forward.
    """
    used_ports = list_occupied_ports()
    results = []
    port = 9999
    cnt = 0
    while cnt < num and port > 1024:
        if port not in used_ports:
            results.append(port)
            cnt += 1
        port -= 1
    return results

def list_occupied_ports():
    """Lists all the host ports occupied by adb forward.

    Returns:
        A list of integers representing occupied host ports.
    """
    out = AdbProxy().forward("--list")
    clean_lines = str(out, 'utf-8').strip().split('\n')
    used_ports = []
    for line in clean_lines:
        tokens = line.split(" tcp:")
        if len(tokens) != 3:
            continue
        used_ports.append(int(tokens[1]))
    return used_ports

def is_port_availble(port):
    """Checks if a port number on the host is available.

    Args:
        port: The host port number to check.

    Returns:
        True is this port is available for adb forward.
    """
    return port not in list_occupied_ports()

class AdbProxy():
    """Proxy class for ADB.

    For syntactic reasons, the '-' in adb commands need to be replaced with
    '_'. Can directly execute adb commands on an object:
    >> adb = AdbProxy(<serial>)
    >> adb.start_server()
    >> adb.devices() # will return the console output of "adb devices".
    """
    def __init__(self, serial=""):
        self.serial = serial
        if serial:
            self.adb_str = "adb -s {}".format(serial)
        else:
            self.adb_str = "adb"

    def _exec_adb_cmd(self, name, arg_str):
        return exe_cmd(' '.join((self.adb_str, name, arg_str)))

    def tcp_forward(self, host_port, device_port):
        """Starts tcp forwarding.

        Args:
            host_port: Port number to use on the computer.
            device_port: Port number to use on the android device.
        """
        self.forward("tcp:{} tcp:{}".format(host_port, device_port))

    def start_sl4a(self, port=8080):
        """Starts sl4a server on the android device.

        Args:
            port: Port number to use on the android device.
        """
        self.shell(SL4A_LAUNCH_CMD.format(port))
        # TODO(angli): Make is_sl4a_running reliable so we don't have to do a
        # dumb wait.
        time.sleep(3)
        if not self.is_sl4a_running():
            raise AdbError(
              "com.googlecode.android_scripting process never started.")

    def is_sl4a_running(self):
        """Checks if the sl4a app is running on an android device.

        Returns:
            True if the sl4a app is running, False otherwise.
        """
        #Grep for process with a preceding S which means it is truly started.
        out = self.shell('ps | grep "S com.googlecode.android_scripting"')
        if len(out)==0:
          return False
        return True

    def __getattr__(self, name):
        def adb_call(*args):
            clean_name = name.replace('_', '-')
            arg_str = ' '.join(str(elem) for elem in args)
            return self._exec_adb_cmd(clean_name, arg_str)
        return adb_call
