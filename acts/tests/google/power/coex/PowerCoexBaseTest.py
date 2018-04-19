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

from acts import base_test
from acts import utils
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.controllers.ap_lib import hostapd_constants as hc
from acts.test_decorators import test_tracker_info


class PowerCoexBaseTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        self.access_point = self.access_points[0]
        req_params = ['coexbaseline_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.coexbaseline_params)
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

    def teardown_class(self):
        """Clean up the test class after all tests finish running

        """
        self.mon.usb('on')
        self.access_point.close()  # Just as a precaution

    def teardown_test(self):
        """Tear down necessary objects/settings after test finishes

        """
        if self.brconfigs:
            self.access_point.bridge.teardown(self.brconfigs)
        self.access_point.close()

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

    @test_tracker_info(uuid='f3fc6667-73d8-4fb5-bdf3-0253e52043b1')
    def test_wifi_discon_bt_on_screen_off(self):
        """Measure power when WiFi is ON (disconnected) and BT is toggled ON

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON BT and WiFi (disconnected)
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self, bt_on='ON', wifi_on='ON', screen_status='OFF')
        self.measure_power()

    @test_tracker_info(uuid='1bec36d1-f7b2-4a4b-9f5d-dfb5ed985649')
    def test_wifi_2G_bt_on_screen_off(self):
        """Measure power when WiFi is connected to 2G and BT is ON

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON BT and WiFi is connected to 2.4 GHz
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF')
        self.measure_power()

    @test_tracker_info(uuid='88170cad-8336-4dff-8e53-3cc693d01b72')
    def test_wifi_5G_bt_on_screen_off(self):
        """Measure power when WiFi is connected to 5G and BT is ON

        Steps:
        1. Sets the phone in airplane mode, disables gestures and location
        2. Turns ON BT and WiFi is connected to 5 GHz
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF')
        self.measure_power()

    @test_tracker_info(uuid='b82e59a9-9b27-4ba2-88f6-48d7917066f4')
    def test_bt_on_cellular_verizon_on_screen_off(self):
        """Measure power when BT and cellular (Verizon) are ON

        Steps:
        1. Disables gestures and location
        2. Turns ON BT and cellular (Verizon)
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='OFF',
            screen_status='OFF',
            regular_mode=True)
        self.measure_power()

    @test_tracker_info(uuid='6409a02e-d63a-4c46-a210-1d5f1b006556')
    def test_cellular_verizon_on_wifi_5G_screen_off(self):
        """Measure power when WiFi is connected to 5G and cellular is ON

        Steps:
        1. Disables gestures and location
        2. Connect Wifi to 5 GHz and have cellular idle (Verizon)
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='OFF',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF',
            regular_mode=True)
        self.measure_power()

    @test_tracker_info(uuid='6f22792f-b304-4804-853d-e41484d442ab')
    def test_cellular_verizon_on_wifi_2G_screen_off(self):
        """Measure power when WiFi is connected to 2G and cellular is ON

        Steps:
        1. Disables gestures and location
        2. Connect Wifi to 2.4 GHz and have cellular idle (Verizon)
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='OFF',
            wifi_on='ON',
            network=self.main_network[hc.BAND_2G],
            screen_status='OFF',
            regular_mode=True)
        self.measure_power()

    @test_tracker_info(uuid='11bb1683-4544-46b4-ad4a-875e31323729')
    def test_cellular_verizon_on_bt_on_wifi_5G_screen_off(self):
        """Measure power when WiFi is connected to 5G, BT and cellular are ON

        Steps:
        1. Disables gestures and location
        2. Connect Wifi to 5 GHz and turn BT and cellular ON
        3. Measures the power consumption
        4. Asserts pass/fail criteria based on measured power
        """
        self.brconfigs = wputils.setup_phone_wireless(
            test_class=self,
            bt_on='ON',
            wifi_on='ON',
            network=self.main_network[hc.BAND_5G],
            screen_status='OFF',
            regular_mode=True)
        self.measure_power()
