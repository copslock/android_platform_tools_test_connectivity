#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
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

###############################################
# TIMERS
###############################################
# Max time to wait for phone data/network connection state update
WAIT_TIME_CONNECTION_STATE_UPDATE = 20

# Max time to wait for network reselection
WAIT_TIME_NW_SELECTION = 120

# Wait time for call drop
WAIT_TIME_CALL_DROP = 60

# Time to wait after call setup before declaring
# that the call is actually successful
WAIT_TIME_IN_CALL = 15

# Time to wait after phone receive incoming call before phone answer this call.
WAIT_TIME_ANSWER_CALL = 2

# Time to wait after phone receive incoming call before phone reject this call.
WAIT_TIME_REJECT_CALL = WAIT_TIME_ANSWER_CALL

# Time to wait after phone receive incoming video call before phone answer this call.
WAIT_TIME_ANSWER_VIDEO_CALL = WAIT_TIME_ANSWER_CALL

# Time to wait after caller make a call and before
# callee start ringing
WAIT_TIME_CALLEE_RINGING = 30

# Time to leave a voice message after callee reject the incoming call
WAIT_TIME_TO_LEAVE_VOICE_MAIL = 30

# Time to wait after caller make a call and before
# callee start ringing
WAIT_TIME_ACCEPT_CALL_TO_OFFHOOK_EVENT = 30

# Time to wait after accept video call and before checking state
WAIT_TIME_ACCEPT_VIDEO_CALL_TO_CHECK_STATE = 2

# Time to wait after ad end a call and before get
# "onCallStatehangedIdle" event
WAIT_TIME_HANGUP_TO_IDLE_EVENT = 30

# Time to wait after toggle airplane mode and before
# get expected event
WAIT_TIME_AIRPLANEMODE_EVENT = 90

# Time to wait after device sent an SMS and before
# get "onSmsSentSuccess" event
WAIT_TIME_SMS_SENT_SUCCESS = 60

# Time to wait after MT SMS was sent and before device
# actually receive this MT SMS.
WAIT_TIME_SMS_RECEIVE = 120

# (For IMS, e.g. VoLTE-VoLTE, WFC-WFC, VoLTE-WFC test only)
# Time to wait after call setup before declaring
# that the call is actually successful
WAIT_TIME_IN_CALL_FOR_IMS = 30

# Time delay to ensure user actions are performed in
# 'human' time rather than at the speed of the script
WAIT_TIME_ANDROID_STATE_SETTLING = 1

# Time to wait after registration to ensure the phone
# has sufficient time to reconfigure based on new network
WAIT_TIME_BETWEEN_REG_AND_CALL = 5

# Time to wait for IMS registration
WAIT_TIME_IMS_REGISTRATION = 120

# Max time to wait after initiating a call for telecom to report in-call
WAIT_TIME_CALL_INITIATION = 15

# Time to wait for 1xrtt voice attach check
# After DUT voice network type report 1xrtt (from unknown), it need to wait for
# several seconds before the DUT can receive incoming call.
WAIT_TIME_FOR_1XRTT_VOICE_ATTACH = 30

# TODO: b/26338156 WAIT_TIME_VOLTE_ENABLED and WAIT_TIME_WFC_ENABLED should only
# be used for wait after IMS registration.

# Max time to wait for VoLTE enabled flag to be True
WAIT_TIME_VOLTE_ENABLED = WAIT_TIME_IMS_REGISTRATION + 20

# Max time to wait for WFC enabled flag to be True
WAIT_TIME_WFC_ENABLED = WAIT_TIME_IMS_REGISTRATION + 50

# Maximum Wait for WiFi Manager to Connect to an AP
WAIT_TIME_WIFI_CONNECTION = 30

# During wifi tethering, wait time for data status change.
WAIT_TIME_FOR_DATA_STATUS_CHANGE_DURING_WIFI_TETHERING = 30

