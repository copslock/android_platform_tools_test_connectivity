#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#           http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import time

from enum import Enum

from acts.controllers import abstract_inst

LTE_ATTACH_RESP = 'ATT'
LTE_CONN_RESP = 'CONN'
LTE_PSWITCHED_ON_RESP = 'ON'
LTE_PSWITCHED_OFF_RESP = 'OFF'
LTE_TURN_ON_RESP = 'ON,ADJ'
LTE_TURN_OFF_RESP = 'OFF,ADJ'


class LteState(Enum):
    """LTE ON and OFF"""
    LTE_ON = 'ON'
    LTE_OFF = 'OFF'


class BtsNumber(Enum):
    """Base station Identifiers."""
    BTS1 = 'PCC'
    BTS2 = 'SCC1'
    BTS3 = 'SCC2'
    BTS4 = 'SCC3'
    BTS5 = 'SCC4'
    BTS6 = 'SCC6'
    BTS7 = 'SCC7'


class LteBandwidth(Enum):
    """Supported LTE bandwidths."""
    BANDWIDTH_1MHz = 'B014'
    BANDWIDTH_3MHz = 'B030'
    BANDWIDTH_5MHz = 'B050'
    BANDWIDTH_10MHz = 'B100'
    BANDWIDTH_15MHz = 'B150'
    BANDWIDTH_20MHz = 'B200'


class DuplexMode(Enum):
    """Duplex Modes"""
    FDD = 'FDD'
    TDD = 'TDD'


class TransmissionModes(Enum):
    """Supported transmission modes."""
    TM1 = 'TM1'
    TM2 = 'TM2'
    TM3 = 'TM3'
    TM4 = 'TM4'
    TM6 = 'TM6'
    TM7 = 'TM7'
    TM8 = 'TM8'
    TM9 = 'TM9'


class UseCarrierSpecific(Enum):
    """Enable or disable carrier specific."""
    UCS_ON = 'ON'
    UCS_OFF = 'OFF'


