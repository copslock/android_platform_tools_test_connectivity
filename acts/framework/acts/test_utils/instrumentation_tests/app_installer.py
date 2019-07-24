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

import re

from acts.libs.proc import job

PKG_NAME_PATTERN = r"^package:\s+name='(?P<pkg_name>.*?)'"


class AppInstaller(object):
    """Class for installing apps on an Android device."""
    def __init__(self, device):
        self.ad = device
        self._pkgs = {}

    def install(self, apk_path, *extra_args):
        """Installs an apk on the device.

        Args:
            apk_path: Path to the apk to install
            extra_args: Additional flags to the ADB install command.
                Note that '-r' is included by default.
        """
        self.ad.log.info('Installing app %s' % apk_path)
        self.ad.ensure_screen_on()
        args = '-r %s' % ' '.join(extra_args)
        self.ad.adb.install('%s %s' % (args, apk_path))

    def uninstall(self, apk_path, *extra_args):
        """Finds the package corresponding to the apk and uninstalls it from the
        device.

        Args:
            apk_path: Path to the apk
            extra_args: Additional flags to the uninstall command.
        """
        if self.is_installed(apk_path):
            pkg_name = self.get_package_name(apk_path)
            self.ad.log.info('Uninstalling app %s' % pkg_name)
            self.ad.adb.shell(
                'pm uninstall %s %s' % (' '.join(extra_args), pkg_name))

    def is_installed(self, apk_path):
        """Verifies that an apk is installed on the device.

        Args:
            apk_path: Path to the apk

        Returns: True if the apk is installed on the device.
        """
        pkg_name = self.get_package_name(apk_path)
        if not pkg_name:
            self.ad.log.warning('No package name found for %s' % apk_path)
            return False
        return self.ad.is_apk_installed(pkg_name)

    def get_package_name(self, apk_path):
        """Get the package name corresponding to the apk from aapt

        Args:
            apk_path: Path to the apk

        Returns: The package name
        """
        if apk_path not in self._pkgs:
            dump = job.run(
                'aapt dump badging %s' % apk_path, ignore_status=True).stdout
            match = re.compile(PKG_NAME_PATTERN).search(dump)
            self._pkgs[apk_path] = match.group('pkg_name') if match else ''
        return self._pkgs[apk_path]
