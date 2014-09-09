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
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import *


class BleStressTest(BaseTestClass):
  TAG = "BleStressTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
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

  def bleadvertise_verify_onsuccess_handler(self, event):
    test_result = True
    self.log.debug("Verifying onSuccess event")
    self.log.debug(pprint.pformat(event))
    return test_result

  def test_loop_scanning_100(self):
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    test_result = True
    for x in range(100):
      filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
        scan_droid)
      scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
      scan_droid.stopBleScan(scan_callback)
    return test_result

  def test_loop_advertising_100(self):
    advertise_droid, advertise_event_dispatcher = self.droid, self.ed
    test_result = True
    for x in range(100):
      advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
        advertise_droid)
      advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
      worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler, expected_advertise_event_name, ([]),
        self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
        test_result = False
      except concurrent.futures._base.TimeoutError as error:
        self.log.debug(" ".join(["Test failed, filtering callback onSuccess never occurred:",
                               str(error)]))
        test_result = False
      advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result
