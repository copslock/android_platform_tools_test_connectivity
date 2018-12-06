#!/usr/bin/env python3.4
#
#   Copyright 2018 - The Android Open Source Project
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

from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.controllers.anritsu_lib.md8475a import TestProcedure
from acts.controllers.anritsu_lib.md8475a import TestPowerControl
from acts.controllers.anritsu_lib.md8475a import TestMeasurement
from acts.test_utils.power.tel_simulations.LteSimulation import LteSimulation


class LteCaSimulation(LteSimulation):
    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_LTE_CA'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_CA_config'

    def __init__(self, anritsu, log, dut, test_config, calibration_table):
        """ Configures Anritsu system for LTE simulation with carrier
        aggregation.

        Loads a simple LTE simulation enviroment with 5 basestations.

        Args:
            anritsu: the Anritsu callbox controller
            log: a logger handle
            dut: the android device handler
            test_config: test configuration obtained from the config file
            calibration_table: a dictionary containing path losses for
                different bands.

        """

        super().__init__(anritsu, log, dut, test_config, calibration_table)

        self.bts2 = self.anritsu.get_BTS(BtsNumber.BTS2)
        self.bts3 = self.anritsu.get_BTS(BtsNumber.BTS3)
        self.bts4 = self.anritsu.get_BTS(BtsNumber.BTS4)
        self.bts5 = self.anritsu.get_BTS(BtsNumber.BTS5)

    def parse_parameters(self, parameters):
        """ Configs an LTE simulation with CA using a list of parameters.

        Calls the parent method first, then consumes parameters specific to LTE

        Args:
            parameters: list of parameters
        Returns:
            False if there was an error while parsing the config
        """

        if not super(LteSimulation, self).parse_parameters(parameters):
            return False
        self.set_band(self.bts1, 3)

        self.set_band(self.bts2, 3, calibrate_if_necessary=False)
        # self.set_band(self.bts3, 7, calibrate_if_necessary=False)
        # self.set_band(self.bts4, 7, calibrate_if_necessary=False)
        # self.set_band(self.bts5, 28, calibrate_if_necessary=False)

        time.sleep(10)
        self.bts2.dl_channel = 1773
        # self.bts4.dl_channel = 3298

        self.set_channel_bandwidth(self.bts1, 20)
        self.set_channel_bandwidth(self.bts2, 20)
        # self.set_channel_bandwidth(self.bts3, 20)
        # self.set_channel_bandwidth(self.bts4, 20)
        # self.set_channel_bandwidth(self.bts5, 20)

        # No errors were found
        return True

    def start_test_case(self):
        """ Attaches the phone to all the other basestations.

        Starts the CA test case. Requires being attached to
        basestation 1 first.

        """

        testcase = self.anritsu.get_AnritsuTestCases()
        testcase.procedure = TestProcedure.PROCEDURE_MULTICELL
        testcase.power_control = TestPowerControl.POWER_CONTROL_DISABLE
        testcase.measurement_LTE = TestMeasurement.MEASUREMENT_DISABLE
        # self.bts1.dl_cc_enabled = True
        self.bts2.dl_cc_enabled = True
        self.bts3.dl_cc_enabled = True
        self.bts4.dl_cc_enabled = True
        self.bts5.dl_cc_enabled = False
        self.anritsu.start_testcase()

        retry_counter = 0
        self.log.info("Waiting for the test case to start...")
        time.sleep(5)

        while self.anritsu.get_testcase_status() == "0":
            retry_counter += 1
            if retry_counter == 3:
                self.log.error("The test case failed to start.")
                return False
            time.sleep(10)

        return True
