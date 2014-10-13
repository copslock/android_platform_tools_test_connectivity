#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
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
    Test Script for Telephony Conference Call
"""

import time
from base_test import BaseTestClass
from queue import Empty
from test_utils.tel.tel_test_utils import call_process
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import verify_active_call_number
from test_utils.tel.tel_test_utils import verify_http_connection
from test_utils.tel.tel_test_utils import verify_incall_state

class ConfCallTest(BaseTestClass):
    TAG = "ConfCallTest"
    log_path = ''.join((BaseTestClass.log_path, TAG, "/"))

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.android_devices[1].get_droid()
        self.ed1.start()
        self.droid2, self.ed2 = self.android_devices[2].get_droid()
        self.ed2.start()
        self.tests = (
                      "test_conf_call",
                      "test_pretest_ensure_lte_volte",
                      "test_conf_call_volte",
                      )
        self.phone_number_0 = None
        self.phone_number_1 = None
        self.phone_number_2 = None
        self.time_wait_in_call = 10
        self.delay_between_test = 5
        self.max_wait_time_for_lte = 60

    def setup_class(self):
        if self.phone_number_0 is None:
            self.phone_number_0 = self.droid0.getLine1Number()
        if self.phone_number_1 is None:
            self.phone_number_1 = self.droid1.getLine1Number()
        if self.phone_number_2 is None:
            self.phone_number_2 = self.droid2.getLine1Number()
        if (self.phone_number_0 is None or
            self.phone_number_1 is None or
            self.phone_number_2 is None):
            self.log.error("In setup can not get phone number")
            return False
        for droid in [self.droid0, self.droid1, self.droid2]:
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, False)
        return True

    def teardown_test(self):
        droids = [self.droid0, self.droid1, self.droid2]
        for droid in droids:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        #Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    """ Tests Begin """
    def test_conf_call(self):
        """ Test Conf Call among three phones.

        Call from PhoneA to PhoneB, accept on PhoneB.
        Call from PhoneA to PhoneC, accept on PhoneC.
        On PhoneA, merge to conference call.
        End call on PhoneC, verify call continues.
        Call from PhoneC to PhoneA, accept on PhoneA.
        On PhoneA, merge to conference call.
        End call between A and C on PhoneA, verify call continues.

        Returns:
            True if pass; False if fail.
        """
        #TODO(yangxliu): Add code to check voice. Currently only check status.
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        toggle_airplane_mode(self.log, self.droid2, self.ed2, False)
        self.log.info("Step1: Call From PhoneA to PhoneB.")
        call_process(self.log, self.droid0, self.droid1,
                     self.ed0, self.ed1, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_1)
        verify_active_call_number(self.droid0, 1)
        calls = self.droid0.telecomPhoneGetCallIds()
        call_one_id = calls[0]
        self.log.info("Step2: Call From PhoneA to PhoneC.")
        call_process(self.log, self.droid0, self.droid2,
                     self.ed0, self.ed2, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_2)
        verify_active_call_number(self.droid0, 2)
        calls = self.droid0.telecomPhoneGetCallIds()
        call_two_id = calls[1]
        self.log.info("Step3: Merge to Conf Call and verify Conf Call.")
        self.droid0.telecomJoinCallsInConf(call_one_id, call_two_id)
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 3)
        droids = [self.droid0, self.droid1, self.droid2]
        verify_incall_state(self.log, droids, True)
        self.log.info("Step4: End call on PhoneC and verify call continues.")
        self.droid2.telecomEndCall()
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 1)
        droids = [self.droid0, self.droid1]
        verify_incall_state(self.log, droids, True)
        droids = [self.droid2]
        verify_incall_state(self.log, droids, False)
        call_AB = self.droid0.telecomPhoneGetCallIds()[0]
        self.log.info("Step5: Call from PhoneC to PhoneA.")
        call_process(self.log, self.droid2, self.droid0,
                     self.ed2, self.ed0, self.time_wait_in_call,
                     self.phone_number_2, self.phone_number_0)
        verify_active_call_number(self.droid0, 2)
        self.log.info("Step6: Merge to Conf Call and verify Conf Call.")
        call_AC = None
        calls = self.droid0.telecomPhoneGetCallIds()
        for call in calls:
            if call != call_AB:
                call_AC = call
        self.droid0.telecomJoinCallsInConf(call_AB, call_AC)
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 3)
        droids = [self.droid0, self.droid1, self.droid2]
        verify_incall_state(self.log, droids, True)
        self.log.info("Step7: End from A to C and verify call continues")
        self.droid0.telecomCallDisconnect(call_AC)
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 1)
        droids = [self.droid0, self.droid1]
        verify_incall_state(self.log, droids, True)
        droids = [self.droid2]
        verify_incall_state(self.log, droids, False)
        self.droid0.telecomEndCall()
        return True

    def test_pretest_ensure_lte_volte(self):
        """Pretest operation: ensure preferred network is LTE and VoLTE enabled.

        Set preferred network to LTE.
        Toggle ON/OFF airplane mode.
        Enable VoLTE.
        """
        for droid in [self.droid0, self.droid1, self.droid2]:
            set_preferred_network_type(droid, "LTE")
        for (droid,ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1),
                           (self.droid2, self.ed2)]:
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        for droid in [self.droid0, self.droid1, self.droid2]:
            toggle_volte(droid, True)
        return True

    def test_conf_call_volte(self):
        """Test Conf Call VoLTE case among three phones.

        Make Sure phone is on LTE mode.
        Call from PhoneA to PhoneB, accept on PhoneB.
        Call from PhoneA to PhoneC, accept on PhoneC.
        On PhoneA, merge to conference call.
        End call on PhoneB, verify call continues.
        Disable VoLTE on PhoneB.
        Call from PhoneB to PhoneC, accept on PhoneC.
        On PhoneC, merge to conference call.
        End call on PhoneA, verify call continues.

        Returns:
            True if pass; False if fail.
        """
        #TODO(yangxliu): Add code to check voice. Currently only check status.
        #Check if VoLTE is enabled by platform before proceed this test case.
        for droid in [self.droid0, self.droid1, self.droid2]:
            if not droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                self.log.error("VoLTE is not supported by platform.")
                return False
        #Wait for droids in LTE mode, before proceed VoLTE call.
        #TODO(yangxliu): replace loop time wait with SL4A event.
        for droid in [self.droid0, self.droid1, self.droid2]:
            max_wait_time = self.max_wait_time_for_lte
            while droid.getNetworkType() != "lte":
                time.sleep(1)
                max_wait_time = max_wait_time - 1
                if max_wait_time < 0:
                    self.log.error("Phone not in LTE mode.")
                    return False
        self.log.info("Step1: Call From PhoneA to PhoneB.")
        call_process(self.log, self.droid0, self.droid1,
                     self.ed0, self.ed1, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_1)
        verify_active_call_number(self.droid0, 1)
        calls = self.droid0.telecomPhoneGetCallIds()
        call_one_id = calls[0]
        self.log.info("Step2: Call From PhoneA to PhoneC.")
        call_process(self.log, self.droid0, self.droid2,
                     self.ed0, self.ed2, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_2)
        verify_active_call_number(self.droid0, 2)
        calls = self.droid0.telecomPhoneGetCallIds()
        call_two_id = calls[1]
        self.log.info("Step3: Merge to Conf Call and verify Conf Call.")
        self.droid0.telecomJoinCallsInConf(call_one_id, call_two_id)
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 3)
        droids = [self.droid0, self.droid1, self.droid2]
        verify_incall_state(self.log, droids, True)
        self.log.info("Step4: End call on PhoneB and verify call continues.")
        self.droid1.telecomEndCall()
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid0, 1)
        droids = [self.droid0, self.droid2]
        verify_incall_state(self.log, droids, True)
        droids = [self.droid1]
        verify_incall_state(self.log, droids, False)
        self.log.info("Step5: Disable VoLTE PhoneB, Call from PhoneB to PhoneC.")
        toggle_volte(self.droid1, False)
        #Wait for disable volte to take effect in android system.
        time.sleep(0.5)
        #Make sure internet connection still valid at this time.
        verify_http_connection(self.droid1)
        call_process(self.log, self.droid1, self.droid2,
                     self.ed1, self.ed2, self.time_wait_in_call,
                     self.phone_number_1, self.phone_number_2)
        verify_active_call_number(self.droid2, 2)
        self.log.info("Step6: Merge to Conf Call and verify Conf Call.")
        calls = self.droid2.telecomPhoneGetCallIds()
        call_one_id = calls[0]
        call_two_id = calls[1]
        self.droid2.telecomJoinCallsInConf(call_one_id, call_two_id)
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid2, 3)
        droids = [self.droid0, self.droid1, self.droid2]
        verify_incall_state(self.log, droids, True)
        self.log.info("Step7: End call on A, and verify call continues")
        self.droid0.telecomEndCall()
        time.sleep(self.time_wait_in_call)
        verify_active_call_number(self.droid2, 1)
        droids = [self.droid1, self.droid2]
        verify_incall_state(self.log, droids, True)
        droids = [self.droid0]
        verify_incall_state(self.log, droids, False)
        self.droid2.telecomEndCall()
        for droid in [self.droid0, self.droid1, self.droid2]:
            toggle_volte(droid, False)
        return True
    """ Tests End """