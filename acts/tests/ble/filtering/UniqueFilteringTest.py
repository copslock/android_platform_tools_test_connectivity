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
This test script exercises different filters and outcomes not exercised in FiltersTest.

This test script was designed with this setup in mind:
Shield box one: Android Device
Shield box two: Android Device
Antenna between the two shield boxes.
"""

import pprint
import concurrent
import time

from queue import Empty
from base_test import BaseTestClass
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import (verify_bluetooth_on_event,
                                                       generate_ble_scan_objects,
                                                       generate_ble_advertise_objects)


class UniqueFilteringTest(BaseTestClass):
  TAG = "UniqueFilteringTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_scan_flush_pending_scan_results",
      "test_scan_trigger_on_batch_scan_results",
      "test_scan_flush_results_without_on_batch_scan_results_triggered",
      "test_scan_non_existent_name_filter",
      "test_scan_advertisement_with_device_service_uuid_filter_expect_no_events",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.ed1.start()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    verify_bluetooth_on_event(self.ed)
    verify_bluetooth_on_event(self.ed1)

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
                               ", Found callback type:",str(callbacktype)]))
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
      self.log.debug(" ".join(["Difference in time in between scan start and onBatchScanResult:",
                               str(length_of_time)]))
      buffer = 1000000000  # 1 second
      if length_of_time > (report_delay_nanos + buffer):
        self.log.debug("Difference was greater than the allowable difference.")
        test_result = False
    return test_result

  # Handler Functions End

  def test_scan_flush_pending_scan_results(self):
    """
    Test that flush pending scan results doesn't affect onScanResults from triggering.
    Steps:
    1. Setup the scanning android device
    2. Setup the advertiser android devices.
    3. Trigger flushPendingScanResults on the scanning droid.
    4. Verify that only one onScanResults callback was triggered.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    scan_droid.flushPendingScanResults(scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1]), self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with TimeoutError:",str(error)]))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_trigger_on_batch_scan_results(self):
    """
    Test that triggers onBatchScanResults and verifies the time to trigger within one second leeway.
    Steps:
    1. Setup the scanning android device with report delay seconds set to 5000.
    2. Setup the advertiser android devices.
    3. Verify that only one onScanResults callback was triggered.
    4. Compare the system time that the scan was started with the elapsed time that is in the
    callback.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    scan_droid.setScanSettings(1, 5000, 0, 0)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onBatchScanResult"])
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    system_time_nanos = scan_droid.getSystemElapsedRealtimeNanos()
    self.log.debug(" ".join(["Current system time:",str(system_time_nanos)]))
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onbatchscanresult_event_handler,
      expected_event_name, ([system_time_nanos, 5000000000]),
      self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with:",str(error)]))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_flush_results_without_on_batch_scan_results_triggered(self):
    """
    Test flush pending scan results with a report delay seconds set to 0. No onBatchScanResults
    callback should be triggered.
    Steps:
    1. Setup the scanning android device with report delay seconds set to 0 (or just use default.
    2. Setup the advertiser android devices.
    3. Verify that no onBatchScanResults were triggered.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onBatchScanResults"])
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onbatchscanresult_event_handler,
      expected_event_name, ([]), self.default_timeout)
    scan_droid.flushPendingScanResults(scan_callback)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   10)
      self.log.debug(" ".join(["Unexpectedly found an advertiser:",event_info]))
      test_result = False
    except Empty as error:
      self.log.debug("No onBatchScanResult events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_non_existent_name_filter(self):
    """
    Test scan filter on non-existent device name.
    Steps:
    1. Setup the scanning android device with scan filter for device name set to an unexpected
    value.
    2. Setup the advertiser android devices.
    3. Verify that no onScanResults were triggered.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    filter_name = "".join([advertise_droid.bluetoothGetLocalName(),"_probably_wont_find"])
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    scan_droid.setScanFilterDeviceName(filter_name)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1]), self.default_timeout)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   10)
      self.log.debug(" ".join(["Unexpectedly found an advertiser:",event_info]))
      test_result = False
    except Empty as error:
      self.log.debug("No events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_scan_advertisement_with_device_service_uuid_filter_expect_no_events(
    self):
    """
    Test that exercises a service uuid filter on the scanner but no server uuid added to the
    advertisement.
    Steps:
    1. Setup the scanning android device with scan filter including a service uuid and mask.
    2. Setup the advertiser android devices.
    3. Verify that no onScanResults were triggered.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    service_uuid = "00000000-0000-1000-8000-00805F9B34FB"
    service_mask = "00000000-0000-1000-8000-00805F9B34FA"
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    scan_droid.setScanFilterServiceUuid(service_uuid, service_mask)
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_event_name, ([1]), self.default_timeout)
    try:
      event_info = scan_event_dispatcher.pop_event(expected_event_name,
                                                   self.default_timeout)
      self.log.debug(" ".join(["Unexpectedly found an advertiser:",event_info]))
      test_result = False
    except Empty as error:
      self.log.debug("No events were found as expected.")
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result
