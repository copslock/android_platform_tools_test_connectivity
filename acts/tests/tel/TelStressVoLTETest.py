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
    Test Script for Telephony Stress VoLTE test
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
from test_utils.tel.tel_test_utils import wait_for_droid_in_network_type
from test_utils.utils import load_config

class TelStressVoLTETest(BaseTestClass):
    TAG = "TelStressVoLTETest"
    log_path = ''.join((BaseTestClass.log_path, TAG, "/"))

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.android_devices[1].get_droid()
        self.ed1.start()
        self.tests = (
                      "test_call_est_basic_volte",
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
            if get_network_type(droid, "data") != "lte":
                set_preferred_network_type(droid, "LTE")
                toggle_airplane_mode(self.log, droid, ed, True)
                toggle_airplane_mode(self.log, droid, ed, False)
        # Add delay to avoid possibility that:
        # Devices just turn off airplane mode, lte connection not stable
        # Then the first VoLTE call may fail due to CSFB in unstable LTE.
        time.sleep(self.delay_in_setup_class)
        for droid in [self.droid0, self.droid1]:
            toggle_volte(droid, True)
        # Add delay here to make sure phone is stable after enable VoLTE.
        time.sleep(self.delay_in_setup_class)
        return True

    def setup_test(self):
        self.log.info("Check & Wait for droids to be in LTE mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
        return True

    def teardown_test(self):
        for droid in [self.droid0, self.droid1]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        # Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    def _call_process_helper_VoLTE(self, params):
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
                              caller_mode_VoLTE = True, callee_mode_VoLTE = True)
        return result

    """ Tests Begin """
    def test_call_est_basic_volte(self):
        """ Test VoLTE call establishment basic ok on two phones.

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
                                                  self._call_process_helper_VoLTE,
                                                  params)
            self.log.debug("Failed ones: " + str(failed))
            total_exec = total_exec + 4;
            total_failed = total_failed + len(failed)
        if total_failed > 0:
            return False
        return True
    """ Tests End """
