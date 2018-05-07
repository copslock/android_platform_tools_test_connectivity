#!/usr/bin/env python3.4
#
#   Copyright 2018 - Google
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
    Connectivity Monitor and Telephony Troubleshooter Tests
"""

import re
import time

from acts import signals
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_data_utils import wifi_tethering_setup_teardown
from acts.test_utils.tel.tel_defines import CAPABILITY_VOLTE
from acts.test_utils.tel.tel_defines import CAPABILITY_VT
from acts.test_utils.tel.tel_defines import CAPABILITY_WFC
from acts.test_utils.tel.tel_defines import CAPABILITY_WFC_MODE_CHANGE
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_TETHERING_ENTITLEMENT_CHECK
from acts.test_utils.tel.tel_defines import TETHERING_MODE_WIFI
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_defines import VT_STATE_BIDIRECTIONAL
from acts.test_utils.tel.tel_test_utils import bring_up_connectivity_monitor
from acts.test_utils.tel.tel_test_utils import toggle_connectivity_monitor_setting
from acts.test_utils.tel.tel_test_utils import call_setup_teardown
from acts.test_utils.tel.tel_test_utils import get_model_name
from acts.test_utils.tel.tel_test_utils import get_operator_name
from acts.test_utils.tel.tel_test_utils import hangup_call
from acts.test_utils.tel.tel_test_utils import reboot_device
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import trigger_modem_crash
from acts.test_utils.tel.tel_test_utils import trigger_modem_crash_by_modem
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_2g
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_3g
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_csfb
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_iwlan
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_volte
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_2g
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_3g
from acts.test_utils.tel.tel_voice_utils import phone_setup_csfb
from acts.test_utils.tel.tel_voice_utils import phone_setup_iwlan
from acts.test_utils.tel.tel_voice_utils import phone_setup_volte
from acts.test_utils.tel.tel_video_utils import video_call_setup_teardown
from acts.test_utils.tel.tel_video_utils import phone_setup_video
from acts.test_utils.tel.tel_video_utils import \
    is_phone_in_call_video_bidirectional


class TelLiveConnectivityMonitorTest(TelephonyBaseTest):
    def setup_class(self):
        TelephonyBaseTest.setup_class(self)
        self.dut = self.android_devices[0]
        self.ad_reference = self.android_devices[1]
        self.dut_model = get_model_name(self.dut)
        self.dut_operator = get_operator_name(self.log, self.dut)
        self.dut_capabilities = self.dut.telephony.get("capabilities", [])
        self.reference_capabilities = self.ad_reference.telephony.get(
            "capabilities", [])
        self.dut.log.info("DUT capabilities: %s", self.dut_capabilities)
        self.skip_reset_between_cases = False
        self.user_params["telephony_auto_rerun"] = 0

    def setup_test(self):
        TelephonyBaseTest.setup_test(self)
        bring_up_connectivity_monitor(self.dut)

    def _setup_wfc_non_apm(self):
        if CAPABILITY_WFC not in self.dut_capabilities and (
                CAPABILITY_WFC_MODE_CHANGE not in self.dut_capabilities):
            raise signals.TestSkip(
                "WFC in non-APM is not supported, abort test.")
        if not phone_setup_iwlan(
                self.log, self.dut, False, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            return False
        self.dut.log.info("Phone is in WFC enabled state.")
        return True

    def _setup_wfc_apm(self):
        if CAPABILITY_WFC not in self.dut_capabilities:
            raise signals.TestSkip("WFC is not supported, abort test.")
        if not phone_setup_iwlan(
                self.log, self.dut, True, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            return False
        self.dut.log.info("Phone is in WFC enabled state.")
        return True

    def _setup_volte(self):
        if CAPABILITY_VOLTE not in self.dut_capabilities:
            raise signals.TestSkip("VoLTE is not supported, abort test.")
        if not phone_setup_volte(self.log, self.dut):
            self.dut.log.error("Phone failed to enable VoLTE.")
            return False
        self.dut.log.info("Phone VOLTE is enabled successfully.")
        return True

    def _setup_csfb(self):
        if not phone_setup_csfb(self.log, self.dut):
            self.dut.log.error("Phone failed to setup CSFB.")
            return False
        return True

    def _setup_3g(self):
        if not phone_setup_voice_3g(self.log, self.dut):
            self.dut.log.error("Phone failed to setup 3g.")
            return False
        self.dut.log.info("Phone RAT 3G is enabled successfully.")
        return True

    def _setup_2g(self):
        if self.dut_operator not in ("tmo", "uk_ee"):
            raise signals.TestSkip("2G is not supported, abort test.")
        if not phone_setup_voice_2g(self.log, self.dut):
            self.dut.log.error("Phone failed to setup 2g.")
            return False
        self.dut.log.info("RAT 2G is enabled successfully.")
        return True

    def _setup_vt(self):
        if CAPABILITY_VT not in self.dut_capabilities or (
                CAPABILITY_VT not in self.reference_capabilities):
            raise signals.TestSkip("VT is not supported, abort test.")
        for ad in (self.dut, self.ad_reference):
            if not phone_setup_video(self.log, ad):
                ad.log.error("Failed to setup VT.")
                return False
            return True

    def _check_tethering(self):
        self.log.info("Check tethering")
        for i in range(3):
            try:
                if not self.dut.droid.carrierConfigIsTetheringModeAllowed(
                        TETHERING_MODE_WIFI,
                        MAX_WAIT_TIME_TETHERING_ENTITLEMENT_CHECK):
                    self.log.error("Tethering Entitlement check failed.")
                    if i == 2: return False
                    time.sleep(10)
            except Exception as e:
                if i == 2:
                    self.dut.log.error(e)
                    return False
                time.sleep(10)
        if not wifi_tethering_setup_teardown(
                self.log,
                self.dut, [self.ad_reference],
                check_interval=5,
                check_iteration=1):
            self.log.error("Tethering check failed.")
            return False
        return True

    def _trigger_modem_crash(self):
        # Modem SSR
        self.user_params["check_crash"] = False
        self.dut.log.info("Triggering ModemSSR")
        try:
            self.dut.droid.logI("======== Trigger modem crash ========")
        except Exception:
            pass
        if (not self.dut.is_apk_installed("com.google.mdstest")
            ) or self.dut.adb.getprop("ro.build.version.release")[0] in (
                "8", "O", "7", "N") or self.dut.model in ("angler", "bullhead",
                                                          "sailfish",
                                                          "marlin"):
            trigger_modem_crash(self.dut)
        else:
            trigger_modem_crash_by_modem(self.dut)

    def _call_drop_by_modem_crash(self,
                                  call_verification_function=None,
                                  vt=False):
        if vt:
            if not video_call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    None,
                    video_state=VT_STATE_BIDIRECTIONAL,
                    verify_caller_func=is_phone_in_call_video_bidirectional,
                    verify_callee_func=is_phone_in_call_video_bidirectional):
                self.dut.log.error("VT Call Failed.")
                return False
        else:
            if not call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    ad_hangup=None,
                    verify_caller_func=call_verification_function,
                    wait_time_in_call=10):
                self.log.error("Call setup failed")
                return False

        # Modem SSR
        self._trigger_modem_crash()

        try:
            if self.dut.droid.telecomIsInCall():
                self.dut.log.info("Still in call after trigger modem crash")
                return False
            else:
                reasons = self.dut.search_logcat(
                    "qcril_qmi_voice_map_qmi_to_ril_last_call_failure_cause")
                if reasons:
                    self.dut.log.info(reasons[-1]["log_message"])
        except Exception as e:
            self.dut.log.error(e)

    def _trigger_toggling_apm(self):
        self.user_params["check_crash"] = True
        # Toggle airplane mode
        toggle_airplane_mode(self.log, self.dut, new_state=None)
        time.sleep(5)
        toggle_airplane_mode(self.log, self.dut, new_state=None)
        time.sleep(5)

    def _parsing_call_summary(self):
        call_summary = self.dut.adb.shell(
            "dumpsys activity service com.google.android.connectivitymonitor/"
            ".ConnectivityMonitorService")
        self.dut.log.info(call_summary)
        call_summary_info = {}
        results = re.findall(r"(\S+): (\d+) out of (\d+) calls dropped",
                             call_summary)
        for result in results:
            call_summary_info[result[0]] = int(result[2])
            call_summary_info["%s_dropped" % result[0]] = int(result[1])
        results = re.findall(r"(\S+): predominant failure reason=(.+)",
                             call_summary)
        for result in results:
            call_summary_info["%s_failure_reason" % result[0]] = result[1]
        return call_summary_info

    def _call_drop_with_connectivity_monitor(self,
                                             setup=None,
                                             trigger="modem_crash"):
        """
        Steps -
        1. Start Telephony Monitor using adb/developer options
        2. Verify if it is running
        3. Turn off connectivity monitor
        4. Phone Call from A to B
        5. Answer on B
        6. Trigger ModemSSR on A
        7. There will be a call drop with Media Timeout/Server Unreachable
        8. Parse logcat to confirm that

        Expected Results:
            UI Notification is received by User

        Returns:
            True is pass, False if fail.
        """
        call_verification_function = None
        if trigger and trigger != "toggling_apm":
            checking_counters = ["Calls", "Calls_dropped"]
        else:
            checking_counters = ["Calls"]
        checking_reasons = []
        result = True
        if setup:
            if not hasattr(self, "_setup_%s" % setup):
                self.log.error("_setup_%s function is not defined", setup)
                return False
            else:
                func = getattr(self, "_setup_%s" % setup)
                if not func():
                    return False
                if setup in ("wfc_apm", "wfc_non_apm"):
                    call_verification_function = is_phone_in_call_iwlan
                    checking_counters.append("VOWIFI")
                    if trigger and trigger != "toggling_apm":
                        checking_counters.append("VOWIFI_dropped")
                        checking_reasons.append("VOWIFI_failure_reason")
                elif setup == "volte":
                    call_verification_function = is_phone_in_call_volte
                    checking_counters.append("VOLTE")
                    if trigger and trigger != "toggling_apm":
                        checking_counters.append("VOLTE_dropped")
                        checking_reasons.append("VOLTE_failure_reason")
                elif setup in ("csfb", "3g", "2g"):
                    checking_counters.append("CS")
                    if trigger and trigger != "toggling_apm":
                        checking_counters.append("CS_dropped")
                        checking_reasons.append("CS_failure_reason")
                    if setup == "csfb":
                        call_verification_function = is_phone_in_call_csfb
                    elif setup == "3g":
                        call_verification_function = is_phone_in_call_3g
                    elif setup == "2g":
                        call_verification_function = is_phone_in_call_2g

        call_data_summary_before = self._parsing_call_summary()

        if setup == "vt":
            if not video_call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    None,
                    video_state=VT_STATE_BIDIRECTIONAL,
                    verify_caller_func=is_phone_in_call_video_bidirectional,
                    verify_callee_func=is_phone_in_call_video_bidirectional):
                self.dut.log.error("VT Call Failed.")
                return False
        else:
            if not call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    ad_hangup=None,
                    verify_caller_func=call_verification_function,
                    wait_time_in_call=10):
                self.log.error("Call setup failed")
                return False

        # Trigger in-call event to drop the call
        if trigger == "modem_crash":
            self._trigger_modem_crash()
        elif trigger == "toggling_apm":
            self._trigger_toggling_apm()

        expected_reason = None
        try:
            if self.dut.droid.telecomIsInCall():
                hangup_call(self.log, self.dut)
                if trigger:
                    self.dut.log.info("Still in call after trigger %s",
                                      trigger)
                    result = False
            else:
                self.dut.log.info("Not in call anymore, there is call drop")
                reasons = self.dut.search_logcat(
                    "qcril_qmi_voice_map_qmi_to_ril_last_call_failure_cause")
                if reasons:
                    log_msg = reasons[-1]["log_message"]
                    self.dut.log.info(log_msg)
                    search_result = re.search(r"ril reason str: (.+)", log_msg)
                    if search_result:
                        expected_reason = search_result.group(1)
        except Exception as e:
            self.dut.log.error(e)

        call_data_summary_after = self._parsing_call_summary()

        for counter in checking_counters:
            if call_data_summary_after.get(
                    counter,
                    0) != call_data_summary_before.get(counter, 0) + 1:
                self.dut.log.error("Counter %s did not increase", counter)
                result = False
        for reason_key in checking_reasons:
            if call_data_summary_after.get(reason_key):
                drop_reason = call_data_summary_after[reason_key]
                self.dut.log.info("%s is: %s", reason_key, drop_reason)
                if expected_reason and drop_reason.strip(
                ) not in expected_reason:
                    self.dut.log.warning(
                        "call failure reason '%s' does not match "
                        "ril reason string '%s' in logcat", drop_reason,
                        expected_reason)
            else:
                self.dut.log.error("%s is not provided in summary report",
                                   reason_key)
                result = False

        if not trigger or trigger == "toggling_apm":
            return result
        # Parse logcat for UI notification only for the first failure
        if self.dut.search_logcat("Bugreport notification title Call Drop:",
                                  self.begin_time):
            self.dut.log.info("User got the Call Drop Notification with "
                              "TelephonyMonitor/ConnectivityMonitor on")
            return result
        else:
            self.dut.log.warning("User didn't get Call Drop Notify with "
                                 "TelephonyMonitor/ConnectivityMonitor on")
            if call_data_summary_after.get("Calls_dropped", 0) > 1:
                return result
            else:
                return False

    """ Tests Begin """

    @test_tracker_info(uuid="96ee7af3-96cf-48a7-958b-834684b670dc")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor()

    @test_tracker_info(uuid="6b9c8f45-a3cc-4fa8-9a03-bc439ed5b415")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_volte(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="volte")

    @test_tracker_info(uuid="bf9938a7-7001-4d95-be23-95ece5392805")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_volte(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               not counted as call drop by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="volte", trigger="toggling_apm")

    @test_tracker_info(uuid="b91a1e8d-3630-4b81-bc8c-c7d3dad42c77")
    @TelephonyBaseTest.tel_test_wrap
    def test_healthy_call_with_connectivity_monitor_volte(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. No call drop during the call
            3. Verify the call summary report

        Expected Results:
            feature work fine, and healthy call is added to report

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="volte", trigger=None)

    @test_tracker_info(uuid="f2633204-c2ac-4c57-9465-ef6de3223de3")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_csfb(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="csfb")

    @test_tracker_info(uuid="8e1ba024-3b43-4a7d-adc8-2252da81c55c")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_csfb(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="csfb", trigger="toggling_apm")

    @test_tracker_info(uuid="2f581f6a-087f-4d12-a75c-a62778cb741b")
    @TelephonyBaseTest.tel_test_wrap
    def test_healthy_call_with_connectivity_monitor_csfb(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="csfb", trigger=None)

    @test_tracker_info(uuid="ec274cb6-0b75-4026-94a7-0228a43a0f5f")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_3g(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="3g")

    @test_tracker_info(uuid="fe6afae4-fa04-435f-8bbc-4a63f5fb525c")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_3g(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="3g", trigger="toggling_apm")

    @test_tracker_info(uuid="b9b439c0-4200-47d6-824b-f12b64dfeecd")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_2g(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="2g")

    @test_tracker_info(uuid="cc089e2b-d0e1-42a3-80de-597986be3d4e")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_2g(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="2g", trigger="toggling_apm")

    @test_tracker_info(uuid="a4e43270-f7fa-4709-bbe2-c7368af39227")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_vt(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="vt")

    @test_tracker_info(uuid="cb52110c-7470-4886-b71f-e32f0e489cbd")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_vt(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="vt", trigger="toggling_apm")

    @test_tracker_info(uuid="1c880cf8-082c-4451-b890-22081177d084")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_wfc_apm(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="wfc_apm")

    @test_tracker_info(uuid="f8ba9655-572c-4a90-be59-6a5bc9a8fad0")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_wfc_apm(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="wfc_apm", trigger="toggling_apm")

    @test_tracker_info(uuid="a5989001-8201-4356-9903-581d0e361b38")
    @TelephonyBaseTest.tel_test_wrap
    def test_healthy_call_with_connectivity_monitor_wfc_apm(self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Make a call and hung up the call
            3. Verify the healthy call is added to the call summary report

        Expected Results:
            feature work fine

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="wfc_apm", trigger=None)

    @test_tracker_info(uuid="0210675f-5c62-4803-bcc1-c36dbe5da125")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_with_connectivity_monitor_wfc_non_apm(
            self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(setup="wfc_non_apm")

    @test_tracker_info(uuid="f2995df9-f56d-442c-977a-141e3269481f")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_toggling_apm_with_connectivity_monitor_wfc_non_apm(
            self):
        """Telephony Monitor Functional Test

        Steps:
            1. Verify Connectivity Monitor is on
            2. Force Trigger a call drop : media timeout and ensure it is
               notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        return self._call_drop_with_connectivity_monitor(
            setup="wfc_non_apm", trigger="toggling_apm")

    @test_tracker_info(uuid="df101d61-10e1-4fa7-bbc3-c1402e5ad59e")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drop_by_modem_crash_without_connectivity_monitor(self):
        """Connectivity Monitor Off Test

        Steps:
            1. Verify Connectivity Monitor can be turned off
            2. Force Trigger a call drop : media timeout and ensure it is
               not notified by Connectivity Monitor

        Expected Results:
            feature work fine, and does not report to User about Call Drop

        Returns:
            True is pass, False if fail.
        """
        try:
            bring_up_connectivity_monitor(self.dut)
            toggle_connectivity_monitor_setting(self.dut, False)

            self._call_drop_by_modem_crash()
            if self.dut.search_logcat(
                    "Bugreport notification title Call Drop:",
                    self.begin_time):
                self.dut.log.error("User got the Call Drop Notification with "
                                   "TelephonyMonitor/ConnectivityMonitor off")
                return False
            else:
                self.dut.log.info("User didn't get Call Drop Notify with "
                                  "TelephonyMonitor/ConnectivityMonitor off")
                return True
        finally:
            bring_up_connectivity_monitor(self.dut)
            reboot_device(self.dut)


""" Tests End """
