#!/usr/bin/python3.4
#
#   Copyright 2014 - The Android Open Source Project
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
import traceback

from queue import Empty

from acts.base_test import BaseTestClass
from acts.test_utils.wifi_test_utils import match_networks
from acts.test_utils.wifi_test_utils import reset_droid_wifi
from acts.test_utils.wifi_test_utils import start_wifi_connection_scan
from acts.test_utils.wifi_test_utils import wifi_forget_network
from acts.test_utils.wifi_test_utils import wifi_test_device_init
from acts.test_utils.wifi_test_utils import wifi_toggle_state
from acts.test_utils.wifi_test_utils import WifiEnums
from acts.test_utils.wifi_test_utils import WifiEventNames
from acts.utils import find_field
from acts.utils import trim_model_name

class WifiManagerTest(BaseTestClass):

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_toggle_state",
            "test_toggle_with_screen",
            "test_scan",
            "test_add_network",
            "test_forget_network",
            "test_tdls_supported",
            "test_energy_info",
            "test_iot_with_password",
            )

    def setup_class(self):
        self.dut = self.android_devices[0]
        wifi_test_device_init(self.dut)
        req_params = (
            "iot_networks",
            "open_network",
            "iperf_server_address",
            "tdls_models",
            "energy_info_models"
            )
        self.assert_true(self.unpack_userparams(req_params),
            "Failed to unpack user params")
        self.assert_true(len(self.iot_networks) > 0,
            "Need at least one iot network with psk.")
        self.assert_true(wifi_toggle_state(self.droid, self.ed, True),
            "Failed to turn on wifi before tests.")
        self.iot_networks = self.iot_networks + [self.open_network]
        self.iperf_server = self.iperf_servers[0]
        return True

    def setup_test(self):
        self.droid.wakeLockAcquireBright()
        self.droid.wakeUpNow()
        self.iperf_server.start()
        return True

    def teardown_test(self):
        self.droid.wakeLockRelease()
        self.droid.goToSleepNow()
        reset_droid_wifi(self.droid, self.ed)
        self.iperf_server.stop()

    """Helper Functions"""
    def connect_to_wifi_network_with_password(self, params):
        """Connection logic for open and psk wifi networks.

        Logic steps are
        1. Connect to the network.
        2. Run iperf traffic.

        Args:
            params: A tuple of network info and AndroidDevice object.

        Returns:
            True if successful, False otherwise.
        """
        result = False
        wait_time = 5
        network, ad = params
        droid = ad.droid
        ed = ad.ed
        SSID = network[WifiEnums.SSID_KEY]
        try:
            ed.clear_all_events()
            start_wifi_connection_scan(droid, ed)
            droid.wifiStartTrackingStateChange()
            self.assert_true(droid.wifiConnect(network),
                "wifi connect returned false.")
            connect_result = ed.pop_event(WifiEventNames.WIFI_CONNECTED)
            self.log.debug(connect_result)
            result = connect_result['data'][WifiEnums.SSID_KEY] == SSID
            if result:
                self.log.info("Starting iperf traffic through {}".format(SSID))
                time.sleep(wait_time)
                port_arg = "-p {}".format(self.iperf_server.port)
                result, data = ad.run_iperf_client(self.iperf_server_address,
                                                   port_arg)
                self.log.debug(pprint.pformat(data))
        except Empty:
            self.log.error("Failed to connect to {}".format(SSID))
            self.log.debug(traceback.format_exc())
        finally:
            droid.wifiStopTrackingStateChange()
        return result

    def run_iperf(self, iperf_args):
        if "iperf_server_address" not in self.user_params:
            self.log.error(("Missing iperf_server_address. "
                "Provide one in config."))
        else:
            iperf_addr = self.user_params["iperf_server_address"]
            self.log.info("Running iperf client.")
            result, data = self.dut.run_iperf_client(iperf_addr,
                iperf_args)
            self.log.debug(data)

    def run_iperf_rx_tx(self, time, omit=10):
        args = "-p {} -t {} -O 10".format(self.iperf_server.port, time, omit)
        self.log.info("Running iperf client {}".format(args))
        self.run_iperf(args)
        args = "-p {} -t {} -O 10 -R".format(self.iperf_server.port, time, omit)
        self.log.info("Running iperf client {}".format(args))
        self.run_iperf(args)

    """Tests"""
    def test_toggle_state(self):
        """Test toggling wifi"""
        self.log.debug("Going from on to off.")
        assert wifi_toggle_state(self.droid, self.ed, False)
        self.log.debug("Going from off to on.")
        assert wifi_toggle_state(self.droid, self.ed, True)
        return True

    def test_toggle_with_screen(self):
        """Test toggling wifi with screen on/off"""
        wait_time = 5
        self.log.debug("Screen from off to on.")
        self.droid.wakeLockAcquireBright()
        self.droid.wakeUpNow()
        time.sleep(wait_time)
        self.log.debug("Going from on to off.")
        try:
            assert wifi_toggle_state(self.droid, self.ed, False)
            time.sleep(wait_time)
            self.log.debug("Going from off to on.")
            assert wifi_toggle_state(self.droid, self.ed, True)
        finally:
            self.droid.wakeLockRelease()
            time.sleep(wait_time)
            self.droid.goToSleepNow()
        return True

    def test_scan(self):
        """Test wifi connection scan can start and find expected networks."""
        wifi_toggle_state(self.droid, self.ed, True)
        self.log.debug("Start regular wifi scan.")
        start_wifi_connection_scan(self.droid, self.ed)
        wifi_results = self.droid.wifiGetScanResults()
        self.log.debug("Scan results: %s" % wifi_results)
        condition = {WifiEnums.SSID_KEY: self.open_network[WifiEnums.SSID_KEY]}
        assert match_networks(condition, wifi_results)
        return True

    def test_add_network(self):
        """Test wifi connection scan."""
        ssid = self.open_network[WifiEnums.SSID_KEY]
        nId = self.droid.wifiAddNetwork(self.open_network)
        self.assert_true(nId > -1, "Failed to add network.")
        configured_networks = self.droid.wifiGetConfiguredNetworks()
        self.log.debug(("Configured networks after adding: %s" %
                        configured_networks))
        condition = {WifiEnums.SSID_KEY: ssid}
        assert match_networks(condition, configured_networks)
        return True

    def test_forget_network(self):
        self.assert_true(self.test_add_network(), "Failed to add network.")
        ssid = self.open_network[WifiEnums.SSID_KEY]
        wifi_forget_network(self.dut, ssid)
        configured_networks = self.droid.wifiGetConfiguredNetworks()
        for nw in configured_networks:
            self.assert_true(nw[WifiEnums.BSSID_KEY] != ssid,
                "Found forgotten network %s in configured networks." % ssid)
        return True

    def test_iot_with_password(self):
        params = list(itertools.product(self.iot_networks, self.android_devices))
        name_gen = lambda p : "test_connection_to-%s" % p[0][WifiEnums.SSID_KEY]
        failed = self.run_generated_testcases(
            self.connect_to_wifi_network_with_password,
            params,
            name_func=name_gen)
        self.assert_true(not failed, "Failed ones: {}".format(failed))
        return True

    def test_tdls_supported(self):
        model = trim_model_name(self.dut.model)
        self.log.debug("Model is %s" % model)
        if model in self.tdls_models:
            assert self.droid.wifiIsTdlsSupported()
        else:
            assert not self.droid.wifiIsTdlsSupported()
        return True

    # TODO(angli): Actually connect to a network and do an http request between
    # iterations.
    def test_energy_info(self):
        """Verify the WiFi energy info reporting feature.

        Steps:
            1. Check that the WiFi energy info reporting support on this device
               is as expected (support or not).
            2. If the device does not support energy info reporting as
               expected, skip the test.
            3. Call API to get WiFi energy info.
            4. Verify the values of "ControllerEnergyUsed" and
               "ControllerIdleTimeMillis" in energy info don't decrease.
            5. Repeat from Step 3 for 10 times.
        """
        # Check if dut supports energy info reporting.
        actual_support = self.dut.droid.wifiIsEnhancedPowerReportingSupported()
        model = self.dut.model
        expected_support = model in self.energy_info_models
        msg = "Expect energy info support to be %s on %s, got %s." % (
              expected_support, model, actual_support)
        self.assert_true(actual_support == expected_support, msg)
        if not actual_support:
            self.skip(("Device %s does not support energy info reporting as "
                       "expected.") % model)
        # Verify reported values don't decrease.
        self.log.info(("Device %s supports energy info reporting, verify that "
                       "the reported values don't decrease.") % model)
        energy = 0
        idle_time = 0
        for i in range(10):
            info = self.droid.wifiGetControllerActivityEnergyInfo()
            self.log.debug("Iteration %d, got energy info: %s" % (i, info))
            new_energy = info["ControllerEnergyUsed"]
            new_idle_time = info["ControllerIdleTimeMillis"]
            self.assert_true(new_energy >= energy,
                "Energy value decreased: previous %d, now %d" % (energy,
                    new_energy))
            energy = new_energy
            self.assert_true(new_idle_time >= idle_time,
                "Idle time decreased: previous %d, now %d" % (idle_time,
                    new_idle_time))
            idle_time = new_idle_time
            start_wifi_connection_scan(self.droid, self.ed)
        return True

if __name__ == "__main__":
    pass
