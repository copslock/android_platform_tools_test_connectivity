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

import string

from acts import asserts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class DiscoveryTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware discovery."""

  # configuration parameters used by tests
  PAYLOAD_SIZE_MIN = 0
  PAYLOAD_SIZE_TYPICAL = 1
  PAYLOAD_SIZE_MAX = 2

  # message strings
  query_msg = "How are you doing? 你好嗎？"
  response_msg = "Doing ok - thanks! 做的不錯 - 謝謝！"

  # message re-transmit counter (increases reliability in open-environment)
  # Note: reliability of message transmission is tested elsewhere
  msg_retx_count = 5  # hard-coded max value, internal API

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def create_base_config(self, is_publish, ptype, stype, payload_size, ttl,
                         term_ind_on, null_match):
    """Create a base configuration based on input parameters.

    Args:
      is_publish: True if a publish config, else False
      ptype: unsolicited or solicited (used if is_publish is True)
      stype: passive or active (used if is_publish is False)
      payload_size: min, typical, max (PAYLOAD_SIZE_xx)
      ttl: time-to-live configuration (0 - forever)
      term_ind_on: is termination indication enabled
      null_match: null-out the middle match filter
    Returns:
      publish discovery configuration object.
    """
    config = {}
    if is_publish:
      config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = ptype
    else:
      config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = stype
    config[aconsts.DISCOVERY_KEY_TTL] = ttl
    config[aconsts.DISCOVERY_KEY_TERM_CB_ENABLED] = term_ind_on
    if payload_size == self.PAYLOAD_SIZE_MIN:
      config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = "a"
      config[aconsts.DISCOVERY_KEY_SSI] = None
      config[aconsts.DISCOVERY_KEY_MATCH_FILTER_LIST] = []
    elif payload_size == self.PAYLOAD_SIZE_TYPICAL:
      config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = "GoogleTestServiceX"
      if is_publish:
        config[aconsts.DISCOVERY_KEY_SSI] = string.ascii_letters
      else:
        config[aconsts.DISCOVERY_KEY_SSI] = string.ascii_letters[::
                                                                 -1]  # reverse
      config[aconsts.DISCOVERY_KEY_MATCH_FILTER_LIST] = autils.encode_list(
          [(10).to_bytes(1, byteorder="big"), "hello there string"
          if not null_match else None,
           bytes(range(40))])
    return config

  def create_publish_config(self, ptype, payload_size, ttl, term_ind_on,
                            null_match):
    """Create a publish configuration based on input parameters.

    Args:
      ptype: unsolicited or solicited
      payload_size: min, typical, max (PAYLOAD_SIZE_xx)
      ttl: time-to-live configuration (0 - forever)
      term_ind_on: is termination indication enabled
      null_match: null-out the middle match filter
    Returns:
      publish discovery configuration object.
    """
    return self.create_base_config(True, ptype, None, payload_size, ttl,
                                   term_ind_on, null_match)

  def create_subscribe_config(self, stype, payload_size, ttl, term_ind_on,
                              null_match):
    """Create a subscribe configuration based on input parameters.

    Args:
      stype: passive or active
      payload_size: min, typical, max (PAYLOAD_SIZE_xx)
      ttl: time-to-live configuration (0 - forever)
      term_ind_on: is termination indication enabled
      null_match: null-out the middle match filter
    Returns:
      subscribe discovery configuration object.
    """
    return self.create_base_config(False, None, stype, payload_size, ttl,
                                   term_ind_on, null_match)

  def positive_discovery_test_utility(self, ptype, stype, payload_size, ttl,
                                      term_ind_on):
    """Utility which runs a positive discovery test:
    - Discovery (publish/subscribe)
    - Exchange messages
    - Update publish/subscribe
    - Terminate

    Args:
      ptype: Publish discovery type
      stype: Subscribe discovery type
      payload_size: One of PAYLOAD_SIZE_* constants - MIN, TYPICAL, MAX
      ttl: Duration of discovery session, 0 for unlimited
      term_ind_on: True if a termination indication is wanted, False otherwise
    """
    p_dut = self.android_devices[0]
    s_dut = self.android_devices[1]

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    s_id = s_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # Publisher: start publish and wait for confirmation
    p_config = self.create_publish_config(ptype, payload_size, ttl, term_ind_on,
                                          null_match=False)
    p_disc_id = p_dut.droid.wifiAwarePublish(p_id, p_config)
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_PUBLISH_STARTED)

    # Subscriber: start subscribe and wait for confirmation
    s_config = self.create_subscribe_config(stype, payload_size, ttl,
                                            term_ind_on, null_match=True)
    s_disc_id = s_dut.droid.wifiAwareSubscribe(s_id, s_config)
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED)

    # Subscriber: wait for service discovery
    discovery_event = autils.wait_for_event(
        s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)
    peer_id_on_sub = discovery_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]

    # Subscriber: validate contents of discovery (specifically that getting the
    # Publisher's SSI and MatchFilter!)
    autils.assert_equal_strings(
        bytes(discovery_event["data"][
            aconsts.SESSION_CB_KEY_SERVICE_SPECIFIC_INFO]).decode("utf-8"),
        p_config[aconsts.DISCOVERY_KEY_SSI],
        "Discovery mismatch: service specific info (SSI)")
    asserts.assert_equal(
        autils.decode_list(
            discovery_event["data"][aconsts.SESSION_CB_KEY_MATCH_FILTER_LIST]),
        autils.decode_list(p_config[aconsts.DISCOVERY_KEY_MATCH_FILTER_LIST]),
        "Discovery mismatch: match filter")

    # Subscriber: send message to peer (Publisher)
    s_dut.droid.wifiAwareSendMessage(s_disc_id, peer_id_on_sub,
                                     self.get_next_msg_id(), self.query_msg,
                                     self.msg_retx_count)
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_MESSAGE_SENT)

    # Publisher: wait for received message
    pub_rx_msg_event = autils.wait_for_event(
        p_dut, aconsts.SESSION_CB_ON_MESSAGE_RECEIVED)
    peer_id_on_pub = pub_rx_msg_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]

    # Publisher: validate contents of message
    asserts.assert_equal(
        pub_rx_msg_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_AS_STRING],
        self.query_msg, "Subscriber -> Publisher message corrupted")

    # Publisher: send message to peer (Subscriber)
    p_dut.droid.wifiAwareSendMessage(p_disc_id, peer_id_on_pub,
                                     self.get_next_msg_id(), self.response_msg,
                                     self.msg_retx_count)
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_MESSAGE_SENT)

    # Subscriber: wait for received message
    sub_rx_msg_event = autils.wait_for_event(
        s_dut, aconsts.SESSION_CB_ON_MESSAGE_RECEIVED)

    # Subscriber: validate contents of message
    asserts.assert_equal(
        sub_rx_msg_event["data"][aconsts.SESSION_CB_KEY_PEER_ID],
        peer_id_on_sub,
        "Subscriber received message from different peer ID then discovery!?")
    autils.assert_equal_strings(
        sub_rx_msg_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_AS_STRING],
        self.response_msg, "Publisher -> Subscriber message corrupted")

    # Subscriber: validate that we're not getting another Service Discovery
    autils.fail_on_event(s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # Publisher: update publish and wait for confirmation
    p_config[aconsts.DISCOVERY_KEY_SSI] = "something else"
    p_dut.droid.wifiAwareUpdatePublish(p_disc_id, p_config)
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_SESSION_CONFIG_UPDATED)

    # Subscriber: expect a new service discovery
    discovery_event = autils.wait_for_event(
        s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # Subscriber: validate contents of discovery
    autils.assert_equal_strings(
        bytes(discovery_event["data"][
            aconsts.SESSION_CB_KEY_SERVICE_SPECIFIC_INFO]).decode("utf-8"),
        p_config[aconsts.DISCOVERY_KEY_SSI],
        "Discovery mismatch (after pub update): service specific info (SSI)")
    asserts.assert_equal(
        autils.decode_list(
            discovery_event["data"][aconsts.SESSION_CB_KEY_MATCH_FILTER_LIST]),
        autils.decode_list(p_config[aconsts.DISCOVERY_KEY_MATCH_FILTER_LIST]),
        "Discovery mismatch: match filter")

    # Subscribe: update subscribe and wait for confirmation
    s_config = self.create_subscribe_config(stype, payload_size, ttl,
                                            term_ind_on, null_match=False)
    s_dut.droid.wifiAwareUpdateSubscribe(s_disc_id, s_config)
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SESSION_CONFIG_UPDATED)

    # Subscriber: should not get a new service discovery (no new information)
    autils.fail_on_event(s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # Publisher: should never get a service discovery event!
    autils.fail_on_event(p_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # Publisher+Subscriber: Terminate sessions
    p_dut.droid.wifiAwareDestroyDiscoverySession(p_disc_id)
    s_dut.droid.wifiAwareDestroyDiscoverySession(s_disc_id)

    # Publisher+Subscriber: Expect (or not) to receive termination indication
    # Note: if TTL is 0 (i.e. continuous session - which we terminate
    # explicitly) then do not expect indications no matter the configuration
    if term_ind_on and ttl != 0:
      autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_SESSION_TERMINATED)
      autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SESSION_TERMINATED)
    else:
      autils.fail_on_event(p_dut, aconsts.SESSION_CB_ON_SESSION_TERMINATED)
      autils.fail_on_event(s_dut, aconsts.SESSION_CB_ON_SESSION_TERMINATED)

  #######################################
  # Positive tests key:
  #
  # names is: test_<pub_type>_<sub_type>_<size>_<lifetime>_<term_ind>,
  # where:
  #
  # pub_type: Type of publish discovery session: unsolicited or solicited.
  # sub_type: Type of subscribe discovery session: passive or active.
  # size: Size of payload fields (service name, service specific info, and match
  # filter: typical, max, or min.
  # lifetime: Discovery session lifetime: ongoing or limited.
  # term_ind: Termination indication enabled or disabled: termind or "".
  #           Only relevant for limited lifetime (i.e. TTL != 0).
  #######################################

  def test_positive_unsolicited_passive_typical_ongoing(self):
    """Functional test case / Discovery test cases / positive test case:
    - Solicited publish + passive subscribe
    - Typical payload fields size
    - Ongoing lifetime (i.e. no TTL specified)

    Verifies that discovery and message exchange succeeds.
    """
    self.positive_discovery_test_utility(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        payload_size=self.PAYLOAD_SIZE_TYPICAL,
        ttl=0,
        term_ind_on=True)  # term_ind_on is irrelevant since ttl=0

  def test_positive_unsolicited_passive_min_ongoing(self):
    """Functional test case / Discovery test cases / positive test case:
    - Solicited publish + passive subscribe
    - Minimal payload fields size
    - Ongoing lifetime (i.e. no TTL specified)

    Verifies that discovery and message exchange succeeds.
    """
    self.positive_discovery_test_utility(
        ptype=aconsts.PUBLISH_TYPE_UNSOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_PASSIVE,
        payload_size=self.PAYLOAD_SIZE_MIN,
        ttl=0,
        term_ind_on=True)  # term_ind_on is irrelevant since ttl=0

  def test_positive_solicited_active_typical_ongoing(self):
    """Functional test case / Discovery test cases / positive test case:
    - Unsolicited publish + active subscribe
    - Typical payload fields size
    - Ongoing lifetime (i.e. no TTL specified)

    Verifies that discovery and message exchange succeeds.
    """
    self.positive_discovery_test_utility(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        payload_size=self.PAYLOAD_SIZE_TYPICAL,
        ttl=0,
        term_ind_on=True)  # term_ind_on is irrelevant since ttl=0

  def test_positive_solicited_active_min_ongoing(self):
    """Functional test case / Discovery test cases / positive test case:
    - Unsolicited publish + active subscribe
    - Minimal payload fields size
    - Ongoing lifetime (i.e. no TTL specified)

    Verifies that discovery and message exchange succeeds.
    """
    self.positive_discovery_test_utility(
        ptype=aconsts.PUBLISH_TYPE_SOLICITED,
        stype=aconsts.SUBSCRIBE_TYPE_ACTIVE,
        payload_size=self.PAYLOAD_SIZE_MIN,
        ttl=0,
        term_ind_on=True)  # term_ind_on is irrelevant since ttl=0
