#!/usr/bin/env python
#
#   Copyright 2017 - The Android Open Source Project
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

import os

from metrics.metric import Metric


class AdbHashMetric(Metric):
    """Gathers metrics on environment variable and a hash of that directory.

    This class will verify that $ADB_VENDOR_KEYS is in the environment variables,
    return True or False, and then verify that the hash of that directory
    matches the 'golden' directory.
    """

    def _verify_env(self):
        """Verifies that the $ADB_VENDOR_KEYS variable is set.

        Returns:
            True if the env variable is set, False otherwise.
        """
        return 'ADB_VENDOR_KEYS' in os.environ

    def _find_hash(self):
        """Determines the hash of keys in $ADB_VENDOR_KEYS folder.

        As of now, it just gets the hash, and returns it.

        Returns:
            The hash of the $ADB_VENDOR_KEYS directory excluding hidden files.
        """
        return self._shell.run(
            'find $ADB_VENDOR_KEYS -not -path \'*/\.*\' -type f -exec md5sum {}'
            ' + | awk \'{print $1}\' | sort | md5sum').stdout.split(' ')[0]

    def gather_metric(self):
        """Gathers data on adb keys environment variable, and the hash of the dir

        Returns:
            A dictionary with 'env' set to True or False, and key 'hash' with an
            md5sum as value.
        """
        return {'env': self._verify_env(), 'hash': self._find_hash()}
