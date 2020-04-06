#!/usr/bin/env python3.4
#
#   Copyright 2020 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from acts import base_test
from acts.metrics.loggers.blackbox import BlackboxMappedMetricLogger
from acts.test_utils.wifi import wifi_performance_test_utils as wputils
from acts.test_utils.wifi import wifi_retail_ap as retail_ap


class WifiPerformancePreflightTest(base_test.BaseTestClass):
    """Class for Wifi performance preflight tests.

    This class implements WiFi performance tests to perform before any other
    test suite. Currently, the preflight checklist checks the wifi firmware and
    config files, i.e., bdf files for any changes by retrieving their version
    number and checksum.
    """
    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.testcase_metric_logger = (
            BlackboxMappedMetricLogger.for_test_case())

    def setup_class(self):
        self.dut = self.android_devices[-1]
        # Initialize AP to ensure that tests can be run in later suites
        req_params = ['RetailAccessPoints']
        self.unpack_userparams(req_params)
        self.access_point = retail_ap.create(self.RetailAccessPoints)[0]

    def test_wifi_sw_signature(self):
        sw_signature = wputils.get_sw_signature(self.dut)
        self.testcase_metric_logger.add_metric('bdf_signature',
                                               sw_signature['bdf_signature'])
        self.testcase_metric_logger.add_metric('fw_signature',
                                               sw_signature['fw_signature'])
