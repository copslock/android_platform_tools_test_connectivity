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

import pprint
from queue import Empty

from base_test import BaseTestClass
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import *


class GattConnectTest(BaseTestClass):
  TAG = "GattConnectTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_swag",
      "test_gatt_connect",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    time.sleep(self.default_timeout)
    self.ed1.start()

  # Handler Functions Begin
  def blescan_verify_onfailure_event_handler(self, event):
    self.log.debug("Verifying onFailure event")
    self.log.debug(pprint.pformat(event))
    return event

  def blescan_get_mac_address_from_onScanResult(self, event,
                                                expected_callbacktype=None,
                                                system_time_nanos=None):
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    return event['data']['Result']['deviceInfo']['address']

  def gatt_on_connection_state_change(self, event, expected_state):
    test_result = True
    self.log.debug("Verifying onConnectionStateChange event")
    self.log.debug(pprint.pformat(event))
    if event['data']['State'] != expected_state:
      test_result = False
    return test_result

  def gatt_on_service_added_handler(self, event, expected_service_uuid):
    test_result = True
    self.log.debug("Verifying onServiceAdded event")
    self.log.debug(pprint.pformat(event))
    if event['data']['serviceUuid'] != expected_service_uuid:
      test_result = False
    return test_result

  def bleadvertise_verify_onsuccess_handler(self, event):
    self.log.debug("onSuccess event found for advertisement.")
    self.log.debug(pprint.pformat(event))
    return True

  def gatt_on_read_remote_rssi_handler(self, event):
    self.log.debug("onReadRemoteRssi event found.")
    self.log.debug(pprint.pformat(event))
    return True

  def gatt_on_services_discovered_handler(self, event, expected_status):
    self.log.debug("onServicesDiscovered event found.")
    self.log.debug(pprint.pformat(event))
    if event['data']['Status'] != expected_status:
      return False
    return True

  # Handler Functions End

  def _setupGattCharacteristics(self, droid, input):
    characteristic_list = []
    for item in input:
      index = droid.createBluetoothGattCharacteristic(
        item['uuid'],
        item['property'],
        item['permission'])
      characteristic_list.append(index)
    return characteristic_list

  def _setupGattDescriptors(self, droid, input):
    descriptor_list = []
    for item in input:
      index = droid.createBluetoothGattDescriptor(
        item['uuid'],
        item['property'],
      )
      descriptor_list.append(index)
    return descriptor_list

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
    characteristic_list = self._setupGattCharacteristics(droid,
                                                        characteristic_input)
    descriptor_list = self._setupGattDescriptors(droid,
                                                descriptor_input)
    return characteristic_list,descriptor_list

  def test_swag(self):
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    gattServerCallback = advertise_droid.createGattServerCallback()
    gattServer = advertise_droid.openGattServer(gattServerCallback)
    characteristic_list, descriptor_list = (
      self._setup_characteristics_and_descriptors(advertise_droid))
    advertise_droid.bluetoothGattCharacteristicAddDescriptor(
      characteristic_list[1], descriptor_list[0])
    advertise_droid.bluetoothGattCharacteristicAddDescriptor(
      characteristic_list[2], descriptor_list[1])
    gattService = advertise_droid.createGattService(
      "2649a34c-aa23-44a1-af1c-f560b0084e44",
      BluetoothGattService.SERVICE_TYPE_SECONDARY.value)
    for characteristic in characteristic_list:
      advertise_droid.bluetoothGattAddCharacteristicToService(gattService,
                                                              characteristic)
    advertise_droid.gattServerAddService(gattServer, gattService)
    expected_add_service_event_name = "GattServer" + str(
      gattServerCallback) + "onServiceAdded"
    worker = advertise_event_dispatcher.handle_event(
      self.gatt_on_service_added_handler,
      expected_add_service_event_name, (["2649a34c-aa23-44a1-af1c-f560b0084e44"]))
    test_result = worker.result()
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    advertise_droid.setAdvertisementSettingsIsConnectable(True)
    advertise_droid.setAdvertisementSettingsTxPowerLevel(
      AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value)
    advertise_droid.addAdvertiseDataServiceData(
        "00000000-0000-1000-8000-00805f9b34fb",
        "1,2,3")
    advertise_droid.setAdvertiseDataSetServiceUuids(["00000000-0000-1000-8000-00805f9b34fb"])
    advertise_data, advertise_settings, advertise_callback = (
      generate_ble_advertise_objects(advertise_droid))
    startbleadvertise(advertise_droid, advertise_data,
                                    advertise_settings,
                                    advertise_callback)
    expected_onsuccess_event = ("BleAdvertise" + str(advertise_callback)
                                     + "onSuccess")
    advertise_worker = advertise_event_dispatcher.handle_event(
      self.bleadvertise_verify_onsuccess_handler,
      expected_onsuccess_event, ([]), self.default_timeout)
    test_result = advertise_worker.result(self.default_timeout)
    if test_result is False:
      self.log.debug("Advertising Failed to start.")
      return False
    autoconnect = True
    test_result, bluetooth_gatt, gatt_callback = self._setup_gatt_connection(
      scan_droid,
      advertise_droid,
      scan_event_dispatcher,
      autoconnect)
    scan_droid.bluetoothGattRefresh(bluetooth_gatt)
    test_result = self._trigger_on_services_discovered_callback(
      scan_droid,
      scan_event_dispatcher,
      bluetooth_gatt,
      BluetoothGatt.GATT_SUCCESS.value)
    scan_droid.bluetoothGattRequestConnectionPriority( gatt_callback,
      BluetoothGattConnectionPriority.CONNECTION_PRIORITY_HIGH.value)
    test_result = self._trigger_on_read_rssi_callback(
      scan_droid,
      scan_event_dispatcher,
      bluetooth_gatt)
    scan_droid.bluetoothGattDisconnect(gatt_callback)
    advertise_droid.stopBleAdvertising(advertise_callback)
    return test_result

  def _setup_gatt_connection(self, scan_droid, advertise_droid,
                            scan_event_dispatcher, autoconnect):
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback)
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    worker = scan_event_dispatcher.handle_event(
      self.blescan_get_mac_address_from_onScanResult,
      expected_event_name, (), None)
    try:
      mac_address = worker.result()
      self.log.debug("Mac address found: " + mac_address)
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    self.log.debug("Creating Gatt Callback")
    gatt_callback = scan_droid.createGattCallback()
    self.log.debug("Gatt Connect to mac address " + mac_address)
    bluetooth_gatt = scan_droid.connectGatt(gatt_callback, mac_address,
                                            autoconnect)
    expected_event_name = "GattConnect" + str(
      gatt_callback) + "onConnectionStateChange"
    expected_status = GattConnectionState.STATE_CONNECTED.value
    worker = scan_event_dispatcher.handle_event(
      self.gatt_on_connection_state_change,
      expected_event_name, ([expected_status]), self.default_timeout)
    try:
      self.log.debug(worker.result())
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))

    return test_result, bluetooth_gatt, gatt_callback

  # TODO: Finish test case!
  def test_gatt_connect(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    autoconnect = True
    test_result, gatt_callback = self.setup_gatt_connection(scan_droid,
                                                            advertise_droid,
                                                            scan_event_dispatcher,
                                                            autoconnect)
    scan_droid.bluetoothGattDisconnect(gatt_callback)

    return test_result

  def _trigger_on_services_discovered_callback(self, scan_droid,
                                               scan_event_dispatcher,
                                               bluetooth_gatt,
                                               expected_status):
    test_result = True
    if scan_droid.bluetoothGattDiscoverServices(bluetooth_gatt):
      expected_services_discovered_event_name = ("GattConnect" + str(
      bluetooth_gatt) + "onServicesDiscovered")
      worker = scan_event_dispatcher.handle_event(
        self.gatt_on_services_discovered_handler,
        expected_services_discovered_event_name,
        ([expected_status]),
        self.default_timeout)
      try:
        test_result = worker.result(self.default_timeout)
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with: " + str(error))
    else:
      test_result = False
    return test_result

  def _trigger_on_read_rssi_callback(
    self, scan_droid,
    scan_event_dispatcher,
    bluetooth_gatt):
    test_result = True
    if scan_droid.bluetoothGattReadRSSI(bluetooth_gatt):
      expected_read_rssi_event_name = ("GattConnect" + str(bluetooth_gatt) +
                                    "onReadRemoteRssi")
      worker = scan_event_dispatcher.handle_event(
        self.gatt_on_read_remote_rssi_handler,
        expected_read_rssi_event_name, (), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with: " + str(error))
    else:
      test_result = False
    return test_result