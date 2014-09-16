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
import itertools as it
import pprint
import time

from queue import Empty
from base_test import BaseTestClass
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import (verify_bluetooth_on_event,
                                                       generate_ble_scan_objects,
                                                       generate_ble_advertise_objects)


class FilteringTest(BaseTestClass):
  TAG = "FilteringTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 20

  valid_filter_suite = [
    {
      'include_device_name': True
    },
    {
      'include_tx_power_level': True
    },
    {
      'filter_device_address': True
    },
    {
      'manufacturer_specific_data_id': 1,
      'manufacturer_specific_data': "1"
    },
    {
      'manufacturer_specific_data_id': 1,
      'manufacturer_specific_data': "14,0,54,0,0,0,0,0"
    },
    {
      'manufacturer_specific_data_id': 1,
      'manufacturer_specific_data': "1",
      'manufacturer_specific_data_mask': "1"
    },
    {
      'service_data_uuid': "0000110A-0000-1000-8000-00805F9B34FB",
      'service_data': "11,17,80"
    },
    {
      'service_data_uuid': "0000110B-0000-1000-8000-00805F9B34FB",
      'service_data': "13,0,8"
    },
    {
      'service_data_uuid': "0000110C-0000-1000-8000-00805F9B34FB",
      'service_data': "11,14,50"
    },
    {
      'service_data_uuid': "0000110D-0000-1000-8000-00805F9B34FB",
      'service_data': "16,22,11"
    },
    {
      'service_data_uuid': "0000110E-0000-1000-8000-00805F9B34FB",
      'service_data': "2,9,54"
    },
    {
      'service_data_uuid': "0000110F-0000-1000-8000-00805F9B34FB",
      'service_data': "69,11,50"
    },
    {
      'service_data_uuid': "00001101-0000-1000-8000-00805F9B34FB",
      'service_data': "12,11,21"
    },
    {
      'service_data_uuid': "00001102-0000-1000-8000-00805F9B34FB",
      'service_data': "12,12,44"
    },
    {
      'service_data_uuid': "00001103-0000-1000-8000-00805F9B34FB",
      'service_data': "4,54,1"
    },
    {
      'service_data_uuid': "00001104-0000-1000-8000-00805F9B34FB",
      'service_data': "33,22,44"
    },
    {
      'service_uuid': "00000000-0000-1000-8000-00805f9b34fb",
      'service_mask': "00000000-0000-1000-8000-00805f9b34fb",
    },
    {
      'service_uuid': "00000000-0000-1000-8000-00805f9b34fb",
    },
  ]

  valid_filter_variants = {
    'include_device_name': [True, False],
    'include_tx_power_level': [True, False],
    'manufacturer_specific_data_id': [1, 2, 65535],
    'manufacturer_specific_data': ["1", "1,2", "127"],
    'service_data_uuid': ["00000000-0000-1000-8000-00805f9b34fb"],
    'service_data': ["1,2,3", "1", "127"],
  }

  multi_manufacturer_specific_data_suite = {
    'manufacturer_specific_data_list': [[(1, "1"), (2, "2"), (65535, "127")]],
  }

  settings_in_effect_variants = {
    "mode": [
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value,
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
    ],
    "tx_power_level": [
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value,
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value,
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value,
    ],
    "is_connectable": [True, False]
  }

  default_callback = 1
  default_is_connectable = True
  default_advertise_mode = 0
  default_tx_power_level = 2

  def _get_combinations(self, t):
    varNames = sorted(t)
    return (
      [dict(zip(varNames, prod)) for prod
       in it.product(*(t[varName] for varName in varNames))])

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_settings_in_effect_suite",
      "test_filters_suite",
      "test_valid_filters",
      # "test_multi_manufacturer_specific_data",
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

  def blescan_verify_onscanresult_event_handler(self, event, filters):
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    callback_type = event['data']['CallbackType']
    if 'callback_type' in filters.keys():
      if filters['callback_type'] != callback_type:
        self.log.debug(" ".join(["Expected callback type:",str(filters['callback_type']),
                                 ", Found callback type:",str(callback_type)]))
      test_result = False
    elif self.default_callback != callback_type:
      self.log.debug(" ".join(["Expected callback type:",str(self.default_callback),
                               ", Found callback type:",
                               str(callback_type)]))
      test_result = False
    if 'include_device_name' in filters.keys() and filters[
      'include_device_name'] is not False:
      if event['data']['Result']['deviceName'] != filters[
        'include_device_name']:
        self.log.debug(" ".join(["Expected device name:",filters['include_device_name'],
                                 ", Found device name:",
                                 event['data']['Result']['deviceName']]))
        test_result = False
    elif 'deviceName' in event['data']['Result'].keys():
      self.log.debug("Device name was found when it wasn't meant to be included.")
      test_result = False
    if ('include_tx_power_level' in filters.keys() and filters[
      'include_tx_power_level'] is not False and event['data']['Result'][
      'txPowerLevel'] != JavaInteger.MIN.value):
      if not event['data']['Result']['txPowerLevel']:
        self.log.debug("Expected to find tx power level in event but found none.")
        test_result = False
    elif (event['data']['Result']['txPowerLevel'] !=
            JavaInteger.MIN.value):
      self.log.debug(" ".join(["Tx power level found as min java integer, was not meant",
                              "to be included in the advertisement."]))
      test_result = False
    if not event['data']['Result']['rssi']:
      self.log.debug("Expected rssi in the advertisement, found none.")
      test_result = False
    if not event['data']['Result']['timestampNanos']:
      self.log.debug("Expected rssi in the advertisement, found none.")
      test_result = False
    return test_result

  def bleadvertise_verify_onsuccess_handler(self, event, settings_in_effect):
    self.log.debug(pprint.pformat(event))
    test_result = True
    if 'is_connectable' in settings_in_effect.keys():
      if (event['data']['SettingsInEffect']['isConnectable'] !=
            settings_in_effect['is_connectable']):
        self.log.debug(" ".join(["Expected is connectable value:",
                       str(settings_in_effect['is_connectable']),
                       "Actual is connectable value:",
                       str(event['data']['SettingsInEffect']['isConnectable'])]))
        test_result = False
    elif (event['data']['SettingsInEffect']['isConnectable'] !=
            self.default_is_connectable):
      self.log.debug("Default value for isConnectable did not match what was found.")
      test_result = False
    if 'mode' in settings_in_effect.keys():
      if (event['data']['SettingsInEffect']['mode'] !=
            settings_in_effect['mode']):
        self.log.debug(" ".join(["Expected mode value:",str(settings_in_effect['mode']),
                                "Actual mode value:",
                                str(event['data']['SettingsInEffect']['mode'])]))
        test_result = False
    elif (event['data']['SettingsInEffect']['mode'] !=
            self.default_advertise_mode):
      self.log.debug("Default value for filtering mode did not match what was found.")
      test_result = False
    if 'tx_power_level' in settings_in_effect.keys():
      if (event['data']['SettingsInEffect']['txPowerLevel'] ==
            JavaInteger.MIN.value):
        self.log.debug(" ".join(["Expected tx power level was not meant to be",
                                str(JavaInteger.MIN.value)]))
        test_result = False
    elif (event['data']['SettingsInEffect']['txPowerLevel'] !=
            self.default_tx_power_level):
      self.log.debug("Default value for tx power level did not match what was found.")
      test_result = False
    return test_result

  # Handler Functions End

  def _magic(self, params):
    (filters, settings_in_effect) = params
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    self.log.debug(" ".join(["Settings in effect:",pprint.pformat(settings_in_effect)]))
    self.log.debug(" ".join(["filters:",pprint.pformat(filters)]))
    test_result = True
    if 'is_connectable' in settings_in_effect.keys():
      advertise_droid.setAdvertisementSettingsIsConnectable(settings_in_effect['is_connectable'])
    if 'mode' in settings_in_effect.keys():
      advertise_droid.setAdvertisementSettingsAdvertiseMode(settings_in_effect['mode'])
    if 'tx_power_level' in settings_in_effect.keys():
      advertise_droid.setAdvertisementSettingsTxPowerLevel(settings_in_effect['tx_power_level'])
    filter_list = scan_droid.genFilterList()
    if 'include_device_name' in filters.keys() and filters['include_device_name'] is not False:
      advertise_droid.setAdvertiseDataIncludeDeviceName(True)
      filters['include_device_name'] = advertise_droid.bluetoothGetLocalName()
      scan_droid.setScanFilterDeviceName(filters['include_device_name'])
    if ('include_tx_power_level' in filters.keys() and filters[
      'include_tx_power_level'] is not False):
      advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    if 'manufacturer_specific_data_id' in filters.keys():
      if 'manufacturer_specific_data_mask' in filters.keys():
        advertise_droid.addAdvertiseDataManufacturerId(
          filters['manufacturer_specific_data_id'],
          filters['manufacturer_specific_data'])
        scan_droid.setScanFilterManufacturerData(
          filters['manufacturer_specific_data_id'],
          filters['manufacturer_specific_data'],
          filters['manufacturer_specific_data_mask'])
      else:
        advertise_droid.addAdvertiseDataManufacturerId(
          filters['manufacturer_specific_data_id'],
          filters['manufacturer_specific_data'])
        scan_droid.setScanFilterManufacturerData(
          filters['manufacturer_specific_data_id'],
          filters['manufacturer_specific_data'])
    if 'service_data' in filters.keys():
      advertise_droid.addAdvertiseDataServiceData(
        filters['service_data_uuid'],
        filters['service_data'])
      scan_droid.setScanFilterServiceData(
        filters['service_data_uuid'],
        filters['service_data'])
    if 'manufacturer_specific_data_list' in filters.keys():
      for pair in filters['manufacturer_specific_data_list']:
        (manu_id, manu_data) = pair
        advertise_droid.addAdvertiseDataManufacturerId(manu_id, manu_data)
    if 'service_mask' in filters.keys():
      scan_droid.setScanFilterServiceUuid(filters['service_uuid'],
                                          filters['service_mask'])
      advertise_droid.setAdvertiseDataSetServiceUuids([filters['service_uuid']])
    elif 'service_uuid' in filters.keys():
      scan_droid.setScanFilterServiceUuid(filters['service_uuid'])
      advertise_droid.setAdvertiseDataSetServiceUuids([filters['service_uuid']])
    scan_droid.buildScanFilter(filter_list)
    advertise_data, advertise_settings, advertise_callback = (
      generate_ble_advertise_objects(advertise_droid))
    scan_droid.setScanSettings(
      ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
      ScanSettingsScanMode.SCAN_MODE_LOW_LATENCY.value,
      ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
    scan_settings = scan_droid.buildScanSetting()
    scan_callback = scan_droid.genScanCallback()
    advertise_droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
    expected_advertise_event_name = "".join(["BleAdvertise",str(advertise_callback),"onSuccess"])
    self.log.debug(expected_advertise_event_name)
    advertise_worker = advertise_event_dispatcher.handle_event(
      self.bleadvertise_verify_onsuccess_handler,
      expected_advertise_event_name, ([settings_in_effect]),
      self.default_timeout)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback)
    try:
      test_result = advertise_worker.result(self.default_timeout)
    except Empty as error:
      self.log.debug(" ".join(["Test failed with Empty error:",str(error)]))
      return False
    except concurrent.futures._base.TimeoutError as error:
      self.log.debug(" ".join(["Test failed, filtering callback onSuccess never occurred:",
                               str(error)]))
      return False
    expected_scan_event_name = "".join(["BleScan",str(scan_callback),"onScanResults"])
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onscanresult_event_handler,
      expected_scan_event_name, ([filters]), self.default_timeout)
    try:
      test_result = worker.result(self.default_timeout)
    except Empty as error:
      test_result = False
      self.log.debug(" ".join(["Test failed with:",str(error)]))
    except concurrent.futures._base.TimeoutError as error:
      scan_droid.stopBleScan(scan_callback)
      advertise_droid.stopBleAdvertising(advertise_callback)
      test_result = False
      self.log.debug(" ".join(["Test failed with:",str(error)]))
    scan_droid.stopBleScan(scan_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def test_default_advertisement(self):
    filters = {}
    settings_in_effect = {}
    return self._magic(filters, settings_in_effect)

  def test_settings_in_effect_suite(self):
    settings_in_effect_suite = self._get_combinations(
      self.settings_in_effect_variants)
    filters = [{"defaults": True}]
    params = list(it.product(filters, settings_in_effect_suite))
    failed = self.run_generated_testcases("Ble advertisement settings in effect test",
                                          self._magic,
                                          params)
    if failed:
      return False
    return True

  def test_filters_suite(self):
    valid_filter_suit = self._get_combinations(self.valid_filter_variants)
    settings = [
      {'mode': AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value}]
    params = list(it.product(valid_filter_suit, settings))
    failed = self.run_generated_testcases("Ble advertisement filters suite in effect test",
                                          self._magic,
                                          params)
    if failed:
      return False
    return True

  def test_valid_filters(self):
    settings = [
      {'mode': AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value}]
    params = list(it.product(self.valid_filter_suite, settings))
    failed = self.run_generated_testcases("Ble advertisement filters in effect test",
                                          self._magic,
                                          params)
    if failed:
      return False
    return True

  def test_multi_manufacturer_specific_data(self):
    settings = [
      {'mode': AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value}]
    multi = self._get_combinations(self.multi_manufacturer_specific_data_suite)
    params = list(it.product(multi,
                             settings))
    self.log.debug(pprint.pformat(params))
    failed = self.run_generated_testcases("Ble advertisement filters in effect test",
                                          self._magic,
                                          params)
    if failed:
      return True
    return False