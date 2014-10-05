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
  ADVERTISE_TYPE_NON_CONNECTABLE = 0
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


class BluetoothGattCharacteristic(Enum):
  PROPERTY_BROADCAST = 0x01
  PROPERTY_READ = 0x02
  PROPERTY_WRITE_NO_RESPONSE = 0x04
  PROPERTY_WRITE = 0x08
  PROPERTY_NOTIFY = 0x10
  PROPERTY_INDICATE = 0x20
  PROPERTY_SIGNED_WRITE = 0x40
  PROPERTY_EXTENDED_PROPS = 0x80
  PERMISSION_READ = 0x01
  PERMISSION_READ_ENCRYPTED = 0x02
  PERMISSION_READ_ENCRYPTED_MITM = 0x04
  PERMISSION_WRITE = 0x10
  PERMISSION_WRITE_ENCRYPTED = 0x20
  PERMISSION_WRITE_ENCRYPTED_MITM = 0x40
  PERMISSION_WRITE_SIGNED = 0x80
  PERMISSION_WRITE_SIGNED_MITM = 0x100
  WRITE_TYPE_DEFAULT = 0x02
  WRITE_TYPE_NO_RESPONSE = 0x01
  WRITE_TYPE_SIGNED = 0x04
  FORMAT_UINT8 = 0x11
  FORMAT_UINT16 = 0x12
  FORMAT_UINT32 = 0x14
  FORMAT_SINT8 = 0x21
  FORMAT_SINT16 = 0x22
  FORMAT_SINT32 = 0x24
  FORMAT_SFLOAT = 0x32
  FORMAT_FLOAT = 0x34

class BluetoothGattDescriptor(Enum):
  ENABLE_NOTIFICATION_VALUE = [0x01, 0x00]
  ENABLE_INDICATION_VALUE = [0x02, 0x00]
  DISABLE_NOTIFICATION_VALUE = [0x00, 0x00]
  PERMISSION_READ = 0x01
  PERMISSION_READ_ENCRYPTED = 0x02
  PERMISSION_READ_ENCRYPTED_MITM = 0x04
  PERMISSION_WRITE = 0x10
  PERMISSION_WRITE_ENCRYPTED = 0x20
  PERMISSION_WRITE_ENCRYPTED_MITM = 0x40
  PERMISSION_WRITE_SIGNED = 0x80
  PERMISSION_WRITE_SIGNED_MITM = 0x100
  
class BluetoothGattService(Enum):
  SERVICE_TYPE_PRIMARY = 0
  SERVICE_TYPE_SECONDARY = 1

class BluetoothGattConnectionPriority(Enum):
  CONNECTION_PRIORITY_BALANCED = 0
  CONNECTION_PRIORITY_HIGH = 1
  CONNECTION_PRIORITY_LOW_POWER = 2

class BluetoothGatt(Enum):
  GATT_SUCCESS = 0
  GATT_FAILURE = 0x101

class AdvertiseErrorCode(Enum):
  DATA_TOO_LARGE = 1
  TOO_MANY_ADVERTISERS = 2
  ADVERTISE_ALREADY_STARTED = 3
  BLUETOOTH_INTERNAL_FAILURE = 4
  FEATURE_NOT_SUPPORTED = 5

class BluetoothAdapterState(Enum):
  STATE_OFF = 10
  STATE_TURNING_ON = 11
  STATE_ON = 12
  STATE_TURNING_OFF = 13