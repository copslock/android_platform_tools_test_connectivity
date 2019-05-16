#!/usr/bin/env python3
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

import itertools

from acts import utils
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib import hostapd_config
from acts.test_utils.abstract_devices.wlan_device import create_wlan_device
from acts.test_utils.abstract_devices.utils_lib.wlan_utils import setup_ap_and_associate
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

FREQUENCY_24 = ['2.4GHz']
FREQUENCY_5 = ['5GHz']
CHANNEL_BANDWIDTH_20 = ['HT20']
CHANNEL_BANDWIDTH_40_LOWER = ['HT40-']
CHANNEL_BANDWIDTH_40_UPPER = ['HT40+']
LDPC = [hostapd_constants.N_CAPABILITY_LDPC, '']
TX_STBC = [hostapd_constants.N_CAPABILITY_TX_STBC, '']
RX_STBC = [hostapd_constants.N_CAPABILITY_RX_STBC1, '']
SGI_20 = [hostapd_constants.N_CAPABILITY_SGI20, '']
SGI_40 = [hostapd_constants.N_CAPABILITY_SGI40, '']
DSSS_CCK = [hostapd_constants.N_CAPABILITY_DSSS_CCK_40, '']
INTOLERANT_40 = [hostapd_constants.N_CAPABILITY_40_INTOLERANT, '']
MAX_AMPDU_7935 = [hostapd_constants.N_CAPABILITY_MAX_AMSDU_7935, '']
SMPS = [hostapd_constants.N_CAPABILITY_SMPS_STATIC, '']


def generate_test_name(settings):
    """Generates a string based on the n_capabilities for a test case

    Args:
        settings: A dictionary of hostapd constant n_capabilities.

    Returns:
        A string that represents a test case name.
    """
    ret = []
    for cap in hostapd_constants.N_CAPABILITIES_MAPPING.keys():
        if cap in settings['n_capabilities']:
            ret.append(hostapd_constants.N_CAPABILITIES_MAPPING[cap])
    return '%s_%s_%s' % (settings['frequency'],
                         settings['chbw'],
                         ''.join(ret))


class WlanPhyCompliance11NTest(WifiBaseTest):
    """Tests for validating 11n PHYS.

    Test Bed Requirement:
    * One Android device or Fuchsia device
    * One Access Point
    """
    def __init__(self, controllers):
        WifiBaseTest.__init__(self, controllers)
        if 'dut' in self.user_params:
            if self.user_params['dut'] == 'fuchsia_devices':
                self.dut = create_wlan_device(self.fuchsia_devices[0])
            elif self.user_params['dut'] == 'android_devices':
                self.dut = create_wlan_device(self.android_devices[0])
            else:
                raise ValueError('Invalid DUT specified in config. (%s)'
                                 % self.user_params['dut'])
        else:
            # Default is an android device, just like the other tests
            self.dut = create_wlan_device(self.android_devices[0])

        self.access_point = self.access_points[0]

    def setup_class(self):
        self.access_point.stop_all_aps()

    def setup_test(self):
        if hasattr(self, "android_devices"):
            for ad in self.android_devices:
                ad.droid.wakeLockAcquireBright()
                ad.droid.wakeUpNow()
        self.dut.wifi_toggle_state(True)

    def teardown_test(self):
        if hasattr(self, "android_devices"):
            for ad in self.android_devices:
                ad.droid.wakeLockRelease()
                ad.droid.goToSleepNow()
        self.dut.turn_location_off_and_scan_toggle_off()
        self.dut.disconnect()
        self.dut.reset_wifi()
        self.access_point.stop_all_aps()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.get_log(test_name, begin_time)

    def setup_and_connect(self, ap_settings):
        """Generates a hostapd config, setups up the AP with that config, then
           attempts to associate a DUT

        Args:
               ap_settings: A dictionary of hostapd constant n_capabilities.
        """
        temp_n_capabilities = list(ap_settings['n_capabilities'])
        n_capabilities = []
        for n_capability in temp_n_capabilities:
            if n_capability in hostapd_constants.N_CAPABILITIES_MAPPING.keys():
                n_capabilities.append(n_capability)

        if ap_settings['chbw'] == 'HT20' or ap_settings['chbw'] == 'HT40+':
            if ap_settings['frequency'] == '2.4GHz':
                channel = 1
            elif ap_settings['frequency'] == '5GHz':
                channel = 36
            else:
                raise ValueError('Invalid frequence: %s'
                                 % ap_settings['frequency'])

        if ap_settings['chbw'] == 'HT40-':
            if ap_settings['frequency'] == '2.4GHz':
                channel = 11
            elif ap_settings['frequency'] == '5GHz':
                channel = 60
            else:
                raise ValueError('Invalid frequency: %s'
                                 % ap_settings['frequency'])

        if ap_settings['chbw'] == 'HT40-' or ap_settings['chbw'] == 'HT40+':
            if hostapd_config.ht40_plus_allowed(channel):
                extended_channel = hostapd_constants.N_CAPABILITY_HT40_PLUS
            elif hostapd_config.ht40_minus_allowed(channel):
                extended_channel = hostapd_constants.N_CAPABILITY_HT40_MINUS
            else:
                raise ValueError('Invalid channel: %s'
                                 % channel)
            n_capabilities.append(extended_channel)

        setup_ap_and_associate(
            access_point=self.access_point,
            client=self.dut,
            profile_name='whirlwind',
            mode=hostapd_constants.MODE_11N_MIXED,
            channel=channel,
            n_capabilities=n_capabilities,
            ac_capabilities=[],
            force_wmm=True,
            ssid=utils.rand_ascii_str(20))

    def test_11n_capabilities_24_HT20(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_24,
                                             CHANNEL_BANDWIDTH_20,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             INTOLERANT_40,
                                             MAX_AMPDU_7935,
                                             SMPS):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)

    def test_11n_capabilities_24_HT40_lower(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_24,
                                             CHANNEL_BANDWIDTH_40_LOWER,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             SGI_40,
                                             MAX_AMPDU_7935,
                                             SMPS,
                                             DSSS_CCK):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)

    def test_11n_capabilities_24_HT40_upper(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_24,
                                             CHANNEL_BANDWIDTH_40_UPPER,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             SGI_40,
                                             MAX_AMPDU_7935,
                                             SMPS,
                                             DSSS_CCK):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)

    def test_11n_capabilities_5_HT20(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_5,
                                             CHANNEL_BANDWIDTH_20,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             INTOLERANT_40,
                                             MAX_AMPDU_7935,
                                             SMPS):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)

    def test_11n_capabilities_5_HT40_lower(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_5,
                                             CHANNEL_BANDWIDTH_40_LOWER,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             SGI_40,
                                             MAX_AMPDU_7935,
                                             SMPS,
                                             DSSS_CCK):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)

    def test_11n_capabilities_5_HT40_upper(self):
        test_list = []
        for combination in itertools.product(FREQUENCY_5,
                                             CHANNEL_BANDWIDTH_40_UPPER,
                                             LDPC,
                                             TX_STBC,
                                             RX_STBC,
                                             SGI_20,
                                             SGI_40,
                                             MAX_AMPDU_7935,
                                             SMPS,
                                             DSSS_CCK):
            test_frequency = combination[0]
            test_chbw = combination[1]
            n_capabilities = combination[2:]
            test_list.append({'frequency': test_frequency,
                              'chbw': test_chbw,
                              'n_capabilities': n_capabilities})
        self.run_generated_testcases(
            self.setup_and_connect,
            settings=test_list,
            name_func=generate_test_name)
