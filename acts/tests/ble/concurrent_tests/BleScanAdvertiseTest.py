# !/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- Google, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Test Scripts to test Advertisement feature against scan results
"""

import time
from base_test import BaseTestClass
from test_utils.ble_test_utils import *
from tests.ble.concurrent_tests.BleAdvertiseUtilConfig import *


class BleScanAdvertiseTest(BaseTestClass):
  TAG = "BleScanAdvertiseTest"
  log_path = ''.join((BaseTestClass.log_path, TAG, "/"))
  is_testcase_failed = False
  is_advertiser_start = False

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.ed1.start()

    self.tests = (
      "test_start_stop_advertise_connectable_nonconnectable_with_scan",
      "test_start_advertise_turn_off_on_advertiser",
      "test_start_advertise_turn_off_on_scanner",
      "test_start_advertise_turn_off_on_advertiser_scanner",
      "test_start_advertise_turn_off_on_advertiser_scanner_advertise",
      "test_advertise_multiple_start_of_same_instance_with_scan",
      "test_start_stop_advertise_randomly_with_different_instances",
      "test_start_stop_advertise_four_instances_with_scan",
      "test_start_stop_advertise_more_than_four_instances_with_scan",
      "test_start_stop_advertise_stress_test_with_scan",
      "test_start_stop_advertise_single_instance_with_scan_iteration",
      "test_advertise_multiple_start_of_same_instance_multiple_times_iteration",
      "test_start_stop_advertise_four_instances_with_scan_iteration",
      "test_start_stop_advertise_more_than_four_instances_with_scan_iteration",
      "test_start_stop_advertise_stress_test_with_scan_iteration",
    )


  """Helper functions to test advertising feature with scan results
  """
  def configure_advertisement(self, number_of_advertise_instance):
    """To get the scan device and advertiser device information
       under test and to configure Advertisement data.
    """
    advertiser = device_list['advertiser']
    name = self.droid.bluetoothGetLocalName()
    if name == advertiser:
      advertise_droid = self.droid
      advertise_event_dispatcher = self.ed
      scan_droid = self.droid1
      scan_event_dispatcher = self.ed1
    else:
      advertise_droid = self.droid1
      advertise_event_dispatcher = self.ed1
      self.is_advertiser_start = True
      scan_droid = self.droid
      scan_event_dispatcher = self.ed
    choose_advertise_data.get(number_of_advertise_instance, lambda: None)()
    build_advertise_settings_list(advertise_settings, advertise_droid)
    build_advertise_data_list(advertise_data, advertise_droid)
    return (advertise_droid, scan_droid, advertise_event_dispatcher,
            scan_event_dispatcher)


  def verify_scan_results(self, scan_event_dispatcher, scan_callback_index,
                          is_scan_result_recv):
    """Verify Scan results against the Advertisement Data used for advertising
    """
    if is_scan_result_recv is False:
      status = self.verify_no_scanresult_received(scan_event_dispatcher,
                                                  scan_callback_index)
    else:
      status = self.verify_scanresult_received(scan_event_dispatcher,
                                               scan_callback_index)
    return status


  def delay_scan_results(self, scan_event_dispatcher, scan_callback_index):
    """Time out Function to flush old Scan results
    """
    loop = 0
    event_name = "".join([BLE_FILTERSCAN, str(scan_callback_index),
                          BLE_ONSCANRESULT])
    while loop < 50:
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.debug("delay_scan_results::OnLeScan Event not received")
      else:
        self.log.debug("delay_scan_results::OnLeScan Event received")
      loop += 1


  def verify_scanresult_received(self, scan_event_dispatcher,
                                 scan_callback_index):
    """Verify Scan results against Advertisement Data used for advertising and
       also verify for scan results for not advertised data
    """
    success_response_list = []
    failure_response_list = []
    advertise_status_list = []
    failure_status_list = []
    loop = 0
    uuid_success_count = 0
    uuid_failure_count = 0
    on_success_event_name = BLE_ONSUCCESS
    total_success_events = 0
    total_failure_events = 0
    for expected_result in expected_advertise_result:
      expected_event_name = expected_result['Expected Result']['Status']
      expected_index = expected_result['Expected Result']['Index']
      expected_uuid = advertise_uuid[expected_index]
      if expected_event_name == on_success_event_name:
        success_response_list.append(expected_uuid)
        total_success_events += 1
        advertise_status_list.append(False)
      else:
        failure_response_list.append(expected_uuid)
        total_failure_events += 2
        failure_status_list.append(False)

    event_name = "".join([BLE_FILTERSCAN, str(scan_callback_index),
                          BLE_ONSCANRESULT])
    max_loop_count = 1000 * len(success_response_list)
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.debug("verify_scanresult_received:OnLeScan Event not received")
      else:
        service_data_uuidlist = scan_result['data']['Result']['serviceUuidList']
        service_data_uuid = extract_string_from_byte_array(
          service_data_uuidlist)
        onScanResult_received = True
      finally:
        if onScanResult_received is True:
          if uuid_success_count < total_success_events:
            success_index = 0
            for expected_uuid in success_response_list:
              if (expected_uuid == service_data_uuid and
                  advertise_status_list[success_index] == False):
                advertise_status_list[success_index] = True
                uuid_success_count += 1
              success_index += 1
          else:
            loop = max_loop_count
          failure_index = 0
          for expected_uuid in failure_response_list:
            if expected_uuid == service_data_uuid:
              if failure_status_list[failure_index] == False:
                failure_status_list[failure_index] = True
              else:
                uuid_failure_count += 1
            failure_index += 1
        loop += 1
        if (uuid_success_count == total_success_events or
            uuid_failure_count > total_failure_events):
          break

    del success_response_list[0:len(success_response_list)]
    del advertise_status_list[0:len(advertise_status_list)]
    del failure_response_list[0:len(failure_response_list)]
    self.log.debug(" ".join(["LOOP :", str(loop), ":: FAIL : ",
                             str(uuid_failure_count), ":: TOTAL FAIL :",
                             str(total_failure_events), ":: SUCCESS :",
                             str(uuid_success_count), ":: TOTAL SUCCESS :",
                             str(total_success_events)]))
    if (uuid_failure_count <= total_failure_events and
        uuid_success_count == total_success_events):
      return True
    else:
      return False


  def verify_scan_with_no_advertise(self, scan_event_dispatcher, event_name):
    """Verify Scan results against Advertisement Data which
       are not advertised yet
    """
    loop = 0
    onScanResult_received = False
    status = True
    max_loop_count = 25
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.debug("No Advertise:OnLeScan Event not received")
      else:
        service_data_uuidlist = scan_result['data']['Result']['serviceUuidList']
        service_data_uuid = extract_string_from_byte_array(
          service_data_uuidlist)
        onScanResult_received = True
      finally:
        if onScanResult_received is True:
          for expected_uuid in advertise_uuid:
            if expected_uuid == service_data_uuid:
              status = False
              break
          if status == False:
            break
      loop += 1
    return status


  def verify_scan_with_advertise(self, scan_event_dispatcher, event_name):
    """Verify Scan results against Advertisement Data which
       are advertised but must not receive data in the scan result
    """
    loop = 0
    onScanResult_received = False
    status = False
    max_loop_count = 50
    fail_count = 0
    total_fail_count = 0
    fail_status = []
    for expexted_result in expected_advertise_result:
      fail_status.append(False)
      total_fail_count += 2
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.debug("Advertise:OnLeScan Event not received")
      else:
        service_data_uuidlist = scan_result['data']['Result']['serviceUuidList']
        service_data_uuid = extract_string_from_byte_array(
          service_data_uuidlist)
        onScanResult_received = True
      finally:
        if onScanResult_received is True:
          index = 0
          for expexted_result in expected_advertise_result:
            expected_index = expexted_result['Expected Result']['Index']
            expected_uuid = advertise_uuid[expected_index]
            if expected_uuid == service_data_uuid:
              if fail_status[index] == False:
                fail_status[index] = True
              else:
                fail_count += 1
            index += 1
      loop += 1
    if fail_count < total_fail_count:
      status = True
    return status


  def verify_no_scanresult_received(self, scan_event_dispatcher,
                                    scan_callback_index):
    """Verify Scan results against Advertisement Data which
       are advertised but must not receive data in the scan result
    """
    event_name = "".join([BLE_FILTERSCAN, str(scan_callback_index),
                          BLE_ONSCANRESULT])
    if 0 == len(expected_advertise_result):
      status = self.verify_scan_with_no_advertise(scan_event_dispatcher,
                                                  event_name)
    else:
      status = self.verify_scan_with_advertise(scan_event_dispatcher,
                                               event_name)
    return status


  def teardown_test(self):
    """Clean up the resources after every test case run and
       reset Bluetooth State only if Test case Fails
    """
    if self.is_advertiser_start is True:
      clean_up_resources(self.droid1)
    else:
      clean_up_resources(self.droid)

    if self.is_testcase_failed is True:
      self.droid.bluetoothToggleState(False)
      self.droid1.bluetoothToggleState(False)
      self.droid.bluetoothToggleState(True)
      self.droid1.bluetoothToggleState(True)
      self.is_testcase_failed = False
      verify_bluetooth_on_event(self.ed)
      verify_bluetooth_on_event(self.ed1)


  def teardown_class(self):
    """Reset Bluetooth State after Test Class Run Complete
    """
    self.droid.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(True)
    verify_bluetooth_on_event(self.ed)
    verify_bluetooth_on_event(self.ed1)


  """BLE Advertise Functional Test cases validated with Scan results
  """
  def test_start_stop_advertise_connectable_nonconnectable_with_scan(self):
    """Test that validates Advertisement against the Scan results for both
       connectable and non-connectable advertisement data.
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan Received for connectable and non-connectable advertisement
          which are not started yet.
       3. Start advertising connectable and non-connectable advertisement.
       4. Verify onSuccess callback triggered for both advertisement and
          Scan Results received for both advertisement only after
          start advertising
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(2)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_advertise_turn_off_on_advertiser(self):
    """Test that validates Advertisement during Advertiser's Bluetooth
       Toggle State
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan results not received for advertisement which are
          not started yet.
       3. Start advertising and verify onSuccess callback received.
       4. Reset Advertiser Bluetooth State.
       5. Verify Scan Results not received after Bluetooth Reset.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(2)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      advertise_droid.bluetoothToggleState(False)
      advertise_droid.bluetoothToggleState(True)
      verify_bluetooth_on_event(advertise_event_dispatcher)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_advertise_turn_off_on_scanner(self):
    """Test that validates Advertisement during Scanner's Bluetooth
       Toggle State
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan results not received for advertisement which are
          not started yet.
       3. Start advertising and verify onSuccess callback received.
       4. Reset Scanner Bluetooth State.
       5. Verify Scan Results received after Scanner Bluetooth Reset.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(2)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      scan_droid.bluetoothToggleState(False)
      scan_droid.bluetoothToggleState(True)
      verify_bluetooth_on_event(scan_event_dispatcher)
      (filter_list, scan_settings,
       scan_callback_index) = generate_ble_scan_objects(scan_droid)
      scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_advertise_turn_off_on_advertiser_scanner(self):
    """Test that validates Advertisement during both advertiser and
       Scanner Bluetooth Toggle State
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan results not received for advertisement which are
          not started yet.
       3. Start advertising and verify onSuccess callback received.
       4. Reset both Advertiser and Scanner Bluetooth State.
       5. Verify Scan Results not received after both advertiser and
          Scanner Bluetooth Reset.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(2)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      advertise_droid.bluetoothToggleState(False)
      scan_droid.bluetoothToggleState(False)
      advertise_droid.bluetoothToggleState(True)
      scan_droid.bluetoothToggleState(True)
      verify_bluetooth_on_event(scan_event_dispatcher)
      verify_bluetooth_on_event(advertise_event_dispatcher)
      (filter_list, scan_settings,
       scan_callback_index) = generate_ble_scan_objects(scan_droid)
      scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_advertise_turn_off_on_advertiser_scanner_advertise(self):
    """Test that validates Advertisement during both advertiser and
       Scanner Bluetooth Toggle State and again start advertisement
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan results not received for advertisement which are
          not started yet.
       3. Start advertising and verify onSuccess callback received.
       4. Reset both Advertiser and Scanner Bluetooth State.
       5. Verify Scan Results not received after both advertiser and
          Scanner Bluetooth Reset.
       6. Start advertising and verify onSuccess callback received.
       7. Verify Scan Results received after both advertiser and
          Scanner Bluetooth Reset.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(2)

    (filter_list, scan_settings,
     scan_callback_index) = generate_ble_scan_objects(scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      advertise_droid.bluetoothToggleState(False)
      scan_droid.bluetoothToggleState(False)
      advertise_droid.bluetoothToggleState(True)
      scan_droid.bluetoothToggleState(True)
      verify_bluetooth_on_event(scan_event_dispatcher)
      verify_bluetooth_on_event(advertise_event_dispatcher)
      (filter_list, scan_settings,
       scan_callback_index) = generate_ble_scan_objects(scan_droid)
      scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_advertise_multiple_start_of_same_instance_with_scan(self):
    """Test that valiadtes Scan Results against Start advertising with
       one instance and start advertising again the same instance
       without stopping advertisement.
       Steps:
       1. Start Scan for advertisements.
       2. Verify onScanResults callback not triggered for the advertisement.
       3. Start Advertisement and verify onSuccess Callback triggered.
       4. Verify onScanResults callback is triggered for the advertisement.
       5. Start Advertising again same instnace and verify onFailure callabck
          is triggered with error code.
       6. Verify onScanResults callback is triggered for the advertisement.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(1)

    (filter_list, scan_settings,
     scan_callback_index) = generate_ble_scan_objects(scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      expected_advertise_result.pop()
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONFAILURE}})
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      expected_advertise_result.pop()
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_randomly_with_different_instances(self):
    """Test that valdates random call of Start and Stop Advertising with
       multiple instances against scan results for appropriate advertisements.
       Test Steps:
       1. Start Advertising instance 0 and verify scan result for instance 0
       2. Start Advertising instance 1 and verify scan result for
          instance 0 and 1
       3. Start Advertising instance 2 and verify scan result for
          instance 0, 1 and 2
       4. Stop Advertising instance 1 and verify scan result for
          instance 0 and 2
       5. Start Advertising instance 2 which is already started advertising and
          verify scan result for instance 0 and 2
       6. Start Advertising instance 4 and verify scan result for
          instance 0, 2 and 4
       7. Start Advertising instance 1 and verify scan result for
          instance 0, 1, 2 and 4
       8. Stop Advertising instance 1 and verify scan result for
          instance 0, 2 and 4
       9. Start Advertising instance 6 and verify scan result for
          instance 0, 2, 4 and 6
       10. Start Advertising instance 3 which should fail due to max quota and
           verify scan result for instance 0, 2, 4 and 6
       11. Stop Advertising instances 2 and 4 and verify scan result for
           instance 0 and 6
       12. Start Advertising instance 1 and verify scan result for
           instance 0, 6 and 1
       13. Start Advertising instance 3 and verify scan result for
           instance 0, 6, 1 and 3
       14. Start Advertising instance 9 which should fail due to max quota and
           verify scan result for instance 0, 6, 1 and 3
       15. Stop Advertising instances 0, 6 and 3 and verify scan result for
           instance 1
       16. Start Advertising instance 9 and verify scan result for
           instance 1 and 9
       17. Start Advertising instances 5, 6 and 7, Instance 7 has to fail due
           to max quota and verify scan result for instance 1, 9, 5 and 6
       18. Start Advertising instance 9 which is already started advertising
            and verify scan result for instance 1, 9, 5 and 6
       19. Stop Advertising all instances 1, 9, 5 and 6
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(10)

    (filter_list, scan_settings,
     scan_callback_index) = generate_ble_scan_objects(scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)
    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 4, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 5, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 6, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 7, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 8, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 9, "Status": BLE_ONFAILURE}})

      modify_expected_result(0, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(1, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(2, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(2, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      modify_expected_result(1, BLE_ONFAILURE)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(2, BLE_ONFAILURE)
      test_result, error_value = start_advertising(2, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(2, BLE_ONSUCCESS)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(4, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(4, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      modify_expected_result(1, BLE_ONFAILURE)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(6, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(6, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(3, BLE_ONFAILURE)
      test_result, error_value = start_advertising(3, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(2, 1, advertise_droid)
      stop_advertising(4, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

      modify_expected_result(2, BLE_ONFAILURE)
      modify_expected_result(4, BLE_ONFAILURE)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(1, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(3, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(3, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, BLE_ONFAILURE)
      test_result, error_value = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      stop_advertising(6, 1, advertise_droid)
      stop_advertising(3, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

      modify_expected_result(0, BLE_ONFAILURE)
      modify_expected_result(6, BLE_ONFAILURE)
      modify_expected_result(3, BLE_ONFAILURE)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(5, BLE_ONSUCCESS)
      modify_expected_result(6, BLE_ONSUCCESS)
      modify_expected_result(7, BLE_ONFAILURE)
      test_result, error_value = start_advertising(5, 3, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, BLE_ONFAILURE)
      test_result, error_value = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(9, BLE_ONSUCCESS)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 10, advertise_droid)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 10, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_four_instances_with_scan(self):
    """Test that validates Advertisement for four instances.
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan not received for four advertisements.
       3. Start advertising four instances.
       4. Verify onSuccess callback triggered for all four instances.
       5. Verify onScanResults received for all four instances.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(4)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      test_result, error_value = start_advertising(0, 4, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 4, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 4, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_more_than_four_instances_with_scan(self):
    """Test that validates Advertisement for six instances.
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan not received for six advertisements.
       3. Start advertising six instances.
       4. Verify onSuccess callback triggered for first four instances
          and onFailure for remaining instances.
       5. Verify onScanResults received for all four instances.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(6)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 4, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 5, "Status": BLE_ONFAILURE}})
      test_result, error_value = start_advertising(0, 6, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 6, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 6, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_stress_test_with_scan(self):
    """Test that validates Advertisement for ten instances.
       Steps:
       1. Start Scan for Advertisements.
       2. Verify Scan not received for ten advertisements.
       3. Start advertising ten instances.
       4. Verify onSuccess callback triggered for first four instances
          and onFailure for remaining instances.
       5. Verify onScanResults received for all four instances.
    """
    test_result = True
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 4, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 5, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 6, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 7, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 8, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 9, "Status": BLE_ONFAILURE}})
      test_result, error_value = start_advertising(0, 10, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 10, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 10, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_single_instance_with_scan_iteration(self):
    """Test that validates Advertisement with one instance in Iteration.
       Steps:
       1. Start Scan for Advertisement.
       2. Verify Scan not received for advertisement.
       3. Start advertising and verify onSuccess callback triggered.
       4. Verify onScanResults received for the advertisement.
       5. Repeat the steps till iteration complete.
       6. Verify onScanResults received for all iterations.
    """
    test_result = True
    Iteration = 5
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      while Index < Iteration:
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, False)
        if test_result is False:
          break
        Index += 1

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_advertise_multiple_start_of_same_instance_multiple_times_iteration(
    self):
    """Test that validates Advertisement started again multiple times
       in Iteration.
       Steps:
       1. Start Scan for Advertisement.
       2. Verify Scan not received for advertisement.
       3. Start advertising and verify onSuccess callback triggered.
       4. Verify onScanResults received for the advertisement.
       5. Start advertising and verify onFailure callback triggered.
       6. Verify onScanResults received for the advertisement.
       7. Repeat the steps till iteration complete.
       8. Verify onScanResults received for all iterations.
    """
    test_result = True
    Iteration = 5
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      while Index < Iteration:
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          expected_advertise_result.pop()
          expected_advertise_result.append({"Expected Result":
                                    {"Index": 0, "Status": BLE_ONFAILURE}})
          test_result, error_value = start_advertising(0, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          expected_advertise_result.pop()
          expected_advertise_result.append({"Expected Result":
                                    {"Index": 0, "Status": BLE_ONSUCCESS}})
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, False)
        if test_result is False:
          break
        Index += 1

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_four_instances_with_scan_iteration(self):
    """Test that validates Advertisement for four instances in Iteration.
       Steps:
       1. Start Scan for Advertisement.
       2. Verify Scan not received for advertisement.
       3. Start advertising four instances.
       4. verify onSuccess callback triggered for all four instances.
       5. Verify onScanResults received for all four advertisement.
       6. Repeat the steps till iteration complete.
       7. Verify onScanResults received for all iterations.
    """
    test_result = True
    Iteration = 5
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(4)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      while Index < Iteration:
        test_result, error_value = start_advertising(0, 4, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 4, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, False)
        if test_result is False:
          break
        Index += 1

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 4, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_more_than_four_instances_with_scan_iteration(
    self):
    """Test that validates Advertisement for six instances in Iteration.
       Steps:
       1. Start Scan for Advertisement.
       2. Verify Scan not received for advertisement.
       3. Start advertising six instances.
       4. verify onSuccess callback triggered for all four instances.
       5. verify onFailure callback triggered for remaining instances.
       6. Verify onScanResults received for all four advertisement.
       7. Repeat the steps till iteration complete.
       8. Verify onScanResults received for all iterations.
    """
    test_result = True
    Iteration = 5
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(6)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 4, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 5, "Status": BLE_ONFAILURE}})
      while Index < Iteration:
        test_result, error_value = start_advertising(0, 6, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 6, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, False)
        if test_result is False:
          break
        Index += 1

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 6, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_stress_test_with_scan_iteration(self):
    """Test that validates Advertisement for ten instances in Iteration.
       Steps:
       1. Start Scan for Advertisement.
       2. Verify Scan not received for advertisement.
       3. Start advertising ten instances.
       4. verify onSuccess callback triggered for all four instances.
       5. verify onFailure callback triggered for remaining instances.
       6. Verify onScanResults received for all four advertisement.
       7. Repeat the steps till iteration complete.
       8. Verify onScanResults received for all iterations.
    """
    test_result = True
    Iteration = 5
    (advertise_droid, scan_droid, advertise_event_dispatcher,
     scan_event_dispatcher) = self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    scan_droid.startBleScan(filter_list,scan_settings,scan_callback_index)
    test_result = self.verify_scan_results(scan_event_dispatcher,
                                           scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 2, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 3, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 4, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 5, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 6, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 7, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 8, "Status": BLE_ONFAILURE}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 9, "Status": BLE_ONFAILURE}})
      while Index < Iteration:
        test_result, error_value = start_advertising(0, 10, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 10, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, False)
        if test_result is False:
          break
        Index += 1

    scan_droid.stopBleScan(scan_callback_index)
    stop_advertising(0, 10, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result
