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


class RttDisableTest(RttBaseTest):
  """Test class for RTT ranging enable/disable flows."""

  def __init__(self, controllers):
    RttBaseTest.__init__(self, controllers)

  def run_disable_rtt(self, disable_wifi):
    """Validate the RTT disabled flows: whether by disabling Wi-Fi or entering
    doze mode.

    Args:
      disable_wifi: True to disable Wi-Fi, False to enable doze.
    """
    dut = self.android_devices[0]

    # validate start-up conditions
    asserts.assert_true(dut.droid.wifiIsRttAvailable(), "RTT is not available")

    # scan to get some APs to be used later
    all_aps = rutils.scan_networks(dut)
    asserts.assert_true(len(all_aps) > 0, "Need at least one visible AP!")

    # disable RTT and validate broadcast & API
    if disable_wifi:
      wutils.wifi_toggle_state(dut, False)
    else:
      dut.adb.shell("cmd deviceidle force-idle")
    rutils.wait_for_event(dut, rconsts.BROADCAST_WIFI_RTT_NOT_AVAILABLE)
    asserts.assert_false(dut.droid.wifiIsRttAvailable(), "RTT is available")

    # request a range and validate error
    id = dut.droid.wifiRttStartRangingToAccessPoints(all_aps[0:1])
    event = rutils.wait_for_event(dut, rutils.decorate_event(
        rconsts.EVENT_CB_RANGING_ON_FAIL, id))
    asserts.assert_equal(event["data"][rconsts.EVENT_CB_RANGING_KEY_STATUS],
                         rconsts.RANGING_FAIL_CODE_RTT_NOT_AVAILABLE,
                         "Invalid error code")

    # enable RTT and validate broadcast & API
    if disable_wifi:
      wutils.wifi_toggle_state(dut, True)
    else:
      dut.adb.shell("cmd deviceidle unforce")
    rutils.wait_for_event(dut, rconsts.BROADCAST_WIFI_RTT_AVAILABLE)
    asserts.assert_true(dut.droid.wifiIsRttAvailable(), "RTT is not available")

  ############################################################################

  def test_disable_wifi(self):
    """Validate that getting expected broadcast when Wi-Fi is disabled and that
    any range requests are rejected."""
    self.run_disable_rtt(True)

  def test_enable_doze(self):
    """Validate that getting expected broadcast when RTT is disabled due to doze
    mode and that any range requests are rejected."""
    self.run_disable_rtt(False)