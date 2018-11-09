#!/usr/bin/env python3
#
#   Copyright 2018 - Google
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

######################################################
# Wifi P2p framework designed value
######################################################
P2P_FIND_TIMEOUT = 120
GO_IP_ADDRESS = '192.168.49.1'

######################################################
# Wifi P2p Acts flow control timer value
######################################################

DEFAULT_TIMEOUT = 30
DEFAULT_SLEEPTIME = 5
DEFAULT_FUNCTION_SWITCH_TIME = 10

######################################################
# Wifi P2p sl4a Event String
######################################################
CONNECTED_EVENT = "WifiP2pConnected"
DISCONNECTED_EVENT = "WifiP2pDisconnected"
PEER_AVAILABLE_EVENT = "WifiP2pOnPeersAvailable"
CONNECTION_INFO_AVAILABLE_EVENT = "WifiP2pOnConnectionInfoAvailable"
ONGOING_PEER_INFO_AVAILABLE_EVENT = "WifiP2pOnOngoingPeerAvailable"
ONGOING_PEER_SET_SUCCESS_EVENT = "WifiP2psetP2pPeerConfigureOnSuccess"
CONNECT_SUCCESS_EVENT = "WifiP2pConnectOnSuccess"
