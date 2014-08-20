#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014 - The Android Open Source Project
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

import threading, time, os
from base_test import BaseTestClass
from test_utils.wifi_test_utils import *
from test_utils.utils import *
from queue import Empty

class WifiManagerTest(BaseTestClass):
  TAG = "WifiManagerTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  def __init__(self, controllers):
    BaseTestClass.__init__(self, self.TAG, controllers)
    # ssid of the wifi that is supposed to be discovered by scans
    self.reference_wifi_name = "GoogleGuest"
    self.tests = (
             self.test_toggle_state,
             self.test_scan,
             self.test_add_network,
             self.test_enable_network,
            )

  """ Tests Begin """
  def test_toggle_state(self):
    """ Test wifi can be turned on/off properly"""
    self.log.debug("Going from on to off.")
    wifi_toggle_state(self.droid, self.ed, False)
    self.log.debug("Going from off to on.")
    wifi_toggle_state(self.droid, self.ed, True)
    return True

  def test_scan(self):
    """ Test wifi connection scan can start and find expected networks. """
    wifi_toggle_state(self.droid, self.ed, True)
    self.log.debug("Start regular wifi scan.")
    self.droid.wifiStartScan()
    try:
      self.ed.pop_event("WifiScanFinished")
    except Empty:
      self.log.error("Wifi connection scan timed out.")
      return False
    wifi_results = self.droid.wifiGetScanResults()
    self.log.debug("Scan results:")
    self.log.debug(wifi_results)
    return has_network(wifi_results, self.reference_wifi_name)

  def test_add_network(self):
    """ Test wifi connection scan. """
    reset_wifi(self.droid)
    nId = self.droid.wifiAddNetwork(self.reference_wifi_name)
    if nId == -1:
      self.log.error("Failed to add network.")
      return False
    configured_networks = self.droid.wifiGetConfiguredNetworks()
    self.log.debug("Configured networks after adding:")
    self.log.debug(configured_networks)
    return has_network(configured_networks, self.reference_wifi_name)

  def test_enable_network(self):
    self.droid.wifiStartTrackingStateChange()
    configured_networks = self.droid.wifiGetConfiguredNetworks()
    net_id = find_field(configured_networks,
                        self.reference_wifi_name,
                        network_matches,
                        "networkId")
    self.log.debug("Network Id is " + str(net_id))
    if not self.droid.wifiEnableNetwork(net_id, True):
      self.log.error("Failed to enable wifi network.")
      return False
    connect_result = self.ed.pop_event("WifiNetworkConnected")
    self.droid.wifiStopTrackingStateChange()
    self.log.debug(connect_result)
    result = network_matches(connect_result['data'], self.reference_wifi_name)
    reset_wifi(self.droid)
    return result
  """ Tests End """

if __name__ == "__main__":
  tester = WifiManagerTest()
  tester.run()

