#/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

import time
from queue import Empty
from datetime import datetime

from acts.controllers.anritsu_lib._anritsu_utils import AnritsuUtils
from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.controllers.anritsu_lib.md8475a import BtsNwNameEnable
from acts.controllers.anritsu_lib.md8475a import BtsServiceState
from acts.controllers.anritsu_lib.md8475a import BtsTechnology
from acts.controllers.anritsu_lib.md8475a import CsfbType
from acts.controllers.anritsu_lib.md8475a import ImsCscfCall
from acts.controllers.anritsu_lib.md8475a import ImsCscfStatus
from acts.controllers.anritsu_lib.md8475a import MD8475A
from acts.controllers.anritsu_lib.md8475a import ReturnToEUTRAN
from acts.controllers.anritsu_lib.md8475a import VirtualPhoneStatus
from acts.controllers.anritsu_lib.md8475a import TestProcedure
from acts.controllers.anritsu_lib.md8475a import TestPowerControl
from acts.controllers.anritsu_lib.md8475a import TestMeasurement
from acts.test_utils.tel.tel_defines import CALL_TEARDOWN_PHONE
from acts.test_utils.tel.tel_defines import CALL_TEARDOWN_REMOTE
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_CALL_DROP
from acts.test_utils.tel.tel_defines import RAT_1XRTT
from acts.test_utils.tel.tel_defines import WAIT_TIME_IN_CALL
from acts.test_utils.tel.tel_defines import WAIT_TIME_IN_CALL_FOR_IMS
from acts.test_utils.tel.tel_defines import EventCmasReceived
from acts.test_utils.tel.tel_defines import EventEtwsReceived
from acts.test_utils.tel.tel_defines import EventSmsDeliverSuccess
from acts.test_utils.tel.tel_defines import EventSmsSentSuccess
from acts.test_utils.tel.tel_defines import EventSmsReceived
from acts.test_utils.tel.tel_test_utils import ensure_phone_idle
from acts.test_utils.tel.tel_test_utils import hangup_call
from acts.test_utils.tel.tel_test_utils import initiate_call
from acts.test_utils.tel.tel_test_utils import wait_and_answer_call
from acts.test_utils.tel.tel_test_utils import wait_for_droid_not_in_call

# Timers
# Time to wait after registration before sending a command to Anritsu
# to ensure the phone has sufficient time to reconfigure based on new
# network in Anritsu
WAIT_TIME_ANRITSU_REG_AND_OPER = 10
# Time to wait after registration to ensure the phone
# has sufficient time to reconfigure based on new network in Anritsu
WAIT_TIME_ANRITSU_REG_AND_CALL = 10
# Max time to wait for Anritsu's virtual phone state change
MAX_WAIT_TIME_VIRTUAL_PHONE_STATE = 45
# Time to wait for Anritsu's IMS CSCF state change
MAX_WAIT_TIME_IMS_CSCF_STATE = 30

# Test PLMN information
TEST_PLMN_LTE_NAME = "MD8475A_LTE"
TEST_PLMN_WCDMA_NAME = "MD8475A_WCDMA"
TEST_PLMN_GSM_NAME = "MD8475A_GSM"
TEST_PLMN_1X_NAME = "MD8475A_1X"
TEST_PLMN_1_MCC = "001"
TEST_PLMN_1_MNC = "01"
DEFAULT_MCC = "001"
DEFAULT_MNC = "01"
DEFAULT_RAC = 1
DEFAULT_LAC = 1

# IP address information for internet sharing
GATEWAY_IPV4_ADDRESS = "192.168.137.1"
UE_IPV4_ADDRESS_1 = "192.168.137.2"
UE_IPV4_ADDRESS_2 = "192.168.137.3"
DNS_IPV4_ADDRESS = "192.168.137.1"
CSCF_IPV4_ADDRESS = "192.168.137.1"

# LTE BAND constants
LTE_BAND_1 = 1
LTE_BAND_2 = 2
LTE_BAND_3 = 3
LTE_BAND_4 = 4
LTE_BAND_5 = 5
LTE_BAND_7 = 7
LTE_BAND_12 = 12
LTE_BAND_13 = 13

# WCDMA BAND constants
WCDMA_BAND_1 = 1
WCDMA_BAND_2 = 2
WCDMA_BAND_4 = 4
WCDMA_BAND_5 = 5
WCDMA_BAND_8 = 8

# GSM BAND constants
GSM_BAND_GSM450 = "GSM450"
GSM_BAND_GSM480 = "GSM480"
GSM_BAND_GSM850 = "GSM850"
GSM_BAND_PGSM900 = "P-GSM900"
GSM_BAND_EGSM900 = "E-GSM900"
GSM_BAND_RGSM900 = "R-GSM900"
GSM_BAND_DCS1800 = "DCS1800"
GSM_BAND_PCS1900 = "PCS1900"

# CDMA 1X BAND constants
CDMA_1X_BAND_0 = 0
CDMA_1X_BAND_1 = 1

# CDMA 1X DL Channel constants
CDMA1X_CHANNEL_356 = 356

# CDMA 1X SID constants
CDMA1X_SID_0 = 0

# CDMA 1X NID constants
CDMA1X_NID_65535 = 65535

# BANDWIDTH constants
CDMA1X_NID_65535 = 65535

# CMAS Message IDs
CMAS_MESSAGE_PRESIDENTIAL_ALERT = hex(0x1112)
CMAS_MESSAGE_EXTREME_IMMEDIATE_OBSERVED = hex(0x1113)
CMAS_MESSAGE_EXTREME_IMMEDIATE_LIKELY = hex(0x1114)
CMAS_MESSAGE_EXTREME_EXPECTED_OBSERVED = hex(0x1115)
CMAS_MESSAGE_EXTREME_EXPECTED_LIKELY = hex(0x1116)
CMAS_MESSAGE_SEVERE_IMMEDIATE_OBSERVED = hex(0x1117)
CMAS_MESSAGE_SEVERE_IMMEDIATE_LIKELY = hex(0x1118)
CMAS_MESSAGE_SEVERE_EXPECTED_OBSERVED = hex(0x1119)
CMAS_MESSAGE_SEVERE_EXPECTED_LIKELY = hex(0x111A)
CMAS_MESSAGE_CHILD_ABDUCTION_EMERGENCY = hex(0x111B)
CMAS_MESSAGE_MONTHLY_TEST = hex(0x111C)
CMAS_MESSAGE_CMAS_EXECERCISE = hex(0x111D)

