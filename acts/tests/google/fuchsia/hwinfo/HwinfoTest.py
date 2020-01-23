#!/usr/bin/env python3
#
# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from acts import signals
from acts.base_test import BaseTestClass
from acts import asserts


class HwinfoTest(BaseTestClass):
    def setup_class(self):
        super().setup_class()
        self.dut = self.fuchsia_devices[0]
        self.dut.hwinfo_lib.init()

    def test_get_info(self):
        """Verify that getting the hardware information of a Fuchsia
        device does not return an error.

        Steps:
        1. Get the hardware info of a Fuchsia device.

        Expected Result:
        No errors in getting the hardware info.

        Returns:
          signals.TestPass if no errors
          signals.TestFailure if there are any errors during the test.

        TAGS: Hardware
        Priority: 2
        """
        result = self.dut.hwinfo_lib.getInfo()
        if result.get("error") is None:
            self.log.info("HW info found: {}".format(result))
            signals.TestPass(result.get("result"))
        else:
            signals.TestFailure(result.get("error"))