class Cmw500(abstract_inst.SocketInstrument):

    def __init__(self, ip_addr, port):
        """Init method to setup variables for controllers.

        Args:
              ip_addr: Controller's ip address.
              port: Port
        """
        super(Cmw500, self).__init__(ip_addr, port)
        self._connect_socket()
        self._send('*CLS')
        self._send('*ESE 0;*SRE 0')
        self._send('*CLS')
        self._send('*ESE 1;*SRE 4')
        self._send('SYST:DISP:UPD ON')

    def switch_lte_signalling(self, state):
        """Turns LTE signalling ON/OFF.

        Args:
              state: ON/OFF.
        """
        cmd = 'SOURce:LTE:SIGN:CELL:STATe {}'.format(state.value)
        self.send_and_recv(cmd)
        self.wait_for_lte_state_change()

    def enable_packet_switching(self):
        """Enable packet switching in call box."""
        self.send_and_recv('CALL:LTE:SIGN:PSWitched:ACTion CONNect')
        self.wait_for_pswitched_state()

    def disable_packet_switching(self):
        """Disable packet switching in call box."""
        self.send_and_recv('CALL:LTE:SIGN:PSWitched:ACTion DISConnect')
        self.wait_for_pswitched_state()

    @property
    def use_carrier_specific(self):
        """Gets current status of carrier specific duplex configuration."""
        return self.send_and_recv('CONFigure:LTE:SIGN:DMODe:UCSPECific?')

    @use_carrier_specific.setter
    def use_carrier_specific(self, state):
        """Sets the carrier specific duplex configuration.

        Args:
            state: ON/OFF UCS configuration.
        """
        cmd = 'CONFigure:LTE:SIGN:DMODe:UCSPECific {}'.format(state)
        self.send_and_recv(cmd)

    def send_and_recv(self, cmd):
        """Send and recv the status of the command.

        Args:
            cmd: Command to send.

        Returns:
            status: returns the status of the command sent.
        """

        self._send(cmd)
        if '?' in cmd:
            status = self._recv()
            return status

    def set_mimo(self):
        """Sets the scenario for the test."""
        # TODO:(ganeshganesh) Create a common function to set mimo modes.
        self.send_and_recv('ROUTe:LTE:SIGN:SCENario:SCELl:FLEXible SUW1,RF1C,'
                           'RX1,RF1C,TX1')

    def wait_for_lte_state_change(self, timeout=20):
        """Waits until the state of LTE changes.

        Args:
            timeout: timeout for lte to be turned ON/OFF.

        Raises:
            CmwError on timeout.
        """
        end_time = time.time() + timeout
        while time.time() <= end_time:
            state = self.send_and_recv('SOURce:LTE:SIGN:CELL:STATe:ALL?')

            if state == LTE_TURN_ON_RESP:
                self._logger.debug('LTE turned ON.')
                break
            elif state == LTE_TURN_OFF_RESP:
                self._logger.debug('LTE turned OFF.')
                break
        else:
            raise CmwError('Failed to turn ON/OFF lte signalling.')

    def wait_for_pswitched_state(self, timeout=10):
        """Wait until pswitched state.

        Args:
            timeout: timeout for lte pswitched state.

        Raises:
            CmwError on timeout.
        """
        end_time = time.time() + timeout
        while time.time() <= end_time:
            state = self.send_and_recv('FETCh:LTE:SIGN:PSWitched:STATe?')
            if state == LTE_PSWITCHED_ON_RESP:
                self._logger.debug('Connection to setup initiated.')
                break
            elif state == LTE_PSWITCHED_OFF_RESP:
                self._logger.debug('Connection to setup detached.')
                break
        else:
            raise CmwError('Failure in setting up/detaching connection')

    def wait_for_connected_state(self, timeout=120):
        """Attach the controller with device.

        Args:
            timeout: timeout for phone to get attached.

        Raises:
            CmwError on time out.
        """
        end_time = time.time() + timeout
        while time.time() <= end_time:
            state = self.send_and_recv('FETCh:LTE:SIGN:PSWitched:STATe?')

            if state == LTE_ATTACH_RESP:
                self._logger.debug('Call box attached with device')
                break
        else:
            raise CmwError('Device could not be attached')

        conn_state = self.send_and_recv('SENSe:LTE:SIGN:RRCState?')

        if conn_state == LTE_CONN_RESP:
            self._logger.debug('Call box connected with device')
        else:
            raise CmwError('Call box could not be connected with device')

    def reset(self):
        """System level reset"""
        self.send_and_recv('*RST; *OPC')

    @property
    def get_instrument_id(self):
        """Gets instrument identification number"""
        return self.send_and_recv('*IDN?')

    def disconnect(self):
        """Detach controller from device and switch to local mode."""
        self.switch_lte_signalling(LteState.LTE_OFF)
        self.close_remote_mode()
        self._close_socket()

    def close_remote_mode(self):
        """Exits remote mode to local mode."""
        self.send_and_recv('&GTL')

    def get_base_station(self, bts_num=BtsNumber.BTS1):
        """Gets the base station object based on bts num. By default
        bts_num set to PCC

        Args:
            bts_num: base station identifier

        Returns:
            base station object.
        """
        return BaseStation(self, bts_num)


