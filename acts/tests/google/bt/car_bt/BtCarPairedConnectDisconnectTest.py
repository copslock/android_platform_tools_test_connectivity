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
Test script to test connect and disconnect sequence between two devices which can run
SL4A. The script does the following:
  Setup:
    Clear up the bonded devices on both bluetooth adapters and bond the DUTs to each other.
  Test (NUM_TEST_RUNS times):
    1. Connect A2dpSink and HeadsetClient
      1.1. Check that devices are connected.
    2. Disconnect A2dpSink and HeadsetClient
      2.1 Check that devices are disconnected.
"""

import time

from acts.base_test import BaseTestClass
from acts.test_utils.bt.bt_test_utils import log_energy_info
from acts.test_utils.bt.bt_test_utils import pair_pri_to_sec
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs

class BtCarPairedConnectDisconnectTest(BaseTestClass):
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.droid_ad = self.android_devices[0]
        self.droid1_ad = self.android_devices[1]
        self.tests = (
            "test_connect_disconnect_paired",
        )

    def setup_class(self):
        return True

    def setup_test(self):
        # Reset the devices in a clean state.
        setup_multiple_devices_for_bt_test(self.android_devices)
        reset_bluetooth(self.android_devices)
        for a in self.android_devices:
            a.ed.clear_all_events()

        # Pair the devices.
        # This call may block until some specified timeout in bt_test_utils.py.
        result = pair_pri_to_sec(self.droid_ad.droid, self.droid1_ad.droid)

        if result is False:
            self.log.info("pair_pri_to_sec returned false.")
            return False

        # Check for successful setup of test.
        devices = self.droid_ad.droid.bluetoothGetBondedDevices()
        if (len(devices) == 0):
            self.log.info("pair_pri_to_sec succeeded but no bonded devices.")
            return False
        return True

    def teardown_test(self):
        return True

    def on_fail(self, test_name, begin_time):
        take_btsnoop_logs(self.android_devices, self, test_name)

    def test_connect_disconnect_paired(self):
        NUM_TEST_RUNS = 2
        failure = 0
        for i in range(NUM_TEST_RUNS):
            self.log.info("Running test [" + str(i) + "/" + str(NUM_TEST_RUNS) + "]")
            # Connect the device.
            devices = self.droid_ad.droid.bluetoothGetBondedDevices()
            if (len(devices) == 0):
                self.log.info("No bonded devices.")
                failure = failure + 1
                continue

            self.log.info("Attempting to connect.")
            self.droid_ad.droid.bluetoothConnectBonded(devices[0]['address'])
            end_time = time.time() + 10
            expected_address = self.droid1_ad.droid.bluetoothGetLocalAddress()
            connected = False
            # Busy loop to check if we found a matching device.
            while time.time() < end_time:
                connected_devices = self.droid_ad.droid.bluetoothGetConnectedDevices()
                for d in connected_devices:
                    if d['address'] == expected_address:
                        connected = True
                        break
                if connected is True:
                    break
                time.sleep(1)

            # Check if we got connected.
            if connected is False:
                self.log.info("No connected devices.")
                failure = failure + 1
                continue

            # Disconnect the devices.
            self.log.info("Attempt to disconnect.")
            self.droid_ad.droid.bluetoothDisconnectConnected(expected_address)

            end_time = time.time() + 10
            disconnected = False
            # Busy loop to check if we have successfully disconnected from the
            # device
            while time.time() < end_time:
                connectedDevices = self.droid_ad.droid.bluetoothGetConnectedDevices()
                exists = False
                connected_devices = self.droid_ad.droid.bluetoothGetConnectedDevices()
                for d in connected_devices:
                  if d['address'] == expected_address:
                      exists = True
                      break
                if exists is False:
                    disconnected = True
                    break
                time.sleep(1)

            if disconnected is False:
                self.log.info("Still connected devices.")
                failure = failure + 1
                continue
        self.log.info("Failure {} total tests {}".format(failure, NUM_TEST_RUNS))
        if failure > 0:
            return False
        else:
            return True
