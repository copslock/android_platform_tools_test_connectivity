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

import os
import re
import time

from acts import signals
from acts import utils
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import CAPABILITY_VOLTE
from acts.test_utils.tel.tel_defines import CAPABILITY_VT
from acts.test_utils.tel.tel_defines import CAPABILITY_WFC
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_FOR_STATE_CHANGE
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
from acts.test_utils.tel.tel_test_utils import toggle_volte
from acts.test_utils.tel.tel_test_utils import toggle_wfc
from acts.test_utils.tel.tel_test_utils import wifi_toggle_state
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
TROUBLES = {
    1: "WIFI_CALL_DROPS_IN_BAD_WIFI_SIGNAL",
    2: "WIFI_CALL_DROPS_IN_GOOD_WIFI_SIGNAL_ON_SPECIFIC_WIFI_NETWORK",
    3: "WIFI_CALL_DROPS_WITH_SPECIFIC_REASON_IN_GOOD_WIFI_SIGNAL",
    4: "WIFI_CALL_DROPS_WITH_RANDOM_FAILURES_IN_GOOD_WIFI_SIGNAL",
    5: "VOLTE_CALL_DROPS_IN_BAD_LTE_SIGNAL_AREAS",
    6: "VOLTE_CALL_DROPS_IN_GOOD_LTE_SIGNAL_AREAS",
    7: "CS_CALL_DROPS_IMS_DISABLED",
    8: "CS_CALL_DROPS_WFC_DISABLED",
    9: "CS_CALL_DROPS_IMS_REGISTRATION_FAILURES",
    10: "CS_CALL_DROPS_DURING_SRVCC",
    11: "CS_CALL_DROPS_IN_BAD_RF_CONDITIONS",
    12: "CS_CALL_DROPS_IN_GOOD_RF_CONDITIONS_WITH_SPECIFIC_REASON",
    13: "UNABLE_TO_TRIAGE"
}

ACTIONS = {
    1: "CHECK_BLUETOOTH",
    2: "CHECK_HEADSET",
    3: "SWITCH_FROM_WIFI_PREFERRED_TO_CELLULAR_PREFERRED",
    4: "SWITCH_FROM_CELLULAR_PREFERRED_TO_WIFI_PREFERRED",
    5: "ENABLE_ADVANCED_4G_CALLING",
    6: "DISABLE_ADVANCED_4G_CALLING",
    7: "TOGGLE_AIRPLANE_MODE_TWICE",
    8: "REBOOT_THE_PHONE",
    9: "ENABLE_WIFI_CALLING",
    10: "DISABLE_WIFI_CALLING",
    11: "DISABLE_AIRPLANE_MODE",
    12: "NONE"
}

IGNORED_CALL_DROP_REASONS = ["Radio Link Lost", "Media Timeout"]

CALL_DATA_LOGS = ("/data/data/com.google.android.connectivitymonitor/databases"
                  "/call_data_logs.db")