# Maximum Wait time for Video Session Modify Messaging
WAIT_TIME_VIDEO_SESSION_EVENT = 10

# Max time to wait after a network connection for ConnectivityManager to
# report a working user plane data connection
WAIT_TIME_USER_PLANE_DATA = 20

# Timeout value (second) for tethering entitlement check
TETHERING_ENTITLEMENT_CHECK_TIMEOUT = 15

# invalid SIM slot index
INVALID_SIM_SLOT_INDEX = -1

# WiFI RSSI is -127 if WiFi is not connected
INVALID_WIFI_RSSI = -127

# MAX and MIN value for attenuator settings
ATTEN_MAX_VALUE = 90
ATTEN_MIN_VALUE = 0

MAX_RSSI_RESERVED_VALUE = 100
MIN_RSSI_RESERVED_VALUE = -200

# cellular weak RSSI value
CELL_WEAK_RSSI_VALUE = -120
# cellular strong RSSI value
CELL_STRONG_RSSI_VALUE = -70
# WiFi weak RSSI value
WIFI_WEAK_RSSI_VALUE = -80

# Wait time for rssi calibration.
# This is the delay between <WiFi Connected> and <Turn on Screen to get RSSI>.
WAIT_TIME_FOR_WIFI_RSSI_CALIBRATION_WIFI_CONNECTED = 10
# This is the delay between <Turn on Screen> and <Call API to get WiFi RSSI>.
WAIT_TIME_FOR_WIFI_RSSI_CALIBRATION_SCREEN_ON = 2

# These are used in phone_number_formatter
PHONE_NUMBER_STRING_FORMAT_7_DIGIT = 7
PHONE_NUMBER_STRING_FORMAT_10_DIGIT = 10
PHONE_NUMBER_STRING_FORMAT_11_DIGIT = 11
PHONE_NUMBER_STRING_FORMAT_12_DIGIT = 12

# MAX screen-on time during test (in unit of second)
MAX_SCREEN_ON_TIME = 1800

# In Voice Mail box, press this digit to delete one message.
VOICEMAIL_DELETE_DIGIT = '7'
# MAX number of saved voice mail in voice mail box.
MAX_SAVED_VOICE_MAIL = 25
# Time to wait for each operation on voice mail box.
VOICE_MAIL_SERVER_RESPONSE_DELAY = 10
# Time to wait for voice mail count report correct result.
MAX_WAIT_TIME_FOR_VOICE_MAIL_COUNT = 30

# Time to wait after registration to ensure the phone
# has sufficient time to reconfigure based on new network in Anritsu
WAIT_TIME_ANRITSU_REG_AND_CALL = 10

# Time to wait after registration before sending a command to Anritsu
# to ensure the phone has sufficient time to reconfigure based on new
# network in Anritsu
WAIT_TIME_ANRITSU_REG_AND_OPER = 10

# Time to wait for Anritsu's virtual phone state change
WAIT_TIME_FOR_VIRTUAL_PHONE_STATE = 45

# SIM1 slot index
SIM1_SLOT_INDEX = 0

# SIM2 slot index
SIM2_SLOT_INDEX = 1

# Data SIM change time
WAIT_TIME_DATA_SUB_CHANGE = 150

# Wait time for radio to up and running after reboot
WAIT_TIME_AFTER_REBOOT = 10

# Wait time for tethering test after reboot
WAIT_TIME_FOR_TETHERING_AFTER_REBOOT = 10

# invalid Subscription ID
INVALID_SUB_ID = -1

AOSP_PREFIX = "aosp_"

INCALL_UI_DISPLAY_FOREGROUND = "foreground"
INCALL_UI_DISPLAY_BACKGROUND = "background"
INCALL_UI_DISPLAY_DEFAULT = "default"

