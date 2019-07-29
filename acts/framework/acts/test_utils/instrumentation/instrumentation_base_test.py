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

import os

import yaml
from acts.keys import Config
from acts.test_utils.instrumentation import app_installer
from acts.test_utils.instrumentation import config_wrapper
from acts.test_utils.instrumentation.instrumentation_command_builder import \
    InstrumentationCommandBuilder
from acts.test_utils.instrumentation.adb_commands import common

from acts import base_test

RESOLVE_FILE_MARKER = 'FILE'
FILE_NOT_FOUND = 'File is missing from ACTS config'
DEFAULT_POWER_CONFIG_FILE = 'power_config.yaml'


class InstrumentationTestError(Exception):
    pass


class InstrumentationBaseTest(base_test.BaseTestClass):
    """Base class for power tests based on am instrument."""

    def __init__(self, configs):
        """Initialize an InstrumentationBaseTest

        Args:
            configs: Dict representing the test configuration
        """
        super().__init__(configs)
        # Take power config path directly from ACTS config if found, otherwise
        # try to find the power config in the same directory as the ACTS config
        power_config_path = ''
        if 'power_config' in self.user_params:
            power_config_path = self.user_params['power_config']
        elif Config.key_config_path.value in self.user_params:
            power_config_path = os.path.join(
                self.user_params[Config.key_config_path.value],
                DEFAULT_POWER_CONFIG_FILE)
        self._power_config = None
        if os.path.exists(power_config_path):
            self._power_config = self._load_power_config(power_config_path)
        else:
            self.log.warning(
                'Power config file %s does not exist' % power_config_path)

    def _load_power_config(self, path):
        """Load the power config file into a InstrumentationConfigWrapper
        object.

        Args:
            path: Path to the power config file.

        Returns: The loaded power config as an InstrumentationConfigWrapper
        """
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        except Exception as e:
            raise InstrumentationTestError(
                'Cannot open or parse power config file %s' % path) from e
        if not self._resolve_file_paths(config_dict):
            self.log.warning('File paths missing from power config.')

        # Write out a copy of the resolved power config
        with open(os.path.join(self.log_path, 'resolved_power_config.yaml'),
                  mode='w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f)

        return config_wrapper.ConfigWrapper(config_dict)

    def _resolve_file_paths(self, config):
        """Recursively resolve all 'FILE' markers found in the power config to
        their corresponding paths in the ACTS config, i.e. in self.user_params.

        Args:
            config: The power config to update

        Returns: True if all 'FILE' markers are resolved.
        """
        success = True
        for key, value in config.items():
            # Recursive call; resolve files in nested maps
            if isinstance(value, dict):
                success &= self._resolve_file_paths(value)
            # Replace file resolver markers with paths from ACTS config
            elif value == RESOLVE_FILE_MARKER:
                if key not in self.user_params:
                    success = False
                    config[key] = FILE_NOT_FOUND
                else:
                    config[key] = self.user_params[key]
        return success

    def _prepare_device(self):
        """Prepares the device for testing."""
        pass

    def setup_class(self):
        """Class setup"""
        self.ad_dut = self.android_devices[0]
        self.ad_apps = app_installer.AppInstaller(self.ad_dut)
        self._prepare_device()

    def adb_run(self, cmds, non_blocking=False):
        """Run the specified command, or list of commands, with the ADB shell.

        Args:
            cmds: A string or list of strings representing ADB shell command(s)
            non_blocking: Run asynchronously
        """
        if isinstance(cmds, str):
            cmds = [cmds]
        adb = self.ad_dut.adb
        adb_shell = adb.shell_nb if non_blocking else adb.shell
        for cmd in cmds:
            adb_shell(cmd)

    # Basic preparer methods

    def enable_airplane_mode(self):
        """Run the set of commands to properly enable airplane mode."""
        self.adb_run(common.airplane_mode.toggle(True))
        self.adb_run(common.auto_time.toggle(False))
        self.adb_run(common.auto_timezone.toggle(False))
        self.adb_run(common.location_gps.toggle(False))
        self.adb_run(common.location_network.toggle(False))
        self.adb_run(common.wifi.toggle(False))
        self.adb_run(common.bluetooth.toggle(False))

    def grant_permissions(self, permissions_apk_path):
        """Grant all runtime permissions with PermissionUtils.

        Args:
            permissions_apk_path: Path to PermissionUtils.apk
        """
        self.log.info('Granting all revoked runtime permissions.')

        # Install PermissionUtils.apk
        self.ad_apps.install(permissions_apk_path)
        if not self.ad_apps.is_installed(permissions_apk_path):
            raise InstrumentationTestError(
                'Failed to install PermissionUtils.apk, abort!')
        package_name = self.ad_apps.get_package_name(permissions_apk_path)

        # Run the instrumentation command
        cmd_builder = InstrumentationCommandBuilder()
        cmd_builder.set_manifest_package(package_name)
        cmd_builder.set_runner('.PermissionInstrumentation')
        cmd_builder.add_flag('-w')
        cmd_builder.add_flag('-r')
        cmd_builder.add_key_value_param('command', 'grant-all')
        cmd = cmd_builder.build()
        self.log.debug('Instrumentation call: %s' % cmd)
        self.adb_run(cmd)

        # Uninstall PermissionUtils.apk
        self.ad_apps.uninstall(permissions_apk_path)
