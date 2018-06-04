#!/usr/bin/env python3
#
# Copyright (C) 2018 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import json
import os
import threading
import time

from acts.base_test import BaseTestClass
from acts.test_utils.bt.bt_test_utils import disable_bluetooth
from acts.test_utils.bt.bt_test_utils import enable_bluetooth
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs
from acts.test_utils.coex.coex_test_utils import a2dp_dumpsys_parser
from acts.test_utils.coex.coex_test_utils import (
    collect_bluetooth_manager_dumpsys_logs)
from acts.test_utils.coex.coex_test_utils import configure_and_start_ap
from acts.test_utils.coex.coex_test_utils import iperf_result
from acts.test_utils.coex.coex_test_utils import get_phone_ip
from acts.test_utils.coex.coex_test_utils import wifi_connection_check
from acts.test_utils.coex.coex_test_utils import xlsheet
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi.wifi_test_utils import reset_wifi
from acts.test_utils.wifi.wifi_test_utils import wifi_connect
from acts.test_utils.wifi.wifi_test_utils import wifi_test_device_init
from acts.test_utils.wifi.wifi_test_utils import wifi_toggle_state
from acts.utils import create_dir
from acts.utils import start_standing_subprocess
from acts.utils import stop_standing_subprocess

TEST_CASE_TOKEN = "[Test Case]"
RESULT_LINE_TEMPLATE = TEST_CASE_TOKEN + " %s %s"
IPERF_SERVER_WAIT_TIME = 5
AVRCP_WAIT_TIME = 2