NETWORK_CONNECTION_TYPE_WIFI = 'wifi'
NETWORK_CONNECTION_TYPE_CELL = 'cell'
NETWORK_CONNECTION_TYPE_MMS = 'mms'
NETWORK_CONNECTION_TYPE_HIPRI = 'hipri'
NETWORK_CONNECTION_TYPE_UNKNOWN = 'unknown'

TETHERING_MODE_WIFI = 'wifi'

NETWORK_SERVICE_VOICE = 'voice'
NETWORK_SERVICE_DATA = 'data'

CARRIER_VZW = 'vzw'
CARRIER_ATT = 'att'
CARRIER_TMO = 'tmo'
CARRIER_SPT = 'spt'
CARRIER_EEUK = 'eeuk'
CARRIER_VFUK = 'vfuk'
CARRIER_UNKNOWN = 'unknown'

RAT_FAMILY_CDMA = 'cdma'
RAT_FAMILY_CDMA2000 = 'cdma2000'
RAT_FAMILY_IDEN = 'iden'
RAT_FAMILY_GSM = 'gsm'
RAT_FAMILY_UMTS = 'umts'
RAT_FAMILY_WLAN = 'wlan'
RAT_FAMILY_LTE = 'lte'
RAT_FAMILY_UNKNOWN = 'unknown'

CAPABILITY_PHONE = 'phone'
CAPABILITY_VOLTE = 'volte'
CAPABILITY_VT = 'vt'
CAPABILITY_WFC = 'wfc'
CAPABILITY_MSIM = 'msim'
CAPABILITY_OMADM = 'omadm'

# Constant for operation direction
MOBILE_ORIGINATED = "MO"
MOBILE_TERMINATED = "MT"

# Constant for call teardown side
CALL_TEARDOWN_PHONE = "PHONE"
CALL_TEARDOWN_REMOTE = "REMOTE"

WIFI_VERBOSE_LOGGING_ENABLED = 1
WIFI_VERBOSE_LOGGING_DISABLED = 0

"""
Begin shared constant define for both Python and Java
"""

# Constant for WiFi Calling WFC mode
WFC_MODE_WIFI_ONLY = "WIFI_ONLY"
WFC_MODE_CELLULAR_PREFERRED = "CELLULAR_PREFERRED"
WFC_MODE_WIFI_PREFERRED = "WIFI_PREFERRED"
WFC_MODE_DISABLED = "DISABLED"
WFC_MODE_UNKNOWN = "UNKNOWN"

# Constant for Video Telephony VT state
VT_STATE_AUDIO_ONLY = "AUDIO_ONLY"
VT_STATE_TX_ENABLED = "TX_ENABLED"
VT_STATE_RX_ENABLED = "RX_ENABLED"
VT_STATE_BIDIRECTIONAL = "BIDIRECTIONAL"
VT_STATE_TX_PAUSED = "TX_PAUSED"
VT_STATE_RX_PAUSED = "RX_PAUSED"
VT_STATE_BIDIRECTIONAL_PAUSED = "BIDIRECTIONAL_PAUSED"
VT_STATE_STATE_INVALID = "INVALID"

# Constant for Video Telephony Video quality
VT_VIDEO_QUALITY_DEFAULT = "DEFAULT"
VT_VIDEO_QUALITY_UNKNOWN = "UNKNOWN"
VT_VIDEO_QUALITY_HIGH = "HIGH"
VT_VIDEO_QUALITY_MEDIUM = "MEDIUM"
VT_VIDEO_QUALITY_LOW = "LOW"
VT_VIDEO_QUALITY_INVALID = "INVALID"

# Constant for Call State (for call object)
CALL_STATE_ACTIVE = "ACTIVE"
CALL_STATE_NEW = "NEW"
CALL_STATE_DIALING = "DIALING"
CALL_STATE_RINGING = "RINGING"
CALL_STATE_HOLDING = "HOLDING"
CALL_STATE_DISCONNECTED = "DISCONNECTED"
CALL_STATE_PRE_DIAL_WAIT = "PRE_DIAL_WAIT"
CALL_STATE_CONNECTING = "CONNECTING"
CALL_STATE_DISCONNECTING = "DISCONNECTING"
CALL_STATE_UNKNOWN = "UNKNOWN"
CALL_STATE_INVALID = "INVALID"

