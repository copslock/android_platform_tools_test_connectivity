#!/usr/bin/env python3.4
#
#   Copyright 2018 - The Android Open Source Project
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

import scapy.all as scapy
import time
from acts.test_utils.power import IperfHelper as IPH
from acts.test_utils.power import PowerCellularLabBaseTest as PWCEL
from acts.test_utils.tel.tel_test_utils import WIFI_CONFIG_APBAND_2G
from acts.test_utils.tel.tel_test_utils import WIFI_CONFIG_APBAND_5G
from acts.test_utils.wifi import wifi_power_test_utils as wputils
from acts.test_utils.wifi import wifi_test_utils as wutils


class PowerTelTrafficTest(PWCEL.PowerCellularLabBaseTest):
    """ Cellular traffic power test.

    Inherits from PowerCellularLabBaseTest. Parses config specific
    to this kind of test. Contains methods to start data traffic
    between a local instance of iPerf and one running in the dut.

    """

    # Keywords for test name parameters
    PARAM_TRAFFIC_PATTERN = 'pattern'

    # Iperf waiting time
    IPERF_MARGIN = 10

    def __init__(self, controllers):
        """ Class initialization.

        Sets test parameters to initial values.
        """

        super().__init__(controllers)

        # Traffic pattern variables. Values are set later
        # when reading config from test name.
        self.traffic_pattern_dl = 0
        self.traffic_pattern_ul = 0

    def setup_test(self):
        """ Executed before every test case.

        Parses test configuration from the test name and prepares
        the simulation for measurement.
        """

        # Call parent method first to setup simulation
        if not super().setup_test():
            return False

        try:
            values = self.consume_parameter(self.PARAM_TRAFFIC_PATTERN, 2)
            self.traffic_pattern_dl = int(values[1])
            self.traffic_pattern_ul = int(values[2])
        except:
            self.log.error("The test name has to include parameter {} followed by two int values separated by an "
                           "underscore indicating DL and UL traffic percentage.".format(self.PARAM_TRAFFIC_PATTERN))
            return False

        return True

    def teardown_test(self):
        """Tear down necessary objects after test case is finished.

        """

        for ips in self.iperf_servers:
            ips.stop()

    def power_tel_traffic_test(self):
        """ Measures power and throughput during data transmission.

        Measurement step in this test. Starts iPerf client in the DUT and then
        initiates power measurement. After that, DUT is connected again and
        the result from iPerf is collected. Pass or fail is decided with a
        threshold value.
        """

        # Start data traffic
        client_iperf_helper = self.start_tel_traffic(self.dut)

        # Measure power
        self.collect_power_data()

        # Wait for iPerf to finish
        time.sleep(self.IPERF_MARGIN + 2)

        # Collect throughput measurement
        throughput = []
        for iph in client_iperf_helper:
            print('Setting: {}\n'.format(iph.iperf_args))
            throughput.append(iph.process_iperf_results(self.dut, self.log, self.iperf_servers, self.test_name))

        # Check if power measurement is below the required value
        # self.pass_fail_check()

        return self.test_result, throughput

    def start_tel_traffic(self, client_host):
        """ Starts iPerf in the indicated device and initiates traffic.

        Starts the required iperf clients and servers according to the traffic
        pattern config in the current test.

        Args:
            client_host: Android device handler in which to start the iperf client.

        Returns:
            A list of iperf helpers.
        """

        # The iPerf server is hosted in this computer
        self.iperf_server_address = scapy.get_if_addr(self.pkt_sender.interface)

        # Start iPerf traffic
        iperf_helpers = []

        if self.traffic_pattern_ul > 0 and self.traffic_pattern_dl > 0:
            # Bidirectional traffic
            # Calculate traffic limit to do traffic shaping
            max_t_ul = self.simulation.maximum_uplink_throughput() * 0.98 * self.traffic_pattern_ul / 100
            max_t_dl = self.simulation.maximum_downlink_throughput() * 0.98 * self.traffic_pattern_dl / 100
            # Initiate traffic
            iperf_helpers.append(self.start_iperf_traffic(client_host, server_idx=len(iperf_helpers), traffic_direction='UL', bandwidth=max_t_ul))
            iperf_helpers.append(self.start_iperf_traffic(client_host, server_idx=len(iperf_helpers), traffic_direction='DL', bandwidth=max_t_dl))
        elif self.traffic_pattern_ul > 0:
            # Uplink traffic
            iperf_helpers.append(self.start_iperf_traffic(client_host, server_idx=len(iperf_helpers), traffic_direction='UL'))
        elif self.traffic_pattern_dl > 0:
            # Downlink traffic
            iperf_helpers.append(self.start_iperf_traffic(client_host, server_idx=len(iperf_helpers), traffic_direction='DL'))

        return iperf_helpers

    def start_iperf_traffic(self, client_host, server_idx, traffic_direction, bandwidth = 0):
        """Starts iPerf data traffic.

        Starts an iperf client in an android device and a server locally.

        Args:
            client_host: android device handler in which to start the iperf client
            server_idx: id of the iperf server to connect to
            traffic_direction: has to be either 'UL' or 'DL'
            bandwidth: bandwidth limit for data traffic

        Returns:
            An IperfHelper object for the started client/server pair.
        """

        config = {
            'traffic_type': 'TCP',
            'duration': self.mon_duration + self.mon_offset + self.IPERF_MARGIN,
            'start_meas_time': 4,
            'server_idx': server_idx,
            'port': self.iperf_servers[server_idx].port,
            'traffic_direction': traffic_direction
        }

        # If bandwidth is equal to zero then no bandwith requirements are set
        if bandwidth > 0:
            config['bandwidth'] = bandwidth

        iph = IPH.IperfHelper(config)

        # Start the server locally
        self.iperf_servers[server_idx].start()

        # Start the client in the android device
        wputils.run_iperf_client_nonblocking(client_host, self.iperf_server_address, iph.iperf_args)

        return iph


