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
from acts.test_utils.wifi.rtt import rtt_const as rconsts
from acts.test_utils.wifi.rtt import rtt_test_utils as rutils


class RttBaseTest(BaseTestClass):

  def __init__(self, controllers):
    super(RttBaseTest, self).__init__(controllers)

  def setup_test(self):
    required_params = ("rtt_reference_distance_mm",)
    self.unpack_userparams(required_params)

    for ad in self.android_devices:
      asserts.skip_if(
          not ad.droid.doesDeviceSupportWifiRttFeature(),
          "Device under test does not support Wi-Fi RTT - skipping test")
      wutils.wifi_toggle_state(ad, True)
      rtt_avail = ad.droid.wifiIsRttAvailable()
      if not rtt_avail:
          self.log.info('RTT not available. Waiting ...')
          rutils.wait_for_event(ad, rconsts.BROADCAST_WIFI_RTT_AVAILABLE)
      ad.ed.clear_all_events()

  def teardown_test(self):
    for ad in self.android_devices:
      if not ad.droid.doesDeviceSupportWifiRttFeature():
        return

      # clean-up queue from the System Service UID
      ad.droid.wifiRttCancelRanging([1000])
