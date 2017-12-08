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
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class RangeApTest(AwareBaseTest, RttBaseTest):
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
    AwareBaseTest.__init__(self, controllers)
    RttBaseTest.__init__(self, controllers)

  def setup_test(self):
    """Manual setup here due to multiple inheritance: explicitly execute the
    setup method from both parents."""
    AwareBaseTest.setup_test(self)
    RttBaseTest.setup_test(self)

  def teardown_test(self):
    """Manual teardown here due to multiple inheritance: explicitly execute the
    teardown method from both parents."""
    AwareBaseTest.teardown_test(self)
    RttBaseTest.teardown_test(self)

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

  def run_rtt_supporting_ap_only(self, with_responder):
    """Scan for APs and perform RTT only to those which support 802.11mc

    Args:
      with_responder: True to run a Responder on the device.
    """
    dut = self.android_devices[0]
    max_peers = dut.droid.wifiRttMaxPeersInRequest()
    rtt_supporting_aps = rutils.scan_for_rtt_supporting_networks(dut, repeat=10)
    dut.log.info("RTT Supporting APs=%s", rtt_supporting_aps)

    asserts.assert_true(
        len(rtt_supporting_aps) > 0,
        "Need at least one AP which supports 802.11mc!")
    if len(rtt_supporting_aps) > max_peers:
      rtt_supporting_aps = rtt_supporting_aps[0:max_peers]

    if with_responder:
      id = dut.droid.wifiAwareAttach(False)
      autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)
      p_config = autils.add_ranging_to_pub(
          autils.create_discovery_config("GoogleResponderXYZXYZ",
                                         aconsts.PUBLISH_TYPE_UNSOLICITED),
          enable_ranging=True)
      dut.droid.wifiAwarePublish(id, p_config)
      autils.wait_for_event(dut, aconsts.SESSION_CB_ON_PUBLISH_STARTED)

    events = self.run_ranging(dut, aps=rtt_supporting_aps,
                              iter_count=self.NUM_ITER,
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

  def test_rtt_supporting_ap_only(self):
    """Scan for APs and perform RTT only to those which support 802.11mc"""
    self.run_rtt_supporting_ap_only(with_responder=False)

  def test_rtt_supporting_ap_only_with_responder(self):
    """Scan for APs and perform RTT only to those which support 802.11mc.
    Enable a Responder on the device."""
    self.run_rtt_supporting_ap_only(with_responder=True)

  def test_rtt_all_aps(self):
    """Scan for APs and perform RTT on the first 10 visible APs"""
    dut = self.android_devices[0]
    max_peers = dut.droid.wifiRttMaxPeersInRequest()
    all_aps = rutils.scan_networks(dut)
    if len(all_aps) > max_peers:
      all_aps = all_aps[0:max_peers]
    dut.log.info("Visible APs=%s", all_aps)

    events = self.run_ranging(dut, aps=all_aps,
        iter_count=self.NUM_ITER,
        time_between_iterations=self.TIME_BETWEEN_ITERATIONS)
    self.verify_results(events)


