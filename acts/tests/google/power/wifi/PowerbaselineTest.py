#!/usr/bin/env python3.4
#
#   Copyright 2017 - The Android Open Source Project
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

import logging
import os
from acts import base_test
from acts import utils
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_decorators import test_tracker_info


class PowerbaselineTest(base_test.BaseTestClass):
    """Power baseline tests for rockbottom state.
    Rockbottom for wifi on/off, screen on/off, everything else turned off

    """

    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        wputils.force_countrycode(self.dut, 'US')
        req_params = ['baselinetest_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.baselinetest_params)
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon = self.monsoons[0]
        self.mon.set_max_current(8.0)
        self.mon.set_voltage(4.2)
        self.mon.attach_device(self.dut)
        self.mon_info = wputils.create_monsoon_info(self)
        for file in self.custom_files:
            if 'pass_fail_threshold' in file:
                self.threshold_file = file
        self.threshold = wputils.unpack_custom_file(self.threshold_file,
                                                    self.TAG)
        self.tests = self._get_all_test_names()
        self.mon_offset = self.mon_info['offset']

    def teardown_class(self):
        """Tearing down the entire test class.

        """
        self.log.info('Tearing down the test class')
        self.mon.usb('on')

    def teardown_test(self):
        """Tearing down the test case.

        """
        self.log.info('Tearing down the test')
        self.mon.usb('on')

    def unpack_testparams(self, bulk_params):
        """Unpack all the test specific parameters.

        Args:
            bulk_params: dict with all test specific params in the config file
        """
        for key in bulk_params.keys():
            setattr(self, key, bulk_params[key])

    def rockbottom_test_func(self, screen_status, wifi_status):
        """Test function for baseline rockbottom tests.

        Args:
            screen_status: screen on or off
            wifi_status: wifi enable or disable, on/off, not connected even on
        """
        # Add more offset to the first tests to ensure system collapse
        if self.current_test_name == self.tests[0]:
            self.mon_info['offset'] = self.mon_offset + 300
        else:
            self.mon_info['offset'] = self.mon_offset
        # Initialize the dut to rock-bottom state
        wputils.dut_rockbottom(self.dut)
        if wifi_status == 'ON':
            wutils.wifi_toggle_state(self.dut, True)
        if screen_status == 'OFF':
            self.dut.droid.goToSleepNow()
            self.dut.log.info('Screen is OFF')
        # Collecting current measurement data and plot
        begin_time = utils.get_current_epoch_time()
        file_path, avg_current = wputils.monsoon_data_collect_save(
            self.dut, self.mon_info, self.current_test_name)
        wputils.monsoon_data_plot(self.mon_info, file_path)
        # Take Bugreport
        if bool(self.bug_report) == True:
            self.dut.take_bug_report(self.test_name, begin_time)
        wputils.pass_fail_check(self, avg_current)

    # Test cases
    @test_tracker_info(uuid='e7ab71f4-1e14-40d2-baec-cde19a3ac859')
    def test_rockbottom_screenoff_wifidisabled(self):

        self.rockbottom_test_func('OFF', 'OFF')

    @test_tracker_info(uuid='167c847d-448f-4c7c-900f-82c552d7d9bb')
    def test_rockbottom_screenoff_wifidisconnected(self):

        self.rockbottom_test_func('OFF', 'ON')

    @test_tracker_info(uuid='2cd25820-8548-4e60-b0e3-63727b3c952c')
    def test_rockbottom_screenon_wifidisabled(self):

        self.rockbottom_test_func('ON', 'OFF')

    @test_tracker_info(uuid='d7d90a1b-231a-47c7-8181-23814c8ff9b6')
    def test_rockbottom_screenon_wifidisconnected(self):

        self.rockbottom_test_func('ON', 'ON')
