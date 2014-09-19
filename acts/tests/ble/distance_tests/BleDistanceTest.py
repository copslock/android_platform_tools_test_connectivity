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

"""
This test script exercises distance based testcases.

This test script was designed with this setup in mind:
Shield box one: Android Device
Shield box two: Android Device
An attenuator sitting in between the two shield boxes.
"""

import pprint
import concurrent
import time

from base_test import BaseTestClass
from queue import Empty
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import (verify_bluetooth_on_event,
                                                       generate_ble_scan_objects,
                                                       generate_ble_advertise_objects)


class BleDistanceTest(BaseTestClass):
  TAG = "BleDistanceTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_scan_default_advertisement_high_attenuation",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.ed1.start()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    verify_bluetooth_on_event(self.ed)
    verify_bluetooth_on_event(self.ed1)

  def blescan_verify_onscanresult_event_handler(self, event):
    """
    An event handler that validates the onScanResult event.
    :param event: dict that represents the callback onScanResult
    :return: test_result: bool
    """
    # Todo: Implement proper validation steps.
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    return test_result

  def test_scan_default_advertisement_high_attenuation(self):
    """
    Test that tests a large distance between the advertiser android and the
    scanner android.
    Steps:
    1. Set attenuation to 90 (the highest value for the attenuator).
    2. Setup the scanning android device
    3. Setup the advertiser android devices.
    3. Verify that no onScanResult callbacks were recorded.
    :return: test_result: bool
    """
    test_result = True
    self.attenuators[0].set_atten(0, 90)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    if test_result is False:
      self.log.debug("Advertising failed.")
      return test_result
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([]), self.default_timeout)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   10)
      self.log.debug(" ".join(["Unexpectedly found an advertiser:",pprint.pformat(event_info)]))
      test_result = False
    except Empty as error:
      self.log.debug("No events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    print (test_result)
    return test_result