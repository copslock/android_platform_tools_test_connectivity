#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import unittest

import mock
from acts.test_utils.instrumentation import instrumentation_proto_parser \
    as parser
from acts.test_utils.instrumentation.proto.gen import instrumentation_data_pb2


DEST_DIR = 'dest/proto_dir'
SOURCE_PATH = 'source/proto/protofile'
SAMPLE_PROTO = 'data/sample.instrumentation_data_proto'


class InstrumentationProtoParserTest(unittest.TestCase):
    """Unit tests for instrumentation proto parser."""

    def setUp(self):
        self.ad = mock.MagicMock()

    @mock.patch('os.path.exists', return_value=True)
    def test_pull_proto_returns_correct_path_given_source(self, *_):
        self.assertEqual(parser.pull_proto(self.ad, DEST_DIR, SOURCE_PATH),
                         'dest/proto_dir/protofile')

    @mock.patch('os.path.exists', return_value=True)
    def test_pull_proto_returns_correct_path_from_default_location(self, *_):
        self.ad.adb.shell.side_effect = ['', 'default']
        self.assertEqual(parser.pull_proto(self.ad, DEST_DIR),
                         'dest/proto_dir/default')

    def test_pull_proto_fails_if_no_default_proto_found(self, *_):
        self.ad.adb.shell.side_effect = ['', None]
        pulled_proto = parser.pull_proto(self.ad, DEST_DIR)
        self.assertIn('No instrumentation result',
                      self.ad.log.warning.call_args[0][0])
        self.assertEqual(pulled_proto, '')

    @mock.patch('os.path.exists', return_value=False)
    def test_pull_proto_fails_if_adb_pull_fails(self, *_):
        pulled_proto = parser.pull_proto(self.ad, DEST_DIR, SOURCE_PATH)
        self.assertIn('Failed to pull', self.ad.log.warning.call_args[0][0])
        self.assertEqual(pulled_proto, '')

    def test_parser_converts_valid_proto(self):
        proto_file = os.path.join(os.path.dirname(__file__), SAMPLE_PROTO)
        self.assertIsInstance(parser.get_session_from_local_file(proto_file),
                              instrumentation_data_pb2.Session)


if __name__ == '__main__':
    unittest.main()
