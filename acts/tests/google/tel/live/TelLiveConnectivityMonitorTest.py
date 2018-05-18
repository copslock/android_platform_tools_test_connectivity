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
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_FOR_STATE_CHANGE
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_TETHERING_ENTITLEMENT_CHECK
from acts.test_utils.tel.tel_defines import TETHERING_MODE_WIFI
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_defines import VT_STATE_BIDIRECTIONAL
from acts.test_utils.tel.tel_test_utils import bring_up_connectivity_monitor
from acts.test_utils.tel.tel_test_utils import call_setup_teardown
from acts.test_utils.tel.tel_test_utils import ensure_wifi_connected
from acts.test_utils.tel.tel_test_utils import fastboot_wipe
from acts.test_utils.tel.tel_test_utils import get_device_epoch_time
from acts.test_utils.tel.tel_test_utils import get_model_name
from acts.test_utils.tel.tel_test_utils import get_operator_name
from acts.test_utils.tel.tel_test_utils import hangup_call
from acts.test_utils.tel.tel_test_utils import last_call_drop_reason
from acts.test_utils.tel.tel_test_utils import reboot_device
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import toggle_connectivity_monitor_setting
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

CALL_DROP_CODE_MAPPING = {
    373: "Radio Internal Error",
    175: "Invalid Transaction Identifier V02",
    159: "Temporary Failure",
    135: "Rejected by Network V02",
    118: "SS Not Available",
    115: "Call Barred V02",
    42: "Access Block V02",
    41: "Incompatible V02"
}

CONSECUTIVE_CALL_FAILS = 5
CALL_TROUBLE_THRESHOLD = 25
TROUBLES = [
    "WIFI_CALL_DROPS_IN_BAD_WIFI_SIGNAL",
    "WIFI_CALL_DROPS_IN_GOOD_WIFI_SIGNAL_ON_SPECIFIC_WIFI_NETWORK",
    "WIFI_CALL_DROPS_WITH_SPECIFIC_REASON_IN_GOOD_WIFI_SIGNAL",
    "WIFI_CALL_DROPS_WITH_RANDOM_FAILURES_IN_GOOD_WIFI_SIGNAL",
    "VOLTE_CALL_DROPS_IN_BAD_LTE_SIGNAL_AREAS",
    "VOLTE_CALL_DROPS_IN_GOOD_LTE_SIGNAL_AREAS", "CS_CALL_DROPS_IMS_DISABLED",
    "CS_CALL_DROPS_WFC_DISABLED", "CS_CALL_DROPS_IMS_REGISTRATION_FAILURES",
    "CS_CALL_DROPS_DURING_SRVCC", "CS_CALL_DROPS_IN_BAD_RF_CONDITIONS",
    "CS_CALL_DROPS_IN_GOOD_RF_CONDITIONS_WITH_SPECIFIC_REASON",
    "UNABLE_TO_TRIAGE"
]

ACTIONS = [
    "CHECK_BLUETOOTH", "CHECK_HEADSET",
    "SWITCH_FROM_WIFI_PREFERRED_TO_CELLULAR_PREFERRED",
    "SWITCH_FROM_CELLULAR_PREFERRED_TO_WIFI_PREFERRED",
    "ENABLE_ADVANCED_4G_CALLING", "DISABLE_ADVANCED_4G_CALLING",
    "TOGGLE_AIRPLANE_MODE_TWICE", "REBOOT_THE_PHONE", "ENABLE_WIFI_CALLING",
    "DISABLE_WIFI_CALLING", "DISABLE_AIRPLANE_MODE", "NONE"
]


