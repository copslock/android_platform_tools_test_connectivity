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

import queue
import time

from acts import asserts
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils
from acts.test_utils.wifi.aware.AwareBaseTest import AwareBaseTest


class LatencyTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware to measure latency of Aware operations."""

  NUM_ITERATIONS = 100

  # number of second to 'reasonably' wait to make sure that devices synchronize
  # with each other - useful for OOB test cases, where the OOB discovery would
  # take some time
  WAIT_FOR_CLUSTER = 5

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def start_discovery_session(self, dut, session_id, is_publish, dtype):
    """Start a discovery session

    Args:
      dut: Device under test
      session_id: ID of the Aware session in which to start discovery
      is_publish: True for a publish session, False for subscribe session
      dtype: Type of the discovery session

    Returns:
      Discovery session started event.
    """
    config = {}
    config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = dtype
    config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = "GoogleTestServiceXY"

    if is_publish:
      disc_id = dut.droid.wifiAwarePublish(session_id, config)
      event_name = aconsts.SESSION_CB_ON_PUBLISH_STARTED
    else:
      disc_id = dut.droid.wifiAwareSubscribe(session_id, config)
      event_name = aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED

    event = autils.wait_for_event(dut, event_name)
    return disc_id, event

  def run_discovery_latency(self, results, do_unsolicited_passive, dw_24ghz,
                            dw_5ghz):
    """Run the service discovery latency test with the specified DW intervals.

    Args:
      results: Result array to be populated - will add results (not erase it)
      do_unsolicited_passive: True for unsolicited/passive, False for
                              solicited/active.
      dw_24ghz: DW interval in the 2.4GHz band.
      dw_5ghz: DW interval in the 5GHz band.
    """
    key = "%s_dw24_%d_dw5_%d" % (
        "unsolicited_passive"
        if do_unsolicited_passive else "solicited_active", dw_24ghz, dw_5ghz)
    results[key] = {}
    results[key]["num_iterations"] = self.NUM_ITERATIONS

    p_dut = self.android_devices[0]
    p_dut.pretty_name = "Publisher"
    s_dut = self.android_devices[1]
    s_dut.pretty_name = "Subscriber"

    # Publisher+Subscriber: attach and wait for confirmation
    p_id = p_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(p_dut, aconsts.EVENT_CB_ON_ATTACHED)
    s_id = s_dut.droid.wifiAwareAttach(False)
    autils.wait_for_event(s_dut, aconsts.EVENT_CB_ON_ATTACHED)

    # override the default DW configuration
    p_dut.adb.shell(
        "cmd wifiaware native_api set dw_default_24ghz %d" % dw_24ghz)
    p_dut.adb.shell("cmd wifiaware native_api set dw_default_5ghz %d" % dw_5ghz)
    s_dut.adb.shell(
        "cmd wifiaware native_api set dw_default_24ghz %d" % dw_24ghz)
    s_dut.adb.shell("cmd wifiaware native_api set dw_default_5ghz %d" % dw_5ghz)

    # start publish
    p_disc_event = self.start_discovery_session(
        p_dut, p_id, True, aconsts.PUBLISH_TYPE_UNSOLICITED
        if do_unsolicited_passive else aconsts.PUBLISH_TYPE_SOLICITED)

    # wait for for devices to synchronize with each other - used so that first
    # discovery isn't biased by synchronization.
    time.sleep(self.WAIT_FOR_CLUSTER)

    # loop, perform discovery, and collect latency information
    latencies = []
    failed_discoveries = 0
    for i in range(self.NUM_ITERATIONS):
      # start subscribe
      s_disc_id, s_session_event = self.start_discovery_session(
          s_dut, s_id, False, aconsts.SUBSCRIBE_TYPE_PASSIVE
          if do_unsolicited_passive else aconsts.SUBSCRIBE_TYPE_ACTIVE)

      # wait for discovery (allow for failures here since running lots of
      # samples and would like to get the partial data even in the presence of
      # errors)
      try:
        discovery_event = s_dut.ed.pop_event(
            aconsts.SESSION_CB_ON_SERVICE_DISCOVERED, autils.EVENT_TIMEOUT)
      except queue.Empty:
        s_dut.log.info("[Subscriber] Timed out while waiting for "
                       "SESSION_CB_ON_SERVICE_DISCOVERED")
        failed_discoveries = failed_discoveries + 1
        continue
      finally:
        # destroy subscribe
        s_dut.droid.wifiAwareDestroyDiscoverySession(s_disc_id)

      # collect latency information
      latencies.append(
          discovery_event["data"][aconsts.SESSION_CB_KEY_TIMESTAMP_MS] -
          s_session_event["data"][aconsts.SESSION_CB_KEY_TIMESTAMP_MS])
      self.log.info("Latency #%d = %d" % (i, latencies[-1]))

    autils.extract_stats(
        s_dut,
        data=latencies,
        results=results[key],
        key_prefix="",
        log_prefix="Subscribe Session Discovery (%s, dw24=%d, dw5=%d)" %
        ("Unsolicited/Passive"
         if do_unsolicited_passive else "Solicited/Active", dw_24ghz, dw_5ghz))
    results[key]["num_failed_discovery"] = failed_discoveries

  ########################################################################

  def test_discovery_latency_default_dws(self):
    """Measure the service discovery latency with the default DW configuration.
    """
    results = {}
    self.run_discovery_latency(
        results=results, do_unsolicited_passive=True, dw_24ghz=-1, dw_5ghz=-1)
    asserts.explicit_pass(
        "test_discovery_latency_default_parameters finished", extras=results)

  def test_discovery_latency_non_interactive_dws(self):
    """Measure the service discovery latency with the DW configuration for non
    -interactive mode (lower power)."""
    results = {}
    self.run_discovery_latency(
        results=results, do_unsolicited_passive=True, dw_24ghz=4, dw_5ghz=0)
    asserts.explicit_pass(
        "test_discovery_latency_non_interactive_dws finished", extras=results)
