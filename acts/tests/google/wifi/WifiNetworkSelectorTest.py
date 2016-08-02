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

import time

from acts import asserts
from acts import base_test
from acts.controllers import android_device
from acts.controllers import attenuator
from acts.test_utils.wifi import wifi_test_utils as wutils


class WifiNetworkSelectorTest(base_test.BaseTestClass):
    """These tests verify the behavior of the Android Wi-Fi Network Selector
    feature.
    """

    def setup_class(self):
        self.dut = self.register_controller(android_device)[0]
        self.attenuators = self.register_controller(attenuator)
        wutils.wifi_test_device_init(self.dut)

    def setup_test(self):
        wutils.reset_wifi(self.dut)
        self.dut.ed.clear_all_events()

    def verify_connected_bssid(self, expected_bssid):
        """Verifies the DUT is connected to the correct BSSID.

        Args:
            expected_bssid: Network bssid to which connection.

        Returns:
            True if connection to given network happen, else return False.
        """
        time.sleep(30)
        actual_network = self.dut.droid.wifiGetConnectionInfo()
        self.log.debug("Actual network: %s", actual_network)
        asserts.assert_equal(expected_bssid,
                             actual_network[WifiEnums.BSSID_KEY])

    def add_network(self, ad, networks):
        """Add Wi-Fi networks to an Android device and verify the networks were
        added correctly

        Args:
            ad: the AndroidDevice object to add networks to.
            networks: a list of dicts, each dict represents a Wi-Fi network.
        """
        for network in networks:
            ret = ad.droid.wifiAddNetwork(network)
            asserts.assert_true(ret != 1, "Failed to add network %s" % network)
            configured_networks = ad.droid.wifiGetConfiguredNetworks()
            is_configured = wutils.match_networks(network, configured_networks)
            asserts.assert_true(
                is_configured,
                "Network %s was added but it's not in the configured list.")

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.cat_adb_log(test_name, begin_time)

    def test_network_selector_basic_connection(self):
        """
            1. Add one saved network to DUT.
            2. Move the DUT in range and wake up the DUT.
            3. Verify the DUT is connected to the network.
        """

    def test_network_selector_basic_connection_prefer_5g(self):
        """
            1. Add one saved SSID with 2G and 5G BSSIDs of similar RSSI.
            2. Move the DUT in range and wake up the DUT.
            3. Verify the DUT is connected to the 5G BSSID.
        """

    def test_network_selector_prefer_stronger_rssi(self):
        """
            1. Add two saved SSID to DUT, same band, one has stronger RSSI
               than the other.
            2. Move the DUT in range and wake up the DUT.
            3. Verify the DUT is connected to the SSID with stronger RSSI.
        """

    def test_network_selector_prefer_secure_to_open_network(self):
        """
            1. Add two saved networks to DUT, same band, similar RSSI, one uses
               WPA2 security, the other is open.
            2. Move the DUT in range and wake up the DUT.
            3. Verify the DUT is connected to the network that uses WPA2.
        """

    def test_network_selector_blacklist_by_connection_failure(self):
        """
            1. Add two saved secured networks X and Y to DUT. X has stronger
               RSSI than Y. X has wrong password configured.
            2. Move the DUT in range and wake up the DUT.
            3. Verify the DUT is connected to network Y.
        """

    def test_network_selector_2g_to_5g_prefer_same_SSID(self):
        """
            1. Add SSID_A and SSID_B to DUT. Both SSIDs have both 2G and 5G
               BSSIDs.
            2. Attenuate the networks so that the DUT is connected to SSID_A's
               2G in the beginning.
            3. Increase the RSSI of both SSID_A's 5G and SSID_B's 5G.
            4. Wake up the DUT.
            5. Verify the DUT switches to SSID_A's 5G.
        """

    def test_network_selector_2g_to_5g_different_ssid(self):
        """
            1. Add SSID_A and SSID_B to DUT. Both SSIDs have both 2G and 5G
               BSSIDs.
            2. Attenuate the networks so that the DUT is connected to SSID_A's
               2G in the beginning.
            3. Increase the RSSI of SSID_B's 5G while attenuate down SSID_A's
               2G RSSI.
            4. Wake up the DUT.
            5. Verify the DUT switches to SSID_B's 5G.
        """

    def test_network_selector_5g_to_2g_same_ssid(self):
        """
            1. Add one SSID that has both 2G and 5G to the DUT.
            2. Attenuate down the 2G RSSI.
            3. Connect the DUT to the 5G BSSID.
            4. Bring up the 2G RSSI and attenuate down the 5G RSSI.
            5. Wake up the DUT.
            6. Verify the DUT switches to the 2G BSSID.
        """

    def test_network_selector_stay_on_qualified_network(self):
        """
            1. Add two 5G WPA2 BSSIDs X and Y to the DUT. X has higher RSSI
               than Y.
            2. Connect the DUT to X.
            3. Change attenuation so that Y's RSSI goes above X's.
            4. Wake up the DUT.
            5. Verify the DUT stays on X.
        """

    def test_network_selector_stay_on_user_selected_network(self):
        """
            1. Connect the DUT to SSID_A by adding the network and enabling it.
            2. Connect the DUT to SSID_B via user select code path.
            3. Lower SSID_B's RSSI right above dropoff threshold.
            4. Wake up the DUT.
            5. Verify DUT stays on SSID_B
        """

    # def test_network_selector_2g_to_5g_same_SSID_roaming(self):
    #     """ Implement this in HAL test suite when it's ready.
    #         1. Add one SSID that has both 2G and 5G to the DUT.
    #         2. Attenuate the networks so that the DUT is connected to 2G.
    #         3. Increase the RSSI of 5G and lower the RSSI of 2G.
    #         4. Verify DUT switches to 5G without waking up.
    #     """
