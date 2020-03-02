#!/usr/bin/env python3
#
#   Copyright 2020 - The Android Open Source Project
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

import acts.test_utils.power.cellular.cellular_pdcch_power_test as cppt


class PowerTelPdcch_Modem_Test(cppt.PowerTelPDCCHTest):
    def test_lte_band_13_pul_low_bw_10_tm_3_dlmcs_4_ulmcs_4_mimo_2x2_direction_dlul_phich_16_cfi_1(self):
        self.power_pdcch_test()

    def test_lte_band_7_pul_low_bw_20_tm_3_dlmcs_4_ulmcs_4_mimo_2x2_direction_dlul_phich_16_cfi_1(self):
        self.power_pdcch_test()

    def test_lte_band_4_pul_low_bw_20_tm_3_dlmcs_4_ulmcs_4_mimo_2x2_direction_dlul_phich_16_cfi_1(self):
        self.power_pdcch_test()

    def test_lte_band_40_pul_low_bw_20_tm_3_dlmcs_4_ulmcs_4_mimo_2x2_direction_dlul_phich_16_cfi_1(self):
        self.power_pdcch_test()