class CoexBaseTest(BaseTestClass):

    def __init__(self, controllers):
        super().__init__(controllers)
        self.pri_ad = self.android_devices[0]
        if len(self.android_devices) == 2:
            self.sec_ad = self.android_devices[1]
        elif len(self.android_devices) == 3:
            self.third_ad = self.android_devices[2]

    def setup_class(self):
        self.tag = 0
        self.iperf_result = {}
        self.thread_list = []
        self.log_files = []
        if not setup_multiple_devices_for_bt_test(self.android_devices):
            self.log.error("Failed to setup devices for bluetooth test")
            return False
        req_params = ["network", "iperf"]
        opt_params = ["AccessPoint", "RetailAccessPoints", "RelayDevice"]
        self.unpack_userparams(req_params, opt_params)
        if hasattr(self, "RelayDevice"):
            self.audio_receiver = self.relay_devices[0]
            self.audio_receiver.power_on()
        else:
            self.log.warning("Missing Relay config file.")
        self.path = self.pri_ad.log_path
        if hasattr(self, "AccessPoint"):
            self.ap = self.access_points[0]
            configure_and_start_ap(self.ap, self.network)
        elif hasattr(self, "RetailAccessPoints"):
            self.access_points = retail_ap.create(self.RetailAccessPoints)
            self.access_point = self.access_points[0]
            band = self.access_point.band_lookup_by_channel(
                self.network["channel"])
            self.access_point.set_channel(band, self.network["channel"])
        else:
            self.log.warning("config file have no access point information")
        wifi_test_device_init(self.pri_ad)
        wifi_connect(self.pri_ad, self.network)

    def setup_test(self):
        self.result = {}
        self.received = []
        for a in self.android_devices:
            a.ed.clear_all_events()
        self.json_file = "{}/{}.json".format(self.pri_ad.log_path,
                                             self.current_test_name)
        if not wifi_connection_check(self.pri_ad, self.network["SSID"]):
            self.log.error("Wifi connection does not exist")
            return False
        if not enable_bluetooth(self.pri_ad.droid, self.pri_ad.ed):
            self.log.error("Failed to enable bluetooth")
            return False

    def teardown_test(self):
        if "a2dp_streaming" in self.current_test_name:
            if not collect_bluetooth_manager_dumpsys_logs(
                    self.pri_ad, self.current_test_name):
                return False
            self.result["a2dp_packet_drop"] = a2dp_dumpsys_parser()
        with open(self.json_file, 'w+') as results_file:
            json.dump(self.result, results_file, indent=4)
        if not disable_bluetooth(self.pri_ad.droid):
            self.log.info("Failed to disable bluetooth")
            return False
        self.teardown_thread()

    def teardown_class(self):
        if hasattr(self, "AccessPoint"):
            self.ap.close()
        reset_wifi(self.pri_ad)
        wifi_toggle_state(self.pri_ad, False)
        json_result = self.results.json_str()
        xlsheet(self.pri_ad, json_result)

    def start_iperf_server_on_shell(self, server_port):
        """Starts iperf server on android device with specified.

        Args:
            server_port: Port in which server should be started.
        """
        log_path = os.path.join(self.pri_ad.log_path,
                                "iPerf{}".format(server_port))
        iperf_server = "iperf3 -s -p {} -J".format(server_port)
        create_dir(log_path)
        out_file_name = "IPerfServer,{},{},{}.log".format(
            server_port, self.tag, len(self.log_files))
        self.tag = self.tag + 1
        self.iperf_server_path = os.path.join(log_path, out_file_name)
        cmd = "adb -s {} shell {} > {}".format(
            self.pri_ad.serial, iperf_server, self.iperf_server_path)
        self.iperf_process.append(start_standing_subprocess(cmd))
        self.log_files.append(self.iperf_server_path)
        time.sleep(IPERF_SERVER_WAIT_TIME)

    def stop_iperf_server_on_shell(self):
        """Stops all the instances of iperf server on shell."""
        try:
            for process in self.iperf_process:
                stop_standing_subprocess(process)
        except Exception:
            pass

    def run_iperf_and_get_result(self):
        """Frames iperf command based on test and starts iperf client on
        host machine.
        """
        self.flag_list = []
        self.iperf_process = []
        test_params = self.current_test_name.split("_")

        self.protocol = test_params[-2:-1]
        self.stream = test_params[-1:]

        if self.protocol[0] == "tcp":
            self.iperf_args = "-t {} -p {} {} -J".format(
                self.iperf["duration"], self.iperf["port_1"],
                self.iperf["tcp_window_size"])
        else:
            self.iperf_args = ("-t {} -p {} -u {} -J"
                               .format(self.iperf["duration"],
                                       self.iperf["port_1"],
                                       self.iperf["udp_bandwidth"]))

        if self.stream[0] == "ul":
            self.iperf_args += " -R"

        if self.protocol[0] == "tcp" and self.stream[0] == "bidirectional":
            self.bidirectional_args = "-t {} -p {} {} -R -J".format(
                self.iperf["duration"], self.iperf["port_2"],
                self.iperf["tcp_window_size"])
        else:
            self.bidirectional_args = ("-t {} -p {} -u {}"
                                       " -J".format(self.iperf["duration"],
                                                    self.iperf["port_2"],
                                                    self.iperf["udp_bandwidth"]
                                                    ))

        if self.stream[0] == "bidirectional":
            self.start_iperf_server_on_shell(self.iperf["port_2"])
        self.start_iperf_server_on_shell(self.iperf["port_1"])

        if self.stream[0] == "bidirectional":
            args = [
                lambda: self.run_iperf(self.iperf_args),
                lambda: self.run_iperf(self.bidirectional_args)
            ]
            self.run_thread(args)
        else:
            args = [
                lambda: self.run_iperf(self.iperf_args)
            ]
            self.run_thread(args)
        return True

    def run_iperf(self, iperf_args):
        """Gets android device ip and start iperf client from host machine to
        that ip and parses the iperf result.

        Args:
            iperf_args: Iperf parameters to run traffic.
        """
        ip = get_phone_ip(self.pri_ad)
        iperf_client = self.iperf_clients[0]
        self.iperf_client_path = iperf_client.start(iperf_args, self.pri_ad, ip)
        if self.protocol[0] == "udp":
            if "-R" in iperf_args:
                received = iperf_result(self.iperf_client_path)
            else:
                received = iperf_result(self.iperf_server_path)
        else:
            received = iperf_result(self.iperf_client_path)
        if received == False:
            self.log.error("Iperf failed/stopped")
            self.flag_list.append(False)
            self.received.append("Iperf Failed")
        else:
            self.received.append(str(round(received, 2)) + "Mb/s")
            self.log.info("Received: {} Mb/s".format(received))
            self.flag_list.append(True)
        self.iperf_result[self.current_test_name] = self.received

    def on_fail(self, record, test_name, begin_time):
        """A function that is executed upon a test case failure.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """
        self.log.info(
            "Test {} failed, Fetching Btsnoop logs and bugreport".format(
                test_name))
        take_btsnoop_logs(self.android_devices, self, test_name)
        self._take_bug_report(test_name, begin_time)
        record.extras = self.received

    def _on_fail(self, record):
        """Proxy function to guarantee the base implementation of on_fail is
        called.

        Args:
            record: The records.TestResultRecord object for the failed test
            case.
        """
        if record.details:
            self.log.error(record.details)
        self.log.info(RESULT_LINE_TEMPLATE, record.test_name, record.result)
        self.on_fail(record, record.test_name, record.log_begin_time)

    def _on_pass(self, record):
        """Proxy function to guarantee the base implementation of on_pass is
        called.

        Args:
            record: The records.TestResultRecord object for the passed test
            case.
        """
        msg = record.details
        if msg:
            self.log.info(msg)
        self.log.info(RESULT_LINE_TEMPLATE, record.test_name, record.result)
        record.extras = self.received

    def run_thread(self, kwargs):
        """Convenience function to start thread.

        Args:
            kwargs: Function object to start in thread.
        """
        for function in kwargs:
            self.thread = threading.Thread(target=function)
            self.thread_list.append(self.thread)
            self.thread.start()

    def teardown_result(self):
        """Convenience function to join thread and fetch iperf result."""
        for thread_id in self.thread_list:
            if thread_id.is_alive():
                thread_id.join()
        self.stop_iperf_server_on_shell()
        if False in self.flag_list:
            return False
        return True

    def teardown_thread(self):
        """Convenience function to join thread."""
        for thread_id in self.thread_list:
            if thread_id.is_alive():
                thread_id.join()
        self.stop_iperf_server_on_shell()

    def push_music_to_android_device(self, ad):
        """Add music to Android device as specified by the test config

        Args:
            ad: Android device

        Returns:
            True on success, False on failure
        """
        self.log.info("Pushing music to the Android device")
        music_path_str = "music_file"
        android_music_path = "/sdcard/Music/"
        if music_path_str not in self.user_params:
            self.log.error("Need music for audio testcases")
            return False
        music_path = self.user_params[music_path_str]
        if type(music_path) is list:
            self.log.info("Media ready to push as is.")
        if type(music_path) is list:
            for item in music_path:
                self.music_file_to_play = item
                ad.adb.push("{} {}".format(item, android_music_path))
        return True

    def avrcp_actions(self):
        """Performs avrcp controls like volume up, volume down, skip next and
        skip previous.

        Returns: True if successful, otherwise False.
        """
        if "Volume_up" and "Volume_down" in (
                self.relay_devices[0].relays.keys()):
            current_volume = self.pri_ad.droid.getMediaVolume()
            self.audio_receiver.press_volume_up()
            if current_volume == self.pri_ad.droid.getMediaVolume():
                self.log.error("Increase volume failed")
                return False
            time.sleep(AVRCP_WAIT_TIME)
            current_volume = self.pri_ad.droid.getMediaVolume()
            self.audio_receiver.press_volume_down()
            if current_volume == self.pri_ad.droid.getMediaVolume():
                self.log.error("Decrease volume failed")
                return False
        else:
            self.log.warning("No volume control pins specfied in relay config.")

        if "Next" and "Previous" in self.relay_devices[0].relays.keys():
            self.audio_receiver.press_next()
            time.sleep(AVRCP_WAIT_TIME)
            self.audio_receiver.press_previous()
            time.sleep(AVRCP_WAIT_TIME)
        else:
            self.log.warning("No track change pins specfied in relay config.")
        return True

    def get_call_volume(self):
        """Function to get call volume when bluetooth headset connected.

        Returns:
            Call volume.
        """
        return self.pri_ad.adb.shell(
            "settings list system|grep volume_bluetooth_sco_bt_sco_hs")

    def change_volume(self):
        """Changes volume with HFP call.

        Returns: True if successful, otherwise False.
        """
        if "Volume_up" and "Volume_down" in (
                self.relay_devices[0].relays.keys()):
            current_volume = self.get_call_volume()
            self.audio_receiver.press_volume_down()
            time.sleep(AVRCP_WAIT_TIME)  # wait till volume_changes
            if current_volume == self.get_call_volume():
                self.log.error("Decrease volume failed")
                return False
            time.sleep(AVRCP_WAIT_TIME)
            current_volume = self.get_call_volume()
            self.audio_receiver.press_volume_up()
            time.sleep(AVRCP_WAIT_TIME)  # wait till volume_changes
            if current_volume == self.get_call_volume():
                self.log.error("Increase volume failed")
                return False
        else:
            self.log.warning("No volume control pins specfied in relay config.")
        return True
