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
    Test Script for Telephony Pre Check In Sanity
"""

import collections
import time
import os

from acts import signals
from acts.utils import create_dir
from acts.utils import unzip_maintain_permissions
from acts.utils import get_current_epoch_time
from acts.utils import exe_cmd
from acts.test_decorators import test_tracker_info
from acts.controllers.sl4a_lib.sl4a_types import Sl4aNetworkInfo
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_data_utils import wifi_tethering_setup_teardown
from acts.test_utils.tel.tel_defines import CAPABILITY_VOLTE
from acts.test_utils.tel.tel_defines import CAPABILITY_VT
from acts.test_utils.tel.tel_defines import CAPABILITY_WFC
from acts.test_utils.tel.tel_defines import CAPABILITY_OMADM
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_TETHERING_ENTITLEMENT_CHECK
from acts.test_utils.tel.tel_defines import NETWORK_SERVICE_DATA
from acts.test_utils.tel.tel_defines import GEN_4G
from acts.test_utils.tel.tel_defines import RAT_FAMILY_WLAN
from acts.test_utils.tel.tel_defines import TETHERING_MODE_WIFI
from acts.test_utils.tel.tel_defines import WAIT_TIME_AFTER_REBOOT
from acts.test_utils.tel.tel_defines import WAIT_TIME_FOR_BOOT_COMPLETE
from acts.test_utils.tel.tel_defines import WAIT_TIME_AFTER_CRASH
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_defines import VT_STATE_BIDIRECTIONAL
from acts.test_utils.tel.tel_lookup_tables import device_capabilities
from acts.test_utils.tel.tel_lookup_tables import operator_capabilities
from acts.test_utils.tel.tel_test_utils import call_setup_teardown
from acts.test_utils.tel.tel_test_utils import ensure_phone_subscription
from acts.test_utils.tel.tel_test_utils import get_model_name
from acts.test_utils.tel.tel_test_utils import get_operator_name
from acts.test_utils.tel.tel_test_utils import get_outgoing_voice_sub_id
from acts.test_utils.tel.tel_test_utils import get_slot_index_from_subid
from acts.test_utils.tel.tel_test_utils import is_droid_in_network_generation
from acts.test_utils.tel.tel_test_utils import is_sim_locked
from acts.test_utils.tel.tel_test_utils import mms_send_receive_verify
from acts.test_utils.tel.tel_test_utils import power_off_sim
from acts.test_utils.tel.tel_test_utils import power_on_sim
from acts.test_utils.tel.tel_test_utils import reboot_device
from acts.test_utils.tel.tel_test_utils import sms_send_receive_verify
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import trigger_modem_crash
from acts.test_utils.tel.tel_test_utils import trigger_modem_crash_by_modem
from acts.test_utils.tel.tel_test_utils import unlock_sim
from acts.test_utils.tel.tel_test_utils import wait_for_wfc_enabled
from acts.test_utils.tel.tel_test_utils import wait_for_cell_data_connection
from acts.test_utils.tel.tel_test_utils import wait_for_network_generation
from acts.test_utils.tel.tel_test_utils import wait_for_network_rat
from acts.test_utils.tel.tel_test_utils import wait_for_wifi_data_connection
from acts.test_utils.tel.tel_test_utils import verify_internet_connection
from acts.test_utils.tel.tel_test_utils import wait_for_state
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_3g
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_csfb
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_iwlan
from acts.test_utils.tel.tel_voice_utils import is_phone_in_call_volte
from acts.test_utils.tel.tel_voice_utils import phone_idle_volte
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_3g
from acts.test_utils.tel.tel_voice_utils import phone_setup_csfb
from acts.test_utils.tel.tel_voice_utils import phone_setup_iwlan
from acts.test_utils.tel.tel_voice_utils import phone_setup_volte
from acts.test_utils.tel.tel_video_utils import video_call_setup_teardown
from acts.test_utils.tel.tel_video_utils import phone_setup_video
from acts.test_utils.tel.tel_video_utils import \
    is_phone_in_call_video_bidirectional

from acts.utils import get_current_epoch_time
from acts.utils import rand_ascii_str


class TelLiveNoQXDMLogTest(TelephonyBaseTest):
    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.dut = self.android_devices[0]
        self.ad_reference = self.android_devices[1] if len(
            self.android_devices) > 1 else None
        setattr(self.dut, "qxdm_log", False)
        setattr(self.ad_reference, "qxdm_log", False)
        self.stress_test_number = int(
            self.user_params.get("stress_test_number", 5))
        self.skip_reset_between_cases = False
        self.dut_model = get_model_name(self.dut)
        self.dut_operator = get_operator_name(self.log, self.dut)
        self.dut_capabilities = set(
            device_capabilities.get(
                self.dut_model, device_capabilities["default"])) & set(
                    operator_capabilities.get(
                        self.dut_operator, operator_capabilities["default"]))
        self.dut.log.info("DUT capabilities: %s", self.dut_capabilities)
        self.user_params["check_crash"] = False
        self.skip_reset_between_cases = False

    def _get_list_average(self, input_list):
        total_sum = float(sum(input_list))
        total_count = float(len(input_list))
        if input_list == []:
            return False
        return float(total_sum / total_count)

    def _telephony_bootup_time_test(self):
        """Telephony Bootup Perf Test

        Arguments:
            check_lte_data: whether to check the LTE data.
            check_volte: whether to check Voice over LTE.
            check_wfc: whether to check Wifi Calling.

        Expected Results:
            Time

        Returns:
            True is pass, False if fail.
        """
        self.number_of_devices = 1
        ad = self.dut
        toggle_airplane_mode(self.log, ad, False)
        if not phone_setup_volte(self.log, ad):
            ad.log.error("Failed to setup VoLTE.")
            return False
        fail_count = collections.defaultdict(int)
        test_result = True
        keyword_time_dict = {}

        text_search_mapping = {
            'boot_complete': "processing action (sys.boot_completed=1)",
            'Voice_Reg': "< VOICE_REGISTRATION_STATE {.regState = REG_HOME",
            'Data_Reg': "< DATA_REGISTRATION_STATE {.regState = REG_HOME",
            'Data_Call_Up': "onSetupConnectionCompleted result=SUCCESS",
            'VoLTE_Enabled': "isVolteEnabled=true",
        }

        text_obj_mapping = {
            "boot_complete": None,
            "Voice_Reg": None,
            "Data_Reg": None,
            "Data_Call_Up": None,
            "VoLTE_Enabled": None,
        }
        blocked_for_calculate = ["boot_complete"]
        for i in range(1, self.stress_test_number + 1):
            ad.log.info("Telephony Bootup Time Test %s Iteration: %d / %d",
                        self.test_name, i, self.stress_test_number)
            begin_time = get_current_epoch_time()
            ad.log.debug("Begin Time is %s", begin_time)
            ad.log.info("reboot!")
            reboot_device(ad)
            iteration_result = "pass"

            time.sleep(WAIT_TIME_FOR_BOOT_COMPLETE)

            dict_match = ad.search_logcat(
                text_search_mapping['boot_complete'], begin_time=begin_time)
            if len(dict_match) != 0:
                text_obj_mapping['boot_complete'] = dict_match[0][
                    'datetime_obj']
                ad.log.debug("Datetime for boot_complete is %s",
                             text_obj_mapping['boot_complete'])
                bootup_time = dict_match[0]['datetime_obj'].strftime('%s')
                bootup_time = int(bootup_time) * 1000
                ad.log.info("Bootup Time is %d", bootup_time)
            else:
                ad.log.error("TERMINATE- boot_complete not seen in logcat")
                return False

            for tel_state in text_search_mapping:
                if tel_state == "boot_complete":
                    continue
                dict_match = ad.search_logcat(
                    text_search_mapping[tel_state], begin_time=bootup_time)
                if len(dict_match) != 0:
                    text_obj_mapping[tel_state] = dict_match[0]['datetime_obj']
                    ad.log.debug("Datetime for %s is %s", tel_state,
                                 text_obj_mapping[tel_state])
                else:
                    ad.log.error("Cannot Find Text %s in logcat",
                                 text_search_mapping[tel_state])
                    blocked_for_calculate.append(tel_state)
                    ad.log.debug("New Blocked %s", blocked_for_calculate)

            ad.log.info("List Blocked %s", blocked_for_calculate)
            for tel_state in text_search_mapping:
                if tel_state not in blocked_for_calculate:
                    time_diff = text_obj_mapping[tel_state] - \
                                text_obj_mapping['boot_complete']
                    ad.log.info("Time Diff is %d for %s", time_diff.seconds,
                                tel_state)
                    if tel_state in keyword_time_dict:
                        keyword_time_dict[tel_state].append(time_diff.seconds)
                    else:
                        keyword_time_dict[tel_state] = [
                            time_diff.seconds,
                        ]
                    ad.log.debug("Keyword Time Dict %s", keyword_time_dict)

            ad.log.info("Telephony Bootup Time Test %s Iteration: %d / %d %s",
                        self.test_name, i, self.stress_test_number,
                        iteration_result)
        ad.log.info("Final Keyword Time Dict %s", keyword_time_dict)
        for tel_state in text_search_mapping:
            if tel_state not in blocked_for_calculate:
                avg_time = self._get_list_average(keyword_time_dict[tel_state])
                if avg_time < 12.0:
                    ad.log.info("Average %s for %d iterations = %.2f seconds",
                                tel_state, self.stress_test_number, avg_time)
                else:
                    ad.log.error("Average %s for %d iterations = %.2f seconds",
                                 tel_state, self.stress_test_number, avg_time)
                    fail_count[tel_state] += 1

        ad.log.info("Bootup Time Dict: %s", keyword_time_dict)
        ad.log.info("fail_count: %s", dict(fail_count))
        for failure, count in fail_count.items():
            if count:
                ad.log.error("%s %s failures in %s iterations", count, failure,
                             self.stress_test_number)
                test_result = False
        return test_result

    """ Tests Begin """

    @test_tracker_info(uuid="109d59ff-a488-4a68-87fd-2d8d0c035326")
    @TelephonyBaseTest.tel_test_wrap
    def test_bootup_optimized_stress(self):
        """Bootup Optimized Reliability Test

        Steps:
            1. Reboot DUT.
            2. Parse logcat for time taken by Voice, Data, VoLTE
            3. Repeat Step 1~2 for N times. (before reboot)

        Expected Results:
            No crash happens in stress test.

        Returns:
            True is pass, False if fail.
        """
        return self._telephony_bootup_time_test()

    @test_tracker_info(uuid="67f50d11-a987-4e79-9a20-1569d365511b")
    @TelephonyBaseTest.tel_test_wrap
    def test_modem_power_anomaly_file_existence(self):
        """Verify if the power anomaly file exists

        1. Collect Bugreport
        2. unzip bugreport
        3. remane the .bin file to .tar
        4. unzip dumpstate.tar
        5. Verify if the file exists

        """
        ad = self.android_devices[0]
        cmd = ("am broadcast -a "
               "com.google.gservices.intent.action.GSERVICES_OVERRIDE "
               "-e \"ce.cm.power_anomaly_data_enable\" \"true\"")
        ad.adb.shell(cmd)
        time.sleep(60)
        begin_time = get_current_epoch_time()
        for i in range(3):
            try:
                bugreport_path = os.path.join(ad.log_path, self.test_name)
                create_dir(bugreport_path)
                ad.take_bug_report(self.test_name, begin_time)
                break
            except Exception as e:
                ad.log.error("bugreport attempt %s error: %s", i + 1, e)
        ad.log.info("Bugreport Path is %s" % bugreport_path)
        try:
            list_of_files = os.listdir(bugreport_path)
            ad.log.info(list_of_files)
            for filename in list_of_files:
                if ".zip" in filename:
                    ad.log.info(filename)
                    file_path = os.path.join(bugreport_path, filename)
                    ad.log.info(file_path)
                    unzip_maintain_permissions(file_path, bugreport_path)
            dumpstate_path = os.path.join(bugreport_path,
                                          "dumpstate_board.bin")
            if os.path.isfile(dumpstate_path):
                os.rename(dumpstate_path,
                          bugreport_path + "/dumpstate_board.tar")
                os.chmod(bugreport_path + "/dumpstate_board.tar", 0o777)
                current_dir = os.getcwd()
                os.chdir(bugreport_path)
                exe_cmd("tar -xvf %s" %
                        (bugreport_path + "/dumpstate_board.tar"))
                os.chdir(current_dir)
                if os.path.isfile(bugreport_path + "/power_anomaly_data.txt"):
                    ad.log.info("Modem Power Anomaly File Exists!!")
                    return True
            ad.log.info("Modem Power Anomaly File DO NOT Exist!!")
            return False
        except Exception as e:
            ad.log.error(e)
            return False


""" Tests End """
