#!/usr/bin/env python3
#
#   Copyright 2016 - Google
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

# Constants for Wifi related events.
WIFI_CONNECTED = "WifiNetworkConnected"
WIFI_DISCONNECTED = "WifiNetworkDisconnected"
SUPPLICANT_CON_CHANGED = "SupplicantConnectionChanged"
WIFI_STATE_CHANGED = "WifiStateChanged"
WIFI_FORGET_NW_SUCCESS = "WifiManagerForgetNetworkOnSuccess"

# These constants will be used by the ACTS wifi tests.
CONNECT_BY_CONFIG_SUCCESS = 'WifiManagerConnectByConfigOnSuccess'
CONNECT_BY_NETID_SUCCESS = 'WifiManagerConnectByNetIdOnSuccess'

# Softap related constants
SOFTAP_CALLBACK_EVENT = "WifiManagerSoftApCallback-"
# Callback Event for softap state change
# WifiManagerSoftApCallback-[callbackId]-OnStateChanged
SOFTAP_STATE_CHANGED = "-OnStateChanged"
# Cllback Event for client number change:
# WifiManagerSoftApCallback-[callbackId]-OnNumClientsChanged
SOFTAP_NUMBER_CLIENTS_CHANGED = "-OnNumClientsChanged"
SOFTAP_NUMBER_CLIENTS_CALLBACK_KEY = "NumClients"
SOFTAP_STATE_CHANGE_CALLBACK_KEY = "State"
WIFI_AP_DISABLING_STATE = 10
WIFI_AP_DISABLED_STATE = 11
WIFI_AP_ENABLING_STATE = 12
WIFI_AP_ENABLED_STATE = 13
WIFI_AP_FAILED_STATE = 14
DEFAULT_SOFTAP_TIMEOUT_S = 600 # 10 minutes


# AP related constants
AP_MAIN = "main_AP"
AP_AUX = "aux_AP"
SSID = "SSID"

# cnss_diag property related constants
DEVICES_USING_LEGACY_PROP = ["sailfish", "marlin", "walleye", "taimen", "muskie"]
CNSS_DIAG_PROP = "persist.vendor.sys.cnss.diag_txt"
LEGACY_CNSS_DIAG_PROP = "persist.sys.cnss.diag_txt"
