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

import time

import acts.base_test
import acts.signals
import acts.test_utils.wifi.wifi_test_utils as wutils
import acts.utils

from acts import asserts
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest


class WifiHiddenSSIDTest(WifiBaseTest):
    """Tests for APIs in Android's WifiManager class.

    Test Bed Requirement:
    * One Android device
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
            "open_network", "reference_networks"]
        self.unpack_userparams(
            req_param_names=req_params, opt_param_names=opt_param)

        if "AccessPoint" in self.user_params:
            self.legacy_configure_ap_and_start(hidden=True)

        asserts.assert_true(
            len(self.reference_networks) > 0,
            "Need at least one reference network with psk.")
        self.wpa_2g = self.reference_networks[0]["2g"]
        self.wpa_5g = self.reference_networks[0]["5g"]

    def setup_test(self):
        self.dut.droid.wakeLockAcquireBright()
        self.dut.droid.wakeUpNow()

    def teardown_test(self):
        self.dut.droid.wakeLockRelease()
        self.dut.droid.goToSleepNow()

    def on_fail(self, test_name, begin_time):
        #self.dut.take_bug_report(test_name, begin_time)
        #self.dut.cat_adb_log(test_name, begin_time)
        pass

    def teardown_class(self):
        wutils.reset_wifi(self.dut)
        if "AccessPoint" in self.user_params:
            del self.user_params["reference_networks"]
            del self.user_params["open_network"]

    """Helper Functions"""

    def add_hiddenSSID_and_connect(self, hidden_network):
        """Add the hidden network and connect to it.

        Args:
            hidden_network: The hidden network config to connect to.

        """
        ret = self.dut.droid.wifiAddNetwork(hidden_network)
        asserts.assert_true(ret != -1, "Add network %r failed" % hidden_network)
        self.dut.droid.wifiEnableNetwork(ret, 0)
        wutils.connect_to_wifi_network(self.dut, hidden_network)
        if not wutils.validate_connection(self.dut):
            raise signals.TestFailure("Fail to connect to internet on %s" %
                                       hidden_network)

    """Tests"""

    @test_tracker_info(uuid="")
    def test_stress_connect_disconnect_5g(self):
        


