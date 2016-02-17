#!/usr/bin/python3.4
#
#   Copyright 2015 - The Android Open Source Project
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

from acts import base_test
from acts import logger
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

class ActsAndroidDeviceTest(base_test.BaseTestClass):
    """This test class has unit tests for the implementation of everything
    under acts.controllers.android_device.
    """

    def __init__(self, controllers):
        super(ActsAndroidDeviceTest, self).__init__(controllers)

    """ Begin of Tests """
    @mock.patch.object(android_device, "get_all_instances",
                       new=mock_get_all_instances)
    @mock.patch.object(android_device, "list_adb_devices",
                       new=mock_list_adb_devices)
    def test_create_with_pickup_all(self):
        pick_all_token = android_device.ANDROID_DEVICE_PICK_ALL_TOKEN
        actual_ads = android_device.create(pick_all_token, logging)
        for actual, expected in zip(actual_ads, get_mock_ads(5)):
            self.assert_true(actual.serial == expected.serial,
                             "Expected serial %s, got %s." % (expected.serial,
                                                              actual.serial))

    def test_create_with_empty_config(self):
        expected_msg = android_device.ANDROID_DEVICE_EMPTY_CONFIG_MSG
        try:
            android_device.create([], logging)
            self.fail("Did not get expected AndroidDeviceError.")
        except android_device.AndroidDeviceError as e:
            self.assert_true(expected_msg == str(e),
                             "Expected error msg %s, got %s." % (expected_msg,
                                                                 str(e)))

    def test_create_with_not_list_config(self):
        expected_msg = android_device.ANDROID_DEVICE_NOT_LIST_CONFIG_MSG
        try:
            android_device.create("HAHA", logging)
            self.fail("Did not get expected AndroidDeviceError.")
        except android_device.AndroidDeviceError as e:
            self.assert_true(expected_msg == str(e),
                             "Expected error msg %s, got %s." % (expected_msg,
                                                                 str(e)))

    def test_get_device_success_with_serial(self):
        ads = get_mock_ads(5)
        expected_serial = 0
        ad = android_device.get_device(ads, serial=expected_serial)
        self.assert_true(ad.serial == expected_serial,
                         ("Expected to get an ad of serial %d, got serial %d."
                         ) % (expected_serial, ad.serial))

    def test_get_device_success_with_serial_and_extra_field(self):
        ads = get_mock_ads(5)
        expected_serial = 1
        expected_h_port = 5555
        ads[1].h_port = expected_h_port
        ad = android_device.get_device(ads,
                                       serial=expected_serial,
                                       h_port=expected_h_port)
        self.assert_true(ad.serial == expected_serial,
                         ("Expected to get an ad of serial %d, got serial %d."
                         ) % (expected_serial, ad.serial))
        self.assert_true(ad.h_port == expected_h_port,
                         ("Expected to get an ad of h_port %d, got h_port %d."
                         ) % (expected_h_port, ad.h_port))

    def test_get_device_no_match(self):
        ads = get_mock_ads(5)
        try:
            ad = android_device.get_device(ads, serial=len(ads))
        except android_device.AndroidDeviceError as e:
            self.assert_true("Could not find a target device" in str(e),
                             ("Expected AndroidDeviceError with no match "
                              "found, got AndroidDeviceError: %s." % e))
            self.explicit_pass("Got expected AndroidDeviceError %s, pass." % e)
        self.fail("Did not get expected AndroidDeviceError signalling no "
                  "matching device found.")

    def test_get_device_too_many_matches(self):
        ads = get_mock_ads(5)
        target_serial = ads[1].serial = ads[0].serial
        try:
            ad = android_device.get_device(ads, serial=target_serial)
        except android_device.AndroidDeviceError as e:
            self.assert_true("More than one device matched" in str(e),
                             ("Expected AndroidDeviceError with too many match"
                              "es found, got AndroidDeviceError: %s." % e)
                            )
            self.explicit_pass("Got expected AndroidDeviceError %s, pass." % e)
        self.fail("Did not get expected AndroidDeviceError signalling too many"
                  " matching devices found.")

    """ End of Tests """
