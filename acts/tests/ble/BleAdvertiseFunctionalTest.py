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
Test Scripts to test Advertisement functionality
"""

import time
from base_test import BaseTestClass
from test_utils.ble_advertise_utils import *


class BleAdvertiseFunctionalTest(BaseTestClass):
  TAG = "BleAdvertiseFunctionalTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  is_testcase_failed = False

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_validate_advertise_data",
      #"test_start_stop_advertise",
      "test_start_stop_advertise_with_single_instance",
      "test_validate_start_advertise_with_data_greater_than_31bytes",
      "test_validate_start_advertise_with_only_uuid",
      "test_validate_start_advertise_with_only_manufacturer_data",
      "test_validate_start_advertise_with_only_service_data",
      "test_validate_start_advertise_with_manufacturer_data_uuid",
      "test_validate_start_advertise_with_service_data_uuid",
      "test_validate_start_advertise_with_manufacturer_data_service_data",
      "test_validate_start_advertise_with_manufacturer_data_service_data_uuid",
      "test_validate_start_advertise_with_only_uuidlist",
      "test_validate_start_advertise_with_manufacturer_data_uuidlist",
      "test_validate_start_advertise_with_service_data_uuidlist",
      "test_validate_start_advertise_with_manufacturer_data_service_data_uuidlist",
      "test_advertise_multiple_start_of_same_instance",
      "test_start_stop_advertise_with_four_instances",
      "test_start_stop_advertise_with_five_instances",
      "test_start_stop_advertise_with_six_instances",
      "test_start_stop_advertise_stress_with_ten_instances",
      "test_start_stop_advertise_single_instance_multiple_time",
      "test_validate_stop_before_start_advertise_multiple_time",
      "test_start_stop_advertise_two_instances_multiple_time",
      "test_advertise_multiple_start_of_same_instances_iteration",
      "test_start_stop_advertise_three_instances_multiple_time",
      "test_start_stop_advertise_four_instances_multiple_time",
      "test_start_stop_advertise_more_than_four_instances_multiple_time",
      "test_start_stop_advertise_with_ten_instances_Stress_multiple_time",
    )

  #Helper functions to test advertising feature
  def configure_advertisement(self, number_of_advertise_instance):
    self.log.info("Get the Device ID")
    advertise_droid = self.droid
    advertise_event_dispatcher = self.ed
    self.log.info("Configure Advertisement Data")
    choose_advertise_data.get(number_of_advertise_instance, lambda: None)()
    self.log.info("Build Advertisement Data")
    build_advertise_settings_list(advertise_settings, advertise_droid)
    build_advertise_data_list(advertise_data, advertise_droid)
    return advertise_droid, advertise_event_dispatcher

  def validate_advertise_settings(self, droid, settings_index, mode, tx_power,
                                  type):
    #Function to Validate Advertise Settings
    status = False
    recv_mode = droid.getAdvertisementSettingsMode(settings_index)
    if (mode == recv_mode):
      recv_tx_power = droid.getAdvertisementSettingsTxPowerLevel(settings_index)
      if (tx_power == recv_tx_power):
        recv_type = droid.getAdvertisementSettingsIsConnectable(settings_index)
        if (type == recv_type):
          status = True
    return status

  def validate_advertise_settings_list(self, droid, expected_settings):
    #Function to Validate Advertise Settings List
    index = 0
    status = False
    for settings in expected_settings:
      mode = settings['mode']
      tx_power = settings['txpwr']
      type = settings['type']
      settings_index = advertise_settings_index[index]
      status = self.validate_advertise_settings(droid, settings_index, mode,
                                                tx_power, type)
      if (status is False):
        break
      index += 1
    return status

  def validate_advertise_data(self, droid, data_index, tx_power_level,
                              incl_device_name,
                              manu_id, exp_manu_data, service_uuid,
                              exp_service_data, exp_uuids):
    #Function to Validate Advertise Data
    status = False
    recv_tx_power = droid.getAdvertiseDataIncludeTxPowerLevel(data_index)
    if (tx_power_level == recv_tx_power):
      status = True

    recv_device_name = droid.getAdvertiseDataIncludeDeviceName(data_index)
    if (incl_device_name == recv_device_name):
      status = True

    recv_manu_data = droid.getAdvertiseDataManufacturerSpecificData(data_index,
                                                                    manu_id)
    if ((exp_manu_data is -1) and (recv_manu_data is '')):
      status = True
    else:
      if recv_manu_data == exp_manu_data:
        status = True

    recv_service_data = droid.getAdvertiseDataServiceData(data_index,
                                                          service_uuid)
    if ((exp_service_data is -1) and (recv_service_data is '')):
      status = True
    else:
      if recv_service_data == exp_service_data:
        status = True

    recv_uuids = droid.getAdvertiseDataServiceUuids(data_index)
    if ((exp_uuids == -1) and (0 == len(recv_uuids))):
      status = True
    else:
      status = case_insensitive_compare_uuidlist(exp_uuids, recv_uuids)
    return status

  def validate_advertise_data_list(self, droid, expected_advertise_data):
    #Function to Validate Advertise Data List
    status = False
    index = 0
    for data in expected_advertise_data:
      pwr_incl = data['PWRINCL']
      name_incl = data['INCLNAME']
      id = data['ID']
      manu_data = data['MANU_DATA']
      serv_data = data['SERVICE_DATA']
      serv_uuid = data['SERVICE_UUID']
      uuid = data['UUIDLIST']
      data_index = advertise_data_index[index]
      status = self.validate_advertise_data(droid, data_index, pwr_incl,
                                            name_incl,
                                            id, manu_data, serv_uuid, serv_data,
                                            uuid)
      if (status == False):
        break
      index += 1
    return status

  #def teardown_test(self):
  #  clean_up_resources(self.droid)
  #  super().clean_up()

    #Turn ON and Turn OFF BT if a Test Case Fails
  #  if self.is_testcase_failed is True:
  #    self.droid.bluetoothToggleState(False)
  #    self.droid.bluetoothToggleState(True)
  #    self.is_testcase_failed = False
  #    time.sleep(1)

  def teardown_class(self):
    #Turn ON and Turn OFF BT if a Test Case Fails
    self.droid.bluetoothToggleState(False)
    self.droid.bluetoothToggleState(True)
    time.sleep(1)

  #BLE Advertise Functional Test cases
  def test_validate_advertise_data(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      10)
    test_result = self.validate_advertise_settings_list(advertise_droid,
                                                        advertise_settings)

    if test_result is True:
      test_result = self.validate_advertise_data_list(advertise_droid,
                                                      advertise_data)

    if test_result is True:
      settingsIdx = build_advertise_settings(advertise_droid,
                                             AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
                                             AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value,
                                             AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value)

      dataIdx, callbackIdx = build_advertise_data(advertise_droid, False, True,
                                                  15,
                                                  MANUFACTURER_DATA_7, UUID_4,
                                                  SERVICE_DATA_5, UUID_LIST_1)

      test_result = self.validate_advertise_settings(advertise_droid,
                                                     settingsIdx,
                                                     AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
                                                     AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value,
                                                     AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value)

    if test_result is True:
      test_result = self.validate_advertise_data(advertise_droid, dataIdx,
                                                 False, True,
                                                 15, MANUFACTURER_DATA_7,
                                                 UUID_4, SERVICE_DATA_5,
                                                 UUID_LIST_1)

    if not test_result:
      self.is_testcase_failed = True
    return test_result

  def test_start_stop_advertise(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      0)

    settingsIdx = build_advertise_settings(advertise_droid,
                                           AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                                           AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                                           AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value)

    dataIdx, callbackIdx = build_advertise_data(advertise_droid, True, True,
                                                MANUFACTURER_ID[0],
                                                MANUFACTURER_DATA_1, UUID_1,
                                                SERVICE_DATA_1, -1)

    expected_advertise_result.append({"Expected Result": {"Index": 0,
                                                          "Status": "onSuccess"}})
    expected_result = expected_advertise_result[0]
    advertise_event_dispatcher.start()
    test_result = startbleadvertise(advertise_droid, callbackIdx, dataIdx,
                                    settingsIdx)

    if test_result is True:
      test_result = verify_advertisement(advertise_event_dispatcher, 0,
                                         callbackIdx,
                                         expected_result)
    advertise_event_dispatcher.stop()
    test_result = stopbleadvertise(advertise_droid, callbackIdx)
    if test_result is True:
      self.log.info("Set and Get Advertisement Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Set and Get Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_single_instance(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      1)

    expected_advertise_result.append({"Expected Result": {"Index": 0,
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_validate_start_advertise_with_data_greater_than_31bytes(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      100)

    expected_advertise_result.append({"Expected Result": {"Index": 0,
                                                          "Status": "onFailure"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Validate Start Advertisement with Data Greater than 31 bytes is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Validate Start Advertisement with Data Greater than 31 bytes is Not OK")
    return test_result

  def test_validate_start_advertise_with_only_uuid(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      101)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement with Only UUID is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement with Only UUID is Not OK")
    return test_result

  def test_validate_start_advertise_with_only_manufacturer_data(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      102)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement with Only Manufacturer Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement with Only Manufacturer Data is Not OK")
    return test_result

  def test_validate_start_advertise_with_only_service_data(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      103)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement with Only Service Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement with Only Service Data is Not OK")
    return test_result

  def test_validate_start_advertise_with_manufacturer_data_uuid(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      104)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Only Manufacturer Data and UUID is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Only Manufacturer Data and UUID is Not OK")
    return test_result

  def test_validate_start_advertise_with_service_data_uuid(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      105)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement with Only Service Data and UUID is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Only Service Data and UUID is Not OK")
    return test_result

  def test_validate_start_advertise_with_manufacturer_data_service_data(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      106)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Only Service Data and Manufacturer Data is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Only Service Data and Manufacturer Data is Not OK")
    return test_result

  def test_validate_start_advertise_with_manufacturer_data_service_data_uuid(
    self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      107)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onFailure"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Manufacturer Data, Service Data and UUIDLIST is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Manufacturer Data, Service Data and UUIDLIST is Not OK")
    return test_result

  def test_validate_start_advertise_with_only_uuidlist(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      108)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement with Only UUIDLIST is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement with Only UUIDLIST is Not OK")
    return test_result

  def test_validate_start_advertise_with_manufacturer_data_uuidlist(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      109)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Only Manufacturer Data and UUIDLIST is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Only Manufacturer Data and UUIDLIST is Not OK")
    return test_result

  def test_validate_start_advertise_with_service_data_uuidlist(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      110)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Only Service Data and UUIDLIST is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Only Service Data and UUIDLIST is Not OK")
    return test_result

  def test_validate_start_advertise_with_manufacturer_data_service_data_uuidlist(
    self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      111)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onFailure"}})

    test_result = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)
    if test_result is True:
      self.log.info(
        "Start Advertisement with Manufacturer Data, Service Data and UUIDLIST is OK")
    else:
      self.is_testcase_failed = True
      self.log.info(
        "Start Advertisement with Manufacturer Data, Service Data and UUIDLIST is Not OK")
    return test_result

  def test_advertise_multiple_start_of_same_instance(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      2)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})

    test_result = start_advertising(0, 2, advertise_droid,
                                    advertise_event_dispatcher)
    if test_result is True:
      modify_expected_result(1, "onFailure")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      modify_expected_result(1, "onSuccess")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(0, "onFailure")
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, "onFailure")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      modify_expected_result(0, "onSuccess")
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(0, "onFailure")
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, "onFailure")
      test_result = start_advertising(1, 1, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      test_result = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      modify_expected_result(0, "onSuccess")
      modify_expected_result(1, "onSuccess")
      test_result = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)

    stop_advertising(0, 2, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_four_instances(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      4)

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
    stop_advertising(0, 4, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_five_instances(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      5)

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

    test_result = start_advertising(0, 5, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 5, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_six_instances(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      6)

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

    test_result = start_advertising(0, 6, advertise_droid,
                                    advertise_event_dispatcher)
    stop_advertising(0, 6, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_stress_with_ten_instances(self):
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      10)

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
    stop_advertising(0, 10, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_single_instance_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      1)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 1, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_validate_stop_before_start_advertise_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      2)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})
    Index = 0
    while (Index < Iteration):
      stop_advertising(0, 2, advertise_droid)
      test_result = start_advertising(0, 1, advertise_droid,
                                      advertise_event_dispatcher)
      if test_result is True:
        test_result = start_advertising(1, 1, advertise_droid,
                                        advertise_event_dispatcher)
      if test_result is False:
        break
      Index += 1
    stop_advertising(0, 2, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_two_instances_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      2)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 2, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_advertise_multiple_start_of_same_instances_iteration(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      2)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})

    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 2, advertise_droid,
                                      advertise_event_dispatcher)
      if test_result is True:
        modify_expected_result(1, "onFailure")
        test_result = start_advertising(1, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(1, 1, advertise_droid)
        modify_expected_result(1, "onSuccess")
        test_result = start_advertising(1, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(0, "onFailure")
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(1, "onFailure")
        test_result = start_advertising(1, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(0, 1, advertise_droid)
        modify_expected_result(0, "onSuccess")
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(0, "onFailure")
        test_result = start_advertising(0, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(1, "onFailure")
        test_result = start_advertising(1, 1, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        test_result = start_advertising(0, 2, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(0, 2, advertise_droid)
        modify_expected_result(0, "onSuccess")
        modify_expected_result(1, "onSuccess")
        test_result = start_advertising(0, 2, advertise_droid,
                                        advertise_event_dispatcher)

      if test_result is False:
        break
      Index += 1
    stop_advertising(0, 2, advertise_droid)
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_three_instances_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      3)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                          "Status": "onSuccess"}})
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 3, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 3, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_four_instances_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      4)

    expected_advertise_result.append({"Expected Result": {"Index": 0, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 1, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 2, \
                                                          "Status": "onSuccess"}})
    expected_advertise_result.append({"Expected Result": {"Index": 3, \
                                                          "Status": "onSuccess"}})
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 4, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 4, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_more_than_four_instances_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      6)

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
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 6, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 6, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result

  def test_start_stop_advertise_with_ten_instances_Stress_multiple_time(self):
    Iteration = 10
    advertise_droid, advertise_event_dispatcher = self.configure_advertisement(
      10)

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
    Index = 0
    while (Index < Iteration):
      test_result = start_advertising(0, 10, advertise_droid,
                                      advertise_event_dispatcher)
      stop_advertising(0, 10, advertise_droid)
      if test_result is False:
        break
      Index += 1
    if test_result is True:
      self.log.info("Start Advertisement and Stop Advertisement is OK")
    else:
      self.is_testcase_failed = True
      self.log.info("Start Advertisement and Stop Advertisement is Not OK")
    return test_result
