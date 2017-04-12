#/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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
Sanity tests for voice tests in telephony
"""
import time

from acts.controllers.anritsu_lib._anritsu_utils import AnritsuError
from acts.controllers.anritsu_lib.md8475a import CBCHSetup
from acts.controllers.anritsu_lib.md8475a import CTCHSetup
from acts.controllers.anritsu_lib.md8475a import MD8475A
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_CATEGORY_AMBER
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_CATEGORY_EXTREME
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_CATEGORY_PRESIDENTIAL
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_CERTIANTY_LIKELY
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_RESPONSETYPE_EVACUATE
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_RESPONSETYPE_MONITOR
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_RESPONSETYPE_SHELTER
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_SEVERITY_EXTREME
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_URGENCY_IMMEDIATE
from acts.test_utils.tel.anritsu_utils import CMAS_C2K_CERTIANTY_OBSERVED
from acts.test_utils.tel.anritsu_utils import CMAS_MESSAGE_CHILD_ABDUCTION_EMERGENCY
from acts.test_utils.tel.anritsu_utils import CMAS_MESSAGE_EXTREME_IMMEDIATE_LIKELY
from acts.test_utils.tel.anritsu_utils import CMAS_MESSAGE_PRESIDENTIAL_ALERT
from acts.test_utils.tel.anritsu_utils import cb_serial_number
from acts.test_utils.tel.anritsu_utils import cmas_receive_verify_message_cdma1x
from acts.test_utils.tel.anritsu_utils import cmas_receive_verify_message_lte_wcdma
from acts.test_utils.tel.anritsu_utils import set_system_model_1x
from acts.test_utils.tel.anritsu_utils import set_system_model_1x_evdo
from acts.test_utils.tel.anritsu_utils import set_system_model_lte
from acts.test_utils.tel.anritsu_utils import set_system_model_gsm
from acts.test_utils.tel.anritsu_utils import set_system_model_wcdma
from acts.test_utils.tel.anritsu_utils import set_usim_parameters
from acts.test_utils.tel.tel_defines import NETWORK_MODE_CDMA
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GSM_ONLY
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GSM_UMTS
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_GSM_WCDMA
from acts.test_utils.tel.tel_defines import RAT_1XRTT
from acts.test_utils.tel.tel_defines import RAT_LTE
from acts.test_utils.tel.tel_defines import RAT_GSM
from acts.test_utils.tel.tel_defines import RAT_WCDMA
from acts.test_utils.tel.tel_defines import RAT_FAMILY_CDMA2000
from acts.test_utils.tel.tel_defines import RAT_FAMILY_GSM
from acts.test_utils.tel.tel_defines import RAT_FAMILY_LTE
from acts.test_utils.tel.tel_defines import RAT_FAMILY_UMTS
from acts.test_utils.tel.tel_test_utils import ensure_network_rat
from acts.test_utils.tel.tel_test_utils import ensure_phones_idle
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest

WAIT_TIME_BETWEEN_REG_AND_MSG = 15  # default 15 sec


class TelLabCmasTest(TelephonyBaseTest):
    SERIAL_NO = cb_serial_number()

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.ad = self.android_devices[0]
        self.ad.sim_card = getattr(self.ad, "sim_card", None)
        self.md8475a_ip_address = self.user_params[
            "anritsu_md8475a_ip_address"]
        self.wlan_option = self.user_params.get("anritsu_wlan_option", False)
        self.wait_time_between_reg_and_msg = self.user_params.get(
            "wait_time_between_reg_and_msg", WAIT_TIME_BETWEEN_REG_AND_MSG)

    def setup_class(self):
        try:
            self.anritsu = MD8475A(self.md8475a_ip_address, self.log,
                                   self.wlan_option)
        except AnritsuError:
            self.log.error("Error in connecting to Anritsu Simulator")
            return False
        return True

    def setup_test(self):
        ensure_phones_idle(self.log, self.android_devices)
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

    def _send_receive_cmas_message(
            self,
            set_simulation_func,
            rat,
            message_id,
            warning_message,
            c2k_response_type=CMAS_C2K_RESPONSETYPE_SHELTER,
            c2k_severity=CMAS_C2K_SEVERITY_EXTREME,
            c2k_urgency=CMAS_C2K_URGENCY_IMMEDIATE,
            c2k_certainty=CMAS_C2K_CERTIANTY_OBSERVED):
        try:
            [self.bts1] = set_simulation_func(self.anritsu, self.user_params,
                                              self.ad.sim_card)
            set_usim_parameters(self.anritsu, self.ad.sim_card)
            self.anritsu.start_simulation()

            if rat == RAT_LTE:
                preferred_network_setting = NETWORK_MODE_LTE_GSM_WCDMA
                rat_family = RAT_FAMILY_LTE
            elif rat == RAT_WCDMA:
                self.bts1.wcdma_ctch = CTCHSetup.CTCH_ENABLE
                self.ad.droid.telephonyToggleDataConnection(False)
                preferred_network_setting = NETWORK_MODE_GSM_UMTS
                rat_family = RAT_FAMILY_UMTS
            elif rat == RAT_GSM:
                self.bts1.gsm_cbch = CBCHSetup.CBCH_ENABLE
                self.ad.droid.telephonyToggleDataConnection(False)
                preferred_network_setting = NETWORK_MODE_GSM_ONLY
                rat_family = RAT_FAMILY_GSM
            elif rat == RAT_1XRTT:
                preferred_network_setting = NETWORK_MODE_CDMA
                rat_family = RAT_FAMILY_CDMA2000
            else:
                self.log.error("No valid RAT provided for CMAS test.")
                return False

            if not ensure_network_rat(
                    self.log,
                    self.ad,
                    preferred_network_setting,
                    rat_family,
                    toggle_apm_after_setting=True):
                self.log.error(
                    "Failed to set rat family {}, preferred network:{}".format(
                        rat_family, preferred_network_setting))
                return False

            self.anritsu.wait_for_registration_state()
            if rat != RAT_1XRTT:
                if not cmas_receive_verify_message_lte_wcdma(
                        self.log, self.ad, self.anritsu,
                        next(TelLabCmasTest.SERIAL_NO), message_id,
                        warning_message):
                    self.log.error("Phone {} Failed to receive CMAS message"
                                   .format(self.ad.serial))
                    return False
            else:
                if not cmas_receive_verify_message_cdma1x(
                        self.log, self.ad, self.anritsu,
                        next(TelLabCmasTest.SERIAL_NO), message_id,
                        warning_message, c2k_response_type, c2k_severity,
                        c2k_urgency, c2k_certainty):
                    self.log.error("Phone {} Failed to receive CMAS message"
                                   .format(self.ad.serial))
                    return False
        except AnritsuError as e:
            self.log.error("Error in connection with Anritsu Simulator: " +
                           str(e))
            return False
        except Exception as e:
            self.log.error("Exception during CMAS send/receive: " + str(e))
            return False
        return True

    """ Tests Begin """

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_presidential_alert_lte(self):
        """CMAS Presidential alert message reception on LTE

        Tests the capability of device to receive and inform the user
        about the CMAS presedential alert message when camped on LTE newtork

        Steps:
        1. Make Sure Phone is camped on LTE network
        2. Send CMAS Presidential message from Anritsu

        Expected Result:
        Phone receives CMAS Presidential alert message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(set_system_model_lte, RAT_LTE,
                                               CMAS_MESSAGE_PRESIDENTIAL_ALERT,
                                               "LTE CMAS Presidential Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_extreme_immediate_likely_lte(self):
        """CMAS Extreme immediate likely message reception on LTE

        Tests the capability of device to receive and inform the user
        about the Extreme immediate likely message when camped on LTE newtork

        1. Make Sure Phone is camped on LTE network
        2. Send CMAS Extreme immediate likely message from Anritsu

        Expected Result:
        Phone receives CMAS Extreme immediate likely message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_lte, RAT_LTE,
            CMAS_MESSAGE_EXTREME_IMMEDIATE_LIKELY,
            "LTE CMAS Extreme Immediate Likely")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_child_abduction_emergency_lte(self):
        """CMAS Child abduction emergency message reception on LTE

        Tests the capability of device to receive and inform the user
        about the CMAS Child abduction emergency message when camped on LTE newtork

        1. Make Sure Phone is camped on LTE network
        2. Send CMAS Child abduction emergency message from Anritsu

        Expected Result:
        Phone receives CMAS Child abduction emergency message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_lte, RAT_LTE,
            CMAS_MESSAGE_CHILD_ABDUCTION_EMERGENCY,
            "LTE CMAS Child abduction Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_presidential_alert_wcdma(self):
        """CMAS Presidential alert message reception on WCDMA

        Tests the capability of device to receive and inform the user
        about the CMAS presedential alert message when camped on WCDMA newtork

        Steps:
        1. Make Sure Phone is camped on WCDMA network
        2. Send CMAS Presidential message from Anritsu

        Expected Result:
        Phone receives CMAS Presidential alert message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_wcdma, RAT_WCDMA, CMAS_MESSAGE_PRESIDENTIAL_ALERT,
            "WCDMA CMAS Presidential Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_extreme_immediate_likely_wcdma(self):
        """CMAS Extreme immediate likely message reception on WCDMA

        Tests the capability of device to receive and inform the user
        about the Extreme immediate likely message when camped on WCDMA newtork

        1. Make Sure Phone is camped on WCDMA network
        2. Send CMAS Extreme immediate likely message from Anritsu

        Expected Result:
        Phone receives CMAS Extreme immediate likely message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_wcdma, RAT_WCDMA,
            CMAS_MESSAGE_EXTREME_IMMEDIATE_LIKELY,
            "WCDMA CMAS Extreme Immediate Likely")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_child_abduction_emergency_wcdma(self):
        """CMAS Child abduction emergency message reception on WCDMA

        Tests the capability of device to receive and inform the user
        about the CMAS Child abduction emergency message when camped on WCDMA newtork

        1. Make Sure Phone is camped on WCDMA network
        2. Send CMAS Child abduction emergency message from Anritsu

        Expected Result:
        Phone receives CMAS Child abduction emergency message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_wcdma, RAT_WCDMA,
            CMAS_MESSAGE_CHILD_ABDUCTION_EMERGENCY,
            "WCDMA CMAS Child abduction Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_presidential_alert_1x(self):
        """CMAS Presidential alert message reception on 1x

        Tests the capability of device to receive and inform the user
        about the CMAS presedential alert message when camped on 1x newtork

        Steps:
        1. Make Sure Phone is camped on 1x network
        2. Send CMAS Presidential message from Anritsu

        Expected Result:
        Phone receives CMAS Presidential alert message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(set_system_model_1x, RAT_1XRTT,
                                               CMAS_C2K_CATEGORY_PRESIDENTIAL,
                                               "1X CMAS Presidential Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_extreme_immediate_likely_1x(self):
        """CMAS Extreme immediate likely message reception on 1x

        Tests the capability of device to receive and inform the user
        about the Extreme immediate likely message when camped on 1x newtork

        1. Make Sure Phone is camped on 1x network
        2. Send CMAS Extreme immediate likely message from Anritsu

        Expected Result:
        Phone receives CMAS Extreme immediate likely message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_1x, RAT_1XRTT, CMAS_C2K_CATEGORY_EXTREME,
            "1X CMAS Extreme Immediate Likely", CMAS_C2K_RESPONSETYPE_EVACUATE,
            CMAS_C2K_SEVERITY_EXTREME, CMAS_C2K_URGENCY_IMMEDIATE,
            CMAS_C2K_CERTIANTY_LIKELY)

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_child_abduction_emergency_1x(self):
        """CMAS Child abduction emergency message reception on 1x

        Tests the capability of device to receive and inform the user
        about the CMAS Child abduction emergency message when camped on 1x newtork

        1. Make Sure Phone is camped on 1x network
        2. Send CMAS Child abduction emergency message from Anritsu

        Expected Result:
        Phone receives CMAS Child abduction emergency message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_1x, RAT_1XRTT, CMAS_C2K_CATEGORY_AMBER,
            "1X CMAS Child abduction Alert", CMAS_C2K_RESPONSETYPE_MONITOR,
            CMAS_C2K_SEVERITY_EXTREME, CMAS_C2K_URGENCY_IMMEDIATE,
            CMAS_C2K_CERTIANTY_OBSERVED)

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_presidential_alert_1x_evdo(self):
        """CMAS Presidential alert message reception on 1x with EVDO

        Tests the capability of device to receive and inform the user
        about the CMAS presedential alert message when camped on 1x newtork

        Steps:
        1. Make Sure Phone is camped on 1x network with EVDO
        2. Send CMAS Presidential message from Anritsu

        Expected Result:
        Phone receives CMAS Presidential alert message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_1x_evdo, RAT_1XRTT,
            CMAS_C2K_CATEGORY_PRESIDENTIAL, "1X CMAS Presidential Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_extreme_immediate_likely_1x_evdo(self):
        """CMAS Extreme immediate likely message reception on 1x with EVDO

        Tests the capability of device to receive and inform the user
        about the Extreme immediate likely message when camped on 1x newtork

        1. Make Sure Phone is camped on 1x network with EVDO
        2. Send CMAS Extreme immediate likely message from Anritsu

        Expected Result:
        Phone receives CMAS Extreme immediate likely message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_1x_evdo, RAT_1XRTT, CMAS_C2K_CATEGORY_EXTREME,
            "1X CMAS Extreme Immediate Likely", CMAS_C2K_RESPONSETYPE_EVACUATE,
            CMAS_C2K_SEVERITY_EXTREME, CMAS_C2K_URGENCY_IMMEDIATE,
            CMAS_C2K_CERTIANTY_LIKELY)

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_child_abduction_emergency_1x_evdo(self):
        """CMAS Child abduction emergency message reception on 1x with EVDO

        Tests the capability of device to receive and inform the user
        about the CMAS Child abduction emergency message when camped on 1x newtork

        1. Make Sure Phone is camped on 1x network
        2. Send CMAS Child abduction emergency message from Anritsu

        Expected Result:
        Phone receives CMAS Child abduction emergency message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_1x_evdo, RAT_1XRTT, CMAS_C2K_CATEGORY_AMBER,
            "1X CMAS Child abduction Alert", CMAS_C2K_RESPONSETYPE_MONITOR,
            CMAS_C2K_SEVERITY_EXTREME, CMAS_C2K_URGENCY_IMMEDIATE,
            CMAS_C2K_CERTIANTY_OBSERVED)

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_presidential_alert_gsm(self):
        """CMAS Presidential alert message reception on GSM

        Tests the capability of device to receive and inform the user
        about the CMAS presedential alert message when camped on GSM newtork

        Steps:
        1. Make Sure Phone is camped on GSM network
        2. Send CMAS Presidential message from Anritsu

        Expected Result:
        Phone receives CMAS Presidential alert message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(set_system_model_gsm, RAT_GSM,
                                               CMAS_MESSAGE_PRESIDENTIAL_ALERT,
                                               "GSM CMAS Presidential Alert")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_extreme_immediate_likely_gsm(self):
        """CMAS Extreme immediate likely message reception on GSM

        Tests the capability of device to receive and inform the user
        about the Extreme immediate likely message when camped on GSM newtork

        1. Make Sure Phone is camped on GSM network
        2. Send CMAS Extreme immediate likely message from Anritsu

        Expected Result:
        Phone receives CMAS Extreme immediate likely message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_gsm, RAT_GSM,
            CMAS_MESSAGE_EXTREME_IMMEDIATE_LIKELY,
            "GSM CMAS Extreme Immediate Likely")

    @TelephonyBaseTest.tel_test_wrap
    def test_cmas_child_abduction_emergency_gsm(self):
        """CMAS Child abduction emergency message reception on GSM

        Tests the capability of device to receive and inform the user
        about the CMAS Child abduction emergency message when camped on GSM newtork

        1. Make Sure Phone is camped on GSM network
        2. Send CMAS Child abduction emergency message from Anritsu

        Expected Result:
        Phone receives CMAS Child abduction emergency message

        Returns:
            True if pass; False if fail
        """
        return self._send_receive_cmas_message(
            set_system_model_gsm, RAT_GSM,
            CMAS_MESSAGE_CHILD_ABDUCTION_EMERGENCY,
            "GSM CMAS Child abduction Alert")

    """ Tests End """
