#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- The Android Open Source Project
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

"""
Controller interface for Anritsu Signalling Tester MD8475A.
"""

import time
import socket
from enum import Enum
from enum import IntEnum

from . _anritsu_utils import AnritsuUtils
from . _anritsu_utils import AnritsuError

TERMINATOR = "\0"


class ProcessingStatus(Enum):
    ''' MD8475A processing status for UE,Packet,Voice,Video,SMS,
        PPP, PWS '''
    PROCESS_STATUS_NONE = "NONE"
    PROCESS_STATUS_NOTRUN = "NOTRUN"
    PROCESS_STATUS_POWEROFF = "POWEROFF"
    PROCESS_STATUS_REGISTRATION = "REGISTRATION"
    PROCESS_STATUS_DETACH = "DETACH"
    PROCESS_STATUS_IDLE = "IDLE"
    PROCESS_STATUS_ORIGINATION = "ORIGINATION"
    PROCESS_STATUS_HANDOVER = "HANDOVER"
    PROCESS_STATUS_UPDATING = "UPDATING"
    PROCESS_STATUS_TERMINATION = "TERMINATION"
    PROCESS_STATUS_COMMUNICATION = "COMMUNICATION"
    PROCESS_STATUS_UERELEASE = "UERELEASE"
    PROCESS_STATUS_NWRELEASE = "NWRELEASE"


class BtsNumber(Enum):
    '''ID number for MD8475A supported BTS '''
    BTS1 = "BTS1"
    BTS2 = "BTS2"
    BTS3 = "BTS3"
    BTS4 = "BTS4"


class BtsTechnology(Enum):
    ''' BTS system technology'''
    LTE = "LTE"
    WCDMA = "WCDMA"
    TDSCDMA = "TDSCDMA"
    GSM = "GSM"
    CDMA1X = "CDMA1X"
    EVDO = "EVDO"


class BtsBandwidth(Enum):
    ''' Values for Cell Bandwidth '''
    LTE_BANDWIDTH_1dot4MHz = "1.4MHz"
    LTE_BANDWIDTH_3MHz = "3MHz"
    LTE_BANDWIDTH_5MHz = "5MHz"
    LTE_BANDWIDTH_10MHz = "10MHz"
    LTE_BANDWIDTH_15MHz = "15MHz"
    LTE_BANDWIDTH_20MHz = "20MHz"


class BtsPacketRate(Enum):
    ''' Values for Cell Packet rate '''
    LTE_MANUAL = "MANUAL"
    LTE_BESTEFFORT = "BESTEFFORT"
    WCDMA_DLHSAUTO_REL7_UL384K = "DLHSAUTO_REL7_UL384K"
    WCDMA_DL18_0M_UL384K = "DL18_0M_UL384K"
    WCDMA_DL21_6M_UL384K = "DL21_6M_UL384K"
    WCDMA_DLHSAUTO_REL7_ULHSAUTO = "DLHSAUTO_REL7_ULHSAUTO"
    WCDMA_DL18_0M_UL1_46M = "DL18_0M_UL1_46M"
    WCDMA_DL18_0M_UL2_0M = "DL18_0M_UL2_0M"
    WCDMA_DL18_0M_UL5_76M = "DL18_0M_UL5_76M"
    WCDMA_DL21_6M_UL1_46M = "DL21_6M_UL1_46M"
    WCDMA_DL21_6M_UL2_0M = "DL21_6M_UL2_0M"
    WCDMA_DL21_6M_UL5_76M = "DL21_6M_UL5_76M"
    WCDMA_DLHSAUTO_REL8_UL384K = "DLHSAUTO_REL8_UL384K"
    WCDMA_DL23_4M_UL384K = "DL23_4M_UL384K"
    WCDMA_DL28_0M_UL384K = "DL28_0M_UL384K"
    WCDMA_DL36_0M_UL384K = "DL36_0M_UL384K"
    WCDMA_DL43_2M_UL384K = "DL43_2M_UL384K"
    WCDMA_DLHSAUTO_REL8_ULHSAUTO = "DLHSAUTO_REL8_ULHSAUTO"
    WCDMA_DL23_4M_UL1_46M = "DL23_4M_UL1_46M"
    WCDMA_DL23_4M_UL2_0M = "DL23_4M_UL2_0M"
    WCDMA_DL23_4M_UL5_76M = "DL23_4M_UL5_76M"
    WCDMA_DL28_0M_UL1_46M = "DL28_0M_UL1_46M"
    WCDMA_DL28_0M_UL2_0M = "DL28_0M_UL2_0M"
    WCDMA_DL28_0M_UL5_76M = "L28_0M_UL5_76M"
    WCDMA_DL36_0M_UL1_46M = "DL36_0M_UL1_46M"
    WCDMA_DL36_0M_UL2_0M = "DL36_0M_UL2_0M"
    WCDMA_DL36_0M_UL5_76M = "DL36_0M_UL5_76M"
    WCDMA_DL43_2M_UL1_46M = "DL43_2M_UL1_46M"
    WCDMA_DL43_2M_UL2_0M = "DL43_2M_UL2_0M"
    WCDMA_DL43_2M_UL5_76M = "L43_2M_UL5_76M"


