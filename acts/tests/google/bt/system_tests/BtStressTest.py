#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
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

"""
Basic Bluetooth Classic stress tests.
"""

from acts.base_test import BaseTestClass
from acts.test_utils.bt.bt_test_utils import log_energy_info
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import setup_multiple_devices_for_bt_test


class BtStressTest(BaseTestClass):
    tests = None
    default_timeout = 10

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_toggle_bluetooth",
        )

    def setup_class(self):
        self.droid1, self.ed1 = self.droids[1], self.eds[1]
        return setup_multiple_devices_for_bt_test(self.droids, self.eds)

    def setup_test(self):
        return reset_bluetooth(self.droids, self.eds)

    def setup_test(self):
        setup_result = reset_bluetooth(self.droids, self.eds)
        self.log.debug(log_energy_info(self.droids, "Start"))
        for e in self.eds:
            e.clear_all_events()
        return setup_result

    def teardown_test(self):
        self.log.debug(log_energy_info(self.droids, "End"))
        return True

    def test_toggle_bluetooth(self):
        """Stress test toggling bluetooth on and off.

        Test the integrity of toggling bluetooth on and off.

        Steps:
        1. Toggle bluetooth off.
        2. Toggle bluetooth on.
        3. Repeat steps 1 and 2 one-hundred times.

        Expected Result:
        Each iteration of toggling bluetooth on and off should not cause an
        exception.

        Returns:
          Pass if True
          Fail if False

        TAGS: Classic, Stress
        Priority: 1
        """
        droid, ed = self.droid, self.ed
        n = 0
        test_result = True
        test_result_list = []
        while n < 100:
            self.log.info("Toggling bluetooth iteration {}.".format(n))
            test_result = reset_bluetooth([droid], [ed])
            test_result_list.append(test_result)
            n += 1
        if False in test_result_list:
            return False
        return test_result
