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
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_CALLEE_RINGING
from acts.test_utils.tel.tel_defines import DEFAULT_DEVICE_PASSWORD
from acts.test_utils.tel.tel_test_utils import dumpsys_telecom_call_info
from acts.test_utils.tel.tel_test_utils import fastboot_wipe
from acts.test_utils.tel.tel_test_utils import hung_up_call_by_adb
from acts.test_utils.tel.tel_test_utils import initiate_call
from acts.test_utils.tel.tel_test_utils import initiate_emergency_dialer_call_by_adb
from acts.test_utils.tel.tel_test_utils import reset_device_password
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode_by_adb
from acts.test_utils.tel.tel_test_utils import unlocking_device
from acts.test_utils.tel.tel_test_utils import unlock_sim


class TelLiveSprintEmergencyTest(TelephonyBaseTest):
    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.dut = self.android_devices[0]

    def teardown_test(self):
        self.dut.ensure_screen_on()
        reset_device_password(self.dut, None)

    def emergency_526_call_test(self, by_emergency_dialer=True):
        callee = "526"
        if by_emergency_dialer:
            dialing_func = initiate_emergency_dialer_call_by_adb
        else:
            dialing_func = initiate_call
            # Initiate_call method has to have "+" in front
            # otherwise the number will be in dialer without dial out
            # with sl4a fascade. Need further investigation
            callee = "+%s" % callee
        result = True
        if not dialing_func(self.log, self.dut, callee):
            self.dut.log.info("Call to %s failed", callee)
            result = False
        else:
            self.dut.log.info("Call to %s succeeded", callee)
        hung_up_call_by_adb(self.dut)
        self.dut.send_keycode("BACK")
        self.dut.send_keycode("BACK")
        return result

    """ Tests Begin """

    @test_tracker_info(uuid="ea13fd5e-7d09-4523-b99b-9e9a0ac97ab0")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer(self):
        """Test emergency call with emergency dialer in user account.

        Use the emergency dialer to call 526.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.emergency_526_call_test()

    @test_tracker_info(uuid="23975c54-a499-4d9d-b8b1-134dd507e07e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_dialer(self):
        """Test emergency call with dialer.

        Call 526 by dialer.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.emergency_526_call_test(by_emergency_dialer=False)

    @test_tracker_info(uuid="5c66ce2d-8b92-4b60-b71b-62dfeb8ae17b")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_apm(self):
        """Test emergency call with emergency dialer in airplane mode.

        Enable airplane mode.
        Use the emergency dialer to call 526.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            if self.emergency_526_call_test():
                return True
            else:
                return False
        finally:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)

    @test_tracker_info(uuid="c70a931c-5d07-45eb-8a7e-3252a5e1727d")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Use the emergency dialer to call 526.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        toggle_airplane_mode_by_adb(self.log, self.dut, False)
        reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
        self.dut.reboot(stop_at_lock_screen=True)
        if self.emergency_526_call_test():
            return True
        else:
            return False

    @test_tracker_info(uuid="743c6b89-7107-41ff-b4fe-2a8e80c99a0d")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock_apm(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Use the emergency dialer to call 526.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.reboot(stop_at_lock_screen=True)
            if self.emergency_526_call_test():
                return True
            else:
                return False
        finally:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)

    @test_tracker_info(uuid="55d55d7f-dc9b-4e73-b1ca-ec8c9a5e86ba")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_setupwizard(self):
        """Test emergency call with emergency dialer in setupwizard.

        Wipe the device and then reboot upto setupwizard.
        Use the emergency dialer to call 526.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            fastboot_wipe(self.dut, skip_setup_wizard=False)
            if self.emergency_526_call_test():
                return True
            else:
                return False
        finally:
            self.dut.exit_setup_wizard()


""" Tests End """
