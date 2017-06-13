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

from metrics import process_time_metric
from tests import fake
import mock


class ProcessTimeMetricTest(unittest.TestCase):
    def test_get_adb_fastboot_pids_only_adb(self):
        fake_pids = {'adb': ['123', '456', '789'], 'fastboot': []}
        fake_shell = fake.MockShellCommand(fake_pids=fake_pids)
        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        self.assertEqual(metric_obj.get_adb_fastboot_pids(), fake_pids['adb'])

    def test_get_adb_fastboot_pids_only_fastboot(self):
        fake_pids = {'adb': [], 'fastboot': ['123', '456', '789']}
        fake_shell = fake.MockShellCommand(fake_pids=fake_pids)

        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        self.assertEqual(metric_obj.get_adb_fastboot_pids(),
                         fake_pids['fastboot'])

    def test_get_adb_fastboot_pids_both(self):
        fake_pids = {
            'adb': ['987', '654', '321'],
            'fastboot': ['123', '456', '789']
        }
        fake_shell = fake.MockShellCommand(fake_pids=fake_pids)
        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        self.assertEqual(metric_obj.get_adb_fastboot_pids(),
                         fake_pids['adb'] + fake_pids['fastboot'])

    def test_gather_metric_returns_times(self):
        # create list of fake results
        fake_result = [
            fake.FakeResult(stdout='01:46:34'),
            fake.FakeResult(stdout='9-23:43:12')
        ]
        fake_pids = {'adb': ['123'], 'fastboot': ['456']}
        fake_shell = fake.MockShellCommand(
            fake_pids=fake_pids, fake_result=fake_result)
        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        expected_result = {
            process_time_metric.ProcessTimeMetric.PID_TIMES:
            [('01:46:34', '123'), ('9-23:43:12', '456')]
        }

        self.assertEqual(metric_obj.gather_metric(), expected_result)


if __name__ == '__main__':
    unittest.main()
