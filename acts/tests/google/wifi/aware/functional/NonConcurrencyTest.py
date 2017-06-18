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

from acts import asserts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class NonConcurrencyTest(AwareBaseTest):
  """Tests lack of concurrency scenarios Wi-Fi Aware with WFD (p2p) and
  SoftAP

  Note: these tests should be modified if the concurrency behavior changes!"""

  SERVICE_NAME = "GoogleTestXYZ"

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  ##########################################################################

  def test_run_p2p_then_aware(self):
    """Validate that if p2p is already up then any Aware operation fails"""
    dut = self.android_devices[0]

    # start p2p
    dut.droid.wifiP2pInitialize()

    # expect an announcement about Aware non-availability
    autils.wait_for_event(dut, aconsts.BROADCAST_WIFI_AWARE_NOT_AVAILABLE)

    # try starting anyway (expect failure)
    dut.droid.wifiAwareAttach()
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACH_FAILED)

    # close p2p
    dut.droid.wifiP2pClose()

    # expect an announcement about Aware availability
    autils.wait_for_event(dut, aconsts.BROADCAST_WIFI_AWARE_AVAILABLE)

    # try starting Aware
    dut.droid.wifiAwareAttach()
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)

  def test_run_aware_then_p2p(self):
    """Validate that a running Aware session terminates when p2p is started"""
    dut = self.android_devices[0]

    # start Aware
    id = dut.droid.wifiAwareAttach()
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)

    # start p2p
    dut.droid.wifiP2pInitialize()

    # expect an announcement about Aware non-availability
    autils.wait_for_event(dut, aconsts.BROADCAST_WIFI_AWARE_NOT_AVAILABLE)
