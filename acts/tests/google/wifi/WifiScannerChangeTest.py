#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

import json
import os
from queue import Empty

from acts.controllers.ap.access_point import AP
from acts.base_test import BaseTestClass
from acts.utils import load_config
from acts.test_utils.wifi.wifi_test_utils import start_wifi_tracking_change
from acts.test_utils.wifi.wifi_test_utils import WifiEnums
from acts.test_utils.wifi.wifi_test_utils import wifi_toggle_state

SCANCHANNEL = [2412,2437,2457,2462,5180,5200,5220,5745]
SCANTIME = 5000
SHORT_TIMEOUT = 30
EVENT_TAG = "WifiScannerChange"

class WifiScannerScanError(Exception):
  pass

class WifiScannerChangeTest(BaseTestClass):
  tests = None
  current_path = os.path.dirname(os.path.abspath(__file__))

  def __init__(self, controllers):
    BaseTestClass.__init__(self, controllers)
    # A list of all test cases to be executed in this class.
    self.tests = (
        "test_wifi_track_change_turn_off_two",
        "test_wifi_start_track_change_with_wifi_off"
        )

  def setup_class(self):
    if hasattr(self, "access_points"):
      self.config = load_config(self.current_path
                                + "/WifiScannerTests.config")
      # Initialize APs with config file.
      for item in self.config["AP"]:
        self.log.info("Setting up AP " + str(item["index"]))
        self.access_points[item["index"]].apply_configs(item)
      return True

  """ Helper Functions Begin """
  def start_wifi_track_change_expect_failure(self):
    try:
      idx = self.droid.wifiScannerStartTrackingChange()
      event = self.ed.pop_event(''.join((EVENT_TAG, str(idx), "onFailure")),
                                SHORT_TIMEOUT)
    except Empty:
      events = self.ed.pop_events(EVENT_TAG, SHORT_TIMEOUT)
      self.log.error("Did not get expected onFailure. Got\n" + str(events))
      return False
    self.log.debug("Got expected onFailure:\n" + str(event))
    return True

  def verify_one_changing_results(self, expected, actual):
    for k,v in expected.items():
      if k not in actual:
        self.log.error(' '.join(("Missing", k, "in", actual)))
        return False
      if actual[k] != v:
        self.log.error(' '.join(("Missmatch: expected", v, "got", actual[k])))
        return False
    return True

  def verify_onChanging_results(self, expected, actuals):
    # Create a result lookup table by bssid.
    actual_results = {}
    for a in actuals:
      actual_results[a["bssid"]] = a
    status = True
    for exp in expected:
      if exp["bssid"] not in actual_results:
        self.log.error("Missing " + str(exp))
        continue
      a_result = actual_results[exp["bssid"]]
      if not self.verify_one_changing_results(exp, a_result):
        status = False
    return status
  """ Helper Functions End """

  """ Tests Begin """
  def test_wifi_track_change_turn_off_two(self):
    # Get bssid infos.
    ap = self.access_points[0]
    bssids0 = ap.get_active_bssids_info("radio0", "frequency", "ssid")
    bssids1 = ap.get_active_bssids_info("radio1", "frequency", "ssid")
    bssids = bssids0 + bssids1
    idx = start_wifi_tracking_change(self.droid, self.ed)
    self.log.debug("Wait for onQuiescence.")
    event = self.ed.pop_event(EVENT_TAG + str(idx) + "onQuiescence", 120)
    self.log.debug("Tuning off " + str(bssids))
    ap.toggle_radio_state("radio0", False)
    ap.toggle_radio_state("radio1", False)
    self.log.debug("Waiting for onChanging.")
    event = self.ed.pop_event(''.join((EVENT_TAG, str(idx), "onChanging")), 60)
    self.log.debug("Got:\n" + str(event))
    self.droid.wifiScannerStopTrackingChange(idx)
    return self.verify_onChanging_results(bssids, event["data"]["Results"])

  def test_wifi_start_track_change_with_wifi_off(self):
    self.log.debug("Make sure wifi is off.")
    wifi_toggle_state(self.droid, self.ed, False)
    status = self.start_wifi_track_change_expect_failure()
    self.log.debug("Turning wifi back on.")
    wifi_toggle_state(self.droid, self.ed, True)
    return status
  """ Tests End """

if __name__ == "__main__":
  tester = WifiScannerChangeTest()
  tester.run()

