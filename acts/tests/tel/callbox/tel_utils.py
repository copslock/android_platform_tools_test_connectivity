#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (C) 2014- The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
from queue import Empty

from tel.md8475a import BtsNumber
from tel.md8475a import BtsTechnology
from tel.md8475a import BtsNwNameEnable
from tel.md8475a import CsfbType
from tel.md8475a import ReturnToEUTRAN

LTE_NW_NAME = "MD8475A_LTE"
WCDMA_NW_NAME = "MD8475A_WCDMA"
NW_MCC = "001"
NW_MNC = "01"
GATEWAY_IPV4_ADDRESS = "192.168.137.1"
UE_IPV4_ADDRESS_1 = "192.168.137.2"
UE_IPV4_ADDRESS_2 = "192.168.137.3"
DNS_IPV4_ADDRESS = "192.168.137.1"
CSCF_IPV4_ADDRESS = "192.168.137.1"

NETWORK_MODE_WCDMA_PREF = 0
NETWORK_MODE_GSM_ONLY = 1
NETWORK_MODE_WCDMA_ONLY = 2
NETWORK_MODE_GSM_UMTS = 3
NETWORK_MODE_LTE_GSM_WCDMA = 9
NETWORK_MODE_LTE_ONLY = 11
NETWORK_MODE_LTE_WCDMA = 12

LTE_NW_NAME = "MD8475A_LTE"
WCDMA_NW_NAME = "MD8475A_WCDMA"
NW_MCC = "001"
NW_MNC = "01"

MD8475A_IP_ADDRESS = "192.168.137.1"


def _init_lte_bts(bts):
    bts.nw_fullname_enable = BtsNwNameEnable.NAME_ENABLE
    bts.nw_fullname = LTE_NW_NAME
    bts.mcc = NW_MCC
    bts.mnc = NW_MNC


def _init_wcdma_bts(bts):
    bts.nw_fullname_enable = BtsNwNameEnable.NAME_ENABLE
    bts.nw_fullname = WCDMA_NW_NAME
    bts.mcc = NW_MCC
    bts.mnc = NW_MNC


def _init_PDN(anritsuHandle, pdn, ipAddress):
    # Setting IP address for internet connection sharing
    anritsuHandle.gateway_ipv4addr = GATEWAY_IPV4_ADDRESS
    pdn.ue_address_ipv4 = ipAddress
    pdn.primary_dns_address_ipv4 = DNS_IPV4_ADDRESS
    pdn.secondary_dns_address_ipv4 = DNS_IPV4_ADDRESS
    pdn.cscf_address_ipv4 = CSCF_IPV4_ADDRESS


def _init_lte_wcdma_system(anritsuHandle):
    PDN_ONE = 1

    anritsuHandle.set_simulation_model(BtsTechnology.LTE,
                                       BtsTechnology.WCDMA)
    anritsuHandle.csfb_type = CsfbType.CSFB_TYPE_REDIRECTION
    anritsuHandle.csfb_return_to_eutran = ReturnToEUTRAN.RETEUTRAN_ENABLE

    # setting BTS parameters
    lte_bts = anritsuHandle.get_BTS(BtsNumber.BTS1)
    wcdma_bts = anritsuHandle.get_BTS(BtsNumber.BTS2)
    _init_lte_bts(lte_bts)
    _init_wcdma_bts(wcdma_bts)

    pdn1 = anritsuHandle.get_PDN(PDN_ONE)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsuHandle, pdn1, UE_IPV4_ADDRESS_1)

    return lte_bts, wcdma_bts


def _init_wcdma_system(anritsuHandle):
    PDN_ONE = 1

    anritsuHandle.set_simulation_model(BtsTechnology.WCDMA)

    # setting BTS parameters
    wcdma_bts = anritsuHandle.get_BTS(BtsNumber.BTS1)
    _init_wcdma_bts(wcdma_bts)

    pdn1 = anritsuHandle.get_PDN(PDN_ONE)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(pdn1)
    return wcdma_bts


def set_system_model(anritsuHandle, model):
    ''' set the simulation model and returns handles to
        specifed BTS(s) in the system '''

    if model == "LTE":
        return None
    elif model == "WCDMA":
        wcdma_bts = _init_wcdma_system(anritsuHandle)
        return wcdma_bts
    elif model == "LTE_WCDMA":
        lte_bts, wcdma_bts = _init_lte_wcdma_system(anritsuHandle)
        return lte_bts, wcdma_bts
    elif model == "LTE_LTE":
        return one
    elif model == "WCDMA_LTE":
        return None
    elif model == "WCDMA_WCDMA":
        return None


