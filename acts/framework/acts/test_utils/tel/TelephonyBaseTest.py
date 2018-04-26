#!/usr/bin/env python3
#
#   Copyright 2016 - Google
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
    Base Class for Defining Common Telephony Test Functionality
"""

import logging
import os
import re
import shutil

from acts import asserts
from acts import logger as acts_logger
from acts import signals
from acts.base_test import BaseTestClass
from acts.controllers.android_device import DEFAULT_QXDM_LOG_PATH
from acts.keys import Config
from acts import records
from acts import utils

from acts.test_utils.tel.tel_subscription_utils import \
    initial_set_up_for_subid_infomation
from acts.test_utils.tel.tel_test_utils import enable_radio_log_on
from acts.test_utils.tel.tel_test_utils import ensure_phone_default_state
from acts.test_utils.tel.tel_test_utils import ensure_phone_idle
from acts.test_utils.tel.tel_test_utils import extract_test_log
from acts.test_utils.tel.tel_test_utils import get_operator_name
from acts.test_utils.tel.tel_test_utils import get_screen_shot_log
from acts.test_utils.tel.tel_test_utils import get_sim_state
from acts.test_utils.tel.tel_test_utils import get_tcpdump_log
from acts.test_utils.tel.tel_test_utils import multithread_func
from acts.test_utils.tel.tel_test_utils import print_radio_info
from acts.test_utils.tel.tel_test_utils import reboot_device
from acts.test_utils.tel.tel_test_utils import run_multithread_func
from acts.test_utils.tel.tel_test_utils import setup_droid_properties
from acts.test_utils.tel.tel_test_utils import set_phone_screen_on
from acts.test_utils.tel.tel_test_utils import set_phone_silent_mode
from acts.test_utils.tel.tel_test_utils import set_qxdm_logger_command
from acts.test_utils.tel.tel_test_utils import start_qxdm_logger
from acts.test_utils.tel.tel_test_utils import start_qxdm_loggers
from acts.test_utils.tel.tel_test_utils import start_tcpdumps
from acts.test_utils.tel.tel_test_utils import stop_qxdm_logger
from acts.test_utils.tel.tel_test_utils import stop_tcpdumps
from acts.test_utils.tel.tel_test_utils import unlock_sim
from acts.test_utils.tel.tel_test_utils import wait_for_sim_ready_by_adb
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING
from acts.test_utils.tel.tel_defines import SIM_STATE_ABSENT
from acts.test_utils.tel.tel_defines import SIM_STATE_UNKNOWN
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_ENABLED
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_DISABLED


class TelephonyBaseTest(BaseTestClass):
    def __init__(self, controllers):

        BaseTestClass.__init__(self, controllers)
        self.wifi_network_ssid = self.user_params.get(
            "wifi_network_ssid") or self.user_params.get(
                "wifi_network_ssid_2g") or self.user_params.get(
                    "wifi_network_ssid_5g")
        self.wifi_network_pass = self.user_params.get(
            "wifi_network_pass") or self.user_params.get(
                "wifi_network_pass_2g") or self.user_params.get(
                    "wifi_network_ssid_5g")

        self.log_path = getattr(logging, "log_path", None)
        self.qxdm_log = self.user_params.get("qxdm_log", True)
        self.enable_radio_log_on = self.user_params.get(
            "enable_radio_log_on", True)
        qxdm_log_mask_cfg = self.user_params.get("qxdm_log_mask_cfg", None)
        if isinstance(qxdm_log_mask_cfg, list):
            qxdm_log_mask_cfg = qxdm_log_mask_cfg[0]
        if qxdm_log_mask_cfg and "dev/null" in qxdm_log_mask_cfg:
            qxdm_log_mask_cfg = None
        tasks = [(self._init_device, (ad, qxdm_log_mask_cfg))
                 for ad in self.android_devices]
        multithread_func(self.log, tasks)
        self.skip_reset_between_cases = self.user_params.get(
            "skip_reset_between_cases", True)
        self.log_path = getattr(logging, "log_path", None)

    # Use for logging in the test cases to facilitate
    # faster log lookup and reduce ambiguity in logging.
    @staticmethod
    def tel_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            test_id = "%s:%s:%s" % (self.__class__.__name__, self.test_name,
                                    self.log_begin_time.replace(' ', '-'))
            self.test_id = test_id
            self.result_detail = ""
            tries = int(self.user_params.get("telephony_auto_rerun", 1))
            for ad in self.android_devices:
                ad.log_path = self.log_path
            for i in range(tries + 1):
                result = True
                if i > 0:
                    log_string = "[Test Case] RERUN %s" % self.test_name
                    self.log.info(log_string)
                    self._teardown_test(self.test_name)
                    self._setup_test(self.test_name)
                try:
                    result = fn(self, *args, **kwargs)
                except signals.TestFailure:
                    if i < tries + 1:
                        continue
                    if self.result_detail:
                        signal.details = self.result_detail
                    raise
                except signals.TestSignal:
                    if self.result_detail:
                        signal.details = self.result_detail
                    raise
                except Exception as e:
                    self.log.exception(e)
                    asserts.fail(self.result_detail)
                if result is False:
                    if i < tries + 1:
                        continue
                else:
                    break
            if self.user_params.get("check_crash", True):
                new_crash = ad.check_crash_report(self.test_name,
                                                  self.begin_time, True)
                if new_crash:
                    msg = "Find new crash reports %s" % new_crash
                    ad.log.error(msg)
                    self.result_detail = "%s %s %s" % (self.result_detail,
                                                       ad.serial, msg)
                    result = False
            if result is not False:
                asserts.explicit_pass(self.result_detail)
            else:
                asserts.fail(self.result_detail)

        return _safe_wrap_test_case

    def setup_class(self):
        sim_conf_file = self.user_params.get("sim_conf_file")
        if not sim_conf_file:
            self.log.info("\"sim_conf_file\" is not provided test bed config!")
        else:
            if isinstance(sim_conf_file, list):
                sim_conf_file = sim_conf_file[0]
            # If the sim_conf_file is not a full path, attempt to find it
            # relative to the config file.
            if not os.path.isfile(sim_conf_file):
                sim_conf_file = os.path.join(
                    self.user_params[Config.key_config_path], sim_conf_file)
                if not os.path.isfile(sim_conf_file):
                    self.log.error("Unable to load user config %s ",
                                   sim_conf_file)

        tasks = [(self._setup_device, (ad, sim_conf_file))
                 for ad in self.android_devices]
        return multithread_func(self.log, tasks)

    def _init_device(self, ad, qxdm_log_mask_cfg=None):
        if self.enable_radio_log_on:
            enable_radio_log_on(ad)
        ad.log_path = self.log_path
        print_radio_info(ad)
        unlock_sim(ad)
        ad.wakeup_screen()
        ad.adb.shell("input keyevent 82")
        ad.qxdm_log = getattr(ad, "qxdm_log", self.qxdm_log)
        stop_qxdm_logger(ad)
        if ad.qxdm_log:
            qxdm_log_mask = getattr(ad, "qxdm_log_mask", None)
            if qxdm_log_mask_cfg:
                qxdm_mask_path = self.user_params.get("qxdm_log_path",
                                                      DEFAULT_QXDM_LOG_PATH)
                ad.adb.shell("mkdir %s" % qxdm_mask_path)
                ad.log.info("Push %s to %s", qxdm_log_mask_cfg, qxdm_mask_path)
                ad.adb.push("%s %s" % (qxdm_log_mask_cfg, qxdm_mask_path))
                mask_file_name = os.path.split(qxdm_log_mask_cfg)[-1]
                qxdm_log_mask = os.path.join(qxdm_mask_path, mask_file_name)
            set_qxdm_logger_command(ad, mask=qxdm_log_mask)
        start_qxdm_logger(ad, utils.get_current_epoch_time())

    def _setup_device(self, ad, sim_conf_file):
        if not unlock_sim(ad):
            raise signals.TestAbortClass("unable to unlock the SIM")

        if "sdm" in ad.model:
            if ad.adb.getprop("persist.radio.multisim.config") != "ssss":
                ad.adb.shell("setprop persist.radio.multisim.config ssss")
                reboot_device(ad)
                # Workaround for b/77814510
                ad.adb.shell(
                    "rm /data/user_de/0/com.android.providers.telephony"
                    "/databases/telephony.db")
                reboot_device(ad)

        if get_sim_state(ad) in (SIM_STATE_ABSENT, SIM_STATE_UNKNOWN):
            ad.log.info("Device has no or unknown SIM in it")
            ensure_phone_idle(self.log, ad)
        elif self.user_params.get("Attenuator"):
            ad.log.info("Device in chamber room")
            ensure_phone_idle(self.log, ad)
            setup_droid_properties(self.log, ad, sim_conf_file)
        else:
            if not wait_for_sim_ready_by_adb(self.log, ad):
                raise signals.TestAbortClass("unable to load the SIM")
            ensure_phone_default_state(self.log, ad)
            setup_droid_properties(self.log, ad, sim_conf_file)

        # Setup VoWiFi MDN for Verizon. b/33187374
        if get_operator_name(self.log, ad) == "vzw" and ad.is_apk_installed(
                "com.google.android.wfcactivation"):
            ad.log.info("setup VoWiFi MDN per b/33187374")
        ad.adb.shell("setprop dbg.vzw.force_wfc_nv_enabled true")
        ad.adb.shell("am start --ei EXTRA_LAUNCH_CARRIER_APP 0 -n "
                     "\"com.google.android.wfcactivation/"
                     ".VzwEmergencyAddressActivity\"")
        # Sub ID setup
        initial_set_up_for_subid_infomation(self.log, ad)

        # If device is setup already, skip the following setup procedures
        if getattr(ad, "telephony_test_setup", None):
            return True

        if "enable_wifi_verbose_logging" in self.user_params:
            ad.droid.wifiEnableVerboseLogging(WIFI_VERBOSE_LOGGING_ENABLED)

        # Disable Emergency alerts
        # Set chrome browser start with no-first-run verification and
        # disable-fre. Give permission to read from and write to storage.
        for cmd in ("pm disable com.android.cellbroadcastreceiver",
                    "pm grant com.android.chrome "
                    "android.permission.READ_EXTERNAL_STORAGE",
                    "pm grant com.android.chrome "
                    "android.permission.WRITE_EXTERNAL_STORAGE",
                    "rm /data/local/chrome-command-line",
                    "am set-debug-app --persistent com.android.chrome",
                    'echo "chrome --no-default-browser-check --no-first-run '
                    '--disable-fre" > /data/local/tmp/chrome-command-line'):
            ad.adb.shell(cmd)

        # Curl for 2016/7 devices
        if not getattr(ad, "curl_capable", False):
            try:
                out = ad.adb.shell("/data/curl --version")
                if not out or "not found" in out:
                    if int(ad.adb.getprop("ro.product.first_api_level")) >= 25:
                        tel_data = self.user_params.get("tel_data", "tel_data")
                        if isinstance(tel_data, list):
                            tel_data = tel_data[0]
                        curl_file_path = os.path.join(tel_data, "curl")
                        if not os.path.isfile(curl_file_path):
                            curl_file_path = os.path.join(
                                self.user_params[Config.key_config_path],
                                curl_file_path)
                        if os.path.isfile(curl_file_path):
                            ad.log.info("Pushing Curl to /data dir")
                            ad.adb.push("%s /data" % (curl_file_path))
                            ad.adb.shell(
                                "chmod 777 /data/curl", ignore_status=True)
                else:
                    setattr(ad, "curl_capable", True)
            except Exception:
                ad.log.info("Failed to push curl on this device")

        # Ensure that a test class starts from a consistent state that
        # improves chances of valid network selection and facilitates
        # logging.
        try:
            if not set_phone_screen_on(self.log, ad):
                self.log.error("Failed to set phone screen-on time.")
                return False
            if not set_phone_silent_mode(self.log, ad):
                self.log.error("Failed to set phone silent mode.")
                return False
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND, True)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING, True)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND, True)
        except Exception as e:
            self.log.error("Failure with %s", e)
        setattr(ad, "telephony_test_setup", True)
        return True

    def teardown_class(self):
        try:
            for ad in self.android_devices:
                stop_qxdm_logger(ad)
                ad.droid.disableDevicePassword()
                if "enable_wifi_verbose_logging" in self.user_params:
                    ad.droid.wifiEnableVerboseLogging(
                        WIFI_VERBOSE_LOGGING_DISABLED)
            return True
        except Exception as e:
            self.log.error("Failure with %s", e)

    def setup_test(self):
        if "wfc" in self.test_name and not self.user_params.get(
                "qxdm_log_mask_cfg", None):
            for ad in self.android_devices:
                set_qxdm_logger_command(ad, "IMS_DS_CNE_LnX_Golden.cfg")
        if getattr(self, "qxdm_log", True):
            start_qxdm_loggers(self.log, self.android_devices, self.begin_time)
        if getattr(self, "tcpdump_log", False) or "wfc" in self.test_name:
            mask = getattr(self, "tcpdump_mask", "all")
            interface = getattr(self, "tcpdump_interface", "wlan0")
            start_tcpdumps(
                self.android_devices,
                begin_time=self.begin_time,
                interface=interface,
                mask=mask)
        else:
            stop_tcpdumps(self.android_devices)
        for ad in self.android_devices:
            if self.skip_reset_between_cases:
                ensure_phone_idle(self.log, ad)
            else:
                ensure_phone_default_state(self.log, ad)
            for session in ad._sl4a_manager.sessions.values():
                ed = session.get_event_dispatcher()
                ed.clear_all_events()
            output = ad.adb.logcat("-t 1")
            match = re.search(r"\d+-\d+\s\d+:\d+:\d+.\d+", output)
            if match:
                ad.test_log_begin_time = match.group(0)

    def teardown_test(self):
        stop_tcpdumps(self.android_devices)
        if "wfc" in self.test_name and not self.user_params.get(
                "qxdm_log_mask_cfg", None):
            for ad in self.android_devices:
                set_qxdm_logger_command(ad, None)

    def on_fail(self, test_name, begin_time):
        self._take_bug_report(test_name, begin_time)

    def on_blocked(self, test_name, begin_time):
        self.on_fail(test_name, begin_time)

    def _ad_take_extra_logs(self, ad, test_name, begin_time):
        extra_qxdm_logs_in_seconds = self.user_params.get(
            "extra_qxdm_logs_in_seconds", 60 * 3)
        result = True
        if getattr(ad, "qxdm_log", True):
            # Gather qxdm log modified 3 minutes earlier than test start time
            if begin_time:
                qxdm_begin_time = begin_time - 1000 * extra_qxdm_logs_in_seconds
            else:
                qxdm_begin_time = None
            try:
                ad.get_qxdm_logs(test_name, qxdm_begin_time)
            except Exception as e:
                ad.log.error("Failed to get QXDM log for %s with error %s",
                             test_name, e)
                result = False

        # get tcpdump and screen shot log
        get_tcpdump_log(ad, test_name, begin_time)
        get_screen_shot_log(ad, test_name, begin_time)

        try:
            ad.check_crash_report(test_name, begin_time, log_crash_report=True)
        except Exception as e:
            ad.log.error("Failed to check crash report for %s with error %s",
                         test_name, e)
            result = False

        extract_test_log(self.log, ad.adb_logcat_file_path,
                         os.path.join(self.log_path, test_name,
                                      "%s_%s.logcat" % (ad.serial, test_name)),
                         test_name)
        return result

    def _take_bug_report(self, test_name, begin_time):
        if self._skip_bug_report():
            return
        dev_num = getattr(self, "number_of_devices", None) or len(
            self.android_devices)
        tasks = [(self._ad_take_bugreport, (ad, test_name, begin_time))
                 for ad in self.android_devices[:dev_num]]
        tasks.extend([(self._ad_take_extra_logs, (ad, test_name, begin_time))
                      for ad in self.android_devices[:dev_num]])
        run_multithread_func(self.log, tasks)
        for ad in self.android_devices[:dev_num]:
            if getattr(ad, "reboot_to_recover", False):
                reboot_device(ad)
                ad.reboot_to_recover = False
        # Extract test_run_info.txt, test_run_detail.txt
        for file_name in ("test_run_info.txt", "test_run_details.txt"):
            extract_test_log(self.log, os.path.join(self.log_path, file_name),
                             os.path.join(self.log_path, test_name,
                                          "%s_%s" % (test_name, file_name)),
                             "\[Test Case\] %s" % test_name)

        # Zip log folder
        if not self.user_params.get("zip_log", False): return
        src_dir = os.path.join(self.log_path, test_name)
        file_name = "%s_%s" % (src_dir, begin_time)
        self.log.info("Zip folder %s to %s.zip", src_dir, file_name)
        shutil.make_archive(file_name, "zip", src_dir)
        shutil.rmtree(src_dir)

    def _block_all_test_cases(self, tests):
        """Over-write _block_all_test_case in BaseTestClass."""
        for (i, (test_name, test_func)) in enumerate(tests):
            signal = signals.TestBlocked("Failed class setup")
            record = records.TestResultRecord(test_name, self.TAG)
            record.test_begin()
            # mark all test cases as FAIL
            record.test_fail(signal)
            self.results.add_record(record)
            # only gather bug report for the first test case
            if i == 0:
                self.on_fail(test_name, record.begin_time)

    def get_stress_test_number(self):
        """Gets the stress_test_number param from user params.

        Gets the stress_test_number param. If absent, returns default 100.
        """
        return int(self.user_params.get("stress_test_number", 100))
