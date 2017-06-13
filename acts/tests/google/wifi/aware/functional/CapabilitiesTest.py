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


class CapabilitiesTest(AwareBaseTest):
  """Set of tests for Wi-Fi Aware Capabilities - verifying that the provided
  capabilities are real (i.e. available)."""

  def __init__(self, controllers):
    AwareBaseTest.__init__(self, controllers)

  def create_config(self, dtype, service_name):
    """Create a discovery configuration based on input parameters.

    Args:
      dtype: Publish or Subscribe discovery type
      service_name: Service name.

    Returns:
      Discovery configuration object.
    """
    config = {}
    config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = dtype
    config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = service_name
    return config

  def start_discovery_session(self, dut, session_id, is_publish, dtype,
                              service_name, expect_success):
    """Start a discovery session

    Args:
      dut: Device under test
      session_id: ID of the Aware session in which to start discovery
      is_publish: True for a publish session, False for subscribe session
      dtype: Type of the discovery session
      service_name: Service name to use for the discovery session
      expect_success: True if expect session to be created, False otherwise

    Returns:
      Discovery session ID.
    """
    config = {}
    config[aconsts.DISCOVERY_KEY_DISCOVERY_TYPE] = dtype
    config[aconsts.DISCOVERY_KEY_SERVICE_NAME] = service_name

    if is_publish:
      disc_id = dut.droid.wifiAwarePublish(session_id, config)
      event_name = aconsts.SESSION_CB_ON_PUBLISH_STARTED
    else:
      disc_id = dut.droid.wifiAwareSubscribe(session_id, config)
      event_name = aconsts.SESSION_CB_ON_SUBSCRIBE_STARTED

    if expect_success:
      autils.wait_for_event(dut, event_name)
    else:
      autils.wait_for_event(dut, aconsts.SESSION_CB_ON_SESSION_CONFIG_FAILED)

    return disc_id

  ###############################

  def test_max_discovery_sessions(self):
    """Validate that the device can create as many discovery sessions as are
    indicated in the device capabilities
    """
    dut = self.android_devices[0]

    # attach
    session_id = dut.droid.wifiAwareAttach(True)
    autils.wait_for_event(dut, aconsts.EVENT_CB_ON_ATTACHED)

    service_name_template = 'GoogleTestService-%s-%d'

    # start the max number of publish sessions
    for i in range(dut.aware_capabilities[aconsts.CAP_MAX_PUBLISHES]):
      # create publish discovery session of both types
      pub_disc_id = self.start_discovery_session(
          dut, session_id, True, aconsts.PUBLISH_TYPE_UNSOLICITED
          if i % 2 == 0 else aconsts.PUBLISH_TYPE_SOLICITED,
          service_name_template % ('pub', i), True)

    # start the max number of subscribe sessions
    for i in range(dut.aware_capabilities[aconsts.CAP_MAX_SUBSCRIBES]):
      # create publish discovery session of both types
      sub_disc_id = self.start_discovery_session(
          dut, session_id, False, aconsts.SUBSCRIBE_TYPE_PASSIVE
          if i % 2 == 0 else aconsts.SUBSCRIBE_TYPE_ACTIVE,
          service_name_template % ('sub', i), True)

    # start another publish & subscribe and expect failure
    self.start_discovery_session(dut, session_id, True,
                                 aconsts.PUBLISH_TYPE_UNSOLICITED,
                                 service_name_template % ('pub', 900), False)
    self.start_discovery_session(dut, session_id, False,
                                 aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                 service_name_template % ('pub', 901), False)

    # delete one of the publishes and try again (see if can create subscribe
    # instead - should not)
    dut.droid.wifiAwareDestroyDiscoverySession(pub_disc_id)
    self.start_discovery_session(dut, session_id, False,
                                 aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                 service_name_template % ('pub', 902), False)
    self.start_discovery_session(dut, session_id, True,
                                 aconsts.PUBLISH_TYPE_UNSOLICITED,
                                 service_name_template % ('pub', 903), True)

    # delete one of the subscribes and try again (see if can create publish
    # instead - should not)
    dut.droid.wifiAwareDestroyDiscoverySession(sub_disc_id)
    self.start_discovery_session(dut, session_id, True,
                                 aconsts.PUBLISH_TYPE_UNSOLICITED,
                                 service_name_template % ('pub', 904), False)
    self.start_discovery_session(dut, session_id, False,
                                 aconsts.SUBSCRIBE_TYPE_ACTIVE,
                                 service_name_template % ('pub', 905), True)
