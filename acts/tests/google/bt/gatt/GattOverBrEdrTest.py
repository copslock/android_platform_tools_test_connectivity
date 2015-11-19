# python3.4
# Copyright (C) 2014 The Android Open Source Project
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
Test suite for GATT over BR/EDR.
"""

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.BleEnum import BluetoothGattCharacteristic
from acts.test_utils.bt.BleEnum import BluetoothGattDescriptor
from acts.test_utils.bt.BleEnum import BluetoothGattService
from acts.test_utils.bt.bt_test_utils import descriptor_write
from acts.test_utils.bt.bt_test_utils import descriptor_write_request
from acts.test_utils.bt.bt_test_utils import disconnect_gatt_connection
from acts.test_utils.bt.bt_test_utils import gatt_services_discovered
from acts.test_utils.bt.bt_test_utils import get_advanced_droid_list
from acts.test_utils.bt.bt_test_utils import get_bt_mac_address
from acts.test_utils.bt.bt_test_utils import orchestrate_gatt_connection
from acts.test_utils.bt.bt_test_utils import read_remote_rssi
from acts.test_utils.bt.bt_test_utils import service_added
from acts.test_utils.bt.bt_test_utils import setup_gatt_characteristics
from acts.test_utils.bt.bt_test_utils import setup_gatt_descriptors
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs

class GattOverBrEdrTest(BluetoothBaseTest):
    tests = None
    default_timeout = 10
    default_discovery_timeout = 3
    droid_list = ()
    per_droid_mac_address = None

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.droid_list = get_advanced_droid_list(self.droids, self.eds)
        self.cen_droid, self.cen_ed = self.droids[0], self.eds[0]
        self.per_droid, self.per_ed = self.droids[1], self.eds[1]
        self.tests = (
            "test_gatt_bredr_connect",
            "test_gatt_bredr_connect_trigger_on_read_rssi",
            "test_gatt_bredr_connect_trigger_on_services_discovered",
            "test_gatt_bredr_connect_trigger_on_services_discovered_iterate_attributes",
            "test_gatt_bredr_connect_with_service_uuid_variations",
            "test_gatt_bredr_connect_multiple_iterations",
            "test_bredr_write_descriptor_stress",
        )

    def setup_class(self):
        self.log.info("Setting up devices for bluetooth testing.")
        if not setup_multiple_devices_for_bt_test(self.droids, self.eds):
            return False
        self.per_droid_mac_address = get_bt_mac_address(
            self.cen_droid, self.per_droid, False)
        if not self.per_droid_mac_address:
            return False
        return True

    def on_fail(self, test_name, begin_time):
        take_btsnoop_logs(self.droids, self, test_name)
        reset_bluetooth(self.droids, self.eds)

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
            self.cen_droid, self.cen_ed, bluetooth_gatt,
            gatt_callback)
        if not test_result:
            self.log.info("Failed to disconnect from peripheral device.")
            return False
        return True

    def _iterate_attributes(self, discovered_services_index):
        services_count = self.cen_droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)
        for i in range(services_count):
            service = self.cen_droid.gattClientGetDiscoveredServiceUuid(
                discovered_services_index, i)
            self.log.info("Discovered service uuid {}".format(service))
            characteristic_uuids = (
                self.cen_droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic in characteristic_uuids:
                self.log.info(
                    "Discovered characteristic uuid {}".format(characteristic))
                descriptor_uuids = (
                    self.cen_droid.gattClientGetDiscoveredDescriptorUuids(
                        discovered_services_index, i, characteristic))
                for descriptor in descriptor_uuids:
                    self.log.info(
                        "Discovered descriptor uuid {}".format(descriptor))

    def _find_service_added_event(self, gatt_server_callback, uuid):
        event = self.per_ed.pop_event(
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
            self.per_droid.gattServerCreateGattServerCallback())
        gatt_server = self.per_droid.gattServerOpenGattServer(
            gatt_server_callback)
        characteristic_list, descriptor_list = (
            self._setup_characteristics_and_descriptors(self.per_droid))
        self.per_droid.gattServerCharacteristicAddDescriptor(
            characteristic_list[1], descriptor_list[0])
        self.per_droid.gattServerCharacteristicAddDescriptor(
            characteristic_list[2], descriptor_list[1])
        gatt_service = self.per_droid.gattServerCreateService(
            "00000000-0000-1000-8000-00805f9b34fb",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        gatt_service2 = self.per_droid.gattServerCreateService(
            "FFFFFFFF-0000-1000-8000-00805f9b34fb",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        gatt_service3 = self.per_droid.gattServerCreateService(
            "3846D7A0-69C8-11E4-BA00-0002A5D5C51B",
            BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
        for characteristic in characteristic_list:
            self.per_droid.gattServerAddCharacteristicToService(gatt_service,
                                                                characteristic)
        self.per_droid.gattServerAddService(gatt_server, gatt_service)
        result = self._find_service_added_event(
            gatt_server_callback,
            "00000000-0000-1000-8000-00805f9b34fb")
        if not result:
            return False
        for characteristic in characteristic_list:
            self.per_droid.gattServerAddCharacteristicToService(gatt_service2,
                                                                characteristic)
        self.per_droid.gattServerAddService(gatt_server, gatt_service2)
        result = self._find_service_added_event(
            gatt_server_callback,
            "FFFFFFFF-0000-1000-8000-00805f9b34fb")
        if not result:
            return False
        for characteristic in characteristic_list:
            self.per_droid.gattServerAddCharacteristicToService(gatt_service3,
                                                                characteristic)
        self.per_droid.gattServerAddService(gatt_server, gatt_service3)
        result = self._find_service_added_event(
            gatt_server_callback,
            "3846D7A0-69C8-11E4-BA00-0002A5D5C51B")
        if not result:
            return False, False
        return gatt_server_callback, gatt_server

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect(self):
        """Test GATT connection over BR/EDR.

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

        TAGS: BR/EDR, Filtering, GATT, Scanning
        Priority: 0
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect_trigger_on_read_rssi(self):
        """Test GATT connection over BR/EDR read RSSI.

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

        TAGS: BR/EDR, Scanning, GATT, RSSI
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        if self.cen_droid.gattClientReadRSSI(bluetooth_gatt):
            self.cen_ed.pop_event(
                read_remote_rssi.format(gatt_callback), self.default_timeout)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect_trigger_on_services_discovered(self):
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

        TAGS: BR/EDR, Scanning, GATT, Services
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        discovered_services_index = -1
        if self.cen_droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect_trigger_on_services_discovered_iterate_attributes(self):
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

        TAGS: BR/EDR, Scanning, GATT, Services
        Characteristics, Descriptors
        Priority: 1
        """
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        discovered_services_index = -1
        if self.cen_droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
            self._iterate_attributes(discovered_services_index)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect_with_service_uuid_variations(self):
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

        TAGS: BR/EDR, Scanning, GATT, Services
        Priority: 2
        """
        gatt_server_callback, gatt_server = self._setup_multiple_services()
        if not gatt_server_callback or not gatt_server:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        discovered_services_index = -1
        if self.cen_droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
            self._iterate_attributes(discovered_services_index)
        return self._orchestrate_gatt_disconnection(bluetooth_gatt,
                                                    gatt_callback)

    @BluetoothBaseTest.bt_test_wrap
    def test_gatt_bredr_connect_multiple_iterations(self):
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

        TAGS: BR/EDR, Scanning, GATT, Stress
        Priority: 1
        """
        autoconnect = False
        mac_address = get_bt_mac_address(self.cen_droid, self.per_droid)
        for i in range(20):
            bluetooth_gatt, gatt_callback, adv_callback = (
                orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                            self.per_droid, self.per_ed, False,
                                            self.per_droid_mac_address))
            self.log.info("Disconnecting from peripheral device.")
            test_result = self._orchestrate_gatt_disconnection(
                bluetooth_gatt, gatt_callback)
            if not test_result:
                self.log.info("Failed to disconnect from peripheral device.")
                return False
        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_bredr_write_descriptor_stress(self):
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

        TAGS: BR/EDR, Scanning, GATT, Stress, Characteristics, Descriptors
        Priority: 1
        """
        gatt_server_callback, gatt_server = self._setup_multiple_services()
        if not gatt_server_callback or not gatt_server:
            return False
        bluetooth_gatt, gatt_callback, adv_callback = (
            orchestrate_gatt_connection(self.cen_droid, self.cen_ed,
                                        self.per_droid, self.per_ed, False,
                                        self.per_droid_mac_address))
        if self.cen_droid.gattClientDiscoverServices(bluetooth_gatt):
            event = self.cen_ed.pop_event(
                gatt_services_discovered.format(gatt_callback),
                self.default_timeout)
            discovered_services_index = event['data']['ServicesIndex']
        else:
            self.log.info("Failed to discover services.")
            return False
        services_count = self.cen_droid.gattClientGetDiscoveredServicesCount(
            discovered_services_index)

        connected_device_list = self.per_droid.gattServerGetConnectedDevices(
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
                self.cen_droid.gattClientGetDiscoveredCharacteristicUuids(
                    discovered_services_index, i))
            for characteristic in characteristic_uuids:
                descriptor_uuids = (
                    self.cen_droid.gattClientGetDiscoveredDescriptorUuids(
                        discovered_services_index, i, characteristic))
                for _ in range(100):
                    for descriptor in descriptor_uuids:
                        self.cen_droid.gattClientDescriptorSetValue(
                            bluetooth_gatt, discovered_services_index, i,
                            characteristic, descriptor, test_value)
                        self.cen_droid.gattClientWriteDescriptor(
                            bluetooth_gatt, discovered_services_index, i,
                            characteristic, descriptor)
                        event = self.per_ed.pop_event(
                            descriptor_write_request.format(gatt_callback),
                            self.default_timeout)
                        self.log.info(
                            "onDescriptorWriteRequest event found: {}".format(
                                event))
                        request_id = event['data']['requestId']
                        found_value = event['data']['value']
                        if found_value != test_value:
                            self.log.info("Values didn't match. Found: {}, "
                                          "Expected: {}".format(found_value,
                                                                test_value))
                            return False
                        self.per_droid.gattServerSendResponse(
                            gatt_server, bt_device_id, request_id, status,
                            offset, test_value_return)
                        self.log.info(
                            "onDescriptorWrite event found: {}".format(
                                self.cen_ed.pop_event(
                                descriptor_write.format(bluetooth_gatt),
                                self.default_timeout)))
        return True
