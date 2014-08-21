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

from base_test import BaseTestClass
from test_utils.ble_scan_test_utils import *
from test_utils.BleEnum import *
from test_utils.blescan_api_helper import *


class BleScanVerificationError(Exception):
    """Error in fetching BleScanner Scan result."""


class BleSetScanSettingsError(Exception):
    """Error in setting Ble Scan Settings"""


class BleSetScanFilterError(Exception):
    """Error in setting Ble Scan Settings"""


class BleScanTest(BaseTestClass):
    TAG = "BleFunctionalScanTest"
    log_path = BaseTestClass.log_path + TAG + '/'
    tests = None

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.tests = (
            "test_start_ble_scan_with_default_settings",
            "test_stop_ble_scan_default_settings",
            "test_scan_settings_defaults",
            "test_scan_settings_callback_type_all_matches",
            "test_scan_settings_set_callback_type_first_match",
            "test_scan_settings_set_callback_type_match_lost",
            "test_scan_settings_set_invalid_callback_type",
            "test_scan_settings_set_scan_mode_low_power",
            "test_scan_settings_set_scan_mode_balanced",
            "test_scan_settings_set_scan_mode_low_latency",
            "test_scan_settings_set_invalid_scan_mode",
            "test_scan_settings_set_report_delay_millis_min",
            "test_scan_settings_set_report_delay_millis_min_plus_one",
            "test_scan_settings_set_report_delay_millis_max",
            "test_scan_settings_set_report_delay_millis_max_minus_one",
            "test_scan_settings_set_invalid_report_delay_millis_min_minus_one",
            "test_scan_settings_set_invalid_report_delay_millis_min",
            "test_scan_settings_set_scan_result_type_full",
            "test_scan_settings_set_scan_result_type_abbreviated",
            "test_scan_settings_set_invalid_scan_result_type",
            "test_scan_filter_default_settings",
            "test_scan_filter_set_device_name",
            "test_scan_filter_set_device_name_blank",
            "test_scan_filter_set_device_name_special_chars",
            "test_scan_filter_set_device_address",
            "test_scan_filter_set_invalid_device_address_lower_case",
            "test_scan_filter_set_invalid_device_address_blank",
            "test_scan_filter_set_invalid_device_address_bad_format",
            "test_scan_filter_set_invalid_device_address_bad_address",
            # "test_scan_filter_set_rssi",
            #"test_scan_filter_set_rssi_inner_bounds",
            #"test_scan_filter_set_rssi_reverse_values",
            #"test_scan_filter_set_rssi_same_values",
            #"test_scan_filter_set_invalid_rssi_max_bound_plus_one",
            #"test_scan_filter_set_invalid_rssi_min_bound_minus_one",
            "test_scan_filter_set_manufacturer_id_data",
            "test_scan_filter_set_manufacturer_id_data_mask",
            "test_scan_filter_set_manufacturer_max_id",
            "test_scan_filter_set_manufacturer_data_empty",
            "test_scan_filter_set_manufacturer_data_mask_empty",
            "test_scan_filter_set_invalid_manufacturer_min_id_minus_one",
            "test_scan_filter_set_service_uuid",
            "test_scan_filter_service_uuid_polar_service",
            "test_classic_ble_scan_with_service_uuids_polar",
            "test_classic_ble_scan_with_service_uuids_hr",
            "test_classic_ble_scan_with_service_uuids_empty_uuid_list",
            "test_classic_ble_scan_with_service_uuids_hr_and_p",
        )

    # Handler Functions Begin
    def blescantest_verify_onfailure_event_handler(self, event):
        self.log.info("Verifying onFailure event")
        self.log.info(pprint.pformat(event))
        return event

    # Handler Functions End

    # Test Ble Scan API's.

    def _format_defaults(self, input):
        if 'ScanSettings' not in input.keys():
            input['ScanSettings'] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                     ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                     ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        if 'ScanFilterManufacturerDataId' not in input.keys():
            input['ScanFilterManufacturerDataId'] = -1
        if 'ScanFilterDeviceName' not in input.keys():
            input['ScanFilterDeviceName'] = None
        if 'ScanFilterDeviceAddress' not in input.keys():
            input['ScanFilterDeviceAddress'] = None
        if 'ScanFilterManufacturerData' not in input.keys():
            input['ScanFilterManufacturerData'] = ""
        return input

    def validate_scan_settings_helper(self, input, droid):
        filter_list = gen_filterlist(droid)
        if 'ScanSettings' in input.keys():
            try:
                droid.setScanSettings(input['ScanSettings'][0], input['ScanSettings'][1],
                                      input['ScanSettings'][2], input['ScanSettings'][3])
            except android.SL4AAPIError as error:
                self.log.info("Set Scan Settings failed with: " + str(error))
                return False
        if 'ScanFilterDeviceName' in input.keys():
            try:
                droid.setScanFilterDeviceName(input['ScanFilterDeviceName'])
            except android.SL4AAPIError as error:
                self.log.info("Set Scan Filter Device Name failed with: " + str(error))
                return False
        if 'ScanFilterDeviceAddress' in input.keys():
            try:
                droid.setScanFilterDeviceAddress(input['ScanFilterDeviceAddress'])
            except android.SL4AAPIError as error:
                self.log.info("Set Scan Filter Device Address failed with: " + str(error))
                return False
        if 'ScanFilterManufacturerDataId' in input.keys() \
                and 'ScanFilterManufacturerDataMask' in input.keys():
            try:
                droid.setScanFilterManufacturerData(input['ScanFilterManufacturerDataId'],
                                                    input['ScanFilterManufacturerData'],
                                                    input['ScanFilterManufacturerDataMask'])
            except android.SL4AAPIError as error:
                self.log.info(
                    "Set Scan Filter Manufacturer info with data mask failed with: " + str(error))
                return False
        if ('ScanFilterManufacturerDataId' in input.keys()
            and 'ScanFilterManufacturerData' in input.keys()
            and 'ScanFilterManufacturerDataMask' not in input.keys()):
            try:
                droid.setScanFilterManufacturerData(input['ScanFilterManufacturerDataId'],
                                                    input['ScanFilterManufacturerData'])
            except android.SL4AAPIError as error:
                self.log.info("Set Scan Filter Manufacturer info failed with: " + str(error))
                return False
        if 'ScanFilterServiceUuid' in input.keys() and 'ScanFilterServiceMask' in input.keys():
            droid.setScanFilterServiceUuid(input['ScanFilterServiceUuid'],
                                           input['ScanFilterServiceMask'])

        input = self._format_defaults(input)
        scan_settings_index = build_scansettings(droid)
        scan_settings = (droid.getScanSettingsCallbackType(scan_settings_index),
                         droid.getScanSettingsReportDelayMillis(scan_settings_index),
                         droid.getScanSettingsScanMode(scan_settings_index),
                         droid.getScanSettingsScanResultType(scan_settings_index))

        scan_filter_index = build_scanfilter(droid, filter_list)
        device_name_filter = droid.getScanFilterDeviceName(filter_list, scan_filter_index)
        device_address_filter = droid.getScanFilterDeviceAddress(filter_list, scan_filter_index)
        manufacturer_id = droid.getScanFilterManufacturerId(filter_list, scan_filter_index)
        manufacturer_data = droid.getScanFilterManufacturerData(filter_list, scan_filter_index)

        if scan_settings != input['ScanSettings']:
            self.log.info("Scan Settings did not match. expected: " + input[
                'ScanSettings'] + ", found: " + str(scan_settings))
            return False
        if device_name_filter != input['ScanFilterDeviceName']:
            self.log.info("Scan Filter device name did not match. expected: " + input[
                'ScanFilterDeviceName'] + ", found: " + device_name_filter)
            return False
        if device_address_filter != input['ScanFilterDeviceAddress']:
            self.log.info("Scan Filter address name did not match. expected: " + input[
                'ScanFilterDeviceAddress'] + ", found: " + device_address_filter)
            return False
        if manufacturer_id != input['ScanFilterManufacturerDataId']:
            self.log.info("Scan Filter manufacturer data id did not match. expected: " + input[
                'ScanFilterManufacturerDataId'] + ", found: " + manufacturer_id)
            return False
        if manufacturer_data != input['ScanFilterManufacturerData']:
            self.log.info("Scan Filter manufacturer data did not match. expected: " + input[
                'ScanFilterManufacturerData'] + ", found: " + manufacturer_data)
            return False
        if 'ScanFilterManufacturerDataMask' in input.keys():
            manufacturer_data_mask = droid.getScanFilterManufacturerDataMask(filter_list,
                                                                             scan_filter_index)
            if manufacturer_data_mask != input['ScanFilterManufacturerDataMask']:
                self.log.info("Manufacturer data mask did not match. expected: " + input[
                    'ScanFilterManufacturerDataMask'] + ", found: " + manufacturer_data_mask)
                return False
        if 'ScanFilterServiceUuid' in input.keys() and 'ScanFilterServiceMask' in input.keys():
            expected_service_uuid = input['ScanFilterServiceUuid']
            expected_service_mask = input['ScanFilterServiceMask']
            service_uuid = droid.getScanFilterServiceUuid(filter_list, scan_filter_index)
            service_mask = droid.getScanFilterServiceUuidMask(filter_list, scan_filter_index)
            if service_uuid != expected_service_uuid.lower():
                self.log.info(
                    "Service uuid did not match. expected: " + expected_service_uuid
                    + ", found: " + service_uuid)
                return False
            if service_mask != expected_service_mask.lower():
                self.log.info(
                    "Service mask did not match. expected: " + expected_service_mask
                    + ", found: " + service_mask)
                return False
        self.scan_settings_index = scan_settings_index
        self.filter_list = filter_list
        self.scan_callback = droid.genLeScanCallback()
        return True

    def test_start_ble_scan_with_default_settings(self):
        self.log.info("Test default scan settings.")
        input = {}
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_stop_ble_scan_default_settings(self):
        self.log.info("Test default scan settings with a start ble scan and stop ble scan.")
        input = {}
        test_result = self.validate_scan_settings_helper(input, self.droid)
        if not test_result:
            self.log.info("Could not setup ble scanner.")
            return test_result
        test_result = startblescan(self.droid, self.filter_list, self.scan_settings_index,
                                   self.scan_callback)
        try:
            self.log.info("Step 4: Stop Bluetooth Le Scan.")
            test_result = stopblescan(self.droid, self.scan_callback)
        except BleScanResultError as error:
            self.log.info(str(error))
            test_result = False
        return test_result

    def test_scan_settings_callback_type_all_matches(self):
        self.log.info("Test scan settings callback type all matches.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_callback_type_first_match(self):
        self.log.info("Test scan settings callback type first lost.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_FIRST_MATCH.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_callback_type_match_lost(self):
        self.log.info("Test scan settings callback type match lost.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_MATCH_LOST.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_invalid_callback_type(self):
        self.log.info("Test scan settings callback type invalid type.")
        input = {}
        input["ScanSettings"] = (-1, 0, ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_settings_set_scan_mode_low_power(self):
        self.log.info("Test scan settings scan mode low power.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_scan_mode_balanced(self):
        self.log.info("Test scan settings scan mode balanced.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_BALANCED.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_scan_mode_low_latency(self):
        self.log.info("Test scan settings scan mode low latency.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_LATENCY.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_invalid_scan_mode(self):
        self.log.info("Test scan settings scan mode invalid value.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0, -1,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_settings_set_report_delay_millis_min(self):
        self.log.info("Test scan settings report delay seconds min.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                                 ScanSettingsReportDelaySeconds.MIN.value,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_report_delay_millis_min_plus_one(self):
        self.log.info("Test scan settings report delay seconds min plus 1.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                                 ScanSettingsReportDelaySeconds.MIN.value + 1,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_report_delay_millis_max(self):
        self.log.info("Test scan settings report delay seconds max.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                                 ScanSettingsReportDelaySeconds.MAX.value,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_report_delay_millis_max_minus_one(self):
        self.log.info("Test scan settings report delay seconds max minus 1.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                                 ScanSettingsReportDelaySeconds.MAX.value - 1,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_invalid_report_delay_millis_min_minus_one(self):
        self.log.info("Test scan settings report delay seconds max minus 1.")
        droid = self.droid
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                                 ScanSettingsReportDelaySeconds.MIN.value - 1,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, droid)
        return not test_result

    def test_scan_settings_set_scan_result_type_full(self):
        self.log.info("Test scan settings result type full.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_scan_result_type_abbreviated(self):
        self.log.info("Test scan settings result type abbreviated.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                                 ScanSettingsScanResultType.SCAN_RESULT_TYPE_ABBREVIATED.value)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_settings_set_invalid_scan_result_type(self):
        self.log.info("Test scan settings result type invalid.")
        input = {}
        input["ScanSettings"] = (ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value, 0,
                                 ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value, -1)
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_device_name(self):
        self.log.info("Test scan filter device name. ")
        input = {}
        input['ScanFilterDeviceName'] = "sl4atest"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_device_name_blank(self):
        self.log.info("Test scan filter device name as empty string. ")
        droid = self.droid
        input = {}
        input['ScanFilterDeviceName'] = ""
        test_result = self.validate_scan_settings_helper(input, droid)
        return test_result

    def test_scan_filter_set_device_name_special_chars(self):
        self.log.info("Test scan filter device name to be special chars. ")
        input = {}
        input['ScanFilterDeviceName'] = "!@#$%^&*()\":<>/"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_device_address(self):
        self.log.info("Test scan filter device address 01:02:03:AB:CD:EF. ")
        input = {}
        input['ScanFilterDeviceAddress'] = "01:02:03:AB:CD:EF"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_invalid_device_address_lower_case(self):
        self.log.info("Test scan filter invalid device address 01:02:03:ab:cd:ef")
        input = {}
        input['ScanFilterDeviceAddress'] = "01:02:03:ab:cd:ef"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_invalid_device_address_blank(self):
        self.log.info("Test scan filter invalid device address as empty string")
        input = {}
        input['ScanFilterDeviceAddress'] = ""
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_invalid_device_address_bad_format(self):
        self.log.info("Test scan filter invalid device address as 10.10.10.10.10")
        input = {}
        input['ScanFilterDeviceAddress'] = "10.10.10.10.10"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_invalid_device_address_bad_address(self):
        self.log.info("Test scan filter invalid device address as ZZ:ZZ:ZZ:ZZ:ZZ:ZZ")
        input = {}
        input['ScanFilterDeviceAddress'] = "ZZ:ZZ:ZZ:ZZ:ZZ:ZZ"
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_rssi(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_min_rssi = ScanFilterRssi.MIN.value
        expected_max_rssi = ScanFilterRssi.MAX.value
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        verify_scan_filters_rssi(self, droid, expected_min_rssi,
                                 expected_max_rssi)

        return

    def test_scan_filter_set_rssi_inner_bounds(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_min_rssi = ScanFilterRssi.MIN.value + 1
        expected_max_rssi = ScanFilterRssi.MAX.value - 1
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        verify_scan_filters_rssi(self, droid, expected_min_rssi,
                                 expected_max_rssi)

        return

    def test_scan_filter_set_rssi_reverse_values(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_max_rssi = ScanFilterRssi.MIN.value
        expected_min_rssi = ScanFilterRssi.MAX.value
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        verify_scan_filters_rssi(self, droid, expected_min_rssi,
                                 expected_max_rssi)

        return

    def test_scan_filter_set_rssi_same_values(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_max_rssi = 0
        expected_min_rssi = 0
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        return verify_scan_filters_rssi(self, droid,
                                        expected_min_rssi,
                                        expected_max_rssi)

    def test_scan_filter_set_invalid_rssi_max_bound_plus_one(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_max_rssi = ScanFilterRssi.MIN.value
        expected_min_rssi = ScanFilterRssi.MAX.value + 1
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        verify_invalid_scan_filters_rssi(self, droid, expected_min_rssi,
                                         expected_max_rssi)

        return

    def test_scan_filter_set_invalid_rssi_min_bound_minus_one(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        expected_max_rssi = ScanFilterRssi.MIN.value - 1
        expected_min_rssi = ScanFilterRssi.MAX.value
        self.log.info("Step 2: Set the scan filters object's value to "
                      + "min rssi " + str(expected_min_rssi) + ", max rssi "
                      + str(expected_max_rssi))
        verify_invalid_scan_filters_rssi(self, droid, expected_min_rssi,
                                         expected_max_rssi)

        return

    def test_scan_filter_set_manufacturer_id_data(self):
        expected_manufacturer_id = 0
        expected_manufacturer_data = "1,2,1,3,4,5,6"
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_manufacturer_id_data_mask(self):
        expected_manufacturer_id = 1
        expected_manufacturer_data = "1"
        expected_manufacturer_data_mask = "1,2,1,3,4,5,6"
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data + ", manufacturer data mask " + expected_manufacturer_data_mask)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        input['ScanFilterManufacturerDataMask'] = expected_manufacturer_data_mask
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_manufacturer_max_id(self):
        expected_manufacturer_id = 2147483647
        expected_manufacturer_data = "1,2,1,3,4,5,6"
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_manufacturer_data_empty(self):
        expected_manufacturer_id = 1
        expected_manufacturer_data = ""
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_manufacturer_data_mask_empty(self):
        expected_manufacturer_id = 1
        expected_manufacturer_data = "1,2,1,3,4,5,6"
        expected_manufacturer_data_mask = ""
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data
                      + ", manufacturer data mask " + expected_manufacturer_data_mask)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        input['ScanFilterManufacturerDataMask'] = expected_manufacturer_data_mask
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_set_invalid_manufacturer_min_id_minus_one(self):
        expected_manufacturer_id = -1
        expected_manufacturer_data = "1,2,1,3,4,5,6"
        self.log.info("Test scan filter set manufacturer id " + str(
            expected_manufacturer_id) + ", manufacturer data " + expected_manufacturer_data)
        input = {}
        input['ScanFilterManufacturerDataId'] = expected_manufacturer_id
        input['ScanFilterManufacturerData'] = expected_manufacturer_data
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_scan_filter_set_service_uuid(self):
        expected_service_uuid = "00000000-0000-1000-8000-00805F9B34FB"
        expected_service_mask = "00000000-0000-1000-8000-00805F9B34FB"
        self.log.info(
            "Test scan filter set service uuid " + expected_service_uuid + ", service uuid "
            + expected_service_mask)
        input = {}
        input['ScanFilterServiceUuid'] = expected_service_uuid
        input['ScanFilterServiceMask'] = expected_service_mask
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return test_result

    def test_scan_filter_service_uuid_p_service(self):
        expected_service_uuid = Uuids.P.value
        expected_service_mask = "00000000-0000-1000-8000-00805F9B34FB"
        self.log.info(
            "Test scan filter set service uuid " + expected_service_uuid + ", service uuid "
            + expected_service_mask)
        input = {}
        input['ScanFilterServiceUuid'] = expected_service_uuid
        input['ScanFilterServiceMask'] = expected_service_mask
        test_result = self.validate_scan_settings_helper(input, self.droid)
        return not test_result

    def test_classic_ble_scan_with_service_uuids_p(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        service_uuid_list = [Uuids.P_Service.value]
        scan_callback = droid.genLeScanCallback()
        return verify_classic_ble_scan_with_service_uuids(self, droid, self.ed,
                                                          scan_callback,
                                                          service_uuid_list)

    def test_classic_ble_scan_with_service_uuids_hr(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        service_uuid_list = [Uuids.HR_SERVICE.value]
        scan_callback = droid.genLeScanCallback()
        return verify_classic_ble_scan_with_service_uuids(self, droid, self.ed,
                                                          scan_callback,
                                                          service_uuid_list)

    def test_classic_ble_scan_with_service_uuids_empty_uuid_list(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        service_uuid_list = []
        scan_callback = droid.genLeScanCallback()
        return verify_classic_ble_scan_with_service_uuids(self, droid, self.ed,
                                                          scan_callback,
                                                          service_uuid_list)

    def test_classic_ble_scan_with_service_uuids_hr_and_p(self):
        self.log.info("Step 1: Setup environment.")

        droid = self.droid
        service_uuid_list = [Uuids.HR_SERVICE.value, Uuids.P_Service.value]
        scan_callback = droid.genLeScanCallback()
        return verify_classic_ble_scan_with_service_uuids(self, droid, self.ed,
                                                          scan_callback,
                                                          service_uuid_list)