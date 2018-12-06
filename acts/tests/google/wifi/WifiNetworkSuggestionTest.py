#!/usr/bin/env python3.4
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

import itertools
import pprint
import queue
import time

import acts.base_test
import acts.signals as signals
import acts.test_utils.wifi.wifi_test_utils as wutils
import acts.utils

from acts import asserts
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest
from acts.test_utils.wifi import wifi_constants

WifiEnums = wutils.WifiEnums

# Default timeout used for reboot, toggle WiFi and Airplane mode,
# for the system to settle down after the operation.
DEFAULT_TIMEOUT = 10

class WifiNetworkSuggestionTest(WifiBaseTest):
    """Tests for WifiNetworkSuggestion API surface.

    Test Bed Requirement:
    * one Android device
    * Several Wi-Fi networks visible to the device, including an open Wi-Fi
      network.
    """

    def __init__(self, controllers):
        WifiBaseTest.__init__(self, controllers)

    def setup_class(self):
        self.dut = self.android_devices[0]
        wutils.wifi_test_device_init(self.dut)
        req_params = []
        opt_param = [
            "open_network", "reference_networks"
        ]
        self.unpack_userparams(
            req_param_names=req_params, opt_param_names=opt_param)

        if "AccessPoint" in self.user_params:
            self.legacy_configure_ap_and_start(wpa_network=True,
                                               wep_network=True)

        asserts.assert_true(
            len(self.reference_networks) > 0,
            "Need at least one reference network with psk.")
        self.wpa_psk_2g = self.reference_networks[0]["2g"]
        self.wpa_psk_5g = self.reference_networks[0]["5g"]
        self.open_2g = self.open_network[0]["2g"]
        self.open_5g = self.open_network[0]["5g"]
        self.dut.droid.wifiRemoveNetworkSuggestions([])

    def setup_test(self):
        self.dut.droid.wakeLockAcquireBright()
        self.dut.droid.wakeUpNow()
        wutils.wifi_toggle_state(self.dut, True)

    def teardown_test(self):
        self.dut.droid.wakeLockRelease()
        self.dut.droid.goToSleepNow()
        self.dut.droid.wifiRemoveNetworkSuggestions([])
        wutils.reset_wifi(self.dut)
        self.dut.ed.clear_all_events()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.cat_adb_log(test_name, begin_time)

    def teardown_class(self):
        if "AccessPoint" in self.user_params:
            del self.user_params["reference_networks"]
            del self.user_params["open_network"]

    """Helper Functions"""
    def add_suggestions_and_ensure_connection(self, network_suggestions,
                                              expected_ssid,
                                              expect_post_connection_broadcast):
        self.dut.log.info("Adding network suggestions");
        asserts.assert_true(
            self.dut.droid.wifiAddNetworkSuggestions(network_suggestions),
            "Failed to add suggestions")
        wutils.wait_for_connect(self.dut, expected_ssid)

        if expect_post_connection_broadcast is None:
            return;

        # Check if we expected to get the broadcast.
        try:
            self.dut.droid.wifiStartTrackingStateChange()
            event = self.dut.ed.pop_event(
                wifi_constants.WIFI_NETWORK_SUGGESTION_POST_CONNECTION, 60)
            self.dut.droid.wifiStopTrackingStateChange()
        except queue.Empty:
            if expect_post_connection_broadcast:
                raise signals.TestFailure(
                    "Did not receive post connection broadcast")
        else:
            if not expect_post_connection_broadcast:
                raise signals.TestFailure(
                    "Received post connection broadcast")


    @test_tracker_info(uuid="bda8ed20-4382-4380-831a-64cf77eca108")
    def test_connect_to_wpa_psk_2g(self):
        """ Adds a network suggestion and ensure that the device connected.

        Steps:
        1. Send a network suggestion to the device.
        2. Wait for the device to connect to it.
        3. Ensure that we did not receive the post connection broadcast
           (isAppInteractionRequired = False).
        4. Remove the suggestions and ensure the device disconnected.
        """
        self.add_suggestions_and_ensure_connection(
            [self.wpa_psk_2g], self.wpa_psk_2g[WifiEnums.SSID_KEY],
            False)
        self.dut.log.info("Removing network suggestions");
        asserts.assert_true(
            self.dut.droid.wifiRemoveNetworkSuggestions([self.wpa_psk_2g]),
            "Failed to remove suggestions")
        wutils.wait_for_disconnect(self.dut)


    @test_tracker_info(uuid="b1d27eea-23c8-4c4f-b944-ef118e4cc35f")
    def test_connect_to_wpa_psk_2g_with_post_connection_broadcast(self):
        """ Adds a network suggestion and ensure that the device connected.

        Steps:
        1. Send a network suggestion to the device with
           isAppInteractionRequired set.
        2. Wait for the device to connect to it.
        3. Ensure that we did receive the post connection broadcast
           (isAppInteractionRequired = True).
        4. Remove the suggestions and ensure the device disconnected.
        """
        network_suggestion = self.wpa_psk_2g
        network_suggestion[WifiEnums.IS_APP_INTERACTION_REQUIRED] = True
        self.add_suggestions_and_ensure_connection(
            [network_suggestion], self.wpa_psk_2g[WifiEnums.SSID_KEY],
            True)
        self.dut.log.info("Removing network suggestions");
        asserts.assert_true(
            self.dut.droid.wifiRemoveNetworkSuggestions([network_suggestion]),
            "Failed to remove suggestions")
        wutils.wait_for_disconnect(self.dut)


    @test_tracker_info(uuid="a036a24d-29c0-456d-ae6a-afdde34da710")
    def test_connect_to_wpa_psk_5g_reboot_config_store(self):
        """
        Adds a network suggestion and ensure that the device connects to it
        after reboot.

        Steps:
        1. Send a network suggestion to the device.
        2. Wait for the device to connect to it.
        3. Ensure that we did not receive the post connection broadcast
           (isAppInteractionRequired = False).
        4. Reboot the device.
        5. Wait for the device to connect to back to it.
        6. Remove the suggestions and ensure the device disconnected.
        """
        self.add_suggestions_and_ensure_connection(
            [self.wpa_psk_5g], self.wpa_psk_5g[WifiEnums.SSID_KEY],
            None)

        # Reboot and wait for connection back to the same suggestion.
        self.dut.reboot()
        time.sleep(DEFAULT_TIMEOUT)

        wutils.wait_for_connect(self.dut, self.wpa_psk_5g[WifiEnums.SSID_KEY])

        self.dut.log.info("Removing network suggestions");
        asserts.assert_true(
            self.dut.droid.wifiRemoveNetworkSuggestions([self.wpa_psk_5g]),
            "Failed to remove suggestions")
        wutils.wait_for_disconnect(self.dut)
