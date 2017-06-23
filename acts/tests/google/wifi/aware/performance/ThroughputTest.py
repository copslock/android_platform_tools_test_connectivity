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

import json
import pprint
import time

from acts import asserts
from acts.test_utils.net import connectivity_const as cconsts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class ThroughputTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware to measure latency of Aware operations."""

  # number of second to 'reasonably' wait to make sure that devices synchronize
  # with each other - useful for OOB test cases, where the OOB discovery would
  # take some time
  WAIT_FOR_CLUSTER = 5

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def request_network(self, dut, ns):
    """Request a Wi-Fi Aware network.

    Args:
      dut: Device
      ns: Network specifier
    Returns: the request key
    """
    network_req = {"TransportType": 5, "NetworkSpecifier": ns}
    return dut.droid.connectivityRequestWifiAwareNetwork(network_req)

  ########################################################################

  def test_iperf_single_ndp_aware_only(self):
    """Measure iperf performance on a single NDP, with Aware enabled and no
    infrastructure connection - i.e. device is not associated to an AP"""
    init_dut = self.android_devices[0]
    init_dut.pretty_name = "Initiator"
    resp_dut = self.android_devices[1]
    resp_dut.pretty_name = "Responder"

    # Initiator+Responder: attach and wait for confirmation & identity
    init_id = init_dut.droid.wifiAwareAttach(True)
    autils.wait_for_event(init_dut, aconsts.EVENT_CB_ON_ATTACHED)
    init_ident_event = autils.wait_for_event(
        init_dut, aconsts.EVENT_CB_ON_IDENTITY_CHANGED)
    init_mac = init_ident_event["data"]["mac"]
    time.sleep(self.device_startup_offset)
    resp_id = resp_dut.droid.wifiAwareAttach(True)
    autils.wait_for_event(resp_dut, aconsts.EVENT_CB_ON_ATTACHED)
    resp_ident_event = autils.wait_for_event(
        resp_dut, aconsts.EVENT_CB_ON_IDENTITY_CHANGED)
    resp_mac = resp_ident_event["data"]["mac"]

    # wait for for devices to synchronize with each other - there are no other
    # mechanisms to make sure this happens for OOB discovery (except retrying
    # to execute the data-path request)
    time.sleep(self.WAIT_FOR_CLUSTER)

    # Responder: request network
    resp_req_key = self.request_network(
        resp_dut,
        resp_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            resp_id, aconsts.DATA_PATH_RESPONDER, init_mac, None))

    # Initiator: request network
    init_req_key = self.request_network(
        init_dut,
        init_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            init_id, aconsts.DATA_PATH_INITIATOR, resp_mac, None))

    # Initiator & Responder: wait for network formation
    init_net_event = autils.wait_for_event_with_keys(
        init_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_NDP_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LINK_PROPERTIES_CHANGED),
        (cconsts.NETWORK_CB_KEY_ID, init_req_key))
    resp_net_event = autils.wait_for_event_with_keys(
        resp_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_NDP_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LINK_PROPERTIES_CHANGED),
        (cconsts.NETWORK_CB_KEY_ID, resp_req_key))

    init_aware_if = init_net_event["data"][
        cconsts.NETWORK_CB_KEY_INTERFACE_NAME]
    resp_aware_if = resp_net_event["data"][
        cconsts.NETWORK_CB_KEY_INTERFACE_NAME]
    self.log.info("Interface names: I=%s, R=%s", init_aware_if, resp_aware_if)

    init_ipv6 = init_dut.droid.connectivityGetLinkLocalIpv6Address(
        init_aware_if).split("%")[0]
    resp_ipv6 = resp_dut.droid.connectivityGetLinkLocalIpv6Address(
        resp_aware_if).split("%")[0]
    self.log.info("Interface addresses (IPv6): I=%s, R=%s", init_ipv6,
                  resp_ipv6)

    # Run iperf3
    result, data = init_dut.run_iperf_server("-D")
    asserts.assert_true(result, "Can't start iperf3 server")

    result, data = resp_dut.run_iperf_client(
        "%s%%%s" % (init_ipv6, resp_aware_if), "-6 -J")
    self.log.debug(data)
    asserts.assert_true(result,
                        "Failure starting/running iperf3 in client mode")
    self.log.debug(pprint.pformat(data))

    # clean-up
    resp_dut.droid.connectivityUnregisterNetworkCallback(resp_req_key)
    init_dut.droid.connectivityUnregisterNetworkCallback(init_req_key)

    # Collect results
    results = {}
    data_json = json.loads("".join(data))
    results["tx_rate"] = data_json["end"]["sum_sent"]["bits_per_second"]
    results["rx_rate"] = data_json["end"]["sum_received"]["bits_per_second"]
    self.log.info("iPerf3: Sent = %d bps Received = %d bps", results["tx_rate"],
                  results["rx_rate"])
    asserts.explicit_pass("Aware data-path test passes", extras=results)
