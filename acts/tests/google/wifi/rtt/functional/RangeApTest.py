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
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class RangeApTest(RttBaseTest):
  """Test class for RTT ranging to Access Points"""

  # Number of RTT iterations
  NUM_ITER = 10

  # Maximum failure rate (%) for APs supporting IEEE 802.11mc
  MAX_FAILURE_RATE_80211MC_SUPPORTING_APS = 10

  # Maximum failure rate (%) for APs which do not support IEEE 802.11mc (and
  # hence executing one-sided RTT)
  MAX_FAILURE_RATE_ONE_SIDED_RTT_APS = 50

  # Allowed absolute margin of distance measurements (in mm)
  DISTANCE_MARGIN_MM = 1000

  # Maximum ratio (%) of tests which are allowed to exceed the margin
  MAX_MARGIN_EXCEEDED_RATE_80211MC_SUPPORTING_APS = 10

  # Minimum expected RSSI
  MIN_EXPECTED_RSSI = -100

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
    return self.analyze_results(events)

  def analyze_results(self, all_aps_events):
    """Verifies the results of the RTT experiment.

    Args:
      all_aps_events: Dictionary of APs, each a list of RTT result events.
    """
    all_stats = {}
    for bssid, events in all_aps_events.items():
      stats = rutils.extract_stats(events, self.rtt_reference_distance_mm,
                                   self.DISTANCE_MARGIN_MM,
                                   self.MIN_EXPECTED_RSSI,
                                   self.lci_reference,
                                   self.lcr_reference)
      all_stats[bssid] = stats
    self.log.info("Stats: %s", all_stats)
    return all_stats

  #############################################################################

  def test_rtt_80211mc_supporting_aps(self):
    """Scan for APs and perform RTT only to those which support 802.11mc"""
    dut = self.android_devices[0]
    rtt_supporting_aps = rutils.scan_with_rtt_support_constraint(dut, True,
                                                                 repeat=10)
    dut.log.debug("RTT Supporting APs=%s", rtt_supporting_aps)
    stats = self.run_ranging_and_analyze(dut, rtt_supporting_aps)

    for bssid, stat in stats.items():
      asserts.assert_true(stat['num_no_results'] == 0,
                          "Missing (timed-out) results", extras=stats)
      asserts.assert_false(stat['any_lci_mismatch'],
                           "LCI mismatch, extras=stats")
      asserts.assert_false(stat['any_lcr_mismatch'],
                           "LCR mismatch, extras=stats")
      asserts.assert_true(stat['num_failures'] <=
              self.MAX_FAILURE_RATE_80211MC_SUPPORTING_APS
                          * self.NUM_ITER / 100,
              "Failure rate is too high", extras=stats)
      asserts.assert_true(stat['num_range_out_of_margin'] <=
              self.MAX_MARGIN_EXCEEDED_RATE_80211MC_SUPPORTING_APS
                          * self.NUM_ITER / 100,
              "Results exceeding error margin rate is too high", extras=stats)
    asserts.explicit_pass("RTT test done", extras=stats)

  def test_rtt_non_80211mc_supporting_aps(self):
    """Scan for APs and perform RTT on non-IEEE 802.11mc supporting APs"""
    dut = self.android_devices[0]
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", non_rtt_aps)
    stats = self.run_ranging_and_analyze(dut, non_rtt_aps)

    for bssid, stat in stats.items():
      asserts.assert_true(stat['num_no_results'] == 0,
                          "Missing (timed-out) results", extras=stats)
      asserts.assert_false(stat['any_lci_mismatch'],
                           "LCI mismatch, extras=stats")
      asserts.assert_false(stat['any_lcr_mismatch'],
                           "LCR mismatch, extras=stats")
      asserts.assert_true(stat['num_failures'] <=
                          self.MAX_FAILURE_RATE_ONE_SIDED_RTT_APS
                          * self.NUM_ITER / 100,
                          "Failure rate is too high", extras=stats)
    asserts.explicit_pass("RTT test done", extras=stats)

  def test_rtt_non_80211mc_supporting_aps_wo_privilege(self):
    """Scan for APs and perform RTT on non-IEEE 802.11mc supporting APs with the
    device not having privilege access (expect failures)."""
    dut = self.android_devices[0]
    rutils.config_privilege_override(dut, True)
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", non_rtt_aps)
    stats = self.run_ranging_and_analyze(dut, non_rtt_aps)

    for bssid, stat in stats.items():
      asserts.assert_true(stat['num_no_results'] == 0,
                          "Missing (timed-out) results", extras=stats)
      asserts.assert_false(stat['any_lci_mismatch'],
                           "LCI mismatch, extras=stats")
      asserts.assert_false(stat['any_lcr_mismatch'],
                           "LCR mismatch, extras=stats")
      asserts.assert_true(stat['num_failures'] == self.NUM_ITER,
        "All one-sided RTT requests must fail when executed without privilege",
                          extras=stats)
      for code in stat['status_codes']:
        asserts.assert_true(code ==
        rconsts.EVENT_CB_RANGING_STATUS_RESPONDER_DOES_NOT_SUPPORT_IEEE80211MC,
                            "Expected non-support error code", extras=stats)
    asserts.explicit_pass("RTT test done", extras=stats)

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
    stats = self.run_ranging_and_analyze(dut, mix_list)

    for bssid, stat in stats.items():
      asserts.assert_true(stat['num_no_results'] == 0,
                          "Missing (timed-out) results", extras=stats)
      asserts.assert_false(stat['any_lci_mismatch'],
                           "LCI mismatch, extras=stats")
      asserts.assert_false(stat['any_lcr_mismatch'],
                           "LCR mismatch, extras=stats")
      if bssid == rtt_aps[0][wutils.WifiEnums.BSSID_KEY]:
        asserts.assert_true(stat['num_failures'] <=
                            self.MAX_FAILURE_RATE_80211MC_SUPPORTING_APS
                            * self.NUM_ITER / 100,
                            "Failure rate is too high", extras=stats)
        asserts.assert_true(stat['num_range_out_of_margin'] <=
                            self.MAX_MARGIN_EXCEEDED_RATE_80211MC_SUPPORTING_APS
                            * self.NUM_ITER / 100,
                            "Results exceeding error margin rate is too high",
                            extras=stats)
      else:
        asserts.assert_true(stat['num_failures'] == self.NUM_ITER,
        "All one-sided RTT requests must fail when executed without privilege",
                            extras=stats)
        for code in stat['status_codes']:
          asserts.assert_true(code ==
            rconsts.EVENT_CB_RANGING_STATUS_RESPONDER_DOES_NOT_SUPPORT_IEEE80211MC,
                              "Expected non-support error code", extras=stats)
    asserts.explicit_pass("RTT test done", extras=stats)

  def test_rtt_non_80211mc_supporting_ap_faked_as_supporting(self):
    """Scan for APs which do not support IEEE 802.11mc, maliciously modify the
    Responder config to indicate support and pass-through to service. Verify
    that get an error result.
    """
    dut = self.android_devices[0]
    non_rtt_aps = rutils.scan_with_rtt_support_constraint(dut, False)
    non_rtt_aps = non_rtt_aps[0:1] # pick first
    non_rtt_aps[0][rconsts.SCAN_RESULT_KEY_RTT_RESPONDER] = True # falsify
    dut.log.debug("Visible non-IEEE 802.11mc APs=%s", non_rtt_aps)
    stats = self.run_ranging_and_analyze(dut, non_rtt_aps)

    for bssid, stat in stats.items():
      asserts.assert_true(stat['num_no_results'] == 0,
                          "Missing (timed-out) results", extras=stats)
      asserts.assert_false(stat['any_lci_mismatch'],
                           "LCI mismatch, extras=stats")
      asserts.assert_false(stat['any_lcr_mismatch'],
                           "LCR mismatch, extras=stats")
      asserts.assert_true(stat['num_failures'] == self.NUM_ITER,
                          "Failures expected for falsified responder config",
                          extras=stats)
    asserts.explicit_pass("RTT test done", extras=stats)

  #########################################################################
  #
  # LEGACY API test code
  #
  #########################################################################

  def test_legacy_rtt_80211mc_supporting_aps(self):
    """Scan for APs and perform RTT only to those which support 802.11mc - using
    the LEGACY API!"""
    dut = self.android_devices[0]
    rtt_supporting_aps = rutils.scan_with_rtt_support_constraint(dut, True,
                                                                 repeat=10)
    dut.log.debug("RTT Supporting APs=%s", rtt_supporting_aps)

    rtt_configs = []
    for ap in rtt_supporting_aps:
      rtt_configs.append(self.rtt_config_from_scan_result(ap))
    dut.log.debug("RTT configs=%s", rtt_configs)

    results = []
    num_missing = 0
    for i in range(self.NUM_ITER):
        idx = dut.droid.wifiRttStartRanging(rtt_configs)
        event = None
        try:
          events = dut.ed.pop_events("WifiRttRanging%d" % idx, 30)
          dut.log.debug("Event=%s", events)
          for event in events:
            results.append(event["data"][rconsts.EVENT_CB_RANGING_KEY_RESULTS])
        except queue.Empty:
          self.log.debug("Waiting for RTT event timed out.")
          results.append([])
          num_missing = num_missing + 1

    # basic error checking:
    # 1. no missing
    # 2. overall (all BSSIDs) success rate > threshold
    asserts.assert_equal(num_missing, 0,
                         "Missing results (timeout waiting for event)",
                         extras=results)

    num_results = 0
    num_errors = 0
    for result_group in results:
      num_results = num_results + len(result_group)
      for result in result_group:
        if result["status"] != 0:
          num_errors = num_errors + 1

    asserts.assert_true(
      num_errors <= self.MAX_FAILURE_RATE_80211MC_SUPPORTING_APS
        * num_results / 100,
      "Failure rate is too high", extras=results)
    asserts.explicit_pass("RTT test done", extras=results)

  def rtt_config_from_scan_result(self, scan_result):
    """Creates an Rtt configuration based on the scan result of a network.
    """
    WifiEnums = wutils.WifiEnums
    ScanResult = WifiEnums.ScanResult
    RttParam = WifiEnums.RttParam
    RttBW = WifiEnums.RttBW
    RttPreamble = WifiEnums.RttPreamble
    RttType = WifiEnums.RttType

    scan_result_channel_width_to_rtt = {
      ScanResult.CHANNEL_WIDTH_20MHZ: RttBW.BW_20_SUPPORT,
      ScanResult.CHANNEL_WIDTH_40MHZ: RttBW.BW_40_SUPPORT,
      ScanResult.CHANNEL_WIDTH_80MHZ: RttBW.BW_80_SUPPORT,
      ScanResult.CHANNEL_WIDTH_160MHZ: RttBW.BW_160_SUPPORT,
      ScanResult.CHANNEL_WIDTH_80MHZ_PLUS_MHZ: RttBW.BW_160_SUPPORT
    }
    p = {}
    freq = scan_result[RttParam.frequency]
    p[RttParam.frequency] = freq
    p[RttParam.BSSID] = scan_result[WifiEnums.BSSID_KEY]
    if freq > 5000:
      p[RttParam.preamble] = RttPreamble.PREAMBLE_VHT
    else:
      p[RttParam.preamble] = RttPreamble.PREAMBLE_HT
    cf0 = scan_result[RttParam.center_freq0]
    if cf0 > 0:
      p[RttParam.center_freq0] = cf0
    cf1 = scan_result[RttParam.center_freq1]
    if cf1 > 0:
      p[RttParam.center_freq1] = cf1
    cw = scan_result["channelWidth"]
    p[RttParam.channel_width] = cw
    p[RttParam.bandwidth] = scan_result_channel_width_to_rtt[cw]
    if scan_result["is80211McRTTResponder"]:
      p[RttParam.request_type] = RttType.TYPE_TWO_SIDED
    else:
      p[RttParam.request_type] = RttType.TYPE_ONE_SIDED
    return p