class BtsPacketWindowSize(Enum):
    ''' Values for Cell Packet window size '''
    WINDOW_SIZE_1 = 1
    WINDOW_SIZE_8 = 8
    WINDOW_SIZE_16 = 16
    WINDOW_SIZE_32 = 32
    WINDOW_SIZE_64 = 64
    WINDOW_SIZE_128 = 128
    WINDOW_SIZE_256 = 256
    WINDOW_SIZE_512 = 512
    WINDOW_SIZE_768 = 768
    WINDOW_SIZE_1024 = 1024
    WINDOW_SIZE_1536 = 1536
    WINDOW_SIZE_2047 = 2047


class BtsServiceState(Enum):
    ''' Values for BTS service state '''
    SERVICE_STATE_IN = "IN"
    SERVICE_STATE_OUT = "OUT"


class BtsCellBarred(Enum):
    ''' Values for Cell barred parameter '''
    NOTBARRED = "NOTBARRED"
    BARRED = "BARRED"


class BtsAccessClassBarred(Enum):
    ''' Values for Access class barred parameter '''
    NOTBARRED = "NOTBARRED"
    EMERGENCY = "EMERGENCY"
    BARRED = "BARRED"
    USERSPECIFIC = "USERSPECIFIC"


class BtsLteEmergencyAccessClassBarred(Enum):
    ''' Values for Lte emergency access class barred parameter '''
    NOTBARRED = "NOTBARRED"
    BARRED = "BARRED"


class BtsNwNameEnable(Enum):
    ''' Values for BT network name enable parameter '''
    NAME_ENABLE = "ON"
    NAME_DISABLE = "OFF"


class IPAddressType(Enum):
    ''' Values for IP address type '''
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    IPV4V6 = "IPV4V6"


class TriggerMessageIDs(Enum):
    ''' ID for Trigger messages  '''
    RRC_CONNECTION_REQ = 111101
    RRC_CONN_REESTABLISH_REQ = 111100
    ATTACH_REQ = 141141
    DETACH_REQ = 141145
    MM_LOC_UPDATE_REQ = 221108
    GMM_ATTACH_REQ = 241101
    GMM_RA_UPDATE_REQ = 241108


class TriggerMessageReply(Enum):
    ''' Values for Trigger message reply parameter '''
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    IGNORE = "IGNORE"
    NONE = "NONE"
    ILLEGAL = "ILLEGAL"


class TestProcedure(Enum):
    ''' Values for different Test procedures in MD8475A '''
    PROCEDURE_BL = "BL"
    PROCEDURE_SELECTION = "SELECTION"
    PROCEDURE_RESELECTION = "RESELECTION"
    PROCEDURE_REDIRECTION = "REDIRECTION"
    PROCEDURE_HO = "HO"
    PROCEDURE_HHO = "HHO"
    PROCEDURE_SHO = "SHO"
    PROCEDURE_MEASUREMENT = "MEASUREMENT"
    PROCEDURE_CELLCHANGE = "CELLCHANGE"
    PROCEDURE_MULTICELL = "MULTICELL"


class TestPowerControl(Enum):
    ''' Values for power control in test procedure '''
    POWER_CONTROL_ENABLE = "ENABLE"
    POWER_CONTROL_DISABLE = "DISABLE"


class TestMeasurement(Enum):
    ''' Values for mesaurement in test procedure '''
    MEASUREMENT_ENABLE = "ENABLE"
    MEASUREMENT_DISABLE = "DISABLE"


_PROCESS_STATES = {
    "NONE": ProcessingStatus.PROCESS_STATUS_NONE,
    "NOTRUN": ProcessingStatus.PROCESS_STATUS_NOTRUN,
    "POWEROFF": ProcessingStatus.PROCESS_STATUS_POWEROFF,
    "REGISTRATION": ProcessingStatus.PROCESS_STATUS_REGISTRATION,
    "DETACH": ProcessingStatus.PROCESS_STATUS_DETACH,
    "IDLE": ProcessingStatus.PROCESS_STATUS_IDLE,
    "ORIGINATION": ProcessingStatus.PROCESS_STATUS_ORIGINATION,
    "HANDOVER": ProcessingStatus.PROCESS_STATUS_HANDOVER,
    "UPDATING": ProcessingStatus.PROCESS_STATUS_UPDATING,
    "TERMINATION": ProcessingStatus.PROCESS_STATUS_TERMINATION,
    "COMMUNICATION": ProcessingStatus.PROCESS_STATUS_COMMUNICATION,
    "UERELEASE": ProcessingStatus.PROCESS_STATUS_UERELEASE,
    "NWRELEASE": ProcessingStatus.PROCESS_STATUS_NWRELEASE,
}


