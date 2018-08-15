#!/usr/bin/env python3
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
"""This script shows simple examples of how to get started with bluetooth
   low energy testing in acts.
"""

import pprint
import random
import time

from acts.controllers import android_device
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_constants import adv_succ
from acts.test_utils.bt.bt_constants import scan_result
from acts.test_utils.bt.bt_test_utils import cleanup_scanners_and_advertisers
from acts.test_utils.bt.bt_test_utils import reset_bluetooth


class BleFuchsiaTest(BluetoothBaseTest):
    default_timeout = 10
    active_scan_callback_list = []
    active_adv_callback_list = []
    droid = None

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)

        if (len(self.fuchsia_devices) < 2):
            self.log.error("BleFuchsiaTest Init: Not enough fuchsia devices.")
        self.log.info("Running testbed setup with two fuchsia devices")
        self.fuchsia_adv = self.fuchsia_devices[0]
        self.fuchsia_scan = self.fuchsia_devices[1]

    def teardown_test(self):
        self.fuchsia_adv.clean_up()
        self.fuchsia_scan.clean_up()

    @BluetoothBaseTest.bt_test_wrap
    def test_fuchsia_publish_service(self):
        service_id = 0
        service_primary = True
        # Random uuid
        service_type = "0000180f-0000-1000-8000-00805fffffff"

        # Generate a random key for sl4f storage of proxy key
        service_proxy_key = "SProxy" + str(random.randint(0, 1000000))
        res = self.fuchsia.ble_lib.blePublishService(
            service_id, service_primary, service_type, service_proxy_key)
        self.log.info("Publish result: {}".format(res))

        return True

    @BluetoothBaseTest.bt_test_wrap
    def test_fuchsia_scan_fuchsia_adv(self):
        # Initialize advertising on fuchsia dveice with name and interval
        fuchsia_name = "testADV1234"
        adv_data = {"name": fuchsia_name}
        interval = 1000

        # Start advertising
        self.fuchsia_adv.ble_lib.bleStartBleAdvertising(adv_data, interval)
        self.log.info("Fuchsia advertising name: {}".format(fuchsia_name))

        # Create the scan filter (based on advertising name) for scan and run scan for 30 seconds
        scan_time = 30000  # in ms
        scan_filter = {"name_substring": fuchsia_name}
        scan_count = 1
        scan_res = self.fuchsia_scan.ble_lib.bleStartBleScan(
            scan_time, scan_filter, scan_count)

        # Get the result and validate
        self.log.info("Scan res: {}".format(scan_res))

        try:
            scan_res = scan_res["result"]
            #Validate result
            res = False
            for device in scan_res:
                name, did, connectable = device["name"], device["id"], device[
                    "connectable"]
                if (name):
                    self.log.info(
                        "Discovered device with name: {}".format(name))
                if (name == fuchsia_name):
                    self.log.info(
                        "Successfully found Fuchsia device advertising! name, id: {}, {}".
                        format(name, did))
                    res = True

        except:
            self.log.error("Failed to discovered fuchsia device")
            res = False

        # Stop advertising
        self.fuchsia_adv.ble_lib.bleStopBleAdvertising()

        return res

    @BluetoothBaseTest.bt_test_wrap
    def test_fuchsia_gatt_fuchsia_periph(self):
        # Create random service with id, primary, and uuid
        service_id = 3
        service_primary = True
        # Random uuid
        service_type = "0000180f-0000-1000-8000-00805fffffff"

        # Generate a random key for sl4f storage of proxy key
        service_proxy_key = "SProxy" + str(random.randint(0, 1000000))
        res = self.fuchsia_adv.ble_lib.blePublishService(
            service_id, service_primary, service_type, service_proxy_key)
        self.log.info("Publish result: {}".format(res))

        # Initialize advertising on fuchsia dveice with name and interval
        fuchsia_name = "testADV1234"
        adv_data = {"name": fuchsia_name}
        interval = 1000

        # Start advertising
        self.fuchsia_adv.ble_lib.bleStartBleAdvertising(adv_data, interval)
        self.log.info("Fuchsia advertising name: {}".format(fuchsia_name))

        # Create the scan filter (based on advertising name) for scan and run scan for 30 seconds
        scan_time = 30000  # in ms
        scan_filter = {"name_substring": fuchsia_name}
        scan_count = 1
        scan_res = self.fuchsia_scan.ble_lib.bleStartBleScan(
            scan_time, scan_filter, scan_count)

        # Get the result and validate
        self.log.info("Scan res: {}".format(scan_res))

        try:
            scan_res = scan_res["result"]
            #Validate result
            res = False
            for device in scan_res:
                name, did, connectable = device["name"], device["id"], device[
                    "connectable"]
                if (name):
                    self.log.info(
                        "Discovered device with name: {}".format(name))
                if (name == fuchsia_name):
                    self.log.info(
                        "Successfully found fuchsia device advertising! name, id: {}, {}".
                        format(name, did))
                    res = True

        except:
            self.log.error("Failed to discovered fuchsia device")
            res = False

        connect = self.fuchsia_scan.ble_lib.bleConnectToPeripheral(did)
        self.log.info("Connecting returned status: {}".format(connect))

        services = self.fuchsia_scan.ble_lib.bleListServices(did)
        self.log.info("Listing services returned: {}".format(services))

        dconnect = self.fuchsia_scan.ble_lib.bleDisconnectPeripheral(did)
        self.log.info("Disconnect status: {}".format(dconnect))

        # Stop fuchsia advertising
        self.fuchsia_adv.ble_lib.bleStopBleAdvertising()

        return res
