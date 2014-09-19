# !/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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

"""Helper functions for Advertisement Feature
"""

from test_utils.ble_test_utils import *
from .BleConfig import *


"""Configure the Advertiser and Scanner for the Test Bed
"""
device_list = {'advertiser' : "device1", 'scanner' : "device2"}


"""Switch Statement Functions to configure Advertisement Data and Settings
"""
def build_tenth_advertise_data():
  advertise_settings.append(SETTINGS_10)
  advertise_data.append(DATA_10)
  uuid = DATA_10['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_ninth_advertise_data()

def build_ninth_advertise_data():
  advertise_settings.append(SETTINGS_9)
  advertise_data.append(DATA_9)
  uuid = DATA_9['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_eighth_advertise_data()

def build_eighth_advertise_data():
  advertise_settings.append(SETTINGS_8)
  advertise_data.append(DATA_8)
  uuid = DATA_8['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_seventh_advertise_data()

def build_seventh_advertise_data():
  advertise_settings.append(SETTINGS_7)
  advertise_data.append(DATA_7)
  uuid = DATA_7['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_sixth_advertise_data()

def build_sixth_advertise_data():
  advertise_settings.append(SETTINGS_6)
  advertise_data.append(DATA_6)
  uuid = DATA_6['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_fifth_advertise_data()

def build_fifth_advertise_data():
  advertise_settings.append(SETTINGS_5)
  advertise_data.append(DATA_5)
  uuid = DATA_5['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_fourth_advertise_data()

def build_fourth_advertise_data():
  advertise_settings.append(SETTINGS_4)
  advertise_data.append(DATA_4)
  uuid = DATA_4['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_third_advertise_data()

def build_third_advertise_data():
  advertise_settings.append(SETTINGS_3)
  advertise_data.append(DATA_3)
  uuid = DATA_3['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_second_advertise_data()

def build_second_advertise_data():
  advertise_settings.append(SETTINGS_2)
  advertise_data.append(DATA_2)
  uuid = DATA_2['SERVICE_UUID']
  advertise_uuid.append(uuid)
  build_first_advertise_data()

def build_first_advertise_data():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_1)
  uuid = DATA_1['SERVICE_UUID']
  advertise_uuid.append(uuid)

def build_advertise_data_greater_than_31bytes():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_100)
  uuid = DATA_100['SERVICE_UUID']
  advertise_uuid.append(uuid)

def build_advertise_data_with_only_uuidlist():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_200)
  uuid = DATA_200['SERVICE_UUID']
  advertise_uuid.append(uuid)

def build_advertise_data_with_manufacturer_data_uuidlist():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_300)
  uuid = DATA_300['SERVICE_UUID']
  advertise_uuid.append(uuid)

def build_advertise_data_with_service_data_uuidlist():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_400)
  uuid = DATA_400['SERVICE_UUID']
  advertise_uuid.append(uuid)

def build_advertise_data_with_manufacturer_data_service_data_uuidlist():
  advertise_settings.append(SETTINGS_1)
  advertise_data.append(DATA_500)
  uuid = DATA_500['SERVICE_UUID']
  advertise_uuid.append(uuid)

choose_advertise_data = {1: build_first_advertise_data,
                         2: build_second_advertise_data,
                         3: build_third_advertise_data,
                         4: build_fourth_advertise_data,
                         5: build_fifth_advertise_data,
                         6: build_sixth_advertise_data,
                         7: build_seventh_advertise_data,
                         8: build_eighth_advertise_data,
                         9: build_ninth_advertise_data,
                         10: build_tenth_advertise_data,
                         100: build_advertise_data_greater_than_31bytes,
                         200: build_advertise_data_with_only_uuidlist,
                         300: build_advertise_data_with_manufacturer_data_uuidlist,
                         400: build_advertise_data_with_service_data_uuidlist,
                         500: build_advertise_data_with_manufacturer_data_service_data_uuidlist
}

"""Advertisemet Data Configuration List
"""
advertise_settings = []
advertise_data = []
advertise_uuid = []
expected_advertise_result = []

"""Active Advertisement List
"""
advertise_callback_index = []
advertise_settings_index = []
advertise_data_index = []


def build_advertise_settings_list(advertise_settings, droid):
  """Build Advertise Settings List
  """
  del advertise_settings_index[0:len(advertise_settings_index)]
  for settings in advertise_settings:
    mode = settings['mode']
    tx_power = settings['txpwr']
    type = settings['type']
    settings_index = build_advertise_settings(droid, mode, tx_power, type)
    advertise_settings_index.append(settings_index)


def build_advertise_data_list(advertise_data, droid):
  """Build Advertise Data List
  """
  del advertise_data_index[0:len(advertise_data_index)]
  del advertise_callback_index[0:len(advertise_callback_index)]
  for data in advertise_data:
    pwr_incl = data['PWRINCL']
    name_incl = data['INCLNAME']
    id = data['ID']
    manu_data = data['MANU_DATA']
    serv_data = data['SERVICE_DATA']
    serv_uuid = data['SERVICE_UUID']
    uuid = data['UUIDLIST']
    data_index, callback_index = build_advertise_data(droid, pwr_incl,
                                                      name_incl, id, manu_data,
                                                      serv_uuid, serv_data,
                                                      uuid)
    advertise_data_index.append(data_index)
    advertise_callback_index.append(callback_index)


def advertise_error_codes(error_code):
  """Returns appropriate Error Log based on Error Code
  """
  if error_code == AdvertiseErrorCode.DATA_TOO_LARGE.value:
    return ("".join(["Failed to Start Advertising as the advertise data",
                     " to be broadcasted is larger than 31 bytes."]))

  elif error_code == AdvertiseErrorCode.TOO_MANY_ADVERTISERS.value:
    return ("".join(["Failed to Start Advertising",
                     " because no advertising instance is available."]))

  elif error_code == AdvertiseErrorCode.ADVERTISE_ALREADY_STARTED.value:
    return "Fails to Start Advertising as the advertising is already started."

  elif error_code == AdvertiseErrorCode.BLUETOOTH_INTERNAL_FAILURE.value:
    return "Operation failed due to an internal error."

  elif error_code == AdvertiseErrorCode.FEATURE_NOT_SUPPORTED.value:
    return "This feature is not supported on this platform."


def verify_advertisement(event_dispatcher, index, callbackIdx, expected_result):
  """Verify Advertisement Status, Handles onSuccess and onFailure Events
  """
  status = False
  onSuccess_received = False
  error_value = ''
  expected_index = expected_result['Expected Result']['Index']
  expected_status = expected_result['Expected Result']['Status']
  advt_event_onSuccess = "".join([BLE_ADVERTISE, str(callbackIdx),
                                  BLE_ONSUCCESS])
  advt_event_onFailure = "".join([BLE_ADVERTISE, str(callbackIdx),
                                  BLE_ONFAILURE])
  try:
    success_result = event_dispatcher.pop_event(advt_event_onSuccess, 5)
  except Exception:
    onSuccess_received = False
  else:
    onSuccess_received = True
    type = success_result['data']['Type']
    if ((type == expected_status) and (expected_index == index)):
      status = True

  if onSuccess_received is False:
    try:
      failure_result = event_dispatcher.pop_event(advt_event_onFailure, 5)
    except Exception:
      status = False
    else:
      type = failure_result['data']['Type']
      error_code = failure_result['data']['ErrorCode']
      error_value = advertise_error_codes(error_code)
      if ((type == expected_status) and (expected_index == index)):
        status = True
  return status, error_value


def start_advertising(start_index, total_advertise, droid, event_dispatcher):
  """Start Advertising for all instances
  """
  total_advertise = start_index + total_advertise
  status = False
  error_value = ''
  for index in range(start_index, total_advertise):
    callbackIdx = advertise_callback_index[index]
    settingsIdx = advertise_settings_index[index]
    dataIdx = advertise_data_index[index]
    droid.startBleAdvertising(callbackIdx, dataIdx, settingsIdx)
    if status is True:
      expected_result = expected_advertise_result[index]
      callback = advertise_callback_index[index]
      status, error_value = verify_advertisement(event_dispatcher, index,
                                                 callback, expected_result)
      if status is False:
        break
    else:
      break
  return status, error_value




def stop_advertising(start_index, total_advertise, droid):
  """Stop Advertising for all instances
  """
  total_advertise = start_index + total_advertise
  for index in range(start_index, total_advertise):
    callbackIdx = advertise_callback_index[index]
    status = droid.stopBleAdvertising(callbackIdx)


def modify_expected_result(index, event_name):
  """Modify the Expected Result with Status Field
  """
  expected_advertise_result.pop(index)
  expected_advertise_result.insert(index,{"Expected Result":
                                         {"Index": index,"Status": event_name}})


def clean_up_resources(droid):
  """Clear Advertisement Data Information
  """
  for callback in advertise_callback_index:
    droid.removeBleAdvertiseCallback(callback)

  for settings in advertise_settings_index:
    droid.removeBleAdvertiseSetting(settings)

  for data in advertise_data_index:
    droid.removeBleAdvertiseData(data)

  del advertise_callback_index[0:len(advertise_callback_index)]
  del advertise_settings_index[0:len(advertise_settings_index)]
  del advertise_data_index[0:len(advertise_data_index)]

  del advertise_settings[0:len(advertise_settings)]
  del advertise_data[0:len(advertise_data)]
  del advertise_uuid[0:len(advertise_uuid)]
  del expected_advertise_result[0:len(expected_advertise_result)]
