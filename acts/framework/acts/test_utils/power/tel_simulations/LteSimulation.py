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

from enum import Enum

from acts.controllers.anritsu_lib.md8475a import BtsBandwidth
from acts.controllers.anritsu_lib.md8475a import BtsPacketRate
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_ONLY
from acts.test_utils.tel.tel_test_utils import set_preferred_apn_by_adb
from test_utils.power.tel_simulations.BaseSimulation import BaseSimulation


class LteSimulation(BaseSimulation):
    """ Simple LTE simulation with only one basestation.

    """

    # Simulation config files in the callbox computer.
    # These should be replaced in the future by setting up
    # the same configuration manually.

    LTE_BASIC_SIM_FILE = ('C:\\Users\MD8475A\Documents\DAN_configs\\'
                          'SIM_default_LTE.wnssp')
    LTE_BASIC_CELL_FILE = ('C:\\Users\MD8475A\Documents\\DAN_configs\\'
                           'CELL_LTE_config.wnscp')

    # Simulation config keywords contained in the test name

    PARAM_BW = "bw"
    PARAM_SCHEDULING = "scheduling"
    PARAM_TM = "tm"
    PARAM_UL_PW = 'pul'
    PARAM_DL_PW = 'pdl'
    PARAM_BAND = "band"

    class TransmissionMode(Enum):
        ''' Transmission modes for LTE (e.g., TM1, TM4, ..)

        '''
        TM1 = "TM1"
        TM2 = "TM2"
        TM3 = "TM3"
        TM4 = "TM4"

    class SchedulingMode(Enum):
        ''' Traffic scheduling modes (e.g., STATIC, DYNAMIC)

        '''
        DYNAMIC = 0
        STATIC = 1

    # RSRP signal levels thresholds (as reported by Android). Units are dBm/15KHz

    downlink_rsrp_dictionary = {
        'excellent': -60,
        'high': -110,
        'medium': -115,
        'weak': -120
    }

    # Transmitted output power for the phone
    # Units are dBm

    uplink_signal_level_dictionary = {
        'max': 23,
        'high': 13,
        'medium': 3,
        'low': -20
    }

    def __init__(self, anritsu, log, dut):
        """ Configures Anritsu system for LTE simulation with 1 basetation

        Loads a simple LTE simulation enviroment with 1 basestation.

        Args:
            anritsu: the Anritsu callbox controller
            log: a logger handle
            dut: the android device handler

        """

        super().__init__(anritsu, log, dut)

        anritsu.load_simulation_paramfile(self.LTE_BASIC_SIM_FILE)
        anritsu.load_cell_paramfile(self.LTE_BASIC_CELL_FILE)

        if not dut.droid.telephonySetPreferredNetworkTypesForSubscription(NETWORK_MODE_LTE_ONLY,
            dut.droid.subscriptionGetDefaultSubId()):
            log.error("Coold not set preferred network type.")
        else:
            log.info("Preferred network type set.")

        set_preferred_apn_by_adb(self.dut, "anritsu1.com")
        log.info("Prefered apn set to anritsu1.com")

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
          self.set_band(self.bts1, band, calibrate_if_necessary=True)

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

            if values[1] == "dynamic":
                scheduling = LteSimulation.SchedulingMode.DYNAMIC
            elif values[1] == "static":
                scheduling = LteSimulation.SchedulingMode.STATIC

        except:
            self.log.error(
                "The test name needs to include parameter {} followed by either "
                                   "dynamic or static.".format(self.PARAM_SCHEDULING))
            return False
        else:
            self.set_scheduling_mode(self.bts1, scheduling)

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
        """ Converts rsrp to signal power

        RSRP is measured per subcarrier, so linear power needs to be multiplied
        by the number of subcarriers in the channel.

        Args:
            rsrp: desired rsrp in dBm
            bts: basestation handler for which the unit conversion is done

        Returns:
            Transmitted signal power in dBm
        """

        bandwidth = bts.bandwidth

        if bandwidth == BtsBandwidth.LTE_BANDWIDTH_20MHz.value:
            # 100 RBs
            power = rsrp + 18.57
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_15MHz.value:
            # 75 RBs
            power = rsrp + 22.55
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_10MHz.value:
            # 50 RBs
            power = rsrp + 24.77
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_5MHz.value:
            # 25 RBs
            power = rsrp + 27.78
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_3MHz.value:
            # 15 RBs
            power = rsrp + 29.54
        elif bandwidth == BtsBandwidth.LTE_BANDWIDTH_1dot4MHz.value:
            # 6 RBs
            power = rsrp + 30.79
        else:
            raise ValueError("Invalidad bandwith value.")

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

        if tmode == self.TransmissionMode.TM1:
            bts.dl_antenna = 1
            bts.transmode = "TM1"
        elif tmode == self.TransmissionMode.TM4:
            bts.dl_antenna = 2
            bts.transmode = "TM4"
        else:
            msg = "TM = {} is not valid for LTE".format(tmode)
            self.log.error(msg)
            raise ValueError(msg)

    def set_scheduling_mode(self,
                            bts,
                            scheduling,
                            packet_rate=BtsPacketRate.LTE_BESTEFFORT,
                            mcs_dl=0,
                            mcs_ul=0,
                            nrb_dl=5,
                            nrb_ul=5):
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