class TelLiveConnectivityMonitorTest(TelephonyBaseTest):
    def setup_class(self):
        TelephonyBaseTest.setup_class(self)
        self.dut = self.android_devices[0]
        self.ad_reference = self.android_devices[1]
        self.dut_model = get_model_name(self.dut)
        self.dut_operator = get_operator_name(self.log, self.dut)
        self.dut_capabilities = self.dut.telephony.get("capabilities", [])
        self.dut_wfc_modes = self.dut.telephony.get("wfc_modes", [])
        self.reference_capabilities = self.ad_reference.telephony.get(
            "capabilities", [])
        self.dut.log.info("DUT capabilities: %s", self.dut_capabilities)
        self.skip_reset_between_cases = False
        self.user_params["telephony_auto_rerun"] = 0
        self.number_of_devices = 1
        self.call_drop_override_code = self.user_params.get(
            "call_drop_override_code", 373)

    def setup_test(self):
        TelephonyBaseTest.setup_test(self)
        bring_up_connectivity_monitor(self.dut)

    def teardown_test(self):
        self.set_drop_reason_override(override_code=None)
        TelephonyBaseTest.teardown_test(self)

    def connect_to_wifi(self):
        if not ensure_wifi_connected(self.log, self.dut,
                                     self.wifi_network_ssid,
                                     self.wifi_network_pass):
            self.dut.log.error("Fail to connected to WiFi")
            return False
        else:
            self.dut.log.info("Connected to WiFi")
            return True

    def setup_wfc_non_apm(self):
        if CAPABILITY_WFC not in self.dut_capabilities and (
                WFC_MODE_WIFI_PREFERRED not in self.dut_wfc_modes):
            raise signals.TestSkip(
                "WFC in non-APM is not supported, abort test.")
        if not phone_setup_iwlan(
                self.log, self.dut, False, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            raise signals.TestFailure("Failed to setup WFC in non-APM")
        self.dut.log.info("Phone is in WFC enabled state.")
        return True

    def setup_wfc_apm(self):
        if CAPABILITY_WFC not in self.dut_capabilities:
            raise signals.TestSkip("WFC is not supported, abort test.")
        if not phone_setup_iwlan(
                self.log, self.dut, True, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            raise signals.TestFailure("Failed to setup WFC in APM")
        self.dut.log.info("Phone is in WFC enabled state.")
        return True

    def setup_volte(self):
        if CAPABILITY_VOLTE not in self.dut_capabilities:
            raise signals.TestSkip("VoLTE is not supported, abort test.")
        if not phone_setup_volte(self.log, self.dut):
            self.dut.log.error("Phone failed to enable VoLTE.")
            raise signals.TestFailure("Failed to enable VoLTE")
        self.dut.log.info("Phone VOLTE is enabled successfully.")
        return True

    def setup_csfb(self):
        if not phone_setup_csfb(self.log, self.dut):
            self.dut.log.error("Phone failed to setup CSFB.")
            raise signals.TestFailure("Failed to setup CSFB")
        return True

    def setup_3g(self):
        if not phone_setup_voice_3g(self.log, self.dut):
            self.dut.log.error("Phone failed to setup 3G.")
            raise signals.TestFailure("Faile to setup 3G")
        self.dut.log.info("Phone RAT 3G is enabled successfully.")
        return True

    def setup_2g(self):
        if self.dut_operator not in ("tmo", "uk_ee"):
            raise signals.TestSkip("2G is not supported, abort test.")
        if not phone_setup_voice_2g(self.log, self.dut):
            self.dut.log.error("Phone failed to setup 2G.")
            raise signals.TestFailure("Failed to setup 2G")
        self.dut.log.info("RAT 2G is enabled successfully.")
        return True

    def setup_vt(self):
        if CAPABILITY_VT not in self.dut_capabilities or (
                CAPABILITY_VT not in self.reference_capabilities):
            raise signals.TestSkip("VT is not supported, abort test.")
        for ad in (self.dut, self.ad_reference):
            if not phone_setup_video(self.log, ad):
                ad.log.error("Failed to setup VT.")
                return False
            return True

    def set_drop_reason_override(self, override_code=None):
        if not override_code:
            if self.dut.adb.shell("getprop vendor.radio.call_end_reason"):
                self.dut.adb.shell("setprop vendor.radio.call_end_reason ''")
        else:
            if self.dut.adb.shell("getprop vendor.radio.call_end_reason"
                                  ) != str(override_code):
                cmd = "setprop vendor.radio.call_end_reason %s"\
                      % override_code
                self.dut.log.info("====== %s ======", cmd)
                self.dut.adb.shell(cmd)

    def trigger_modem_crash(self):
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

    def call_drop_by_modem_crash(self,
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
        self.trigger_modem_crash()

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

    def trigger_toggling_apm(self):
        self.user_params["check_crash"] = True
        # Toggle airplane mode
        toggle_airplane_mode(self.log, self.dut, new_state=None)
        time.sleep(5)
        toggle_airplane_mode(self.log, self.dut, new_state=None)
        time.sleep(5)

    def clearn_up_bugreport_database(self):
        self.dut.adb.shell(
            "rm /data/data/com.google.android.connectivitymonitor/"
            "shared_prefs/ConnectivityMonitor_BugReport.xml")

    def clearn_up_troubleshooter_database(self):
        self.dut.adb.shell(
            "rm /data/data/com.google.android.connectivitymonitor/"
            "shared_prefs/ConnectivityMonitor_TroubleshooterResult.xml")

    def parsing_bugreport_database(self):
        output = self.dut.adb.shell(
            "cat /data/data/com.google.android.connectivitymonitor/"
            "shared_prefs/ConnectivityMonitor_BugReport.xml")
        return re.findall(r"<string>(\S+)</string>", output)

    def parsing_troubleshooter_database(self):
        output = self.dut.adb.shell(
            "cat /data/data/com.google.android.connectivitymonitor/"
            "shared_prefs/ConnectivityMonitor_TroubleshooterResult.xml")
        results = re.findall(r"name=\"(\S+)\">(\S+)<", output)
        troubleshooter_database = {}
        for result in results:
            if "count" in result[0] or "num_calls" in result[0]:
                troubleshooter_database[result[0]] = int(result[1])
            else:
                troubleshooter_database[result[0]] = result[1]
        self.dut.log.info("TroubleshooterResult=%s",
                          sorted(troubleshooter_database.items()))
        return troubleshooter_database

    def parsing_call_summary(self):
        call_summary = self.dut.adb.shell(
            "dumpsys activity service com.google.android.connectivitymonitor/"
            ".ConnectivityMonitorService")
        self.dut.log.info(call_summary)
        call_summary_info = {}
        results = re.findall(
            r"(\S+): (\d+) out of (\d+) calls dropped, percentage=(\S+)",
            call_summary)
        for result in results:
            call_summary_info[result[0]] = int(result[2])
            call_summary_info["%s_dropped" % result[0]] = int(result[1])
            if result[3] == "NaN":
                call_summary_info["%s_dropped_percentage" % result[0]] = 0
            else:
                call_summary_info["%s_dropped_percentage" % result[0]] = float(
                    result[3])
        results = re.findall(r"(\S+): predominant failure reason=(.+)",
                             call_summary)
        for result in results:
            call_summary_info["%s_failure_reason" % result[0]] = result[1]
        self.dut.log.info("call summary dumpsys = %s",
                          sorted(call_summary_info.items()))
        return call_summary_info

    def parsing_call_statistics(self):
        call_statistics_info = {}
        call_statistics = self.dut.adb.shell(
            "content query --uri content://com.google.android."
            "connectivitymonitor.troubleshooterprovider/call_statistics")
        self.dut.log.info("troubleshooterprovider call_statistics:\n%s",
                          call_statistics)
        results = re.findall(r"KEY=(\S+), VALUE=(\S+)", call_statistics)
        for result in results:
            if ("count" in result[0] or "num_calls" in result[0]):
                if result[1] == "NULL":
                    call_statistics_info[result[0]] = 0
                else:
                    call_statistics_info[result[0]] = int(result[1])
            else:
                call_statistics_info[result[0]] = result[1]
        self.dut.log.info("troubleshooterprovider call_statistics: %s",
                          sorted(call_statistics_info.items()))
        return call_statistics_info

    def parsing_diagnostics(self):
        diagnostics_info = {}
        diagnostics = self.dut.adb.shell(
            "content query --uri content://com.google.android."
            "connectivitymonitor.troubleshooterprovider/diagnostics")
        self.dut.log.info("troubleshooterprovider diagnostics:\n%s",
                          diagnostics)
        results = re.findall(r"KEY=(\S+), VALUE=(\S+)", diagnostics)
        for result in results:
            diagnostics_info[result[0]] = result[1]
        self.dut.log.info("troubleshooterprovider diagnostics: %s",
                          sorted(diagnostics_info.items()))
        return diagnostics_info

    def call_setup_and_connectivity_monitor_checking(
            self, setup=None, trigger=None, expected_drop_reason=None):

        call_verification_function = None
        begin_time = get_device_epoch_time(self.dut)
        call_data_summary_before = self.parsing_call_summary()
        call_statistics_before = self.parsing_call_statistics()
        self.parsing_diagnostics()
        self.parsing_troubleshooter_database()
        bugreport_database_before = self.parsing_bugreport_database()

        checking_counters = ["Calls"]
        checking_reasons = []
        result = True
        if setup in ("wfc_apm", "wfc_non_apm"):
            call_verification_function = is_phone_in_call_iwlan
            if trigger and trigger != "toggling_apm":
                checking_counters.extend(
                    ["Calls_dropped", "VOWIFI", "VOWIFI_dropped"])
                checking_reasons.append("VOWIFI_failure_reason")
            elif call_data_summary_before.get("Calls_dropped", 0):
                checking_counters.append("VOWIFI")
        elif setup == "volte":
            call_verification_function = is_phone_in_call_volte
            if trigger and trigger != "toggling_apm":
                checking_counters.extend(
                    ["Calls_dropped", "VOLTE", "VOLTE_dropped"])
                checking_reasons.append("VOLTE_failure_reason")
            elif call_data_summary_before.get("Calls_dropped", 0):
                checking_counters.append("VOLTE")
        elif setup in ("csfb", "3g", "2g"):
            if trigger and trigger != "toggling_apm":
                checking_counters.extend(["Calls_dropped", "CS", "CS_dropped"])
                checking_reasons.append("CS_failure_reason")
            elif call_data_summary_before.get("Calls_dropped", 0):
                checking_counters.append("CS")
            if setup == "csfb":
                call_verification_function = is_phone_in_call_csfb
            elif setup == "3g":
                call_verification_function = is_phone_in_call_3g
            elif setup == "2g":
                call_verification_function = is_phone_in_call_2g
        call_setup_result = True
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
                call_setup_result = False
        else:
            if not call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    ad_hangup=None,
                    verify_caller_func=call_verification_function,
                    wait_time_in_call=10):
                self.log.error("Call setup failed")
                call_setup_result = False

        if call_setup_result:
            # Trigger in-call event to drop the call
            if trigger == "modem_crash":
                self.trigger_modem_crash()
            elif trigger == "toggling_apm":
                self.trigger_toggling_apm()
            elif trigger == "drop_reason_override":
                hangup_call(self.log, self.ad_reference)
                time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)

        last_call_drop_reason(self.dut, begin_time)
        for ad in (self.ad_reference, self.dut):
            try:
                if ad.droid.telecomIsInCall():
                    if trigger:
                        ad.log.info("Still in call after trigger %s", trigger)
                        result = False
                    hangup_call(self.log, ad)
                    time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)
            except Exception as e:
                ad.log.error(e)

        call_data_summary_after = self.parsing_call_summary()
        call_statistics_after = self.parsing_call_statistics()
        diagnostics_after = self.parsing_diagnostics()
        ts_database_after = self.parsing_troubleshooter_database()

        for counter in checking_counters:
            if call_data_summary_after.get(
                    counter,
                    0) != call_data_summary_before.get(counter, 0) + 1:
                self.dut.log.error("Counter %s did not increase", counter)
                result = False
            else:
                self.dut.log.info("Counter %s increased", counter)
            if counter == "Calls":
                if call_statistics_after.get("num_calls",
                                             0) - call_statistics_before.get(
                                                 "num_calls", 0) < 1:
                    self.dut.log.error(
                        "call_statistics num_calls didn't increase")
                    # result = False
                else:
                    self.dut.log.info("call_statistics num_calls increased")
            if "_dropped" in counter and counter != "Calls_dropped":
                desc = counter.split("_")[0]
                if desc == "VOWIFI":
                    stat_key = "recent_wfc_fail_count"
                else:
                    stat_key = "recent_%s_fail_count" % desc.lower()
                before = call_statistics_after.get(stat_key, 0)
                after = call_statistics_after.get(stat_key, 0)
                most_failure_call_type = call_statistics_after.get(
                    "call_type_with_most_failures")
                diagnosis = diagnostics_after.get("diagnosis")
                actions = diagnostics_after.get("actions")
                if after - before < 1:
                    self.dut.log.error("call_statistics %s didn't increase, "
                                       "before %s, after %s" % (stat_key,
                                                                before, after))
                    # result = False
                else:
                    self.dut.log.info("call_statistics %s increased", stat_key)
                if most_failure_call_type != desc:
                    self.dut.log.error(
                        "call_statistics call_type_with_most_failures "
                        "is %s, not %s", most_failure_call_type, desc)
                    # result = False
                else:
                    self.dut.log.info(
                        "call_statistics call_type_with_most_failures is %s",
                        most_failure_call_type)
                dropped = call_data_summary_after.get("%s_dropped" % desc, 0)
                drop_percentage = call_data_summary_after.get(
                    "%s_dropped_percentage" % desc, 0)
                self.dut.log.info("%s_dropped = %s, percentage = %s", desc,
                                  dropped, drop_percentage)
                if drop_percentage > CALL_TROUBLE_THRESHOLD and dropped > CONSECUTIVE_CALL_FAILS:
                    if diagnosis == "UNABLE_TO_TRIAGE":
                        self.dut.log.error(
                            "troubleshooter failed to triage failure,"
                            "diagnosis = %s", diagnosis)
                        result = False
                    if actions == "NONE":
                        self.dut.log.error(
                            "troubleshooter failed to provide suggestion, "
                            "actions = %s", actions)
                        result = False

        for reason_key in checking_reasons:
            if call_data_summary_after.get(reason_key, None):
                drop_reason = call_data_summary_after[reason_key]
                if drop_reason != expected_drop_reason:
                    self.dut.log.error("%s is: %s, expecting %s", reason_key,
                                       drop_reason, expected_drop_reason)
                else:
                    self.dut.log.info("%s is: %s", reason_key, drop_reason)
            else:
                self.dut.log.error("%s is not provided in summary report",
                                   reason_key)
                result = False

        if not trigger or trigger == "toggling_apm" or "Call Drop: %s" % (
                expected_drop_reason) in bugreport_database_before:
            return result
        # Parse logcat for UI notification only for the first failure
        if self.dut.search_logcat("Bugreport notification title Call Drop:",
                                  begin_time):
            self.dut.log.info(
                "Bugreport notification title Call Drop is seen in logcat")
            return result
        else:
            self.dut.log.warning(
                "Bugreport notification title Call Drop is not seen in logcat")
            if call_data_summary_after.get("Calls_dropped", 0) > 1:
                return result
            else:
                return False

    def call_drop_test(self, setup=None, count=CONSECUTIVE_CALL_FAILS):
        result = True
        drop_reason = None
        if self.dut.model in ("marlin", "sailfish", "walleye", "taimen"):
            trigger = "modem_crash"
            drop_reason = "Error Unspecified"
        else:
            trigger = "drop_reason_override"
            self.set_drop_reason_override(
                override_code=self.call_drop_override_code)
            drop_reason = CALL_DROP_CODE_MAPPING[int(
                self.call_drop_override_code)]
        for iter in range(count):
            if not self.call_setup_and_connectivity_monitor_checking(
                    setup=setup, trigger=trigger,
                    expected_drop_reason=drop_reason):
                self._ad_take_bugreport(self.dut, "%s_%s_iter_%s_failure" %
                                        (self.test_name, trigger,
                                         iter + 1), self.begin_time)
                result = False
        return result

    def call_drop_triggered_suggestion_test(self, setup=None):
        call_summary = self.parsing_call_summary()
        total_call = 0
        if setup in ("wfc_apm", "wfc_non_apm"):
            total_call = call_summary.get("VOWIFI", 0)
        elif setup == "volte":
            total_call = call_summary.get("VOLTE", 0)
        elif setup in ("csfb", "3g", "2g"):
            total_call = call_summary.get("CS", 0)
        if total_call < CONSECUTIVE_CALL_FAILS:
            total_call = CONSECUTIVE_CALL_FAILS
        else:
            total_call = total_call + CONSECUTIVE_CALL_FAILS
        self.dut.log.info("Generate %s call drops countinously", total_call)
        result = self.call_drop_test(setup=setup, count=total_call)
        self.dut.log.info("Generate %s healthy calls countinously", total_call)
        if not self.healthy_call_test(setup=setup, count=total_call):
            result = False
        return result

    def healthy_call_test(self, setup=None, count=1):
        if self.dut.model not in ("marlin", "sailfish", "walleye", "taimen"):
            self.set_drop_reason_override(override_code=25)
        result = True
        for iter in range(count):
            if not self.call_setup_and_connectivity_monitor_checking(
                    setup=setup, trigger=None):
                self._ad_take_bugreport(
                    self.dut, "%s_healthy_call_iter_%s_failure" %
                    (self.test_name, iter + 1), self.begin_time)
                result = False
        return result

    def call_drop_test_after_wipe(self, setup=None, count=5):
        func = getattr(self, "setup_%s" % setup)
        if not func(): return False
        fastboot_wipe(self.dut)
        bring_up_connectivity_monitor(self.dut)
        if not func(): return False
        return self.call_drop_triggered_suggestion_test(setup=setup)

    def call_drop_test_after_reboot(self, setup=None):
        func = getattr(self, "setup_%s" % setup)
        if not func(): return False
        self.call_drop_test(setup=setup, count=CONSECUTIVE_CALL_FAILS)
        self.healthy_call_test(setup=setup, count=1)
        reboot_device(self.dut)
        return self.call_drop_triggered_suggestion_test(setup=setup)

    """ Tests Begin """

    @test_tracker_info(uuid="fee3d03d-701b-4727-9320-426ff6b29974")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_call_drop_triggered_suggestion(self):
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
        self.setup_volte()
        return self.call_drop_triggered_suggestion_test(setup="volte")

    @test_tracker_info(uuid="8c3ee59a-74e5-4885-8f42-8a15d4550d5f")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_call_drop_triggered_suggestion(self):
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
        self.setup_csfb()
        return self.call_drop_triggered_suggestion_test(setup="csfb")

    @test_tracker_info(uuid="6cd12786-c048-4925-8745-1d5d30094257")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_call_drop_triggered_suggestion(self):
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
        self.setup_3g()
        return self.call_drop_triggered_suggestion_test(setup="3g")

    @test_tracker_info(uuid="51166448-cea6-480b-93d8-7063f940ce0a")
    @TelephonyBaseTest.tel_test_wrap
    def test_2g_call_drop_triggered_suggestion(self):
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
        self.setup_2g()
        return self.call_drop_triggered_suggestion_test(setup="2g")

    @test_tracker_info(uuid="409f3331-5d64-4793-b300-2b3d3fa50ba5")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_apm_call_drop_triggered_suggestion(self):
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
        self.setup_wfc_apm()
        return self.call_drop_triggered_suggestion_test(setup="wfc_apm")

    @test_tracker_info(uuid="336c383f-ec19-4447-af37-7f9bb0bac4dd")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_non_apm_call_drop_triggered_suggestion(self):
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
        self.setup_wfc_non_apm()
        return self.call_drop_triggered_suggestion_test(setup="wfc_non_apm")

    @test_tracker_info(uuid="fd8d22ac-66b2-4e91-a922-8ecec45c85e6")
    @TelephonyBaseTest.tel_test_wrap
    def test_vt_call_drop_triggered_suggestion(self):
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
        self.setup_vt()
        return self.call_drop_triggered_suggestion_test(setup="vt")

    @test_tracker_info(uuid="11c4068e-9710-4a40-8587-79d32a68a37e")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="volte")

    @test_tracker_info(uuid="8c7083e1-7c06-40c9-9a58-485adceb8690")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="csfb")

    @test_tracker_info(uuid="a7938250-ea3c-4d37-85fe-72edf67c61f7")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="3g")

    @test_tracker_info(uuid="24f498c4-26c5-447f-8e7d-fc3ff1d1e9d5")
    @TelephonyBaseTest.tel_test_wrap
    def test_2g_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="2g")

    @test_tracker_info(uuid="9fd0fc1e-9480-40b7-bd6f-fe6ac95c2018")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_apm_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="wfc_apm")

    @test_tracker_info(uuid="8fd9f1a0-b1e0-4469-8617-608ed0682f91")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_non_apm_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="wfc_non_apm")

    @test_tracker_info(uuid="86056126-9c0b-4702-beb5-49b66368a806")
    @TelephonyBaseTest.tel_test_wrap
    def test_vt_call_drop_after_user_data_wipe(self):
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
        return self.call_drop_test_after_wipe(setup="vt")

    @test_tracker_info(uuid="96ee7af3-96cf-48a7-958b-834684b670dc")
    @TelephonyBaseTest.tel_test_wrap
    def test_stats_and_suggestion_after_reboot(self):
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
        return self.call_drop_test_after_reboot(setup="volte")

    @test_tracker_info(uuid="6b9c8f45-a3cc-4fa8-9a03-bc439ed5b415")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_drops_equally_across_all_types(self):
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
        self.setup_wfc_non_apm()
        return self.call_drop_test_after_same_type_healthy_call(
            setup="wfc_non_apm")

    @test_tracker_info(uuid="f2633204-c2ac-4c57-9465-ef6de3223de3")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_call_drop_with_wifi_on_cellular_preferred(self):
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
        self.setup_volte()
        self.connect_to_wifi()
        return self.call_drop_triggered_suggestion_test(setup="volte")

    @test_tracker_info(uuid="ec274cb6-0b75-4026-94a7-0228a43a0f5f")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_call_drop_with_wifi_on_cellular_preferred(self):
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
        self.setup_csfb()
        self.connect_to_wifi()
        return self.call_drop_triggered_suggestion_test(setup="csfb")

    @test_tracker_info(uuid="b9b439c0-4200-47d6-824b-f12b64dfeecd")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_call_drop_with_wifi_on_cellular_preferred(self):
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
        self.setup_3g()
        self.connect_to_wifi()
        return self.call_drop_triggered_suggestion_test(setup="3g")

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

            self.call_drop_by_modem_crash()
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
        self.setup_volte()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="volte", trigger="toggling_apm")

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
        self.setup_csfb()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="csfb", trigger="toggling_apm")

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
        self.setup_3g()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="3g", trigger="toggling_apm")

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
        self.setup_2g()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="2g", trigger="toggling_apm")

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
        self.setup_wfc_apm()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="wfc_apm", trigger="toggling_apm")

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
        self.setup_wfc_non_apm()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="wfc_non_apm", trigger="toggling_apm")

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
        self.setup_vt()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="vt", trigger="toggling_apm")

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
        self.setup_volte()
        return self.healthy_call_test(setup="volte", count=1)

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
        self.setup_csfb()
        return self.healthy_call_test(setup="csfb", count=1)

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
        self.setup_wfc_apm()
        return self.healthy_call_test(setup="wfc_apm", count=1)


""" Tests End """
