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

    # The id of a command is: client_id.test_id
    def build_id(self, test_id):
        return self.client_id + "." + str(test_id)

    def send_command(self, test_id, test_cmd, test_args):
        test_data = json.dumps({
            "jsonrpc": "2.0",
            "id": test_id,
            "method": test_cmd,
            "params": test_args
        })
        test_res = requests.get(url=self.address, data=test_data).json()
        return test_res

    #Formulate args based on FIDL API, with key = fidl api arg name (verbatim)
    def bleStopBleAdvertising(self):
        test_cmd = "bluetooth.BleStopAdvertise"
        test_args = {}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleStartBleAdvertising(self, interval, advertising_data):
        test_cmd = "bluetooth.BleAdvertise"
        test_args = {
            "advertising_data": advertising_data,
            "interval_ms": interval
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def bleStartBleScan(self, scan_time_ms, scan_filter, scan_count):
        test_cmd = "bluetooth.BleScan"
        test_args = {
            "scan_time_ms": scan_time_ms,
            "filter": scan_filter,
            "scan_count": scan_count
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)
