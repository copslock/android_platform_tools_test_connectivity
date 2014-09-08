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

"""
Advertisement Settings and Advertise Data Values to build Advertise Data
"""

from test_utils.BleEnum import *

#Manufacturer ID's
MANUFACTURER_ID = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

#Manufacturer Data
MANUFACTURER_DATA_1     = "4,0,54"
MANUFACTURER_DATA_2     = "13,0,8"
MANUFACTURER_DATA_3     = "11,0,50"
MANUFACTURER_DATA_4     = "3,1,45"
MANUFACTURER_DATA_5     = "2,9,54"
MANUFACTURER_DATA_6     = "12,11,50"
MANUFACTURER_DATA_7     = "2,12,13"
MANUFACTURER_DATA_8     = "4,54,12"
MANUFACTURER_DATA_9     = "12,33,12"
MANUFACTURER_DATA_10    = "4,54,1"
MANUFACTURER_DATA_MASK  = "4,0,0"
LARGE_MANUFACTURER_DATA = "4,0,54,0,0,0,0,0"

#Service data
SERVICE_DATA_1     = "11,17,80"
SERVICE_DATA_2     = "13,0,8"
SERVICE_DATA_3     = "11,14,50"
SERVICE_DATA_4     = "16,22,11"
SERVICE_DATA_5     = "2,9,54"
SERVICE_DATA_6     = "69,11,50"
SERVICE_DATA_7     = "12,11,21"
SERVICE_DATA_8     = "12,12,44"
SERVICE_DATA_9     = "4,54,1"
SERVICE_DATA_10    = "33,22,44"
SERVICE_DATA_MASK  = "11,0,0"
LARGE_SERVICE_DATA = "11,17,80,0,0,0,0,0"

#Service UUID
UUID_1    = "0000110A-0000-1000-8000-00805F9B34FB"
UUID_2    = "0000110B-0000-1000-8000-00805F9B34FB"
UUID_3    = "0000110C-0000-1000-8000-00805F9B34FB"
UUID_4    = "0000110D-0000-1000-8000-00805F9B34FB"
UUID_5    = "0000110E-0000-1000-8000-00805F9B34FB"
UUID_6    = "0000110F-0000-1000-8000-00805F9B34FB"
UUID_7    = "00001101-0000-1000-8000-00805F9B34FB"
UUID_8    = "00001102-0000-1000-8000-00805F9B34FB"
UUID_9    = "00001103-0000-1000-8000-00805F9B34FB"
UUID_10   = "00001104-0000-1000-8000-00805F9B34FB"
UUID_MASK = "0000110D-0000-1000-8000-00805F9B3400"

#UUID LIST
UUID_LIST_1 = [UUID_1]
UUID_LIST_2 = [UUID_1,UUID_2]

#Advertisement Settings
SETTINGS_1 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_2 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_3 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_4 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_5 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_6 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_7 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_8 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_9 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value, \
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_10 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
                "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
                "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

#Advertisement Settings values for Corner Scenarios
SETTINGS_100 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_101 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_102 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_103 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_104 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_105 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_106 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_107 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_108 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_109 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_110 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_111 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value, \
                 "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value, \
                 "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

#Advertisement Data
DATA_1 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
           "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1, \
           "SERVICE_UUID" : UUID_1, "UUIDLIST" : -1 }

DATA_2 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[1], \
           "MANU_DATA" : MANUFACTURER_DATA_2, "SERVICE_DATA" : SERVICE_DATA_2, \
           "SERVICE_UUID" : UUID_2, "UUIDLIST" : -1 }

DATA_3 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[2], \
           "MANU_DATA" : MANUFACTURER_DATA_3, "SERVICE_DATA" : SERVICE_DATA_3, \
           "SERVICE_UUID" : UUID_3, "UUIDLIST" : -1 }

DATA_4 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[3], \
           "MANU_DATA" : MANUFACTURER_DATA_4, "SERVICE_DATA" : SERVICE_DATA_4, \
           "SERVICE_UUID" : UUID_4, "UUIDLIST" : -1 }

DATA_5 = { "PWRINCL" : False, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
           "SERVICE_DATA" : SERVICE_DATA_5, "SERVICE_UUID" : UUID_5, "UUIDLIST" : -1 }

