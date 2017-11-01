#!/usr/bin/env python3.4
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
import copy
import enum
from acts import config_parser
from acts import keys

NAME = 'name'


class ActsConfigParserTests(unittest.TestCase):
    """Test class for acts.config_parser."""

    original_config = None

    class Config(enum.Enum):
        key_testbed_name = NAME
        user_param_overridable = ['trumpets', 'potato']

    @classmethod
    def setUpClass(cls):
        # Mocks the override keys for unit tests.
        ActsConfigParserTests.original_config = keys.Config
        keys.Config = ActsConfigParserTests.Config

    @classmethod
    def tearDownClass(cls):
        # Restores the original keys after the tests have finished
        keys.Config = ActsConfigParserTests.original_config

    def test_set_config_overrides_override_does_not_exist(self):
        mock_testbed_original = {
            NAME: 'JohnCena',
            'trumpets': 'doot doot doot dooo'
        }
        mock_testbed = copy.deepcopy(mock_testbed_original)
        mock_acts_config = {'testbeds': [mock_testbed]}
        config_parser._set_config_overrides(mock_acts_config, mock_testbed)
        self.assertDictEqual(mock_testbed_original, mock_testbed)

    def test_set_config_overrides_override_exists(self):
        mock_testbed = {NAME: 'JohnCena', 'trumpets': 'doot doot doot dooo'}
        mock_acts_config = {
            'testbeds': [mock_testbed],
            'JohnCena_trumpets': 'meep beep beep beee'
        }
        config_parser._set_config_overrides(mock_acts_config, mock_testbed)
        self.assertEqual(mock_testbed['trumpets'],
                         mock_acts_config['JohnCena_trumpets'])

    def test_set_config_overrides_multiple_overrides(self):
        mock_testbed = {
            NAME: 'JohnCena',
            'trumpets': 'doot doot doot dooo',
            'potato': 'salad'
        }
        mock_acts_config = {
            'testbeds': [mock_testbed],
            'JohnCena_trumpets': 'meep beep beep beee',
            'JohnCena_potato': 'quality'
        }
        config_parser._set_config_overrides(mock_acts_config, mock_testbed)
        self.assertEqual(mock_testbed['trumpets'],
                         mock_acts_config['JohnCena_trumpets'])
        self.assertEqual(mock_testbed['potato'],
                         mock_acts_config['JohnCena_potato'])

    def test_set_config_early_return_no_name(self):
        acts_config = {}
        testbed_config = {}
        config_parser._set_config_overrides(acts_config, testbed_config)
        self.assertDictEqual(testbed_config, {})
