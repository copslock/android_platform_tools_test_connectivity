#!/usr/bin/python3.4
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

"""Holds Scan and Filtering Configurations and
   Helper functions for Scan and Filtering
"""

from .BleConfig import *
from test_utils.ble_test_utils import *


"""Indicates the type of Scan Filter to be used by the scanner
"""
NO_FILTER = 0
NAME_FILTER = 1
MANUFACTURER_DATA_FILTER = 2
SERVICE_DATA_FILTER = 3
SERVICE_UUID_FILTER = 4
ALL_TYPE_FILTER = 5
MULTIPLE_FILTER = 6


"""Advertiser Array Indexes to hold Scan Filter Type for
   each advertisement instances, to hold advertise data information
"""
DEVICE_INDEX = 0
DISPATCHER_INDEX = 1
FILTER_INDEX = 2
CALLBACK_INDEX = 3
SETTINGS_INDEX = 4
DATA_INDEX = 5
SET_EACH_FILTER = 6
FILTER_TYPE_INDEX = 7


"""Information about the Scan Device under test
"""
SCAN_DEVICE_1 = { 'deviceName'     : "device1",
                  'CallbackType'   : ScanSettingsCallbackType.CALLBACK_TYPE_ALL_MATCHES.value,
                  'ScanMode'       : ScanSettingsScanMode.SCAN_MODE_LOW_POWER.value,
                  'ScanResultType' : ScanSettingsScanResultType.SCAN_RESULT_TYPE_FULL.value,
                  'ReportDelay'    : ScanSettingsReportDelaySeconds.MIN.value }


"""List of Advertisers used for scanning
"""
ADVERTISERS = [ { 'deviceName' : "device2", 'setFilter' : True,
                  'SETTINGS'   : [SETTINGS_1,SETTINGS_2,SETTINGS_3,SETTINGS_4],
                  'DATA'       : [DATA_1,DATA_2,DATA_3,DATA_4],
                  'FILTER_LIST': [True,False,True,False],
                  'TYPE'       : -1 } ]


"""Array Indexes to hold the expected status for each device advertisement
"""
NAME_IDX = 0
SUCCESSLIST_IDX = 1
STATUSLIST_IDX = 2
FAILURELIST_IDX = 3
DEVICE_STATUS_IDX = 4
SUCCESS_COUNT_IDX = 5


"""List of Advertisers
"""
advertise_device_list = []


"""Scan Callback Lists to send Scan Request for Advertisers
"""
scancallback_list = []
scanfilter_list = []
scansettings_list = []


def get_scan_device(droidlist, dispatcherlist, scanner):
  """Identify the Scan Device to be tested based on the config
     and get the device information
  """
  index = 0
  for droid in droidlist:
    dispatcher = dispatcherlist[index]
    device_name = droid.bluetoothGetLocalName()
    scanner_name = scanner['deviceName']
    if scanner_name == device_name:
      return droid, dispatcher
    index += 1
  return 0, 0


def get_scan_device_scansettings(scanner):
  """Get default Scan Settings for the Scan device to be tested
  """
  deviceName = scanner['deviceName']
  callbackType = scanner['CallbackType']
  scanMode = scanner['ScanMode']
  scanResultType = scanner['ScanResultType']
  reportDelayMillis = scanner['ReportDelay']
  return deviceName, callbackType, scanMode, scanResultType, reportDelayMillis


def config_advertise_devices(droidlist, dispatcherlist, advertiserlist):
  """Holds the list of advertisers from ADVERTISERS configuration
     and each device information
  """
  advertise = [0,0,0,0,0,0,0,0]
  index = 0
  for droid in droidlist:
    dispatcher = dispatcherlist[index]
    device_name = droid.bluetoothGetLocalName()
    for advertiser in advertiserlist:
      advertiser_name = advertiser['deviceName']
      if advertiser_name == device_name:
        advertise[DEVICE_INDEX] = droid
        advertise[DISPATCHER_INDEX] = dispatcher
        advertise[FILTER_INDEX] = advertiser['setFilter']
        advertise[SETTINGS_INDEX] = advertiser['SETTINGS']
        advertise[DATA_INDEX] = advertiser['DATA']
        advertise[SET_EACH_FILTER] = advertiser['FILTER_LIST']
        advertise[FILTER_TYPE_INDEX] = advertiser['TYPE']
        advertise_device_list.append(advertise)
        advertise = [0,0,0,0,0,0,0,0]
    index += 1
  del advertise[ 0:len(advertise) ]


