#!/usr/bin/python3.4
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

from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class AttachTest(AwareBaseTest):
  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def test_attach(self):
    """Functional test case / Attach test cases / attach

    Validates that attaching to the Wi-Fi Aware service works (receive
    the expected callback).
    """
    dut = self.android_devices[0]
    dut.droid.wifiAwareAttach()
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)
