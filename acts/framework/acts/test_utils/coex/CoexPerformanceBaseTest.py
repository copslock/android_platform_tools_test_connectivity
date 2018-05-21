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
import time

from acts.test_utils.bt.bt_test_utils import disable_bluetooth
from acts.test_utils.coex.CoexBaseTest import CoexBaseTest
from acts.test_utils.coex.coex_test_utils import a2dp_dumpsys_parser
from acts.test_utils.coex.coex_test_utils import bokeh_plot
from acts.test_utils.coex.coex_test_utils import (
    collect_bluetooth_manager_dumpsys_logs)
from acts.test_utils.coex.coex_test_utils import multithread_func
from acts.test_utils.coex.coex_test_utils import wifi_connection_check
from acts.test_utils.coex.coex_test_utils import xlsheet
from acts.test_utils.wifi.wifi_test_utils import reset_wifi
from acts.test_utils.wifi.wifi_test_utils import wifi_connect
from acts.test_utils.wifi.wifi_test_utils import wifi_toggle_state


class CoexPerformanceBaseTest(CoexBaseTest):
    """Base test class for performance tests

    Attributes:
        rvr : Dict to save attenuation, throughput, fixed_attenuation.
        flag : Used to denote a2dp test cases.
    """
    def __init__(self, controllers):
        super().__init__(controllers)
        self.rvr = {}
        self.flag = False

    def setup_class(self):
        req_params = ["test_params", "Attenuator"]
        self.unpack_userparams(req_params)
        if hasattr(self, "Attenuator"):
            self.num_atten = self.attenuators[0].instrument.num_atten
        else:
            self.log.error("Attenuator should be connected to run tests.")
            return False
        for i in range(self.num_atten):
            self.attenuators[i].set_atten(0)
        super().setup_class()
        if "performance_result_path" in self.user_params["test_params"]:
            self.performance_files_list = [
                os.path.join(self.test_params["performance_result_path"],
                             file) for file in os.listdir(
                                 self.test_params["performance_result_path"])
            ]
        self.attenuation_range = range(self.test_params["attenuation_start"],
                                       self.test_params["attenuation_stop"],
                                       self.test_params["attenuation_step"])

    def setup_test(self):
        if not wifi_connection_check(self.pri_ad, self.network["SSID"]):
            reset_wifi(self.pri_ad)
            wifi_connect(self.pri_ad, self.network, num_of_tries=5)
        super().setup_test()

    def teardown_test(self):
        self.performance_baseline_check()
        if not disable_bluetooth(self.pri_ad.droid):
            self.log.error("Failed to disable bluetooth")
            return False
        self.teardown_thread()

    def teardown_class(self):
        reset_wifi(self.pri_ad)
        wifi_toggle_state(self.pri_ad, False)
        json_result = self.results.json_str()
        xlsheet(self.pri_ad, json_result, self.attenuation_range)

    def set_attenuation_and_run_iperf(self, called_func=None):
        """Sets attenuation and runs iperf for Attenuation max value.

        Args:
            called_func : Function object to run.

        Returns:
            True if Pass
            False if Fail
        """
        self.iperf_received = []
        for atten in self.attenuation_range:
            self.log.info("Setting attenuation = {}".format(atten))
            for i in range(self.num_atten):
                self.attenuators[i].set_atten(atten)
            if not wifi_connection_check(self.pri_ad, self.network["SSID"]):
                return False
            time.sleep(5)  # Time for attenuation to set.
            if called_func:
                if not multithread_func(self.log, called_func):
                    return False
            else:
                self.run_iperf_and_get_result()
            if "a2dp_streaming" in self.current_test_name:
                if not collect_bluetooth_manager_dumpsys_logs(
                        self.pri_ad, self.current_test_name):
                    return False
            self.teardown_result()
        for i in range(self.num_atten):
            self.attenuators[i].set_atten(0)
        for received in self.received:
            iperf_value = str(received).strip("Mb/s")
            if iperf_value == "Iperf Failed":
                self.iperf_received.append(0)
            else:
                self.iperf_received.append(float(iperf_value))
        self.rvr["test_name"] = self.current_test_name
        self.rvr["attenuation"] = list(self.attenuation_range)
        self.rvr["throughput_received"] = self.iperf_received
        self.rvr["fixed_attenuation"] = (
            self.test_params["fixed_attenuation"][str(self.network["channel"])])
        return True

    def performance_baseline_check(self):
        """Checks for performance_result_path in config. If present, plots
        comparision chart else plot chart for that particular test run.

        Returns:
            True if success, False otherwise.
        """
        self.flag = False
        if "a2dp_streaming" in self.current_test_name:
            self.flag = True
        if self.rvr:
            self.plot_graph_for_attenuation()
            with open(self.json_file, 'a') as results_file:
                json.dump(self.rvr, results_file, indent=4)
            self.throughput_pass_fail_check()
        else:
            self.log.error("Throughput dict empty!")
            return False
        return True


    def plot_graph_for_attenuation(self):
        """Plots graph and add as JSON formatted results for attenuation with
        respect to its iperf values. Compares rvr results with baseline
        values by calculating throughput limits.
        """
        test_name = self.current_test_name
        x_label = 'Attenuation (dB)'
        y_label = 'Throughput (Mbps)'
        legends = [self.current_test_name]
        plot = [0]
        fig_property = {
            "title": test_name,
            "x_label": x_label,
            "y_label": y_label,
            "linewidth": 3,
            "markersize": 10
        }
        total_atten = self.total_attenuation(self.rvr)
        data_sets = [[total_atten], [self.rvr["throughput_received"]]]
        shaded_region = None

        if "performance_result_path" in self.user_params["test_params"]:
            throughput_received = []
            try:
                attenuation_path = [
                    file_name for file_name in self.performance_files_list
                    if test_name in file_name
                ]
                attenuation_path = attenuation_path[0]
                with open(attenuation_path, 'r') as throughput_file:
                    throughput_results = json.load(throughput_file)
                legends.insert(0, "Performance Results")
                throughput_attenuation = [
                    att + throughput_results["fixed_attenuation"]
                    for att in self.rvr["attenuation"]
                ]
                for idx,_ in enumerate(throughput_attenuation):
                    throughput_received.append(
                        throughput_results["throughput_received"][idx])
                data_sets[0].insert(0, throughput_attenuation)
                data_sets[1].insert(0, throughput_received)
                throughput_limits = self.get_throughput_limits(
                    attenuation_path)
                shaded_region = {
                    "x_vector": throughput_limits["attenuation"],
                    "lower_limit": throughput_limits["lower_limit"],
                    "upper_limit": throughput_limits["upper_limit"]
                }
            except Exception as e:
                shaded_region = None
                self.log.warning("ValueError: Performance file not found")

        if self.flag:
            plot = [0, 1]
            self.rvr["a2dp_packet_drop"] = a2dp_dumpsys_parser()
            y_label1 = "Packets Dropped (in %)"
            fig_property["y_label"] = [y_label1, y_label]
            legends.insert(0, 'Packet drops')
            data_sets[0].insert(0, total_atten)
            data_sets[1].insert(0, self.rvr["a2dp_packet_drop"])

        output_file_path = os.path.join(
            self.pri_ad.log_path, '%s.html' % test_name)
        bokeh_plot(
            plot,
            data_sets,
            legends,
            fig_property,
            shaded_region=shaded_region,
            output_file_path=output_file_path)

    def total_attenuation(self, performance_dict):
        """Calculates attenuation with adding fixed attenuation.

        Args:
            performance_dict: dict containing attenuation and fixed attenuation.

        Returns:
            Total attenuation is returned.
        """
        total_atten = [
            att + performance_dict["fixed_attenuation"]
            for att in performance_dict["attenuation"]
        ]
        return total_atten

    def throughput_pass_fail_check(self):
        """Check the test result and decide if it passed or failed
        by comparing with throughput limits.The pass/fail tolerances are
        provided in the config file.

        Returns:
            True if successful, False otherwise.
        """
        test_name = self.current_test_name
        try:
            performance_path = [
                file_name for file_name in self.performance_files_list
                if test_name in file_name
            ]
            performance_path = performance_path[0]
            throughput_limits = self.get_throughput_limits(
                    performance_path)
            failure_count = 0
            for idx, current_throughput in enumerate(
                    self.rvr["throughput_received"]):
                current_att = self.rvr["attenuation"][idx] + self.rvr["fixed_attenuation"]
                if (current_throughput < throughput_limits["lower_limit"][idx] or
                        current_throughput > throughput_limits["upper_limit"][idx]):
                    failure_count = failure_count + 1
                    self.log.info(
                        "Throughput at {} dB attenuation is beyond limits. "
                        "Throughput is {} Mbps. Expected within [{}, {}] Mbps.".
                        format(current_att, current_throughput,
                            throughput_limits["lower_limit"][idx],
                                   throughput_limits["upper_limit"][idx]))
            if failure_count >= self.test_params["failure_count_tolerance"]:
                self.log.info(
                    "Test failed. Found {} points outside throughput limits.".
                        format(failure_count))
                return False
            self.log.info(
                "Test passed. Found {} points outside throughput limits.".format(
                    failure_count))
        except Exception as e:
            self.log.warning("ValueError: Performance file not found")


    def get_throughput_limits(self, performance_path):
        """Compute throughput limits for current test.

        Checks the RvR test result and compares to a throughput limits for
        the same configuration. The pass/fail tolerances are provided in the
        config file.

        Args:
            performance_path: path to baseline file used to generate limits

        Returns:
            throughput_limits: dict containing attenuation and throughput
            limit data
        """
        with open(performance_path, 'r') as performance_file:
            performance_results = json.load(performance_file)
            performance_attenuation = self.total_attenuation(performance_results)
        attenuation = []
        lower_limit = []
        upper_limit = []
        for idx, current_throughput in enumerate(
                self.rvr["throughput_received"]):
            current_att = self.rvr["attenuation"][idx] + self.rvr["fixed_attenuation"]
            att_distances = [
                abs(current_att - performance_att)
                for performance_att in performance_attenuation
            ]
            sorted_distances = sorted(
                enumerate(att_distances), key=lambda x: x[1])
            closest_indeces = [dist[0] for dist in sorted_distances[0:3]]
            closest_throughputs = [
                performance_results["throughput_received"][index]
                for index in closest_indeces
            ]
            closest_throughputs.sort()
            attenuation.append(current_att)
            lower_limit.append(
                max(closest_throughputs[0] - max(
                    self.test_params["abs_tolerance"], closest_throughputs[0] *
                    self.test_params["pct_tolerance"] / 100), 0))
            upper_limit.append(closest_throughputs[-1] + max(
                self.test_params["abs_tolerance"], closest_throughputs[-1] *
                self.test_params["pct_tolerance"] / 100))
        throughput_limits = {
            "attenuation": attenuation,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit
        }
        return throughput_limits