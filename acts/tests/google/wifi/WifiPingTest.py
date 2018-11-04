#!/usr/bin/env python3.4
#
#   Copyright 2017 - The Android Open Source Project
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

import json
import logging
import os
import statistics
import time
from acts import asserts
from acts import base_test
from acts import utils
from acts.metrics.loggers.blackbox import BlackboxMetricLogger
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils


class WifiPingTest(base_test.BaseTestClass):
    """Class for ping-based Wifi performance tests.

    This class implements WiFi ping performance tests such as range and RTT.
    The class setups up the AP in the desired configurations, configures
    and connects the phone to the AP, and runs  For an example config file to
    run this test class see example_connectivity_performance_ap_sta.json.
    """

    TEST_TIMEOUT = 10
    SHORT_SLEEP = 1
    MED_SLEEP = 5

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.ping_range_metric = BlackboxMetricLogger.for_test_case(
            metric_name='ping_range')
        self.ping_rtt_metric = BlackboxMetricLogger.for_test_case(
            metric_name='ping_rtt')
        self.tests = (
            "test_ping_range_ch1_VHT20", "test_fast_ping_rtt_ch1_VHT20",
            "test_slow_ping_rtt_ch1_VHT20", "test_ping_range_ch6_VHT20",
            "test_fast_ping_rtt_ch6_VHT20", "test_slow_ping_rtt_ch6_VHT20",
            "test_ping_range_ch11_VHT20", "test_fast_ping_rtt_ch11_VHT20",
            "test_slow_ping_rtt_ch11_VHT20", "test_ping_range_ch36_VHT20",
            "test_fast_ping_rtt_ch36_VHT20", "test_slow_ping_rtt_ch36_VHT20",
            "test_ping_range_ch36_VHT40", "test_fast_ping_rtt_ch36_VHT40",
            "test_slow_ping_rtt_ch36_VHT40", "test_ping_range_ch36_VHT80",
            "test_fast_ping_rtt_ch36_VHT80", "test_slow_ping_rtt_ch36_VHT80",
            "test_ping_range_ch40_VHT20", "test_ping_range_ch44_VHT20",
            "test_ping_range_ch44_VHT40", "test_ping_range_ch48_VHT20",
            "test_ping_range_ch149_VHT20", "test_fast_ping_rtt_ch149_VHT20",
            "test_slow_ping_rtt_ch149_VHT20", "test_ping_range_ch149_VHT40",
            "test_fast_ping_rtt_ch149_VHT40", "test_slow_ping_rtt_ch149_VHT40",
            "test_ping_range_ch149_VHT80", "test_fast_ping_rtt_ch149_VHT80",
            "test_slow_ping_rtt_ch149_VHT80", "test_ping_range_ch153_VHT20",
            "test_ping_range_ch157_VHT20", "test_ping_range_ch157_VHT40",
            "test_ping_range_ch161_VHT20")

    def setup_class(self):
        self.client_dut = self.android_devices[-1]
        req_params = [
            "ping_test_params", "testbed_params", "main_network",
            "RetailAccessPoints"
        ]
        opt_params = ["golden_files_list"]
        self.unpack_userparams(req_params, opt_params)
        self.test_params = self.ping_test_params
        self.num_atten = self.attenuators[0].instrument.num_atten
        # iperf server doubles as ping server to reduce config parameters
        self.iperf_server = self.iperf_servers[0]
        self.access_points = retail_ap.create(self.RetailAccessPoints)
        self.access_point = self.access_points[0]
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        self.log_path = os.path.join(logging.log_path, "results")
        utils.create_dir(self.log_path)
        if not hasattr(self, "golden_files_list"):
            self.golden_files_list = [
                os.path.join(self.testbed_params["golden_results_path"],
                             file) for file in os.listdir(
                                 self.testbed_params["golden_results_path"])
            ]
        self.testclass_results = []

        # Turn WiFi ON
        for dev in self.android_devices:
            wutils.wifi_toggle_state(dev, True)

    def pass_fail_check_ping_rtt(self, ping_range_result):
        """Check the test result and decide if it passed or failed.

        The function computes RTT statistics and fails any tests in which the
        tail of the ping latency results exceeds the threshold defined in the
        configuration file.

        Args:
            ping_range_result: dict containing ping results and other meta data
        """
        ignored_fraction = self.test_params[
            "rtt_ignored_interval"] / self.test_params["rtt_ping_duration"]
        sorted_rtt = [
            sorted(x["rtt"][round(ignored_fraction * len(x["rtt"])):])
            for x in ping_range_result["ping_results"]
        ]
        mean_rtt = [statistics.mean(x) for x in sorted_rtt]
        std_rtt = [statistics.stdev(x) for x in sorted_rtt]
        rtt_at_test_percentile = [
            x[int(
                len(x) *
                ((100 - self.test_params["rtt_test_percentile"]) / 100))]
            for x in sorted_rtt
        ]
        # Set blackbox metric
        self.ping_rtt_metric.metric_value = max(rtt_at_test_percentile)
        # Evaluate test pass/fail
        test_failed = False
        for idx, rtt in enumerate(rtt_at_test_percentile):
            if rtt > self.test_params["rtt_threshold"] * 1000:
                test_failed = True
                self.log.info(
                    "RTT Failed. Test %ile RTT = {}ms. Mean = {}ms. Stdev = {}".
                    format(rtt, mean_rtt[idx], std_rtt[idx]))
        if test_failed:
            asserts.fail("RTT above threshold")
        else:
            asserts.explicit_pass(
                "Test Passed. RTTs at test percentile = {}".format(
                    rtt_at_test_percentile))

    def pass_fail_check_ping_range(self, ping_range_result):
        """Check the test result and decide if it passed or failed.

        Checks whether the attenuation at which ping packet losses begin to
        exceed the threshold matches the range derived from golden
        rate-vs-range result files. The test fails is ping range is
        range_gap_threshold worse than RvR range.

        Args:
            ping_range_result: dict containing ping results and meta data
        """
        try:
            rvr_range = self.get_range_from_rvr()
        except:
            rvr_range = float("nan")

        ping_loss_over_att = [
            x["packet_loss_percentage"]
            for x in ping_range_result["ping_results"]
        ]
        ping_loss_above_threshold = [
            int(x < self.test_params["range_ping_loss_threshold"])
            for x in ping_loss_over_att
        ]
        attenuation_at_range = self.atten_range[ping_loss_above_threshold.index(
            0) - 1] + ping_range_result["fixed_attenuation"]
        # Set Blackbox metric
        self.ping_range_metric.metric_value = attenuation_at_range
        # Evaluate test pass/fail
        if attenuation_at_range - rvr_range < -self.test_params["range_gap_threshold"]:
            asserts.fail(
                "Attenuation at range is {}dB. Golden range is {}dB".format(
                    attenuation_at_range, rvr_range))
        else:
            asserts.explicit_pass(
                "Attenuation at range is {}dB. Golden range is {}dB".format(
                    attenuation_at_range, rvr_range))

    def post_process_ping_results(self, ping_range_result):
        """Saves and plots ping results.

        Args:
            ping_range_result: dict containing ping results and metadata
        """
        results_file_path = "{}/{}.json".format(self.log_path,
                                                self.current_test_name)
        with open(results_file_path, 'w') as results_file:
            json.dump(ping_range_result, results_file, indent=4)

        x_data = [
            list(range(len(x["rtt"])))
            for x in ping_range_result["ping_results"] if len(x["rtt"]) > 1
        ]
        rtt_data = [
            x["rtt"] for x in ping_range_result["ping_results"]
            if len(x["rtt"]) > 1
        ]
        #legend = ["Round Trip Time" for x in ping_range_result["ping_results"]]
        legend = [
            "RTT @ {}dB".format(att)
            for att in ping_range_result["attenuation"]
        ]

        data_sets = [x_data, rtt_data]
        fig_property = {
            "title": self.current_test_name,
            "x_label": 'Sample Index',
            "y_label": 'Round Trip Time (ms)',
            "linewidth": 3,
            "markersize": 0
        }
        output_file_path = "{}/{}.html".format(self.log_path,
                                               self.current_test_name)
        wputils.bokeh_plot(
            data_sets,
            legend,
            fig_property,
            shaded_region=None,
            output_file_path=output_file_path)

    def get_range_from_rvr(self):
        """Function gets range from RvR golden results

        The function fetches the attenuation at which the RvR throughput goes
        to zero.

        Returns:
            range: range derived from looking at rvr curves
        """
        # Fetch the golden RvR results
        test_name = self.current_test_name
        rvr_golden_file_name = "test_rvr_TCP_DL_" + "_".join(
            test_name.split("_")[3:])
        golden_path = [
            file_name for file_name in self.golden_files_list
            if rvr_golden_file_name in file_name
        ]
        with open(golden_path[0], 'r') as golden_file:
            golden_results = json.load(golden_file)
        # Get 0 Mbps attenuation and backoff by low_rssi_backoff_from_range
        atten_idx = golden_results["throughput_receive"].index(0)
        rvr_range = golden_results["attenuation"][atten_idx -
                                                  1] + golden_results["fixed_attenuation"]
        return rvr_range

    def get_ping_stats(self, ping_from_dut, ping_duration, ping_interval,
                       ping_size):
        """Run ping to or from the DUT.

        The function computes either pings the DUT or pings a remote ip from
        DUT.

        Args:
            ping_from_dut: boolean set to true if pinging from the DUT
            ping_duration: timeout to set on the the ping process (in seconds)
            ping_interval: time between pings (in seconds)
            ping_size: size of ping packet payload
        Returns:
            ping_result: dict containing ping results and other meta data
        """
        ping_cmd = "ping -w {} -i {} -s {}".format(
            ping_duration,
            ping_interval,
            ping_size,
        )
        if ping_from_dut:
            ping_cmd = "{} {}".format(
                ping_cmd, self.testbed_params["outgoing_ping_address"])
            ping_output = self.client_dut.adb.shell(
                ping_cmd,
                timeout=ping_duration + self.TEST_TIMEOUT,
                ignore_status=True)
        else:
            ping_cmd = "sudo {} {}".format(ping_cmd, self.dut_ip)
            ping_output = self.iperf_server.ssh_session.run(
                ping_cmd, ignore_status=True).stdout
        ping_output = ping_output.splitlines()

        if len(ping_output) == 1:
            ping_result = {"connected": 0}
        else:
            packet_loss_line = [line for line in ping_output if "loss" in line]
            packet_loss_percentage = int(
                packet_loss_line[0].split("%")[0].split(" ")[-1])
            if packet_loss_percentage == 100:
                rtt = [float("nan")]
            else:
                rtt = [
                    line.split("time=")[1] for line in ping_output
                    if "time=" in line
                ]
                rtt = [float(line.split(" ")[0]) for line in rtt]
            ping_result = {
                "connected": 1,
                "rtt": rtt,
                "packet_loss_percentage": packet_loss_percentage
            }
        return ping_result

    def ping_test(self, channel, mode, atten_levels, ping_duration,
                  ping_interval, ping_size):
        """Main function to test ping.

        The function sets up the AP in the correct channel and mode
        configuration and calls get_ping_stats while sweeping attenuation

        Args:
            channel: Specifies AP's channel
            mode: Specifies AP's bandwidth/mode (11g, VHT20, VHT40, VHT80)
            atten_levels: array of attenuation levels to run ping test at
            ping_duration: timeout to set on the the ping process (in seconds)
            ping_interval: time between pings (in seconds)
            ping_size: size of ping packet payload
        Returns:
            test_result: dict containing ping results and other meta data
        """
        band = self.access_point.band_lookup_by_channel(channel)
        if "2G" in band:
            frequency = wutils.WifiEnums.channel_2G_to_freq[channel]
        else:
            frequency = wutils.WifiEnums.channel_5G_to_freq[channel]
        if frequency in wutils.WifiEnums.DFS_5G_FREQUENCIES:
            self.access_point.set_region(self.testbed_params["DFS_region"])
        else:
            self.access_point.set_region(self.testbed_params["default_region"])
        self.access_point.set_channel(band, channel)
        self.access_point.set_bandwidth(band, mode)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))

        # Set attenuator to 0 dB
        for atten in atten_levels:
            for attenuator in self.attenuators:
                attenuator.set_atten(0)
        # Resest, configure, and connect DUT
        wutils.reset_wifi(self.client_dut)
        self.client_dut.droid.wifiSetCountryCode(
            self.test_params["country_code"])
        self.main_network[band]["channel"] = channel
        wutils.wifi_connect(
            self.client_dut, self.main_network[band], num_of_tries=5)
        self.dut_ip = self.client_dut.droid.connectivityGetIPv4Addresses(
            'wlan0')[0]
        time.sleep(self.MED_SLEEP)

        test_result = {"ping_results": []}
        test_result["test_name"] = self.current_test_name
        test_result["ap_config"] = self.access_point.ap_settings.copy()
        test_result["attenuation"] = atten_levels
        test_result["fixed_attenuation"] = self.testbed_params[
            "fixed_attenuation"][str(channel)]
        for atten in atten_levels:
            for attenuator in self.attenuators:
                attenuator.set_atten(atten)
            time.sleep(self.SHORT_SLEEP)
            current_ping_stats = self.get_ping_stats(0, ping_duration,
                                                     ping_interval, ping_size)
            if current_ping_stats["connected"]:
                self.log.info(
                    "Attenuation = {0}dB Packet Loss Rate = {1}%. Avg Ping RTT = {2:.2f}ms".
                    format(atten, current_ping_stats["packet_loss_percentage"],
                           statistics.mean(current_ping_stats["rtt"])))
            else:
                self.log.info(
                    "Attenuation = {}dB. Disconnected.".format(atten))
            test_result["ping_results"].append(current_ping_stats)
        return test_result

    def _test_ping_rtt(self):
        """ Function that gets called for each RTT test case

        The function gets called in each RTT test case. The function customizes
        the RTT test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        self.channel = int(test_params[4][2:])
        self.mode = test_params[5]
        self.atten_range = self.test_params["rtt_test_attenuation"]
        ping_range_result = self.ping_test(
            self.channel, self.mode, self.atten_range,
            self.test_params["rtt_ping_duration"],
            self.test_params["rtt_ping_interval"][test_params[1]],
            self.test_params["ping_size"])
        self.post_process_ping_results(ping_range_result)
        self.pass_fail_check_ping_rtt(ping_range_result)

    def _test_ping_range(self):
        """ Function that gets called for each range test case

        The function gets called in each range test case. It customizes the
        range test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        self.channel = int(test_params[3][2:])
        self.mode = test_params[4]
        num_atten_steps = int((self.test_params["range_atten_stop"] -
                               self.test_params["range_atten_start"]) /
                              self.test_params["range_atten_step"])
        self.atten_range = [
            self.test_params["range_atten_start"] +
            x * self.test_params["range_atten_step"]
            for x in range(0, num_atten_steps)
        ]
        ping_range_result = self.ping_test(
            self.channel, self.mode, self.atten_range,
            self.test_params["range_ping_duration"],
            self.test_params["range_ping_interval"],
            self.test_params["ping_size"])
        self.post_process_ping_results(ping_range_result)
        self.pass_fail_check_ping_range(ping_range_result)

    def test_ping_range_ch1_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch6_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch11_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch36_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch36_VHT40(self):
        self._test_ping_range()

    def test_ping_range_ch36_VHT80(self):
        self._test_ping_range()

    def test_ping_range_ch40_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch44_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch44_VHT40(self):
        self._test_ping_range()

    def test_ping_range_ch48_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch149_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch149_VHT40(self):
        self._test_ping_range()

    def test_ping_range_ch149_VHT80(self):
        self._test_ping_range()

    def test_ping_range_ch153_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch157_VHT20(self):
        self._test_ping_range()

    def test_ping_range_ch157_VHT40(self):
        self._test_ping_range()

    def test_ping_range_ch161_VHT20(self):
        self._test_ping_range()

    def test_fast_ping_rtt_ch1_VHT20(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch1_VHT20(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch36_VHT20(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch36_VHT20(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch36_VHT40(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch36_VHT40(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch36_VHT80(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch36_VHT80(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch149_VHT20(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch149_VHT20(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch149_VHT40(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch149_VHT40(self):
        self._test_ping_rtt()

    def test_fast_ping_rtt_ch149_VHT80(self):
        self._test_ping_rtt()

    def test_slow_ping_rtt_ch149_VHT80(self):
        self._test_ping_rtt()