# ETWS Message IDs
ETWS_WARNING_EARTHQUAKE = hex(0x1100)
ETWS_WARNING_TSUNAMI = hex(0x1101)
ETWS_WARNING_EARTHQUAKETSUNAMI = hex(0x1102)
ETWS_WARNING_TEST_MESSAGE = hex(0x1103)
ETWS_WARNING_OTHER_EMERGENCY = hex(0x1104)

# C2K CMAS Message Constants
CMAS_C2K_CATEGORY_PRESIDENTIAL = "Presidential"
CMAS_C2K_CATEGORY_EXTREME = "Extreme"
CMAS_C2K_CATEGORY_SEVERE = "Severe"
CMAS_C2K_CATEGORY_AMBER = "AMBER"
CMAS_C2K_CATEGORY_CMASTEST = "CMASTest"

CMAS_C2K_PRIORITY_NORMAL = "Normal"
CMAS_C2K_PRIORITY_INTERACTIVE = "Interactive"
CMAS_C2K_PRIORITY_URGENT = "Urgent"
CMAS_C2K_PRIORITY_EMERGENCY = "Emergency"

CMAS_C2K_RESPONSETYPE_SHELTER = "Shelter"
CMAS_C2K_RESPONSETYPE_EVACUATE = "Evacuate"
CMAS_C2K_RESPONSETYPE_PREPARE = "Prepare"
CMAS_C2K_RESPONSETYPE_EXECUTE = "Execute"
CMAS_C2K_RESPONSETYPE_MONITOR = "Monitor"
CMAS_C2K_RESPONSETYPE_AVOID = "Avoid"
CMAS_C2K_RESPONSETYPE_ASSESS = "Assess"
CMAS_C2K_RESPONSETYPE_NONE = "None"

CMAS_C2K_SEVERITY_EXTREME = "Extreme"
CMAS_C2K_SEVERITY_SEVERE = "Severe"

CMAS_C2K_URGENCY_IMMEDIATE = "Immediate"
CMAS_C2K_URGENCY_EXPECTED = "Expected"

CMAS_C2K_CERTIANTY_OBSERVED = "Observed"
CMAS_C2K_CERTIANTY_LIKELY = "Likely"

#PDN Numbers
PDN_NO_1 = 1

#Cell Numbers
CELL_1 = 1
CELL_2 = 2

# default ims virtual network id for Anritsu ims call test.
DEFAULT_IMS_VIRTUAL_NETWORK_ID = 1


def cb_serial_number():
    """ CMAS/ETWS serial number generator """
    i = 0x3000
    while True:
        yield i
        i += 1


def save_anritsu_log_files(anritsu_handle, test_name, user_params):
    """ saves the anritsu smart studio log files
        The logs should be saved in Anritsu system. Need to provide
        log folder path in Anritsu system

    Args:
        anritsu_handle: anritusu device object.
        test_name: test case name
        user_params : user supplied parameters list

    Returns:
        None
    """
    md8475a_log_folder = user_params["anritsu_log_file_path"]
    file_name = getfilenamewithtimestamp(test_name)
    seq_logfile = "{}\\{}_seq.csv".format(md8475a_log_folder, file_name)
    msg_logfile = "{}\\{}_msg.csv".format(md8475a_log_folder, file_name)
    trace_logfile = "{}\\{}_trace.lgex".format(md8475a_log_folder, file_name)
    anritsu_handle.save_sequence_log(seq_logfile)
    anritsu_handle.save_message_log(msg_logfile)
    anritsu_handle.save_trace_log(trace_logfile, "BINARY", 1, 0, 0)
    anritsu_handle.clear_sequence_log()
    anritsu_handle.clear_message_log()


def getfilenamewithtimestamp(test_name):
    """ Gets the test name appended with current time

    Args:
        test_name : test case name

    Returns:
        string of test name appended with current time
    """
    time_stamp = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    return "{}_{}".format(test_name, time_stamp)


def _init_lte_bts(bts, user_params, cell_no):
    """ initializes the LTE BTS
        All BTS parameters should be set here

    Args:
        bts: BTS object.
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        None
    """
    bts.nw_fullname_enable = BtsNwNameEnable.NAME_ENABLE
    bts.nw_fullname = TEST_PLMN_LTE_NAME
    bts.mcc = get_lte_mcc(user_params, cell_no)
    bts.mnc = get_lte_mnc(user_params, cell_no)
    bts.band = get_lte_band(user_params, cell_no)


def _init_wcdma_bts(bts, user_params, cell_no):
    """ initializes the WCDMA BTS
        All BTS parameters should be set here

    Args:
        bts: BTS object.
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        None
    """
    bts.nw_fullname_enable = BtsNwNameEnable.NAME_ENABLE
    bts.nw_fullname = TEST_PLMN_WCDMA_NAME
    bts.mcc = get_lte_mcc(user_params, cell_no)
    bts.mnc = get_lte_mnc(user_params, cell_no)
    bts.band = get_wcdma_band(user_params, cell_no)
    bts.rac = get_wcdma_rac(user_params, cell_no)
    bts.lac = get_wcdma_lac(user_params, cell_no)


def _init_gsm_bts(bts, user_params, cell_no):
    """ initializes the GSM BTS
        All BTS parameters should be set here

    Args:
        bts: BTS object.
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        None
    """
    bts.nw_fullname_enable = BtsNwNameEnable.NAME_ENABLE
    bts.nw_fullname = TEST_PLMN_GSM_NAME
    bts.mcc = get_lte_mcc(user_params, cell_no)
    bts.mnc = get_lte_mnc(user_params, cell_no)
    bts.band = get_gsm_band(user_params, cell_no)
    bts.rac = get_gsm_rac(user_params, cell_no)
    bts.lac = get_gsm_lac(user_params, cell_no)


