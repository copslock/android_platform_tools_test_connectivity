#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
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
from distutils.version import LooseVersion
import unittest

from acts.controllers.android_lib import android_api


class LogcatTest(unittest.TestCase):
    """Tests acts.controllers.android_lib.android_api"""

    def test_android_platform_definitions_in_ascending_order(self):
        cur = LooseVersion('0')
        for e in android_api.AndroidPlatform:
            msg = 'AndroidPlatform enums must be defined in ascending order.'
            self.assertGreaterEqual(e.value, cur, msg)
            cur = e.value


if __name__ == '__main__':
    unittest.main()
