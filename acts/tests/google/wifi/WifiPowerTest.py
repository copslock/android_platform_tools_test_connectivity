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

import acts.base_test
import acts.test_utils.wifi_test_utils as wutils
import acts.test_utils.tel.tel_test_utils as tel_utils

class WifiPowerTest(acts.base_test.BaseTestClass):

    def __init__(self, controllers):
        super(WifiPowerTest, self).__init__(controllers)
        self.tests = (
            "test_power",
        )

    def setup_class(self):
        self.mon = self.monsoons[0]
        self.mon.set_voltage(4.2)
        self.mon.set_max_current(7.8)
        self.dut = self.android_devices[0]
        required_userparam_names = (
            # These two params should follow the format of
            # {"SSID": <SSID>, "password": <Password>}
            "network_2g",
            "network_5g"
        )
        assert self.unpack_userparams(required_userparam_names)
        wutils.wifi_test_device_init(self.dut)
        start_pmc_cmd = ("am start -n com.android.pmc/com.android.pmc."
            "PMCMainActivity")
        # Start pmc app.
        self.dut.adb.shell(start_pmc_cmd)
        pmc_base_cmd = ("am broadcast -a com.android.pmc.action.AUTOPOWER --es"
                        " PowerAction ")
        self.pmc_start_connect_scan_cmd = pmc_base_cmd + "StartConnectivityScan"
        self.pmc_stop_connect_scan_cmd = pmc_base_cmd + "StopConnectivityScan"
        self.pmc_start_gscan_no_dfs_cmd = pmc_base_cmd + "StartGScanBand"
        self.pmc_start_gscan_specific_channels_cmd = pmc_base_cmd + "StartGScanChannel"
        self.pmc_stop_gscan_cmd = pmc_base_cmd + "StopGScan"
        self.pmc_start_1MB_download_cmd = pmc_base_cmd + "Download1MB"
        self.pmc_stop_1MB_download_cmd = pmc_base_cmd + "StopDownload"
        tel_utils.toggle_airplane_mode(self.log, self.dut, True)
        return True

    def teardown_class(self):
        self.dut.adb.shell(self.pmc_stop_gscan_cmd)
        wutils.reset_wifi(self.dut)

    def teardown_test(self):
        # TODO(angli): save monsoon data and bugreport.
        pass

    def wifi_off(self, ad):
        self.assert_true(wutils.wifi_toggle_state(self.dut, False),
                         "Failed to toggle wifi off.")
        return True

    def wifi_on(self, ad):
        self.assert_true(wutils.wifi_toggle_state(self.dut, True),
                         "Failed to toggle wifi on.")
        return True

    def wifi_on_with_connectivity_scan(self, ad):
        self.dut.adb.shell(self.pmc_start_connect_scan_cmd)
        self.log.info("Started connectivity scan.")
        return True

    def connected_to_2g(self, ad):
        self.dut.adb.shell(self.pmc_stop_connect_scan_cmd)
        self.log.info("Stoped connectivity scan.")
        wutils.reset_wifi(self.dut)
        wutils.wifi_connect(self.dut, self.network_2g)
        return True

    def connected_to_2g_download_1MB(self, ad):
        self.log.info("Start downloading 1MB file consecutively.")
        self.dut.adb.shell(self.pmc_start_1MB_download_cmd)
        return True

    def connected_to_5g(self, ad):
        self.dut.adb.shell(self.pmc_stop_1MB_download_cmd)
        self.log.info("Stopped downloading 1MB file.")
        wutils.reset_wifi(ad)
        wutils.wifi_connect(self.dut, self.network_5g)
        return True

    def connected_to_5g_download_1MB(self, ad):
        self.log.info("Start downloading 1MB file consecutively.")
        self.dut.adb.shell(self.pmc_start_1MB_download_cmd)
        return True

    def gscan_with_three_channels(self, ad):
        wutils.reset_wifi(self.dut)
        self.log.info("Disconnected from wifi.")
        self.dut.adb.shell(self.pmc_stop_1MB_download_cmd)
        self.log.info("Stopped downloading 1MB file.")
        self.dut.adb.shell(self.pmc_start_gscan_specific_channels_cmd)
        self.log.info("Started gscan for the three main 2G channels.")
        return True

    def gscan_with_all_channels(self, ad):
        self.dut.adb.shell(self.pmc_stop_gscan_cmd)
        self.log.info("Stopped gscan with channels.")
        self.dut.adb.shell(self.pmc_start_gscan_no_dfs_cmd)
        self.log.info("Started gscan for all but DFS channels.")
        return True

    def test_power(self):
        durations = 1
        funcs = [
            self.wifi_off,
            self.wifi_on,
            self.wifi_on_with_connectivity_scan,
            self.connected_to_2g,
            self.connected_to_2g_download_1MB,
            self.connected_to_5g,
            self.connected_to_5g_download_1MB,
            self.gscan_with_three_channels,
            self.gscan_with_all_channels
        ]
        params = [[func] for func in funcs]
        def gen_name(step_funcs, hz, duration, ad, offset_sec):
            return "test_%s" % step_funcs[0].__name__
        self.run_generated_testcases(
                self.mon.execute_sequence_and_measure,
                params,
                10, 1, self.dut, 30,
                name_func=gen_name
            )
