#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from acts.test_utils.instrumentation_tests.adb_command_types \
    import DeviceBinaryCommandSeries
from acts.test_utils.instrumentation_tests.adb_command_types \
    import DeviceSetting
from acts.test_utils.instrumentation_tests.adb_command_types import DeviceState

GLOBAL = 'global'
SYSTEM = 'system'
SECURE = 'secure'

"""Common device settings for power testing."""

# TODO: add descriptions to each setting

airplane_mode = DeviceBinaryCommandSeries(
    [
        DeviceSetting(GLOBAL, 'airplane_mode_on'),
        DeviceState(
            'am broadcast -a android.intent.action.AIRPLANE_MODE --ez state',
            'true', 'false')
    ]
)

mobile_data = DeviceBinaryCommandSeries(
    [
        DeviceSetting(GLOBAL, 'mobile_data'),
        DeviceState('svc data', 'enable', 'disable')
    ]
)

cellular = DeviceSetting(GLOBAL, 'cell_on')

wifi = DeviceBinaryCommandSeries(
    [
        DeviceSetting(GLOBAL, 'wifi_on'),
        DeviceState('svc wifi', 'enable', 'disable')
    ]
)

ethernet = DeviceState('ifconfig eth0', 'up', 'down')

bluetooth = DeviceState('service call bluetooth_manager', '6', '8')

nfc = DeviceState('svc nfc', 'enable', 'disable')

screen_adaptive_brightness = DeviceSetting(
    SYSTEM, 'screen_brightness_mode')

screen_brightness = DeviceSetting(SYSTEM, 'screen_brightness')

auto_time = DeviceSetting(GLOBAL, 'auto_time')

auto_timezone = DeviceSetting(GLOBAL, 'auto_time_zone')

location_gps = DeviceSetting(SECURE, 'location_providers_allowed',
                             '+gps', '-gps')

location_network = DeviceSetting(SECURE, 'location_providers_allowed',
                                 '+network', '-network')
