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


class BleAdvertiseResultError(Exception):
    """Error in fetching BleAdvertise Scan result."""


def build_scansettings(droid):
    try:
        scan_index = droid.buildScanSetting()
        return scan_index
    except BleScanResultError as error:
        return False


def build_advertisesettings(droid):
    try:
        advertisement_index = droid.buildAdvertisementSettings()
        return advertisement_index
    except BleScanResultError as error:
        return False


def build_advertisedata(droid):
    try:
        advertise_data = droid.buildAdvertiseData()
        return advertise_data
    except BleScanResultError as error:
        return False


def gen_filterlist(droid):
    try:
        filter_list_index = droid.genFilterList()
        return filter_list_index
    except BleScanResultError as error:
        return False


def build_scanfilter(droid, filter_index):
    try:
        scan_filter_index = droid.buildScanFilter(filter_index)
        return scan_filter_index
    except BleScanResultError as error:
        return False


def gen_scancallback(droid):
    try:
        scan_callbackIndex = droid.genScanCallback()
        return scan_callbackIndex
    except BleScanResultError as error:
        return False


def startblescan(droid, filter_list, scan_settings, scan_callback):
    try:
        droid.startBleScan(filter_list, scan_settings, scan_callback)
        return True
    except BleScanResultError as error:
        return False


def startbleadvertise(droid, advertise_data, advertise_settings, advertise_callback):
    try:
        droid.startBleAdvertising(advertise_callback, advertise_data, advertise_settings)
        return True
    except BleAdvertiseResultError as error:
        return False


def stopblescan(droid, scan_callback):
    try:
        droid.stopBleScan(scan_callback)
        return True
    except BleScanResultError as error:
        return False


def generate_ble_scan_objects(droid):
    filter_list = gen_filterlist(droid)
    filter_index = build_scanfilter(droid, filter_list)
    scan_settings = build_scansettings(droid)
    scan_callback = gen_scancallback(droid)
    return filter_list, scan_settings, scan_callback


def generate_ble_advertise_objects(droid):
    advertise_data = droid.buildAdvertiseData()
    advertise_settings = droid.buildAdvertisementSettings()
    advertise_callback = droid.genBleAdvertiseCallback()
    return advertise_data, advertise_settings, advertise_callback


def unexpected_onscanfailed_event(event_info):
    return ("Ble Scan Failed with error code: " + str(event_info['data']['ErrorCode'])
            + ". Event details: \n" + pprint.pformat(event_info))


def get_device_info(droid):
    return ("Device Id: " + droid.getDeviceId() + "\n" +
            "Device Software Version: " + droid.getDeviceSoftwareVersion())


def cleanup(devices):
    for device in devices:
        device.kill_all_droids()

def stopbleadvertise(droid, advertise_callback):
    try:
        droid.stopBleAdvertising(advertise_callback)
        return True
    except BleAdvertiseResultError:
        return False