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

from metrics import uptime_metric
from tests import fake


class UptimeMetricTest(unittest.TestCase):
    """Class for testing UptimeMetric."""

    def setUp(self):
        pass

    def test_correct_uptime(self):
        # Create sample stdout string ShellCommand.run() would return
        stdout_string = "358350.70 14241538.06"
        FAKE_RESULT = fake.FakeResult(stdout=stdout_string)
        fake_shell = fake.MockShellCommand(fake_result=FAKE_RESULT)
        metric_obj = uptime_metric.UptimeMetric(shell=fake_shell)

        expected_result = {
            uptime_metric.UptimeMetric.TIME_SECONDS: 358350.70,
        }
        self.assertEqual(expected_result, metric_obj.gather_metric())


if __name__ == '__main__':
    unittest.main()
