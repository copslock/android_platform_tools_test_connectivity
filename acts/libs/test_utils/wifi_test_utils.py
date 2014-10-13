#!/usr/bin/python3.4
#
#   Copyright 2014 Google, Inc.
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

from enum import Enum
import json
from queue import Empty
# Number of seconds to wait for events that are supposed to happen quickly.
# Like onSuccess for start background scan and confirmation on wifi state
# change.

class WifiEnums():
    SHORT_TIMEOUT = 10
    # Macros for wifi p2p.
    WIFI_P2P_SERVICE_TYPE_ALL = 0
    WIFI_P2P_SERVICE_TYPE_BONJOUR = 1
    WIFI_P2P_SERVICE_TYPE_UPNP = 2
    WIFI_P2P_SERVICE_TYPE_VENDOR_SPECIFIC = 255
    # Macros as specified in the WifiScanner code.
    WIFI_BAND_UNSPECIFIED = 0      # not specified
    WIFI_BAND_24_GHZ = 1           # 2.4 GHz band
    WIFI_BAND_5_GHZ = 2            # 5 GHz band without DFS channels
    WIFI_BAND_5_GHZ_DFS_ONLY  = 4  # 5 GHz band with DFS channels
    WIFI_BAND_5_GHZ_WITH_DFS  = 6  # 5 GHz band with DFS channels
    WIFI_BAND_BOTH = 3             # both bands without DFS channels
    WIFI_BAND_BOTH_WITH_DFS = 7    # both bands with DFS channels

    REPORT_EVENT_AFTER_BUFFER_FULL = 0
    REPORT_EVENT_AFTER_EACH_SCAN = 1
    REPORT_EVENT_FULL_SCAN_RESULT = 2

    # US Wifi frequencies
    ALL_2G_FREQUENCIES = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452,
                          2457, 2462]
    DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520, 5540, 5560, 5580,
                          5660, 5680, 5700]
    NONE_DFS_5G_FREQUENCIES = [5180, 5200, 5220, 5240, 5745, 5765, 5785, 5805,
                               5825]
    ALL_5G_FREQUENCIES = DFS_5G_FREQUENCIES + NONE_DFS_5G_FREQUENCIES

    band_to_frequencies = {
      WIFI_BAND_24_GHZ: ALL_2G_FREQUENCIES,
      WIFI_BAND_5_GHZ: NONE_DFS_5G_FREQUENCIES,
      WIFI_BAND_5_GHZ_DFS_ONLY: DFS_5G_FREQUENCIES,
      WIFI_BAND_5_GHZ_WITH_DFS: ALL_5G_FREQUENCIES,
      WIFI_BAND_BOTH: ALL_2G_FREQUENCIES + NONE_DFS_5G_FREQUENCIES,
      WIFI_BAND_BOTH_WITH_DFS: ALL_5G_FREQUENCIES + ALL_2G_FREQUENCIES
    }

    # All Wifi frequencies to channels lookup.
    freq_to_channel = {
        2412: 1,
        2417: 2,
        2422: 3,
        2427: 4,
        2432: 5,
        2437: 6,
        2442: 7,
        2447: 8,
        2452: 9,
        2457: 10,
        2462: 11,
        2467: 12,
        2472: 13,
        2484: 14,
        4915: 183,
        4920: 184,
        4925: 185,
        4935: 187,
        4940: 188,
        4945: 189,
        4960: 192,
        4980: 196,
        5035: 7,
        5040: 8,
        5045: 9,
        5055: 11,
        5060: 12,
        5080: 16,
        5170: 34,
        5180: 36,
        5190: 38,
        5200: 40,
        5210: 42,
        5220: 44,
        5230: 46,
        5240: 48,
        5260: 52,
        5280: 56,
        5300: 60,
        5320: 64,
        5500: 100,
        5520: 104,
        5540: 108,
        5560: 112,
        5580: 116,
        5600: 120,
        5620: 124,
        5640: 128,
        5660: 132,
        5680: 136,
        5700: 140,
        5745: 149,
        5765: 153,
        5785: 157,
        5805: 161,
        5825: 165,
    }

    # All Wifi channels to frequencies lookup.
    channel_2G_to_freq = {
        1: 2412,
        2: 2417,
        3: 2422,
        4: 2427,
        5: 2432,
        6: 2437,
        7: 2442,
        8: 2447,
        9: 2452,
        10: 2457,
        11: 2462,
        12: 2467,
        13: 2472,
        14: 2484
    }

    channel_5G_to_freq = {
        183: 4915,
        184: 4920,
        185: 4925,
        187: 4935,
        188: 4940,
        189: 4945,
        192: 4960,
        196: 4980,
        7: 5035,
        8: 5040,
        9: 5045,
        11: 5055,
        12: 5060,
        16: 5080,
        34: 5170,
        36: 5180,
        38: 5190,
        40: 5200,
        42: 5210,
        44: 5220,
        46: 5230,
        48: 5240,
        52: 5260,
        56: 5280,
        60: 5300,
        64: 5320,
        100: 5500,
        104: 5520,
        108: 5540,
        112: 5560,
        116: 5580,
        120: 5600,
        124: 5620,
        128: 5640,
        132: 5660,
        136: 5680,
        140: 5700,
        149: 5745,
        153: 5765,
        157: 5785,
        161: 5805,
        165: 5825
    }

