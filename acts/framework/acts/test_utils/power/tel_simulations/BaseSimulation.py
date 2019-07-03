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
from enum import Enum

import numpy as np

from acts.controllers.anritsu_lib._anritsu_utils import AnritsuError
from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.test_utils.tel.tel_test_utils import get_telephony_signal_strength
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode
from acts.test_utils.tel.tel_test_utils import toggle_cell_data_roaming


class BaseSimulation():
    """ Base class for an Anritsu Simulation abstraction.

    Classes that inherit from this base class implement different simulation
    setups. The base class contains methods that are common to all simulation
    configurations.

    """

    NUM_UL_CAL_READS = 3
    NUM_DL_CAL_READS = 5
    DL_CAL_TARGET_POWER = {'A': -15.0, 'B': -35.0}
    MAX_BTS_INPUT_POWER = 30
    MAX_PHONE_OUTPUT_POWER = 23
    DL_MAX_POWER = {'A': -10.0, 'B': -30.0}
    UL_MIN_POWER = -60.0

    # Key to read the calibration setting from the test_config dictionary.
    KEY_CALIBRATION = "calibration"

    # Filepath to the config files stored in the Anritsu callbox. Needs to be
    # formatted to replace {} with either A or B depending on the model.
    CALLBOX_PATH_FORMAT_STR = 'C:\\Users\\MD8475{}\\Documents\\DAN_configs\\'

    # Time in seconds to wait for the phone to settle
    # after attaching to the base station.
    SETTLING_TIME = 10

    # Time in seconds to wait for the phone to attach
    # to the basestation after toggling airplane mode.
    ATTACH_WAITING_TIME = 120

    # Max retries before giving up attaching the phone
    ATTACH_MAX_RETRIES = 3

    # These two dictionaries allow to map from a string to a signal level and
    # have to be overriden by the simulations inheriting from this class.
    UPLINK_SIGNAL_LEVEL_DICTIONARY = {}
    DOWNLINK_SIGNAL_LEVEL_DICTIONARY = {}

    # Units for downlink signal level. This variable has to be overriden by
    # the simulations inheriting from this class.
    DOWNLINK_SIGNAL_LEVEL_UNITS = None

    class BtsConfig:
        """ Base station configuration class. This class is only a container for
        base station parameters and should not interact with the instrument
        controller.

        Atributes:
            output_power: a float indicating the required signal level at the
                instrument's output.
            input_level: a float indicating the required signal level at the
                instrument's input.
        """
        def __init__(self):
            """ Initialize the base station config by setting all its
            parameters to None. """
            self.output_power = None
            self.input_power = None

        def incorporate(self, new_config):
            """ Incorporates a different configuration by replacing the current
            values with the new ones for all the parameters different to None.
            """
            for attr, value in vars(new_config).items():
                if value:
                    setattr(self, attr, value)

    def __init__(self, simulator, log, dut, test_config, calibration_table):
        """ Initializes the Simulation object.

        Keeps a reference to the callbox, log and dut handlers and
        initializes the class attributes.

        Args:
            simulator: a cellular simulator controller
            log: a logger handle
            dut: the android device handler
            test_config: test configuration obtained from the config file
            calibration_table: a dictionary containing path losses for
                different bands.
        """

        self.simulator = simulator
        self.anritsu = simulator.anritsu
        self.log = log
        self.dut = dut
        self.calibration_table = calibration_table

        # Turn calibration on or off depending on the test config value. If the
        # key is not present, set to False by default
        if self.KEY_CALIBRATION not in test_config:
            self.log.warning("The '{} 'key is not set in the testbed "
                             "parameters. Setting to off by default. To "
                             "turn calibration on, include the key with "
                             "a true/false value.".format(
                                 self.KEY_CALIBRATION))

        self.calibration_required = test_config.get(self.KEY_CALIBRATION,
                                                    False)

        # Gets BTS1 since this sim only has 1 BTS
        self.bts1 = self.anritsu.get_BTS(BtsNumber.BTS1)

        # Configuration object for the primary base station
        self.primary_config = self.BtsConfig()

        # Store the current calibrated band
        self.current_calibrated_band = None

        # Path loss measured during calibration
        self.dl_path_loss = None
        self.ul_path_loss = None

        # Target signal levels obtained during configuration
        self.sim_dl_power = None
        self.sim_ul_power = None

        # Stores RRC status change timer
        self.rrc_sc_timer = None

        # Set to default APN
        log.info("Setting preferred APN to anritsu1.com.")
        dut.droid.telephonySetAPN("anritsu1.com", "anritsu1.com")

        # Enable roaming on the phone
        toggle_cell_data_roaming(self.dut, True)

        # Load callbox config files
        self.callbox_config_path = self.CALLBOX_PATH_FORMAT_STR.format(
            self.anritsu._md8475_version)
        self.load_config_files()

        # Make sure airplane mode is on so the phone won't attach right away
        toggle_airplane_mode(self.log, self.dut, True)

        # Wait for airplane mode setting to propagate
        time.sleep(2)

        # Start simulation if it wasn't started
        self.anritsu.start_simulation()

    def load_config_files(self):
        """ Loads configuration files for the simulation.

        This method needs to be implement by derived simulation classes. """

        raise NotImplementedError()

    def attach(self):
        """ Attach the phone to the basestation.

        Sets a good signal level, toggles airplane mode
        and waits for the phone to attach.

        Returns:
            True if the phone was able to attach, False if not.
        """

        # Turn on airplane mode
        toggle_airplane_mode(self.log, self.dut, True)

        # Wait for airplane mode setting to propagate
        time.sleep(2)

        # Provide a good signal power for the phone to attach easily
        new_config = self.BtsConfig()
        new_config.input_power = -10
        new_config.output_power = -30
        self.configure_bts(self.bts1, new_config)
        self.primary_config.incorporate(new_config)

        # Try to attach the phone.
        for i in range(self.ATTACH_MAX_RETRIES):

            try:

                # Turn off airplane mode
                toggle_airplane_mode(self.log, self.dut, False)

                # Wait for the phone to attach.
                self.anritsu.wait_for_registration_state(
                    time_to_wait=self.ATTACH_WAITING_TIME)

            except AnritsuError as e:

                # The phone failed to attach
                self.log.info(
                    "UE failed to attach on attempt number {}.".format(i + 1))
                self.log.info("Error message: {}".format(str(e)))

                # Turn airplane mode on to prepare the phone for a retry.
                toggle_airplane_mode(self.log, self.dut, True)

                # Wait for APM to propagate
                time.sleep(3)

                # Retry
                if i < self.ATTACH_MAX_RETRIES - 1:
                    # Retry
                    continue
                else:
                    # No more retries left. Return False.
                    return False

            else:
                # The phone attached successfully.
                time.sleep(self.SETTLING_TIME)
                self.log.info("UE attached to the callbox.")
                break

        return True

    def detach(self):
        """ Detach the phone from the basestation.

        Turns airplane mode and resets basestation.
        """

        # Set the DUT to airplane mode so it doesn't see the
        # cellular network going off
        toggle_airplane_mode(self.log, self.dut, True)

        # Wait for APM to propagate
        time.sleep(2)

        # Try to power off the basestation. An exception will be raised if the
        # simulation is not running, which is ok because it means the phone is
        # not attached.
        try:
            self.anritsu.set_simulation_state_to_poweroff()
        except AnritsuError:
            self.log.warning('Could not power off the basestation. The '
                             'simulation might be stopped.')

    def stop(self):
        """  Detach phone from the basestation by stopping the simulation.

        Send stop command to anritsu and turn on airplane mode.

        """

        # Set the DUT to airplane mode so it doesn't see the
        # cellular network going off
        toggle_airplane_mode(self.log, self.dut, True)

        # Wait for APM to propagate
        time.sleep(2)

        # Stop the simulation
        self.anritsu.stop_simulation()

    def start(self):
        """ Start the simulation by attaching the phone and setting the
        required DL and UL power.

        Note that this refers to starting the simulated testing environment
        and not to starting the simulation in the Anritsu callbox, which was
        done during the class initialization. """

        if not self.attach():
            raise RuntimeError('Could not attach to base station.')

        # Set signal levels obtained from the test parameters
        new_config = self.BtsConfig()
        new_config.output_power = self.calibrated_downlink_rx_power(
            self.primary_config, self.sim_dl_power)
        new_config.input_power = self.calibrated_uplink_tx_power(
            self.primary_config, self.sim_ul_power)
        self.configure_bts(self.bts1, new_config)
        self.primary_config.incorporate(new_config)

    def parse_parameters(self, parameters):
        """ Configures simulation using a list of parameters.

        Consumes parameters from a list.
        Children classes need to call this method first.

        Args:
            parameters: list of parameters
        """

        raise NotImplementedError()

    def configure_bts(self, bts_handle, config):
        """ Configures the base station in the Anritsu callbox.

        Parameters set to None in the configuration object are skipped.

        Args:
            bts_handle: a handle to the Anritsu base station controller.
            config: a BtsConfig object containing the desired configuration.
        """

        if config.output_power:
            bts_handle.output_level = config.output_power

        if config.input_power:
            bts_handle.input_level = config.input_power

    def consume_parameter(self, parameters, parameter_name, num_values=0):
        """ Parses a parameter from a list.

        Allows to parse the parameter list. Will delete parameters from the
        list after consuming them to ensure that they are not used twice.

        Args:
            parameters: list of parameters
            parameter_name: keyword to look up in the list
            num_values: number of arguments following the
                parameter name in the list
        Returns:
            A list containing the parameter name and the following num_values
            arguments
        """

        try:
            i = parameters.index(parameter_name)
        except ValueError:
            # parameter_name is not set
            return []

        return_list = []

        try:
            for j in range(num_values + 1):
                return_list.append(parameters.pop(i))
        except IndexError:
            raise ValueError(
                "Parameter {} has to be followed by {} values.".format(
                    parameter_name, num_values))

        return return_list

    def get_uplink_power_from_parameters(self, parameters):
        """ Reads uplink power from a list of parameters. """

        values = self.consume_parameter(parameters, self.PARAM_UL_PW, 1)

        if not values or values[1] not in self.UPLINK_SIGNAL_LEVEL_DICTIONARY:
            raise ValueError(
                "The test name needs to include parameter {} followed by one "
                "the following values: {}.".format(
                    self.PARAM_UL_PW,
                    list(self.UPLINK_SIGNAL_LEVEL_DICTIONARY.keys())))

        return self.UPLINK_SIGNAL_LEVEL_DICTIONARY[values[1]]

    def get_downlink_power_from_parameters(self, parameters):
        """ Reads downlink power from a list of parameters. """

        values = self.consume_parameter(parameters, self.PARAM_DL_PW, 1)

        if values:
            if values[1] not in self.DOWNLINK_SIGNAL_LEVEL_DICTIONARY:
                raise ValueError("Invalid signal level value {}.".format(
                    values[1]))
            else:
                return self.DOWNLINK_SIGNAL_LEVEL_DICTIONARY[values[1]]
        else:
            # Use default value
            power = self.DOWNLINK_SIGNAL_LEVEL_DICTIONARY['excellent']
            self.log.info("No DL signal level value was indicated in the test "
                          "parameters. Using default value of {} {}.".format(
                              power, self.DOWNLINK_SIGNAL_LEVEL_UNITS))
            return power

    def calibrated_downlink_rx_power(self, bts_config, signal_level):
        """ Calculates the power level at the instrument's output in order to
        obtain the required rx power level at the DUT's input.

        If calibration values are not available, returns the uncalibrated signal
        level.

        Args:
            bts_config: the current configuration at the base station. derived
                classes implementations can use this object to indicate power as
                spectral power density or in other units.
            signal_level: desired downlink received power, can be either a
                key value pair, an int or a float
        """

        # Obtain power value if the provided signal_level is a key value pair
        if isinstance(signal_level, Enum):
            power = signal_level.value
        else:
            power = signal_level

        # Try to use measured path loss value. If this was not set, it will
        # throw an TypeError exception
        try:
            calibrated_power = round(power + self.dl_path_loss)
            if (calibrated_power >
                    self.DL_MAX_POWER[self.anritsu._md8475_version]):
                self.log.warning(
                    "Cannot achieve phone DL Rx power of {} dBm. Requested TX "
                    "power of {} dBm exceeds callbox limit!".format(
                        power, calibrated_power))
                calibrated_power = self.DL_MAX_POWER[
                    self.anritsu._md8475_version]
                self.log.warning(
                    "Setting callbox Tx power to max possible ({} dBm)".format(
                        calibrated_power))

            self.log.info(
                "Requested phone DL Rx power of {} dBm, setting callbox Tx "
                "power at {} dBm".format(power, calibrated_power))
            time.sleep(2)
            # Power has to be a natural number so calibration wont be exact.
            # Inform the actual received power after rounding.
            self.log.info(
                "Phone downlink received power is {0:.2f} dBm".format(
                    calibrated_power - self.dl_path_loss))
            return calibrated_power
        except TypeError:
            self.log.info("Phone downlink received power set to {} (link is "
                          "uncalibrated).".format(round(power)))
            return round(power)

    def calibrated_uplink_tx_power(self, bts_config, signal_level):
        """ Calculates the power level at the instrument's input in order to
        obtain the required tx power level at the DUT's output.

        If calibration values are not available, returns the uncalibrated signal
        level.

        Args:
            bts_config: the current configuration at the base station. derived
                classes implementations can use this object to indicate power as
                spectral power density or in other units.
            signal_level: desired uplink transmitted power, can be either a
                key value pair, an int or a float
        """

        # Obtain power value if the provided signal_level is a key value pair
        if isinstance(signal_level, Enum):
            power = signal_level.value
        else:
            power = signal_level

        # Starts IP traffic while changing this setting to force the UE to be
        # in Communication state, as UL power cannot be set in Idle state
        self.start_traffic_for_calibration()

        # Wait until it goes to communication state
        self.anritsu.wait_for_communication_state()

        # Try to use measured path loss value. If this was not set, it will
        # throw an TypeError exception
        try:
            calibrated_power = round(power - self.ul_path_loss)
            if calibrated_power < self.UL_MIN_POWER:
                self.log.warning(
                    "Cannot achieve phone UL Tx power of {} dBm. Requested UL "
                    "power of {} dBm exceeds callbox limit!".format(
                        power, calibrated_power))
                calibrated_power = self.UL_MIN_POWER
                self.log.warning(
                    "Setting UL Tx power to min possible ({} dBm)".format(
                        calibrated_power))

            self.log.info(
                "Requested phone UL Tx power of {} dBm, setting callbox Rx "
                "power at {} dBm".format(power, calibrated_power))
            time.sleep(2)
            # Power has to be a natural number so calibration wont be exact.
            # Inform the actual transmitted power after rounding.
            self.log.info(
                "Phone uplink transmitted power is {0:.2f} dBm".format(
                    calibrated_power + self.ul_path_loss))
            return calibrated_power
        except TypeError:
            self.log.info("Phone uplink transmitted power set to {} (link is "
                          "uncalibrated).".format(round(power)))
            return round(power)

        # Stop IP traffic after setting the UL power level
        self.stop_traffic_for_calibration()

    def calibrate(self, band):
        """ Calculates UL and DL path loss if it wasn't done before.

        The should be already set to the required band before calling this
        method.

        Args:
            band: the band that is currently being calibrated.
        """

        if self.dl_path_loss and self.ul_path_loss:
            self.log.info("Measurements are already calibrated.")

        # Attach the phone to the base station
        if not self.attach():
            self.log.info(
                "Skipping calibration because the phone failed to attach.")
            return

        # If downlink or uplink were not yet calibrated, do it now
        if not self.dl_path_loss:
            self.dl_path_loss = self.downlink_calibration()
        if not self.ul_path_loss:
            self.ul_path_loss = self.uplink_calibration()

        # Detach after calibrating
        self.detach()
        time.sleep(2)

    def start_traffic_for_calibration(self):
        """
            Starts UDP IP traffic before running calibration. Uses APN_1
            configured in the phone.
        """
        try:
            self.anritsu.start_ip_traffic()
        except AnritsuError as inst:
            # This typically happens when traffic is already running
            self.log.warning("{}\n".format(inst))
        time.sleep(4)

    def stop_traffic_for_calibration(self):
        """
            Stops IP traffic after calibration.
        """
        try:
            self.anritsu.stop_ip_traffic()
        except AnritsuError as inst:
            # This typically happens when traffic has already been stopped
            self.log.warning("{}\n".format(inst))
        time.sleep(2)

    def downlink_calibration(self,
                             rat=None,
                             power_units_conversion_func=None):
        """ Computes downlink path loss and returns the calibration value

        The DUT needs to be attached to the base station before calling this
        method.

        Args:
            rat: desired RAT to calibrate (matching the label reported by
                the phone)
            power_units_conversion_func: a function to convert the units
                reported by the phone to dBm. needs to take two arguments: the
                reported signal level and bts. use None if no conversion is
                needed.
        Returns:
            Dowlink calibration value and measured DL power.
        """

        # Check if this parameter was set. Child classes may need to override
        # this class passing the necessary parameters.
        if not rat:
            raise ValueError(
                "The parameter 'rat' has to indicate the RAT being used as "
                "reported by the phone.")

        # Save initial output level to restore it after calibration
        restoration_config = self.BtsConfig()
        restoration_config.output_power = self.primary_config.output_power

        # Set BTS to a good output level to minimize measurement error
        initial_screen_timeout = self.dut.droid.getScreenTimeout()
        new_config = self.BtsConfig()
        new_config.output_power = self.DL_CAL_TARGET_POWER[
            self.anritsu._md8475_version]
        self.configure_bts(self.bts1, new_config)

        # Set phone sleep time out
        self.dut.droid.setScreenTimeout(1800)
        self.dut.droid.goToSleepNow()
        time.sleep(2)

        # Starting IP traffic
        self.start_traffic_for_calibration()

        down_power_measured = []
        for i in range(0, self.NUM_DL_CAL_READS):
            # For some reason, the RSRP gets updated on Screen ON event
            self.dut.droid.wakeUpNow()
            time.sleep(4)
            signal_strength = get_telephony_signal_strength(self.dut)
            down_power_measured.append(signal_strength[rat])
            self.dut.droid.goToSleepNow()
            time.sleep(5)

        # Stop IP traffic
        self.stop_traffic_for_calibration()

        # Reset phone and bts to original settings
        self.dut.droid.goToSleepNow()
        self.dut.droid.setScreenTimeout(initial_screen_timeout)
        self.configure_bts(self.bts1, restoration_config)
        time.sleep(2)

        # Calculate the mean of the measurements
        reported_asu_power = np.nanmean(down_power_measured)

        # Convert from RSRP to signal power
        if power_units_conversion_func:
            avg_down_power = power_units_conversion_func(
                reported_asu_power, self.primary_config)
        else:
            avg_down_power = reported_asu_power

        # Calculate Path Loss
        dl_target_power = self.DL_CAL_TARGET_POWER[
            self.anritsu._md8475_version]
        down_call_path_loss = dl_target_power - avg_down_power

        # Validate the result
        if not 0 < down_call_path_loss < 100:
            raise RuntimeError(
                "Downlink calibration failed. The calculated path loss value "
                "was {} dBm.".format(down_call_path_loss))

        self.log.info(
            "Measured downlink path loss: {} dB".format(down_call_path_loss))

        return down_call_path_loss

    def uplink_calibration(self):
        """ Computes uplink path loss and returns the calibration value

        The DUT needs to be attached to the base station before calling this
        method.

        Returns:
            Uplink calibration value and measured UL power
        """

        # Save initial input level to restore it after calibration
        restoration_config = self.BtsConfig()
        restoration_config.input_power = self.primary_config.input_power

        # Set BTS1 to maximum input allowed in order to perform
        # uplink calibration
        target_power = self.MAX_PHONE_OUTPUT_POWER
        initial_screen_timeout = self.dut.droid.getScreenTimeout()
        new_config = self.BtsConfig()
        new_config.input_power = self.MAX_BTS_INPUT_POWER
        self.configure_bts(self.bts1, new_config)

        # Set phone sleep time out
        self.dut.droid.setScreenTimeout(1800)
        self.dut.droid.wakeUpNow()
        time.sleep(2)

        # Start IP traffic
        self.start_traffic_for_calibration()

        up_power_per_chain = []
        # Get the number of chains
        cmd = 'MONITOR? UL_PUSCH'
        uplink_meas_power = self.anritsu.send_query(cmd)
        str_power_chain = uplink_meas_power.split(',')
        num_chains = len(str_power_chain)
        for ichain in range(0, num_chains):
            up_power_per_chain.append([])

        for i in range(0, self.NUM_UL_CAL_READS):
            uplink_meas_power = self.anritsu.send_query(cmd)
            str_power_chain = uplink_meas_power.split(',')

            for ichain in range(0, num_chains):
                if (str_power_chain[ichain] == 'DEACTIVE'):
                    up_power_per_chain[ichain].append(float('nan'))
                else:
                    up_power_per_chain[ichain].append(
                        float(str_power_chain[ichain]))

            time.sleep(3)

        # Stop IP traffic
        self.stop_traffic_for_calibration()

        # Reset phone and bts to original settings
        self.dut.droid.goToSleepNow()
        self.dut.droid.setScreenTimeout(initial_screen_timeout)
        self.configure_bts(self.bts1, restoration_config)
        time.sleep(2)

        # Phone only supports 1x1 Uplink so always chain 0
        avg_up_power = np.nanmean(up_power_per_chain[0])
        if np.isnan(avg_up_power):
            raise RuntimeError(
                "Calibration failed because the callbox reported the chain to "
                "be deactive.")

        up_call_path_loss = target_power - avg_up_power

        # Validate the result
        if not 0 < up_call_path_loss < 100:
            raise RuntimeError(
                "Uplink calibration failed. The calculated path loss value "
                "was {} dBm.".format(up_call_path_loss))

        self.log.info(
            "Measured uplink path loss: {} dB".format(up_call_path_loss))

        return up_call_path_loss

    def set_band(self, bts, band, calibrate_if_necessary=True):
        """ Sets the band used for communication.

        When moving to a new band, recalibrate the link.

        Args:
            bts: basestation handle
            band: desired band
            calibrate_if_necessary: if False calibration will be skipped
        """

        bts.band = band
        time.sleep(5)  # It takes some time to propagate the new band

        # Invalidate the calibration values
        self.dl_path_loss = None
        self.ul_path_loss = None

        # Only calibrate when required.
        if self.calibration_required and calibrate_if_necessary:
            # Try loading the path loss values from the calibration table. If
            # they are not available, use the automated calibration procedure.
            try:
                self.dl_path_loss = self.calibration_table[band]["dl"]
                self.ul_path_loss = self.calibration_table[band]["ul"]
            except KeyError:
                self.calibrate(band)

            # Complete the calibration table with the new values to be used in
            # the next tests.
            if band not in self.calibration_table:
                self.calibration_table[band] = {}

            if "dl" not in self.calibration_table[band] and self.dl_path_loss:
                self.calibration_table[band]["dl"] = self.dl_path_loss

            if "ul" not in self.calibration_table[band] and self.ul_path_loss:
                self.calibration_table[band]["ul"] = self.ul_path_loss

    def maximum_downlink_throughput(self):
        """ Calculates maximum achievable downlink throughput in the current
        simulation state.

        Because thoughput is dependent on the RAT, this method needs to be
        implemented by children classes.

        Returns:
            Maximum throughput in mbps
        """
        raise NotImplementedError()

    def maximum_uplink_throughput(self):
        """ Calculates maximum achievable downlink throughput in the current
        simulation state.

        Because thoughput is dependent on the RAT, this method needs to be
        implemented by children classes.

        Returns:
            Maximum throughput in mbps
        """
        raise NotImplementedError()

    def start_test_case(self):
        """ Starts a test case in the current simulation.

        Requires the phone to be attached.
        """

        pass

    def wait_for_rrc_idle_state(self, wait_time):
        """ Waits for UE RRC state change to idle mode.

        Raises exception when UE fails to move to idle state
        """

        self.anritsu.wait_for_idle_state(wait_time)
