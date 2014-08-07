#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- Google, Inc.
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

def network_matches(network, target_id):
  s1 = False
  s2 = False
  if 'bssid' in network and network['bssid']==target_id:
    s1 = True
  if 'ssid' in network and network['ssid']==target_id:
    s2 = True
  return s1 or s2

def has_network(network_list, target_id):
  for item in network_list:
    if network_matches(item, target_id):
      return True
  return False

def wifi_toggle_state(droid, ed, new_state):
  if new_state != droid.wifiCheckState():
    droid.wifiStartTrackingStateChange()
    droid.wifiToggleState(new_state)
    event = ed.pop_event("SupplicantConnectionChanged", 10)
    assert event['data']['Connected'] == new_state
    droid.wifiStopTrackingStateChange()

def reset_wifi(droid):
  droid.wifiToggleState(True)
  ''' Forget all configured networks '''
  networks = droid.wifiGetConfiguredNetworks()
  for n in networks:
    droid.wifiForgetNetwork(n['networkId'])
