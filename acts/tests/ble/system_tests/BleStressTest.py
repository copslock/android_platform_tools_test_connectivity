# python3.4
# Copyright (C) 2014 The Android Open Source Project
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

import pprint
import concurrent
import time

from queue import Empty
from base_test import BaseTestClass
from test_utils.BleEnum import *
from test_utils.ble_helper_functions import *


class BleStressTest(BaseTestClass):
  TAG = "BleStressTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_loop_scanning_100",
      "test_loop_advertising_100",
    )
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    time.sleep(self.default_timeout)

  def test_loop_scanning_100(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    test_result = True
    for x in range(100):
      filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
        scan_droid)
      self.log.debug(
        "Step 4: Start Bluetooth Le Scan on callback ID: " + str(
          scan_callback))
      test_result = startblescan(scan_droid, filter_list, scan_settings,
                                 scan_callback)
      scan_droid.flushPendingScanResults(scan_callback)
      scan_droid.stopBleScan(scan_callback)
      if not test_result:
        self.log.debug(
          "Callback " + str(scan_callback) + " failed to start scan.")
    return test_result

  def test_loop_advertising_100(self):
    self.log.debug("Step 1: Setting up environment")
    advertise_droid, advertise_event_dispatcher = self.droid, self.ed
    for x in range(100):
      advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
        advertise_droid)
      test_result = startbleadvertise(advertise_droid, advertise_data,
                                      advertise_settings,
                                      advertise_callback)
      advertise_droid.stopBleAdvertising(advertise_callback)
      if not test_result:
        self.log.debug(
          "Starting ble advertiser on callback " + str(
            advertise_callback) + " failed.")
    return test_result
