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
import acts.controllers.cellular_simulator as cc
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
            self.anritsu = md8475a.MD8475A(ip_address,
                                           md8475_version=self.MD8475_VERSION)
        except anritsu.AnristuError:
            raise cc.CellularSimulatorError('Could not connect to MD8475.')

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

    def setup_lte_ca_scenario(self):
        """ Configures the equipment for an LTE with CA simulation. """
        cell_file_name = self.LTE_CA_BASIC_CELL_FILE
        sim_file_name = self.LTE_CA_BASIC_SIM_FILE

        cell_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, cell_file_name)
        sim_file_path = ntpath.join(self.CALLBOX_CONFIG_PATH, sim_file_name)

        self.anritsu.load_simulation_paramfile(sim_file_path)
        self.anritsu.load_cell_paramfile(cell_file_path)
        self.anritsu.start_simulation()


class MD8475BCellularSimulator(MD8475CellularSimulator):

    MD8475_VERSION = 'B'

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = True

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = True

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = True

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
