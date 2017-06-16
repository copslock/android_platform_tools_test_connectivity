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

  def request_network(self, dut, ns):
    """Request a Wi-Fi Aware network.

    Args:
      dut: Device
      ns: Network specifier
    Returns: the request key
    """
    network_req = {"TransportType": 5, "NetworkSpecifier": ns}
    return dut.droid.connectivityRequestWifiAwareNetwork(network_req)


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
        asserts.fail("MAC address %s repeated %d times (all=%s)" % (mac,
                     mac_addresses[mac], mac_addresses))

    # Verify that infra interface (e.g. wlan0) MAC address is not used for NMI
    infra_mac = autils.get_wifi_mac_address(dut)
    asserts.assert_false(
        infra_mac in mac_addresses,
        "Infrastructure MAC address (%s) is used for Aware NMI (all=%s)" %
        (infra_mac, mac_addresses))

  def test_nmi_randomization_on_interval(self):
    """Validate randomization of the NMI (NAN management interface) on a set
    interval. Default value is 30 minutes - change to a small value to allow
    testing in real-time"""
    RANDOM_INTERVAL = 120 # minimal value in current implementation

    dut = self.android_devices[0]

    # set randomization interval to 5 seconds
    dut.adb.shell("cmd wifiaware native_api set mac_random_interval_sec %d" %
                  RANDOM_INTERVAL)

    # attach and wait for first identity
    id = dut.droid.wifiAwareAttach(True)
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)
    ident_event = autils.wait_for_event(dut,
                                        aconsts.EVENT_CB_ON_IDENTITY_CHANGED)
    mac1 = ident_event["data"]["mac"]

    # wait for second identity callback
    # Note: exact randomization interval is not critical, just approximate,
    # hence giving a few more seconds.
    ident_event = autils.wait_for_event(dut,
                                        aconsts.EVENT_CB_ON_IDENTITY_CHANGED,
                                        timeout=RANDOM_INTERVAL + 5)
    mac2 = ident_event["data"]["mac"]

    # validate MAC address is randomized
    asserts.assert_false(
        mac1 == mac2,
        "Randomized MAC addresses (%s, %s) should be different" % (mac1, mac2))

    # clean-up
    dut.droid.wifiAwareDestroy(id)

  def test_ndi_randomization_on_enable(self):
    """Validate randomization of the NDI (NAN data interface) on each
    enable/disable cycle

    Notes:
      1. Currently assumes a single NDI in the system (doesn't try to force
         each NDP on a particular NDI).
      2. There's no API to obtain the actual NDI MAC address. However, the IPv6
         is obtainable and is a good proxy for the MAC since it is link-local
         (i.e. most likely uses the bits of the MAC address).
    """
    init_dut = self.android_devices[0]
    init_dut.pretty_name = "Initiator"
    resp_dut = self.android_devices[1]
    resp_dut.pretty_name = "Responder"

    init_ipv6_addresses = {}
    resp_ipv6_addresses = {}
    for i in range(self.NUM_ITERATIONS):
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
          init_dut, cconsts.EVENT_NETWORK_CALLBACK,
          autils.EVENT_TIMEOUT,
          (cconsts.NETWORK_CB_KEY_EVENT,
           cconsts.NETWORK_CB_LINK_PROPERTIES_CHANGED),
          (cconsts.NETWORK_CB_KEY_ID, init_req_key))
      resp_net_event = autils.wait_for_event_with_keys(
          resp_dut, cconsts.EVENT_NETWORK_CALLBACK,
          autils.EVENT_TIMEOUT,
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

      if init_ipv6 in init_ipv6_addresses:
        init_ipv6_addresses[init_ipv6] = init_ipv6_addresses[init_ipv6] + 1
      else:
        init_ipv6_addresses[init_ipv6] = 1
      if resp_ipv6 in resp_ipv6_addresses:
        resp_ipv6_addresses[resp_ipv6] = resp_ipv6_addresses[resp_ipv6] + 1
      else:
        resp_ipv6_addresses[resp_ipv6] = 1

      # terminate sessions and wait for ON_LOST callbacks
      init_dut.droid.wifiAwareDestroy(init_id)
      resp_dut.droid.wifiAwareDestroy(resp_id)

      autils.wait_for_event_with_keys(
          init_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_TIMEOUT,
          (cconsts.NETWORK_CB_KEY_EVENT,
           cconsts.NETWORK_CB_LOST), (cconsts.NETWORK_CB_KEY_ID, init_req_key))
      autils.wait_for_event_with_keys(
          resp_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_TIMEOUT,
          (cconsts.NETWORK_CB_KEY_EVENT,
           cconsts.NETWORK_CB_LOST), (cconsts.NETWORK_CB_KEY_ID, resp_req_key))

      # clean-up
      resp_dut.droid.connectivityUnregisterNetworkCallback(resp_req_key)
      init_dut.droid.connectivityUnregisterNetworkCallback(init_req_key)

    # Test for uniqueness
    for ipv6 in init_ipv6_addresses.keys():
      if init_ipv6_addresses[ipv6] != 1:
        asserts.fail("IPv6 of Initiator's NDI %s repeated %d times (all=%s)" %
                     (ipv6, init_ipv6_addresses[ipv6], init_ipv6_addresses))
    for ipv6 in resp_ipv6_addresses.keys():
      if resp_ipv6_addresses[ipv6] != 1:
        asserts.fail("IPv6 of Responders's NDI %s repeated %d times (all=%s)" %
                     (ipv6, resp_ipv6_addresses[ipv6], resp_ipv6_addresses))
