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
    Test Script for Telephony Smoke Test
"""

import time
from acts.base_test import BaseTestClass
from queue import Empty
from acts.test_utils.tel.tel_test_utils import *
from acts.test_utils.tel.tel_data_utils import *
from acts.test_utils.tel.tel_voice_utils import *
from acts.utils import load_config
from acts.utils import rand_ascii_str
from acts.keys import Config
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest

SKIP = 'Skip'

class TelLiveSmokeTest(TelephonyBaseTest):

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.tests = (
                      "test_wfc_capability_phone_smoke",
                      )

        self.simconf = load_config(self.user_params["sim_conf_file"])

        self.wifi_network_ssid = self.user_params["wifi_network_ssid"]
        try:
            self.wifi_network_pass = self.user_params["wifi_network_pass"]
        except KeyError:
            self.wifi_network_pass = None

    """ Tests Begin """
    def _test_smoke_volte(self):
        ads = self.android_devices
        sms_idle_result = False
        sms_incall_result = False
        data_idle_result = False
        data_incall_result = False
        call_result = False

        self.log.info("--------start test_smoke_volte--------")
        ensure_phones_default_state(self.log, ads)
        tasks = [(phone_setup_volte, (self.log, ads[0])),
                 (phone_setup_volte, (self.log, ads[1]))]
        if not multithread_func(self.log, tasks):
            self.log.error("Phone Failed to Set Up VoLTE.")
            return False

        # TODO: this is hack to reduce call fail in VoLTE mode.
        time.sleep(10)

        self.log.info("1. SMS in LTE idle.")
        sms_idle_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                  [rand_ascii_str(50)])

        self.log.info("2. Data in LTE idle.")
        if (wait_for_cell_data_connection(self.log, ads[0], True) and
            verify_http_connection(self.log, ads[0])):
            data_idle_result = True

        self.log.info("3. Setup VoLTE Call.")
        if not call_setup_teardown(self.log, ads[0], ads[1],
                               ad_hangup=None,
                               verify_caller_func=is_phone_in_call_volte,
                               verify_callee_func=is_phone_in_call_volte,
                               wait_time_in_call=WAIT_TIME_IN_CALL_FOR_IMS):
            self.log.error("Setup VoLTE Call Failed.")
            return False

        self.log.info("4. Verify SMS in call.")
        sms_incall_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                    [rand_ascii_str(51)])

        self.log.info("5. Verify Data in call.")
        if (wait_for_cell_data_connection(self.log, ads[0], True) and
            verify_http_connection(self.log, ads[0])):
            data_incall_result = True

        self.log.info("6. Verify Call not drop and hangup.")
        if (is_phone_in_call_volte(self.log, ads[0]) and
            is_phone_in_call_volte(self.log, ads[1]) and
            hangup_call(self.log, ads[0])):
            call_result = True

        self.log.info("Summary-VoLTE Smoke Test: SMS idle: {}, Data idle: {}, "
                      "VoLTE Call: {}, SMS in call: {}, Data in call: {}".
            format(sms_idle_result, data_idle_result,
                   call_result, sms_incall_result, data_incall_result))

        return (sms_idle_result and data_idle_result and call_result and
                sms_incall_result and data_incall_result)

    def _test_smoke_csfb_3g(self):
        ads = self.android_devices
        sms_idle_result = False
        sms_incall_result = False
        data_idle_result = False
        data_incall_result = False
        call_result = False

        self.log.info("--------start test_smoke_csfb_3g--------")
        ensure_phones_default_state(self.log, ads)
        tasks = [(phone_setup_csfb, (self.log, ads[0])),
                 (phone_setup_csfb, (self.log, ads[1]))]
        if not multithread_func(self.log, tasks):
            self.log.error("Phone Failed to Set Up CSFB_3G.")
            return False

        # TODO: this is hack to reduce SMS send failure in CSFB mode.
        time.sleep(10)

        self.log.info("1. SMS in LTE idle (no IMS).")
        sms_idle_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                  [rand_ascii_str(50)])

        self.log.info("2. Data in LTE idle (no IMS).")
        if (wait_for_cell_data_connection(self.log, ads[0], True) and
            verify_http_connection(self.log, ads[0])):
            data_idle_result = True

        self.log.info("3. Setup CSFB_3G Call.")
        if not call_setup_teardown(self.log, ads[0], ads[1],
                               ad_hangup=None,
                               verify_caller_func=is_phone_in_call_csfb,
                               verify_callee_func=is_phone_in_call_csfb):
            self.log.error("Setup CSFB_3G Call Failed.")
            return False

        self.log.info("4. Verify SMS in call.")
        sms_incall_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                    [rand_ascii_str(51)])

        self.log.info("5. Verify Data in call.")
        if is_rat_svd_capable(get_network_rat(self.log, ads[0],
            NETWORK_SERVICE_VOICE)):
            if (wait_for_cell_data_connection(self.log, ads[0], True) and
                verify_http_connection(self.log, ads[0])):
                data_incall_result = True
        else:
            self.log.info("Data in call not supported on current RAT."
                          "Skip Data verification.")
            data_incall_result = SKIP

        self.log.info("6. Verify Call not drop and hangup.")
        if (is_phone_in_call_csfb(self.log, ads[0]) and
            is_phone_in_call_csfb(self.log, ads[1]) and
            hangup_call(self.log, ads[0])):
            call_result = True

        self.log.info("Summary-CSFB 3G Smoke Test: SMS idle: {}, Data idle: {},"
                      " CSFB_3G Call: {}, SMS in call: {}, Data in call: {}".
            format(sms_idle_result, data_idle_result,
                   call_result, sms_incall_result, data_incall_result))

        return (sms_idle_result and data_idle_result and call_result and
                sms_incall_result and
                ((data_incall_result is True) or (data_incall_result == SKIP)))

    def _test_smoke_3g(self):
        ads = self.android_devices
        sms_idle_result = False
        sms_incall_result = False
        data_idle_result = False
        data_incall_result = False
        call_result = False

        self.log.info("--------start test_smoke_3g--------")
        ensure_phones_default_state(self.log, ads)
        tasks = [(phone_setup_3g, (self.log, ads[0])),
                 (phone_setup_3g, (self.log, ads[1]))]
        if not multithread_func(self.log, tasks):
            self.log.error("Phone Failed to Set Up 3G.")
            return False
        self.log.info("1. SMS in LTE idle (no IMS).")
        sms_idle_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                  [rand_ascii_str(50)])

        self.log.info("2. Data in LTE idle (no IMS).")
        if (wait_for_cell_data_connection(self.log, ads[0], True) and
            verify_http_connection(self.log, ads[0])):
            data_idle_result = True

        self.log.info("3. Setup 3G Call.")
        if not call_setup_teardown(self.log, ads[0], ads[1],
                               ad_hangup=None,
                               verify_caller_func=is_phone_in_call_3g,
                               verify_callee_func=is_phone_in_call_3g):
            self.log.error("Setup 3G Call Failed.")
            return False

        self.log.info("4. Verify SMS in call.")
        sms_incall_result = sms_send_receive_verify(self.log, ads[0], ads[1],
                                                    [rand_ascii_str(51)])

        self.log.info("5. Verify Data in call.")
        if is_rat_svd_capable(get_network_rat(self.log, ads[0],
            NETWORK_SERVICE_VOICE)):
            if (wait_for_cell_data_connection(self.log, ads[0], True) and
                verify_http_connection(self.log, ads[0])):
                data_incall_result = True
        else:
            self.log.info("Data in call not supported on current RAT."
                          "Skip Data verification.")
            data_incall_result = SKIP

        self.log.info("6. Verify Call not drop and hangup.")
        if (is_phone_in_call_3g(self.log, ads[0]) and
            is_phone_in_call_3g(self.log, ads[1]) and
            hangup_call(self.log, ads[0])):
            call_result = True

        self.log.info("Summary-3G Smoke Test: SMS idle: {}, Data idle: {},"
                      " 3G Call: {}, SMS in call: {}, Data in call: {}".
            format(sms_idle_result, data_idle_result,
                   call_result, sms_incall_result, data_incall_result))

        return (sms_idle_result and data_idle_result and call_result and
                sms_incall_result and
                ((data_incall_result is True) or (data_incall_result == SKIP)))

    def _test_smoke_wfc(self):
        ads = self.android_devices
        sms_idle_result = False
        sms_incall_result = False
        call_result = False

        self.log.info("--------start test_smoke_wfc--------")
        for ad in [ads[0], ads[1]]:
            if not ad.droid.imsIsWfcEnabledByPlatform():
                self.log.info("WFC not supported by platform.")
                return SKIP

        ensure_phones_default_state(self.log, ads)
        tasks = [(phone_setup_iwlan,
                  (self.log, ads[0], True, WFC_MODE_WIFI_PREFERRED,
                   self.wifi_network_ssid, self.wifi_network_pass)),
                 (phone_setup_iwlan,
                  (self.log, ads[1], True, WFC_MODE_WIFI_PREFERRED,
                   self.wifi_network_ssid, self.wifi_network_pass))]
        if not multithread_func(self.log, tasks):
            self.log.error("Phone Failed to Set Up WiFI Calling.")
            return False

        self.log.info("1. Verify SMS in idle.")
        if sms_send_receive_verify(self.log, ads[0], ads[1],
                                   [rand_ascii_str(50)]):
            sms_idle_result = True

        self.log.info("2. Setup WiFi Call.")
        if not call_setup_teardown(self.log, ads[0], ads[1],
                               ad_hangup=None,
                               verify_caller_func=is_phone_in_call_iwlan,
                               verify_callee_func=is_phone_in_call_iwlan):
            self.log.error("Setup WiFi Call Failed.")
            self.log.info("sms_idle_result:{}".format(sms_idle_result))
            return False

        self.log.info("3. Verify SMS in call.")
        if sms_send_receive_verify(self.log, ads[0], ads[1],
                                   [rand_ascii_str(51)]):
            sms_incall_result = True

        self.log.info("4. Verify Call not drop and hangup.")
        if (is_phone_in_call_iwlan(self.log, ads[0]) and
            is_phone_in_call_iwlan(self.log, ads[1]) and
            hangup_call(self.log, ads[0])):
            call_result = True

        self.log.info("Summary-WFC Smoke Test: SMS in idle:{}, WiFi Call:{},"
                      " SMS in call:{}".
                      format(sms_idle_result, call_result, sms_incall_result))

        return (call_result and sms_idle_result and sms_incall_result)

    def _test_smoke_data(self):
        ads = self.android_devices
        apm_result = False
        nw_switch_result = False
        tethering_result = False

        self.log.info("--------start test_smoke_data--------")
        ensure_phones_default_state(self.log, ads)
        self.log.info("1. Verify toggle airplane mode.")
        apm_result = airplane_mode_test(self.log, ads[0])
        self.log.info("2. Verify LTE-WiFi network switch.")
        nw_switch_result = wifi_cell_switching(self.log, ads[0],
                                               self.wifi_network_ssid,
                                               self.wifi_network_pass,
                                               GEN_4G)
        if ads[0].droid.phoneIsTetheringModeAllowed(TETHERING_MODE_WIFI,
            TETHERING_ENTITLEMENT_CHECK_TIMEOUT):
            self.log.info("3. Verify WiFi Tethering.")
            if ads[0].droid.wifiIsApEnabled():
                WifiUtils.stop_wifi_tethering(self.log, ads[0])
            tethering_result = wifi_tethering_setup_teardown(self.log,
                ads[0], [ads[1]], ap_band=WifiUtils.WIFI_CONFIG_APBAND_2G,
                check_interval=10, check_iteration=4)
            # check_interval=10, check_iteration=4: in this Smoke test,
            # check tethering connection for 4 times, each time delay 10s,
            # to provide a reasonable check_time (10*4=40s) and also reduce test
            # execution time. In regular test, check_iteration is set to 10.
        else:
            self.log.info("3. Skip WiFi Tethering."
                          "Tethering not allowed on SIM.")
            tethering_result = SKIP

        self.log.info("Summary-Data Smoke Test: Airplane Mode:{}, "
                      "Network Switch:{}, Tethering:{}".
                      format(apm_result, nw_switch_result, tethering_result))

        return (apm_result and nw_switch_result and
                ((tethering_result is True) or (tethering_result == SKIP)))

    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_capability_phone_smoke(self):
        """Verify basic WFC, VoLTE, CS, Data, and Messaging features.
        1. Verify WFC features.
            Setup WFC in APM mode, WiFi-preferred mode.
            Send/Receive one SMS in WFC idle mode.
            Make WFC call.
            Send/Receive one SMS in WFC active call.
        2. Verify VoLTE+LTE Data/Message features.
            Setup VoLTE.
            Verify SMS and Data in idle.
            Make VoLTE call.
            Send/Receive one SMS in VoLTE active call.
            Verify Data in VoLTE active call.
        3. Verify Data features.
            Verify toggle airplane mode.
            Verify LTE-WiFi network switch.
            Verify WiFI Tethering.
        4. Verify CSFB+LTE Data/Message features.
            Setup LTE without VoLTE.
            Verify SMS and Data in idle.
            Make CSFB call.
            Send/Receive one SMS in CSFB 3G active call.
            Verify Data in CSFB 3G active call (if current network rat support).
        5. Verify 3G Voice/Data/Message features.
            Setup 3G.
            Verify SMS and Data in idle.
            Make 3G voice call.
            Send/Receive one SMS in 3G active call.
            Verify Data in 3G active call (if current network rat support).
        """
        try:
            result_wfc = self._test_smoke_wfc()
            result_volte = self._test_smoke_volte()
            result_data = self._test_smoke_data()
            result_csfb_3g = self._test_smoke_csfb_3g()
            result_3g = self._test_smoke_3g()

            self.log.info("Summary for test run. Testbed:<{}>. WFC:{}, "
                "VoLTE+LTE Data/Message:{}, Data Basic:{}, "
                "CSFB+LTE Data/Message:{}, 3G Voice/Data/Message:{}".
                format(getattr(self, Config.ikey_testbed_name.value),
                       result_wfc, result_volte, result_data, result_csfb_3g,
                       result_3g))

            return (result_volte and result_data and result_csfb_3g
                    and result_3g and ((result_wfc is True)
                                       or (result_wfc == SKIP)))
        except Exception as e:
            self.log.error("Summary Failed. Exception:{}".format(e))
            return False

    @TelephonyBaseTest.tel_test_wrap
    def test_volte_capability_phone_smoke(self):
        """Verify basic VoLTE, CS, Data, and Messaging features.
        1. Verify VoLTE+LTE Data/Message features.
            Setup VoLTE.
            Verify SMS and Data in idle.
            Make VoLTE call.
            Send/Receive one SMS in VoLTE active call.
            Verify Data in VoLTE active call.
        2. Verify Data features.
            Verify toggle airplane mode.
            Verify LTE-WiFi network switch.
            Verify WiFI Tethering.
        3. Verify CSFB+LTE Data/Message features.
            Setup LTE without VoLTE.
            Verify SMS and Data in idle.
            Make CSFB call.
            Send/Receive one SMS in CSFB 3G active call.
            Verify Data in CSFB 3G active call (if current network rat support).
        4. Verify 3G Voice/Data/Message features.
            Setup 3G.
            Verify SMS and Data in idle.
            Make 3G voice call.
            Send/Receive one SMS in 3G active call.
            Verify Data in 3G active call (if current network rat support).
        """
        try:
            result_volte = self._test_smoke_volte()
            result_data = self._test_smoke_data()
            result_csfb_3g = self._test_smoke_csfb_3g()
            result_3g = self._test_smoke_3g()

            self.log.info("Summary for test run. Testbed:<{}>. "
                "VoLTE+LTE Data/Message:{}, Data Basic:{}, "
                "CSFB+LTE Data/Message:{}, 3G Voice/Data/Message:{}".
                format(getattr(self, Config.ikey_testbed_name.value),
                    result_volte, result_data, result_csfb_3g, result_3g))

            return (result_volte and result_data and result_csfb_3g
                    and result_3g)
        except Exception as e:
            self.log.error("Summary Failed. Exception:{}".format(e))
            return False

    @TelephonyBaseTest.tel_test_wrap
    def test_lte_capability_phone_smoke(self):
        """Verify basic CS, Data, and Messaging features.
        1. Verify Data features.
            Verify toggle airplane mode.
            Verify LTE-WiFi network switch.
            Verify WiFI Tethering.
        2. Verify CSFB+LTE Data/Message features.
            Setup LTE without VoLTE.
            Verify SMS and Data in idle.
            Make CSFB call.
            Send/Receive one SMS in CSFB 3G active call.
            Verify Data in CSFB 3G active call (if current network rat support).
        3. Verify 3G Voice/Data/Message features.
            Setup 3G.
            Verify SMS and Data in idle.
            Make 3G voice call.
            Send/Receive one SMS in 3G active call.
            Verify Data in 3G active call (if current network rat support).
        """
        try:
            result_data = self._test_smoke_data()
            result_csfb_3g = self._test_smoke_csfb_3g()
            result_3g = self._test_smoke_3g()

            self.log.info("Summary for test run. Testbed:<{}>. Data Basic:{}, "
                "CSFB+LTE Data/Message:{}, 3G Voice/Data/Message:{}".
                format(getattr(self, Config.ikey_testbed_name.value),
                    result_data, result_csfb_3g, result_3g))

            return (result_data and result_csfb_3g and result_3g)
        except Exception as e:
            self.log.error("Summary Failed. Exception:{}".format(e))
            return False
    """ Tests End """
