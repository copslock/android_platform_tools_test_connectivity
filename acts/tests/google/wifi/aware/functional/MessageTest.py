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
import time

from acts import asserts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class MessageTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware L2 (layer 2) message exchanges."""

  # configuration parameters used by tests
  PAYLOAD_SIZE_MIN = 0
  PAYLOAD_SIZE_TYPICAL = 1
  PAYLOAD_SIZE_MAX = 2

  NUM_MSGS_NO_QUEUE = 10
  NUM_MSGS_QUEUE_DEPTH_MULT = 2  # number of messages = mult * queue depth

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def create_msg(self, caps, payload_size, id):
    """Creates a message string of the specified size containing the input id.

    Args:
      caps: Device capabilities.
      payload_size: The size of the message to create - min (null or empty
                    message), typical, max (based on device capabilities). Use
                    the PAYLOAD_SIZE_xx constants.
      id: Information to include in the generated message (or None).

    Returns: A string of the requested size, optionally containing the id.
    """
    if payload_size == self.PAYLOAD_SIZE_MIN:
      # arbitrarily return a None or an empty string (equivalent messages)
      return None if id % 2 == 0 else ""
    elif payload_size == self.PAYLOAD_SIZE_TYPICAL:
      return "*** ID=%d ***" % id + string.ascii_uppercase
    else:  # PAYLOAD_SIZE_MAX
      return "*** ID=%4d ***" % id + "M" * (
          caps[aconsts.CAP_MAX_SERVICE_SPECIFIC_INFO_LEN] - 15)

  def create_config(self, is_publish):
    """Create a base configuration based on input parameters.

    Args:
      is_publish: True for publish, False for subscribe sessions.

    Returns:
      publish discovery configuration object.
    """
    config = {}
    if is_publish:
      config[aconsts.
             DISCOVERY_KEY_DISCOVERY_TYPE] = aconsts.PUBLISH_TYPE_UNSOLICITED
    else:
      config[
          aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = aconsts.SUBSCRIBE_TYPE_PASSIVE
    config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = "GoogleTestServiceX"
    return config

  def prep_message_exchange(self):
    """Creates a discovery session (publish and subscribe), and waits for
    service discovery - at that point the sessions are ready for message
    exchange.
    """
    p_dut = self.android_devices[0]
    p_dut.pretty_name = "Publisher"
    s_dut = self.android_devices[1]
    s_dut.pretty_name = "Subscriber"

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    s_id = s_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # Publisher: start publish and wait for confirmation
    p_disc_id = p_dut.droid.wifiAwarePublish(p_id, self.create_config(True))
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_PUBLISH_STARTED)

    # Subscriber: start subscribe and wait for confirmation
    s_disc_id = s_dut.droid.wifiAwareSubscribe(s_id, self.create_config(False))
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED)

    # Subscriber: wait for service discovery
    discovery_event = autils.wait_for_event(
        s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)
    peer_id_on_sub = discovery_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]

    return {
        "p_dut": p_dut,
        "s_dut": s_dut,
        "p_id": p_id,
        "s_id": s_id,
        "p_disc_id": p_disc_id,
        "s_disc_id": s_disc_id,
        "peer_id_on_sub": peer_id_on_sub
    }

  def run_message_no_queue(self, payload_size):
    """Validate L2 message exchange between publisher & subscriber with no
    queueing - i.e. wait for an ACK on each message before sending the next
    message.

    Args:
      payload_size: min, typical, or max (PAYLOAD_SIZE_xx).
    """
    discovery_info = self.prep_message_exchange()
    p_dut = discovery_info["p_dut"]
    s_dut = discovery_info["s_dut"]
    p_disc_id = discovery_info["p_disc_id"]
    s_disc_id = discovery_info["s_disc_id"]
    peer_id_on_sub = discovery_info["peer_id_on_sub"]

    for i in range(self.NUM_MSGS_NO_QUEUE):
      msg = self.create_msg(s_dut.aware_capabilities, payload_size, i)
      msg_id = self.get_next_msg_id()
      s_dut.droid.wifiAwareSendMessage(s_disc_id, peer_id_on_sub, msg_id, msg,
                                       0)
      tx_event = autils.wait_for_event(s_dut,
                                       aconsts.SESSION_CB_ON_MESSAGE_SENT)
      rx_event = autils.wait_for_event(p_dut,
                                       aconsts.SESSION_CB_ON_MESSAGE_RECEIVED)
      asserts.assert_equal(msg_id,
                           tx_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_ID],
                           "Subscriber -> Publisher message ID corrupted")
      autils.assert_equal_strings(
          msg, rx_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_AS_STRING],
          "Subscriber -> Publisher message %d corrupted" % i)

    peer_id_on_pub = rx_event["data"][aconsts.SESSION_CB_KEY_PEER_ID]
    for i in range(self.NUM_MSGS_NO_QUEUE):
      msg = self.create_msg(s_dut.aware_capabilities, payload_size, 1000 + i)
      msg_id = self.get_next_msg_id()
      p_dut.droid.wifiAwareSendMessage(p_disc_id, peer_id_on_pub, msg_id, msg,
                                       0)
      tx_event = autils.wait_for_event(p_dut,
                                       aconsts.SESSION_CB_ON_MESSAGE_SENT)
      rx_event = autils.wait_for_event(s_dut,
                                       aconsts.SESSION_CB_ON_MESSAGE_RECEIVED)
      asserts.assert_equal(msg_id,
                           tx_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_ID],
                           "Publisher -> Subscriber message ID corrupted")
      autils.assert_equal_strings(
          msg, rx_event["data"][aconsts.SESSION_CB_KEY_MESSAGE_AS_STRING],
          "Publisher -> Subscriber message %d corrupted" % i)

    # verify there are no more events
    time.sleep(autils.EVENT_TIMEOUT)
    autils.verify_no_more_events(p_dut, timeout=0)
    autils.verify_no_more_events(s_dut, timeout=0)

  ############################################################################

  def test_message_no_queue_min(self):
    """Functional / Message / No queue
    - Minimal payload size (None or "")
    """
    self.run_message_no_queue(self.PAYLOAD_SIZE_MIN)

  def test_message_no_queue_typical(self):
    """Functional / Message / No queue
    - Typical payload size
    """
    self.run_message_no_queue(self.PAYLOAD_SIZE_TYPICAL)

  def test_message_no_queue_max(self):
    """Functional / Message / No queue
    - Max payload size (based on device capabilities)
    """
    self.run_message_no_queue(self.PAYLOAD_SIZE_MAX)
