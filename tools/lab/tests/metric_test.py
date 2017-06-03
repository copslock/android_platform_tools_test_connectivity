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

from metrics import disk_metric


class FakeResult(object):
    """A fake version of the object returned from ShellCommand.run. """

    def __init__(self, exit_status=1, stdout='', stderr=''):
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr


class MockShellCommand(object):
    """A fake ShellCommand object.

    Attributes:
        fake_result: a FakeResult object
    """

    def __init__(self, fake_result):
        self._fake_result = fake_result

    """Returns a FakeResult object.

    Args:
        Same as ShellCommand.run, but none are used in function

    Returns:
        The FakeResult object it was initalized with
    """

    def run(self, command, timeout=3600):
        return self._fake_result


class DiskMetricTest(unittest.TestCase):
    """Class for testing DiskMetric."""

    def setUp(self):
        pass

    def test_return_total_used_avail_percent(self):
        # Create sample stdout string ShellCommand.run() would return
        stdout_string = ('Filesystem     1K-blocks     Used Available Use% '
                         'mounted on\n/dev/dm-1       57542652 18358676 '
                         '36237928  34% /')
        self.FAKE_RESULT = FakeResult(stdout=stdout_string)
        fake_shell = MockShellCommand(fake_result=self.FAKE_RESULT)
        self.metric_obj = disk_metric.DiskMetric(shell=fake_shell)

        expected_result = {
            disk_metric.DiskMetric.TOTAL: 57542652,
            disk_metric.DiskMetric.USED: 18358676,
            disk_metric.DiskMetric.AVAIL: 36237928,
            disk_metric.DiskMetric.PERCENT_USED: 34
        }
        self.assertEqual(expected_result, self.metric_obj.gather_metric())


if __name__ == '__main__':
    unittest.main()
