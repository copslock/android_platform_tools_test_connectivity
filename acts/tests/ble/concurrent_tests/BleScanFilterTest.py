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

"""Test Scripts to test Scan Feature for concurrent advertisements
"""

import time
from base_test import BaseTestClass
from tests.ble.concurrent_tests.BleScanUtilConfig import *


class BleScanFilterTest(BaseTestClass):
  TAG = "BleScanFilterTest"
  log_path = ''.join((BaseTestClass.log_path, TAG, "/"))
  is_testcase_failed = False
  is_data_mask_present = False

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)

    self.droidlist = []
    self.dispatcherlist = []
    self.droidlist.append(self.droid)
    self.dispatcherlist.append(self.ed)
    for index in range(1,len(self.android_devices)):
      droid, dispatcher = self.android_devices[index].get_droid()
      dispatcher.start()
      self.droidlist.append(droid)
      self.dispatcherlist.append(dispatcher)

    self.tests = (
      "test_scanning_with_no_filter_incl_devicename",
      "test_scanning_with_no_filter_no_incl_devicename",
      "test_scanning_namefilter_with_incl_devicename",
      "test_scanning_namefilter_with_no_devicename",
      "test_scanning_namefilter_with_incl_no_incl_devicename",
      "test_scanning_with_manufacturer_data_filter",
      "test_scanning_with_manufacturer_data_mask_filter",
      "test_scanning_with_service_data_filter",
      "test_scanning_with_service_data_mask_filter",
      "test_scanning_with_service_uuid_filter",
      "test_scanning_with_service_uuid_mask_filter",
      "test_scanning_with_all_filters_incl_devicename",
      "test_scanning_with_all_filters_no_incl_devicename",
      "test_scanning_with_all_filters_all_no_incl_devicename",
      "test_scanning_with_name_manudata_filters_both_incl_devicename",
      "test_scanning_with_name_incl_devicename_manudata_no_devicename_filters",
      "test_scanning_with_name_no_devicename_manudata_incl_devicename_filters",
      "test_scanning_with_name_manudata_filters_both_no_devicename",
      "test_scanning_with_name_servicedata_filters",
      "test_scanning_with_name_serviceuuid_filters",
      "test_scanning_with_manudata_servicedata_filters",
      "test_scanning_with_manudata_serviceuuid_filters",
      "test_scanning_with_servicedata_serviceuuid_filters",
      "test_scanning_with_name_manudata_servicedata_filters",
      "test_scanning_start_stop_scan_with_filters",
    )


  """Helper functions to test scan feature
  """
  def extract_filters(self,filter_type,recv_filter):
    """Extract the Filter information from scan result received filter
       based on filter type
    """
    filter = []
    index = 0
    filter.append(filter_type)
    if filter_type == -1:
      filter.append(recv_filter[3])
    elif filter_type == NAME_FILTER:
      filter.append(recv_filter[0])
      filter.append(recv_filter[3])
    elif filter_type == MANUFACTURER_DATA_FILTER:
      filter.append(recv_filter[1])
      filter.append(recv_filter[2])
    elif filter_type == SERVICE_DATA_FILTER:
      filter.append(recv_filter[3])
      filter.append(recv_filter[4])
    elif filter_type == SERVICE_UUID_FILTER:
      filter.append(recv_filter[5])
      if recv_filter[5] != '':
        for index in range(6,(6 + recv_filter[5])):
          filter.append(recv_filter[index])
    recv_filter = filter
    return recv_filter


  def validate_filter(self, filter_type, filter, recv_filter):
    """Validate the scan result received filter with expected filter
    """
    status = False
    temp_filter = list(recv_filter)
    empty_device_name = "NO_DEVICE_NAME"
    if temp_filter[0] == empty_device_name:
      temp_filter[0] = filter[0]

    if filter_type is MULTIPLE_FILTER:
      temp_filter = self.extract_filters(filter[0],temp_filter)

    if temp_filter == filter:
      status = True
    return status


  def received_filter_result(self, filter_type, scan_result):
    """Get the Filter from scan result based on filter type
    """
    status = False
    recv_filter = []
    if filter_type is NAME_FILTER:
      try:
        name = scan_result['data']['Result']['deviceName']
      except Exception:
        name = "NO_DEVICE_NAME"
      recv_filter.append(name)
      serviceUuidList = scan_result['data']['Result']['serviceUuidList']
      recv_filter.append(extract_string_from_byte_array(serviceUuidList))
      status = True

    elif filter_type is MANUFACTURER_DATA_FILTER:
      manu_id_list = scan_result['data']['Result']['manufacturereIdList']
      manu_data_list = scan_result['data']['Result']['manufacturerSpecificDataList']
      recv_manu_id_list = convert_integer_string_to_arraylist(manu_id_list, 1,
                          (len(manu_id_list) - 1))
      if(0 == len(recv_manu_id_list)):
        recv_filter.append(0)
      else:
        recv_filter.append(recv_manu_id_list[0])
      recv_filter.append(extract_string_from_byte_array(manu_data_list))
      status = True

    elif filter_type is SERVICE_DATA_FILTER:
      serviceUuidList = scan_result['data']['Result']['serviceUuidList']
      recv_filter.append(extract_string_from_byte_array(serviceUuidList))
      serviceDataList = scan_result['data']['Result']['serviceDataList']
      recv_filter.append(extract_string_from_byte_array(serviceDataList))
      status = True

    elif filter_type is SERVICE_UUID_FILTER:
      serviceUuidList = scan_result['data']['Result']['serviceUuids']
      if serviceUuidList != '':
        uuidlist = extract_uuidlist_from_record(serviceUuidList)
        recv_filter.append(len(uuidlist))
        for uuid in uuidlist:
          recv_filter.append(uuid)
      else:
        recv_filter.append('')
      status = True

    elif (filter_type is ALL_TYPE_FILTER or
          filter_type is MULTIPLE_FILTER or
          filter_type is NO_FILTER):
      try:
        name = scan_result['data']['Result']['deviceName']
      except Exception:
        name = "NO_DEVICE_NAME"
      recv_filter.append(name)
      manu_id_list = scan_result['data']['Result']['manufacturereIdList']
      manu_data_list = scan_result['data']['Result']['manufacturerSpecificDataList']
      recv_manu_id_list = convert_integer_string_to_arraylist(manu_id_list, 1,
                          (len(manu_id_list) - 1))
      if(0 == len(recv_manu_id_list)):
        recv_filter.append(0)
      else:
        recv_filter.append(recv_manu_id_list[0])
      recv_filter.append(extract_string_from_byte_array(manu_data_list))

      serviceUuidList = scan_result['data']['Result']['serviceUuidList']
      recv_filter.append(extract_string_from_byte_array(serviceUuidList))
      serviceDataList = scan_result['data']['Result']['serviceDataList']
      recv_filter.append(extract_string_from_byte_array(serviceDataList))

      serviceUuidList = scan_result['data']['Result']['serviceUuids']
      if serviceUuidList != '':
        uuidlist = extract_uuidlist_from_record(serviceUuidList)
        recv_filter.append(len(uuidlist))
        for uuid in uuidlist:
          recv_filter.append(uuid)
      else:
        recv_filter.append('')
      status = True
    return status, recv_filter


  def get_wait_time(self, device_list):
    """Get the Maximum time Out to receive scan results for validation
    """
    max_count = 100
    success_count = 0
    if len(device_list) == 0:
      max_count = max_count * len(advertise_device_list)
    else:
      for device in device_list:
        success_list = device[SUCCESSLIST_IDX]
        if len(success_list) == 0:
          success_count += 1

    if success_count == 0:
      max_count = max_count * 10 * len(advertise_device_list)
    else:
      max_count = max_count * len(advertise_device_list)
    return max_count


  def verify_filter(self, expected_event_name, event_dispatcher,
                    device_list, filter_type):
    """Receive Scan Results and Verify the Filter against expected result
    """
    loop = 0
    success_count = 0
    fail_count = 0
    total_count = 0
    other_device_count = 0
    other_device_found = False
    max_loop_count = self.get_wait_time(device_list)
    empty_device_name = "NO_DEVICE_NAME"
    status = False
    while loop < max_loop_count:
      scan_result_received = False
      try:
        scan_result = event_dispatcher.pop_event(expected_event_name,5)
      except Exception:
        self.log.debug(" ".join(["SCAN_RESULT NOT RECEIVED : ", str(loop)]))
        if loop > 25:
          loop += 50
        scan_result_received = False
      else:
        scan_result_received = True
        self.log.debug(" ".join(["SCAN_RESULT RECEIVED : ", str(scan_result)]))
      finally:
        if scan_result_received is True:
          other_device_found = True
          try:
            recv_name = scan_result['data']['Result']['deviceName']
          except Exception:
            recv_name = "NO_DEVICE_NAME"
          status, recv_filter = self.received_filter_result(filter_type,
                                                            scan_result)
          self.log.debug(" ".join(["RECEIVED FILTER : ", str(recv_filter)]))
          if status is True:
            status = False
            device_found = False
            for device in device_list:
              exp_name = device[NAME_IDX]
              if (recv_name == exp_name or recv_name == empty_device_name):
                other_device_found = False
                device_found = True
                success_filter_list = device[SUCCESSLIST_IDX]
                success_filter_status = device[STATUSLIST_IDX]
                failure_filter_list = device[FAILURELIST_IDX]
                success_count = device[SUCCESS_COUNT_IDX]
                break

            if device_found is True:
              index = 0
              for filter in failure_filter_list:
                result = self.validate_filter(filter_type,filter,recv_filter)
                if result is True:
                  fail_count += 1
                  break

              index = 0
              for filter in success_filter_list:
                if False == success_filter_status[index]:
                  result = self.validate_filter(filter_type, filter,
                                                recv_filter)
                  if result is True:
                    success_filter_status[index] = True
                    success_count += 1
                    device[SUCCESS_COUNT_IDX] = success_count
                    break
                index += 1
              if device[SUCCESS_COUNT_IDX] == len(success_filter_list):
                if device[DEVICE_STATUS_IDX] is False:
                  device[DEVICE_STATUS_IDX] = True
                  total_count += 1

      if other_device_found is True:
        other_device_count += 1

      if (total_count == len(device_list) or fail_count > 5):
        loop += 50
      loop += 1

    if (fail_count == 0 and total_count == len(device_list)):
      if filter_type is NO_FILTER:
        if other_device_count != 0:
          status = True
      else:
        if other_device_count is 0:
          status = True
    self.log.debug(" ".join(["SUCCESS :",str(total_count), ", OTHER DEVICE :",
                             str(other_device_count), ", TOTAL :",
                             str(len(device_list))]))
    return status


  def build_expected_filter(self, data, filter_type, filter, filter_value):
    """Build the Expected Filter Result
    """
    advertise_droid = filter[DEVICE_INDEX]
    if filter_type is NAME_FILTER:
      filter_value.append(advertise_droid.bluetoothGetLocalName())
      filter_value.append(data['SERVICE_UUID'])

    elif filter_type is MANUFACTURER_DATA_FILTER:
      filter_value.append(data['ID'])
      filter_value.append(data['MANU_DATA'])

    elif filter_type is SERVICE_DATA_FILTER:
      filter_value.append(data['SERVICE_UUID'])
      filter_value.append(data['SERVICE_DATA'])

    elif filter_type is SERVICE_UUID_FILTER:
      serv_uuid_list = data['UUIDLIST']
      if serv_uuid_list != -1:
        filter_value.append(len(serv_uuid_list))
        for uuid in serv_uuid_list:
          filter_value.append(uuid)
      else:
        filter_value.append('')

    elif filter_type is ALL_TYPE_FILTER:
      filter_value.append(advertise_droid.bluetoothGetLocalName())
      filter_value.append(data['ID'])
      filter_value.append(data['MANU_DATA'])
      filter_value.append(data['SERVICE_UUID'])
      filter_value.append(data['SERVICE_DATA'])
      serv_uuid_list = data['UUIDLIST']
      if serv_uuid_list != -1:
        filter_value.append(len(serv_uuid_list))
        for uuid in serv_uuid_list:
          filter_value.append(uuid)
      else:
        filter_value.append('')

    elif filter_type is NO_FILTER:
      filter_value.append(advertise_droid.bluetoothGetLocalName())
      filter_value.append(data['ID'])
      filter_value.append(data['MANU_DATA'])
      filter_value.append(data['SERVICE_UUID'])
      filter_value.append(data['SERVICE_DATA'])
      serv_uuid_list = data['UUIDLIST']
      if serv_uuid_list != -1:
        filter_value.append(len(serv_uuid_list))
        for uuid in serv_uuid_list:
          filter_value.append(uuid)
      else:
        filter_value.append('')
    else:
      filter_value.append(data['SERVICE_UUID'])
    return filter_value


  def expected_filter(self, filter, filter_type, data_list):
    """Build Expected Success and failure Filter list
    """
    set_filter_list = filter[SET_EACH_FILTER]
    success_filter_list = []
    success_filter_status = []
    temp_filter_list = []
    temp_filter_status = []
    failure_filter_list = []
    add_to_success_list = False
    is_device_empty = False
    name_filter_present = False
    if (filter_type != NAME_FILTER and
        filter_type != NO_FILTER and
        filter_type != MULTIPLE_FILTER and
        filter_type != ALL_TYPE_FILTER and
        filter_type != MANUFACTURER_DATA_FILTER and
        filter_type != SERVICE_DATA_FILTER and
        filter_type != SERVICE_UUID_FILTER):
      is_device_empty = True
    else:
      index = 0
      isFilterSet = filter[FILTER_INDEX]
      filter_type_list = filter[FILTER_TYPE_INDEX]
      for data in data_list:
        add_to_success_list = False
        filter_value = []
        temp_filter = filter_type
        if filter_type is MULTIPLE_FILTER:
          if filter_type_list != -1:
            filter_type = filter_type_list[index]
            filter_value.append(filter_type)
            if data['INCLNAME'] is True:
              add_to_success_list = True

        filter_value = self.build_expected_filter(data,filter_type,filter,
                                                  filter_value)
        if isFilterSet is True:
          set_filter = set_filter_list[index]
          if filter_type is NO_FILTER:
            success_filter_status.append(False)
            success_filter_list.append(filter_value)
          elif filter_type is NAME_FILTER:
            name_filter_present = True
            if data['INCLNAME'] is True:
              success_filter_status.append(False)
              success_filter_list.append(filter_value)
            else:
              failure_filter_list.append(filter_value)
          elif (filter_type is MANUFACTURER_DATA_FILTER or
                filter_type is SERVICE_DATA_FILTER or
                filter_type is SERVICE_UUID_FILTER):
            if set_filter is True:
              success_filter_status.append(False)
              success_filter_list.append(filter_value)
            else:
              failure_filter_list.append(filter_value)
          elif filter_type is ALL_TYPE_FILTER:
            if set_filter is True:
              success_filter_status.append(False)
              success_filter_list.append(filter_value)
            else:
              if data['INCLNAME'] is True:
                success_filter_status.append(False)
                success_filter_list.append(filter_value)
              else:
                failure_filter_list.append(filter_value)
          else:
            if add_to_success_list is True:
              temp_filter_status.append(False)
              temp_filter_list.append(filter_value)
            else:
              failure_filter_list.append(filter_value)
          index += 1
        else:
          if filter_type is NO_FILTER:
            success_filter_status.append(False)
            success_filter_list.append(filter_value)
          else:
            failure_filter_list.append(filter_value)
        filter_type = temp_filter
      if name_filter_present is True:
        success_filter_status += temp_filter_status
        success_filter_list += temp_filter_list
    return (is_device_empty, success_filter_list, success_filter_status,
            failure_filter_list)


  def expected_filter_list(self, filter_type):
    """Build Expected Filter List
    """
    device_list = []
    is_device_empty = True
    for filter in advertise_device_list:
      data_list = filter[DATA_INDEX]
      (is_device_empty, success_filter_list, success_filter_status,
       failure_filter_list) = self.expected_filter(filter, filter_type,
                                                   data_list)

      if is_device_empty is False:
        device = [0,0,0,0,0,0]
        advertise_droid = filter[DEVICE_INDEX]
        device[NAME_IDX] = advertise_droid.bluetoothGetLocalName()
        device[SUCCESSLIST_IDX] = success_filter_list
        device[STATUSLIST_IDX] = success_filter_status
        device[FAILURELIST_IDX] = failure_filter_list
        device[DEVICE_STATUS_IDX] = False
        device[SUCCESS_COUNT_IDX] = 0
        device_list.append(device)
        device = [0,0,0,0,0,0]
    return device_list


  def verify_scan_filter(self, event_dispatcher, filter_type):
    """Verify Scan Filters for all advertisements against expected results
    """
    device_list = self.expected_filter_list(filter_type)
    status_count = 0
    for callback in scancallback_list:
      expected_event_name = "".join([BLE_FILTERSCAN, str(callback),
                                     BLE_ONSCANRESULT])
      status = self.verify_filter(expected_event_name,event_dispatcher,
                                  device_list,filter_type)
      if status is True:
        status_count += 1
    if status_count == len(scancallback_list):
      return True
    else:
      return False


  def build_filter(self, scan_droid, filter, filter_type, data_list):
    """Set and Build Filters to scan for filter based advertisements
    """
    advertise_droid = filter[DEVICE_INDEX]
    filter_list = gen_filterlist(scan_droid)

    if filter_type is NAME_FILTER:
      filter_name = advertise_droid.bluetoothGetLocalName()
      scan_droid.setScanFilterDeviceName(filter_name)
      build_scanfilter(scan_droid, filter_list)
    elif filter_type is MANUFACTURER_DATA_FILTER:
      set_manufacturer_data_filter(scan_droid, self.is_data_mask_present,
                                   filter, data_list, filter_list)
    elif filter_type is SERVICE_DATA_FILTER:
      set_service_data_filter(scan_droid, self.is_data_mask_present, filter,
                              data_list, filter_list)
    elif filter_type is SERVICE_UUID_FILTER:
      set_service_uuid_filter(scan_droid, self.is_data_mask_present, filter,
                              data_list, filter_list)
    elif filter_type is ALL_TYPE_FILTER:
      set_all_filter(scan_droid, self.is_data_mask_present, filter,
                     data_list, filter_list)
    elif filter_type is MULTIPLE_FILTER:
      set_multiple_filter(scan_droid, self.is_data_mask_present, filter,
                          data_list, filter_list)
    else:
      self.log.debug("Build Scan with No Filter")
      build_scanfilter(scan_droid, filter_list)
    return filter_list


  def build_scan_filter(self, scan_droid, filter_type, scan_device):
    """Build Filters for each filter advertisement for all advertisers
    """
    filter_count = 0
    for filter in advertise_device_list:
      isFilterSet = filter[FILTER_INDEX]
      if isFilterSet is True:
        filter_count += 1
        data_list = filter[DATA_INDEX]
        filter_list = self.build_filter(scan_droid,filter,filter_type,
                                        data_list)

        (scan_device_name, callbackType, scanMode, scanResultType,
         reportDelayMillis) = get_scan_device_scansettings(scan_device)

        scan_droid.setScanSettings(callbackType,reportDelayMillis,
                                   scanMode,scanResultType)
        scan_settings = build_scansettings(scan_droid)
        scan_callback = gen_scancallback(scan_droid)
        scancallback_list.append(scan_callback)
        scanfilter_list.append(filter_list)
        scansettings_list.append(scan_settings)
      else:
        self.log.debug("No Filters Set")

    if filter_count is 0:
      return False
    else:
      return True


  def teardown_test(self):
    """Clean up the Scan Data Information and
       reset Bluetooth State only if Test Fails
    """
    clean_up_resources()
    self.is_data_mask_present = False

    #Turn ON and Turn OFF BT if a Test Case Fails
    if self.is_testcase_failed is True:
      for droid in self.droidlist:
        droid.bluetoothToggleState(False)
        time.sleep(1)
        droid.bluetoothToggleState(True)
      self.is_testcase_failed = False
      time.sleep(10)


  def teardown_class(self):
    """Reset Bluetooth State after Test Class Run complete
    """
    for index in range(1,len(self.dispatcherlist)):
      dispatcher = self.dispatcherlist[index]
      dispatcher.stop()

    for droid in self.droidlist:
      droid.bluetoothToggleState(False)
      time.sleep(1)
      droid.bluetoothToggleState(True)
    time.sleep(10)
    del self.dispatcherlist[ 0:len(self.dispatcherlist) ]
    del self.droidlist[ 0:len(self.droidlist) ]


  """BLE Scan Functional Test cases for concurrent advertisements
  """
  def test_scanning_with_no_filter_incl_devicename(self):
    """Test that validates Scan with No filter and set include device name in
       advertisement data to true.
       Steps:
       1. Scan filter not set.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with two instances data include
          device name set to True and other two to false.
       5. Verify onScanResults callback triggered for all four instances.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, NO_FILTER, SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher, NO_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_no_filter_no_incl_devicename(self):
    """Test that validates Scan with No filter and set include
       device name in advertisement data to false.
       Steps:
       1. Scan filter not set.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with two instances data include
          device name set to True and other two to false.
       5. Verify onScanResults callback triggered for all four instances.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,False,True],
      'TYPE'       : -1 } ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, NO_FILTER, SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher, NO_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_namefilter_with_incl_devicename(self):
    """Test that validates Scan with Name filter and set include
       device name in advertisement data set to True.
       Steps:
       1. Set Scan filter to Name Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with all instances data include
          device name set to True.
       5. Verify onScanResults callback triggered for all four instances.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_3,DATA_5,DATA_7],
      'FILTER_LIST': [True,True,True,True],
      'TYPE'       : -1} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, NAME_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher, NAME_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_namefilter_with_no_devicename(self):
    """Test that validates Scan with Name filter and set include
       device name in advertisement data set to False.
       Steps:
       1. Set Scan filter to Name Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with all instances data include
          device name set to False.
       5. Verify onScanResults callback not triggered for all instances.
    """
    test_result = False
    status = True
    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_2,DATA_4,DATA_6,DATA_8],
      'FILTER_LIST': [False,False,False,False],
      'TYPE'       : -1} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, NAME_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      status = self.verify_scan_filter(scan_event_dispatcher, NAME_FILTER)
      if status == True:
        test_result = False

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_namefilter_with_incl_no_incl_devicename(self):
    """Test that validates Scan with Name filter and set include
       device name in advertisement data set to both True and False
       for multiple instances.
       Steps:
       1. Set Scan filter to Name Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with two instances data include
          device name set to True and other two set to false.
       5. Verify onScanResults callback not triggered for
          instances with no device name.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_4,DATA_5],
      'FILTER_LIST': [True,False,False,True],
      'TYPE'       : -1} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, NAME_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher, NAME_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_manufacturer_data_filter(self):
    """Test that validates Scan with Manufacturer data filter.
       Steps:
       1. Set Scan filter to Manufacturer Data Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Manufacturer data set for
          two instances
       5. Verify onScanResults callback triggered only for instances that
          contains manufacturer data filter.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MANUFACTURER_DATA_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MANUFACTURER_DATA_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_manufacturer_data_mask_filter(self):
    """Test that validates Scan with Manufacturer data Mask filter.
       Steps:
       1. Set Scan filter to Manufacturer Data Mask Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Manufacturer mask data
          set for one instance
       5. Verify onScanResults callback triggered only for instances that
          contains manufacturer data mask filter.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)
    FILTER_LIST = [False,False,False,True]
    update_filter_list(FILTER_LIST)

    test_result = start_advertisement()
    if test_result is True:
      self.is_data_mask_present = True
      test_result = self.build_scan_filter(scan_droid, MANUFACTURER_DATA_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MANUFACTURER_DATA_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_service_data_filter(self):
    """Test that validates Scan with Service data filter.
       Steps:
       1. Set Scan filter to Service Data Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Service data
          set for two instances.
       5. Verify onScanResults callback triggered only for instances that
          contains Service data filter.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)
    FILTER_LIST = [False,True,False,True]
    update_filter_list(FILTER_LIST)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, SERVICE_DATA_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            SERVICE_DATA_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_service_data_mask_filter(self):
    """Test that validates Scan with Service data Mask filter.
       Steps:
       1. Set Scan filter to Service Data Mask Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Service data Mask
          set for two instances.
       5. Verify onScanResults callback triggered only for instances that
          contains Service data Mask filter.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)
    FILTER_LIST = [False,False,True,False]
    update_filter_list(FILTER_LIST)

    test_result = start_advertisement()
    if test_result is True:
      self.is_data_mask_present = True
      test_result = self.build_scan_filter(scan_droid, SERVICE_DATA_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            SERVICE_DATA_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_service_uuid_filter(self):
    """Test that validates Scan with Service UUID filter.
       Steps:
       1. Set Scan filter to Service UUID Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Service UUID
          set for two instances.
       5. Verify onScanResults callback triggered only for instances that
          contains Service UUID filter.
    """
    ADV_DATA_1 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[0],
                   "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_7,UUID_1] }

    ADV_DATA_2 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[1],
                   "MANU_DATA" : MANUFACTURER_DATA_2, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_8,UUID_2] }

    ADV_DATA_3 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[2],
                   "MANU_DATA" : MANUFACTURER_DATA_3, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_9,UUID_3]}

    ADV_DATA_4 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[3],
                   "MANU_DATA" : MANUFACTURER_DATA_4, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_10,UUID_4] }

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [ADV_DATA_1,ADV_DATA_2,ADV_DATA_3,ADV_DATA_4],
      'FILTER_LIST': [True,False,True,False],
      'TYPE'       : -1 } ]

    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, SERVICE_UUID_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            SERVICE_UUID_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_service_uuid_mask_filter(self):
    """Test that validates Scan with Service UUID Mask filter.
       Steps:
       1. Set Scan filter to Service UUID Mask Filter.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with Service UUID mask
          set for two instances.
       5. Verify onScanResults callback triggered only for instances that
          contains Service UUID Mask filter.
    """
    ADV_DATA_1 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[0],
                   "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_7,UUID_1] }

    ADV_DATA_2 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[1],
                   "MANU_DATA" : MANUFACTURER_DATA_2, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_8,UUID_2] }

    ADV_DATA_3 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[2],
                   "MANU_DATA" : MANUFACTURER_DATA_3, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_9,UUID_3]}

    ADV_DATA_4 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[3],
                   "MANU_DATA" : MANUFACTURER_DATA_4, "SERVICE_DATA" : -1,
                   "SERVICE_UUID" : -1, "UUIDLIST" : [UUID_10,UUID_4] }

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [ADV_DATA_1,ADV_DATA_2,ADV_DATA_3,ADV_DATA_4],
      'FILTER_LIST': [False,True,False,True],
      'TYPE'       : -1 } ]

    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      self.is_data_mask_present = True
      test_result = self.build_scan_filter(scan_droid, SERVICE_UUID_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            SERVICE_UUID_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_all_filters_incl_devicename(self):
    """Test that validates Scan with All filters.
       Steps:
       1. Set Scan filter to All Filter types.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with all filter type set
          for two instances and include device name set to true for
          two devices.
       5. Verify onScanResults callback triggered only for instances that
          contains All filters and for instances which has device name.
    """
    test_result = False
    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, ALL_TYPE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            ALL_TYPE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_all_filters_no_incl_devicename(self):
    """Test that validates Scan with All filters with set include device
       name to false.
       Steps:
       1. Set Scan filter to All Filter types.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with all filter type set
          for two instances which has no device name.
       5. Verify onScanResults callback triggered for all four instances that
          contains All filters for two instances and device name for
          remaining instances.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [False,True,False,True],
      'TYPE'       : -1 } ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, ALL_TYPE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            ALL_TYPE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_all_filters_all_no_incl_devicename(self):
    """Test that validates Scan with All filters with set include device
       name to false for all instances.
       Steps:
       1. Set Scan filter to All Filter types.
       2. Start Scan for advertisement.
       3. Verify onScanResults callback not triggered.
       4. Start Advertising four instances with all filter type set
          for two instances which has no device name.
       5. Verify onScanResults callback triggered for only two instances that
          contains only device name.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_2,DATA_4,DATA_6,DATA_10],
      'FILTER_LIST': [True,False,True,False],
      'TYPE'       : -1 } ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, ALL_TYPE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            ALL_TYPE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_manudata_filters_both_incl_devicename(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is true and Manufacturer data filter for one
       instance whose include device name is true
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to true.
       2. Set Scan filter to Manufacturer filter for advertisement instance 3
          whose device name set to true.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered only for instances 1 and 3.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,False,True,False],
      'TYPE'       : [NAME_FILTER,-1,MANUFACTURER_DATA_FILTER,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_incl_devicename_manudata_no_devicename_filters(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is true and Manufacturer data filter for one
       instance whose include device name is false.
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to true.
       2. Set Scan filter to Manufacturer filter for advertisement instance 2
          whose device name set to false.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instances 1, 2 and 3,
       7. Verify onScanResults callback triggered for instance 3 since it
          has device name set to true.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,False,False],
      'TYPE'       : [NAME_FILTER,MANUFACTURER_DATA_FILTER,-1,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_no_devicename_manudata_incl_devicename_filters(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is false and Manufacturer data filter for one
       instance whose include device name is True.
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to false.
       2. Set Scan filter to Manufacturer filter for advertisement instance 2
          whose device name set to true.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instances 1, and 3,
       7. Verify onScanResults not received for instance 2 since it has
          no device name.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,False,False],
      'TYPE'       : [MANUFACTURER_DATA_FILTER,NAME_FILTER,-1,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_manudata_filters_both_no_devicename(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is false and Manufacturer data filter for one
       instance whose include device name is false.
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to false.
       2. Set Scan filter to Manufacturer filter for advertisement instance 2
          whose device name set to false.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instances 4.
       7. Verify onScanResults callback triggered for instances 1 and 3
          since it has device name.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [False,True,False,True],
      'TYPE'       : [-1,NAME_FILTER,-1,MANUFACTURER_DATA_FILTER]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_servicedata_filters(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is true and Service data filter for one
       instance whose include device name is false.
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to true.
       2. Set Scan filter to service data filter for advertisement instance 2
          whose device name set to false.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instances 2.
       7. Verify onScanResults callback triggered for instances 1 and 3
          since it has device name.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,False,False],
      'TYPE'       : [NAME_FILTER,SERVICE_DATA_FILTER,-1,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_serviceuuid_filters(self):
    """Test that validates Scan with Name filter for one instance whose
       include device name is true and Service uuid filter for one
       instance whose include device name is false.
       Steps:
       1. Set Scan filter to Name filter for advertisement instance 1
          whose device name set to true.
       2. Set Scan filter to service uuid filter for advertisement instance 2
          whose device name set to false.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instances 2.
       7. Verify onScanResults callback triggered for instances 1 and 3
          since it has device name.
    """
    test_result = False

    ADV_DATA_1 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_1,
                   "SERVICE_UUID" : UUID_7, "UUIDLIST" : [UUID_7,UUID_1] }

    ADV_DATA_2 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_2,
                   "SERVICE_UUID" : UUID_8, "UUIDLIST" : [UUID_8,UUID_2] }

    ADV_DATA_3 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_3,
                   "SERVICE_UUID" : UUID_9, "UUIDLIST" : [UUID_9,UUID_3]}

    ADV_DATA_4 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_4,
                   "SERVICE_UUID" : UUID_10, "UUIDLIST" : [UUID_10,UUID_4] }

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [ADV_DATA_1,ADV_DATA_2,ADV_DATA_3,ADV_DATA_4],
      'FILTER_LIST': [True,True,False,False],
      'TYPE'       : [NAME_FILTER,SERVICE_UUID_FILTER,-1,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_manudata_servicedata_filters(self):
    """Test that validates Scan with Manufacturer data filter and
       Service data filter.
       Steps:
       1. Set Scan filter to Manufacturer data filter for instance 1.
       2. Set Scan filter to service data filter for instance 2.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered only for instances 1 and 2.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,False,False],
      'TYPE'       : [MANUFACTURER_DATA_FILTER,SERVICE_DATA_FILTER,-1,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_manudata_serviceuuid_filters(self):
    """Test that validates Scan with Manufacturer data filter and
       Service uuid filter.
       Steps:
       1. Set Scan filter to Manufacturer data filter for instance 2.
       2. Set Scan filter to service uuid filter for instance 3.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered only for instances 2 and 3.
    """
    test_result = False

    ADV_DATA_1 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[0], "MANU_DATA" : MANUFACTURER_DATA_1,
                   "SERVICE_DATA" : -1,"SERVICE_UUID" : -1,
                   "UUIDLIST" : [UUID_7,UUID_1] }

    ADV_DATA_2 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[1], "MANU_DATA" : MANUFACTURER_DATA_2,
                   "SERVICE_DATA" : -1, "SERVICE_UUID" : -1,
                   "UUIDLIST" : [UUID_8,UUID_2] }

    ADV_DATA_3 = { "PWRINCL" : True, "INCLNAME" : True,
                   "ID" : MANUFACTURER_ID[2], "MANU_DATA" : MANUFACTURER_DATA_3,
                   "SERVICE_DATA" : -1,"SERVICE_UUID" : -1,
                   "UUIDLIST" : [UUID_9,UUID_3]}

    ADV_DATA_4 = { "PWRINCL" : False, "INCLNAME" : False,
                   "ID" : MANUFACTURER_ID[3], "MANU_DATA" : MANUFACTURER_DATA_4,
                   "SERVICE_DATA" : -1, "SERVICE_UUID" : -1,
                   "UUIDLIST" : [UUID_10,UUID_4] }

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [ADV_DATA_1,ADV_DATA_2,ADV_DATA_3,ADV_DATA_4],
      'FILTER_LIST': [False,True,True,False],
      'TYPE'       : [-1,MANUFACTURER_DATA_FILTER,SERVICE_UUID_FILTER,-1]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_servicedata_serviceuuid_filters(self):
    """Test that validates Scan with Service data filter and
       Service uuid filter.
       Steps:
       1. Set Scan filter to Service data filter for instance 3.
       2. Set Scan filter to service uuid filter for instance 4.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered only for instances 3 and 4.
    """
    test_result = False

    ADV_DATA_1 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_1,
                   "SERVICE_UUID" : UUID_7, "UUIDLIST" : [UUID_7,UUID_1] }

    ADV_DATA_2 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_2,
                   "SERVICE_UUID" : UUID_8, "UUIDLIST" : [UUID_8,UUID_2] }

    ADV_DATA_3 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_3,
                   "SERVICE_UUID" : UUID_9, "UUIDLIST" : [UUID_9,UUID_3]}

    ADV_DATA_4 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : -1,
                   "MANU_DATA" : -1, "SERVICE_DATA" : SERVICE_DATA_4,
                   "SERVICE_UUID" : UUID_10, "UUIDLIST" : [UUID_10,UUID_4] }

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [ADV_DATA_1,ADV_DATA_2,ADV_DATA_3,ADV_DATA_4],
      'FILTER_LIST': [False,False,True,True],
      'TYPE'       : [-1,-1,SERVICE_DATA_FILTER,SERVICE_UUID_FILTER]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_with_name_manudata_servicedata_filters(self):
    """Test that validates Scan with Name Filter, Manufacturer data and
       Service data filter.
       Steps:
       1. Set Scan filter to Name filter for instance 1.
       2. Set Scan filter to Manufacturer data filter for instance 2.
       3. Set Scan filter to Service data filter for instance 3.
       4. Start Scan for advertisement.
       5. Verify onScanResults callback not triggered.
       6. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       7. Verify onScanResults callback triggered only for instance 1, 2, and 3.
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [True,True,True,False],
      'TYPE'       : [NAME_FILTER,MANUFACTURER_DATA_FILTER,SERVICE_DATA_FILTER,-1]}]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result


  def test_scanning_start_stop_scan_with_filters(self):
    """Test that validates Start Scan and Stop Scan with Name Filter and
        Manufacturer data filter.
       Steps:
       1. Set Scan filter to Name filter for instance 3.
       2. Set Scan filter to Manufacturer data filter for instance 4.
       3. Start Scan for advertisement.
       4. Verify onScanResults callback not triggered.
       5. Start Advertising four instances with instance 1 and 3 device name
          set to true and instance 2 and 4 device name set to false.
       6. Verify onScanResults callback triggered for instance 3, and 4.
       7. Verify onScanResults callback triggered for instance 1 since
          device name is true.
       8. Stop Scan and verify onScanResult not received.
       9. Again start scan with same callback.
       10. Verify onScanResults callback triggered for instance 3, and 4.
       11. Verify onScanResults callback triggered for instance 1 since
    """
    test_result = False

    ADVERTISERS_2 = [ { 'deviceName' : "device2", 'setFilter' : True,
      'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
      'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
      'FILTER_LIST': [False,False,True,True],
      'TYPE'       : [-1,-1,NAME_FILTER,MANUFACTURER_DATA_FILTER]} ]

    scan_droid, scan_event_dispatcher = get_scan_device(self.droidlist,
                                        self.dispatcherlist, SCAN_DEVICE_1)
    config_advertise_devices(self.droidlist, self.dispatcherlist, ADVERTISERS_2)

    test_result = start_advertisement()
    if test_result is True:
      test_result = self.build_scan_filter(scan_droid, MULTIPLE_FILTER,
                                           SCAN_DEVICE_1)

    if test_result is True:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    if test_result is True:
      stop_ble_scan(scan_droid)
      time.sleep(5)
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    if test_result is False:
      test_result = start_ble_scan(scan_droid)

    if test_result is True:
      test_result = self.verify_scan_filter(scan_event_dispatcher,
                                            MULTIPLE_FILTER)

    stop_ble_scan(scan_droid)
    stop_advertisement()

    if not test_result:
      self.is_testcase_failed = True
    return test_result
