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

import collections
import json
import logging
import math
import os
from acts import asserts
from acts import base_test
from acts import utils
from acts.controllers import iperf_server as ipf
from acts.controllers.utils_lib import ssh
from acts.metrics.loggers.blackbox import BlackboxMetricLogger
from acts.test_utils.wifi import wifi_performance_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils


class WifiRvrTest(base_test.BaseTestClass):
    """Class to test WiFi rate versus range.

    This class implements WiFi rate versus range tests on single AP single STA
    links. The class setups up the AP in the desired configurations, configures
    and connects the phone to the AP, and runs iperf throughput test while
    sweeping attenuation. For an example config file to run this test class see
    example_connectivity_performance_ap_sta.json.
    """

    TEST_TIMEOUT = 5
    SHORT_SLEEP = 1
    RSSI_POLL_INTERVAL = 1
    MAX_CONSECUTIVE_ZEROS = 3

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.failure_count_metric = BlackboxMetricLogger.for_test_case(
            metric_name="failure_count")

    def setup_class(self):
        """Initializes common test hardware and parameters.

        This function initializes hardwares and compiles parameters that are
        common to all tests in this class.
        """
        self.client_dut = self.android_devices[-1]
        req_params = [
            "RetailAccessPoints", "rvr_test_params", "testbed_params",
            "RemoteServer"
        ]
        opt_params = ["main_network", "golden_files_list"]
        self.unpack_userparams(req_params, opt_params)
        self.testclass_params = self.rvr_test_params
        self.num_atten = self.attenuators[0].instrument.num_atten
        self.iperf_server = self.iperf_servers[0]
        self.remote_server = ssh.connection.SshConnection(
            ssh.settings.from_config(self.RemoteServer[0]["ssh_config"]))
        self.iperf_client = self.iperf_clients[0]
        self.access_points = retail_ap.create(self.RetailAccessPoints)
        self.access_point = self.access_points[0]
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        self.log_path = os.path.join(logging.log_path, "results")
        utils.create_dir(self.log_path)
        if not hasattr(self, "golden_files_list"):
            self.golden_files_list = [
                os.path.join(self.testbed_params["golden_results_path"], file)
                for file in os.listdir(
                    self.testbed_params["golden_results_path"])
            ]
        self.testclass_results = []

        # Turn WiFi ON
        for dev in self.android_devices:
            wutils.wifi_toggle_state(dev, True)

    def teardown_test(self):
        self.iperf_server.stop()

    def teardown_class(self):
        # Turn WiFi OFF
        for dev in self.android_devices:
            wutils.wifi_toggle_state(dev, False)
        self.process_testclass_results()

    def process_testclass_results(self):
        """Saves plot with all test results to enable comparison."""
        # Plot and save all results
        plots = collections.OrderedDict()
        for result in self.testclass_results:
            testcase_params = self.parse_test_params(result["test_name"])
            plot_id = (testcase_params["channel"], testcase_params["mode"])
            if plot_id not in plots:
                plots[plot_id] = wputils.BokehFigure(
                    title=result["test_name"],
                    x_label="Attenuation (dB)",
                    primary_y="Throughput (Mbps)")
            total_attenuation = [
                att + result["fixed_attenuation"]
                for att in result["attenuation"]
            ]
            plots[plot_id].add_line(
                total_attenuation,
                result["throughput_receive"],
                result["test_name"],
                marker="circle")
        figure_list = []
        for plot_id, plot in plots.items():
            plot.generate_figure()
            figure_list.append(plot)
        output_file_path = os.path.join(self.log_path, "results.html")
        wputils.BokehFigure.save_figures(figure_list, output_file_path)

    def pass_fail_check(self, rvr_result):
        """Check the test result and decide if it passed or failed.

        Checks the RvR test result and compares to a throughput limites for
        the same configuration. The pass/fail tolerances are provided in the
        config file.

        Args:
            rvr_result: dict containing attenuation, throughput and other meta
            data
        """
        try:
            throughput_limits = self.compute_throughput_limits(rvr_result)
        except:
            asserts.fail("Test failed: Golden file not found")

        failure_count = 0
        for idx, current_throughput in enumerate(
                rvr_result["throughput_receive"]):
            if (current_throughput < throughput_limits["lower_limit"][idx]
                    or current_throughput >
                    throughput_limits["upper_limit"][idx]):
                failure_count = failure_count + 1
        self.failure_count_metric.metric_value = failure_count
        if failure_count >= self.testclass_params["failure_count_tolerance"]:
            asserts.fail("Test failed. Found {} points outside limits.".format(
                failure_count))
        asserts.explicit_pass(
            "Test passed. Found {} points outside throughput limits.".format(
                failure_count))

    def compute_throughput_limits(self, rvr_result):
        """Compute throughput limits for current test.

        Checks the RvR test result and compares to a throughput limites for
        the same configuration. The pass/fail tolerances are provided in the
        config file.

        Args:
            rvr_result: dict containing attenuation, throughput and other meta
            data
        Returns:
            throughput_limits: dict containing attenuation and throughput limit data
        """
        test_name = self.current_test_name
        golden_path = next(file_name for file_name in self.golden_files_list
                           if test_name in file_name)
        with open(golden_path, "r") as golden_file:
            golden_results = json.load(golden_file)
            golden_attenuation = [
                att + golden_results["fixed_attenuation"]
                for att in golden_results["attenuation"]
            ]
        attenuation = []
        lower_limit = []
        upper_limit = []
        for idx, current_throughput in enumerate(
                rvr_result["throughput_receive"]):
            current_att = rvr_result["attenuation"][idx] + rvr_result[
                "fixed_attenuation"]
            att_distances = [
                abs(current_att - golden_att)
                for golden_att in golden_attenuation
            ]
            sorted_distances = sorted(
                enumerate(att_distances), key=lambda x: x[1])
            closest_indeces = [dist[0] for dist in sorted_distances[0:3]]
            closest_throughputs = [
                golden_results["throughput_receive"][index]
                for index in closest_indeces
            ]
            closest_throughputs.sort()

            attenuation.append(current_att)
            lower_limit.append(
                max(
                    closest_throughputs[0] - max(
                        self.testclass_params["abs_tolerance"],
                        closest_throughputs[0] *
                        self.testclass_params["pct_tolerance"] / 100), 0))
            upper_limit.append(closest_throughputs[-1] + max(
                self.testclass_params["abs_tolerance"], closest_throughputs[-1]
                * self.testclass_params["pct_tolerance"] / 100))
        throughput_limits = {
            "attenuation": attenuation,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit
        }
        return throughput_limits

    def process_test_results(self, rvr_result):
        """Saves plots and JSON formatted results.

        Args:
            rvr_result: dict containing attenuation, throughput and other meta
            data
        """
        # Save output as text file
        test_name = self.current_test_name
        results_file_path = os.path.join(
            self.log_path, "{}.json".format(self.current_test_name))
        with open(results_file_path, "w") as results_file:
            json.dump(rvr_result, results_file, indent=4)
        # Plot and save
        figure = wputils.BokehFigure(
            title=test_name,
            x_label="Attenuation (dB)",
            primary_y="Throughput (Mbps)")
        try:
            golden_path = next(file_name
                               for file_name in self.golden_files_list
                               if test_name in file_name)
            with open(golden_path, "r") as golden_file:
                golden_results = json.load(golden_file)
            golden_attenuation = [
                att + golden_results["fixed_attenuation"]
                for att in golden_results["attenuation"]
            ]
            throughput_limits = self.compute_throughput_limits(rvr_result)
            shaded_region = {
                "x_vector": throughput_limits["attenuation"],
                "lower_limit": throughput_limits["lower_limit"],
                "upper_limit": throughput_limits["upper_limit"]
            }
            figure.add_line(
                golden_attenuation,
                golden_results["throughput_receive"],
                "Golden Results",
                color="green",
                marker="circle",
                shaded_region=shaded_region)
        except:
            self.log.warning("ValueError: Golden file not found")

        total_attenuation = [
            att + rvr_result["fixed_attenuation"]
            for att in rvr_result["attenuation"]
        ]
        # Generate graph annotatios
        hover_text = [
            "TX MCS = {0} ({1:.1f}%). RX MCS = {2} ({3:.1f}%)".format(
                curr_llstats["summary"]["common_tx_mcs"],
                curr_llstats["summary"]["common_tx_mcs_freq"] * 100,
                curr_llstats["summary"]["common_rx_mcs"],
                curr_llstats["summary"]["common_rx_mcs_freq"] * 100)
            for curr_llstats in rvr_result["llstats"]
        ]
        figure.add_line(
            total_attenuation,
            rvr_result["throughput_receive"],
            "Test Results",
            hover_text=hover_text,
            color="red",
            marker="circle")

        output_file_path = os.path.join(self.log_path,
                                        "{}.html".format(test_name))
        figure.generate_figure(output_file_path)

    def run_rvr_test(self, testcase_params):
        """Test function to run RvR.

        The function runs an RvR test in the current device/AP configuration.
        Function is called from another wrapper function that sets up the
        testbed for the RvR test

        Args:
            testcase_params: dict containing test-specific parameters
        Returns:
            rvr_result: dict containing rvr_results and meta data
        """
        battery_level = utils.get_battery_level(self.client_dut)
        if battery_level < 10 and testcase_params["traffic_direction"] == "UL":
            asserts.skip("Battery level too low. Skipping test.")
        self.log.info("Start running RvR")
        llstats_obj = wputils.LinkLayerStats(self.client_dut)
        zero_counter = 0
        throughput = []
        llstats = []
        rssi = []
        for atten in testcase_params["atten_range"]:
            # Set Attenuation
            for attenuator in self.attenuators:
                attenuator.set_atten(atten, strict=False)
            # Refresh link layer stats
            llstats_obj.update_stats()
            # Start iperf session
            self.iperf_server.start(tag=str(atten))
            rssi_future = wputils.get_connected_rssi_nb(
                self.client_dut, testcase_params["iperf_duration"] - 1, 1, 1)
            client_output_path = self.iperf_client.start(
                testcase_params["iperf_server_address"],
                testcase_params["iperf_args"], str(atten),
                testcase_params["iperf_duration"] + self.TEST_TIMEOUT)
            server_output_path = self.iperf_server.stop()
            current_rssi = rssi_future.result()["signal_poll_rssi"]["mean"]
            rssi.append(current_rssi)
            # Parse and log result
            if testcase_params["use_client_output"]:
                iperf_file = client_output_path
            else:
                iperf_file = server_output_path
            try:
                iperf_result = ipf.IPerfResult(iperf_file)
                curr_throughput = (math.fsum(iperf_result.instantaneous_rates[
                    self.testclass_params["iperf_ignored_interval"]:-1]) / len(
                        iperf_result.instantaneous_rates[self.testclass_params[
                            "iperf_ignored_interval"]:-1])) * 8 * (1.024**2)
            except:
                self.log.warning(
                    "ValueError: Cannot get iperf result. Setting to 0")
                curr_throughput = 0
            throughput.append(curr_throughput)
            llstats_obj.update_stats()
            curr_llstats = llstats_obj.llstats_incremental.copy()
            llstats.append(curr_llstats)
            self.log.info(
                ("Throughput at {0:.2f} dB is {1:.2f} Mbps. RSSI = {2:.2f}."
                 ).format(atten, curr_throughput, current_rssi))
            if curr_throughput == 0:
                zero_counter = zero_counter + 1
            else:
                zero_counter = 0
            if zero_counter == self.MAX_CONSECUTIVE_ZEROS:
                self.log.info(
                    "Throughput stable at 0 Mbps. Stopping test now.")
                throughput.extend(
                    [0] *
                    (len(testcase_params["atten_range"]) - len(throughput)))
                break
        for attenuator in self.attenuators:
            attenuator.set_atten(0, strict=False)
        # Compile test result and meta data
        rvr_result = collections.OrderedDict()
        rvr_result["test_name"] = self.current_test_name
        rvr_result["ap_settings"] = self.access_point.ap_settings.copy()
        rvr_result["fixed_attenuation"] = self.testbed_params[
            "fixed_attenuation"][str(testcase_params["channel"])]
        rvr_result["attenuation"] = list(testcase_params["atten_range"])
        rvr_result["rssi"] = rssi
        rvr_result["throughput_receive"] = throughput
        rvr_result["llstats"] = llstats
        return rvr_result

    def setup_ap(self, testcase_params):
        """Sets up the access point in the configuration required by the test.

        Args:
            testcase_params: dict containing AP and other test params
        """
        band = self.access_point.band_lookup_by_channel(
            testcase_params["channel"])
        if "2G" in band:
            frequency = wutils.WifiEnums.channel_2G_to_freq[
                testcase_params["channel"]]
        else:
            frequency = wutils.WifiEnums.channel_5G_to_freq[
                testcase_params["channel"]]
        if frequency in wutils.WifiEnums.DFS_5G_FREQUENCIES:
            self.access_point.set_region(self.testbed_params["DFS_region"])
        else:
            self.access_point.set_region(self.testbed_params["default_region"])
        self.access_point.set_channel(band, testcase_params["channel"])
        self.access_point.set_bandwidth(band, testcase_params["mode"])
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))

    def setup_dut(self, testcase_params):
        """Sets up the DUT in the configuration required by the test.

        Args:
            testcase_params: dict containing AP and other test params
        """
        band = self.access_point.band_lookup_by_channel(
            testcase_params["channel"])
        wutils.reset_wifi(self.client_dut)
        self.client_dut.droid.wifiSetCountryCode(
            self.testclass_params["country_code"])
        self.main_network[band]["channel"] = testcase_params["channel"]
        wutils.wifi_connect(
            self.client_dut,
            self.main_network[band],
            num_of_tries=5,
            check_connectivity=False)
        self.dut_ip = self.client_dut.droid.connectivityGetIPv4Addresses(
            "wlan0")[0]

    def setup_rvr_test(self, testcase_params):
        """Function that gets devices ready for the test.

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Configure AP
        self.setup_ap(testcase_params)
        # Set attenuator to 0 dB
        for attenuator in self.attenuators:
            attenuator.set_atten(0, strict=False)
        # Reset, configure, and connect DUT
        self.setup_dut(testcase_params)
        # Get iperf_server address
        if isinstance(self.iperf_server, ipf.IPerfServerOverAdb):
            testcase_params["iperf_server_address"] = self.dut_ip
        else:
            testcase_params[
                "iperf_server_address"] = wputils.get_server_address(
                    self.remote_server, self.dut_ip, "255.255.255.0")

    def parse_test_params(self, test_name):
        """Function that generates test params based on the test name."""
        test_name_params = test_name.split("_")
        testcase_params = collections.OrderedDict()
        testcase_params["traffic_type"] = test_name_params[2]
        testcase_params["traffic_direction"] = test_name_params[3]
        testcase_params["channel"] = int(test_name_params[4][2:])
        testcase_params["mode"] = test_name_params[5]
        num_atten_steps = int((self.testclass_params["atten_stop"] -
                               self.testclass_params["atten_start"]) /
                              self.testclass_params["atten_step"])
        testcase_params["atten_range"] = [
            self.testclass_params["atten_start"] +
            x * self.testclass_params["atten_step"]
            for x in range(0, num_atten_steps)
        ]
        testcase_params["iperf_args"] = "-i 1 -t {} -J ".format(
            self.testclass_params["iperf_duration"])
        if testcase_params["traffic_type"] == "UDP":
            testcase_params["iperf_args"] = testcase_params[
                "iperf_args"] + "-u -b {} -l 1400".format(
                    self.testclass_params["UDP_rates"][
                        testcase_params["mode"]])
        if (testcase_params["traffic_direction"] == "DL"
                and not isinstance(self.iperf_server, ipf.IPerfServerOverAdb)
            ) or (testcase_params["traffic_direction"] == "UL"
                  and isinstance(self.iperf_server, ipf.IPerfServerOverAdb)):
            testcase_params[
                "iperf_args"] = testcase_params["iperf_args"] + " -R"
            testcase_params["use_client_output"] = True
        else:
            testcase_params["use_client_output"] = False
        return testcase_params

    def _test_rvr(self):
        """ Function that gets called for each test case

        The function gets called in each rvr test case. The function customizes
        the rvr test based on the test name of the test that called it
        """
        # Compile test parameters from config and test name
        testcase_params = self.parse_test_params(self.current_test_name)
        testcase_params.update(self.testclass_params)

        # Prepare devices and run test
        self.setup_rvr_test(testcase_params)
        rvr_result = self.run_rvr_test(testcase_params)

        # Post-process results
        self.testclass_results.append(rvr_result)
        self.process_test_results(rvr_result)
        self.pass_fail_check(rvr_result)

    #Test cases
    def test_rvr_TCP_DL_ch1_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch1_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch6_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch6_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch11_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch11_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch36_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch36_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch36_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch40_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch40_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch44_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch44_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch44_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch44_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch48_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch48_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch52_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch52_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch56_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch56_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch60_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch60_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch64_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch64_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch100_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch100_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch100_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch100_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch100_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch100_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch104_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch104_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch108_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch108_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch112_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch112_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch116_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch116_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch132_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch132_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch136_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch136_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch140_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch140_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch149_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch149_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch149_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch149_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch149_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch149_VHT80(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch153_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch153_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch157_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch157_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch157_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch157_VHT40(self):
        self._test_rvr()

    def test_rvr_TCP_DL_ch161_VHT20(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch161_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch6_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch6_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch36_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch36_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch149_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch149_VHT20(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch36_VHT40(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch36_VHT40(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch36_VHT80(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch36_VHT80(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch149_VHT40(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch149_VHT40(self):
        self._test_rvr()

    def test_rvr_UDP_DL_ch149_VHT80(self):
        self._test_rvr()

    def test_rvr_UDP_UL_ch149_VHT80(self):
        self._test_rvr()


# Classes defining test suites
class WifiRvr_2GHz_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = ("test_rvr_TCP_DL_ch1_VHT20", "test_rvr_TCP_UL_ch1_VHT20",
                      "test_rvr_TCP_DL_ch6_VHT20", "test_rvr_TCP_UL_ch6_VHT20",
                      "test_rvr_TCP_DL_ch11_VHT20",
                      "test_rvr_TCP_UL_ch11_VHT20")


class WifiRvr_UNII1_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_DL_ch36_VHT20", "test_rvr_TCP_UL_ch36_VHT20",
            "test_rvr_TCP_DL_ch36_VHT40", "test_rvr_TCP_UL_ch36_VHT40",
            "test_rvr_TCP_DL_ch36_VHT80", "test_rvr_TCP_UL_ch36_VHT80",
            "test_rvr_TCP_DL_ch40_VHT20", "test_rvr_TCP_UL_ch40_VHT20",
            "test_rvr_TCP_DL_ch44_VHT20", "test_rvr_TCP_UL_ch44_VHT20",
            "test_rvr_TCP_DL_ch44_VHT40", "test_rvr_TCP_UL_ch44_VHT40",
            "test_rvr_TCP_DL_ch48_VHT20", "test_rvr_TCP_UL_ch48_VHT20")


class WifiRvr_UNII3_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_DL_ch149_VHT20", "test_rvr_TCP_UL_ch149_VHT20",
            "test_rvr_TCP_DL_ch149_VHT40", "test_rvr_TCP_UL_ch149_VHT40",
            "test_rvr_TCP_DL_ch149_VHT80", "test_rvr_TCP_UL_ch149_VHT80",
            "test_rvr_TCP_DL_ch153_VHT20", "test_rvr_TCP_UL_ch153_VHT20",
            "test_rvr_TCP_DL_ch157_VHT20", "test_rvr_TCP_UL_ch157_VHT20",
            "test_rvr_TCP_DL_ch157_VHT40", "test_rvr_TCP_UL_ch157_VHT40",
            "test_rvr_TCP_DL_ch161_VHT20", "test_rvr_TCP_UL_ch161_VHT20")


class WifiRvr_SampleDFS_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_DL_ch64_VHT20", "test_rvr_TCP_UL_ch64_VHT20",
            "test_rvr_TCP_DL_ch100_VHT20", "test_rvr_TCP_UL_ch100_VHT20",
            "test_rvr_TCP_DL_ch100_VHT40", "test_rvr_TCP_UL_ch100_VHT40",
            "test_rvr_TCP_DL_ch100_VHT80", "test_rvr_TCP_UL_ch100_VHT80",
            "test_rvr_TCP_DL_ch116_VHT20", "test_rvr_TCP_UL_ch116_VHT20",
            "test_rvr_TCP_DL_ch132_VHT20", "test_rvr_TCP_UL_ch132_VHT20",
            "test_rvr_TCP_DL_ch140_VHT20", "test_rvr_TCP_UL_ch140_VHT20")


class WifiRvr_SampleUDP_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_UDP_DL_ch6_VHT20", "test_rvr_UDP_UL_ch6_VHT20",
            "test_rvr_UDP_DL_ch36_VHT20", "test_rvr_UDP_UL_ch36_VHT20",
            "test_rvr_UDP_DL_ch36_VHT40", "test_rvr_UDP_UL_ch36_VHT40",
            "test_rvr_UDP_DL_ch36_VHT80", "test_rvr_UDP_UL_ch36_VHT80",
            "test_rvr_UDP_DL_ch149_VHT20", "test_rvr_UDP_UL_ch149_VHT20",
            "test_rvr_UDP_DL_ch149_VHT40", "test_rvr_UDP_UL_ch149_VHT40",
            "test_rvr_UDP_DL_ch149_VHT80", "test_rvr_UDP_UL_ch149_VHT80")


class WifiRvr_TCP_All_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_DL_ch1_VHT20", "test_rvr_TCP_UL_ch1_VHT20",
            "test_rvr_TCP_DL_ch6_VHT20", "test_rvr_TCP_UL_ch6_VHT20",
            "test_rvr_TCP_DL_ch11_VHT20", "test_rvr_TCP_UL_ch11_VHT20",
            "test_rvr_TCP_DL_ch36_VHT20", "test_rvr_TCP_UL_ch36_VHT20",
            "test_rvr_TCP_DL_ch36_VHT40", "test_rvr_TCP_UL_ch36_VHT40",
            "test_rvr_TCP_DL_ch36_VHT80", "test_rvr_TCP_UL_ch36_VHT80",
            "test_rvr_TCP_DL_ch40_VHT20", "test_rvr_TCP_UL_ch40_VHT20",
            "test_rvr_TCP_DL_ch44_VHT20", "test_rvr_TCP_UL_ch44_VHT20",
            "test_rvr_TCP_DL_ch44_VHT40", "test_rvr_TCP_UL_ch44_VHT40",
            "test_rvr_TCP_DL_ch48_VHT20", "test_rvr_TCP_UL_ch48_VHT20",
            "test_rvr_TCP_DL_ch149_VHT20", "test_rvr_TCP_UL_ch149_VHT20",
            "test_rvr_TCP_DL_ch149_VHT40", "test_rvr_TCP_UL_ch149_VHT40",
            "test_rvr_TCP_DL_ch149_VHT80", "test_rvr_TCP_UL_ch149_VHT80",
            "test_rvr_TCP_DL_ch153_VHT20", "test_rvr_TCP_UL_ch153_VHT20",
            "test_rvr_TCP_DL_ch157_VHT20", "test_rvr_TCP_UL_ch157_VHT20",
            "test_rvr_TCP_DL_ch157_VHT40", "test_rvr_TCP_UL_ch157_VHT40",
            "test_rvr_TCP_DL_ch161_VHT20", "test_rvr_TCP_UL_ch161_VHT20")


class WifiRvr_TCP_Downlink_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_DL_ch1_VHT20", "test_rvr_TCP_DL_ch6_VHT20",
            "test_rvr_TCP_DL_ch11_VHT20", "test_rvr_TCP_DL_ch36_VHT20",
            "test_rvr_TCP_DL_ch36_VHT40", "test_rvr_TCP_DL_ch36_VHT80",
            "test_rvr_TCP_DL_ch40_VHT20", "test_rvr_TCP_DL_ch44_VHT20",
            "test_rvr_TCP_DL_ch44_VHT40", "test_rvr_TCP_DL_ch48_VHT20",
            "test_rvr_TCP_DL_ch149_VHT20", "test_rvr_TCP_DL_ch149_VHT40",
            "test_rvr_TCP_DL_ch149_VHT80", "test_rvr_TCP_DL_ch153_VHT20",
            "test_rvr_TCP_DL_ch157_VHT20", "test_rvr_TCP_DL_ch157_VHT40",
            "test_rvr_TCP_DL_ch161_VHT20")


class WifiRvr_TCP_Uplink_Test(WifiRvrTest):
    def __init__(self, controllers):
        super().__init__(controllers)
        self.tests = (
            "test_rvr_TCP_UL_ch1_VHT20", "test_rvr_TCP_UL_ch6_VHT20",
            "test_rvr_TCP_UL_ch11_VHT20", "test_rvr_TCP_UL_ch36_VHT20",
            "test_rvr_TCP_UL_ch36_VHT40", "test_rvr_TCP_UL_ch36_VHT80",
            "test_rvr_TCP_UL_ch40_VHT20", "test_rvr_TCP_UL_ch44_VHT20",
            "test_rvr_TCP_UL_ch44_VHT40", "test_rvr_TCP_UL_ch48_VHT20",
            "test_rvr_TCP_UL_ch149_VHT20", "test_rvr_TCP_UL_ch149_VHT40",
            "test_rvr_TCP_UL_ch149_VHT80", "test_rvr_TCP_UL_ch153_VHT20",
            "test_rvr_TCP_UL_ch157_VHT20", "test_rvr_TCP_UL_ch157_VHT40",
            "test_rvr_TCP_UL_ch161_VHT20")
