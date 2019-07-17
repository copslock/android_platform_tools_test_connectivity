#!/usr/bin/env python3.4
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

import collections
import itertools
import json
import os
from acts import base_test
from acts import context
from acts.metrics.loggers.blackbox import BlackboxMetricLogger
from acts.test_utils.wifi import ota_chamber
from acts.test_utils.wifi import wifi_performance_test_utils as wputils
from functools import partial
from WifiPingTest import WifiPingTest
from WifiRvrTest import WifiRvrTest
from WifiRssiTest import WifiRssiTest
from WifiSensitivityTest import WifiSensitivityTest


class WifiOtaRvrTest(WifiRvrTest):
    """Class to test over-the-air RvR

    This class implements measures WiFi RvR tests in an OTA chamber. It enables
    setting turntable orientation and other chamber parameters to study
    performance in varying channel conditions
    """

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.failure_count_metric = BlackboxMetricLogger.for_test_case(
            metric_name='failure_count')

    def setup_class(self):
        WifiRvrTest.setup_class(self)
        self.ota_chamber = ota_chamber.create(
            self.user_params['OTAChamber'])[0]

    def teardown_class(self):
        WifiRvrTest.teardown_class(self)
        self.ota_chamber.reset_chamber()

    def setup_rvr_test(self, testcase_params):
        """Function that gets devices ready for the test.

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Set turntable orientation
        self.ota_chamber.set_orientation(testcase_params['orientation'])
        # Continue test setup
        WifiRvrTest.setup_rvr_test(self, testcase_params)

    def parse_test_params(self, test_name):
        """Function that generates test params based on the test name."""
        # Call parent parsing function
        testcase_params = WifiRvrTest.parse_test_params(self, test_name)
        # Add orientation information
        test_name_params = test_name.split('_')
        testcase_params['orientation'] = int(test_name_params[6][0:-3])
        return testcase_params

    def generate_test_cases(self, channels, modes, angles, traffic_types,
                            directions):
        test_cases = []
        testcase_wrapper = self._test_rvr
        allowed_configs = {
            'VHT20': [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 36, 40, 44, 48, 149, 153,
                157, 161
            ],
            'VHT40': [36, 44, 149, 157],
            'VHT80': [36, 149]
        }
        for channel, mode, angle, traffic_type, direction in itertools.product(
                channels, modes, angles, traffic_types, directions):
            if channel not in allowed_configs[mode]:
                continue
            testcase_name = 'test_rvr_{}_{}_ch{}_{}_{}deg'.format(
                traffic_type, direction, channel, mode, angle)
            setattr(self, testcase_name, testcase_wrapper)
            test_cases.append(testcase_name)
        return test_cases


class WifiOtaRvr_StandardOrientation_Test(WifiOtaRvrTest):
    def __init__(self, controllers):
        WifiOtaRvrTest.__init__(self, controllers)
        self.tests = self.generate_test_cases(
            [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161],
            ['VHT20', 'VHT40', 'VHT80'], list(range(0, 360,
                                                    45)), ['TCP'], ['DL'])


class WifiOtaRvr_SampleChannel_Test(WifiOtaRvrTest):
    def __init__(self, controllers):
        WifiOtaRvrTest.__init__(self, controllers)
        self.tests = self.generate_test_cases([6, 36, 149], ['VHT20', 'VHT80'],
                                              list(range(0, 360, 45)), ['TCP'],
                                              ['DL'])


class WifiOtaRvr_SingleOrientation_Test(WifiOtaRvrTest):
    def __init__(self, controllers):
        WifiOtaRvrTest.__init__(self, controllers)
        self.tests = self.generate_test_cases(
            [6, 36, 40, 44, 48, 149, 153, 157, 161],
            ['VHT20', 'VHT40', 'VHT80'], [0], ['TCP'], ['DL', 'UL'])


# Ping Tests
class WifiOtaPingTest(WifiPingTest):
    """Class to test over-the-air ping

    This class tests WiFi ping performance in an OTA chamber. It enables
    setting turntable orientation and other chamber parameters to study
    performance in varying channel conditions
    """

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)
        self.ping_range_metric = BlackboxMetricLogger.for_test_case(
            metric_name='ping_range')
        self.ping_rtt_metric = BlackboxMetricLogger.for_test_case(
            metric_name='ping_rtt')

    def setup_class(self):
        WifiPingTest.setup_class(self)
        self.ota_chamber = ota_chamber.create(
            self.user_params['OTAChamber'])[0]

    def teardown_class(self):
        self.process_testclass_results()
        self.ota_chamber.reset_chamber()

    def process_testclass_results(self):
        """Saves all test results to enable comparison."""
        WifiPingTest.process_testclass_results(self)

        range_vs_angle = collections.OrderedDict()
        for test in self.testclass_results:
            curr_params = self.parse_test_params(test['test_name'])
            curr_config = curr_params['channel']
            if curr_config in range_vs_angle:
                range_vs_angle[curr_config]['orientation'].append(
                    curr_params['orientation'])
                range_vs_angle[curr_config]['range'].append(test['range'])
            else:
                range_vs_angle[curr_config] = {
                    'orientation': [curr_params['orientation']],
                    'range': [test['range']]
                }
        figure = wputils.BokehFigure(
            title='Range vs. Orientation',
            x_label='Angle (deg)',
            primary_y='Range (dB)',
        )
        for config, config_data in range_vs_angle.items():
            figure.add_line(config_data['orientation'], config_data['range'],
                            'Channel {}'.format(config))
        current_context = context.get_current_context().get_full_output_path()
        plot_file_path = os.path.join(current_context, 'results.html')
        figure.generate_figure(plot_file_path)

        # Save results
        results_file_path = os.path.join(current_context,
                                         'testclass_summary.json')
        with open(results_file_path, 'w') as results_file:
            json.dump(range_vs_angle, results_file, indent=4)

    def setup_ping_test(self, testcase_params):
        """Function that gets devices ready for the test.

        Args:
            testcase_params: dict containing test-specific parameters
        """
        # Configure AP
        self.setup_ap(testcase_params)
        # Set attenuator to 0 dB
        for attenuator in self.attenuators:
            attenuator.set_atten(0, strict=False)
        # Setup turntable
        self.ota_chamber.set_orientation(testcase_params['orientation'])
        # Reset, configure, and connect DUT
        self.setup_dut(testcase_params)

    def parse_test_params(self, test_name):
        """Function that generates test params based on the test name."""
        # Call parent parsing function
        testcase_params = WifiPingTest.parse_test_params(self, test_name)
        # Add orientation information
        test_name_params = test_name.split('_')
        testcase_params['orientation'] = int(test_name_params[5][0:-3])
        return testcase_params

    def generate_test_cases(self, channels, modes, angles):
        test_cases = []
        testcase_wrapper = self._test_ping_range
        allowed_configs = {
            'VHT20': [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 36, 40, 44, 48, 149, 153,
                157, 161
            ],
            'VHT40': [36, 44, 149, 157],
            'VHT80': [36, 149]
        }
        for channel, mode, angle in itertools.product(channels, modes, angles):
            if channel not in allowed_configs[mode]:
                continue
            testcase_name = 'test_ping_range_ch{}_{}_{}deg'.format(
                channel, mode, angle)
            setattr(self, testcase_name, testcase_wrapper)
            test_cases.append(testcase_name)
        return test_cases


class WifiOtaPing_TenDegree_Test(WifiOtaPingTest):
    def __init__(self, controllers):
        WifiOtaPingTest.__init__(self, controllers)
        self.tests = self.generate_test_cases(
            [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161], ['VHT20'],
            list(range(0, 360, 10)))


class WifiOtaPing_45Degree_Test(WifiOtaPingTest):
    def __init__(self, controllers):
        WifiOtaPingTest.__init__(self, controllers)
        self.tests = self.generate_test_cases(
            [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161], ['VHT20'],
            list(range(0, 360, 45)))


# Sensitivity Test
class WifiOtaSensitivityTest(WifiSensitivityTest):
    """Class to test over-the-air senstivity.

    This class implements measures WiFi sensitivity tests in an OTA chamber.
    It allows setting orientation and other chamber parameters to study
    performance in varying channel conditions
    """

    def setup_class(self):
        WifiSensitivityTest.setup_class(self)
        self.ota_chamber = ota_chamber.create(
            self.user_params['OTAChamber'])[0]

    def teardown_class(self):
        WifiSensitivityTest.teardown_class(self)
        self.ota_chamber.reset_chamber()

    def process_testclass_results(self):
        """Saves and plots test results from all executed test cases."""
        testclass_results_dict = collections.OrderedDict()
        id_fields = ['mode', 'rate', 'num_streams', 'chain_mask']
        for result in self.testclass_results:
            testcase_params = self.parse_test_params(result['test_name'])
            test_id = collections.OrderedDict(
                (key, value) for key, value in testcase_params.items()
                if key in id_fields)
            test_id = tuple(test_id.items())
            channel = testcase_params['channel']
            if test_id not in testclass_results_dict:
                testclass_results_dict[test_id] = collections.OrderedDict()
            if channel not in testclass_results_dict[test_id]:
                testclass_results_dict[test_id][channel] = {
                    'orientation': [],
                    'sensitivity': []
                }
            testclass_results_dict[test_id][channel]['orientation'].append(
                testcase_params['orientation'])
            if result['peak_throughput_pct'] == 100:
                testclass_results_dict[test_id][channel]['sensitivity'].append(
                    result['sensitivity'])
            else:
                testclass_results_dict[test_id][channel]['sensitivity'].append(
                    float('nan'))

        for test_id, test_data in testclass_results_dict.items():
            curr_plot = wputils.BokehFigure(
                title=str(test_id),
                x_label='Orientation (deg)',
                primary_y='Sensitivity (dBm)')
            for channel, channel_results in test_data.items():
                curr_plot.add_line(
                    channel_results['orientation'],
                    channel_results['sensitivity'],
                    legend='Channel {}'.format(channel))
            current_context = (
                context.get_current_context().get_full_output_path())
            output_file_path = os.path.join(current_context,
                                            str(test_id) + '.html')
            curr_plot.generate_figure(output_file_path)

    def setup_sensitivity_test(self, testcase_params):
        # Setup turntable
        self.ota_chamber.set_orientation(testcase_params['orientation'])
        # Continue test setup
        WifiSensitivityTest.setup_sensitivity_test(self, testcase_params)

    def get_start_atten(self):
        """Gets the starting attenuation for this sensitivity test.

        The function gets the starting attenuation by checking whether a test
        at the same rate configuration has executed. If so it sets the starting
        point a configurable number of dBs below the reference test.

        Returns:
            start_atten: starting attenuation for current test
        """
        # Get the current and reference test config. The reference test is the
        # one performed at the current MCS+1
        current_test_params = self.parse_test_params(self.current_test_name)
        current_test_params.pop('orientation')
        ref_test_params = current_test_params.copy()

        # Check if reference test has been run and set attenuation accordingly
        previous_params = []
        for result in self.testclass_results:
            test_param = self.parse_test_params(result['test_name'])
            test_param.pop('orientation')
            previous_params.append(test_param)

        try:
            ref_index = previous_params[::-1].index(ref_test_params)
            ref_index = len(previous_params) - 1 - ref_index
            start_atten = self.testclass_results[ref_index][
                'atten_at_range'] - (
                    self.testclass_params['adjacent_mcs_range_gap'])
        except ValueError:
            print('Reference test not found. Starting from {} dB'.format(
                self.testclass_params['atten_start']))
            start_atten = self.testclass_params['atten_start']
        return start_atten

    def parse_test_params(self, test_name):
        """Function that generates test params based on the test name."""
        # Call parent parsing function
        testcase_params = WifiSensitivityTest.parse_test_params(
            self, test_name)
        # Add orientation information
        test_name_params = test_name.split('_')
        testcase_params['orientation'] = int(test_name_params[7][0:-3])
        return testcase_params

    def generate_test_cases(self, channels, requested_rates, chain_mask,
                            angles):
        """Function that auto-generates test cases for a test class."""
        testcase_wrapper = self._test_sensitivity
        test_cases = []
        for channel in channels:
            for mode in self.VALID_TEST_CONFIGS[channel]:
                if 'VHT' in mode:
                    valid_rates = self.VALID_RATES[mode]
                elif 'HT' in mode:
                    valid_rates = self.VALID_RATES[mode]
                elif 'legacy' in mode and channel < 14:
                    valid_rates = self.VALID_RATES['legacy_2GHz']
                elif 'legacy' in mode and channel > 14:
                    valid_rates = self.VALID_RATES['legacy_5GHz']
                else:
                    raise ValueError('Invalid test mode.')
                for chain, rate, angle in itertools.product(
                        chain_mask, valid_rates, angles):
                    if rate not in requested_rates:
                        continue
                    if str(chain) in ['0', '1'] and rate[1] == 2:
                        # Do not test 2-stream rates in single chain mode
                        continue
                    if 'legacy' in mode:
                        testcase_name = ('test_sensitivity_ch{}_{}_{}_nss{}'
                                         '_ch{}_{}deg'.format(
                                             channel, mode,
                                             str(rate.mcs).replace('.', 'p'),
                                             rate.streams, chain, angle))
                    else:
                        testcase_name = ('test_sensitivity_ch{}_{}_mcs{}_nss{}'
                                         '_ch{}_{}deg'.format(
                                             channel, mode, rate.mcs,
                                             rate.streams, chain, angle))
                    setattr(self, testcase_name, testcase_wrapper)
                    test_cases.append(testcase_name)
        return test_cases


class WifiOtaSensitivity_10Degree_Test(WifiOtaSensitivityTest):
    def __init__(self, controllers):
        WifiSensitivityTest.__init__(self, controllers)
        requested_channels = [6, 36, 149]
        requested_rates = [
            self.RateTuple(8, 1, 86.7),
            self.RateTuple(0, 1, 7.2),
            self.RateTuple(8, 2, 173.3),
            self.RateTuple(0, 2, 14.4)
        ]
        self.tests = self.generate_test_cases(requested_channels,
                                              requested_rates, ['2x2'],
                                              list(range(0, 360, 10)))


class WifiOtaSensitivity_SingleChain_10Degree_Test(WifiOtaSensitivityTest):
    def __init__(self, controllers):
        WifiSensitivityTest.__init__(self, controllers)
        requested_channels = [6, 36, 149]
        requested_rates = [
            self.RateTuple(8, 1, 86.7),
            self.RateTuple(0, 1, 7.2),
        ]
        self.tests = self.generate_test_cases(requested_channels,
                                              requested_rates, ['2x2'],
                                              list(range(0, 360, 10)))


class WifiOtaSensitivity_45Degree_Test(WifiOtaSensitivityTest):
    def __init__(self, controllers):
        WifiSensitivityTest.__init__(self, controllers)
        requested_rates = [
            self.RateTuple(8, 1, 86.7),
            self.RateTuple(0, 1, 7.2),
            self.RateTuple(8, 2, 173.3),
            self.RateTuple(0, 2, 14.4)
        ]
        self.tests = self.generate_test_cases(
            [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161], requested_rates,
            ['2x2'], list(range(0, 360, 45)))


# Sensitivity Test
class WifiOtaRssiTest(WifiRssiTest):
    """Class to test over-the-air senstivity.

    This class implements measures WiFi sensitivity tests in an OTA chamber.
    It allows setting orientation and other chamber parameters to study
    performance in varying channel conditions
    """

    def setup_class(self):
        WifiRssiTest.setup_class(self)
        self.ota_chamber = ota_chamber.create(
            self.user_params['OTAChamber'])[0]

    def teardown_class(self):
        WifiRssiTest.teardown_class(self)
        self.ota_chamber.reset_chamber()

    def teardown_test(self):
        self.ota_chamber.reset_chamber()

    def setup_rssi_test(self, testcase_params):
        # Test setup
        WifiRssiTest.setup_rssi_test(self, testcase_params)
        if testcase_params['chamber_mode'] == 'StirrersOn':
            self.ota_chamber.start_continuous_stirrers()
        else:
            self.ota_chamber.set_orientation(testcase_params['orientation'])

    def _test_rssi_variation(self, testcase_params):
        self._test_rssi_stability(testcase_params)

    def generate_test_cases(self, test_types, channels, modes, traffic_modes,
                            chamber_modes, orientations):
        """Function that auto-generates test cases for a test class."""
        test_cases = []
        allowed_configs = {
            'VHT20': [
                1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 36, 40, 44, 48, 149, 153,
                157, 161
            ],
            'VHT40': [36, 44, 149, 157],
            'VHT80': [36, 149]
        }

        for (channel, mode, traffic, chamber_mode,
             orientation, test_type) in itertools.product(
                 channels, modes, traffic_modes, chamber_modes, orientations,
                 test_types):
            if channel not in allowed_configs[mode]:
                continue
            test_name = test_type + '_ch{}_{}_{}_{}_{}deg'.format(
                channel, mode, traffic, chamber_mode, orientation)
            test_params = collections.OrderedDict(
                channel=channel,
                mode=mode,
                active_traffic=(traffic == 'ActiveTraffic'),
                traffic_type=self.user_params['rssi_test_params']
                ['traffic_type'],
                polling_frequency=self.user_params['rssi_test_params']
                ['polling_frequency'],
                chamber_mode=chamber_mode,
                orientation=orientation)
            test_function = getattr(self, '_{}'.format(test_type))
            setattr(self, test_name, partial(test_function, test_params))
            test_cases.append(test_name)
        return test_cases


class WifiOtaRssiVariationTest(WifiOtaRssiTest):
    def __init__(self, controllers):
        WifiRssiTest.__init__(self, controllers)
        self.tests = self.generate_test_cases(
            ['test_rssi_variation'], [6, 36, 149], ['VHT20'],
            ['ActiveTraffic'], ['StirrersOn'], [0])
