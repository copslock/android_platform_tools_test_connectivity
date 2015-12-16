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
from acts.controllers.tel.md8475a import VirtualPhoneStatus
from acts.test_utils.tel.tel_test_anritsu_utils import *
from acts.test_utils.tel.tel_test_utils import *
from acts.test_utils.tel.tel_voice_utils import *
from acts.controllers.tel.md8475a import CsfbType
from acts.controllers.tel.md8475a import VirtualPhoneAutoAnswer
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest

class TelLabVoiceTest(TelephonyBaseTest):

    CELL_PARAM_FILE = 'C:\\MX847570\\CellParam\\2cell_param.wnscp'

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.tests = (
                    "test_mo_voice_call_lte_wcdma_csfb_redirection_phone_hangup",
                    "test_mo_voice_call_lte_wcdma_csfb_redirection_remote_hangup",
                    "test_mo_voice_call_lte_wcdma_csfb_handover_phone_hangup",
                    "test_mo_voice_call_lte_wcdma_csfb_handover_remote_hangup",
                    "test_mt_voice_call_lte_wcdma_csfb_redirection_phone_hangup",
                    "test_mt_voice_call_lte_wcdma_csfb_redirection_remote_hangup",
                    "test_mt_voice_call_lte_wcdma_csfb_handover_phone_hangup",
                    "test_mt_voice_call_lte_wcdma_csfb_handover_remote_hangup",
                    "test_mo_voice_call_wcdma_phone_hangup",
                    "test_mo_voice_call_wcdma_remote_hangup",
                    "test_mt_voice_call_wcdma_phone_hangup",
                    "test_mt_voice_call_wcdma_remote_hangup",
                    "test_mo_voice_call_gsm_phone_hangup",
                    "test_mo_voice_call_gsm_remote_hangup",
                    "test_mt_voice_call_gsm_phone_hangup",
                    "test_mt_voice_call_gsm_remote_hangup",
                    "test_mo_voice_call_1x_phone_hangup",
                    "test_mo_voice_call_1x_remote_hangup",
                    "test_mt_voice_call_1x_phone_hangup",
                    "test_mt_voice_call_1x_remote_hangup",
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

    def _setup_voice_call(self, set_simulation_func, rat, mo_mt=MOBILE_ORIGINATED,
        teardown_side=CALL_TEARDOWN_PHONE, csfb_type=None):
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

            self.ad.droid.telephonySetPreferredNetwork(pref_network_type)
            if not phone_setup_func(self.log, self.ad):
                self.log.error("Phone {} Failed to Set Up Properly"
                              .format(self.ad.serial))
                return False
            self.anritsu.wait_for_registration_state()
            time.sleep(10)
            if mo_mt == MOBILE_ORIGINATED:
                if not call_mo_setup_teardown(self.log, self.ad,
                                             self.virtualPhoneHandle,
                                             "777777", teardown_side,
                                             emergency=False):
                    self.log.error("Phone {} Failed to make MO call to 777777"
                                 .format(self.ad.serial))
                    return False
            else:
                if not call_mt_setup_teardown(self.log, self.ad,
                                             self.virtualPhoneHandle,
                                             "777777", teardown_side, rat):
                    self.log.error("Phone {} Failed to make MT call from 777777"
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
    def test_mo_voice_call_lte_wcdma_csfb_redirection_phone_hangup(self):
        """ Test MO Call on LTE - CSFB Redirection, hangup at phone

        Make Sure Phone is in LTE mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call from Phone
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_PHONE,
                                      CsfbType.CSFB_TYPE_REDIRECTION)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_lte_wcdma_csfb_redirection_remote_hangup(self):
        """ Test MO Call on LTE - CSFB Redirection, hangup at remote

        Make Sure Phone is in LTE mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE, MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_REMOTE,
                                      CsfbType.CSFB_TYPE_REDIRECTION)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_lte_wcdma_csfb_handover_phone_hangup(self):
        """ Test MO Call on LTE - CSFB Handover, hangup at phone

        Make Sure Phone is in LTE mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_PHONE,
                                      CsfbType.CSFB_TYPE_HANDOVER)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_lte_wcdma_csfb_handover_remote_hangup(self):
        """ Test MO Call on LTE - CSFB Handover, hangup at remote

        Make Sure Phone is in LTE mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE, MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_REMOTE,
                                      CsfbType.CSFB_TYPE_HANDOVER)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_lte_wcdma_csfb_redirection_phone_hangup(self):
        """ Test MT Call on LTE - CSFB Redirection, hangup at phone

        Make Sure Phone is in LTE mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from Phone
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_PHONE,
                                      CsfbType.CSFB_TYPE_REDIRECTION)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_lte_wcdma_csfb_redirection_remote_hangup(self):
        """ Test MT Call on LTE - CSFB Redirection, hangup at remote

        Make Sure Phone is in LTE mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_REMOTE,
                                      CsfbType.CSFB_TYPE_REDIRECTION)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_lte_wcdma_csfb_handover_phone_hangup(self):
        """ Test MT Call on LTE - CSFB Handover, hangup at phone

        Make Sure Phone is in LTE mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from Phone
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_PHONE,
                                      CsfbType.CSFB_TYPE_HANDOVER)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_lte_wcdma_csfb_handover_remote_hangup(self):
        """ Test MO Call on LTE - CSFB Handover, hangup at phone

        Make Sure Phone is in LTE mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_lte_wcdma,
                                      RAT_LTE,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_REMOTE,
                                      CsfbType.CSFB_TYPE_HANDOVER)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_wcdma_phone_hangup(self):
        """ Test MO Call on WCDMA - hangup at phone

        Make Sure Phone is in WCDMA mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_wcdma,
                                      RAT_WCDMA,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_wcdma_remote_hangup(self):
        """ Test MO Call on WCDMA - hangup at remote

        Make Sure Phone is in WCDMA mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_wcdma,
                                      RAT_WCDMA,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_REMOTE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_wcdma_phone_hangup(self):
        """ Test MO Call on WCDMA - hangup at phone

        Make Sure Phone is in WCDMA mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_wcdma,
                                      RAT_WCDMA,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_wcdma_remote_hangup(self):
        """ Test MO Call on WCDMA - hangup at phone

        Make Sure Phone is in WCDMA mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_wcdma,
                                      RAT_WCDMA,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_REMOTE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_gsm_phone_hangup(self):
        """ Test MO Call on GSM - hangup at phone

        Make Sure Phone is in GSM mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_gsm,
                                      RAT_GSM,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_gsm_remote_hangup(self):
        """ Test MO Call on GSM - hangup at remote

        Make Sure Phone is in GSM mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_gsm,
                                      RAT_GSM,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_REMOTE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_gsm_phone_hangup(self):
        """ Test MO Call on GSM - hangup at phone

        Make Sure Phone is in GSM mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_gsm,
                                      RAT_GSM,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_gsm_remote_hangup(self):
        """ Test MO Call on GSM - hangup at phone

        Make Sure Phone is in GSM mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_gsm,
                                      RAT_GSM,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_REMOTE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_1x_phone_hangup(self):
        """ Test MO Call on CDMA 1X  - hangup at phone

        Make Sure Phone is in CDMA 1X  mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_1x,
                                      RAT_1XRTT,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mo_voice_call_1x_remote_hangup(self):
        """ Test MO Call on CDMA 1X  - hangup at remote

        Make Sure Phone is in CDMA 1X  mode
        Initiate a voice call from Phone
        Answer the call at Anritsu
        Verify call state
        Disconnects the call at Anritsu
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_1x,
                                      RAT_1XRTT,MOBILE_ORIGINATED,
                                      CALL_TEARDOWN_REMOTE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_1x_phone_hangup(self):
        """ Test MO Call on CDMA 1X  - hangup at phone

        Make Sure Phone is in CDMA 1X  mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_1x,
                                      RAT_1XRTT,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_PHONE)

    @TelephonyBaseTest.tel_test_wrap
    def test_mt_voice_call_1x_remote_hangup(self):
        """ Test MO Call on CDMA 1X - hangup at phone

        Make Sure Phone is in CDMA 1X  mode
        Initiate a voice call from Anritsu
        Answer the call at phone
        Verify call state
        Disconnects the call from remote
        Verify call state

        Returns:
            True if pass; False if fail
        """
        return self._setup_voice_call(set_system_model_1x,
                                      RAT_1XRTT,MOBILE_TERMINATED,
                                      CALL_TEARDOWN_REMOTE)
    """ Tests End """
