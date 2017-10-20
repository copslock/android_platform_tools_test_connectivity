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
from acts.base_test import BaseTestClass
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class StressRangeApTest(RttBaseTest):
  """Test class for stress testing of RTT ranging to Access Points"""

  NUM_ITERATIONS = 10
  PASS_RATE = 0.9 # 90% of iterations must pass

  def __init__(self, controllers):
    BaseTestClass.__init__(self, controllers)

  #############################################################################

  def run_rtt_supporting_ap_only(self, use_queue):
    """Scan for APs and perform RTT only to those which support 802.11mc.

    Stress test: repeat ranging to the same AP. Verify rate of success and
    stability of results.

    Args:
      use_queue: True to use the request queue (i.e. not wait for results before
      sending the next ranging request), False to wait for results before
      requesting another range.
    """
    dut = self.android_devices[0]
    rtt_supporting_aps = rutils.scan_for_rtt_supporting_networks(dut, repeat=2)
    dut.log.info("RTT Supporting APs=%s", rtt_supporting_aps)

    asserts.assert_true(
        len(rtt_supporting_aps) > 0,
        "Need at least one AP which supports 802.11mc!")
    rtt_supporting_aps = rtt_supporting_aps[0:1] # pick one

    # run all iterations
    results = []
    if use_queue:
      ids = []
      for i in range(self.NUM_ITERATIONS):
        ids.append(dut.droid.wifiRttStartRangingToAccessPoints(rtt_supporting_aps))
      for i in range(self.NUM_ITERATIONS):
        event = rutils.wait_for_event(dut,
                                      rutils.decorate_event(
                                          rconsts.EVENT_CB_RANGING_ON_RESULT,
                                          ids[i]))
        results.append(event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS][0])
    else:
      for i in range(self.NUM_ITERATIONS):
        id = dut.droid.wifiRttStartRangingToAccessPoints(rtt_supporting_aps)
        event = rutils.wait_for_event(dut,
                                      rutils.decorate_event(
                                          rconsts.EVENT_CB_RANGING_ON_RESULT,
                                          id))
        results.append(event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS][0])

    # review results (TODO: copy margin code from WifiRttManagerTest.py)
    num_success = 0
    for result in results:
      if (result[rconsts.EVENT_CB_RANGING_KEY_STATUS] ==
          rconsts.EVENT_CB_RANGING_STATUS_SUCCESS):
        num_success = num_success + 1

    asserts.assert_true(num_success >= self.PASS_RATE * self.NUM_ITERATIONS,
                        "Success rate too low", extras=results)

  def test_rtt_supporting_ap_only_no_queue(self):
    """Scan for APs and perform RTT only to those which support 802.11mc. Tests
    without queueing requests.

    Stress test: repeat ranging to the same AP. Verify rate of success and
    stability of results.
    """
    self.run_rtt_supporting_ap_only(use_queue=False)

  def test_rtt_supporting_ap_only_queue(self):
    """Scan for APs and perform RTT only to those which support 802.11mc. Uses
    range request queue.

    Stress test: repeat ranging to the same AP. Verify rate of success and
    stability of results.
    """
    self.run_rtt_supporting_ap_only(use_queue=True)
