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

from enum import Enum

class ScanSettingsCallbackType(Enum):
    CALLBACK_TYPE_ALL_MATCHES = 1
    CALLBACK_TYPE_FIRST_MATCH = 2
    CALLBACK_TYPE_MATCH_LOST = 4


class ScanSettingsScanResultType(Enum):
    SCAN_RESULT_TYPE_FULL = 0
    SCAN_RESULT_TYPE_ABBREVIATED = 1


class ScanSettingsScanMode(Enum):
    SCAN_MODE_LOW_POWER = 0
    SCAN_MODE_BALANCED = 1
    SCAN_MODE_LOW_LATENCY = 2


class ScanSettingsReportDelaySeconds(Enum):
    MIN = 0
    MAX = 9223372036854775807


class AdvertiseSettingsAdvertiseType(Enum):
    ADVERTISE_TYPE_NON_CONNECTABLE  = 0
    ADVERTISE_TYPE_CONNECTABLE = 1

class AdvertiseSettingsAdvertiseMode(Enum):
    ADVERTISE_MODE_LOW_POWER = 0
    ADVERTISE_MODE_BALANCED = 1
    ADVERTISE_MODE_LOW_LATENCY = 2

class AdvertiseSettingsAdvertiseTxPower(Enum):
    ADVERTISE_TX_POWER_ULTRA_LOW = 0
    ADVERTISE_TX_POWER_LOW = 1
    ADVERTISE_TX_POWER_MEDIUM = 2
    ADVERTISE_TX_POWER_HIGH = 3


class JavaInteger(Enum):
    MIN = -2147483648
    MAX = 2147483647


class Uuids(Enum):
    P_Service = "0000feef-0000-1000-8000-00805f9b34fb"
    HR_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"

class GattConnectionState(Enum):
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    STATE_DISCONNECTING = 3