# Constant for PRECISE Call State (for call object)
PRECISE_CALL_STATE_ACTIVE = "ACTIVE"
PRECISE_CALL_STATE_ALERTING = "ALERTING"
PRECISE_CALL_STATE_DIALING = "DIALING"
PRECISE_CALL_STATE_INCOMING = "INCOMING"
PRECISE_CALL_STATE_HOLDING = "HOLDING"
PRECISE_CALL_STATE_DISCONNECTED = "DISCONNECTED"
PRECISE_CALL_STATE_WAITING = "WAITING"
PRECISE_CALL_STATE_DISCONNECTING = "DISCONNECTING"
PRECISE_CALL_STATE_IDLE = "IDLE"
PRECISE_CALL_STATE_UNKNOWN = "UNKNOWN"
PRECISE_CALL_STATE_INVALID = "INVALID"

# Constant for DC POWER STATE
DC_POWER_STATE_LOW = "LOW"
DC_POWER_STATE_HIGH = "HIGH"
DC_POWER_STATE_MEDIUM = "MEDIUM"
DC_POWER_STATE_UNKNOWN = "UNKNOWN"

# Constant for Audio Route
AUDIO_ROUTE_EARPIECE = "EARPIECE"
AUDIO_ROUTE_BLUETOOTH = "BLUETOOTH"
AUDIO_ROUTE_SPEAKER = "SPEAKER"
AUDIO_ROUTE_WIRED_HEADSET = "WIRED_HEADSET"
AUDIO_ROUTE_WIRED_OR_EARPIECE = "WIRED_OR_EARPIECE"

# Constant for Call Capability
CALL_CAPABILITY_HOLD = "HOLD"
CALL_CAPABILITY_SUPPORT_HOLD = "SUPPORT_HOLD"
CALL_CAPABILITY_MERGE_CONFERENCE = "MERGE_CONFERENCE"
CALL_CAPABILITY_SWAP_CONFERENCE = "SWAP_CONFERENCE"
CALL_CAPABILITY_UNUSED_1 = "UNUSED_1"
CALL_CAPABILITY_RESPOND_VIA_TEXT = "RESPOND_VIA_TEXT"
CALL_CAPABILITY_MUTE = "MUTE"
CALL_CAPABILITY_MANAGE_CONFERENCE = "MANAGE_CONFERENCE"
CALL_CAPABILITY_SUPPORTS_VT_LOCAL_RX = "SUPPORTS_VT_LOCAL_RX"
CALL_CAPABILITY_SUPPORTS_VT_LOCAL_TX = "SUPPORTS_VT_LOCAL_TX"
CALL_CAPABILITY_SUPPORTS_VT_LOCAL_BIDIRECTIONAL = "SUPPORTS_VT_LOCAL_BIDIRECTIONAL"
CALL_CAPABILITY_SUPPORTS_VT_REMOTE_RX = "SUPPORTS_VT_REMOTE_RX"
CALL_CAPABILITY_SUPPORTS_VT_REMOTE_TX = "SUPPORTS_VT_REMOTE_TX"
CALL_CAPABILITY_SUPPORTS_VT_REMOTE_BIDIRECTIONAL = "SUPPORTS_VT_REMOTE_BIDIRECTIONAL"
CALL_CAPABILITY_SEPARATE_FROM_CONFERENCE = "SEPARATE_FROM_CONFERENCE"
CALL_CAPABILITY_DISCONNECT_FROM_CONFERENCE = "DISCONNECT_FROM_CONFERENCE"
CALL_CAPABILITY_SPEED_UP_MT_AUDIO = "SPEED_UP_MT_AUDIO"
CALL_CAPABILITY_CAN_UPGRADE_TO_VIDEO = "CAN_UPGRADE_TO_VIDEO"
CALL_CAPABILITY_CAN_PAUSE_VIDEO = "CAN_PAUSE_VIDEO"
CALL_CAPABILITY_UNKOWN = "UNKOWN"

