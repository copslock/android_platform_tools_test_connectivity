#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
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

import concurrent
import pprint
import time

from queue import Empty
from acts.base_test import BaseTestClass
from acts.test_utils.bt.BleEnum import *
from acts.test_utils.bt.bt_test_utils import *


class BugsTest(BaseTestClass):
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, controllers)
    self.tests = (
      "test_scan_advertise_50",
      "test_swarm_scan",
      "test_three_advertisers_and_three_scanners",
      "test_dual_scans",
      "test_multiple_advertisers_on_batch_scan_result",
      "test_advertisement_service_uuid",
      "test_btu_hci_advertisement_crash",
      "test_deep_sleep_advertising",
      "test_random_mac_address_filtering",
      "test_advertisement",
      "test_28_advertisers",
    )

  def setup_class(self):
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.ed1.start()
    return setup_multiple_devices_for_bt_test(self.droids, self.eds)

  def on_fail(self, test_name, begin_time):
    take_btsnoop_logs(self.droids, self, test_name)
    reset_bluetooth(self.droids, self.eds)

  # Handler Functions Begin
  def blescan_verify_onfailure_event_handler(self, event):
    self.log.debug("Verifying onFailure event")
    self.log.debug(pprint.pformat(event))
    return event

  def bleadvertise_verify_onsuccess_handler(self, event):
    self.log.debug(pprint.pformat(event))
    return True

  def ble_scan_get_mac_address_handler(self, event):
    self.log.info(pprint.pformat(event))
    return event['data']['Result']['deviceInfo']['address']

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

  def blescan_verify_onscanresult_event_handler2(self, event,
                                                system_time_nanos=None):
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    return event['data']['Result']['deviceInfo']['address']

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
    advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(
      advertise_droid)
    n = 0
    while n < 50:
      test_result = advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data,
                                              advertise_settings)
      if not test_result:
        self.log.debug("Advertising failed.")
        return test_result
      self.log.debug("Step 4: Start Bluetooth Le Scan on callback ID: " + str(
        scan_callback))
      test_result = scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
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
      scan_droid.bleStopBleScan(scan_callback)
      advertise_droid.bleStopBleAdvertising(advertise_callback)
      advertise_droid.bluetoothToggleState(False)
      advertise_droid.bluetoothToggleState(True)
      time.sleep(12)
      n += 1
    return test_result

  def test_swarm_scan(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(
      advertise_droid)
    n = 0
    while n < 10000:
      test_result = advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      test_result = scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
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
      scan_droid.bleStopBleScan(scan_callback)
      n += 1
      advertise_droid.bleStopBleAdvertising(advertise_callback)
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
      test_result = scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
      test_result = scan_droid2.bluetoothStartBleScan(filter_list2,scan_settings2,scan_callback2)
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
      scan_droid.bleStopBleScan(scan_callback)
      scan_droid2.bluetoothStopBleScan(scan_callback2)
      n += 1
    return test_result

  def test_three_advertisers_and_three_scanners(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
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
    advertise_callback, advertise_data, advertise_settings = (
      generate_ble_advertise_objects(advertise_droid))
    advertise_callback1, advertise_data1, advertise_settings1 = (
      generate_ble_advertise_objects(advertise_droid))
    advertise_callback2, advertise_data2, advertise_settings2 = (
      generate_ble_advertise_objects(advertise_droid))
    test_result = advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    test_result = advertise_droid.bleStartBleAdvertising(advertise_callback1, advertise_data1,
                                                      advertise_settings1)
    test_result = advertise_droid.bleStartBleAdvertising(advertise_callback2, advertise_data2,
                                                      advertise_settings2)

    test_result = scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
    test_result = scan_droid.bleStartBleScan(filter_list1,scan_settings1,scan_callback1)
    test_result = scan_droid.bleStartBleScan(filter_list2,scan_settings2,scan_callback2)
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
    scan_droid.bleStopBleScan(scan_callback)
    scan_droid.bleStopBleScan(scan_callback1)
    scan_droid.bleStopBleScan(scan_callback2)
    advertise_droid.bleStopBleAdvertising(advertise_callback)
    advertise_droid.bleStopBleAdvertising(advertise_callback1)
    advertise_droid.bleStopBleAdvertising(advertise_callback2)

    return test_result

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
      advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(
        advertise_droid)
      advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
      worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler, expected_advertise_event_name, ([]),
        self.default_timeout)
      ad_callbacks.append(advertise_callback)
    #self.attenuators[0].set_atten(0, 0)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    scan_droid.bleSetScanSettingsReportDelayMillis(1000)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "".join(["BleScan",str(scan_callback),"onBatchScanResult"])
    scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
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
    scan_droid.bleStopBleScan(scan_callback)
    for x in ad_callbacks:
      advertise_droid.bleStopBleAdvertising(x)
    print (self.ble_device_addresses) #temporary
    print (str(len(self.ble_device_addresses))) #temporary
    return test_result

  def test_advertisement_service_uuid(self):
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_droid.bleSetAdvertiseDataSetServiceUuids(["00000000-0000-1000-8000-00805f9b34fb"])
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)

    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_callback, advertise_data, advertise_settings = (
      generate_ble_advertise_objects(advertise_droid))
    test_result = advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)

    test_result = scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
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
    scan_droid.bleStopBleScan(scan_callback)
    advertise_droid.bleStopBleAdvertising(advertise_callback)

    return test_result


  #{'is_connectable': True, 'mode': 0, 'tx_power_level': 2}
  def test_btu_hci_advertisement_crash(self):
    test_result = True
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    x = 0
    while x < 50:
      advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
        AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value)
      advertise_droid.bleSetAdvertiseSettingsIsConnectable(True)
      advertise_droid.bleSetAdvertiseSettingsTxPowerLevel(2)
      filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
        scan_droid)

      expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
      advertise_callback, advertise_data, advertise_settings = (
        generate_ble_advertise_objects(advertise_droid))
      advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      advertise_droid.bleStopBleAdvertising(advertise_callback)
      x+=1

    return test_result

  def test_deep_sleep_advertising(self):
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    max_advertisements = 4
    advertisement_callback_list = []
    advertisement_mac_addr_list = []
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    while len(advertisement_mac_addr_list) < max_advertisements:
      advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
        AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
      advertise_callback, advertise_data, advertise_settings = (
        generate_ble_advertise_objects(advertise_droid))
      advertisement_callback_list.append(advertise_callback)
      advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
      worker = scan_event_dispatcher.handle_event(
        self.ble_scan_get_mac_address_handler,
        expected_event_name, (), self.default_timeout)
      try:
        mac_address = worker.result(self.default_timeout)
        print(mac_address)
        if mac_address not in advertisement_mac_addr_list:
          advertisement_mac_addr_list.append(mac_address)
      except Exception:
        self.log.info("failed to find advertisement")
    scan_droid.bleStopBleScan(scan_callback)
    print("putting advertise droid to sleep")
    try:
      print (pprint.pformat(self.ed1.pop_all(expected_event_name)))
    except Exception:
      print ("lol fail")
    advertise_droid.setDeepSleep(960000) #16 minutes
    advertise_droid.wakeUpNow()
    scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
    advertisement_mac_addr_list2 = []
    while len(advertisement_mac_addr_list2) < max_advertisements:
      worker = scan_event_dispatcher.handle_event(
        self.ble_scan_get_mac_address_handler,
        expected_event_name, (), self.default_timeout)
      try:
        mac_address = worker.result(self.default_timeout)
        print(mac_address)
        if mac_address not in advertisement_mac_addr_list2:
          advertisement_mac_addr_list2.append(mac_address)
      except Exception:
        self.log.info("failed to find advertisement")
    scan_droid.bleStopBleScan(scan_callback)
    diff_list = list(set(advertisement_mac_addr_list) - set(advertisement_mac_addr_list2))
    print(pprint.pformat(advertisement_mac_addr_list))
    print(pprint.pformat(advertisement_mac_addr_list2))
    for callback in advertisement_callback_list:
      advertise_droid.bleStopBleAdvertising(callback)
    print("new callback")
    print(pprint.pformat(diff_list))
    print("done")
    if len(diff_list) != max_advertisements:
      return False
    else:
      return True

  def test_random_mac_address_filtering(self):
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    advertisement_callback_list = []
    advertisement_mac_addr_list = []
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_callback, advertise_data, advertise_settings = (
      generate_ble_advertise_objects(advertise_droid))
    advertisement_callback_list.append(advertise_callback)
    advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    worker = scan_event_dispatcher.handle_event(
      self.ble_scan_get_mac_address_handler,
      expected_event_name, (), self.default_timeout)
    mac_address = None
    try:
      mac_address = worker.result(self.default_timeout)
      print(mac_address)
      if mac_address not in advertisement_mac_addr_list:
        advertisement_mac_addr_list.append(mac_address)
    except Exception:
      self.log.info("failed to find advertisement")
    try:
      scan_event_dispatcher.stop()
      scan_event_dispatcher.start()
    except Exception:
      print("do nothing")
    scan_droid.bleStopBleScan(scan_callback)
    print("This mac address is being set for a filter: " + mac_address)
    filter_list2 = scan_droid.bleGenFilterList()
    scan_droid.bleSetScanFilterDeviceAddress(mac_address)
    scan_droid.bleBuildScanFilter(filter_list)
    scan_settings2 = scan_droid.bleBuildScanSetting()
    scan_callback2 = scan_droid.bleGenScanCallback()

    scan_droid.bleStartBleScan(filter_list2,scan_settings2,scan_callback2)
    expected_event_name = "BleScan" + str(scan_callback2) + "onScanResults"
    worker = scan_event_dispatcher.handle_event(
      self.ble_scan_get_mac_address_handler,
      expected_event_name, (), self.default_timeout)
    try:
      mac_address = worker.result(self.default_timeout)
      print(mac_address)
      if mac_address not in advertisement_mac_addr_list:
        advertisement_mac_addr_list.append(mac_address)
    except Exception:
      self.log.info("failed to find advertisement")
      return False
    scan_droid.bleStopBleScan(scan_callback2)
    advertise_droid.bleStopBleAdvertising(advertise_callback)
    return True



  def test_advertisement(self):
    test_result = True
    max_advertisers = 4
    ad_callbacks = []
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    #if False:
    #  from acts.etc.development.ide.pycharm.android_intellisense import AndroidIntellisense
    #  assert isinstance(advertise_droid, AndroidIntellisense)
    advertiser_local_name = advertise_droid.bluetoothGetLocalName()
    advertise_droid.bleSetAdvertiseDataIncludeDeviceName(False)
    advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(
      advertise_droid)
    advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    print("Sleeping")
    #time.sleep(30)
    expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
    worker = advertise_event_dispatcher.handle_event(
      self.bleadvertise_verify_onsuccess_handler, expected_advertise_event_name, ([]),
      self.default_timeout)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    filter_list = scan_droid.bleGenFilterList()
    scan_droid.bleSetScanFilterDeviceName(advertiser_local_name)
    scan_droid.bleBuildScanFilter(filter_list)
    scan_settings = scan_droid.bleBuildScanSetting()
    scan_callback = scan_droid.bleGenScanCallback()
    expected_event_name = "".join(["BleScan",str(scan_callback),"onScanResult"])
    scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
    worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([1]), self.default_timeout)
    try:
      self.log.info(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with TimeoutError:",str(error)]))
    scan_droid.bleStopBleScan(scan_callback)
    advertise_droid.bleStopBleAdvertising(advertise_callback)
    print("Advertiser " + advertise_droid.bluetoothGetLocalName())
    print("Scanner" + scan_droid.bluetoothGetLocalName())
    return test_result

  def test_28_advertisers(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    max_advertisements = 28
    advertise_callback_list = []
    d_counter = 0
    sprout_counter = 0
    while d_counter < len(self.droids):
      advertise_droid, advertise_event_dispatcher = self.droids[d_counter], self.eds[d_counter]
      d_counter+=1
      sprout_names = ["Sprout","Micromax AQ4501","4560MMX"]
      print("Checking device model")
      if advertise_droid.getBuildModel() not in sprout_names:
        continue
      n = 0
      sprout_counter+=1
      while n < max_advertisements:
        advertise_droid.bleSetAdvertiseDataIncludeDeviceName(True)
        advertise_droid.bleSetAdvertiseSettingsAdvertiseMode(
          AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
        advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(
          advertise_droid)
        test_result = advertise_droid.bleStartBleAdvertising(advertise_callback, advertise_data, advertise_settings)
        expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
        worker = advertise_event_dispatcher.handle_event(
        self.bleadvertise_verify_onsuccess_handler, expected_advertise_event_name, ([]),
        self.default_timeout)
        try:
          worker.result()
        except Exception as e:
          self.log.info("Advertising failed due to " + str(e))
          reset_bluetooth(self.droids, self.eds)
          return False
        print (str(n) + "th advertisement successful")
        n+=1
    mac_address_list = []
    done = False
    advertisements_to_find = sprout_counter * max_advertisements
    min_advertisements_to_pass = int(advertisements_to_find * 0.9)
    print("START SNIFFER")
    time.sleep(30)
    end_time = time.time() + 120
    while not done and time.time() < end_time:
      print("try again " + str(mac_address_list))
      print(str(len(mac_address_list)))
      filter_list = scan_droid.bleGenFilterList()
      scan_droid.bleSetScanFilterDeviceName("Micromax AQ4501")
      scan_droid.bleBuildScanFilter(filter_list)
      scan_droid.bleSetScanFilterDeviceName("4560MMX")
      scan_droid.bleBuildScanFilter(filter_list)
      scan_settings = scan_droid.bleBuildScanSetting()
      scan_callback = scan_droid.bleGenScanCallback()
      scan_droid.bleStartBleScan(filter_list,scan_settings,scan_callback)
      expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler2,
        expected_event_name, ([]), self.default_timeout)
      try:
        mac_address = worker.result(self.default_timeout)
        print(mac_address)
        if mac_address not in mac_address_list:
          mac_address_list.append(mac_address)
          print (str(len(mac_address_list)) + " advertisements found")
        if len(mac_address_list) >= advertisements_to_find:
          done = True
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        self.log.debug("Test failed with TimeoutError: " + str(error))
      scan_droid.bleStopBleScan(scan_callback)
    return test_result