DATA_6 = { "PWRINCL" : True, "INCLNAME" : False, "ID" : MANUFACTURER_ID[5], \
           "MANU_DATA" : MANUFACTURER_DATA_6, "SERVICE_DATA" : SERVICE_DATA_6, \
           "SERVICE_UUID" : UUID_6, "UUIDLIST" : -1 }

DATA_7 = { "PWRINCL" : False, "INCLNAME" : True, "ID" : MANUFACTURER_ID[6], \
           "MANU_DATA" : MANUFACTURER_DATA_7, "SERVICE_DATA" : SERVICE_DATA_7, \
           "SERVICE_UUID" : UUID_7, "UUIDLIST" : -1 }

DATA_8 = { "PWRINCL" : True, "INCLNAME" : False, "ID" : -1, "MANU_DATA" : -1, \
           "SERVICE_DATA" : SERVICE_DATA_8, "SERVICE_UUID" : UUID_8, "UUIDLIST" : -1 }

DATA_9 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
           "SERVICE_DATA" : SERVICE_DATA_9, "SERVICE_UUID" : UUID_9, "UUIDLIST" : -1 }

DATA_10 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[9], \
            "MANU_DATA" : MANUFACTURER_DATA_10, "SERVICE_DATA" : SERVICE_DATA_10, \
            "SERVICE_UUID" : UUID_10, "UUIDLIST" : -1 }

#Advertisement Data values for Corner Cases
DATA_100 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : LARGE_MANUFACTURER_DATA, "SERVICE_DATA" : LARGE_SERVICE_DATA, \
             "SERVICE_UUID" : UUID_1, "UUIDLIST" : -1 }

DATA_101 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
             "SERVICE_DATA" : -1, "SERVICE_UUID" : -1, "UUIDLIST" : UUID_LIST_1 }

DATA_102 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1, "SERVICE_UUID" : -1, \
             "UUIDLIST" : -1 }

DATA_103 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
             "SERVICE_DATA" : SERVICE_DATA_1, "SERVICE_UUID" : UUID_1, "UUIDLIST" : -1 }

DATA_104 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1, "SERVICE_UUID" : -1, \
             "UUIDLIST" : UUID_LIST_1 }

DATA_105 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
             "SERVICE_DATA" : SERVICE_DATA_1, "SERVICE_UUID" : UUID_1, "UUIDLIST" : UUID_LIST_1 }

DATA_106 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1, \
             "SERVICE_UUID" : UUID_1, "UUIDLIST" : UUID_LIST_1 }

DATA_107 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1, \
             "SERVICE_UUID" : UUID_1, "UUIDLIST" : -1 }

DATA_108 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
             "SERVICE_DATA" : -1, "SERVICE_UUID" : -1, "UUIDLIST" : UUID_LIST_2 }

DATA_109 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1, "SERVICE_UUID" : -1, \
             "UUIDLIST" : UUID_LIST_2 }

DATA_110 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1, \
             "SERVICE_DATA" : SERVICE_DATA_1, "SERVICE_UUID" : UUID_1, "UUIDLIST" : UUID_LIST_2 }

DATA_111 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0], \
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1, \
             "SERVICE_UUID" : UUID_1, "UUIDLIST" : UUID_LIST_2 }

#Flag to handle Success / Failure
SUCCESS = 0
FAIL = 1

#Function to extract the UUID from Scan Result
def case_insensitive_compare_uuidlist(exp_uuids, recv_uuids):
    #Compare Case Insensitive UUID LIST
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
            if ((exp_uuid.lower() == recv_uuid.lower()) and (succ_list[index] == False)):
                succ_count += 1
                succ_list[index] = True
    del succ_list[ 0:len(succ_list)]
    if (succ_count == expected_succ_count):
        return True
    else:
        return False

#Function to convert strings to array list
def convert_string_to_int_array(string_list):
    int_array = []
    loop = 0
    ch = string_list[0]
    while (ch != ']'):
        ch = string_list[loop]
        if ((ch != ',') and (ch != '[') and (ch != ']')):
            id = int(ch)
            int_array.append(id)
        loop += 1
    return int_array

#Function to extract the string from byte array list
def extract_string_from_byte_array(string_list):
    start = 1
    end = len(string_list) - 1
    extract_string = string_list[start:end]
    return extract_string