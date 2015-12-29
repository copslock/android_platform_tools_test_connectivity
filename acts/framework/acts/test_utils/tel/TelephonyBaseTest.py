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
from acts.base_test import BaseTestClass
from acts.signals import TestSignal

from .tel_test_utils import ensure_phones_default_state
from .tel_test_utils import get_sub_ids_for_sim_slots
from .tel_test_utils import set_phone_screen_on
from .tel_test_utils import set_phone_silent_mode
from .tel_test_utils import setup_droid_properties
from .tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND
from .tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING
from .tel_defines import PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND
from .tel_defines import WIFI_VERBOSE_LOGGING_ENABLED
from .tel_defines import WIFI_VERBOSE_LOGGING_DISABLED


class TelephonyBaseTest(BaseTestClass):

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)

    # Use for logging in the test cases to facilitate
    # faster log lookup and reduce ambiguity in logging.
    def tel_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            test_id = "{}:{}:{}".format(
                self.__class__.__name__,
                fn.__name__,
                time.time())
            log_string = "[Test ID] {}".format(test_id)
            self.log.info(log_string)
            try:
                for ad in self.android_devices:
                    ad.droid.logI("Started "+log_string)
                # TODO: start QXDM Logging b/19002120
                return fn(self, *args, **kwargs)
            except TestSignal:
                raise
            except Exception as e:
                self.log.error(str(e))
                return False
            finally:
                # TODO: stop QXDM Logging b/19002120
                for ad in self.android_devices:
                    try:
                        ad.adb.wait_for_device()
                        ad.droid.logI("Finished "+log_string)
                    except Exception as e:
                        self.log.error(str(e))
        return _safe_wrap_test_case

    def setup_class(self):
        for ad in self.android_devices:
            setup_droid_properties(
                self.log, ad, self.user_params["sim_conf_file"])
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
                get_sub_ids_for_sim_slots(self.log,
                                          self.android_devices))
        return True

    def teardown_class(self):
        ensure_phones_default_state(self.log, self.android_devices)

        for ad in self.android_devices:
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND, False)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING, False)
            ad.droid.telephonyAdjustPreciseCallStateListenLevel(
                PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND, False)
            if "enable_wifi_verbose_logging" in self.user_params:
                ad.droid.wifiEnableVerboseLogging(WIFI_VERBOSE_LOGGING_DISABLED)
        return True

    def setup_test(self):
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
                    ad.take_bug_reports(
                        test_name, begin_time, self.android_devices)
                    # FIXME(nharold): rename tombstone files correctly
                    # TODO(nharold): make support generic and move to
                    # base_test and utils respectively
                    ad.adb.pull('/data/tombstones/', self.log_path)
                except:
                    ad.log.error("Failed to take a bug report for {}, {}"
                                 .format(ad.serial, test_name))
