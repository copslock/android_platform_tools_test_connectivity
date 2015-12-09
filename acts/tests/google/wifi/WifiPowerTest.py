#!/usr/bin/python3.4
#
#   Copyright 2014 - The Android Open Source Project
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

import itertools
import json
import time
import traceback

from queue import Empty

from acts.base_test import BaseTestClass
from acts.utils import find_field
from acts.utils import rand_ascii_str
from acts.utils import sync_device_time

from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.wifi_test_utils import reset_wifi
from acts.test_utils.wifi_test_utils import start_wifi_connection_scan
from acts.test_utils.wifi_test_utils import wifi_connect
from acts.test_utils.wifi_test_utils import wifi_toggle_state
from acts.test_utils.wifi_test_utils import WifiEnums

class WifiPowerTest(BaseTestClass):

    def __init__(self, controllers):
        self.tests = (
            "test_power",
            )
        BaseTestClass.__init__(self, controllers)

    def setup_class(self):
        self.mon = self.monsoons[0]
        self.mon.set_voltage(4.2)
        self.mon.set_max_current(7.8)
        self.ad = self.android_devices[0]
        required_userparam_names = (
            # These two params should follow the format of
            # {"SSID": <SSID>, "password": <Password>}
            "network_2g",
            "network_5g"
        )
        assert self.unpack_userparams(required_userparam_names)
        sync_device_time(self.ad)
        reset_wifi(self.ad.droid, self.ad.ed)
        return True

    def test_power(self):
        toggle_airplane_mode(self.log, self.ad, True)
        # 30min for each measurement.
        durations = 1
        start_pmc = ("am start -n com.android.pmc/com.android.pmc."
            "PMCMainActivity")
        pmc_base_cmd = "am broadcast -a com.android.pmc.action.AUTOPOWER --es PowerAction "
        pmc_start_connect_scan = pmc_base_cmd + "StartConnectivityScan"
        pmc_stop_connect_scan = pmc_base_cmd + "StopConnectivityScan"
        pmc_start_gscan_no_dfs = pmc_base_cmd + "StartGScanBand"
        pmc_start_gscan_specific_channels = pmc_base_cmd + "StartGScanChannel"
        pmc_stop_gscan = pmc_base_cmd + "StopGScan"
        pmc_start_1MB_download = pmc_base_cmd + "Download1MB"
        pmc_stop_1MB_download = pmc_base_cmd + "StopDownload"
        # Start pmc app.
        self.ad.adb.shell(start_pmc)
        def wifi_off(ad):
            assert wifi_toggle_state(ad, False)
            return True
        def wifi_on(ad):
            assert wifi_toggle_state(ad, True)
            return True
        def wifi_on_with_connectivity_scan(ad):
            ad.adb.shell(pmc_start_connect_scan)
            self.log.info("Started connectivity scan.")
            return True
        def connected_to_2g(ad):
            ad.adb.shell(pmc_stop_connect_scan)
            self.log.info("Stoped connectivity scan.")
            reset_wifi(ad)
            ssid = self.network_2g["SSID"]
            pwd = self.network_2g["password"]
            msg = "Failed to connect to %s" % ssid
            assert wifi_connect(ad, ssid, pwd), msg
            self.log.info("Connected to %s" % ssid)
            return True
        def connected_to_2g_download_1MB(ad):
            self.log.info("Start downloading 1MB file consecutively.")
            ad.adb.shell(pmc_start_1MB_download)
            return True
        def connected_to_5g(ad):
            ad.adb.shell(pmc_stop_1MB_download)
            self.log.info("Stopped downloading 1MB file.")
            reset_wifi(ad)
            ssid = self.network_5g["SSID"]
            pwd = self.network_5g["password"]
            msg = "Failed to connect to %s" % ssid
            assert wifi_connect(ad, ssid, pwd), msg
            self.log.info("Connected to %s" % ssid)
            return True
        def connected_to_5g_download_1MB(ad):
            self.log.info("Start downloading 1MB file consecutively.")
            ad.adb.shell(pmc_start_1MB_download)
            return True
        def gscan_with_three_channels(ad):
            reset_wifi(ad)
            self.log.info("Disconnected from wifi.")
            ad.adb.shell(pmc_stop_1MB_download)
            self.log.info("Stopped downloading 1MB file.")
            ad.adb.shell(pmc_start_gscan_specific_channels)
            self.log.info("Started gscan for the three main 2G channels.")
            return True
        def gscan_with_all_channels(ad):
            ad.adb.shell(pmc_stop_gscan)
            self.log.info("Stopped gscan with channels.")
            ad.adb.shell(pmc_start_gscan_no_dfs)
            self.log.info("Started gscan for all but DFS channels.")
            return True
        def clean_up(ad):
            ad.adb.shell(pmc_stop_gscan)
            reset_wifi(ad)
            return False
        funcs = (
            wifi_off,
            wifi_on,
            wifi_on_with_connectivity_scan,
            connected_to_2g,
            connected_to_2g_download_1MB,
            connected_to_5g,
            connected_to_5g_download_1MB,
            gscan_with_three_channels,
            gscan_with_all_channels
        )
        results = self.mon.execute_sequence_and_measure(10, durations, funcs, self.ad, offset_sec=30)
        assert len(results) == len(funcs), "Did not get enough results!"
        return True
