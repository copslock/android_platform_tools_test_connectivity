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
import time
import socket

from acts import asserts
from acts import base_test
from acts import test_runner
from acts import utils
from acts.controllers import adb
from acts.test_utils.tel import tel_data_utils
from acts.test_utils.tel import tel_test_utils
from acts.test_utils.tel import tel_defines
from acts.test_utils.wifi import wifi_test_utils

dum_class = "com.android.uid.DummyActivity"


class CoreNetworkingTest(base_test.BaseTestClass):
    """ Tests for UID networking """

    def setup_class(self):
        """ Setup devices for tests and unpack params """
        self.dut = self.android_devices[0]
        wifi_test_utils.wifi_toggle_state(self.dut, False)
        self.dut.droid.telephonyToggleDataConnection(True)
        tel_data_utils.wait_for_cell_data_connection(self.log, self.dut, True)
        asserts.assert_true(
            tel_test_utils.verify_http_connection(self.log, self.dut),
            "HTTP verification failed on cell data connection")

    def teardown_class(self):
        """ Reset devices """
        wifi_test_utils.wifi_toggle_state(self.dut, True)

    """ Test Cases """

    def test_uid_derace_doze_mode(self):
        """ Verify UID de-race doze mode

        Steps:
            1. Connect to DUT to data network and verify internet
            2. Enable doze mode
            3. Launch app and verify internet connectiviy
            4. Disable doze mode
        """
        # Enable doze mode
        self.log.info("Enable Doze mode")
        asserts.assert_true(utils.enable_doze(self.dut),
                            "Could not enable doze mode")

        # Launch app, check internet connectivity and close app
        res = self.dut.droid.launchForResult(dum_class)
        self.log.info("Internet connectivity status after app launch: %s "
                      % res['extras']['result'])

        # Disable doze mode
        self.log.info("Disable Doze mode")
        asserts.assert_true(utils.disable_doze(self.dut),
                            "Could not disable doze mode")

        return res['extras']['result']

    def test_uid_derace_doze_light_mode(self):
        """ Verify UID de-race doze light mode

        Steps:
            1. Connect DUT to data network and verify internet
            2. Enable doze light mode
            3. Launch app and verify internet connectivity
            4. Disable doze light mode
        """
        # Enable doze light mode
        self.log.info("Enable doze light mode")
        asserts.assert_true(utils.enable_doze_light(self.dut),
                            "Could not enable doze light mode")

        # Launch app, check internet connectivity and close app
        res = self.dut.droid.launchForResult(dum_class)
        self.log.info("Internet connectivity status after app launch: %s "
                      % res['extras']['result'])

        # Disable doze light mode
        self.log.info("Disable doze light mode")
        asserts.assert_true(utils.disable_doze_light(self.dut),
                            "Could not disable doze light mode")

        return res['extras']['result']

    def test_uid_derace_data_saver_mode(self):
        """ Verify UID de-race data saver mode

        Steps:
            1. Connect DUT to data network and verify internet
            2. Enable data saver mode
            3. Launch app and verify internet connectivity
            4. Disable data saver mode
        """
        # Enable data saver mode
        self.log.info("Enable data saver mode")
        self.dut.adb.shell("cmd netpolicy set restrict-background true")

        # Launch app, check internet connectivity and close app
        res = self.dut.droid.launchForResult(dum_class)
        self.log.info("Internet connectivity status after app launch: %s "
                      % res['extras']['result'])

        # Disable data saver mode
        self.log.info("Disable data saver mode")
        self.dut.adb.shell("cmd netpolicy set restrict-background false")

        return res['extras']['result']
