#!/usr/bin/env python3
#
#   Copyright 2018 Google, Inc.
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

import logging
import os
import pprint
import time

from enum import IntEnum
from queue import Empty

from acts import asserts
from acts import signals
from acts import utils
from acts.test_utils.wifi.p2p import wifi_p2p_const as p2pconsts
import acts.utils

def is_discovered(event, ad):
    """Check an Android device exist in WifiP2pOnPeersAvailable event or not.

    Args:
        event: WifiP2pOnPeersAvailable which include all of p2p devices.
        ad: The android device
    Returns:
        True: if an Android device exist in p2p list
        False: if not exist
    """
    for device in event['data']['Peers']:
        if device['Name'] == ad.name:
            ad.deviceAddress = device['Address']
            return True
    return False

def check_disconnect(ad):
    """Check an Android device disconnect or not

    Args:
        ad: The android device
    """
    ad.droid.wifiP2pRequestConnectionInfo()
    # wait disconnect event
    ad.ed.pop_event(p2pconsts.DISCONNECTED_EVENT,
            p2pconsts.DEFAULT_TIMEOUT)


def p2p_disconnect(ad):
    """Invoke an Android device removeGroup to trigger p2p disconnect

    Args:
        ad: The android device
    """
    ad.log.debug("Disconnect")
    ad.droid.wifiP2pRemoveGroup()
    check_disconnect(ad)

def p2p_connection_ping_test(ad, target_ip_address):
    """Let an Android device to start ping target_ip_address

    Args:
        ad: The android device
        target_ip_address: ip address which would like to ping
    """
    ad.log.debug("Run Ping Test, %s ping %s "% (ad.serial, target_ip_address))
    asserts.assert_true(
            acts.utils.adb_shell_ping(ad, count=3, dest_ip=target_ip_address,
            timeout=20),"%s ping failed" % (ad.serial))

def is_go(ad):
    """Check an Android p2p role is Go or not

    Args:
        ad: The android device
    Return:
        True: An Android device is p2p  go
        False: An Android device is p2p gc
    """
    ad.log.debug("is go check")
    ad.droid.wifiP2pRequestConnectionInfo()
    ad_connect_info_event = ad.ed.pop_event(
            p2pconsts.CONNECTION_INFO_AVAILABLE_EVENT,
            p2pconsts.DEFAULT_TIMEOUT)
    if ad_connect_info_event['data']['isGroupOwner']:
        return True
    return False

