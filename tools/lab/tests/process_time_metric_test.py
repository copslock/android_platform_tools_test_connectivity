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
        fake_result = [
            fake.FakeResult(stdout='1037453 command'),
            fake.FakeResult(stdout='1234 other command')
        ]
        fake_pids = {'adb': ['123'], 'fastboot': ['456']}
        fake_shell = fake.MockShellCommand(
            fake_pids=fake_pids, fake_result=fake_result)
        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        expected_result = {
            process_time_metric.ProcessTimeMetric.PID_TIMES: [(1037453, '123'),
                                                              (1234, '456')]
        }

        self.assertEqual(metric_obj.gather_metric(), expected_result)

    def test_gather_metric_returns_times_no_forkserver(self):
        fake_result = [
            fake.FakeResult(stdout='1037453 command'),
            fake.FakeResult(stdout='1234 other command'),
            fake.FakeResult(stdout='9998 fork-server adb')
        ]
        fake_pids = {'adb': ['123'], 'fastboot': ['456', '789']}
        fake_shell = fake.MockShellCommand(
            fake_pids=fake_pids, fake_result=fake_result)
        metric_obj = process_time_metric.ProcessTimeMetric(shell=fake_shell)
        expected_result = {
            process_time_metric.ProcessTimeMetric.PID_TIMES: [(1037453, '123'),
                                                              (1234, '456')]
        }

        self.assertEqual(metric_obj.gather_metric(), expected_result)


if __name__ == '__main__':
    unittest.main()
