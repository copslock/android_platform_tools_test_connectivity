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
from acts import signals
from acts.test_utils.power.PowerBaseTest import PowerBaseTest
from acts.test_utils.gnss import dut_log_test_utils as diaglog
from acts.test_utils.gnss import gnss_test_utils as gutils
from acts.test_utils.wifi import wifi_test_utils as wutils


class GTWGnssPowerTest(PowerBaseTest):
    """GTW Gnss Power test"""

    def setup_class(self):
        super().setup_class()
        self.ad = self.android_devices[0]
        req_params = ['wifi_network', 'pixel_lab_location', 'qdsp6m_path']
        self.unpack_userparams(req_param_names=req_params)

    def setup_test(self):
        super().setup_test()
        # Enable GNSS setting for GNSS standalone mode
        self.ad.adb.shell('settings put secure location_mode 3')

    def start_gnss_tracking_with_power_data(self, signal=True):
        """Start GNSS tracking and collect power metrics.
        Args:
            signal: default True, False for no Gnss signal test.
        """
        gutils.start_gnss_by_gtw_gpstool(
            self.dut, state=True, type='gnss', bgdisplay=True)
        self.ad.send_keycode('SLEEP')
        result = self.collect_power_data()
        gutils.start_gnss_by_gtw_gpstool(self.ad, False)
        if signal:
            gutils.parse_gtw_gpstool_log(
                self.ad, self.pixel_lab_location, type='gnss')
        self.pass_fail_check(result.average_current)

    # Test cases
    def test_power_baseline(self):
        """
            1. Let DUT sleep.
            2. Mesuring the baseline after rockbottom DUT.
        """
        self.ad.send_keycode('SLEEP')
        result = self.collect_power_data()
        self.pass_fail_check(result.average_current)

    def test_baseline_gnss_request_1Hz(self):
        """
            1. Attenuate signal to strong GNSS level.
            2. Open GPStool and tracking with DUT sleep.
            3. Collect power data.
        """
        self.set_attenuation(self.atten_level[self.current_test_name])
        self.start_gnss_tracking_with_power_data()

    def test_DPO_on_gnss_request_1Hz(self):
        """
            1. Attenuate signal to strong GNSS level.
            2. Turn DPO ON.
            3. Open GPStool and tracking with DUT sleep.
            4. Collect power data.
        """
        self.set_attenuation(self.atten_level[self.current_test_name])
        self.start_gnss_tracking_with_power_data()

    def test_L1_L5_weak_signal_gnss_request_1Hz(self):
        """
            1. Attenuate signal to weak GNSS level.
            3. Open GPStool and tracking with DUT sleep.
            4. Collect power data.
        """
        self.set_attenuation(self.atten_level[self.current_test_name])
        self.start_gnss_tracking_with_power_data()

    def test_no_signal_gnss_request_1Hz(self):
        """
            1. Attenuate signal to no GNSS signal level.
            3. Open GPStool and tracking with DUT sleep.
            3. Collect power data.
        """
        self.set_attenuation(self.atten_level[self.current_test_name])
        self.start_gnss_tracking_with_power_data(signal=False)
