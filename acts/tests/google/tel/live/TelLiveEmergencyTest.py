#!/usr/bin/env python3.4
#
#   Copyright 2017 - Google
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
from acts import signals
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import CAPABILITY_WFC
from acts.test_utils.tel.tel_defines import DEFAULT_DEVICE_PASSWORD
from acts.test_utils.tel.tel_defines import PHONE_TYPE_CDMA
from acts.test_utils.tel.tel_defines import WFC_MODE_WIFI_PREFERRED
from acts.test_utils.tel.tel_lookup_tables import operator_capabilities
from acts.test_utils.tel.tel_test_utils import abort_all_tests
from acts.test_utils.tel.tel_test_utils import call_setup_teardown
from acts.test_utils.tel.tel_test_utils import dumpsys_last_call_info
from acts.test_utils.tel.tel_test_utils import dumpsys_last_call_number
from acts.test_utils.tel.tel_test_utils import get_operator_name
from acts.test_utils.tel.tel_test_utils import get_service_state_by_adb
from acts.test_utils.tel.tel_test_utils import fastboot_wipe
from acts.test_utils.tel.tel_test_utils import hangup_call_by_adb
from acts.test_utils.tel.tel_test_utils import initiate_call
from acts.test_utils.tel.tel_test_utils import is_sim_lock_enabled
from acts.test_utils.tel.tel_test_utils import initiate_emergency_dialer_call_by_adb
from acts.test_utils.tel.tel_test_utils import reset_device_password
from acts.test_utils.tel.tel_test_utils import toggle_airplane_mode_by_adb
from acts.test_utils.tel.tel_test_utils import unlock_sim
from acts.test_utils.tel.tel_test_utils import verify_internet_connection
from acts.test_utils.tel.tel_test_utils import wait_for_sim_ready_by_adb
from acts.test_utils.tel.tel_voice_utils import phone_setup_csfb
from acts.test_utils.tel.tel_voice_utils import phone_setup_iwlan
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_3g
from acts.test_utils.tel.tel_voice_utils import phone_setup_voice_2g

IMS_FIRST_CMD = (
    "am broadcast -a com.google.android.carrier.action.LOCAL_OVERRIDE -n "
    "com.google.android.carrier/.ConfigOverridingReceiver --ez "
    "carrier_use_ims_first_for_emergency_bool %s")


