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
import time
from acts import asserts
from acts import base_test
from acts import utils
from acts.controllers import iperf_server as ipf
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils

TEST_TIMEOUT = 10
EPSILON = 1e-6


class WifiRvrTest(base_test.BaseTestClass):
    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):
        self.dut = self.android_devices[0]
        req_params = ["rvrtest_params", "main_network"]
        opt_params = ["RetailAccessPoints"]
        self.unpack_userparams(req_params, opt_params)
        self.num_atten = self.attenuators[0].instrument.num_atten
        self.iperf_server = self.iperf_servers[0]
        self.access_points = retail_ap.create(self.RetailAccessPoints)
        self.access_point = self.access_points[0]
        self.log_path = os.path.join(logging.log_path, "rvr_results")
        utils.create_dir(self.log_path)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))

    def teardown_test(self):
        self.iperf_server.stop()

    def pass_fail_check(self, rvr_result):
        """Check the test result and decide if it passed or failed.

        Checks the RvR test result and compares to a golden file of results for
        the same configuration. The pass/fail tolerances are provided in the
        config file. Currently, the test fails if any a single point is out of
        range of the corresponding point in the golden file.

        Args:
            rvr_result: dict containing attenuation, throughput and other meta
            data
        """
        test_name = self.current_test_name
        gldn_path = os.path.join(self.rvrtest_params["golden_results_path"],
                                 "{}.json".format(test_name))
        with open(gldn_path, 'r') as gldn_file:
            gldn_results = json.load(gldn_file)
        for idx, current_throughput in enumerate(
                rvr_result["throughput_receive"]):
            current_att = rvr_result["attenuation"][idx]
            gldn_att_index = gldn_results["attenuation"].index(current_att)
            gldn_throughput = gldn_results["throughput_receive"][
                gldn_att_index]
            abs_difference = abs(current_throughput - gldn_throughput)
            pct_difference = (abs_difference /
                              (gldn_throughput + EPSILON)) * 100
            if (abs_difference > self.rvrtest_params["abs_tolerance"]
                    and pct_difference > self.rvrtest_params["pct_tolerance"]):
                asserts.fail(
                    "Throughput at {}dB attenuation is beyond limits. "
                    "Throughput is {} Mbps. Expected {} Mbps.".format(
                        current_att, current_throughput, gldn_throughput))
        asserts.explicit_pass("Measurement finished for %s." % test_name)

    def post_process_results(self, rvr_result):
        """Saves plots and JSON formatted results.

        Args:
            rvr_result: dict containing attenuation, throughput and other meta
            data
        """
        # Save output as text file
        test_name = self.current_test_name
        results_file_path = "{}/{}.txt".format(self.log_path,
                                               self.current_test_name)
        with open(results_file_path, 'w') as results_file:
            json.dump(rvr_result, results_file)
        # Plot and save
        legends = self.current_test_name
        x_label = 'Attenuation (dB)'
        y_label = 'Throughput (Mbps)'
        data_sets = [[rvr_result["attenuation"]],
                     [rvr_result["throughput_receive"]]]
        fig_property = {
            "title": test_name,
            "x_label": x_label,
            "y_label": y_label,
            "linewidth": 3,
            "markersize": 10
        }
        output_file_path = "{}/{}.html".format(self.log_path, test_name)
        wputils.bokeh_plot(data_sets, legends, fig_property, output_file_path)

    def rvr_test(self):
        """Test function to run RvR.

        The function runs an RvR test in the current device/AP configuration.
        Function is called from another wrapper function that sets up the
        testbed for the RvR test

        Returns:
            rvr_result: dict containing rvr_results and meta data
        """
        self.log.info("Start running RvR")
        rvr_result = []
        for atten in self.rvr_atten_range:
            # Set Attenuation
            self.log.info("Setting attenuation to {} dB".format(atten))
            [
                self.attenuators[i].set_atten(atten)
                for i in range(self.num_atten)
            ]
            # Start iperf session
            self.iperf_server.start(tag=str(atten))
            try:
                self.dut.run_iperf_client(
                    self.rvrtest_params["iperf_server_address"],
                    self.iperf_args,
                    timeout=self.rvrtest_params["iperf_duration"] +
                    TEST_TIMEOUT)
            except:
                self.log.warning("Iperf measurement timed out.")
            self.iperf_server.stop()
            # Parse and log result
            try:
                iperf_result = ipf.IPerfResult(self.iperf_server.log_files[-1])
                curr_throughput = iperf_result.avg_receive_rate * 8
            except:
                self.log.warning(
                    "Cannot get iperf result, likely due to timeout. Setting to 0"
                )
                curr_throughput = 0
            rvr_result.append(curr_throughput)
            self.log.info("Throughput at {0:d} dB is {1:.2f} Mbps".format(
                atten, curr_throughput))
        [self.attenuators[i].set_atten(0) for i in range(self.num_atten)]
        return rvr_result

    def rvr_test_func(self, channel, mode):
        """Main function to test RvR.

        The function sets up the AP in the correct channel and mode
        configuration and called run_rvr to sweep attenuation and measure
        throughput

        Args:
            channel: Specifies AP's channel
            mode: Specifies AP's bandwidth/mode (11g, VHT20, VHT40, VHT80)
        Returns:
            rvr_result: dict containing rvr_results and meta data
        """
        #Initialize RvR test parameters
        self.rvr_atten_range = range(self.rvrtest_params["rvr_atten_start"],
                                     self.rvrtest_params["rvr_atten_stop"],
                                     self.rvrtest_params["rvr_atten_step"])
        rvr_result = {}
        # Configure AP
        band = self.access_point.band_lookup_by_channel(channel)
        self.access_point.set_channel(band, channel)
        self.access_point.set_bandwidth(band, mode)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        # Set attenuator to 0 dB
        [self.attenuators[i].set_atten(0) for i in range(self.num_atten)]
        # Connect DUT to Network
        self.main_network[band]["channel"] = channel
        wutils.wifi_connect(self.dut, self.main_network[band])
        time.sleep(5)
        # Run RvR and log result
        rvr_result["ap_settings"] = self.access_point.ap_settings.copy()
        rvr_result["attenuation"] = list(self.rvr_atten_range)
        rvr_result["throughput_receive"] = self.rvr_test()
        return rvr_result

    def _test_rvr(self):
        """ Function that gets called for each test case

        The function gets called in each rvr test case. The function customizes
        the rvr test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        channel = int(test_params[4][2:])
        mode = test_params[5]
        self.iperf_args = '-i 1 -t {}'.format(
            self.rvrtest_params["iperf_duration"])
        if test_params[3] == "DL":
            self.iperf_args = self.iperf_args + ' -R'
        rvr_result = self.rvr_test_func(channel, mode)
        self.post_process_results(rvr_result)
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