def init_phone(droid, ed):
    turn_on_modem(droid)
    droid.setPreferredNetwork(NETWORK_MODE_LTE_GSM_WCDMA)
    droid.toggleDataConnection(True)
    _set_test_apn(droid)

    # make sure that device is in Power Off state
    # before starting simulation"
    turn_off_modem(droid)
    ed.clear_all_events()


def _set_test_apn(droid):
    selected_apn = droid.getSelectedAPN()

    if selected_apn is None or selected_apn == "":
        droid.setAPN("Anritsu", "anritsu.com")


def wait_for_network_state(ed, logHandle, state, time_to_wait=60, nwtype=""):
    sleep_interval = 1
    status = "failed"
    stateEvent = None

    if state == "IN_SERVICE":
        service_state_event = "onServiceStateChangedInService"+nwtype
    elif state == "OUT_OF_SERVICE":
        service_state_event = "onServiceStateChangedOutOfService"
    elif state == "POWER_OFF":
        service_state_event = "onServiceStateChangedPowerOff"
    elif state == "EMERGENCY_ONLY":
        service_state_event = "onServiceStateChangedEmergencyOnly"
    else:
        logHandle.info("Wrong state value.")
        return status, stateEvent

    try:
        if state == "IN_SERVICE":
            events = ed.pop_events(service_state_event, time_to_wait)
            stateEvent = events[0]
        else:
            stateEvent = ed.pop_event(service_state_event, time_to_wait)
        status = "passed"
    except Empty:
        logHandle.info("Timeout: Expected event is not received.")
    return status, stateEvent


def wait_for_bts_camping(anritsuHandle, logHandle, nw_type,  timeout=30):
    '''This is to wait for Anritsu to camp on a cell '''
    status = "failed"
    bts_number = ""
    rat_info = ""
    expected_bts_type = ""
    waiting_time = timeout
    sleep_interval = 1

    if nw_type == "LTE":
        expected_bts_type = "LTE"
    elif nw_type == "UMTS":
        expected_bts_type = "WCDMA"

    logHandle.info("Waiting for UE Idle/communication state in anritsu")
    anritsuHandle.wait_for_ue_registration()

    while (waiting_time > 0):
        bts_number, rat_info = anritsuHandle.get_camping_cell()
        if (bts_number == BtsNumber.BTS1.value or
           bts_number == BtsNumber.BTS2.value):
            if rat_info == expected_bts_type:
                status = "passed"
            break
        else:
            # system is in transition state.
            time.sleep(sleep_interval)
            waiting_time = waiting_time - 1

    return status


def wait_for_data_state(ed, logHandle, state, time_to_wait=60):
    status = "failed"
    event = None

    if state == "DATA_CONNECTED":
        data_state_event = "onDataConnectionStateChangedConnected"
    elif state == "DATA_DISCONNECTED":
        data_state_event = "onDataConnectionStateChangedDisconnected"
    else:
        logHandle.info("Wrong state value.")
        return status, event

    try:
        event = ed.pop_event(data_state_event, time_to_wait)
        status = "passed"
    except Empty:
        logHandle.info("Timeout: Expected event is not received.")

    return status, event


def wait_for_network_registration(ed, anritsuHandle, logHandle, nw_type=""):
    logHandle.info("Waiting for service state: IN_SERVICE")
    status, event = wait_for_network_state(ed, logHandle,
                                           "IN_SERVICE", 360, nw_type)

    # wait for data registration
    if (status == "passed" and
       event['data']['DataRegState'] == "OUT_OF_SERVICE"):
        status, event = wait_for_network_state(ed, logHandle,
                                               "IN_SERVICE", 240, nw_type)

    if status == "passed":
        status = "failed"
        status = wait_for_bts_camping(anritsuHandle,
                                      logHandle,
                                      event['data']['VoiceNetworkType'])

    return status, event


def turn_on_modem(droid):
    sleep_interval = 1
    droid.toggleAirplaneMode(False)
    time.sleep(sleep_interval)
    status = droid.checkAirplaneMode()
    return status


def turn_off_modem(droid):
    sleep_interval = 1
    droid.toggleAirplaneMode(True)
    status = droid.checkAirplaneMode()
    return status