def _init_1x_bts(bts, user_params, cell_no):
    """ initializes the 1X BTS
        All BTS parameters should be set here

    Args:
        bts: BTS object.
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        None
    """
    bts.sector1_mcc = get_1x_mcc(user_params, cell_no)
    bts.band = get_1x_band(user_params, cell_no)
    bts.dl_channel = get_1x_channel(user_params, cell_no)
    bts.sector1_sid = get_1x_sid(user_params, cell_no)
    bts.sector1_nid = get_1x_nid(user_params, cell_no)


def _init_evdo_bts(bts, user_params, cell_no):
    """ initializes the EVDO BTS
        All BTS parameters should be set here

    Args:
        bts: BTS object.
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        None
    """
    # TODO: b/26296702 add logic to initialize EVDO BTS
    pass


def _init_PDN(anritsu_handle, pdn, ip_address):
    """ initializes the PDN parameters
        All PDN parameters should be set here

    Args:
        anritsu_handle: anritusu device object.
        pdn: pdn object
        ip_address : UE IP address

    Returns:
        None
    """
    # Setting IP address for internet connection sharing
    anritsu_handle.gateway_ipv4addr = GATEWAY_IPV4_ADDRESS
    pdn.ue_address_ipv4 = ip_address
    pdn.primary_dns_address_ipv4 = DNS_IPV4_ADDRESS
    pdn.secondary_dns_address_ipv4 = DNS_IPV4_ADDRESS
    pdn.cscf_address_ipv4 = CSCF_IPV4_ADDRESS


