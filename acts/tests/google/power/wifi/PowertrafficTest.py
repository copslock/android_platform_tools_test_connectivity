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
import math
import os
import time
from acts import base_test
from acts import utils
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest
import acts.controllers.iperf_server as ipf

TEMP_FILE = '/sdcard/Download/tmp.log'


class PowertrafficTest(base_test.BaseTestClass):
    def __init__(self, controllers):

        WifiBaseTest.__init__(self, controllers)

    def setup_class(self):

        self.log = logging.getLogger()
        self.dut = self.android_devices[0]
        req_params = ['traffictest_params', 'custom_files']
        self.unpack_userparams(req_params)
        self.unpack_testparams(self.traffictest_params)
        self.num_atten = self.attenuators[0].instrument.num_atten
        self.mon_data_path = os.path.join(self.log_path, 'Monsoon')
        self.mon_duration = self.iperf_duration - 10
        self.mon = self.monsoons[0]
        self.mon.set_max_current(8.0)
        self.mon.set_voltage(4.2)
        self.mon.attach_device(self.dut)
        self.mon_info = wputils.create_monsoon_info(self)
        self.iperf_server = self.iperf_servers[0]
        self.access_point = self.access_points[0]
        self.pkt_sender = self.packet_senders[0]
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

        Bring down the AP interface, delete the bridge interface, stop IPERF
        server and reset the ethernet interface for iperf traffic
        """
        self.log.info('Tearing down the test case')
        self.iperf_server.stop()
        self.access_point.bridge.teardown(self.brconfigs)
        self.access_point.close()
        wputils.reset_host_interface(self.pkt_sender.interface)
        self.mon.usb('on')

    def teardown_class(self):
        """Clean up the test class after tests finish running

        """
        self.log.info('Tearing down the test class')
        self.mon.usb('on')
        self.access_point.close()

    def unpack_testparams(self, bulk_params):
        """Unpack all the test specific parameters.

        Args:
            bulk_params: dict with all test specific params in the config file
        """
        for key in bulk_params.keys():
            setattr(self, key, bulk_params[key])

    def iperf_power_test_func(self):
        """Test function for iperf power measurement at different RSSI level.

        Args:
            screen_status: screen ON or OFF
            band: desired band for AP to operate on
        """
        # Decode test parameters for the current test
        test_params = self.current_test_name.split('_')
        screen_status = test_params[2][6:]
        band = test_params[3]
        traffic_direction = test_params[4]
        traffic_type = test_params[5]
        signal_level = test_params[6][:-4]
        oper_mode = test_params[7]
        bandwidth = int(test_params[8])

        # Set device to rockbottom first
        wputils.dut_rockbottom(self.dut)
        wutils.wifi_toggle_state(self.dut, True)

        # Set up the AP
        network = self.main_network[band]
        self.brconfigs = wputils.ap_setup(self.access_point, network,
                                          bandwidth)

        # Wait for DHCP on the ethernet port and get IP as Iperf server address
        # Time out in 60 seconds if not getting DHCP address
        iface_eth = self.pkt_sender.interface
        self.iperf_server_address = wputils.wait_for_dhcp(iface_eth)

        # Set attenuator to desired level
        self.log.info('Set attenuation to desired RSSI level')
        atten_setting = band + '_' + signal_level
        for i in range(self.num_atten):
            attenuation = self.atten_level[atten_setting][i]
            self.attenuators[i].set_atten(attenuation)

        # Connect the phone to the AP
        wutils.wifi_connect(self.dut, network)
        time.sleep(5)
        if screen_status == 'off':
            self.dut.droid.goToSleepNow()
        RSSI = wputils.get_wifi_rssi(self.dut)

        # Construct the iperf command based on the test params
        iperf_args = '-i 1 -t {} -p {} -J'.format(self.iperf_duration,
                                                  self.iperf_server.port)
        if traffic_type == "UDP":
            iperf_args = iperf_args + "-u -b 2g"
        if traffic_direction == "DL":
            iperf_args = iperf_args + ' -R'
            use_client_output = True
        else:
            use_client_output = False
        # Parse the client side data to a file saved on the phone
        iperf_args = iperf_args + ' > %s' % TEMP_FILE

        # Run IPERF
        self.iperf_server.start()
        wputils.run_iperf_client_nonblocking(
            self.dut, self.iperf_server_address, iperf_args)

        # Collect power data and plot
        begin_time = utils.get_current_epoch_time()
        file_path, avg_current = wputils.monsoon_data_collect_save(
            self.dut, self.mon_info, self.current_test_name)

        # Get IPERF results
        RESULTS_DESTINATION = os.path.join(self.iperf_server.log_path,
                                           "iperf_client_output_{}.log".format(
                                               self.current_test_name))
        PULL_FILE = '{} {}'.format(TEMP_FILE, RESULTS_DESTINATION)
        self.dut.adb.pull(PULL_FILE)
        # Calculate the average throughput
        if use_client_output:
            iperf_file = RESULTS_DESTINATION
        else:
            iperf_file = self.iperf_server.log_files[-1]
        try:
            iperf_result = ipf.IPerfResult(iperf_file)
            throughput = (math.fsum(iperf_result.instantaneous_rates[:-1]) /
                          len(iperf_result.instantaneous_rates[:-1])) * 8
            self.log.info("The average throughput is {}".format(throughput))
        except:
            self.log.warning(
                "ValueError: Cannot get iperf result. Setting to 0")
            throughput = 0

        # Monsoon Power data plot with IPerf throughput information
        tag = '_RSSI_{0:d}dBm_Throughput_{1:.2f}Mbps'.format(RSSI, throughput)
        wputils.monsoon_data_plot(self.mon_info, file_path, tag)

        # Take Bugreport
        if bool(self.bug_report) == True:
            self.dut.take_bug_report(self.test_name, begin_time)
        # Pass and fail check
        wputils.pass_fail_check(self, avg_current)

    # Screen off TCP test cases
    @test_tracker_info(uuid='93f79f74-88d9-4781-bff0-8899bed1c336')
    def test_traffic_screenoff_2g_DL_TCP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='147eff45-97d7-47c0-b306-f84d9adecd9b')
    def test_traffic_screenoff_2g_DL_TCP_mediumRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='5982268b-57e4-40bf-848e-fee80fabf9d7')
    def test_traffic_screenoff_2g_DL_TCP_lowRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='c71a8c77-d355-4a82-b9f1-7cc8b888abd8')
    def test_traffic_screenoff_5g_DL_TCP_highRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='307945a6-32b7-42d0-a26c-d439f1599963')
    def test_traffic_screenoff_5g_DL_TCP_mediumRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='e9a900a1-e263-45ad-bdf3-9c463f761d3c')
    def test_traffic_screenoff_5g_DL_TCP_lowRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='1d1d9a06-98e1-486e-a1db-2102708161ec')
    def test_traffic_screenoff_5g_DL_TCP_highRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='feeaad15-6893-4d49-aaf6-bf9802780f5d')
    def test_traffic_screenoff_5g_DL_TCP_mediumRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='f378679a-1c20-43a1-bff6-a6a5482a8e3d')
    def test_traffic_screenoff_5g_DL_TCP_lowRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='6a05f133-49e5-4436-ba84-0746f04021ef')
    def test_traffic_screenoff_5g_DL_TCP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='750bf1c3-2099-4b89-97dd-18f8e72df462')
    def test_traffic_screenoff_5g_DL_TCP_mediumRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='1ea458af-1ae0-40ee-853d-ac57b51d3eda')
    def test_traffic_screenoff_5g_DL_TCP_lowRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='43d9b146-3547-4a27-9d79-c9341c32ccda')
    def test_traffic_screenoff_2g_UL_TCP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='f00a868b-c8b1-4b36-8136-b39b5c2396a7')
    def test_traffic_screenoff_2g_UL_TCP_mediumRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='cd0c37ac-23fe-4dd1-9130-ccb2dfa71020')
    def test_traffic_screenoff_2g_UL_TCP_lowRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='f9173d39-b46d-4d80-a5a5-7966f5eed9de')
    def test_traffic_screenoff_5g_UL_TCP_highRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='cf77e1dc-30bc-4df9-88be-408f1fddc24f')
    def test_traffic_screenoff_5g_UL_TCP_mediumRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='48f91745-22dc-47c9-ace6-c2719df651d6')
    def test_traffic_screenoff_5g_UL_TCP_lowRSSI_VHT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='18456aa7-62f0-4560-a7dc-4d7e01f6aca5')
    def test_traffic_screenoff_5g_UL_TCP_highRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='8ad237d7-f5e1-45e1-a4a2-a010628a4db9')
    def test_traffic_screenoff_5g_UL_TCP_mediumRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='3e29173f-b950-4a41-a7f6-6cc0731bf477')
    def test_traffic_screenoff_5g_UL_TCP_lowRSSI_VHT_40(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='3d4cdb21-a1b0-4011-9956-ca0b7a9f3bec')
    def test_traffic_screenoff_5g_UL_TCP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='8427d3f0-9418-4b5c-aea9-7509e5959ce6')
    def test_traffic_screenoff_5g_UL_TCP_mediumRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='5ac91734-0323-464b-b04a-c7d3d7ff8cdf')
    def test_traffic_screenoff_5g_UL_TCP_lowRSSI_VHT_80(self):

        self.iperf_power_test_func()

    # Screen off UDP tests - only check 5g VHT 80
    @test_tracker_info(uuid='1ab4a4e2-bce2-4ff8-be9d-f8ed2bb617cd')
    def test_traffic_screenoff_5g_DL_UDP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='a2c66d63-e93f-42aa-a021-0c6cdfdc87b8')
    def test_traffic_screenoff_5g_DL_UDP_mediumRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='68e6f92a-ae15-4e76-81e7-a7b491e181fe')
    def test_traffic_screenoff_5g_DL_UDP_lowRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='258500f4-f177-43df-82a7-a64d66e90720')
    def test_traffic_screenoff_5g_UL_UDP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='3d2d3d45-575d-4080-86f9-b32a96963032')
    def test_traffic_screenoff_5g_UL_UDP_mediumRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='a17c7d0b-58ca-47b5-9f32-0b7a3d7d3d9d')
    def test_traffic_screenoff_5g_UL_UDP_lowRSSI_VHT_80(self):

        self.iperf_power_test_func()

    # Screen on point check
    @test_tracker_info(uuid='c1c71639-4463-4999-8f5d-7d9153402c79')
    def test_traffic_screenon_2g_DL_TCP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='40daebc4-45a2-4299-b724-e8cb917b86e8')
    def test_traffic_screenon_5g_DL_TCP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='2e286f36-1a47-4895-a0e8-a161d6a9fd9f')
    def test_traffic_screenon_2g_UL_TCP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='9f6b52cb-b48a-4382-8061-3d3a511a261a')
    def test_traffic_screenon_5g_UL_TCP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='59d79274-15cf-446b-a567-655c07f8a778')
    def test_traffic_screenon_2g_DL_UDP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='02891671-48cc-4186-9a95-3e02671477d0')
    def test_traffic_screenon_5g_DL_UDP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='02821540-7b08-4e4f-a1f1-b455fd4cec6e')
    def test_traffic_screenon_2g_UL_UDP_highRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='59ea06ac-3ac8-4ecc-abb1-bcde34f47358')
    def test_traffic_screenon_2g_UL_UDP_mediumRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='0cbbd849-7b59-4143-95e7-92cf1fd955dc')
    def test_traffic_screenon_2g_UL_UDP_lowRSSI_HT_20(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='d84f11d8-41a9-4ce8-a351-ebb0379d56c1')
    def test_traffic_screenon_5g_UL_UDP_highRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='01b6087c-b39a-441d-90e9-da659aa0db7f')
    def test_traffic_screenon_5g_UL_UDP_mediumRSSI_VHT_80(self):

        self.iperf_power_test_func()

    @test_tracker_info(uuid='7e16dcaa-128f-4874-ab52-2f43e25e6da8')
    def test_traffic_screenon_5g_UL_UDP_lowRSSI_VHT_80(self):

        self.iperf_power_test_func()
