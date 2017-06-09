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

from metrics import zombie_metric
from tests import fake


class ZombieMetricTest(unittest.TestCase):
    """Class for testing ZombieMetric."""

    def test_return_one_process(self):
        stdout_string = '30888 Z+ adb <defunct>'
        FAKE_RESULT = fake.FakeResult(stdout=stdout_string)
        fake_shell = fake.MockShellCommand(fake_result=FAKE_RESULT)
        metric_obj = zombie_metric.ZombieMetric(shell=fake_shell)

        expected_result = {
            zombie_metric.ZombieMetric.ADB_ZOMBIES: [(30888, 'Z+',
                                                      'adb <defunct>')],
            zombie_metric.ZombieMetric.FASTBOOT_ZOMBIES: [],
            zombie_metric.ZombieMetric.OTHER_ZOMBIES: []
        }
        self.assertEqual(expected_result, metric_obj.gather_metric())

    def test_return_one_of_each(self):
        stdout_string = ('30888 Z+ adb <defunct>\n'
                         '12345 Z+ fastboot\n'
                         '99999 Z+ random\n')
        FAKE_RESULT = fake.FakeResult(stdout=stdout_string)
        fake_shell = fake.MockShellCommand(fake_result=FAKE_RESULT)
        metric_obj = zombie_metric.ZombieMetric(shell=fake_shell)

        expected_result = {
            zombie_metric.ZombieMetric.ADB_ZOMBIES: [(30888, 'Z+',
                                                      'adb <defunct>')],
            zombie_metric.ZombieMetric.FASTBOOT_ZOMBIES: [(12345, 'Z+',
                                                           'fastboot')],
            zombie_metric.ZombieMetric.OTHER_ZOMBIES: [(99999, 'Z+', 'random')]
        }


if __name__ == '__main__':
    unittest.main()