class VirtualPhoneStatus(IntEnum):
    ''' MD8475A virtual phone status for UE voice and UE video
        PPP, PWS '''
    STATUS_IDLE = 0
    STATUS_VOICECALL_ORIGINATION = 1
    STATUS_VOICECALL_INCOMING = 2
    STATUS_VOICECALL_INPROGRESS = 3
    STATUS_VOICECALL_DISCONNECTING = 4
    STATUS_VOICECALL_DISCONNECTED = 5
    STATUS_VIDEOCALL_ORIGINATION = 6
    STATUS_VIDEOCALL_INCOMING = 7
    STATUS_VIDEOCALL_INPROGRESS = 8
    STATUS_VIDEOCALL_DISCONNECTING = 9
    STATUS_VIDEOCALL_DISCONNECTED = 10

_VP_STATUS = {
    "0": VirtualPhoneStatus.STATUS_IDLE,
    "1": VirtualPhoneStatus.STATUS_VOICECALL_ORIGINATION,
    "2": VirtualPhoneStatus.STATUS_VOICECALL_INCOMING,
    "3": VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS,
    "4": VirtualPhoneStatus.STATUS_VOICECALL_DISCONNECTING,
    "5": VirtualPhoneStatus.STATUS_VOICECALL_DISCONNECTED,
    "6": VirtualPhoneStatus.STATUS_VIDEOCALL_ORIGINATION,
    "7": VirtualPhoneStatus.STATUS_VIDEOCALL_INCOMING,
    "8": VirtualPhoneStatus.STATUS_VIDEOCALL_INPROGRESS,
    "9": VirtualPhoneStatus.STATUS_VIDEOCALL_DISCONNECTING,
    "10": VirtualPhoneStatus.STATUS_VIDEOCALL_DISCONNECTED,
}


class CsfbType(Enum):
    CSFB_TYPE_REDIRECTION = "REDIRECTION"
    CSFB_TYPE_HANDOVER = "HO"


class ReturnToEUTRAN(Enum):
    RETEUTRAN_ENABLE = "ENABLE"
    RETEUTRAN_DISABLE = "DISABLE"


