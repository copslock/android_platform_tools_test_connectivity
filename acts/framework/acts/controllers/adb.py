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

from builtins import str

import logging
import random
import socket
import time

from acts.controllers.utils_lib import host_utils
from acts.controllers.utils_lib.ssh import connection
from acts.libs.proc import job

class AdbError(Exception):
    """Raised when there is an error in adb operations."""

    def __init__(self, cmd, stdout, stderr, ret_code):
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        self.ret_code = ret_code

    def __str__(self):
        return ("Error executing adb cmd '%s'. ret: %d, stdout: %s, stderr: %s"
                ) % (self.cmd, self.ret_code, self.stdout, self.stderr)


class AdbProxy(object):
    """Proxy class for ADB.

    For syntactic reasons, the '-' in adb commands need to be replaced with
    '_'. Can directly execute adb commands on an object:
    >> adb = AdbProxy(<serial>)
    >> adb.start_server()
    >> adb.devices() # will return the console output of "adb devices".
    """

    _SERVER_LOCAL_PORT = None

    def __init__(self, serial="", ssh_connection=None):
        """Construct an instance of AdbProxy.

        Args:
            serial: str serial number of Android device from `adb devices`
            ssh_connection: SshConnection instance if the Android device is
                            conected to a remote host that we can reach via SSH.
        """
        self.serial = serial
        adb_path = str(self._exec_cmd("which adb"), "utf-8").strip()
        adb_cmd = [adb_path]
        if serial:
            adb_cmd.append("-s %s" % serial)
        if ssh_connection is not None and not AdbProxy._SERVER_LOCAL_PORT:
            # Kill all existing adb processes on the remote host (if any)
            # Note that if there are none, then pkill exits with non-zero status
            ssh_connection.run("pkill adb", ignore_status=True)
            # Copy over the adb binary to a temp dir
            temp_dir = ssh_connection.run("mktemp -d").stdout.strip()
            ssh_connection.send_file(adb_path, temp_dir)
            # Start up a new adb server running as root from the copied binary.
            remote_adb_cmd = "%s/adb %s root" % (
                temp_dir,
                "-s %s" % serial if serial else "")
            ssh_connection.run(remote_adb_cmd)
            # Proxy a local port to the adb server port
            local_port = ssh_connection.create_ssh_tunnel(5037)
            AdbProxy._SERVER_LOCAL_PORT = local_port

        if AdbProxy._SERVER_LOCAL_PORT:
            adb_cmd.append("-P %d" % local_port)
        self.adb_cmd = " ".join(adb_cmd)
        self._ssh_connection = ssh_connection

    def _exec_cmd(self, cmd):
        """Executes adb commands in a new shell.

        This is specific to executing adb binary because stderr is not a good
        indicator of cmd execution status.

        Args:
            cmds: A string that is the adb command to execute.

        Returns:
            The output of the adb command run if exit code is 0.

        Raises:
            AdbError is raised if the adb command exit code is not 0.
        """
        result = job.run(cmd, ignore_status=True)
        ret, out, err = result.exit_status, result.raw_stdout, result.raw_stderr

        logging.debug("cmd: %s, stdout: %s, stderr: %s, ret: %s", cmd, out,
                      err, ret)
        if ret == 0:
            return out
        else:
            raise AdbError(cmd=cmd, stdout=out, stderr=err, ret_code=ret)

    def _exec_adb_cmd(self, name, arg_str):
        return self._exec_cmd(' '.join((self.adb_str, name, arg_str)))

    def tcp_forward(self, host_port, device_port):
        """Starts tcp forwarding.

        Args:
            host_port: Port number to use on the computer.
            device_port: Port number to use on the android device.
        """
        if self._ssh_connection:
            # TODO(wiley): We need to actually pick a free port on the
            #              intermediate host
            self._ssh_connection.create_ssh_tunnel(host_port, local_port=host_port)
        self.forward("tcp:{} tcp:{}".format(host_port, device_port))

    def getprop(self, prop_name):
        """Get a property of the device.

        This is a convenience wrapper for "adb shell getprop xxx".

        Args:
            prop_name: A string that is the name of the property to get.

        Returns:
            A string that is the value of the property, or None if the property
            doesn't exist.
        """
        return self.shell("getprop %s" % prop_name).decode("utf-8").strip()

    def __getattr__(self, name):
        def adb_call(*args):
            clean_name = name.replace('_', '-')
            arg_str = ' '.join(str(elem) for elem in args)
            return self._exec_adb_cmd(clean_name, arg_str)

        return adb_call
