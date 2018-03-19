#!/usr/bin/env python3.4
#
#   Copyright 2018 - The Android Open Source Project
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
import re
import statistics
import time
from acts import asserts
from acts import base_test
from acts import utils
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap
from acts.test_utils.wifi import wifi_test_utils as wutils

SHORT_SLEEP = 1
MED_SLEEP = 6
STATION_DUMP = "iw wlan0 station dump"
SCAN = "wpa_cli scan"
SCAN_RESULTS = "wpa_cli scan_results"
SIGNAL_POLL = "wpa_cli signal_poll"
CONST_3dB = 3.01029995664
RSSI_ERROR_VAL = float("nan")


class WifiRssiTest(base_test.BaseTestClass):
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
        self.log_path = os.path.join(logging.log_path, "results")
        utils.create_dir(self.log_path)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        self.testclass_results = []

    def teardown_test(self):
        self.iperf_server.stop()

    def pass_fail_check_rssi_stability(self, rssi_result):
        """Check the test result and decide if it passed or failed.

        Checks the RSSI test result and fails the test if the standard
        deviation of signal_poll_rssi is beyond the threshold defined in the
        config file.

        Args:
            rssi_result: dict containing attenuation, rssi, and other meta
            data. This dict is the output of self.post_process_results
        """
        # Save output as text file
        test_name = self.current_test_name
        results_file_path = "{}/{}.json".format(self.log_path,
                                                self.current_test_name)
        with open(results_file_path, 'w') as results_file:
            json.dump(rssi_result, results_file, indent=4)

        x_data = []
        y_data = []
        legends = []
        std_deviations = {
            "signal_poll_rssi": [],
            "signal_poll_avg_rssi": [],
            "chain_0_rssi": [],
            "chain_1_rssi": [],
        }
        for data_point in rssi_result["rssi_result"]:
            for key, val in data_point["connected_rssi"].items():
                if type(val) == list:
                    x_data.append([
                        x * self.test_params["polling_frequency"]
                        for x in range(len(val))
                    ])
                    y_data.append(val)
                    legends.append(key)
                    std_deviations[key].append(
                        data_point["connected_rssi"]["stdev_" + key])
        data_sets = [x_data, y_data]
        x_label = 'Time (s)'
        y_label = 'RSSI (dBm)'
        fig_property = {
            "title": test_name,
            "x_label": x_label,
            "y_label": y_label,
            "linewidth": 3,
            "markersize": 0
        }
        output_file_path = "{}/{}.html".format(self.log_path, test_name)
        wputils.bokeh_plot(
            data_sets,
            legends,
            fig_property,
            shaded_region=None,
            output_file_path=output_file_path)

        test_failed = any([
            stdev > self.test_params["stdev_tolerance"]
            for stdev in std_deviations["signal_poll_rssi"]
        ])
        if test_failed:
            asserts.fail(
                "RSSI stability failed. Standard deviations were {0} dB "
                "(limit {1}), per chain standard deviation [{2}, {3}] dB".
                format([
                    float("{:.2f}".format(x))
                    for x in std_deviations["signal_poll_rssi"]
                ], self.test_params["stdev_tolerance"], [
                    float("{:.2f}".format(x))
                    for x in std_deviations["chain_0_rssi"]
                ], [
                    float("{:.2f}".format(x))
                    for x in std_deviations["chain_1_rssi"]
                ]))
        asserts.explicit_pass(
            "RSSI stability passed. Standard deviations were {0} dB "
            "(limit {1}), per chain standard deviation [{2}, {3}] dB".format([
                float("{:.2f}".format(x))
                for x in std_deviations["signal_poll_rssi"]
            ], self.test_params["stdev_tolerance"], [
                float("{:.2f}".format(x))
                for x in std_deviations["chain_0_rssi"]
            ], [
                float("{:.2f}".format(x))
                for x in std_deviations["chain_1_rssi"]
            ]))

    def pass_fail_check_rssi_vs_attenuation(self, postprocessed_results):
        """Check the test result and decide if it passed or failed.

        Checks the RSSI test result and compares and compute its deviation from
        the predicted RSSI. This computation is done for all reported RSSI
        values. The test fails if any of the RSSI values specified in
        rssi_under_test have an average error beyond what is specified in the
        configuration file.

        Args:
            result: dict containing attenuation, rssi, and other meta
            data. This dict is the output of self.post_process_results
        """

        error_data = {
            "signal_poll_rssi": [
                postprocessed_results["mean_signal_poll_rssi"][idx] -
                postprocessed_results["predicted_rssi"][idx]
                for idx in range(len(postprocessed_results["predicted_rssi"]))
            ],
            "signal_poll_avg_rssi": [
                postprocessed_results["mean_signal_poll_avg_rssi"][idx] -
                postprocessed_results["predicted_rssi"][idx]
                for idx in range(len(postprocessed_results["predicted_rssi"]))
            ],
            "scan_rssi": [
                postprocessed_results["mean_scan_rssi"][idx] -
                postprocessed_results["predicted_rssi"][idx]
                for idx in range(len(postprocessed_results["predicted_rssi"]))
            ],
            "chain_0_rssi": [
                postprocessed_results["mean_chain_0_rssi"][idx] + CONST_3dB -
                postprocessed_results["predicted_rssi"][idx]
                for idx in range(len(postprocessed_results["predicted_rssi"]))
            ],
            "chain_1_rssi": [
                postprocessed_results["mean_chain_1_rssi"][idx] + CONST_3dB -
                postprocessed_results["predicted_rssi"][idx]
                for idx in range(len(postprocessed_results["predicted_rssi"]))
            ]
        }

        test_failed = False
        test_message = ""
        for key, val in error_data.items():
            # Compute the error metrics ignoring invalid RSSI readings
            # If all readings invalid, set error to RSSI_ERROR_VAL
            filtered_errors = [x for x in val if not math.isnan(x)]
            if filtered_errors:
                avg_error = sum([abs(x) for x in filtered_errors
                                 ]) / len(filtered_errors)
                avg_shift = sum(filtered_errors) / len(filtered_errors)
            else:
                avg_error = RSSI_ERROR_VAL
            rssi_failure = (avg_error > self.test_params["abs_tolerance"]
                            ) or math.isnan(avg_error)
            if rssi_failure and key in self.test_params["rssi_under_test"]:
                test_message = test_message + (
                    "{} failed. Average error is {:.2f} dB. "
                    "Average shift is {:.2f} dB.\n").format(
                        key, avg_error, avg_shift)
                test_failed = True
            elif rssi_failure:
                test_message = test_message + (
                    "{} failed (ignored). Average error is {:.2f} dB. "
                    "Average shift is {:.2f} dB.\n").format(
                        key, avg_error, avg_shift)
            else:
                test_message = test_message + (
                    "{} passed. Average error is {:.2f} dB. "
                    "Average shift is {:.2f} dB.\n").format(
                        key, avg_error, avg_shift)

        if test_failed:
            asserts.fail(test_message)
        asserts.explicit_pass(test_message)

    def post_process_rssi_vs_attenuation(self, rssi_result):
        """Saves plots and JSON formatted results.

        Args:
            rssi_result: dict containing attenuation, rssi and other meta
            data
        Returns:
            postprocessed_results: compiled arrays of RSSI measurements used in
            pass/fail check
        """
        # Save output as text file
        test_name = self.current_test_name
        results_file_path = "{}/{}.json".format(self.log_path,
                                                self.current_test_name)
        with open(results_file_path, 'w') as results_file:
            json.dump(rssi_result, results_file, indent=4)
        # Plot and save
        total_attenuation = [
            att + rssi_result["fixed_attenuation"]
            for att in rssi_result["attenuation"]
        ]
        # Compile results into arrays of RSSIs suitable for plotting
        postprocessed_results = {
            "total_attenuation":
            total_attenuation,
            "mean_signal_poll_rssi": [
                x["connected_rssi"]["mean_signal_poll_rssi"]
                for x in rssi_result["rssi_result"]
            ],
            "mean_signal_poll_avg_rssi": [
                x["connected_rssi"]["mean_signal_poll_avg_rssi"]
                for x in rssi_result["rssi_result"]
            ],
            "mean_scan_rssi": [
                x["scan_rssi"][rssi_result["connected_bssid"]]["avg_rssi"]
                for x in rssi_result["rssi_result"]
            ],
            "mean_chain_0_rssi": [
                x["connected_rssi"]["mean_chain_0_rssi"]
                for x in rssi_result["rssi_result"]
            ],
            "mean_chain_1_rssi": [
                x["connected_rssi"]["mean_chain_1_rssi"]
                for x in rssi_result["rssi_result"]
            ],
            "predicted_rssi":
            [rssi_result["ap_tx_power"] - att for att in total_attenuation]
        }
        data_sets = [[
            total_attenuation, total_attenuation, total_attenuation,
            total_attenuation, total_attenuation, total_attenuation
        ], [
            postprocessed_results["mean_signal_poll_rssi"],
            postprocessed_results["mean_signal_poll_avg_rssi"],
            postprocessed_results["mean_scan_rssi"],
            postprocessed_results["mean_chain_0_rssi"],
            postprocessed_results["mean_chain_1_rssi"],
            postprocessed_results["predicted_rssi"]
        ]]
        legends = [
            "Signal Poll RSSI", "Signal Poll AVG_RSSI", "Scan RSSI",
            "Chain 0 RSSI", "Chain 1 RSSI", "Predicted RSSI"
        ]
        x_label = 'Attenuation (dB)'
        y_label = 'RSSI (dBm)'
        fig_property = {
            "title": test_name,
            "x_label": x_label,
            "y_label": y_label,
            "linewidth": 3,
            "markersize": 10
        }
        output_file_path = "{}/{}.html".format(self.log_path, test_name)
        wputils.bokeh_plot(
            data_sets,
            legends,
            fig_property,
            shaded_region=None,
            output_file_path=output_file_path)
        return postprocessed_results

    def get_scan_rssi(self, tracked_bssids, num_measurements=1):
        """Gets scan RSSI for specified BSSIDs.

        Args:
            tracked_bssids: array of BSSIDs to gather RSSI data for
            num_measurements: number of scans done, and RSSIs collected
        Returns:
            scan_rssi: dict containing the measurement results as well as the
            statistics of the scan RSSI for all BSSIDs in tracked_bssids
        """
        scan_rssi = {}
        for bssid in tracked_bssids:
            scan_rssi[bssid] = {"rssi": [], "avg_rssi": None}
        for idx in range(num_measurements):
            scan_output = self.dut.adb.shell(SCAN)
            time.sleep(MED_SLEEP)
            scan_output = self.dut.adb.shell(SCAN_RESULTS)
            for bssid in tracked_bssids:
                bssid_result = re.search(
                    bssid + ".*", scan_output, flags=re.IGNORECASE)
                if bssid_result:
                    bssid_result = bssid_result.group(0).split("\t")
                    scan_rssi[bssid]["rssi"].append(int(bssid_result[2]))
                else:
                    scan_rssi[bssid]["rssi"].append(RSSI_ERROR_VAL)
        # Compute mean RSSIs. Only average valid readings.
        # Output RSSI_ERROR_VAL if no readings found.
        for key, val in scan_rssi.items():
            filtered_rssi_values = [
                x for x in val["rssi"] if not math.isnan(x)
            ]
            if filtered_rssi_values:
                scan_rssi[key]["avg_rssi"] = sum(filtered_rssi_values) / len(
                    filtered_rssi_values)
                if len(filtered_rssi_values) > 1:
                    scan_rssi[key]["stdev"] = statistics.stdev(
                        filtered_rssi_values)
                else:
                    scan_rssi[key]["stdev"] = 0
            else:
                scan_rssi[key]["avg_rssi"] = RSSI_ERROR_VAL
                scan_rssi[key]["stdev"] = RSSI_ERROR_VAL
        return scan_rssi

    def get_connected_rssi(self,
                           num_measurements=1,
                           polling_frequency=SHORT_SLEEP):
        """Gets all RSSI values reported for the connected access point/BSSID.

        Args:
            num_measurements: number of scans done, and RSSIs collected
            polling_frequency: time to wait between RSSI measurements
        Returns:
            connected_rssi: dict containing the measurements results for
            all reported RSSI values (signal_poll, per chain, etc.) and their
            statistics
        """
        connected_rssi = {
            "signal_poll_rssi": [],
            "signal_poll_avg_rssi": [],
            "chain_0_rssi": [],
            "chain_1_rssi": []
        }
        for idx in range(num_measurements):
            # Get signal poll RSSI
            signal_poll_output = self.dut.adb.shell(SIGNAL_POLL)
            match = re.search("RSSI=.*", signal_poll_output)
            if match:
                temp_rssi = int(match.group(0).split("=")[1])
                if temp_rssi == -9999:
                    connected_rssi["signal_poll_rssi"].append(RSSI_ERROR_VAL)
                else:
                    connected_rssi["signal_poll_rssi"].append(temp_rssi)
            else:
                connected_rssi["signal_poll_rssi"].append(RSSI_ERROR_VAL)
            match = re.search("AVG_RSSI=.*", signal_poll_output)
            if match:
                connected_rssi["signal_poll_avg_rssi"].append(
                    int(match.group(0).split("=")[1]))
            else:
                connected_rssi["signal_poll_avg_rssi"].append(RSSI_ERROR_VAL)
            # Get per chain RSSI
            per_chain_rssi = self.dut.adb.shell(STATION_DUMP)
            match = re.search(".*signal avg:.*", per_chain_rssi)
            if match:
                per_chain_rssi = per_chain_rssi[per_chain_rssi.find("[") + 1:
                                                per_chain_rssi.find("]")]
                per_chain_rssi = per_chain_rssi.split(", ")
                connected_rssi["chain_0_rssi"].append(int(per_chain_rssi[0]))
                connected_rssi["chain_1_rssi"].append(int(per_chain_rssi[1]))
            else:
                connected_rssi["chain_0_rssi"].append(RSSI_ERROR_VAL)
                connected_rssi["chain_1_rssi"].append(RSSI_ERROR_VAL)
            time.sleep(polling_frequency)
        # Compute mean RSSIs. Only average valid readings.
        # Output RSSI_ERROR_VAL if no valid connected readings found.
        for key, val in connected_rssi.copy().items():
            filtered_rssi_values = [x for x in val if not math.isnan(x)]
            if filtered_rssi_values:
                connected_rssi["mean_{}".format(key)] = sum(
                    filtered_rssi_values) / len(filtered_rssi_values)
                if len(filtered_rssi_values) > 1:
                    connected_rssi["stdev_{}".format(key)] = statistics.stdev(
                        filtered_rssi_values)
                else:
                    connected_rssi["stdev_{}".format(key)] = 0
            else:
                connected_rssi["mean_{}".format(key)] = RSSI_ERROR_VAL
                connected_rssi["stdev_{}".format(key)] = RSSI_ERROR_VAL
        return connected_rssi

    def rssi_test(self, iperf_traffic, connected_measurements,
                  scan_measurements, bssids, polling_frequency):
        """Test function to run RSSI tests.

        The function runs an RSSI test in the current device/AP configuration.
        Function is called from another wrapper function that sets up the
        testbed for the RvR test

        Args:
            iperf_traffic: boolean specifying whether or not to run traffic
            during RSSI tests
            connected_measurements: number of RSSI measurements to make for the
            connected AP per attenuation point
            scan_measurements: number of scans and scan RSSIs to make per
            attenuation point
            bssids: list of BSSIDs to monitor in scans
            polling_frequency: time between connected AP measurements
        Returns:
            rssi_result: dict containing rssi_result and meta data
        """
        self.log.info("Start running RSSI test.")
        rssi_result = []
        # Start iperf traffic if required by test
        if self.iperf_traffic:
            self.iperf_server.start(tag=0)
            self.dut.run_iperf_client_nb(
                self.test_params["iperf_server_address"],
                self.iperf_args,
                timeout=3600)
        for atten in self.rssi_atten_range:
            # Set Attenuation
            self.log.info("Setting attenuation to {} dB".format(atten))
            [
                self.attenuators[i].set_atten(atten)
                for i in range(self.num_atten)
            ]
            time.sleep(MED_SLEEP)
            current_rssi = {}
            current_rssi["connected_rssi"] = self.get_connected_rssi(
                connected_measurements, polling_frequency)
            current_rssi["scan_rssi"] = self.get_scan_rssi(
                bssids, scan_measurements)
            rssi_result.append(current_rssi)
            self.log.info("Connected RSSI at {0:.2f} dB is {1:.2f} dB".format(
                atten, current_rssi["connected_rssi"][
                    "mean_signal_poll_rssi"]))
        # Stop iperf traffic if needed
        if self.iperf_traffic:
            self.iperf_server.stop()
            self.dut.adb.shell("pkill iperf3")
        [self.attenuators[i].set_atten(0) for i in range(self.num_atten)]
        return rssi_result

    def rssi_test_func(self, iperf_traffic, connected_measurements,
                       scan_measurements, bssids, polling_frequency):
        """Main function to test RSSI.

        The function sets up the AP in the correct channel and mode
        configuration and called rssi_test to sweep attenuation and measure
        RSSI

        Returns:
            rssi_result: dict containing rssi_results and meta data
        """
        #Initialize test settings
        rssi_result = {}
        # Configure AP
        band = self.access_point.band_lookup_by_channel(self.channel)
        self.access_point.set_channel(band, self.channel)
        self.access_point.set_bandwidth(band, self.mode)
        self.log.info("Access Point Configuration: {}".format(
            self.access_point.ap_settings))
        # Set attenuator to starting attenuation
        [
            self.attenuators[i].set_atten(self.rssi_atten_range[0])
            for i in range(self.num_atten)
        ]
        # Connect DUT to Network
        wutils.wifi_toggle_state(self.dut, True)
        wutils.reset_wifi(self.dut)
        self.main_network[band]["channel"] = self.channel
        wutils.wifi_connect(self.dut, self.main_network[band], num_of_tries=5)
        time.sleep(5)
        # Run RvR and log result
        rssi_result["test_name"] = self.current_test_name
        rssi_result["ap_settings"] = self.access_point.ap_settings.copy()
        rssi_result["attenuation"] = list(self.rssi_atten_range)
        rssi_result["connected_bssid"] = self.main_network[band]["BSSID"]
        rssi_result["ap_tx_power"] = self.test_params["ap_tx_power"][str(
            self.channel)]
        rssi_result["fixed_attenuation"] = self.test_params[
            "fixed_attenuation"][str(self.channel)]
        rssi_result["rssi_result"] = self.rssi_test(
            iperf_traffic, connected_measurements, scan_measurements, bssids,
            polling_frequency)
        self.testclass_results.append(rssi_result)
        return rssi_result

    def _test_rssi_vs_atten(self):
        """ Function that gets called for each test case of rssi_vs_atten

        The function gets called in each rvr test case. The function customizes
        the test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        self.channel = int(test_params[4][2:])
        self.mode = test_params[5]
        self.iperf_traffic = "ActiveTraffic" in test_params[6]
        self.iperf_args = '-i 1 -t 3600 -J -R'
        band = self.access_point.band_lookup_by_channel(self.channel)
        num_atten_steps = int((self.test_params["rssi_atten_stop"] -
                               self.test_params["rssi_atten_start"]) /
                              self.test_params["rssi_atten_step"])
        self.rssi_atten_range = [
            self.test_params["rssi_atten_start"] +
            x * self.test_params["rssi_atten_step"]
            for x in range(0, num_atten_steps)
        ]
        rssi_result = self.rssi_test_func(
            self.iperf_traffic, self.test_params["connected_measurements"],
            self.test_params["scan_measurements"], [
                self.main_network[band]["BSSID"]
            ], self.test_params["polling_frequency"])
        postprocessed_results = self.post_process_rssi_vs_attenuation(
            rssi_result)
        self.pass_fail_check_rssi_vs_attenuation(postprocessed_results)

    def _test_rssi_stability(self):
        """ Function that gets called for each test case of rssi_stability

        The function gets called in each stability test case. The function
        customizes test based on the test name of the test that called it
        """
        test_params = self.current_test_name.split("_")
        self.channel = int(test_params[3][2:])
        self.mode = test_params[4]
        self.iperf_traffic = "ActiveTraffic" in test_params[5]
        self.iperf_args = '-i 1 -t 3600 -J -R'
        band = self.access_point.band_lookup_by_channel(self.channel)
        self.rssi_atten_range = self.test_params["stability_test_atten"]
        connected_measurements = int(
            self.test_params["stability_test_duration"] /
            self.test_params["polling_frequency"])
        rssi_result = self.rssi_test_func(
            self.iperf_traffic, connected_measurements, 0, [
                self.main_network[band]["BSSID"]
            ], self.test_params["polling_frequency"])
        self.pass_fail_check_rssi_stability(rssi_result)

    @test_tracker_info(uuid='519689b8-0a3c-4fd9-9227-fd7962d0f1a0')
    def test_rssi_stability_ch1_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='23eca2ab-d0b4-4730-9f32-ec2d901ae493')
    def test_rssi_stability_ch2_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='63d340c0-dcf9-4e14-87bd-a068a59836b2')
    def test_rssi_stability_ch3_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='ddbe88d8-be20-40eb-8f29-55049e3fef28')
    def test_rssi_stability_ch4_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='9c06304e-2b60-4619-8fb3-73fd2cb4b854')
    def test_rssi_stability_ch5_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='74b656ca-132e-4d66-9584-560287081607')
    def test_rssi_stability_ch6_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='23b5f19a-539b-4908-a197-06ce505d3d23')
    def test_rssi_stability_ch7_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='e7b85167-f4c4-4adb-a111-04d8a5f10e1a')
    def test_rssi_stability_ch8_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='2a0a9393-4b68-4c08-8787-3f35d1a8458b')
    def test_rssi_stability_ch9_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='069c7acf-3e7e-4298-91cb-d292c6025ae1')
    def test_rssi_stability_ch10_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='95c5a27c-1dea-47a4-a1c5-edf955545f12')
    def test_rssi_stability_ch11_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='8aeab023-a096-4fbe-80dd-fd01466f9fac')
    def test_rssi_stability_ch36_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='872fed9f-d0bb-4a7b-a2a7-bf8df7740b2d')
    def test_rssi_stability_ch36_VHT40_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='27395fd1-e286-473a-b98e-5a50db2a598a')
    def test_rssi_stability_ch36_VHT80_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='6f6b25e3-1a1e-4a61-930a-1d0aa25ba900')
    def test_rssi_stability_ch40_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='c6717da7-855c-4c6e-a6e2-ee42b8feaaab')
    def test_rssi_stability_ch44_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='2e34f735-079c-4619-9e74-b96dc8d0597f')
    def test_rssi_stability_ch44_VHT40_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='d543c019-1ff5-41d4-9b37-ccdc593f3edd')
    def test_rssi_stability_ch48_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='2bb08914-36b2-4f58-9b3e-c3f3f4fac8ab')
    def test_rssi_stability_ch149_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='e2f585f5-7811-4570-b987-23da301eb75d')
    def test_rssi_stability_ch149_VHT40_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='f3e74d5b-73f6-4723-abf3-c9c147db08e3')
    def test_rssi_stability_ch149_VHT80_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='06503ed0-baf3-4cd1-ac5e-4124e3c7f52f')
    def test_rssi_stability_ch153_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='0cf8286f-a919-4e29-a9f2-e7738a4afe8f')
    def test_rssi_stability_ch157_VHT20_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='f9a0165c-468b-4096-8f4b-cc80bae564a0')
    def test_rssi_stability_ch157_VHT40_ActiveTraffic(self):
        self._test_rssi_stability()

    @test_tracker_info(uuid='4b74dd46-4190-4556-8ad8-c55808e9e847')
    def test_rssi_stability_ch161_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='ae54b7cc-d76d-4460-8dcc-2c439265c7c9')
    def test_rssi_vs_atten_ch1_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='07fe7899-886d-45ba-9c1d-7daaf9844c9c')
    def test_rssi_vs_atten_ch2_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='9e86578b-a6cd-4de9-a79d-eabac5bd5f4e')
    def test_rssi_vs_atten_ch3_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='e9d258ca-8e70-408e-b704-782fce7a07c5')
    def test_rssi_vs_atten_ch4_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='1c5d71a0-7532-49e4-98a9-1c2d9d8d58d2')
    def test_rssi_vs_atten_ch5_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='107f01f3-b6b9-470b-9895-6345edfc9599')
    def test_rssi_vs_atten_ch6_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='88cb18b2-30bf-4c01-ac28-15451289e7cd')
    def test_rssi_vs_atten_ch7_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='c07a7442-bd1d-40c7-80ed-167e30b8cfaf')
    def test_rssi_vs_atten_ch8_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='b8946280-88d5-400d-a417-2bdc9d7e054a')
    def test_rssi_vs_atten_ch9_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='a05db91b-740d-4984-a447-79ab438034f0')
    def test_rssi_vs_atten_ch10_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='f4d565f8-f060-462c-9b3c-cd1f7d27b3ea')
    def test_rssi_vs_atten_ch11_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='a33a93ac-604a-414f-ae96-42dffbe59a93')
    def test_rssi_vs_atten_ch36_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='39875ab0-e0e9-464b-8a47-4dedd65f066e')
    def test_rssi_vs_atten_ch36_VHT40_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='c6ff8768-f124-4190-baf2-bbf14b612de3')
    def test_rssi_vs_atten_ch36_VHT80_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='ed4705af-e202-4737-b410-8bab0515e79f')
    def test_rssi_vs_atten_ch40_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='1388df99-ecbf-4412-9ded-d66552f37ec5')
    def test_rssi_vs_atten_ch44_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='06868677-ad3c-4f50-9b9e-ae8d9455ae4d')
    def test_rssi_vs_atten_ch44_VHT40_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='9b6676de-c736-4603-a9b3-97670bea8f25')
    def test_rssi_vs_atten_ch48_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='2641c4b8-0092-4e29-9139-fdb3b3f04d05')
    def test_rssi_vs_atten_ch149_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='c8bc3f7d-b459-4e40-9c73-b0bf534c6c08')
    def test_rssi_vs_atten_ch149_VHT40_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='3e08f5b6-9f3c-4905-8b10-82e1ca830cc9')
    def test_rssi_vs_atten_ch149_VHT80_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='2343efe3-fdda-4180-add7-4786d35e29bb')
    def test_rssi_vs_atten_ch153_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='89a16974-2399-4356-b720-17b765ff1c3a')
    def test_rssi_vs_atten_ch157_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='c8e0e44a-b962-4e71-ba8f-068f268c8823')
    def test_rssi_vs_atten_ch157_VHT40_ActiveTraffic(self):
        self._test_rssi_vs_atten()

    @test_tracker_info(uuid='581b5794-239e-4d1c-b0ce-7c6dc5bd373f')
    def test_rssi_vs_atten_ch161_VHT20_ActiveTraffic(self):
        self._test_rssi_vs_atten()


class WifiRssi_2GHz_ActiveTraffic_Test(WifiRssiTest):
    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.tests = ("test_rssi_stability_ch1_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch2_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch3_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch4_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch5_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch6_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch7_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch8_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch9_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch10_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch11_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch1_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch2_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch3_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch4_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch5_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch6_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch7_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch8_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch9_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch10_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch11_VHT20_ActiveTraffic")


class WifiRssi_5GHz_ActiveTraffic_Test(WifiRssiTest):
    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.tests = ("test_rssi_stability_ch36_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch36_VHT40_ActiveTraffic",
                      "test_rssi_stability_ch36_VHT80_ActiveTraffic",
                      "test_rssi_stability_ch40_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch44_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch44_VHT40_ActiveTraffic",
                      "test_rssi_stability_ch48_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch149_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch149_VHT40_ActiveTraffic",
                      "test_rssi_stability_ch149_VHT80_ActiveTraffic",
                      "test_rssi_stability_ch153_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch157_VHT20_ActiveTraffic",
                      "test_rssi_stability_ch157_VHT40_ActiveTraffic",
                      "test_rssi_stability_ch161_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch36_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch36_VHT40_ActiveTraffic",
                      "test_rssi_vs_atten_ch36_VHT80_ActiveTraffic",
                      "test_rssi_vs_atten_ch40_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch44_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch44_VHT40_ActiveTraffic",
                      "test_rssi_vs_atten_ch48_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch149_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch149_VHT40_ActiveTraffic",
                      "test_rssi_vs_atten_ch149_VHT80_ActiveTraffic",
                      "test_rssi_vs_atten_ch153_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch157_VHT20_ActiveTraffic",
                      "test_rssi_vs_atten_ch157_VHT40_ActiveTraffic",
                      "test_rssi_vs_atten_ch161_VHT20_ActiveTraffic")
