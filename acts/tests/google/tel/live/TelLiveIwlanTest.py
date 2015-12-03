#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright 2014 - The Android Open Source Project
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

from acts.base_test import BaseTestClass
from acts.test_utils.tel.tel_test_utils import *
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest


class TelLiveIwlanTest(TelephonyBaseTest):

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.tests = ('test_iwlan_setup_delay_wifi_on',
                'test_iwlan_connect_disconnect_wifi_lte_volte',
                'test_iwlan_toggle_wifi_enable_lte_volte',
                'test_iwlan_toggle_cell_mode_wifi_mode_lte_volte'
                )

        self.wifi_network_ssid = self.user_params["wifi_network_ssid"]
        self.wifi_network_pass = self.user_params["wifi_network_pass"]

    # TODO: Set pass/fail criteria
    @TelephonyBaseTest.tel_test_wrap
    def test_iwlan_setup_delay_wifi_on(self):

        """ Measures the time delay in enabling WiFi calling

        Returns:
            True if pass; False if fail.
        """

        ad = self.android_devices[0]

        time_values = {
            'start': 0,
            'wifi_enabled': 0,
            'wifi_connected': 0,
            'wifi_data': 0,
            'iwlan_rat': 0,
            'ims_registered': 0,
            'wfc_enabled': 0,
            'mo_call_success': 0
        }

        WifiUtils.wifi_reset(self.log, ad)
        toggle_airplane_mode(self.log, ad, True)

        set_wfc_mode(self.log, ad, WFC_MODE_WIFI_PREFERRED)

        time_values['start'] = time.time()

        self.log.info("Start Time {}s".format(time_values['start']))

        WifiUtils.wifi_toggle_state(self.log, ad, True)
        time_values['wifi_enabled'] = time.time()
        self.log.info("WiFi Enabled After {}s".format(
            time_values['wifi_enabled'] - time_values['start']))

        WifiUtils.wifi_connect(
            self.log, ad, self.wifi_network_ssid, self.wifi_network_pass)

        # FIXME: bug/25296245
        ad.droid.wakeUpNow()

        if not wait_for_wifi_data_connection(
                self.log, ad, True, WAIT_TIME_WIFI_CONNECTION):
            self.log.error("Failed wifi connection, aborting!")
            return False
        time_values['wifi_connected'] = time.time()

        self.log.info("Wifi Connected After {}s".format(
            time_values['wifi_connected'] - time_values['wifi_enabled']))

        if not verify_http_connection(
                self.log, ad, 'http://www.google.com', 100, .1):
            self.log.error("Failed to get user-plane traffic, aborting!")
            return False

        time_values['wifi_data'] = time.time()
        self.log.info("WifiData After {}s".format(
            time_values['wifi_data'] - time_values['wifi_connected']))

        if not wait_for_droid_in_network_rat(
                self.log, ad, RAT_IWLAN, WAIT_TIME_NW_SELECTION,
                NETWORK_SERVICE_DATA):
            self.log.error("Failed to set-up iwlan, aborting!")
            if is_droid_in_network_rat(self.log, ad, RAT_IWLAN,
                                       NETWORK_SERVICE_DATA):
                self.log.error("Never received the event, but droid in iwlan")
            else:
                return False
        time_values['iwlan_rat'] = time.time()
        self.log.info("iWLAN Reported After {}s".format(
            time_values['iwlan_rat'] - time_values['wifi_data']))

        if not wait_for_ims_registered(
                self.log, ad, WAIT_TIME_IMS_REGISTRATION):
            self.log.error("Never received IMS registered, aborting")
            return False
        time_values['ims_registered'] = time.time()
        self.log.info("Ims Registered After {}s".format(
            time_values['ims_registered'] - time_values['iwlan_rat']))

        if not wait_for_wfc_enabled(self.log, ad, WAIT_TIME_WFC_ENABLED):
            self.log.error("Never received WFC feature, aborting")
            return False

        time_values['wfc_enabled'] = time.time()
        self.log.info("Wifi Calling Feature Enabled After {}s".format(
            time_values['wfc_enabled'] - time_values['ims_registered']))

        set_wfc_mode(self.log, ad, WFC_MODE_DISABLED)

        wait_for_droid_not_in_network_rat(
            self.log, ad, RAT_IWLAN, WAIT_TIME_NW_SELECTION,
            NETWORK_SERVICE_DATA)

        # TODO: Format the output nicely in the log
        self.log.info(time_values)
        return True

    @TelephonyBaseTest.tel_test_wrap
    def test_iwlan_connect_disconnect_wifi_lte_volte(self):
        """ Test IWLAN<->Cell switching when repeatedly connecting to
            and disconnecting from a wifi network.

        Returns:
            True if pass; False if fail.
        """
        return self._test_iwlan_in_out_lte_volte(
            self._iwlan_in_connect_wifi, self._iwlan_out_disconnect_wifi)

    @TelephonyBaseTest.tel_test_wrap
    def test_iwlan_toggle_wifi_enable_lte_volte(self):
        """ Test IWLAN<->Cell switching when repeatedly enabling and disabling
        wifi.

        Returns:
            True if pass; False if fail.
        """
        return self._test_iwlan_in_out_lte_volte(
            self._iwlan_in_enable_wifi, self._iwlan_out_disable_wifi)

    @TelephonyBaseTest.tel_test_wrap
    def test_iwlan_toggle_cell_mode_wifi_mode_lte_volte(self):
        """ Test IWLAN<->Cell switching when toggling between "wifi preferred"
        and "cellular only"/"wifi calling disabled" modes of wifi calling.

        Returns:
            True if pass; False if fail.
        """

        ad = self.android_devices[0]

        self.log.info("Setup Device in LTE with VoLTE Enabled, Wifi Disabled")

        if not ensure_network_rat(
                self.log, ad, RAT_LTE, WAIT_TIME_NW_SELECTION,
                NETWORK_SERVICE_DATA):
            self.log.error("Device failed to select {}".format("lte"))
            return False

        set_wfc_mode(self.log, ad, WFC_MODE_DISABLED)

        toggle_volte(self.log, ad, True)
        if not wait_for_volte_enabled(self.log, ad, WAIT_TIME_VOLTE_ENABLED):
            self.log.error("Device failed to acquire VoLTE service")
            return False

        WifiUtils.wifi_toggle_state(self.log, ad, True)
        WifiUtils.wifi_connect(
            self.log, ad, self.wifi_network_ssid, self.wifi_network_pass)

        # FIXME: bug/25296245
        ad.droid.wakeUpNow()

        if not wait_for_wifi_data_connection(
                self.log, ad, True,
                WAIT_TIME_WIFI_CONNECTION + WAIT_TIME_USER_PLANE_DATA):
            self.log.error("Data did not come up on wifi")
            return False

        if not verify_http_connection(
                self.log, ad):
            self.log.error("No data over WiFi!")
            return False

        # FIXME this number should be a parameter
        for i in range(1, 6):

            self.log.info("Step {}-1: Set WiFi Preferred".format(i))

            set_wfc_mode(self.log, ad, WFC_MODE_WIFI_PREFERRED)

            self.log.info("Step {}-2: Wait for IWLAN Tunnel".format(i))
            self.log.info("WiFi RSSI: {}".format(
                ad.droid.wifiGetConnectionInfo()['rssi']))

            # This isn't a real network selection
            # it's iwlan tunnel establishment, which should take <<30s
            if not wait_for_droid_in_network_rat(
                    self.log, ad, RAT_IWLAN, WAIT_TIME_NW_SELECTION,
                    NETWORK_SERVICE_DATA):
                self.log.error("Failed to set-up iwlan!")
                return False

            self.log.info("Step {}-3: Wait for IMS Registration".format(i))

            if not wait_for_ims_registered(
                    self.log, ad, WAIT_TIME_IMS_REGISTRATION):
                self.log.error("Never received IMS registered!")
                return False

            self.log.info("Step {}-4: Wait for WFC Feature Enabled".format(i))

            # Once IMS is registered on IWLAN,
            # this should be almost instantaneous.
            # leaving 2 seconds to be generous
            if not wait_for_wfc_enabled(self.log, ad, WAIT_TIME_WFC_ENABLED):
                self.log.error("Never received WFC Feature!")
                return False

            self.log.info(
                "Step {}-5: Set WFC to Cellular Only mode".format(i))

            set_wfc_mode(self.log, ad, WFC_MODE_DISABLED)

            if not wait_for_droid_in_network_rat(
                    self.log, ad, RAT_LTE, WAIT_TIME_NW_SELECTION,
                    NETWORK_SERVICE_DATA):
                self.log.error("Device never returned to LTE!")
                return False

            self.log.info("Step {}-7: Wait for VoLTE Feature Enabled".format(i))

            if not wait_for_volte_enabled(
                    self.log, ad, WAIT_TIME_VOLTE_ENABLED):
                self.log.error("Device failed to acquire VoLTE service")
                return False
        return True

    ####################################################################
    # Begin Internal Helper Functions
    ####################################################################


    def _iwlan_in_enable_wifi(self):
        ad = self.android_devices[0]
        WifiUtils.wifi_toggle_state(self.log, ad, True)
        WifiUtils.wifi_connect(
            self.log, ad, self.wifi_network_ssid, self.wifi_network_pass)

    def _iwlan_out_disable_wifi(self):
        ad = self.android_devices[0]
        WifiUtils.wifi_toggle_state(self.log, ad, False)

    def _iwlan_in_connect_wifi(self):
        self._iwlan_in_enable_wifi()

    def _iwlan_out_disconnect_wifi(self):
        ad = self.android_devices[0]
        WifiUtils.wifi_reset(self.log, ad, False)

    def _test_iwlan_in_out_lte_volte(self, iwlan_in_func, iwlan_out_func):

        ad = self.android_devices[0]

        self.log.info("Setup Device in LTE with VoLTE Enabled, Wifi Disabled")

        if not ensure_network_rat(
                self.log, ad, RAT_LTE, WAIT_TIME_NW_SELECTION,
                NETWORK_SERVICE_DATA):
            self.log.error("Device failed to select {}".format("lte"))
            return False

        toggle_volte(self.log, ad, True)

        if not wait_for_volte_enabled(self.log, ad, WAIT_TIME_VOLTE_ENABLED):
            self.log.error("Device failed to acquire VoLTE service")
            return False

        set_wfc_mode(self.log, ad, "WIFI_PREFERRED")

        # FIXME this number should be a parameter
        for i in range(1, 6):

            self.log.info("Step {}-1: Connect to WiFi".format(i))

            iwlan_in_func()

            # FIXME: bug/25296245
            ad.droid.wakeUpNow()

            if not wait_for_wifi_data_connection(
                    self.log, ad, True,
                    WAIT_TIME_WIFI_CONNECTION + WAIT_TIME_USER_PLANE_DATA):
                self.log.error("Data did not come up on wifi")

            self.log.info("Step {}-2: Wait for Wifi Data Connection".format(i))

            if not verify_http_connection(
                    self.log, ad):
                self.log.error("No data over WiFi!")
                return False

            self.log.info("Step {}-3: Wait for IWLAN Tunnel".format(i))
            self.log.info("WiFi RSSI: {}".format(
                self.android_devices[0].droid.wifiGetConnectionInfo()['rssi']))

            # This isn't a real network selection
            # it's iwlan tunnel establishment, which should take <<30s
            if not wait_for_droid_in_network_rat(
                    self.log, ad, RAT_IWLAN, WAIT_TIME_NW_SELECTION,
                    NETWORK_SERVICE_DATA):
                self.log.error("Failed to set-up iwlan!")
                return False

            self.log.info("Step {}-4: Wait for IMS Registration".format(i))

            if not wait_for_ims_registered(
                    self.log, ad, WAIT_TIME_IMS_REGISTRATION):
                self.log.error("Never received IMS registered!")
                return False

            self.log.info("Step {}-5: Wait for WFC Feature Enabled".format(i))


            # Once IMS is registered on IWLAN,
            # this should be almost instantaneous.
            # leaving 2 seconds to be generous
            if not wait_for_wfc_enabled(self.log, ad, WAIT_TIME_WFC_ENABLED):
                self.log.error("Never received WFC Feature!")
                return False

            self.log.info(
                "Step {}-6: Disable Wifi, wait for LTE Data".format(i))

            iwlan_out_func()

            if not wait_for_droid_in_network_rat(
                    self.log, ad, RAT_LTE, WAIT_TIME_NW_SELECTION,
                    NETWORK_SERVICE_DATA):
                self.log.error("Failed to return to LTE!")
                return False

            self.log.info("Step {}-7: Wait for VoLTE Feature Enabled".format(i))

            if not wait_for_volte_enabled(
                    self.log, ad, WAIT_TIME_VOLTE_ENABLED):
                self.log.error("Device failed to acquire VoLTE service")
                return False
        return True

if __name__ == "__main__":
    raise Exception("Cannot run this class directly")