class MD8475A():
    """Class to communicate with Anritsu MD8475A Signalling Tester.
       This uses GPIB command to interface with Anritsu MD8475A """

    def __init__(self, ip_address):
        self._error_reporting = True
        self._ipaddr = ip_address
        print(self._ipaddr)

        # Open socket connection to Signaling Tester
        print("Opening Socket Connection with "
              "Signaling Tester ({}) ".format(self._ipaddr))
        try:
            self._sock = socket.create_connection(("192.168.137.1", 28002),
                                                  timeout=30)
            self.send_query("*IDN?", 60)
            print("Communication with Signaling Tester OK.")
            print("Opened Socket connection to ({})"
                  "with handle ({})".format(self._ipaddr, self._sock))
            # launching Smart Studio Application needed for the simulation
            ret = self.launch_smartstudio()
        except socket.timeout:
            raise AnritsuError("Timeout happened while conencting to"
                               " Anritsu MD8475A")
        except socket.error:
            raise AnritsuError("Socket creation error")

    def get_BTS(self, btsnumber):
        return _BaseTransceiverStation(self, btsnumber)

    def get_AnritsuTestCases(self):
        return _AnritsuTestCases(self)

    def get_VirtualPhone(self):
        return _VirtualPhone(self)

    def get_PDN(self, pdn_number):
        return _PacketDataNetwork(self, pdn_number)

    def get_TriggerMessage(self):
        return _TriggerMessage(self)

    def send_query(self, query, sock_timeout=10):
        print("--> {}".format(query))
        querytoSend = (query + TERMINATOR).encode('utf-8')
        self._sock.settimeout(sock_timeout)
        try:
            self._sock.send(querytoSend)
            result = self._sock.recv(256).rstrip(TERMINATOR.encode('utf-8'))
            response = result.decode('utf-8')
            print('<-- {}'.format(response))
            return response
        except socket.timeout:
            raise AnritsuError("Timeout: Response from Anritsu")
        except socket.error:
            raise AnritsuError("Socket Error")

    def send_command(self, command, sock_timeout=20):
        print("--> {}".format(command))
        if self._error_reporting:
            cmdToSend = (command + ";ERROR?" + TERMINATOR).encode('utf-8')
            self._sock.settimeout(sock_timeout)
            try:
                self._sock.send(cmdToSend)
                err = self._sock.recv(256).rstrip(TERMINATOR.encode('utf-8'))
                error = int(err.decode('utf-8'))
                if error != 0:
                    raise AnritsuError(error,  command)
                else:
                    # check operation status
                    status = self.send_query("*OPC?")
                    if status != "1":
                        raise AnritsuError("Operation not completed")
            except socket.timeout:
                raise AnritsuError("Timeout for Command Response from Anritsu")
            except socket.error:
                raise AnritsuError("Socket Error for Anritsu command")
        else:
            cmdToSend = (command + TERMINATOR).encode('utf-8')
            try:
                self._sock.send(cmdToSend)
            except socket.error:
                raise AnritsuError("Socket Error", command)
            return

    def launch_smartstudio(self):
        ''' launch the Smart studio application '''
        # check the Smart Studio status . If Smart Studio doesn't exist ,
        # start it.if it is running, stop it. Smart Studio should be in
        # NOTRUN (Simulation Stopped) state to start new simulation
        stat = self.send_query("STAT?", 30)
        if stat == "NOTEXIST":
            print("Launching Smart Studio Application,"
                  "it takes about a minute.")
            time_to_wait = 90
            sleep_interval = 15
            waiting_time = 0

            err = self.send_command("RUN", 120)
            stat = self.send_query("STAT?")
            while stat != "NOTRUN":
                time.sleep(sleep_interval)
                waiting_time = waiting_time + sleep_interval
                if waiting_time <= time_to_wait:
                    stat = self.send_query("STAT?")
                else:
                    raise AnritsuError("Timeout: Smart Studio launch")
        elif stat == "RUNNING":
            # Stop simulation if necessary
            self.send_command("STOP", 60)
            stat = self.send_query("STAT?")

        # The state of the Smart Studio should be NOTRUN at this point
        # after the one of the steps from above
        if stat != "NOTRUN":
            logging.error("Can not launch Smart Studio, "
                          "please shut down all the Smart Studio SW components")
            raise AnritsuError("Could not run SmartStudio")

    def close_smartstudio(self):
        self.stop_simulation()
        self.send_command("EXIT", 60)

    def start_simulation(self):
        ''' Starting the simulation of the network model.
            simulation model or simulation parameter file
            should be set before starting the simulation'''
        time_to_wait = 45
        sleep_interval = 5
        waiting_time = 0

        self.send_command("START", 60)
        callstat = self.send_query("CALLSTAT?").split(",")
        while callstat[0] != "POWEROFF":
            time.sleep(sleep_interval)
            waiting_time = waiting_time + sleep_interval
            if waiting_time <= time_to_wait:
                callstat = self.send_query("CALLSTAT?").split(",")
            else:
                raise AnritsuError("Timeout: Starting simulation")

    def stop_simulation(self):
        ''' stops simulation'''
        stat = self.send_query("STAT?")
        # Stop simulation if its is RUNNING
        if stat == "RUNNING":
            self.set_simulation_state_to_poweroff()
            self.send_command("STOP", 60)
            stat = self.send_query("STAT?")
            if stat != "NOTRUN":
                logging.error("Failed to stop simulation")
                raise AnritsuError("Failed to stop simulation")
        self.send_command("*RST", 30)

    def load_simulation_paramfile(self, filepath):
        self.stop_simulation()
        cmd = "LOADSIMPARAM \"" + filepath + '\";ERROR?'
        self.send_query(cmd)

    def set_simulation_model(self, bts1, bts2=None, bts3=None, bts4=None):
        self.stop_simulation()
        simmodel = bts1.value
        if bts2 is not None:
            simmodel = simmodel + "," + bts2.value
        cmd = "SIMMODEL " + simmodel
        self.send_command(cmd)

    def set_simulation_state_to_poweroff(self):
        self.send_command("RESETSIMULATION POWEROFF")
        time_to_wait = 30
        sleep_interval = 2
        waiting_time = 0

        callstat = self.send_query("CALLSTAT?").split(",")
        while callstat[0] != "POWEROFF":
            time.sleep(sleep_interval)
            waiting_time = waiting_time + sleep_interval
            if waiting_time <= time_to_wait:
                callstat = self.send_query("CALLSTAT?").split(",")
            else:
                break

    def set_simulation_state_to_idle(self, btsnumber):
        if not isinstance(btsnumber, BtsNumber):
            raise ValueError(' The parameter should be of type "BtsNumber" ')
        cmd = "RESETSIMULATION IDLE," + btsnumber
        self.send_command(cmd)
        time_to_wait = 30
        sleep_interval = 2
        waiting_time = 0

        callstat = self.send_query("CALLSTAT?").split(",")
        while callstat[0] != "IDLE":
            time.sleep(sleep_interval)
            waiting_time = waiting_time + sleep_interval
            if waiting_time <= time_to_wait:
                callstat = self.send_query("CALLSTAT?").split(",")
            else:
                break

    def wait_for_ue_registration(self):
        print("wait for UE to register on the network.")
        time_to_wait = 240
        sleep_interval = 1
        waiting_time = 0

        callstat = self.send_query("CALLSTAT?").split(",")
        print(callstat)
        while callstat[0] != "IDLE" and callstat[1] != "COMMUNICATION":
            time.sleep(sleep_interval)
            waiting_time = waiting_time + sleep_interval
            if waiting_time <= time_to_wait:
                callstat = self.send_query("CALLSTAT?").split(",")
                print(callstat)
            else:
                raise AnritsuError("UE failed to register on network")

    def get_camping_cell(self):
        ''' returns a tuple (BTS number, RAT Technology) '''
        bts_number, rat_info = self.send_query("CAMPINGCELL?").split(",")
        return bts_number, rat_info

    def start_testcase(self):
        self.send_command("STARTTEST")

    def get_testcase_status(self):
        return self.send_query("TESTSTAT?")

    @property
    def gateway_ipv4addr(self):
        return self.send_query("DGIPV4?")

    @gateway_ipv4addr.setter
    def gateway_ipv4addr(self, ipv4_addr):
        cmd = "DGIPV4 " + ipv4_addr
        self.send_command(cmd)

    def get_ue_status(self):
        UE_STATUS_INDEX = 0
        ue_status = self.send_query("CALLSTAT?").split(",")[UE_STATUS_INDEX]
        return _PROCESS_STATES[ue_status]

    def get_packet_status(self):
        PACKET_STATUS_INDEX = 1
        packet_status = self.send_query("CALLSTAT?").split(",")[PACKET_STATUS_INDEX]
        return _PROCESS_STATES[packet_status]

    def disconnect(self):
        # exit smart studio application
        self.close_smartstudio()
        self._sock.close()

    def machine_reboot(self):
        self.send_command("REBOOT")

    @property
    def csfb_type(self):
        return self.send_query("SIMMODELEX? CSFB")

    @csfb_type.setter
    def csfb_type(self, type):
        if not isinstance(type, CsfbType):
            raise ValueError('The parameter should be of type "CsfbType" ')
        cmd = "SIMMODELEX CSFB," + type.value
        self.send_command(cmd)

    @property
    def csfb_return_to_eutran(self):
        return self.send_query("SIMMODELEX? RETEUTRAN")

    @csfb_return_to_eutran.setter
    def csfb_return_to_eutran(self, enable):
        if not isinstance(enable, ReturnToEUTRAN):
            raise ValueError('The parameter should be of type "ReturnToEUTRAN"')
        cmd = "SIMMODELEX RETEUTRAN," + enable.value
        self.send_command(cmd)


