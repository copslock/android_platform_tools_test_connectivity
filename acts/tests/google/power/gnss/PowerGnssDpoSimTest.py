#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

import acts.test_utils.power.PowerGnssBaseTest as GBT
from acts.test_utils.gnss import dut_log_test_utils as diaglog
import time
import os
from acts import utils
MDLOG_RUNNING_TIME = 300

class PowerGnssDpoSimTest(GBT.PowerGnssBaseTest):
    """Power baseline tests for rockbottom state.
    Rockbottom for GNSS on/off, screen on/off, everything else turned off

    """

    def measure_gnsspower_test_func(self):
        """Test function for baseline rockbottom tests.

        Decode the test config from the test name, set device to desired state.
        Measure power and plot results.
        """
        self.collect_power_data()
        self.pass_fail_check()

    # Test cases
    def test_gnss_dpoOFF_measurement(self):
        utils.set_location_service(self.dut, True)
        self.dut.send_keycode("SLEEP")
        self.measure_gnsspower_test_func()
        diaglog.start_diagmdlog_background(self.dut, maskfile=self.maskfile)
        time.sleep(MDLOG_RUNNING_TIME)
        qxdm_log_path = os.path.join(self.log_path, 'QXDM')
        diaglog.stop_background_diagmdlog(self.dut, qxdm_log_path)

    def test_gnss_dpoON_measurement(self):
        utils.set_location_service(self.dut, True)
        self.dut.send_keycode("SLEEP")
        self.measure_gnsspower_test_func()
        diaglog.start_diagmdlog_background(self.dut, maskfile=self.maskfile)
        time.sleep(MDLOG_RUNNING_TIME)
        qxdm_log_path = os.path.join(self.log_path, 'QXDM')
        diaglog.stop_background_diagmdlog(self.dut, qxdm_log_path)