class BaseStation(object):
    """Class to interact with different base stations"""

    def __init__(self, cmw, bts_num):
        if not isinstance(bts_num, BtsNumber):
            raise ValueError('bts_num should be an instance of BtsNumber.')
        self._bts = bts_num.value
        self._cmw = cmw

    @property
    def duplex_mode(self):
        """Gets current duplex of cell."""
        cmd = 'CONFigure:LTE:SIGN:{}:DMODe?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @duplex_mode.setter
    def duplex_mode(self, mode):
        """Sets the Duplex mode of cell.

        Args:
            mode: String indicating FDD or TDD.
        """
        if not isinstance(mode, DuplexMode):
            raise ValueError('mode should be an instance of DuplexMode.')
        cmd = 'CONFigure:LTE:SIGN:{}:DMODe {}'.format(self._bts, mode.value)
        self._cmw.send_and_recv(cmd)

    @property
    def band(self):
        """Gets the current band of cell."""
        cmd = 'CONFigure:LTE:SIGN:{}:BAND?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @band.setter
    def band(self, band):
        """Sets the Band of cell.

        Args:
            band: band of cell.
        """
        cmd = 'CONFigure:LTE:SIGN:{}:BAND {}'.format(self._bts, band)
        self._cmw.send_and_recv(cmd)

    @property
    def dl_channel(self):
        """Gets the downlink channel of cell."""
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:DL?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @dl_channel.setter
    def dl_channel(self, channel):
        """Sets the downlink channel number of cell.

        Args:
            channel: downlink channel number of cell.
        """
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:DL {}'.format(
            self._bts, channel)
        self._cmw.send_and_recv(cmd)

    @property
    def ul_channel(self):
        """Gets the uplink channel of cell."""
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:UL?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @ul_channel.setter
    def ul_channel(self, channel):
        """Sets the up link channel number of cell.

        Args:
            channel: up link channel number of cell.
        """
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:UL {}'.format(
            self._bts, channel)
        self._cmw.send_and_recv(cmd)

    @property
    def bandwidth(self):
        """Get the channel bandwidth of the cell."""
        cmd = 'CONFigure:LTE:SIGN:CELL:BANDwidth:{}:DL?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @bandwidth.setter
    def bandwidth(self, bandwidth):
        """Sets the channel bandwidth of the cell.

        Args:
            bandwidth: channel bandwidth of cell.
        """
        if not isinstance(bandwidth, LteBandwidth):
            raise ValueError('bandwidth should be an instance of '
                             'LteBandwidth.')
        cmd = 'CONFigure:LTE:SIGN:CELL:BANDwidth:{}:DL {}'.format(
            self._bts, bandwidth.value)
        self._cmw.send_and_recv(cmd)

    @property
    def ul_frequency(self):
        """Get the uplink frequency of the cell."""
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:UL? MHZ'.format(
            self._bts)
        return self._cmw.send_and_recv(cmd)

    @ul_frequency.setter
    def ul_frequency(self, freq):
        """Get the uplink frequency of the cell.

        Args:
            freq: uplink frequency of the cell.
        """
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:UL {} MHZ'.format(
            self._bts, freq)
        self._cmw.send_and_recv(cmd)

    @property
    def dl_frequency(self):
        """Get the downlink frequency of the cell"""
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:DL? MHZ'.format(
            self._bts)
        return self._cmw.send_and_recv(cmd)

    @dl_frequency.setter
    def dl_frequency(self, freq):
        """Get the downlink frequency of the cell.

        Args:
            freq: downlink frequency of the cell.
        """
        cmd = 'CONFigure:LTE:SIGN:RFSettings:{}:CHANnel:DL {} MHZ'.format(
            self._bts, freq)
        self._cmw.send_and_recv(cmd)

    @property
    def transmode(self):
        """Gets the TM of cell."""
        cmd = 'CONFigure:LTE:SIGN:CONNection:{}:TRANsmission?'.format(
            self._bts)
        return self._cmw.send_and_recv(cmd)

    @transmode.setter
    def transmode(self, tm_mode):
        """Sets the TM of cell.

        Args:
            tm_mode: TM of cell.
        """
        if not isinstance(tm_mode, TransmissionModes):
            raise ValueError('tm_mode should be an instance of '
                             'Transmission modes.')
        cmd = 'CONFigure:LTE:SIGN:CONNection:{}:TRANsmission {}'.format(
            self._bts, tm_mode.value)
        self._cmw.send_and_recv(cmd)

    @property
    def downlink_power_level(self):
        """Gets RSPRE level."""
        cmd = 'CONFigure:LTE:SIGN:DL:{}:RSEPre:LEVel?'.format(self._bts)
        return self._cmw.send_and_recv(cmd)

    @downlink_power_level.setter
    def downlink_power_level(self, pwlevel):
        """Modifies RSPRE level.

        Args:
            pwlevel: power level in dBm.
        """
        cmd = 'CONFigure:LTE:SIGN:DL:{}:RSEPre:LEVel {}'.format(self._bts,
                                                                pwlevel)
        self._cmw.send_and_recv(cmd)


class CmwError(Exception):
    """Class to raise exceptions related to cmw."""