class PowerTelRvRTest(PowerTelTrafficTest):
    """ Gets Range vs Rate curves while measuring power consumption.

    Uses PowerTelTrafficTest as a base class.
    """

    # Test name configuration keywords
    PARAM_SWEEP = "sweep"
    PARAM_SWEEP_UPLINK = "uplink"
    PARAM_SWEEP_DOWNLINK = "downlink"

    # Sweep values. Need to be set before starting test by test
    # function or child class.
    downlink_power_sweep = None
    uplink_power_sweep = None

    def setup_test(self):
        """ Executed before every test case.

        Parses test configuration from the test name and prepares
        the simulation for measurement.
        """

        # Call parent method first to setup simulation
        if not super().setup_test():
            return False


        # Get which power value to sweep from config

        try:
            values = self.consume_parameter(self.PARAM_SWEEP, 1)

            if values[1] == self.PARAM_SWEEP_UPLINK:
                self.sweep = self.PARAM_SWEEP_UPLINK
            elif values[1] == self.PARAM_SWEEP_DOWNLINK:
                self.sweep = self.PARAM_SWEEP_DOWNLINK
            else:
                raise ValueError()
        except:
            self.log.error("The test name has to include parameter {} followed by either {} or {}.".format(
                self.PARAM_SWEEP,
                self.PARAM_SWEEP_DOWNLINK,
                self.PARAM_SWEEP_UPLINK)
            )
            return False

        return True

    def power_tel_rvr_test(self):
        """ Main function for the RvR test.

        Produces the RvR curve according to the indicated sweep values.
        """

        if self.sweep == self.PARAM_SWEEP_DOWNLINK:
            sweep_range = self.downlink_power_sweep
        elif self.sweep == self.PARAM_SWEEP_UPLINK:
            sweep_range = self.uplink_power_sweep

        current = []
        throughput = []

        for pw in sweep_range:

            if self.sweep == self.PARAM_SWEEP_DOWNLINK:
                self.simulation.set_downlink_rx_power(pw)
            elif self.sweep == self.PARAM_SWEEP_UPLINK:
                self.simulation.set_uplink_tx_power(pw)

            i, t = self.power_tel_traffic_test()
            self.log.info("---------------------")
            self.log.info("{} -- {} --".format(self.sweep, pw))
            self.log.info("{} ----- {}".format(i, t[0]))
            self.log.info("---------------------")

            current.append(i)
            throughput.append(t[0])

        print(sweep_range)
        print(current)
        print(throughput)


class PowerTelTetheringTest(PowerTelTrafficTest):
    """ Cellular traffic over WiFi tethering power test.

    Treated as a different case of data traffic. Inherits from PowerTelTrafficTest
    and only needs to make a change in the measurement step.
    """

    # Test name configuration keywords
    PARAM_WIFI_BAND = "wifiband"
    PARAM_2G_BAND = "2g"
    PARAM_5G_BAND = "5g"

    def __init__(self, controllers):
        """ Class initialization

        Set attributes to default values.
        """

        super().__init__(controllers)

        self.wifi_band = WIFI_CONFIG_APBAND_2G

    def power_tel_tethering_test(self):
        """ Measure power and throughput during data transmission.

        Starts WiFi tethering in the DUT and connects a second device. Then
        the iPerf client is hosted in the second android device.

        """

        # Setup tethering

        # The second device needs to have a country code to be able to
        # use the 5GHz band
        self.android_devices[1].droid.wifiSetCountryCode('US')

        self.network = { "SSID": "Pixel_1030", "password": "1234567890" }

        wutils.start_wifi_tethering(self.dut,
                                    self.network[wutils.WifiEnums.SSID_KEY],
                                    self.network[wutils.WifiEnums.PWD_KEY],
                                    self.wifi_band)

        wutils.wifi_connect(self.android_devices[1], self.network, check_connectivity=False)

        # Start data traffic
        client_iperf_helper = self.start_tel_traffic(self.android_devices[1])

        # Measure power
        self.collect_power_data()

        # Wait for iPerf to finish
        time.sleep(self.IPERF_MARGIN + 2)

        # Collect throughput measurement
        for iph in client_iperf_helper:
            print('Setting: {}\n'.format(iph.iperf_args))
            iph.process_iperf_results(self.android_devices[1], self.log, self.iperf_servers, self.test_name)

        # Checks if power is below the required threshold.
        self.pass_fail_check()


    def setup_test(self):
        """ Executed before every test case.

        Parses test configuration from the test name and prepares
        the simulation for measurement.
        """

        # Call parent method first to setup simulation
        if not super().setup_test():
            return False

        try:
            values = self.consume_parameter(self.PARAM_WIFI_BAND, 1)

            if values[1] == self.PARAM_2G_BAND:
                self.wifi_band = WIFI_CONFIG_APBAND_2G
            elif values[1] == self.PARAM_5G_BAND:
                self.wifi_band = WIFI_CONFIG_APBAND_5G
            else:
                raise ValueError()
        except:
            self.log.error("The test name has to include parameter {} followed by either {} or {}.".format(
                self.PARAM_WIFI_BAND,
                self.PARAM_2G_BAND,
                self.PARAM_5G_BAND)
            )
            return False

        return True