def set_system_model_lte_lte(anritsu_handle, user_params):
    """ Configures Anritsu system for LTE and LTE simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte and Wcdma BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.LTE, BtsTechnology.LTE)
    # setting BTS parameters
    lte1_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    lte2_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_lte_bts(lte1_bts, user_params, CELL_1)
    _init_lte_bts(lte2_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [lte1_bts, lte2_bts]


def set_system_model_wcdma_wcdma(anritsu_handle, user_params):
    """ Configures Anritsu system for WCDMA and WCDMA simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte and Wcdma BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.WCDMA,
                                        BtsTechnology.WCDMA)
    # setting BTS parameters
    wcdma1_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    wcdma2_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_wcdma_bts(wcdma1_bts, user_params, CELL_1)
    _init_wcdma_bts(wcdma2_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [wcdma1_bts, wcdma2_bts]


def set_system_model_lte_wcdma(anritsu_handle, user_params):
    """ Configures Anritsu system for LTE and WCDMA simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte and Wcdma BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.LTE, BtsTechnology.WCDMA)
    # setting BTS parameters
    lte_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    wcdma_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_lte_bts(lte_bts, user_params, CELL_1)
    _init_wcdma_bts(wcdma_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [lte_bts, wcdma_bts]


def set_system_model_lte_gsm(anritsu_handle, user_params):
    """ Configures Anritsu system for LTE and GSM simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte and Wcdma BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.LTE, BtsTechnology.GSM)
    # setting BTS parameters
    lte_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    gsm_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_lte_bts(lte_bts, user_params, CELL_1)
    _init_gsm_bts(gsm_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [lte_bts, gsm_bts]


def set_system_model_lte_1x(anritsu_handle, user_params):
    """ Configures Anritsu system for LTE and 1x simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte and 1x BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.LTE,
                                        BtsTechnology.CDMA1X)
    # setting BTS parameters
    lte_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    cdma1x_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_lte_bts(lte_bts, user_params, CELL_1)
    _init_1x_bts(cdma1x_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [lte_bts, cdma1x_bts]


def set_system_model_wcdma_gsm(anritsu_handle, user_params):
    """ Configures Anritsu system for WCDMA and GSM simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Wcdma and Gsm BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.WCDMA, BtsTechnology.GSM)
    # setting BTS parameters
    wcdma_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    gsm_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_wcdma_bts(wcdma_bts, user_params, CELL_1)
    _init_gsm_bts(gsm_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [wcdma_bts, gsm_bts]


def set_system_model_gsm_gsm(anritsu_handle, user_params):
    """ Configures Anritsu system for GSM and GSM simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Wcdma and Gsm BTS objects
    """
    anritsu_handle.set_simulation_model(BtsTechnology.GSM, BtsTechnology.GSM)
    # setting BTS parameters
    gsm1_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    gsm2_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_gsm_bts(gsm1_bts, user_params, CELL_1)
    _init_gsm_bts(gsm2_bts, user_params, CELL_2)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [gsm1_bts, gsm2_bts]


def set_system_model_lte(anritsu_handle, user_params):
    """ Configures Anritsu system for LTE simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Lte BTS object
    """
    anritsu_handle.set_simulation_model(BtsTechnology.LTE)
    # setting BTS parameters
    lte_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    _init_lte_bts(lte_bts, user_params, CELL_1)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [lte_bts]


def set_system_model_wcdma(anritsu_handle, user_params):
    """ Configures Anritsu system for WCDMA simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Wcdma BTS object
    """
    anritsu_handle.set_simulation_model(BtsTechnology.WCDMA)
    # setting BTS parameters
    wcdma_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    _init_wcdma_bts(wcdma_bts, user_params, CELL_1)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [wcdma_bts]


def set_system_model_gsm(anritsu_handle, user_params):
    """ Configures Anritsu system for GSM simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Gsm BTS object
    """
    anritsu_handle.set_simulation_model(BtsTechnology.GSM)
    # setting BTS parameters
    gsm_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    _init_gsm_bts(gsm_bts, user_params, CELL_1)
    pdn1 = anritsu_handle.get_PDN(PDN_NO_1)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [gsm_bts]


def set_system_model_1x(anritsu_handle, user_params):
    """ Configures Anritsu system for CDMA 1X simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Cdma 1x BTS object
    """
    PDN_ONE = 1
    anritsu_handle.set_simulation_model(BtsTechnology.CDMA1X)
    # setting BTS parameters
    cdma1x_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    _init_1x_bts(cdma1x_bts, user_params, CELL_1)
    pdn1 = anritsu_handle.get_PDN(PDN_ONE)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [cdma1x_bts]


def set_system_model_1x_evdo(anritsu_handle, user_params):
    """ Configures Anritsu system for CDMA 1X simulation

    Args:
        anritsu_handle: anritusu device object.
        user_params: pointer to user supplied parameters

    Returns:
        Cdma 1x BTS object
    """
    PDN_ONE = 1
    anritsu_handle.set_simulation_model(BtsTechnology.CDMA1X,
                                        BtsTechnology.EVDO)
    # setting BTS parameters
    cdma1x_bts = anritsu_handle.get_BTS(BtsNumber.BTS1)
    evdo_bts = anritsu_handle.get_BTS(BtsNumber.BTS2)
    _init_1x_bts(cdma1x_bts, user_params, CELL_1)
    _init_evdo_bts(evdo_bts, user_params, CELL_1)
    pdn1 = anritsu_handle.get_PDN(PDN_ONE)
    # Initialize PDN IP address for internet connection sharing
    _init_PDN(anritsu_handle, pdn1, UE_IPV4_ADDRESS_1)
    return [cdma1x_bts]


def wait_for_bts_state(log, btsnumber, state, timeout=30):
    """ Waits for BTS to be in the specified state ("IN" or "OUT")

    Args:
        btsnumber: BTS number.
        state: expected state

    Returns:
        True for success False for failure
    """
    #  state value are "IN" and "OUT"
    status = False
    sleep_interval = 1
    wait_time = timeout

    if state is "IN":
        service_state = BtsServiceState.SERVICE_STATE_IN
    elif state is "OUT":
        service_state = BtsServiceState.SERVICE_STATE_OUT
    else:
        log.info("wrong state value")
        return status

    if btsnumber.service_state is service_state:
        log.info("BTS state is already in {}".format(state))
        return True

    # set to desired service state
    btsnumber.service_state = service_state

    while wait_time > 0:
        if service_state == btsnumber.service_state:
            status = True
            break
        time.sleep(sleep_interval)
        wait_time = wait_time - sleep_interval

    if not status:
        log.info("Timeout: Expected BTS state is not received.")
    return status


class _CallSequenceException(Exception):
    pass


def call_mo_setup_teardown(
        log,
        ad,
        anritsu_handle,
        callee_number,
        teardown_side=CALL_TEARDOWN_PHONE,
        is_emergency=False,
        wait_time_in_call=WAIT_TIME_IN_CALL,
        is_ims_call=False,
        ims_virtual_network_id=DEFAULT_IMS_VIRTUAL_NETWORK_ID):
    """ Makes a MO call and tear down the call

    Args:
        ad: Android device object.
        anritsu_handle: Anritsu object.
        callee_number: Number to be called.
        teardown_side: the side to end the call (Phone or remote).
        is_emergency: is the call an emergency call.
        wait_time_in_call: Time to wait when phone in call.
        is_ims_call: is the call expected to be ims call.
        ims_virtual_network_id: ims virtual network id.

    Returns:
        True for success False for failure
    """

    log.info("Making Call to " + callee_number)
    virtual_phone_handle = anritsu_handle.get_VirtualPhone()

    try:
        # for an IMS call we either check CSCF or *nothing* (no virtual phone).
        if is_ims_call:
            # we only need pre-call registration in a non-emergency case
            if not is_emergency:
                if not wait_for_ims_cscf_status(log, anritsu_handle,
                                                ims_virtual_network_id,
                                                ImsCscfStatus.SIPIDLE.value):
                    raise _CallSequenceException(
                        "Phone IMS status is not idle.")
        else:
            if not wait_for_virtualphone_state(log, virtual_phone_handle,
                                               VirtualPhoneStatus.STATUS_IDLE):
                raise _CallSequenceException("Virtual Phone not idle.")

        if not initiate_call(log, ad, callee_number, is_emergency):
            raise _CallSequenceException("Initiate call failed.")

        if is_ims_call:
            if not wait_for_ims_cscf_status(log, anritsu_handle,
                                            ims_virtual_network_id,
                                            ImsCscfStatus.CALLING.value):
                raise _CallSequenceException(
                    "Phone IMS status is not calling.")
            if not wait_for_ims_cscf_status(log, anritsu_handle,
                                            ims_virtual_network_id,
                                            ImsCscfStatus.CONNECTED.value):
                raise _CallSequenceException(
                    "Phone IMS status is not connected.")
        else:
            # check Virtual phone answered the call
            if not wait_for_virtualphone_state(
                    log, virtual_phone_handle,
                    VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS):
                raise _CallSequenceException("Virtual Phone not in call.")

        time.sleep(wait_time_in_call)

        if not ad.droid.telecomIsInCall():
            raise _CallSequenceException("Call ended before delay_in_call.")

        if teardown_side is CALL_TEARDOWN_REMOTE:
            log.info("Disconnecting the call from Remote")
            if is_ims_call:
                anritsu_handle.ims_cscf_call_action(ims_virtual_network_id,
                                                    ImsCscfCall.END.value)
            else:
                virtual_phone_handle.set_voice_on_hook()
            if not wait_for_droid_not_in_call(log, ad,
                                              MAX_WAIT_TIME_CALL_DROP):
                raise _CallSequenceException("DUT call not drop.")
        else:
            log.info("Disconnecting the call from DUT")
            if not hangup_call(log, ad):
                raise _CallSequenceException(
                    "Error in Hanging-Up Call on DUT.")

        if is_ims_call:
            if not wait_for_ims_cscf_status(log, anritsu_handle,
                                            ims_virtual_network_id,
                                            ImsCscfStatus.SIPIDLE.value):
                raise _CallSequenceException("Phone IMS status is not idle.")
        else:
            if not wait_for_virtualphone_state(log, virtual_phone_handle,
                                               VirtualPhoneStatus.STATUS_IDLE):
                raise _CallSequenceException(
                    "Virtual Phone not idle after hangup.")
        return True

    except _CallSequenceException as e:
        log.error(e)
        return False
    finally:
        try:
            if ad.droid.telecomIsInCall():
                ad.droid.telecomEndCall()
        except Exception as e:
            log.error(str(e))


# This procedure is for SRLTE CSFB and SRVCC test cases
def ims_mo_cs_teardown(log,
                       ad,
                       anritsu_handle,
                       callee_number,
                       teardown_side=CALL_TEARDOWN_PHONE,
                       is_emergency=False,
                       check_ims_reg=True,
                       check_ims_calling=True,
                       srvcc=False,
                       wait_time_in_volte=WAIT_TIME_IN_CALL_FOR_IMS,
                       wait_time_in_cs=WAIT_TIME_IN_CALL,
                       ims_virtual_network_id=DEFAULT_IMS_VIRTUAL_NETWORK_ID):
    """ Makes a MO call after IMS registred, transit to CS, tear down the call

    Args:
        ad: Android device object.
        anritsu_handle: Anritsu object.
        callee_number: Number to be called.
        teardown_side: the side to end the call (Phone or remote).
        is_emergency: to make emergency call on the phone.
        check_ims_reg: check if Anritsu cscf server state is "SIPIDLE".
        check_ims_calling: check if Anritsu cscf server state is "CALLING".
        srvcc: is the test case a SRVCC call.
        wait_time_in_volte: Time for phone in VoLTE call, not used for SRLTE
        wait_time_in_cs: Time for phone in CS call.
        ims_virtual_network_id: ims virtual network id.

    Returns:
        True for success False for failure
    """

    virtual_phone_handle = anritsu_handle.get_VirtualPhone()

    try:
        # confirm ims registration
        if check_ims_reg:
            if not wait_for_ims_cscf_status(log, anritsu_handle,
                                            ims_virtual_network_id,
                                            ImsCscfStatus.SIPIDLE.value):
                raise _CallSequenceException("IMS/CSCF status is not idle.")
        # confirm virtual phone in idle
        if not wait_for_virtualphone_state(log, virtual_phone_handle,
                                           VirtualPhoneStatus.STATUS_IDLE):
            raise _CallSequenceException("Virtual Phone not idle.")
        # make mo call
        log.info("Making Call to " + callee_number)
        if not initiate_call(log, ad, callee_number, is_emergency):
            raise _CallSequenceException("Initiate call failed.")
        # if check ims calling is required
        if check_ims_calling:
            if not wait_for_ims_cscf_status(log, anritsu_handle,
                                            ims_virtual_network_id,
                                            ImsCscfStatus.CALLING.value):
                raise _CallSequenceException(
                    "Phone IMS status is not calling.")
            # if SRVCC, check if VoLTE call is connected, then Handover
            if srvcc:
                if not wait_for_ims_cscf_status(log, anritsu_handle,
                                                ims_virtual_network_id,
                                                ImsCscfStatus.CONNECTED.value):
                    raise _CallSequenceException(
                        "Phone IMS status is not connected.")
                # stay in call for "wait_time_in_volte" seconds
                time.sleep(wait_time_in_volte)
                # SRVCC by handover test case procedure
                srvcc_tc = anritsu_handle.get_AnritsuTestCases()
                srvcc_tc.procedure = TestProcedure.PROCEDURE_HO
                srvcc_tc.bts_direction = (BtsNumber.BTS1, BtsNumber.BTS2)
                srvcc_tc.power_control = TestPowerControl.POWER_CONTROL_DISABLE
                srvcc_tc.measurement_LTE = TestMeasurement.MEASUREMENT_DISABLE
                anritsu_handle.start_testcase()
        # check if Virtual phone answers the call
        if not wait_for_virtualphone_state(
                log, virtual_phone_handle,
                VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS):
            raise _CallSequenceException("Virtual Phone not in call.")
        # stay in call for "wait_time_in_cs" seconds
        time.sleep(wait_time_in_cs)
        # check if the phone stay in call
        if not ad.droid.telecomIsInCall():
            raise _CallSequenceException("Call ended before delay_in_call.")
        # end the call
        if teardown_side is CALL_TEARDOWN_REMOTE:
            log.info("Disconnecting the call from Remote")
            virtual_phone_handle.set_voice_on_hook()
            if not wait_for_droid_not_in_call(log, ad,
                                              MAX_WAIT_TIME_CALL_DROP):
                raise _CallSequenceException("DUT call not drop.")
        else:
            log.info("Disconnecting the call from DUT")
            if not hangup_call(log, ad):
                raise _CallSequenceException(
                    "Error in Hanging-Up Call on DUT.")
        # confirm if virtual phone status is back to idle
        if not wait_for_virtualphone_state(log, virtual_phone_handle,
                                           VirtualPhoneStatus.STATUS_IDLE):
            raise _CallSequenceException(
                "Virtual Phone not idle after hangup.")
        return True

    except _CallSequenceException as e:
        log.error(e)
        return False
    finally:
        try:
            if ad.droid.telecomIsInCall():
                ad.droid.telecomEndCall()
        except Exception as e:
            log.error(str(e))


def call_mt_setup_teardown(log,
                           ad,
                           virtual_phone_handle,
                           caller_number=None,
                           teardown_side=CALL_TEARDOWN_PHONE,
                           rat=""):
    """ Makes a call from Anritsu Virtual phone to device and tear down the call

    Args:
        ad: Android device object.
        virtual_phone_handle: Anritus virtual phone handle
        caller_number =  Caller number
        teardown_side = specifiy the side to end the call (Phone or remote)

    Returns:
        True for success False for failure
    """
    log.info("Receive MT Call - Making a call to the phone from remote")
    try:
        if not wait_for_virtualphone_state(log, virtual_phone_handle,
                                           VirtualPhoneStatus.STATUS_IDLE):
            raise Exception("Virtual Phone is not in a state to start call")
        if caller_number is not None:
            if rat == RAT_1XRTT:
                virtual_phone_handle.id_c2k = caller_number
            else:
                virtual_phone_handle.id = caller_number
        virtual_phone_handle.set_voice_off_hook()

        if not wait_and_answer_call(log, ad, caller_number):
            raise Exception("Answer call Fail")

        time.sleep(WAIT_TIME_IN_CALL)

        if not ad.droid.telecomIsInCall():
            raise Exception("Call ended before delay_in_call.")
    except Exception:
        return False

    if ad.droid.telecomIsInCall():
        if teardown_side is CALL_TEARDOWN_REMOTE:
            log.info("Disconnecting the call from Remote")
            virtual_phone_handle.set_voice_on_hook()
        else:
            log.info("Disconnecting the call from Phone")
            ad.droid.telecomEndCall()

    wait_for_virtualphone_state(log, virtual_phone_handle,
                                VirtualPhoneStatus.STATUS_IDLE)
    ensure_phone_idle(log, ad)

    return True


def wait_for_sms_deliver_success(log, ad, time_to_wait=60):
    sms_deliver_event = EventSmsDeliverSuccess
    sleep_interval = 2
    status = False
    event = None

    try:
        event = ad.ed.pop_event(sms_deliver_event, time_to_wait)
        status = True
    except Empty:
        log.info("Timeout: Expected event is not received.")
    return status


def wait_for_sms_sent_success(log, ad, time_to_wait=60):
    sms_sent_event = EventSmsSentSuccess
    sleep_interval = 2
    status = False
    event = None

    try:
        event = ad.ed.pop_event(sms_sent_event, time_to_wait)
        log.info(event)
        status = True
    except Empty:
        log.info("Timeout: Expected event is not received.")
    return status


def wait_for_incoming_sms(log, ad, time_to_wait=60):
    sms_received_event = EventSmsReceived
    sleep_interval = 2
    status = False
    event = None

    try:
        event = ad.ed.pop_event(sms_received_event, time_to_wait)
        log.info(event)
        status = True
    except Empty:
        log.info("Timeout: Expected event is not received.")
    return status, event


def verify_anritsu_received_sms(log, vp_handle, receiver_number, message, rat):
    if rat == RAT_1XRTT:
        receive_sms = vp_handle.receiveSms_c2k()
    else:
        receive_sms = vp_handle.receiveSms()

    if receive_sms == "NONE":
        return False
    split = receive_sms.split('&')
    text = ""
    if rat == RAT_1XRTT:
        # TODO: b/26296388 There is some problem when retrieving message with é
        # from Anritsu.
        return True
    for i in range(len(split)):
        if split[i].startswith('Text='):
            text = split[i][5:]
            text = AnritsuUtils.gsm_decode(text)
            break
    # TODO: b/26296388 Verify Phone number
    if text != message:
        log.error("Wrong message received")
        return False
    return True


def sms_mo_send(log, ad, vp_handle, receiver_number, message, rat=""):
    try:
        if not wait_for_virtualphone_state(log, vp_handle,
                                           VirtualPhoneStatus.STATUS_IDLE):
            raise Exception("Virtual Phone is not in a state to receive SMS")
        log.info("Sending SMS to " + receiver_number)
        ad.droid.smsSendTextMessage(receiver_number, message, False)
        log.info("Waiting for SMS sent event")
        test_status = wait_for_sms_sent_success(log, ad)
        if not test_status:
            raise Exception("Failed to send SMS")
        if not verify_anritsu_received_sms(log, vp_handle, receiver_number,
                                           message, rat):
            raise Exception("Anritsu didn't receive message")
    except Exception as e:
        log.error("Exception :" + str(e))
        return False
    return True


def sms_mt_receive_verify(log, ad, vp_handle, sender_number, message, rat=""):
    ad.droid.smsStartTrackingIncomingMessage()
    try:
        if not wait_for_virtualphone_state(log, vp_handle,
                                           VirtualPhoneStatus.STATUS_IDLE):
            raise Exception("Virtual Phone is not in a state to receive SMS")
        log.info("Waiting for Incoming SMS from " + sender_number)
        if rat == RAT_1XRTT:
            vp_handle.sendSms_c2k(sender_number, message)
        else:
            vp_handle.sendSms(sender_number, message)
        test_status, event = wait_for_incoming_sms(log, ad)
        if not test_status:
            raise Exception("Failed to receive SMS")
        log.info("Incoming SMS: Sender " + event['data']['Sender'])
        log.info("Incoming SMS: Message " + event['data']['Text'])
        if event['data']['Sender'] != sender_number:
            raise Exception("Wrong sender Number")
        if event['data']['Text'] != message:
            raise Exception("Wrong message")
    except Exception as e:
        log.error("exception: " + str(e))
        return False
    finally:
        ad.droid.smsStopTrackingIncomingMessage()
    return True


def wait_for_ims_cscf_status(log,
                             anritsu_handle,
                             virtual_network_id,
                             status,
                             timeout=MAX_WAIT_TIME_IMS_CSCF_STATE):
    """ Wait for IMS CSCF to be in expected state.

    Args:
        log: log object
        anritsu_handle: anritsu object
        virtual_network_id: virtual network id to be monitored
        status: expected status
        timeout: wait time
    """
    sleep_interval = 1
    wait_time = timeout
    while wait_time > 0:
        if status == anritsu_handle.get_ims_cscf_status(virtual_network_id):
            return True
        time.sleep(sleep_interval)
        wait_time = wait_time - sleep_interval
    return False


def wait_for_virtualphone_state(log,
                                vp_handle,
                                state,
                                timeout=MAX_WAIT_TIME_VIRTUAL_PHONE_STATE):
    """ Waits for Anritsu Virtual phone to be in expected state

    Args:
        ad: Android device object.
        vp_handle: Anritus virtual phone handle
        state =  expected state

    Returns:
        True for success False for failure
    """
    status = False
    sleep_interval = 1
    wait_time = timeout
    while wait_time > 0:
        if vp_handle.status == state:
            log.info(vp_handle.status)
            status = True
            break
        time.sleep(sleep_interval)
        wait_time = wait_time - sleep_interval

    if not status:
        log.info("Timeout: Expected state is not received.")
    return status


# There is a difference between CMAS/ETWS message formation in LTE/WCDMA and CDMA 1X
# LTE and CDMA : 3GPP
# CDMA 1X: 3GPP2
# hence different functions
def cmas_receive_verify_message_lte_wcdma(
        log, ad, anritsu_handle, serial_number, message_id, warning_message):
    """ Makes Anritsu to send a CMAS message and phone and verifies phone
        receives the message on LTE/WCDMA

    Args:
        ad: Android device object.
        anritsu_handle: Anritus device object
        serial_number =  serial number of CMAS message
        message_id =  CMAS message ID
        warning_message =  CMAS warning message

    Returns:
        True for success False for failure
    """
    status = False
    event = None
    ad.droid.smsStartTrackingGsmEmergencyCBMessage()
    anritsu_handle.send_cmas_lte_wcdma(
        hex(serial_number), message_id, warning_message)
    try:
        log.info("Waiting for CMAS Message")
        event = ad.ed.pop_event(EventCmasReceived, 60)
        status = True
        log.info(event)
        if warning_message != event['data']['message']:
            log.info("Wrong warning messgae received")
            status = False
        if message_id != hex(event['data']['serviceCategory']):
            log.info("Wrong warning messgae received")
            status = False
    except Empty:
        log.info("Timeout: Expected event is not received.")

    ad.droid.smsStopTrackingGsmEmergencyCBMessage()
    return status


def cmas_receive_verify_message_cdma1x(
        log,
        ad,
        anritsu_handle,
        message_id,
        service_category,
        alert_text,
        response_type=CMAS_C2K_RESPONSETYPE_SHELTER,
        severity=CMAS_C2K_SEVERITY_EXTREME,
        urgency=CMAS_C2K_URGENCY_IMMEDIATE,
        certainty=CMAS_C2K_CERTIANTY_OBSERVED):
    """ Makes Anritsu to send a CMAS message and phone and verifies phone
        receives the message on CDMA 1X

    Args:
        ad: Android device object.
        anritsu_handle: Anritus device object
        serial_number =  serial number of CMAS message
        message_id =  CMAS message ID
        warning_message =  CMAS warning message

    Returns:
        True for success False for failure
    """
    status = False
    event = None
    ad.droid.smsStartTrackingCdmaEmergencyCBMessage()
    anritsu_handle.send_cmas_etws_cdma1x(message_id, service_category,
                                         alert_text, response_type, severity,
                                         urgency, certainty)
    try:
        log.info("Waiting for CMAS Message")
        event = ad.ed.pop_event(EventCmasReceived, 60)
        status = True
        log.info(event)
        if alert_text != event['data']['message']:
            log.info("Wrong alert messgae received")
            status = False

        if event['data']['cmasResponseType'].lower() != response_type.lower():
            log.info("Wrong response type received")
            status = False

        if event['data']['cmasUrgency'].lower() != urgency.lower():
            log.info("Wrong cmasUrgency received")
            status = False

        if event['data']['cmasSeverity'].lower() != severity.lower():
            Log.info("Wrong cmasSeverity received")
            status = False
    except Empty:
        log.info("Timeout: Expected event is not received.")

    ad.droid.smsStopTrackingCdmaEmergencyCBMessage()
    return status


def etws_receive_verify_message_lte_wcdma(
        log, ad, anritsu_handle, serial_number, message_id, warning_message):
    """ Makes Anritsu to send a ETWS message and phone and verifies phone
        receives the message on LTE/WCDMA

    Args:
        ad: Android device object.
        anritsu_handle: Anritus device object
        serial_number =  serial number of ETWS message
        message_id =  ETWS message ID
        warning_message =  ETWS warning message

    Returns:
        True for success False for failure
    """
    status = False
    event = None
    if message_id == ETWS_WARNING_EARTHQUAKE:
        warning_type = "Earthquake"
    elif message_id == ETWS_WARNING_EARTHQUAKETSUNAMI:
        warning_type = "EarthquakeandTsunami"
    elif message_id == ETWS_WARNING_TSUNAMI:
        warning_type = "Tsunami"
    elif message_id == ETWS_WARNING_TEST_MESSAGE:
        warning_type = "test"
    elif message_id == ETWS_WARNING_OTHER_EMERGENCY:
        warning_type = "other"
    ad.droid.smsStartTrackingGsmEmergencyCBMessage()
    anritsu_handle.send_etws_lte_wcdma(
        hex(serial_number), message_id, warning_type, warning_message, "ON",
        "ON")
    try:
        log.info("Waiting for ETWS Message")
        event = ad.ed.pop_event(EventEtwsReceived, 60)
        status = True
        log.info(event)
        # TODO: b/26296388 Event data verification
    except Empty:
        log.info("Timeout: Expected event is not received.")

    ad.droid.smsStopTrackingGsmEmergencyCBMessage()
    return status


def etws_receive_verify_message_cdma1x(log, ad, anritsu_handle, serial_number,
                                       message_id, warning_message):
    """ Makes Anritsu to send a ETWS message and phone and verifies phone
        receives the message on CDMA1X

    Args:
        ad: Android device object.
        anritsu_handle: Anritus device object
        serial_number =  serial number of ETWS message
        message_id =  ETWS message ID
        warning_message =  ETWS warning message

    Returns:
        True for success False for failure
    """
    status = False
    event = None
    # TODO: b/26296388 need to add logic to check etws.
    return status


def read_ue_identity(log, ad, anritsu_handle, identity_type):
    """ Get the UE identity IMSI, IMEI, IMEISV

    Args:
        ad: Android device object.
        anritsu_handle: Anritus device object
        identity_type: Identity type(IMSI/IMEI/IMEISV)

    Returns:
        Requested Identity value
    """
    return anritsu_handle.get_ue_identity(identity_type)


def get_lte_band(user_params, cell_no):
    """ Returns the LTE BAND to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        LTE BAND to be used
    """
    key = "cell{}_lte_band".format(cell_no)
    try:
        lte_band = user_params[key]
    except KeyError:
        lte_band = LTE_BAND_2
    return lte_band


def get_wcdma_band(user_params, cell_no):
    """ Returns the WCDMA BAND to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        WCDMA BAND to be used
    """
    key = "cell{}_wcdma_band".format(cell_no)
    try:
        wcdma_band = user_params[key]
    except KeyError:
        wcdma_band = WCDMA_BAND_1
    return wcdma_band


def get_gsm_band(user_params, cell_no):
    """ Returns the GSM BAND to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        GSM BAND to be used
    """
    key = "cell{}_gsm_band".format(cell_no)
    try:
        gsm_band = user_params[key]
    except KeyError:
        gsm_band = GSM_BAND_GSM850
    return gsm_band


def get_1x_band(user_params, cell_no):
    """ Returns the 1X BAND to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        1X BAND to be used
    """
    key = "cell{}_1x_band".format(cell_no)
    try:
        cdma_1x_band = user_params[key]
    except KeyError:
        cdma_1x_band = CDMA_1X_BAND_0
    return cdma_1x_band


def get_wcdma_rac(user_params, cell_no):
    """ Returns the WCDMA RAC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        WCDMA RAC to be used
    """
    key = "cell{}_wcdma_rac".format(cell_no)
    try:
        wcdma_rac = user_params[key]
    except KeyError:
        wcdma_rac = DEFAULT_RAC
    return wcdma_rac


def get_gsm_rac(user_params, cell_no):
    """ Returns the GSM RAC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        GSM RAC to be used
    """
    key = "cell{}_gsm_rac".format(cell_no)
    try:
        gsm_rac = user_params[key]
    except KeyError:
        gsm_rac = DEFAULT_RAC
    return gsm_rac


def get_wcdma_lac(user_params, cell_no):
    """ Returns the WCDMA LAC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        WCDMA LAC to be used
    """
    key = "cell{}_wcdma_lac".format(cell_no)
    try:
        wcdma_lac = user_params[key]
    except KeyError:
        wcdma_lac = DEFAULT_LAC
    return wcdma_lac


def get_gsm_lac(user_params, cell_no):
    """ Returns the GSM LAC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        GSM LAC to be used
    """
    key = "cell{}_gsm_lac".format(cell_no)
    try:
        gsm_lac = user_params[key]
    except KeyError:
        gsm_lac = DEFAULT_LAC
    return gsm_lac


def get_lte_mcc(user_params, cell_no):
    """ Returns the LTE MCC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        LTE MCC to be used
    """
    key = "cell{}_lte_mcc".format(cell_no)
    try:
        lte_mcc = user_params[key]
    except KeyError:
        lte_mcc = DEFAULT_MCC
    return lte_mcc


def get_lte_mnc(user_params, cell_no):
    """ Returns the LTE MNC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        LTE MNC to be used
    """
    key = "cell{}_lte_mnc".format(cell_no)
    try:
        lte_mnc = user_params[key]
    except KeyError:
        lte_mnc = DEFAULT_MNC
    return lte_mnc


def get_wcdma_mcc(user_params, cell_no):
    """ Returns the WCDMA MCC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        WCDMA MCC to be used
    """
    key = "cell{}_wcdma_mcc".format(cell_no)
    try:
        wcdma_mcc = user_params[key]
    except KeyError:
        wcdma_mcc = DEFAULT_MCC
    return wcdma_mcc


def get_wcdma_mnc(user_params, cell_no):
    """ Returns the WCDMA MNC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        WCDMA MNC to be used
    """
    key = "cell{}_wcdma_mnc".format(cell_no)
    try:
        wcdma_mnc = user_params[key]
    except KeyError:
        wcdma_mnc = DEFAULT_MNC
    return wcdma_mnc


def get_gsm_mcc(user_params, cell_no):
    """ Returns the GSM MCC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        GSM MCC to be used
    """
    key = "cell{}_gsm_mcc".format(cell_no)
    try:
        gsm_mcc = user_params[key]
    except KeyError:
        gsm_mcc = DEFAULT_MCC
    return gsm_mcc


def get_gsm_mnc(user_params, cell_no):
    """ Returns the GSM MNC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        GSM MNC to be used
    """
    key = "cell{}_gsm_mnc".format(cell_no)
    try:
        gsm_mnc = user_params[key]
    except KeyError:
        gsm_mnc = DEFAULT_MNC
    return gsm_mnc


def get_1x_mcc(user_params, cell_no):
    """ Returns the 1X MCC to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        1X MCC to be used
    """
    key = "cell{}_1x_mcc".format(cell_no)
    try:
        cdma_1x_mcc = user_params[key]
    except KeyError:
        cdma_1x_mcc = DEFAULT_MCC
    return cdma_1x_mcc


def get_1x_channel(user_params, cell_no):
    """ Returns the 1X Channel to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        1X Channel to be used
    """
    key = "cell{}_1x_channel".format(cell_no)
    try:
        cdma_1x_channel = user_params[key]
    except KeyError:
        cdma_1x_channel = CDMA1X_CHANNEL_356
    return cdma_1x_channel


def get_1x_sid(user_params, cell_no):
    """ Returns the 1X SID to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        1X SID to be used
    """
    key = "cell{}_1x_sid".format(cell_no)
    try:
        cdma_1x_sid = user_params[key]
    except KeyError:
        cdma_1x_sid = CDMA1X_SID_0
    return cdma_1x_sid


def get_1x_nid(user_params, cell_no):
    """ Returns the 1X NID to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        1X NID to be used
    """
    key = "cell{}_1x_nid".format(cell_no)
    try:
        cdma_1x_nid = user_params[key]
    except KeyError:
        cdma_1x_nid = CDMA1X_NID_65535
    return cdma_1x_nid


def get_csfb_type(user_params):
    """ Returns the CSFB Type to be used from the user specified parameters
        or default value

    Args:
        user_params: pointer to user supplied parameters
        cell_no: specify the cell number this BTS is configured
        Anritsu supports two cells. so cell_1 or cell_2

    Returns:
        CSFB Type to be used
    """
    try:
        csfb_type = user_params["csfb_type"]
    except KeyError:
        csfb_type = CsfbType.CSFB_TYPE_REDIRECTION
    return csfb_type
