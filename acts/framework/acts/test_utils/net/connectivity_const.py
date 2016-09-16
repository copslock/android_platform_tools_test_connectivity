#!/usr/bin/env python3.4
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

######################################################
# ConnectivityManager.NetworkCallback events
######################################################
EVENT_NETWORK_CALLBACK = "NetworkCallback"

# event types
NETWORK_CB_PRE_CHECK = "PreCheck"
NETWORK_CB_AVAILABLE = "Available"
NETWORK_CB_LOSING = "Losing"
NETWORK_CB_LOST = "Lost"
NETWORK_CB_UNAVAILABLE = "Unavailable"
NETWORK_CB_CAPABILITIES_CHANGED = "CapabilitiesChanged"
NETWORK_CB_SUSPENDED = "Suspended"
NETWORK_CB_RESUMED = "Resumed"
NETWORK_CB_LINK_PROPERTIES_CHANGED = "LinkPropertiesChanged"
NETWORK_CB_INVALID = "Invalid"

# event data keys
NETWORK_CB_KEY_ID = "id"
NETWORK_CB_KEY_EVENT = "networkCallbackEvent"
NETWORK_CB_KEY_MAX_MS_TO_LIVE = "maxMsToLive"
NETWORK_CB_KEY_RSSI = "rssi"
NETWORK_CB_KEY_INTERFACE_NAME = "interfaceName"