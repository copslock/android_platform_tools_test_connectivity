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

"""Test Scripts to test Advertisement functionality without scan results
"""

import time
from base_test import BaseTestClass
from tests.ble.concurrent_tests.BleAdvertiseUtilConfig import *


class BleAdvertiseTest(BaseTestClass):
  TAG = "BleAdvertiseTest"
  log_path = ''.join((BaseTestClass.log_path, TAG, "/"))
  is_testcase_failed = False
  is_default_droid_active = False


  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)

    if len(self.android_devices) > 1:
      self.droid1, self.ed1 = self.android_devices[1].get_droid()
      self.ed1.start()

    self.tests = (
      "test_validate_start_advertise_with_data_greater_than_31bytes",
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


  """Helper functions to test advertising feature
  """
  def configure_advertisement(self, number_of_advertise_instance):
    """To get the device information under test and
       to configure Advertisement data.
    """
    if 1 == len(self.android_devices):
      advertise_droid = self.droid
      advertise_event_dispatcher = self.ed
      self.is_default_droid_active = True
    else:
      advertiser = device_list['advertiser']
      name = self.droid.bluetoothGetLocalName()
      if name == advertiser:
        advertise_droid = self.droid
        advertise_event_dispatcher = self.ed
        self.is_default_droid_active = True
      else:
        advertise_droid = self.droid1
        advertise_event_dispatcher = self.ed1
    choose_advertise_data.get(number_of_advertise_instance, lambda: None)()
    build_advertise_settings_list(advertise_settings, advertise_droid)
    build_advertise_data_list(advertise_data, advertise_droid)
    return advertise_droid, advertise_event_dispatcher


  def teardown_test(self):
    """To clean up resources after each test run and
       to reset Bluetooth State only if Test Case Fails.
    """
    if self.is_default_droid_active is True:
      droid = self.droid
    else:
      droid = self.droid1
    clean_up_resources(droid)

    if self.is_testcase_failed is True:
      droid.bluetoothToggleState(False)
      time.sleep(1)
      droid.bluetoothToggleState(True)
      self.is_testcase_failed = False
      time.sleep(10)


  def teardown_class(self):
    """To reset Bluetooth State after Test Class complete.
    """
    if len(self.android_devices) > 1:
      self.ed1.stop()
      self.droid1.bluetoothToggleState(False)
      time.sleep(1)
      self.droid1.bluetoothToggleState(True)
    self.droid.bluetoothToggleState(False)
    time.sleep(1)
    self.droid.bluetoothToggleState(True)
    time.sleep(10)


  """BLE Advertise Functional Test cases
  """
  def test_validate_start_advertise_with_data_greater_than_31bytes(self):
    """Test that validates Start Advertisement for data greater than 31 bytes.
       Steps:
       1. Build Advertisement Data for more than 31 bytes.
       2. Start Advertising with data greater than 31 bytes.
       3. Verify that only onFailure callback is triggered with Error Code
          "Failed since data Greater than 31 bytes".
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(100)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONFAILURE}})

    test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                 advertise_event_dispatcher)
    self.log.info(error_value)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_validate_start_advertise_with_only_uuidlist(self):
    """Test that validates Start Advertisement for data with only UUID List.
       Steps:
       1. Build Advertisement Data for UUID List only.
       2. Start Advertising with the data.
       3. Verify that only onSuccess Callback is triggered.
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(200)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})

    test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                 advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_validate_start_advertise_with_manufacturer_data_uuidlist(self):
    """Test that validates Start Advertisement for data with Manufacturer Data
       and UUID List.
       Steps:
       1. Build Advertisement Data for UUID List and Manufacturer Data.
       2. Start Advertising with the data.
       3. Verify that only onSuccess Callback is triggered.
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(300)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})

    test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                 advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_validate_start_advertise_with_service_data_uuidlist(self):
    """Test that validates Start Advertisement for data with Service Data
       and UUID List.
       Steps:
       1. Build Advertisement Data for UUID List and Service Data.
       2. Start Advertising with the data.
       3. Verify that only onSuccess Callback is triggered.
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(400)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})

    test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                 advertise_event_dispatcher)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_validate_start_advertise_with_manufacturer_data_service_data_uuidlist(self):
    """Test that validates Start Advertisement for data with Manufacturer Data,
       Service Data and UUID List which is greater than 31 bytes.
       Steps:
       1. Build Advertisement Data with Manufacturer Data, Service Data and
          UUID that exceeds 31 bytes.
       2. Start Advertising with data greater than 31 bytes.
       3. Verify that only onFailure callback is triggered with Error Code
          "Failed since data Greater than 31 bytes".
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(500)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONFAILURE}})

    test_result, error_value = start_advertising(0, 1, advertise_droid,
                                    advertise_event_dispatcher)
    self.log.info(error_value)
    stop_advertising(0, 1, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_advertise_multiple_start_of_same_instance(self):
    """Test that validates Start Advertisement when called same instance
       multiple times without stop advertisement.
       Steps:
       1. Start advertising two instances concurrently.
       2. Start advertising again same instances randomly
          without stop advertisement.
       3. Verify onFailure callback is triggered with appropriate Error Code
          "Start Advertisement already started" when start advertising again.
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(2)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 1, "Status": BLE_ONSUCCESS}})

    test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                 advertise_event_dispatcher)
    if test_result is True:
      modify_expected_result(1, BLE_ONFAILURE)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(1, 1, advertise_droid)
      modify_expected_result(1, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(0, BLE_ONFAILURE)
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, BLE_ONFAILURE)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(0, 1, advertise_droid)
      modify_expected_result(0, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(0, BLE_ONFAILURE)
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      modify_expected_result(1, BLE_ONFAILURE)
      test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                   advertise_event_dispatcher)

    if test_result is True:
      stop_advertising(0, 2, advertise_droid)
      modify_expected_result(0, BLE_ONSUCCESS)
      modify_expected_result(1, BLE_ONSUCCESS)
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                   advertise_event_dispatcher)

    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_with_four_instances(self):
    """Test that validates Start Advertisement for four concurrent instances.
       Steps:
       1. Start advertising four instances concurrently.
       2. Verify only onSuccess callback is triggered for all four instances.
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(4)

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
    stop_advertising(0, 4, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_with_five_instances(self):
    """Test that validates Start Advertisement for five concurrent instances.
       Steps:
       1. Start advertising five instances concurrently.
       2. Verify only onSuccess callback is triggered for first four instances.
       3. Verify onFailure callback is triggered for fifth instance with
          error code "Too Many Advertisers"
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(5)

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

    test_result, error_value = start_advertising(0, 5, advertise_droid,
                                                 advertise_event_dispatcher)
    stop_advertising(0, 5, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_with_six_instances(self):
    """Test that validates Start Advertisement for six concurrent instances.
       Steps:
       1. Start advertising six instances concurrently.
       2. Verify only onSuccess callback is triggered for first four instances.
       3. Verify onFailure callback is triggered for fifth and sixth instance
          with error code "Too Many Advertisers"
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(6)

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
    stop_advertising(0, 6, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_stress_with_ten_instances(self):
    """Test that validates Start Advertisement for ten concurrent instances.
       Steps:
       1. Start advertising ten instances concurrently.
       2. Verify only onSuccess callback is triggered for first four instances.
       3. Verify onFailure callback is triggered for rest of the instances
          with error code "Too Many Advertisers" or "Internal Failure".
    """
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(10)

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
    stop_advertising(0, 10, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_single_instance_multiple_time(self):
    """Test that validates Start and Stop Advertisement for one instance
       multiple times.
       Steps:
       1. Start advertising and stop advertising in iteration
       2. Verify only onSuccess callback is triggered for each iteration.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(1)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 1, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_validate_stop_before_start_advertise_multiple_time(self):
    """Test that validates Stop Advertisement before Start Advertisement
       doesnt fail the system.
       Steps:
       1. Stop advertising before start advertisement.
       2. Start advertising.
       3. Repeat the Steps in Iteration.
       4. Verify only onSuccess callback is triggered after
          Start advertisement for each iteration.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(2)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 1, "Status": BLE_ONSUCCESS}})
    Index = 0
    while Index < Iteration:
      stop_advertising(0, 2, advertise_droid)
      test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                   advertise_event_dispatcher)
      if test_result is True:
        test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                     advertise_event_dispatcher)
      if test_result is False:
        break
      Index += 1
    stop_advertising(0, 2, advertise_droid)

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_two_instances_multiple_time(self):
    """Test that validates Start Advertisement for two concurrent instances
       in iteration.
       Steps:
       1. Start advertising two instances concurrently.
       2. Repeat the steps in iteration.
       3. Verify only onSuccess callback is triggered for all instances
          for each Iteration.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(2)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 1, "Status": BLE_ONSUCCESS}})
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 2, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_advertise_multiple_start_of_same_instances_iteration(self):
    """Test that validates Start Advertisement when called again the same
       instances multiple times without stop advertisement in iteration.
       Steps:
       1. Start advertising two instances concurrently.
       2. Start again the same instances without stop advertisement.
       3. Repeat the steps in iteration.
       4. Verify onFailure callback is triggered with error code
          "Advertisement already started" for each Iteration.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(2)

    Index = 0
    while Index < Iteration:
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 0, "Status": BLE_ONSUCCESS}})
      expected_advertise_result.append({"Expected Result":
                                       {"Index": 1, "Status": BLE_ONSUCCESS}})

      test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                   advertise_event_dispatcher)
      if test_result is True:
        modify_expected_result(1, BLE_ONFAILURE)
        test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(1, 1, advertise_droid)
        modify_expected_result(1, BLE_ONSUCCESS)
        test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(0, BLE_ONFAILURE)
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(1, BLE_ONFAILURE)
        test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(0, 1, advertise_droid)
        modify_expected_result(0, BLE_ONSUCCESS)
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(0, BLE_ONFAILURE)
        test_result, error_value = start_advertising(0, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        modify_expected_result(1, BLE_ONFAILURE)
        test_result, error_value = start_advertising(1, 1, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                     advertise_event_dispatcher)

      if test_result is True:
        stop_advertising(0, 2, advertise_droid)
        modify_expected_result(0, BLE_ONSUCCESS)
        modify_expected_result(1, BLE_ONSUCCESS)
        test_result, error_value = start_advertising(0, 2, advertise_droid,
                                                     advertise_event_dispatcher)

      stop_advertising(0, 2, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_three_instances_multiple_time(self):
    """Test that validates Start Advertisement for three concurrent instances.
       Steps:
       1. Start advertising three instances concurrently.
       2. Verify only onSuccess callback is triggered for all three instances.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(3)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 1, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 2, "Status": BLE_ONSUCCESS}})
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 3, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 3, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_four_instances_multiple_time(self):
    """Test that validates Start Advertisement for four concurrent instances.
       Steps:
       1. Start advertising four instances concurrently.
       2. Verify only onSuccess callback is triggered for all four instances.
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(4)

    expected_advertise_result.append({"Expected Result":
                                     {"Index": 0, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 1, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 2, "Status": BLE_ONSUCCESS}})
    expected_advertise_result.append({"Expected Result":
                                     {"Index": 3, "Status": BLE_ONSUCCESS}})
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 4, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 4, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_more_than_four_instances_multiple_time(self):
    """Test that validates Start Advertisement for six concurrent instances.
       Steps:
       1. Start advertising six instances concurrently.
       2. Verify only onSuccess callback is triggered for first four instances.
       3. Verify onFailure callback is triggered for rest of the instances
          with error code "Too Many Advertisers" or "Internal Failure".
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(6)

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
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 6, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 6, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_start_stop_advertise_with_ten_instances_Stress_multiple_time(self):
    """Test that validates Start Advertisement for ten concurrent instances.
       Steps:
       1. Start advertising ten instances concurrently.
       2. Verify only onSuccess callback is triggered for first four instances.
       3. Verify onFailure callback is triggered for rest of the instances
          with error code "Too Many Advertisers" or "Internal Failure".
    """
    Iteration = 5
    (advertise_droid,
     advertise_event_dispatcher) = self.configure_advertisement(10)

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
    Index = 0
    while Index < Iteration:
      test_result, error_value = start_advertising(0, 10, advertise_droid,
                                                   advertise_event_dispatcher)
      stop_advertising(0, 10, advertise_droid)
      if test_result is False:
        break
      Index += 1

    if not test_result:
      self.is_testcase_failed = True
    return test_result
