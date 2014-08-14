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
Test script for functional Ble Scan tests.
"""

import pprint
from queue import Empty

from test_utils.ble_advertise_test_utils import *
from test_utils.blescan_api_helper import *
from base_test import BaseTestClass
from test_utils.BleEnum import *


class BleAdvertiseTest(BaseTestClass):
    TAG = "BleFunctionalAdvertiseTest"
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

    def verify_advertise_data_attributes(self, input, droid):
        if "service_uuids" in input.keys():
            self.log.info("taco")
        else:
            self.log.info("no taco")
        return True

    def test_derp(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        input = {
            "service_uuids": [],
            "service_data_uuid": None,
            "manufacturer_id": -1,
            "include_tx_power_level": False,
            "include_device_name": False,
        }
        return self.verify_advertise_data_attributes(input, droid)

    def test_advertise_settings_defaults(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        self.log.debug("Step 2: Build advertisement settings.")
        advertise_settings = build_advertisesettings(droid)
        self.log.debug("Step 3: Get all default values.")
        advertise_mode = droid.getAdvertisementSettingsMode(advertise_settings)
        tx_power_level = droid.getAdvertisementSettingsTxPowerLevel(
            advertise_settings)
        is_connectable = droid.getAdvertisementSettingsIsConnectable(
            advertise_settings)

        expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
        expected_tx_power_level = AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value
        expected_is_connectable = True
        self.log.debug("Step 4: Verify all defaults match expected values.")
        if advertise_mode != expected_advertise_mode:
            test_result = False
            self.log.debug("Expected advertise mode: " + str(
                expected_advertise_mode) + ", found advertise mode: " + str(
                advertise_mode))
        if tx_power_level != expected_tx_power_level:
            test_result = False
            self.log.debug("Expected tx power level: " + str(
                expected_tx_power_level)
                           + ", found advertise tx power level: " + str(
                expected_tx_power_level))
        if expected_is_connectable != is_connectable:
            test_result = False
            self.log.debug("Expected is connectable: " + str(
                expected_is_connectable)
                           + ", found advertise is connectable: " + str(
                is_connectable))
        if not test_result:
            self.log.debug("Some values didn't match the defaults.")
        else:
            self.log.debug("All default values passed.")
        return test_result

    def test_advertise_data_defaults(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        self.log.debug("Step 2: Build advertisement data.")
        advertise_data = build_advertisedata(droid)
        self.log.debug("Step 3: Get all default values.")
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
            self.log.debug("Expected advertise service uuids: " + str(
                expected_service_uuids)
                           + ", found advertise service uuids: " + str(
                service_uuids))
        if include_tx_power_level != expected_include_tx_power_level:
            test_result = False
            self.log.debug("Expected advertise include tx power level: " + str(
                expected_include_tx_power_level)
                           + ", found advertise include tx power level: "
                           + str(include_tx_power_level))
        if include_device_name != expected_include_device_name:
            test_result = False
            self.log.debug("Expected advertise include tx power level: " + str(
                expected_include_device_name)
                           + ", found advertise include tx power level: " + str(
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
            "Step 2: Set the advertise settings object's value to " + str(
                expected_advertise_mode))
        return verify_advertise_settings_advertise_mode(self, droid,
                                                        expected_advertise_mode)

    def test_advertise_settings_set_advertise_mode_low_power(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value
        self.log.debug(
            "Step 2: Set the advertise settings object's value to " + str(
                expected_advertise_mode))
        return verify_advertise_settings_advertise_mode(self, droid,
                                                        expected_advertise_mode)

    def test_advertise_settings_set_advertise_mode_low_latency(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_advertise_mode = AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value
        self.log.debug(
            "Step 2: Set the advertise settings object's value to " + str(
                expected_advertise_mode))
        return verify_advertise_settings_advertise_mode(self, droid,
                                                        expected_advertise_mode)

    def test_advertise_settings_set_invalid_advertise_mode(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_advertise_mode = -1
        self.log.debug("Step 2: Set the advertise mode to -1")
        return verify_invalid_advertise_settings_advertise_mode(self, droid,
                                                                expected_advertise_mode)

    def test_advertise_settings_set_advertise_tx_power_level_high(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_advertise_tx_power = (AdvertiseSettingsAdvertiseTxPower
                                       .ADVERTISE_TX_POWER_HIGH.value)
        self.log.debug(
            "Step 2: Set the advertise settings object's value to "
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
            "Step 2: Set the advertise settings object's value to "
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
            "Step 2: Set the advertise settings object's value to "
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
            "Step 2: Set the advertise settings object's value to "
            + str(expected_advertise_tx_power))
        return verify_advertise_settings_tx_power_level(self, droid,
                                                        expected_advertise_tx_power)

    def test_advertise_settings_set_invalid_advertise_tx_power_level(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_advertise_tx_power = -1
        self.log.debug("Step 2: Set the advertise mode to -1")
        return verify_invalid_advertise_settings_tx_power_level(self, droid,
                                                                expected_advertise_tx_power)

    def test_advertise_settings_set_is_connectable_true(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_is_connectable = True
        self.log.debug(
            "Step 2: Set the advertise settings object's value to " + str(
                expected_is_connectable))
        return verify_advertise_settings_is_connectable(self, droid,
                                                        expected_is_connectable)

    def test_advertise_settings_set_is_connectable_false(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_is_connectable = False
        self.log.debug(
            "Step 2: Set the advertise settings object's value to " + str(
                expected_is_connectable))
        return verify_advertise_settings_is_connectable(self, droid,
                                                        expected_is_connectable)

    def test_advertise_data_set_service_uuids_empty(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_service_uuids = []
        self.log.debug(
            "Step 2: Set the advertise data object's value to " + str(
                expected_service_uuids))
        return verify_advertise_data_service_uuids(self, droid,
                                                   expected_service_uuids)

    def test_advertise_data_set_service_uuids_single(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_service_uuids = ["00000000-0000-1000-8000-00805f9b34fb"]
        self.log.debug(
            "Step 2: Set the advertise data object's value to " + str(
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
            "Step 2: Set the advertise data object's value to " + str(
                expected_service_uuids))
        return verify_advertise_data_service_uuids(self, droid,
                                                   expected_service_uuids)

    def test_advertise_data_set_service_uuids_invalid_uuid(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_service_uuids = ["0"]
        self.log.debug(
            "Step 2: Set the advertise data service uuids to " + str(
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
            "Step 2: Set the advertise data object's service data uuid to: " + str(
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
            "Step 2: Set the advertise data object's service data uuid to: " + str(
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
            "Step 2: Set the advertise data object's service data uuid to: " + str(
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
            "Step 2: Set the advertise data object's service data manufacturer id: " + str(
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
            "Step 2: Set the advertise data object's service data manufacturer id: " + str(
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
            "Step 2: Set the advertise data object's service data manufacturer id: " + str(
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
            "Step 2: Set the advertise data object's service data manufacturer id: " + str(
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
            "Step 2: Set the advertise data object's include tx power level: " + str(
                expected_include_tx_power_level))
        return verify_advertise_data_include_tx_power_level(self, droid,
                                                            expected_include_tx_power_level)

    def test_advertise_data_set_include_tx_power_level_false(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_include_tx_power_level = False
        self.log.debug(
            "Step 2: Set the advertise data object's include tx power level: " + str(
                expected_include_tx_power_level))
        return verify_advertise_data_include_tx_power_level(self, droid,
                                                            expected_include_tx_power_level)

    def test_advertise_data_set_include_device_name_true(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_include_device_name = True
        self.log.debug(
            "Step 2: Set the advertise data object's include device name: " + str(
                expected_include_device_name))
        return verify_advertise_data_include_device_name(self, droid,
                                                         expected_include_device_name)

    def test_advertise_data_set_include_device_name_false(self):
        self.log.debug("Step 1: Setup environment.")
        test_result = True
        droid = self.droid
        expected_include_device_name = False
        self.log.debug(
            "Step 2: Set the advertise data object's include device name: " + str(
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
        droid.setAdvertiseDataSetServiceUuids(["0000110A-0000-1000-8000-00805F9B34FB"])
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

        print("now advertising")
        import time

        time.sleep(800)
        return True
