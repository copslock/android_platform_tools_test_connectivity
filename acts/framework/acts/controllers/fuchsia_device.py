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

import collections
import json
import logging
import math
import os
import random
import re
import requests
import socket
import time
import urllib as ul
import webbrowser
import xmlrpc.client

from subprocess import call

from acts import logger as acts_logger
from acts import signals
from acts import tracelogger
from acts import utils

from acts.controllers.fuchsia_lib.ble_lib import FuchsiaBleLib

ACTS_CONTROLLER_CONFIG_NAME = "FuchsiaDevice"
ACTS_CONTROLLER_REFERENCE_NAME = "fuchsia_devices"

FUCHSIA_DEVICE_EMPTY_CONFIG_MSG = "Configuration is empty, abort!"
FUCHSIA_DEVICE_NOT_LIST_CONFIG_MSG = "Configuration should be a list, abort!"

SL4F_APK_NAME = "com.googlecode.android_scripting"


class FuchsiaDeviceError(signals.ControllerError):
    pass


def create(configs):
    if not configs:
        raise FuchsiaDeviceError(FUCHSIA_DEVICE_EMPTY_CONFIG_MSG)
    elif not isinstance(configs, list):
        raise FuchsiaDeviceError(FUCHSIA_DEVICE_NOT_LIST_CONFIG_MSG)
    elif isinstance(configs[0], str):
        # Configs is a list of IP addresses
        f_devices = get_instances(configs)
    return f_devices


def destroy(fds):
    for fd in fds:
        del fd


def get_info(fds):
    """Get information on a list of FuchsiaDevice objects.

    Args:
        fds: A list of FuchsiaDevice objects.

    Returns:
        A list of dict, each representing info for FuchsiaDevice objects.
    """
    device_info = []
    for fd in fds:
        info = {"ip": fd.ip}
        device_info.append(info)
    return device_info


def get_instances(ips):
    """Create FuchsiaDevice instances from a list of Fuchsia ips.

    Args:
        ips: A list of Fuchsia ip addrs

    Returns:
        A list of FuchsiaDevice objects.
    """

    return [FuchsiaDevice(ip) for ip in ips]


class FuchsiaDevice:
    """Class representing a Fuchsia device.

    Each object of this class represents one Fuchsia device in ACTS.

    Attributes:
        address: The full address to contact the Fuchsia device at
        log: A logger object.
        port: The TCP port number of the Fuchsia device.
    """

    def __init__(self, ip="", port=80):
        """
        Args:
            ip: string, Ip address of fuchsia device.
            port: int, Port number of connection
        """
        log_path_base = getattr(logging, "log_path", "/tmp/logs")
        self.log_path = os.path.join(log_path_base, "FuchsiaDevice%s" % ip)
        self.log = tracelogger.TraceLogger(
            FuchsiaDeviceLoggerAdapter(logging.getLogger(), {"ip": ip}))

        self.ip = ip
        self.log = logging.getLogger()
        self.port = port

        self.address = "http://{}:{}".format(ip, self.port)
        self.init_address = self.address + "/init"
        self.cleanup_address = self.address + "/cleanup"
        self.print_address = self.address + "/print_clients"

        # TODO(): Come up with better client numbering system
        self.client_id = "FuchsiaClient" + str(random.randint(0, 1000000))
        self.test_counter = 0

        # Grab commands from FuchsiaBleLib
        setattr(self, "ble_lib",
                FuchsiaBleLib(self.address, self.test_counter, self.client_id))

        #Init server
        self.init_server_connection()

    def build_id(self, test_id):
        """Concatenates client_id and test_id to form a command_id
            
        Args:
            test_id: string, unique identifier of test command
        """
        return self.client_id + "." + str(test_id)

    def init_server_connection(self):
        """Initializes HTTP connection with SL4F server."""
        self.log.debug("Initialziing server connection")
        init_data = json.dumps({
            "jsonrpc": "2.0",
            "id": self.build_id(self.test_counter),
            "method": "sl4f.sl4f_init",
            "params": {
                "client_id": self.client_id
            }
        })
        r = requests.get(url=self.init_address, data=init_data)
        self.test_counter += 1

    def print_clients(self):
        """Gets connected clients from SL4F server"""
        self.log.debug("Request to print clients")
        print_id = self.build_id(self.test_counter)
        print_args = {}
        print_method = "sl4f.sl4f_print_clients"
        data = json.dumps({
            "jsonrpc": "2.0",
            "id": print_id,
            "method": print_method,
            "params": print_args
        })

        r = requests.get(url=self.print_address, data=data).json()
        self.test_counter += 1

        return r

    def clean_up(self):
        """Cleans up the FuchsiaDevice object and releases any resources it
        claimed.
        """
        cleanup_id = self.build_id(self.test_counter)
        cleanup_args = {}
        cleanup_method = "sl4f.sl4f_cleanup"
        data = json.dumps({
            "jsonrpc": "2.0",
            "id": cleanup_id,
            "method": cleanup_method,
            "params": cleanup_args
        })

        r = requests.get(url=self.cleanup_address, data=data).json()
        self.test_counter += 1

        self.log.debug("Cleaned up with status: ", r)
        return r

    def start_services(self, skip_sl4f=False, skip_setup_wizard=True):
        """Starts long running services on the Fuchsia device.

        1. Start adb logcat capture.
        2. Start SL4F if not skipped.

        Args:
            skip_sl4f: Does not attempt to start SL4F if True.
            skip_setup_wizard: Whether or not to skip the setup wizard.
        """
        pass

    def stop_services(self):
        """Stops long running services on the android device.

        Stop adb logcat and terminate sl4f sessions if exist.
        """
        pass

    def load_config(self, config):
        pass


class FuchsiaDeviceLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        msg = "[FuchsiaDevice|%s] %s" % (self.extra["ip"], msg)
        return (msg, kwargs)
