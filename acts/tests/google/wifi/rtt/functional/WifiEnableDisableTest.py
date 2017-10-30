#!/usr/bin/python3.4
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

from acts import asserts
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class WifiEnableDisableTest(RttBaseTest):
  """Test class for RTT ranging interaction with Wi-Fi being disabled and
  enabled."""

  def __init__(self, controllers):
    RttBaseTest.__init__(self, controllers)

  def test_disable_flow(self):
    """Validate that getting expected broadcast when Wi-Fi is disabled and that
    any range requests are rejected."""
    dut = self.android_devices[0]

    # validate start-up conditions
    asserts.assert_true(dut.droid.wifiIsRttAvailable(), "RTT is not available")

    # scan to get some APs to be used later
    all_aps = rutils.scan_networks(dut)
    asserts.assert_true(len(all_aps) > 0, "Need at least one visible AP!")

    # disable Wi-Fi and validate broadcast & API
    wutils.wifi_toggle_state(dut, False)
    rutils.wait_for_event(dut, rconsts.BROADCAST_WIFI_RTT_NOT_AVAILABLE)
    asserts.assert_false(dut.droid.wifiIsRttAvailable(), "RTT is available")

    # request a range and validate error
    id = dut.droid.wifiRttStartRangingToAccessPoints(all_aps[0:1])
    event = rutils.wait_for_event(dut, rutils.decorate_event(
        rconsts.EVENT_CB_RANGING_ON_FAIL, id))
    asserts.assert_equal(event["data"][rconsts.EVENT_CB_RANGING_KEY_STATUS],
                         rconsts.RANGING_FAIL_CODE_RTT_NOT_AVAILABLE,
                         "Invalid error code")

    # enable Wi-Fi and validate broadcast & API
    wutils.wifi_toggle_state(dut, True)
    rutils.wait_for_event(dut, rconsts.BROADCAST_WIFI_RTT_AVAILABLE)
    asserts.assert_true(dut.droid.wifiIsRttAvailable(), "RTT is not available")
