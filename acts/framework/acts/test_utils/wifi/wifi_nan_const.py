#!/usr/bin/env python3.4
#
#   Copyright 2016 - Google
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
# Broadcast events
######################################################
BROADCAST_WIFI_NAN_ENABLED = "WifiNanEnabled"
BROADCAST_WIFI_NAN_DISABLED = "WifiNanDisabled"

######################################################
# ConfigRequest keys
######################################################

CONFIG_KEY_5G_BAND = "Support5gBand"
CONFIG_KEY_MASTER_PREF = "MasterPreference"
CONFIG_KEY_CLUSTER_LOW = "ClusterLow"
CONFIG_KEY_CLUSTER_HIGH = "ClusterHigh"
CONFIG_KEY_ENABLE_IDEN_CB = "EnableIdentityChangeCallback"

######################################################
# PublishConfig keys
######################################################

PUBLISH_KEY_SERVICE_NAME = "ServiceName"
PUBLISH_KEY_SSI = "ServiceSpecificInfo"
PUBLISH_KEY_MATCH_FILTER = "MatchFilter"
PUBLISH_KEY_TYPE = "PublishType"
PUBLISH_KEY_COUNT = "PublishCount"
PUBLISH_KEY_TTL = "TtlSec"
PUBLISH_KEY_ENABLE_TERM_CB = "EnableTerminateNotification"

######################################################
# SubscribeConfig keys
######################################################

SUBSCRIBE_KEY_SERVICE_NAME = "ServiceName"
SUBSCRIBE_KEY_SSI = "ServiceSpecificInfo"
SUBSCRIBE_KEY_MATCH_FILTER = "MatchFilter"
SUBSCRIBE_KEY_TYPE = "SubscribeType"
SUBSCRIBE_KEY_COUNT = "SubscribeCount"
SUBSCRIBE_KEY_TTL = "TtlSec"
SUBSCRIBE_KEY_STYLE = "MatchStyle"
SUBSCRIBE_KEY_ENABLE_TERM_CB = "EnableTerminateNotification"

######################################################
# WifiNanEventCallback events
######################################################
EVENT_CB_ON_CONNECT_SUCCSSS = "WifiNanOnConnectSuccess"
EVENT_CB_ON_CONNECT_FAIL = "WifiNanOnConnectFail"
EVENT_CB_ON_IDENTITY_CHANGED = "WifiNanOnIdentityChanged"

# WifiNanEventCallback events keys
EVENT_CB_KEY_REASON = "reason"
EVENT_CB_KEY_MAC = "mac"

######################################################
# WifiNanSessionCallback events
######################################################
SESSION_CB_ON_PUBLISH_STARTED = "WifiNanSessionOnPublishStarted"
SESSION_CB_ON_SUBSCRIBE_STARTED = "WifiNanSessionOnSubscribeStarted"
SESSION_CB_ON_SESSION_CONFIG_SUCCESS = "WifiNanSessionOnSessionConfigSuccess"
SESSION_CB_ON_SESSION_CONFIG_FAIL = "WifiNanSessionOnSessionConfigFail"
SESSION_CB_ON_SESSION_TERMINATED = "WifiNanSessionOnSessionTerminated"
SESSION_CB_ON_MATCH = "WifiNanSessionOnMatch"
SESSION_CB_ON_MESSAGE_SEND_SUCCESS = "WifiNanSessionOnMessageSendSuccess"
SESSION_CB_ON_MESSAGE_SEND_FAIL = "WifiNanSessionOnMessageSendFail"
SESSION_CB_ON_MESSAGE_RECEIVED = "WifiNanSessionOnMessageReceived"

# WifiNanSessionCallback events keys
SESSION_CB_KEY_CB_ID = "callbackId"
SESSION_CB_KEY_SESSION_ID = "sessionId"
SESSION_CB_KEY_REASON = "reason"
SESSION_CB_KEY_PEER_ID = "peerId"
SESSION_CB_KEY_SERVICE_SPECIFIC_INFO = "serviceSpecificInfo"
SESSION_CB_KEY_MATCH_FILTER = "matchFilter"
SESSION_CB_KEY_MESSAGE = "message"
SESSION_CB_KEY_MESSAGE_AS_STRING = "messageAsString"

######################################################
# WifiNanRangingListener events (RttManager.RttListener)
######################################################
RTT_LISTENER_CB_ON_SUCCESS = "WifiNanRangingListenerOnSuccess"
RTT_LISTENER_CB_ON_FAILURE = "WifiNanRangingListenerOnFailure"
RTT_LISTENER_CB_ON_ABORT = "WifiNanRangingListenerOnAborted"

# WifiNanRangingListener events (RttManager.RttListener) keys
RTT_LISTENER_CB_KEY_CB_ID = "callbackId"
RTT_LISTENER_CB_KEY_SESSION_ID = "sessionId"
RTT_LISTENER_CB_KEY_RESULTS = "Results"
RTT_LISTENER_CB_KEY_REASON = "reason"
RTT_LISTENER_CB_KEY_DESCRIPTION = "description"

######################################################

# NAN Data-Path Constants
DATA_PATH_INITIATOR = 0
DATA_PATH_RESPONDER = 1

# Maximum send retry
MAX_TX_RETRIES = 5