class _AnritsuTestCases:
    '''Class to interact with the MD8475 supported test procedures '''

    def __init__(self, anritsu):
        self._anritsu = anritsu

    @property
    def procedure(self):
        return self._anritsu.send_query("TESTPROCEDURE?")

    @procedure.setter
    def procedure(self, procedure):
        if not isinstance(procedure, TestProcedure):
            raise ValueError('The parameter should be of type "TestProcedure" ')
        cmd = "TESTPROCEDURE " + procedure.value
        self._anritsu.send_command(cmd)

    @property
    def bts_direction(self):
        return self._anritsu.send_query("TESTBTSDIRECTION?")

    @bts_direction.setter
    def bts_direction(self, direction):
        ''' assign the value as a tuple (from-bts,to_bts) of type BtsNumber'''
        if not isinstance(direction, tuple) or len(direction) is not 2:
            raise ValueError("Pass a tuple with two items")
        from_bts, to_bts = direction
        if (isinstance(from_bts, BtsNumber) and isinstance(to_bts, BtsNumber)):
            cmd = "TESTBTSDIRECTION {},{}".format(from_bts.value, to_bts.value)
            self._anritsu.send_command(cmd)
        else:
            raise ValueError(' The parameters should be of type "BtsNumber" ')

    @property
    def registration_timeout(self):
        return self._anritsu.send_query("TESTREGISTRATIONTIMEOUT?")

    @registration_timeout.setter
    def registration_timeout(self, timeout_value):
        cmd = "TESTREGISTRATIONTIMEOUT " + str(timeout_value)
        self._anritsu.send_command(cmd)

    @property
    def power_control(self):
        return self._anritsu.send_query("TESTPOWERCONTROL?")

    @power_control.setter
    def power_control(self, enable):
        if not isinstance(enable, TestPowerControl):
            raise ValueError(' The parameter should be of type'
                             ' "TestPowerControl" ')
        cmd = "TESTPOWERCONTROL " + enable.value
        self._anritsu.send_command(cmd)

    @property
    def measurement_LTE(self):
        return self._anritsu.send_query("TESTMEASUREMENT? LTE")

    @measurement_LTE.setter
    def measurement_LTE(self, enable):
        if not isinstance(enable, TestMeasurement):
            raise ValueError(' The parameter should be of type'
                             ' "TestMeasurement" ')
        cmd = "TESTMEASUREMENT LTE," + enable.value
        self._anritsu.send_command(cmd)

    @property
    def measurement_WCDMA(self):
        return self._anritsu.send_query("TESTMEASUREMENT? WCDMA")

    @measurement_WCDMA.setter
    def measurement_WCDMA(self, enable):
        if not isinstance(enable, TestMeasurement):
            raise ValueError(' The parameter should be of type'
                             ' "TestMeasurement" ')
        cmd = "TESTMEASUREMENT WCDMA," + enable.value
        self._anritsu.send_command(cmd)

    @property
    def measurement_TDSCDMA(self):
        return self._anritsu.send_query("TESTMEASUREMENT? TDSCDMA")

    @measurement_TDSCDMA.setter
    def measurement_WCDMA(self, enable):
        if not isinstance(enable, TestMeasurement):
            raise ValueError(' The parameter should be of type'
                             ' "TestMeasurement" ')
        cmd = "TESTMEASUREMENT TDSCDMA," + enable.value
        self._anritsu.send_command(cmd)

    def set_pdn_targeteps(self, pdn_order, pdn_number=1):
        cmd = "TESTPDNTARGETEPS " + pdn_order
        if pdn_order == "USER":
            cmd = cmd + "," + str(pdn_number)
        self._anritsu.send_command(cmd)


