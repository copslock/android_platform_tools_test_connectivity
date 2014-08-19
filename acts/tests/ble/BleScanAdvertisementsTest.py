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

"""
Test Scripts to Advertisement feature against scanning
"""

import time
from base_test import BaseTestClass
from test_utils.ble_advertise_utils import *
from test_utils.ble_helper_functions import (build_scansettings, build_scanfilter,
                                           generate_ble_scan_objects,
                                           startblescan,
                                           stopblescan, gen_filterlist,
                                           gen_scancallback)


class BleScanAdvertisementsTest(BaseTestClass):
  TAG = "BleScanAdvertisementsTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  is_testcase_failed = False

  #Helper functions to test advertising feature
  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.droid1, self.ed1 = self.android_devices[1].get_droid()
    self.test = (
      "test_start_stop_advertise_single_instance_with_scan"
      "test_start_stop_advertise_connectable_nonconnectable_with_scan"
      "test_verify_start_stop_advertise_no_include_tx_powe"
      "test_verify_start_stop_advertise_no_include_device_name"
      "test_verify_start_stop_advertise_with_manufacturer_data"
      "test_verify_start_stop_advertise_service_data"
      "test_verify_start_stop_advertise_uuid"
      "test_advertise_multiple_start_of_same_instance_with_scan"
      "test_start_stop_advertise_randomly_with_different_instances"
      "test_start_stop_advertise_four_instances_with_scan"
      "test_start_stop_advertise_more_than_four_instances_with_scan"
      "test_start_stop_advertise_stress_test_with_scan"
      "test_start_stop_advertise_single_instance_with_scan_iteration"
      "test_advertise_multiple_start_of_same_instance_multiple_times_iteration"
      "test_start_stop_advertise_with_different_instances_random_iterate"
      "test_start_stop_advertise_four_instances_with_scan_iteration"
      "test_start_stop_advertise_more_than_four_instances_with_scan_iteration"
      "test_start_stop_advertise_stress_test_with_scan_iteration"
    )

  #Helper functions to test advertising feature
  def configure_advertisement(self, number_of_advertise_instance):
    self.log.info("Get the Device ID")
    advertise_droid = self.droid
    advertise_event_dispatcher = self.ed
    scan_droid = self.droid1
    scan_event_dispatcher = self.ed1
    self.log.info("Configure Advertisement Data")
    choose_advertise_data.get(number_of_advertise_instance, lambda: None)()

    self.log.info("Build Advertisement Data")
    build_advertise_settings_list(advertise_settings, advertise_droid)
    build_advertise_data_list(advertise_data, advertise_droid)
    return advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher

  def validate_scan_no_include_tx_power(self, expected_advertise_data,
                                        scan_result):
    loop_continue = False
    service_data_list = scan_result['data']['Result']['serviceUuidList']
    service_data = extract_string_from_byte_array(service_data_list)
    exp_serv_data = expected_advertise_data[1]

    txPowerLevel = scan_result['data']['Result']['txPowerLevel']
    if (0 != len(service_data) and service_data.lower() ==
      exp_serv_data.lower()):
      loop_continue = True
      if txPowerLevel == 0:
        return True, loop_continue
    return False, loop_continue

  def validate_scan_no_include_device_name(self, expected_advertise_data,
                                           scan_result):
    status = False
    loop_continue = False
    service_data_list = scan_result['data']['Result']['serviceUuidList']
    service_data = extract_string_from_byte_array(service_data_list)
    exp_serv_data = expected_advertise_data[1]
    if 0 != len(service_data) and service_data.lower() == exp_serv_data.lower():
      loop_continue = True
      try:
        name = scan_result['data']['Result']['deviceInfo']['name']
      except Exception:
        status = True
      else:
        if name == '':
          status = True
      try:
        deviceName = scan_result['data']['Result']['deviceName']
      except Exception:
        status = True
      else:
        if deviceName == '':
          status = True
    return status, loop_continue

  def validate_scan_manufacturer_data(self, expected_advertise_data,
                                      scan_result):
    exp_manu_id = expected_advertise_data[1]
    exp_manu_data = expected_advertise_data[2]
    manu_id_list = scan_result['data']['Result']['manufacturereIdList']
    manu_data_list = scan_result['data']['Result'][
      'manufacturerSpecificDataList']
    recv_manu_id_list = convert_string_to_int_array(manu_id_list)
    recv_manu_data = extract_string_from_byte_array(manu_data_list)
    status = False
    loop_continue = False
    if 0 != len(recv_manu_id_list):
      for recv_manu_id in recv_manu_id_list:
        if exp_manu_id == recv_manu_id:
          break
      if exp_manu_data == recv_manu_data:
        loop_continue = True
        status = True

      serviceUuids = scan_result['data']['Result']['serviceUuids']
      if serviceUuids == '':
        status = True
    return status, loop_continue

  def validate_scan_service_data(self, expected_advertise_data, scan_result):
    exp_data_id = expected_advertise_data[1]
    exp_serv_data = expected_advertise_data[2]
    status = False
    loop_continue = False
    serviceDataList = scan_result['data']['Result']['serviceDataList']
    serviceUuidList = scan_result['data']['Result']['serviceUuidList']
    service_data_uuid = extract_string_from_byte_array(serviceUuidList)
    service_data = extract_string_from_byte_array(serviceDataList)
    if 0 != len(
      service_data_uuid) and exp_data_id.lower() == service_data_uuid.lower():
      loop_continue = True
      if 0 != len(service_data) and service_data == exp_serv_data:
        status = True
    return status, loop_continue

  def validate_scan_uuid(self, expected_advertise_data, scan_result):
    exp_uuid_list = expected_advertise_data[1]
    status = False
    loop_continue = False
    service_uuid = scan_result['data']['Result']['serviceUuids']
    length = len(service_uuid)
    if length is not 0:
      service_uuid_list = []
      start = 1
      end = start + 36
      while start < length:
        uuid = service_uuid[start:end]
        service_uuid_list.append(uuid)
        start = end + 1
        end = start + 36
      if len(exp_uuid_list) == len(service_uuid_list):
        status = case_insensitive_compare_uuidlist(exp_uuid_list,
                                                   service_uuid_list)
      del service_uuid_list[0:len(service_uuid_list)]

    if status is True:
      loop_continue = True
      service_data = scan_result['data']['Result']['serviceUuidList']
      service_data_uuid = extract_string_from_byte_array(service_data)
      if 0 == len(service_data_uuid):
        recv_manu_data_list = scan_result['data']['Result'][
          'manufacturerSpecificDataList']
        recv_manu_data = extract_string_from_byte_array(recv_manu_data_list)
        if 0 == len(recv_manu_data):
          status = True
        else:
          status = False
      else:
        status = False
    return status, loop_continue

  def verify_scan_advertise_data_type(self, scan_event_dispatcher,
                                      scan_callback_index,
                                      expected_advertise_data):
    loop = 0
    type = expected_advertise_data[0]
    scan_event_dispatcher.start()
    event_name = "BleScan" + str(scan_callback_index) + "onScanResults"
    loop_continue = False
    status = False
    while loop < 25:
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.info("OnLeScan Event not received")
      else:
        if type == ADVERTISE_DATA_NO_INCLUDE_TX_POWER:
          status, loop_continue = \
            self.validate_scan_no_include_tx_power(expected_advertise_data,
                                                   scan_result)

        elif type == ADVERTISE_DATA_NO_INCLUDE_DEVICE_NAME:
          status, loop_continue = \
            self.validate_scan_no_include_device_name(expected_advertise_data,
                                                      scan_result)

        elif type == ADVERTISE_DATA_ONLY_MANUFACTURER_DATA:
          status, loop_continue = \
            self.validate_scan_manufacturer_data(expected_advertise_data,
                                                 scan_result)

        elif type == ADVERTISE_DATA_ONLY_SERVICE_DATA:
          status, loop_continue = \
            self.validate_scan_service_data(expected_advertise_data,
                                            scan_result)

        elif type == ADVERTISE_DATA_ONLY_UUIDS:
          status, loop_continue = \
            self.validate_scan_uuid(expected_advertise_data, scan_result)

        else:
          self.log.info("Invalid Advertise Type")
      finally:
        if status is True or loop_continue is True:
          break
      loop += 1
    scan_event_dispatcher.stop()
    return status

  def verify_scan_results(self, scan_event_dispatcher, scan_callback_index,
                          is_scan_result_recv):
    #Function to Verify Scan results
    scan_event_dispatcher.start()
    if is_scan_result_recv is False:
      status = self.verify_no_scanresult_received(scan_event_dispatcher,
                                                  scan_callback_index)
    else:
      status = self.verify_scanresult_received(scan_event_dispatcher,
                                               scan_callback_index)
    scan_event_dispatcher.stop()
    return status

  def delay_scan_results(self, scan_event_dispatcher, scan_callback_index):
    scan_event_dispatcher.start()
    loop = 0
    event_name = "BleScan" + str(scan_callback_index) + "onScanResults"
    while loop < 50:
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.info("OnLeScan Event not received")
      else:
        self.log.info("OnLeScan Event received")
      loop += 1
    scan_event_dispatcher.stop()

  def verify_scanresult_received(self, scan_event_dispatcher,
                                 scan_callback_index):
    success_response_list = []
    failure_response_list = []
    advertise_status_list = []
    loop = 0
    uuid_success_count = 0
    uuid_failure_count = 0
    on_success_event_name = "onSuccess"
    total_success_events = 0
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

    event_name = "BleScan" + str(scan_callback_index) + "onScanResults"
    max_loop_count = 100 * len(success_response_list)
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.info("OnLeScan Event not received")
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
              self.log.info("EXPECTED UUID: " + str(expected_uuid))
              if (expected_uuid.lower() ==
                    service_data_uuid.lower() and
                      advertise_status_list[success_index] == False):
                advertise_status_list[success_index] = True
                uuid_success_count += 1
              success_index += 1
          else:
            loop = max_loop_count
          for expected_uuid in failure_response_list:
            if expected_uuid.lower() == service_data_uuid.lower():
              uuid_failure_count += 1
            if uuid_failure_count != 0:
              break
          if uuid_failure_count != 0:
            break
        loop += 1
        if (uuid_failure_count == 0 and uuid_success_count ==
          total_success_events):
          break

    del success_response_list[0:len(success_response_list)]
    del advertise_status_list[0:len(advertise_status_list)]
    del failure_response_list[0:len(failure_response_list)]
    if (uuid_failure_count == 0 and uuid_success_count ==
      total_success_events):
      return True
    else:
      return False

  def verify_scan_with_no_advertise(self, scan_event_dispatcher, event_name):
    loop = 0
    onScanResult_received = False
    status = True
    max_loop_count = 25
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.info("OnLeScan Event not received")
      else:
        service_data_uuidlist = scan_result['data']['Result']['serviceUuidList']
        service_data_uuid = extract_string_from_byte_array(
          service_data_uuidlist)
        onScanResult_received = True
        self.log.info("RECEIVED UUID: " + str(service_data_uuid))
      finally:
        if onScanResult_received is True:
          for expected_uuid in advertise_uuid:
            self.log.info("EXPECTED UUID: " + str(expected_uuid))
            if expected_uuid.lower() == service_data_uuid.lower():
              status = False
              break
          if status == False:
            break
      loop += 1
    return status

  def verify_scan_with_advertise(self, scan_event_dispatcher, event_name):
    loop = 0
    onScanResult_received = False
    status = True
    max_loop_count = 25
    while loop < max_loop_count:
      onScanResult_received = False
      try:
        scan_result = scan_event_dispatcher.pop_event(event_name, 5)
      except Exception:
        self.log.info("OnLeScan Event not received")
      else:
        service_data_uuidlist = scan_result['data']['Result']['serviceUuidList']
        service_data_uuid = extract_string_from_byte_array(
          service_data_uuidlist)
        onScanResult_received = True
        self.log.info("RECEIVED UUID: " + str(service_data_uuid))
      finally:
        if onScanResult_received is True:
          for expexted_result in expected_advertise_result:
            expected_index = expexted_result['Expected Result']['Index']
            expected_uuid = advertise_uuid[expected_index]
            self.log.info("EXPECTED UUID: " + str(expected_uuid))
            if expected_uuid.lower() == service_data_uuid.lower():
              status = False
              break
          if status == False:
            break
      loop += 1
    return status

  def verify_no_scanresult_received(self, scan_event_dispatcher,
                                    scan_callback_index):
    event_name = "BleScan" + str(scan_callback_index) + "onScanResults"
    if 0 == len(expected_advertise_result):
      status = self.verify_scan_with_no_advertise(scan_event_dispatcher,
                                                  event_name)
    else:
      status = self.verify_scan_with_advertise(scan_event_dispatcher,
                                               event_name)
    return status

  def teardown_test(self):
    clean_up_resources(self.droid)
    super().clean_up()

    #Turn ON and Turn OFF BT if a Test Case Fails
    if self.is_testcase_failed is True:
      self.droid.bluetoothToggleState(False)
      self.droid.bluetoothToggleState(True)
      self.droid1.bluetoothToggleState(False)
      self.droid1.bluetoothToggleState(True)
      self.is_testcase_failed = False
      time.sleep(1)

  def teardown_class(self):
    #Turn ON and Turn OFF BT if a Test Case Fails
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    self.droid1.bluetoothToggleState(False)
    self.droid1.bluetoothToggleState(True)
    time.sleep(1)

  #BLE Advertise Functional with Scan Test cases
  def test_start_stop_advertise_single_instance_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_connectable_nonconnectable_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(2)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      test_result = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 2, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_verify_start_stop_advertise_no_include_tx_power(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value)
    dataIdx, callbackIdx = build_advertise_data(advertise_droid, False, True,
                                                -1, -1,
                                                UUID_1, SERVICE_DATA_1, -1)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    advertise_event_dispatcher.start()
    if test_result is True:
      test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                      settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)
    if test_result is True:
      expected_advertise_data = []
      advertise_type = ADVERTISE_DATA_NO_INCLUDE_TX_POWER
      expected_advertise_data.append(advertise_type)
      expected_advertise_data.append(UUID_1)
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)

    if test_result is True:
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)
      del expected_advertise_data[0:len(expected_advertise_data)]

    stopblescan(scan_droid, scan_callback_index)
    stopbleadvertise(advertise_droid, callbackIdx)
    advertise_event_dispatcher.stop()
    if test_result is True:
      self.log.info(
        "Start and Stop Advertisement with no Include TX Power is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start and Stop Advertisement with no Include TX Power is Not OK")
    return test_result

  def test_verify_start_stop_advertise_no_include_device_name(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value)
    dataIdx, callbackIdx = build_advertise_data(advertise_droid, True, False,
                                                -1, -1,
                                                UUID_1, SERVICE_DATA_1, -1)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    advertise_event_dispatcher.start()
    if test_result is True:
      test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                      settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)

    if test_result is True:
      expected_advertise_data = []
      advertise_type = ADVERTISE_DATA_NO_INCLUDE_DEVICE_NAME
      expected_advertise_data.append(advertise_type)
      expected_advertise_data.append(UUID_1)
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)

    if test_result is True:
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)
      del expected_advertise_data[0:len(expected_advertise_data)]

    stopblescan(scan_droid, scan_callback_index)
    stopbleadvertise(advertise_droid, callbackIdx)
    advertise_event_dispatcher.stop()
    if test_result is True:
      self.log.info(
        "Start and Stop Advertisement with no Include Device Name is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start and Stop Advertisement with no Include Device Name is Not OK")
    return test_result

  def test_verify_start_stop_advertise_with_manufacturer_data(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value)
    dataIdx, callbackIdx = build_advertise_data(advertise_droid, False, False,
                                                MANUFACTURER_ID[0],
                                                MANUFACTURER_DATA_1, -1, -1, -1)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    advertise_event_dispatcher.start()
    if test_result is True:
      test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                      settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)

    if test_result is True:
      expected_advertise_data = []
      advertise_type = ADVERTISE_DATA_ONLY_MANUFACTURER_DATA
      expected_advertise_data.append(advertise_type)
      expected_advertise_data.append(MANUFACTURER_ID[0])
      expected_advertise_data.append(MANUFACTURER_DATA_1)
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)

    if test_result is True:
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)
      del expected_advertise_data[0:len(expected_advertise_data)]

    stopblescan(scan_droid, scan_callback_index)
    stopbleadvertise(advertise_droid, callbackIdx)
    advertise_event_dispatcher.stop()
    if test_result is True:
      self.log.info(
        "Start and Stop Advertisement with only Manufacturer Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start and Stop Advertisement with only Manufacturer Data is Not OK")
    return test_result

  def test_verify_start_stop_advertise_service_data(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value)
    dataIdx, callbackIdx = build_advertise_data(advertise_droid, True, True, -1,
                                                -1,
                                                UUID_1, SERVICE_DATA_1, -1)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    advertise_event_dispatcher.start()
    if test_result is True:
      test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                      settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)

    if test_result is True:
      expected_advertise_data = []
      advertise_type = ADVERTISE_DATA_ONLY_SERVICE_DATA
      expected_advertise_data.append(advertise_type)
      expected_advertise_data.append(UUID_1)
      expected_advertise_data.append(SERVICE_DATA_1)
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)

    if test_result is True:
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)
      del expected_advertise_data[0:len(expected_advertise_data)]

    stopblescan(scan_droid, scan_callback_index)
    stopbleadvertise(advertise_droid, callbackIdx)
    advertise_event_dispatcher.stop()
    if test_result is True:
      self.log.info("Start and Stop Advertisement with Service Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start and Stop Advertisement with Service Data is Not OK")
    return test_result

  def test_verify_start_stop_advertise_uuid(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value)
    dataIdx, callbackIdx = build_advertise_data(advertise_droid, True, True, -1,
                                                -1, -1, -1,
                                                UUID_LIST_2)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    advertise_event_dispatcher.start()
    if test_result is True:
      test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                      settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)

    if test_result is True:
      expected_advertise_data = []
      advertise_type = ADVERTISE_DATA_ONLY_UUIDS
      expected_advertise_data.append(advertise_type)
      expected_advertise_data.append(UUID_LIST_2)
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)

    if test_result is True:
      test_result = self.verify_scan_advertise_data_type(scan_event_dispatcher,
                                                         scan_callback_index,
                                                         expected_advertise_data)
      del expected_advertise_data[0:len(expected_advertise_data)]

    stopblescan(scan_droid, scan_callback_index)
    stopbleadvertise(advertise_droid, callbackIdx)
    advertise_event_dispatcher.stop()
    if test_result is True:
      self.log.info("Start and Stop Advertisement with UUID List is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start and Stop Advertisement with UUID List is Not OK")
    return test_result

  def test_advertise_multiple_start_of_same_instance_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      expected_advertise_result.pop()
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onFailure"}})
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      expected_advertise_result.pop()
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_randomly_with_different_instances(self):
    #Random Active Advertisements
    #Step 1:  0           Start Advertising 0
    #Step 2:  0 1         Start Advertising 1
    #Step 3:  0 1 2       Start Advertising 2
    #Step 4:  0 2         Stop  Advertising 1
    #Step 5:  0 2         Start Advertising 2, 2 fails due to already advertising
    #Step 6:  0 2 4       Start Advertising 4
    #Step 7:  0 2 4 1     Start Advertising 1
    #Step 8:  0 2 4       Stop  Advertising 1
    #Step 9:  0 2 4 6     Start Advertising 6
    #Step 10: 0 2 4 6     Start Advertising 3, 3 fails due to max quota
    #Step 11: 0 6         Stop  Advertising 2 and 4
    #Step 12: 0 6 1       Start Advertising 1
    #Step 13: 0 6 1 3     Start Advertising 3
    #Step 14: 0 6 1 3     Start Advertising 9, 9 fails due to max quota
    #Step 15: 1           Stop  Advertising 0 6 3
    #Step 16: 1 9         Start Advertising 9
    #Step 17: 1 9 5 6     Start Advertising 5 6 7, 7 fails due to max quota
    #Step 18: 1 9 5 6     Start Advertising 9, 9 fails due to already advertising
    #Step 19: - - - -     Stop  Advertising 1 9 5 6

    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 5, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 6, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 7, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 8, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 9, \
                                                            "Status": "onFailure"}})

      modify_expected_result(0, "onSuccess")
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(1, "onSuccess")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(2, "onSuccess")
      test_result = start_advertising(2, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      modify_expected_result(1, "onFailure")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(2, "onFailure")
      test_result = start_advertising(2, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(2, "onSuccess")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(4, "onSuccess")
      test_result = start_advertising(4, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, "onSuccess")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      modify_expected_result(1, "onFailure")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(6, "onSuccess")
      test_result = start_advertising(6, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(3, "onFailure")
      test_result = start_advertising(3, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(2, 1, advertise_droid)
      stop_advertising(4, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

      modify_expected_result(2, "onFailure")
      modify_expected_result(4, "onFailure")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(1, "onSuccess")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(3, "onSuccess")
      test_result = start_advertising(3, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, "onFailure")
      test_result = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      stop_advertising(6, 1, advertise_droid)
      stop_advertising(3, 1, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

      modify_expected_result(0, "onFailure")
      modify_expected_result(6, "onFailure")
      modify_expected_result(3, "onFailure")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, "onSuccess")
      test_result = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(5, "onSuccess")
      modify_expected_result(6, "onSuccess")
      modify_expected_result(7, "onFailure")
      test_result = start_advertising(5, 3, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      modify_expected_result(9, "onFailure")
      test_result = start_advertising(9, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(9, "onSuccess")
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 10, advertise_droid)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 10, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_four_instances_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(4)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      test_result = start_advertising(0, 4, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 4, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 4, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result

  def test_start_stop_advertise_more_than_four_instances_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(6)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 5,
                                                            "Status": "onFailure"}})
      test_result = start_advertising(0, 6, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 6, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 6, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result

  def test_start_stop_advertise_stress_test_with_scan(self):
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 5, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 6, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 7, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 8, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 9, \
                                                            "Status": "onFailure"}})
      test_result = start_advertising(0, 10, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, True)

    if test_result is True:
      stop_advertising(0, 10, advertise_droid)
      self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 10, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result

  def test_start_stop_advertise_single_instance_with_scan_iteration(self):
    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      while Index < Iteration:
        test_result = start_advertising(0, 1, advertise_droid,
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

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_advertise_multiple_start_of_same_instance_multiple_times_iteration(
    self):
    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(1)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      while Index < Iteration:
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          expected_advertise_result.pop()
          expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                                "Status": "onFailure"}})
          test_result = start_advertising(0, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          expected_advertise_result.pop()
          expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                                "Status": "onSuccess"}})
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

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_different_instances_random_iterate(self):
    #Random Active Advertisements
    #Step 1:  0           Start Advertising 0
    #Step 2:  0 1         Start Advertising 1
    #Step 3:  0 1 2       Start Advertising 2
    #Step 4:  0 2         Stop  Advertising 1
    #Step 5:  0 2         Start Advertising 2, 2 fails due to already advertising
    #Step 6:  0 2 4       Start Advertising 4
    #Step 7:  0 2 4 1     Start Advertising 1
    #Step 8:  0 2 4       Stop  Advertising 1
    #Step 9:  0 2 4 6     Start Advertising 6
    #Step 10: 0 2 4 6     Start Advertising 3, 3 fails due to max quota
    #Step 11: 0 6         Stop  Advertising 2 and 4
    #Step 12: 0 6 1       Start Advertising 1
    #Step 13: 0 6 1 3     Start Advertising 3
    #Step 14: 0 6 1 3     Start Advertising 9, 9 fails due to max quota
    #Step 15: 1           Stop  Advertising 0 6 3
    #Step 16: 1 9         Start Advertising 9
    #Step 17: 1 9 5 6     Start Advertising 5 6 7, 7 fails due to max quota
    #Step 18: 1 9 5 6     Start Advertising 9, 9 fails due to already advertising
    #Step 19: - - - -     Stop  Advertising 1 9 5 6

    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      while Index < Iteration:
        #Initialize the Expected Result to failure for every Iteration
        expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 5, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 6, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 7, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 8, \
                                                              "Status": "onFailure"}})
        expected_advertise_result.append({"Expected Result": {"Index": 9, \
                                                              "Status": "onFailure"}})

        modify_expected_result(0, "onSuccess")
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(1, "onSuccess")
          test_result = start_advertising(1, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(2, "onSuccess")
          test_result = start_advertising(2, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(1, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          modify_expected_result(1, "onFailure")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(2, "onFailure")
          test_result = start_advertising(2, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          modify_expected_result(2, "onSuccess")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(4, "onSuccess")
          test_result = start_advertising(4, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          modify_expected_result(1, "onSuccess")
          test_result = start_advertising(1, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(1, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)
          modify_expected_result(1, "onFailure")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(6, "onSuccess")
          test_result = start_advertising(6, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(3, "onFailure")
          test_result = start_advertising(3, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(2, 1, advertise_droid)
          stop_advertising(4, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

          modify_expected_result(2, "onFailure")
          modify_expected_result(4, "onFailure")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(1, "onSuccess")
          test_result = start_advertising(1, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          modify_expected_result(3, "onSuccess")
          test_result = start_advertising(3, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(9, "onFailure")
          test_result = start_advertising(9, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 1, advertise_droid)
          stop_advertising(6, 1, advertise_droid)
          stop_advertising(3, 1, advertise_droid)
          self.delay_scan_results(scan_event_dispatcher, scan_callback_index)

          modify_expected_result(0, "onFailure")
          modify_expected_result(6, "onFailure")
          modify_expected_result(3, "onFailure")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(9, "onSuccess")
          test_result = start_advertising(9, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(5, "onSuccess")
          modify_expected_result(6, "onSuccess")
          modify_expected_result(7, "onFailure")
          test_result = start_advertising(5, 3, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          modify_expected_result(9, "onFailure")
          test_result = start_advertising(9, 1, advertise_droid,
                                          advertise_event_dispatcher)

        if test_result is True:
          modify_expected_result(9, "onSuccess")
          test_result = self.verify_scan_results(scan_event_dispatcher,
                                                 scan_callback_index, True)

        if test_result is True:
          stop_advertising(0, 10, advertise_droid)

        if test_result is False:
          break
        Index += 1

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 10, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_four_instances_with_scan_iteration(self):
    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(4)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      while Index < Iteration:
        test_result = start_advertising(0, 4, advertise_droid,
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

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 4, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result

  def test_start_stop_advertise_more_than_four_instances_with_scan_iteration(
    self):
    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(6)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 5, \
                                                            "Status": "onFailure"}})
      while Index < Iteration:
        test_result = start_advertising(0, 6, advertise_droid,
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

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 6, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result

  def test_start_stop_advertise_stress_test_with_scan_iteration(self):
    Iteration = 10
    advertise_droid, scan_droid, advertise_event_dispatcher, scan_event_dispatcher = \
      self.configure_advertisement(10)

    filter_list, scan_settings, scan_callback_index = generate_ble_scan_objects(
      scan_droid)
    test_result = startblescan(scan_droid, filter_list, scan_settings,
                               scan_callback_index)
    if test_result is True:
      test_result = self.verify_scan_results(scan_event_dispatcher,
                                             scan_callback_index, False)

    if test_result is True:
      Index = 0
      expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                            "Status": "onSuccess"}})
      expected_advertise_result.append({"Expected Result": {"Index": 4, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 5, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 6, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 7, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 8, \
                                                            "Status": "onFailure"}})
      expected_advertise_result.append({"Expected Result": {"Index": 9, \
                                                            "Status": "onFailure"}})
      while Index < Iteration:
        test_result = start_advertising(0, 10, advertise_droid,
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

    stopblescan(scan_droid, scan_callback_index)
    stop_advertising(0, 10, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instances is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement and Stop Advertisement for Multiple Instance is Not OK")
    return test_result