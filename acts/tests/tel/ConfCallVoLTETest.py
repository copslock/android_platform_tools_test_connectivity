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
    Test Script for Telephony Conference Call VoLTE
"""

import time
from base_test import BaseTestClass
from queue import Empty
from test_utils.tel.tel_test_utils import call_process
from test_utils.tel.tel_test_utils import get_network_type
from test_utils.tel.tel_test_utils import get_operator_name
from test_utils.tel.tel_test_utils import get_phone_number
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import verify_active_call_number
from test_utils.tel.tel_test_utils import verify_http_connection
from test_utils.tel.tel_test_utils import verify_incall_state
from test_utils.tel.tel_test_utils import wait_for_droid_in_network_type
from test_utils.utils import load_config

class ConfCallVoLTETest(BaseTestClass):
    TAG = "ConfCallVoLTETest"
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
                      "test_conf_call_volte",
                      )
        # The path for "sim config file" should be set
        # in "testbed.config" entry "sim_conf_file".
        self.simconf = load_config(self.user_params["sim_conf_file"])
        self.time_wait_in_call = 30
        self.delay_between_test = 5
        self.max_wait_time_for_lte = 120

    def setup_class(self):
        for i,d in enumerate(self.droids):
            num = get_phone_number(d, self.simconf)
            assert num, "Fail to get phone number on {}".format(d)
            setattr(self,"phone_number_" + str(i), num)
            self.log.info("phone_number_{} : {} <{}>".format(i, num,
                                                             get_operator_name(d)))
        # Only droid0 and droid1 required to be LTE
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            if get_network_type(droid, "data") != "lte":
                set_preferred_network_type(droid, "LTE")
                toggle_airplane_mode(self.log, droid, ed, True)
                toggle_airplane_mode(self.log, droid, ed, False)
        for droid in [self.droid0, self.droid1]:
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, True)
        return True

    def teardown_test(self):
        droids = [self.droid0, self.droid1, self.droid2]
        for droid in droids:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        # Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    """ Tests Begin """
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
        # TODO(yangxliu): Add code to check voice. Currently only check status.
        # Check if VoLTE is enabled by platform before proceed this test case.
        # PhoneA and PhoneB are required to have VoLTE.
        # PhoneC is OK to use non-VoLTE phone.
        for droid in [self.droid0, self.droid1]:
            if not droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                self.log.error("VoLTE is not supported by platform on {}.".
                               format(droid))
                return False
        # Wait for droids in LTE mode, before proceed VoLTE call.
        wait_for_droid_in_network_type(self.log,
                                       [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
        self.log.info("Step1: Call From PhoneA to PhoneB.")
        call_process(self.log, self.droid0, self.droid1,
                     self.ed0, self.ed1, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_1,
                     verify_call_mode_caller = True,
                     verify_call_mode_callee = True,
                     caller_mode_VoLTE = True,
                     callee_mode_VoLTE = True)
        verify_active_call_number(self.droid0, 1)
        calls = self.droid0.telecomPhoneGetCallIds()
        call_one_id = calls[0]
        self.log.info("Step2: Call From PhoneA to PhoneC.")
        call_process(self.log, self.droid0, self.droid2,
                     self.ed0, self.ed2, self.time_wait_in_call,
                     self.phone_number_0, self.phone_number_2,
                     verify_call_mode_caller = True,
                     verify_call_mode_callee = False,
                     caller_mode_VoLTE = True,
                     callee_mode_VoLTE = False)
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
        # In Non-VoLTE Conf call, we need to :
        # verify_active_call_number(self.droid0, 1).
        # However, in VoLTE Conf Call, the number of calls in Conf host is still
        # 3 at this point.
        # So in here print the calls in host as log.info.
        calls = self.droid0.telecomPhoneGetCallIds()
        self.log.info("Current active calls in Conf host: {}. Total: {}".
                      format(calls, len(calls)))
        droids = [self.droid0, self.droid2]
        verify_incall_state(self.log, droids, True)
        droids = [self.droid1]
        verify_incall_state(self.log, droids, False)
        self.log.info("Step5: Disable VoLTE PhoneB, Call from PhoneB to PhoneC.")
        toggle_volte(self.droid1, False)
        # Wait for disable volte to take effect in android system.
        time.sleep(5)
        # Make sure internet connection still valid at this time.
        verify_http_connection(self.droid1)
        call_process(self.log, self.droid1, self.droid2,
                     self.ed1, self.ed2, self.time_wait_in_call,
                     self.phone_number_1, self.phone_number_2,
                     verify_call_mode_caller = True,
                     verify_call_mode_callee = False,
                     caller_mode_VoLTE = False,
                     callee_mode_VoLTE = False)
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
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, True)
        time.sleep(5)
        verify_active_call_number(self.droid0, 0)
        verify_active_call_number(self.droid1, 0)
        verify_active_call_number(self.droid2, 0)
        return True
    """ Tests End """