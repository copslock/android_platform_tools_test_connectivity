#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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

from test_utils.bluetooth.ble_helper_functions import BleScanResultError


class BleScanVerificationError(Exception):
    """Error in fetsching BleScanner Scan result."""


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
