#!/usr/bin/env python3.4
#
#   Copyright 2017 - Google
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
    Test Script for Telephony Stress Call Test
"""

import collections
import random
import time
from acts.asserts import explicit_pass
from acts.asserts import fail
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_ONLY
from acts.test_utils.tel.tel_defines import NETWORK_MODE_WCDMA_ONLY
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GLOBAL
from acts.test_utils.tel.tel_defines import NETWORK_MODE_CDMA
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GSM_ONLY
from acts.test_utils.tel.tel_defines import NETWORK_MODE_TDSCDMA_GSM_WCDMA
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_CDMA_EVDO_GSM_WCDMA
from acts.test_utils.tel.tel_defines import WAIT_TIME_AFTER_MODE_CHANGE
from acts.test_utils.tel.tel_test_utils import active_file_download_test
from acts.test_utils.tel.tel_test_utils import is_phone_in_call
from acts.test_utils.tel.tel_test_utils import call_setup_teardown
from acts.test_utils.tel.tel_test_utils import ensure_phone_default_state
from acts.test_utils.tel.tel_test_utils import ensure_phone_subscription
from acts.test_utils.tel.tel_test_utils import ensure_phones_idle
from acts.test_utils.tel.tel_test_utils import ensure_wifi_connected
from acts.test_utils.tel.tel_test_utils import hangup_call
from acts.test_utils.tel.tel_test_utils import run_multithread_func
from acts.test_utils.tel.tel_test_utils import set_wfc_mode
from acts.test_utils.tel.tel_test_utils import sms_send_receive_verify
from acts.test_utils.tel.tel_test_utils import start_adb_tcpdump
from acts.test_utils.tel.tel_test_utils import stop_adb_tcpdump
from acts.test_utils.tel.tel_test_utils import start_qxdm_loggers
from acts.test_utils.tel.tel_test_utils import mms_send_receive_verify
from acts.test_utils.tel.tel_test_utils import verify_incall_state
from acts.test_utils.tel.tel_test_utils import set_preferred_network_mode_pref
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_3g
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_2g
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_csfb
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_iwlan
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_volte
from acts.test_utils.tel.tel_voice_utils import phone_setup_csfb
from acts.test_utils.tel.tel_voice_utils import phone_setup_iwlan
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_3g
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_2g
from acts.test_utils.tel.tel_voice_utils import phone_setup_volte
from acts.test_utils.tel.tel_voice_utils import phone_idle_iwlan
from acts.test_utils.tel.tel_voice_utils import get_current_voice_rat
from acts.logger import epoch_to_log_line_timestamp
from acts.utils import get_current_epoch_time
from acts.utils import rand_ascii_str

import socket
from acts.controllers.sl4a_client import Sl4aProtocolError

IGNORE_EXCEPTIONS = (BrokenPipeError, Sl4aProtocolError)
EXCEPTION_TOLERANCE = 20


class TelLiveStressTest(TelephonyBaseTest):
    def setup_class(self):
        super(TelLiveStressTest, self).setup_class()
        self.dut = self.android_devices[0]
        self.helper = self.android_devices[1]
        self.android_devices = self.android_devices[:2]
        self.user_params["telephony_auto_rerun"] = False
        self.wifi_network_ssid = self.user_params.get(
            "wifi_network_ssid") or self.user_params.get(
                "wifi_network_ssid_2g")
        self.wifi_network_pass = self.user_params.get(
            "wifi_network_pass") or self.user_params.get(
                "wifi_network_pass_2g")
        self.phone_call_iteration = int(
            self.user_params.get("phone_call_iteration", 500))
        self.max_phone_call_duration = int(
            self.user_params.get("max_phone_call_duration", 600))
        self.min_sleep_time = int(self.user_params.get("min_sleep_time", 10))
        self.max_sleep_time = int(self.user_params.get("max_sleep_time", 120))
        self.max_run_time = int(self.user_params.get("max_run_time", 14400))
        self.max_sms_length = int(self.user_params.get("max_sms_length", 1000))
        self.max_mms_length = int(self.user_params.get("max_mms_length", 160))
        self.min_sms_length = int(self.user_params.get("min_sms_length", 1))
        self.min_mms_length = int(self.user_params.get("min_mms_length", 1))
        self.min_phone_call_duration = int(
            self.user_params.get("min_phone_call_duration", 10))
        self.crash_check_interval = int(
            self.user_params.get("crash_check_interval", 300))

        return True

    def on_fail(self, test_name, begin_time):
        pass

    def _setup_wfc(self):
        for ad in self.android_devices:
            if not ensure_wifi_connected(
                    self.log,
                    ad,
                    self.wifi_network_ssid,
                    self.wifi_network_pass,
                    retries=3):
                ad.log.error("Phone Wifi connection fails.")
                return False
            ad.log.info("Phone WIFI is connected successfully.")
            if not set_wfc_mode(self.log, ad, WFC_MODE_WIFI_PREFERRED):
                ad.log.error("Phone failed to enable Wifi-Calling.")
                return False
            ad.log.info("Phone is set in Wifi-Calling successfully.")
            if not phone_idle_iwlan(self.log, ad):
                ad.log.error("Phone is not in WFC enabled state.")
                return False
            ad.log.info("Phone is in WFC enabled state.")
        return True

    def _setup_lte_volte_enabled(self):
        for ad in self.android_devices:
            if not phone_setup_volte(self.log, ad):
                ad.log.error("Phone failed to enable VoLTE.")
                return False
            ad.log.info("Phone VOLTE is enabled successfully.")
        return True

    def _setup_lte_volte_disabled(self):
        for ad in self.android_devices:
            if not phone_setup_csfb(self.log, ad):
                ad.log.error("Phone failed to setup CSFB.")
                return False
            ad.log.info("Phone VOLTE is disabled successfully.")
        return True

    def _setup_3g(self):
        for ad in self.android_devices:
            if not phone_setup_voice_3g(self.log, ad):
                ad.log.error("Phone failed to setup 3g.")
                return False
            ad.log.info("Phone RAT 3G is enabled successfully.")
        return True

    def _setup_2g(self):
        for ad in self.android_devices:
            if not phone_setup_voice_2g(self.log, ad):
                ad.log.error("Phone failed to setup 2g.")
                return False
            ad.log.info("RAT 2G is enabled successfully.")
        return True

    def _send_message(self, ads):
        selection = random.randrange(0, 2)
        message_type_map = {0: "SMS", 1: "MMS"}
        max_length_map = {0: self.max_sms_length, 1: self.max_mms_length}
        min_length_map = {0: self.min_sms_length, 1: self.min_mms_length}
        length = random.randrange(min_length_map[selection],
                                  max_length_map[selection] + 1)
        message_func_map = {
            0: sms_send_receive_verify,
            1: mms_send_receive_verify
        }
        message_type = message_type_map[selection]
        self.result_info["Total %s" % message_type] += 1
        the_number = self.result_info["Total %s" % message_type]
        begin_time = get_current_epoch_time()
        start_qxdm_loggers(self.log, self.android_devices)
        log_msg = "The %s-th %s test: of length %s from %s to %s" % (
            the_number, message_type, length, ads[0].serial, ads[1].serial)
        self.log.info(log_msg)
        for ad in ads:
            try:
                for i in range(3):
                    try:
                        ad.droid.logI(log_msg)
                        break
                    except Exception:
                        if i == 2:
                            raise
                        else:
                            sleep(5)
            except Exception:
                ad.log.info("SL4A error: %s, restart SL4A service", e)
                raise
        text = "%s: " % log_msg
        text_length = len(text)
        if length < text_length:
            text = text[:length]
        else:
            text += rand_ascii_str(length - text_length)
        message_content_map = {0: [text], 1: [(log_msg, text, None)]}
        incall_non_ims = False
        for ad in ads:
            if ad.droid.telecomIsInCall() and (
                    not ad.droid.telephonyIsImsRegistered()):
                incall_non_ims = True
                break

        if not message_func_map[selection](self.log, ads[0], ads[1],
                                           message_content_map[selection]):
            if message_type == "SMS":
                self.log.error("%s fails", log_msg)
                self.result_info["%s failure" % message_type] += 1
                self._take_bug_report("%s_%s_No_%s_failure" %
                                      (self.test_name, message_type,
                                       the_number), begin_time)
            else:
                if incall_non_ims:
                    self.log.info(
                        "Device not in IMS, MMS in call is not support")
                    return True
                else:
                    self.log.error("%s fails", log_msg)
                    self.result_info["MMS failure"] += 1
                    if self.result_info["MMS failure"] == 1:
                        self._take_bug_report("%s_%s_No_%s_failure" %
                                              (self.test_name, message_type,
                                               the_number), begin_time)
            return False
        else:
            self.log.info("%s succeed", log_msg)
            return True

    def _make_phone_call(self, ads, call_verification_func=None):
        self.result_info["Total Calls"] += 1
        the_number = self.result_info["Total Calls"]
        log_msg = "The %s-th phone call test from %s to %s" % (the_number,
                                                               ads[0].serial,
                                                               ads[1].serial)
        self.log.info(log_msg)
        for ad in ads:
            try:
                for i in range(3):
                    try:
                        ad.droid.logI(log_msg)
                        break
                    except Exception:
                        if i == 2:
                            raise
                        else:
                            sleep(5)
            except Exception:
                ad.log.info("SL4A error: %s, restart SL4A service", e)
                try:
                    self.terminate_all_sessions()
                except Exception as e:
                    ad.log.warning("Fail to terminate SL4A session: %s", e)
                try:
                    droid, ed = self.get_droid()
                    ed.start()
                except:
                    self.log.exception("Failed to start sl4a!")
                    raise
        begin_time = get_current_epoch_time()
        start_qxdm_loggers(self.log, self.android_devices)
        if not call_setup_teardown(
                self.log, ads[0], ads[1], ad_hangup=None, wait_time_in_call=0):
            self.log.error("%s: Setup Call failed.", log_msg)
            self.result_info["Call Setup Failure"] += 1
            self._take_bug_report("%s_call_No_%s_setup_failure" %
                                  (self.test_name, the_number), begin_time)
            return False
        duration = random.randrange(self.min_phone_call_duration,
                                    self.max_phone_call_duration)
        elapsed_time = 0
        check_interval = 5
        while (elapsed_time < duration):
            check_interval = min(check_interval, duration - elapsed_time)
            time.sleep(check_interval)
            elapsed_time += check_interval
            time_message = "at <%s>/<%s> second." % (elapsed_time, duration)
            for ad in ads:
                if not call_verification_func(self.log, ad):
                    ad.log.error("Call is NOT in correct %s state at %s",
                                 call_verification_func.__name__, time_message)
                    self.result_info["Call Maintenance Failure"] += 1
                    self._take_bug_report("%s_call_No_%s_maintenance_failure" %
                                          (self.test_name,
                                           the_number), begin_time)
                    return False
        if not hangup_call(self.log, ads[0]):
            time.sleep(10)
            for ad in ads:
                if ad.droid.telecomIsInCall():
                    ad.log.error("Still in call after hungup")
                    self.result_info["Call Teardown Failure"] += 1
                    self._take_bug_report("%s_call_No_%s_teardown_failure" %
                                          (self.test_name,
                                           the_number), begin_time)
                    return False
        self.log.info("Call setup and teardown succeed.")
        return True

    def _prefnetwork_mode_change(self, sub_id):
        # ModePref change to non-LTE
        begin_time = get_current_epoch_time()
        network_preference_list = [
            NETWORK_MODE_TDSCDMA_GSM_WCDMA, NETWORK_MODE_WCDMA_ONLY,
            NETWORK_MODE_GLOBAL, NETWORK_MODE_CDMA, NETWORK_MODE_GSM_ONLY
        ]
        network_preference = random.choice(network_preference_list)
        set_preferred_network_mode_pref(self.log, self.dut, sub_id,
                                        network_preference)
        time.sleep(WAIT_TIME_AFTER_MODE_CHANGE)
        self.dut.log.info("Current Voice RAT is %s",
                          get_current_voice_rat(self.log, self.dut))

        # ModePref change back to with LTE
        set_preferred_network_mode_pref(self.log, self.dut, sub_id,
                                        NETWORK_MODE_LTE_CDMA_EVDO_GSM_WCDMA)
        time.sleep(WAIT_TIME_AFTER_MODE_CHANGE)
        rat = get_current_voice_rat(self.log, self.dut)
        self.dut.log.info("Current Voice RAT is %s", rat)
        if rat != "LTE":
            self.result_info["RAT change failure"] += 1
            self._take_bug_report("%s_rat_change_failure" % self.test_name,
                                  begin_time)
            return False
        return True

    def crash_check_test(self):
        failure = 0
        while time.time() < self.finishing_time:
            self.log.info(dict(self.result_info))
            try:
                begin_time = get_current_epoch_time()
                time.sleep(self.crash_check_interval)
                for ad in self.android_devices():
                    crash_report = ad.check_crash_report(
                        "checking_crash", begin_time, log_crash_report=True)
                    if crash_report:
                        ad.log.error("Find new crash reports %s", crash_report)
                        failure += 1
                        self.result_info["Crashes"] += 1
            except IGNORE_EXCEPTIONS as e:
                self.log.error("Exception error %s", str(e))
                self.result_info["Exception Errors"] += 1
                if self.result_info["Exception Errors"] > EXCEPTION_TOLERANCE:
                    raise
            except Exception:
                raise
            self.log.info("Crashes found: %s", failure)
        if failure:
            return False
        else:
            return True

    def call_test(self, call_verification_func=None):
        while time.time() < self.finishing_time:
            try:
                ads = self.android_devices[:2]
                random.shuffle(ads)
                self._make_phone_call(ads, call_verification_func)
                time.sleep(
                    random.randrange(self.min_sleep_time, self.max_sleep_time))
            except IGNORE_EXCEPTIONS as e:
                self.log.error("Exception error %s", str(e))
                self.result_info["Exception Errors"] += 1
                if self.result_info["Exception Errors"] > EXCEPTION_TOLERANCE:
                    raise
            except Exception as e:
                raise
            self.log.info("%s", dict(self.result_info))
        if any([
                self.result_info["Call Setup Failure"],
                self.result_info["Call Maintenance Failure"],
                self.result_info["Call Teardown Failure"]
        ]):
            return False
        else:
            return True

    def volte_modechange_volte_test(self):
        sub_id = self.dut.droid.subscriptionGetDefaultSubId()
        while time.time() < self.finishing_time:
            try:
                ads = self.android_devices[:2]
                self._make_phone_call(
                    ads, call_verification_func=is_phone_in_call_volte)
                self._prefnetwork_mode_change(sub_id)
            except IGNORE_EXCEPTIONS as e:
                self.log.error("Exception error %s", str(e))
                self.result_info["Exception Errors"] += 1
                if self.result_info["Exception Errors"] > EXCEPTION_TOLERANCE:
                    raise
            except Exception:
                raise
            self.log.info(dict(self.result_info))
        if self.result_info["Call Failure"] or self.result_info["RAT change failure"]:
            return False
        else:
            return True

    def message_test(self):
        while time.time() < self.finishing_time:
            try:
                ads = self.android_devices[:2]
                random.shuffle(ads)
                self._send_message(ads)
                time.sleep(
                    random.randrange(self.min_sleep_time, self.max_sleep_time))
            except IGNORE_EXCEPTIONS as e:
                self.log.error("Exception error %s", str(e))
                self.result_info["Exception Errors"] += 1
                if self.result_info["Exception Errors"] > EXCEPTION_TOLERANCE:
                    raise
            except Exception as e:
                raise
            self.log.info(dict(self.result_info))
        if self.result_info["SMS failure"] or (
                self.result_info["MMS failure"] / self.result_info["Total MMS"]
                > 0.3):
            return False
        else:
            return True

    def data_test(self):
        #file_names = ["5MB", "10MB", "20MB", "50MB", "200MB", "512MB", "1GB"]
        file_names = ["5MB", "10MB", "20MB", "50MB", "200MB", "512MB"]
        while time.time() < self.finishing_time:
            begin_time = get_current_epoch_time()
            tcpdump_pid = None
            try:
                self.dut.log.info(dict(self.result_info))
                self.result_info["Total file download"] += 1
                selection = random.randrange(0, len(file_names))
                file_name = file_names[selection]
                start_qxdm_loggers(self.log, self.android_devices)
                if self.result_info["File download failure"] < 1:
                    (tcpdump_pid, tcpdump_file) = start_adb_tcpdump(
                        self.dut,
                        "%s_file_download" % self.test_name,
                        mask="all")
                if not active_file_download_test(self.log, self.dut,
                                                 file_name):
                    self.result_info["File download failure"] += 1
                    if self.result_info["File download failure"] == 1:
                        if tcpdump_pid is not None:
                            stop_adb_tcpdump(self.dut, tcpdump_pid,
                                             tcpdump_file, True)
                        self._take_bug_report(
                            "%s_file_download_failure" % self.test_name,
                            begin_time)
                elif tcpdump_pid is not None:
                    stop_adb_tcpdump(self.dut, tcpdump_pid, tcpdump_file,
                                     False)
                time.sleep(
                    random.randrange(self.min_sleep_time, self.max_sleep_time))
            except IGNORE_EXCEPTIONS as e:
                self.log.error("Exception error %s", str(e))
                self.result_info["Exception Errors"] += 1
                if self.result_info["Exception Errors"] > EXCEPTION_TOLERANCE:
                    raise "Too many %s errors" % IGNORE_EXCEPTIONS
            except Exception as e:
                self.log.error(e)
                raise
            self.log.info("%s", dict(self.result_info))
        if self.result_info["File download failure"] / self.result_info["Total file download"] > 0.1:
            return False
        else:
            return True

    def parallel_tests(self, setup_func=None, call_verification_func=None):
        if setup_func and not setup_func():
            msg = "Test setup %s failed" % setup_func.__name__
            self.log.error(msg)
            fail(msg)
        if not call_verification_func:
            call_verification_func = is_phone_in_call
        self.result_info = collections.defaultdict(int)
        self.finishing_time = time.time() + self.max_run_time
        results = run_multithread_func(
            self.log, [(self.call_test, [call_verification_func]),
                       (self.message_test, []), (self.data_test, []),
                       (self.crash_check_test, [])])
        result_message = "Total Calls: %s" % self.result_info["Total Calls"]
        for count in ("Call Setup Failure", "Call Maintenance Failure",
                      "Call Teardown Failure", "Total SMS", "SMS failure",
                      "Total MMS", "MMS failure", "Total file download",
                      "File download failure"):
            result_message = "%s, %s: %s" % (result_message, count,
                                             self.result_info[count])
        self.log.info(result_message)
        if all(results):
            explicit_pass(result_message)
        else:
            fail(result_message)

    def parallel_volte_tests(self, setup_func=None):
        if setup_func and not setup_func():
            self.log.error("Test setup %s failed", setup_func.__name__)
            return False
        self.result_info = collections.defaultdict(int)
        self.finishing_time = time.time() + self.max_run_time
        results = run_multithread_func(self.log,
                                       [(self.volte_modechange_volte_test, []),
                                        (self.crash_check_test, [])])
        result_message = "Total Calls: %s" % self.result_info["Total Calls"]
        for count in ("Call Setup Failure", "Call Maintenance Failure",
                      "Call Teardown Failure", "RAT change failure"):
            result_message = "%s, %s: %s" % (result_message, count,
                                             self.result_info[count])
        if all(results):
            explicit_pass(result_message)
        else:
            fail(result_message)

    """ Tests Begin """

    @test_tracker_info(uuid="d035e5b9-476a-4e3d-b4e9-6fd86c51a68d")
    @TelephonyBaseTest.tel_test_wrap
    def test_default_parallel_stress(self):
        """ Default state stress test"""
        return self.parallel_tests()

    @test_tracker_info(uuid="c21e1f17-3282-4f0b-b527-19f048798098")
    @TelephonyBaseTest.tel_test_wrap
    def test_lte_volte_parallel_stress(self):
        """ VoLTE on stress test"""
        return self.parallel_tests(
            setup_func=self._setup_lte_volte_enabled,
            call_verification_func=is_phone_in_call_volte)

    @test_tracker_info(uuid="a317c23a-41e0-4ef8-af67-661451cfefcf")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_parallel_stress(self):
        """ LTE non-VoLTE stress test"""
        return self.parallel_tests(
            setup_func=self._setup_lte_volte_disabled,
            call_verification_func=is_phone_in_call_csfb)

    @test_tracker_info(uuid="fdb791bf-c414-4333-9fa3-cc18c9b3b234")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_parallel_stress(self):
        """ Wifi calling on stress test"""
        return self.parallel_tests(
            setup_func=self._setup_wfc,
            call_verification_func=is_phone_in_call_iwlan)

    @test_tracker_info(uuid="4566eef6-55de-4ac8-87ee-58f2ef41a3e8")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_parallel_stress(self):
        """ 3G stress test"""
        return self.parallel_tests(
            setup_func=self._setup_3g,
            call_verification_func=is_phone_in_call_3g)

    @test_tracker_info(uuid="f34f1a31-3948-4675-8698-372a83b8088d")
    @TelephonyBaseTest.tel_test_wrap
    def test_call_2g_parallel_stress(self):
        """ 2G call stress test"""
        return self.parallel_tests(
            setup_func=self._setup_2g,
            call_verification_func=is_phone_in_call_2g)

    @test_tracker_info(uuid="af580fca-fea6-4ca5-b981-b8c710302d37")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_modeprefchange_parallel_stress(self):
        """ VoLTE Mode Pref call stress test"""
        return self.parallel_volte_tests(
            setup_func=self._setup_lte_volte_enabled)

    """ Tests End """
