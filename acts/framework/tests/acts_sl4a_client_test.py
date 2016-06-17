#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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


__author__ = 'angli@google.com (Ang Li)'


from builtins import str

import json
import mock
import socket
import unittest

from acts.controllers import android

MOCK_RESP = b'{"id": 0, "result": 123, "error": null, "status": 1, "uid": 1}'
MOCK_RESP_TEMPLATE = '{"id": %d, "result": 123, "error": null, "status": 1, "uid": 1}'


class MockSocketFile(object):
    def __init__(self):
        self._id = 0
        self.resp = MOCK_RESP_TEMPLATE % self._id

    def write(self, msg):
        j_msg = json.loads(str(msg, encoding='utf-8').strip())
        if "id" in j_msg:
            self._id = j_msg["id"]
        self.resp = MOCK_RESP_TEMPLATE % self._id

    def readline(self):
        return self.resp.encode("utf-8")

    def flush(self):
        pass


class ActsSl4aClientTest(unittest.TestCase):
    """This test class has unit tests for the implementation of everything
    under acts.controllers.android, which is the RPC client module for sl4a.
    """

    @mock.patch('socket.create_connection')
    @mock.patch('acts.controllers.android.Android._cmd',
                return_value=MOCK_RESP)
    def test_counter(self, mock_cmd, mock_socket_conn):
        droid = android.Android()
        droid.client = MockSocketFile()
        for i in range(10):
            droid.some_call()
        self.assertEqual(next(droid._counter), 10)


if __name__ == "__main__":
    unittest.main()
