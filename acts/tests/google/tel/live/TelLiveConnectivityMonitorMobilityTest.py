#!/usr/bin/env python3.4
#
#   Copyright 2016 - Google
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
    Test Script for epdg RF shield box related tests.
"""

import time
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_atten_utils import set_rssi
from acts.test_utils.tel.tel_defines import CELL_WEAK_RSSI_VALUE
from acts.test_utils.tel.tel_defines import GEN_4G
from acts.test_utils.tel.tel_defines import INVALID_WIFI_RSSI
from acts.test_utils.tel.tel_defines import MAX_RSSI_RESERVED_VALUE
from acts.test_utils.tel.tel_defines import MIN_RSSI_RESERVED_VALUE
from acts.test_utils.tel.tel_defines import NETWORK_SERVICE_DATA
from acts.test_utils.tel.tel_defines import WAIT_TIME_WIFI_RSSI_CALIBRATION_SCREEN_ON
from acts.test_utils.tel.tel_defines import WAIT_TIME_WIFI_RSSI_CALIBRATION_WIFI_CONNECTED
from acts.test_utils.tel.tel_defines import WFC_MODE_CELLULAR_PREFERRED
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_defines import WIFI_WEAK_RSSI_VALUE
from acts.test_utils.tel.tel_defines import SignalStrengthContainer
from acts.test_utils.tel.tel_test_utils import ensure_network_generation
from acts.test_utils.tel.tel_test_utils import ensure_phones_default_state
from acts.test_utils.tel.tel_test_utils import ensure_wifi_connected
from acts.test_utils.tel.tel_test_utils import set_wfc_mode
from acts.test_utils.tel.tel_test_utils import wait_for_wifi_data_connection
from acts.test_utils.tel.tel_test_utils import verify_http_connection
from acts.test_utils.tel.tel_defines import CAPABILITY_VOLTE
from TelLiveConnectivityMonitorBaseTest import TelLiveConnectivityMonitorBaseTest
from TelLiveConnectivityMonitorBaseTest import ACTIONS
from TelLiveConnectivityMonitorBaseTest import TROUBLES

# Attenuator name
ATTEN_NAME_FOR_WIFI_2G = 'wifi0'
ATTEN_NAME_FOR_WIFI_5G = 'wifi1'
ATTEN_NAME_FOR_CELL_3G = 'cell0'
ATTEN_NAME_FOR_CELL_4G = 'cell1'

# WiFi RSSI settings for ROVE_IN test
WIFI_RSSI_FOR_ROVE_IN_TEST_PHONE_ROVE_IN = -60
WIFI_RSSI_FOR_ROVE_IN_TEST_PHONE_NOT_ROVE_IN = -70

# WiFi RSSI settings for ROVE_OUT test
WIFI_RSSI_FOR_ROVE_OUT_TEST_PHONE_INITIAL_STATE = -60
WIFI_RSSI_FOR_ROVE_OUT_TEST_PHONE_NOT_ROVE_OUT = -70
WIFI_RSSI_FOR_ROVE_OUT_TEST_PHONE_ROVE_OUT = -90

# WiFi RSSI settings for HAND_IN test
WIFI_RSSI_FOR_HAND_IN_TEST_PHONE_NOT_HAND_IN = -80
WIFI_RSSI_FOR_HAND_IN_TEST_PHONE_HAND_IN = -50

# WiFi RSSI settings for HAND_OUT test
WIFI_RSSI_FOR_HAND_OUT_TEST_PHONE_NOT_HAND_OUT = -60
WIFI_RSSI_FOR_HAND_OUT_TEST_PHONE_HAND_OUT = -85


class TelLiveConnectivityMonitorMobilityTest(
        TelLiveConnectivityMonitorBaseTest):
    def __init__(self, controllers):
        TelLiveConnectivityMonitorBaseTest.__init__(self, controllers)

        self.attens = {}
        for atten in self.attenuators:
            self.attens[atten.path] = atten
            atten.set_atten(atten.get_max_atten())  # Default all attens to max

    def setup_class(self):
        TelLiveConnectivityMonitorBaseTest.setup_class(self)

        # Do WiFi RSSI calibration.
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MAX_RSSI_RESERVED_VALUE)

        if not ensure_network_generation(
                self.log,
                self.android_devices[0],
                GEN_4G,
                voice_or_data=NETWORK_SERVICE_DATA,
                toggle_apm_after_setting=True):
            self.log.error("Setup_class: phone failed to select to LTE.")
            return False
        if not ensure_wifi_connected(self.log, self.android_devices[0],
                                     self.wifi_network_ssid,
                                     self.wifi_network_pass):
            self.log.error("{} connect WiFI failed".format(
                self.android_devices[0].serial))
            return False
        if (not wait_for_wifi_data_connection(self.log,
                                              self.android_devices[0], True) or
                not verify_http_connection(self.log, self.android_devices[0])):
            self.log.error("No Data on Wifi")
            return False

        # Delay WAIT_TIME_WIFI_RSSI_CALIBRATION_WIFI_CONNECTED after WiFi
        # Connected to make sure WiFi RSSI reported value is correct.
        time.sleep(WAIT_TIME_WIFI_RSSI_CALIBRATION_WIFI_CONNECTED)
        # Turn On Screen and delay WAIT_TIME_WIFI_RSSI_CALIBRATION_SCREEN_ON
        # then get WiFi RSSI to avoid WiFi RSSI report -127(invalid value).
        self.android_devices[0].droid.wakeUpNow()
        time.sleep(WAIT_TIME_WIFI_RSSI_CALIBRATION_SCREEN_ON)

        setattr(self, "wifi_rssi_with_no_atten",
                self.android_devices[0].droid.wifiGetConnectionInfo()['rssi'])
        if self.wifi_rssi_with_no_atten == INVALID_WIFI_RSSI:
            self.log.error(
                "Initial WiFi RSSI calibration value is wrong: -127.")
            return False
        self.log.info("WiFi RSSI calibration info: atten=0, RSSI={}".format(
            self.wifi_rssi_with_no_atten))
        ensure_phones_default_state(self.log, [self.android_devices[0]])

        # Do Cellular RSSI calibration.
        setattr(self, "cell_rssi_with_no_atten",
                self.android_devices[0].droid.telephonyGetSignalStrength()[
                    SignalStrengthContainer.SIGNAL_STRENGTH_LTE_DBM])
        self.log.info(
            "Cellular RSSI calibration info: atten=0, RSSI={}".format(
                self.cell_rssi_with_no_atten))
        return True

    def teardown_class(self):

        TelLiveConnectivityMonitorBase.teardown_class()

        self.android_devices[
            0].droid.telephonyStopTrackingSignalStrengthChange()
        return True

    def teardown_test(self):

        super().teardown_test()
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_strong_cell_strong(self):
        self.log.info("--->Setting WiFi strong cell strong<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_strong_cell_weak(self):
        self.log.info("--->Setting WiFi strong cell weak<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        return True

    def set_wifi_strong_cell_absent(self):
        self.log.info("--->Setting WiFi strong cell absent<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_weak_cell_strong(self):
        self.log.info("--->Setting WiFi weak cell strong<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_weak_cell_weak(self):
        self.log.info("--->Setting WiFi weak cell weak<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        return True

    def set_wifi_weak_cell_absent(self):
        self.log.info("--->Setting WiFi weak cell absent<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G],
                 self.wifi_rssi_with_no_atten, WIFI_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_absent_cell_strong(self):
        self.log.info("--->Setting WiFi absent cell strong<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MAX_RSSI_RESERVED_VALUE)
        return True

    def set_wifi_absent_cell_weak(self):
        self.log.info("--->Setting WiFi absent cell weak<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G],
                 self.cell_rssi_with_no_atten, CELL_WEAK_RSSI_VALUE)
        return True

    def set_wifi_absent_cell_absent(self):
        self.log.info("--->Setting WiFi absent cell absent<---")
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_2G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_WIFI_5G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_3G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        set_rssi(self.log, self.attens[ATTEN_NAME_FOR_CELL_4G], 0,
                 MIN_RSSI_RESERVED_VALUE)
        return True

    """ Tests Begin """

    @test_tracker_info(uuid="d474725b-c34d-4686-8b5f-c0d4733a0cc1")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_call_drop_by_poor_signals(self):
        self.setup_volte()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="volte",
            trigger="set_wifi_absent_cell_absent",
            extra_trigger=None,
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="7f62f1c0-6d9e-4e7e-812f-b1c60d2f4b41")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_call_drop_by_poor_signals(self):
        self.setup_csfb()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="csfb",
            trigger="set_wifi_absent_cell_absent",
            extra_trigger=None,
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="8d1c8c44-be54-43ec-892c-c3f41855c7c8")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_call_drop_by_poor_signal(self):
        self.setup_3g()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="3g",
            trigger="set_wifi_absent_cell_absent",
            extra_trigger=None,
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="66e01cb3-3bea-4d08-9ab4-7f22790c57b1")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_apm_call_drop_by_poor_signal(self):
        self.setup_wfc_apm()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="wfc_apm",
            trigger="set_wifi_absent_cell_absent",
            extra_trigger=None,
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="669e9f97-6931-403a-a13d-4f179bd4406f")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_non_apm_call_drop_by_poor_signal(self):
        self.setup_wfc_non_apm()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="wfc_non_apm",
            trigger="set_wifi_absent_cell_absent",
            extra_trigger=None,
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="c7619788-2357-4c49-a754-50ffaf433d59")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_handover_to_wfc_then_hangup(self):
        self.setup_volte()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_setup_and_connectivity_monitor_checking(
            setup="volte",
            trigger=None,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="c10c8406-6a0c-4039-b2ce-3782593774f2")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_handover_to_wfc_then_hangup(self):
        self.setup_csfb()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_setup_and_connectivity_monitor_checking(
            setup="csfb",
            trigger=None,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="fcb62ea3-3a39-407c-90d8-21896c981ef4")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_handover_to_wfc_then_hangup(self):
        self.setup_3g()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_setup_and_connectivity_monitor_checking(
            setup="3g",
            trigger=None,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="85f32373-d1b2-4763-8812-d7ff43a9b3e6")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_handover_to_volte_then_hangup(self):
        self.setup_volte()
        self.connect_to_wifi()
        self.enable_wfc()
        self.set_wifi_strong_cell_absent()
        return self.call_setup_and_connectivity_monitor_checking(
            setup="volte",
            trigger="set_wifi_absent_cell_strong",
            extra_trigger="set_wifi_strong_cell_strong",
            expected_drop_reason=None,
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="c3dee2ba-1637-4382-97a7-ec9ca795f3dc")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_handover_to_volte_then_call_drop(self):
        self.setup_volte()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_WIFI_PREFERRED)
        return self.call_drop_test(
            setup="volte",
            count=1,
            extra_trigger="set_wifi_absent_cell_strong",
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="90bc318a-b8ba-45c9-8d8f-e642eeb00460")
    @TelephonyBaseTest.tel_test_wrap
    def test_wfc_handover_to_csfb_then_call_drop(self):
        self.setup_csfb()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_WIFI_PREFERRED)
        return self.call_drop_test(
            setup="csfb",
            count=1,
            extra_trigger="set_wifi_absent_cell_absent",
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="0557709e-6d82-4c66-b622-6f36db8bdcc2")
    @TelephonyBaseTest.tel_test_wrap
    def test_volte_handover_to_wfc_then_call_drop(self):
        self.setup_volte()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_drop_test(
            setup="volte",
            count=1,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="3453ed14-8227-4050-96f1-e9ac7973df3b")
    @TelephonyBaseTest.tel_test_wrap
    def test_csfb_handover_to_wfc_then_call_drop(self):
        self.setup_csfb()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_drop_test(
            setup="csfb",
            count=1,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_trouble=None,
            expected_action=None)

    @test_tracker_info(uuid="68cc68db-c60b-4c4a-a974-8e0d1fa211f2")
    @TelephonyBaseTest.tel_test_wrap
    def test_3g_handover_to_wfc_then_call_drop(self):
        self.setup_3g()
        self.connect_to_wifi()
        self.enable_wfc()
        set_wfc_mode(self.log, self.dut, WFC_MODE_CELLULAR_PREFERRED)
        return self.call_drop_test(
            setup="3g",
            count=1,
            extra_trigger="set_wifi_strong_cell_absent",
            expected_trouble=None,
            expected_action=None)


""" Tests End """
