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

import ntpath
import time
import acts.controllers.cellular_simulator as cc
from acts.test_utils.power.tel_simulations import LteSimulation
from acts.controllers.anritsu_lib import md8475a
from acts.controllers.anritsu_lib import _anritsu_utils as anritsu


class MD8475CellularSimulator(cc.AbstractCellularSimulator):

    MD8475_VERSION = 'A'

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = False

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = False

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = False

    # The maximum number of carriers that this simulator can support for LTE
    LTE_MAX_CARRIERS = 2

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_default_LTE.wnssp'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_config.wnscp'
    LTE_CA_BASIC_SIM_FILE = 'SIM_LTE_CA.wnssp'
    LTE_CA_BASIC_CELL_FILE = 'CELL_LTE_CA_config.wnscp'

    # Filepath to the config files stored in the Anritsu callbox. Needs to be
    # formatted to replace {} with either A or B depending on the model.
    CALLBOX_CONFIG_PATH = 'C:\\Users\\MD8475A\\Documents\\DAN_configs\\'

    def __init__(self, ip_address):
        """ Initializes the cellular simulator.

        Args:
            ip_address: the ip address of the MD8475 instrument
        """
        super().__init__()

        try:
            self.anritsu = md8475a.MD8475A(
                ip_address, md8475_version=self.MD8475_VERSION)
        except anritsu.AnristuError:
            raise cc.CellularSimulatorError('Could not connect to MD8475.')

        self.bts = None

    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        self.anritsu.stop_simulation()
        self.anritsu.disconnect()

    def setup_lte_scenario(self):
        """ Configures the equipment for an LTE simulation. """
        cell_file_name = self.LTE_BASIC_CELL_FILE
        sim_file_name = self.LTE_BASIC_SIM_FILE

        cell_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, cell_file_name)
        sim_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, sim_file_name)

        self.anritsu.load_simulation_paramfile(sim_file_path)
        self.anritsu.load_cell_paramfile(cell_file_path)
        self.anritsu.start_simulation()

        self.bts = [self.anritsu.get_BTS(md8475a.BtsNumber.BTS1)]

    def setup_lte_ca_scenario(self):
        """ Configures the equipment for an LTE with CA simulation. """
        cell_file_name = self.LTE_CA_BASIC_CELL_FILE
        sim_file_name = self.LTE_CA_BASIC_SIM_FILE

        cell_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, cell_file_name)
        sim_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, sim_file_name)

        self.anritsu.load_simulation_paramfile(sim_file_path)
        self.anritsu.load_cell_paramfile(cell_file_path)
        self.anritsu.start_simulation()

        self.bts = [
            self.anritsu.get_BTS(md8475a.BtsNumber.BTS1),
            self.anritsu.get_BTS(md8475a.BtsNumber.BTS2)
        ]

    def configure_bts(self, config, bts_index=0):
        """ Commands the equipment to setup a base station with the required
        configuration. This method applies configurations that are common to all
        RATs.

        Args:
            config: a BaseSimulation.BtsConfig object.
            bts_index: the base station number.
        """

        bts_handle = self.bts[bts_index]

        if config.output_power:
            bts_handle.output_level = config.output_power

        if config.input_power:
            bts_handle.input_level = config.input_power

        if isinstance(config, LteSimulation.LteSimulation.BtsConfig):
            self.configure_lte_bts(config, bts_index)

    def configure_lte_bts(self, config, bts_index=0):
        """ Commands the equipment to setup an LTE base station with the
        required configuration.

        Args:
            config: an LteSimulation.BtsConfig object.
            bts_index: the base station number.
        """

        bts_handle = self.bts[bts_index]

        if config.band:
            self.set_band(bts_handle, config.band)

        if config.dlul_config:
            self.set_dlul_configuration(bts_handle, config.dlul_config)

        if config.bandwidth:
            self.set_channel_bandwidth(bts_handle, config.bandwidth)

        if config.dl_channel:
            # Temporarily adding this line to workaround a bug in the
            # Anritsu callbox in which the channel number needs to be set
            # to a different value before setting it to the final one.
            bts_handle.dl_channel = str(config.dl_channel + 1)
            time.sleep(8)
            bts_handle.dl_channel = str(config.dl_channel)

        if config.mimo_mode:
            self.set_mimo_mode(bts_handle, config.mimo_mode)

        if config.transmission_mode:
            self.set_transmission_mode(bts_handle, config.transmission_mode)

        if config.scheduling_mode:

            if (config.scheduling_mode == LteSimulation.SchedulingMode.STATIC
                    and not all([
                        config.dl_rbs, config.ul_rbs, config.dl_mcs,
                        config.ul_mcs
                    ])):
                raise ValueError('When the scheduling mode is set to manual, '
                                 'the RB and MCS parameters are required.')

            # If scheduling mode is set to Dynamic, the RB and MCS parameters
            # will be ignored by set_scheduling_mode.
            self.set_scheduling_mode(
                bts_handle,
                config.scheduling_mode,
                packet_rate=md8475a.BtsPacketRate.LTE_MANUAL,
                nrb_dl=config.dl_rbs,
                nrb_ul=config.ul_rbs,
                mcs_ul=config.ul_mcs,
                mcs_dl=config.dl_mcs)

        # This variable stores a boolean value so the following is needed to
        # differentiate False from None
        if config.dl_cc_enabled is not None:
            bts_handle.dl_cc_enabled = config.dl_cc_enabled

        if config.dl_modulation_order:
            bts_handle.lte_dl_modulation_order = config.dl_modulation_order

        if config.ul_modulation_order:
            bts_handle.lte_u_modulation_order = config.ul_modulation_order

        # This variable stores a boolean value so the following is needed to
        # differentiate False from None
        if config.tbs_pattern_on is not None:
            if config.tbs_pattern_on:
                bts_handle.tbs_pattern = "FULLALLOCATION"
            else:
                bts_handle.tbs_pattern = "OFF"

    def set_band(self, bts, band):
        """ Sets the right duplex mode before switching to a new band.

        Args:
            bts: basestation handle
            band: desired band
            calibrate_if_necessary: if False calibration will be skipped
        """

        bts.duplex_mode = self.get_duplex_mode(band).value
        bts.band = band
        time.sleep(5)  # It takes some time to propagate the new band

    def get_duplex_mode(self, band):
        """ Determines if the band uses FDD or TDD duplex mode

        Args:
            band: a band number
        Returns:
            an variable of class DuplexMode indicating if band is FDD or TDD
        """

        if 33 <= int(band) <= 46:
            return LteSimulation.DuplexMode.TDD
        else:
            return LteSimulation.DuplexMode.FDD

    def set_dlul_configuration(self, bts, config):
        """ Sets the frame structure for TDD bands.

        Args:
            config: the desired frame structure. An int between 0 and 6.
        """

        if not 0 <= config <= 6:
            raise ValueError("The frame structure configuration has to be a "
                             "number between 0 and 6")

        bts.uldl_configuration = config

        # Wait for the setting to propagate
        time.sleep(5)

    def set_channel_bandwidth(self, bts, bandwidth):
        """ Sets the LTE channel bandwidth (MHz)

        Args:
            bts: basestation handle
            bandwidth: desired bandwidth (MHz)
        """
        if bandwidth == 20:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_20MHz
        elif bandwidth == 15:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_15MHz
        elif bandwidth == 10:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_10MHz
        elif bandwidth == 5:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_5MHz
        elif bandwidth == 3:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_3MHz
        elif bandwidth == 1.4:
            bts.bandwidth = md8475a.BtsBandwidth.LTE_BANDWIDTH_1dot4MHz
        else:
            msg = "Bandwidth = {} MHz is not valid for LTE".format(bandwidth)
            self.log.error(msg)
            raise ValueError(msg)
        time.sleep(5)  # It takes some time to propagate the new settings

    def set_mimo_mode(self, bts, mimo):
        """ Sets the number of DL antennas for the desired MIMO mode.

        Args:
            bts: basestation handle
            mimo: object of class MimoMode
        """

        # If the requested mimo mode is not compatible with the current TM,
        # warn the user before changing the value.

        if mimo == LteSimulation.MimoMode.MIMO_1x1:
            if bts.transmode not in [
                    LteSimulation.TransmissionMode.TM1,
                    LteSimulation.TransmissionMode.TM7
            ]:
                self.log.warning(
                    "Using only 1 DL antennas is not allowed with "
                    "the current transmission mode. Changing the "
                    "number of DL antennas will override this "
                    "setting.")
            bts.dl_antenna = 1
        elif mimo == LteSimulation.MimoMode.MIMO_2x2:
            if bts.transmode not in [
                    LteSimulation.TransmissionMode.TM2,
                    LteSimulation.TransmissionMode.TM3,
                    LteSimulation.TransmissionMode.TM4,
                    LteSimulation.TransmissionMode.TM8,
                    LteSimulation.TransmissionMode.TM9
            ]:
                self.log.warning("Using two DL antennas is not allowed with "
                                 "the current transmission mode. Changing the "
                                 "number of DL antennas will override this "
                                 "setting.")
            bts.dl_antenna = 2
        elif mimo == LteSimulation.MimoMode.MIMO_4x4:
            if bts.transmode not in [
                    LteSimulation.TransmissionMode.TM2,
                    LteSimulation.TransmissionMode.TM3,
                    LteSimulation.TransmissionMode.TM4,
                    LteSimulation.TransmissionMode.TM9
            ]:
                self.log.warning("Using four DL antennas is not allowed with "
                                 "the current transmission mode. Changing the "
                                 "number of DL antennas will override this "
                                 "setting.")

            bts.dl_antenna = 4
        else:
            RuntimeError("The requested MIMO mode is not supported.")

    def set_scheduling_mode(self,
                            bts,
                            scheduling,
                            packet_rate=None,
                            mcs_dl=None,
                            mcs_ul=None,
                            nrb_dl=None,
                            nrb_ul=None):
        """ Sets the scheduling mode for LTE

        Args:
            bts: basestation handle
            scheduling: DYNAMIC or STATIC scheduling (Enum list)
            mcs_dl: Downlink MCS (only for STATIC scheduling)
            mcs_ul: Uplink MCS (only for STATIC scheduling)
            nrb_dl: Number of RBs for downlink (only for STATIC scheduling)
            nrb_ul: Number of RBs for uplink (only for STATIC scheduling)
        """

        bts.lte_scheduling_mode = scheduling.value

        if scheduling == LteSimulation.SchedulingMode.STATIC:

            if not packet_rate:
                raise RuntimeError("Packet rate needs to be indicated when "
                                   "selecting static scheduling.")

            bts.packet_rate = packet_rate

            if packet_rate == md8475a.BtsPacketRate.LTE_MANUAL:

                if not (mcs_dl and mcs_ul and nrb_dl and nrb_ul):
                    raise RuntimeError("When using manual packet rate the "
                                       "number of dl/ul RBs and the dl/ul "
                                       "MCS needs to be indicated with the "
                                       "optional arguments.")

                bts.lte_mcs_dl = mcs_dl
                bts.lte_mcs_ul = mcs_ul
                bts.nrb_dl = nrb_dl
                bts.nrb_ul = nrb_ul

        time.sleep(5)  # It takes some time to propagate the new settings

    def set_transmission_mode(self, bts, tmode):
        """ Sets the transmission mode for the LTE basetation

        Args:
            bts: basestation handle
            tmode: Enum list from class 'TransmissionModeLTE'
        """

        # If the selected transmission mode does not support the number of DL
        # antennas, throw an exception.
        if (tmode in [
                LteSimulation.TransmissionMode.TM1,
                LteSimulation.TransmissionMode.TM7
        ] and bts.dl_antenna != '1'):
            # TM1 and TM7 only support 1 DL antenna
            raise ValueError("{} allows only one DL antenna. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.".format(tmode.value))
        elif (tmode == LteSimulation.TransmissionMode.TM8
              and bts.dl_antenna != '2'):
            # TM8 requires 2 DL antennas
            raise ValueError("TM2 requires two DL antennas. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.")
        elif (tmode in [
                LteSimulation.TransmissionMode.TM2,
                LteSimulation.TransmissionMode.TM3,
                LteSimulation.TransmissionMode.TM4,
                LteSimulation.TransmissionMode.TM9
        ] and bts.dl_antenna == '1'):
            # TM2, TM3, TM4 and TM9 require 2 or 4 DL antennas
            raise ValueError("{} requires at least two DL atennas. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.".format(tmode.value))

        # The TM mode is allowed for the current number of DL antennas, so it
        # is safe to change this setting now
        bts.transmode = tmode.value

        time.sleep(5)  # It takes some time to propagate the new settings


