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
from test_utils.BleEnum import *
from test_utils.ble_helper_functions import *


class GattConnectTest(BaseTestClass):
  TAG = "GattConnectTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_gatt_connect"
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

  # Handler Functions End

  def setup_gatt_connection(self, scan_droid, advertise_droid,
                            scan_event_dispatcher, autoconnect):
    advertise_droid.setAdvertisementSettingsAdvertiseMode(
      AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    self.log.debug(
      "Advertising droid: " + get_device_info(advertise_droid))
    self.log.debug(
      "Step 3: Create default scan filter, scan settings, and scan callback")
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"

    advertise_droid.setAdvertiseDataIncludeDeviceName(True)
    advertise_droid.setAdvertiseDataIncludeTxPowerLevel(True)
    advertise_data, advertise_settings, advertise_callback = generate_ble_advertise_objects(
      advertise_droid)
    test_result = startbleadvertise(advertise_droid, advertise_data,
                                    advertise_settings,
                                    advertise_callback)
    if test_result is False:
      self.log.debug(
        "Advertising failed on device: " + get_device_info(
          advertise_droid))
      return
    scan_event_dispatcher.start()
    self.log.debug(
      "Step 4: Start Bluetooth Le Scan on callback ID: " + str(
        scan_callback))
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback)
    self.log.debug(
      "Step 5: Verify the Bluetooth Le Scan did not cause an onScanFailed event.")

    worker = scan_event_dispatcher.handle_event(
      self.blescan_get_mac_address_from_onScanResult,
      expected_event_name, (), None, 10)
    scan_droid.flushPendingScanResults(scan_callback)
    scan_event_dispatcher.stop()
    try:
      mac_address = worker.result()
      self.log.debug("Mac address found: " + mac_address)
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    self.log.debug("Creating Gatt Callback")
    gatt_callback = scan_droid.createGattCallback()
    scan_event_dispatcher.start()
    self.log.debug("Gatt Connect to mac address " + mac_address)
    bluetooth_gatt = scan_droid.connectGatt(gatt_callback, mac_address,
                                            autoconnect)
    print("Made bluetooth gatt connection " + str(bluetooth_gatt))
    expected_event_name = "GattConnect" + str(
      gatt_callback) + "onConnectionStateChange"
    expected_status = GattConnectionState.STATE_CONNECTED.value
    worker = scan_event_dispatcher.handle_event(
      self.gatt_on_connection_state_change,
      expected_event_name, ([expected_status]), None, 10)
    test_result = worker.result()
    scan_event_dispatcher.stop()
    import time

    scan_droid.bluetoothGattDiscoverServices(bluetooth_gatt)
    time.sleep(10)
    scan_droid.bluetoothGattRefresh(bluetooth_gatt)
    time.sleep(10)
    scan_droid.bluetoothGattReadRSSI(bluetooth_gatt)
    time.sleep(10)
    print(scan_droid.bluetoothGattGetServices(bluetooth_gatt))
    # print(scan_droid.bluetoothGattGetConnectedDevices(bluetooth_gatt)) Depricated
    return test_result, gatt_callback

  # TODO: Finish test case!
  def test_gatt_connect(self):
    self.log.debug("Step 1: Setting up environment")
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    self.log.debug("Scanning droid: " + get_device_info(scan_droid))
    advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
    autoconnect = True
    test_result, gatt_callback = self.setup_gatt_connection(scan_droid,
                                                            advertise_droid,
                                                            scan_event_dispatcher,
                                                            autoconnect)
    scan_droid.bluetoothGattDisconnect(gatt_callback)
    return test_result


