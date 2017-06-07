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

from metrics import ram_metric
from tests import fake


class RamMetricTest(unittest.TestCase):
    """Class for testing RamMetric."""

    def setUp(self):
        pass

    def test_correct_ram_output(self):
        # Create sample stdout string ShellCommand.run() would return
        stdout_string = ('             total       used       free     shared'
                         'buffers     cached\nMem:      65894480   35218588   '
                         '30675892     309024    1779900   24321888\n-/+ '
                         'buffers/cache:    9116800   56777680\nSwap:     '
                         '67031036          0   67031036')

        FAKE_RESULT = fake.FakeResult(stdout=stdout_string)
        fake_shell = fake.MockShellCommand(fake_result=FAKE_RESULT)
        metric_obj = ram_metric.RamMetric(shell=fake_shell)

        expected_result = {
            ram_metric.RamMetric.TOTAL: 65894480,
            ram_metric.RamMetric.USED: 35218588,
            ram_metric.RamMetric.FREE: 30675892,
            ram_metric.RamMetric.BUFFERS: 1779900,
            ram_metric.RamMetric.CACHED: 24321888
        }
        self.assertEqual(expected_result, metric_obj.gather_metric())


if __name__ == '__main__':
    unittest.main()