class _BaseTransceiverStation:
    '''Class to interact different BTS supported by MD8475 '''
    def __init__(self, anritsu, btsnumber):
        if not isinstance(btsnumber, BtsNumber):
            raise ValueError(' The parameter should be of type "BtsNumber" ')
        self._bts_number = btsnumber.value
        self._anritsu = anritsu

    @property
    def output_level(self):
        cmd = "OLVL? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @output_level.setter
    def output_level(self, level):
        cmd = "OLVL {},{}".format(level, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def input_level(self):
        cmd = "RFLVL? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @input_level.setter
    def input_level(self, level):
        cmd = "RFLVL {},{}".format(level, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def band(self):
        cmd = "BAND? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @band.setter
    def band(self, band):
        cmd = "BAND {},{}".format(band, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def bandwidth(self):
        cmd = "BANDWIDTH? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @bandwidth.setter
    def bandwidth(self, bandwidth):
        if not isinstance(bandwidth, BtsBandwidth):
            raise ValueError(' The parameter should be of type "BtsBandwidth" ')
        cmd = "BANDWIDTH {},{}".format(bandwidth.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def packet_rate(self):
        cmd = "PACKETRATE? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @packet_rate.setter
    def packet_rate(self, packetrate):
        if not isinstance(packetrate, BtsPacketRate):
            raise ValueError(' The parameter should be of type'
                             ' "BtsPacketRate" ')
        cmd = "PACKETRATE {},{}".format(packetrate.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def ul_windowsize(self):
        cmd = "ULWINSIZE? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @ul_windowsize.setter
    def ul_windowsize(self, windowsize):
        if not isinstance(windowsize, BtsPacketWindowSize):
            raise ValueError(' The parameter should be of type'
                             ' "BtsPacketWindowSize" ')
        cmd = "ULWINSIZE {},{}".format(windowsize.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def dl_windowsize(self):
        cmd = "DLWINSIZE? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @dl_windowsize.setter
    def dl_windowsize(self, windowsize):
        if not isinstance(windowsize, BtsPacketWindowSize):
            raise ValueError(' The parameter should be of type'
                             ' "BtsPacketWindowSize" ')
        cmd = "DLWINSIZE {},{}".format(windowsize.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def service_state(self):
        cmd = "OUTOFSERVICE? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @service_state.setter
    def service_state(self, service_state):
        if not isinstance(service_state, BtsServiceState):
            raise ValueError(' The parameter should be of type'
                             ' "BtsServiceState" ')
        cmd = "OUTOFSERVICE {},{}".format(service_state.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def cell_barred(self):
        cmd = "CELLBARRED?" + self._bts_number
        return self._anritsu.send_query(cmd)

    @cell_barred.setter
    def cell_barred(self, barred_option):
        if not isinstance(barred_option, BtsCellBarred):
            raise ValueError(' The parameter should be of type'
                             ' "BtsCellBarred" ')
        cmd = "CELLBARRED {},{}".format(barred_option.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def accessclass_barred(self):
        cmd = "ACBARRED? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @accessclass_barred.setter
    def accessclass_barred(self, barred_option):
        if not isinstance(barred_option, BtsAccessClassBarred):
            raise ValueError(' The parameter should be of type'
                             ' "BtsAccessClassBarred" ')
        cmd = "ACBARRED {},{}".format(barred_option.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def lteemergency_ac_barred(self):
        cmd = "LTEEMERGENCYACBARRED? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @lteemergency_ac_barred.setter
    def lteemergency_ac_barred(self, barred_option):
        if not isinstance(barred_option, BtsLteEmergencyAccessClassBarred):
            raise ValueError(' The parameter should be of type'
                             ' "BtsLteEmergencyAccessClassBarred" ')
        cmd = "LTEEMERGENCYACBARRED {},{}".format(barred_option.value,
                                                  self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def mcc(self):
        cmd = "MCC? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @mcc.setter
    def mcc(self, mcc_code):
        cmd = "MCC {},{}".format(mcc_code, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def mnc(self):
        cmd = "MNC? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @mnc.setter
    def mnc(self, mnc_code):
        cmd = "MNC {},{}".format(mnc_code, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def nw_fullname_enable(self):
        cmd = "NWFNAMEON? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @nw_fullname_enable.setter
    def nw_fullname_enable(self, enable):
        if not isinstance(enable, BtsNwNameEnable):
            raise ValueError(' The parameter should be of type'
                             ' "BtsNwNameEnable" ')
        cmd = "NWFNAMEON {},{}".format(enable.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def nw_fullname(self):
        cmd = "NWFNAME? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @nw_fullname.setter
    def nw_fullname(self, fullname):
        cmd = "NWFNAME {},{}".format(fullname, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def nw_shortname_enable(self):
        cmd = "NWSNAMEON? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @nw_shortname_enable.setter
    def nw_shortname_enable(self, enable):
        if not isinstance(enable, BtsNwNameEnable):
            raise ValueError(' The parameter should be of type'
                             ' "BtsNwNameEnable" ')
        cmd = "NWSNAMEON {},{}".format(enable.value, self._bts_number)
        self._anritsu.send_command(cmd)

    @property
    def nw_shortname(self):
        cmd = "NWSNAME? " + self._bts_number
        return self._anritsu.send_query(cmd)

    @nw_shortname.setter
    def nw_shortname(self, shortname):
        cmd = "NWSNAME {},{}".format(shortname, self._bts_number)
        self._anritsu.send_command(cmd)

    def apply_parameter_changes(self):
        '''USe to apply the parameter changes at run time '''
        cmd = "APPLYPARAM"
        self._anritsu.send_command(cmd)


class _VirtualPhone:
    '''Class to interact with virtual phone supported by MD8475 '''
    def __init__(self, anritsu):
        self._anritsu = anritsu

    @property
    def id(self):
        cmd = "VPID? "
        return self._anritsu.send_query(cmd)

    @id.setter
    def id(self, phonenumber):
        cmd = "VPID {}".format(phonenumber)
        self._anritsu.send_command(cmd)

    @property
    def auto_answer(self):
        cmd = "VPAUTOANSWER? "
        return self._anritsu.send_query(cmd)

    @auto_answer.setter
    def auto_answer(self, option):
        enable = "OFF"
        time = 5

        try:
            enable, time = option
        except ValueError:
            if enable != "OFF":
                raise ValueError("Pass a tuple with two items for"
                                 " Turning on Auto Answer")
        cmd = "VPAUTOANSWER {},{}".format(enable, time)
        self._anritsu.send_command(cmd)

    @property
    def calling_mode(self):
        cmd = "VPCALLINGMODE? "
        return self._anritsu.send_query(cmd)

    @calling_mode.setter
    def calling_mode(self, calling_mode):
        cmd = "VPCALLINGMODE {}".format(calling_mode)
        self._anritsu.send_command(cmd)

    def set_voice_off_hook(self):
        cmd = "OPERATEVPHONE 0"
        return self._anritsu.send_command(cmd)

    def set_voice_on_hook(self):
        cmd = "OPERATEVPHONE 1"
        return self._anritsu.send_command(cmd)

    def set_video_off_hook(self):
        cmd = "OPERATEVPHONE 2"
        return self._anritsu.send_command(cmd)

    def set_video_on_hook(self):
        cmd = "OPERATEVPHONE 3"
        return self._anritsu.send_command(cmd)

    def set_call_waiting(self):
        cmd = "OPERATEVPHONE 4"
        return self._anritsu.send_command(cmd)

    @property
    def status(self):
        cmd = "VPSTAT?"
        status = self._anritsu.send_query(cmd)
        return _VP_STATUS[status]

    def sendSms(self, phoneNumber, message):
        cmd = ("SENDSMS /?PhoneNumber=001122334455&Sender={}&Text={}"
               "&DCS=00").format(phoneNumber, AnritsuUtils.gsm_encode(message))
        return self._anritsu.send_command(cmd)

    def receiveSms(self):
        return self._anritsu.send_query("RECEIVESMS?")

    def setSmsStatusReport(self, status):
        cmd = "SMSSTATUSREPORT {}".format(status)
        print(cmd)
        return self._anritsu.send_command(cmd)


class _PacketDataNetwork:
    '''Class to configure PDN parameters'''
    def __init__(self, anritsu, pdnnumber):
        self._pdn_number = pdnnumber
        self._anritsu = anritsu

    @property
    def ue_address_iptype(self):
        cmd = "PDNIPTYPE? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @ue_address_iptype.setter
    def ue_address_iptype(self, ip_type):
        if not isinstance(ip_type, IPAddressType):
            raise ValueError(' The parameter should be of type "IPAddressType"')
        cmd = "PDNIPTYPE {},{}".format(self._pdn_number, ip_type.value)
        self._anritsu.send_command(cmd)

    @property
    def ue_address_ipv4(self):
        cmd = "PDNIPV4? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @ue_address_ipv4.setter
    def ue_address_ipv4(self, ip_address):
        cmd = "PDNIPV4 {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def ue_address_ipv6(self):
        cmd = "PDNIPV6? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @ue_address_ipv6.setter
    def ue_address_ipv6(self, ip_address):
        cmd = "PDNIPV6 {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def primary_dns_address_ipv4(self):
        cmd = "PDNDNSIPV4PRI? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @primary_dns_address_ipv4.setter
    def primary_dns_address_ipv4(self, ip_address):
        cmd = "PDNDNSIPV4PRI {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def secondary_dns_address_ipv4(self):
        cmd = "PDNDNSIPV4SEC? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @secondary_dns_address_ipv4.setter
    def secondary_dns_address_ipv4(self, ip_address):
        cmd = "PDNDNSIPV4SEC {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def dns_address_ipv6(self):
        cmd = "PDNDNSIPV6? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @dns_address_ipv6.setter
    def dns_address_ipv6(self, ip_address):
        cmd = "PDNDNSIPV6 {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def cscf_address_ipv4(self):
        cmd = "PDNPCSCFIPV4? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @cscf_address_ipv4.setter
    def cscf_address_ipv4(self, ip_address):
        cmd = "PDNPCSCFIPV4 {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)

    @property
    def cscf_address_ipv6(self):
        cmd = "PDNPCSCFIPV6? " + self._pdn_number
        return self._anritsu.send_query(cmd)

    @cscf_address_ipv6.setter
    def cscf_address_ipv6(self, ip_address):
        cmd = "PDNPCSCFIPV6 {},{}".format(self._pdn_number, ip_address)
        self._anritsu.send_command(cmd)


class _TriggerMessage:
    '''Class to interact with trigger message handling supported by MD8475 '''
    def __init__(self, anritsu):
        self._anritsu = anritsu

    def set_reply_type(self, message_id, reply_type):
        if not isinstance(message_id, TriggerMessageIDs):
            raise ValueError(' The parameter should be of type'
                             ' "TriggerMessageIDs"')
        if not isinstance(reply_type, TriggerMessageReply):
            raise ValueError(' The parameter should be of type'
                             ' "TriggerMessageReply"')

        cmd = "REJECTTYPE {},{}".format(message_id.value, reply_type.value)
        self._anritsu.send_command(cmd)

    def set_reject_cause(self, message_id, cause):
        if not isinstance(message_id, TriggerMessageIDs):
            raise ValueError(' The parameter should be of type'
                             ' "TriggerMessageIDs"')

        cmd = "REJECTCAUSE {},{}".format(message_id.value, cause)
        self._anritsu.send_command(cmd)