class MD8475BCellularSimulator(MD8475CellularSimulator):

    MD8475_VERSION = 'B'

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = True

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = True

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = True

    # The maximum number of carriers that this simulator can support for LTE
    LTE_MAX_CARRIERS = 5

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_default_LTE.wnssp2'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_config.wnscp2'
    LTE_CA_BASIC_SIM_FILE = 'SIM_LTE_CA.wnssp2'
    LTE_CA_BASIC_CELL_FILE = 'CELL_LTE_CA_config.wnscp2'

    # Filepath to the config files stored in the Anritsu callbox. Needs to be
    # formatted to replace {} with either A or B depending on the model.
    CALLBOX_CONFIG_PATH = 'C:\\Users\\MD8475B\\Documents\\DAN_configs\\'

    def configure_lte_bts(self, config, bts_index=0):
        """ Commands the equipment to setup an LTE base station with the
        required configuration.

        Args:
            config: an LteSimulation.BtsConfig object.
            bts_index: the base station number.
        """

        bts_handle = self.bts[bts_index]

        # The callbox won't restore the band-dependent default values if the
        # request is to switch to the same band as the one the base station is
        # currently using. To ensure that default values are restored, go to a
        # different band before switching.
        if config.band and int(bts_handle.band) == config.band:
            # Using bands 1 and 2 but it could be any others
            bts_handle.band = '1' if config.band != 1 else '2'
            # Switching to config.band will be handled by the parent class
            # implementation of this method.

    def setup_lte_ca_scenario(self):
        """ The B model can support up to five carriers. """

        super().setup_lte_ca_scenario()

        self.bts.extend([
            self.anritsu.get_BTS(md8475a.BtsNumber.BTS3),
            self.anritsu.get_BTS(md8475a.BtsNumber.BTS4),
            self.anritsu.get_BTS(md8475a.BtsNumber.BTS5)
        ])
