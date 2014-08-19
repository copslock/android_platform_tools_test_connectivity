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

from base_test import BaseTestClass
from queue import Empty
from test_utils.BleEnum import *
from test_utils.ble_helper_functions import *


class BleAttenuatorTest(BaseTestClass):
  TAG = "BleAttenuatorTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_scan_default_advertisement_high_attenuation"
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    time.sleep(self.default_timeout)
    self.ed1.start()

  def blescan_verify_onscanresult_event_handler(self, event,
                                                expected_callbacktype=None,
                                                system_time_nanos=None):
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    callbacktype = event['data']['CallbackType']
    if callbacktype != expected_callbacktype:
      self.log.debug(
        "Expected callback type: " + str(expected_callbacktype)
        + ", Found callback type: " + str(callbacktype))
      test_result = False
    return test_result

  def test_scan_default_advertisement_high_attenuation(self):
    self.log.debug("Step 1: Setting up environment")

    self.attn.set_atten(0, 90)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    test_result = startbleadvertise(advertise_droid, advertise_data,
                                    advertise_settings,
                                    advertise_callback)
    if test_result is False:
      self.log.debug("Advertising failed.")
      return test_result

    self.log.debug("Step 4: Start Bluetooth Le Scan on callback ID: " + str(
      scan_callback))
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback)
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1]), self.default_timeout)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   10)
      self.log.debug("Unexpectedly found an advertiser: " + event_info)
      test_result = False
    except Empty as error:
      self.log.debug("No events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result