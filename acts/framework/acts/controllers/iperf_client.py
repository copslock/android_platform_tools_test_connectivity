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
"""
Starts iperf client on host machine.
"""
import os
import logging
import subprocess

from acts import utils
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings

ACTS_CONTROLLER_CONFIG_NAME = "IPerfClient"
ACTS_CONTROLLER_REFERENCE_NAME = "iperf_clients"


def create(configs):
    """ Factory method for iperf client.

    The function creates iperf clients based on at least one config.
    If configs only specify a port number, a regular local IPerfClient object
    will be created. If configs contains ssh settings for a remote host,
    a RemoteIPerfClient object will be instantiated

    Args:
        config: config parameters for the iperf client
    """
    results = []
    print(configs)
    for c in configs:
        try:
            results.append(IPerfClient(c))
        except:
            pass
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
        if type(config) is dict and "ssh_config" in config:
            self.ssh_settings = settings.from_config(config["ssh_config"])
            self.ssh_session = connection.SshConnection(self.ssh_settings)
            self.client_type = "remote"
        else:
            self.client_type = config["type"]
        self.iperf_process = None
        self.log_files = []

    def start(self, iperf_args, ad, ip, test_name):
        """Starts iperf client on specified port.

        Args:
            iperf_args: A string representing arguments to start iperf
            client. Eg: iperf_args = "-t 10 -p 5001 -w 512k/-u -b 200M -J".
            ad: Android device object.
            ip: Iperf server ip address.

        Returns:
            full_out_path: Iperf result path.
        """
        iperf_cmd = "iperf3 -c {} ".format(ip) + iperf_args
        port = iperf_cmd.split(' ')[6]
        log_path = os.path.join(ad.log_path, test_name, "iPerf{}".format(port))
        utils.create_dir(log_path)
        out_file_name = "IPerfClient,{},{}.log".format(port, len(
            self.log_files))
        full_out_path = os.path.join(log_path, out_file_name)
        if self.client_type == "remote":
            try:
                job_result = self.ssh_session.run(iperf_cmd)
                self.iperf_process = job_result.stdout
                with open(full_out_path, 'w') as outfile:
                    outfile.write(self.iperf_process)
            except Exception:
                logging.info("Iperf run failed.")
        else:
            cmd = iperf_cmd.split()
            with open(full_out_path, "w") as f:
                subprocess.call(cmd, stdout=f)
        self.log_files.append(full_out_path)
        return full_out_path