# Constant for Call Property
CALL_PROPERTY_HIGH_DEF_AUDIO = "HIGH_DEF_AUDIO"
CALL_PROPERTY_CONFERENCE = "CONFERENCE"
CALL_PROPERTY_GENERIC_CONFERENCE = "GENERIC_CONFERENCE"
CALL_PROPERTY_WIFI = "WIFI"
CALL_PROPERTY_EMERGENCY_CALLBACK_MODE = "EMERGENCY_CALLBACK_MODE"
CALL_PROPERTY_UNKNOWN = "UNKNOWN"

# Constant for Call Presentation
CALL_PRESENTATION_ALLOWED = "ALLOWED"
CALL_PRESENTATION_RESTRICTED = "RESTRICTED"
CALL_PRESENTATION_PAYPHONE = "PAYPHONE"
CALL_PRESENTATION_UNKNOWN = "UNKNOWN"

# Constant for Network Generation
GEN_2G = "2G"
GEN_3G = "3G"
GEN_4G = "4G"
GEN_UNKNOWN = "UNKNOWN"

# Constant for Network RAT
RAT_IWLAN = "IWLAN"
RAT_LTE = "LTE"
RAT_4G = "4G"
RAT_3G = "3G"
RAT_2G = "2G"
RAT_WCDMA = "WCDMA"
RAT_UMTS = "UMTS"
RAT_1XRTT = "1XRTT"
RAT_EDGE = "EDGE"
RAT_GPRS = "GPRS"
RAT_HSDPA = "HSDPA"
RAT_HSUPA = "HSUPA"
RAT_CDMA = "CDMA"
RAT_EVDO = "EVDO"
RAT_EVDO_0 = "EVDO_0"
RAT_EVDO_A = "EVDO_A"
RAT_EVDO_B = "EVDO_B"
RAT_IDEN = "IDEN"
RAT_EHRPD = "EHRPD"
RAT_HSPA = "HSPA"
RAT_HSPAP = "HSPAP"
RAT_GSM = "GSM"
RAT_TD_SCDMA = "TD_SCDMA"
RAT_GLOBAL = "GLOBAL"
RAT_UNKNOWN = "UNKNOWN"

# NETWORK_MODE_* See ril.h RIL_REQUEST_SET_PREFERRED_NETWORK_TYPE
NETWORK_MODE_WCDMA_PREF     = 0 # GSM/WCDMA (WCDMA preferred)
NETWORK_MODE_GSM_ONLY       = 1 # GSM only
NETWORK_MODE_WCDMA_ONLY     = 2 # WCDMA only
NETWORK_MODE_GSM_UMTS       = 3 # GSM/WCDMA (auto mode, according to PRL)
                                #     AVAILABLE Application Settings menu
NETWORK_MODE_CDMA           = 4 # CDMA and EvDo (auto mode, according to PRL)
                                #    AVAILABLE Application Settings menu
NETWORK_MODE_CDMA_NO_EVDO   = 5 # CDMA only
NETWORK_MODE_EVDO_NO_CDMA   = 6 # EvDo only
NETWORK_MODE_GLOBAL         = 7 # GSM/WCDMA, CDMA, and EvDo
                                #    (auto mode, according to PRL)
                                #     AVAILABLE Application Settings menu
