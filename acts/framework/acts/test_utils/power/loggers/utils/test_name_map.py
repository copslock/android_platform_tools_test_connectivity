TEST_SUITE_NAME_MAP = {
  'PowerTelTraffic_LTE_Test': 'TechEng LTE Traffic',
  'PowerTelIdle_LTE_Test': 'TechEng LTE Idle',
  'PowerTelTraffic_Modem_Test': 'QComm dashboard - Traffic',
  'PowerTelIdle_Modem_Test': 'QComm dashboard - Idle',
  'PowerBaselineTest': 'Rockbottom',
}

TEST_CASE_NAME_MAP = {
  # LTE Traffic
  'test_lte_traffic_band_12_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_1': 'LTE traffic - Band 12, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_12_pul_max_bw_5_tm_1_mimo_1x1_pattern_0_100_2': 'LTE traffic - Band 12, max UL power, 5 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_12_pul_low_bw_14_tm_1_mimo_1x1_pattern_0_100_3': 'LTE traffic - Band 12, low UL power, 14 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_20_pul_low_bw_5_tm_3_mimo_2x2_pattern_100_0_4': 'LTE traffic - Band 20, low UL power, 5 MHz BW, TM3 2x2, 100/0 pattern',
  'test_lte_traffic_band_13_pul_low_bw_5_tm_1_mimo_1x1_pattern_75_25_5': 'LTE traffic - Band 13, low UL power, 5 MHz BW, TM3 1x1, 75/25 pattern',
  'test_lte_traffic_band_13_pul_max_bw_10_tm_1_mimo_1x1_pattern_100_100_6': 'LTE traffic - Band 13, max UL power, 10 MHz BW, TM3 1x1, 100/100 pattern',
  'test_lte_traffic_band_5_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_7': 'LTE traffic - Band 5, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_1_pul_medium_bw_20_tm_3_mimo_4x4_pattern_100_0_8': 'LTE traffic - Band 1, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_1_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_9': 'LTE traffic - Band 1, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_3_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_10': 'LTE traffic - Band 3, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_3_pul_max_bw_10_tm_1_mimo_1x1_pattern_100_100_11': 'LTE traffic - Band 3, max UL power, 10 MHz BW, TM3 1x1, 100/100 pattern',
  'test_lte_traffic_band_2_pul_low_bw_3_tm_1_mimo_1x1_pattern_0_100_12': 'LTE traffic - Band 2, low UL power, 3 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_2_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_13': 'LTE traffic - Band 2, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_2_pul_medium_bw_20_tm_3_mimo_4x4_pattern_100_0_14': 'LTE traffic - Band 2, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_15': 'LTE traffic - Band 4, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_4_pul_low_bw_5_tm_3_mimo_4x4_pattern_100_0_16': 'LTE traffic - Band 4, low UL power, 5 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pul_max_bw_5_tm_3_mimo_4x4_pattern_100_100_17': 'LTE traffic - Band 4, max UL power, 5 MHz BW, TM3 4x4, 100/100 pattern',
  'test_lte_traffic_band_4_pul_medium_bw_10_tm_3_mimo_4x4_pattern_100_0_18': 'LTE traffic - Band 4, medium UL power, 10 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pul_medium_bw_20_tm_3_mimo_4x4_pattern_100_0_19': 'LTE traffic - Band 4, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pul_max_bw_20_tm_1_mimo_1x1_pattern_100_100_20': 'LTE traffic - Band 4, max UL power, 20 MHz BW, TM3 1x1, 100/100pattern',
  'test_lte_traffic_band_7_pul_high_bw_15_tm_1_mimo_1x1_pattern_0_100_21': 'LTE traffic - Band 7, high UL power, 15 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_7_pul_high_bw_20_tm_1_mimo_1x1_pattern_0_100_22': 'LTE traffic - Band 7, high UL power, 20 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_7_pul_max_bw_10_tm_1_mimo_1x1_pattern_100_100_23': 'LTE traffic - Band 7, max UL power, 10 MHz BW, TM3 1x1, 100/100 pattern',
  'test_lte_traffic_band_7_pul_max_bw_20_tm_1_mimo_1x1_pattern_100_100_24': 'LTE traffic - Band 7, max UL power, 20 MHz BW, TM3 1x1, 100/100 pattern',
  'test_lte_traffic_band_7_pul_low_bw_10_tm_4_mimo_2x2_pattern_75_25_25': 'LTE traffic - Band 7, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_7_pul_medium_bw_10_tm_3_mimo_4x4_pattern_100_0_26': 'LTE traffic - Band 7, medium UL power, 10 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_7_pul_medium_bw_20_tm_3_mimo_4x4_pattern_100_0_27': 'LTE traffic - Band 7, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_38_pul_medium_bw_20_tm_3_mimo_4x4_tddconfig_2_28': 'LTE traffic - Band 38, medium UL power, 20 MHz BW, TM3 4x4, TDD 2 pattern',
  'test_lte_traffic_band_38_pul_max_bw_10_tm_1_mimo_1x1_tddconfig_1_29': 'LTE traffic - Band 38, max UL power, 10 MHz BW, TM3 1x1, TDD 1 pattern',
  'test_lte_traffic_band_38_pul_high_bw_5_tm_1_mimo_1x1_tddconfig_5_30': 'LTE traffic - Band 38, high UL power, 5 MHz BW, TM3 1x1, TDD 5 pattern',
  'test_lte_traffic_band_40_pul_low_bw_20_tm_4_mimo_2x2_tddconfig_2_31': 'LTE traffic - Band 40, low UL power, 20 MHz BW, TM3 2x2, TDD 2 pattern',
  'test_lte_traffic_band_40_pul_max_bw_10_tm_1_mimo_1x1_tddconfig_5_32': 'LTE traffic - Band 40, max UL power, 10 MHz BW, TM3 1x1, TDD 5 pattern',
  'test_lte_traffic_band_41_pul_medium_bw_20_tm_3_mimo_4x4_tddconfig_2_33': 'LTE traffic - Band 41, medium UL power, 20 MHz BW, TM3 4x4, TDD 2 pattern',
  'test_lte_traffic_band_41_pul_high_bw_15_tm_1_mimo_1x1_tddconfig_1_34': 'LTE traffic - Band 41, high UL power, 15 MHz BW, TM3 1x1, TDD 1 pattern',
  'test_lte_traffic_band_42_pul_low_bw_20_tm_4_mimo_2x2_tddconfig_2_35': 'LTE traffic - Band 42, low UL power, 20 MHz BW, TM3 2x2, TDD 2 pattern',

  # LTE Idle
  'test_lte_idle_band_13_pul_low_bw_10_tm_1_mimo_1x1_rrcstatuschangetimer_10_1': 'LTE Idle - Band 13, low UL power, 10 MHz BW, TM3 1x1, RRC Status Change Timer 10',
  'test_lte_idle_band_41_pul_low_bw_10_tm_1_mimo_1x1_rrcstatuschangetimer_10_tddconfig_2_2': 'LTE Idle - Band 41, low UL power, 10 MHz BW, TM3 1x1, RRC Status Change Timer 10, TDD 2',

  # Cellular Rockbottom
  'test_power_baseline': 'Power Baseline',

  # QComm LTE Traffic
  'test_lte_band_13_pul_0_bw_10_tm_3_dlmcs_28_mimo_2x2_direction_dlul_phich_16_cfi_1': 'LTE1E - Cat3 B13',
  'test_lte_band_38_pul_0_bw_20_tm_3_mimo_2x2_direction_dlul_tddconfig_1_phich_16_cfi_1_ssf_7': 'LTE5E - Cat3 B38',
  'test_lte_band_7_pul_0_bw_20_tm_3_dlmcs_28_mimo_2x2_direction_dlul_phich_16_cfi_1': 'LTE7E - Cat4 B7',
  'test_lteca_band_3a4a_pul_0_bw_20_tm_3_mimo_2x2_direction_dlul_phich_16_cfi_1': 'LTE10E - Cat6 B3 - B4',
  'test_lteca_band_3a7a20a_pul_0_bw_20_tm_3_mimo_2x2_direction_dlul_phich_16_cfi_1': 'LTE21E - Cat9 B3 B7 B20',

  # QComm Idle
  'test_lte_band_13_pul_0_bw_10_tm_3_dlmcs_28_mimo_2x2_paging_2560_rrcstatuschangetimer_10': 'LS1 - B13',
  'test_lte_band_41_pul_0_bw_10_tm_3_dlmcs_28_mimo_2x2_tddconfig_1_ssf_7_paging_2560_rrcstatuschangetimer_10': 'LS3 - B41',
  'test_lte_band_1_pul_0_bw_20_tm_1_dlmcs_28_mimo_1x1_paging_1280_rrcstatuschangetimer_10': 'LS11 - B1',

  # TODO(codycaldwell) Remove once older test results are no longer visible in the dashboard
  'test_lte_traffic_band_12_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_1': 'LTE traffic - Band 12, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_12_pdl_excellent_pul_max_bw_5_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_2': 'LTE traffic - Band 12, max UL power, 5 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_12_pdl_excellent_pul_low_bw_14_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_3': 'LTE traffic - Band 12, low UL power, 14 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_20_pdl_excellent_pul_low_bw_5_tm_3_mimo_2x2_scheduling_static_direction_dl_pattern_100_0_4': 'LTE traffic - Band 20, low UL power, 5 MHz BW, TM3 2x2, 100/0 pattern',
  'test_lte_traffic_band_13_pdl_excellent_pul_low_bw_5_tm_1_mimo_1x1_scheduling_static_direction_dlul_pattern_75_25_5': 'LTE traffic - Band 13, low UL power, 5 MHz BW, TM3 1x1, 75/25 pattern',
  'test_lte_traffic_band_13_pdl_excellent_pul_max_bw_10_tm_1_mimo_1x1_scheduling_static_direction_dl_pattern_100_0_6': 'LTE traffic - Band 13, max UL power, 10 MHz BW, TM3 1x1, 100/0 pattern',
  'test_lte_traffic_band_5_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_7': 'LTE traffic - Band 5, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_1_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_8': 'LTE traffic - Band 1, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_1_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_9': 'LTE traffic - Band 1, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_3_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_10': 'LTE traffic - Band 3, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_3_pdl_excellent_pul_max_bw_10_tm_1_mimo_1x1_scheduling_static_direction_dl_pattern_100_0_11': 'LTE traffic - Band 3, max UL power, 10 MHz BW, TM3 1x1, 100/0 pattern',
  'test_lte_traffic_band_2_pdl_excellent_pul_low_bw_3_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_12': 'LTE traffic - Band 2, low UL power, 3 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_2_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_13': 'LTE traffic - Band 2, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_2_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_14': 'LTE traffic - Band 2, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_15': 'LTE traffic - Band 4, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_low_bw_5_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_16': 'LTE traffic - Band 4, low UL power, 5 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_max_bw_5_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_17': 'LTE traffic - Band 4, max UL power, 5 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_medium_bw_10_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_18': 'LTE traffic - Band 4, medium UL power, 10 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_19': 'LTE traffic - Band 4, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_4_pdl_excellent_pul_max_bw_20_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_20': 'LTE traffic - Band 4, max UL power, 20 MHz BW, TM3 1x1, 0/100pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_high_bw_15_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_21': 'LTE traffic - Band 7, high UL power, 15 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_high_bw_20_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_22': 'LTE traffic - Band 7, high UL power, 20 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_max_bw_10_tm_1_mimo_1x1_scheduling_static_direction_dl_pattern_100_0_23': 'LTE traffic - Band 7, max UL power, 10 MHz BW, TM3 1x1, 100/0 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_max_bw_20_tm_1_mimo_1x1_scheduling_static_direction_ul_pattern_0_100_24': 'LTE traffic - Band 7, max UL power, 20 MHz BW, TM3 1x1, 0/100 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_low_bw_10_tm_4_mimo_2x2_scheduling_static_direction_dlul_pattern_75_25_25': 'LTE traffic - Band 7, low UL power, 10 MHz BW, TM3 2x2, 75/25 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_medium_bw_10_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_26': 'LTE traffic - Band 7, medium UL power, 10 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_7_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dl_pattern_100_0_27': 'LTE traffic - Band 7, medium UL power, 20 MHz BW, TM3 4x4, 100/0 pattern',
  'test_lte_traffic_band_38_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dlul_tddconfig_2_28': 'LTE traffic - Band 38, medium UL power, 20 MHz BW, TM3 4x4, TDD 2 pattern',
  'test_lte_traffic_band_38_pdl_excellent_pul_max_bw_10_tm_1_mimo_1x1_scheduling_static_direction_dlul_tddconfig_1_29': 'LTE traffic - Band 38, max UL power, 10 MHz BW, TM3 1x1, TDD 1 pattern',
  'test_lte_traffic_band_38_pdl_excellent_pul_high_bw_5_tm_1_mimo_1x1_scheduling_static_direction_dlul_tddconfig_5_30': 'LTE traffic - Band 38, high UL power, 5 MHz BW, TM3 1x1, TDD 5 pattern',
  'test_lte_traffic_band_40_pdl_excellent_pul_low_bw_20_tm_4_mimo_2x2_scheduling_static_direction_dlul_tddconfig_2_31': 'LTE traffic - Band 40, low UL power, 20 MHz BW, TM3 2x2, TDD 2 pattern',
  'test_lte_traffic_band_40_pdl_excellent_pul_max_bw_10_tm_1_mimo_1x1_scheduling_static_direction_dlul_tddconfig_5_32': 'LTE traffic - Band 40, max UL power, 10 MHz BW, TM3 1x1, TDD 5 pattern',
  'test_lte_traffic_band_41_pdl_excellent_pul_medium_bw_20_tm_3_mimo_4x4_scheduling_static_direction_dlul_tddconfig_2_33': 'LTE traffic - Band 41, medium UL power, 20 MHz BW, TM3 4x4, TDD 2 pattern',
  'test_lte_traffic_band_41_pdl_excellent_pul_high_bw_15_tm_1_mimo_1x1_scheduling_static_direction_dlul_tddconfig_1_34': 'LTE traffic - Band 41, high UL power, 15 MHz BW, TM3 1x1, TDD 1 pattern',
  'test_lte_traffic_band_42_pdl_excellent_pul_low_bw_20_tm_4_mimo_2x2_scheduling_static_direction_dlul_tddconfig_2_35': 'LTE traffic - Band 42, low UL power, 20 MHz BW, TM3 2x2, TDD 2 pattern',
}

class TestNameType:
  TEST_SUITE = 1
  TEST_CASE = 2

class TestNameMap:
  @staticmethod
  def get_display_name(key, test_type=TestNameType.TEST_SUITE):
    """Maps the given test suite or test case name to its display name

    Args:
        key: String representing the test suite or test case to map
        test_type: TestNameType enum specifying the type of key (suite or test case)
    Return:
        The display name for the suite or test case. If none exists, the provided
        key is returned instead
    """
    name_map = TEST_SUITE_NAME_MAP
    if test_type == TestNameType.TEST_CASE:
      name_map = TEST_CASE_NAME_MAP
    return name_map.get(key, key)
