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
This test script that acts as a sandbox for testing various bugs. Testcases here
may eventually be made into actual testscases later.
"""

import pprint
import concurrent
import time

from queue import Empty
from base_test import BaseTestClass
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import *


class BugsTest(BaseTestClass):
  TAG = "BugsTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_scan_advertise_50",
      "test_swarm_scan",
      "test_three_advertisers_and_three_scanners",
      "test_dual_scans",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    time.sleep(self.default_timeout)
    self.ed1.start()

  # Handler Functions Begin
  def blescan_verify_onfailure_event_handler(self, event):
    self.log.debug("Verifying onFailure event")
    self.log.debug(pprint.pformat(event))
    return event

  def blescan_verify_onscanresult_event_handler(self, event,
                                                expected_callbacktype=None,
                                                system_time_nanos=None):
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    callbacktype = event['data']['CallbackType']
    if callbacktype != expected_callbacktype:
      self.log.debug(" ".join(["Expected callback type:",str(expected_callbacktype),
                               ", Found callback type: " + str(callbacktype)]))
      test_result = False
    return test_result

  # Handler Functions End

  def test_scan_advertise_50(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    n = 0
    while n < 50:
      test_result = advertise_droid.startBleAdvertising(advertise_callback, advertise_data,
                                              advertise_settings)
      if not test_result:
        self.log.debug("Advertising failed.")
        return test_result
      self.log.debug("Step 4: Start Bluetooth Le Scan on callback ID: " + str(
        scan_callback))
      test_result = scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
      self.log.debug(
        "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))
      scan_droid.stopBleScan(scan_callback)
      advertise_droid.stopBleAdvertising(advertise_callback)
      advertise_droid.bluetoothToggleState(False)
      advertise_droid.bluetoothToggleState(True)
      time.sleep(12)
      n += 1
    return test_result


  def test_swarm_scan(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    n = 0
    while n < 10000:
      test_result = advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      test_result = scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
      self.log.debug(
        "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))
      scan_droid.stopBleScan(scan_callback)
      n += 1
      advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_dual_scans(self):
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    scan_droid2, scan_event_dispatcher2 = self.droid1, self.ed1
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    filter_list2, scan_settings2, scan_callback2 = generate_ble_scan_objects(
      scan_droid2)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    expected_event_name2 = "BleScan" + str(scan_callback2) + "onScanResults"
    n = 0
    while n < 1000000:
      test_result = scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
      test_result = scan_droid2.startBleScan(filter_list2,scan_settings2,scan_callback2)
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))
      worker2 = scan_event_dispatcher2.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name2, ([1]), self.default_timeout)
      try:
        self.log.debug(worker2.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))
      scan_droid.stopBleScan(scan_callback)
      scan_droid2.stopBleScan(scan_callback2)
      n += 1
    return test_result

  def test_three_advertisers_and_three_scanners(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    filter_list1, scan_settings1, scan_callback1 = generate_ble_scan_objects(
      scan_droid)
    filter_list2, scan_settings2, scan_callback2 = generate_ble_scan_objects(
      scan_droid)

    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = (
      generate_ble_advertise_objects(advertise_droid))
    advertise_data1, advertise_settings1, advertise_callback1 = (
      generate_ble_advertise_objects(advertise_droid))
    advertise_data2, advertise_settings2, advertise_callback2 = (
      generate_ble_advertise_objects(advertise_droid))
    test_result = advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    test_result = advertise_droid.startBleAdvertising(advertise_callback1, advertise_data1,
                                                      advertise_settings1)
    test_result = advertise_droid.startBleAdvertising(advertise_callback2, advertise_data2,
                                                      advertise_settings2)

    test_result = scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    test_result = scan_droid.startBleScan(filter_list1,scan_settings1,scan_callback1)
    test_result = scan_droid.startBleScan(filter_list2,scan_settings2,scan_callback2)
    time.sleep(30)
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1]), self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with Empty error: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with TimeoutError: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    scan_droid.stopBleScan(scan_callback1)
    scan_droid.stopBleScan(scan_callback2)
    advertise_droid.stopBleAdvertising(advertise_callback)
    advertise_droid.stopBleAdvertising(advertise_callback1)
    advertise_droid.stopBleAdvertising(advertise_callback2)

    return test_result