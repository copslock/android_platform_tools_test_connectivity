#!/usr/bin python3
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
"""Python module for Rohde & Schwarz SMBV100 Vector Signal Generator."""

import acts.controllers.gnssinst_lib.abstract_inst as abstract_inst


class SMBV100Error(abstract_inst.SocketInstrumentError):
    """SMBV100 Instrument Error Class."""


class SMBV100(abstract_inst.SocketInstrument):
    """SMBV100 Class, inherted from abstract_inst SocketInstrument."""

    def __init__(self, ip_addr, ip_port):
        """Init method for SMBV100.

        Args:
            ip_addr: IP Address.
                Type, str.
            ip_port: TCPIP Port.
                Type, str.
        """
        super(SMBV100, self).__init__(ip_addr, ip_port)

        self.idn = ''

    def connect(self):
        """Init and Connect to SMBV100."""
        self._connect_socket()

        self.get_idn()

        infmsg = 'Connected to SMBV100, with ID: {}'.format(self.idn)
        self._logger.debug(infmsg)

    def close(self):
        """Close SMBV100."""
        self._close_socket()

        self._logger.debug('Closed connection to SMBV100')

    def get_idn(self):
        """Get the Idenification of SMBV100.

        Returns:
            SMBV100 Identifier
        """
        self.idn = self._query('*IDN?')

        return self.idn

    def preset(self):
        """Preset SMBV100 to default status."""
        self._send('*RST')

        self._logger.debug('Preset SMBV100')

    def set_rfout(self, state):
        """set SMBV100 RF output state.

        Args:
            state: RF output state.
                Type, str. Option, ON/OFF.

        Raises:
            SMBV100Error: raise when state is not ON/OFF.
        """

        if state not in ['ON', 'OFF']:
            raise SMBV100Error(error='"state" input must be "ON" or "OFF"',
                               command='set_rfout')

        self._send(':OUTP ' + state)

        infmsg = 'set SMBV100 RF output to "{}"'.format(state)
        self._logger.debug(infmsg)
