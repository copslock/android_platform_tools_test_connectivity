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
    default_timeout = 10

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)

    def setup_class(self):
        return setup_multiple_devices_for_bt_test(self.android_devices)

    def setup_test(self):
        return reset_bluetooth(self.android_devices)

    def setup_test(self):
        setup_result = reset_bluetooth(self.android_devices)
        self.log.debug(log_energy_info(self.android_devices, "Start"))
        for a in self.android_devices:
            a.ed.clear_all_events()
        return setup_result

    def teardown_test(self):
        self.log.debug(log_energy_info(self.android_devices, "End"))
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
        n = 0
        test_result = True
        test_result_list = []
        while n < 100:
            self.log.info("Toggling bluetooth iteration {}.".format(n))
            test_result = reset_bluetooth([self.android_devices[0]])
            test_result_list.append(test_result)
            n += 1
        if False in test_result_list:
            return False
        return test_result