#trigger p2p connect to ad2 from ad1
def p2p_connect(ad1, ad2, isReconnect, wpsSetup):
    """trigger p2p connect to ad2 from ad1

    Args:
        ad1: The android device
        ad2: The android device
        isReconnect: boolean, if persist group is exist,
                isReconnect is true, otherswise is false.
        wpsSetup: which wps connection would like to use
    """
    ad1.log.info("Create p2p connection from %s to %s via wps: %s" %
            (ad1.name, ad2.name, wpsSetup))
    find_p2p_device(ad1, ad2)
    time.sleep(p2pconsts.DEFAULT_SLEEPTIME)
    wifi_p2p_config = {WifiP2PEnums.WifiP2pConfig.DEVICEADDRESS_KEY:
            ad2.deviceAddress, WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY:
            {WifiP2PEnums.WpsInfo.WPS_SETUP_KEY: wpsSetup}}
    ad1.droid.wifiP2pConnect(wifi_p2p_config)
    ad1.ed.pop_event(p2pconsts.CONNECT_SUCCESS_EVENT,
            p2pconsts.DEFAULT_TIMEOUT)
    time.sleep(p2pconsts.DEFAULT_SLEEPTIME)
    if not isReconnect:
        ad1.droid.requestP2pPeerConfigure()
        ad1_peerConfig = ad1.ed.pop_event(
                p2pconsts.ONGOING_PEER_INFO_AVAILABLE_EVENT,
                p2pconsts.DEFAULT_TIMEOUT)
        ad1.log.debug(ad1_peerConfig['data'])
        ad2.droid.requestP2pPeerConfigure()
        ad2_peerConfig = ad2.ed.pop_event(
                p2pconsts.ONGOING_PEER_INFO_AVAILABLE_EVENT,
                p2pconsts.DEFAULT_TIMEOUT)
        ad2.log.debug(ad2_peerConfig['data'])
        if wpsSetup == WifiP2PEnums.WpsInfo.WIFI_WPS_INFO_DISPLAY:
              asserts.assert_true(WifiP2PEnums.WpsInfo.WPS_PIN_KEY
                      in ad1_peerConfig['data'][
                      WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY],
                      "Can't get pin value");
              ad2_peerConfig['data'][WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY][
                      WifiP2PEnums.WpsInfo.WPS_PIN_KEY] = ad1_peerConfig[
                      'data'][WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY][
                      WifiP2PEnums.WpsInfo.WPS_PIN_KEY]
              ad2.droid.setP2pPeerConfigure(ad2_peerConfig['data'])
              ad2.ed.pop_event(p2pconsts.ONGOING_PEER_SET_SUCCESS_EVENT,
                      p2pconsts.DEFAULT_TIMEOUT);
              ad2.droid.wifiP2pAcceptConnection()
        elif wpsSetup == WifiP2PEnums.WpsInfo.WIFI_WPS_INFO_KEYPAD:
              asserts.assert_true( WifiP2PEnums.WpsInfo.WPS_PIN_KEY
                      in ad2_peerConfig['data'][
                      WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY],
                      "Can't get pin value");
              ad1_peerConfig['data'][WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY][
                      WifiP2PEnums.WpsInfo.WPS_PIN_KEY] = ad2_peerConfig[
                      'data'][WifiP2PEnums.WifiP2pConfig.WPSINFO_KEY][
                      WifiP2PEnums.WpsInfo.WPS_PIN_KEY]
              ad1.droid.setP2pPeerConfigure(ad1_peerConfig['data'])
              ad1.ed.pop_event(p2pconsts.ONGOING_PEER_SET_SUCCESS_EVENT,
                      p2pconsts.DEFAULT_TIMEOUT)
              #Need to Accpet first in ad1 to avoid connect time out in ad2,
              #the timeout just 1 sec in ad2
              ad1.droid.wifiP2pAcceptConnection()
              time.sleep(p2pconsts.DEFAULT_SLEEPTIME)
              ad2.droid.wifiP2pConfirmConnection()
        elif wpsSetup == WifiP2PEnums.WpsInfo.WIFI_WPS_INFO_PBC:
              ad2.droid.wifiP2pAcceptConnection()

    #wait connected event
    ad1.ed.pop_event(p2pconsts.CONNECTED_EVENT,
            p2pconsts.DEFAULT_TIMEOUT)
    ad2.ed.pop_event(p2pconsts.CONNECTED_EVENT,
            p2pconsts.DEFAULT_TIMEOUT)

def find_p2p_device(ad1, ad2):
    """Check an Android device ad1 can discover an Android device ad2

    Args:
        ad1: The android device
        ad2: The android device
    """
    ad1.droid.wifiP2pDiscoverPeers()
    ad2.droid.wifiP2pDiscoverPeers()
    p2p_find_result = False
    while  not p2p_find_result:
        ad1_event = ad1.ed.pop_event(p2pconsts.PEER_AVAILABLE_EVENT,
                p2pconsts.P2P_FIND_TIMEOUT)
        ad1.log.debug(ad1_event['data'])
        p2p_find_result = is_discovered(ad1_event, ad2)
    asserts.assert_true(p2p_find_result,
            "DUT didn't discovered peer:%s device"% (ad2.name))

class WifiP2PEnums():

    class WifiP2pConfig():
        DEVICEADDRESS_KEY = "deviceAddress"
        WPSINFO_KEY = "wpsInfo"
        GO_INTENT_KEY = "groupOwnerIntent"
        NETID_KEY = "netId"

    class WpsInfo():
        WPS_SETUP_KEY = "setup"
        BSSID_KEY = "BSSID"
        WPS_PIN_KEY = "pin"
        #TODO: remove it from wifi_test_utils.py
        WIFI_WPS_INFO_PBC = 0
        WIFI_WPS_INFO_DISPLAY = 1
        WIFI_WPS_INFO_KEYPAD = 2
        WIFI_WPS_INFO_LABEL = 3
        WIFI_WPS_INFO_INVALID = 4

    class WifiP2pServiceInfo():
        #TODO: remove it from wifi_test_utils.py
        # Macros for wifi p2p.
        WIFI_P2P_SERVICE_TYPE_ALL = 0
        WIFI_P2P_SERVICE_TYPE_BONJOUR = 1
        WIFI_P2P_SERVICE_TYPE_UPNP = 2
        WIFI_P2P_SERVICE_TYPE_VENDOR_SPECIFIC = 255
