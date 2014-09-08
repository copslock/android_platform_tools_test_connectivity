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
from event_dispatcher import IllegalStateError
from queue import Empty
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import *


class BleLongevityTest(BaseTestClass):
  TAG = "BleLongevityTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_b17040164",
      # "test_long_advertising_same_callback",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    # self.droid.bluetoothToggleState(False)
    # self.droid.bluetoothToggleState(True)
    # self.droid1.bluetoothToggleState(False)
    # self.droid1.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    # time.sleep(self.default_timeout)
    # self.ed1.start()
    self.droid.eventClearBuffer()
    self.droid1.eventClearBuffer()

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

  def bleadvertise_verify_onsuccess_event_handler(self, event):
    test_result = True
    self.log.debug("Verifying onSuccess event")
    self.log.debug(pprint.pformat(event))
    return test_result

  def test_long_advertising_same_callback(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    looperCount = 100000
    expected_advertise_event = "BleAdvertise" + str(
      advertise_callback) + "onSuccess"
    while looperCount != 0:
      start = time.time()
      self.droid.eventClearBuffer()
      self.ed1.start()
      self.droid1.eventClearBuffer()
      test_result = startbleadvertise(advertise_droid, advertise_data,
                                      advertise_settings,
                                      advertise_callback)

      if not test_result:
        self.log.debug("Advertising failed.")
        return test_result
      self.log.debug(
        "Start Bluetooth Le Scan on callback ID: " + str(scan_callback))

      worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_event_handler,
        expected_advertise_event, (), 20)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))

      startblescan(scan_droid, filter_list, scan_settings, scan_callback)
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]), 20)

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
      try:
        self.ed1.pop_all(expected_advertise_event)
      except IllegalStateError as error:
        self.log.debug("herpa derpa")
      looperCount -= 1
      self.log.debug(
        "total time taken for this loop: " + str(time.time() - start))
      self.ed1.stop()
      time.sleep(2)
      start += 2
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    return test_result

  def test_long_advertising_different_callback(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    looperCount = 100000

    while looperCount != 0:
      start = time.time()
      advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
        advertise_droid)
      test_result = startbleadvertise(advertise_droid, advertise_data,
                                      advertise_settings,
                                      advertise_callback)
      expected_advertise_event = "BleAdvertise" + str(
        advertise_callback) + "onSuccess"

      if not test_result:
        self.log.debug("Advertising failed.")
        return test_result
      self.log.debug(
        "Start Bluetooth Le Scan on callback ID: " + str(scan_callback))
      '''
      worker = advertise_event_dispatcher.handle_event(self.bleadvertise_verify_onsuccess_event_handler,
                                              expected_advertise_event, ())
      try:
          self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
          test_result = False
          self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
          test_result = False
          self.log.debug("Test failed with TimeoutError: " + str(error))
      '''
      startblescan(scan_droid, filter_list, scan_settings, scan_callback)
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]))

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
      looperCount -= 1
      self.log.debug(
        "total time taken for this loop: " + str(time.time() - start))
      time.sleep(2)
      start += 2
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    return test_result

  def test_b17040164(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    looperCount = 1000
    expected_advertise_event = "BleAdvertise" + str(
      advertise_callback) + "onSuccess"
    while looperCount != 0:
      advertise_droid.eventClearBuffer()
      self.ed1.start()
      advertise_droid.bluetoothToggleState(True)
      time.sleep(10)
      advertise_droid.eventClearBuffer()
      test_result = startbleadvertise(advertise_droid, advertise_data,
                                      advertise_settings,
                                      advertise_callback)
      time.sleep(5)
      scan_droid.stopBleScan(scan_callback)
      time.sleep(5)
      advertise_droid.stopBleAdvertising(advertise_callback)
      looperCount -= 1
      self.ed1.stop()
      advertise_droid.bluetoothToggleState(False)
      time.sleep(5)
      self.log.debug("Done with iteration " + str(looperCount))