#!/usr/bin/env python3.4
#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
"""
This test exercises basic scanning functionality to confirm expected behavior
related to wlan scanning
"""

from datetime import datetime

import pprint
import time

import acts.base_test
import acts.test_utils.wifi.wifi_test_utils as wutils

from acts import signals
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

class WlanScanTest(WifiBaseTest):
    """wlan scan test class.

    Test Bed Requirement:
    * One Fuchsia device
    * Several Wi-Fi networks visible to the device, including an open Wi-Fi
      network.
    """
    def __init__(self, controllers):
      WifiBaseTest.__init__(self, controllers)

    def setup_class(self):
      self.dut = self.fuchsia_devices[0]

    """Tests"""
    def test_basic_scan_request(self):
      """Verify a general scan trigger returns at least one result"""
      start_time = datetime.now()

      scan_result_response = self.dut.wlan_lib.wlanStartScan()
      scan_results = scan_result_response["result"]
      if scan_results is None:
          self.log.info("scan command did not return results")
          raise signals.TestFailure("Scan failed - no results returned")
      self.log.info("scan contained %d results", len(scan_results))

      total_time_ms = (datetime.now() - start_time).total_seconds() * 1000
      self.log.info("scan time: %d ms", total_time_ms)

      if len(scan_results) > 0:
          raise signals.TestPass(details="", extras={"Scan time":"%d" %total_time_ms})
      else:
          raise signals.TestFailure("Scan failed or did not find any networks")

