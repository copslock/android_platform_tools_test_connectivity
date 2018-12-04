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
import re
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

    # Simulation config keywords contained in the test name
    PARAM_CA = 'ca'

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

        self.bts = [self.bts1, self.anritsu.get_BTS(BtsNumber.BTS2)]

        if self.anritsu._md8475_version == 'B':
            self.bts.extend([
                anritsu.get_BTS(BtsNumber.BTS3),
                anritsu.get_BTS(BtsNumber.BTS4),
                anritsu.get_BTS(BtsNumber.BTS5)
            ])

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

        # Get the CA band configuration

        values = self.consume_parameter(parameters, self.PARAM_CA, 1)

        if not values:
            self.log.error(
                "The test name needs to include parameter '{}' followed by "
                "the CA configuration. For example: ca_3c7c28a".format(
                    self.PARAM_CA))
            return False

        # Carrier aggregation configurations are indicated with the band numbers
        # followed by the CA classes in a single string. For example, for 5 CA
        # using 3C 7C and 28A the parameter value should be 3c7c28a.
        ca_configs = re.findall(r'(\d+[abcABC])', values[1])

        if not ca_configs:
            self.log.error(
                "The CA configuration has to be indicated with one string as "
                "in the following example: ca_3c7c28a".format(self.PARAM_CA))
            return False

        carriers = []
        bts_index = 0

        # Elements in the ca_configs array are combinations of band numbers
        # and CA classes. For example, '7A', '3C', etc.

        for ca in ca_configs:

            band = int(ca[:-1])
            ca_class = ca[-1]

            if ca_class.upper() == 'B':
                self.log.error("Class B carrier aggregation is not supported.")
                return False

            if band in carriers:
                self.log.error("Intra-band non contiguous carrier aggregation "
                               "is not supported.")
                return False

            if ca_class.upper() == 'A':

                if bts_index >= len(self.bts):
                    self.log.error("This callbox model doesn't allow the "
                                   "requested CA configuration")
                    return False

                self.set_band(
                    self.bts[bts_index],
                    band,
                    calibrate_if_necessary=bts_index == 0)

                self.set_channel_bandwidth(self.bts[bts_index], 20)

                bts_index += 1

            elif ca_class.upper() == 'C':

                if bts_index + 1 >= len(self.bts):
                    self.log.error("This callbox model doesn't allow the "
                                   "requested CA configuration")
                    return False

                self.set_band(
                    self.bts[bts_index],
                    band,
                    calibrate_if_necessary=bts_index == 0)
                self.set_band(
                    self.bts[bts_index + 1],
                    band,
                    calibrate_if_necessary=False)

                self.set_channel_bandwidth(self.bts[bts_index], 20)
                self.set_channel_bandwidth(self.bts[bts_index], 20)

                self.bts[bts_index + 1].dl_channel = str(
                    int(self.bts[bts_index + 1].dl_channel) + 20 * 10 - 2)

                bts_index += 2

            else:
                self.log.error("Invalid carrier aggregation configuration: "
                               "{}{}.".format(band, ca_class))
                return False

            carriers.append(band)

        # Ensure there are at least two carriers being used
        self.num_carriers = bts_index
        if self.num_carriers < 2:
            self.log.error("At least two carriers need to be indicated for the"
                           " carrier aggregation sim.")
            return False

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

        for bts_index in range(1, self.num_carriers):
            self.bts[bts_index].dl_cc_enabled = True

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
