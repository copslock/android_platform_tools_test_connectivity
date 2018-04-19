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

import logging
import os
import time

from acts import base_test
from acts import utils
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.bt import bt_power_test_utils as btutils
from acts.test_decorators import test_tracker_info


class PowerBTbaselineTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        req_params = ['btbaseline_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.btbaseline_params)
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon = self.monsoons[0]
        self.mon.set_max_current(wputils.MONSOON_MAX_CURRENT)
        self.mon.set_voltage(wputils.PHONE_BATTERY_VOLTAGE)
        self.mon.attach_device(self.dut)
        self.mon_info = wputils.create_monsoon_info(self)
        for file in self.custom_files:
            if 'pass_fail_threshold_' + self.dut.model in file:
                self.threshold_file = file
        self.threshold = wputils.unpack_custom_file(self.threshold_file,
                                                    self.TAG)

        # Reset BT to factory defaults
        self.dut.droid.bluetoothFactoryReset()
        time.sleep(2)

    def teardown_class(self):
        """Clean up the test class after all tests finish running

        """
        self.mon.usb('on')
        self.dut.droid.bluetoothFactoryReset()

    def unpack_testparams(self, bulk_params):
        """Unpack all the test specific parameters.

        Args:
            bulk_params: dict with all test specific params in the config file
        """
        for key in bulk_params.keys():
            setattr(self, key, bulk_params[key])

    def measure_power(self):
        """Measures current consumption and evaluates pass/fail criteria

        """
        # Measure current and plot
        begin_time = utils.get_current_epoch_time()
        file_path, avg_current = wputils.monsoon_data_collect_save(
            self.dut, self.mon_info, self.current_test_name)
        wputils.monsoon_data_plot(self.mon_info, file_path)
        # Take Bugreport
        if bool(self.bug_report) == True:
            self.dut.take_bug_report(self.test_name, begin_time)

        # Compute pass or fail check
        wputils.pass_fail_check(self, avg_current)

    # Test cases- Baseline
    @test_tracker_info(uuid='3f8ac0cb-f20d-4569-a58e-6009c89ea049')
    def test_bt_ON_screen_OFF_connectable(self):
        """Measures baseline power when BT is toggled ON and screen is OFF

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON BT (i.e., page scan) and turns screen OFF
        4. Measures the power consumption
        5. Asserts pass/fail criteria based on measured power
        """
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # This is the default mode: devices enters paging periodically
        self.dut.droid.bluetoothMakeConnectable()

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='d54a992e-37ed-460a-ada7-2c51941557fd')
    def test_bt_ON_screen_OFF_discoverable(self):
        """Measures baseline power when BT is discoverable and screen is OFF

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Sets phone discoverable (i.e., inquiry scan) and turns screen OFF
        4. Measures the power consumption
        5. Asserts pass/fail criteria based on measured power
        """
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # Device will enter Inquiry state
        duration = self.mon_info['duration'] + self.mon_info['offset']
        self.dut.droid.bluetoothMakeDiscoverable(duration)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='8f4c36b5-b18e-4aa5-9fe5-aafb729c1034')
    def test_bt_ON_screen_ON_connectable(self):
        """Measures baseline power when BT is toggled ON and screen is ON

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON BT (i.e., page scan) and turns screen ON
        4. Measures the power consumption
        5. Asserts pass/fail criteria based on measured power
        """
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'ON')

        # This is the default mode: devices enters paging periodically
        self.dut.droid.bluetoothMakeConnectable()

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='7128356f-67d8-46b3-9d6b-1a4c9a7a1745')
    def test_bt_ON_screen_ON_discoverable(self):
        """Measures baseline power when BT is discoverable and screen is ON

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Sets phone discoverable (i.e., inquiry scan) and turns screen ON
        4. Measures the power consumption
        5. Asserts pass/fail criteria based on measured power
        """
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'ON')

        # Device will enter Inquiry state
        duration = self.mon_info['duration'] + self.mon_info['offset']
        self.dut.droid.bluetoothMakeDiscoverable(duration)

        # Measure power
        self.measure_power()
