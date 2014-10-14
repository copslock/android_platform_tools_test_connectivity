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
    Test Script for Telephony Stress 3g test
"""

import time
from base_test import BaseTestClass
from queue import Empty
from test_utils.tel.tel_test_utils import call_process
from test_utils.tel.tel_test_utils import get_operator_name
from test_utils.tel.tel_test_utils import get_phone_number
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import wait_for_droid_in_network_type
from test_utils.utils import load_config

class TelStress3gTest(BaseTestClass):
    TAG = "TelStress3gTest"
    log_path = ''.join((BaseTestClass.log_path, TAG, "/"))

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.android_devices[1].get_droid()
        self.ed1.start()
        self.tests = (
                      "test_call_est_basic_3g",
                      )
        # The path for "sim config file" should be set
        # in "testbed.config" entry "sim_conf_file".
        self.simconf = load_config(self.user_params["sim_conf_file"])
        self.stress_test_number = self.user_params["stress_test_number"]
        self.time_wait_in_call = 15
        self.delay_between_test = 5
        self.delay_in_setup_class = 5
        self.max_wait_time_for_lte = 120

    def setup_class(self):
        for i,d in enumerate(self.droids):
            num = get_phone_number(d, self.simconf)
            assert num, "Fail to get phone number on {}".format(d)
            setattr(self,"phone_number_" + str(i), num)
            self.log.info("phone_number_{} : {} <{}>".format(i, num,
                                                             get_operator_name(d)))
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            set_preferred_network_type(droid, "3g")
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        # Add delay to avoid possible unstable connection.
        time.sleep(self.delay_in_setup_class)
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        for droid in [self.droid0, self.droid1]:
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, False)
        # Add delay here to make sure phone is stable after disable VoLTE.
        time.sleep(self.delay_in_setup_class)
        return True

    def setup_test(self):
        self.log.info("Check & Wait for droids to be in 3g mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        return True

    def teardown_test(self):
        for droid in [self.droid0, self.droid1]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        # Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    def _call_process_helper_3g(self, params):
        """Wrapper function for _call_process.

        This is to wrap call_process, so it can be executed by generated
        test cases with a set of params.
        """
        (droid_caller, droid_callee, ed_caller,ed_callee, delay_in_call,
         caller_number, callee_number, droid_hangup) = params
        result = call_process(self.log, droid_caller, droid_callee,
                              ed_caller, ed_callee, delay_in_call,
                              caller_number, callee_number,
                              hangup = True, droid_hangup = droid_hangup,
                              verify_call_mode_caller = True,
                              verify_call_mode_callee = True,
                              caller_mode_VoLTE = False, callee_mode_VoLTE = False)
        return result

    """ Tests Begin """
    def test_call_est_basic_3g(self):
        """ Test 3g call establishment basic ok on two phones.

        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneB.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        call_params = [(self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid0),
                       (self.droid1, self.droid0,
                        self.ed1, self.ed0, self.time_wait_in_call,
                        self.phone_number_1, self.phone_number_0, self.droid1),
                       (self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid0),
                       (self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid1)]
        params = list(call_params)
        total_exec = 0;
        total_failed = 0;
        for i in range(int(self.stress_test_number)):
            self.log.info("Finished <{}>/<{}> loop in stress test. {}/{} failed".
                          format(i, self.stress_test_number, total_failed,
                                 total_exec))
            failed = self.run_generated_testcases("Call establish test",
                                                  self._call_process_helper_3g,
                                                  params)
            self.log.debug("Failed ones: " + str(failed))
            total_exec = total_exec + 4;
            total_failed = total_failed + len(failed)
        if total_failed > 0:
            return False
        return True
    """ Tests End """
