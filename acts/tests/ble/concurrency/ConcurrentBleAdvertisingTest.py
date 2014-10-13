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

import concurrent
import time

"""
Test script to exercises different ways Ble Advertisements can run in concurrency.
This test was designed to be run in a shield box.
"""

from queue import Empty
from base_test import BaseTestClass
from test_utils.BleEnum import *
from test_utils.ble_test_utils import (generate_ble_advertise_objects,
                                       generate_ble_scan_objects,
                                       setup_multiple_devices_for_bluetooth_test,
                                       take_btsnoop_log,
                                       reset_bluetooth)

class ConcurrentBleAdvertisingTest(BaseTestClass):
  TAG = "ConcurrentBleAdvertisingTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 10
  max_advertisements = 4

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_max_advertisements_defaults",
      "test_max_advertisements_include_device_name_and_filter_device_name",
      "test_max_advertisements_exclude_device_name_and_filter_device_name",
      "test_max_advertisements_with_manufacturer_data",
      "test_max_advertisements_with_manufacturer_data_mask",
      "test_max_advertisements_with_service_data",
      "test_max_advertisements_with_manufacturer_data_mask_and_include_device_name",
      "test_max_advertisements_with_service_uuids",
      "test_max_advertisements_with_service_uuid_and_service_mask",
      "test_max_advertisements_plus_one",
      "test_start_two_advertisements_on_same_callback",
      "test_toggle_advertiser_bt_state",
      "test_restart_advertise_callback_after_bt_toggle",
    )

  def setup_class(self):
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.ed1.start()
    return setup_multiple_devices_for_bluetooth_test(self.android_devices)

  def on_exception(self, test_name, begin_time):
    self.log.debug(" ".join(["Test", test_name, "failed. Gathering bugreport and btsnoop logs"]))
    for ad in self.android_devices:
      take_btsnoop_log(self, test_name, ad)

  def on_success(self, test_name, begin_time):
    reset_bluetooth([self.android_devices[1]])

  def on_fail(self, test_name, begin_time):
    reset_bluetooth(self.android_devices)

  def blescan_verify_onscanresult_event_handler(self, event):
    return event

  def bleadvertise_verify_onsuccess_handler(self, event):
    return event

  def _verify_n_advertisements(self, num_advertisements, filter_list):
    test_result = False
    address_list = []
    self.scan_droid.setScanSettings(
      ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
      ScanSettingsScanMode.SCAN_MODE_LOW_LATENCY.value,
      ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
    self.advertise_droid.setAdvertisementSettingsAdvertiseMode(
        AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_data = self.advertise_droid.buildAdvertiseData()
    advertise_settings = self.advertise_droid.buildAdvertisementSettings()
    advertise_callback_list = []
    for _ in range(num_advertisements):
      advertise_callback = self.advertise_droid.genBleAdvertiseCallback()
      advertise_callback_list.append(advertise_callback)
      self.advertise_droid.startBleAdvertising(advertise_callback, advertise_data,
                                               advertise_settings)
      expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
      advertise_worker = self.advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler,
        expected_advertise_event_name, (),
        self.default_timeout)
      try:
        advertise_worker.result(self.default_timeout)
      except Empty as error:
        self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
        return False
      except concurrent.futures._base.TimeoutError as error:
        self.log.debug(" ".join(["Test failed, filtering callback onSuccess never occurred:",
                               str(error)]))
        return False
    scan_settings = self.scan_droid.buildScanSetting()
    scan_callback = self.scan_droid.genScanCallback()
    self.scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    expected_scan_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    start_time = time.time()
    while (start_time + self.default_timeout) > time.time():
      worker = self.scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_scan_event_name, (), self.default_timeout)
      event = None
      try:
        event = worker.result(self.default_timeout)
      except Empty as error:
        self.log.debug(" ".join(["Test failed with:",str(error)]))
        return test_result
      except concurrent.futures._base.TimeoutError as error:
        self.log.debug(" ".join(["Test failed with:",str(error)]))
        return test_result
      address = event['data']['Result']['deviceInfo']['address']
      if address not in address_list:
        address_list.append(address)
      if len(address_list) == num_advertisements:
        test_result = True
        break
    for callback in advertise_callback_list:
      self.advertise_droid.stopBleAdvertising(callback)
    self.scan_droid.stopBleScan(scan_callback)
    return test_result

  def test_max_advertisements_defaults(self):
    """Test that a single device can have the max advertisements concurrently
    advertising.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Start scanning on the max_advertisements as defined in the script.
    4. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.buildScanFilter(filter_list)
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_include_device_name_and_filter_device_name(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the device name as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include device name in each advertisement.
    4. Include device name filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    self.advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterDeviceName(self.advertise_droid.bluetoothGetLocalName())
    self.scan_droid.buildScanFilter(filter_list)
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_exclude_device_name_and_filter_device_name(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the device name as a part of the filter but not the
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include device name filter in the scanner.
    4. Start scanning on the max_advertisements as defined in the script.
    5. Verify that no advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    self.advertise_droid.setAdvertiseDataIncludeDeviceName(False)
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterDeviceName(self.advertise_droid.bluetoothGetLocalName())
    self.scan_droid.buildScanFilter(filter_list)
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return not test_result

  def test_max_advertisements_with_manufacturer_data(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the manufacturer data as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include manufacturer data in each advertisement.
    4. Include manufacturer data filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterManufacturerData(1,"1")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.addAdvertiseDataManufacturerId(1,"1")
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_with_manufacturer_data_mask(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the manufacturer data mask as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include manufacturer data in each advertisement.
    4. Include manufacturer data mask filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterManufacturerData(1,"1","1")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.addAdvertiseDataManufacturerId(1,"1")
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_with_service_data(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the service data as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include service data in each advertisement.
    4. Include service data filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterServiceData("0000110A-0000-1000-8000-00805F9B34FB", "11,17,80")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.addAdvertiseDataServiceData(
      "0000110A-0000-1000-8000-00805F9B34FB", "11,17,80")
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_with_manufacturer_data_mask_and_include_device_name(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the device name and manufacturer data as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include device name and manufacturer data in each advertisement.
    4. Include device name and manufacturer data filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    self.scan_droid.setScanFilterDeviceName(self.advertise_droid.bluetoothGetLocalName())
    self.scan_droid.setScanFilterManufacturerData(1,"1","1")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.addAdvertiseDataManufacturerId(1,"1")
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_with_service_uuids(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the service uuid as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include service uuid in each advertisement.
    4. Include service uuid filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterServiceUuid("00000000-0000-1000-8000-00805f9b34fb")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.setAdvertiseDataSetServiceUuids(["00000000-0000-1000-8000-00805f9b34fb"])
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_with_service_uuid_and_service_mask(self):
    """Test that a single device can have the max advertisements concurrently
    advertising. Include the service mask as a part of the filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Include service uuid in each advertisement.
    4. Include service mask filter in the scanner.
    5. Start scanning on the max_advertisements as defined in the script.
    6. Verify that all advertisements are found.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.setScanFilterServiceUuid("00000000-0000-1000-8000-00805f9b34fb",
                                        "00000000-0000-1000-8000-00805f9b34fb")
    self.scan_droid.buildScanFilter(filter_list)
    self.advertise_droid.setAdvertiseDataSetServiceUuids(["00000000-0000-1000-8000-00805f9b34fb"])
    test_result = self._verify_n_advertisements(self.max_advertisements, filter_list)
    return test_result

  def test_max_advertisements_plus_one(self):
    """Test that a single device can have the max advertisements concurrently
    advertising but fail on starting the max advertisements plus one.
    filter and
    advertisement data.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Start max_advertisements + 1.
    :return: test_result: bool
    """
    test_result = True
    self.scan_droid, self.scan_event_dispatcher = self.droid, self.ed
    self.advertise_droid, self.advertise_event_dispatcher = self.droid1, self.ed1
    filter_list = self.scan_droid.genFilterList()
    self.scan_droid.buildScanFilter(filter_list)
    test_result = self._verify_n_advertisements(self.max_advertisements + 1, filter_list)
    return not test_result

  def test_start_two_advertisements_on_same_callback(self):
    """Test that a single device cannot have two advertisements start on the same
    callback.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Call start ble advertising on the same callback.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data,
                                               advertise_settings)
    expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
    advertise_worker = advertise_event_dispatcher.handle_event(
      self.bleadvertise_verify_onsuccess_handler,
      expected_advertise_event_name, (),
      self.default_timeout)
    try:
      advertise_worker.result(self.default_timeout)
    except Empty as error:
      self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
      return False
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test failed, filtering callback onSuccess never occurred:",
                               str(error)]))
    try:
      advertise_droid.startBleAdvertising(advertise_callback, advertise_data,
                                               advertise_settings)
      expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
      advertise_worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler,
        expected_advertise_event_name, (),
      self.default_timeout)
      advertise_worker.result(self.default_timeout)
      test_result = False
    except Empty as error:
      self.log.debug(" ".join(["Test passed with Empty error:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test passed, filtering callback onSuccess never occurred:",
                               str(error)]))

    return test_result

  def test_toggle_advertiser_bt_state(self):
    """Test that a single device resets its callbacks when the bluetooth state is
    reset. There should be no advertisements.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Call start ble advertising.
    4. Toggle bluetooth on and off.
    5. Scan for any advertisements.
    :return: test_result: bool
    """
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data,
                                               advertise_settings)
    expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
    advertise_worker = advertise_event_dispatcher.handle_event(
      self.bleadvertise_verify_onsuccess_handler,
      expected_advertise_event_name, (),
      self.default_timeout)
    try:
      advertise_worker.result(self.default_timeout)
    except Empty as error:
      self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
      return False
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test failed, filtering callback onSuccess never occurred:",
                               str(error)]))
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(scan_droid)
    #begin here
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    expected_scan_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_scan_event_name, ([]), self.default_timeout)
    try:
      test_result = worker.result(self.default_timeout)
    except Empty as error:
      self.log.debug(" ".join(["Test failed with:",str(error)]))
      return False
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test failed with:",str(error)]))
      return False
    scan_droid.stopBleScan(scan_callback)
    test_result = reset_bluetooth([self.android_devices[1]])
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    if not test_result:
      return test_result
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_scan_event_name, ([]), self.default_timeout)
    try:
      test_result = worker.result(self.default_timeout)
      return False
    except Empty as error:
      self.log.debug(" ".join(["Test passed with:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test passed with:",str(error)]))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_restart_advertise_callback_after_bt_toggle(self):
    """Test that a single device resets its callbacks when the bluetooth state is
    reset.
    Steps:
    1. Setup the scanning android device.
    2. Setup the advertiser android device.
    3. Call start ble advertising.
    4. Toggle bluetooth on and off.
    5. Call start ble advertising on the same callback.
    :return: test_result: bool
    """
    test_result = True
    advertise_droid, advertise_event_dispatcher = self.droid, self.ed
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(advertise_droid)
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
    test_result = reset_bluetooth([self.android_devices[0]])
    if not test_result:
      return test_result
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
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
    return test_result