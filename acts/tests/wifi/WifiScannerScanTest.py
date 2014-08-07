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

import threading, time, os
from base_test import BaseTestClass
from ap.access_point import AP
from test_utils.wifi_test_utils import *
from test_utils.utils import *

SCANCHANNEL = [2412,2437,2457,2462,5180,5200,5220,5745]
SCANTIME = 5000

WIFI_BAND_UNSPECIFIED = 0;      # not specified
WIFI_BAND_24_GHZ = 1;           # 2.4 GHz band
WIFI_BAND_5_GHZ = 2;            # 5 GHz band without DFS channels
WIFI_BAND_5_GHZ_DFS_ONLY  = 4;  # 5 GHz band with DFS channels
WIFI_BAND_5_GHZ_WITH_DFS  = 6;  # 5 GHz band with DFS channels
WIFI_BAND_BOTH = 3;             # both bands without DFS channels
WIFI_BAND_BOTH_WITH_DFS = 7;    # both bands with DFS channels

REPORT_EVENT_AFTER_BUFFER_FULL = 0
REPORT_EVENT_AFTER_EACH_SCAN = 1
REPORT_EVENT_FULL_SCAN_RESULT = 2
SHORT_TIMEOUT = 10
EVENT_TAG = "WifiScanner"

class WifiScannerScanTest(BaseTestClass):
  TAG = "WifiScannerScanTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  current_path = os.path.dirname(os.path.abspath(__file__))

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.config = load_config(self.current_path + "/WifiScannerScanTest.config")
    # Initialize APs with config file.
    for item in self.config["AP"]:
      self.access_points[item["index"]].apply_configs(item)
    self.tests = (
        self.test_wifi_scanner_each_scan_report,
        self.test_wifi_scanner_each_scan_report_fail)

  """ Helper Functions Begin """
  def start_wifi_background_scan_with_band(self, band, wait_time, reportevent):
    idx = self.droid.startWifiScannerScanBand(band, wait_time, reportevent)
    event = self.ed.pop_events(EVENT_TAG, SHORT_TIMEOUT)[0]
    self.log.debug(idx, event)
    return idx, event  
  """ Helper Functions End """

  """ Tests Begin """
  # Threadhold types for reporting full report: buffer full, after each scan.
  # Need to test each of them
  def test_wifi_scanner_each_scan_report(self):
    wifi_toggle_state(self.droid, self.ed, True)
    idx, event = self.start_wifi_background_scan_with_band(
                                              WIFI_BAND_BOTH_WITH_DFS,
                                              SCANTIME,
                                              REPORT_EVENT_AFTER_EACH_SCAN)
    if event['data']['Type'] == "onSuccess":
      self.log.debug("Got onSuccess, scan started, waiting on results.")
      event = self.ed.pop_event("WifiScannerScan" + str(idx))
      self.log.debug(event)
      self.droid.stopWifiScannerScan(idx)
      return True
    self.log.error("Did not get onSuccess, got:\n" + str(event))
    return False

  def test_wifi_scanner_each_scan_report_fail(self):
    verdict = False
    self.log.debug("Make sure wifi is off.")
    wifi_toggle_state(self.droid, self.ed, False)
    idx, event = self.start_wifi_background_scan_with_band(
                                              WIFI_BAND_BOTH_WITH_DFS,
                                              SCANTIME,
                                              REPORT_EVENT_AFTER_EACH_SCAN)
    if event['data']['Type'] == "onFailure":
      self.log.debug("Got onFailure, as expected.")
      verdict = True
    else:
      self.log.error("Expected onFailure, but got" + str(event))
      self.droid.stopWifiScannerScan(idx)
    self.log.debug("Turning wifi back on.")
    wifi_toggle_state(self.droid, self.ed, True)
    return verdict

    """ Tests End """

if __name__ == "__main__":
  tester = WifiScannerScanTest()
  tester.run()

