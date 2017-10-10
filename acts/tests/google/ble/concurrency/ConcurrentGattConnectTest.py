#/usr/bin/env python3.4
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
"""
Test script for concurrent Gatt connections.
Testbed assumes 6 Android devices. One will be the central and the rest
peripherals.
"""

from queue import Empty
import time
from acts.test_utils.bt.bt_gatt_utils import setup_gatt_connection
from acts.test_utils.bt.bt_constants import ble_scan_settings_modes
from acts.test_utils.bt.bt_constants import ble_advertise_settings_modes
from acts.test_utils.bt.bt_constants import bt_profile_constants
from acts.test_decorators import test_tracker_info
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest


class ConcurrentGattConnectTest(BluetoothBaseTest):
    bt_default_timeout = 10
    max_connections = 5

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.pri_dut = self.android_devices[0]

    @BluetoothBaseTest.bt_test_wrap
    @test_tracker_info(uuid='6638282c-69b5-4237-9f0d-18e131424a9f')
    def test_concurrent_gatt_connections(self):
        """Test max concurrent GATT connections

        Connect to all peripherals.

        Steps:
        1. Scan
        2. Save addresses
        3. Connect all addresses of the peripherals

        Expected Result:
        All connections successful.

        Returns:
          Pass if True
          Fail if False

        TAGS: Bluetooth, GATT
        Priority: 2
        """
        # Create 4 advertisements from different android devices
        # List of tuples (android_device, advertise_callback)
        advertise_callbacks = []
        # List of tuples (android_deivce, gatt_server_callback)
        gatt_server_callbacks = []
        # List of tubles (android_device, gatt_server)
        gatt_servers = []
        advertisement_names = []
        for i in range(1, self.max_connections + 1):
            # Set device name
            ad = self.android_devices[i]
            name = "test_adv_{}".format(i)
            advertisement_names.append(name)
            ad.droid.bluetoothSetLocalName(name)

            # Setup and start advertisements
            ad.droid.bleSetAdvertiseDataIncludeDeviceName(True)
            ad.droid.bleSetAdvertiseSettingsAdvertiseMode(
                ble_advertise_settings_modes['low_latency'])
            advertise_data = ad.droid.bleBuildAdvertiseData()
            advertise_settings = ad.droid.bleBuildAdvertiseSettings()
            advertise_callback = ad.droid.bleGenBleAdvertiseCallback()
            ad.droid.bleStartBleAdvertising(advertise_callback, advertise_data,
                                            advertise_settings)
            advertise_callbacks.append((ad, advertise_callback))
            # Setup generic Gatt server
            gatt_server_callback = ad.droid.gattServerCreateGattServerCallback(
            )
            gatt_server_callbacks.append((ad, gatt_server_callback))
            gatt_server = ad.droid.gattServerOpenGattServer(
                gatt_server_callback)
            gatt_servers.append((ad, gatt_server))

        # From central device, scan for all appropriate addresses by name
        filter_list = self.pri_dut.droid.bleGenFilterList()
        self.pri_dut.droid.bleSetScanSettingsScanMode(
            ble_scan_settings_modes['low_latency'])
        scan_settings = self.pri_dut.droid.bleBuildScanSetting()
        scan_callback = self.pri_dut.droid.bleGenScanCallback()
        for name in advertisement_names:
            self.pri_dut.droid.bleSetScanFilterDeviceName(name)
            self.pri_dut.droid.bleBuildScanFilter(filter_list)
        self.pri_dut.droid.bleStartBleScan(filter_list, scan_settings,
                                           scan_callback)
        address_list = []
        scan_timeout = 20
        end_time = time.time() + scan_timeout
        while time.time() < end_time and len(address_list) < len(
                self.android_devices) - 1:
            try:
                event = self.pri_dut.ed.pop_event(
                    "BleScan{}onScanResults".format(scan_callback),
                    self.bt_default_timeout)
                mac_address = event['data']['Result']['deviceInfo']['address']
                if mac_address not in address_list:
                    self.log.info(
                        "Found new mac address: {}".format(mac_address))
                    address_list.append(mac_address)
            except Empty as err:
                self.log.error("Failed to find any scan results.")
                return False
        if len(address_list) < self.max_connections:
            self.log.error("Could not find all necessary advertisements.")
            return False

        # Connect to all addresses
        for address in address_list:
            try:
                autoconnect = False
                bluetooth_gatt, gatt_callback = setup_gatt_connection(
                    self.pri_dut, address, autoconnect)
                self.log.info("Successfully connected to {}".format(address))
            except Exception as err:
                self.log.error(
                    "Failed to establish connection to {}".format(address))
                return False
        if (len(
                self.pri_dut.droid.bluetoothGetConnectedLeDevices(
                    bt_profile_constants['gatt_server'])) !=
                self.max_connections):
            self.log.error("Did not reach max connection count.")
            return False

        return True
