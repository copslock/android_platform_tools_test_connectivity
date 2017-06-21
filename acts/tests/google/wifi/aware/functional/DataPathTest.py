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

from acts.test_utils.net import connectivity_const as cconsts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class DataPathTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware data-path."""

  # configuration parameters used by tests
  ENCR_TYPE_OPEN = 0
  ENCR_TYPE_PASSPHRASE = 1
  ENCR_TYPE_PMK = 2

  PASSPHRASE = "This is some random passphrase - very very secure!!"
  PASSPHRASE_MIN = "01234567"
  PASSPHRASE_MAX = "012345678901234567890123456789012345678901234567890123456789012"
  PMK = "ODU0YjE3YzdmNDJiNWI4NTQ2NDJjNDI3M2VkZTQyZGU="
  PASSPHRASE2 = "This is some random passphrase - very very secure - but diff!!"
  PMK2 = "NjRhZGJiMmJkZWQyYTZhNjZhMmZjYzVlNTA3MmM3YTANCg=="

  PING_MSG = "ping"

  # message re-transmit counter (increases reliability in open-environment)
  # Note: reliability of message transmission is tested elsewhere
  MSG_RETX_COUNT = 5  # hard-coded max value, internal API

  # number of second to 'reasonably' wait to make sure that devices synchronize
  # with each other - useful for OOB test cases, where the OOB discovery would
  # take some time
  WAIT_FOR_CLUSTER = 5

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def create_config(self, dtype):
    """Create a base configuration based on input parameters.

    Args:
      dtype: Publish or Subscribe discovery type

    Returns:
      Discovery configuration object.
    """
    config = {}
    config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = dtype
    config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = "GoogleTestServiceDataPath"
    return config

  def request_network(self, dut, ns):
    """Request a Wi-Fi Aware network.

    Args:
      dut: Device
      ns: Network specifier
    Returns: the request key
    """
    network_req = {"TransportType": 5, "NetworkSpecifier": ns}
    return dut.droid.connectivityRequestWifiAwareNetwork(network_req)

  def set_up_discovery(self, ptype, stype, get_peer_id):
    """Set up discovery sessions and wait for service discovery.

    Args:
      ptype: Publish discovery type
      stype: Subscribe discovery type
      get_peer_id: Send a message across to get the peer's id
    """
    p_dut = self.android_devices[0]
    p_dut.pretty_name = "Publisher"
    s_dut = self.android_devices[1]
    s_dut.pretty_name = "Subscriber"

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach()
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    time.sleep(self.device_startup_offset)
    s_id = s_dut.droid.wifiAwareAttach()
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # Publisher: start publish and wait for confirmation
    p_disc_id = p_dut.droid.wifiAwarePublish(p_id, self.create_config(ptype))
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_PUBLISH_STARTED)

    # Subscriber: start subscribe and wait for confirmation
    s_disc_id = s_dut.droid.wifiAwareSubscribe(s_id, self.create_config(stype))
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED)

    # Subscriber: wait for service discovery
    discovery_event = autils.wait_for_event(
        s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)
    peer_id_on_sub = discovery_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]

    peer_id_on_pub = None
    if get_peer_id: # only need message to receive peer ID
      # Subscriber: send message to peer (Publisher - so it knows our address)
      s_dut.droid.wifiAwareSendMessage(s_disc_id, peer_id_on_sub,
                                       self.get_next_msg_id(), self.PING_MSG,
                                       self.MSG_RETX_COUNT)
      autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_MESSAGE_SENT)

      # Publisher: wait for received message
      pub_rx_msg_event = autils.wait_for_event(
          p_dut, aconsts.SESSION_CB_ON_MESSAGE_RECEIVED)
      peer_id_on_pub = pub_rx_msg_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]

    return (p_dut, s_dut, p_id, s_id, p_disc_id, s_disc_id, peer_id_on_sub,
            peer_id_on_pub)

  def run_ib_data_path_test(self,
      ptype,
      stype,
      encr_type,
      use_peer_id,
      passphrase_to_use=None):
    """Runs the in-band data-path tests.

    Args:
      ptype: Publish discovery type
      stype: Subscribe discovery type
      encr_type: Encryption type, one of ENCR_TYPE_*
      use_peer_id: On Responder (publisher): True to use peer ID, False to
                   accept any request
      passphrase_to_use: The passphrase to use if encr_type=ENCR_TYPE_PASSPHRASE
                         If None then use self.PASSPHRASE
    """
    (p_dut, s_dut, p_id, s_id, p_disc_id, s_disc_id, peer_id_on_sub,
     peer_id_on_pub) = self.set_up_discovery(ptype, stype, use_peer_id)

    key = None
    if encr_type == self.ENCR_TYPE_PASSPHRASE:
      key = self.PASSPHRASE if passphrase_to_use == None else passphrase_to_use
    elif encr_type == self.ENCR_TYPE_PMK:
      key = self.PMK

    # Publisher: request network
    p_req_key = self.request_network(
        p_dut,
        p_dut.droid.wifiAwareCreateNetworkSpecifier(p_disc_id, peer_id_on_pub if
        use_peer_id else None, key))

    # Subscriber: request network
    s_req_key = self.request_network(
        s_dut,
        s_dut.droid.wifiAwareCreateNetworkSpecifier(s_disc_id, peer_id_on_sub,
                                                    key))

    # Publisher & Subscriber: wait for network formation
    p_net_event = autils.wait_for_event_with_keys(
        p_dut, cconsts.EVENT_NETWORK_CALLBACK,
        autils.EVENT_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LINK_PROPERTIES_CHANGED),
        (cconsts.NETWORK_CB_KEY_ID, p_req_key))
    s_net_event = autils.wait_for_event_with_keys(
        s_dut, cconsts.EVENT_NETWORK_CALLBACK,
        autils.EVENT_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LINK_PROPERTIES_CHANGED),
        (cconsts.NETWORK_CB_KEY_ID, s_req_key))

    p_aware_if = p_net_event["data"][cconsts.NETWORK_CB_KEY_INTERFACE_NAME]
    s_aware_if = s_net_event["data"][cconsts.NETWORK_CB_KEY_INTERFACE_NAME]
    self.log.info("Interface names: p=%s, s=%s", p_aware_if, s_aware_if)

    p_ipv6 = p_dut.droid.connectivityGetLinkLocalIpv6Address(p_aware_if).split(
        "%")[0]
    s_ipv6 = s_dut.droid.connectivityGetLinkLocalIpv6Address(s_aware_if).split(
        "%")[0]
    self.log.info("Interface addresses (IPv6): p=%s, s=%s", p_ipv6, s_ipv6)

    # TODO: possibly send messages back and forth, prefer to use netcat/nc

    # terminate sessions and wait for ON_LOST callbacks
    p_dut.droid.wifiAwareDestroy(p_id)
    s_dut.droid.wifiAwareDestroy(s_id)

    autils.wait_for_event_with_keys(
        p_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LOST), (cconsts.NETWORK_CB_KEY_ID, p_req_key))
    autils.wait_for_event_with_keys(
        s_dut, cconsts.EVENT_NETWORK_CALLBACK, autils.EVENT_TIMEOUT,
        (cconsts.NETWORK_CB_KEY_EVENT,
         cconsts.NETWORK_CB_LOST), (cconsts.NETWORK_CB_KEY_ID, s_req_key))

    # clean-up
    p_dut.droid.connectivityUnregisterNetworkCallback(p_req_key)
    s_dut.droid.connectivityUnregisterNetworkCallback(s_req_key)

  def run_oob_data_path_test(self, encr_type, use_peer_id):
    """Runs the out-of-band data-path tests.

    Args:
      encr_type: Encryption type, one of ENCR_TYPE_*
      use_peer_id: On Responder: True to use peer ID, False to accept any
                   request
    """
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

    key = None
    if encr_type == self.ENCR_TYPE_PASSPHRASE:
      key = self.PASSPHRASE
    elif encr_type == self.ENCR_TYPE_PMK:
      key = self.PMK

    # Responder: request network
    resp_req_key = self.request_network(
        resp_dut,
        resp_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            resp_id, aconsts.DATA_PATH_RESPONDER, init_mac
            if use_peer_id else None, key))

    # Initiator: request network
    init_req_key = self.request_network(
        init_dut,
        init_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            init_id, aconsts.DATA_PATH_INITIATOR, resp_mac, key))

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

    # TODO: possibly send messages back and forth, prefer to use netcat/nc

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

  def run_mismatched_ib_data_path_test(self, pub_mismatch, sub_mismatch):
    """Runs the negative in-band data-path tests: mismatched peer ID.

    Args:
      pub_mismatch: Mismatch the publisher's ID
      sub_mismatch: Mismatch the subscriber's ID
    """
    (p_dut, s_dut, p_id, s_id, p_disc_id, s_disc_id,
     peer_id_on_sub, peer_id_on_pub) = self.set_up_discovery(
         aconsts.PUBLISH_TYPE_UNSOLICITED, aconsts.SUBSCRIBE_TYPE_PASSIVE, True)

    if pub_mismatch:
      peer_id_on_pub = peer_id_on_pub -1
    if sub_mismatch:
      peer_id_on_sub = peer_id_on_sub - 1

    # Publisher: request network
    p_req_key = self.request_network(
        p_dut,
        p_dut.droid.wifiAwareCreateNetworkSpecifier(p_disc_id, peer_id_on_pub,
                                                    None))

    # Subscriber: request network
    s_req_key = self.request_network(
        s_dut,
        s_dut.droid.wifiAwareCreateNetworkSpecifier(s_disc_id, peer_id_on_sub,
                                                    None))

    # Publisher & Subscriber: fail on network formation
    time.sleep(autils.EVENT_TIMEOUT)
    autils.fail_on_event(p_dut, cconsts.EVENT_NETWORK_CALLBACK, timeout=0)
    autils.fail_on_event(s_dut, cconsts.EVENT_NETWORK_CALLBACK, timeout=0)

    # clean-up
    p_dut.droid.connectivityUnregisterNetworkCallback(p_req_key)
    s_dut.droid.connectivityUnregisterNetworkCallback(s_req_key)

  def run_mismatched_oob_data_path_test(self,
      init_mismatch_mac=False,
      resp_mismatch_mac=False,
      init_encr_type=ENCR_TYPE_OPEN,
      resp_encr_type=ENCR_TYPE_OPEN):
    """Runs the negative out-of-band data-path tests: mismatched information
    between Responder and Initiator.

    Args:
      init_mismatch_mac: True to mismatch the Initiator MAC address
      resp_mismatch_mac: True to mismatch the Responder MAC address
      init_encr_type: Encryption type of Initiator - ENCR_TYPE_*
      resp_encr_type: Encryption type of Responder - ENCR_TYPE_*
    """
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

    if init_mismatch_mac: # assumes legit ones don't start with "00"
      init_mac = "00" + init_mac[2:]
    if resp_mismatch_mac:
      resp_mac = "00" + resp_mac[2:]

    # wait for for devices to synchronize with each other - there are no other
    # mechanisms to make sure this happens for OOB discovery (except retrying
    # to execute the data-path request)
    time.sleep(self.WAIT_FOR_CLUSTER)

    # set up separate keys: even if types are the same we want a mismatch
    init_key = None
    if init_encr_type == self.ENCR_TYPE_PASSPHRASE:
      init_key = self.PASSPHRASE
    elif init_encr_type == self.ENCR_TYPE_PMK:
      init_key = self.PMK

    resp_key = None
    if resp_encr_type == self.ENCR_TYPE_PASSPHRASE:
      resp_key = self.PASSPHRASE2
    elif resp_encr_type == self.ENCR_TYPE_PMK:
      resp_key = self.PMK2

    # Responder: request network
    resp_req_key = self.request_network(
        resp_dut,
        resp_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            resp_id, aconsts.DATA_PATH_RESPONDER, init_mac, resp_key))

    # Initiator: request network
    init_req_key = self.request_network(
        init_dut,
        init_dut.droid.wifiAwareCreateNetworkSpecifierOob(
            init_id, aconsts.DATA_PATH_INITIATOR, resp_mac, init_key))

    # Initiator & Responder: fail on network formation
    time.sleep(autils.EVENT_TIMEOUT)
    autils.fail_on_event(init_dut, cconsts.EVENT_NETWORK_CALLBACK, timeout=0)
    autils.fail_on_event(resp_dut, cconsts.EVENT_NETWORK_CALLBACK, timeout=0)

    # clean-up
    resp_dut.droid.connectivityUnregisterNetworkCallback(resp_req_key)
    init_dut.droid.connectivityUnregisterNetworkCallback(init_req_key)


  #######################################
  # Positive In-Band (IB) tests key:
  #
  # names is: test_ib_<pub_type>_<sub_type>_<encr_type>_<peer_spec>
  # where:
  #
  # pub_type: Type of publish discovery session: unsolicited or solicited.
  # sub_type: Type of subscribe discovery session: passive or active.
  # encr_type: Encription type: open, passphrase
  # peer_spec: Peer specification method: any or specific
  #
  # Note: In-Band means using Wi-Fi Aware for discovery and referring to the
  # peer using the Aware-provided peer handle (as opposed to a MAC address).
  #######################################

  def test_ib_unsolicited_passive_open_specific(self):
    """Data-path: in-band, unsolicited/passive, open encryption, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=True)

  def test_ib_unsolicited_passive_open_any(self):
    """Data-path: in-band, unsolicited/passive, open encryption, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=False)

  def test_ib_unsolicited_passive_passphrase_specific(self):
    """Data-path: in-band, unsolicited/passive, passphrase, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=True)

  def test_ib_unsolicited_passive_passphrase_any(self):
    """Data-path: in-band, unsolicited/passive, passphrase, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=False)

  def test_ib_unsolicited_passive_pmk_specific(self):
    """Data-path: in-band, unsolicited/passive, PMK, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=True)

  def test_ib_unsolicited_passive_pmk_any(self):
    """Data-path: in-band, unsolicited/passive, PMK, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=False)

  def test_ib_solicited_active_open_specific(self):
    """Data-path: in-band, solicited/active, open encryption, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=True)

  def test_ib_solicited_active_open_any(self):
    """Data-path: in-band, solicited/active, open encryption, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=False)

  def test_ib_solicited_active_passphrase_specific(self):
    """Data-path: in-band, solicited/active, passphrase, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=True)

  def test_ib_solicited_active_passphrase_any(self):
    """Data-path: in-band, solicited/active, passphrase, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=False)

  def test_ib_solicited_active_pmk_specific(self):
    """Data-path: in-band, solicited/active, PMK, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=True)

  def test_ib_solicited_active_pmk_any(self):
    """Data-path: in-band, solicited/active, PMK, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_ib_data_path_test(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=False)

  #######################################
  # Positive Out-of-Band (OOB) tests key:
  #
  # names is: test_oob_<encr_type>_<peer_spec>
  # where:
  #
  # encr_type: Encription type: open, passphrase
  # peer_spec: Peer specification method: any or specific
  #
  # Note: Out-of-Band means using a non-Wi-Fi Aware mechanism for discovery and
  # exchange of MAC addresses and then Wi-Fi Aware for data-path.
  #######################################

  def test_oob_open_specific(self):
    """Data-path: out-of-band, open encryption, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=True)

  def test_oob_open_any(self):
    """Data-path: out-of-band, open encryption, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_OPEN,
        use_peer_id=False)

  def test_oob_passphrase_specific(self):
    """Data-path: out-of-band, passphrase, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=True)

  def test_oob_passphrase_any(self):
    """Data-path: out-of-band, passphrase, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_PASSPHRASE,
        use_peer_id=False)

  def test_oob_pmk_specific(self):
    """Data-path: out-of-band, PMK, specific peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=True)

  def test_oob_pmk_any(self):
    """Data-path: out-of-band, PMK, any peer

    Verifies end-to-end discovery + data-path creation.
    """
    self.run_oob_data_path_test(
        encr_type=self.ENCR_TYPE_PMK,
        use_peer_id=False)

  ##############################################################

  def test_passphrase_min(self):
    """Data-path: minimum passphrase length

    Use in-band, unsolicited/passive, any peer combination
    """
    self.run_ib_data_path_test(ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
                               stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
                               encr_type=self.ENCR_TYPE_PASSPHRASE,
                               use_peer_id=False,
                               passphrase_to_use=self.PASSPHRASE_MIN)

  def test_passphrase_max(self):
    """Data-path: maximum passphrase length

    Use in-band, unsolicited/passive, any peer combination
    """
    self.run_ib_data_path_test(ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
                               stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
                               encr_type=self.ENCR_TYPE_PASSPHRASE,
                               use_peer_id=False,
                               passphrase_to_use=self.PASSPHRASE_MAX)

  def test_negative_mismatch_publisher_peer_id(self):
    """Data-path: failure when publisher peer ID is mismatched"""
    self.run_mismatched_ib_data_path_test(pub_mismatch=True, sub_mismatch=False)

  def test_negative_mismatch_subscriber_peer_id(self):
    """Data-path: failure when subscriber peer ID is mismatched"""
    self.run_mismatched_ib_data_path_test(pub_mismatch=False, sub_mismatch=True)

  def test_negative_mismatch_init_mac(self):
    """Data-path: failure when Initiator MAC address mismatch"""
    self.run_mismatched_oob_data_path_test(
        init_mismatch_mac=True,
        resp_mismatch_mac=False)

  def test_negative_mismatch_resp_mac(self):
    """Data-path: failure when Responder MAC address mismatch"""
    self.run_mismatched_oob_data_path_test(
        init_mismatch_mac=False,
        resp_mismatch_mac=True)

  def test_negative_mismatch_passphrase(self):
    """Data-path: failure when passphrases mismatch"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PASSPHRASE,
        resp_encr_type=self.ENCR_TYPE_PASSPHRASE)

  def test_negative_mismatch_pmk(self):
    """Data-path: failure when PMK mismatch"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PMK,
        resp_encr_type=self.ENCR_TYPE_PMK)

  def test_negative_mismatch_open_passphrase(self):
    """Data-path: failure when initiator is open, and responder passphrase"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_OPEN,
        resp_encr_type=self.ENCR_TYPE_PASSPHRASE)

  def test_negative_mismatch_open_pmk(self):
    """Data-path: failure when initiator is open, and responder PMK"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_OPEN,
        resp_encr_type=self.ENCR_TYPE_PMK)

  def test_negative_mismatch_pmk_passphrase(self):
    """Data-path: failure when initiator is pmk, and responder passphrase"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PMK,
        resp_encr_type=self.ENCR_TYPE_PASSPHRASE)

  def test_negative_mismatch_passphrase_open(self):
    """Data-path: failure when initiator is passphrase, and responder open"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PASSPHRASE,
        resp_encr_type=self.ENCR_TYPE_OPEN)

  def test_negative_mismatch_pmk_open(self):
    """Data-path: failure when initiator is PMK, and responder open"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PMK,
        resp_encr_type=self.ENCR_TYPE_OPEN)

  def test_negative_mismatch_passphrase_pmk(self):
    """Data-path: failure when initiator is passphrase, and responder pmk"""
    self.run_mismatched_oob_data_path_test(
        init_encr_type=self.ENCR_TYPE_PASSPHRASE,
        resp_encr_type=self.ENCR_TYPE_OPEN)
