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

import shlex


class DeviceCommand(object):
    """Base interface class for adb shell commands."""

    def __init__(self, device, command):
        """Create a DeviceCommand.

        Args:
            device: AndroidDevice object
            command: adb command string to run
        """
        self._ad = device
        self._command = command

    def run(self):
        """Runs the adb command"""
        self._ad.adb.shell(self._command)


class DeviceState(object):
    """Class for adb commands for setting device properties to a value."""

    def __init__(self, device, base_cmd):
        """Create a DeviceState.

        Args:
            device: AndroidDevice object
            base_cmd: The base adb command. Needs to accept an argument/value to
                generate the full command.
        """
        self._ad = device
        self._base_cmd = base_cmd

    def set_value(self, value):
        """Runs the adb command with the given argument/value.

        Args:
            value: The value to run the command with
        """
        self._ad.adb.shell('%s %s' % (self._base_cmd, shlex.quote(str(value))))


class DeviceBinaryState(object):
    """Class for adb commands for toggling on/off properties."""

    def __init__(self, device, on_cmd, off_cmd):
        """Create a DeviceBinaryState.

        Args:
            device: AndroidDevice object
            on_cmd: Command used for the 'on' state
            off_cmd: Command used for the 'off' state
        """
        self._ad = device
        self._on_cmd = on_cmd
        self._off_cmd = off_cmd

    def toggle(self, enabled):
        """Run the command corresponding to the desired state.

        Args:
            enabled: True for the 'on' state.
        """
        self._ad.adb.shell(self._on_cmd if enabled else self._off_cmd)


class DeviceSetprop(DeviceState):
    """Class for setprop commands."""

    def __init__(self, device, prop):
        """Create a DeviceSetprop.

        Args:
            device: AndroidDevice object
            prop: Property name
        """
        super().__init__(device, 'setprop %s' % prop)


class DeviceBinarySetprop(DeviceBinaryState):
    """Class for setprop commands that toggles a boolean value."""

    def __init__(self, device, prop, on_val='1', off_val='0'):
        """Create a DeviceBinarySetting.

        Args:
            device: AndroidDevice object
            prop: Property name
            on_val: Value used for the 'on' state
            off_val: Value used for the 'off' state
        """
        on_cmd = 'setprop %s %s' % (prop, on_val)
        off_cmd = 'setprop %s %s' % (prop, off_val)
        super().__init__(device, on_cmd, off_cmd)


class DeviceSetting(DeviceState):
    """Class for commands to set a settings.db entry to a value."""

    def __init__(self, device, namespace, setting):
        """Create a DeviceSetting.

        Args:
            device: AndroidDevice object
            namespace: Namespace of the setting
            setting: Setting name
        """
        super().__init__(device, 'settings put %s %s' % (namespace, setting))


class DeviceBinarySetting(DeviceBinaryState):
    """Class for commands to toggle a settings.db value on/off."""

    def __init__(self, device, namespace, setting, on_val='1', off_val='0'):
        """Create a DeviceBinarySetting.

        Args:
            device: AndroidDevice object
            namespace: Namespace of the setting
            setting: Setting name
            on_val: Value used for the 'on' state
            off_val: Value used for the 'off' state
        """
        on_cmd = 'settings put %s %s %s' % (namespace, setting, on_val)
        off_cmd = 'settings put %s %s %s' % (namespace, setting, off_val)
        super().__init__(device, on_cmd, off_cmd)
