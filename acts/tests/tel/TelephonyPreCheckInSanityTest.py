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
from test_utils.tel.tel_enum import TelEnums
from test_utils.tel.tel_test_utils import call_process
from test_utils.tel.tel_test_utils import get_network_type
from test_utils.tel.tel_test_utils import get_operator_name
from test_utils.tel.tel_test_utils import get_phone_number
from test_utils.tel.tel_test_utils import set_preferred_network_type
from test_utils.tel.tel_test_utils import sms_send_receive_verify
from test_utils.tel.tel_test_utils import toggle_airplane_mode
from test_utils.tel.tel_test_utils import toggle_call_state
from test_utils.tel.tel_test_utils import toggle_volte
from test_utils.tel.tel_test_utils import toggle_wifi_verify_data_connection
from test_utils.tel.tel_test_utils import verify_http_connection
from test_utils.tel.tel_test_utils import wait_for_data_connection_status
from test_utils.tel.tel_test_utils import wait_for_droid_in_network_type
from test_utils.utils import load_config
from test_utils.wifi_test_utils import reset_droid_wifi
from test_utils.wifi_test_utils import start_wifi_connection_scan
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
                      "test_pretest_ensure_lte",
                      "test_sms_basic",
                      "test_call_est_basic_csfb",
                      "test_airplane_mode_basic_attach_detach_connectivity",
                      "test_data_pretest_ensure_wifi_connect_to_live_network",
                      "test_data_conn_network_switching",
                      "test_data_connectivity_lte",
                      "test_pretest_ensure_3g",
                      "test_call_est_basic_3g",
                      "test_data_connectivity_3g",
                      "test_sms_basic",
                      )
        # The path for "sim config file" should be set
        # in "testbed.config" entry "sim_conf_file".
        self.simconf = load_config(self.user_params["sim_conf_file"])
        self.time_wait_in_call = 15
        self.delay_between_test = 5
        self.max_wait_time_for_lte = 120
        self.live_network_ssid = "GoogleGuest"

    def setup_class(self):
        for i,d in enumerate(self.droids):
            num = get_phone_number(d, self.simconf)
            assert num, "Fail to get phone number on {}".format(d)
            setattr(self,"phone_number_" + str(i), num)
            self.log.info("phone_number_{} : {} <{}>".format(i, num,
                                                             get_operator_name(d)))
        self.operator_name_droid0 = get_operator_name(self.droid0)
        for droid in [self.droid0, self.droid1]:
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, False)
        return True

    def teardown_test(self):
        for droid in [self.droid0, self.droid1]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
        # Leave the delay time for droid recover to idle from last test.
        time.sleep(self.delay_between_test)
        return True

    def _call_process_helper_NonVoLTE(self, params):
        """Wrapper function for _call_process.

        This is to wrap call_process, so it can be executed by generated
        testcases with a set of params.
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
    def test_pretest_ensure_lte(self):
        """Pretest operation: ensure preferred network is LTE.

        Set preferred network to LTE.
        Toggle ON/OFF airplane mode.
        """
        for droid in [self.droid0, self.droid1]:
            set_preferred_network_type(droid, "LTE")
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        self.log.info("Waiting for droids to be in LTE mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
        return True

    def test_call_est_basic_csfb(self):
        """ Test call establishment basic ok on two phones. (LTE CSFB call)

        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        # Wait for droids in LTE mode, before proceed call.
        self.log.info("Waiting for droids to be in LTE mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "lte")
        call_params = [(self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid0),
                       (self.droid1, self.droid0,
                        self.ed1, self.ed0, self.time_wait_in_call,
                        self.phone_number_1, self.phone_number_0, self.droid0),
                       (self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid1)]
        params = list(call_params)
        failed = self.run_generated_testcases("Call establish test",
                                              self._call_process_helper_NonVoLTE,
                                              params)
        self.log.debug("Failed ones: " + str(failed))
        if failed:
            return False
        return True

    def test_airplane_mode_basic_attach_detach_connectivity(self):
        """ Test airplane mode basic on Phone and Live SIM.

        Turn on airplane mode to make sure detach.
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
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.log.debug("Step4 verify voice call: " + self.phone_number_0)
        result_call = call_process(self.log, self.droid0, self.droid1,
                                   self.ed0, self.ed1,
                                   self.time_wait_in_call,
                                   self.phone_number_0, self.phone_number_1,
                                   hangup = True, droid_hangup = self.droid0)
        if not result_call:
            self.log.error("Step4 verify call error")
        wait_for_data_connection_status(self.log, self.droid0, self.ed0, True)
        self.log.debug("Step5 verify internet: " + self.phone_number_0)
        result_internet = self.droid0.networkIsConnected()
        network_type = self.droid0.networkGetActiveConnectionTypeName()
        if (not result_internet or
            not (network_type == "MOBILE" or network_type == "Cellular")):
            self.log.error("Step5 internet error. Network type: " + network_type)
            return False
        verify_http_connection(self.droid0)
        if not result_call:
            return False
        return True

    def test_data_pretest_ensure_wifi_connect_to_live_network(self):
        """Pre test for network switching.

        This is pre test for network switching.
        The purpose is to make sure the phone can connect to live network by WIFI.

        Returns:
            True if pass.
        """
        reset_droid_wifi(self.droid0, self.ed0)
        wifi_toggle_state(self.droid0, self.ed0, True)
        start_wifi_connection_scan(self.droid0, self.ed0)
        wifi_results = self.droid0.wifiGetScanResults()
        self.log.debug(str(wifi_results))
        self.droid0.wifiStartTrackingStateChange()
        nId = self.droid0.wifiAddNetwork(self.live_network_ssid)
        self.droid0.wifiEnableNetwork(nId, True)
        self.ed0.pop_event("WifiNetworkConnected")
        return True

    def test_data_conn_network_switching(self):
        """Test data connection network switching.

        Before test started, ensure wifi can connect to live network,
        airplane mode is off, data connection is on, wifi is on.
        Turn off wifi, verify data is on cell and browse to google.com is ok.
        Turn on wifi, verify data is on wifi and browse to google.com is ok.
        Turn off wifi, verify data is on cell and browse to google.com is ok.

        Returns:
            True if pass.
        """
        self.droid0.phoneStartTrackingDataConnectionStateChange()
        self.log.info("Step1 Airplane Off, Wifi On, Data On.")
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        wifi_toggle_state(self.droid0, self.ed0, True)
        self.droid0.toggleDataConnection(True)
        self.log.info("Step2 Wifi is Off, Data is on Cell.")
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        self.log.info("Step3 Wifi is On, Data is on Wifi.")
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, True)
        self.log.info("Step4 Wifi is Off, Data is on Cell.")
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        return True

    def test_data_connectivity_lte(self):
        """Test LTE data connection before call and in call.

        Turn off airplane, turn off wifi, turn on data, verify internet.
        Initial call and accept.
        Verify internet.
        Hangup and turn data back on.
        """
        self.droid0.phoneStartTrackingDataConnectionStateChange()
        self.log.info("Step1 Airplane Off, Wifi Off, Data On, verify internet.")
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.droid0.toggleDataConnection(True)
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        self.log.info("Step2 Initiate call and accept.")
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5,
                              self.phone_number_0, self.phone_number_1)
        if not result:
            self.log.error("Call error.")
            return False
        # Only Tmo run step 3, Vzw does not.
        # Look up for network technology (current in use) from TelEnums.network_tbl
        # Look up for True or False from TelEnums.test_tbl
        network_technology = TelEnums.network_tbl[self.operator_name_droid0]["3g"]
        if TelEnums.test_tbl["verify data during call"][network_technology]:
            self.log.info("Step3 Verify internet.")
            verify_http_connection(self.droid0)
        else:
            self.log.info("Skip Verify internet.")
        toggle_call_state(self.droid0, self.ed0, self.ed1, "hangup")
        return True

    def test_pretest_ensure_3g(self):
        """Pretest operation: ensure preferred network is 3G.

        Set preferred network to 3G.
        Toggle ON/OFF airplane mode.
        """
        for droid in [self.droid0, self.droid1]:
            set_preferred_network_type(droid, "3g")
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        self.log.info("Waiting for droids to be in 3g mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        return True

    def test_call_est_basic_3g(self):
        """ Test call establishment basic ok on two phones. (3g call)

        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        # Wait for droids in 3g mode, before proceed call.
        self.log.info("Waiting for droids to be in 3g mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        call_params = [(self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid0),
                       (self.droid1, self.droid0,
                        self.ed1, self.ed0, self.time_wait_in_call,
                        self.phone_number_1, self.phone_number_0, self.droid0),
                       (self.droid0, self.droid1,
                        self.ed0, self.ed1, self.time_wait_in_call,
                        self.phone_number_0, self.phone_number_1, self.droid1)]
        params = list(call_params)
        failed = self.run_generated_testcases("Call establish test",
                                              self._call_process_helper_NonVoLTE,
                                              params)
        self.log.debug("Failed ones: " + str(failed))
        if failed:
            return False
        return True

    def test_data_connectivity_3g(self):
        """Test 3G data connection before call and in call.

        Turn off airplane, turn off wifi, turn on data, verify internet.
        Initial call and accept.
        Verify internet.
        Turn off data and verify not connected.
        Hangup and turn data back on.

        Returns:
            True if success.
            False if failed.
        """
        result = False
        # Wait for droids in 3g mode, before proceed.
        self.log.info("Waiting for droids to be in 3g mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        self.droid0.phoneStartTrackingDataConnectionStateChange()
        self.log.info("Step1 Airplane Off, Wifi Off, Data On, verify internet.")
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.droid0.toggleDataConnection(True)
        toggle_wifi_verify_data_connection(self.log, self.droid0,
                                           self.ed0, False)
        self.log.info("Step2 Initiate call and accept.")
        result = call_process(self.log, self.droid0, self.droid1,
                              self.ed0, self.ed1, 5,
                              self.phone_number_0, self.phone_number_1)
        if not result:
            self.log.error("Step2 initiate call failed.")
            return False
        # Only Tmo run step 3, Vzw does not.
        # Look up for network technology (current in use) from TelEnums.network_tbl
        # Look up for True or False from TelEnums.test_tbl
        network_technology = TelEnums.network_tbl[self.operator_name_droid0]["3g"]
        if TelEnums.test_tbl["verify data during call"][network_technology]:
            self.log.info("Step3 Verify internet.")
            verify_http_connection(self.droid0)
            self.log.info("Step4 Turn off data and verify not connected.")
            self.droid0.toggleDataConnection(False)
            wait_for_data_connection_status(self.log, self.droid0, self.ed0, False)
            result = True
            try:
                verify_http_connection(self.droid0)
            except Exception:
                result = False
            if result:
                self.log.error("Step4 turn off data failed.")
                return False
            self.droid0.toggleDataConnection(True)
            wait_for_data_connection_status(self.log, self.droid0, self.ed0, True)
        else:
            self.log.info("Skip Verify internet.")
        self.log.info("Step5 Hang up.")
        toggle_call_state(self.droid0, self.ed0, self.ed1, "hangup")
        # Wait for droids back in 3g mode.
        self.log.info("Step6 Waiting for droids back in 3g mode.")
        wait_for_droid_in_network_type(self.log, [self.droid0, self.droid1],
                                       self.max_wait_time_for_lte, "3g")
        return True

    def test_sms_basic(self):
        """Test SMS basic function between two phone.

        Airplane mode is off.
        Send SMS from PhoneA to PhoneB.
        Verify received message on PhoneB is correct.

        Returns:
            True if success.
            False if failed.
        """
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        sms_send_receive_verify(self.log, self.droid0, self.droid1,
                                self.phone_number_0,
                                self.phone_number_1,
                                self.ed0, self.ed1, 50)
        sms_send_receive_verify(self.log, self.droid0, self.droid1,
                                self.phone_number_0,
                                self.phone_number_1,
                                self.ed0, self.ed1, 160)
        sms_send_receive_verify(self.log, self.droid0, self.droid1,
                                self.phone_number_0,
                                self.phone_number_1,
                                self.ed0, self.ed1, 180)
        sms_send_receive_verify(self.log, self.droid1, self.droid0,
                                self.phone_number_1,
                                self.phone_number_0,
                                self.ed1, self.ed0, 50)
        sms_send_receive_verify(self.log, self.droid1, self.droid0,
                                self.phone_number_1,
                                self.phone_number_0,
                                self.ed1, self.ed0, 160)
        sms_send_receive_verify(self.log, self.droid1, self.droid0,
                                self.phone_number_1,
                                self.phone_number_0,
                                self.ed1, self.ed0, 180)
        return True
    """ Tests End """