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

import os
import logging
import subprocess
from acts import utils
from acts.controllers import android_device
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings

ACTS_CONTROLLER_CONFIG_NAME = "IPerfClient"
ACTS_CONTROLLER_REFERENCE_NAME = "iperf_clients"


def create(configs):
    """ Factory method for iperf clients.

    The function creates iperf clients based on at least one config.
    If configs contain ssh settings or and AndroidDevice, remote iperf clients
    will be started on those devices, otherwise, a the client will run on the
    local machine.

    Args:
        config: config parameters for the iperf server
    """
    results = []
    for c in configs:
        if type(c) is dict and "AndroidDevice" in c:
            results.append(IPerfClientOverAdb(c))
        elif type(c) is dict and "ssh_config" in c:
            results.append(IPerfClientOverSsh(c))
        else:
            results.append(IPerfClient(c))
    return results


def destroy(objs):
    for ipf in objs:
        try:
            ipf.stop()
        except:
            pass


class IPerfClient():
    """Class that handles iperf3 client operations."""

    def __init__(self, config):
        self.client_type = "local"
        self.log_path = os.path.join(logging.log_path, "iperf_client_files")
        utils.create_dir(self.log_path)
        self.log_files = []

    def start(self, ip, iperf_args, tag, timeout=3600):
        """Starts iperf client on specified port.

        Args:
            ip: iperf server ip address.
            iperf_args: A string representing arguments to start iperf
            client. Eg: iperf_args = "-t 10 -p 5001 -w 512k/-u -b 200M -J".
            tag: tag to further identify iperf results file

        Returns:
            full_out_path: iperf result path.
        """
        iperf_cmd = "iperf3 -c {} {} ".format(ip, iperf_args)
        out_file_name = "IPerfClient,{},{}.log".format(tag, len(
            self.log_files))
        full_out_path = os.path.join(self.log_path, out_file_name)
        cmd = iperf_cmd.split()
        with open(full_out_path, "w") as out_file:
            subprocess.call(cmd, stdout=out_file)
        self.log_files.append(full_out_path)
        return full_out_path


class IPerfClientOverSsh():
    """Class that handles iperf3 client operations on remote machines."""

    def __init__(self, config):
        self.client_type = "remote"
        self.ssh_settings = settings.from_config(config["ssh_config"])
        self.ssh_session = connection.SshConnection(self.ssh_settings)
        self.log_path = os.path.join(logging.log_path, "iperf_client_files")
        utils.create_dir(self.log_path)
        self.log_files = []

    def start(self, ip, iperf_args, tag, timeout=3600):
        """Starts iperf client on specified port.

        Args:
            ip: iperf server ip address.
            iperf_args: A string representing arguments to start iperf
            client. Eg: iperf_args = "-t 10 -p 5001 -w 512k/-u -b 200M -J".
            tag: tag to further identify iperf results file

        Returns:
            full_out_path: iperf result path.
        """
        iperf_cmd = "iperf3 -c {} {} ".format(ip, iperf_args)
        out_file_name = "IPerfClient,{},{}.log".format(tag, len(
            self.log_files))
        full_out_path = os.path.join(self.log_path, out_file_name)
        try:
            iperf_process = self.ssh_session.run(iperf_cmd, timeout=timeout)
            iperf_output = iperf_process.stdout
            with open(full_out_path, 'w') as out_file:
                out_file.write(iperf_output)
        except Exception:
            logging.info("iperf run failed.")
        self.log_files.append(full_out_path)
        return full_out_path


class IPerfClientOverAdb():
    """Class that handles iperf3 operations over ADB devices."""

    def __init__(self, config):
        # Note: skip_sl4a must be set to True in iperf server config since
        # ACTS may have already initialized and started services on device
        self.client_type = "adb"
        self.adb_device = android_device.create(config["AndroidDevice"])
        self.adb_device = self.adb_device[0]
        self.log_path = os.path.join(logging.log_path, "iperf_client_files")
        utils.create_dir(self.log_path)
        self.log_files = []

    def start(self, ip, iperf_args, tag, timeout=3600):
        """Starts iperf client on specified port.

        Args:
            ip: iperf server ip address.
            iperf_args: A string representing arguments to start iperf
            client. Eg: iperf_args = "-t 10 -p 5001 -w 512k/-u -b 200M -J".
            tag: tag to further identify iperf results file

        Returns:
            full_out_path: iperf result path.
        """
        try:
            iperf_output = ""
            iperf_status, iperf_output = self.adb_device.run_iperf_client(
                ip, iperf_args, timeout=timeout)
        except:
            self.log.warning("TimeoutError: Iperf measurement timed out.")
        out_file_name = "IPerfClient,{},{}.log".format(tag, len(
            self.log_files))
        full_out_path = os.path.join(self.log_path, out_file_name)
        with open(full_out_path, 'w') as out_file:
            out_file.write("\n".join(iperf_output))
        self.log_files.append(full_out_path)
        return full_out_path