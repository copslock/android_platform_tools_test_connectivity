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
Test script to execute Bluetooth Connection-orient Channel (CoC) functionality for
2 connections test cases. This test was designed to be run in a shield box.
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


class BleCoc2ConnTest(BluetoothBaseTest):
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

    def _run_coc_connection_throughput_2_conn(self, is_secured):
        """Test LE CoC data throughput on two connections

        Test Data Throughput of 2 L2CAP CoC connections. 3 phones are required.

        Steps:
        1. Get the mac address of the server device.
        2. Establish a L2CAP CoC connection from the client to the server#1 AD.
        The connection may be secured or insecured depending on test.
        3. Verify that the L2CAP CoC connection is active from both the client
        and server.
        4. Establish a L2CAP CoC connection from the client to the server#2 AD.
        The connection may be secured or insecured depending on test.
        5. Verify that the L2CAP CoC connection is active from both the client
        and server.
        6. Write data from the client to both server#1 and server#2.
        7. Verify data matches from client and server
        8. Disconnect the 2 L2CAP CoC connections.

        Expected Result:
        L2CAP CoC connections are established, data written to both servers,
        then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """

        # Make sure at least 3 phones are setup
        if len(self.android_devices) <= 2:
            self.log.info("test_coc_connection_throughput_2_conn: "
                          "Error: 3rd phone not configured in file")
            return False

        # Temporary workaround: It seems that the LE CoC connection failures happen more
        # when secured.
        self.log.info(
            "test_coc_connection_throughput_2_conn: calling "
            "orchestrate_coc_connection for server1. is_secured={}".format(
                is_secured))
        status, client_conn_id1, server_conn_id1 = orchestrate_coc_connection(
            self.client_ad, self.server_ad, True, is_secured)
        if not status:
            return False

        self.log.info(
            "test_coc_connection_throughput_2_conn: calling "
            "orchestrate_coc_connection for server2. is_secured={}".format(
                is_secured))
        status, client_conn_id2, server_conn_id2 = orchestrate_coc_connection(
            self.client_ad, self.server2_ad, True, is_secured)
        if not status:
            return False

        # The num_iterations is that number of repetitions of each
        # set of buffers r/w.
        # number_buffers is the total number of data buffers to transmit per
        # set of buffers r/w.
        # buffer_size is the number of bytes per L2CAP data buffer.
        num_iterations = 10
        number_buffers = 100
        # Note: A 117 octets buffer size would fix nicely to a 123 bytes Data Length
        buffer_size = 117
        list_server_ad = [self.server_ad, self.server2_ad]
        list_client_conn_id = [client_conn_id1, client_conn_id2]
        data_rate = do_multi_connection_throughput(
            self.client_ad, list_server_ad, list_client_conn_id,
            num_iterations, number_buffers, buffer_size)
        if data_rate <= 0:
            return False

        self.log.info(
            "test_coc_connection_throughput_2_conn: throughput=%d bytes per "
            "sec", data_rate)

        self.client_ad.droid.bluetoothSocketConnStop(client_conn_id1)
        self.client_ad.droid.bluetoothSocketConnStop(client_conn_id2)
        self.server_ad.droid.bluetoothSocketConnStop(server_conn_id1)
        self.server2_ad.droid.bluetoothSocketConnStop(server_conn_id2)
        return True

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='27226006-b725-4312-920e-6193cf0539d4')
    def test_coc_insecured_connection_throughput_2_conn(self):
        """Test LE CoC data throughput on two insecured connections

        Test Data Throughput of 2 L2CAP CoC insecured connections.
        3 phones are required.

        Steps:
        See description in _run_coc_connection_throughput_2_conn()

        Expected Result:
        L2CAP CoC connections are established, data written to both servers,
        then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """

        status = self._run_coc_connection_throughput_2_conn(False)
        return status

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='1a5fb032-8a27-42f1-933f-3e39311c09a6')
    def test_coc_secured_connection_throughput_2_conn(self):
        """Test LE CoC data throughput on two secured connections

        Test Data Throughput of 2 L2CAP CoC secured connections.
        3 phones are required.

        Steps:
        See description in _run_coc_connection_throughput_2_conn()

        Expected Result:
        L2CAP CoC connections are established, data written to both servers,
        then disconnected succcessfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: BLE, CoC
        Priority: 1
        """

        status = self._run_coc_connection_throughput_2_conn(True)
        return status
