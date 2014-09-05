#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014 - The Android Open Source Project
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
from base_test import BaseTestClass
from test_utils.tel_test_utils import call_process
from test_utils.tel_test_utils import toggle_airplane_mode
from test_utils.wifi_test_utils import wifi_toggle_state

class TelephonyPreCheckInSanityTest(BaseTestClass):
    TAG = "TelephonyPreCheckInSanityTest"
    log_path = ''.join((BaseTestClass.log_path, TAG, "/"))

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.android_devices[1].get_droid()
        self.ed1.start()
        self.tests = (
                      "test_call_est_basic",
                      "test_airplane_mode_basic_attach_detach_connectivity",
                      )
        self.phone_number_0 = None
        self.phone_number_1 = None
        self.time_wait_in_call = 10

    def setup_class(self):
        if self.phone_number_0 is None:
            self.phone_number_0 = self.droid0.getLine1Number()
        if self.phone_number_1 is None:
            self.phone_number_1 = self.droid1.getLine1Number()
        if self.phone_number_0 is None or self.phone_number_1 is None :
            self.log.error("In setup can not get phone number")
            return False
        return True

    def _call_process_helper(self, params):
        """Wrapper function for _call_process.

        This is to wrap call_process, so it can be execuated by generated
        testcases with a set of params.
        """
        (droid_caller, droid_callee, droid_hangup, ed_caller,
         ed_callee, delay_in_call, caller_number, callee_number) = params
        result = call_process(self.log, droid_caller, droid_callee,
                              droid_hangup, ed_caller, ed_callee, delay_in_call,
                              caller_number, callee_number)
        return result

    """ Tests Begin """
    def test_call_est_basic(self):
        """ Test call establishment basic ok on two phones.

        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        toggle_airplane_mode(self.log, self.droid0, self.ed0, True)
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, True)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        call_params = [(self.droid0, self.droid1, self.droid0,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1),
                       (self.droid1, self.droid0, self.droid0,
                        self.ed1, self.ed0, self.time_wait_in_call,
                        self.phone_number_1, self.phone_number_0),
                       (self.droid0, self.droid1, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1)]
        params = list(call_params)
        failed = self.run_generated_testcases("Call establish test",
                                              self._call_process_helper,
                                              params)
        self.log.debug("Failed ones: " + str(failed))
        if failed:
            return False
        return True

    def test_airplane_mode_basic_attach_detach_connectivity(self):
        """ Test airplane mode basic on Phone and Live SIM.

        Turn on airplane mode to make sure deatch.
        Turn off airplane mode to make sure attach.
        Verify voice call and internet connection.

        Returns:
            True if pass; False if fail.
        """
        self.log.debug("Step1 ensure attach: " + self.phone_number_0)
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        self.log.debug("Step2 enable airplane mode and ensure detach: " +
                      self.phone_number_0)
        toggle_airplane_mode(self.log, self.droid0, self.ed0, True)
        self.log.debug("Step3 disable airplane mode and ensure attach: " +
                      self.phone_number_0)
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        self.log.debug("Step4 verify voice call: " + self.phone_number_0)
        result_call = call_process(self.log, self.droid0, self.droid1,
                                   self.droid0, self.ed0, self.ed1,
                                   self.time_wait_in_call,
                                   self.phone_number_0, self.phone_number_1)
        if not result_call:
            self.log.error("Step4 verify call error")
        self.log.debug("Step5 verify internet: " + self.phone_number_0)
        wifi_toggle_state(self.droid0, self.ed0, False)
        result_internet = self.droid0.networkIsConnected()
        network_type = self.droid0.networkGetConnectionType()
        if not result_internet or not network_type == "MOBILE":
            self.log.error("Step5 verify internet error")
            return False
        if not result_call:
            return False
        return True
    """ Tests End """