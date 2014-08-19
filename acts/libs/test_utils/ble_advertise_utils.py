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

"""
Helper functions for Advertise Feature
"""

from test_utils.ble_utils import *
from test_utils.ble_helper_functions import *

#Build Advertise Data based on below configs
ADVERTISE_DATA_NO_INCLUDE_TX_POWER = 0
ADVERTISE_DATA_NO_INCLUDE_DEVICE_NAME = 1
ADVERTISE_DATA_ONLY_MANUFACTURER_DATA = 2
ADVERTISE_DATA_ONLY_SERVICE_DATA = 3
ADVERTISE_DATA_ONLY_UUIDS = 4


class BleAdvertiseVerificationError(Exception):
    """Error in fetsching BleScanner Advertise result."""

#Switch Statement Functions to handle Advertisement Error Codes
def error_data_too_large(self):
  self.log.info(
    "Failed to Start Advertising as the advertise data to be broadcasted is larger than 31 bytes.")


def error_too_many_advertisers(self):
  self.log.info(
    "Failed to Start Advertising because no advertising instance is available.")


def error_already_started(self):
  self.log.info(
    "Fails to Start Advertising as the advertising is already started.")


def error_internal_failure(self):
  self.log.info("Operation failed due to an internal error")


def error_feature_not_supported(self):
  self.log.info("This feature is not supported on this platform")


advertise_error_codes = {1: error_data_too_large,
                         2: error_too_many_advertisers,
                         3: error_already_started,
                         4: error_internal_failure,
                         5: error_feature_not_supported,
}

