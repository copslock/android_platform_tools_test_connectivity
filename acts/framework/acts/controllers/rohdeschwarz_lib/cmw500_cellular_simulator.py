#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import time

from acts.controllers.rohdeschwarz_lib import cmw500
from acts.controllers import cellular_simulator as cc


class CMW500CellularSimulator(cc.AbstractCellularSimulator):
    """ A cellular simulator for telephony simulations based on the CMW 500
    controller. """

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = None

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = None

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = None

    # The maximum number of carriers that this simulator can support for LTE
    LTE_MAX_CARRIERS = None

    def __init__(self, ip_address, port):
        """ Initializes the cellular simulator.

        Args:
            ip_address: the ip address of the CMW500
            port: the port number for the CMW500 controller
        """
        super().__init__()

        try:
            self.cmw = cmw500.Cmw500(ip_address, port)
        except cmw500.CmwError:
            raise cc.CellularSimulatorError('Could not connect to CMW500.')

        self.bts = None
        self.dl_modulation = None
        self.ul_modulation = None

    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        raise NotImplementedError()

    def setup_lte_scenario(self):
        """ Configures the equipment for an LTE simulation. """
        self.bts = [self.cmw.get_base_station()]
        self.cmw.switch_lte_signalling(cmw500.LteState.LTE_ON)

    def setup_lte_ca_scenario(self):
        """ Configures the equipment for an LTE with CA simulation. """
        raise NotImplementedError()

    def set_band(self, bts_index, band):
        """ Sets the band for the indicated base station.

        Args:
            bts_index: the base station number
            band: the new band
        """
        bts = self.bts[bts_index]
        bts.duplex_mode = self.get_duplex_mode(band)
        band = 'OB' + band
        bts.band = band
        self.log.debug('Band set to {}'.format(band))

    def get_duplex_mode(self, band):
        """ Determines if the band uses FDD or TDD duplex mode

        Args:
            band: a band number

        Returns:
            an variable of class DuplexMode indicating if band is FDD or TDD
        """
        if 33 <= int(band) <= 46:
            return cmw500.DuplexMode.TDD
        else:
            return cmw500.DuplexMode.FDD

    def set_input_power(self, bts_index, input_power):
        """ Sets the input power for the indicated base station.

        Args:
            bts_index: the base station number
            input_power: the new input power
        """
        raise NotImplementedError()

    def set_output_power(self, bts_index, output_power):
        """ Sets the output power for the indicated base station.

        Args:
            bts_index: the base station number
            output_power: the new output power
        """
        raise NotImplementedError()

    def set_tdd_config(self, bts_index, tdd_config):
        """ Sets the tdd configuration number for the indicated base station.

        Args:
            bts_index: the base station number
            tdd_config: the new tdd configuration number
        """
        self.bts[bts_index].uldl_configuration = tdd_config

    def set_bandwidth(self, bts_index, bandwidth):
        """ Sets the bandwidth for the indicated base station.

        Args:
            bts_index: the base station number
            bandwidth: the new bandwidth
        """
        bts = self.bts[bts_index]

        if bandwidth == 20:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_20MHz
        elif bandwidth == 15:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_15MHz
        elif bandwidth == 10:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_10MHz
        elif bandwidth == 5:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_5MHz
        elif bandwidth == 3:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_3MHz
        elif bandwidth == 1.4:
            bts.bandwidth = cmw500.LteBandwidth.BANDWIDTH_1MHz
        else:
            msg = 'Bandwidth {} MHz is not valid for LTE'.format(bandwidth)
            raise ValueError(msg)

    def set_downlink_channel_number(self, bts_index, channel_number):
        """ Sets the downlink channel number for the indicated base station.

        Args:
            bts_index: the base station number
            channel_number: the new channel number
        """
        bts = self.bts[bts_index]
        bts.dl_channel = channel_number
        self.log.debug('Downlink Channel set to {}'.format(bts.dl_channel))

    def set_mimo_mode(self, bts_index, mimo_mode):
        """ Sets the mimo mode for the indicated base station.

        Args:
            bts_index: the base station number
            mimo_mode: the new mimo mode
        """
        bts = self.bts[bts_index]

        if mimo_mode == cmw500.MimoModes.MIMO1x1:
            self.cmw.configure_mimo_settings(cmw500.MimoScenario.SCEN1x1)
            bts.dl_antenna = cmw500.MimoModes.MIMO1x1

        elif mimo_mode == cmw500.MimoModes.MIMO2x2:
            self.cmw.configure_mimo_settings(cmw500.MimoScenario.SCEN2x2)
            bts.dl_antenna = cmw500.MimoModes.MIMO2x2

        elif mimo_mode == cmw500.MimoModes.MIMO4x4:
            self.cmw.configure_mimo_settings(cmw500.MimoScenario.SCEN4x4)
            bts.dl_antenna = cmw500.MimoModes.MIMO4x4
        else:
            RuntimeError('The requested MIMO mode is not supported.')

    def set_transmission_mode(self, bts_index, tmode):
        """ Sets the transmission mode for the indicated base station.

        Args:
            bts_index: the base station number
            tmode: the new transmission mode
        """
        bts = self.bts[bts_index]

        if (tmode in [
            cmw500.TransmissionModes.TM1,
            cmw500.TransmissionModes.TM7
        ] and bts.dl_antenna != cmw500.MimoModes.MIMO1x1):
            bts.transmode = tmode
        elif (tmode in cmw500.TransmissionModes.__members__ and
              bts.dl_antenna != cmw500.MimoModes.MIMO2x2):
            bts.transmode = tmode
        elif (tmode in [
            cmw500.TransmissionModes.TM2,
            cmw500.TransmissionModes.TM3,
            cmw500.TransmissionModes.TM4,
            cmw500.TransmissionModes.TM6,
            cmw500.TransmissionModes.TM9
        ] and bts.dl_antenna == cmw500.MimoModes.MIMO4x4):
            bts.transmode = tmode

        else:
            raise ValueError('Transmission modes should support the current '
                             'mimo mode')

    def set_scheduling_mode(self, bts_index, scheduling, mcs_dl=None,
                            mcs_ul=None, nrb_dl=None, nrb_ul=None):
        """ Sets the scheduling mode for the indicated base station.

        Args:
            bts_index: the base station number.
            scheduling: the new scheduling mode.
            mcs_dl: Downlink MCS.
            mcs_ul: Uplink MCS.
            nrb_dl: Number of RBs for downlink.
            nrb_ul: Number of RBs for uplink.
        """
        bts = self.bts[bts_index]
        bts.scheduling_mode = scheduling

        if not self.ul_modulation and self.dl_modulation:
            raise ValueError('Modulation should be set prior to scheduling '
                             'call')

        if scheduling == cmw500.SchedulingMode.RMC:

            if not nrb_ul and nrb_dl:
                raise ValueError('nrb_ul and nrb dl should not be none')

            bts.rb_configuration_ul = (nrb_ul, self.ul_modulation, 'KEEP')
            self.log.info('ul rb configurations set to {}'.format(
                bts.rb_configuration_ul))

            time.sleep(1)

            self.log.debug('Setting rb configurations for down link')
            bts.rb_configuration_dl = (nrb_dl, self.dl_modulation, 'KEEP')
            self.log.info('dl rb configurations set to {}'.format(
                bts.rb_configuration_ul))

        elif scheduling == cmw500.SchedulingMode.USERDEFINEDCH:

            if not all([nrb_ul, nrb_dl, mcs_dl, mcs_ul]):
                raise ValueError('All parameters are mandatory.')

            bts.rb_configuration_ul = (nrb_ul, 0, self.ul_modulation,
                                       mcs_ul)
            self.log.info('ul rb configurations set to {}'.format(
                bts.rb_configuration_ul))

            time.sleep(1)

            bts.rb_configuration_dl = (nrb_dl, 0, self.dl_modulation, mcs_dl)
            self.log.info('dl rb configurations set to {}'.format(
                bts.rb_configuration_dl))

    def set_enabled_for_ca(self, bts_index, enabled):
        """ Enables or disables the base station during carrier aggregation.

        Args:
            bts_index: the base station number
            enabled: whether the base station should be enabled for ca.
        """
        raise NotImplementedError()

    def set_dl_modulation(self, bts_index, modulation):
        """ Sets the DL modulation for the indicated base station.

        Args:
            bts_index: the base station number
            modulation: the new DL modulation
        """

        # This function is only used to store the values of modulation to
        # be inline with abstract class signature.
        self.dl_modulation = modulation
        self.log.warning('Modulation config stored but not applied until '
                         'set_scheduling_mode called.')

    def set_ul_modulation(self, bts_index, modulation):
        """ Sets the UL modulation for the indicated base station.

        Args:
            bts_index: the base station number
            modulation: the new UL modulation
        """
        # This function is only used to store the values of modulation to
        # be inline with abstract class signature.
        self.ul_modulation = modulation
        self.log.warning('Modulation config stored but not applied until '
                         'set_scheduling_mode called.')

    def set_tbs_pattern_on(self, bts_index, tbs_pattern_on):
        """ Enables or disables TBS pattern in the indicated base station.

        Args:
            bts_index: the base station number
            tbs_pattern_on: the new TBS pattern setting
        """
        raise NotImplementedError()

    def lte_attach_secondary_carriers(self):
        """ Activates the secondary carriers for CA. Requires the DUT to be
        attached to the primary carrier first. """
        raise NotImplementedError()

    def wait_until_attached(self, timeout=120):
        """ Waits until the DUT is attached to the primary carrier.

        Args:
            timeout: after this amount of time the method will raise a
                CellularSimulatorError exception. Default is 120 seconds.
        """
        self.cmw.wait_for_attached_state(timeout=timeout)

    def wait_until_communication_state(self, timeout=120):
        """ Waits until the DUT is in Communication state.

        Args:
            timeout: after this amount of time the method will raise a
                CellularSimulatorError exception. Default is 120 seconds.
        """
        self.cmw.wait_for_connected_state(timeout=timeout)

    def wait_until_idle_state(self, timeout=120):
        """ Waits until the DUT is in Idle state.

        Args:
            timeout: after this amount of time the method will raise a
                CellularSimulatorError exception. Default is 120 seconds.
        """
        raise NotImplementedError()

    def detach(self):
        """ Turns off all the base stations so the DUT loose connection."""
        self.cmw.disconnect()

    def stop(self):
        """ Stops current simulation. After calling this method, the simulator
        will need to be set up again. """
        raise NotImplementedError()

    def start_data_traffic(self):
        """ Starts transmitting data from the instrument to the DUT. """
        raise NotImplementedError()

    def stop_data_traffic(self):
        """ Stops transmitting data from the instrument to the DUT. """
        raise NotImplementedError()
