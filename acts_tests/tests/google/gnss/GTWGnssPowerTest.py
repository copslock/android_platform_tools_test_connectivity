#!/usr/bin/env python3
#
#   Copyright 2020 - The Android Open Source Project
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
import time

from acts import signals
from acts import utils
from acts.test_utils.instrumentation.device.command.instrumentation_command_builder import InstrumentationCommandBuilder
from acts.test_utils.instrumentation.device.command.instrumentation_command_builder import InstrumentationTestCommandBuilder
from acts.test_utils.power.PowerBaseTest import PowerBaseTest
from acts.test_utils.gnss import dut_log_test_utils as diaglog
from acts.test_utils.gnss import gnss_test_utils as gutils
from acts.test_utils.wifi import wifi_test_utils as wutils

DPO_NV_VALUE = '15DC'
MDS_TEST_PACKAGE = 'com.google.mdstest'
MDS_RUNNER = 'com.google.mdstest.instrument.ModemConfigInstrumentation'
POWER_TEST_PACKAGE = 'com.google.android.platform.powertests'
DEFAULT_RUNNER = 'androidx.test.runner.AndroidJUnitRunner'


class GTWGnssPowerTest(PowerBaseTest):
    """GTW Gnss Power test"""

    def setup_class(self):
        super().setup_class()
        self.ad = self.android_devices[0]
        req_params = ['wifi_network', 'pixel_lab_location', 'qdsp6m_path']
        self.unpack_userparams(req_param_names=req_params)
        gutils.disable_xtra_throttle(self.ad)

    def setup_test(self):
        super().setup_test()
        # Enable GNSS setting for GNSS standalone mode
        self.ad.adb.shell('settings put secure location_mode 3')

    def teardown_test(self):
        begin_time = utils.get_current_epoch_time()
        self.ad.take_bug_report(self.test_name, begin_time)
        gutils.get_gnss_qxdm_log(self.ad, self.qdsp6m_path)

    def baseline_test(self):
        """Baseline power measurement"""
        self.ad.droid.goToSleepNow()
        result = self.collect_power_data()
        self.ad.log.info('TestResult AVG_Current %.2f' % result.average_current)

    def start_gnss_tracking_with_power_data(self, mode, is_signal=True):
        """Start GNSS tracking and collect power metrics.

        Args:
            is_signal: default True, False for no Gnss signal test.
        """
        self.ad.adb.shell('settings put secure location_mode 3')
        gutils.clear_aiding_data_by_gtw_gpstool(self.ad)
        gutils.start_gnss_by_gtw_gpstool(
            self.ad, state=True, type='gnss', bgdisplay=True)
        self.ad.droid.goToSleepNow()

        if mode == 'standalone':
            self.ad.log.info('Wait 1200 seconds to collect SV data')
            time.sleep(1200)
        else:
            time.sleep(120)

        result = self.collect_power_data()
        self.ad.log.info('TestResult AVG_Current %.2f' % result.average_current)
        self.ad.send_keycode('WAKEUP')
        gutils.start_gnss_by_gtw_gpstool(self.ad, False, type='gnss')
        if is_signal:
            gutils.parse_gtw_gpstool_log(
                self.ad, self.pixel_lab_location, type='gnss')

    def build_instrumentation_call(self,
                                   package,
                                   runner,
                                   test_methods=None,
                                   options=None):
        """Build an instrumentation call for the tests

        Args:
            package: A string to identify test package.
            runner: A string to identify test runner.
            test_methods: A dictionary contains {class_name, test_method}.
            options: A dictionary constaion {key, value} param for test.

        Returns:
            An instrumentation call command.
        """
        if test_methods is None:
            test_methods = {}
            cmd_builder = InstrumentationCommandBuilder()
        else:
            cmd_builder = InstrumentationTestCommandBuilder()

        if options is None:
            options = {}

        cmd_builder.set_manifest_package(package)
        cmd_builder.set_runner(runner)
        cmd_builder.add_flag('-w')

        for class_name, test_method in test_methods.items():
            cmd_builder.add_test_method(class_name, test_method)

        for option_key, option_value in options.items():
            cmd_builder.add_key_value_param(option_key, option_value)

        return cmd_builder.build()

    def enable_DPO(self, enable=True):
        """Enable or disable the DPO option

        Args:
             enable: True of False to enable DPO
        """
        self.ad.log.info('Change DPO to new state: %s.' % enable)
        val = '02' if enable else '00'
        options = {'request': 'writeNV', 'item': DPO_NV_VALUE, 'data': val}
        instrument_cmd = self.build_instrumentation_call(
            MDS_TEST_PACKAGE, MDS_RUNNER, options=options)
        result = self.ad.adb.shell(instrument_cmd)
        self.ad.log.info(result)
        self.ad.reboot()
        self.dut_rockbottom()

    # Test cases
    # Standalone tests
    def test_standalone_gps_power_baseline(self):
        """
            1. Set DUT rockbottom.
            2. Collect power data.
        """
        self.baseline_test()

    def test_standalone_DPO_on(self):
        """
            1. Attenuate signal to strong GNSS level.
            2. Turn DPO on.
            3. Open GPStool and tracking with DUT sleep.
            4. Collect power data.
        """
        self.set_attenuation(self.atten_level['strong_signal'])
        self.enable_DPO(True)
        self.start_gnss_tracking_with_power_data(mode='standalone')

    def test_standalone_DPO_off(self):
        """
            1. Attenuate signal to strong GNSS level.
            2. Turn DPO off.
            3. Open GPStool and tracking with DUT sleep.
            4. Collect power data.
        """
        self.set_attenuation(self.atten_level['strong_signal'])
        self.enable_DPO(False)
        self.start_gnss_tracking_with_power_data(mode='standalone')

    def test_partial_wake_lock(self):
        """
            1. Attenuate signal to strong GNSS level.
            2. Trigger instrumentation to hold the partial wake lock.
            3. Collect power data.
        """
        self.set_attenuation(self.atten_level['strong_signal'])
        test_class = 'com.google.android.platform.powertests.IdleTestCase'
        test_method = 'testPartialWakelock'
        test_methods = {test_class: test_method}
        options = {'IdleTestCase-testPartialWakelock': self.mon_duration}
        instrument_cmd = self.build_instrumentation_call(
            POWER_TEST_PACKAGE, DEFAULT_RUNNER, test_methods, options)
        self.ad.adb.shell_nb(instrument_cmd)
        self.baseline_test()
