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

import sys
import time

from acts import asserts
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest
from acts.test_utils.wifi.rtt.RttBaseTest import RttBaseTest


class AwareDiscoveryWithRangingTest(AwareBaseTest, RttBaseTest):
  """Set of tests for Wi-Fi Aware discovery configured with ranging (RTT)."""

  SERVICE_NAME = "GoogleTestServiceRRRRR"

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)
    RttBaseTest.__init__(self, controllers)

  def setup_test(self):
    """Manual setup here due to multiple inheritance: explicitly execute the
    setup method from both parents."""
    AwareBaseTest.setup_test(self)
    RttBaseTest.setup_test(self)

  def teardown_test(self):
    """Manual teardown here due to multiple inheritance: explicitly execute the
    teardown method from both parents."""
    AwareBaseTest.teardown_test(self)
    RttBaseTest.teardown_test(self)

  #########################################################################

  def run_discovery(self, p_config, s_config, expect_discovery,
      expect_range=False):
    """Run discovery on the 2 input devices with the specified configurations.

    Args:
      p_config, s_config: Publisher and Subscriber discovery configuration.
      expect_discovery: True or False indicating whether discovery is expected
                        with the specified configurations.
      expect_range: True if we expect distance results (i.e. ranging to happen).
                    Only relevant if expect_discovery is True.
    Returns:
      p_dut, s_dut: Publisher/Subscribe DUT
      p_disc_id, s_disc_id: Publisher/Subscribe discovery session ID
    """
    p_dut = self.android_devices[0]
    p_dut.pretty_name = "Publisher"
    s_dut = self.android_devices[1]
    s_dut.pretty_name = "Subscriber"

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    time.sleep(self.device_startup_offset)
    s_id = s_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # Publisher: start publish and wait for confirmation
    p_disc_id = p_dut.droid.wifiAwarePublish(p_id, p_config)
    autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_PUBLISH_STARTED)

    # Subscriber: start subscribe and wait for confirmation
    s_disc_id = s_dut.droid.wifiAwareSubscribe(s_id, s_config)
    autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED)

    # Subscriber: wait or fail on service discovery
    if expect_discovery:
      event = autils.wait_for_event(s_dut,
                                    aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)
      if expect_range:
        asserts.assert_true(aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
                            "Discovery with ranging expected!")
      else:
        asserts.assert_false(
          aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
          "Discovery with ranging NOT expected!")
    else:
      autils.fail_on_event(s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # (single) sleep for timeout period and then verify that no further events
    time.sleep(autils.EVENT_TIMEOUT)
    autils.verify_no_more_events(p_dut, timeout=0)
    autils.verify_no_more_events(s_dut, timeout=0)

    return p_dut, s_dut, p_disc_id, s_disc_id

  def run_discovery_update(self, p_dut, s_dut, p_disc_id, s_disc_id, p_config,
      s_config, expect_discovery, expect_range=False):
    """Run discovery on the 2 input devices with the specified update
    configurations. I.e. update the existing discovery sessions with the
    configurations.

    Args:
      p_dut, s_dut: Publisher/Subscriber DUTs.
      p_disc_id, s_disc_id: Publisher/Subscriber discovery session IDs.
      p_config, s_config: Publisher and Subscriber discovery configuration.
      expect_discovery: True or False indicating whether discovery is expected
                        with the specified configurations.
      expect_range: True if we expect distance results (i.e. ranging to happen).
                    Only relevant if expect_discovery is True.
    """

    # try to perform reconfiguration at same time (and wait once for all
    # confirmations)
    if p_config is not None:
      p_dut.droid.wifiAwareUpdatePublish(p_disc_id, p_config)
    if s_config is not None:
      s_dut.droid.wifiAwareUpdateSubscribe(s_disc_id, s_config)

    if p_config is not None:
      autils.wait_for_event(p_dut, aconsts.SESSION_CB_ON_SESSION_CONFIG_UPDATED)
    if s_config is not None:
      autils.wait_for_event(s_dut, aconsts.SESSION_CB_ON_SESSION_CONFIG_UPDATED)

    # Subscriber: wait or fail on service discovery
    if expect_discovery:
      event = autils.wait_for_event(s_dut,
                                    aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)
      if expect_range:
        asserts.assert_true(aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
                            "Discovery with ranging expected!")
      else:
        asserts.assert_false(
            aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
            "Discovery with ranging NOT expected!")
    else:
      autils.fail_on_event(s_dut, aconsts.SESSION_CB_ON_SERVICE_DISCOVERED)

    # (single) sleep for timeout period and then verify that no further events
    time.sleep(autils.EVENT_TIMEOUT)
    autils.verify_no_more_events(p_dut, timeout=0)
    autils.verify_no_more_events(s_dut, timeout=0)

  def run_discovery_prange_sminmax_outofrange(self, is_unsolicited_passive):
    """Run discovery with ranging:
    - Publisher enables ranging
    - Subscriber enables ranging with min/max such that out of range (min=large,
      max=large+1)

    Expected: no discovery

    This is a baseline test for the update-configuration tests.

    Args:
      is_unsolicited_passive: True for Unsolicited/Passive, False for
                              Solicited/Active.
    Returns: the return arguments of the run_discovery.
    """
    pub_type = (aconsts.PUBLISH_TYPE_UNSOLICITED if is_unsolicited_passive
                else aconsts.PUBLISH_TYPE_SOLICITED)
    sub_type = (aconsts.SUBSCRIBE_TYPE_PASSIVE if is_unsolicited_passive
                else aconsts.SUBSCRIBE_TYPE_ACTIVE)
    return self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME, pub_type,
                                           ssi=self.getname(2)),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME, sub_type,
                                           ssi=self.getname(2)),
            min_distance_mm=1000000,
            max_distance_mm=1000001),
        expect_discovery=False)

  def getname(self, level=1):
    """Python magic to return the name of the *calling* function.

    Args:
      level: How many levels up to go for the method name. Default = calling
             method.
    """
    return sys._getframe(level).f_code.co_name

  #########################################################################
  # Run discovery with ranging configuration.
  #
  # Names: test_ranged_discovery_<ptype>_<stype>_<p_range>_<s_range>_<ref_dist>
  #
  # where:
  # <ptype>_<stype>: unsolicited_passive or solicited_active
  # <p_range>: prange or pnorange
  # <s_range>: smin or smax or sminmax or snorange
  # <ref_distance>: inrange or outoforange
  #########################################################################

  @test_tracker_info(uuid="3a216e9a-7a57-4741-89c0-84456975e1ac")
  def test_ranged_discovery_unsolicited_passive_prange_snorange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber disables ranging

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                                aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                                ssi=self.getname()),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="859a321e-18e2-437b-aa7a-2a45a42ee737")
  def test_ranged_discovery_solicited_active_prange_snorange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber disables ranging

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                                aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                                ssi=self.getname()),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="12a4f899-4f70-4641-8f3c-351004669b71")
  def test_ranged_discovery_unsolicited_passive_pnorange_smax_inrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher disables ranging
    - Subscriber enables ranging with max such that always within range (large
      max)

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=False),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="b7f90793-113d-4355-be20-856d92ac939f")
  def test_ranged_discovery_solicited_active_pnorange_smax_inrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher disables ranging
    - Subscriber enables ranging with max such that always within range (large
      max)

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=False),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="da3ab6df-58f9-44ae-b7be-8200d9e1bb76")
  def test_ranged_discovery_unsolicited_passive_pnorange_smin_outofrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher disables ranging
    - Subscriber enables ranging with min such that always out of range (large
      min)

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=False),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=None),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="275e0806-f266-4fa6-9ca0-1cfd7b65a6ca")
  def test_ranged_discovery_solicited_active_pnorange_smin_outofrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher disables ranging
    - Subscriber enables ranging with min such that always out of range (large
      min)

    Expect: normal discovery (as if no ranging performed) - no distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=False),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=None),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="8cd0aa1e-6866-4a5d-a550-f25483eebea1")
  def test_ranged_discovery_unsolicited_passive_prange_smin_inrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min such that in range (min=0)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=None),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="97c22c54-669b-4f7a-bf51-2f484e5f3e74")
  def test_ranged_discovery_unsolicited_passive_prange_smax_inrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with max such that in range (max=large)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="616673d7-9d0b-43de-a378-e5e949b51b32")
  def test_ranged_discovery_unsolicited_passive_prange_sminmax_inrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min/max such that in range (min=0,
      max=large)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="2bf84912-dcad-4a8f-971f-e445a07f05ce")
  def test_ranged_discovery_solicited_active_prange_smin_inrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min such that in range (min=0)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=None),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="5cfd7961-9665-4742-a1b5-2d1fc97f9795")
  def test_ranged_discovery_solicited_active_prange_smax_inrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with max such that in range (max=large)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="5cf650ad-0b42-4b7d-9e05-d5f45fe0554d")
  def test_ranged_discovery_solicited_active_prange_sminmax_inrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min/max such that in range (min=0,
      max=large)

    Expect: discovery with distance
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="5277f418-ac35-43ce-9b30-3c895272898e")
  def test_ranged_discovery_unsolicited_passive_prange_smin_outofrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min such that out of range (min=large)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=None),
        expect_discovery=False)

  @test_tracker_info(uuid="8a7e6ab1-acf4-41a7-a5fb-8c164d593b5f")
  def test_ranged_discovery_unsolicited_passive_prange_smax_outofrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with max such that in range (max=0)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=0),
        expect_discovery=False)

  @test_tracker_info(uuid="b744f5f9-2641-4373-bf86-3752e2f9aace")
  def test_ranged_discovery_unsolicited_passive_prange_sminmax_outofrange(self):
    """Verify discovery with ranging:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min/max such that out of range (min=large,
      max=large+1)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=1000001),
        expect_discovery=False)

  @test_tracker_info(uuid="d2e94199-b2e6-4fa5-a347-24594883c801")
  def test_ranged_discovery_solicited_active_prange_smin_outofrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min such that out of range (min=large)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=None),
        expect_discovery=False)

  @test_tracker_info(uuid="a5619835-496a-4244-a428-f85cba3d4115")
  def test_ranged_discovery_solicited_active_prange_smax_outofrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with max such that out of range (max=0)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=None,
            max_distance_mm=0),
        expect_discovery=False)

  @test_tracker_info(uuid="12ebd91f-a973-410b-8ee1-0bd86024b921")
  def test_ranged_discovery_solicited_active_prange_sminmax_outofrange(self):
    """Verify discovery with ranging:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber enables ranging with min/max such that out of range (min=large,
      max=large+1)

    Expect: no discovery
    """
    self.run_discovery(
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=1000000,
            max_distance_mm=1000001),
        expect_discovery=False)

  #########################################################################
  # Run discovery with ranging configuration & update configurations after
  # first run.
  #
  # Names: test_ranged_updated_discovery_<ptype>_<stype>_<scenario>
  #
  # where:
  # <ptype>_<stype>: unsolicited_passive or solicited_active
  # <scenario>: test scenario (details in name)
  #########################################################################

  @test_tracker_info(uuid="59442180-4a6c-428f-b926-86000e8339b4")
  def test_ranged_updated_discovery_unsolicited_passive_oor_to_ir(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: Ranging enabled, min/max such that in range (min=0,
                        max=large)

    Expect: discovery + ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="60188508-104d-42d5-ac3a-3605093c45d7")
  def test_ranged_updated_discovery_unsolicited_passive_pub_unrange(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
    - Reconfigured to: Publisher disables ranging

    Expect: discovery w/o ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=autils.create_discovery_config(self.SERVICE_NAME,
                                             aconsts.PUBLISH_TYPE_UNSOLICITED,
                                             ssi=self.getname()),
        s_config=None, # no updates
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="f96b434e-751d-4eb5-ae01-0c5c3a6fb4a2")
  def test_ranged_updated_discovery_unsolicited_passive_sub_unrange(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: Ranging disabled

    Expect: discovery w/o ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="78970de8-9362-4647-931a-3513bcf58e80")
  def test_ranged_updated_discovery_unsolicited_passive_sub_oor(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: different out-of-range setting

    Expect: no discovery after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                           ssi=self.getname()),
            min_distance_mm=100000,
            max_distance_mm=100001),
        expect_discovery=False)

  @test_tracker_info(uuid="0841ad05-4899-4521-bd24-04a8e2e345ac")
  def test_ranged_updated_discovery_unsolicited_passive_pub_same(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
    - Reconfigured to: Publisher with same settings (ranging enabled)

    Expect: no discovery after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_UNSOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=None, # no updates
        expect_discovery=False)

  @test_tracker_info(uuid="ec6ca57b-f115-4516-813a-4572b930c8d3")
  def test_ranged_updated_discovery_unsolicited_passive_multi_step(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
      - Expect: no discovery
    - Reconfigured to: Ranging enabled, min/max such that in-range (min=0)
      - Expect: discovery with ranging
    - Reconfigured to: Ranging enabled, min/max such that out-of-range
                       (min=large)
      - Expect: no discovery
    - Reconfigured to: Ranging disabled
      - Expect: discovery without ranging
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.add_ranging_to_sub(
                autils.create_discovery_config(self.SERVICE_NAME,
                                               aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                               ssi=self.getname()),
                min_distance_mm=0,
                max_distance_mm=None),
            expect_discovery=True,
            expect_range=True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.add_ranging_to_sub(
                autils.create_discovery_config(self.SERVICE_NAME,
                                               aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                               ssi=self.getname()),
                min_distance_mm=1000000,
                max_distance_mm=None),
            expect_discovery=False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                               aconsts.SUBSCRIBE_TYPE_PASSIVE,
                                               ssi=self.getname()),
            expect_discovery=True,
            expect_range=False)

  @test_tracker_info(uuid="bbaac63b-000c-415f-bf19-0906f04031cd")
  def test_ranged_updated_discovery_solicited_active_oor_to_ir(self):
    """Verify discovery with ranging operation with updated configuration:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: Ranging enabled, min/max such that in range (min=0,
                        max=large)

    Expect: discovery + ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=0,
            max_distance_mm=1000000),
        expect_discovery=True,
        expect_range=True)

  @test_tracker_info(uuid="c385b361-7955-4f34-9109-8d8ca81cb4cc")
  def test_ranged_updated_discovery_solicited_active_pub_unrange(self):
    """Verify discovery with ranging operation with updated configuration:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
    - Reconfigured to: Publisher disables ranging

    Expect: discovery w/o ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=autils.create_discovery_config(self.SERVICE_NAME,
                                                 aconsts.PUBLISH_TYPE_SOLICITED,
                                                 ssi=self.getname()),
        s_config=None, # no updates
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="ec5120ea-77ec-48c6-8820-48b82ad3dfd4")
  def test_ranged_updated_discovery_solicited_active_sub_unrange(self):
    """Verify discovery with ranging operation with updated configuration:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: Ranging disabled

    Expect: discovery w/o ranging after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                                 aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                                 ssi=self.getname()),
        expect_discovery=True,
        expect_range=False)

  @test_tracker_info(uuid="6231cb42-91e4-48d3-b9db-b37efbe8537c")
  def test_ranged_updated_discovery_solicited_active_sub_oor(self):
    """Verify discovery with ranging operation with updated configuration:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber:
      - Starts: Ranging enabled, min/max such that out of range (min=large,
                max=large+1)
      - Reconfigured to: different out-of-range setting

    Expect: no discovery after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=None, # no updates
        s_config=autils.add_ranging_to_sub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                           ssi=self.getname()),
            min_distance_mm=100000,
            max_distance_mm=100001),
        expect_discovery=False)

  @test_tracker_info(uuid="ec999420-6a50-455e-b624-f4c9b4cb7ea5")
  def test_ranged_updated_discovery_solicited_active_pub_same(self):
    """Verify discovery with ranging operation with updated configuration:
    - Solicited Publish/Active Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
    - Reconfigured to: Publisher with same settings (ranging enabled)

    Expect: no discovery after update
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
        p_config=autils.add_ranging_to_pub(
            autils.create_discovery_config(self.SERVICE_NAME,
                                           aconsts.PUBLISH_TYPE_SOLICITED,
                                           ssi=self.getname()),
            enable_ranging=True),
        s_config=None, # no updates
        expect_discovery=False)

  @test_tracker_info(uuid="ec6ca57b-f115-4516-813a-4572b930c8d3")
  def test_ranged_updated_discovery_solicited_active_multi_step(self):
    """Verify discovery with ranging operation with updated configuration:
    - Unsolicited Publish/Passive Subscribe
    - Publisher enables ranging
    - Subscriber: Ranging enabled, min/max such that out of range (min=large,
                  max=large+1)
      - Expect: no discovery
    - Reconfigured to: Ranging enabled, min/max such that in-range (min=0)
      - Expect: discovery with ranging
    - Reconfigured to: Ranging enabled, min/max such that out-of-range
                       (min=large)
      - Expect: no discovery
    - Reconfigured to: Ranging disabled
      - Expect: discovery without ranging
    """
    (p_dut, s_dut, p_disc_id,
     s_disc_id) = self.run_discovery_prange_sminmax_outofrange(True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.add_ranging_to_sub(
                autils.create_discovery_config(self.SERVICE_NAME,
                                               aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                               ssi=self.getname()),
                min_distance_mm=0,
                max_distance_mm=None),
            expect_discovery=True,
            expect_range=True)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.add_ranging_to_sub(
                autils.create_discovery_config(self.SERVICE_NAME,
                                               aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                               ssi=self.getname()),
                min_distance_mm=1000000,
                max_distance_mm=None),
            expect_discovery=False)
    self.run_discovery_update(p_dut, s_dut, p_disc_id, s_disc_id,
            p_config=None, # no updates
            s_config=autils.create_discovery_config(self.SERVICE_NAME,
                                                aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                                ssi=self.getname()),
            expect_discovery=True,
            expect_range=False)

  #########################################################################

  @test_tracker_info(uuid="6edc47ab-7300-4bff-b7dd-5de83f58928a")
  def test_ranged_discovery_multi_session(self):
    """Verify behavior with multiple concurrent discovery session with different
    configurations:

    Device A (Publisher):
      Publisher AA: ranging enabled
      Publisher BB: ranging enabled
      Publisher CC: ranging enabled
      Publisher DD: ranging disabled
    Device B (Subscriber):
      Subscriber AA: ranging out-of-range -> no match
      Subscriber BB: ranging in-range -> match w/range
      Subscriber CC: ranging disabled -> match w/o range
      Subscriber DD: ranging out-of-range -> match w/o range
    """
    p_dut = self.android_devices[0]
    p_dut.pretty_name = "Publisher"
    s_dut = self.android_devices[1]
    s_dut.pretty_name = "Subscriber"

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    time.sleep(self.device_startup_offset)
    s_id = s_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # Subscriber: start sessions
    aa_s_disc_id = s_dut.droid.wifiAwareSubscribe(
        s_id,
        autils.add_ranging_to_sub(
            autils.create_discovery_config("AA",
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE),
            min_distance_mm=1000000, max_distance_mm=1000001),
        True)
    bb_s_disc_id = s_dut.droid.wifiAwareSubscribe(
        s_id,
        autils.add_ranging_to_sub(
            autils.create_discovery_config("BB",
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE),
            min_distance_mm=0, max_distance_mm=1000000),
        True)
    cc_s_disc_id = s_dut.droid.wifiAwareSubscribe(
        s_id,
        autils.create_discovery_config("CC", aconsts.SUBSCRIBE_TYPE_PASSIVE),
        True)
    dd_s_disc_id = s_dut.droid.wifiAwareSubscribe(
        s_id,
        autils.add_ranging_to_sub(
            autils.create_discovery_config("DD",
                                           aconsts.SUBSCRIBE_TYPE_PASSIVE),
            min_distance_mm=1000000, max_distance_mm=1000001),
        True)

    autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED, aa_s_disc_id))
    autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED, bb_s_disc_id))
    autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED, cc_s_disc_id))
    autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED, dd_s_disc_id))

    # Publisher: start sessions
    aa_p_disc_id = p_dut.droid.wifiAwarePublish(
        p_id,
        autils.add_ranging_to_pub(
            autils.create_discovery_config("AA",
                                           aconsts.PUBLISH_TYPE_UNSOLICITED),
            enable_ranging=True),
        True)
    bb_p_disc_id = p_dut.droid.wifiAwarePublish(
        p_id,
        autils.add_ranging_to_pub(
            autils.create_discovery_config("BB",
                                           aconsts.PUBLISH_TYPE_UNSOLICITED),
            enable_ranging=True),
        True)
    cc_p_disc_id = p_dut.droid.wifiAwarePublish(
        p_id,
        autils.add_ranging_to_pub(
            autils.create_discovery_config("CC",
                                           aconsts.PUBLISH_TYPE_UNSOLICITED),
            enable_ranging=True),
        True)
    dd_p_disc_id = p_dut.droid.wifiAwarePublish(
        p_id,
        autils.create_discovery_config("DD", aconsts.PUBLISH_TYPE_UNSOLICITED),
        True)

    autils.wait_for_event(p_dut, autils.decorate_event(
        aconsts.SESSION_CB_ON_PUBLISH_STARTED, aa_p_disc_id))
    autils.wait_for_event(p_dut, autils.decorate_event(
        aconsts.SESSION_CB_ON_PUBLISH_STARTED, bb_p_disc_id))
    autils.wait_for_event(p_dut, autils.decorate_event(
        aconsts.SESSION_CB_ON_PUBLISH_STARTED, cc_p_disc_id))
    autils.wait_for_event(p_dut, autils.decorate_event(
        aconsts.SESSION_CB_ON_PUBLISH_STARTED, dd_p_disc_id))

    # Expected and unexpected service discovery
    event = autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SERVICE_DISCOVERED, bb_s_disc_id))
    asserts.assert_true(aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
                        "Discovery with ranging for BB expected!")
    event = autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SERVICE_DISCOVERED, cc_s_disc_id))
    asserts.assert_false(
        aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
        "Discovery with ranging for CC NOT expected!")
    event = autils.wait_for_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SERVICE_DISCOVERED, dd_s_disc_id))
    asserts.assert_false(
        aconsts.SESSION_CB_KEY_DISTANCE_MM in event["data"],
        "Discovery with ranging for DD NOT expected!")
    autils.fail_on_event(s_dut, autils.decorate_event(
      aconsts.SESSION_CB_ON_SERVICE_DISCOVERED, aa_s_disc_id))

    # (single) sleep for timeout period and then verify that no further events
    time.sleep(autils.EVENT_TIMEOUT)
    autils.verify_no_more_events(p_dut, timeout=0)
    autils.verify_no_more_events(s_dut, timeout=0)