def update_filter_list(filterlist):
  """Change Scan Filter Types at run time based on test requirements
  """
  for advertise in advertise_device_list:
    advertise[SET_EACH_FILTER] = filterlist


def get_advertise_data(droid, settings, data):
  """Get the Advertisement Data to Start Advertising
  """
  mode = settings['mode']
  txpower = settings['txpwr']
  type = settings['type']
  settings_index = build_advertise_settings(droid, mode, txpower, type)

  pwr_level = data['PWRINCL']
  device_name = data['INCLNAME']
  manu_id = data['ID']
  manu_data = data['MANU_DATA']
  data_uuid = data['SERVICE_UUID']
  serv_data = data['SERVICE_DATA']
  uuid = data['UUIDLIST']
  data_index, callback_index = build_advertise_data(droid, pwr_level,
                                                    device_name, manu_id,
                                                    manu_data, data_uuid,
                                                    serv_data, uuid)
  return settings_index, data_index, callback_index


def verify_onsuccess_advertisement(advertise_event_dispatcher,
                                   callbackIdx, expected_result):
  """Verify Advertisement for Success or failure
  """
  advt_event_onSuccess = "".join([BLE_ADVERTISE, str(callbackIdx),
                                  BLE_ONSUCCESS])
  try:
    success_result = advertise_event_dispatcher.pop_event(advt_event_onSuccess,
                                                          5)
  except Exception:
    return False
  else:
    type = success_result['data']['Type']
    if (type == expected_result):
      return True
    else:
      return False


def start_advertisement():
  """Start Advertisement for all instances and for all advertisers
  """
  status = False
  callback_list = []
  for advertise in advertise_device_list:
    droid = advertise[DEVICE_INDEX]
    filter = advertise[FILTER_INDEX]
    settings_list = advertise[SETTINGS_INDEX]
    data_list = advertise[DATA_INDEX]
    dispatcher = advertise[DISPATCHER_INDEX]
    index = 0
    for settings in settings_list:
      data = data_list[index]
      settings_index, data_index, callback = get_advertise_data(droid,
                                             settings, data)
      index += 1
      droid.startBleAdvertising(callback, data_index, settings_index)
      expected_result = BLE_ONSUCCESS
      status = verify_onsuccess_advertisement(dispatcher, callback,
                                              expected_result)
      if status is False:
        break
      else:
        callback_list.append(callback)
    advertise[CALLBACK_INDEX] = callback_list
    callback_list = []
  return status


def stop_advertisement():
  """Stop Advertisement for all instances and for all advertisers
  """
  for advertise in advertise_device_list:
    droid = advertise[DEVICE_INDEX]
    callback_list = advertise[CALLBACK_INDEX]
    for callback in callback_list:
      status = droid.stopBleAdvertising(callback)


def set_manufacturer_data_filter(droid, add_mask, filter, data_list,
                                 filter_list):
  """Set Manufacturer Data Filter
  """
  index = 0
  set_filter_list = filter[SET_EACH_FILTER]
  for data in data_list:
    set_filter = set_filter_list[index]
    if set_filter is True:
      id = data['ID']
      manu_data = data['MANU_DATA']
      if add_mask is True:
        droid.setScanFilterManufacturerData(id,manu_data,MANUFACTURER_DATA_MASK)
      else:
        droid.setScanFilterManufacturerData(id,manu_data)
      droid.buildScanFilter(filter_list)
    index += 1


def set_service_data_filter(droid, add_mask, filter, data_list, filter_list):
  """Set Service Data Filter
  """
  index = 0
  set_filter_list = filter[SET_EACH_FILTER]
  for data in data_list:
    set_filter = set_filter_list[index]
    if set_filter is True:
      serv_uuid = data['SERVICE_UUID']
      serv_data = data['SERVICE_DATA']
      if add_mask is True:
        droid.setScanFilterServiceData(serv_uuid,serv_data,SERVICE_DATA_MASK)
      else:
        droid.setScanFilterServiceData(serv_uuid,serv_data)
      droid.buildScanFilter(filter_list)
    index += 1


def set_service_uuid_filter(droid, add_mask, filter, data_list, filter_list):
  """Set Service UUID Filter
  """
  index = 0
  set_filter_list = filter[SET_EACH_FILTER]
  for data in data_list:
    set_filter = set_filter_list[index]
    if set_filter is True:
      serv_uuid_list = data['UUIDLIST']
      if serv_uuid_list != -1:
        for serv_uuid in serv_uuid_list:
          if add_mask is True:
            droid.setScanFilterServiceUuid(serv_uuid,UUID_MASK)
          else:
            droid.setScanFilterServiceUuid(serv_uuid)
          droid.buildScanFilter(filter_list)
    index += 1


