#/usr/bin/env python3
#
# Copyright (C) 2018 The Android Open Source Project
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
"""Bluetooth 1st time force pair and connect test implementation."""
# Quick way to get the Apollo serial number:
# python3.5 -c "from acts.controllers.buds_lib.apollo_lib import get_devices; [print(d['serial_number']) for d in get_devices()]"

import statistics
import time

from acts import logger
from acts.base_test import BaseTestClass
from acts.controllers.buds_lib.test_actions.bt_utils import BTUtils
from acts.controllers.buds_lib.test_actions.apollo_acts import ApolloTestActions
from acts.signals import TestFailure
from acts.signals import TestPass
from acts.test_utils.bt.bt_test_utils import clear_bonded_devices
from acts.test_utils.bt.bt_test_utils import enable_bluetooth
from acts.utils import set_location_service

# The number of pairing and connection attempts
PAIR_CONNECT_ATTEMPTS = 200


class BluetoothPairConnectError(Exception):
    pass


class BluetoothPairAndConnectTest(BaseTestClass):
    """Pairs and connects a phone and an Apollo buds device.

   Attributes:
       phone: An Android phone object
       apollo: An Apollo earbuds object
       apollo_act: An Apollo test action object
       dut_bt_addr: The Bluetooth address of the Apollo earbuds
       bt_utils: BTUtils test action object
    """

    def __init__(self, configs):
        BaseTestClass.__init__(self, configs)
        # Sanity check of the devices under test
        # TODO(b/119051823): Investigate using a config validator to replace this.
        if not self.android_devices:
            raise ValueError(
                'Cannot find android phone (need at least one).')
        self.phone = self.android_devices[0]

        if not self.buds_devices:
            raise ValueError(
                'Cannot find apollo device (need at least one).')
        self.apollo = self.buds_devices[0]
        self.log.info('Successfully found needed devices.')

        # Staging the test, create result object, etc.
        self.apollo_act = ApolloTestActions(self.apollo, self.log)
        self.dut_bt_addr = self.apollo.bluetooth_address
        self.bt_utils = BTUtils()

    def setup_test(self):
        # Make sure Bluetooth is on
        enable_bluetooth(self.phone.droid, self.phone.ed)
        set_location_service(self.phone, True)
        clear_bonded_devices(self.phone)
        self.apollo_act.factory_reset()
        self.log.info('===== START BLUETOOTH PAIR AND CONNECT TEST  =====')

    def teardown_test(self):
        self.log.info('Teardown test, shutting down all services...')
        self.apollo.close()

    def _get_device_pair_and_connect_times(self):
        """Gets the pair and connect times of the phone and buds device.

        Pairs the phone with the buds device. Gets the pair and connect times.
        Unpairs the devices.

        Returns:
            pair_time: The time it takes to pair the devices in ms.
            connection_time: The time it takes to connect the devices for the
                             first time after pairing.

        Raises:
            BluetoothPairConnectError
        """
        paired, pair_time = self.bt_utils.bt_pair(self.phone, self.apollo)
        pair_time *= 1000
        if not paired:
            raise BluetoothPairConnectError('Failed to pair devices')
        connection_start_time = time.perf_counter()
        if not self.apollo_act.wait_for_bluetooth_a2dp_hfp():
            raise BluetoothPairConnectError('Failed to connect devices')
        connection_end_time = time.perf_counter()
        connection_time = (connection_end_time - connection_start_time) * 1000

        self.bt_utils.bt_unpair(self.phone, self.apollo)

        return pair_time, connection_time

    def test_bluetooth_connect(self):
        # Store metrics
        metrics = {}
        pair_connect_success = 0
        pair_connect_failures = []
        pair_times = []
        connect_times = []
        first_connection_failure = None

        for attempt in range(PAIR_CONNECT_ATTEMPTS):
            self.log.info('Pair and connection attempt {}'.format(attempt + 1))
            pair_connect_timestamp = time.strftime(logger.log_line_time_format,
                                                   time.localtime())
            try:
                pair_time, connect_time = (self.
                                           _get_device_pair_and_connect_times())
            except BluetoothPairConnectError as err:
                self.log.error(err)
                failure_data = {'timestamp': pair_connect_timestamp,
                                'error': str(err),
                                'pair_and_connect_attempt': attempt + 1}
                pair_connect_failures.append(failure_data)
                if not first_connection_failure:
                    first_connection_failure = err
            else:
                connect_times.append(connect_time)
                pair_times.append(pair_time)
                pair_connect_success += 1

            # Buffer between pair and connect attempts
            time.sleep(3)

        metrics['pair_attempt_count'] = PAIR_CONNECT_ATTEMPTS
        metrics['pair_successful_count'] = pair_connect_success
        metrics['pair_failed_count'] = (PAIR_CONNECT_ATTEMPTS -
                                        pair_connect_success)

        if len(pair_times) > 0:
            metrics['pair_max_time_millis'] = max(pair_times)
            metrics['pair_min_time_millis'] = min(pair_times)
            metrics['pair_avg_time_millis'] = statistics.mean(pair_times)

        if len(connect_times) > 0:
            metrics['first_conn_max_time_millis'] = max(connect_times)
            metrics['first_conn_min_time_millis'] = min(connect_times)
            metrics['first_conn_avg_time_millis'] = (statistics
                                                     .mean(connect_times))

        if pair_connect_failures:
            metrics['pair_conn_failure_info'] = pair_connect_failures

        self.log.info('Metrics: {}'.format(metrics))

        if PAIR_CONNECT_ATTEMPTS != pair_connect_success:
            raise TestFailure(str(first_connection_failure), extras=metrics)
        else:
            raise TestPass('Bluetooth pair and connect test passed',
                           extras=metrics)
