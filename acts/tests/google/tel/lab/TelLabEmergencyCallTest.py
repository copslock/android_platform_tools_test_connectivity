#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (C) 2014- The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sanity tests for voice tests in telephony
"""
from acts.base_test import BaseTestClass
from acts.controllers.tel.md8475a import MD8475A
from acts.controllers.tel._anritsu_utils import AnritsuError
from acts.controllers.tel.md8475a import VirtualPhoneStatus
from acts.test_utils.tel.tel_test_anritsu_utils import *
from acts.test_utils.tel.tel_test_utils import *
from acts.test_utils.tel.tel_voice_utils import *
from acts.controllers.tel.md8475a import CsfbType
from acts.controllers.tel.md8475a import VirtualPhoneAutoAnswer
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest

class TelLabEmergencyCallTest(TelephonyBaseTest):

    CELL_PARAM_FILE = 'C:\\MX847570\\CellParam\\2cell_param.wnscp'

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.tests = (
                      "test_emergency_call_lte_wcdma_csfb_redirection",
                      "test_emergency_call_lte_wcdma_csfb_handover",
                      "test_emergency_call_wcdma",
                      "test_emergency_call_gsm",
                      "test_emergency_call_1x",
                    )
        self.ad = self.android_devices[0]
        self.md8475a_ip_address = self.user_params["anritsu_md8475a_ip_address"]

    def setup_class(self):
        try:
            self.anritsu = MD8475A(self.md8475a_ip_address, self.log)
        except AnritsuError:
            self.log.error("Error in connecting to Anritsu Simulator")
            return False
        return True

    def setup_test(self):
        ensure_phones_idle(self.log, self.android_devices)
        # get a handle to virtual phone
        self.virtualPhoneHandle = self.anritsu.get_VirtualPhone()
        toggle_airplane_mode(self.log, self.ad, True)
        return True

    def teardown_test(self):
        self.log.info("Stopping Simulation")
        self.anritsu.stop_simulation()
        toggle_airplane_mode(self.log, self.ad, True)
        return True

    def teardown_class(self):
        self.anritsu.disconnect()
        return True

    def _setup_emergency_call(self, set_simulation_func, rat, csfb_type=None):
        try:
            self.anritsu.reset()
            self.anritsu.load_cell_paramfile(self.CELL_PARAM_FILE)
            set_simulation_func(self.anritsu, self.user_params)
            self.virtualPhoneHandle.auto_answer = (VirtualPhoneAutoAnswer.ON, 2)
            self.anritsu.start_simulation()

            if rat == RAT_LTE:
                phone_setup_func = phone_setup_csfb
                pref_network_type = NETWORK_MODE_LTE_GSM_WCDMA
                if csfb_type is not None:
                    self.anritsu.csfb_type = csfb_type
            elif rat == RAT_WCDMA:
                phone_setup_func = phone_setup_3g
                pref_network_type = NETWORK_MODE_WCDMA_PREF
            elif rat == RAT_GSM:
                phone_setup_func = phone_setup_2g
                pref_network_type = NETWORK_MODE_GSM_ONLY
            elif rat == RAT_1XRTT:
                phone_setup_func = phone_setup_3g
                pref_network_type = NETWORK_MODE_CDMA
            else:
                phone_setup_func = phone_setup_csfb
                network_type = NETWORK_MODE_LTE_CDMA_EVDO_GSM_WCDMA

            self.ad.droid.setPreferredNetwork(pref_network_type)
            if not phone_setup_func(self.log, self.ad):
                self.log.error("Phone {} Failed to Set Up Properly"
                              .format(self.ad.serial))
                return False
            self.anritsu.wait_for_registration_state()
            time.sleep(WAIT_TIME_ANRITSU_REG_AND_CALL)
            if not call_mo_setup_teardown(self.log, self.ad,
                                          self.virtualPhoneHandle,
                                          "911", teardown_side="phone",
                                          emergency=True):
                self.log.error("Phone {} Failed to make emergency call to 911"
                              .format(self.ad.serial))
                return False
        except AnritsuError as e:
            self.log.error("Error in connection with Anritsu Simulator: " + str(e))
            return False
        except Exception as e:
            self.log.error("Exception during emergency call procedure: " + str(e))
            return False
        return True

    """ Tests Begin """
    @TelephonyBaseTest.tel_test_wrap
    def test_emergency_call_lte_wcdma_csfb_redirection(self):
        """ Test Emergency call functionality on LTE (CSFB to WCDMA).
            CSFB type is REDIRECTION

        Make Sure Phone is in 4G mode
        Make an emergency call to 911
        Make sure Anritsu receives the call and accept
        Tear down the call

        Returns:
            True if pass; False if fail
        """
        return self._setup_emergency_call(set_system_model_lte_wcdma, RAT_LTE,
                                          CsfbType.CSFB_TYPE_REDIRECTION)

    @TelephonyBaseTest.tel_test_wrap
    def test_emergency_call_lte_wcdma_csfb_handover(self):
        """ Test Emergency call functionality on LTE (CSFB to WCDMA).
            CSFB type is HANDOVER

        Make Sure Phone is in 4G mode
        Make an emergency call to 911
        Make sure Anritsu receives the call and accept
        Tear down the call

        Returns:
            True if pass; False if fail
        """
        return self._setup_emergency_call(set_system_model_lte_wcdma, RAT_LTE,
                                          CsfbType.CSFB_TYPE_HANDOVER)

    @TelephonyBaseTest.tel_test_wrap
    def test_emergency_call_wcdma(self):
        """ Test Emergency call functionality on WCDMA

        Make Sure Phone is in 3G mode
        Make an emergency call to 911
        Make sure Anritsu receives the call and accept
        Tear down the call

        Returns:
            True if pass; False if fail
        """
        return self._setup_emergency_call(set_system_model_wcdma, RAT_WCDMA)

    @TelephonyBaseTest.tel_test_wrap
    def test_emergency_call_gsm(self):
        """ Test Emergency call functionality on GSM

        Make Sure Phone is in 2G mode
        Make an emergency call to 911
        Make sure Anritsu receives the call and accept
        Tear down the call

        Returns:
            True if pass; False if fail
        """
        return self._setup_emergency_call(set_system_model_gsm, RAT_GSM)

    @TelephonyBaseTest.tel_test_wrap
    def test_emergency_call_1x(self):
        """ Test Emergency call functionality on CDMA 1X

        Make Sure Phone is in 3G mode
        Make an emergency call to 911
        Make sure Anritsu receives the call and accept
        Tear down the call

        Returns:
            True if pass; False if fail
        """
        return self._setup_emergency_call(set_system_model_1x, RAT_1XRTT)
    """ Tests End """
