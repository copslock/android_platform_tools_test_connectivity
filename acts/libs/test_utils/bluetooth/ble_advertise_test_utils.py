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

from test_utils.bluetooth.blescan_api_helper import *


class BleAdvertiseVerificationError(Exception):
    """Error in fetsching BleScanner Advertise result."""


def verify_advertise_settings_advertise_mode(testcase, droid, expected_advertise_mode):
    try:
        droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the filtering setting's filtering mode.")
    advertise_mode = droid.getAdvertisementSettingsMode(settings_index)
    if expected_advertise_mode is not advertise_mode:
        testcase.log.debug("Expected value: " + str(expected_advertise_mode)
                                + ", Actual value: " + str(advertise_mode))
        return False
    testcase.log.debug("Advertise Setting's filtering mode " + str(expected_advertise_mode)
                           + "  value test Passed.")
    return True


def verify_advertise_settings_tx_power_level(testcase, droid, expected_advertise_tx_power):
    try:
        droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the filtering setting's tx power level.")
    advertise_tx_power_level = droid.getAdvertisementSettingsTxPowerLevel(settings_index)
    if expected_advertise_tx_power is not advertise_tx_power_level:
        testcase.log.debug("Expected value: " + str(expected_advertise_tx_power)
                                + ", Actual value: " + str(advertise_tx_power_level))
        return False
    testcase.log.debug("Advertise Setting's tx power level " + str(expected_advertise_tx_power)
                           + "  value test Passed.")
    return True


def verify_advertise_settings_is_connectable(testcase, droid, expected_is_connectable):
    try:
        droid.setAdvertisementSettingsIsConnectable(expected_is_connectable)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the filtering setting's is connectable value.")
    is_connectable = droid.getAdvertisementSettingsIsConnectable(settings_index)
    if expected_is_connectable is not is_connectable:
        testcase.log.debug("Expected value: " + str(expected_is_connectable)
                                + ", Actual value: " + str(is_connectable))
        return False
    testcase.log.debug("Advertise Setting's is connectable " + str(expected_is_connectable)
                           + "  value test Passed.")
    return True


def verify_advertise_data_service_uuids(testcase, droid, expected_service_uuids):
    try:
        droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the filtering data's service uuids.")
    service_uuids = droid.getAdvertiseDataServiceUuids(data_index)
    if expected_service_uuids != service_uuids:
        testcase.log.debug("Expected value: " + str(expected_service_uuids)
                                + ", Actual value: " + str(service_uuids))
        return False
    testcase.log.debug("Advertise Data's service uuids " + str(expected_service_uuids)
                           + "  value test Passed.")
    return True


def verify_advertise_data_service_data(testcase, droid, expected_service_data_uuid,
                                       expected_service_data):
    try:
        droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 5: Get the filtering data's service data.")
    service_data = droid.getAdvertiseDataServiceData(data_index, expected_service_data_uuid)
    if expected_service_data != service_data:
        testcase.log.debug("Expected value: " + str(expected_service_data)
                                + ", Actual value: " + str(service_data))
        return False
    testcase.log.debug("Advertise Data's service data uuid: " + str(
                           expected_service_data_uuid) + ", service data: "
                           + str(expected_service_data)
                           + "  value test Passed.")
    return True


def verify_advertise_data_manufacturer_id(testcase, droid, expected_manufacturer_id,
                                          expected_manufacturer_specific_data):
    try:
        droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                             expected_manufacturer_specific_data)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 5: Get the filtering data's manufacturer specific data.")
    manufacturer_specific_data = droid.getAdvertiseDataManufacturerSpecificData(data_index, expected_manufacturer_id)
    if expected_manufacturer_specific_data != manufacturer_specific_data:
        testcase.log.debug("Expected value: " + str(expected_manufacturer_specific_data)
                                + ", Actual value: " + str(manufacturer_specific_data))
        return False
    testcase.log.debug("Advertise Data's manufacturer id: " + str(
                           expected_manufacturer_id) + ", manufacturer's specific data: " + str(
                           expected_manufacturer_specific_data)
                           + "  value test Passed.")
    return True


def verify_advertise_data_include_tx_power_level(testcase, droid, expected_include_tx_power_level):
    try:
        droid.setAdvertiseDataIncludeTxPowerLevel(expected_include_tx_power_level)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering settings object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the filtering data's include tx power level.")
    include_tx_power_level = droid.getAdvertiseDataIncludeTxPowerLevel(data_index)
    if expected_include_tx_power_level is not include_tx_power_level:
        testcase.log.debug("Expected value: " + str(expected_include_tx_power_level)
                                + ", Actual value: " + str(include_tx_power_level))
        return False
    testcase.log.debug(
        "Advertise Setting's include tx power level " + str(expected_include_tx_power_level)
        + "  value test Passed.")
    return True


def verify_advertise_data_include_device_name(testcase, droid, expected_include_device_name):
    try:
        droid.setAdvertiseDataIncludeDeviceName(expected_include_device_name)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a filtering settings object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the filtering data's include device name.")
    include_device_name = droid.getAdvertiseDataIncludeDeviceName(data_index)
    if expected_include_device_name is not include_device_name:
        testcase.log.debug("Expected value: " + str(expected_include_device_name)
                                + ", Actual value: " + str(include_device_name))
        return False
    testcase.log.debug(
        "Advertise Setting's include device name " + str(expected_include_device_name)
        + "  value test Passed.")
    return True


def verify_invalid_advertise_settings_advertise_mode(testcase, droid,
                                                     expected_advertise_mode):
    try:
        droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
        build_advertisesettings(droid)
        testcase.log.debug("Set Advertise settings invalid filtering mode passed "
                                + " with input as " + str(expected_advertise_mode))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise settings invalid filtering mode failed successfully"
                               + " with input as " + str(expected_advertise_mode))
        return True


def verify_invalid_advertise_settings_tx_power_level(testcase, droid,
                                                     expected_advertise_tx_power):
    try:
        droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
        build_advertisesettings(droid)
        testcase.log.debug("Set Advertise settings invalid tx power level "
                                + " with input as " + str(expected_advertise_tx_power))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise settings invalid tx power level failed successfully"
                               + " with input as " + str(expected_advertise_tx_power))
        return True


def verify_invalid_advertise_data_service_uuids(testcase, droid,
                                                expected_service_uuids):
    try:
        droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data service uuids "
                                + " with input as " + str(expected_service_uuids))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data invalid service uuids failed successfully"
                               + " with input as " + str(expected_service_uuids))
        return True


def verify_invalid_advertise_data_service_data(testcase, droid,
                                               expected_service_data_uuid, expected_service_data):
    try:
        droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data service data uuid: " + str(
            expected_service_data_uuid) + ", service data: " + str(expected_service_data))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data service data uuid: " + str(
                               expected_service_data_uuid) + ", service data: " + str(
                               expected_service_data) + " failed successfully.")
        return True


def verify_invalid_advertise_data_manufacturer_id(testcase, droid,
                                                  expected_manufacturer_id,
                                                  expected_manufacturer_specific_data):
    try:
        droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                             expected_manufacturer_specific_data)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data manufacturer id: " + str(
                                expected_manufacturer_id) + ", manufacturer specific data: " + str(
                                expected_manufacturer_specific_data))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data manufacturer id: " + str(
                               expected_manufacturer_id) + ", manufacturer specific data: " + str(
                               expected_manufacturer_specific_data) + " failed successfully.")
        return True
