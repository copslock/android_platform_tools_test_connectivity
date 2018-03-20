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

  def getname(self):
    """Python magic to return the name of the *calling* function."""
    return sys._getframe(1).f_code.co_name

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