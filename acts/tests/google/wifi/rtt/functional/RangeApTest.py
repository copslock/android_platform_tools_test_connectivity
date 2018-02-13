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

import queue
import time

from acts import asserts
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class RangeApTest(RttBaseTest):
  """Test class for RTT ranging to Access Points"""

  # Number of RTT iterations
  NUM_ITER = 10

  # Allowed absolute margin of distance measurements (in mm)
  DISTANCE_MARGIN_MM = 1000

  # Maximum expected RSSI
  MAX_EXPECTED_RSSI = 200

  # Time gap (in seconds) between iterations
  TIME_BETWEEN_ITERATIONS = 0

  def __init__(self, controllers):
    RttBaseTest.__init__(self, controllers)

  def run_ranging(self, dut, aps, iter_count, time_between_iterations):
    """Executing ranging to the set of APs.

    Args:
      dut: Device under test
      aps: A list of APs (Access Points) to range to.
      iter_count: Number of measurements to perform.
      time_between_iterations: Number of seconds to wait between iterations.
    Returns: a list of the events containing the RTT results (or None for a
    failed measurement).
    """
    events = {} # need to keep track per BSSID!
    for ap in aps:
      events[ap["BSSID"]] = []

    for i in range(iter_count):
      if i != 0 and time_between_iterations != 0:
        time.sleep(time_between_iterations)

      id = dut.droid.wifiRttStartRangingToAccessPoints(aps)
      try:
        event = dut.ed.pop_event(rutils.decorate_event(
            rconsts.EVENT_CB_RANGING_ON_RESULT, id), rutils.EVENT_TIMEOUT)
        range_results = event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS]
        asserts.assert_equal(
            len(aps),
            len(range_results),
            'Mismatch in length of scan results and range results')
        for result in range_results:
          bssid = result[rconsts.EVENT_CB_RANGING_KEY_MAC_AS_STRING]
          asserts.assert_true(bssid in events,
                              "Result BSSID %s not in requested AP!?" % bssid)
          asserts.assert_equal(len(events[bssid]), i,
                               "Duplicate results for BSSID %s!?" % bssid)
          events[bssid].append(result)
      except queue.Empty:
        for ap in aps:
          events[ap["BSSID"]].append(None)

    return events

  def run_ranging_and_analyze(self, dut, aps):
    """Run ranging on the specified APs and analyze results.

    Args:
      dut: Device under test.
      aps: List of APs.
    """
    max_peers = dut.droid.wifiRttMaxPeersInRequest()

    asserts.assert_true(len(aps) > 0, "Need at least one AP!")
    if len(aps) > max_peers:
      aps = aps[0:max_peers]

    events = self.run_ranging(dut, aps=aps, iter_count=self.NUM_ITER,
                          time_between_iterations=self.TIME_BETWEEN_ITERATIONS)
    self.verify_results(events)

  def verify_results(self, all_aps_events):
    """Verifies the results of the RTT experiment.

    Args:
      all_aps_events: Dictionary of APs, each a list of RTT result events.
    """
    all_stats = {}
    for bssid, events in all_aps_events.items():
      stats = rutils.extract_stats(events, self.rtt_reference_distance_mm,
          self.DISTANCE_MARGIN_MM, self.MAX_EXPECTED_RSSI)
      all_stats[bssid] = stats
    self.log.info("Stats: %s", all_stats)
    asserts.explicit_pass("RTT test done", extras=all_stats)

  #############################################################################

  def test_rtt_80211mc_supporting_aps(self):
    """Scan for APs and perform RTT only to those which support 802.11mc"""
    dut = self.android_devices[0]
    rtt_supporting_aps = rutils.scan_with_rtt_support_constraint(dut, True,
                                                                 repeat=10)
    dut.log.debug("RTT Supporting APs=%s", rtt_supporting_aps)
    self.run_ranging_and_analyze(dut, rtt_supporting_aps)

  def test_rtt_non_80211mc_supporting_aps(self):
    """Scan for APs and perform RTT on non-IEEE 802.11mc supporting APs"""
    dut = self.android_devices[0]
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", non_rtt_aps)
    self.run_ranging_and_analyze(dut, non_rtt_aps)

  def test_rtt_non_80211mc_supporting_aps_wo_privilege(self):
    """Scan for APs and perform RTT on non-IEEE 802.11mc supporting APs with the
    device not having privilege access (expect failures)."""
    dut = self.android_devices[0]
    rutils.config_privilege_override(dut, True)
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", non_rtt_aps)
    self.run_ranging_and_analyze(dut, non_rtt_aps)

  def test_rtt_mixed_80211mc_supporting_aps_wo_privilege(self):
    """Scan for APs and perform RTT on one supporting and one non-supporting
    IEEE 802.11mc APs with the device not having privilege access (expect
    failures)."""
    dut = self.android_devices[0]
    rutils.config_privilege_override(dut, True)
    rtt_aps = rutils.scan_with_rtt_support_constraint(dut, True)
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    mix_list = [rtt_aps[0], non_rtt_aps[0]]
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", mix_list)
    self.run_ranging_and_analyze(dut, mix_list)


