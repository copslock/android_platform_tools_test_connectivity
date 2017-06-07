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

import DataPathTest
import time

from acts import asserts
from acts.test_utils.net import connectivity_const as cconsts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class MacRandomTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware MAC address randomization of NMI (NAN
  management interface) and NDI (NAN data interface)."""

  NUM_ITERATIONS = 10

  # number of second to 'reasonably' wait to make sure that devices synchronize
  # with each other - useful for OOB test cases, where the OOB discovery would
  # take some time
  WAIT_FOR_CLUSTER = 5

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  ##########################################################################

  def test_nmi_randomization_on_enable(self):
    """Validate randomization of the NMI (NAN management interface) on each
    enable/disable cycle"""
    dut = self.android_devices[0]

    # DUT: attach and wait for confirmation & identity 10 times
    mac_addresses = {}
    for i in range(self.NUM_ITERATIONS):
      id = dut.droid.wifiAwareAttach(True)
      autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)
      ident_event = autils.wait_for_event(dut,
                                          aconsts.EVENT_CB_ON_IDENTITY_CHANGED)
      mac = ident_event["data"]["mac"]
      if mac in mac_addresses:
        mac_addresses[mac] = mac_addresses[mac] + 1
      else:
        mac_addresses[mac] = 1
      dut.droid.wifiAwareDestroy(id)

    # Test for uniqueness
    for mac in mac_addresses.keys():
      if mac_addresses[mac] != 1:
        asserts.fail("Mac address %s repeated %d times (all=%s)" % (mac,
                     mac_addresses[mac], mac_addresses))
