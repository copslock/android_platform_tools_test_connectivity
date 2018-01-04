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
import math
import os
import time
from acts import asserts
from acts import base_test
from acts import utils
from acts.controllers import iperf_server as ipf
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils

TEST_TIMEOUT = 10


class WifiThroughputStabilityTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):
        self.dut = self.android_devices[0]
        req_params = ["test_params", "main_network"]
        opt_params = ["RetailAccessPoints"]
        self.unpack_userparams(req_params, opt_params)
        self.num_atten = self.attenuators[0].instrument.num_atten
        self.iperf_server = self.iperf_servers[0]
        self.access_points = retail_ap.create(self.RetailAccessPoints)
        self.access_point = self.access_points[0]
        self.log_path = os.path.join(logging.log_path, "test_results")
        utils.create_dir(self.log_path)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))

    def teardown_test(self):
        self.iperf_server.stop()

    def pass_fail_check(self, test_result_dict):
        """Check the test result and decide if it passed or failed.

        Checks the throughput stability test's PASS/FAIL criteria based on
        minimum instantaneous throughput, and standard deviation.

        Args:
            test_result_dict: dict containing attenuation, throughput and other
            meta data
        """
        #TODO(@oelayach): Check throughput vs RvR golden file
        min_throughput_check = (
            (test_result_dict["iperf_results"]["min_throughput"] /
             test_result_dict["iperf_results"]["avg_throughput"]) *
            100) > self.test_params["min_throughput_threshold"]
        std_deviation_check = (
            (test_result_dict["iperf_results"]["std_deviation"] /
             test_result_dict["iperf_results"]["avg_throughput"]) *
            100) < self.test_params["std_deviation_threshold"]

        if min_throughput_check and std_deviation_check:
            asserts.explicit_pass(
                "Measurement finished for %s." % self.current_test_name)
        asserts.fail(
            "Throughput at {}dB attenuation is unstable. "
            "Average throughput is {} Mbps with a standard deviation of "
            "{} Mbps and dips down to {} Mbps.".format(
                self.atten_level,
                test_result_dict["iperf_results"]["avg_throughput"],
                test_result_dict["iperf_results"]["std_deviation"],
                test_result_dict["iperf_results"]["min_throughput"]))

    def post_process_results(self, test_result):
        """Extracts results and saves plots and JSON formatted results.

        Args:
            test_result: dict containing attenuation, iPerfResult object and
            other meta data
        Returns:
            test_result_dict: dict containing post-processed results including
            avg throughput, other metrics, and other meta data
        """
        # Save output as text file
        test_name = self.current_test_name
        results_file_path = "{}/{}.txt".format(self.log_path,
                                               self.current_test_name)
        test_result_dict = {}
        test_result_dict["ap_settings"] = test_result["ap_settings"].copy()
        test_result_dict["attenuation"] = self.atten_level
        instantaneous_rates_Mbps = [
            rate * 8
            for rate in test_result["iperf_result"].instantaneous_rates[
                self.test_params["iperf_ignored_interval"]:-1]
        ]
        test_result_dict["iperf_results"] = {
            "instantaneous_rates":
            instantaneous_rates_Mbps,
            "avg_throughput":
            math.fsum(instantaneous_rates_Mbps) /
            len(instantaneous_rates_Mbps),
            "std_deviation":
            test_result["iperf_result"].get_std_deviation(
                self.test_params["iperf_ignored_interval"]) * 8,
            "min_throughput":
            min(instantaneous_rates_Mbps)
        }
        with open(results_file_path, 'w') as results_file:
            json.dump(test_result_dict, results_file)
        # Plot and save
        legends = self.current_test_name
        x_label = 'Time (s)'
        y_label = 'Throughput (Mbps)'
        time_data = list(range(0, len(instantaneous_rates_Mbps)))
        data_sets = [[time_data], [instantaneous_rates_Mbps]]
        fig_property = {
            "title": test_name,
            "x_label": x_label,
            "y_label": y_label,
            "linewidth": 3,
            "markersize": 10
        }
        output_file_path = "{}/{}.html".format(self.log_path, test_name)
        wputils.bokeh_plot(data_sets, legends, fig_property, output_file_path)
        return test_result_dict

    def throughput_stability_test_func(self, channel, mode):
        """Main function to test throughput stability.

        The function sets up the AP in the correct channel and mode
        configuration and runs an iperf test to measure throughput.

        Args:
            channel: Specifies AP's channel
            mode: Specifies AP's bandwidth/mode (11g, VHT20, VHT40, VHT80)
        Returns:
            test_result: dict containing test result and meta data
        """
        #Initialize RvR test parameters
        test_result = {}
        # Configure AP
        band = self.access_point.band_lookup_by_channel(channel)
        self.access_point.set_channel(band, channel)
        self.access_point.set_bandwidth(band, mode)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        # Set attenuator to test level
        self.log.info("Setting attenuation to {} dB".format(self.atten_level))
        [
            self.attenuators[i].set_atten(self.atten_level)
            for i in range(self.num_atten)
        ]
        # Connect DUT to Network
        self.main_network[band]["channel"] = channel
        wutils.wifi_connect(self.dut, self.main_network[band])
        time.sleep(5)
        # Run test and log result
        # Start iperf session
        self.log.info("Starting iperf test.")
        self.iperf_server.start(tag=str(self.atten_level))
        try:
            client_status, client_output = self.dut.run_iperf_client(
                self.test_params["iperf_server_address"],
                self.iperf_args,
                timeout=self.test_params["iperf_duration"] + TEST_TIMEOUT)
            client_output_path = os.path.join(
                self.iperf_server.log_path,
                "iperf_client_output_{}".format(self.current_test_name))
            with open(client_output_path, 'w') as out_file:
                out_file.write("\n".join(client_output))
        except:
            self.log.warning("TimeoutError: Iperf measurement timed out.")
        self.iperf_server.stop()
        # Set attenuator to 0 dB
        [self.attenuators[i].set_atten(0) for i in range(self.num_atten)]
        # Parse and log result
        if self.use_client_output:
            iperf_file = client_output_path
        else:
            iperf_file = self.iperf_server.log_files[-1]
        try:
            iperf_result = ipf.IPerfResult(iperf_file)
        except:
            self.log.warning("ValueError: Cannot get iperf result.")
            iperf_result = None
        test_result["ap_settings"] = self.access_point.ap_settings.copy()
        test_result["attenuation"] = self.atten_level
        test_result["iperf_result"] = iperf_result
        return test_result

    def _test_throughput_stability(self):
        """ Function that gets called for each test case

        The function gets called in each test case. The function customizes
        the test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        channel = int(test_params[6][2:])
        mode = test_params[7]
        #TODO(@oelayach): Consider fetching test attenuation from golden file
        if test_params[3] == "high":
            self.atten_level = self.test_params["atten_high_throughput"]
        else:
            self.atten_level = self.test_params["atten_low_throughput"]
        self.iperf_args = '-i 1 -t {} -J'.format(
            self.test_params["iperf_duration"])
        if test_params[4] == "UDP":
            self.iperf_args = self.iperf_args + "-u -b {}".format(
                self.test_params["UDP_rates"][mode])
        if test_params[5] == "DL":
            self.iperf_args = self.iperf_args + ' -R'
            self.use_client_output = True
        else:
            self.use_client_output = False
        test_result = self.throughput_stability_test_func(channel, mode)
        test_result_postprocessed = self.post_process_results(test_result)
        self.pass_fail_check(test_result_postprocessed)

    #Test cases
    def test_tput_stability_high_TCP_DL_ch1_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_TCP_UL_ch1_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_low_TCP_DL_ch1_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_low_TCP_UL_ch1_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_TCP_DL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_TCP_UL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_low_TCP_DL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_low_TCP_UL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_DL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_UL_ch36_VHT20(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_DL_ch36_VHT40(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_UL_ch36_VHT40(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_DL_ch36_VHT80(self):
        self._test_throughput_stability()

    def test_tput_stability_high_UDP_UL_ch36_VHT80(self):
        self._test_throughput_stability()
