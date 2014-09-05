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
This test script exercises different testcases with a lot of ble beacon traffic.

This test script was designed with this setup in mind:
Shield box one: Android Device
Shield box two: Android Device
Shield box three: 100+ BLE beacons controlled by Raspberry Pis.
Antennas combined from shield box one and two into an attenuator that has a
single antenna into shield box three.
"""

import pprint
import concurrent
import time

from base_test import BaseTestClass
from queue import Empty
from test_utils.bluetooth.BleEnum import *
from test_utils.bluetooth.ble_helper_functions import *


class BeaconSwarmTest(BaseTestClass):
  TAG = "BeaconSwarmTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  default_timeout = 20

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_swarm_no_attenuation",
      "test_swarm_1000_on_scan_result",
    )
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    # TODO: Eventually check for event of bluetooth state toggled to true.
    time.sleep(self.default_timeout)
    self.ed1.start()

  def blescan_verify_onbatchscanresult_event_handler(self, event):
    """
    An event handler that validates the onBatchScanResult
    :param event: dict that represents the callback onBatchScanResult
    :return: test_result: bool
    """
    # Todo: Implement proper validation steps.
    test_result = True
    self.log.debug("Verifying onBatchScanResult event")
    self.log.debug(pprint.pformat(event))
    return test_result

  def blescan_verify_onscanresult_event_handler(self, event):
    """
    An event handler that validates the onScanResult event.
    :param event: dict that represents the callback onScanResult
    :return: test_result: bool
    """
    # Todo: Implement proper validation steps.
    test_result = True
    self.log.debug("Verifying onScanResult event")
    self.log.debug(pprint.pformat(event))
    return test_result

  def test_swarm_no_attenuation(self):
    """
    Test that has no attenuation that exercises the onBatchScanResult.
    Assumes beacons already started and advertising.
    Steps:
    1. Set attenuation to 0
    2. Setup the scanning android device
    3. Verify that at least one onBatchScanResult callback was triggered.
    :return: test_result: bool
    """
    self.attenuators[0].set_atten(0, 0)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    scan_droid.setScanSettings(1, 0, 0, 0)
    filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
      scan_droid)
    expected_event_name = "BleScan" + str(scan_callback) + "onBatchScanResult"
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback)
    worker = scan_event_dispatcher.handle_event(
      self.blescan_verify_onbatchscanresult_event_handler,
      expected_event_name, ([]), self.default_timeout)
    try:
      self.log.debug(worker.result(self.default_timeout))
    except Empty as error:
      test_result = False
      self.log.debug("Test failed with Empty error: " + str(error))
    except concurrent.futures._base.TimeoutError as error:
      test_result = False
      self.log.debug("Test failed with TimeoutError: " + str(error))
    scan_droid.stopBleScan(scan_callback)
    return test_result

  def test_swarm_1000_on_scan_result(self):
    """
    Test that has no attenuation that exercises the onScanResult callback to
    happen 1000 times.
    Assumes beacons already started and advertising.
    Steps:
    1. Set attenuation to 0
    2. Setup the scanning android device
    3. Verify that 1000 onScanResult callbacks were triggered.
    :return: test_result: bool
    """
    test_result = True
    self.attenuators[0].set_atten(0, 0)
    scan_droid, scan_event_dispatcher = self.droid, self.ed
    n = 0
    while n < 1000:
      filter_list, scan_settings, scan_callback = generate_ble_scan_objects(
        scan_droid)
      expected_event_name = "BleScan" + str(scan_callback) + "onScanResults"
      startblescan(scan_droid, filter_list, scan_settings,
                   scan_callback)
      worker = scan_event_dispatcher.handle_event(
        self.blescan_verify_onscanresult_event_handler,
        expected_event_name, ([]), self.default_timeout)
      try:
        self.log.debug(worker.result(self.default_timeout))
      except Empty as error:
        test_result = False
        self.log.debug("Test failed with Empty error: " + str(error))
      except concurrent.futures._base.TimeoutError as error:
        test_result = False
        self.log.debug("Test failed with TimeoutError: " + str(error))
      scan_droid.stopBleScan(scan_callback)
      n += 1
    return test_result