#Switch Statement Functions to configure Advertisement Data and Settings
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
  advertise_settings.append(SETTINGS_100)
  advertise_data.append(DATA_100)
  uuid = DATA_100['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_only_uuid():
  advertise_settings.append(SETTINGS_101)
  advertise_data.append(DATA_101)
  uuid = DATA_101['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_only_manufacturer_data():
  advertise_settings.append(SETTINGS_102)
  advertise_data.append(DATA_102)
  uuid = DATA_102['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_only_service_data():
  advertise_settings.append(SETTINGS_103)
  advertise_data.append(DATA_103)
  uuid = DATA_103['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_manufacturer_data_uuid():
  advertise_settings.append(SETTINGS_104)
  advertise_data.append(DATA_104)
  uuid = DATA_104['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_service_data_uuid():
  advertise_settings.append(SETTINGS_105)
  advertise_data.append(DATA_105)
  uuid = DATA_105['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_manufacturer_data_service_data_uuid():
  advertise_settings.append(SETTINGS_106)
  advertise_data.append(DATA_106)
  uuid = DATA_106['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_manufacturer_data_service_data():
  advertise_settings.append(SETTINGS_107)
  advertise_data.append(DATA_107)
  uuid = DATA_107['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_only_uuidlist():
  advertise_settings.append(SETTINGS_108)
  advertise_data.append(DATA_108)
  uuid = DATA_108['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_manufacturer_data_uuidlist():
  advertise_settings.append(SETTINGS_109)
  advertise_data.append(DATA_109)
  uuid = DATA_109['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_service_data_uuidlist():
  advertise_settings.append(SETTINGS_110)
  advertise_data.append(DATA_110)
  uuid = DATA_110['SERVICE_UUID']
  advertise_uuid.append(uuid)


def build_advertise_data_with_manufacturer_data_service_data_uuidlist():
  advertise_settings.append(SETTINGS_111)
  advertise_data.append(DATA_111)
  uuid = DATA_111['SERVICE_UUID']
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
                         101: build_advertise_data_with_only_uuid,
                         102: build_advertise_data_with_only_manufacturer_data,
                         103: build_advertise_data_with_only_service_data,
                         104: build_advertise_data_with_manufacturer_data_uuid,
                         105: build_advertise_data_with_service_data_uuid,
                         106: build_advertise_data_with_manufacturer_data_service_data,
                         107: build_advertise_data_with_manufacturer_data_service_data_uuid,
                         108: build_advertise_data_with_only_uuidlist,
                         109: build_advertise_data_with_manufacturer_data_uuidlist,
                         110: build_advertise_data_with_service_data_uuidlist,
                         111: build_advertise_data_with_manufacturer_data_service_data_uuidlist
}

#Advertisemet Data Configuration List
advertise_settings = []
advertise_data = []
advertise_uuid = []
expected_advertise_result = []

#Active Advertisement List
advertise_callback_index = []
advertise_settings_index = []
advertise_data_index = []


def build_advertise_settings(droid, mode, txpower, type):
  #Function to build advertise Settings
  droid.setAdvertisementSettingsAdvertiseMode(mode)
  droid.setAdvertisementSettingsTxPowerLevel(txpower)
  droid.setAdvertisementSettingsIsConnectable(type)
  settings = droid.buildAdvertisementSettings()
  return settings


def build_advertise_settings_list(advertise_settings, droid):
  #Function to build advertise Settings List
  del advertise_settings_index[0:len(advertise_settings_index)]
  for settings in advertise_settings:
    mode = settings['mode']
    tx_power = settings['txpwr']
    type = settings['type']
    settings_index = build_advertise_settings(droid, mode, tx_power, type)
    advertise_settings_index.append(settings_index)


def build_advertise_data(droid, pwr_incl, name_incl, id, manu_data, serv_uuid,
                         serv_data, uuid):
  #Function to build Advertise Data
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


def build_advertise_data_list(advertise_data, droid):
  #Function to build Advertise Data List
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


def verify_advertisement(event_dispatcher, index, callbackIdx, expected_result):
  #Function to handle onSuccess and onFailure Events
  status = False
  expected_index = expected_result['Expected Result']['Index']
  expected_status = expected_result['Expected Result']['Status']
  advt_event_onSuccess = "BleAdvertise" + str(callbackIdx) + "onSuccess"
  advt_event_onFailure = "BleAdvertise" + str(callbackIdx) + "onFailure"

  try:
    success_result = event_dispatcher.pop_event(advt_event_onSuccess, 5)
  except Exception:
    status = False
  else:
    type = success_result['data']['Type']
    if ((type == expected_status) and (expected_index == index)):
      status = True
  try:
    failure_result = event_dispatcher.pop_event(advt_event_onFailure, 5)
  except Exception:
    status = False
  else:
    type = failure_result['data']['Type']
    error_code = failure_result['data']['ErrorCode']
    advertise_error_codes.get(error_code, lambda: None)()
    if ((type == expected_status) and (expected_index == index)):
      status = True
  return status


def start_advertising(start_index, total_advertise, droid, event_dispatcher):
  total_advertise = start_index + total_advertise
  status = False
  for index in range(start_index, total_advertise):
    callbackIdx = advertise_callback_index[index]
    settingsIdx = advertise_settings_index[index]
    dataIdx = advertise_data_index[index]
    status = startbleadvertise(droid, callbackIdx, dataIdx, settingsIdx)
    if status is True:
      expected_result = expected_advertise_result[index]
      callback = advertise_callback_index[index]
      status = verify_advertisement(event_dispatcher, index, callback,
                                    expected_result)
      if status is False:
        break
    else:
      break
  return status


def stop_advertising(start_index, total_advertise, droid):
  total_advertise = start_index + total_advertise
  for index in range(start_index, total_advertise):
    callbackIdx = advertise_callback_index[index]
    status = stopbleadvertise(droid, callbackIdx)


def modify_expected_result(index, event_name):
  #Function to change the expected result
  expected_advertise_result.pop(index)
  expected_advertise_result.insert(index,
                                   {"Expected Result": {"Index": index,
                                                        "Status": event_name}})


def clean_up_resources(droid):
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

#Configured Parameters to hold Scan Filter Type
NO_FILTER = 0
NAME_FILTER = 1
MACADDRESS_FILTER = 2
MANUFACTURER_DATA_FILTER = 3
SERVICE_DATA_FILTER = 4
SERVICE_UUID_FILTER = 5
ALL_TYPE_FILTER = 6
MULTIPLE_FILTER = 7

#Index Positions of an Array to hold Advertisers information
DEVICE_INDEX = 0
DISPATCHER_INDEX = 1
FILTER_INDEX = 2
CALLBACK_INDEX = 3
SETTINGS_INDEX = 4
DATA_INDEX = 5
SET_EACH_FILTER = 6
FILTER_TYPE_INDEX = 7

#Scan Device under test configuration
SCAN_DEVICE_1 = { 'deviceName'     : "volantis1",
                  'CallbackType'   : ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                  'ScanMode'       : ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                  'ScanResultType' : ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value,
                  'ReportDelay'    : ScanSettingsReportDelaySeconds.MIN.value }

#Advertisers List Configurations
ADVERTISERS = [ { 'deviceName' : "volantis2", 'setFilter' : True,
                  'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
                  'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
                  'FILTER_LIST': [True,False,True,False],
                  'TYPE'       : -1 } ]

#Advertisers with multiple Filters List Configurations
ADVERTISERS_WITH_MULTIPLE_FILTERS = [ { 'deviceName' : "volantis2", 'setFilter' : True,
                  'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
                  'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
                  'FILTER_LIST': [True,False,True,False],
                  'TYPE'       : [NAME_FILTER,-1,
                                  MANUFACTURER_DATA_FILTER,-1]} ]



def verify_advertise_settings_advertise_mode(testcase, droid, expected_advertise_mode):
    try:
        droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the advertise setting's advertise mode.")
    advertise_mode = droid.getAdvertisementSettingsMode(settings_index)
    if expected_advertise_mode is not advertise_mode:
        testcase.log.debug("Expected value: " + str(expected_advertise_mode)
                                + ", Actual value: " + str(advertise_mode))
        return False
    testcase.log.debug("Advertise Setting's advertise mode " + str(expected_advertise_mode)
                           + "  value test Passed.")
    return True


def verify_advertise_settings_tx_power_level(testcase, droid, expected_advertise_tx_power):
    try:
        droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the advertise setting's tx power level.")
    advertise_tx_power_level = droid.getAdvertisementSettingsTxPowerLevel(settings_index)
    if expected_advertise_tx_power is not advertise_tx_power_level:
        testcase.log.debug("Expected value: " + str(expected_advertise_tx_power)
                                + ", Actual value: " + str(advertise_tx_power_level))
        return False
    testcase.log.debug("Advertise Setting's tx power level " + str(expected_advertise_tx_power)
                           + "  value test Passed.")
    return True


def verify_advertise_settings_is_connectable(testcase, droid, expected_is_connectable):
    try:
        droid.setAdvertisementSettingsIsConnectable(expected_is_connectable)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise settings object's index.")
    settings_index = build_advertisesettings(droid)
    testcase.log.debug("Step 4: Get the advertise setting's is connectable value.")
    is_connectable = droid.getAdvertisementSettingsIsConnectable(settings_index)
    if expected_is_connectable is not is_connectable:
        testcase.log.debug("Expected value: " + str(expected_is_connectable)
                                + ", Actual value: " + str(is_connectable))
        return False
    testcase.log.debug("Advertise Setting's is connectable " + str(expected_is_connectable)
                           + "  value test Passed.")
    return True


def verify_advertise_data_service_uuids(testcase, droid, expected_service_uuids):
    try:
        droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the advertise data's service uuids.")
    service_uuids = droid.getAdvertiseDataServiceUuids(data_index)
    if expected_service_uuids != service_uuids:
        testcase.log.debug("Expected value: " + str(expected_service_uuids)
                                + ", Actual value: " + str(service_uuids))
        return False
    testcase.log.debug("Advertise Data's service uuids " + str(expected_service_uuids)
                           + "  value test Passed.")
    return True


def verify_advertise_data_service_data(testcase, droid, expected_service_data_uuid,
                                       expected_service_data):
    try:
        droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 5: Get the advertise data's service data.")
    service_data = droid.getAdvertiseDataServiceData(data_index, expected_service_data_uuid)
    if expected_service_data != service_data:
        testcase.log.debug("Expected value: " + str(expected_service_data)
                                + ", Actual value: " + str(service_data))
        return False
    testcase.log.debug("Advertise Data's service data uuid: " + str(
                           expected_service_data_uuid) + ", service data: "
                           + str(expected_service_data)
                           + "  value test Passed.")
    return True


def verify_advertise_data_manufacturer_id(testcase, droid, expected_manufacturer_id,
                                          expected_manufacturer_specific_data):
    try:
        droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                             expected_manufacturer_specific_data)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise data object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 5: Get the advertise data's manufacturer specific data.")
    manufacturer_specific_data = droid.getAdvertiseDataManufacturerSpecificData(data_index, expected_manufacturer_id)
    if expected_manufacturer_specific_data != manufacturer_specific_data:
        testcase.log.debug("Expected value: " + str(expected_manufacturer_specific_data)
                                + ", Actual value: " + str(manufacturer_specific_data))
        return False
    testcase.log.debug("Advertise Data's manufacturer id: " + str(
                           expected_manufacturer_id) + ", manufacturer's specific data: " + str(
                           expected_manufacturer_specific_data)
                           + "  value test Passed.")
    return True


def verify_advertise_data_include_tx_power_level(testcase, droid, expected_include_tx_power_level):
    try:
        droid.setAdvertiseDataIncludeTxPowerLevel(expected_include_tx_power_level)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise settings object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the advertise data's include tx power level.")
    include_tx_power_level = droid.getAdvertiseDataIncludeTxPowerLevel(data_index)
    if expected_include_tx_power_level is not include_tx_power_level:
        testcase.log.debug("Expected value: " + str(expected_include_tx_power_level)
                                + ", Actual value: " + str(include_tx_power_level))
        return False
    testcase.log.debug(
        "Advertise Setting's include tx power level " + str(expected_include_tx_power_level)
        + "  value test Passed.")
    return True


def verify_advertise_data_include_device_name(testcase, droid, expected_include_device_name):
    try:
        droid.setAdvertiseDataIncludeDeviceName(expected_include_device_name)
    except BleAdvertiseVerificationError as error:
        testcase.log.debug(str(error))
        return False
    testcase.log.debug("Step 3: Get a advertise settings object's index.")
    data_index = build_advertisedata(droid)
    testcase.log.debug("Step 4: Get the advertise data's include device name.")
    include_device_name = droid.getAdvertiseDataIncludeDeviceName(data_index)
    if expected_include_device_name is not include_device_name:
        testcase.log.debug("Expected value: " + str(expected_include_device_name)
                                + ", Actual value: " + str(include_device_name))
        return False
    testcase.log.debug(
        "Advertise Setting's include device name " + str(expected_include_device_name)
        + "  value test Passed.")
    return True


def verify_invalid_advertise_settings_advertise_mode(testcase, droid,
                                                     expected_advertise_mode):
    try:
        droid.setAdvertisementSettingsAdvertiseMode(expected_advertise_mode)
        build_advertisesettings(droid)
        testcase.log.debug("Set Advertise settings invalid advertise mode passed "
                                + " with input as " + str(expected_advertise_mode))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise settings invalid advertise mode failed successfully"
                               + " with input as " + str(expected_advertise_mode))
        return True


def verify_invalid_advertise_settings_tx_power_level(testcase, droid,
                                                     expected_advertise_tx_power):
    try:
        droid.setAdvertisementSettingsTxPowerLevel(expected_advertise_tx_power)
        build_advertisesettings(droid)
        testcase.log.debug("Set Advertise settings invalid tx power level "
                                + " with input as " + str(expected_advertise_tx_power))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise settings invalid tx power level failed successfully"
                               + " with input as " + str(expected_advertise_tx_power))
        return True


def verify_invalid_advertise_data_service_uuids(testcase, droid,
                                                expected_service_uuids):
    try:
        droid.setAdvertiseDataSetServiceUuids(expected_service_uuids)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data service uuids "
                                + " with input as " + str(expected_service_uuids))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data invalid service uuids failed successfully"
                               + " with input as " + str(expected_service_uuids))
        return True


def verify_invalid_advertise_data_service_data(testcase, droid,
                                               expected_service_data_uuid, expected_service_data):
    try:
        droid.addAdvertiseDataServiceData(expected_service_data_uuid, expected_service_data)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data service data uuid: " + str(
            expected_service_data_uuid) + ", service data: " + str(expected_service_data))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data service data uuid: " + str(
                               expected_service_data_uuid) + ", service data: " + str(
                               expected_service_data) + " failed successfully.")
        return True


def verify_invalid_advertise_data_manufacturer_id(testcase, droid,
                                                  expected_manufacturer_id,
                                                  expected_manufacturer_specific_data):
    try:
        droid.addAdvertiseDataManufacturerId(expected_manufacturer_id,
                                             expected_manufacturer_specific_data)
        build_advertisedata(droid)
        testcase.log.debug("Set Advertise Data manufacturer id: " + str(
                                expected_manufacturer_id) + ", manufacturer specific data: " + str(
                                expected_manufacturer_specific_data))
        return False
    except android.SL4AAPIError:
        testcase.log.debug("Set Advertise Data manufacturer id: " + str(
                               expected_manufacturer_id) + ", manufacturer specific data: " + str(
                               expected_manufacturer_specific_data) + " failed successfully.")
        return True
