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


class FuchsiaBleLib():
    def __init__(self, addr, tc, client_id):
        self.address = addr
        self.test_counter = tc
        self.client_id = client_id

    def build_id(self, test_id):
        """Concatenates client_id and test_id to form a command_id.
            
        Args:
            test_id: string, unique identifier of test command.
        """
        return self.client_id + "." + str(test_id)

    def send_command(self, test_id, test_cmd, test_args):
        """Builds and sends a JSON command to SL4F server.

        Args:
            test_id: string, unique identifier of test command.
            test_cmd: string, sl4f method name of command.
            test_args: dictionary, arguments required to execute test_cmd.

        Returns:
            Dictionary, Result of sl4f command executed.
        """
        test_data = json.dumps({
            "jsonrpc": "2.0",
            "id": test_id,
            "method": test_cmd,
            "params": test_args
        })
        test_res = requests.get(url=self.address, data=test_data).json()
        return test_res

    def bleStopBleAdvertising(self):
        """BleStopAdvertising command
  
        Returns:
            Dictionary, None if success, error string if error.
        """
        test_cmd = "bluetooth.BleStopAdvertise"
        test_args = {}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleStartBleAdvertising(self, advertising_data, interval):
        """BleStartAdvertising command

        Args:
            advertising_data: dictionary, advertising data required for ble advertise.
            interval: int, Advertising interval (in ms).

        Returns:
            Dictionary, None if success, error string if error.
        """
        test_cmd = "bluetooth.BleAdvertise"
        test_args = {
            "advertising_data": advertising_data,
            "interval_ms": interval
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleStartBleScan(self, scan_time_ms, scan_filter, scan_count):
        """Starts a BLE scan

        Args:
            scan_time_ms: int, Amount of time to scan for.
            scan_filter: dictionary, Device filter for a scan.
            scan_count: int, Number of devices to scan for before termination.

        Returns:
            Dictionary, List of devices discovered, error string if error.
        """
        test_cmd = "bluetooth.BleScan"
        test_args = {
            "scan_time_ms": scan_time_ms,
            "filter": scan_filter,
            "scan_count": scan_count
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleConnectToPeripheral(self, id):
        """Connects to a peripheral specified by id.

        Args:
            id: string, Peripheral identifier to connect to.

        Returns:
            Dictionary, List of Service Info if success, error string if error.
        """
        test_cmd = "bluetooth.BleConnectPeripheral"
        test_args = {"identifier": id}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleDisconnectPeripheral(self, id):
        """Disconnects from a peripheral specified by id.

        Args:
            id: string, Peripheral identifier to disconnect from.

        Returns:
            Dictionary, None if success, error string if error.
        """
        test_cmd = "bluetooth.BleDisconnectPeripheral"
        test_args = {"identifier": id}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleListServices(self, id):
        """Lists services of a peripheral specified by id.

        Args:
            id: string, Peripheral identifier to list services.

        Returns:
            Dictionary, List of Service Info if success, error string if error.
        """
        test_cmd = "bluetooth.BleListServices"
        test_args = {"identifier": id}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def blePublishService(self, id_, primary, type_, service_id):
        """Publishes services specified by input args

        Args:
            id: string, Identifier of service.
            primary: bool, Flag of service.
            type: string, Canonical 8-4-4-4-12 uuid of service.
            service_proxy_key: string, Unique identifier to specify where to publish service

        Returns:
            Dictionary, None if success, error if error.
        """
        test_cmd = "bluetooth.BlePublishService"
        test_args = {
            "id": id_,
            "primary": primary,
            "type": type_,
            "local_service_id": service_id
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)
