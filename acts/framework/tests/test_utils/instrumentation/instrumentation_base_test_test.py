#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

import copy
import unittest

from acts.test_utils.instrumentation.instrumentation_base_test import \
    InstrumentationBaseTest

MOCK_POWER_CONFIG = {
    'not_file': 'NOT_FILE',
    'file1': 'FILE',
    'lvl1': {
        'file2': 'FILE',
        'lvl2': {'file1': 'FILE'}
    }
}

MOCK_ACTS_USERPARAMS = {
    'file1': '/path/to/file1',
    'file2': '/path/to/file2'
}


class MockInstrumentationBaseTest(InstrumentationBaseTest):
    """Mock test class to initialize required attributes."""
    def __init__(self):
        self.user_params = MOCK_ACTS_USERPARAMS


class InstrumentationBaseTestTest(unittest.TestCase):
    def setUp(self):
        self.instrumentation_test = MockInstrumentationBaseTest()

    def test_resolve_files_from_config(self):
        """Test that params with the 'FILE' marker are properly substituted
        with the corresponding paths from ACTS user_params.
        """
        mock_config = copy.deepcopy(MOCK_POWER_CONFIG)
        self.instrumentation_test._resolve_file_paths(mock_config)
        self.assertEqual(mock_config['not_file'], MOCK_POWER_CONFIG['not_file'])
        self.assertEqual(mock_config['file1'], MOCK_ACTS_USERPARAMS['file1'])
        self.assertEqual(mock_config['lvl1']['file2'],
                         MOCK_ACTS_USERPARAMS['file2'])
        self.assertEqual(mock_config['lvl1']['lvl2']['file1'],
                         MOCK_ACTS_USERPARAMS['file1'])


if __name__ == '__main__':
    unittest.main()
