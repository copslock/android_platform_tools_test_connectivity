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
from test_utils.tel.tel_test_utils import get_phone_number
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_call_state
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import toggle_wifi_verify_data_connection
from test_utils.tel.tel_test_utils import verify_http_connection
from test_utils.tel.tel_test_utils import wait_for_droid_in_network_type
from test_utils.utils import load_config
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
        # The path for "sim config file" should be set
        # in "testbed.config" entry "sim_conf_file".
        self.simconf = load_config(self.user_params["sim_conf_file"])
        self.time_wait_in_call = 10
        self.delay_between_test = 5
        self.max_wait_time_for_lte = 60

    def setup_class(self):
        for i,d in enumerate(self.droids):
            num = get_phone_number(d, self.simconf)
            assert num, "Fail to get phone number on {}".format(d)
            setattr(self,"phone_number_" + str(i), num)
            self.log.info("phone_number_{} : {}".format(str(i), num))
        return True

    def teardown_test(self):
        for droid in [self.droid0, self.droid1]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        # Leave the delay time for droid recover to idle from last test.
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
                              hangup = True, droid_hangup = droid_hangup,
                              verify_call_mode_caller = True,
                              verify_call_mode_callee = True,
                              caller_mode_VoLTE = True, callee_mode_VoLTE = True)
        return result

    """ Tests Begin """
    def test_pretest_ensure_lte_volte(self):
        """Pretest operation: ensure preferred network is LTE and VoLTE enabled.

        Set preferred network to LTE.
        Toggle ON/OFF airplane mode.
        Enable VoLTE.
        """
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            if droid.getNetworkType() != "lte":
                set_preferred_network_type(droid, "LTE")
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
        # Wait for droids in LTE mode, before proceed VoLTE call.
        self.log.info("Waiting for droids to be in LTE mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
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
        # Wait for droids in LTE mode, before proceed VoLTE call.
        self.log.info("Waiting for droids to be in LTE mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
        self.log.info("Step1 verify internet on LTE.")
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.droid0.toggleDataConnection(True)
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        self.log.info("Step2 Establish VoLTE call.")
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5,
                              verify_call_mode_caller = True,
                              verify_call_mode_callee = True,
                              caller_mode_VoLTE = True,
                              callee_mode_VoLTE = True)
        if not result:
            self.log.error("VoLTE Call error.")
            return False
        self.log.info("Step3 Verify internet.")
        verify_http_connection(self.droid0)
        toggle_call_state(self.droid0, self.ed0, self.ed1, "hangup")
        self.log.info("Step4 Disable VoLTE and make 3G call.")
        toggle_volte(self.droid0, False)
        toggle_volte(self.droid1, False)
        # Wait for phone to be completely idle before proceed another nonVoLTE
        # call.
        # TODO(yangxliu): Replace hard coded wait to SL4A event wait.
        time.sleep(5)
        verify_http_connection(self.droid0)
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5,
                              verify_call_mode_caller = True,
                              verify_call_mode_callee = True,
                              caller_mode_VoLTE = False,
                              callee_mode_VoLTE = False)
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