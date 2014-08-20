#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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

import threading, time, os, itertools, json, traceback
from queue import Empty
from base_test import BaseTestClass
from ap.access_point import AP
from test_utils.wifi_test_utils import *
from test_utils.utils import *

SCANCHANNEL = [2412,2437,2457,2462,5180,5200,5220,5745]
SCANTIME = 5000


SHORT_TIMEOUT = 10
EVENT_TAG = "WifiScannerScan"

class WifiScannerScanError(Exception):
  pass

class WifiScannerScanTest(BaseTestClass):
  TAG = "WifiScannerScanTest"
  log_path = BaseTestClass.log_path + TAG + "/"
  tests = None
  current_path = os.path.dirname(os.path.abspath(__file__))

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    if hasattr(self, "access_points"):
      self.config = load_config(self.current_path
                                + "/WifiScannerScanTest.config")
      # Initialize APs with config file.
      for item in self.config["AP"]:
        self.access_points[item["index"]].apply_configs(item)
    # A list of all test cases to be executed in this class.
    self.tests = (
        self.test_wifi_scanner_scan_with_enumerated_params,
        self.test_wifi_scanner_with_wifi_off,
        )

  """ Helper Functions Begin """
  def start_wifi_background_scan(self, scan_setting):
    idx = self.droid.startWifiScannerScan(scan_setting)
    event = self.ed.pop_event(EVENT_TAG + str(idx) + "onSuccess",
                              SHORT_TIMEOUT)
    return idx

  def wifi_generate_scanner_scan_settings(self):
    """Generates all the combinations of different scan setting parameters.
    """
    # Setting parameters
    base_scan_setting = {"periodInMs": SCANTIME}
    report_types = (REPORT_EVENT_AFTER_BUFFER_FULL,
                    REPORT_EVENT_AFTER_EACH_SCAN,
                    REPORT_EVENT_FULL_SCAN_RESULT)
    scan_types = (("band", WIFI_BAND_BOTH_WITH_DFS),
                  ("channels", SCANCHANNEL))
    num_of_bssid = (10, 17)
    # Generate all the combinations of report types and scan types
    setting_combinations = list(itertools.product(report_types,
                                                  scan_types,
                                                  num_of_bssid))
    # Create scan setting strings based on the combinations
    scan_settings = []
    for combo in setting_combinations:
      s = dict(base_scan_setting)
      s["reportEvents"] = combo[0]
      s[combo[1][0]] = combo[1][1]
      s["numBssidsPerScan"] = combo[2]
      scan_settings.append(json.dumps(s))
    return scan_settings

  def scan_rule(self, scan_setting):
    if "band" in scan_setting:
      band_to_frequencies[scan_setting["band"]]

  def wifi_generate_expected_scan_results(self, scan_setting):
    expected = []
    for ap in self.access_points:
      expected += ap.get_active_ssids_info("frequency")
    return expected

  def verify_one_scan_result(self, expected, result):
    for k, v in expected.items():
      if k not in result or v != result[k]:
        self.log.error("Mismatching " + k + ", expected " + v + ", got "
                       + str(result[k]))
        return False
    return True

  def verify_scan_results(self, expected, scan_results):
    # TODO(angli): Add support for bssid oriented check. Right now we don't
    # support duplicated ssid in results
    results = {}
    status = True
    # Create a look up dict so we can easily look up result by ssid.
    for r in scan_results:
      results[r["ssid"]] = r
    for exp in expected:
      ssid = exp["ssid"]
      if ssid not in results:
        status = False
        self.log.error("Missing\n" + str(exp))
      else:
        s = self.verify_one_scan_result(exp, results[ssid])
        if not s:
          status = False
          self.log.error("Mismatch occurred, expected\n" + str(exp) + "\nGot\n"
                         + str(results[ssid]))
    return status

  def wifi_execute_one_scan_test(self, scan_setting):
    try:
      idx = self.start_wifi_background_scan(scan_setting)
    except Empty:
      self.log.error("Did not get onSuccess, got:\n" + str(events))
      return False
    event = self.ed.pop_event(EVENT_TAG + str(idx) + "onResults")
    self.log.debug(event)
    self.droid.stopWifiScannerScan(idx)
    self.ed.clear_all_events()
    return True
  """ Helper Functions End """

  """ Tests Begin """
  def test_wifi_scanner_scan_with_enumerated_params(self):
    scan_settings = self.wifi_generate_scanner_scan_settings()
    self.log.debug("Scan settings:\n" + str(scan_settings))
    failed = self.run_generated_testcases("Wifi Background Scan Test",
                                          self.wifi_execute_one_scan_test,
                                          scan_settings)
    self.log.debug("Settings that caused failure: " + str(failed))
    if len(failed) == 0:
      return True
    return False

  def test_wifi_scanner_with_wifi_off(self):
    self.log.debug("Make sure wifi is off.")
    wifi_toggle_state(self.droid, self.ed, False)
    scan_setting = {
      "band": WIFI_BAND_BOTH_WITH_DFS,
      "periodInMs": SCANTIME,
      "reportEvents": REPORT_EVENT_AFTER_EACH_SCAN
    }
    try:
      idx = self.droid.startWifiScannerScan(json.dumps(scan_setting))
      event = self.ed.pop_event(EVENT_TAG + str(idx) + "onFailure",
                                SHORT_TIMEOUT)
    except Empty:
      self.log.error("Wifi is off, but did not get onFailure.")
      events = self.ed.pop_events(EVENT_TAG, 10)
      self.log.error("Got\n" + events)
      self.log.debug("Turning wifi back on.")
      wifi_toggle_state(self.droid, self.ed, True)
      return False
    self.log.debug("Got onFailure, which is expected.\n"
                   + str(event) + "\nTurning wifi back on.")
    wifi_toggle_state(self.droid, self.ed, True)
    return True
  """ Tests End """

if __name__ == "__main__":
  tester = WifiScannerScanTest()
  tester.run()

