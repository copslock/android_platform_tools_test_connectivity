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
from test_utils.bluetooth.ble_helper_functions import (verify_bluetooth_on_event,
                                                       generate_ble_scan_objects,
                                                       generate_ble_advertise_objects)


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
      "test_multiple_advertisers_on_batch_scan_result",
      "test_advertisement_service_uuid",
      "test_btu_hci_advertisement_crash",
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

  def bleadvertise_verify_onsuccess_handler(self, event, settings_in_effect):
    self.log.debug(pprint.pformat(event))
    return True

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

  ble_device_addresses = []

  def blescan_verify_onbatchscanresult_event_handler(self, event):
    """
    An event handler that validates the onBatchScanResult
    :param event: dict that represents the callback onBatchScanResult
    :return: test_result: bool
    """
    # Todo: Implement proper validation steps.
    test_result = True
    self.log.debug("Verifying onBatchScanResult event")
    self.log.debug(pprint.pformat(event))
    print(pprint.pformat(event))
    for event in event['data']['Results']:
      address = event['deviceInfo']['address']
      if address not in self.ble_device_addresses:
        self.ble_device_addresses.append(address)
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

  # TODO: move test to another script
  def test_multiple_advertisers_on_batch_scan_result(self):
    """
    Test that exercises onBatchScanResults against one device advertising its
    max advertisements.
    This is different from the BeaconSwarmTest:test_swarm_no_attenuation in
    that it uses a second android device's advertisements instead of standalone
    ble beacons.

    Steps:
    1. Setup the scanning android device
    2. Setup max (4) advertisements on secondary device.
    3. Verify that one hundred onBatchScanResult callback was triggered.
    :return: test_result: bool
    """
    test_result = True
    max_advertisers = 4
    ad_callbacks = []
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    for x in range(max_advertisers):
      advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
        advertise_droid)
      advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
      worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler, expected_advertise_event_name, ([]),
        self.default_timeout)
      ad_callbacks.append(advertise_callback)
    #self.attenuators[0].set_atten(0, 0)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    scan_droid.setScanSettings(1, 1000, 0, 0)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onBatchScanResult"])
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    n = 0
    while n < 100:
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onbatchscanresult_event_handler,
        expected_event_name, ([]), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug(" ".join(["Test failed with TimeoutError:",str(error)]))
      n+=1
    scan_droid.stopBleScan(scan_callback)
    for x in ad_callbacks:
      advertise_droid.stopBleAdvertising(x)
    print (self.ble_device_addresses) #temporary
    print (str(len(self.ble_device_addresses))) #temporary
    return test_result

  def test_advertisement_service_uuid(self):
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_droid.setAdvertiseDataSetServiceUuids(["00000000-0000-1000-8000-00805f9b34fb"])
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)

    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_data, advertise_settings, advertise_callback = (
      generate_ble_advertise_objects(advertise_droid))
    test_result = advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)

    test_result = scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    time.sleep(30)
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


  #{'is_connectable': True, 'mode': 0, 'tx_power_level': 2}
  def test_btu_hci_advertisement_crash(self):
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    x = 0
    while x < 50:
      advertise_droid.setAdvertisementSettingsAdvertiseMode(
        AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value)
      advertise_droid.setAdvertisementSettingsIsConnectable(True)
      advertise_droid.setAdvertisementSettingsTxPowerLevel(2)
      filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
        scan_droid)

      expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
      advertise_data, advertise_settings, advertise_callback = (
        generate_ble_advertise_objects(advertise_droid))
      advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      advertise_droid.stopBleAdvertising(advertise_callback)
      x+=1

    return test_result