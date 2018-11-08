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
import math
from enum import Enum

from acts.controllers.anritsu_lib.md8475a import BtsBandwidth
from acts.controllers.anritsu_lib.md8475a import BtsPacketRate
from acts.test_utils.power.tel_simulations.BaseSimulation import BaseSimulation
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_ONLY


class LteSimulation(BaseSimulation):
    """ Simple LTE simulation with only one basestation.

    """

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.
    LTE_BASIC_SIM_FILE = 'SIM_default_LTE'
    LTE_BASIC_CELL_FILE = 'CELL_LTE_config'

    # Simulation config keywords contained in the test name
    PARAM_BW = "bw"
    PARAM_SCHEDULING = "scheduling"
    PARAM_SCHEDULING_STATIC = "static"
    PARAM_SCHEDULING_DYNAMIC = "dynamic"
    PARAM_PATTERN = "pattern"
    PARAM_TM = "tm"
    PARAM_UL_PW = 'pul'
    PARAM_DL_PW = 'pdl'
    PARAM_BAND = "band"
    PARAM_MIMO = "mimo"

    class TransmissionMode(Enum):
        ''' Transmission modes for LTE (e.g., TM1, TM4, ..)

        '''
        TM1 = "TM1"
        TM2 = "TM2"
        TM3 = "TM3"
        TM4 = "TM4"
        TM7 = "TM7"
        TM8 = "TM8"
        TM9 = "TM9"

    class MimoMode(Enum):
        """ Mimo modes """

        MIMO_1x1 = "1x1"
        MIMO_2x2 = "2x2"
        MIMO_4x4 = "4x4"

    class SchedulingMode(Enum):
        ''' Traffic scheduling modes (e.g., STATIC, DYNAMIC)

        '''
        DYNAMIC = 0
        STATIC = 1

    # RSRP signal levels thresholds (as reported by Android) in dBm/15KHz.
    # Excellent is set to -75 since callbox B Tx power is limited to -30 dBm
    downlink_rsrp_dictionary = {
        'excellent': -75,
        'high': -110,
        'medium': -115,
        'weak': -120
    }

    # Transmitted output power for the phone (dBm)
    uplink_signal_level_dictionary = {
        'max': 23,
        'high': 13,
        'medium': 3,
        'low': -20
    }

    # Total RBs for each bandwidth

    total_rbs_dictionary = {
        BtsBandwidth.LTE_BANDWIDTH_20MHz.value: 100,
        BtsBandwidth.LTE_BANDWIDTH_15MHz.value: 75,
        BtsBandwidth.LTE_BANDWIDTH_10MHz.value: 50,
        BtsBandwidth.LTE_BANDWIDTH_5MHz.value: 25,
        BtsBandwidth.LTE_BANDWIDTH_3MHz.value: 15,
        BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value: 6
    }


    # RB groups for each bandwidth

    rbg_dictionary = {
        BtsBandwidth.LTE_BANDWIDTH_20MHz.value: 4,
        BtsBandwidth.LTE_BANDWIDTH_15MHz.value: 4,
        BtsBandwidth.LTE_BANDWIDTH_10MHz.value: 3,
        BtsBandwidth.LTE_BANDWIDTH_5MHz.value: 2,
        BtsBandwidth.LTE_BANDWIDTH_3MHz.value: 2,
        BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value: 1
    }


    def __init__(self, anritsu, log, dut, calibration_table):

        """ Configures Anritsu system for LTE simulation with 1 basetation

        Loads a simple LTE simulation enviroment with 1 basestation.

        Args:
            anritsu: the Anritsu callbox controller
            log: a logger handle
            dut: the android device handler
            calibration_table: a dictionary containing path losses for
                different bands.

        """

        super().__init__(anritsu, log, dut, calibration_table)
        base_path = 'C:\\Users\MD8475' + self.anritsu._md8475_version + '\Documents\DAN_configs\\'

        if self.anritsu._md8475_version == 'A':
            self.sim_file_path = base_path + self.LTE_BASIC_SIM_FILE + '.wnssp'
            self.cell_file_path = base_path + self.LTE_BASIC_CELL_FILE + '.wnscp'
        else:
            self.sim_file_path = base_path + self.LTE_BASIC_SIM_FILE + '.wnssp2'
            self.cell_file_path = base_path + self.LTE_BASIC_CELL_FILE + '.wnscp2'

        if not dut.droid.telephonySetPreferredNetworkTypesForSubscription(NETWORK_MODE_LTE_ONLY,
            dut.droid.subscriptionGetDefaultSubId()):
            log.error("Couldn't set preferred network type.")
        else:
            log.info("Preferred network type set.")

    def parse_parameters(self, parameters):
        """ Configs an LTE simulation using a list of parameters.

        Calls the parent method first, then consumes parameters specific to LTE.

        Args:
            parameters: list of parameters
        Returns:
            False if there was an error while parsing the config
        """

        if not super().parse_parameters(parameters):
            return False

        # Setup band
        try:
          values = self.consume_parameter(parameters, self.PARAM_BAND, 1)
          band = values[1]

        except:
          self.log.error("The test name needs to include parameter {} followed by required band.".format(self.PARAM_BAND))
          return False
        else:
          self.set_band(self.bts1, band)

        # Setup bandwidth
        try:
          values = self.consume_parameter(parameters, self.PARAM_BW, 1)
          bw = float(values[1])

          if bw == 14:
              bw = 1.4
        except:
          self.log.error("The test name needs to include parameter {} followed by an int value "
                         "(to indicate 1.4 MHz use 14).".format(self.PARAM_BW))
          return False
        else:
            self.set_channel_bandwidth(self.bts1, bw)

        # Setup mimo mode

        values = self.consume_parameter(parameters, self.PARAM_MIMO, 1)

        for mimo_mode in LteSimulation.MimoMode:
            if values[1] == mimo_mode.value:
                mimo = mimo_mode
                break
        else:
            raise ValueError("The {} parameter needs to be followed by either "
                             "1x1, 2x2 or 4x4.".format(self.PARAM_MIMO))

        self.set_mimo_mode(self.bts1, mimo)

        # Setup transmission mode
        try:
            values = self.consume_parameter(parameters, self.PARAM_TM, 1)

            if values[1] == "1":
                tm = LteSimulation.TransmissionMode.TM1
            elif values[1] == "2":
                tm = LteSimulation.TransmissionMode.TM2
            elif values[1] == "3":
                tm = LteSimulation.TransmissionMode.TM3
            elif values[1] == "4":
                tm = LteSimulation.TransmissionMode.TM4
            else:
                raise ValueError()
        except:
            self.log.error("The test name needs to include parameter {} followed by an int value from 1 to 4 indicating"
                           " transmission mode.".format(self.PARAM_TM))
            return False
        else:
            self.set_transmission_mode(self.bts1, tm)

        # Setup scheduling mode
        try:
            values = self.consume_parameter(parameters, self.PARAM_SCHEDULING, 1)

            if values[1] == self.PARAM_SCHEDULING_DYNAMIC:
                scheduling = LteSimulation.SchedulingMode.DYNAMIC
            elif values[1] == self.PARAM_SCHEDULING_STATIC:
                scheduling = LteSimulation.SchedulingMode.STATIC

        except ValueError:
            self.log.error(
                "The test name needs to include parameter {} followed by either "
                                   "dynamic or static.".format(self.PARAM_SCHEDULING))
            return False

        if scheduling == LteSimulation.SchedulingMode.STATIC:

            try:

                values = self.consume_parameter(parameters,
                                                self.PARAM_PATTERN,
                                                2)
                dl_pattern = int(values[1])
                ul_pattern = int(values[2])

            except ValueError:

                self.log.error(
                    "When scheduling mode is set to static the parameter {} "
                    "has to be included followed by two ints separated by an "
                    "underscore indicating downlink and uplink percentages of"
                    " total rbs.".format(
                        self.PARAM_PATTERN
                    )
                )

                return False

            else:

                if not (0 <= dl_pattern <= 100 and 0 <= ul_pattern <= 100):

                    self.log.error(
                        "The scheduling pattern parameters need to be two "
                        "positive numbers between 0 and 100."
                    )
                    return False

                dl_rbs, ul_rbs = self.allocation_percentages_to_rbs(self.bts1,
                                                                    dl_pattern,
                                                                    ul_pattern)

                self.set_scheduling_mode(self.bts1,
                                         LteSimulation.SchedulingMode.STATIC,
                                         nrb_dl=dl_rbs,
                                         nrb_ul=ul_rbs)

        else:

            self.set_scheduling_mode(self.bts1,
                                     LteSimulation.SchedulingMode.DYNAMIC)

        # Setup uplink power
        try:
            values = self.consume_parameter(parameters, self.PARAM_UL_PW, 1)

            if values[1] not in self.uplink_signal_level_dictionary:
                raise ValueError("Invalid signal level value.")
            else:
                power = self.uplink_signal_level_dictionary[values[1]]
        except:
            self.log.error(
                "The test name needs to include parameter {} followed by one the following values: {}.".format(
                    self.PARAM_UL_PW,
                    ["\n" + val for val in self.uplink_signal_level_dictionary.keys()]
                ))
            return False
        else:
            # Power is not set on the callbox until after the simulation is started. Will save this value in
            # a variable and use it lated
            self.sim_ul_power = power

        # Setup downlink power
        try:
            values = self.consume_parameter(parameters, self.PARAM_DL_PW, 1)

            if values[1] not in self.downlink_rsrp_dictionary:
                raise ValueError("Invalid signal level value.")
            else:
                power = self.downlink_rsrp_dictionary[values[1]]
        except:
            self.log.error(
                "The test name needs to include parameter {} followed by one the following values: {}.".format(
                    self.PARAM_DL_PW,
                    ["\n" + val for val in self.downlink_rsrp_dictionary.keys()]
                ))
            return False
        else:
            # Power is not set on the callbox until after the simulation is started. Will save this value in
            # a variable and use it later
            self.sim_dl_power = power

        # No errors were found
        return True


    def set_downlink_rx_power(self, rsrp):
        """ Sets downlink rx power in RSRP using calibration

        Lte simulation overrides this method so that it can convert from
        RSRP to total signal power transmitted from the basestation.

        Args:
            rsrp: desired rsrp, contained in a key value pair
        """

        power = self.rsrp_to_signal_power(rsrp, self.bts1)

        self.log.info("Setting downlink signal level to {} RSRP ({} dBm)".format(rsrp, power))

        # Use parent method to set signal level
        super().set_downlink_rx_power(power)


    def downlink_calibration(self, bts, rat = None, power_units_conversion_func = None):
        """ Computes downlink path loss and returns the calibration value

        The bts needs to be set at the desired config (bandwidth, mode, etc)
        before running the calibration. The phone also needs to be attached
        to the desired basesation for calibration

        Args:
            bts: basestation handle
            rat: ignored, replaced by 'lteRsrp'
            power_units_conversion_func: ignored, replaced by self.rsrp_to_signal_power

        Returns:
            Dowlink calibration value and measured DL power. Note that the
            phone only reports RSRP of the primary chain
        """

        return super().downlink_calibration(bts, rat='lteRsrp', power_units_conversion_func=self.rsrp_to_signal_power)

    def rsrp_to_signal_power(self, rsrp, bts):
        """ Converts rsrp to total band signal power

        RSRP is measured per subcarrier, so total band power needs to be multiplied
        by the number of subcarriers being used.

        Args:
            rsrp: desired rsrp in dBm
            bts: basestation handler for which the unit conversion is done

        Returns:
            Total band signal power in dBm
        """

        bandwidth = bts.bandwidth

        if bandwidth == BtsBandwidth.LTE_BANDWIDTH_20MHz.value:       # 100 RBs
            power = rsrp + 30.79
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_15MHz.value:     # 75 RBs
            power = rsrp + 29.54
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_10MHz.value:     # 50 RBs
            power = rsrp + 27.78
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_5MHz.value:      # 25 RBs
            power = rsrp + 24.77
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_3MHz.value:      # 15 RBs
            power = rsrp + 22.55
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value:  # 6 RBs
            power = rsrp + 18.57
        else:
            raise ValueError("Invalid bandwidth value.")

        return power

    def maximum_downlink_throughput(self):
        """ Calculates maximum achievable downlink throughput in the current simulation state.

        Returns:
            Maximum throughput in mbps.

        """

        bandwidth = self.bts1.bandwidth
        chains = float(self.bts1.dl_antenna)

        if bandwidth == BtsBandwidth.LTE_BANDWIDTH_20MHz.value:
            return 71.11 * chains
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_15MHz.value:
            return 52.75 * chains
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_10MHz.value:
            return 29.88 * chains
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_5MHz.value:
            return 14.11 * chains
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_3MHz.value:
            return 5.34 * chains
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value:
            return 0.842 * chains
        else:
            raise ValueError("Invalid bandwidth value.")

    def maximum_uplink_throughput(self):
        """ Calculates maximum achievable uplink throughput in the current simulation state.

        Returns:
            Maximum throughput in mbps.

        """

        bandwidth = self.bts1.bandwidth

        if bandwidth == BtsBandwidth.LTE_BANDWIDTH_20MHz.value:
            return 51.02
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_15MHz.value:
            return 37.88
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_10MHz.value:
            return 25.45
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_5MHz.value:
            return 17.57
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_3MHz.value:
            return 7.99
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value:
            return 2.98
        else:
            raise ValueError("Invalid bandwidth value.")


    def set_transmission_mode(self, bts, tmode):
        """ Sets the transmission mode for the LTE basetation

        Args:
            bts: basestation handle
            tmode: Enum list from class 'TransmissionModeLTE'
        """

        # If the selected transmission mode does not support the number of DL
        # antennas, throw an exception.
        if (tmode in [self.TransmissionMode.TM1, self.TransmissionMode.TM7]
                and bts.dl_antenna != '1'):
            # TM1 and TM7 only support 1 DL antenna
            raise ValueError("{} allows only one DL antenna. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.".format(tmode.value))
        elif tmode == self.TransmissionMode.TM8 and bts.dl_antenna != '2':
            # TM8 requires 2 DL antennas
            raise ValueError("TM2 requires two DL antennas. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.")
        elif (tmode in [self.TransmissionMode.TM2, self.TransmissionMode.TM3,
                       self.TransmissionMode.TM4, self.TransmissionMode.TM9]
                and bts.dl_antenna == '1'):
            # TM2, TM3, TM4 and TM9 require 2 or 4 DL antennas
            raise ValueError("{} requires at least two DL atennas. Change the "
                             "number of DL antennas before setting the "
                             "transmission mode.".format(tmode.value))

        # The TM mode is allowed for the current number of DL antennas, so it
        # is safe to change this setting now
        bts.transmode = tmode.value

        time.sleep(5)  # It takes some time to propagate the new settings

    def set_mimo_mode(self, bts, mimo):
        """ Sets the number of DL antennas for the desired MIMO mode.

        Args:
            bts: basestation handle
            mimo: object of class MimoMode
        """

        # If the requested mimo mode is not compatible with the current TM,
        # warn the user before changing the value.

        if mimo == self.MimoMode.MIMO_1x1:
            if bts.transmode not in [self.TransmissionMode.TM1,
                                     self.TransmissionMode.TM7]:
                self.log.warning("Using only 1 DL antennas is not allowed with "
                                 "the current transmission mode. Changing the "
                                 "number of DL antennas will override this "
                                 "setting.")
            bts.dl_antenna = 1
        elif mimo == self.MimoMode.MIMO_2x2:
            if bts.transmode not in [self.TransmissionMode.TM2,
                                     self.TransmissionMode.TM3,
                                     self.TransmissionMode.TM4,
                                     self.TransmissionMode.TM8,
                                     self.TransmissionMode.TM9]:
                self.log.warning("Using two DL antennas is not allowed with "
                                 "the current transmission mode. Changing the "
                                 "number of DL antennas will override this "
                                 "setting.")
            bts.dl_antenna = 2
        elif mimo == self.MimoMode.MIMO_4x4:
            if bts.transmode not in [self.TransmissionMode.TM2,
                                     self.TransmissionMode.TM3,
                                     self.TransmissionMode.TM4,
                                     self.TransmissionMode.TM9]:
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
                            packet_rate=BtsPacketRate.LTE_MANUAL,
                            mcs_dl=27,
                            mcs_ul=23,
                            nrb_dl=0,
                            nrb_ul=0):
        """ Sets the scheduling mode for LTE

        Args:
            bts: basestation handle
            scheduling: DYNAMIC or STATIC scheduling (Enum list)
            mcs_dl: Downlink MCS (only for STATIC scheduling)
            mcs_ul: Uplink MCS (only for STATIC scheduling)
            nrb_dl: Number of RBs for downlink (only for STATIC scheduling)
            nrb_ul: Number of RBs for uplink (only for STATIC scheduling)
        """

        if scheduling == self.SchedulingMode.DYNAMIC:
            bts.lte_scheduling_mode = "DYNAMIC"
        else:
            bts.lte_scheduling_mode = "STATIC"
            bts.packet_rate = packet_rate
            cmd = "TBSPATTERN OFF, " + bts._bts_number
            self.anritsu.send_command(cmd)
            if packet_rate == BtsPacketRate.LTE_MANUAL:
                bts.lte_mcs_dl = mcs_dl
                bts.lte_mcs_ul = mcs_ul
                bts.nrb_dl = nrb_dl
                bts.nrb_ul = nrb_ul
        time.sleep(5)  # It takes some time to propagate the new settings

    def allocation_percentages_to_rbs(self, bts, dl, ul):
        """ Converts usage percentages to number of DL/UL RBs

        Because not any number of DL/UL RBs can be obtained for a certain
        bandwidth, this function calculates the number of RBs that most
        closely matches the desired DL/UL percentages.

        Args:
            dl: desired percentage of downlink RBs
            ul: desired percentage of uplink RBs
        Returns:
            a tuple indicating the number of downlink and uplink RBs
        """

        # Validate the arguments
        if (not 0 <= dl <= 100) or (not 0 <= ul <= 100):
            raise ValueError("The percentage of DL and UL RBs have to be two "
                             "positive between 0 and 100.")

        # Get the available number of RBs for the channel bandwidth
        bw = bts.bandwidth
        max_rbs = self.total_rbs_dictionary[bw]

        def percentage_to_amount(min_val, max_val, percentage):
            """ Returns the integer between min_val and max_val that is closest
            to percentage/100*max_val
            """

            # Calculate the value that corresponds to the required percentage.
            closest_int = round(max_val * percentage / 100)
            # Cannot be less than min_val
            closest_int = max(closest_int, min_val)
            # RBs cannot be more than max_rbs
            closest_int = min(closest_int, max_val)

            return closest_int


        # Calculate the number of DL RBs

        if dl == 100:
            # If 100% is requested, max_rbs can be used
            dl_rbs = max_rbs
        elif dl == 0:
            # Minimum DL RBs is 1
            dl_rbs = 1
        else:
            # Get the number of DL RBs that corresponds to
            #  the required percentage.
            desired_dl_rbs = percentage_to_amount(min_val=1,
                                                  max_val=max_rbs,
                                                  percentage=dl)

            # DL RBs have to be a multiple of the number of RBs in a RBG
            dl_rbs = desired_dl_rbs - desired_dl_rbs % self.rbg_dictionary[bw]

        # Calculate the number of UL RBs

        if ul == 100:
            # If 100% is requested, max_rbs can be used
            ul_rbs = max_rbs
        elif ul == 0:
            # Minimum UL RBs is 1
            ul_rbs = 1
        else:
            # Get the number of UL RBs that corresponds
            # to the required percentage
            desired_ul_rbs = percentage_to_amount(min_val=1,
                                                  max_val=max_rbs,
                                                  percentage=ul)

            # Create a list of all possible UL RBs assignment
            # The standard allows any number that can be written as
            # 2**a * 3**b * 5**c for any combination of a, b and c.

            def pow_range(max_value, base):
              """ Returns a range of all possible powers of base under
                  the given max_value.
              """
              return range(int(math.ceil(math.log(max_value, base))))

            possible_ul_rbs = [2**a * 3**b * 5**c
                                for a in pow_range(max_rbs, 2)
                                for b in pow_range(max_rbs, 3)
                                for c in pow_range(max_rbs, 5)
                                if 2**a * 3**b * 5**c <= max_rbs]

            # Find the value in the list that is closest to desired_ul_rbs
            differences = [abs(rbs - desired_ul_rbs) for rbs in possible_ul_rbs]
            ul_rbs = possible_ul_rbs[differences.index(min(differences))]

        # Report what are the obtained RB percentages
        self.log.info("Requested a {}% / {}% RB allocation. Closest possible "
                      "percentages are {}% / {}%.".format(
            dl, ul,
            round(100*dl_rbs/max_rbs),
            round(100*ul_rbs/max_rbs)
        ))

        return dl_rbs, ul_rbs


    def set_channel_bandwidth(self, bts, bandwidth):
        """ Sets the LTE channel bandwidth (MHz)

        Args:
            bts: basestation handle
            bandwidth: desired bandwidth (MHz)
        """
        if bandwidth == 20:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_20MHz
        elif bandwidth == 15:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_15MHz
        elif bandwidth == 10:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_10MHz
        elif bandwidth == 5:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_5MHz
        elif bandwidth == 3:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_3MHz
        elif bandwidth == 1.4:
            bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_1dot4MHz
        else:
            msg = "Bandwidth = {} MHz is not valid for LTE".format(bandwidth)
            self.log.Error(msg)
            raise ValueError(msg)
        time.sleep(5)  # It takes some time to propagate the new settings

    def calibrate(self):
        """ Calculates UL and DL path loss if it wasn't done before

        This method overrides the baseclass specifically for LTE calibration.
        For LTE cal, the simulation is set to TM1 and 1 antenna.

        """

        # Set in TM1 mode and 1 antenna for downlink calibration for LTE
        init_dl_antenna = None
        init_transmode = None
        if int(self.bts1.dl_antenna) != 1:
            init_dl_antenna = self.bts1.dl_antenna
            init_transmode = self.bts1.transmode
            self.bts1.dl_antenna = 1
            self.bts1.transmode = "TM1"
            time.sleep(5)  # It takes some time to propagate the new settings

        super().calibrate()

        if init_dl_antenna is not None:
            self.bts1.dl_antenna = init_dl_antenna
            self.bts1.transmode = init_transmode
            time.sleep(5)  # It takes some time to propagate the new settings
