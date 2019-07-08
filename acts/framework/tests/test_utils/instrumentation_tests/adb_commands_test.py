#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

import mock
import unittest

from acts.test_utils.instrumentation_tests.adb_commands import DeviceCommand
from acts.test_utils.instrumentation_tests.adb_commands import DeviceState
from acts.test_utils.instrumentation_tests.adb_commands import DeviceBinaryState
from acts.test_utils.instrumentation_tests.adb_commands import DeviceSetprop
from acts.test_utils.instrumentation_tests.adb_commands import DeviceBinarySetprop
from acts.test_utils.instrumentation_tests.adb_commands import DeviceSetting
from acts.test_utils.instrumentation_tests.adb_commands import DeviceBinarySetting


class AbdCommandTest(unittest.TestCase):
    def setUp(self):
        self.mock_ad = mock.MagicMock()
        self.mock_adb_shell = self.mock_ad.adb.shell

    def test_device_command(self):
        """Tests that DeviceCommand runs the correct ADB command."""
        cmd = 'run this command'
        device_command = DeviceCommand(self.mock_ad, cmd)
        device_command.run()
        self.mock_adb_shell.assert_called_with(cmd)

    def test_device_state(self):
        """Tests that DeviceState runs the correct ADB command."""
        base_cmd = 'run command with val'
        val = 15
        device_state = DeviceState(self.mock_ad, base_cmd)
        device_state.set_value(val)
        self.mock_adb_shell.assert_called_with('%s %s' % (base_cmd, val))

    def test_device_binary_state(self):
        """Tests that DeviceBinaryState runs the correct ADB commands."""
        on_cmd = 'enable this service'
        off_cmd = 'disable the service'
        device_binary_state = DeviceBinaryState(self.mock_ad, on_cmd, off_cmd)
        device_binary_state.toggle(True)
        self.mock_adb_shell.assert_called_with(on_cmd)
        device_binary_state.toggle(False)
        self.mock_adb_shell.assert_called_with(off_cmd)

    def test_device_setprop(self):
        """Tests that DeviceSetprop runs the correct ADB command."""
        prop = 'some.property'
        val = 3
        device_setprop = DeviceSetprop(self.mock_ad, prop)
        device_setprop.set_value(val)
        self.mock_adb_shell.assert_called_with(
            'setprop %s %s' % (prop, val))

    def test_device_binary_setprop(self):
        """Tests that DeviceBinarySetprop runs the correct ADB commands."""
        prop = 'some.other.property'
        on_val = True
        off_val = False
        device_binary_setprop = DeviceBinarySetprop(
            self.mock_ad, prop, on_val, off_val)
        device_binary_setprop.toggle(True)
        self.mock_adb_shell.assert_called_with('setprop %s %s' % (prop, on_val))
        device_binary_setprop.toggle(False)
        self.mock_adb_shell.assert_called_with('setprop %s %s'
                                               % (prop, off_val))

    def test_device_setting(self):
        """Tests that DeviceSetting runs the correct ADB command."""
        namespace = 'global'
        setting = 'some_new_setting'
        val = 10
        device_setting = DeviceSetting(self.mock_ad, namespace, setting)
        device_setting.set_value(val)
        self.mock_adb_shell.assert_called_with(
            'settings put %s %s %s' % (namespace, setting, val))

    def test_device_binary_setting(self):
        """Tests that DeviceBinarySetting runs the correct ADB commands."""
        namespace = 'system'
        setting = 'some_other_setting'
        on_val = 'on'
        off_val = 'off'
        device_binary_setting = DeviceBinarySetting(
            self.mock_ad, namespace, setting, on_val, off_val)
        device_binary_setting.toggle(True)
        self.mock_adb_shell.assert_called_with(
            'settings put %s %s %s' % (namespace, setting, on_val))
        device_binary_setting.toggle(False)
        self.mock_adb_shell.assert_called_with(
            'settings put %s %s %s' % (namespace, setting, off_val))


if __name__ == "__main__":
    unittest.main()
