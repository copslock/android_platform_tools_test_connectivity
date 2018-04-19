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
import math
import os
import time

from acts import base_test
from acts import utils
from acts.controllers.ap_lib import hostapd_constants as hc
from acts.test_decorators import test_tracker_info
from acts.test_utils.bt import bt_power_test_utils as btutils
from acts.test_utils.bt.bt_constants import ble_scan_settings_modes
from acts.test_utils.wifi import wifi_power_test_utils as wputils


class PowerCoexScanTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        wputils.force_countrycode(self.dut, 'US')
        self.access_point = self.access_points[0]
        req_params = ['coexscan_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.coexscan_params)
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon = self.monsoons[0]
        self.mon.set_max_current(wputils.MONSOON_MAX_CURRENT)
        self.mon.set_voltage(wputils.PHONE_BATTERY_VOLTAGE)
        self.mon.attach_device(self.dut)
        self.mon_info = wputils.create_monsoon_info(self)
        self.num_atten = self.attenuators[0].instrument.num_atten
        for file in self.custom_files:
            if 'pass_fail_threshold' in file:
                self.threshold_file = file
            elif 'attenuator_setting' in file:
                self.attenuation_file = file
            elif 'network_config' in file:
                self.network_file = file
        self.threshold = wputils.unpack_custom_file(self.threshold_file,
                                                    self.TAG)
        self.atten_level = wputils.unpack_custom_file(self.attenuation_file,
                                                      self.TAG)
        self.networks = wputils.unpack_custom_file(self.network_file)
        self.main_network = self.networks['main_network']

        # Start PMC app.
        self.log.info('Start PMC app...')
        self.dut.adb.shell(btutils.START_PMC_CMD)
        self.dut.adb.shell(btutils.PMC_VERBOSE_CMD)
        self.tests = self._get_all_test_names()
        self.mon_offset = self.mon_info['offset']

    def setup_test(self):

        iterations = math.floor((self.mon_duration + self.mon_offset + 10) /
                                self.wifi_scan_interval)

        self.PERIODIC_WIFI_SCAN = (
            'am instrument -w -r -e scan-interval \"%d\" -e scan-iterations'
            ' \"%d\" -e class com.google.android.platform.powertests.'
            'WifiTests#testGScanAllChannels com.google.android.platform.'
            'powertests/android.test.InstrumentationTestRunner > /dev/null &' %
            (self.wifi_scan_interval, iterations))

    def teardown_class(self):
        """Clean up the test class after all tests finish running

        """
        self.mon.usb('on')
        self.access_point.close()  # Just as a precaution

    def teardown_test(self):
        """Tear down necessary objects/settings after test finishes

        """
        self.dut.adb.shell(btutils.BLE_LOCATION_SCAN_DISABLE)
        if self.brconfigs:
            self.access_point.bridge.teardown(self.brconfigs)
        self.access_point.close()

    def unpack_testparams(self, bulk_params):
        """Unpack all the test specific parameters

        Args:
            bulk_params: dict with all test specific params in the config file
        """
        for key in bulk_params.keys():
            setattr(self, key, bulk_params[key])

    def measure_power(self):
        """Measures current consumption and evaluates pass/fail criteria

        """
        # Add more offset to the first tests to ensure system collapse
        if self.current_test_name == self.tests[0]:
            self.mon_info['offset'] = self.mon_offset + 180
        else:
            self.mon_info['offset'] = self.mon_offset
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

    @test_tracker_info(uuid='a998dd2b-f5f1-4361-b5da-83e42a69e80b')
    def test_ble_scan_balan_wifi_2G_screen_on(self):
        """Measure power when WiFi is connected to 2.4 GHz and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. BLE starts a balanced scan and WiFi is connected to 2.4 GHz
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='ON')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['opportunistic'],
            self.mon_info['offset'], self.mon_info['duration'])

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='87146825-787a-4ea7-9622-30e9286c8a76')
    def test_filter_ble_scan_low_power_wifi_2G_screen_off(self):
        """Measure power when WiFi is connected to 2.4 GHz and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. BLE starts a filtered low power scan and WiFi is connected to 2G
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_power'],
            self.mon_info['offset'], self.mon_info['duration'])

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='2e645deb-b744-4272-8578-5d4cb159d5aa')
    def test_filter_ble_scan_low_power_wifi_5G_screen_off(self):
        """Measure power when WiFi is connected to 5 GHz and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. BLE starts a filtered low power scan and WiFi is connected to 5G
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_power'],
            self.mon_info['offset'], self.mon_info['duration'])

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='d458bc41-f1c8-4ed6-a7b5-0bec34780dda')
    def test_wifi_scan_bt_on_screen_off(self):
        """Measure power when WiFi is scanning and BT is doing a page scan

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. WiFi is scanning and BT is doing a page scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='6d9c0e8e-6a0f-458b-84d2-7d60fc254170')
    def test_wifi_scan_ble_filter_low_power_scan_screen_off(self):
        """Measure power when WiFi is scanning and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. WiFi is scanning and BLE is doing a low power filtered scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_power'],
            self.mon_info['offset'], self.mon_info['duration'])
        time.sleep(2)

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='ba52317f-426a-4688-a0a5-1394bcc7b092')
    def test_wifi_scan_ble_filter_low_lat_scan_screen_off(self):
        """Measure power when WiFi is scanning and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. WiFi is scanning and BLE is doing a low latency filtered scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_latency'],
            self.mon_info['offset'], self.mon_info['duration'])
        time.sleep(2)

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='b4c63eac-bc77-4e76-afff-ade98dde4411')
    def test_wifi_pno_scan_ble_filter_low_lat_scan_screen_off(self):
        """Measure power when WiFi disconnected (PNO scan) and BLE is scanning

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. WiFi is disconnected (PNOsscan) and BLE is doing a low latency
           filtered scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')

        # Start BLE scan
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_latency'],
            self.mon_info['offset'], self.mon_info['duration'])
        time.sleep(1)

        # Set attenuator to make WiFi disconnect and start PNO scans
        self.log.info('Set attenuation so device loses connection')
        [
            self.attenuators[i].set_atten(
                self.atten_level[self.current_test_name][i])
            for i in range(self.num_atten)
        ]

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='798796dc-960c-42b2-a835-2b2aefa028d5')
    def test_cellular_verizon_on_wifi_scan_screen_off(self):
        """Measure power when cellular is ON, WiFi is scanning and BT is OFF

        Steps:
        1. Disables gestures and location
        2. WiFi is scanning and cellular is idle (Verizon)
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='OFF',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF',
            regular_mode=True)

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='6ae44d84-0e68-4524-99b2-d3bfbd2253b8')
    def test_cellular_on_wifi_scan_ble_backgnd_scan_low_power_screen_off(self):
        """Measure power when cellular is ON, WiFi and BLE are scanning

        Steps:
        1. Disables gestures and location
        2. WiFi is scanning and cellular is idle (Verizon) and BLE is doing
           a low power background scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='OFF',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF',
            regular_mode=True)

        # Start BLE background scans
        self.dut.adb.shell(btutils.BLE_LOCATION_SCAN_ENABLE)
        time.sleep(1)
        self.dut.droid.bluetoothEnableBLE()
        time.sleep(2)
        self.dut.log.info('BLE is ON')
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_power'],
            self.mon_info['offset'], self.mon_info['duration'])
        time.sleep(2)

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()

    @test_tracker_info(uuid='2cb915a3-6319-4ac4-9e4d-9325b3b731c8')
    def test_cellular_on_wifi_scan_ble_backgnd_scan_low_lat_screen_off(self):
        """Measure power when cellular is ON, WiFi and BLE are scanning

        Steps:
        1. Disables gestures and location
        2. WiFi is scanning and cellular is idle (Verizon) and BLE is doing
           a low latency background scan
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        # Set phone in the desired wireless mode
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='OFF',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF',
            regular_mode=True)

        # Start BLE background scans
        self.dut.adb.shell(btutils.BLE_LOCATION_SCAN_ENABLE)
        time.sleep(1)
        self.dut.droid.bluetoothEnableBLE()
        time.sleep(2)
        self.dut.log.info('BLE is ON')
        btutils.start_pmc_ble_scan(
            self.dut, ble_scan_settings_modes['low_latency'],
            self.mon_info['offset'], self.mon_info['duration'])
        time.sleep(2)

        # Start WiFi connectivity scans
        self.dut.adb.shell_nb(self.PERIODIC_WIFI_SCAN)
        self.log.info('Started connectivity scans:')
        self.log.info(self.PERIODIC_WIFI_SCAN)

        # Measure power
        self.measure_power()
