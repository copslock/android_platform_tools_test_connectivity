#!/usr/bin/env python3.4
#
#   Copyright 2017 - Google
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
from acts.base_test import BaseTestClass
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.wifi.aware import aware_const as aconsts
from acts.test_utils.wifi.aware import aware_test_utils as autils


class AwareBaseTest(BaseTestClass):
  def __init__(self, controllers):
    BaseTestClass.__init__(self, controllers)

  # message ID counter to make sure all uses are unique
  msg_id = 0

  def setup_test(self):
    for ad in self.android_devices:
      wutils.wifi_toggle_state(ad, True)
      aware_avail = ad.droid.wifiIsAwareAvailable()
      if not aware_avail:
        self.log.info('Aware not available. Waiting ...')
        autils.wait_for_event(ad, aconsts.BROADCAST_WIFI_AWARE_AVAILABLE)
      ad.aware_capabilities = autils.get_aware_capabilities(ad)
      self.reset_device(ad)

  def teardown_test(self):
    for ad in self.android_devices:
      ad.droid.wifiAwareDestroyAll()
      self.reset_device(ad)

  def reset_device(self, ad):
    """Reset device configurations which may have been set by tests. Should be
    done before tests start (in case previous one was killed without tearing
    down) and after they end (to leave device in usable state).

    Args:
      ad: device to be reset
    """
    ad.adb.shell("cmd wifiaware native_api set mac_random_interval_sec 1800")

  def get_next_msg_id(self):
    """Increment the message ID and returns the new value. Guarantees that
    each call to the method returns a unique value.

    Returns: a new message id value.
    """
    self.msg_id = self.msg_id + 1
    return self.msg_id
