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

from queue import Empty

default_timeout = 10

def generate_ble_scan_objects(droid):
  filter_list = droid.genFilterList()
  droid.buildScanFilter(filter_list)
  scan_settings = droid.buildScanSetting()
  scan_callback = droid.genScanCallback()
  return filter_list, scan_settings, scan_callback


def generate_ble_advertise_objects(droid):
  advertise_data = droid.buildAdvertiseData()
  advertise_settings = droid.buildAdvertisementSettings()
  advertise_callback = droid.genBleAdvertiseCallback()
  return advertise_data, advertise_settings, advertise_callback

def _bluetooth_on_handler(event):
  expected_state = "ON"
  if expected_state != event['data']['State']:
    return False
  else:
    return True

def verify_bluetooth_on_event(ed):
  test_result = True
  expected_bluetooth_on_event_name = "BluetoothOn"
  worker = ed.handle_event(
    _bluetooth_on_handler,
    expected_bluetooth_on_event_name, (), default_timeout)
  try:
    test_result = worker.result(default_timeout)
  except Empty as error:
    test_result = False
  return test_result

def case_insensitive_compare_uuidlist(exp_uuids, recv_uuids):
  """Extract the UUID from Scan Result
  """
  index = 0
  succ_count = 0
  expected_succ_count = 0
  succ_list = []
  for index in range(0,len(exp_uuids)):
    succ_list.append(False)
    expected_succ_count += 1
  for recv_uuid in recv_uuids:
    index = 0
    for index in range(0,len(exp_uuids)):
      exp_uuid = exp_uuids[index]
      if (exp_uuid.lower() == recv_uuid.lower() and
          succ_list[index] == False):
        succ_count += 1
        succ_list[index] = True
  del succ_list[ 0:len(succ_list)]
  if succ_count == expected_succ_count:
    return True
  else:
    return False

def convert_integer_string_to_arraylist(string_list, start, end):
  """Convert string values to integer values and append to array list
  """
  arraylist = []
  innerloop = 0
  while start < end:
    temp = ""
    ch = string_list[start]
    innerloop = start
    while ch != ',':
      temp += ch
      innerloop += 1
      if innerloop >= end:
        break
      ch = string_list[innerloop]
    value = int(temp)
    arraylist.append(value)
    start = innerloop + 1
  return arraylist

def extract_string_from_byte_array(string_list):
  """Extract the string from array of string list
  """
  start = 1
  end = len(string_list) - 1
  extract_string = string_list[start:end]
  return extract_string

def extract_uuidlist_from_record(uuid_string_list):
  """Extract uuid from Service UUID List
  """
  start = 1
  end = len(uuid_string_list) - 1
  uuid_length = 36
  uuidlist = []
  while start < end:
    uuid = uuid_string_list[start:(start + uuid_length)]
    start += uuid_length + 1
    uuidlist.append(uuid)
  return uuidlist

def build_advertise_settings(droid, mode, txpower, type):
  """Build Advertise Settings
  """
  droid.setAdvertisementSettingsAdvertiseMode(mode)
  droid.setAdvertisementSettingsTxPowerLevel(txpower)
  droid.setAdvertisementSettingsIsConnectable(type)
  settings = droid.buildAdvertisementSettings()
  return settings


def build_advertise_data(droid, pwr_incl, name_incl, id, manu_data, serv_uuid,
                         serv_data, uuid):
  """Build Advertise Data
  """
  droid.setAdvertiseDataIncludeTxPowerLevel(pwr_incl)
  droid.setAdvertiseDataIncludeDeviceName(name_incl)
  if (manu_data != -1):
    droid.addAdvertiseDataManufacturerId(id, manu_data);
  if (serv_data != -1):
    droid.addAdvertiseDataServiceData(serv_uuid, serv_data)
  if (uuid != -1):
    droid.setAdvertiseDataSetServiceUuids(uuid)
  data_index = droid.buildAdvertiseData()
  callback_index = droid.genBleAdvertiseCallback()
  return data_index, callback_index
