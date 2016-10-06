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
Automated tests for the testing Connectivity of Avrcp/A2dp profile.
"""

import time

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt import bt_test_utils
from acts.test_utils.car import car_bt_utils
from acts.test_utils.car import car_media_utils
from acts.test_utils.bt import BtEnum

class BtCarMediaConnectionTest(BluetoothBaseTest):
    def setup_class(self):
        # AVRCP roles
        self.CT = self.android_devices[0]
        self.TG = self.android_devices[1]
        # A2DP roles for the same devices
        self.SNK = self.CT
        self.SRC = self.TG

        # Reset bluetooth
        bt_test_utils.setup_multiple_devices_for_bt_test([self.CT, self.TG])
        bt_test_utils.reset_bluetooth([self.CT, self.TG])

        self.btAddrCT = self.CT.droid.bluetoothGetLocalAddress()
        self.btAddrTG = self.TG.droid.bluetoothGetLocalAddress()

        # Pair the devices.
        if not bt_test_utils.pair_pri_to_sec(self.CT.droid, self.TG.droid):
            self.log.error("Failed to pair")
            return False

        # Disable all
        car_bt_utils.set_car_profile_priorities_off(self.SNK, self.SRC)

        # Enable A2DP
        bt_test_utils.set_profile_priority(
            self.SNK, self.SRC, [BtEnum.BluetoothProfile.A2DP_SINK],
            BtEnum.BluetoothPriorityLevel.PRIORITY_ON)

    def setup_test(self):
        for d in self.android_devices:
            d.ed.clear_all_events()

    def on_fail(self, test_name, begin_time):
        self.log.debug("Test {} failed.".format(test_name))

    def test_a2dp_connect_disconnect_from_src(self):
        """
        Test Connect/Disconnect on A2DP profile.

        Pre-Condition:
        1. Devices previously bonded and NOT connected on A2dp

        Steps:
        1. Initiate a connection on A2DP profile from SRC
        2. Check if they connected.
        3. Initiate a disconnect on A2DP profile from SRC
        4. Ensure they disconnected on A2dp alone

        Returns:
        True    if we connected/disconnected successfully
        False   if we did not connect/disconnect successfully

        Priority: 0
        """
        if (car_media_utils.is_a2dp_connected(self.log, self.SNK, self.SRC)):
            self.log.info("Already Connected")
        else:
            result = bt_test_utils.connect_pri_to_sec(
                self.log, self.SRC, self.SNK.droid,
                set([BtEnum.BluetoothProfile.A2DP.value]))
            if (not result):
                self.log.error("Failed to connect on A2dp")
                return False

        result = bt_test_utils.disconnect_pri_from_sec(
            self.log, self.SRC, self.SNK.droid,
            [BtEnum.BluetoothProfile.A2DP.value])
        if not result:
            self.log.error("Failed to disconnect on A2dp")
            return False

        # Logging if we connected right back, since that happens sometimes
        # Not failing the test if it did though
        if (car_media_utils.is_a2dp_connected(self.log, self.SNK, self.SRC)):
            self.log.error("Still connected after a disconnect")

        return True

    def test_a2dp_connect_disconnect_from_snk(self):
        """
        Test Connect/Disconnect on A2DP Sink profile.

        Pre-Condition:
        1. Devices previously bonded and NOT connected on A2dp

        Steps:
        1. Initiate a connection on A2DP Sink profile from SNK
        2. Check if they connected.
        3. Initiate a disconnect on A2DP Sink profile from SNK
        4. Ensure they disconnected on A2dp alone

        Returns:
        True    if we connected/disconnected successfully
        False   if we did not connect/disconnect successfully

        Priority: 0
        """
        # Connect
        if (car_media_utils.is_a2dp_connected(self.log, self.SNK, self.SRC)):
            self.log.info("Already Connected")
        else:
            result = bt_test_utils.connect_pri_to_sec(
                self.log, self.SNK, self.SRC.droid,
                set([BtEnum.BluetoothProfile.A2DP_SINK.value]))
            if (not result):
                self.log.error("Failed to connect on A2dp Sink")
                return False
        # Disconnect
        result = bt_test_utils.disconnect_pri_from_sec(
            self.log, self.SNK, self.SRC.droid,
            [BtEnum.BluetoothProfile.A2DP_SINK.value])
        if not result:
            self.log.error("Failed to disconnect on A2dp Sink")
            return False

        # Logging if we connected right back, since that happens sometimes
        # Not failing the test if it did though
        if (car_media_utils.is_a2dp_connected(self.log, self.SNK, self.SRC)):
            self.log.error("Still connected after a disconnect")

        return True
