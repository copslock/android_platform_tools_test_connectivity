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
This test script exercises different GATT connection tests.
"""

import pprint
from queue import Empty
import time
from contextlib import suppress

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.BleEnum import BluetoothGattCharacteristic
from acts.test_utils.bt.BleEnum import BluetoothGattDescriptor
from acts.test_utils.bt.BleEnum import BluetoothGattService
from acts.test_utils.bt.BleEnum import BluetoothMtuSize
from acts.test_utils.bt.bt_test_utils import characteristic_write_request
from acts.test_utils.bt.bt_test_utils import characteristic_write
from acts.test_utils.bt.bt_test_utils import descriptor_write
from acts.test_utils.bt.bt_test_utils import descriptor_write_request
from acts.test_utils.bt.bt_test_utils import disconnect_gatt_connection
from acts.test_utils.bt.bt_test_utils import gatt_services_discovered
from acts.test_utils.bt.bt_test_utils import get_advanced_droid_list
from acts.test_utils.bt.bt_test_utils import get_mac_address_of_generic_advertisement
from acts.test_utils.bt.bt_test_utils import mtu_changed
from acts.test_utils.bt.bt_test_utils import orchestrate_gatt_connection
from acts.test_utils.bt.bt_test_utils import read_remote_rssi
from acts.test_utils.bt.bt_test_utils import service_added
from acts.test_utils.bt.bt_test_utils import setup_gatt_characteristics
from acts.test_utils.bt.bt_test_utils import setup_gatt_connection
from acts.test_utils.bt.bt_test_utils import setup_gatt_descriptors
from acts.test_utils.bt.bt_test_utils import log_energy_info


class GattConnectTest(BluetoothBaseTest):
    tests = None
    adv_instances = []
    default_timeout = 10
    default_discovery_timeout = 3
    droid_list = ()

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.droid_list = get_advanced_droid_list(self.android_devices)
        self.cen_ad = self.android_devices[0]
        self.per_ad = self.android_devices[1]
        if self.droid_list[1]['max_advertisements'] == 0:
            self.tests = ()
            return
        self.tests = (
            "test_gatt_connect",
            "test_gatt_request_min_mtu",
            "test_gatt_request_max_mtu",
            "test_gatt_request_out_of_bounds_mtu",
            "test_gatt_connect_trigger_on_read_rssi",
            "test_gatt_connect_trigger_on_services_discovered",
            "test_gatt_connect_trigger_on_services_discovered_iterate_attributes",
            "test_gatt_connect_with_service_uuid_variations",
            "test_gatt_connect_in_quick_succession",
            "test_write_descriptor_stress",
            "test_gatt_connect_mitm_attack",
        )

    def teardown_test(self):
        for adv in self.adv_instances:
            self.per_ad.droid.bleStopBleAdvertising(adv)
        self.log.debug(log_energy_info(self.android_devices, "End"))
        return True

    def _setup_characteristics_and_descriptors(self, droid):
        characteristic_input = [
            {
                'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
                'property': BluetoothGattCharacteristic.PROPERTY_WRITE.value |
                        BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE.value,
                'permission': BluetoothGattCharacteristic.PROPERTY_WRITE.value
            },
            {
                'uuid': "21c0a0bf-ad51-4a2d-8124-b74003e4e8c8",
                'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
                        BluetoothGattCharacteristic.PROPERTY_READ.value,
                'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
            },
            {
                'uuid': "6774191f-6ec3-4aa2-b8a8-cf830e41fda6",
                'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
                        BluetoothGattCharacteristic.PROPERTY_READ.value,
                'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
            },
        ]
        descriptor_input = [
            {
                'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
                'property': BluetoothGattDescriptor.PERMISSION_READ.value |
                        BluetoothGattDescriptor.PERMISSION_WRITE.value,
            },
            {
                'uuid': "76d5ed92-ca81-4edb-bb6b-9f019665fb32",
                'property': BluetoothGattDescriptor.PERMISSION_READ.value |
                        BluetoothGattCharacteristic.PERMISSION_WRITE.value,
            }
        ]
        characteristic_list = setup_gatt_characteristics(
            droid, characteristic_input)
        descriptor_list = setup_gatt_descriptors(droid, descriptor_input)
        return characteristic_list, descriptor_list

    def _orchestrate_gatt_disconnection(self, bluetooth_gatt, gatt_callback):
        self.log.info("Disconnecting from peripheral device.")
        test_result = disconnect_gatt_connection(
            self.cen_ad, bluetooth_gatt, gatt_callback)
        if not test_result:
            self.log.info("Failed to disconnect from peripheral device.")
            return False
        return True

    def _iterate_attributes(self, discovered_services_index):
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
                self.log.info(
                    "Discovered characteristic uuid {}".format(characteristic))
                descriptor_uuids = (
                    self.cen_ad.droid.gattClientGetDiscoveredDescriptorUuids(
                        discovered_services_index, i, characteristic))
                for descriptor in descriptor_uuids:
                    self.log.info(
                        "Discovered descriptor uuid {}".format(descriptor))

    def _find_service_added_event(self, gatt_server_callback, uuid):
        event = self.per_ad.ed.pop_event(
            service_added.format(gatt_server_callback),
            self.default_timeout)
        if event['data']['serviceUuid'].lower() != uuid.lower():
            self.log.info(
                "Uuid mismatch. Found: {}, Expected {}.".format(
                    event['data']['serviceUuid'],
                    uuid))
            return False
        return True

    def _setup_multiple_services(self):
        gatt_server_callback = (
            self.per_ad.droid.gattServerCreateGattServerCallback())
        gatt_server = self.per_ad.droid.gattServerOpenGattServer(
            gatt_server_callback)
        characteristic_list, descriptor_list = (
            self._setup_characteristics_and_descriptors(self.per_ad.droid))
        self.per_ad.droid.gattServerCharacteristicAddDescriptor(
            characteristic_list[1], descriptor_list[0])
        self.per_ad.droid.gattServerCharacteristicAddDescriptor(
            characteristic_list[2], descriptor_list[1])
        gatt_service = self.per_ad.droid.gattServerCreateService(
            "00000000-0000-1000-8000-00805f9b34fb",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        gatt_service2 = self.per_ad.droid.gattServerCreateService(
            "FFFFFFFF-0000-1000-8000-00805f9b34fb",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        gatt_service3 = self.per_ad.droid.gattServerCreateService(
            "3846D7A0-69C8-11E4-BA00-0002A5D5C51B",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        for characteristic in characteristic_list:
            self.per_ad.droid.gattServerAddCharacteristicToService(gatt_service,
                                                                characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback, "00000000-0000-1000-8000-00805f9b34fb")
        if not result:
            return False
        for characteristic in characteristic_list:
            self.per_ad.droid.gattServerAddCharacteristicToService(gatt_service2,
                                                                characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service2)
        result = self._find_service_added_event(
            gatt_server_callback, "FFFFFFFF-0000-1000-8000-00805f9b34fb")
        if not result:
            return False
        for characteristic in characteristic_list:
            self.per_ad.droid.gattServerAddCharacteristicToService(gatt_service3,
                                                                characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service3)
        result = self._find_service_added_event(
            gatt_server_callback, "3846D7A0-69C8-11E4-BA00-0002A5D5C51B")
        if not result:
            return False, False
        return gatt_server_callback, gatt_server

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect(self):
        """Test GATT connection over LE.

        Test establishing a gatt connection between a GATT server and GATT
        client.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT
        Priority: 0
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_request_min_mtu(self):
        """Test GATT connection over LE and exercise MTU sizes.

        Test establishing a gatt connection between a GATT server and GATT
        client. Request an MTU size that matches the correct minimum size.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (client) request MTU size change to the
        minimum value.
        7. Find the MTU changed event on the client.
        8. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and the MTU value found
        matches the expected MTU value.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, MTU
        Priority: 0
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        self.cen_ad.droid.gattClientRequestMtu(bluetooth_gatt,
                                            BluetoothMtuSize.MIN.value)
        mtu_event = self.cen_ad.ed.pop_event(mtu_changed.format(bluetooth_gatt))
        if mtu_event['data']['MTU'] != BluetoothMtuSize.MIN.value:
            return False
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_request_max_mtu(self):
        """Test GATT connection over LE and exercise MTU sizes.

        Test establishing a gatt connection between a GATT server and GATT
        client. Request an MTU size that matches the correct maximum size.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (client) request MTU size change to the
        maximum value.
        7. Find the MTU changed event on the client.
        8. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and the MTU value found
        matches the expected MTU value.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, MTU
        Priority: 0
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        self.cen_ad.droid.gattClientRequestMtu(bluetooth_gatt,
            BluetoothMtuSize.MAX.value)
        mtu_event = self.cen_ad.ed.pop_event(mtu_changed.format(bluetooth_gatt))
        if mtu_event['data']['MTU'] != BluetoothMtuSize.MAX.value:
            return False
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_request_out_of_bounds_mtu(self):
        """Test GATT connection over LE and exercise an out of bound MTU size.

        Test establishing a gatt connection between a GATT server and GATT
        client. Request an MTU size that is the MIN value minus 1.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (client) request MTU size change to the
        minimum value minus one.
        7. Find the MTU changed event on the client.
        8. Disconnect the GATT connection.

        Expected Result:
        Verify that an MTU changed event was not discovered and that
        it didn't cause an exception when requesting an out of bounds
        MTU.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, MTU
        Priority: 0
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        self.cen_ad.droid.gattClientRequestMtu(bluetooth_gatt,
            BluetoothMtuSize.MIN.value - 1)
        try:
            self.cen_ad.ed.pop_event(mtu_changed.format(bluetooth_gatt),
                    self.default_timeout)
            self.log.error("Found {} event when it wasn't expected".
                    format(mtu_changed.format(bluetooth_gatt)))
            return False
        except Exception:
            self.log.debug("Successfully didn't find {} event"
                           .format(mtu_changed.format(bluetooth_gatt)))
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_trigger_on_read_rssi(self):
        """Test GATT connection over LE read RSSI.

        Test establishing a gatt connection between a GATT server and GATT
        client then read the RSSI.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner, request to read the RSSI of the advertiser.
        7. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully. Verify that the RSSI was ready correctly.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, RSSI
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientReadRSSI(bluetooth_gatt):
            self.cen_ad.ed.pop_event(
                read_remote_rssi.format(gatt_callback), self.default_timeout)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_trigger_on_services_discovered(self):
        """Test GATT connection and discover services of peripheral.

        Test establishing a gatt connection between a GATT server and GATT
        client the discover all services from the connected device.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (central device), discover services.
        7. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully. Verify that the service were discovered.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Services
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_trigger_on_services_discovered_iterate_attributes(self):
        """Test GATT connection and iterate peripherals attributes.

        Test establishing a gatt connection between a GATT server and GATT
        client and iterate over all the characteristics and descriptors of the
        discovered services.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (central device), discover services.
        7. Iterate over all the characteristics and descriptors of the
        discovered features.
        8. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully. Verify that the services, characteristics, and descriptors
        were discovered.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Services
        Characteristics, Descriptors
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
            self._iterate_attributes(discovered_services_index)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_with_service_uuid_variations(self):
        """Test GATT connection with multiple service uuids.

        Test establishing a gatt connection between a GATT server and GATT
        client with multiple service uuid variations.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. From the scanner (central device), discover services.
        7. Verify that all the service uuid variations are found.
        8. Disconnect the GATT connection.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully. Verify that the service uuid variations are found.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Services
        Priority: 2
        """
        gatt_server_callback, gatt_server = self._setup_multiple_services()
        if not gatt_server_callback or not gatt_server:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
            self._iterate_attributes(discovered_services_index)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_connect_in_quick_succession(self):
        """Test GATT connections multiple times.

        Test establishing a gatt connection between a GATT server and GATT
        client with multiple iterations.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. Disconnect the GATT connection.
        7. Repeat steps 5 and 6 twenty times.

        Expected Result:
        Verify that a connection was established and then disconnected
        successfully twenty times.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Stress
        Priority: 1
        """
        mac_address, adv_callback = get_mac_address_of_generic_advertisement(
            self.cen_ad, self.per_ad)
        autoconnect = False
        for i in range(20):
            test_result, bluetooth_gatt, gatt_callback = setup_gatt_connection(
                self.cen_ad, mac_address, autoconnect)
            if not test_result:
                self.log.info("Could not connect to peripheral.")
                return False
            test_result = self._orchestrate_gatt_disconnection(
                bluetooth_gatt, gatt_callback)
            # Temporary fix
            time.sleep(3)
            if not test_result:
                self.log.info("Failed to disconnect from peripheral device.")
                return False
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_write_descriptor_stress(self):
        """Test GATT connection writing and reading descriptors.

        Test establishing a gatt connection between a GATT server and GATT
        client with multiple service uuid variations.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. Discover services.
        7. Write data to the descriptors of each characteristic 100 times.
        8. Read the data sent to the descriptors.
        9. Disconnect the GATT connection.

        Expected Result:
        Each descriptor in each characteristic is written and read 100 times.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Stress,
        Characteristics, Descriptors
        Priority: 1
        """
        gatt_server_callback, gatt_server = self._setup_multiple_services()
        if not gatt_server_callback or not gatt_server:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)

        connected_device_list = self.per_ad.droid.gattServerGetConnectedDevices(
            gatt_server)
        if len(connected_device_list) == 0:
            self.log.info("No devices connected from peripheral.")
            return False
        bt_device_id = 0
        status = 1
        offset = 1
        test_value = "1,2,3,4,5,6,7"
        test_value_return = "1,2,3"
        for i in range(services_count):
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic in characteristic_uuids:
                descriptor_uuids = (
                    self.cen_ad.droid.gattClientGetDiscoveredDescriptorUuids(
                        discovered_services_index, i, characteristic))
                for x in range(100):
                    for descriptor in descriptor_uuids:
                        self.cen_ad.droid.gattClientDescriptorSetValue(
                            bluetooth_gatt, discovered_services_index, i,
                            characteristic, descriptor, test_value)
                        self.cen_ad.droid.gattClientWriteDescriptor(
                            bluetooth_gatt, discovered_services_index, i,
                            characteristic, descriptor)
                        event = self.per_ad.ed.pop_event(
                            descriptor_write_request.format(
                                gatt_server_callback), self.default_timeout)
                        self.log.info("{} event found: {}".format(
                                      descriptor_write_request.format(
                                          gatt_callback), event))
                        request_id = event['data']['requestId']
                        found_value = event['data']['value']
                        if found_value != test_value:
                            self.log.info("Values didn't match. Found: {}, "
                                          "Expected: {}".format(found_value,
                                                                test_value))
                            return False
                        self.per_ad.droid.gattServerSendResponse(
                            gatt_server, bt_device_id, request_id, status,
                            offset, test_value_return)
                        self.log.info("onDescriptorWrite event found: {}"
                                      .format(
                            self.cen_ad.ed.pop_event(
                                descriptor_write.format(gatt_callback),
                                self.default_timeout)))
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_write_characteristic(self):
        """Test GATT connection writing characteristics.

        Test establishing a gatt connection between a GATT server and GATT
        client and exercise writing a characteristic.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. Discover services.
        7. Set discovered characteristic notification to True
        8. Write data to the characteristic.
        9. Send a response from the peripheral to the central.
        10. Disconnect the GATT connection.

        Expected Result:
        The characteristic data should be written successfully

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Stress,
        Characteristics, Descriptors
        Priority: 1
        """
        gatt_server_callback = self.per_ad.droid.gattServerCreateGattServerCallback(
        )
        gatt_server = self.per_ad.droid.gattServerOpenGattServer(
            gatt_server_callback)
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))

        service_uuid = "3846D7A0-69C8-11E4-BA00-0002A5D5C51B"
        characteristic_uuid = "aa7edd5a-4d1d-4f0e-883a-d145616a1630"
        descriptor_uuid = "aa7edd5a-4d1d-4f0e-883a-d145616a1630"

        characteristic = (
            self.per_ad.droid.gattServerCreateBluetoothGattCharacteristic(
                characteristic_uuid,
                BluetoothGattCharacteristic.PROPERTY_WRITE.value,
                BluetoothGattCharacteristic.PERMISSION_WRITE.value))

        descriptor = self.per_ad.droid.gattServerCreateBluetoothGattDescriptor(
            descriptor_uuid,
            BluetoothGattDescriptor.PERMISSION_READ.value |
            BluetoothGattDescriptor.PERMISSION_WRITE.value,
        )
        self.per_ad.droid.gattServerCharacteristicAddDescriptor(
            characteristic, descriptor)

        gatt_service = self.per_ad.droid.gattServerCreateService(
            service_uuid,
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value
        )

        self.per_ad.droid.gattServerAddCharacteristicToService(gatt_service,
                                                            characteristic)

        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback, service_uuid)
        if not result:
            return False

        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))

        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        disc_service_index = 0
        for i in range(services_count):
            disc_service_uuid = (
                self.cen_ad.droid.gattClientGetDiscoveredServiceUuid(
                    discovered_services_index, i).upper())
            if disc_service_uuid == service_uuid:
                disc_service_index = i
                break

        self.cen_ad.droid.gattClientSetCharacteristicNotification(
            gatt_callback,
            discovered_services_index,
            disc_service_index,
            characteristic_uuid,
            True
        )

        test_value = "1,2,3,4,5,6,7"
        self.cen_ad.droid.gattClientCharacteristicSetValue(
            bluetooth_gatt,
            discovered_services_index,
            disc_service_index,
            characteristic_uuid,
            test_value
        )

        self.cen_ad.droid.gattClientWriteCharacteristic(
            bluetooth_gatt,
            discovered_services_index,
            disc_service_index,
            characteristic_uuid
        )

        event = self.per_ad.ed.pop_event(
            characteristic_write_request.format(gatt_server_callback),
            self.default_timeout
        )

        request_id = event['data']['requestId']
        bt_device_id = 0
        status = 1
        offset = 1
        test_value_return = "1,2,3"
        self.per_ad.droid.gattServerGetConnectedDevices(gatt_server)
        self.per_ad.droid.gattServerSendResponse(
            gatt_server,
            bt_device_id,
            request_id,
            status,
            offset,
            test_value_return
        )

        self.cen_ad.ed.pop_event(
            characteristic_write.format(bluetooth_gatt),
            self.default_timeout
        )
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_write_characteristic_stress(self):
        """Test GATT connection writing characteristics in quick succession.

        Test establishing a gatt connection between a GATT server and GATT
        client and exercise writing a characteristic. Do this quickly 100 times.

        Steps:
        1. Start a generic advertisement.
        2. Start a generic scanner.
        3. Find the advertisement and extract the mac address.
        4. Stop the first scanner.
        5. Create a GATT connection between the scanner and advertiser.
        6. Discover services.
        7. Set discovered characteristic notification to True.
        8. Write data to the characteristic 100 times as fast as possible.
        9. Send a response from the peripheral to the central.
        10. Disconnect the GATT connection.

        Expected Result:
        The characteristic data should be written successfully each iteration

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Stress,
        Characteristics, Descriptors
        Priority: 1
        """
        gatt_server_callback, gatt_server = self._setup_multiple_services()
        if not gatt_server_callback or not gatt_server:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)

        connected_device_list = self.per_ad.droid.gattServerGetConnectedDevices(
            gatt_server)
        if len(connected_device_list) == 0:
            self.log.info("No devices connected from peripheral.")
            return False
        bt_device_id = 0
        status = 1
        offset = 1
        test_value = "1,2,3,4,5,6,7"
        test_value_return = "1,2,3"
        for i in range(services_count):
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for i in range(100):
                for characteristic in characteristic_uuids:
                    self.cen_ad.droid.gattClientCharacteristicSetValue(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic, test_value)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic)
                    time.sleep(8)
                    event = self.per_ad.ed.pop_event(
                        characteristic_write_request.format(
                            gatt_server_callback), self.default_timeout)
                    self.log.info("{} event found: {}".format(
                                  characteristic_write_request.format(
                                      gatt_server_callback), event))
                    request_id = event['data']['requestId']
                    found_value = event['data']['value']
                    if found_value != test_value:
                        self.log.info("Values didn't match. Found: {}, "
                                      "Expected: {}".format(found_value,
                                                            test_value))
                        return False
                    self.per_ad.droid.gattServerSendResponse(
                        gatt_server, bt_device_id, request_id, status, offset,
                        test_value_return)
                    self.log.info(
                        "onCharacteristicWrite event found: {}".format(
                            characteristic_write_request.format(
                                gatt_server_callback),
                            self.cen_ad.ed.pop_event(
                                characteristic_write.format(bluetooth_gatt),
                                self.default_timeout)))
        return True

    def test_gatt_connect_mitm_attack(self):
        """Test GATT connection with permission write encrypted mitm.

        Test establishing a gatt connection between a GATT server and GATT
        client while the GATT server's characteristic includes the property
        write value and the permission write encrypted mitm value. This will
        prompt LE pairing and then the devices will create a bond.

        Steps:
        1. Create a GATT server and server callback on the peripheral device.
        2. Create a unique service and characteristic uuid on the peripheral.
        3. Create a characteristic on the peripheral with these properties:
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        4. Create a GATT service on the peripheral.
        5. Add the characteristic to the GATT service.
        6. Create a GATT connection between your central and peripheral device.
        7. From the central device, discover the peripheral's services.
        8. Iterate the services found until you find the unique characteristic
            created in step 3.
        9. Once found, write a random but valid value to the characteristic.
        10. Start pairing helpers on both devices immediately after attempting
            to write to the characteristic.
        11. Within 10 seconds of writing the characteristic, there should be
            a prompt to bond the device from the peripheral. The helpers will
            handle the UI interaction automatically. (see
            BluetoothConnectionFacade.java bluetoothStartPairingHelper).
        12. Verify that the two devices are bonded.

        Expected Result:
        Verify that a connection was established and the devices are bonded.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Characteristic, MITM
        Priority: 1
        """
        gatt_server_callback = (
            self.per_ad.droid.gattServerCreateGattServerCallback())
        gatt_server = self.per_ad.droid.gattServerOpenGattServer(
            gatt_server_callback)
        service_uuid = "3846D7A0-69C8-11E4-BA00-0002A5D5C51B"
        test_uuid = "aa7edd5a-4d1d-4f0e-883a-d145616a1630"
        bonded = False
        characteristic = self.per_ad.droid.gattServerCreateBluetoothGattCharacteristic(
            test_uuid,
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        )
        gatt_service = self.per_ad.droid.gattServerCreateService(
            service_uuid,
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value
        )
        self.per_ad.droid.gattServerAddCharacteristicToService(
            gatt_service, characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback,
            service_uuid)
        if not result:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        test_value = "1,2,3,4,5,6,7"
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        for i in range(services_count):
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic_uuid in characteristic_uuids:
                if characteristic_uuid == test_uuid:
                    self.cen_ad.droid.bluetoothStartPairingHelper()
                    self.per_ad.droid.bluetoothStartPairingHelper()
                    self.cen_ad.droid.gattClientCharacteristicSetValue(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid, test_value)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid)
                    start_time = time.time() + self.default_timeout
                    target_name = self.per_ad.droid.bluetoothGetLocalName()
                    while time.time() < start_time and bonded == False:
                        bonded_devices = self.cen_ad.droid.bluetoothGetBondedDevices()
                        for device in bonded_devices:
                            if 'name' in device.keys() and device['name'] == target_name:
                                bonded = True
                                break
        return True

    def test_gatt_connect_mitm_attack(self):
        """Test GATT connection with permission write encrypted mitm.

        Test establishing a gatt connection between a GATT server and GATT
        client while the GATT server's characteristic includes the property
        write value and the permission write encrypted mitm value. This will
        prompt LE pairing and then the devices will create a bond.

        Steps:
        1. Create a GATT server and server callback on the peripheral device.
        2. Create a unique service and characteristic uuid on the peripheral.
        3. Create a characteristic on the peripheral with these properties:
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        4. Create a GATT service on the peripheral.
        5. Add the characteristic to the GATT service.
        6. Create a GATT connection between your central and peripheral device.
        7. From the central device, discover the peripheral's services.
        8. Iterate the services found until you find the unique characteristic
            created in step 3.
        9. Once found, write a random but valid value to the characteristic.
        10. Start pairing helpers on both devices immediately after attempting
            to write to the characteristic.
        11. Within 10 seconds of writing the characteristic, there should be
            a prompt to bond the device from the peripheral. The helpers will
            handle the UI interaction automatically. (see
            BluetoothConnectionFacade.java bluetoothStartPairingHelper).
        12. Verify that the two devices are bonded.

        Expected Result:
        Verify that a connection was established and the devices are bonded.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Characteristic, MITM
        Priority: 1
        """
        gatt_server_callback = (
            self.per_ad.droid.gattServerCreateGattServerCallback())
        gatt_server = self.per_ad.droid.gattServerOpenGattServer(
            gatt_server_callback)
        service_uuid = "3846D7A0-69C8-11E4-BA00-0002A5D5C51B"
        test_uuid = "aa7edd5a-4d1d-4f0e-883a-d145616a1630"
        bonded = False
        characteristic = self.per_ad.droid.gattServerCreateBluetoothGattCharacteristic(
            test_uuid,
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        )
        gatt_service = self.per_ad.droid.gattServerCreateService(
            service_uuid,
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value
        )
        self.per_ad.droid.gattServerAddCharacteristicToService(
            gatt_service, characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback,
            service_uuid)
        if not result:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        test_value = "1,2,3,4,5,6,7"
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        for i in range(services_count):
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic_uuid in characteristic_uuids:
                if characteristic_uuid == test_uuid:
                    self.cen_ad.droid.bluetoothStartPairingHelper()
                    self.per_ad.droid.bluetoothStartPairingHelper()
                    self.cen_ad.droid.gattClientCharacteristicSetValue(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid, test_value)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid)
                    start_time = time.time() + self.default_timeout
                    target_name = self.per_ad.droid.bluetoothGetLocalName()
                    while time.time() < start_time and bonded == False:
                        bonded_devices = self.cen_ad.droid.bluetoothGetBondedDevices()
                        for device in bonded_devices:
                            if 'name' in device.keys() and device['name'] == target_name:
                                bonded = True
                                break
        return True

    def test_gatt_connect_mitm_attack(self):
        """Test GATT connection with permission write encrypted mitm.

        Test establishing a gatt connection between a GATT server and GATT
        client while the GATT server's characteristic includes the property
        write value and the permission write encrypted mitm value. This will
        prompt LE pairing and then the devices will create a bond.

        Steps:
        1. Create a GATT server and server callback on the peripheral device.
        2. Create a unique service and characteristic uuid on the peripheral.
        3. Create a characteristic on the peripheral with these properties:
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        4. Create a GATT service on the peripheral.
        5. Add the characteristic to the GATT service.
        6. Create a GATT connection between your central and peripheral device.
        7. From the central device, discover the peripheral's services.
        8. Iterate the services found until you find the unique characteristic
            created in step 3.
        9. Once found, write a random but valid value to the characteristic.
        10. Start pairing helpers on both devices immediately after attempting
            to write to the characteristic.
        11. Within 10 seconds of writing the characteristic, there should be
            a prompt to bond the device from the peripheral. The helpers will
            handle the UI interaction automatically. (see
            BluetoothConnectionFacade.java bluetoothStartPairingHelper).
        12. Verify that the two devices are bonded.

        Expected Result:
        Verify that a connection was established and the devices are bonded.

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Filtering, Scanning, GATT, Characteristic, MITM
        Priority: 1
        """
        gatt_server_callback = (
            self.per_ad.droid.gattServerCreateGattServerCallback())
        gatt_server = self.per_ad.droid.gattServerOpenGattServer(
            gatt_server_callback)
        service_uuid = "3846D7A0-69C8-11E4-BA00-0002A5D5C51B"
        test_uuid = "aa7edd5a-4d1d-4f0e-883a-d145616a1630"
        bonded = False
        characteristic = self.per_ad.droid.gattServerCreateBluetoothGattCharacteristic(
            test_uuid,
            BluetoothGattCharacteristic.PROPERTY_WRITE.value,
            BluetoothGattCharacteristic.PERMISSION_WRITE_ENCRYPTED_MITM.value
        )
        gatt_service = self.per_ad.droid.gattServerCreateService(
            service_uuid,
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value
        )
        self.per_ad.droid.gattServerAddCharacteristicToService(
            gatt_service, characteristic)
        self.per_ad.droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback,
            service_uuid)
        if not result:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_ad, self.per_ad))
        self.adv_instances.append(adv_callback)
        if self.cen_ad.droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ad.ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        test_value = "1,2,3,4,5,6,7"
        services_count = self.cen_ad.droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        for i in range(services_count):
            characteristic_uuids = (
                self.cen_ad.droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic_uuid in characteristic_uuids:
                if characteristic_uuid == test_uuid:
                    self.cen_ad.droid.bluetoothStartPairingHelper()
                    self.per_ad.droid.bluetoothStartPairingHelper()
                    self.cen_ad.droid.gattClientCharacteristicSetValue(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid, test_value)
                    self.cen_ad.droid.gattClientWriteCharacteristic(
                        bluetooth_gatt, discovered_services_index, i,
                        characteristic_uuid)
                    start_time = time.time() + self.default_timeout
                    target_name = self.per_ad.droid.bluetoothGetLocalName()
                    while time.time() < start_time and bonded == False:
                        bonded_devices = self.cen_ad.droid.bluetoothGetBondedDevices()
                        for device in bonded_devices:
                            if 'name' in device.keys() and device['name'] == target_name:
                                bonded = True
                                break
        return True
