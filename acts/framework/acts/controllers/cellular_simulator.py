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
from acts import logger


class AbstractCellularSimulator:
    """ A generic cellular simulator controller class that can be derived to
    implement equipment specific classes and allows the tests to be implemented
    without depending on a singular instrument model.

    This class defines the interface that every cellular simulator controller
    needs to implement and shouldn't be instantiated by itself. """

    # Indicates if it is able to use 256 QAM as the downlink modulation for LTE
    LTE_SUPPORTS_DL_256QAM = None

    # Indicates if it is able to use 64 QAM as the uplink modulation for LTE
    LTE_SUPPORTS_UL_64QAM = None

    # Indicates if 4x4 MIMO is supported for LTE
    LTE_SUPPORTS_4X4_MIMO = None

    # The maximum number of carriers that this simulator can support for LTE
    LTE_MAX_CARRIERS = None

    def __init__(self):
        """ Initializes the cellular simulator. """
        self.log = logger.create_tagged_trace_logger('CellularSimulator')

    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        raise NotImplementedError()

    def setup_lte_scenario(self):
        """ Configures the equipment for an LTE simulation. """
        raise NotImplementedError()

    def setup_lte_ca_scenario(self):
        """ Configures the equipment for an LTE with CA simulation. """
        raise NotImplementedError()

    def configure_bts(self, config, bts_index=0):
        """ Commands the equipment to setup a base station with the required
        configuration. This method applies configurations that are common to all
        RATs.

        Args:
            config: a BaseSimulation.BtsConfig object.
            bts_index: the base station number.
        """
        raise NotImplementedError()

    def configure_lte_bts(self, config, bts_index=0):
        """ Commands the equipment to setup an LTE base station with the
        required configuration.

        Args:
            config: an LteSimulation.BtsConfig object.
            bts_index: the base station number.
        """
        raise NotImplementedError()


class CellularSimulatorError(Exception):
    """ Exceptions thrown when the cellular equipment is unreachable or it
    returns an error after receiving a command. """
    pass
