#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

try:
  from unittest import mock  # PY3
except ImportError:
  import mock  # PY2

import logging
import unittest

from acts import base_test
from acts.controllers import android_device

def get_mock_ads(num):
    """Generates a list of mock AndroidDevice objects.

    The serial number of each device will be integer 0 through num - 1.

    Args:
        num: An integer that is the number of mock AndroidDevice objects to
            create.
    """
    ads = []
    for i in range(num):
        ad = mock.MagicMock(name="AndroidDevice", serial=i, h_port=None)
        ads.append(ad)
    return ads

def mock_get_all_instances():
    return get_mock_ads(5)

def mock_list_adb_devices():
    return [ad.serial for ad in get_mock_ads(5)]

class ActsAndroidDeviceTest(unittest.TestCase):
    """This test class has unit tests for the implementation of everything
    under acts.controllers.android_device.
    """

    @mock.patch.object(android_device, "get_all_instances",
                       new=mock_get_all_instances)
    @mock.patch.object(android_device, "list_adb_devices",
                       new=mock_list_adb_devices)
    def test_create_with_pickup_all(self):
        pick_all_token = android_device.ANDROID_DEVICE_PICK_ALL_TOKEN
        actual_ads = android_device.create(pick_all_token, logging)
        for actual, expected in zip(actual_ads, get_mock_ads(5)):
            self.assertEqual(actual.serial, expected.serial)

    def test_create_with_empty_config(self):
        expected_msg = android_device.ANDROID_DEVICE_EMPTY_CONFIG_MSG
        with self.assertRaises(android_device.AndroidDeviceError,
                               msg=expected_msg):
            android_device.create([], logging)

    def test_create_with_not_list_config(self):
        expected_msg = android_device.ANDROID_DEVICE_NOT_LIST_CONFIG_MSG
        with self.assertRaises(android_device.AndroidDeviceError,
                               msg=expected_msg):
            android_device.create("HAHA", logging)
            self.fail("Did not get expected AndroidDeviceError.")

    def test_get_device_success_with_serial(self):
        ads = get_mock_ads(5)
        expected_serial = 0
        ad = android_device.get_device(ads, serial=expected_serial)
        self.assertEqual(ad.serial, expected_serial)

    def test_get_device_success_with_serial_and_extra_field(self):
        ads = get_mock_ads(5)
        expected_serial = 1
        expected_h_port = 5555
        ads[1].h_port = expected_h_port
        ad = android_device.get_device(ads,
                                       serial=expected_serial,
                                       h_port=expected_h_port)
        self.assertEqual(ad.serial, expected_serial)
        self.assertEqual(ad.h_port, expected_h_port)

    def test_get_device_no_match(self):
        ads = get_mock_ads(5)
        expected_msg = ("Could not find a target device that matches condition"
                        ": {'serial': 5}.")
        with self.assertRaises(android_device.AndroidDeviceError,
                               msg=expected_msg):
            ad = android_device.get_device(ads, serial=len(ads))

    def test_get_device_too_many_matches(self):
        ads = get_mock_ads(5)
        target_serial = ads[1].serial = ads[0].serial
        expected_msg = "More than one device matched: [0, 0]"
        with self.assertRaises(android_device.AndroidDeviceError,
                               msg=expected_msg):
            ad = android_device.get_device(ads, serial=target_serial)

if __name__ == "__main__":
   unittest.main()