NETWORK_MODE_LTE_CDMA_EVDO  = 8 # LTE, CDMA and EvDo
NETWORK_MODE_LTE_GSM_WCDMA  = 9 # LTE, GSM/WCDMA
NETWORK_MODE_LTE_CDMA_EVDO_GSM_WCDMA = 10 # LTE, CDMA, EvDo, GSM/WCDMA
NETWORK_MODE_LTE_ONLY       = 11 # LTE Only mode
NETWORK_MODE_LTE_WCDMA      = 12 # LTE/WCDMA
NETWORK_MODE_TDSCDMA_ONLY            = 13 # TD-SCDMA only
NETWORK_MODE_TDSCDMA_WCDMA           = 14 # TD-SCDMA and WCDMA
NETWORK_MODE_LTE_TDSCDMA             = 15 # TD-SCDMA and LTE
NETWORK_MODE_TDSCDMA_GSM             = 16 # TD-SCDMA and GSM
NETWORK_MODE_LTE_TDSCDMA_GSM         = 17 # TD-SCDMA,GSM and LTE
NETWORK_MODE_TDSCDMA_GSM_WCDMA       = 18 # TD-SCDMA, GSM/WCDMA
NETWORK_MODE_LTE_TDSCDMA_WCDMA       = 19 # TD-SCDMA, WCDMA and LTE
NETWORK_MODE_LTE_TDSCDMA_GSM_WCDMA   = 20 # TD-SCDMA, GSM/WCDMA and LTE
NETWORK_MODE_TDSCDMA_CDMA_EVDO_GSM_WCDMA  = 21 # TD-SCDMA,EvDo,CDMA,GSM/WCDMA
NETWORK_MODE_LTE_TDSCDMA_CDMA_EVDO_GSM_WCDMA = 22 # TD-SCDMA/LTE/GSM/WCDMA,
                                                  #    CDMA, and EvDo

# Constant for Phone Type
PHONE_TYPE_GSM = "GSM"
PHONE_TYPE_NONE = "NONE"
PHONE_TYPE_CDMA = "CDMA"
PHONE_TYPE_SIP = "SIP"

# Constant for SIM State
SIM_STATE_READY = "READY"
SIM_STATE_UNKNOWN = "UNKNOWN"
SIM_STATE_ABSENT = "ABSENT"
SIM_STATE_PUK_REQUIRED = "PUK_REQUIRED"
SIM_STATE_PIN_REQUIRED = "PIN_REQUIRED"
SIM_STATE_NETWORK_LOCKED = "NETWORK_LOCKED"
SIM_STATE_NOT_READY = "NOT_READY"
SIM_STATE_PERM_DISABLED = "PERM_DISABLED"
SIM_STATE_CARD_IO_ERROR = "CARD_IO_ERROR"

# Constant for Data Connection State
DATA_STATE_CONNECTED = "CONNECTED"
DATA_STATE_DISCONNECTED = "DISCONNECTED"
DATA_STATE_CONNECTING = "CONNECTING"
DATA_STATE_SUSPENDED = "SUSPENDED"
DATA_STATE_UNKNOWN = "UNKNOWN"

# Constant for Telephony Manager Call State
TELEPHONY_STATE_RINGING = "RINGING"
TELEPHONY_STATE_IDLE = "IDLE"
TELEPHONY_STATE_OFFHOOK = "OFFHOOK"
TELEPHONY_STATE_UNKNOWN = "UNKNOWN"

# Constant for TTY Mode
TTY_MODE_FULL = "FULL"
TTY_MODE_HCO = "HCO"
TTY_MODE_OFF = "OFF"
TTY_MODE_VCO ="VCO"

# Constant for Service State
SERVICE_STATE_EMERGENCY_ONLY = "EMERGENCY_ONLY"
SERVICE_STATE_IN_SERVICE = "IN_SERVICE"
SERVICE_STATE_OUT_OF_SERVICE = "OUT_OF_SERVICE"
SERVICE_STATE_POWER_OFF = "POWER_OFF"
SERVICE_STATE_UNKNOWN = "UNKNOWN"

