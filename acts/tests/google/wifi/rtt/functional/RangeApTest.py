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
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class RangeApTest(RttBaseTest):
  """Test class for RTT ranging to Access Points"""

  # max number of APs to range concurrently
  MAX_APS = 10

  def __init__(self, controllers):
    RttBaseTest.__init__(self, controllers)

  def test_rtt_supporting_ap_only(self):
    """Scan for APs and perform RTT only to those which support 802.11mc"""
    dut = self.android_devices[0]
    rtt_supporting_aps = rutils.scan_for_rtt_supporting_networks(dut, repeat=2)
    dut.log.info("RTT Supporting APs=%s", rtt_supporting_aps)

    asserts.assert_true(
        len(rtt_supporting_aps) > 0,
        "Need at least one AP which supports 802.11mc!")

    id = dut.droid.wifiRttStartRangingToAp(rtt_supporting_aps)
    event = rutils.wait_for_event(dut,
                                  rutils.decorate_event(
                                      rconsts.EVENT_CB_RANGING_ON_RESULT, id))
    dut.log.info("Ranging results=%s", event)
    rutils.validate_ap_results(
        rtt_supporting_aps, event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS])

  def test_rtt_all_aps(self):
    """Scan for APs and perform RTT on the first 10 visible APs"""
    dut = self.android_devices[0]
    all_aps = rutils.scan_networks(dut)
    if len(all_aps) > self.MAX_APS:
      all_aps = all_aps[0:self.MAX_APS]
    dut.log.info("Visible APs=%s", all_aps)

    id = dut.droid.wifiRttStartRangingToAp(all_aps)
    event = rutils.wait_for_event(dut,
                                  rutils.decorate_event(
                                      rconsts.EVENT_CB_RANGING_ON_RESULT, id))
    dut.log.info("Ranging results=%s", event)
    rutils.validate_ap_results(
        all_aps, event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS])
