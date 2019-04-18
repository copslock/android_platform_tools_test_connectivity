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
from acts import logger
from acts.controllers.fuchsia_lib.base_lib import BaseLib

COMMAND_SCAN = "wlan.scan"
COMMAND_CONNECT = "wlan.connect"
COMMAND_DISCONNECT = "wlan.disconnect"

class FuchsiaWlanLib(BaseLib):
    def __init__(self, addr, tc, client_id):
        self.address = addr
        self.test_counter = tc
        self.client_id = client_id
        self.log = logger.create_tagged_trace_logger(str(addr))

    def wlanStartScan(self):
        """ Starts a wlan scan

                Returns:
                    scan results
        """
        test_cmd = COMMAND_SCAN
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, {})

    def wlanConnectToNetwork(self, target_ssid, target_pwd=None):
        """ Triggers a network connection
                Args:
                    target_ssid: the network to attempt a connection to
                    target_pwd: (optional) password for the target network

                Returns:
                    boolean indicating if the connection was successful
        """
        test_cmd = COMMAND_CONNECT
        test_args = {
            "target_ssid": target_ssid,
            "target_pwd": target_pwd
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def check_connection_for_response(self, connection_response):
        if connection_response.get("error") is None:
            # the command did not get an error response - go ahead and check the
            # result
            connection_result = connection_response.get("result")
            if not connection_result:
                # ideally, we would have the actual error...
                # but logging here to cover that error case
                self.log.error("Connect call failed, aborting!")
                return False
            else:
                # connection successful
                return True
        else:
            # the response indicates an error - log and raise failure
            self.log.error("Aborting! - Connect call failed with error: %s"
                           % connection_response.get("error"))
            return False

    def wlanDisconnect(self):
        """ Disconnect any current wifi connections"""
        test_cmd = COMMAND_DISCONNECT
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, {})

