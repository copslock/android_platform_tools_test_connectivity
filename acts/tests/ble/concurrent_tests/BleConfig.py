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

"""Advertisement Settings and Advertise Data Configuration
   Scan Settings and Filter Setting Configuration
"""

from test_utils.BleEnum import *

"""Manufacturer ID's
"""
MANUFACTURER_ID = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


"""Manufacturer Data
"""
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


"""Service data
"""
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


"""Service UUID's
"""
UUID_1    = "0000110a-0000-1000-8000-00805f9b34fb"
UUID_2    = "0000110b-0000-1000-8000-00805f9b34fb"
UUID_3    = "0000110c-0000-1000-8000-00805f9b34fb"
UUID_4    = "0000110d-0000-1000-8000-00805f9b34fb"
UUID_5    = "0000110e-0000-1000-8000-00805f9b34fb"
UUID_6    = "0000110f-0000-1000-8000-00805f9b34fb"
UUID_7    = "00001101-0000-1000-8000-00805f9b34fb"
UUID_8    = "00001102-0000-1000-8000-00805f9b34fb"
UUID_9    = "00001103-0000-1000-8000-00805f9b34fb"
UUID_10   = "00001104-0000-1000-8000-00805f9b34fb"
UUID_MASK = "0000110d-0000-1000-8000-00805f9b3400"


"""Service UUID LIST
"""
UUID_LIST_1 = [UUID_1]
UUID_LIST_2 = [UUID_1,UUID_2]


"""Advertisement Settings
"""
SETTINGS_1 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_2 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_3 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_4 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_5 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_6 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_7 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_8 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_MEDIUM.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }

SETTINGS_9 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_BALANCED.value,
               "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_LOW.value,
               "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_CONNECTABLE.value }

SETTINGS_10 = { "mode"  : AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_POWER.value,
                "txpwr" : AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_ULTRA_LOW.value,
                "type"  : AdvertiseSettingsAdvertiseType.ADVERTISE_TYPE_NON_CONNECTABLE.value }


"""Advertisement Data
"""
DATA_1 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0],
           "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1,
           "SERVICE_UUID" : UUID_1, "UUIDLIST" : -1 }

DATA_2 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[1],
           "MANU_DATA" : MANUFACTURER_DATA_2, "SERVICE_DATA" : SERVICE_DATA_2,
           "SERVICE_UUID" : UUID_2, "UUIDLIST" : -1 }

DATA_3 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[2],
           "MANU_DATA" : MANUFACTURER_DATA_3, "SERVICE_DATA" : SERVICE_DATA_3,
           "SERVICE_UUID" : UUID_3, "UUIDLIST" : -1 }

DATA_4 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[3],
           "MANU_DATA" : MANUFACTURER_DATA_4, "SERVICE_DATA" : SERVICE_DATA_4,
           "SERVICE_UUID" : UUID_4, "UUIDLIST" : -1 }

DATA_5 = { "PWRINCL" : False, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1,
           "SERVICE_DATA" : SERVICE_DATA_5, "SERVICE_UUID" : UUID_5,
           "UUIDLIST" : -1 }

DATA_6 = { "PWRINCL" : True, "INCLNAME" : False, "ID" : MANUFACTURER_ID[5],
           "MANU_DATA" : MANUFACTURER_DATA_6, "SERVICE_DATA" : SERVICE_DATA_6,
           "SERVICE_UUID" : UUID_6, "UUIDLIST" : -1 }

DATA_7 = { "PWRINCL" : False, "INCLNAME" : True, "ID" : MANUFACTURER_ID[6],
           "MANU_DATA" : MANUFACTURER_DATA_7, "SERVICE_DATA" : SERVICE_DATA_7,
           "SERVICE_UUID" : UUID_7, "UUIDLIST" : -1 }

DATA_8 = { "PWRINCL" : True, "INCLNAME" : False, "ID" : -1, "MANU_DATA" : -1,
           "SERVICE_DATA" : SERVICE_DATA_8, "SERVICE_UUID" : UUID_8,
           "UUIDLIST" : -1 }

DATA_9 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1,
           "SERVICE_DATA" : SERVICE_DATA_9, "SERVICE_UUID" : UUID_9,
           "UUIDLIST" : -1 }

DATA_10 = { "PWRINCL" : False, "INCLNAME" : False, "ID" : MANUFACTURER_ID[9],
            "MANU_DATA" : MANUFACTURER_DATA_10,
            "SERVICE_DATA" : SERVICE_DATA_10, "SERVICE_UUID" : UUID_10,
            "UUIDLIST" : -1 }


"""Advertisement Data for Corner Cases
"""
DATA_100 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0],
             "MANU_DATA" : LARGE_MANUFACTURER_DATA,
             "SERVICE_DATA" : LARGE_SERVICE_DATA, "SERVICE_UUID" : UUID_1,
             "UUIDLIST" : -1 }

DATA_200 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1,
             "SERVICE_DATA" : -1, "SERVICE_UUID" : -1,
             "UUIDLIST" : UUID_LIST_2 }

DATA_300 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0],
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : -1,
             "SERVICE_UUID" : -1, "UUIDLIST" : UUID_LIST_2 }

DATA_400 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : -1, "MANU_DATA" : -1,
             "SERVICE_DATA" : SERVICE_DATA_1, "SERVICE_UUID" : UUID_1,
             "UUIDLIST" : UUID_LIST_2 }

DATA_500 = { "PWRINCL" : True, "INCLNAME" : True, "ID" : MANUFACTURER_ID[0],
             "MANU_DATA" : MANUFACTURER_DATA_1, "SERVICE_DATA" : SERVICE_DATA_1,
             "SERVICE_UUID" : UUID_1, "UUIDLIST" : UUID_LIST_2 }


"""BLE Event Names
"""
BLE_ADVERTISE = "BleAdvertise"
BLE_FILTERSCAN = "BleScan"


"""BLE Status Types
"""
BLE_ONSUCCESS = "onSuccess"
BLE_ONFAILURE = "onFailure"
BLE_ONSCANRESULT = "onScanResults"
