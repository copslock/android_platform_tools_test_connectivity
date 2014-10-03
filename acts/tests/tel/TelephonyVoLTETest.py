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
    Test Script for Telephony Pre Check In Sanity
"""

import time
from base_test import BaseTestClass
from queue import Empty
from test_utils.tel.tel_test_utils import call_process
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_call_state
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import toggle_wifi_verify_data_connection
from test_utils.tel.tel_test_utils import verify_http_connection
from test_utils.wifi_test_utils import wifi_toggle_state

class TelephonyVoLTETest(BaseTestClass):
    TAG = "TelephonyVoLTETest"
    log_path = ''.join((BaseTestClass.log_path, TAG, "/"))

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.android_devices[1].get_droid()
        self.ed1.start()
        self.tests = (
                      "test_pretest_ensure_lte_volte",
                      "test_call_est_basic_volte",
                      "test_data_connectivity_lte_volte",
                      )
        self.phone_number_0 = None
        self.phone_number_1 = None
        self.time_wait_in_call = 10
        self.delay_between_test = 5
        self.max_wait_time_for_lte = 60

    def setup_class(self):
        if self.phone_number_0 is None:
            self.phone_number_0 = self.droid0.getLine1Number()
        if self.phone_number_1 is None:
            self.phone_number_1 = self.droid1.getLine1Number()
        if self.phone_number_0 is None or self.phone_number_1 is None :
            self.log.error("In setup can not get phone number")
            return False
        return True

    def teardown_test(self):
        for droid in [self.droid0, self.droid1]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        #Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    def _call_process_helper(self, params):
        """Wrapper function for _call_process.

        This is to wrap call_process, so it can be executed by generated
        test cases with a set of params.
        """
        (droid_caller, droid_callee, ed_caller,ed_callee, delay_in_call,
         caller_number, callee_number, droid_hangup) = params
        result = call_process(self.log, droid_caller, droid_callee,
                              ed_caller, ed_callee, delay_in_call,
                              caller_number, callee_number,
                              hangup = True, droid_hangup = droid_hangup)
        return result

    """ Tests Begin """
    def test_pretest_ensure_lte_volte(self):
        """Pretest operation: ensure preferred network is LTE and VoLTE enabled.

        Set preferred network to LTE.
        Toggle ON/OFF airplane mode.
        Enable VoLTE.
        """
        for droid in [self.droid0, self.droid1]:
            set_preferred_network_type(droid, "LTE")
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        for droid in [self.droid0, self.droid1]:
            toggle_volte(droid, True)
        return True

    def test_call_est_basic_volte(self):
        """ Test VoLTE call establishment basic ok on two phones.

        Make Sure phone is on LTE mode.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneB.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        #Wait for droids in LTE mode, before proceed VoLTE call.
        #TODO(yangxliu): replace loop time wait with SL4A event.
        for droid in [self.droid0, self.droid1]:
            max_wait_time = self.max_wait_time_for_lte
            while droid.getNetworkType() != "lte":
                time.sleep(1)
                max_wait_time = max_wait_time - 1
                if max_wait_time < 0:
                    self.log.error("Phone not in LTE mode.")
                    return False
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
        failed = self.run_generated_testcases("Call establish test",
                                              self._call_process_helper,
                                              params)
        self.log.debug("Failed ones: " + str(failed))
        if failed:
            return False
        return True

    def test_data_connectivity_lte_volte(self):
        """Data Connectivity test with LTE and VoLTE.

        Verify internet connection on LTE.
        Establish VoLTE call and verify internet connection.
        Disable VoLTE, make 3G call, verify internet connection.

        Returns:
            True if pass; False if fail.
        """
        self.log.info("Step1 verify internet on LTE.")
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.droid0.toggleDataConnection(True)
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        self.log.info("Step2 Establish VoLTE call.")
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5)
        if not result:
            self.log.error("VoLTE Call error.")
            return False
        self.log.info("Step3 Verify internet.")
        verify_http_connection(self.droid0)
        toggle_call_state(self.droid0, self.ed0, self.ed1, "hangup")
        self.log.info("Step4 Disable VoLTE and make 3G call.")
        toggle_volte(self.droid0, False)
        toggle_volte(self.droid1, False)
        verify_http_connection(self.droid0)
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5)
        if not result:
            self.log.error("3G Call error.")
            return False
        self.log.info("Step5 Verify internet.")
        verify_http_connection(self.droid0)
        toggle_call_state(self.droid0, self.ed0, self.ed1, "hangup")
        toggle_volte(self.droid0, True)
        toggle_volte(self.droid1, True)
        return True
    """ Tests End """