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

import itertools
import os
import threading
import time

from base_test import BaseTestClass
from test_utils.utils import find_field
from test_utils.wifi_test_utils import has_network
from test_utils.wifi_test_utils import network_matches
from test_utils.wifi_test_utils import reset_droid_wifi
from test_utils.wifi_test_utils import start_wifi_connection_scan
from test_utils.wifi_test_utils import wifi_toggle_state

class WifiManagerTest(BaseTestClass):
  TAG = "WifiManagerTest"
  log_path = BaseTestClass.log_path + TAG + '/'

  def __init__(self, controllers):
    self.tests = (
             "test_toggle_state",
             "test_scan",
             "test_add_network",
             "test_connect_to_open_network",
             "test_connect_with_password",
            )
    BaseTestClass.__init__(self, self.TAG, controllers)
    # ssid of the wifi that is supposed to be discovered by scans
    self.reference_wifi_name = "GoogleGuest"

  def connect_to_wifi_network_with_password(self, params):
    (network_name, passwd), (droid, ed) = params
    start_wifi_connection_scan(droid, ed)
    droid.wifiStartTrackingStateChange()
    if not droid.wifiConnectWPA(network_name, passwd):
      self.log.error("Failed to connect to " + network_name)
      return False
    ed.clear_all_events()
    connect_result = ed.pop_event("WifiNetworkConnected")
    droid.wifiStopTrackingStateChange()
    self.log.debug(connect_result)
    result = network_matches(connect_result['data'], network_name)
    reset_droid_wifi(droid, ed)
    self.log.debug(result)
    return result

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
    start_wifi_connection_scan(self.droid, self.ed)
    wifi_results = self.droid.wifiGetScanResults()
    self.log.debug("Scan results:")
    self.log.debug(wifi_results)
    return has_network(wifi_results, self.reference_wifi_name)

  def test_add_network(self):
    """ Test wifi connection scan. """
    reset_droid_wifi(self.droid, self.ed)
    nId = self.droid.wifiAddNetwork(self.reference_wifi_name)
    if nId == -1:
      self.log.error("Failed to add network.")
      return False
    configured_networks = self.droid.wifiGetConfiguredNetworks()
    self.log.debug("Configured networks after adding:")
    self.log.debug(configured_networks)
    return has_network(configured_networks, self.reference_wifi_name)

  def test_connect_to_open_network(self):
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
    reset_droid_wifi(self.droid, self.ed)
    return result

  def test_connect_with_password(self):
    credentials = [("Test_40", "hahahaha")]
    for ed in self.eds:
      if not ed.started:
        ed.start()
    droids = zip(self.droids, self.eds)
    params = list(itertools.product(credentials, droids))
    failed = self.run_generated_testcases("Wifi connection test",
                                    self.connect_to_wifi_network_with_password,
                                    params)
    self.log.debug("Failed ones: " + str(failed))
    if failed:
      return False
    return True

  def test_iot_with_password(self):
    credentials = [("AirPort Extreme", "hahahaha"),
                   ("AirPort Express", "hahahaha"),
                   ("Linksys_wrt1900_2GHz", "hahahaha"),
                   ("Linksys_wrt1900_5GHz", "hahahaha"),
                   ("Asus_ac2400_2GHz", "hahahaha"),
                   ("Asus_ac2400_5GHz", "hahahaha"),
                   ("Netgear_r6200_2GHz", "hahahaha"),
                   ("Netgear_r6200_5GHz", "hahahaha")]
    for ed in self.eds:
      if not ed.start:
        ed.start()
    droids = zip(self.droids, self.eds)
    params = list(itertools.product(credentials, droids))
    failed = self.run_generated_testcases("Wifi connection test",
                                    self.connect_to_wifi_network_with_password,
                                    params)
    self.log.debug("Failed ones: " + str(failed))
    if failed:
      return False
    return True
  """ Tests End """

if __name__ == "__main__":
  tester = WifiManagerTest()
  tester.run()

