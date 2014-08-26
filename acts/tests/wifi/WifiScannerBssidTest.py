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

EVENT_TAG = "WifiScannerBssid"

class WifiScannerBssidError(Exception):
  pass

class WifiScannerBssidTest(BaseTestClass):
  TAG = "WifiScannerBssidTest"
  log_path = ''.join((BaseTestClass.log_path, TAG, "/"))
  tests = None
  current_path = os.path.dirname(os.path.abspath(__file__))

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    # A list of all test cases to be executed in this class.
    self.tests = (
        )

  def setup_class(self):
    BaseTestClass.setup_class(self)
    if hasattr(self, "access_points"):
      self.config = load_config(self.current_path
                                + "/WifiScannerTests.config")
      # Initialize APs with config file.
      for item in self.config["AP"]:
        self.log.info("Setting up AP " + str(item["index"]))
        self.access_points[item["index"]].apply_configs(item)
    return True

  """ Helper Functions Begin """
  def start_wifi_track_bssid(self, info):
    idx = self.droid.wifiScannerStartTrackingBssids([json.dumps(info)], -50)
    event = self.ed.pop_event(''.join((EVENT_TAG, str(idx), "onSuccess")),
                                SHORT_TIMEOUT)
    self.log.debug("Got onSuccess:\n" + str(event))
    return idx
  """ Helper Functions End """

  """ Tests Begin """
  def test_wifi_track_bssid(self):
    scan_setting = {
      "band": WIFI_BAND_24_GHZ,
      "periodInMs": 5000,
      "reportEvents": REPORT_EVENT_AFTER_EACH_SCAN,
      'numBssidsPerScan': 16
    }
    bssid_info = {
      "bssid": "e4:f4:c6:f6:80:5b".upper(),
      "high": -20,
      "low": -40,
      "frequencyHint": 2412
    }
    scan_idx = start_wifi_background_scan(self.droid, self.ed, scan_setting)
    idx = self.start_wifi_track_bssid(bssid_info)
    event = self.ed.pop_event(''.join((EVENT_TAG, str(idx), "onFound")), 120)
    self.log.debug(event)
    self.droid.wifiScannerStopTrackingBssids(idx)
    self.droid.wifiScannerStopScan(scan_idx)
    return True
  """ Tests End """

if __name__ == "__main__":
  tester = WifiScannerBssidTest()
  tester.run()