class TelLiveConnectivityMonitorBaseTest(TelephonyBaseTest):
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
        ## Work around for WFC not working issue on 2018 devices
        if "Permissive" not in self.dut.adb.shell("su root getenforce"):
            self.dut.adb.shell("su root setenforce 0")

    def on_fail(self, test_name, begin_time):
        self.dut.log.info("Pulling %s", CALL_DATA_LOGS)
        log_path = os.path.join(self.dut.log_path, test_name,
                                "CallDataLogs_%s" % self.dut.serial)
        utils.create_dir(log_path)
        self.dut.pull_files([CALL_DATA_LOGS], log_path)

        self._take_bug_report(test_name, begin_time)

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

    def enable_volte(self):
        if CAPABILITY_VOLTE not in self.dut_capabilities:
            raise signals.TestSkip("VoLTE is not supported, abort test.")
        toggle_volte(self.log, self.dut, True)

    def enable_wfc(self):
        if CAPABILITY_WFC not in self.dut_capabilities:
            raise signals.TestSkip("WFC is not supported, abort test.")
        toggle_wfc(self.log, self.dut, True)

    def disable_volte(self):
        if CAPABILITY_VOLTE not in self.dut_capabilities:
            raise signals.TestSkip("VoLTE is not supported, abort test.")
        toggle_volte(self.log, self.dut, False)

    def disable_wfc(self):
        if CAPABILITY_WFC not in self.dut_capabilities:
            raise signals.TestSkip("WFC is not supported, abort test.")
        toggle_wfc(self.log, self.dut, False)

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
        if not phone_setup_iwlan(self.log, self.dut, True,
                                 self.dut_wfc_modes[0], self.wifi_network_ssid,
                                 self.wifi_network_pass):
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
        self.dut.log.info("Phone CSFB is enabled successfully.")
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

    def call_setup_and_connectivity_monitor_checking(self,
                                                     setup=None,
                                                     trigger=None,
                                                     pre_trigger=None,
                                                     expected_drop_reason=None,
                                                     expected_trouble=None,
                                                     expected_action=None):

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
                expected_drop_reason = None
        else:
            if not call_setup_teardown(
                    self.log,
                    self.dut,
                    self.ad_reference,
                    ad_hangup=None,
                    verify_caller_func=call_verification_function,
                    wait_time_in_call=10):
                self.log.error("Call setup failed")
                expected_drop_reason = None

        if self.dut.droid.telecomIsInCall():
            self.dut.log.info("Telecom is in call")
            # Trigger in-call event to drop the call
            if pre_trigger:
                if pre_trigger == "toggle_wifi":
                    wifi_toggle_state(self.log, self.dut, None)
                    time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)
                elif getattr(self, pre_trigger, None):
                    pre_trigger_func = getattr(self, pre_trigger)
                    pre_trigger_func()
                    time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)
                self.dut.log.info(
                    "Voice in RAT %s",
                    self.dut.droid.telephonyGetCurrentVoiceNetworkType())
            if self.dut.droid.telecomIsInCall():
                self.dut.log.info("Telecom is in call")
                if trigger == "modem_crash":
                    self.trigger_modem_crash()
                elif trigger == "toggling_apm":
                    self.trigger_toggling_apm()
                elif trigger == "drop_reason_override":
                    hangup_call(self.log, self.ad_reference)
                    time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)
                elif trigger and getattr(self, trigger, None):
                    trigger_func = getattr(self, trigger)
                    trigger_func()
                    time.sleep(MAX_WAIT_TIME_FOR_STATE_CHANGE)
        else:
            self.dut.log.info("Not in call")

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
                    self.dut.log.info(
                        "call_statistics call_type_with_most_failures "
                        "is %s, not %s", most_failure_call_type, desc)
                else:
                    self.dut.log.info(
                        "call_statistics call_type_with_most_failures is %s",
                        most_failure_call_type)
                dropped = call_data_summary_after.get("%s_dropped" % desc, 0)
                drop_percentage = call_data_summary_after.get(
                    "%s_dropped_percentage" % desc, 0)
                self.dut.log.info("%s_dropped = %s, percentage = %s", desc,
                                  dropped, drop_percentage)
                if expected_trouble and expected_trouble != diagnosis:
                    self.dut.log.error("diagnoisis = %s, expecting %s",
                                       diagnosis, expected_trouble)
                if expected_action and expected_action != actions:
                    self.dut.log.error("actions = %s, expecting %s", actions,
                                       expected_action)
                    result = False
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
                if expected_drop_reason and drop_reason != expected_drop_reason:
                    self.dut.log.error("%s is: %s, expecting %s", reason_key,
                                       drop_reason, expected_drop_reason)
                    result = False
                else:
                    self.dut.log.info("%s is: %s", reason_key, drop_reason)
            else:
                self.dut.log.error("%s is not provided in summary report",
                                   reason_key)
                result = False

        if not trigger or trigger == "toggling_apm" or "Call Drop: %s" % (
                expected_drop_reason
        ) in bugreport_database_before or expected_drop_reason in IGNORED_CALL_DROP_REASONS:
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

    def call_drop_test(self,
                       setup=None,
                       count=CONSECUTIVE_CALL_FAILS,
                       pre_trigger=None,
                       trigger=None,
                       expected_trouble=None,
                       expected_action=None):
        result = True
        if not trigger:
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
                    setup=setup,
                    trigger=trigger,
                    pre_trigger=pre_trigger,
                    expected_drop_reason=drop_reason,
                    expected_trouble=expected_trouble,
                    expected_action=expected_action):
                self._ad_take_bugreport(self.dut, "%s_%s_iter_%s_failure" %
                                        (self.test_name, trigger,
                                         iter + 1), self.begin_time)
                result = False
        return result

    def call_drop_triggered_suggestion_test(self,
                                            setup=None,
                                            pre_trigger=None,
                                            expected_trouble=None,
                                            expected_action=None):
        result = True
        call_summary = self.parsing_call_summary()
        diagnostics = self.parsing_diagnostics()
        diagnosis = diagnostics.get("diagnosis")
        actions = diagnostics.get("actions")
        self.dut.log.info("Expected trouble = %s, action = %s",
                          expected_trouble, expected_action)
        if expected_trouble and diagnosis == expected_trouble:
            self.dut.log.info("Diagnosis is the expected %s", trouble)
            if expected_action and expected_action != actions:
                self.dut.log.error("Action is %s, expecting %s", actions,
                                   expected_action)
                result = False
            if setup in ("wfc_apm", "wfc_non_apm"):
                desc = "VOWIFI"
            elif setup == "volte":
                desc = "VOLTE"
            elif setup in ("csfb", "3g", "2g"):
                desc = "CS"
            drops = call_summary.get("%s_dropped" % desc, 0)
            drop_percentage = call_summary.get("%s_dropped_percentage" % desc,
                                               0)
            if drops < CONSECUTIVE_CALL_FAILS or drop_percentage < 25:
                self.dut.log.error(
                    "Should NOT get %s for %s %s_dropped and %s %s_dropped_percentage",
                    trouble, drops, desc, drop_percentage, desc)
                return False
            else:
                return result
        else:
            self.dut.log.info("Generate %s consecutive call drops",
                              CONSECUTIVE_CALL_FAILS)
            return self.call_drop_test(
                setup=setup,
                count=CONSECUTIVE_CALL_FAILS,
                pre_trigger=pre_trigger,
                expected_trouble=expected_trouble,
                expected_action=expected_action)

    def healthy_call_test(self,
                          setup=None,
                          count=1,
                          pre_trigger=None,
                          expected_trouble=None,
                          expected_action=None):
        if self.dut.model not in ("marlin", "sailfish", "walleye", "taimen"):
            self.set_drop_reason_override(override_code=25)
        result = True
        for iter in range(count):
            if not self.call_setup_and_connectivity_monitor_checking(
                    setup=setup,
                    trigger=None,
                    pre_trigger=pre_trigger,
                    expected_trouble=expected_trouble,
                    expected_action=expected_action):
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
        ## Work around for WFC not working issue on 2018 devices
        if "Permissive" not in self.dut.adb.shell("su root getenforce"):
            self.dut.adb.shell("su root setenforce 0")
        if not func(): return False
        return self.call_drop_triggered_suggestion_test(setup=setup)

    def call_drop_test_after_reboot(self, setup=None):
        func = getattr(self, "setup_%s" % setup)
        if not func(): return False
        self.call_drop_test(setup=setup, count=CONSECUTIVE_CALL_FAILS)
        self.healthy_call_test(setup=setup, count=1)
        reboot_device(self.dut)
        return self.call_drop_triggered_suggestion_test(setup=setup)