class TelLiveEmergencyTest(TelephonyBaseTest):
    def __init__(self, controllers):
        TelephonyBaseTest.__init__(self, controllers)
        self.number_of_devices = 1
        fake_number = self.user_params.get("fake_emergency_number", "411")
        self.fake_emergency_number = fake_number.strip("+").replace("-", "")
        self.my_devices = self.android_devices[:]

    def setup_class(self):
        TelephonyBaseTest.setup_class(self)
        for ad in self.android_devices:
            if not is_sim_lock_enabled(ad):
                self.setup_dut(ad)
                return True
        self.log.error("No device meets SIM READY or LOADED requirement")
        raise signals.TestAbortClass("No device meets SIM requirement")

    def setup_dut(self, ad):
        self.dut = ad
        self.dut_operator = get_operator_name(self.log, ad)
        if self.dut_operator == "tmo":
            self.fake_emergency_number = "611"
        elif self.dut_operator == "vzw":
            self.fake_emergency_number = "922"
        elif self.dut_operator == "spt":
            self.fake_emergency_number = "526"
        if (self.dut.droid.telephonyGetPhoneType() == PHONE_TYPE_CDMA):
            self.dut_ecbm = True
        else:
            self.dut_ecbm = False
        if len(self.my_devices) > 1:
            self.android_devices.remove(ad)
            self.android_devices.insert(0, ad)

    def teardown_class(self):
        self.android_devices = self.my_devices
        TelephonyBaseTest.teardown_class(self)

    def setup_test(self):
        if not unlock_sim(self.dut):
            abort_all_tests(self.dut.log, "unable to unlock SIM")
        self.expected_call_result = True

    def teardown_test(self):
        self.dut.ensure_screen_on()
        reset_device_password(self.dut, None)
        self.dut.adb.shell(IMS_FIRST_CMD % "true")

    def change_emergency_number_list(self):
        test_number = "%s:%s" % (self.fake_emergency_number,
                                 self.fake_emergency_number)
        output = self.dut.adb.getprop("ril.test.emergencynumber")
        if output != test_number:
            self.dut.adb.shell(
                "setprop ril.test.emergencynumber %s" % test_number)
        for _ in range(5):
            existing = self.dut.adb.getprop("ril.ecclist")
            self.dut.log.info("Existing ril.ecclist is: %s", existing)
            if self.fake_emergency_number in existing:
                return True
            emergency_numbers = "%s,%s" % (existing,
                                           self.fake_emergency_number)
            cmd = "setprop ril.ecclist %s" % emergency_numbers
            self.dut.log.info(cmd)
            self.dut.adb.shell(cmd)
            # After some system events, ril.ecclist might change
            # wait sometime for it to settle
            time.sleep(10)
            if self.fake_emergency_number in existing:
                return True
        return False

    def change_qcril_emergency_source_mcc_table(self):
        # This will add the fake number into emergency number list for a mcc
        # in qcril. Please note, the fake number will be send as an emergency
        # number by modem and reach the real 911 by this
        qcril_database_path = self.dut.adb.shell("find /data -iname  qcril.db")
        if not qcril_database_path: return
        mcc = self.dut.droid.telephonyGetNetworkOperator()
        mcc = mcc[:3]
        self.dut.log.info("Add %s mcc %s in qcril_emergency_source_mcc_table")
        self.dut.adb.shell(
            "sqlite3 %s \"INSERT INTO qcril_emergency_source_mcc_table VALUES('%s','%s','','')\""
            % (qcril_database_path, mcc, self.fake_emergency_number))

    def fake_emergency_call_test(self, by_emergency_dialer=True, attemps=3):
        self.dut.log.info("ServiceState is in %s",
                          get_service_state_by_adb(self.log, self.dut))
        if by_emergency_dialer:
            dialing_func = initiate_emergency_dialer_call_by_adb
            callee = self.fake_emergency_number
        else:
            dialing_func = initiate_call
            # Initiate_call method has to have "+" in front
            # otherwise the number will be in dialer without dial out
            # with sl4a fascade. Need further investigation
            callee = "+%s" % self.fake_emergency_number
        for i in range(attemps):
            result = True
            if not self.change_emergency_number_list():
                self.dut.log.error("Unable to add number to ril.ecclist")
                return False
            time.sleep(1)
            last_call_number = dumpsys_last_call_number(self.dut)
            dial_result = dialing_func(self.log, self.dut, callee)
            time.sleep(3)
            hangup_call_by_adb(self.dut)
            self.dut.send_keycode("BACK")
            self.dut.send_keycode("BACK")
            for i in range(3):
                if dumpsys_last_call_number(self.dut) > last_call_number:
                    call_info = dumpsys_last_call_info(self.dut)
                    self.dut.log.info("New call info = %s", call_info)
                    break
                else:
                    self.dut.log.error("New call is not in sysdump telecom")
                    if i == 2:
                        result = False
                    time.sleep(5)
            if dial_result == self.expected_call_result:
                self.dut.log.info("Call to %s returns %s as expected", callee,
                                  self.expected_call_result)
            else:
                self.dut.log.info("Call to %s returns %s", callee,
                                  not self.expected_call_result)
                result = False
            if result:
                return True
            reasons = self.dut.search_logcat(
                "qcril_qmi_voice_map_qmi_to_ril_last_call_failure_cause",
                self.begin_time)
            if reasons:
                self.dut.log.info(reasons[-1]["log_message"])
            ecclist = self.dut.adb.getprop("ril.ecclist")
            self.dut.log.info("ril.ecclist = %s", ecclist)
            if self.fake_emergency_number in ecclist:
                if i == attemps - 1:
                    self.dut.log.error("%s is in ril-ecclist, but call failed",
                                       self.fake_emergency_number)
                else:
                    self.dut.log.warning(
                        "%s is in ril-ecclist, but call failed, try again",
                        self.fake_emergency_number)
            else:
                if i == attemps - 1:
                    self.dut.log.error("Fail to write %s to ril-ecclist",
                                       self.fake_emergency_number)
                else:
                    self.dut.log.info("%s is not in ril-ecclist",
                                      self.fake_emergency_number)
        self.dut.log.info("fake_emergency_call_test result is %s", result)
        return result

    def check_emergency_call_back_mode(self,
                                       expected,
                                       by_emergency_dialer=True):
        result = True
        self.log.info("Make fake emergency call and hung up in ringing")
        if by_emergency_dialer:
            initiate_emergency_dialer_call_by_adb(
                self.log, self.dut, self.fake_emergency_number, timeout=0)
        else:
            callee = "+%s" % self.fake_emergency_number
            self.dut.droid.telecomCallNumber(callee)
        time.sleep(3)
        hangup_call_by_adb(self.dut)
        time.sleep(3)
        last_call_number = dumpsys_last_call_number(self.dut)
        if len(self.android_devices) > 1:
            if not call_setup_teardown(
                    self.log,
                    self.dut,
                    self.android_devices[1],
                    ad_hangup=self.dut):
                self.dut.log.error("Regular phone call failed")
                result = False
                reasons = self.dut.search_logcat(
                    "qcril_qmi_voice_map_qmi_to_ril_last_call_failure_cause",
                    self.begin_time)
                if reasons:
                    self.dut.log.info(reasons[-1]["log_message"])
        else:
            initiate_call(self.log, self.dut, "411")
            time.sleep(3)
            hangup_call_by_adb(self.dut)
        for i in range(3):
            if dumpsys_last_call_number(self.dut) > last_call_number:
                call_info = dumpsys_last_call_info(self.dut)
                self.dut.log.info("New call info = %s", call_info)
                if expected:
                    if "ecbm" not in call_info["callProperties"]:
                        self.dut.log.error(
                            "New call not in emergency call back mode.")
                        result = False
                    if verify_internet_connection(
                            self.log, self.dut, expected_state=False):
                        self.dut.log.info("Data connection is off in ECB mode")
                        time.sleep(360)
                        if verify_internet_connection(self.log, self.dut):
                            self.dut.log.info("Data connection comes back "
                                              "after getting out of ECB")
                    else:
                        self.dut.log.error(
                            "Data connection is not off in ECB mode")
                        result = False
                if not expected:
                    if "ecbm" in call_info["callProperties"]:
                        self.dut.log.error(
                            "New call is in emergency call back mode")
                        result = False
                    if not verify_internet_connection(
                            self.log, self.dut, expected_state=True):
                        self.dut.log.error("Data connection is off")
                        result = False
                return result
            elif i == 2:
                self.dut.log.error("New call not in dumpsys telecom")
                return False
            time.sleep(5)
        return result

    """ Tests Begin """

    @test_tracker_info(uuid="fe75ba2c-e4ea-4fc1-881b-97e7a9a7f48e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer(self):
        """Test emergency call with emergency dialer in user account.

        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.fake_emergency_call_test()

    @test_tracker_info(uuid="eb1fa042-518a-4ddb-8e9f-16a6c39c49f1")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer_csfb(self):
        """Test emergency call with emergency dialer in user account.

        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        self.dut.adb.shell(IMS_FIRST_CMD % "false")
        if not phone_setup_csfb(self.log, self.dut):
            return False
        if not self.fake_emergency_call_test():
            return False
        return self.check_emergency_call_back_mode(self.dut_ecbm)

    @test_tracker_info(uuid="7a55991a-adc0-432c-b705-8ac9ee249323")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer_3g(self):
        """Test emergency call with emergency dialer in user account.

        Add a fake emergency number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.
        Verify DUT in emergency call back mode.

        Returns:
            True if success.
            False if failed.
        """
        self.dut.adb.shell(IMS_FIRST_CMD % "false")
        if not phone_setup_voice_3g(self.log, self.dut):
            return False
        if not self.fake_emergency_call_test():
            return False
        return self.check_emergency_call_back_mode(self.dut_ecbm)

    @test_tracker_info(uuid="cc40611b-6fe5-4952-8bdd-c15d6d995516")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer_2g(self):
        """Test emergency call with emergency dialer in user account.

        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.
        Verify DUT in emergency call back mode.

        Returns:
            True if success.
            False if failed.
        """
        if self.dut_operator != "tmo":
            raise signals.TestSkip(
                "2G is not supported for carrier %s" % self.dut_operator)
        self.dut.adb.shell(IMS_FIRST_CMD % "false")
        if not phone_setup_voice_2g(self.log, self.dut):
            return False
        if not self.fake_emergency_call_test():
            return False
        return self.check_emergency_call_back_mode(False)

    @test_tracker_info(uuid="a209864c-93fc-455c-aa81-8d3a83f6ad7c")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer_wfc_apm(self):
        """Test emergency call with emergency dialer in user account.

        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.
        Verify DUT in emergency call back mode.

        Returns:
            True if success.
            False if failed.
        """
        if CAPABILITY_WFC not in operator_capabilities.get(
                self.dut_operator, operator_capabilities["default"]):
            raise signals.TestSkip(
                "WFC is not supported for carrier %s" % self.dut_operator)
        self.dut.adb.shell(IMS_FIRST_CMD % "false")
        if not phone_setup_iwlan(
                self.log, self.dut, True, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            return False
        if not self.fake_emergency_call_test():
            return False
        return self.check_emergency_call_back_mode(False)

    @test_tracker_info(uuid="be654073-0107-4b67-a5df-f25ebec7d93e")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_emergency_dialer_wfc_apm_off(self):
        """Test emergency call with emergency dialer in user account.

        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.
        Verify DUT in emergency call back mode.

        Returns:
            True if success.
            False if failed.
        """
        if CAPABILITY_WFC not in operator_capabilities.get(
                self.dut_operator, operator_capabilities["default"]):
            raise signals.TestSkip(
                "WFC is not supported for carrier %s" % self.dut_operator)
        if self.dut_operator != "tmo":
            raise signals.TestSkip(
                "WFC in non-APM is not supported for carrier %s" %
                self.dut_operator)
        self.dut.adb.shell(IMS_FIRST_CMD % "false")
        if not phone_setup_iwlan(
                self.log, self.dut, False, WFC_MODE_WIFI_PREFERRED,
                self.wifi_network_ssid, self.wifi_network_pass):
            self.dut.log.error("Failed to setup WFC.")
            return False
        if not self.fake_emergency_call_test():
            return False
        return self.check_emergency_call_back_mode(False)

    @test_tracker_info(uuid="8a0978a8-d93e-4f6a-99fe-d0e28bf1be2a")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_by_dialer(self):
        """Test emergency call with dialer.

        Add system emergency number list with storyline number.
        Call storyline by dialer.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        return self.fake_emergency_call_test(by_emergency_dialer=False)

    @test_tracker_info(uuid="2e6fcc75-ff9e-47b1-9ae8-ed6f9966d0f5")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_apm(self):
        """Test emergency call with emergency dialer in airplane mode.

        Enable airplane mode.
        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)

    @test_tracker_info(uuid="469bfa60-6e8f-4159-af1f-ab6244073079")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Add system emergency number list with storyline.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        toggle_airplane_mode_by_adb(self.log, self.dut, False)
        reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
        if not wait_for_sim_ready_by_adb(self.log, self.dut):
            self.dut.log.error("SIM is not ready")
            return False
        self.dut.reboot(stop_at_lock_screen=True)
        if self.fake_emergency_call_test():
            return True
        else:
            return False

    @test_tracker_info(uuid="17401c57-0dc2-49b5-b954-a94dbb2d5ad0")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_screen_lock_apm(self):
        """Test emergency call with emergency dialer in screen lock phase.

        Enable device password and then reboot upto password query window.
        Add system emergency number list with storyline.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            toggle_airplane_mode_by_adb(self.log, self.dut, True)
            reset_device_password(self.dut, DEFAULT_DEVICE_PASSWORD)
            self.dut.reboot(stop_at_lock_screen=True)
            if not wait_for_sim_ready_by_adb(self.log, self.dut):
                self.dut.log.error("SIM is not ready")
                return False
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            toggle_airplane_mode_by_adb(self.log, self.dut, False)

    @test_tracker_info(uuid="ccea13ae-6951-4790-a5f7-b5b7a2451c6c")
    @TelephonyBaseTest.tel_test_wrap
    def test_fake_emergency_call_in_setupwizard(self):
        """Test emergency call with emergency dialer in setupwizard.

        Wipe the device and then reboot upto setupwizard.
        Add system emergency number list with storyline number.
        Use the emergency dialer to call storyline.
        Verify DUT has in call activity.

        Returns:
            True if success.
            False if failed.
        """
        try:
            if not fastboot_wipe(self.dut, skip_setup_wizard=False):
                return False
            if not wait_for_sim_ready_by_adb(self.log, self.dut):
                self.dut.log.error("SIM is not ready")
                return False
            if self.fake_emergency_call_test():
                return True
            else:
                return False
        finally:
            self.dut.exit_setup_wizard()


""" Tests End """
