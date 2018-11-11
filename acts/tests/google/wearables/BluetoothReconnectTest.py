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
"""Bluetooth disconnect and reconnect verification."""
# Quick way to get the Apollo serial number:
# python3.5 -c "from acts.controllers.buds_lib.apollo_lib import get_devices; [print(d['serial_number']) for d in get_devices()]"

import time
from acts import asserts
from acts.base_test import BaseTestClass
from acts.controllers.buds_lib.test_actions.apollo_acts import ApolloTestActions
from acts.test_utils.bt.bt_test_utils import clear_bonded_devices
from acts.test_utils.bt.bt_test_utils import disable_bluetooth
from acts.test_utils.bt.bt_test_utils import enable_bluetooth
from acts.utils import set_location_service

class BluetoothReconnectTest(BaseTestClass):
    """Class representing a TestCase object for handling execution of tests."""

    # TODO: add ACTS style metrics logging
    def __init__(self, configs):
        BaseTestClass.__init__(self, configs)
        # sanity check of the dut devices.
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

    def setup_test(self):
        # Make sure bluetooth is on
        enable_bluetooth(self.phone.droid, self.phone.ed)
        set_location_service(self.phone, True)
        self.log.info('===== START BLUETOOTH RECONNECT TEST  =====')
        return True

    def teardown_test(self):
        self.log.info('Teardown test, shutting down all services...')
        self.apollo.close()
        return True

    def test_bluetooth_reconnect_after_android_disconnect(self):
        """Main test method."""
        # Make sure devices are paired and connected
        clear_bonded_devices(self.phone)
        self.apollo_act.factory_reset()

        # Buffer between reset and pairing
        time.sleep(5)

        self.phone.droid.bluetoothDiscoverAndBond(self.dut_bt_addr)
        paired_and_connected = self.apollo_act.wait_for_bluetooth_a2dp_hfp()
        asserts.assert_true(paired_and_connected,
                            "Failed to pair and connect devices")

        # Disconnect Bluetooth from the phone side
        self.log.info("Disabling Bluetooth on phone")
        bluetooth_disabled = disable_bluetooth(self.phone.droid)
        asserts.assert_true(bluetooth_disabled,
                            "Failed to disconnect Bluetooth from phone")
        self.log.info("Bluetooth disabled on phone")

        # Buffer between disconnect and reconnect
        time.sleep(5)

        # Reconnect Bluetooth from the phone side
        self.log.info("Enabling Bluetooth on phone")
        bluetooth_enabled = enable_bluetooth(self.phone.droid, self.phone.ed)
        asserts.assert_true(bluetooth_enabled,
                            "Failed to reconnect Bluetooth from phone")
        self.log.info("Bluetooth enabled on phone")

        # Verify that the devices have reconnected
        devices_reconnected = self.apollo_act.wait_for_bluetooth_a2dp_hfp()
        asserts.assert_true(devices_reconnected,
                            "Bluetooth profiles failed to reconnect")