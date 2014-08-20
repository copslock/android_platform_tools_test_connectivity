# python3.4
# Copyright (C) 2014 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import threading, time, os, traceback
from queue import Empty

from base_test import BaseTestClass
from ap.access_point import AP
from test_utils.wifi_test_utils import *
from test_utils.utils import *

RTT_TYPE_UNSPECIFIED    = 0;
RTT_TYPE_ONE_SIDED      = 1;
RTT_TYPE_11_V           = 2;
RTT_TYPE_11_MC          = 4;

RTT_PEER_TYPE_UNSPECIFIED    = 0;
RTT_PEER_TYPE_AP             = 1;
RTT_PEER_TYPE_STA            = 2; # Requires NAN.

RTT_CHANNEL_WIDTH_20      = 0;
RTT_CHANNEL_WIDTH_40      = 1;
RTT_CHANNEL_WIDTH_80      = 2;
RTT_CHANNEL_WIDTH_160     = 3;
RTT_CHANNEL_WIDTH_80P80   = 4;
RTT_CHANNEL_WIDTH_5       = 5;
RTT_CHANNEL_WIDTH_10      = 6;
RTT_CHANNEL_WIDTH_UNSPECIFIED = -1;

RTT_STATUS_SUCCESS                  = 0;
RTT_STATUS_FAILURE                  = 1;
RTT_STATUS_FAIL_NO_RSP              = 2;
RTT_STATUS_FAIL_REJECTED            = 3;
RTT_STATUS_FAIL_NOT_SCHEDULED_YET   = 4;
RTT_STATUS_FAIL_TM_TIMEOUT          = 5;
RTT_STATUS_FAIL_AP_ON_DIFF_CHANNEL  = 6;
RTT_STATUS_FAIL_NO_CAPABILITY       = 7;
RTT_STATUS_ABORTED                  = 8;

REASON_UNSPECIFIED              = -1;
REASON_NOT_AVAILABLE            = -2;
REASON_INVALID_LISTENER         = -3;
REASON_INVALID_REQUEST          = -4;

DESCRIPTION_KEY  = "android.net.wifi.RttManager.Description";

class WifiRTTRangingError (Exception):
   """Error in WifiScanner RTT."""

class WifiRttManagerTest(BaseTestClass):
  """Tests for wifi's RttManager APIs."""
  TAG = "WifiRttManagerTest"
  log_path = BaseTestClass.log_path + TAG + '/'
  tests = None
  MAX_RTT_AP = 10
  RttParamDefault = {"deviceType": RTT_PEER_TYPE_AP,
                     "requestType": RTT_TYPE_ONE_SIDED,
                     "bssid": None,
                     "frequency": 2462,
                     "channelWidth": RTT_CHANNEL_WIDTH_20,
                     "num_samples": 20,
                     "num_retries": 10}

  def __init__(self, android_devices):
    BaseTestClass.__init__(self, self.TAG, android_devices)
    self.tests = (self.test_rtt_ranging,)

  """Helper Functions"""
  def find_surrounding_wifi_networks(self):
    wifi_toggle_state(self.droid, self.ed, True)
    self.log.debug("Start regular wifi scan.")
    self.droid.wifiStartScan()
    self.ed.pop_event("WifiScanFinished")
    wifi_networks = self.droid.wifiGetScanResults()
    results = []
    for i, n in enumerate(wifi_networks):
      if i == self.MAX_RTT_AP:
        break
      results.append((n["bssid"],n["frequency"]))
    return results

  """Tests"""
  def test_rtt_ranging(self):
    """Takes first ten or less wifi networks visible and call Rtt ranging on
    them.
    """
    self.log.debug("Look for wifi networks.")
    ap_list = self.find_surrounding_wifi_networks()
    rtt_params = []
    self.log.debug("Found:\n" + str(ap_list) + "\nConstruct Rtt Params.")
    for ap in ap_list:
      self.RttParamDefault["bssid"] = ap[0]
      self.RttParamDefault["frequency"] = ap[1]
      rtt_params.append(json.dumps(self.RttParamDefault))
    self.log.debug("Start Rtt Ranging with params: " + str(rtt_params))
    idx = self.droid.wifiRttStartRanging(rtt_params)
    try:
      event = self.ed.pop_event("WifiRttRanging" + str(idx) + "onSuccess", 30)
    except Empty:
      event = self.ed.pop_events("WifiRttRanging", 30)
      self.log.error("Did not get onSuccess, got:\n" + str(event))
      self.log.exception(traceback.format_exc())
      return False
    finally:
      self.droid.wifiRttStopRanging(idx)
    self.log.debug("Successful, got:\n" + str(event))
    return True