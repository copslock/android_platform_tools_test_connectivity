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
import time

from android import SL4AAPIError
from base_test import BaseTestClass
from test_utils.BleEnum import *
from test_utils.ble_test_utils import *

"""
Test script to exercise Ble Advertisement Api's. This exercises all getters and
setters. This is important since there is a builder object that is immutable
after you set all attributes of each object. If this test suite doesn't pass,
then other test suites utilising Ble Advertisements will also fail.
"""

# TODO: Refactor to work like BleScanApiTest. Add proper documentation.

class BleAdvertiseVerificationError(Exception):
  """Error in fetsching BleScanner Advertise result."""


class BleAdvertiseApiTest(BaseTestClass):
  TAG = "BleAdvertiseApiTest"
  log_path = "".join([BaseTestClass.log_path, TAG, '/'])
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
      "test_advertisement_greater_than_31_bytes",
    )

  def setup_class(self):
    setup_result = True
    for ad in self.android_devices:
      droid, _ = ad.get_droid()
      setup_result = droid.bluetoothSetHciSnoopLog(True)
      if not setup_result:
        return setup_result
    return setup_result

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
    advertise_settings = droid.buildAdvertisementSettings()
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
      self.log.debug(" ".join(["Expected filtering mode:", str(expected_advertise_mode),
                               ", found filtering mode:", str(advertise_mode)]))
    if tx_power_level != expected_tx_power_level:
      test_result = False
      self.log.debug(" ".join(["Expected tx power level:", str(expected_tx_power_level),
                               ", found filtering tx power level: ", str(expected_tx_power_level)]))
    if expected_is_connectable != is_connectable:
      test_result = False
      self.log.debug(" ".join(["Expected is connectable:", str(expected_is_connectable),
                               ", found filtering is connectable: ", str(is_connectable)]))
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
    advertise_data = droid.buildAdvertiseData()
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
      self.log.debug(" ".join(["Expected filtering service uuids:",
                               expected_service_uuids, ", found filtering service uuids:",
                               str(service_uuids)]))
    if include_tx_power_level != expected_include_tx_power_level:
      test_result = False
      self.log.debug(" ".join(["Expected filtering include tx power level:",
                               str(expected_include_tx_power_level),
                               ", found filtering include tx power level:",
                               str(include_tx_power_level)]))
    if include_device_name != expected_include_device_name:
      test_result = False
      self.log.debug(" ".join(["Expected filtering include tx power level:",
                               str(expected_include_device_name),
                               ", found filtering include tx power level:",
                               str(include_device_name)]))
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
    return self.verify_advertise_settings_advertise_mode(droid,
                                                         expected_advertise_mode)

  def test_advertise_settings_set_advertise_mode_low_power(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_advertise_mode))
    return self.verify_advertise_settings_advertise_mode(droid,
                                                         expected_advertise_mode)

  def test_advertise_settings_set_advertise_mode_low_latency(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_advertise_mode))
    return self.verify_advertise_settings_advertise_mode(droid,
                                                         expected_advertise_mode)

  def test_advertise_settings_set_invalid_advertise_mode(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_mode = -1
    self.log.debug("Step 2: Set the filtering mode to -1")
    return self.verify_invalid_advertise_settings_advertise_mode(droid,
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
    return self.verify_advertise_settings_tx_power_level(droid,
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
    return self.verify_advertise_settings_tx_power_level(droid,
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
    return self.verify_advertise_settings_tx_power_level(droid,
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
    return self.verify_advertise_settings_tx_power_level(droid,
                                                         expected_advertise_tx_power)

  def test_advertise_settings_set_invalid_advertise_tx_power_level(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_advertise_tx_power = -1
    self.log.debug("Step 2: Set the filtering mode to -1")
    return self.verify_invalid_advertise_settings_tx_power_level(droid,
                                                                 expected_advertise_tx_power)

  def test_advertise_settings_set_is_connectable_true(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_is_connectable = True
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_is_connectable))
    return self.verify_advertise_settings_is_connectable(droid,
                                                         expected_is_connectable)

  def test_advertise_settings_set_is_connectable_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_is_connectable = False
    self.log.debug(
      "Step 2: Set the filtering settings object's value to " + str(
        expected_is_connectable))
    return self.verify_advertise_settings_is_connectable(droid,
                                                         expected_is_connectable)

  def test_advertise_data_set_service_uuids_empty(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = []
    self.log.debug(
      "Step 2: Set the filtering data object's value to " + str(
        expected_service_uuids))
    return self.verify_advertise_data_service_uuids(droid,
                                                    expected_service_uuids)

  def test_advertise_data_set_service_uuids_single(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = ["00000000-0000-1000-8000-00805f9b34fb"]
    self.log.debug(
      "Step 2: Set the filtering data object's value to " + str(
        expected_service_uuids))
    return self.verify_advertise_data_service_uuids(droid,
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
    return self.verify_advertise_data_service_uuids(droid,
                                                    expected_service_uuids)

  def test_advertise_data_set_service_uuids_invalid_uuid(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_service_uuids = ["0"]
    self.log.debug(
      "Step 2: Set the filtering data service uuids to " + str(
        expected_service_uuids))
    return self.verify_invalid_advertise_data_service_uuids(droid,
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
    return self.verify_advertise_data_service_data(droid,
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
    return self.verify_invalid_advertise_data_service_data(droid,
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
    return self.verify_invalid_advertise_data_service_data(droid,
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
    return self.verify_advertise_data_manufacturer_id(droid,
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
    return self.verify_invalid_advertise_data_manufacturer_id(droid,
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
    return self.verify_invalid_advertise_data_manufacturer_id(droid,
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
    return self.verify_advertise_data_manufacturer_id(droid,
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
    return self.verify_advertise_data_include_tx_power_level(droid,
                                                             expected_include_tx_power_level)

  def test_advertise_data_set_include_tx_power_level_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_tx_power_level = False
    self.log.debug(
      "Step 2: Set the filtering data object's include tx power level: " + str(
        expected_include_tx_power_level))
    return self.verify_advertise_data_include_tx_power_level(droid,
                                                             expected_include_tx_power_level)

  def test_advertise_data_set_include_device_name_true(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_device_name = True
    self.log.debug(
      "Step 2: Set the filtering data object's include device name: " + str(
        expected_include_device_name))
    return self.verify_advertise_data_include_device_name(droid,
                                                          expected_include_device_name)

  def test_advertise_data_set_include_device_name_false(self):
    self.log.debug("Step 1: Setup environment.")
    test_result = True
    droid = self.droid
    expected_include_device_name = False
    self.log.debug(
      "Step 2: Set the filtering data object's include device name: " + str(
        expected_include_device_name))
    return self.verify_advertise_data_include_device_name(droid,
                                                          expected_include_device_name)

  def test_advertisement_greater_than_31_bytes(self):
    test_result = True
    droid = self.droid
    droid.setAdvertiseDataIncludeDeviceName(True)
    droid.setAdvertiseDataIncludeTxPowerLevel(True)
    droid.addAdvertiseDataManufacturerId(1,"14,0,54,0,0,0,0,0")
    droid.addAdvertiseDataServiceData("0000110D-0000-1000-8000-00805F9B34FB", "16,22,11")
    advertise_callback, advertise_data, advertise_settings = generate_ble_advertise_objects(droid)
    try:
      droid.startBleAdvertising(advertise_callback, advertise_data,
                                advertise_settings)
      return False
    except SL4AAPIError:
      self.log.info("Failed as expected.")
    return test_result

  # TODO: in code refactor, remove all verify helper functions.
  def verify_advertise_settings_advertise_mode(self, droid, expected_advertise_mode):
    try:
      droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = droid.buildAdvertisementSettings()
    self.log.debug("Step 4: Get the filtering setting's filtering mode.")
    advertise_mode = droid.getAdvertisementSettingsMode(settings_index)
    if expected_advertise_mode is not advertise_mode:
      self.log.debug("Expected value: " + str(expected_advertise_mode)
                     + ", Actual value: " + str(advertise_mode))
      return False
    self.log.debug("Advertise Setting's filtering mode " + str(expected_advertise_mode)
                   + "  value test Passed.")
    return True

  def verify_advertise_settings_tx_power_level(self, droid, expected_advertise_tx_power):
    try:
      droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = droid.buildAdvertisementSettings()
    self.log.debug("Step 4: Get the filtering setting's tx power level.")
    advertise_tx_power_level = droid.getAdvertisementSettingsTxPowerLevel(settings_index)
    if expected_advertise_tx_power is not advertise_tx_power_level:
      self.log.debug("Expected value: " + str(expected_advertise_tx_power)
                     + ", Actual value: " + str(advertise_tx_power_level))
      return False
    self.log.debug("Advertise Setting's tx power level " + str(expected_advertise_tx_power)
                   + "  value test Passed.")
    return True

  def verify_advertise_settings_is_connectable(self, droid, expected_is_connectable):
    try:
      droid.setAdvertisementSettingsIsConnectable(expected_is_connectable)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = droid.buildAdvertisementSettings()
    self.log.debug("Step 4: Get the filtering setting's is connectable value.")
    is_connectable = droid.getAdvertisementSettingsIsConnectable(settings_index)
    if expected_is_connectable is not is_connectable:
      self.log.debug("Expected value: " + str(expected_is_connectable)
                     + ", Actual value: " + str(is_connectable))
      return False
    self.log.debug("Advertise Setting's is connectable " + str(expected_is_connectable)
                   + "  value test Passed.")
    return True

  def verify_advertise_data_service_uuids(self, droid, expected_service_uuids):
    try:
      droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering data object's index.")
    data_index = droid.buildAdvertiseData()
    self.log.debug("Step 4: Get the filtering data's service uuids.")
    service_uuids = droid.getAdvertiseDataServiceUuids(data_index)
    if expected_service_uuids != service_uuids:
      self.log.debug("Expected value: " + str(expected_service_uuids)
                     + ", Actual value: " + str(service_uuids))
      return False
    self.log.debug("Advertise Data's service uuids " + str(expected_service_uuids)
                   + "  value test Passed.")
    return True

  def verify_advertise_data_service_data(self, droid, expected_service_data_uuid,
                                         expected_service_data):
    try:
      droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering data object's index.")
    data_index = droid.buildAdvertiseData()
    self.log.debug("Step 5: Get the filtering data's service data.")
    service_data = droid.getAdvertiseDataServiceData(data_index, expected_service_data_uuid)
    if expected_service_data != service_data:
      self.log.debug("Expected value: " + str(expected_service_data)
                     + ", Actual value: " + str(service_data))
      return False
    self.log.debug("Advertise Data's service data uuid: " + str(
      expected_service_data_uuid) + ", service data: "
                   + str(expected_service_data)
                   + "  value test Passed.")
    return True

  def verify_advertise_data_manufacturer_id(self, droid, expected_manufacturer_id,
                                            expected_manufacturer_specific_data):
    try:
      droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                           expected_manufacturer_specific_data)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering data object's index.")
    data_index = droid.buildAdvertiseData()
    self.log.debug("Step 5: Get the filtering data's manufacturer specific data.")
    manufacturer_specific_data = droid.getAdvertiseDataManufacturerSpecificData(data_index,
                                                                                expected_manufacturer_id)
    if expected_manufacturer_specific_data != manufacturer_specific_data:
      self.log.debug("Expected value: " + str(expected_manufacturer_specific_data)
                     + ", Actual value: " + str(manufacturer_specific_data))
      return False
    self.log.debug("Advertise Data's manufacturer id: " + str(
      expected_manufacturer_id) + ", manufacturer's specific data: " + str(
      expected_manufacturer_specific_data)
                   + "  value test Passed.")
    return True

  def verify_advertise_data_include_tx_power_level(self, droid,
                                                   expected_include_tx_power_level):
    try:
      droid.setAdvertiseDataIncludeTxPowerLevel(expected_include_tx_power_level)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering settings object's index.")
    data_index = droid.buildAdvertiseData()
    self.log.debug("Step 4: Get the filtering data's include tx power level.")
    include_tx_power_level = droid.getAdvertiseDataIncludeTxPowerLevel(data_index)
    if expected_include_tx_power_level is not include_tx_power_level:
      self.log.debug("Expected value: " + str(expected_include_tx_power_level)
                     + ", Actual value: " + str(include_tx_power_level))
      return False
    self.log.debug(
      "Advertise Setting's include tx power level " + str(expected_include_tx_power_level)
      + "  value test Passed.")
    return True

  def verify_advertise_data_include_device_name(self, droid,
                                                expected_include_device_name):
    try:
      droid.setAdvertiseDataIncludeDeviceName(expected_include_device_name)
    except BleAdvertiseVerificationError as error:
      self.log.debug(str(error))
      return False
    self.log.debug("Step 3: Get a filtering settings object's index.")
    data_index = droid.buildAdvertiseData()
    self.log.debug("Step 4: Get the filtering data's include device name.")
    include_device_name = droid.getAdvertiseDataIncludeDeviceName(data_index)
    if expected_include_device_name is not include_device_name:
      self.log.debug("Expected value: " + str(expected_include_device_name)
                     + ", Actual value: " + str(include_device_name))
      return False
    self.log.debug(
      "Advertise Setting's include device name " + str(expected_include_device_name)
      + "  value test Passed.")
    return True

  def verify_invalid_advertise_settings_advertise_mode(self, droid,
                                                       expected_advertise_mode):
    try:
      droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
      droid.buildAdvertisementSettings()
      self.log.debug("Set Advertise settings invalid filtering mode passed "
                     + " with input as " + str(expected_advertise_mode))
      return False
    except SL4AAPIError:
      self.log.debug("Set Advertise settings invalid filtering mode failed successfully"
                     + " with input as " + str(expected_advertise_mode))
      return True

  def verify_invalid_advertise_settings_tx_power_level(self, droid,
                                                       expected_advertise_tx_power):
    try:
      droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
      droid.buildAdvertisementSettings()
      self.log.debug("Set Advertise settings invalid tx power level "
                     + " with input as " + str(expected_advertise_tx_power))
      return False
    except SL4AAPIError:
      self.log.debug("Set Advertise settings invalid tx power level failed successfully"
                     + " with input as " + str(expected_advertise_tx_power))
      return True

  def verify_invalid_advertise_data_service_uuids(self, droid,
                                                  expected_service_uuids):
    try:
      droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
      droid.buildAdvertiseData()
      self.log.debug("Set Advertise Data service uuids "
                     + " with input as " + str(expected_service_uuids))
      return False
    except SL4AAPIError:
      self.log.debug("Set Advertise Data invalid service uuids failed successfully"
                     + " with input as " + str(expected_service_uuids))
      return True

  def verify_invalid_advertise_data_service_data(self, droid,
                                                 expected_service_data_uuid, expected_service_data):
    try:
      droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
      droid.buildAdvertiseData()
      self.log.debug("Set Advertise Data service data uuid: " + str(
        expected_service_data_uuid) + ", service data: " + str(expected_service_data))
      return False
    except SL4AAPIError:
      self.log.debug("Set Advertise Data service data uuid: " + str(
        expected_service_data_uuid) + ", service data: " + str(
        expected_service_data) + " failed successfully.")
      return True

  def verify_invalid_advertise_data_manufacturer_id(self, droid,
                                                    expected_manufacturer_id,
                                                    expected_manufacturer_specific_data):
    try:
      droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                           expected_manufacturer_specific_data)
      droid.buildAdvertiseData()
      self.log.debug("Set Advertise Data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: " + str(
        expected_manufacturer_specific_data))
      return False
    except SL4AAPIError:
      self.log.debug("Set Advertise Data manufacturer id: " + str(
        expected_manufacturer_id) + ", manufacturer specific data: " + str(
        expected_manufacturer_specific_data) + " failed successfully.")
      return True