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
from acts import utils

from acts.test_utils.tel.tel_subscription_utils import \
    get_subid_from_slot_index
from acts.test_utils.tel.tel_subscription_utils import \
    initial_set_up_for_subid_infomation
from acts.test_utils.tel.tel_subscription_utils import set_subid_for_data
from acts.test_utils.tel.tel_subscription_utils import \
    set_subid_for_message
from acts.test_utils.tel.tel_subscription_utils import \
    set_subid_for_outgoing_call
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import ensure_phones_default_state
from acts.test_utils.tel.tel_test_utils import \
    reset_preferred_network_type_to_allowable_range
from acts.test_utils.tel.tel_test_utils import set_phone_screen_on
from acts.test_utils.tel.tel_test_utils import set_phone_silent_mode
from acts.test_utils.tel.tel_test_utils import setup_droid_properties
from acts.test_utils.tel.tel_test_utils import refresh_droid_config
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_ENABLED
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_DISABLED
from acts.utils import force_airplane_mode


class _TelephonyTraceLogger():
    def __init__(self, logger):
        self._logger = logger

    @staticmethod
    def _get_trace_info(level=1):
        # we want the stack frame above this and above the error/warning/info
        inspect_stack = inspect.stack()
        trace_info = ""
        for i in range(level):
            stack_frames = inspect_stack[2 + i]
            info = inspect.getframeinfo(stack_frames[0])
            trace_info = "%s[%s:%s:%s]" % (trace_info,
                                           os.path.basename(info.filename),
                                           info.function, info.lineno)
        return trace_info

    def error(self, msg, *args, **kwargs):
        trace_info = _TelephonyTraceLogger._get_trace_info(level=3)
        self._logger.error("%s %s" % (msg, trace_info), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        trace_info = _TelephonyTraceLogger._get_trace_info(level=1)
        self._logger.warning("%s %s" % (msg, trace_info), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        trace_info = _TelephonyTraceLogger._get_trace_info(level=1)
        self._logger.info("%s %s" % (msg, trace_info), *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._logger, name)


class TelephonyBaseTest(BaseTestClass):
    def __init__(self, controllers):

        BaseTestClass.__init__(self, controllers)
        self.logger_sessions = []

        self.log = _TelephonyTraceLogger(self.log)
        for ad in self.android_devices:
            ad.log = _TelephonyTraceLogger(ad.log)

    # Use for logging in the test cases to facilitate
    # faster log lookup and reduce ambiguity in logging.
    @staticmethod
    def tel_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            current_time = time.strftime("%m-%d-%Y-%H-%M-%S")
            func_name = fn.__name__
            test_id = "%s:%s:%s" % (self.__class__.__name__, func_name,
                                    current_time)
            self.test_id = test_id
            self.begin_time = current_time
            self.test_name = func_name
            log_string = "[Test ID] %s" % test_id
            self.log.info(log_string)
            try:
                for ad in self.android_devices:
                    ad.droid.logI("Started %s" % log_string)
                    ad.crash_report = ad.check_crash_report(
                        log_crash_report=False)
                    if ad.crash_report:
                        ad.log.warn("Crash reports %s before test %s start",
                                    ad.crash_report, func_name)

                # TODO: b/19002120 start QXDM Logging
                result = fn(self, *args, **kwargs)
                for ad in self.android_devices:
                    ad.droid.logI("Finished %s" % log_string)
                    new_crash = ad.check_crash_report()
                    if new_crash != ad.crash_report:
                        ad.log.error("Find new crash reports %s", new_crash)
                if result is not True and "telephony_auto_rerun" in self.user_params:
                    self.teardown_test()
                    # re-run only once, if re-run pass, mark as pass
                    log_string = "[Rerun Test ID] %s. 1st run failed." % test_id
                    self.log.info(log_string)
                    self.setup_test()
                    for ad in self.android_devices:
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
                return result
            except TestSignal:
                raise
            except Exception as e:
                self.log.error(traceback.format_exc())
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

        if not "sim_conf_file" in self.user_params.keys():
            self.log.warn("Missing mandatory user config \"sim_conf_file\"!")
            sim_conf_file = None
        else:
            sim_conf_file = self.user_params["sim_conf_file"]
            # If the sim_conf_file is not a full path, attempt to find it
            # relative to the config file.
            if not os.path.isfile(sim_conf_file):
                sim_conf_file = os.path.join(
                    self.user_params[Config.key_config_path], sim_conf_file)
                if not os.path.isfile(sim_conf_file):
                    self.log.error("Unable to load user config %s ",
                                   sim_conf_file)
                    return False

        setattr(
            self,
            "diag_logger",
            self.register_controller(
                acts.controllers.diag_logger, required=False))

        ensure_phones_default_state(self.log, self.android_devices)
        for ad in self.android_devices:
            setup_droid_properties(self.log, ad, sim_conf_file)

            # Setup VoWiFi MDN for Verizon. b/33187374
            build_id = ad.build_info["build_id"]
            if "vzw" in [sub["operator"] for sub in ad.cfg[
                    "subscription"].values()] and ad.model in (
                            "marlin", "sailfish") and (build_id.startswith(
                                    "N2") or build_id.startswith("OR")):
                ad.log.info("setup VoWiFi MDN for MR2 or OC branch per b/33187374")
                ad.adb.shell("setprop dbg.vzw.force_wfc_nv_enabled true")
                ad.adb.shell("am start --ei EXTRA_LAUNCH_CARRIER_APP 0 -n "
                             "\"com.google.android.wfcactivation/"
                             ".VzwEmergencyAddressActivity\"")

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

                if "enable_wifi_verbose_logging" in self.user_params:
                    ad.droid.wifiEnableVerboseLogging(
                        WIFI_VERBOSE_LOGGING_ENABLED)
            except Exception as e:
                self.log.error("Failure with %s", e)
        # Sub ID setup
        for ad in self.android_devices:
            initial_set_up_for_subid_infomation(self.log, ad)
        return True

    def teardown_class(self):
        try:
            ensure_phones_default_state(self.log, self.android_devices)

            for ad in self.android_devices:
                ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                    PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND, False)
                ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                    PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING, False)
                ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                    PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND, False)
                if "enable_wifi_verbose_logging" in self.user_params:
                    ad.droid.wifiEnableVerboseLogging(
                        WIFI_VERBOSE_LOGGING_DISABLED)
        finally:
            for ad in self.android_devices:
                toggle_airplane_mode(self.log, ad, True, strict_checking=False)

        return True

    def setup_test(self):
        for ad in self.android_devices:
            refresh_droid_config(self.log, ad)

        if getattr(self, "diag_logger", None):
            for logger in self.diag_logger:
                self.log.info("Starting a diagnostic session %s", logger)
                self.logger_sessions.append((logger, logger.start()))

        return ensure_phones_default_state(self.log, self.android_devices)

    def teardown_test(self):
        return True

    def _cleanup_logger_sessions(self):
        for (logger, session) in self.logger_sessions:
            self.log.info("Resetting a diagnostic session %s, %s", logger,
                          session)
            logger.reset()
        self.logger_sessions = []

    def on_exception(self, test_name, begin_time):
        self._pull_diag_logs(test_name, begin_time)
        self._take_bug_report(test_name, begin_time)
        self._cleanup_logger_sessions()

    def on_fail(self, test_name, begin_time):
        self._pull_diag_logs(test_name, begin_time)
        self._take_bug_report(test_name, begin_time)
        self._cleanup_logger_sessions()

    def on_pass(self, test_name, begin_time):
        self._cleanup_logger_sessions()

    def _pull_diag_logs(self, test_name, begin_time):
        for (logger, session) in self.logger_sessions:
            self.log.info("Pulling diagnostic session %s", logger)
            logger.stop(session)
            diag_path = os.path.join(self.log_path, begin_time)
            utils.create_dir(diag_path)
            logger.pull(session, diag_path)

    def _take_bug_report(self, test_name, begin_time):
        if "no_bug_report_on_fail" in self.user_params:
            return

        # magical sleep to ensure the runtime restart or reboot begins
        time.sleep(1)
        for ad in self.android_devices:
            try:
                ad.adb.wait_for_device()
                ad.take_bug_report(test_name, begin_time)
                tombstone_path = os.path.join(
                    ad.log_path, "BugReports",
                    "{},{}".format(begin_time, ad.serial).replace(' ', '_'))
                utils.create_dir(tombstone_path)
                ad.adb.pull('/data/tombstones/', tombstone_path, timeout=1200)
            except:
                ad.log.error("Failed to take a bug report for %s", test_name)

    def get_stress_test_number(self):
        """Gets the stress_test_number param from user params.

        Gets the stress_test_number param. If absent, returns default 100.
        """
        return int(self.user_params.get("stress_test_number", 100))
