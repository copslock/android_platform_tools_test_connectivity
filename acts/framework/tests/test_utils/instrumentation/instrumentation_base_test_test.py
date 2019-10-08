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

from acts.test_utils.instrumentation.config_wrapper import ConfigWrapper
from acts.test_utils.instrumentation.instrumentation_base_test import \
    InstrumentationBaseTest

MOCK_INSTRUMENTATION_CONFIG = {
    'not_file': 'NOT_FILE',
    'file1': 'FILE',
    'lvl1': {
        'file2': 'FILE',
        'lvl2': {'file1': 'FILE'}
    },
    'MockController': {
        'param1': 1
    },
    'MockInstrumentationBaseTest': {
        'MockController': {
            'param2': 2
        },
        'test_case': {
            'MockController': {
                'param3': 3
            }
        }
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
        self.current_test_name = None
        self._instrumentation_config = ConfigWrapper(
            MOCK_INSTRUMENTATION_CONFIG)
        self._class_config = self._instrumentation_config.get_config(
            self.__class__.__name__)


class InstrumentationBaseTestTest(unittest.TestCase):
    def setUp(self):
        self.instrumentation_test = MockInstrumentationBaseTest()

    def test_resolve_files_from_config(self):
        """Test that params with the 'FILE' marker are properly substituted
        with the corresponding paths from ACTS user_params.
        """
        mock_config = copy.deepcopy(MOCK_INSTRUMENTATION_CONFIG)
        self.instrumentation_test._resolve_file_paths(mock_config)
        self.assertEqual(mock_config['not_file'],
                         MOCK_INSTRUMENTATION_CONFIG['not_file'])
        self.assertEqual(mock_config['file1'], MOCK_ACTS_USERPARAMS['file1'])
        self.assertEqual(mock_config['lvl1']['file2'],
                         MOCK_ACTS_USERPARAMS['file2'])
        self.assertEqual(mock_config['lvl1']['lvl2']['file1'],
                         MOCK_ACTS_USERPARAMS['file1'])

    def test_get_controller_config_for_test_case(self):
        """Test that _get_controller_config returns the corresponding
        controller config for the current test case.
        """
        self.instrumentation_test.current_test_name = 'test_case'
        config = self.instrumentation_test._get_controller_config(
            'MockController')
        self.assertNotIn('param1', config)
        self.assertNotIn('param2', config)
        self.assertIn('param3', config)

    def test_get_controller_config_for_test_class(self):
        """Test that _get_controller_config returns the controller config for
        the current test class (while no test case is running).
        """
        config = self.instrumentation_test._get_controller_config(
            'MockController')
        self.assertIn('param1', config)
        self.assertIn('param2', config)
        self.assertNotIn('param3', config)


if __name__ == '__main__':
    unittest.main()
