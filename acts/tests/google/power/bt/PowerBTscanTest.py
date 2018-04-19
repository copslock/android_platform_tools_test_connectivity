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
from acts.test_utils.bt.bt_constants import ble_scan_settings_modes
from acts.test_utils.bt import bt_power_test_utils as btutils
from acts.test_decorators import test_tracker_info


class PowerBTscanTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        req_params = ['btscan_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.btscan_params)
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon = self.monsoons[0]
        self.mon.set_max_current(wputils.MONSOON_MAX_CURRENT)
        self.mon.set_voltage(wputils.PHONE_BATTERY_VOLTAGE)
        self.mon.attach_device(self.dut)
        self.mon_info = wputils.create_monsoon_info(self)
        for file in self.custom_files:
            if 'pass_fail_threshold' in file:
                self.threshold_file = file
        self.threshold = wputils.unpack_custom_file(self.threshold_file,
                                                    self.TAG)

        # Start PMC app.
        self.log.info('Start PMC app...')
        self.dut.adb.shell(btutils.START_PMC_CMD)
        self.dut.adb.shell(btutils.PMC_VERBOSE_CMD)

        # Reset BT to factory defaults
        self.dut.droid.bluetoothFactoryReset()
        time.sleep(2)
        self.tests = self._get_all_test_names()
        self.mon_offset = self.mon_info['offset']

    def teardown_test(self):
        """Tear down necessary objects/settings after test finishes

        """
        self.dut.adb.shell(btutils.BLE_LOCATION_SCAN_DISABLE)

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

    def scan_ble_measure_power(self, scan_mode):
        """Starts a generic BLE scan and measures the power

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON/OFF BT, BLE and screen according to test conditions
        3. Sends the adb shell command to PMC to start scan
        4. Measures the power consumption
        5. Asserts pass/fail criteria based on measured power

        Args:
            scan_mode: BLE scan type (e.g., low_power)
        """
        # Add more offset to the first tests to ensure system collapse
        if self.current_test_name == self.tests[0]:
            self.mon_info['offset'] = self.mon_offset + 180
        else:
            self.mon_info['offset'] = self.mon_offset
        # Start BLE scan
        btutils.start_pmc_ble_scan(self.dut, scan_mode,
                                   self.mon_info['offset'],
                                   self.mon_info['duration'])

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

    # Test Cases: BLE Scans + Filtered scans
    @test_tracker_info(uuid='e9a36161-1d0c-4b9a-8bd8-80fef8cdfe28')
    def test_ble_screen_ON_default_scan(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'ON')

        # Start scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['balanced'])

    @test_tracker_info(uuid='5fa61bf4-5f04-40bf-af52-6644b534d02e')
    def test_ble_screen_OFF_filter_scan_opport(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['opportunistic'])

    @test_tracker_info(uuid='512b6cde-be83-43b0-b799-761380ba69ff')
    def test_ble_screen_OFF_filter_scan_low_power(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_power'])

    @test_tracker_info(uuid='3a526838-ae7b-4cdb-bc29-89a5503d2306')
    def test_ble_screen_OFF_filter_scan_balanced(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['balanced'])

    @test_tracker_info(uuid='03a57cfd-4269-4a09-8544-84f878d2e801')
    def test_ble_screen_OFF_filter_scan_low_lat(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'ON', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_latency'])

    # Test Cases: Background scans
    @test_tracker_info(uuid='20145317-e362-4bfd-9860-4ceddf764784')
    def test_ble_screen_ON_backgnd_scan_low_lat(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'OFF', 'ON', 'ON')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_latency'])

    @test_tracker_info(uuid='00a53dc3-2c33-43c4-b356-dba93249b823')
    def test_ble_screen_ON_backgnd_scan_low_power(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'OFF', 'ON', 'ON')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_power'])

    @test_tracker_info(uuid='b7185d64-631f-4b18-8d0b-4e14b80db375')
    def test_ble_screen_OFF_filter_backgnd_scan_low_lat(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'OFF', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_latency'])

    @test_tracker_info(uuid='93eb05da-a577-409c-8208-6af1899a10c2')
    def test_ble_screen_OFF_filter_backgnd_scan_low_power(self):
        # Set the phone in the desired state
        btutils.phone_setup_for_BT(self.dut, 'OFF', 'ON', 'OFF')

        # Start BLE scan and measure power
        self.scan_ble_measure_power(ble_scan_settings_modes['low_power'])
