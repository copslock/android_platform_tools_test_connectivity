#!/usr/bin/env python3.4
#
#   Copyright 2019 - The Android Open Source Project
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

from acts import base_test
from acts.metrics.loggers.blackbox import BlackboxMetricLogger
from acts.test_utils.wifi import ota_chamber
from WifiRvrTest import WifiRvrTest


class WifiOtaRvrTest(WifiRvrTest):
    """Class to test over-the-air RvR

    This class implements measures WiFi RvR tests in an OTA chamber. It enables
    setting turntable orientation and other chamber parameters to study
    performance in varying channel conditions
    """

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.failure_count_metric = BlackboxMetricLogger.for_test_case(
            metric_name='failure_count')
        self.tests = ('test_rvr_TCP_UL_ch36_VHT20_0deg',
                      'test_rvr_TCP_UL_ch36_VHT20_90deg',
                      'test_rvr_TCP_UL_ch36_VHT20_180deg',
                      'test_rvr_TCP_UL_ch36_VHT20_270deg')

    def setup_class(self):
        WifiRvrTest.setup_class(self)
        req_params = ['OTAChamber']
        self.unpack_userparams(req_params)
        self.ota_chambers = ota_chamber.create(self.OTAChambers)
        self.ota_chamber = self.ota_chambers[0]

    def setup_rvr_test(self, testcase_params):
        """Function that gets devices ready for the test.

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Configure AP
        self.setup_ap(testcase_params)
        # Set attenuator to 0 dB
        for attenuator in self.attenuators:
            attenuator.set_atten(0)
        # Set turntable orientation
        self.ota_chamber.set_orientation(testcase_params['orientation'])
        # Reset, configure, and connect DUT
        self.setup_dut(testcase_params)

    def parse_test_params(self, test_name):
        """Function that generates test params based on the test name."""
        # Call parent parsing function
        testcase_params = WifiRvrTest.parse_test_params(self)
        # Add orientation information
        test_name_params = test_name.split('_')
        testcase_params['orientation'] = int(test_name_params[6][0:-3])
        return testcase_params

    def test_rvr_TCP_UL_ch36_VHT20_0deg(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT20_90deg(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT20_180deg(self):
        self._test_rvr()

    def test_rvr_TCP_UL_ch36_VHT20_270deg(self):
        self._test_rvr()