def set_all_filter(droid, add_mask, filter, data_list, filter_list):
  """Set All Data Filters
  """
  index = 0
  set_filter_list = filter[SET_EACH_FILTER]
  advertise_droid = filter[DEVICE_INDEX]
  for data in data_list:
    set_filter = set_filter_list[index]
    if set_filter is True:
      filter_name = advertise_droid.bluetoothGetLocalName()
      id = data['ID']
      manu_data = data['MANU_DATA']
      serv_data = data['SERVICE_DATA']
      serv_uuid = data['SERVICE_UUID']
      serv_uuid_list = data['UUIDLIST']
      droid.setScanFilterDeviceName(filter_name)
      droid.buildScanFilter(filter_list)
      if add_mask is True:
        droid.setScanFilterManufacturerData(id,manu_data,MANUFACTURER_DATA_MASK)
        droid.buildScanFilter(filter_list)
        droid.setScanFilterServiceData(serv_uuid,serv_data,SERVICE_DATA_MASK)
        droid.buildScanFilter(filter_list)
        if serv_uuid_list != -1:
          for uuid in serv_uuid_list:
            droid.setScanFilterServiceUuid(uuid,UUID_MASK)
            droid.buildScanFilter(filter_list)
      else:
        droid.setScanFilterManufacturerData(id,manu_data)
        droid.buildScanFilter(filter_list)
        droid.setScanFilterServiceData(serv_uuid,serv_data)
        droid.buildScanFilter(filter_list)
        if serv_uuid_list != -1:
          for uuid in serv_uuid_list:
            droid.setScanFilterServiceUuid(uuid)
            droid.buildScanFilter(filter_list)
    index += 1


def set_multiple_filter(droid, add_mask, filter, data_list, filter_list):
  """Set Multiple Data Filters
  """
  index = 0
  advertise_droid = filter[DEVICE_INDEX]
  filter_type_list = filter[FILTER_TYPE_INDEX]
  for data in data_list:
    filter_type = filter_type_list[index]
    if filter_type is NAME_FILTER:
      filter_name = advertise_droid.bluetoothGetLocalName()
      droid.setScanFilterDeviceName(filter_name)
      droid.buildScanFilter(filter_list)
    elif filter_type is MANUFACTURER_DATA_FILTER:
      id = data['ID']
      manu_data = data['MANU_DATA']
      if add_mask is True:
        droid.setScanFilterManufacturerData(id,manu_data,MANUFACTURER_DATA_MASK)
      else:
        droid.setScanFilterManufacturerData(id,manu_data)
      droid.buildScanFilter(filter_list)
    elif filter_type is SERVICE_DATA_FILTER:
      serv_uuid = data['SERVICE_UUID']
      serv_data = data['SERVICE_DATA']
      if add_mask is True:
        droid.setScanFilterServiceData(serv_uuid,serv_data,SERVICE_DATA_MASK)
      else:
        droid.setScanFilterServiceData(serv_uuid,serv_data)
      droid.buildScanFilter(filter_list)
    elif filter_type is SERVICE_UUID_FILTER:
      serv_uuid_list = data['UUIDLIST']
      if serv_uuid_list != -1:
        for serv_uuid in serv_uuid_list:
          if add_mask is True:
            droid.setScanFilterServiceUuid(serv_uuid,UUID_MASK)
          else:
            droid.setScanFilterServiceUuid(serv_uuid)
          droid.buildScanFilter(filter_list)
    index += 1


def start_ble_scan(droid):
  """start Ble Scan for all advertisers
  """
  index = 0
  status = True
  for callback in scancallback_list:
    settings = scansettings_list[index]
    filter = scanfilter_list[index]
    droid.startBleScan(filter, settings, callback)
    index += 1
  return status


def stop_ble_scan(droid):
  """Stop Ble Scan for all advertisers
  """
  for callback in scancallback_list:
    droid.stopBleScan(callback)


def clean_up_resources():
  """Clean Scan Data information
  """
  for advertise in advertise_device_list:
    callback_list = advertise[CALLBACK_INDEX]
    del callback_list[ 0:len(callback_list) ]
  del advertise_device_list[ 0:len(advertise_device_list) ]
  del scancallback_list[ 0:len(scancallback_list) ]
  del scanfilter_list[ 0:len(scanfilter_list) ]
  del scansettings_list[ 0:len(scansettings_list) ]
