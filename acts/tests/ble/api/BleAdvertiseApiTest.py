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
Test script to exercise Ble Advertisement Api's. This exercises all getters and
setters. This is important since there is a builder object that is immutable
after you set all attributes of each object. If this test suite doesn't pass,
then other test suites utilising Ble Advertisements will also fail.
"""

# TODO: Refactor to work like BleScanApiTest. Add proper documentation.

import pprint
from queue import Empty
import time

from base_test import BaseTestClass
from test_utils.BleEnum import *
from test_utils.ble_advertise_utils import *
from test_utils.ble_helper_functions import *


class BleAdvertiseApiTest(BaseTestClass):
  TAG = "BleAdvertiseApiTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None

  def __init__(self, android_devices):
    BaseTestClass.__init__(self, self.TAG, android_devices)
    self.tests = (
      "test_advertise_settings_defaults",
      "test_advertise_data_defaults",
      "test_advertise_settings_set_advertise_mode_balanced",
      "test_advertise_settings_set_advertise_mode_low_power",
      "test_advertise_settings_set_advertise_mode_low_latency",
      "test_advertise_settings_set_invalid_advertise_mode",
      "test_advertise_settings_set_advertise_tx_power_level_high",
      "test_advertise_settings_set_advertise_tx_power_level_medium",
      "test_advertise_settings_set_advertise_tx_power_level_low",
      "test_advertise_settings_set_advertise_tx_power_level_ultra_low",
      "test_advertise_settings_set_invalid_advertise_tx_power_level",
      "test_advertise_settings_set_is_connectable_true",
      "test_advertise_settings_set_is_connectable_false",
      "test_advertise_data_set_service_uuids_empty",
      "test_advertise_data_set_service_uuids_single",
      "test_advertise_data_set_service_uuids_multiple",
      "test_advertise_data_set_service_uuids_invalid_uuid",
      "test_advertise_data_set_service_data",
      "test_advertise_data_set_service_data_invalid_service_data",
      "test_advertise_data_set_service_data_invalid_service_data_uuid",
      "test_advertise_data_set_manufacturer_id",
      "test_advertise_data_set_manufacturer_id_invalid_manufacturer_id",
      "test_advertise_data_set_manufacturer_id_invalid_manufacturer_specific_data",
      "test_advertise_data_set_manufacturer_id_max",
      "test_advertise_data_set_include_tx_power_level_true",
      "test_advertise_data_set_include_tx_power_level_false",
      "test_advertise_data_set_include_device_name_true",
      "test_advertise_data_set_include_device_name_false",
    )

  def test_advertise_settings_defaults(self):
    """
    Tests the default advertisement settings. This builder object should have a
    proper "get" expectation for each attribute of the builder object once it is
    built.
    Steps:
    1. Build a new advertise settings object.
    2. Get the attributes of the advertise settings object.
    3. Compare the attributes found against the attributes expected.

    :return: test_result: bool
    """
    test_result = True
    droid = self.droid
    advertise_settings = build_advertisesettings(droid)
    advertise_mode = droid.getAdvertisementSettingsMode(advertise_settings)
    tx_power_level = droid.getAdvertisementSettingsTxPowerLevel(
      advertise_settings)
    is_connectable = droid.getAdvertisementSettingsIsConnectable(
      advertise_settings)

    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
    expected_tx_power_level = AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value
    expected_is_connectable = True
    if advertise_mode != expected_advertise_mode:
      test_result = False
      self.log.debug("Expected filtering mode: " + str(
        expected_advertise_mode) + ", found filtering mode: " + str(
        advertise_mode))
    if tx_power_level != expected_tx_power_level:
      test_result = False
      self.log.debug("Expected tx power level: " + str(
        expected_tx_power_level)
                     + ", found filtering tx power level: " + str(
        expected_tx_power_level))
    if expected_is_connectable != is_connectable:
      test_result = False
      self.log.debug("Expected is connectable: " + str(
        expected_is_connectable)
                     + ", found filtering is connectable: " + str(
        is_connectable))
    return test_result

  def test_advertise_data_defaults(self):
    """
    Tests the default advertisement data. This builder object should have a
    proper "get" expectation for each attribute of the builder object once it is
    built.
    Steps:
    1. Build a new advertise data object.
    2. Get the attributes of the advertise settings object.
    3. Compare the attributes found against the attributes expected.

    :return: test_result: bool
    """
    test_result = True
    droid = self.droid
    advertise_data = build_advertisedata(droid)
    service_uuids = droid.getAdvertiseDataServiceUuids(advertise_data)
    include_tx_power_level = droid.getAdvertiseDataIncludeTxPowerLevel(
      advertise_data)
    include_device_name = droid.getAdvertiseDataIncludeDeviceName(
      advertise_data)

    expected_service_uuids = []
    expected_service_data_uuid = None
    expected_manufacturer_id = -1
    expected_include_tx_power_level = False
    expected_include_device_name = False
    self.log.debug("Step 4: Verify all defaults match expected values.")
    if service_uuids != expected_service_uuids:
      test_result = False
      self.log.debug("Expected filtering service uuids: " + str(
        expected_service_uuids)
                     + ", found filtering service uuids: " + str(
        service_uuids))
    if include_tx_power_level != expected_include_tx_power_level:
      test_result = False
      self.log.debug("Expected filtering include tx power level: " + str(
        expected_include_tx_power_level)
                     + ", found filtering include tx power level: "
                     + str(include_tx_power_level))
    if include_device_name != expected_include_device_name:
      test_result = False
      self.log.debug("Expected filtering include tx power level: " + str(
        expected_include_device_name)
                     + ", found filtering include tx power level: " + str(
        include_device_name))
    if not test_result:
      self.log.debug("Some values didn't match the defaults.")
    else:
      self.log.debug("All default values passed.")
    return test_result

  def test_advertise_settings_set_advertise_mode_balanced(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_advertise_mode))
    return verify_advertise_settings_advertise_mode(self, droid,
                                                    expected_advertise_mode)

  def test_advertise_settings_set_advertise_mode_low_power(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_advertise_mode))
    return verify_advertise_settings_advertise_mode(self, droid,
                                                    expected_advertise_mode)

  def test_advertise_settings_set_advertise_mode_low_latency(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_advertise_mode))
    return verify_advertise_settings_advertise_mode(self, droid,
                                                    expected_advertise_mode)

  def test_advertise_settings_set_invalid_advertise_mode(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = -1
    self.log.debug("Step 2: Set the filtering mode to -1")
    return verify_invalid_advertise_settings_advertise_mode(self, droid,
                                                            expected_advertise_mode)

  def test_advertise_settings_set_advertise_tx_power_level_high(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = (AdvertiseSettingsAdvertiseTxPower
                                   .ADVERTISE_TX_POWER_HIGH.value)
    self.log.debug(
      "Step 2: Set the filtering settings object's value to "
      + str(expected_advertise_tx_power))
    return verify_advertise_settings_tx_power_level(self, droid,
                                                    expected_advertise_tx_power)

  def test_advertise_settings_set_advertise_tx_power_level_medium(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = (AdvertiseSettingsAdvertiseTxPower
                                   .ADVERTISE_TX_POWER_MEDIUM.value)
    self.log.debug(
      "Step 2: Set the filtering settings object's value to "
      + str(expected_advertise_tx_power))
    return verify_advertise_settings_tx_power_level(self, droid,
                                                    expected_advertise_tx_power)

  def test_advertise_settings_set_advertise_tx_power_level_low(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = (AdvertiseSettingsAdvertiseTxPower
                                   .ADVERTISE_TX_POWER_LOW.value)
    self.log.debug(
      "Step 2: Set the filtering settings object's value to "
      + str(expected_advertise_tx_power))
    return verify_advertise_settings_tx_power_level(self, droid,
                                                    expected_advertise_tx_power)


  def test_advertise_settings_set_advertise_tx_power_level_ultra_low(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = (AdvertiseSettingsAdvertiseTxPower
                                   .ADVERTISE_TX_POWER_ULTRA_LOW.value)
    self.log.debug(
      "Step 2: Set the filtering settings object's value to "
      + str(expected_advertise_tx_power))
    return verify_advertise_settings_tx_power_level(self, droid,
                                                    expected_advertise_tx_power)

  def test_advertise_settings_set_invalid_advertise_tx_power_level(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = -1
    self.log.debug("Step 2: Set the filtering mode to -1")
    return verify_invalid_advertise_settings_tx_power_level(self, droid,
                                                            expected_advertise_tx_power)

  def test_advertise_settings_set_is_connectable_true(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_is_connectable = True
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_is_connectable))
    return verify_advertise_settings_is_connectable(self, droid,
                                                    expected_is_connectable)

  def test_advertise_settings_set_is_connectable_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_is_connectable = False
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_is_connectable))
    return verify_advertise_settings_is_connectable(self, droid,
                                                    expected_is_connectable)

  def test_advertise_data_set_service_uuids_empty(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = []
    self.log.debug(
      "Step 2: Set the filtering data object's value to " + str(
        expected_service_uuids))
    return verify_advertise_data_service_uuids(self, droid,
                                               expected_service_uuids)

  def test_advertise_data_set_service_uuids_single(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = ["00000000-0000-1000-8000-00805f9b34fb"]
    self.log.debug(
      "Step 2: Set the filtering data object's value to " + str(
        expected_service_uuids))
    return verify_advertise_data_service_uuids(self, droid,
                                               expected_service_uuids)

  def test_advertise_data_set_service_uuids_multiple(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = ["00000000-0000-1000-8000-00805f9b34fb",
                              "00000000-0000-1000-8000-00805f9b34fb"]
    self.log.debug(
      "Step 2: Set the filtering data object's value to " + str(
        expected_service_uuids))
    return verify_advertise_data_service_uuids(self, droid,
                                               expected_service_uuids)

  def test_advertise_data_set_service_uuids_invalid_uuid(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = ["0"]
    self.log.debug(
      "Step 2: Set the filtering data service uuids to " + str(
        expected_service_uuids))
    return verify_invalid_advertise_data_service_uuids(self, droid,
                                                       expected_service_uuids)

  def test_advertise_data_set_service_data(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_data_uuid = "00000000-0000-1000-8000-00805f9b34fb"
    expected_service_data = "1,2,3"
    self.log.debug(
      "Step 2: Set the filtering data object's service data uuid to: " + str(
        expected_service_data_uuid) + ", service data: " + str(
        expected_service_data))
    return verify_advertise_data_service_data(self, droid,
                                              expected_service_data_uuid,
                                              expected_service_data)

  def test_advertise_data_set_service_data_invalid_service_data(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_data_uuid = "00000000-0000-1000-8000-00805f9b34fb"
    expected_service_data = "helloworld"
    self.log.debug(
      "Step 2: Set the filtering data object's service data uuid to: " + str(
        expected_service_data_uuid) + ", service data: " + str(
        expected_service_data))
    return verify_invalid_advertise_data_service_data(self, droid,
                                                      expected_service_data_uuid,
                                                      expected_service_data)

  def test_advertise_data_set_service_data_invalid_service_data_uuid(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_data_uuid = "0"
    expected_service_data = "1,2,3"
    self.log.debug(
      "Step 2: Set the filtering data object's service data uuid to: " + str(
        expected_service_data_uuid) + ", service data: " + str(
        expected_service_data))
    return verify_invalid_advertise_data_service_data(self, droid,
                                                      expected_service_data_uuid,
                                                      expected_service_data)

  def test_advertise_data_set_manufacturer_id(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_manufacturer_id = 0
    expected_manufacturer_specific_data = "1,2,3"
    self.log.debug(
      "Step 2: Set the filtering data object's service data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: "
      + str(expected_manufacturer_specific_data))
    return verify_advertise_data_manufacturer_id(self, droid,
                                                 expected_manufacturer_id,
                                                 expected_manufacturer_specific_data)

  def test_advertise_data_set_manufacturer_id_invalid_manufacturer_id(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_manufacturer_id = -1
    expected_manufacturer_specific_data = "1,2,3"
    self.log.debug(
      "Step 2: Set the filtering data object's service data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: "
      + str(expected_manufacturer_specific_data))
    return verify_invalid_advertise_data_manufacturer_id(self, droid,
                                                         expected_manufacturer_id,
                                                         expected_manufacturer_specific_data)

  def test_advertise_data_set_manufacturer_id_invalid_manufacturer_specific_data(
    self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_manufacturer_id = 0
    expected_manufacturer_specific_data = "helloworld"
    self.log.debug(
      "Step 2: Set the filtering data object's service data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: "
      + str(expected_manufacturer_specific_data))
    return verify_invalid_advertise_data_manufacturer_id(self, droid,
                                                         expected_manufacturer_id,
                                                         expected_manufacturer_specific_data)


  def test_advertise_data_set_manufacturer_id_max(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_manufacturer_id = JavaInteger.MAX.value
    expected_manufacturer_specific_data = "1,2,3"
    self.log.debug(
      "Step 2: Set the filtering data object's service data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: "
      + str(expected_manufacturer_specific_data))
    return verify_advertise_data_manufacturer_id(self, droid,
                                                 expected_manufacturer_id,
                                                 expected_manufacturer_specific_data)

  def test_advertise_data_set_include_tx_power_level_true(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_tx_power_level = True
    self.log.debug(
      "Step 2: Set the filtering data object's include tx power level: " + str(
        expected_include_tx_power_level))
    return verify_advertise_data_include_tx_power_level(self, droid,
                                                        expected_include_tx_power_level)

  def test_advertise_data_set_include_tx_power_level_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_tx_power_level = False
    self.log.debug(
      "Step 2: Set the filtering data object's include tx power level: " + str(
        expected_include_tx_power_level))
    return verify_advertise_data_include_tx_power_level(self, droid,
                                                        expected_include_tx_power_level)

  def test_advertise_data_set_include_device_name_true(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_device_name = True
    self.log.debug(
      "Step 2: Set the filtering data object's include device name: " + str(
        expected_include_device_name))
    return verify_advertise_data_include_device_name(self, droid,
                                                     expected_include_device_name)

  def test_advertise_data_set_include_device_name_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_device_name = False
    self.log.debug(
      "Step 2: Set the filtering data object's include device name: " + str(
        expected_include_device_name))
    return verify_advertise_data_include_device_name(self, droid,
                                                     expected_include_device_name)

  def test_quick_advertise(self):
    droids = self.android_devices
    d0 = droids[0]
    d1 = droids[1]

    droid = self.droid

    self.log.debug("data manu")
    droid.addAdvertiseDataManufacturerId(1, "4,0,54")
    self.log.debug("service uuid")
    droid.setAdvertiseDataSetServiceUuids(
      ["0000110A-0000-1000-8000-00805F9B34FB"])
    self.log.debug("data manu")
    droid.setAdvertiseDataIncludeTxPowerLevel(True)
    droid.setAdvertiseDataIncludeDeviceName(True)
    droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value)
    droid.setAdvertisementSettingsTxPowerLevel(
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value)
    droid.setAdvertisementSettingsIsConnectable(True)
    droid.setAdvertiseDataIncludeDeviceName(True)
    droid.setAdvertiseDataIncludeTxPowerLevel(True)
    data, settings, callback = generate_ble_advertise_objects(droid)
    droid.startBleAdvertising(callback, data, settings)
    time.sleep(800)
    return True
