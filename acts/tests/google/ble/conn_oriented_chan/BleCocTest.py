#/usr/bin/env python3.4
#
# Copyright 2017 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Test script to execute Bluetooth Connection-orient Channel (CoC) functionality
test cases. This test was designed to be run in a shield box.
"""

import threading
import time

from queue import Empty
from acts.test_decorators import test_tracker_info
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import clear_bonded_devices
from acts.test_utils.bt.bt_test_utils import kill_bluetooth_process
from acts.test_utils.bt.bt_test_utils import orchestrate_coc_connection
from acts.test_utils.bt.bt_test_utils import do_multi_connection_throughput
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs
from acts.test_utils.bt.bt_test_utils import write_read_verify_data
from acts.test_utils.bt.bt_test_utils import verify_server_and_client_connected


class BleCocTest(BluetoothBaseTest):
    message = (
        "Space: the final frontier. These are the voyages of "
        "the starship Enterprise. Its continuing mission: to explore "
        "strange new worlds, to seek out new life and new civilizations,"
        " to boldly go where no man has gone before.")

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.client_ad = self.android_devices[0]
        self.server_ad = self.android_devices[1]
        # Note that some tests required a third device.
        if len(self.android_devices) > 2:
            self.server2_ad = self.android_devices[2]

    def setup_class(self):
        return setup_multiple_devices_for_bt_test(self.android_devices)

    def teardown_test(self):
        if verify_server_and_client_connected(
                self.client_ad, self.server_ad, log=False):
            self.client_ad.droid.bluetoothSocketConnStop()
            self.server_ad.droid.bluetoothSocketConnStop()

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='b6989966-c504-4934-bcd7-57fb4f7fde9c')
    def test_coc_secured_connection(self):
        """Test Bluetooth LE CoC secured connection

        Test LE CoC though establishing a basic connection with security.

        Steps:
        1. Get the mac address of the server device.
        2. Establish an LE CoC Secured connection from the client to the server AD.
        3. Verify that the LE CoC connection is active from both the client and
        server.
        Expected Result:
        LE CoC connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """
        is_secured = True
        self.log.info(
            "_test_coc_secured_connection: calling orchestrate_coc_connection but "
            "isBle=1 and securedConn={}".format(is_secured))
        status, client_conn_id, server_conn_id = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False

        self.client_ad.droid.bluetoothSocketConnStop()
        self.server_ad.droid.bluetoothSocketConnStop()
        return True

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='6587792c-78fb-469f-9084-772c249f97de')
    def test_coc_insecured_connection(self):
        """Test Bluetooth LE CoC insecured connection

        Test LE CoC though establishing a basic connection with no security.

        Steps:
        1. Get the mac address of the server device.
        2. Establish an LE CoC Secured connection from the client to the server AD.
        3. Verify that the LE CoC connection is active from both the client and
        server.
        Expected Result:
        LE CoC connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """
        is_secured = False
        self.log.info(
            "test_coc_insecured_connection: calling orchestrate_coc_connection but "
            "isBle=1 and securedConn={}".format(is_secured))
        status, client_conn_id, server_conn_id = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False

        self.client_ad.droid.bluetoothSocketConnStop()
        self.server_ad.droid.bluetoothSocketConnStop()
        return True

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='32a7b02e-f2b5-4193-b414-36c8815ac407')
    def test_coc_secured_connection_write_ascii(self):
        """Test LE CoC secured connection writing and reading ascii data

        Test LE CoC though establishing a secured connection and reading and writing ascii data.

        Steps:
        1. Get the mac address of the server device.
        2. Establish an LE CoC connection from the client to the server AD. The security of
        connection is TRUE.
        3. Verify that the LE CoC connection is active from both the client and
        server.
        4. Write data from the client and read received data from the server.
        5. Verify data matches from client and server
        6. Disconnect the LE CoC connection.

        Expected Result:
        LE CoC connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """
        is_secured = True
        self.log.info(
            "test_coc_secured_connection_write_ascii: calling "
            "orchestrate_coc_connection. is_secured={}".format(is_secured))
        status, client_conn_id, server_conn_id = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False
        if not write_read_verify_data(self.client_ad, self.server_ad,
                                      self.message, False):
            return False
        if not verify_server_and_client_connected(self.client_ad,
                                                  self.server_ad):
            return False

        self.client_ad.droid.bluetoothSocketConnStop()
        self.server_ad.droid.bluetoothSocketConnStop()
        return True

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='12537d27-79c9-40a0-8bdb-d023b0e36b58')
    def test_coc_insecured_connection_write_ascii(self):
        """Test LE CoC insecured connection writing and reading ascii data

        Test LE CoC though establishing a connection.

        Steps:
        1. Get the mac address of the server device.
        2. Establish an LE CoC connection from the client to the server AD. The security of
        connection is FALSE.
        3. Verify that the LE CoC connection is active from both the client and
        server.
        4. Write data from the client and read received data from the server.
        5. Verify data matches from client and server
        6. Disconnect the LE CoC connection.

        Expected Result:
        LE CoC connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """
        is_secured = False
        self.log.info(
            "test_coc_secured_connection_write_ascii: calling "
            "orchestrate_coc_connection. is_secured={}".format(is_secured))
        status, client_conn_id, server_conn_id = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False
        if not write_read_verify_data(self.client_ad, self.server_ad,
                                      self.message, False):
            return False
        if not verify_server_and_client_connected(self.client_ad,
                                                  self.server_ad):
            return False

        self.client_ad.droid.bluetoothSocketConnStop()
        self.server_ad.droid.bluetoothSocketConnStop()
        return True

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='214037f4-f0d1-47db-86a7-5230c71bdcac')
    def test_coc_secured_connection_throughput(self):
        """Test LE CoC writing and measured data throughput with security

        Test CoC thoughput by establishing a secured connection and sending data.

        Steps:
        1. Get the mac address of the server device.
        2. Establish a L2CAP CoC connection from the client to the server AD.
        3. Verify that the L2CAP CoC connection is active from both the client
        and server.
        4. Write data from the client to server.
        5. Verify data matches from client and server
        6. Disconnect the L2CAP CoC connections.

        Expected Result:
        CoC connection is established then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """

        is_secured = True
        self.log.info(
            "test_coc_secured_connection_throughput: calling "
            "orchestrate_coc_connection. is_secured={}".format(is_secured))
        status, client_conn_id, server_conn_id = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False

        # The num_iterations is that number of repetitions of each
        # set of buffers r/w.
        # number_buffers is the total number of data buffers to transmit per
        # set of buffers r/w.
        # buffer_size is the number of bytes per L2CAP data buffer.
        number_buffers = 100
        buffer_size = 23
        num_iterations = 3
        list_server_ad = [self.server_ad]
        list_client_conn_id = [client_conn_id]
        data_rate = do_multi_connection_throughput(
            self.client_ad, list_server_ad, list_client_conn_id,
            num_iterations, number_buffers, buffer_size)
        if data_rate <= 0:
            return False
        self.log.info(
            "test_coc_connection_throughput: throughput=%d bytes per sec",
            data_rate)

        self.client_ad.droid.bluetoothSocketConnStop()
        self.server_ad.droid.bluetoothSocketConnStop()
        return True
