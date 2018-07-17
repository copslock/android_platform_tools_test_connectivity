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
import statistics
import acts.test_utils.power.PowerBaseTest as PBT

from enum import Enum
from acts.controllers.anritsu_lib.md8475a import MD8475A
from acts.controllers.anritsu_lib.md8475a import BtsNumber
from acts.controllers.anritsu_lib.md8475a import BtsBandwidth
from acts.controllers.anritsu_lib.md8475a import BtsPacketRate
from acts.controllers.anritsu_lib._anritsu_utils import AnritsuError
from acts.test_utils.tel.tel_test_utils import get_telephony_signal_strength


class TransmissionModeLTE(Enum):
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


class PowerCellularLabBaseTest(PBT.PowerBaseTest):
    """Base class for Cellular power related tests.

    Inherited from the PowerBaseTest class
    """
    LTE_BASIC_SIM_FILE = ('C:\\Users\MD8475A\Documents\DAN_configs\ '
                          'Anritsu_SIM_Bo.wnssp')
    LTE_BASIC_CELL_FILE = ('C:\\Users\MD8475A\Documents\\DAN_configs\\ '
                           'Anritsu_SIM_cell_config_ul_max_mcs_10mhz_b7.wnscp')
    NUM_UPLINK_CAL_READS = 3
    NUM_DOWNLINK_CAL_READS = 5
    DOWNLINK_CAL_TARGET_POWER_DBM = -15
    MAX_BTS_INPUT_POWER_DBM = 30
    MAX_PHONE_OUTPUT_POWER_DBM = 23
    SCHEDULING_DYNAMIC = 0
    SCHEDULING_STATIC = 1

    def setup_class(self):

        super().setup_class()
        if hasattr(self, 'network_file'):
            self.networks = self.unpack_custom_file(self.network_file, False)
            self.main_network = self.networks['main_network']
            self.aux_network = self.networks['aux_network']
        if hasattr(self, 'packet_senders'):
            self.pkt_sender = self.packet_senders[0]
        # Establish connection to Anritsu Callbox
        return self.connect_to_anritsu()

    def connect_to_anritsu(self):
        """ Connects to Anritsu Callbox and gets handle object
    
        """
        try:
            self.anritsu = MD8475A(self.md8475a_ip_address, self.log,
                                   self.wlan_option)
            return True
        except AnritsuError:
            self.log.error('Error in connecting to Anritsu Callbox')
            return False

    def load_simple_LTE_config_files(self):
        """ Configures Anritsu system for LTE simulation with 1 basetation
    
        Loads a simple LTE simulation enviroment with 1 basestation. It also 
        creates the BTS handle so we can change the parameters as desired
        """
        self.anritsu.load_simulation_paramfile(self.LTE_BASIC_SIM_FILE)
        self.anritsu.load_cell_paramfile(self.LTE_BASIC_CELL_FILE)
        # Getting BTS1 since this sim only has 1 BTS
        self.bts1 = self.anritsu.get_BTS(BtsNumber.BTS1)

    def teardown_test(self):
        """Tear down necessary objects after test case is finished.

        """
        super().teardown_test()

    def teardown_class(self):
        """Clean up the test class after tests finish running

        """
        super().teardown_class()
        self.anritsu.stop_simulation()
        self.anritsu.disconnect()

    def uplink_calibration(self, bts):
        """ Computes uplink path loss and returns the calibration value
        
        The bts needs to be set at the desired config (bandwidth, mode, etc) 
        before running the calibration. The phone also neeeds to be attached
        to the desired basesation for calibration
        
        Args:
            bts: basestation handle
    
        Returns:
            Uplink calibration value and measured UL power
        """
        # Set BTS1 to maximum input allowed in order to do uplink calibration
        target_power = self.MAX_PHONE_OUTPUT_POWER_DBM
        initial_input_level = bts.input_level
        initial_screen_timeout = self.dut.droid.getScreenTimeout()
        bts.input_level = self.MAX_BTS_INPUT_POWER_DBM
        time.sleep(3)

        # Set BTS to maximum input allowed in order to do uplink calibration
        self.dut.droid.setScreenTimeout(1800)
        self.dut.droid.wakeUpNow()

        # Starting first the IP traffic (UDP): Using always APN 1
        try:
            cmd = 'OPERATEIPTRAFFIC START,1'
            self.anritsu.send_command(cmd)
        except AnritsuError as inst:
            self.log.warning("{}\n".format(inst))  # Typically RUNNING already
        time.sleep(4)

        up_power_per_chain = []
        # Get the number of chains
        cmd = 'MONITOR? UL_PUSCH'
        uplink_meas_power = self.anritsu.send_query(cmd)
        str_power_chain = uplink_meas_power.split(',')
        num_chains = len(str_power_chain)
        for ichain in range(0, num_chains):
            up_power_per_chain.append([])

        for i in range(0, self.NUM_UPLINK_CAL_READS):
            uplink_meas_power = self.anritsu.send_query(cmd)
            str_power_chain = uplink_meas_power.split(',')

            for ichain in range(0, num_chains):
                if (str_power_chain[ichain] == 'DEACTIVE'):
                    up_power_per_chain[ichain].append(float('nan'))
                else:
                    up_power_per_chain[ichain].append(
                        float(str_power_chain[ichain]))

            time.sleep(2)

        # Stop the IP traffic (UDP)
        try:
            cmd = 'OPERATEIPTRAFFIC STOP,1'
            self.anritsu.send_command(cmd)
        except AnritsuError as inst:
            self.log.warning("{}\n".format(inst))  # Typically STOPPED already
        time.sleep(1.5)

        # Reset phone and bts to original settings
        self.dut.droid.goToSleepNow()
        self.dut.droid.setScreenTimeout(initial_screen_timeout)
        bts.input_level = initial_input_level

        # Phone only supports 1x1 Uplink so always chain 0
        avg_up_power = statistics.mean(up_power_per_chain[0])
        up_call_path_loss = target_power - avg_up_power

        self.up_call_path_loss = up_call_path_loss
        self.up_call_power_per_chain = up_power_per_chain

        return up_power_per_chain[0], up_call_path_loss

    def downlink_calibration(self, bts, rat='lteRsrp', num_RBs=0):
        """ Computes downlink path loss and returns the calibration value
        
        The bts needs to be set at the desired config (bandwidth, mode, etc) 
        before running the calibration. The phone also neeeds to be attached
        to the desired basesation for calibration
    
        Args:
            bts: basestation handle
            rat: desired RAT to calibrate (currently only works for LTE)
            num_RBs: Number of RBs in use. If set to 0, it will return RSRP
    
        Returns:
            Dowlink calibration value and measured DL power. Note that the 
            phone only reports RSRP of the primary chain
        """
        # Set BTS1 to maximum output level to minimize error
        init_output_level = bts.output_level
        initial_screen_timeout = self.dut.droid.getScreenTimeout()
        bts.output_level = self.DOWNLINK_CAL_TARGET_POWER_DBM
        time.sleep(3)

        # Set BTS to maximum input allowed in order to do uplink calibration
        self.dut.droid.setScreenTimeout(1800)
        self.dut.droid.goToSleepNow()

        # Starting first the IP traffic (UDP): Using always APN 1
        try:
            cmd = 'OPERATEIPTRAFFIC START,1'
            self.anritsu.send_command(cmd)
        except AnritsuError as inst:
            self.log.warning("{}\n".format(inst))  # Typically RUNNING already
        time.sleep(4)

        down_power_measured = []
        for i in range(0, self.MAX_DOWNLINK_CAL_READS):
            # For some reason, the RSRP gets updated on Screen ON event
            self.dut.droid.wakeUpNow()
            time.sleep(4)
            signal_strength = get_telephony_signal_strength(self.dut)
            down_power_measured.append(signal_strength[rat])
            self.dut.droid.goToSleepNow()
            time.sleep(4)

        # Stop the IP traffic (UDP)
        try:
            cmd = 'OPERATEIPTRAFFIC STOP,1'
            self.anritsu.send_command(cmd)
        except AnritsuError as inst:
            self.log.warning("{}\n".format(inst))  # Typically STOPPED already
        time.sleep(1.5)

        # Reset phone and bts to original settings
        self.dut.droid.goToSleepNow()
        self.dut.droid.setScreenTimeout(initial_screen_timeout)
        bts.output_level = init_output_level

        self.down_power_measured_primary = []
        self.down_call_path_loss_primary = []
        self.down_rsrp_measured_primary = statistics.mean(down_power_measured)
        # Returns either the RSRP or total power
        if (num_RBs == 0):
            avg_down_power = self.down_rsrp_measured_primary
            down_call_path_loss = float('nan')
        else:
            avg_down_power = self.down_rsrp_measured_primary + 10 * math.log10(
                12 * num_RBs)
            down_call_path_loss = self.DOWNLINK_CAL_TARGET_POWER_DBM - avg_down_power
            self.down_power_measured_primary = avg_down_power
            self.down_call_path_loss_primary = down_call_path_loss

        return down_power_measured, down_call_path_loss

    def set_lte_channel_bandwidth(self, bts, bandwidth):
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

    def set_lte_scheduling(self,
                           bts,
                           scheduling,
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

        if scheduling == SchedulingMode.DYNAMIC:
            bts.lte_scheduling_mode = "DYNAMIC"
        else:
            bts.lte_scheduling_mode = "STATIC"
            bts.packet_rate = BtsPacketRate.LTE_MANUAL
            cmd = "TBSPATTERN OFF, " + bts._bts_number
            self.anritsu.send_command(cmd)
            bts.lte_mcs_dl = mcs_dl
            bts.lte_mcs_ul = mcs_ul
            bts.nrb_dl = nrb_dl
            bts.nrb_ul = nrb_ul

    def set_lte_bts_mode(self, bts, tmode):
        """ Sets the transmission mode for the LTE basestation
    
        Args:
            bts: basestation handle
            tmode: Enum list from class 'TransmissionModeLTE'
        """

        if tmode == TransmissionModeLTE.TM1:
            bts.dl_antenna = 1
            bts.transmode = TransmissionModeLTE.TM4
        elif tmode == TransmissionModeLTE.TM4:
            bts.dl_antenna = 2
            bts.transmode = TransmissionModeLTE.TM1
        else:
            msg = "TM = {} is not valid for LTE".format(tmode)
            self.log.Error(msg)
            raise ValueError(msg)
