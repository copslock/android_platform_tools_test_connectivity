#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

import os

import acts.base_test
from acts import asserts
from acts import utils
from acts.controllers import iperf_server as ip_server
from acts.controllers import monsoon
from acts.test_utils.wifi import wifi_test_utils as wutils


pmc_base_cmd = ("am broadcast -a com.android.pmc.action.AUTOPOWER --es"
                " PowerAction ")
start_pmc_cmd = ("am start -n com.android.pmc/com.android.pmc."
    "PMCMainActivity")
pmc_interval_cmd = ("am broadcast -a com.android.pmc.action.SETPARAMS --es "
                    "Interval %s ")
pmc_set_params = "am broadcast -a com.android.pmc.action.SETPARAMS --es "

pmc_start_connect_scan_cmd = "%sStartConnectivityScan" % pmc_base_cmd
pmc_stop_connect_scan_cmd = "%sStopConnectivityScan" % pmc_base_cmd
pmc_start_gscan_no_dfs_cmd = "%sStartGScanBand" % pmc_base_cmd
pmc_start_gscan_specific_channels_cmd = "%sStartGScanChannel" % pmc_base_cmd
pmc_stop_gscan_cmd = "%sStopGScan" % pmc_base_cmd
pmc_start_iperf_client = "%sStartIperfClient" % pmc_base_cmd
pmc_stop_iperf_client = "%sStopIperfClient" % pmc_base_cmd
# Path of the iperf json output file from an iperf run.
pmc_iperf_json_file = "/sdcard/iperf.txt"


