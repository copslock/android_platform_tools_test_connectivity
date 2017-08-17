#!/usr/bin/env python3.4
#
#   Copyright 2017 - Google
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
"""
    Test Script for Telephony Pre Check In Sanity
"""

import time
import os
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_test_utils import dumpsys_telecom_call_info
from acts.test_utils.tel.tel_test_utils import fastboot_wipe
from acts.test_utils.tel.tel_test_utils import hung_up_call_by_adb
from acts.test_utils.tel.tel_test_utils import initiate_call
from acts.test_utils.tel.tel_test_utils import initiate_emergency_dialer_call_by_adb
from acts.test_utils.tel.tel_test_utils import reset_device_password
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode_by_adb
from acts.test_utils.tel.tel_test_utils import unlocking_device
from acts.test_utils.tel.tel_test_utils import STORY_LINE

DEFAULT_DEVICE_PASSWORD = "1111"


class TelLiveNoSimTest(TelephonyBaseTest):
    def setup_class(self):
        self.wifi_network_ssid = self.user_params.get(
            "wifi_network_ssid") or self.user_params.get("wifi_network_ssid_2g")
        self.wifi_network_pass = self.user_params.get(
            "wifi_network_pass") or self.user_params.get("wifi_network_pass_2g")
        self.dut = self.android_devices[0]
        fake_number = self.user_params.get("fake_emergency_number", STORY_LINE)
        self.fake_emergency_number = fake_number.strip("+").replace("-", "")

    def teardown_class(self):
        super(TelephonyBaseTest, self).teardown_class()
        #reboot to load default emergency number list ril.ecclist
        self.dut.reboot()

    def setup_test(self):
        pass

    def change_emergency_number_list(self):
        existing = self.dut.adb.shell("getprop ril.ecclist")
        if self.fake_emergency_number in existing: return
        emergency_numbers = "%s,%s" % (existing, self.fake_emergency_number)
        self.dut.log.info("Change emergency numbes to %s", emergency_numbers)
        self.dut.adb.shell("setprop ril.ecclist %s" % emergency_numbers)

    def fake_emergency_call_test(self, by_emergency_dialer=True):
        self.change_emergency_number_list()
        time.sleep(1)
        call_numbers = len(dumpsys_telecom_call_info(self.dut))
        if by_emergency_dialer:
            dialing_func = initiate_emergency_dialer_call_by_adb
        else:
            dialing_func = initiate_call
        if dialing_func(
                self.log, self.dut, self.fake_emergency_number, timeout=10):
            hung_up_call_by_adb(self.dut)
            self.dut.log.error(
                "calling to the fake emergency number should fail")
        calls_info = dumpsys_telecom_call_info(self.dut)
        if len(calls_info) <= call_numbers:
            self.dut.log.error("New call is not in sysdump telecom")
            return False
        else:
            self.dut.log.info("New call info = %s", calls_info[call_numbers])
            return True

    """ Tests Begin """

    @test_tracker_info(uuid="91bc0c02-c1f2-4112-a7f8-c91617bff53e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer(self):
        """Test emergency call with emergency dialer in user account.

        Change system emergency number list to "611".
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.fake_emergency_call_test()

    @test_tracker_info(uuid="cdf7ddad-480f-4757-83bd-a74321b799f7")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_dialer(self):
        """Test emergency call with dialer.

        Change system emergency number list to "611".
        Call "611" by dialer.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.fake_emergency_call_test(by_emergency_dialer=False)

    @test_tracker_info(uuid="e147960a-4227-41e2-bd06-65001ad5e0cd")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_apm(self):
        """Test emergency call with emergency dialer in airplane mode.

        Enable airplane mode.
        Change system emergency number list to "611".
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)

    @test_tracker_info(uuid="34068bc8-bfa0-4c7b-9450-e189a0b93c8a")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Change system emergency number list to "611".
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)
            reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.reboot(stop_at_lock_screen=True)
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            self.dut.send_keycode("BACK")
            self.dut.send_keycode("BACK")
            unlocking_device(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.start_services(self.dut.skip_sl4a)
            reset_device_password(self.dut, None)

    @test_tracker_info(uuid="1ef97f8a-eb3d-45b7-b947-ac409bb70587")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock_apm(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Change system emergency number list to "611".
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.reboot(stop_at_lock_screen=True)
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            self.dut.send_keycode("BACK")
            self.dut.send_keycode("BACK")
            toggle_airplane_mode_by_adb(self.log, self.dut, False)
            unlocking_device(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.start_services(self.dut.skip_sl4a)
            reset_device_password(self.dut, None)

    @test_tracker_info(uuid="50f8b3d9-b126-4419-b5e5-b37b850deb8e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_setupwizard(self):
        """Test emergency call with emergency dialer in setupwizard.

        Wipe the device and then reboot upto setupwizard.
        Change system emergency number list to "611".
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            fastboot_wipe(self.dut, skip_setup_wizard=False)
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            self.dut.send_keycode("BACK")
            self.dut.send_keycode("BACK")
            self.dut.exit_setup_wizard()


""" Tests End """
