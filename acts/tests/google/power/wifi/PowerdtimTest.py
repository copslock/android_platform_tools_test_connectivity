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
import time
from acts import base_test
from acts import utils
from acts.controllers.ap_lib import hostapd_constants as hc
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi import wifi_power_test_utils as wputils


class PowerdtimTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        base_test.BaseTestClass.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        self.access_point = self.access_points[0]
        req_params = ['dtimtest_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.dtimtest_params)
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon = self.monsoons[0]
        self.mon.set_max_current(8.0)
        self.mon.set_voltage(4.2)
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

    def teardown_test(self):
        """Tear down necessary objects after test case is finished.

        Bring down the AP interface and connect device back on.
        """
        self.log.info('Tearing down the test case')
        self.access_point.bridge.teardown(self.brconfigs)
        self.access_point.close()
        self.mon.usb('on')

    def teardown_class(self):

        self.log.info('Tearing down the test class')
        self.access_point.close()
        self.mon.usb('on')

    def unpack_testparams(self, bulk_params):
        """Unpack all the test specific parameters.

        Args:
            bulk_params: dict with all test specific params in the config file
        """
        for key in bulk_params.keys():
            setattr(self, key, bulk_params[key])

    def dtim_test_func(self, dtim, screen_status, network, dtim_max=10):
        """A reusable function for DTIM test.
        Covering different DTIM value, with screen ON or OFF and 2g/5g network

        Args:
            dtim: the value for DTIM set on the phone
            screen_status: screen on or off
            network: a dict of information for the network to connect
        """
        # Initialize the dut to rock-bottom state
        wputils.change_dtim(
            self.dut, gEnableModulatedDTIM=dtim, gMaxLIModulatedDTIM=dtim_max)
        self.dut.log.info('DTIM value of the phone is now {}'.format(dtim))
        wputils.dut_rockbottom(self.dut)
        wutils.wifi_toggle_state(self.dut, True)
        [
            self.attenuators[i].set_atten(self.atten_level['zero_atten'][i])
            for i in range(self.num_atten)
        ]
        self.log.info('Set attenuation level to connect to the AP')
        # Set up the AP
        self.brconfigs = wputils.ap_setup(self.access_point, network, 20)
        wutils.wifi_connect(self.dut, network)
        if screen_status == 'OFF':
            self.dut.droid.goToSleepNow()
            self.dut.log.info('Screen is OFF')
        time.sleep(5)
        # Collect power data and plot
        begin_time = utils.get_current_epoch_time()
        file_path, avg_current = wputils.monsoon_data_collect_save(
            self.dut, self.mon_info, self.current_test_name)
        wputils.monsoon_data_plot(self.mon_info, file_path)
        # Take Bugreport
        if bool(self.bug_report) == True:
            self.dut.take_bug_report(self.test_name, begin_time)
        # Pass and fail check
        wputils.pass_fail_check(self, avg_current)

    # Test cases
    @test_tracker_info(uuid='2a70a78b-93a8-46a6-a829-e1624b8239d2')
    def test_2g_screenoff_dtimx1(self):
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(1, 'OFF', network)

    @test_tracker_info(uuid='b6c4114d-984a-4269-9e77-2bec0e4b6e6f')
    def test_2g_screenoff_dtimx2(self):
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(2, 'OFF', network)

    @test_tracker_info(uuid='2ae5bc29-3d5f-4fbb-9ff6-f5bd499a9d6e')
    def test_2g_screenoff_dtimx4(self):
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(4, 'OFF', network)

    @test_tracker_info(uuid='b37fa75f-6166-4247-b15c-adcda8c7038e')
    def test_2g_screenoff_dtimx5(self):
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(5, 'OFF', network)

    @test_tracker_info(uuid='384d3b0f-4335-4b00-8363-308ec27a150c')
    def test_2g_screenon_dtimx1(self):
        """With screen on, modulated dtim isn't wokring, always DTIMx1.
        So not running through all DTIM cases

        """
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(1, 'ON', network)

    @test_tracker_info(uuid='79d0f065-2c46-4400-b02c-5ad60e79afea')
    def test_2g_screenon_dtimx4(self):
        """Run only extra DTIMx4 for screen on to compare with DTIMx1.
        They should be the same if everything is correct.

        """
        network = self.main_network[hc.BAND_2G]
        self.dtim_test_func(4, 'ON', network)

    @test_tracker_info(uuid='5e2f73cb-7e4e-4a25-8fd5-c85adfdf466e')
    def test_5g_screenoff_dtimx1(self):
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(1, 'OFF', network)

    @test_tracker_info(uuid='017f57c3-e133-461d-80be-d025d1491d8a')
    def test_5g_screenoff_dtimx2(self):
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(2, 'OFF', network)

    @test_tracker_info(uuid='b84a1cb3-9573-4bfd-9875-0f33cb171cc5')
    def test_5g_screenoff_dtimx4(self):
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(4, 'OFF', network)

    @test_tracker_info(uuid='75644df4-2cc8-4bbd-8985-0656a4f9d056')
    def test_5g_screenoff_dtimx5(self):
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(5, 'OFF', network)

    @test_tracker_info(uuid='327af44d-d9e7-49e0-9bda-accad6241dc7')
    def test_5g_screenon_dtimx1(self):
        """With screen on, modulated dtim isn't wokring, always DTIMx1.
        So not running through all DTIM cases

        """
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(1, 'ON', network)

    @test_tracker_info(uuid='8b32585f-2517-426b-a2c9-8087093cf991')
    def test_5g_screenon_dtimx4(self):
        """Run only extra DTIMx4 for screen on to compare with DTIMx1.
        They should be the same if everything is correct.

        """
        network = self.main_network[hc.BAND_5G]
        self.dtim_test_func(4, 'ON', network)
