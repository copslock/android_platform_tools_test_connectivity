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

import time
from acts.test_utils.tel.tel_test_utils import WIFI_CONFIG_APBAND_2G
from acts.test_utils.tel.tel_test_utils import WIFI_CONFIG_APBAND_5G
from acts.test_utils.wifi import wifi_test_utils as wutils
from google.power.tel.lab.PowerTelTrafficTest import PowerTelTrafficTest


class PowerTelHotspotTest(PowerTelTrafficTest):
    """ Cellular traffic over WiFi tethering power test.

    Treated as a different case of data traffic. Inherits from
    PowerTelTrafficTest and only needs to make a change in the measurement step.
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

        self.network = {"SSID": "Pixel_1030", "password": "1234567890"}

        wutils.start_wifi_tethering(
            self.dut, self.network[wutils.WifiEnums.SSID_KEY],
            self.network[wutils.WifiEnums.PWD_KEY], self.wifi_band)

        wutils.wifi_connect(
            self.android_devices[1], self.network, check_connectivity=False)

        # Start data traffic
        client_iperf_helper = self.start_tel_traffic(self.android_devices[1])

        # Measure power
        self.collect_power_data()

        # Wait for iPerf to finish
        time.sleep(self.IPERF_MARGIN + 2)

        # Collect throughput measurement
        for iph in client_iperf_helper:
            print('Setting: {}\n'.format(iph.iperf_args))
            iph.process_iperf_results(self.android_devices[1], self.log,
                                      self.iperf_servers, self.test_name)

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
            self.log.error(
                "The test name has to include parameter {} followed by "
                "either {} or {}.".
                format(self.PARAM_WIFI_BAND, self.PARAM_2G_BAND,
                       self.PARAM_5G_BAND))
            return False

        return True
