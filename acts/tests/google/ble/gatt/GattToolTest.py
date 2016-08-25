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
This test script is for partial automation of LE devices

This script requires these custom parameters in the config file:

"ble_mac_address"
"service_uuid"
"notifiable_char_uuid"
"""

import pprint
from queue import Empty
import time
from contextlib import suppress

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.GattEnum import GattCbStrings
from acts.test_utils.bt.GattEnum import GattDescriptor
from acts.test_utils.bt.GattEnum import GattTransport
from acts.test_utils.bt.bt_gatt_utils import GattTestUtilsError
from acts.test_utils.bt.bt_gatt_utils import disconnect_gatt_connection
from acts.test_utils.bt.bt_gatt_utils import setup_gatt_connection
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import generate_ble_scan_objects


class GattToolTest(BluetoothBaseTest):
    AUTOCONNECT = False
    DEFAULT_TIMEOUT = 10
    adv_instances = []
    timer_list = []

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        # Central role Android device
        self.cen_ad = self.android_devices[0]
        self.ble_mac_address = self.user_params['ble_mac_address']
        self.SERVICE_UUID = self.user_params['service_uuid']
        self.NOTIFIABLE_CHAR_UUID = self.user_params['notifiable_char_uuid']
        # CCC == Client Characteristic Configuration
        self.CCC_DESC_UUID = "00002902-0000-1000-8000-00805f9b34fb"

    def _get_time_in_milliseconds(self):
        return int(round(time.time() * 1000))

    def _log_stats(self):
        if self.timer_list:
            self.log.info("Overall list {}".format(self.timer_list))
            self.log.info("Average of list {}".format(
                sum(self.timer_list) / float(len(self.timer_list))))
            self.log.info("Maximum of list {}".format(max(self.timer_list)))
            self.log.info("Minimum of list {}".format(min(self.timer_list)))
            self.log.info("Total items in list {}".format(len(
                self.timer_list)))

    def setup_test(self):
        super().setup_test()
        input("Press enter when peripheral is advertising.")
        return True

    def teardown_test(self):
        super().teardown_test()
        self._log_stats()
        self.timer_list = []
        return True

    def _log_uuids(self, discovered_services_index):
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        for i in range(services_count):
            service = self.cen_ad.droid.gattClientGetDiscoveredServiceUuid(
                discovered_services_index, i)
            self.log.info("Discovered service uuid {}".format(service))
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic in characteristic_uuids:
                self.log.info("Discovered characteristic uuid {}".format(
                    characteristic))
                descriptor_uuids = (
                    self.cen_ad.droid.gattClientGetDiscoveredDescriptorUuids(
                        discovered_services_index, i, characteristic))
                for descriptor in descriptor_uuids:
                    self.log.info("Discovered descriptor uuid {}".format(
                        descriptor))

    def _pair_non_encrypted_device(self):
        self.cen_ad.droid.bluetoothDiscoverAndBond(self.ble_mac_address)
        end_time = time.time() + self.DEFAULT_TIMEOUT + 20
        self.log.info("Verifying devices are bonded")
        while time.time() < end_time:
            bonded_devices = self.cen_ad.droid.bluetoothGetBondedDevices()
            if self.ble_mac_address in {d['address'] for d in bonded_devices}:
                self.log.info("Successfully bonded to device")
                return True
            time.sleep(1)
        return False

    def _unbond_device(self):
        self.cen_ad.droid.bluetoothUnbond(self.ble_mac_address)
        time.sleep(2)  #Grace timeout for unbonding to finish
        bonded_devices = self.cen_ad.droid.bluetoothGetBondedDevices()
        if bonded_devices:
            self.log.error("Failed to unbond device... found: {}".format(
                bonded_devices))
            return False
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_without_scanning(self):
        """Test the round trip speed of connecting to a peripheral

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script will measure the amount
        of time it takes to establish a GATT connection to the
        peripheral. The test will then disconnect

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Start timer
        3. Perform GATT connection to peripheral
        4. Upon successful connection, stop timer
        5. Disconnect from peripheral

        Expected Result:
        Device should be connected successfully

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        self.AUTOCONNECT = False
        start_time = self._get_time_in_milliseconds()
        try:
            test_result, bluetooth_gatt, gatt_callback = (
                setup_gatt_connection(self.cen_ad, self.ble_mac_address,
                                      self.AUTOCONNECT,
                                      GattTransport.TRANSPORT_LE))
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        end_time = self._get_time_in_milliseconds()
        self.log.info("Total time (ms): {}".format(end_time - start_time))
        try:
            disconnect_gatt_connection(self.cen_ad, bluetooth_gatt,
                                       gatt_callback)
            self.cen_ad.droid.gattClientClose(bluetooth_gatt)
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        self.cen_ad.droid.gattClientClose(bluetooth_gatt)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_stress(self):
        """Test the round trip speed of connecting to a peripheral many times

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script will measure the amount
        of time it takes to establish a GATT connection to the
        peripheral. The test will then disconnect. It will attempt to
        repeat this process multiple times.

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Start timer
        3. Perform GATT connection to peripheral
        4. Upon successful connection, stop timer
        5. Disconnect from peripheral
        6. Repeat steps 2-5 1000 times.

        Expected Result:
        Test should measure 1000 iterations of connect/disconnect cycles.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
            self.cen_ad.droid)
        self.cen_ad.droid.bleStartBleScan(filter_list, scan_settings,
                                          scan_callback)
        self.AUTOCONNECT = False
        iterations = 1000
        n = 0
        while n < iterations:
            start_time = self._get_time_in_milliseconds()
            try:
                test_result, bluetooth_gatt, gatt_callback = (
                    setup_gatt_connection(self.cen_ad, self.ble_mac_address,
                                          self.AUTOCONNECT,
                                          GattTransport.TRANSPORT_LE))
            except GattTestUtilsError as err:
                self.log.error(err)
                return False
            end_time = self._get_time_in_milliseconds()
            total_time = end_time - start_time
            self.timer_list.append(total_time)
            self.log.info("Total time (ms): {}".format(total_time))
            try:
                disconnect_gatt_connection(self.cen_ad, bluetooth_gatt,
                                           gatt_callback)
                self.cen_ad.droid.gattClientClose(bluetooth_gatt)
            except GattTestUtilsError as err:
                self.log.error(err)
                return False
            n += 1
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_iterate_uuids(self):
        """Test the discovery of uuids of a peripheral

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script connects an Android device
        to the periphal and attempt to discover all services,
        characteristics, and descriptors.

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Perform GATT connection to peripheral
        3. Upon successful connection, iterate through all services,
        characteristics, and descriptors.
        5. Disconnect from peripheral

        Expected Result:
        Device services, characteristics, and descriptors should all
        be read.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        try:
            test_result, bluetooth_gatt, gatt_callback = (
                setup_gatt_connection(self.cen_ad, self.ble_mac_address,
                                      self.AUTOCONNECT,
                                      GattTransport.TRANSPORT_LE))
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            expected_event = GattCbStrings.GATT_SERV_DISC.value.format(
                gatt_callback)
            try:
                event = self.cen_ad.ed.pop_event(expected_event,
                                                 self.DEFAULT_TIMEOUT)
                discovered_services_index = event['data']['ServicesIndex']
            except Empty:
                self.log.error(
                    GattCbErr.GATT_SERV_DISC_ERR.value.format(expected_event))
                return False
            self._log_uuids(discovered_services_index)
        try:
            disconnect_gatt_connection(self.cen_ad, bluetooth_gatt,
                                       gatt_callback)
            self.cen_ad.droid.gattClientClose(bluetooth_gatt)
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        self.cen_ad.droid.gattClientClose(bluetooth_gatt)
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_classic_pairing(self):
        """Test pairing to a GATT mac address through classic methods

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script will bond the Android device
        to the peripheral through classic pairing methods.

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Perform Bluetooth pairing to GATT mac address
        3. Upon successful bonding.
        4. Unbond from device

        Expected Result:
        Device services, characteristics, and descriptors should all
        be read.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        if not self._pair_non_encrypted_device():
            return False
        self.cen_ad.droid.bluetoothUnbond(self.ble_mac_address)
        return self._unbond_device()

    @BluetoothBaseTest.bt_test_wrap
    def test_classic_pairing_stress(self):
        """Test the round trip speed of pairing to a peripheral many times

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script will measure the amount
        of time it takes to establish a pairing with a BLE device through
        classic pairing methods.

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Start timer
        3. Perform Bluetooth pairing to GATT mac address
        4. Upon successful bonding, stop timer.
        5. Unbond from device
        6. Repeat steps 2-5 100 times.

        Expected Result:
        Test should measure 100 iterations of bonding.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        iterations = 100
        for _ in range(iterations):
            start_time = self._get_time_in_milliseconds()
            if not self._pair_non_encrypted_device():
                return False
            end_time = self._get_time_in_milliseconds()
            total_time = end_time - start_time
            self.timer_list.append(total_time)
            self.log.info("Total time (ms): {}".format(total_time))
            if not self._unbond_device():
                return False
        return False

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_notification_longev(self):
        """Test GATT characterisitic notifications for long periods of time

        This test will prompt the user to press "Enter" when the
        peripheral is in a connecable advertisement state. Once
        the user presses enter, this script aims to set characteristic
        notification to true on the config file's SERVICE_UUID,
        NOTIFIABLE_CHAR_UUID, and CCC_DESC_UUID. This test assumes
        the peripheral will constantly write data to a notifiable
        characteristic.

        Steps:
        1. Wait for user input to confirm peripheral is advertising.
        2. Perform Bluetooth pairing to GATT mac address
        3. Perform a GATT connection to the periheral
        4. Get the discovered service uuid that matches the user's input
        in the config file
        4. Write to the CCC descriptor to enable notifications
        5. Enable notifications on the user's input Characteristic UUID
        6. Continuously wait for Characteristic Changed events which
        equate to recieving notifications for 15 minutes.

        Expected Result:
        There should be no disconnects and we should constantly receive
        Characteristic Changed information. Values should vary upon user
        interaction with the peripheral.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, GATT
        Priority: 1
        """
        #pair devices
        if not self._pair_non_encrypted_device():
            return False
        try:
            test_result, bluetooth_gatt, gatt_callback = (
                setup_gatt_connection(self.cen_ad, self.ble_mac_address,
                                      self.AUTOCONNECT,
                                      GattTransport.TRANSPORT_LE))
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            expected_event = GattCbStrings.GATT_SERV_DISC.value.format(
                gatt_callback)
            try:
                event = self.cen_ad.ed.pop_event(expected_event,
                                                 self.DEFAULT_TIMEOUT)
                discovered_services_index = event['data']['ServicesIndex']
            except Empty:
                self.log.error(
                    GattCbErr.GATT_SERV_DISC_ERR.value.format(expected_event))
                return False
        # TODO: in setup save service_cound and discovered_services_index
        # programatically
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        test_service_index = None
        for i in range(services_count):
            disc_service_uuid = (
                self.cen_ad.droid.gattClientGetDiscoveredServiceUuid(
                    discovered_services_index, i))
            if disc_service_uuid == self.SERVICE_UUID:
                test_service_index = i
                break
        if not test_service_index:
            self.log.error("Service not found.")
            return False

        self.cen_ad.droid.gattClientDescriptorSetValue(
            bluetooth_gatt, discovered_services_index, test_service_index,
            self.NOTIFIABLE_CHAR_UUID, self.CCC_DESC_UUID,
            GattDescriptor.ENABLE_NOTIFICATION_VALUE.value)

        self.cen_ad.droid.gattClientWriteDescriptor(
            bluetooth_gatt, discovered_services_index, test_service_index,
            self.NOTIFIABLE_CHAR_UUID, self.CCC_DESC_UUID)

        self.cen_ad.droid.gattClientSetCharacteristicNotification(
            bluetooth_gatt, discovered_services_index, test_service_index,
            self.NOTIFIABLE_CHAR_UUID, True)

        # set 15 minute notification test time
        notification_test_time = 900
        end_time = time.time() + notification_test_time
        expected_event = GattCbStrings.CHAR_CHANGE.value.format(bluetooth_gatt)
        while time.time() < end_time:
            try:
                self.log.info(
                    self.cen_ad.ed.pop_event(expected_event,
                                             self.DEFAULT_TIMEOUT))
            except Empty as err:
                self.log.error(
                    GattCbStrings.CHAR_CHANGE_ERR.value.format(expected_event))
                return False
        return True
