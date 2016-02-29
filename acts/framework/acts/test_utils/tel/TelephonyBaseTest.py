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

import time
import traceback
from acts.base_test import BaseTestClass
from acts.signals import TestSignal

from acts.test_utils.tel.tel_test_utils import ensure_phones_default_state
from acts.test_utils.tel.tel_test_utils import get_sub_ids_for_sim_slots
from acts.test_utils.tel.tel_test_utils import get_subid_from_slot_index
from acts.test_utils.tel.tel_test_utils import set_phone_screen_on
from acts.test_utils.tel.tel_test_utils import set_phone_silent_mode
from acts.test_utils.tel.tel_test_utils import set_subid_for_data
from acts.test_utils.tel.tel_test_utils import set_subid_for_message
from acts.test_utils.tel.tel_test_utils import set_subid_for_outgoing_call
from acts.test_utils.tel.tel_test_utils import setup_droid_properties
from acts.test_utils.tel.tel_test_utils import update_phone_number_with_line1number
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING
from acts.test_utils.tel.tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_ENABLED
from acts.test_utils.tel.tel_defines import WIFI_VERBOSE_LOGGING_DISABLED
from acts.utils import force_airplane_mode


class TelephonyBaseTest(BaseTestClass):
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)

    # Use for logging in the test cases to facilitate
    # faster log lookup and reduce ambiguity in logging.
    def tel_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            test_id = "{}:{}:{}".format(self.__class__.__name__, fn.__name__,
                                        time.time())
            log_string = "[Test ID] {}".format(test_id)
            self.log.info(log_string)
            try:
                for ad in self.android_devices:
                    ad.droid.logI("Started " + log_string)
                # TODO: b/19002120 start QXDM Logging
                result = fn(self, *args, **kwargs)
                if result is not True and "telephony_auto_rerun" in self.user_params:
                    self.teardown_test()
                    # re-run only once, if re-run pass, mark as pass
                    log_string = "[Rerun Test ID] {}. 1st run failed.".format(
                        test_id)
                    self.log.info(log_string)
                    self.setup_test()
                    for ad in self.android_devices:
                        ad.droid.logI("Rerun Started "+log_string)
                    result = fn(self, *args, **kwargs)
                    if result:
                        self.log.info("Rerun passed.")
                    else:
                        self.log.info("Rerun failed.")
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
                        ad.droid.logI("Finished " + log_string)
                    except Exception as e:
                        self.log.error(str(e))

        return _safe_wrap_test_case

    def setup_class(self):
        for ad in self.android_devices:
            setup_droid_properties(self.log, ad,
                                   self.user_params["sim_conf_file"])
            if not set_phone_screen_on(self.log, ad):
                self.info.error("Failed to set phone screen-on time.")
                return False
            if not set_phone_silent_mode(self.log, ad):
                self.info.error("Failed to set phone silent mode.")
                return False

            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND, True)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING, True)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND, True)

            if "enable_wifi_verbose_logging" in self.user_params:
                ad.droid.wifiEnableVerboseLogging(WIFI_VERBOSE_LOGGING_ENABLED)

        setattr(self, 'sim_sub_ids',
                get_sub_ids_for_sim_slots(self.log, self.android_devices))

        # Sub ID setup
        for ad in self.android_devices:
            if hasattr(ad, "default_voice_sim_slot_index"):
                set_subid_for_outgoing_call(ad,
                    get_subid_from_slot_index(self.log, ad,
                        ad.default_voice_sim_slot_index))
            if hasattr(ad, "default_message_sim_slot_index"):
                set_subid_for_message(ad,
                    get_subid_from_slot_index(self.log, ad,
                        ad.default_message_sim_slot_index))
            if hasattr(ad, "default_data_sim_slot_index"):
                set_subid_for_data(ad,
                    get_subid_from_slot_index(self.log, ad,
                        ad.default_data_sim_slot_index), 0)
            # This is for Incoming Voice Sub ID
            # If "incoming_voice_sim_slot_index" is set in config file, then
            # incoming voice call will call to the phone number of the SIM in
            # "incoming_voice_sim_slot_index".
            # If "incoming_voice_sim_slot_index" is NOT set in config file,
            # then incoming voice call will call to the phone number of default
            # subId.
            if hasattr(ad, "incoming_voice_sim_slot_index"):
                incoming_voice_sub_id = get_subid_from_slot_index(
                    self.log, ad, ad.incoming_voice_sim_slot_index)
            else:
                incoming_voice_sub_id = ad.droid.subscriptionGetDefaultVoiceSubId()
            setattr(ad, "incoming_voice_sub_id", incoming_voice_sub_id)

            # This is for Incoming SMS Sub ID
            # If "incoming_message_sim_slot_index" is set in config file, then
            # incoming SMS be sent to the phone number of the SIM in
            # "incoming_message_sim_slot_index".
            # If "incoming_message_sim_slot_index" is NOT set in config file,
            # then incoming SMS be sent to the phone number of default
            # subId.
            if hasattr(ad, "incoming_message_sim_slot_index"):
                incoming_message_sub_id = get_subid_from_slot_index(
                    self.log, ad, ad.incoming_message_sim_slot_index)
            else:
                incoming_message_sub_id = ad.droid.subscriptionGetDefaultSmsSubId()
            setattr(ad, "incoming_message_sub_id", incoming_message_sub_id)
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
                try:
                    ad.droid.connectivityToggleAirplaneMode(True)
                except BrokenPipeError:
                # Broken Pipe, can not call SL4A API to turn on Airplane Mode.
                # Use adb command to turn on Airplane Mode.
                    if not force_airplane_mode(ad, True):
                        self.log.error("Can not turn on airplane mode on:{}".
                            format(ad.serial))
        return True

    def setup_test(self):
        for ad in self.android_devices:
            update_phone_number_with_line1number(self.log, ad)
        return ensure_phones_default_state(self.log, self.android_devices)

    def teardown_test(self):
        return True

    def on_fail(self, test_name, begin_time):
        return True

    def on_exception(self, test_name, begin_time):
        # Since it's a debug flag, as long as it's "set" we consider it valid
        if "no_bug_report_on_fail" not in self.user_params:
            # magical sleep to ensure the runtime restart or reboot begins
            time.sleep(1)
            for ad in self.android_devices:
                try:
                    ad.adb.wait_for_device()
                    ad.take_bug_reports(test_name, begin_time,
                                        self.android_devices)
                    # TODO: b/25290103 rename tombstone files correctly
                    # and make support generic and move to
                    # base_test and utils respectively
                    ad.adb.pull('/data/tombstones/', self.log_path)
                except:
                    ad.log.error("Failed to take a bug report for {}, {}"
                                 .format(ad.serial, test_name))
