#!/usr/bin/env python
#
#   copyright 2017 - the android open source project
#
#   licensed under the apache license, version 2.0 (the "license");
#   you may not use this file except in compliance with the license.
#   you may obtain a copy of the license at
#
#       http://www.apache.org/licenses/license-2.0
#
#   unless required by applicable law or agreed to in writing, software
#   distributed under the license is distributed on an "as is" basis,
#   without warranties or conditions of any kind, either express or implied.
#   see the license for the specific language governing permissions and
#   limitations under the license.

import unittest

from metrics import adb_hash_metric
import mock


class HashMetricTest(unittest.TestCase):
    @mock.patch('os.environ', {'ADB_VENDOR_KEYS': '/root/adb/'})
    def test_verify_env_set(self):
        self.assertEquals(adb_hash_metric.AdbHashMetric()._verify_env(), True)

    @mock.patch('os.environ', {})
    def test_verify_env_not_set(self):
        self.assertEquals(adb_hash_metric.AdbHashMetric()._verify_env(), False)


if __name__ == '__main__':
    unittest.main()
