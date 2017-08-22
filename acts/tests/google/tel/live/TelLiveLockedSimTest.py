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
    Test Script for Telephony Locked SIM Emergency Call Test
"""

import time
import os
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import DEFAULT_DEVICE_PASSWORD
from acts.test_utils.tel.tel_defines import SIM_STATE_PIN_REQUIRED
from acts.test_utils.tel.tel_test_utils import dumpsys_telecom_call_info
from acts.test_utils.tel.tel_test_utils import fastboot_wipe
from acts.test_utils.tel.tel_test_utils import hung_up_call_by_adb
from acts.test_utils.tel.tel_test_utils import initiate_call
from acts.test_utils.tel.tel_test_utils import initiate_emergency_dialer_call_by_adb
from acts.test_utils.tel.tel_test_utils import is_sim_locked
from acts.test_utils.tel.tel_test_utils import reset_device_password
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode_by_adb
from acts.test_utils.tel.tel_test_utils import unlocking_device
from acts.test_utils.tel.tel_test_utils import STORY_LINE
from TelLiveEmergencyTest import TelLiveEmergencyTest

EXPECTED_CALL_TEST_RESULT = False


class TelLiveLockedSimTest(TelLiveEmergencyTest):
    def setup_class(self):
        if not is_sim_locked(self.dut):
            self.dut.reboot()
            if not is_sim_locked(self.dut):
                self.dut.log.error("SIM is not locked")
                return False
        self.dut.log.info("SIM is locked")

    def setup_test(self):
        # reboot the device to SIM lock inquiry page if SIM is not locked
        if not is_sim_locked(self.dut):
            self.dut.reboot()
        self.expected_call_result = False

    """ Tests Begin """

    @test_tracker_info(uuid="fd7fb69c-6fd4-4874-a4ca-769353b9db25")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer(self):
        """Test emergency call with emergency dialer in user account.

        Enable SIM lock on the SIM. Reboot device to SIM pin request page.
        Add storyline number to system emergency number list.
        Use the emergency dialer to call "611".
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        toggle_airplane_mode_by_adb(self.log, self.dut, False)
        return self.fake_emergency_call_test()

    @test_tracker_info(uuid="669cf1d9-9513-4f90-b0fd-2f0e8f1cc941")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_dialer(self):
        """Test emergency call with dialer.

        Enable SIM lock on the SIM. Reboot device to SIM pin request page.
        Add system emergency number list with storyline number.
        Call storyline by dialer.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        toggle_airplane_mode_by_adb(self.log, self.dut, False)
        return self.fake_emergency_call_test(by_emergency_dialer=False)

    @test_tracker_info(uuid="1990f166-66a7-4092-b448-c179a9194371")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_apm(self):
        """Test emergency call with emergency dialer in airplane mode.

        Enable airplane mode.
        Enable SIM lock on the SIM. Reboot device to SIM pin request page.
        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
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

    @test_tracker_info(uuid="7ffdad34-b8fb-41b0-b0fd-2def5adc67bc")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable SIM lock on the SIM.
        Enable device password and then reboot upto password and pin query stage.
        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
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

    @test_tracker_info(uuid="12dc1eb6-50ed-4ad9-b195-5d96c6b6952e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock_apm(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and airplane mode
        Enable SIM lock on the SIM.
        Reboot upto pin query window.
        Add system emergency number list with story line.
        Use the emergency dialer to call story line.
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

    @test_tracker_info(uuid="1e01927a-a077-466d-8bf8-52dca87ab87c")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_setupwizard(self):
        """Test emergency call with emergency dialer in setupwizard.

        Enable SIM lock on the SIM.
        Wipe the device and then reboot upto setupwizard.
        Add system emergency number list with story line.
        Use the emergency dialer to call story line.
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
