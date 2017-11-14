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

import time

from acts import asserts
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class RequestManagementTest(RttBaseTest):
  """Test class for RTT request management flows."""

  def __init__(self, controllers):
    RttBaseTest.__init__(self, controllers)

  #############################################################################

  def test_cancel_ranging(self):
    """Request a 'large' number of range operations with various UIDs (using the
    work-source API), then cancel some of them.

    We can't guarantee a reaction time - it is possible that a cancelled test
    was already finished and it's results dispatched back. The test therefore
    stacks the request queue. The sequence is:

    - Request:
      - 50 tests @ UIDs = {uid1, uid2, uid3}
      - 2 tests @ UIDs = {uid2, uid3}
      - 1 test2 @ UIDs = {uid1, uid2, uid3}
    - Cancel UIDs = {uid2, uid3}

    Expect to receive only 51 results.
    """
    dut = self.android_devices[0]
    max_peers = dut.droid.wifiRttMaxPeersInRequest()

    all_uids = [10, 20, 30]
    some_uids = [20, 30]

    aps = rutils.scan_for_rtt_supporting_networks(dut, repeat=10)
    dut.log.info("RTT Supporting APs=%s", aps)

    asserts.assert_true(
        len(aps) > 0,
        "Need at least one AP which supports 802.11mc!")
    if len(aps) > max_peers:
      aps = aps[0:max_peers]

    group1_ids = []
    group2_ids = []
    group3_ids = []

    # step 1: request 50 ranging operations on [uid1, uid2, uid3]
    for i in range(50):
      group1_ids.append(
        dut.droid.wifiRttStartRangingToAccessPoints(aps, all_uids))

    # step 2: request 2 ranging operations on [uid2, uid3]
    for i in range(2):
      group2_ids.append(
        dut.droid.wifiRttStartRangingToAccessPoints(aps, some_uids))

    # step 3: request 1 ranging operation on [uid1, uid2, uid3]
    for i in range(1):
      group3_ids.append(
          dut.droid.wifiRttStartRangingToAccessPoints(aps, all_uids))

    # step 4: cancel ranging requests on [uid2, uid3]
    dut.droid.wifiRttCancelRanging(some_uids)

    # collect results
    for i in range(len(group1_ids)):
      rutils.wait_for_event(dut, rutils.decorate_event(
        rconsts.EVENT_CB_RANGING_ON_RESULT, group1_ids[i]))
    time.sleep(rutils.EVENT_TIMEOUT) # optimize time-outs below to single one
    for i in range(len(group2_ids)):
      rutils.fail_on_event(dut, rutils.decorate_event(
          rconsts.EVENT_CB_RANGING_ON_RESULT, group2_ids[i]), 0)
    for i in range(len(group3_ids)):
      rutils.wait_for_event(dut, rutils.decorate_event(
          rconsts.EVENT_CB_RANGING_ON_RESULT, group3_ids[i]))