class WifiPowerTest(acts.base_test.BaseTestClass):

    def setup_class(self):
        self.hz = 5000
        self.offset = 5 * 60
        self.duration = 30 * 60 + self.offset
        self.scan_interval = 15
        # Continuosly download
        self.download_interval = 0
        self.mon_data_path = os.path.join(self.log_path, "Monsoon")

        self.mon = self.monsoons[0]
        self.mon.set_voltage(4.2)
        self.mon.set_max_current(7.8)
        self.dut = self.android_devices[0]
        self.mon.attach_device(self.dut)
        asserts.assert_true(self.mon.usb("auto"),
                            "Failed to turn USB mode to auto on monsoon.")
        required_userparam_names = (
            # These two params should follow the format of
            # {"SSID": <SSID>, "password": <Password>}
            "network_2g",
            "network_5g",
            "iperf_server_address"
        )
        self.unpack_userparams(required_userparam_names, ("threshold",))
        wutils.wifi_test_device_init(self.dut)
        # Start pmc app.
        self.dut.adb.shell(start_pmc_cmd)
        self.dut.adb.shell("setprop log.tag.PMC VERBOSE")
        self.iperf_server = self.iperf_servers[0]
        # Setup iperf related params on the client side.
        self.dut.adb.shell("%sServerIP %s" % (pmc_set_params,
                                              self.iperf_server_address))
        self.dut.adb.shell("%sServerPort %s" % (pmc_set_params,
                                                self.iperf_server.port))
        self.dut.adb.shell("rm %s" % pmc_iperf_json_file)

    def teardown_class(self):
        self.mon.usb("on")

    def setup_test(self):
        wutils.reset_wifi(self.dut)
        self.dut.ed.clear_all_events()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)

    def on_pass(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)

    def get_iperf_result(self):
        """Pulls the iperf json output from device.

        Returns:
            An IPerfResult object based on the iperf run output.
        """
        dest = os.path.join(self.iperf_server.log_path, "iperf.txt")
        self.dut.adb.pull(pmc_iperf_json_file, " ", dest)
        result = ip_server.IPerfResult(dest)
        self.dut.adb.shell("rm %s" % pmc_iperf_json_file)
        return result

    def measure_and_process_result(self):
        """Measure the current drawn by the device for the period of
        self.duration, at the frequency of self.hz.

        If self.threshold exists, also verify that the average current of the
        measurement is below the acceptable threshold.
        """
        tag = self.current_test_name
        result = self.mon.measure_power(self.hz,
                                        self.duration,
                                        tag=tag,
                                        offset=self.offset)
        asserts.assert_true(result,
                            "Got empty measurement data set in %s." % tag)
        self.log.info(repr(result))
        data_path = os.path.join(self.mon_data_path, "%s.txt" % tag)
        monsoon.MonsoonData.save_to_text_file([result], data_path)
        actual_current = result.average_current
        actual_current_str = "%.2fmA" % actual_current
        result_extra = {"Average Current": actual_current_str}
        if "continuous_traffic" in tag:
            self.dut.adb.shell(pmc_stop_iperf_client)
            iperf_result = self.get_iperf_result()
            asserts.assert_true(iperf_result.avg_rate,
                                "Failed to send iperf traffic",
                                extras=result_extra)
            rate = "%.2fMB/s" % iperf_result.avg_rate
            result_extra["Average Rate"] = rate
        if self.threshold:
            model = utils.trim_model_name(self.dut.model)
            asserts.assert_true(tag in self.threshold[model],
                             "Acceptance threshold for %s is missing" % tag,
                             extras=result_extra)
            acceptable_threshold = self.threshold[model][tag]
            asserts.assert_true(actual_current < acceptable_threshold,
                             ("Measured average current in [%s]: %s, which is "
                              "higher than acceptable threshold %.2fmA.") % (
                              tag, actual_current_str, acceptable_threshold),
                              extras=result_extra)
        asserts.explicit_pass("Measurement finished for %s." % tag,
                              extras=result_extra)

    def test_power_wifi_off(self):
        asserts.assert_true(wutils.wifi_toggle_state(self.dut, False),
                         "Failed to toggle wifi off.")
        self.measure_and_process_result()

    def test_power_wifi_on_idle(self):
        asserts.assert_true(wutils.wifi_toggle_state(self.dut, True),
                         "Failed to toggle wifi on.")
        self.measure_and_process_result()

    def test_power_disconnected_connectivity_scan(self):
        try:
            self.dut.adb.shell(pmc_interval_cmd % self.scan_interval)
            self.dut.adb.shell(pmc_start_connect_scan_cmd)
            self.log.info("Started connectivity scan.")
            self.measure_and_process_result()
        finally:
            self.dut.adb.shell(pmc_stop_connect_scan_cmd)
            self.log.info("Stoped connectivity scan.")

    def test_power_connected_2g_idle(self):
        wutils.reset_wifi(self.dut)
        self.dut.ed.clear_all_events()
        wutils.wifi_connect(self.dut, self.network_2g)
        self.measure_and_process_result()

    def test_power_connected_2g_continuous_traffic(self):
        try:
            wutils.reset_wifi(self.dut)
            self.dut.ed.clear_all_events()
            wutils.wifi_connect(self.dut, self.network_2g)
            self.iperf_server.start()
            self.dut.adb.shell(pmc_start_iperf_client)
            self.log.info("Started iperf traffic.")
            self.measure_and_process_result()
        finally:
            self.iperf_server.stop()
            self.log.info("Stopped iperf traffic.")

    def test_power_connected_5g_idle(self):
        wutils.reset_wifi(self.dut)
        self.dut.ed.clear_all_events()
        wutils.wifi_connect(self.dut, self.network_5g)
        self.measure_and_process_result()

    def test_power_connected_5g_continuous_traffic(self):
        try:
            wutils.reset_wifi(self.dut)
            self.dut.ed.clear_all_events()
            wutils.wifi_connect(self.dut, self.network_5g)
            self.iperf_server.start()
            self.dut.adb.shell(pmc_start_iperf_client)
            self.log.info("Started iperf traffic.")
            self.measure_and_process_result()
        finally:
            self.iperf_server.stop()
            self.log.info("Stopped iperf traffic.")

    def test_power_gscan_three_2g_channels(self):
        try:
            self.dut.adb.shell(pmc_interval_cmd % self.scan_interval)
            self.dut.adb.shell(pmc_start_gscan_specific_channels_cmd)
            self.log.info("Started gscan for 2G channels 1, 6, and 11.")
            self.measure_and_process_result()
        finally:
            self.dut.adb.shell(pmc_stop_gscan_cmd)
            self.log.info("Stopped gscan.")

    def test_power_gscan_all_channels_no_dfs(self):
        try:
            self.dut.adb.shell(pmc_interval_cmd % self.scan_interval)
            self.dut.adb.shell(pmc_start_gscan_no_dfs_cmd)
            self.log.info("Started gscan for all non-DFS channels.")
            self.measure_and_process_result()
        finally:
            self.dut.adb.shell(pmc_stop_gscan_cmd)
            self.log.info("Stopped gscan.")

    def test_power_connected_2g_gscan_all_channels_no_dfs(self):
        try:
            wutils.wifi_connect(self.dut, self.network_2g)
            self.dut.adb.shell(pmc_interval_cmd % self.scan_interval)
            self.dut.adb.shell(pmc_start_gscan_no_dfs_cmd)
            self.log.info("Started gscan for all non-DFS channels.")
            self.measure_and_process_result()
        finally:
            self.dut.adb.shell(pmc_stop_gscan_cmd)
            self.log.info("Stopped gscan.")

    def test_power_connected_5g_gscan_all_channels_no_dfs(self):
        try:
            wutils.wifi_connect(self.dut, self.network_5g)
            self.dut.adb.shell(pmc_interval_cmd % self.scan_interval)
            self.dut.adb.shell(pmc_start_gscan_no_dfs_cmd)
            self.log.info("Started gscan for all non-DFS channels.")
            self.measure_and_process_result()
        finally:
            self.dut.adb.shell(pmc_stop_gscan_cmd)
            self.log.info("Stopped gscan.")