# Constant for VoLTE Hand-over Service State
VOLTE_SERVICE_STATE_HANDOVER_STARTED = "STARTED"
VOLTE_SERVICE_STATE_HANDOVER_COMPLETED = "COMPLETED"
VOLTE_SERVICE_STATE_HANDOVER_FAILED = "FAILED"
VOLTE_SERVICE_STATE_HANDOVER_CANCELED = "CANCELED"
VOLTE_SERVICE_STATE_HANDOVER_UNKNOWN = "UNKNOWN"

# Constant for precise call state state listen level
PRECISE_CALL_STATE_LISTEN_LEVEL_FOREGROUND = "FOREGROUND"
PRECISE_CALL_STATE_LISTEN_LEVEL_RINGING = "RINGING"
PRECISE_CALL_STATE_LISTEN_LEVEL_BACKGROUND = "BACKGROUND"

# Constant for Messaging Event Name
EventSmsDeliverSuccess = "SmsDeliverSuccess"
EventSmsDeliverFailure = "SmsDeliverFailure"
EventSmsSentSuccess = "SmsSentSuccess"
EventSmsSentFailure = "SmsSentFailure"
EventSmsReceived = "SmsReceived"
EventMmsSentSuccess = "MmsSentSuccess"
EventMmsSentFailure = "MmsSentFailure"
EventMmsDownloaded = "MmsDownloaded"
EventWapPushReceived = "WapPushReceived"
EventDataSmsReceived = "DataSmsReceived"
EventCmasReceived = "CmasReceived"
EventEtwsReceived = "EtwsReceived"

# Constant for Telecom Call Event Name
EventTelecomCallStateChanged = "TelecomCallStateChanged"
EventTelecomCallParentChanged = "TelecomCallParentChanged"
EventTelecomCallChildrenChanged = "TelecomCallChildrenChanged"
EventTelecomCallDetailsChanged = "TelecomCallDetailsChanged"
EventTelecomCallCannedTextResponsesLoaded = "TelecomCallCannedTextResponsesLoaded"
EventTelecomCallPostDialWait = "TelecomCallPostDialWait"
EventTelecomCallVideoCallChanged = "TelecomCallVideoCallChanged"
EventTelecomCallDestroyed = "TelecomCallDestroyed"
EventTelecomCallConferenceableCallsChanged = "TelecomCallConferenceableCallsChanged"

# Constant for Video Call Event Name
EventTelecomVideoCallSessionModifyRequestReceived = "TelecomVideoCallSessionModifyRequestReceived"
EventTelecomVideoCallSessionModifyResponseReceived = "TelecomVideoCallSessionModifyResponseReceived"
EventTelecomVideoCallSessionEvent = "TelecomVideoCallSessionEvent"
EventTelecomVideoCallPeerDimensionsChanged = "TelecomVideoCallPeerDimensionsChanged"
EventTelecomVideoCallVideoQualityChanged = "TelecomVideoCallVideoQualityChanged"
EventTelecomVideoCallDataUsageChanged = "TelecomVideoCallDataUsageChanged"
EventTelecomVideoCallCameraCapabilities = "TelecomVideoCallCameraCapabilities"

# Constant for Video Call Call-Back Event Name
EventSessionModifyRequestReceived = "SessionModifyRequestReceived"
EventSessionModifyResponseReceived = "SessionModifyResponseReceived"
EventSessionEvent = "SessionEvent"
EventPeerDimensionsChanged = "PeerDimensionsChanged"
EventVideoQualityChanged = "VideoQualityChanged"
EventDataUsageChanged = "DataUsageChanged"
EventCameraCapabilitiesChanged = "CameraCapabilitiesChanged"
EventInvalid = "Invalid"

# Constant for Video Call Session Event Name
SessionEventRxPause = "SessionEventRxPause"
SessionEventRxResume = "SessionEventRxResume"
SessionEventTxStart = "SessionEventTxStart"
SessionEventTxStop = "SessionEventTxStop"
SessionEventCameraFailure = "SessionEventCameraFailure"
SessionEventCameraReady = "SessionEventCameraReady"
SessionEventUnknown = "SessionEventUnknown"

