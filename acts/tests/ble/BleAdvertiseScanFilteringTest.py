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


class BleAdvertiseScanFilteringTest(BaseTestClass):
  TAG = "BleAdvertiseScanFilteringTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_scan_default_advertisement",
      "test_scan_advertisement_with_device_name_filter",
      "test_scan_flush_pending_scan_results",
      "test_scan_trigger_on_batch_scan_results",
      "test_scan_flush_results_without_on_batch_scan_results_triggered",
      "test_scan_non_existant_name_filter",
      "test_scan_advertisement_with_device_service_uuid_filter",
      "test_scan_advertisement_with_device_service_uuid_filter_expect_no_events",
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
      self.log.debug(
        "Expected callback type: " + str(expected_callbacktype)
        + ", Found callback type: " + str(callbacktype))
      test_result = False
    return test_result

  def blescan_verify_onbatchscanresult_event_handler(self, event,
                                                     system_time_nanos=None,
                                                     report_delay_nanos=None):
    test_result = True
    self.log.debug("Verifying onBatchScanResult event")
    self.log.debug(pprint.pformat(event))
    for result in event['data']['Results']:
      timestamp_nanos = result['timestampNanos']
      length_of_time = timestamp_nanos - system_time_nanos
      self.log.debug(
        "Difference in time in between scan start and onBatchScanResult: " + str(
          length_of_time))
      buffer = 1000000000  # 1 second
      if length_of_time > (report_delay_nanos + buffer):
        self.log.debug(
          "Difference was greater than the allowable difference.")
        test_result = False
    return test_result

  # Handler Functions End

  def test_scan_default_advertisement(self):
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
    test_result = startbleadvertise(advertise_droid, advertise_data,
                                    advertise_settings,
                                    advertise_callback)
    if not test_result:
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
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with Empty error: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with TimeoutError: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result


  def test_scan_advertisement_with_device_name_filter(self):
    self.log.debug("Step 1: Setting up environment")

    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    filter_name = advertise_droid.bluetoothGetLocalName()
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    self.log.debug("Step 2: Create name filter on " + filter_name +
                   ", a default scan settings, and a default scan callback.")
    scan_droid.setScanFilterDeviceName(filter_name)
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
      self.log.debug("Advertising failed on device.")
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
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_flush_pending_scan_results(self):
    self.log.debug("Step 1: Setting up environment")

    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = \
      generate_ble_advertise_objects(
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
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed " +
      "event.")
    scan_droid.flushPendingScanResults(scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1, scan_droid]), None,
      self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_trigger_on_batch_scan_results(self):
    self.log.debug("Step 1: Setting up environment")

    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    scan_droid.setScanSettings(1, 5000, 0, 0)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(
      scan_callback) + "onBatchScanResult"
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
    system_time_nanos = scan_droid.getSystemElapsedRealtimeNanos()
    self.log.debug("Current system time: " + str(system_time_nanos))
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onbatchscanresult_event_handler,
      expected_event_name, ([system_time_nanos, 5000000000]),
      self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_flush_results_without_on_batch_scan_results_triggered(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(
      scan_callback) + "onBatchScanResults"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    test_result = startbleadvertise(advertise_droid, advertise_data,
                                    advertise_settings,
                                    advertise_callback)
    if test_result is False:
      self.log.debug("Advertising failed")
      return test_result
    self.log.debug("Step 4: Start Bluetooth Le Scan on callback ID: " + str(
      scan_callback))
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback)
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onbatchscanresult_event_handler,
      expected_event_name, ([]), self.default_timeout)
    scan_droid.flushPendingScanResults(scan_callback)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   10)
      self.log.debug("Unexpectedly found an advertiser: " + event_info)
      test_result = False
    except Empty as error:
      self.log.debug(
        "No onBatchScanResult events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_non_existant_name_filter(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    filter_name = advertise_droid.bluetoothGetLocalName() + "_probably_wont_find"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    self.log.debug("Step 2: Create name filter on " + filter_name +
                   ", a default scan settings, and a default scan callback.")
    scan_droid.setScanFilterDeviceName(filter_name)
    self.log.debug(
      "Step 3: Create scan filter, scan settings, and scan callback")
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
      self.log.debug("Advertising failed on device.")
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

  def test_scan_advertisement_with_device_service_uuid_filter(self):
    self.log.debug("Step 1: Setting up environment")

    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    service_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    service_mask = "00000000-0000-1000-8000-00805F9B34FA"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    self.log.debug("Step 2: Create service uuid filter on " + service_uuid +
                   ", service mask filter on " + service_mask +
                   ", a default scan settings, and a default scan callback.")
    scan_droid.setScanFilterServiceUuid(service_uuid, service_mask)
    self.log.debug(
      "Step 3: Create scan filter, scan settings, and scan callback")
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_droid.setAdvertiseDataSetServiceUuids([service_uuid])
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
      self.log.debug("Advertising failed")
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
      self.log.debug(worker.result(5))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug(error.__class__)
      self.log.debug(
        "Test failed with: concurrent.futures._base.TimeoutError")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_advertisement_with_device_service_uuid_filter_expect_no_events(
    self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    service_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    service_mask = "00000000-0000-1000-8000-00805F9B34FA"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    self.log.debug("Step 2: Create service uuid filter on " + service_uuid +
                   ", service mask filter on " + service_mask +
                   ", a default scan settings, and a default scan callback.")
    scan_droid.setScanFilterServiceUuid(service_uuid, service_mask)
    self.log.debug(
      "Step 3: Create scan filter, scan settings, and scan callback")
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
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
      return

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
                                                   self.default_timeout)
      self.log.debug("Unexpectedly found an advertiser: " + event_info)
      test_result = False
    except Empty as error:
      self.log.debug("No events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result