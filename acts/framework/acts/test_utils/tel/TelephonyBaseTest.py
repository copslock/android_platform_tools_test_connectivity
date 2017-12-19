#!/usr/bin/env python3.4
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

import os
import time
import inspect
import traceback

import acts.controllers.diag_logger

from acts.base_test import BaseTestClass
from acts.keys import Config
from acts.signals import TestSignal
from acts.signals import TestAbortClass
from acts.signals import TestAbortAll
from acts.signals import TestBlocked
from acts import records
from acts import utils

from acts.test_utils.tel.tel_subscription_utils import \
    initial_set_up_for_subid_infomation
from acts.test_utils.tel.tel_test_utils import abort_all_tests
from acts.test_utils.tel.tel_test_utils import is_sim_locked
from acts.test_utils.tel.tel_test_utils import ensure_phones_default_state
from acts.test_utils.tel.tel_test_utils import ensure_phones_idle
from acts.test_utils.tel.tel_test_utils import find_qxdm_logger_mask
from acts.test_utils.tel.tel_test_utils import run_multithread_func
from acts.test_utils.tel.tel_test_utils import print_radio_info
from acts.test_utils.tel.tel_test_utils import refresh_droid_config
from acts.test_utils.tel.tel_test_utils import setup_droid_properties
from acts.test_utils.tel.tel_test_utils import set_phone_screen_on
from acts.test_utils.tel.tel_test_utils import set_phone_silent_mode
from acts.test_utils.tel.tel_test_utils import set_qxdm_logger_command
from acts.test_utils.tel.tel_test_utils import start_qxdm_loggers
from acts.test_utils.tel.tel_test_utils import stop_qxdm_loggers
from acts.test_utils.tel.tel_test_utils import unlock_sim
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_ENABLED
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_DISABLED
from acts.utils import force_airplane_mode


