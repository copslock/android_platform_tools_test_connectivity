#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
    Test Script for Telephony Pre Check In Sanity
"""

import time
from acts.controllers.tel._anritsu_utils import AnritsuError
from acts.controllers.tel.md8475a import CTCHSetup
from acts.controllers.tel.md8475a import BtsBandwidth
from acts.controllers.tel.md8475a import BtsPacketRate
from acts.controllers.tel.md8475a import BtsServiceState
from acts.controllers.tel.md8475a import MD8475A
from acts.controllers.tel.mg3710a import MG3710A
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import NETWORK_MODE_CDMA
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GSM_ONLY
from acts.test_utils.tel.tel_defines import NETWORK_MODE_GSM_UMTS
from acts.test_utils.tel.tel_defines import NETWORK_MODE_LTE_GSM_WCDMA
from acts.test_utils.tel.tel_defines import RAT_FAMILY_CDMA2000
from acts.test_utils.tel.tel_defines import RAT_FAMILY_GSM
from acts.test_utils.tel.tel_defines import RAT_FAMILY_LTE
from acts.test_utils.tel.tel_defines import RAT_FAMILY_UMTS
from acts.test_utils.tel.tel_test_anritsu_utils import LTE_BAND_2
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_gsm
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_lte
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_lte_lte
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_lte_wcdma
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_wcdma
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_wcdma_gsm
from acts.test_utils.tel.tel_test_anritsu_utils import set_system_model_wcdma_wcdma
from acts.test_utils.tel.tel_test_utils import ensure_network_rat
from acts.test_utils.tel.tel_test_utils import ensure_phones_idle
from cell_configurations import gsm_band850_ch128_fr869_cid58_cell
from cell_configurations import gsm_band850_ch251_fr893_cid59_cell
from cell_configurations import gsm_band1900_ch512_fr1930_cid51_cell
from cell_configurations import gsm_band1900_ch512_fr1930_cid52_cell
from cell_configurations import gsm_band1900_ch512_fr1930_cid53_cell
from cell_configurations import gsm_band1900_ch512_fr1930_cid54_cell
from cell_configurations import gsm_band1900_ch640_fr1955_cid56_cell
from cell_configurations import gsm_band1900_ch750_fr1977_cid57_cell
from cell_configurations import lte_band2_ch900_fr1960_pcid9_cell
from cell_configurations import lte_band4_ch2000_fr2115_pcid1_cell
from cell_configurations import lte_band4_ch2000_fr2115_pcid2_cell
from cell_configurations import lte_band4_ch2000_fr2115_pcid3_cell
from cell_configurations import lte_band4_ch2000_fr2115_pcid4_cell
from cell_configurations import lte_band4_ch2050_fr2120_pcid7_cell
from cell_configurations import lte_band4_ch2050_fr2120_pcid7_cell
from cell_configurations import lte_band4_ch2250_fr2140_pcid8_cell
from cell_configurations import lte_band12_ch5095_fr737_pcid10_cell
from cell_configurations import wcdma_band1_ch10700_fr2140_cid31_cell
from cell_configurations import wcdma_band1_ch10700_fr2140_cid32_cell
from cell_configurations import wcdma_band1_ch10700_fr2140_cid33_cell
from cell_configurations import wcdma_band1_ch10700_fr2140_cid34_cell
from cell_configurations import wcdma_band1_ch10575_fr2115_cid36_cell
from cell_configurations import wcdma_band1_ch10800_fr2160_cid37_cell
from cell_configurations import wcdma_band2_ch9800_fr1960_cid38_cell
from cell_configurations import wcdma_band2_ch9900_fr1980_cid39_cell


class TelLabNeighborCellTest(TelephonyBaseTest):
    # These are not actual DB Loss. the signal strength seen at phone varies this
    # much to the power level set at Anritsu
    LTE_DB_LOSS = -40
    WCDMA_DB_LOSS = -45
    GSM_DB_LOSS = -30
    ALLOWED_VARIATION = 15
    ANRITSU_SETTLING_TIME = 15
    SETTLING_TIME = 75
    LTE_MCS_DL = 5
    LTE_MCS_UL = 5
    NRB_DL = 50
    NRB_UL = 50
    CELL_PARAM_FILE = 'C:\\MX847570\\CellParam\\NEIGHBOR_CELL_TEST_TMO.wnscp'

    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.tests = ("test_ncells_intra_lte_0_cells",
                      "test_ncells_intra_lte_1_cells",
                      "test_ncells_intra_lte_2_cells",
                      "test_ncells_intra_lte_3_cells",
                      "test_ncells_intra_lte_4_cells",
                      "test_neighbor_cell_reporting_lte_intrafreq_0_tmo",
                      "test_neighbor_cell_reporting_lte_intrafreq_1_tmo",
                      "test_neighbor_cell_reporting_lte_intrafreq_2_tmo",
                      "test_neighbor_cell_reporting_lte_intrafreq_3_tmo",
                      "test_neighbor_cell_reporting_lte_interfreq_1_tmo",
                      "test_neighbor_cell_reporting_lte_interfreq_2_tmo",
                      "test_neighbor_cell_reporting_lte_interband_2_tmo",
                      "test_neighbor_cell_reporting_lte_interrat_1_tmo",
                      "test_neighbor_cell_reporting_lte_interrat_2_tmo",
                      "test_neighbor_cell_reporting_wcdma_intrafreq_0_tmo",
                      "test_neighbor_cell_reporting_wcdma_intrafreq_1_tmo",
                      "test_neighbor_cell_reporting_wcdma_intrafreq_2_tmo",
                      "test_neighbor_cell_reporting_wcdma_intrafreq_3_tmo",
                      "test_neighbor_cell_reporting_wcdma_interfreq_1_tmo",
                      "test_neighbor_cell_reporting_wcdma_interfreq_2_tmo",
                      "test_neighbor_cell_reporting_wcdma_interband_2_tmo",
                      "test_neighbor_cell_reporting_wcdma_interrat_2_tmo",
                      "test_neighbor_cell_reporting_gsm_intrafreq_0_tmo",
                      "test_neighbor_cell_reporting_gsm_intrafreq_1_tmo",
                      "test_neighbor_cell_reporting_gsm_intrafreq_2_tmo",
                      "test_neighbor_cell_reporting_gsm_intrafreq_3_tmo",
                      "test_neighbor_cell_reporting_gsm_interfreq_2_tmo",
                      "test_neighbor_cell_reporting_gsm_interband_2_tmo",
                      "test_neighbor_cell_reporting_gsm_interrat_2_tmo", )
        self.ad = self.android_devices[0]
        self.md8475a_ip_address = self.user_params[
            "anritsu_md8475a_ip_address"]
        self.mg3710a_ip_address = self.user_params[
            "anritsu_mg3710a_ip_address"]

    def setup_class(self):
        self.md8475a = None
        self.mg3710a = None
        try:
            self.md8475a = MD8475A(self.md8475a_ip_address, self.log)
        except AnritsuError as e:
            self.log.error("Error in connecting to Anritsu MD8475A:{}".format(
                e))
            return False

        try:
            self.mg3710a = MG3710A(self.mg3710a_ip_address, self.log)
        except AnritsuError as e:
            self.log.error("Error in connecting to Anritsu MG3710A :{}".format(
                e))
            return False
        return True

    def setup_test(self):
        self.turn_off_3710a_sg(1)
        self.turn_off_3710a_sg(2)
        self.mg3710a.set_arb_pattern_aorb_state("A", "OFF", 1)
        self.mg3710a.set_arb_pattern_aorb_state("B", "OFF", 1)
        self.mg3710a.set_arb_pattern_aorb_state("A", "OFF", 2)
        self.mg3710a.set_arb_pattern_aorb_state("B", "OFF", 2)
        self.mg3710a.set_freq_relative_display_status("OFF", 1)
        self.mg3710a.set_freq_relative_display_status("OFF", 2)
        self.ad.droid.telephonySetPreferredNetwork(NETWORK_MODE_LTE_GSM_WCDMA)
        ensure_phones_idle(self.log, self.android_devices)
        self.ad.droid.connectivityToggleAirplaneMode(True)
        self.ad.droid.telephonyToggleDataConnection(True)
        return True

    def teardown_test(self):
        self.ad.droid.connectivityToggleAirplaneMode(True)
        self.turn_off_3710a_sg(1)
        self.turn_off_3710a_sg(2)
        self.log.info("Stopping Simulation")
        self.md8475a.stop_simulation()
        return True

    def teardown_class(self):
        if self.md8475a is not None:
            self.md8475a.disconnect()
        if self.mg3710a is not None:
            self.mg3710a.disconnect()
        return True

    def _setup_lte_serving_cell(self, bts, dl_power, cell_id, physical_cellid):
        bts.output_level = dl_power
        bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_10MHz
        bts.packet_rate = BtsPacketRate.LTE_MANUAL
        bts.lte_mcs_dl = self.LTE_MCS_DL
        bts.lte_mcs_ul = self.LTE_MCS_UL
        bts.nrb_dl = self.NRB_DL
        bts.nrb_ul = self.NRB_UL
        bts.cell_id = cell_id
        bts.physical_cellid = physical_cellid
        bts.neighbor_cell_mode = "DEFAULT"

    def _setup_lte_neighbhor_cell_md8475a(self, bts, band, dl_power, cell_id,
                                          physical_cellid):
        bts.output_level = dl_power
        bts.band = band
        bts.bandwidth = BtsBandwidth.LTE_BANDWIDTH_10MHz
        bts.cell_id = cell_id
        bts.physical_cellid = physical_cellid
        bts.neighbor_cell_mode = "DEFAULT"
        bts.packet_rate = BtsPacketRate.LTE_MANUAL
        bts.lte_mcs_dl = self.LTE_MCS_DL
        bts.lte_mcs_ul = self.LTE_MCS_UL
        bts.nrb_dl = self.NRB_DL
        bts.nrb_ul = self.NRB_UL

    def _setup_wcdma_serving_cell(self, bts, dl_power, cell_id):
        bts.output_level = dl_power
        bts.cell_id = cell_id
        bts.neighbor_cell_mode = "DEFAULT"

    def _setup_wcdma_neighbhor_cell_md8475a(self, bts, band, dl_power,
                                            cell_id):
        bts.output_level = dl_power
        bts.band = band
        bts.cell_id = cell_id
        bts.neighbor_cell_mode = "DEFAULT"

    def _setup_lte_cell_md8475a(self, bts, params, dl_power):
        bts.output_level = dl_power
        bts.band = params['band']
        bts.bandwidth = params['bandwidth']
        bts.cell_id = params['cid']
        bts.physical_cellid = params['pcid']
        bts.mcc = params['mcc']
        bts.mnc = params['mnc']
        bts.tac = params['tac']
        bts.neighbor_cell_mode = "DEFAULT"
        bts.dl_channel = params['channel']
        bts.packet_rate = BtsPacketRate.LTE_MANUAL
        bts.lte_mcs_dl = self.LTE_MCS_DL
        bts.lte_mcs_ul = self.LTE_MCS_UL
        bts.nrb_dl = self.NRB_DL
        bts.nrb_ul = self.NRB_UL

    def _setup_wcdma_cell_md8475a(self, bts, params, dl_power):
        bts.output_level = dl_power
        bts.band = params['band']
        bts.cell_id = params['cid']
        bts.mcc = params['mcc']
        bts.mnc = params['mnc']
        bts.lac = params['lac']
        bts.rac = params['rac']
        bts.neighbor_cell_mode = "DEFAULT"
        bts.primary_scrambling_code = params['psc']
        bts.dl_channel = params['channel']

    def _setup_gsm_cell_md8475a(self, bts, params, dl_power):
        bts.output_level = params['power']
        bts.band = params['band']
        bts.cell_id = params['cid']
        bts.mcc = params['mcc']
        bts.mnc = params['mnc']
        bts.lac = params['lac']
        bts.rac = params['rac']
        bts.neighbor_cell_mode = "DEFAULT"

    def setup_3710a_waveform(self, sg_number, memory, frequency, power_level,
                             wave_package_name, wave_pattern_name):
        self.mg3710a.set_frequency(frequency, sg_number)
        self.mg3710a.set_arb_state("ON", sg_number)
        self.mg3710a.set_arb_combination_mode("EDIT", sg_number)
        self.mg3710a.select_waveform(wave_package_name, wave_pattern_name,
                                     memory, sg_number)
        self.mg3710a.set_arb_pattern_aorb_state(memory, "ON", sg_number)
        self.mg3710a.set_arb_level_aorb(memory, power_level, sg_number)

    def turn_on_3710a_sg(self, sg_number):
        self.mg3710a.set_modulation_state("ON", sg_number)
        self.mg3710a.set_rf_output_state("ON", sg_number)

    def turn_off_3710a_sg(self, sg_number):
        self.mg3710a.set_modulation_state("OFF", sg_number)
        self.mg3710a.set_rf_output_state("OFF", sg_number)

    def _verify_lte_cells_information(self, expected_no_cells, pcid_list,
                                      pcid_power_map):
        acell = self.ad.droid.telephonyGetAllCellInfo()
        if acell is not None:
            self.log.info("All Cell Info")
            self.log.info(acell)
            received_no_of_cells = len(acell)
            self.log.info(
                "Expected Number of Cells (Including Serving Cell): {}"
                .format(expected_no_cells))
            self.log.info(
                "Received Number of Cells (Including Serving Cell): {}"
                .format(received_no_of_cells))
            if received_no_of_cells is not expected_no_cells:
                self.log.error("Wrong number of cells reported")
                return False

            for i in range(received_no_of_cells):
                pcid = acell[i]['pcid']
                power_level = acell[i]['rsrp']
                if not pcid in pcid_list:
                    self.log.error("Wrong pcid reported :{} ".format(pcid))
                    return False

                expected_rsrp = pcid_power_map[pcid] + self.LTE_DB_LOSS
                received_rsrp = power_level
                self.log.info("PCID = {}".format(pcid))
                self.log.info("RAT = {}".format(acell[i]['rat']))
                self.log.info("Expected RSRP = {}".format(expected_rsrp))
                self.log.info("Received RSRP = {}".format(received_rsrp))
                if (received_rsrp <
                    (expected_rsrp - self.ALLOWED_VARIATION / 2) or
                        received_rsrp >
                    (expected_rsrp + self.ALLOWED_VARIATION / 2)):
                    self.log.error("Wrong rsrp reported")
                    return False
            return True
        else:
            self.log.error("API to get cell info returned None ")
            return False

    def _verify_lte_cell(self, cell_info, params):
        found = False
        for i in range(len(params)):
            if params[i]['pcid'] == cell_info['pcid']:
                expected_rsrp = params[i]['power'] + self.LTE_DB_LOSS
                received_rsrp = cell_info['rsrp']
                self.log.info("MCC = {}".format(cell_info['mcc']))
                self.log.info("MNC = {}".format(cell_info['mnc']))
                self.log.info("TAC = {}".format(cell_info['tac']))
                self.log.info("PCID = {}".format(cell_info['pcid']))
                self.log.info("RAT = {}".format(cell_info['rat']))
                self.log.info("Expected RSRP = {}".format(expected_rsrp))
                self.log.info("Received RSRP = {}".format(received_rsrp))
                if int(params[i]['mnc']) != cell_info['mnc']:
                    self.log.error("Wrong mnc reported")
                    break
                if int(params[i]['mcc']) != cell_info['mcc']:
                    self.log.error("Wrong mcc reported")
                    break
                if params[i]['tac'] != cell_info['tac']:
                    self.log.error("Wrong tac reported")
                    break
                if (received_rsrp < (expected_rsrp - self.ALLOWED_VARIATION) or
                        received_rsrp >
                    (expected_rsrp + self.ALLOWED_VARIATION)):
                    self.log.error("Wrong rsrp reported")
                    break
                found = True
                break
        return found

    def _verify_wcdma_cell(self, cell_info, params):
        found = False
        for i in range(len(params)):
            if params[i]['cid'] == cell_info['cid']:
                expected_signal_strength = params[i][
                    'power'] + self.WCDMA_DB_LOSS
                received_signal_strength = cell_info['signal_strength']
                self.log.info("MCC = {}".format(cell_info['mcc']))
                self.log.info("MNC = {}".format(cell_info['mnc']))
                self.log.info("LAC = {}".format(cell_info['lac']))
                self.log.info("CID = {}".format(cell_info['cid']))
                self.log.info("RAT = {}".format(cell_info['rat']))
                self.log.info("PSC = {}".format(cell_info['psc']))
                self.log.info("Expected Signal Strength= {}".format(
                    expected_signal_strength))
                self.log.info("Received Signal Strength = {}".format(
                    received_signal_strength))
                if int(params[i]['mnc']) != cell_info['mnc']:
                    self.log.error("Wrong mnc reported")
                    break
                if int(params[i]['mcc']) != cell_info['mcc']:
                    self.log.error("Wrong mcc reported")
                    break
                if params[i]['lac'] != cell_info['lac']:
                    self.log.error("Wrong mnc reported")
                    break
                if params[i]['psc'] != cell_info['psc']:
                    self.log.error("Wrong psc reported")
                    break
                if (received_signal_strength <
                    (expected_signal_strength - self.ALLOWED_VARIATION / 2) or
                        received_signal_strength >
                    (expected_signal_strength + self.ALLOWED_VARIATION / 2)):
                    self.log.error("Wrong Signal Strength reported")
                    break
                found = True
                break
        return found

    def _verify_gsm_cell(self, cell_info, params):
        found = False
        for i in range(len(params)):
            if params[i]['cid'] == cell_info['cid']:
                expected_signal_strength = params[i][
                    'power'] + self.GSM_DB_LOSS
                received_signal_strength = cell_info['signal_strength']
                self.log.info("MCC = {}".format(cell_info['mcc']))
                self.log.info("MNC = {}".format(cell_info['mnc']))
                self.log.info("LAC = {}".format(cell_info['lac']))
                self.log.info("CID = {}".format(cell_info['cid']))
                self.log.info("RAT = {}".format(cell_info['rat']))
                self.log.info("Expected Signal Strength= {}".format(
                    expected_signal_strength))
                self.log.info("Received Signal Strength = {}".format(
                    received_signal_strength))
                if int(params[i]['mnc']) != cell_info['mnc']:
                    self.log.error("Wrong mnc reported")
                    break
                if int(params[i]['mcc']) != cell_info['mcc']:
                    self.log.error("Wrong mcc reported")
                    break
                if params[i]['lac'] != cell_info['lac']:
                    self.log.error("Wrong lac reported")
                    break
                if (received_signal_strength <
                    (expected_signal_strength - self.ALLOWED_VARIATION / 2) or
                        received_signal_strength >
                    (expected_signal_strength + self.ALLOWED_VARIATION / 2)):
                    self.log.error("Wrong Signal Strength reported")
                    break
                found = True
                break
        return found

    def _verify_cells_information(self, expected_no_cells, params):
        acell = self.ad.droid.telephonyGetAllCellInfo()
        if acell is not None:
            self.log.info("All Cell Info")
            self.log.info(acell)
            received_no_of_cells = len(acell)
            self.log.info(
                "Expected Number of Cells (Including Serving Cell): {}"
                .format(expected_no_cells))
            self.log.info(
                "Received Number of Cells (Including Serving Cell): {}"
                .format(received_no_of_cells))
            if received_no_of_cells is not expected_no_cells:
                self.log.error("Wrong number of cells reported")
                return False

            for i in range(received_no_of_cells):
                print(acell[i])
                if acell[i]['rat'] == 'lte':
                    if not self._verify_lte_cell(acell[i], params):
                        self.log.error("Wrong LTE Cell Received")
                        return False
                elif acell[i]['rat'] == 'wcdma':
                    if not self._verify_wcdma_cell(acell[i], params):
                        self.log.error("Wrong WCDMA Cell Received")
                        return False
                elif acell[i]['rat'] == 'gsm':
                    if not self._verify_gsm_cell(acell[i], params):
                        self.log.error("Wrong GSM Cell Received")
                        return False
            return True
        else:
            self.log.error("API to get cell info returned None ")
            return False

    """ Tests Begin """

    @TelephonyBaseTest.tel_test_wrap
    def test_ncells_intra_lte_0_cells(self):
        """ Test Number of neighbor cells reported by Phone when no neighbor
        cells are present (Phone camped on LTE)

        Setup a single LTE cell configuration on MD8475A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell_cid = 11
        serving_cell_pcid = 11
        serving_cell_dlpower = -20
        expected_no_cells = 1
        pcid_list = [serving_cell_pcid]
        pcid_power_map = {serving_cell_pcid: serving_cell_dlpower, }

        self.md8475a.reset()
        [bts1] = set_system_model_lte(self.md8475a, self.user_params)
        self._setup_lte_serving_cell(bts1, serving_cell_dlpower,
                                     serving_cell_cid, serving_cell_pcid)
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.SETTLING_TIME)
        return self._verify_lte_cells_information(expected_no_cells, pcid_list,
                                                  pcid_power_map)

    @TelephonyBaseTest.tel_test_wrap
    def test_ncells_intra_lte_1_cells(self):
        """ Test Number of neighbor cells reported by Phone when one neighbor
        cell is present (Phone camped on LTE)

        Setup a two LTE cell configuration on MD8475A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell_cid = 11
        serving_cell_pcid = 11
        neigh_cell_cid = 22
        neigh_cell_pcid = 22
        serving_cell_dlpower = -20
        neigh_cell_dlpower = -24
        expected_no_cells = 2
        pcid_list = [serving_cell_pcid, neigh_cell_pcid]
        pcid_power_map = {
            serving_cell_pcid: serving_cell_dlpower,
            neigh_cell_pcid: neigh_cell_dlpower
        }

        self.md8475a.reset()
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_serving_cell(bts1, serving_cell_dlpower,
                                     serving_cell_cid, serving_cell_pcid)
        self._setup_lte_neighbhor_cell_md8475a(bts2, LTE_BAND_2,
                                               neigh_cell_dlpower,
                                               neigh_cell_cid, neigh_cell_pcid)
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.SETTLING_TIME)
        return self._verify_lte_cells_information(expected_no_cells, pcid_list,
                                                  pcid_power_map)

    @TelephonyBaseTest.tel_test_wrap
    def test_ncells_intra_lte_2_cells(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on LTE)

        Setup a two LTE cell configuration on MD8475A
        Setup one waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell_cid = 11
        serving_cell_pcid = 11
        neigh_cell_1_cid = 22
        neigh_cell_1_pcid = 22
        neigh_cell_2_cid = 1
        neigh_cell_2_pcid = 1
        serving_cell_dlpower = -20
        neigh_cell_1_dlpower = -24
        neigh_cell_2_dlpower = -23
        expected_no_cells = 3
        pcid_list = [serving_cell_pcid, neigh_cell_1_pcid, neigh_cell_2_pcid]
        pcid_power_map = {
            serving_cell_pcid: serving_cell_dlpower,
            neigh_cell_1_pcid: neigh_cell_1_dlpower,
            neigh_cell_2_pcid: neigh_cell_2_dlpower
        }

        self.md8475a.reset()
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)

        self._setup_lte_serving_cell(bts1, serving_cell_dlpower,
                                     serving_cell_cid, serving_cell_pcid)
        self._setup_lte_neighbhor_cell_md8475a(
            bts2, LTE_BAND_2, neigh_cell_1_dlpower, neigh_cell_1_cid,
            neigh_cell_1_pcid)
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()

        self.setup_3710a_waveform("1", "A", "1960MHZ", neigh_cell_2_dlpower,
                                  "LTE", "10M_B1_CID1")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_lte_cells_information(expected_no_cells, pcid_list,
                                                  pcid_power_map)

    @TelephonyBaseTest.tel_test_wrap
    def test_ncells_intra_lte_3_cells(self):
        """ Test Number of neighbor cells reported by Phone when three neighbor
        cells are present (Phone camped on LTE)

        Setup two LTE cell configuration on MD8475A
        Setup two waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell_cid = 11
        serving_cell_pcid = 11
        neigh_cell_1_cid = 1
        neigh_cell_1_pcid = 1
        neigh_cell_2_cid = 2
        neigh_cell_2_pcid = 2
        neigh_cell_3_cid = 3
        neigh_cell_3_pcid = 3
        serving_cell_dlpower = -20
        neigh_cell_1_dlpower = -24
        neigh_cell_2_dlpower = -22
        neigh_cell_3_dlpower = -23
        expected_no_cells = 4
        pcid_list = [serving_cell_pcid, neigh_cell_1_pcid, neigh_cell_2_pcid,
                     neigh_cell_3_pcid]
        pcid_power_map = {
            serving_cell_pcid: serving_cell_dlpower,
            neigh_cell_1_pcid: neigh_cell_1_dlpower,
            neigh_cell_2_pcid: neigh_cell_2_dlpower,
            neigh_cell_3_pcid: neigh_cell_3_dlpower
        }

        self.md8475a.reset()
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_serving_cell(bts1, serving_cell_dlpower,
                                     serving_cell_cid, serving_cell_pcid)

        self._setup_lte_neighbhor_cell_md8475a(
            bts2, LTE_BAND_2, neigh_cell_1_dlpower, neigh_cell_1_cid,
            neigh_cell_1_pcid)
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()

        self.setup_3710a_waveform("1", "A", "1960MHZ", neigh_cell_2_dlpower,
                                  "LTE", "10M_B1_CID2")

        self.setup_3710a_waveform("1", "B", "1960MHZ", neigh_cell_3_dlpower,
                                  "LTE", "10M_B1_CID3")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_lte_cells_information(expected_no_cells, pcid_list,
                                                  pcid_power_map)

    @TelephonyBaseTest.tel_test_wrap
    def test_ncells_intra_lte_4_cells(self):
        """ Test Number of neighbor cells reported by Phone when four neighbor
        cells are present (Phone camped on LTE)

        Setup two LTE cell configuration on MD8475A
        Setup three waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell_cid = 11
        serving_cell_pcid = 11
        neigh_cell_1_cid = 1
        neigh_cell_1_pcid = 1
        neigh_cell_2_cid = 2
        neigh_cell_2_pcid = 2
        neigh_cell_3_cid = 3
        neigh_cell_3_pcid = 3
        neigh_cell_4_cid = 5
        neigh_cell_4_pcid = 5
        serving_cell_dlpower = -20
        neigh_cell_1_dlpower = -24
        neigh_cell_2_dlpower = -22
        neigh_cell_3_dlpower = -24
        neigh_cell_4_dlpower = -22
        expected_no_cells = 5
        pcid_list = [serving_cell_pcid, neigh_cell_1_pcid, neigh_cell_2_pcid,
                     neigh_cell_3_pcid, neigh_cell_4_pcid]
        pcid_power_map = {
            serving_cell_pcid: serving_cell_dlpower,
            neigh_cell_1_pcid: neigh_cell_1_dlpower,
            neigh_cell_2_pcid: neigh_cell_2_dlpower,
            neigh_cell_3_pcid: neigh_cell_3_dlpower,
            neigh_cell_4_pcid: neigh_cell_4_dlpower
        }

        self.md8475a.reset()
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_serving_cell(bts1, serving_cell_dlpower,
                                     serving_cell_cid, serving_cell_pcid)

        self._setup_lte_neighbhor_cell_md8475a(
            bts2, LTE_BAND_2, neigh_cell_1_dlpower, neigh_cell_1_cid,
            neigh_cell_1_pcid)
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()

        self.setup_3710a_waveform("1", "A", "1960MHZ", neigh_cell_2_dlpower,
                                  "LTE", "10M_B1_CID2")

        self.setup_3710a_waveform("1", "B", "1960MHZ", neigh_cell_3_dlpower,
                                  "LTE", "10M_B1_CID3")

        self.setup_3710a_waveform("2", "A", "1960MHZ", neigh_cell_4_dlpower,
                                  "LTE", "10M_B1_CID5")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_lte_cells_information(expected_no_cells, pcid_list,
                                                  pcid_power_map)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_intrafreq_0_tmo(self):
        """ Test Number of neighbor cells reported by Phone when no neighbor
        cells are present (Phone camped on LTE)

        Setup a single LTE cell configuration on MD8475A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        serving_cell['power'] = -20
        expected_no_cells = 1
        cell_params = [serving_cell]

        self.md8475a.reset()
        [bts1] = set_system_model_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_intrafreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when one neighbor
        cell is present (Phone camped on LTE)

        Setup a two LTE cell configuration on MD8475A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell = lte_band4_ch2000_fr2115_pcid2_cell
        serving_cell['power'] = -20
        neighbor_cell['power'] = -24
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell,
                                     neighbor_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID2")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_intrafreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on LTE)

        Setup one LTE cell configuration on MD8475A
        Setup two waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = lte_band4_ch2000_fr2115_pcid2_cell
        neighbor_cell_2 = lte_band4_ch2000_fr2115_pcid3_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -23
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID2")
        bts1.set_neighbor_cell_type("LTE", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 2, "LTE_4_C2000_F2115_PCID3")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2115MHz",
                                  neighbor_cell_2['power'], "LTE",
                                  "lte_4_ch2000_pcid3")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_intrafreq_3_tmo(self):
        """ Test Number of neighbor cells reported by Phone when three neighbor
        cells are present (Phone camped on LTE)

        Setup a one LTE cell configuration on MD8475A
        Setup three waveforms on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = lte_band4_ch2000_fr2115_pcid2_cell
        neighbor_cell_2 = lte_band4_ch2000_fr2115_pcid3_cell
        neighbor_cell_3 = lte_band4_ch2000_fr2115_pcid4_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -23
        neighbor_cell_3['power'] = -22
        expected_no_cells = 4
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2,
                       neighbor_cell_3]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID2")
        bts1.set_neighbor_cell_type("LTE", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 2, "LTE_4_C2000_F2115_PCID3")
        bts1.set_neighbor_cell_type("LTE", 3, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 3, "LTE_4_C2000_F2115_PCID4")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2115MHz",
                                  neighbor_cell_2['power'], "LTE",
                                  "lte_4_ch2000_pcid3")

        self.setup_3710a_waveform("1", "B", "2115MHz",
                                  neighbor_cell_3['power'], "LTE",
                                  "lte_4_ch2000_pcid4")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_interfreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter frequency) are present (Phone camped on LTE)

        Setup a a LTE cell configuration on MD8475A
        Setup two LTE waveforms(inter frequency) on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = lte_band4_ch2050_fr2120_pcid7_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -23
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell_1]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2050_F2120_PCID7")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.md8475a.set_packet_preservation()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_interfreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter frequency) are present (Phone camped on LTE)

        Setup a a LTE cell configuration on MD8475A
        Setup two LTE waveforms(inter frequency) on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = lte_band4_ch2050_fr2120_pcid7_cell
        neighbor_cell_2 = lte_band4_ch2250_fr2140_pcid8_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -23
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2050_F2120_PCID7")
        bts1.set_neighbor_cell_type("LTE", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 2, "LTE_4_C2250_F2140_PCID8")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.setup_3710a_waveform("1", "A", "2140MHz",
                                  neighbor_cell_2['power'], "LTE",
                                  "lte_4_ch2250_pcid8")

        self.turn_on_3710a_sg(1)
        self.md8475a.set_packet_preservation()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_interband_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter band) are present (Phone camped on LTE)

        Setup one LTE cell configuration on MD8475A
        Setup two LTE waveforms((inter band)) on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = lte_band2_ch900_fr1960_pcid9_cell
        neighbor_cell_2 = lte_band12_ch5095_fr737_pcid10_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_lte(self.md8475a, self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_lte_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_2_C900_F1960_PCID9")
        bts1.set_neighbor_cell_type("LTE", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 2, "LTE_12_C5095_F737_PCID10")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "737.5MHz",
                                  neighbor_cell_2['power'], "LTE",
                                  "lte_12_ch5095_pcid10")
        self.turn_on_3710a_sg(1)
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.md8475a.set_packet_preservation()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_interrat_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter RAT) are present (Phone camped on LTE)

        Setup one LTE and one WCDMA cell configuration on MD8475A
        Setup one GSM waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = wcdma_band1_ch10700_fr2140_cid31_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_wcdma(self.md8475a,
                                                  self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10700_F2140_CID31")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.md8475a.set_packet_preservation()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_lte_interrat_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter RAT) are present (Phone camped on LTE)

        Setup one LTE and one WCDMA cell configuration on MD8475A
        Setup one GSM waveform on MG3710A
        Make Sure Phone is in LTE mode
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_1 = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_2 = gsm_band1900_ch512_fr1930_cid51_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_wcdma(self.md8475a,
                                                  self.user_params)
        self._setup_lte_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10700_F2140_CID31")
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C512_F1930_CID51")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_LTE_GSM_WCDMA,
                                  RAT_FAMILY_LTE,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_LTE, NETWORK_MODE_LTE_GSM_WCDMA))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "1930.2MHz",
                                  neighbor_cell_2['power'], "GSM",
                                  "gsm_lac51_cid51")
        self.turn_on_3710a_sg(1)
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.md8475a.set_packet_preservation()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_intrafreq_0_tmo(self):
        """ Test Number of neighbor cells reported by Phone when no neighbor
        cells are present (Phone camped on WCDMA)

        Setup a single WCDMA cell configuration on MD8475A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        serving_cell['power'] = -20
        expected_no_cells = 1
        cell_params = [serving_cell]

        self.md8475a.reset()
        [bts1] = set_system_model_wcdma(self.md8475a, self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_intrafreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when one neighbor
        cells is present (Phone camped on WCDMA)

        Setup two WCDMA cell configuration on MD8475A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell = wcdma_band1_ch10700_fr2140_cid34_cell
        serving_cell['power'] = -20
        neighbor_cell['power'] = -24
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell,
                                       neighbor_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10700_F2140_CID34")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_intrafreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on WCDMA)

        Setup two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = wcdma_band1_ch10700_fr2140_cid32_cell
        neighbor_cell_2 = wcdma_band1_ch10700_fr2140_cid33_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10700_F2140_CID32")
        bts1.set_neighbor_cell_type("WCDMA", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 2, "WCDM_1_C10700_F2140_CID33")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2140MHz",
                                  neighbor_cell_2['power'], "WCDMA",
                                  "wcdma_1_psc33_cid33")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_intrafreq_3_tmo(self):
        """ Test Number of neighbor cells reported by Phone when three neighbor
        cells are present (Phone camped on WCDMA)

        Setup two WCDMA cell configuration on MD8475A
        Setup two WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = wcdma_band1_ch10700_fr2140_cid32_cell
        neighbor_cell_2 = wcdma_band1_ch10700_fr2140_cid33_cell
        neighbor_cell_3 = wcdma_band1_ch10700_fr2140_cid34_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -23
        neighbor_cell_3['power'] = -22
        expected_no_cells = 4
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2,
                       neighbor_cell_3]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10700_F2140_CID32")
        bts1.set_neighbor_cell_type("WCDMA", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 2, "WCDM_1_C10700_F2140_CID33")
        bts1.set_neighbor_cell_type("WCDMA", 3, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 3, "WCDM_1_C10700_F2140_CID34")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2140MHz",
                                  neighbor_cell_2['power'], "WCDMA",
                                  "wcdma_1_psc33_cid33")

        self.setup_3710a_waveform("2", "A", "2140MHz",
                                  neighbor_cell_3['power'], "WCDMA",
                                  "wcdma_1_psc34_cid34")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_interfreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter frequency) are present (Phone camped on WCDMA)

        Setup a two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phonene

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = wcdma_band1_ch10800_fr2160_cid37_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell_1]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10800_F2160_CID37")
        self.md8475a.start_simulation()
        #To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_interfreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter frequency) are present (Phone camped on WCDMA)

        Setup a two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phonene

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = wcdma_band1_ch10575_fr2115_cid36_cell
        neighbor_cell_2 = wcdma_band1_ch10800_fr2160_cid37_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -23
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_1_C10575_F2115_CID36")
        bts1.set_neighbor_cell_type("WCDMA", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 2, "WCDM_1_C10800_F2160_CID37")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2160MHz",
                                  neighbor_cell_2['power'], "WCDMA",
                                  "wcdma_1_psc37_cid37")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_interband_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter band) are present (Phone camped on WCDMA)

        Setup a two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = wcdma_band2_ch9800_fr1960_cid38_cell
        neighbor_cell_2 = wcdma_band2_ch9900_fr1980_cid39_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -23
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_wcdma(self.md8475a,
                                                    self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_wcdma_cell_md8475a(bts2, neighbor_cell_1,
                                       neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("WCDMA", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 1, "WCDM_2_C9800_F1960_CID38")
        bts1.set_neighbor_cell_type("WCDMA", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 2, "WCDM_2_C9900_F1980_CID39")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "1980MHz",
                                  neighbor_cell_2['power'], "WCDMA",
                                  "wcdma_2_psc39_cid39")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_interrat_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on WCDMA)

        Setup a two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_2 = lte_band4_ch2000_fr2115_pcid1_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -23
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_lte_wcdma(self.md8475a,
                                                  self.user_params)
        self._setup_wcdma_cell_md8475a(bts2, serving_cell,
                                       serving_cell['power'])
        self._setup_lte_cell_md8475a(bts1, neighbor_cell_2,
                                     neighbor_cell_2['power'])
        bts2.neighbor_cell_mode = "USERDATA"
        bts2.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts2.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID1")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts1.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts1.service_state = BtsServiceState.SERVICE_STATE_IN
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_wcdma_interrat_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on WCDMA)

        Setup a two WCDMA cell configuration on MD8475A
        Setup one WCDMA waveform on MG3710A
        Make Sure Phone camped on WCDMA
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = wcdma_band1_ch10700_fr2140_cid31_cell
        neighbor_cell_1 = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_2 = lte_band4_ch2000_fr2115_pcid1_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -23
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1, bts2] = set_system_model_wcdma_gsm(self.md8475a,
                                                  self.user_params)
        self._setup_wcdma_cell_md8475a(bts1, serving_cell,
                                       serving_cell['power'])
        self._setup_gsm_cell_md8475a(bts2, neighbor_cell_1,
                                     neighbor_cell_1['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C512_F1930_CID51")
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID1")
        self.md8475a.start_simulation()
        # To make sure phone camps on BTS1
        bts2.service_state = BtsServiceState.SERVICE_STATE_OUT

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_UMTS,
                                  RAT_FAMILY_UMTS,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_UMTS, NETWORK_MODE_GSM_UMTS))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        bts2.service_state = BtsServiceState.SERVICE_STATE_IN
        self.setup_3710a_waveform("1", "A", "2115MHz",
                                  neighbor_cell_2['power'], "LTE",
                                  "lte_4_ch2000_pcid1")
        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_intrafreq_0_tmo(self):
        """ Test Number of neighbor cells reported by Phone when no neighbor
        cells are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        serving_cell['power'] = -30
        expected_no_cells = 1
        cell_params = [serving_cell]

        self.md8475a.reset()
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        self.md8475a.start_simulation()
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_intrafreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when one neighbor
        cell is present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell = gsm_band1900_ch512_fr1930_cid52_cell
        serving_cell['power'] = -20
        neighbor_cell['power'] = -22
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C512_F1930_CID52")
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        time.sleep(self.ANRITSU_SETTLING_TIME)
        self.setup_3710a_waveform("1", "A", "1930.2MHz",
                                  neighbor_cell['power'], "GSM",
                                  "gsm_lac52_cid52")

        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_intrafreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup two GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = gsm_band1900_ch512_fr1930_cid52_cell
        neighbor_cell_2 = gsm_band1900_ch512_fr1930_cid53_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C512_F1930_CID52")
        bts1.set_neighbor_cell_type("GSM", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 2, "GSM_1900_C512_F1930_CID53")
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "1930.2MHz",
                                  neighbor_cell_1['power'], "GSM",
                                  "gsm_lac52_cid52")

        self.setup_3710a_waveform("2", "A", "1930.2MHz",
                                  neighbor_cell_2['power'], "GSM",
                                  "gsm_lac53_cid53")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_intrafreq_3_tmo(self):
        """ Test Number of neighbor cells reported by Phone when three neighbor
        cells are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup three GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = gsm_band1900_ch512_fr1930_cid52_cell
        neighbor_cell_2 = gsm_band1900_ch512_fr1930_cid53_cell
        neighbor_cell_3 = gsm_band1900_ch512_fr1930_cid54_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        neighbor_cell_3['power'] = -24
        expected_no_cells = 4
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2,
                       neighbor_cell_3]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C512_F1930_CID52")
        bts1.set_neighbor_cell_type("GSM", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 2, "GSM_1900_C512_F1930_CID53")
        bts1.set_neighbor_cell_type("GSM", 3, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 3, "GSM_1900_C512_F1930_CID53")
        self.md8475a.start_simulation()

        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "1930.2MHz",
                                  neighbor_cell_1['power'], "GSM",
                                  "gsm_lac52_cid52")

        self.setup_3710a_waveform("2", "A", "1930.2MHz",
                                  neighbor_cell_2['power'], "GSM",
                                  "gsm_lac53_cid53")

        self.setup_3710a_waveform("2", "B", "1930.2MHz",
                                  neighbor_cell_3['power'], "GSM",
                                  "gsm_lac54_cid54")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_interfreq_1_tmo(self):
        """ Test Number of neighbor cells reported by Phone when one neighbor
        cells(inter frequency) is present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup two GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = gsm_band1900_ch640_fr1955_cid56_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        expected_no_cells = 2
        cell_params = [serving_cell, neighbor_cell_1]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C640_F1955_CID56")
        self.md8475a.start_simulation()

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "1955.8MHz",
                                  neighbor_cell_1['power'], "GSM",
                                  "gsm_lac56_cid56")

        self.turn_on_3710a_sg(1)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_interfreq_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter frequency) are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup two GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = gsm_band1900_ch640_fr1955_cid56_cell
        neighbor_cell_2 = gsm_band1900_ch750_fr1977_cid57_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_1900_C640_F1955_CID56")
        bts1.set_neighbor_cell_type("GSM", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 2, "GSM_1900_C750_F1977_CID57")
        self.md8475a.start_simulation()

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "1955.8MHz",
                                  neighbor_cell_1['power'], "GSM",
                                  "gsm_lac56_cid56")

        self.setup_3710a_waveform("2", "A", "1977.8MHz",
                                  neighbor_cell_2['power'], "GSM",
                                  "gsm_lac57_cid57")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_interband_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when two neighbor
        cells(inter band) are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup two GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = gsm_band850_ch128_fr869_cid58_cell
        neighbor_cell_2 = gsm_band850_ch251_fr893_cid59_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("GSM", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 1, "GSM_850_C128_F869_CID58")
        bts1.set_neighbor_cell_type("GSM", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("GSM", 2, "GSM_850_C251_F893_CID59")
        self.md8475a.start_simulation()

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "869MHz", neighbor_cell_1['power'],
                                  "GSM", "gsm_lac58_cid58")

        self.setup_3710a_waveform("2", "A", "893MHz", neighbor_cell_2['power'],
                                  "GSM", "gsm_lac59_cid59")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    @TelephonyBaseTest.tel_test_wrap
    def test_neighbor_cell_reporting_gsm_interrat_2_tmo(self):
        """ Test Number of neighbor cells reported by Phone when no neighbor
        cells(inter RAT) are present (Phone camped on GSM)

        Setup one GSM cell configuration on MD8475A
        Setup one LTE and one GSM waveforms on MG3710A
        Make Sure Phone camped on GSM
        Verify the number of neighbor cells reported by Phone

        Returns:
            True if pass; False if fail
        """
        serving_cell = gsm_band1900_ch512_fr1930_cid51_cell
        neighbor_cell_1 = lte_band4_ch2000_fr2115_pcid1_cell
        neighbor_cell_2 = wcdma_band1_ch10700_fr2140_cid31_cell
        serving_cell['power'] = -20
        neighbor_cell_1['power'] = -24
        neighbor_cell_2['power'] = -22
        expected_no_cells = 3
        cell_params = [serving_cell, neighbor_cell_1, neighbor_cell_2]

        self.md8475a.reset()
        self.md8475a.load_cell_paramfile(self.CELL_PARAM_FILE)
        [bts1] = set_system_model_gsm(self.md8475a, self.user_params)
        self._setup_gsm_cell_md8475a(bts1, serving_cell, serving_cell['power'])
        bts1.neighbor_cell_mode = "USERDATA"
        bts1.set_neighbor_cell_type("LTE", 1, "CELLNAME")
        bts1.set_neighbor_cell_name("LTE", 1, "LTE_4_C2000_F2115_PCID1")
        bts1.set_neighbor_cell_type("WCDMA", 2, "CELLNAME")
        bts1.set_neighbor_cell_name("WCDMA", 2, "WCDM_1_C10700_F2140_CID31")
        self.md8475a.start_simulation()

        self.ad.droid.telephonyToggleDataConnection(False)
        if not ensure_network_rat(self.log,
                                  self.ad,
                                  NETWORK_MODE_GSM_ONLY,
                                  RAT_FAMILY_GSM,
                                  toggle_apm_after_setting=True):
            self.log.error(
                "Failed to set rat family {}, preferred network:{}".format(
                    RAT_FAMILY_GSM, NETWORK_MODE_GSM_ONLY))
            return False
        self.md8475a.wait_for_registration_state()
        self.setup_3710a_waveform("1", "A", "2115MHz",
                                  neighbor_cell_1['power'], "LTE",
                                  "lte_1_ch2000_pcid1")

        self.setup_3710a_waveform("2", "A", "2140MHz",
                                  neighbor_cell_2['power'], "WCDMA",
                                  "wcdma_1_psc31_cid31")
        self.turn_on_3710a_sg(1)
        self.turn_on_3710a_sg(2)
        time.sleep(self.SETTLING_TIME)
        return self._verify_cells_information(expected_no_cells, cell_params)

    """ Tests End """
