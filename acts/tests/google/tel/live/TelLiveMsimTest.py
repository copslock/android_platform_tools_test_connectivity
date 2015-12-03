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
    Test Script for MSIM
"""

import time
from acts.base_test import BaseTestClass
from queue import Empty
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_test_utils import *
from acts.utils import load_config
from acts.test_utils.wifi_test_utils import reset_droid_wifi
from acts.test_utils.wifi_test_utils import start_wifi_connection_scan
from acts.test_utils.wifi_test_utils import wifi_toggle_state

class TelLiveMsimTest(TelephonyBaseTest):

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.droid0 = self.droid
        self.ed0 = self.ed
        self.droid1, self.ed1 = self.droids[1], self.eds[1]
        self.tests = (
                      "test_data_connection_on_each_sim",
                      "test_call_est_basic_on_each_sim",
                      "test_sms_basic_on_each_sim",
                      "test_airplane_mode_basic_attach_detach_connectivity",
                      "test_data_pretest_ensure_wifi_connect_to_live_network",
                      "test_data_conn_network_switching",
                      "test_pretest_ensure_3g",
                      "test_data_connectivity_3g",
                      )
        # The path for "sim config file" should be set
        # in "testbed.config" entry "sim_conf_file".
        self.simconf = load_config(self.user_params["sim_conf_file"])
        self.time_wait_in_call = 15
        self.wifi_network_ssid = "GoogleGuest"

    def setup_class(self):
        self.phone_number_0 = None
        self.phone_number_0_sim0 = None
        self.phone_number_0_sim1 = None
        self.operator_name_droid0 = None
        self.operator_name_droid0_sim0 = None
        self.operator_name_droid0_sim1 = None
        self.phone_number_tbl = {}
        self.operator_tbl = {}
        wait_for_droid_in_network_rat(self.log, self.droid1, RAT_LTE,
                                      WAIT_TIME_NW_SELECTION,
                                      NETWORK_SERVICE_VOICE)

        # self.droid0 (PhonaA) is MSIM device.
        # phone_number_0_sim0 and phone_number_0_sim1 are numbers for MSIM device.
        # self.droid1 (PhoneB) is test harness to test MSIM device.
        subInfo = self.droid0.subscriptionGetAllSubInfoList()
        for i in range(len(subInfo)):
            subId = subInfo[i]["subId"]
            simserial = subInfo[i]["iccId"]
            num = self.simconf[simserial]["phone_num"]
            assert num, "Fail to get phone number on phoneA sim{}".format(i)
            self.phone_number_tbl[subId] = num
            setattr(self,"phone_number_0_sim" + str(i), num)
            # TODO: we shouldn't access TelEnums directly: create accessor func
            operator_name = get_operator_name(
                self.droid0.getSimOperatorBySubId(subId))
            self.operator_tbl[subId] = operator_name
            setattr(self,"operator_name_droid0_sim" + str(i), operator_name)
            self.log.info("Information for PhoneA subId: {}".format(subId))
            self.log.info("phone_number_0_sim{} : {} <{}>".format(i, num,
                                                                  operator_name))
            self.log.info("IMEI: {}".
                          format(self.droid0.getDeviceIdBySlotId(subInfo[i]["slotId"])))
            self.log.info("Roaming: {}".
                          format(self.droid0.checkNetworkRoamingBySubId(subId)))
            self.log.info("Current Network Type: Voice {}, Data {}.".
                          format(self.droid0.getVoiceNetworkTypeForSubscriber(subId),
                                 self.droid0.getDataNetworkTypeForSubscriber(subId)))

        self.phone_number_1 = get_phone_number(self.log, self.droid1, self.simconf)
        assert self.phone_number_1, "Fail to get phone number on PhoneB"
        self.log.info("phone_number_1 : {} <{}>".format(self.phone_number_1,
                                                        get_operator_name(self.log, self.droid1)))
        for droid in [self.droid0, self.droid1]:
            if droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
                toggle_volte(droid, False)
        return True

    def _setting_subId_for_voice_data_sms(self, droid, voice=None,
                                          data=None, sms=None):
        if voice:
            # droid.subscriptionSetDefaultVoiceSubId not working
            # if subscriptionSetDefaultVoiceSubId is called to set default subId
            # to make a call, then the outgoing subId will not change.
            # need to use the following one
            droid.telecomSetUserSelectedOutgoingPhoneAccount(str(voice))
        if data:
            droid.subscriptionSetDefaultDataSubId(str(data))
        if sms:
            droid.subscriptionSetDefaultSmsSubId(str(sms))
        time.sleep(5)
        # Wait to make sure settings take effect

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

    def gen_call_process_test_name(self, params):
        (droid_caller, droid_callee, ed_caller,ed_callee, delay_in_call,
         caller_number, callee_number, droid_hangup) = params
        return "test_call_{}_to_{}".format(caller_number, callee_number)

    """ Tests Begin """
    @TelephonyBaseTest.tel_test_wrap
    def test_data_connection_on_each_sim(self):
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        self.log.info("Turn off Wifi, turn on Data.")
        wifi_toggle_state(self.droid0, self.ed0, False)
        self.droid0.toggleDataConnection(True)

        subInfo = self.droid0.subscriptionGetAllSubInfoList()
        for i in range(len(subInfo)):
            subId = subInfo[i]["subId"]
            self.log.info("Setting Data/Voice/Sms to subId: {}".format(subId))
            self._setting_subId_for_voice_data_sms(self.droid0, subId, subId, subId)
            time.sleep(5)
            print(self.droid0.getDataConnectionState())
            if self.droid0.getDataConnectionState() != DATA_STATE_CONNECTED:
                result = wait_for_data_connection_status(self.log, self.droid0,
                                                          self.ed0, True)
                print("wait for connected")
                print(result)
                assert result, "Data not connected on PhoneA subId: {}".format(subId)
            self.droid0.toggleDataConnection(False)
            time.sleep(5)
            print(self.droid0.getDataConnectionState())
            if self.droid0.getDataConnectionState() != DATA_STATE_DISCONNECTED:
                result = wait_for_data_connection_status(self.log, self.droid0,
                                                          self.ed0, False)
                print("wait for disconnected")
                print(result)
                assert result, "Disable data fail on PhoneA subId: {}".format(subId)
            self.droid0.toggleDataConnection(True)
            time.sleep(5)
        return True

    @TelephonyBaseTest.tel_test_wrap
    def test_call_est_basic_on_each_sim(self):
        """ Test call establishment basic ok on two phones.

        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneA.
        Call from PhoneB to PhoneA, accept on PhoneA, hang up on PhoneA.
        Call from PhoneA to PhoneB, accept on PhoneB, hang up on PhoneB.

        Returns:
            True if pass; False if fail.
        """
        result = True
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        subInfo = self.droid0.subscriptionGetAllSubInfoList()

        for i in range(len(subInfo)):
            subId = subInfo[i]["subId"]
            self.log.info("Setting Data/Voice/Sms to subId: {}".format(subId))
            self._setting_subId_for_voice_data_sms(self.droid0, subId, subId, subId)
            self.phone_number_0 = self.phone_number_tbl[subId]
            self.operator_name_droid0 = self.operator_tbl[subId]
            call_params = [(self.droid0, self.droid1,
                            self.ed0, self.ed1, self.time_wait_in_call,
                            self.phone_number_0, self.phone_number_1, self.droid0),
                           (self.droid1, self.droid0,
                            self.ed1, self.ed0, self.time_wait_in_call,
                            self.phone_number_1, self.phone_number_0, self.droid0),
                           (self.droid0, self.droid1,
                            self.ed0, self.ed1, self.time_wait_in_call,
                            self.phone_number_0, self.phone_number_1, self.droid1),
                           (self.droid1, self.droid0,
                            self.ed1, self.ed0, self.time_wait_in_call,
                            self.phone_number_1, self.phone_number_0, self.droid1)]
            params = list(call_params)
            failed = self.run_generated_testcases(self._call_process_helper_NonVoLTE,
                                                  params,
                                                  name_func=self.gen_call_process_test_name)
            self.log.debug("Failed ones: " + str(failed))
            if failed:
                result = False
        return result

    @TelephonyBaseTest.tel_test_wrap
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
            # FIXME: Why doesn't this return a failure here!??!?
        wait_for_data_connection_status(self.log, self.droid0, self.ed0, True)

        self.log.debug("Step5 verify internet: " + self.phone_number_0)
        result_internet = self.droid0.connectivityNetworkIsConnected()
        network_type = connection_type_from_type_string(
            self.droid0.connectivityNetworkGetActiveConnectionTypeName())
        if not result_internet or network_type != NETWORK_CONNECTION_TYPE_CELL:
            self.log.error("Step5 internet error. Network type: " + network_type)
            return False

        verify_http_connection(self.log, self.droid0)
        if not result_call:
            return False
        return True

    @TelephonyBaseTest.tel_test_wrap
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
        nId = self.droid0.wifiAddNetwork(self.wifi_network_ssid)
        self.droid0.wifiEnableNetwork(nId, True)
        self.ed0.pop_event("WifiNetworkConnected")
        return True

    @TelephonyBaseTest.tel_test_wrap
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

    @TelephonyBaseTest.tel_test_wrap
    def test_pretest_ensure_3g(self):
        """Pretest operation: ensure preferred network is 3G.

        Set preferred network to 3G.
        Toggle ON/OFF airplane mode.
        """
        self._setting_subId_for_voice_data_sms(self.droid0, "2", "2", "2")
        self.phone_number_0 = self.phone_number_0_sim1
        self.operator_name_droid0 = self.operator_name_droid0_sim1


        for droid in [self.droid0, self.droid1]:
            set_preferred_network_type(droid, RAT_3G)
        for (droid, ed) in [(self.droid0, self.ed0), (self.droid1, self.ed1)]:
            toggle_airplane_mode(self.log, droid, ed, True)
            toggle_airplane_mode(self.log, droid, ed, False)
        self.log.info("Waiting for droids to be in 3g mode.")
        wait_for_droids_in_network_generation(
            self.log, [self.droid0, self.droid1], RAT_3G, WAIT_TIME_NW_SELECTION)
        return True

    @TelephonyBaseTest.tel_test_wrap
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
        wait_for_droids_in_network_generation(
            self.log, [self.droid0, self.droid1], RAT_3G, WAIT_TIME_NW_SELECTION)
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
        # Check in technology_tbl to see is this type can
        # do data and voice simultaneously or not.
        voice_technology = get_network_rat(self.droid0, NETWORK_SERVICE_VOICE)
        if is_rat_svd_capable(voice_technology):
            self.log.info("Step3 Verify internet.")
            verify_http_connection(self.log, self.droid0)
            self.log.info("Step4 Turn off data and verify not connected.")
            self.droid0.toggleDataConnection(False)
            wait_for_data_connection_status(self.log, self.droid0, self.ed0, False)
            result = True
            try:
                verify_http_connection(self.log, self.droid0)
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
        hangup_call(self.log, self.droid0)
        # Wait for droids back in 3g mode.
        self.log.info("Step6 Waiting for droids back in 3g mode.")
        wait_for_droids_in_network_generation(
            self.log, [self.droid0, self.droid1], RAT_3G,
                                              WAIT_TIME_NW_SELECTION)
        return True

    def _sms_process_helper(self, params):
        """Wrapper function for sms_send_receive_verify.

        This is to wrap sms_send_receive_verify, so it can be executed by
        generated testcases with a set of params.
        """
        (droid_tx, droid_rx, phone_number_tx,
         phone_number_rx, ed_tx, ed_rx, length) = params
        result = sms_send_receive_verify(self.log, droid_tx, droid_rx,
                                         phone_number_tx, phone_number_rx,
                                         ed_tx, ed_rx, length)
        return result

    def gen_sms_test_name(self, params):
        (droid_tx, droid_rx, phone_number_tx,
         phone_number_rx, ed_tx, ed_rx, length) = params
        return "test_sms_{}_to_{}".format(phone_number_tx, phone_number_rx)

    @TelephonyBaseTest.tel_test_wrap
    def test_sms_basic_on_each_sim(self):
        """Test SMS basic function between two phone.

        Airplane mode is off.
        Send SMS from PhoneA to PhoneB.
        Verify received message on PhoneB is correct.

        Returns:
            True if success.
            False if failed.
        """
        # Tmo->Att if longer than 160, test will fail
        # Seems it is carrier limit
        result = True
        toggle_airplane_mode(self.log, self.droid0, self.ed0, False)
        toggle_airplane_mode(self.log, self.droid1, self.ed1, False)
        subInfo = self.droid0.subscriptionGetAllSubInfoList()

        for i in range(len(subInfo)):
            subId = subInfo[i]["subId"]
            self.log.info("Setting Data/Voice/Sms to subId: {}".format(subId))
            self._setting_subId_for_voice_data_sms(self.droid0, subId, subId, subId)
            self.phone_number_0 = self.phone_number_tbl[subId]
            self.operator_name_droid0 = self.operator_tbl[subId]
            sms_params = [(self.droid0, self.droid1,
                           self.phone_number_0, self.phone_number_1,
                           self.ed0, self.ed1, 50),
                          (self.droid0, self.droid1,
                           self.phone_number_0, self.phone_number_1,
                           self.ed0, self.ed1, 160),
                          (self.droid0, self.droid1,
                           self.phone_number_0, self.phone_number_1,
                           self.ed0, self.ed1, 180),
                          (self.droid1, self.droid0,
                           self.phone_number_1, self.phone_number_0,
                           self.ed1, self.ed0, 50),
                          (self.droid1, self.droid0,
                           self.phone_number_1, self.phone_number_0,
                           self.ed1, self.ed0, 160),
                          (self.droid1, self.droid0,
                           self.phone_number_1, self.phone_number_0,
                           self.ed1, self.ed0, 180)]
            params = list(sms_params)
            failed = self.run_generated_testcases(self._sms_process_helper,
                                                  params,
                                                  name_func=self.gen_sms_test_name)
            self.log.debug("Failed ones: " + str(failed))
            if failed:
                result = False
        return result
    """ Tests End """

def call_process(log, ad_caller, ad_callee, delay_in_call,
                 caller_number=None, callee_number=None, delay_answer=1,
                 hangup=False, ad_hangup=None,
                 verify_call_mode_caller=False, verify_call_mode_callee=False,
                 caller_mode_VoLTE=None, callee_mode_VoLTE=None):
    """ Call process, including make a phone call from caller,
    accept from callee, and hang up.

    In call process, call from <droid_caller> to <droid_callee>,
    after ringing, wait <delay_answer> to accept the call,
    wait <delay_in_call> during the call process,
    (optional)then hang up from <droid_hangup>.

    Args:
        ad_caller: Caller Android Device Object.
        ad_callee: Callee Android Device Object.
        delay_in_call: Wait time in call process.
        caller_number: Optional, caller phone number.
            If None, will get number by SL4A.
        callee_number: Optional, callee phone number.
            if None, will get number by SL4A.
        delay_answer: After callee ringing state, wait time before accept.
            If None, default value is 1.
        hangup: Whether hangup in this function.
            Optional. Default value is False.
        ad_hangup: Android Device Object end the phone call.
            Optional. Default value is None.
        verify_call_mode_caller: Whether verify caller call mode (VoLTE or CS).
            Optional. Default value is False, not verify.
        verify_call_mode_callee: Whether verify callee call mode (VoLTE or CS).
            Optional. Default value is False, not verify.
        caller_mode_VoLTE: If verify_call_mode_caller is True,
            this is expected caller mode. True for VoLTE mode. False for CS mode.
            Optional. Default value is None.
        callee_mode_VoLTE: If verify_call_mode_callee is True,
            this is expected callee mode. True for VoLTE mode. False for CS mode.
            Optional. Default value is None.

    Returns:
        True if call process without any error.
        False if error happened.

    Raises:
        TelTestUtilsError if VoLTE check fail.
    """
    warnings.warn("tel_utils.call_process() is Deprecated"
                  " use tel_utils.call_setup_teardown()",
                  DeprecationWarning)

    if not caller_number:
        caller_number = ad_caller.droid.getLine1Number()
    if not callee_number:
        callee_number = ad_callee.droid.getLine1Number()
    if not caller_number or not callee_number:
        log.error("Caller or Callee number invalid.")
        return False

    log.info("Call from {} to {}".format(caller_number, callee_number))
    result = initiate_call(log, ad_caller, callee_number)
    if not result:
        log.error("Initiate call failed.")
        return False

    result = wait_and_answer_call(
        log, ad_callee, incoming_number=caller_number)
    if not result:
        log.error("Answer call fail.")
        return False

    time.sleep(1)  # ensure that all internal states are updated in telecom
    if (not ad_caller.droid.telecomIsInCall() or not
            ad_callee.droid.telecomIsInCall()):
        log.error("Call connection failed.")
        return False

    if verify_call_mode_caller:
        network_type = get_network_rat(log, ad_caller, NETWORK_SERVICE_VOICE)
        if caller_mode_VoLTE and network_type != RAT_LTE:
            raise TelTestUtilsError("Error: Caller not in VoLTE. Expected VoLTE. Type:{}".
                                    format(network_type))
            return False
        if not caller_mode_VoLTE and network_type == RAT_LTE:
            raise TelTestUtilsError("Error: Caller in VoLTE. Expected not VoLTE. Type:{}".
                                    format(network_type))
            return False
    if verify_call_mode_callee:
        network_type = get_network_rat(log, ad_callee, NETWORK_SERVICE_VOICE)
        if callee_mode_VoLTE and network_type != RAT_LTE:
            raise TelTestUtilsError("Error: Callee not in VoLTE. Expected VoLTE. Type:{}".
                                    format(network_type))
            return False
        if not callee_mode_VoLTE and network_type == RAT_LTE:
            raise TelTestUtilsError("Error: Callee in VoLTE. Expected not VoLTE.. Type:{}".
                                    format(network_type))
            return False

    time.sleep(delay_in_call)

    if (not ad_caller.droid.telecomIsInCall() or not
            ad_callee.droid.telecomIsInCall()):
        log.error("Call ended before delay_in_call.")
        return False

    if not hangup:
        return result
    if result:
        result = hangup_call(log, ad_hangup)
    if not result:
        for ad in [ad_caller, ad_callee]:
            if ad.droid.telecomIsInCall():
                ad.droid.telecomEndCall()
    return result