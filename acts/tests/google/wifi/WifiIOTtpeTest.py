#!/usr/bin/env python3.4
#
#   Copyright 2017 - The Android Open Source Project
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

import itertools
import pprint
import time

import acts.signals
import acts.test_utils.wifi.wifi_test_utils as wutils

from acts import asserts
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

WifiEnums = wutils.WifiEnums


class WifiIOTtpeTest(WifiBaseTest):
    """ Tests for wifi IOT

        Test Bed Requirement:
          * One Android device
          * Wi-Fi IOT networks visible to the device
    """

    def __init__(self, controllers):
        self.attenuators = None
        WifiBaseTest.__init__(self, controllers)

    def setup_class(self):
        self.dut = self.android_devices[0]
        wutils.wifi_test_device_init(self.dut)

        req_params = [ "iot_networks", ]
        opt_params = [ "open_network", "iperf_server_address" ]
        self.unpack_userparams(req_param_names=req_params,
                               opt_param_names=opt_params)

        asserts.assert_true(
            len(self.iot_networks) > 0,
            "Need at least one iot network with psk.")

        if getattr(self, 'open_network', False):
            self.iot_networks.append(self.open_network)

        wutils.wifi_toggle_state(self.dut, True)
        if "iperf_server_address" in self.user_params:
            self.iperf_server = self.iperf_servers[0]
            self.iperf_server.start()

        # create hashmap for testcase name and SSIDs
        self.iot_test_prefix = "test_iot_connection_to_"
        self.ssid_map = {}
        for network in self.iot_networks:
            SSID = network['SSID'].replace('-','_')
            self.ssid_map[SSID] = network

    def setup_test(self):
        self.dut.droid.wakeLockAcquireBright()
        self.dut.droid.wakeUpNow()

    def teardown_test(self):
        self.dut.droid.wakeLockRelease()
        self.dut.droid.goToSleepNow()
        wutils.reset_wifi(self.dut)

    def teardown_class(self):
        if "iperf_server_address" in self.user_params:
            self.iperf_server.stop()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.cat_adb_log(test_name, begin_time)

    """Helper Functions"""

    def connect_to_wifi_network(self, network):
        """Connection logic for open and psk wifi networks.

        Args:
            params: Dictionary with network info.
        """
        SSID = network[WifiEnums.SSID_KEY]
        self.dut.ed.clear_all_events()
        wutils.start_wifi_connection_scan(self.dut)
        scan_results = self.dut.droid.wifiGetScanResults()
        wutils.assert_network_in_list({WifiEnums.SSID_KEY: SSID}, scan_results)
        wutils.wifi_connect(self.dut, network, num_of_tries=3)

    def run_iperf_client(self, network):
        """Run iperf traffic after connection.

        Args:
            params: Dictionary with network info.
        """
        if "iperf_server_address" in self.user_params:
            wait_time = 5
            SSID = network[WifiEnums.SSID_KEY]
            self.log.info("Starting iperf traffic through {}".format(SSID))
            time.sleep(wait_time)
            port_arg = "-p {}".format(self.iperf_server.port)
            success, data = self.dut.run_iperf_client(self.iperf_server_address,
                                                      port_arg)
            self.log.debug(pprint.pformat(data))
            asserts.assert_true(success, "Error occurred in iPerf traffic.")

    def connect_to_wifi_network_and_run_iperf(self, network):
        """Connection logic for open and psk wifi networks.

        Logic steps are
        1. Connect to the network.
        2. Run iperf traffic.

        Args:
            params: A dictionary with network info.
        """
        self.connect_to_wifi_network(network)
        self.run_iperf_client(network)

    """Tests"""

    #ASUS
    @test_tracker_info(uuid="d56cc46a-f772-4c96-b84e-4e05c82f5f9d")
    def test_iot_connection_to_ASUS_RT_AC68U_2G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])

    def test_iot_connection_to_ASUS_RT_AC68U_5G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])

    def test_iot_connection_to_ASUS_RT_AC66U_2G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])

    def test_iot_connection_to_ASUS_RT_AC66U_5G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])

    def test_iot_connection_to_ASUS_RT_N66U_2G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])

    def test_iot_connection_to_ASUS_RT_N66U_5G(self):
        ssid_key = self.current_test_name.replace(self.iot_test_prefix, "")
        self.connect_to_wifi_network_and_run_iperf(self.ssid_map[ssid_key])  
  
