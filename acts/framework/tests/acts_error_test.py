#!/usr/bin/env python3
#
# Copyright 2018 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest

from acts import error


class ActsErrorTest(unittest.TestCase):
    def test_error_without_args(self):
        e = error.ActsError()
        self.assertEqual(e.error_code, 100)
        self.assertEqual(e.message, 'Base Acts Error')
        self.assertEqual(e.extra, ())

    def test_error_with_args(self):
        args = 'hello'
        e = error.ActsError(args)
        self.assertEqual(e.error_code, 100)
        self.assertEqual(e.message, 'Base Acts Error')
        self.assertEqual(e.extra, ('hello',))


if __name__ == '__main__':
    unittest.main()
