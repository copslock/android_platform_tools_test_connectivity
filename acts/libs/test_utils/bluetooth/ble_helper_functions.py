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
import threading
import pprint

import android


class BleScanResultError(Exception):
    """Error in fetching BleScanner Scan result."""

def generate_ble_scan_objects(droid):
    filter_list = droid.genFilterList()
    filter_index = droid.buildScanFilter(filter_list)
    scan_settings = droid.buildScanSetting()
    scan_callback = droid.genScanCallback()
    return filter_list, scan_settings, scan_callback

def generate_ble_advertise_objects(droid):
    advertise_data = droid.buildAdvertiseData()
    advertise_settings = droid.buildAdvertisementSettings()
    advertise_callback = droid.genBleAdvertiseCallback()
    return advertise_data, advertise_settings, advertise_callback