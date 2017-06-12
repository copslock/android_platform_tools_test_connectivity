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

import time

from acts import asserts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class ProtocolsTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware data-paths: validating protocols running on
  top of a data-path"""

  SERVICE_NAME = "GoogleTestServiceXY"

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def run_ping6(self, dut, peer_ipv6, dut_if):
    """Run a ping6 over the specified device/link

    Args:
      dut: Device on which to execute ping6
      peer_ipv6: IPv6 address of the peer to ping
      dut_if: interface name on the dut
    """
    cmd = "ping6 -c 3 -W 5 %s%%%s" % (peer_ipv6, dut_if)
    results = dut.adb.shell(cmd)
    self.log.info("cmd='%s' -> '%s'", cmd, results)
    if results == "":
      asserts.fail("ping6 empty results - seems like a failure")

  ########################################################################

  def test_ping6_oob(self):
    """Validate that ping6 works correctly on an NDP created using OOB (out-of
    band) discovery"""
    init_dut = self.android_devices[0]
    resp_dut = self.android_devices[1]

    # create NDP
    (init_req_key, resp_req_key, init_aware_if, resp_aware_if, init_ipv6,
     resp_ipv6) = autils.create_oob_ndp(init_dut, resp_dut)
    self.log.info("Interface names: I=%s, R=%s", init_aware_if, resp_aware_if)
    self.log.info("Interface addresses (IPv6): I=%s, R=%s", init_ipv6,
                  resp_ipv6)

    # run ping6
    self.run_ping6(init_dut, resp_ipv6, init_aware_if)
    self.run_ping6(resp_dut, init_ipv6, resp_aware_if)

    # clean-up
    resp_dut.droid.connectivityUnregisterNetworkCallback(resp_req_key)
    init_dut.droid.connectivityUnregisterNetworkCallback(init_req_key)

  def test_ping6_ib_unsolicited_passive(self):
    """Validate that ping6 works correctly on an NDP created using Aware
    discovery with UNSOLICITED/PASSIVE sessions."""
    p_dut = self.android_devices[0]
    s_dut = self.android_devices[1]

    # create NDP
    (p_req_key, s_req_key, p_aware_if, s_aware_if, p_ipv6,
     s_ipv6) = autils.create_ib_ndp(
         p_dut,
         s_dut,
         p_config=autils.create_discovery_config(
             self.SERVICE_NAME, aconsts.PUBLISH_TYPE_UNSOLICITED),
         s_config=autils.create_discovery_config(
             self.SERVICE_NAME, aconsts.SUBSCRIBE_TYPE_PASSIVE))
    self.log.info("Interface names: P=%s, S=%s", p_aware_if, s_aware_if)
    self.log.info("Interface addresses (IPv6): P=%s, S=%s", p_ipv6, s_ipv6)

    # run ping6
    self.run_ping6(p_dut, s_ipv6, p_aware_if)
    self.run_ping6(s_dut, p_ipv6, s_aware_if)

    # clean-up
    p_dut.droid.connectivityUnregisterNetworkCallback(p_req_key)
    s_dut.droid.connectivityUnregisterNetworkCallback(s_req_key)

  def test_ping6_ib_solicited_active(self):
    """Validate that ping6 works correctly on an NDP created using Aware
    discovery with SOLICITED/ACTIVE sessions."""
    p_dut = self.android_devices[0]
    s_dut = self.android_devices[1]

    # create NDP
    (p_req_key, s_req_key, p_aware_if, s_aware_if, p_ipv6,
     s_ipv6) = autils.create_ib_ndp(
        p_dut,
        s_dut,
        p_config=autils.create_discovery_config(
            self.SERVICE_NAME, aconsts.PUBLISH_TYPE_SOLICITED),
        s_config=autils.create_discovery_config(
            self.SERVICE_NAME, aconsts.SUBSCRIBE_TYPE_ACTIVE))
    self.log.info("Interface names: P=%s, S=%s", p_aware_if, s_aware_if)
    self.log.info("Interface addresses (IPv6): P=%s, S=%s", p_ipv6, s_ipv6)

    # run ping6
    self.run_ping6(p_dut, s_ipv6, p_aware_if)
    self.run_ping6(s_dut, p_ipv6, s_aware_if)

    # clean-up
    p_dut.droid.connectivityUnregisterNetworkCallback(p_req_key)
    s_dut.droid.connectivityUnregisterNetworkCallback(s_req_key)
