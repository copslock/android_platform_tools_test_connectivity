# python3.4
# Copyright (C) 2014 The Android Open Source Project
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
This script shows simple examples of how to get started with bluetooth low energy testing in acts.
"""

from base_test import BaseTestClass
from test_utils.ble_test_utils import (reset_bluetooth,
                                       setup_multiple_devices_for_bluetooth_test,
                                       take_btsnoop_log)


class BleExamplesTest(BaseTestClass):
  TAG = "BleExamplesTest"
  log_path = "".join([BaseTestClass.log_path,TAG,'/'])
  tests = None
  default_timeout = 10

  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    self.tests = (
      "test_bt_toggle",
    )

  # An optional function. This runs after __init__.
  # It overrides the default setup_class in base_test.
  # Put anything specific here that involves setting
  # up the testcase.
  #def setup_class(self):
  #  self.droid1, self.ed1 = self.android_devices[1].get_droid()
  #  self.ed1.start()
  #  return setup_multiple_devices_for_bluetooth_test(self.android_devices)

  # An optional function. This overrides the default
  # on_exception in base_test. If the test throws an
  # unexpected exception, you can customise it.
  def on_exception(self, test_name, begin_time):
    self.log.debug(" ".join(["Test", test_name, "failed. Gathering bugreport and btsnoop logs"]))
    for ad in self.android_devices:
      self.take_bug_report(test_name, ad)
      take_btsnoop_log(self, test_name, ad)

  # An optional function. This overrides the default
  # on_fail in base_test. If any testcase fails you can
  # customise the result of the failure.
  def on_fail(self, test_name, begin_time):
    reset_bluetooth(self.android_devices)

  def test_bt_toggle(self):
    self.droid.bluetoothConfigHciSnoopLog(True)
    take_btsnoop_log(self, "test_bt_toggle", self.android_devices[0])
    return reset_bluetooth([self.android_devices[0]])
