#!/usr/bin/python3.4
#
#   Copyright 2015 - The Android Open Source Project
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

import json
import os

from acts.base_test import BaseTestClass

class ActsBaseClassSetupClassTest(BaseTestClass):
    """This class tests aborting test class by causing a failure in
    setup_class.

    When implementation is correct, no test case in this class should be
    executed.
    """

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_never",
        )

    def setup_class(self):
        self.fail("Fail setup_class to abort this test", extras=42)

    def test_never(self):
        self.log.error("This test should never happen.")
        self.assert_true(False, "BAD!!")