# Constant for Other Event Name
EventCallStateChanged = "CallStateChanged"
EventPreciseStateChanged = "PreciseStateChanged"
EventDataConnectionRealTimeInfoChanged = "DataConnectionRealTimeInfoChanged"
EventDataConnectionStateChanged = "DataConnectionStateChanged"
EventServiceStateChanged = "ServiceStateChanged"
EventVolteServiceStateChanged = "VolteServiceStateChanged"
EventMessageWaitingIndicatorChanged = "MessageWaitingIndicatorChanged"
EventConnectivityChanged = "ConnectivityChanged"

# Constant for Packet Keep Alive Call Back
PacketKeepaliveCallBack = "PacketKeepliveCallBack"
PacketKeepaliveCallBackStarted = "Started"
PacketKeepaliveCallBackStopped = "Stopped"
PacketKeepaliveCallBackError = "Error"
PacketKeepaliveCallBackInvalid = "Invalid"

# Constant for Network Call Back
NetworkCallBack = "NetworkCallBack"
NetworkCallBackPreCheck = "PreCheck"
NetworkCallBackAvailable = "Available"
NetworkCallBackLosing = "Losing"
NetworkCallBackLost = "Lost"
NetworkCallBackUnavailable = "Unavailable"
NetworkCallBackCapabilitiesChanged = "CapabilitiesChanged"
NetworkCallBackSuspended = "Suspended"
NetworkCallBackResumed = "Resumed"
NetworkCallBackLinkPropertiesChanged = "LinkPropertiesChanged"
NetworkCallBackInvalid = "Invalid"

NetworkModeWcdmaPref = "NetworkModeWcdmaPref"
NetworkModeGsmOnly = "NetworkModeGsmOnly"
NetworkModeWcdmaOnly = "NetworkModeWcdmaOnly"
NetworkModeGsmUmts = "NetworkModeGsmUmts"
NetworkModeCdma = "NetworkModeCdma"
NetworkModeCdmaNoEvdo = "NetworkModeCdmaNoEvdo"
NetworkModeEvdoNoCdma = "NetworkModeEvdoNoCdma"
NetworkModeGlobal = "NetworkModeGlobal"
NetworkModeLteCdmaEvdo = "NetworkModeLteCdmaEvdo"
NetworkModeLteGsmWcdma = "NetworkModeLteGsmWcdma"
NetworkModeLteCdmaEvdoGsmWcdma = "NetworkModeLteCdmaEvdoGsmWcdma"
NetworkModeLteOnly = "NetworkModeLteOnly"
NetworkModeLteWcdma = "NetworkModeLteWcdma"
NetworkModeTdscdmaOnly = "NetworkModeTdscdmaOnly"
NetworkModeTdscdmaWcdma = "NetworkModeTdscdmaWcdma"
NetworkModeLteTdscdma = "NetworkModeLteTdscdma"
NetworkModeTdsdmaGsm = "NetworkModeTdsdmaGsm"
NetworkModeLteTdscdmaGsm = "NetworkModeLteTdscdmaGsm"
NetworkModeTdscdmaGsmWcdma = "NetworkModeTdscdmaGsmWcdma"
NetworkModeLteTdscdmaWcdma = "NetworkModeLteTdscdmaWcdma"
NetworkModeLteTdscdmaGsmWcdma = "NetworkModeLteTdscdmaGsmWcdma"
NetworkModeTdscdmaCdmaEvdoGsmWcdma = "NetworkModeTdscdmaCdmaEvdoGsmWcdma"
NetworkModeLteTdscdmaCdmaEvdoGsmWcdma = "NetworkModeLteTdscdmaCdmaEvdoGsmWcdma"

"""
End shared constant define for both Python and Java
"""