class WifiTestUtilsError(Exception):
    pass

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

def wifi_toggle_state(droid, ed, new_state=None):
  """Toggles the state of wifi.

  Params:
    droid: Sl4a session to use.
    ed: event_dispatcher associated with the sl4a session.
    new_state: Wifi state to set to. If None, opposite of the current state.
  """
  # Check if the new_state is already achieved, so we don't wait for the
  # state change event by mistake.
  if new_state == droid.wifiCheckState():
    return True
  droid.wifiStartTrackingStateChange()
  droid.wifiToggleState(new_state)
  event = ed.pop_event("SupplicantConnectionChanged", WifiEnums.SHORT_TIMEOUT)
  assert event['data']['Connected'] == new_state
  droid.wifiStopTrackingStateChange()

def reset_droid_wifi(droid, ed):
  """Disconnects and removes all configured Wifi networks on an android device.

  Params:
    droid: Sl4a session to use.
    ed: Event dispatcher instance associated with the sl4a session.

  Raises:
    WIFIUTILError if forget network operation failed.
  """
  droid.wifiToggleState(True)
  networks = droid.wifiGetConfiguredNetworks()
  if not networks:
    return
  for n in networks:
    droid.wifiForgetNetwork(n['networkId'])
    try:
      event = ed.pop_event("WifiManagerForgetNetworkOnSuccess",
                           WifiEnums.SHORT_TIMEOUT)
    except Empty:
      raise WifiTestUtilsError("Failed to remove network " + str(n))

def sort_wifi_scan_results(results, key="level"):
  """Sort wifi scan results by key.

  Params:
    results: A list of results to sort.
    key: Name of the field to sort the results by.

  Returns:
    A list of results in sorted order.
  """
  return sorted(results, lambda d: (key not in d, d[key]))

def start_wifi_connection_scan(droid, ed):
    """Starts a wifi connection scan and wait for results to become available.

    Params:
    droid: Sl4a session to use.
    ed: Event dispatcher instance associated with the sl4a session.
    """
    droid.wifiStartScan()
    ed.pop_event("WifiManagerScanResultsAvailable", 60)

def start_wifi_background_scan(droid, ed, scan_setting):
    idx = droid.wifiScannerStartScan(json.dumps(scan_setting))
    event = ed.pop_event("WifiScannerScan" + str(idx) + "onSuccess",
                         WifiEnums.SHORT_TIMEOUT)
    return idx

def start_wifi_tracking_change(droid, ed, log):
    idx = droid.wifiScannerStartTrackingChange()
    event = ed.pop_event("WifiScannerChange" + str(idx) + "onSuccess",
                         WifiEnums.SHORT_TIMEOUT)
    return idx
