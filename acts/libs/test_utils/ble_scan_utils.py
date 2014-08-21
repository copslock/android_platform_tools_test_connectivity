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

import android
from test_utils.ble_helper_functions import *


class BleScanVerificationError(Exception):
    """Error in fetsching BleScanner Scan result."""



def verify_scan_filters_rssi(testcase, droid, expected_min_rssi, expected_max_rssi):
    filter_list = gen_filterlist(droid)
    try:
        droid.setScanFilterRssiRange(expected_min_rssi, expected_max_rssi)

    except BleScanVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 4: Build the scan filter object.")
    scan_filter_index = build_scanfilter(droid, filter_list)
    testcase.log.debug("Step 5: Get the scan filter's min and max rssi")
    min_rssi = droid.getScanFilterMinRssi(filter_list, scan_filter_index)
    max_rssi = droid.getScanFilterMaxRssi(filter_list, scan_filter_index)

    if min_rssi != expected_min_rssi:
        testcase.log.debug("Expected min rssi: " + str(expected_min_rssi)
                                + ", Actual min rssi: " + str(min_rssi))
        return False
    if max_rssi != expected_max_rssi:
        testcase.log.debug("Expected min rssi: " + str(expected_max_rssi)
                                + ", Actual min rssi: " + str(max_rssi))

        return False
    testcase.log.debug("Scan Filter min rssi " + str(min_rssi) + ", max rssi "
                           + str(max_rssi) + " test Passed.")
    return True


def verify_invalid_scan_filters_rssi(testcase, droid, expected_min_rssi,
                                     expected_max_rssi):
    try:
        droid.setScanFilterRssiRange(expected_min_rssi, expected_max_rssi)
        build_scansettings(droid)
        testcase.log.debug("Set Scan Filter invalid device address passed "
                                + " with input as  min rssi " + str(expected_min_rssi)
                                + ", max rssi " + str(expected_max_rssi))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Scan Filter invalid device address failed successfully"
                               + " with input as  min rssi " + str(expected_min_rssi)
                               + ", max rssi " + str(expected_max_rssi))
        return True



def verify_ble_scan(testcase, droid, event_dispatcher, filter_list, scan_settings, scan_callback):
    try:
        droid.startBleScan(filter_list, scan_settings, scan_callback)
    except BleScanResultError as error:
        testcase.log.debug(str(error))
        return False
    droid.stopBleScan(scan_callback)
    testcase.log.debug("Passed")
    return True


def verify_classic_ble_scan_with_service_uuids(testcase, droid, event_dispatcher, scan_callback,
                                               service_uuid_list):
    test_result = True
    try:
        test_result = droid.startClassicBleScanWithServiceUuids(scan_callback, service_uuid_list)
    except BleScanResultError as error:
        testcase.log.debug(str(error))
        return False
    droid.stopClassicBleScan(scan_callback)
    if not test_result:
        testcase.log.debug(
            "Start classic ble scan with service uuids return false boolean value.")
        return False
    else:
        testcase.log.debug("Passed")
    return True

    # Verification functions End