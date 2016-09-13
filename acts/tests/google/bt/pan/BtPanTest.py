#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Test script to test PAN testcases.

Test Script assumes that an internet connection
is available through a telephony provider that has
tethering allowed.

This device was not intended to run in a sheild box.
"""
import time
from queue import Empty
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import bluetooth_enabled_check
from acts.test_utils.bt.bt_test_utils import pair_pri_to_sec
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import verify_http_connection


class BtPanTest(BluetoothBaseTest):
    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.pan_dut = self.android_devices[0]
        self.panu_dut = self.android_devices[1]

    @BluetoothBaseTest.bt_test_wrap
    def test_pan_connection(self):
        """Test bluetooth PAN connection

        Test basic PAN connection between two devices.

        Steps:
        1. Enable Airplane mode on PANU device. Enable Bluetooth only.
        2. Enable Bluetooth tethering on PAN Service device.
        3. Pair the PAN Service device to the PANU device.
        4. Verify that Bluetooth tethering is enabled on PAN Service device.
        5. Enable PAN profile from PANU device to PAN Service device.
        6. Verify HTTP connection on PANU device.
        7. Disable Bluetooth tethering on PAN Service device.

        Expected Result:
        PAN profile connected and HTTP

        Returns:
          Pass if True
          Fail if False

        TAGS: Classic, PAN, tethering
        Priority: 1
        """
        if not toggle_airplane_mode(self.log, self.panu_dut, True):
            self.log.error("Failed to toggle airplane mode on")
            return False
        if not bluetooth_enabled_check(self.panu_dut):
            return False
        self.pan_dut.droid.bluetoothPanSetBluetoothTethering(True)
        if not (pair_pri_to_sec(self.pan_dut.droid, self.panu_dut.droid)):
            return False
        if not self.pan_dut.droid.bluetoothPanIsTetheringOn():
            self.log.error("Failed to enable Bluetooth tethering.")
            return False
        self.panu_dut.droid.bluetoothConnectBonded(
            self.pan_dut.droid.bluetoothGetLocalAddress())
        if not verify_http_connection(self.log, self.panu_dut):
            self.log.error("Can't verify http connection on PANU device.")
            if not verify_http_connection(self.log, self.pan_dut):
                self.log.info(
                    "Can't verify http connection on PAN service device")
            return False
        self.pan_dut.droid.bluetoothPanSetBluetoothTethering(False)
        return True

