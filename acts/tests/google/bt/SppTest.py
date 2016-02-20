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
Test script to execute Bluetooth basic functionality test cases.
This test was designed to be run in a shield box.
"""

import threading
import time

from queue import Empty
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import get_bt_mac_address
from acts.test_utils.bt.bt_test_utils import log_energy_info
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import rfcomm_accept
from acts.test_utils.bt.bt_test_utils import rfcomm_connect
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs


class SppTest(BluetoothBaseTest):
    default_timeout = 10
    scan_discovery_time = 5
    thread_list = []
    message = ("Space: the final frontier. These are the voyages of "
               "the starship Enterprise. Its continuing mission: to explore "
               "strange new worlds, to seek out new life and new civilizations,"
               " to boldly go where no man has gone before.")

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.server_ad = self.android_devices[0]
        self.client_ad = self.android_devices[1]
        self.tests = (
            "test_spp_connection",
        )

    def _clear_bonded_devices(self):
        for a in self.android_devices:
            bonded_device_list = a.droid.bluetoothGetBondedDevices()
            for device in bonded_device_list:
                a.droid.bluetoothUnbond(device['address'])

    def setup_class(self):
        return setup_multiple_devices_for_bt_test(self.android_devices)

    def setup_test(self):
        self._clear_bonded_devices()
        self.log.debug(log_energy_info(self.android_devices, "Start"))
        for a in self.android_devices:
            a.ed.clear_all_events()
        return True

    def teardown_test(self):
        self.log.debug(log_energy_info(self.android_devices, "End"))
        return True

    def on_fail(self, test_name, begin_time):
        take_btsnoop_logs(self.android_devices, self, test_name)
        reset_bluetooth(self.android_devices)

    def teardown_test(self):
        for thread in self.thread_list:
            thread.join()

    def orchestrate_rfcomm_connect(self, server_mac):
        accept_thread = threading.Thread(
            target=rfcomm_accept, args=(self.server_ad.droid,))
        self.thread_list.append(accept_thread)
        accept_thread.start()
        connect_thread = threading.Thread(
            target=rfcomm_connect, args=(self.client_ad.droid, server_mac))
        self.thread_list.append(connect_thread)
        connect_thread.start()

    @BluetoothBaseTest.bt_test_wrap
    def test_spp_connection(self):
        """Test bluetooth SPP profile.

        Test SPP profile though establishing an RFCOMM connection.

        Steps:
        1. Get the mac address of the server device.
        2. Establish an RFCOMM connection from the client to the server AD.
        3. Verify that the RFCOMM connection is active from both the client and
        server.
        4. Disconnect the RFCOMM connection.

        Expected Result:
        RFCOMM connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: Classic, SPP, RFCOMM
        Priority: 1
        """
        server_mac = get_bt_mac_address(self.client_ad.droid,
            self.server_ad.droid)
        # temporary workaround. Need to find out why I can't connect after I do
        # a device discovery from get_bt_mac_address
        reset_bluetooth([self.server_ad])
        self.orchestrate_rfcomm_connect(server_mac)
        self.log.info("Write message.")
        self.client_ad.droid.bluetoothRfcommWrite(self.message)
        self.log.info("Read message.")
        read_msg = self.server_ad.droid.bluetoothRfcommRead()
        self.log.info("Verify message.")
        assert self.message == read_msg, "Mismatch! Read {}".format(read_msg)
        if len(self.server_ad.droid.bluetoothRfcommActiveConnections()) == 0:
            self.log.info("No rfcomm connections found on server.")
            return False
        if len(self.client_ad.droid.bluetoothRfcommActiveConnections()) == 0:
            self.log.info("no rfcomm connections found on client.")
            return False
        self.client_ad.droid.bluetoothRfcommStop()
        self.server_ad.droid.bluetoothRfcommStop()
        return True