class TelephonyBaseTest(BaseTestClass):
    def __init__(self, controllers):

        BaseTestClass.__init__(self, controllers)
        self.logger_sessions = []

        qxdm_log_mask_cfg = self.user_params.get("qxdm_log_mask_cfg", None)
        if isinstance(qxdm_log_mask_cfg, list):
            qxdm_log_mask_cfg = qxdm_log_mask_cfg[0]
        if qxdm_log_mask_cfg and "dev/null" in qxdm_log_mask_cfg:
            qxdm_log_mask_cfg = None
        stop_qxdm_loggers(self.log, self.android_devices)
        for ad in self.android_devices:
            ad.qxdm_log = getattr(ad, "qxdm_log", True)
            qxdm_log_mask = getattr(ad, "qxdm_log_mask", None)
            if ad.qxdm_log:
                if qxdm_log_mask_cfg:
                    qxdm_mask_path = find_qxdm_logger_mask(ad, "default.cfg")
                    qxdm_mask_path = os.path.split(qxdm_mask_path)[0]
                    ad.log.info("Push %s to %s", qxdm_log_mask_cfg,
                                qxdm_mask_path)
                    ad.adb.push("%s %s" % (qxdm_log_mask_cfg, qxdm_mask_path))
                    mask_file_name = os.path.split(qxdm_log_mask_cfg)[-1]
                    qxdm_log_mask = os.path.join(qxdm_mask_path,
                                                 mask_file_name)
                set_qxdm_logger_command(ad, mask=qxdm_log_mask)
                ad.adb.shell("rm %s" % os.path.join(ad.qxdm_logger_path, "*"))
            print_radio_info(ad)
            if not unlock_sim(ad):
                abort_all_tests(ad.log, "unable to unlock SIM")

        if getattr(self, "qxdm_log", True):
            start_qxdm_loggers(self.log, self.android_devices,
                               utils.get_current_epoch_time())
        self.skip_reset_between_cases = self.user_params.get(
            "skip_reset_between_cases", True)

    # Use for logging in the test cases to facilitate
    # faster log lookup and reduce ambiguity in logging.
    @staticmethod
    def tel_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            test_id = "%s:%s:%s" % (self.__class__.__name__, self.test_name,
                                    self.log_begin_time.replace(' ', '-'))
            self.test_id = test_id
            log_string = "[Test ID] %s" % test_id
            self.log.info(log_string)
            no_crash = True
            try:
                for ad in self.android_devices:
                    if getattr(ad, "droid"):
                        ad.droid.logI("Started %s" % log_string)
                # TODO: b/19002120 start QXDM Logging
                result = fn(self, *args, **kwargs)
                for ad in self.android_devices:
                    if getattr(ad, "droid"):
                        ad.droid.logI("Finished %s" % log_string)
                    new_crash = ad.check_crash_report(self.test_name,
                                                      self.begin_time, result)
                    if self.user_params.get("check_crash", True) and new_crash:
                        ad.log.error("Find new crash reports %s", new_crash)
                        no_crash = False
                if not result and self.user_params.get("telephony_auto_rerun"):
                    self.teardown_test()
                    # re-run only once, if re-run pass, mark as pass
                    log_string = "[Rerun Test ID] %s. 1st run failed." % test_id
                    self.log.info(log_string)
                    self.setup_test()
                    for ad in self.android_devices:
                        if getattr(ad, "droid"):
                            ad.droid.logI("Rerun Started %s" % log_string)
                    result = fn(self, *args, **kwargs)
                    if result is True:
                        self.log.info("Rerun passed.")
                    elif result is False:
                        self.log.info("Rerun failed.")
                    else:
                        # In the event that we have a non-bool or null
                        # retval, we want to clearly distinguish this in the
                        # logs from an explicit failure, though the test will
                        # still be considered a failure for reporting purposes.
                        self.log.info("Rerun indeterminate.")
                        result = False
                return result and no_crash
            except (TestSignal, TestAbortClass, TestAbortAll):
                raise
            except Exception as e:
                self.log.error(str(e))
                return False
            finally:
                # TODO: b/19002120 stop QXDM Logging
                for ad in self.android_devices:
                    try:
                        ad.adb.wait_for_device()
                    except Exception as e:
                        self.log.error(str(e))

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

        setattr(self, "diag_logger",
                self.register_controller(
                    acts.controllers.diag_logger, required=False))

        if not self.user_params.get("Attenuator"):
            ensure_phones_default_state(self.log, self.android_devices)
        else:
            ensure_phones_idle(self.log, self.android_devices)
        for ad in self.android_devices:
            setup_droid_properties(self.log, ad, sim_conf_file)

            # Setup VoWiFi MDN for Verizon. b/33187374
            build_id = ad.build_info["build_id"]
            if "vzw" in [
                    sub["operator"] for sub in ad.cfg["subscription"].values()
            ] and ad.is_apk_installed("com.google.android.wfcactivation"):
                ad.log.info("setup VoWiFi MDN per b/33187374")
                ad.adb.shell("setprop dbg.vzw.force_wfc_nv_enabled true")
                ad.adb.shell("am start --ei EXTRA_LAUNCH_CARRIER_APP 0 -n "
                             "\"com.google.android.wfcactivation/"
                             ".VzwEmergencyAddressActivity\"")
            # Sub ID setup
            initial_set_up_for_subid_infomation(self.log, ad)
            if "enable_wifi_verbose_logging" in self.user_params:
                ad.droid.wifiEnableVerboseLogging(WIFI_VERBOSE_LOGGING_ENABLED)
            # If device is setup already, skip the following setup procedures
            if getattr(ad, "telephony_test_setup", None):
                continue
            # Disable Emergency alerts
            # Set chrome browser start with no-first-run verification and
            # disable-fre. Give permission to read from and write to storage.
            for cmd in (
                    "pm disable com.android.cellbroadcastreceiver",
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
            try:
                if int(ad.adb.getprop("ro.product.first_api_level")) >= 25:
                    out = ad.adb.shell("/data/curl --version")
                    if not out or "not found" in out:
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
        stop_qxdm_loggers(self.log, self.android_devices)
        try:
            for ad in self.android_devices:
                ad.droid.disableDevicePassword()
                if "enable_wifi_verbose_logging" in self.user_params:
                    ad.droid.wifiEnableVerboseLogging(
                        WIFI_VERBOSE_LOGGING_DISABLED)
            return True
        except Exception as e:
            self.log.error("Failure with %s", e)

    def setup_test(self):
        if getattr(self, "qxdm_log", True):
            start_qxdm_loggers(self.log, self.android_devices, self.begin_time)
        if getattr(self, "diag_logger", None):
            for logger in self.diag_logger:
                self.log.info("Starting a diagnostic session %s", logger)
                self.logger_sessions.append((logger, logger.start()))
        if self.skip_reset_between_cases:
            ensure_phones_idle(self.log, self.android_devices)
        else:
            ensure_phones_default_state(self.log, self.android_devices)

    def teardown_test(self):
        return True

    def on_exception(self, test_name, begin_time):
        self._pull_diag_logs(test_name, begin_time)
        self._take_bug_report(test_name, begin_time)
        self._cleanup_logger_sessions()

    def on_fail(self, test_name, begin_time):
        self._pull_diag_logs(test_name, begin_time)
        self._take_bug_report(test_name, begin_time)
        self._cleanup_logger_sessions()

    def on_blocked(self, test_name, begin_time):
        self.on_fail(test_name, begin_time)

    def _block_all_test_cases(self, tests):
        """Over-write _block_all_test_case in BaseTestClass."""
        for (i, (test_name, test_func)) in enumerate(tests):
            signal = TestBlocked("Failed class setup")
            record = records.TestResultRecord(test_name, self.TAG)
            record.test_begin()
            # mark all test cases as FAIL
            record.test_fail(signal)
            self.results.add_record(record)
            # only gather bug report for the first test case
            if i == 0:
                self.on_fail(test_name, record.log_begin_time)

    def on_pass(self, test_name, begin_time):
        self._cleanup_logger_sessions()

    def get_stress_test_number(self):
        """Gets the stress_test_number param from user params.

        Gets the stress_test_number param. If absent, returns default 100.
        """
        return int(self.user_params.get("stress_test_number", 100))
