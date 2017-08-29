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
    Test Script for Project Fi Setting
"""

import time
import os
import re
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.TelephonyBaseTest import TelephonyBaseTest
from acts.test_utils.tel.tel_defines import CARRIER_SPT
from acts.test_utils.tel.tel_defines import CARRIER_TMO
from acts.test_utils.tel.tel_defines import CARRIER_USCC
from acts.test_utils.tel.tel_defines import MAX_WAIT_TIME_NW_SELECTION
from acts.test_utils.tel.tel_lookup_tables import operator_name_from_plmn_id
from acts.test_utils.tel.tel_test_utils import send_dialer_secret_code

_CARRIER_DIALER_CODE_LOOKUP = {
    CARRIER_SPT: '34777',
    CARRIER_TMO: '34866',
    CARRIER_USCC: '34872'
}

_SWITCHING_PREF_FILE = (
    '/data/data/com.google.android.apps.tycho/shared_prefs/switching.xml')


class TelLiveProjectFiTest(TelephonyBaseTest):
    def setup_class(self):
        pass

    def get_active_carrier(self, ad):
        """Gets the active carrier profile value from the device.

        Args:
            ad: An AndroidDevice Object.

        Returns:
            (string) A key from the CARRIER_TO_MCC_MNC map representing the
            active carrier.

        Raises:
            KeyError: when an mcc_mnc code reported by the device is not a
            recognized Fi partner carrier.
        """
        mcc_mnc = ad.droid.telephonyGetSimOperator()
        if not mcc_mnc:
            return "UNKNOWN"
        try:
            return operator_name_from_plmn_id(mcc_mnc)
        except KeyError:
            ad.log.error('Unknown Mobile Country Code/Mobile Network Code %s',
                         mcc_mnc)
        raise

    def set_active_carrier(self,
                           ad,
                           carrier,
                           timeout=MAX_WAIT_TIME_NW_SELECTION,
                           check_interval=10):
        """Requests an active carrier to be set on the device sim.

        If switching to a different carrier, after the switch is completed
        auto-switching will be disabled. To re-enable, call enable_auto_switching.

        Args:
            ad: An AndroidDevice Object.
            carrier: (carrier_constants.Carrier) Which carrier to switch to.
            timeout: (optional -- integer) the number of seconds in which a
                     switch should be completed.

        Raises:
            Error: whenever a device is not set to the desired carrier within
                   the timeout window.
        """
        # If there's no need to switch, then don't.
        max_time = timeout
        while max_time >= 0:
            if self.is_ready_to_make_carrier_switch(ad):
                break
            time.sleep(check_interval)
            max_time -= check_interval
        else:
            ad.log.error("Device stays in carrier switch lock state")
            return False
        old_carrier = self.get_active_carrier(ad)
        if carrier == old_carrier:
            ad.log.info('Already on %s, so no need to switch', carrier)
            return True

        # Start switch on device, using events to verify that the switch starts.
        ad.log.info('Initiating unsolicited switch from %s to %s.',
                    old_carrier, carrier)
        send_dialer_secret_code(ad, _CARRIER_DIALER_CODE_LOOKUP[carrier])
        return self.wait_for_carrier_switch_completed(
            ad, carrier, timeout=timeout, check_interval=check_interval)

    def is_switching_silent(self, ad):
        """Checks if Tycho switching controller is in silent mode.

        Note that silent mode is a sign of airplane mode, not of a switching lock.

        Args: ad: An AndroidDevice Object.

        Returns:
            A Boolean True if the preferences file reports True, False otherwise.
        """
        return "isInSilentMode\" value=\"true" in ad.adb.shell(
            "cat %s | grep isInSilentMode" % _SWITCHING_PREF_FILE,
            ignore_status=True)

    def is_switching_locked(self, ad):
        """Checks if Tycho switching controller is locked.

        Args: ad: An AndroidDevice Object.

        Returns:
            A Boolean True if the switching controller is locked for any reason,
            False otherwise.
        """
        return "switchingInProgress\" value=\"true" in ad.adb.shell(
            "cat %s | grep switchingInProgress" % _SWITCHING_PREF_FILE)

    def is_ready_to_make_carrier_switch(self, ad):
        """Checks if device is ready to make carrier switch.

        Args:
            ad: An AndroidDevice Object.

        Returns:
             A Boolean True if it is ready to make switch, False otherwise.
        """
        # Check Tycho switching controller states.
        if self.is_switching_silent(ad):
            ad.log.info(
                "Cannot make carrier switch: SwitchingController is in silent "
                "mode!")
            return False
        if self.is_switching_locked(ad):
            ad.log.info(
                "Cannot make carrier switch: SwitchingController is locked!")
            return False
        if self.is_carrier_switch_in_progress(ad):
            ad.log.info("Cannot make carrier switch: Switch in progress!")
            return False
        return True

    def is_carrier_switch_in_progress(self, ad):
        """Checks if Tycho says that a switch is currently in progress.

        Args:
            ad: An AndroidDevice Object.

        Returns:
             A Boolean True if the preferences file reports True, False otherwise.
        """
        switching_preferences = ad.adb.shell("cat %s" % _SWITCHING_PREF_FILE)
        return 'InProgress\" value=\"true' in switching_preferences

    def wait_for_carrier_switch_completed(self,
                                          ad,
                                          carrier,
                                          timeout=MAX_WAIT_TIME_NW_SELECTION,
                                          check_interval=10):
        """Wait for carrier switch to complete.

        This function waits for a carrier switch to complete by monitoring the
        Tycho switching controller preference file.

        Args:
            ad: An Android device object.
            carrier: The target carrier network to switch to.
            timeout: (integer) Time wait for switch to complete.

        Return:
            True or False for successful/unsuccessful switch.
        """
        while timeout >= 0:
            if self.get_active_carrier(ad) == carrier and (
                    not self.is_carrier_switch_in_progress(ad)):
                ad.log.info("Switched to %s", carrier)
                return True
            time.sleep(check_interval)
            timeout -= check_interval
        ad.log.error("Carrier is %s. Fail to switch to %s",
                     self.get_active_carrier(ad), carrier)
        return False

    def network_switch_test(self, carrier):
        result = True
        for ad in self.android_devices:
            if not self.set_active_carrier(ad, carrier):
                ad.log.error("Failed to switch to %s", carrier)
                result = False
        return result

    """ Tests Begin """

    @test_tracker_info(uuid="6bfbcc1d-e318-4964-bf36-5b82f086860d")
    @TelephonyBaseTest.tel_test_wrap
    def test_switch_to_tmobile_network(self):
        """Test switch to tmobile network.

        Returns:
            True if success.
            False if failed.
        """
        return self.network_switch_test(CARRIER_TMO)

    @test_tracker_info(uuid="4f27944d-f3c5-423d-b0c5-5c66dbb98376")
    @TelephonyBaseTest.tel_test_wrap
    def test_switch_to_sprint_network(self):
        """Test switch to tmobile network.

        Returns:
            True if success.
            False if failed.
        """
        return self.network_switch_test(CARRIER_SPT)

    @test_tracker_info(uuid="5f30c9bd-b79e-4805-aa46-7855ed9023f0")
    @TelephonyBaseTest.tel_test_wrap
    def test_switch_to_uscc_network(self):
        """Test switch to tmobile network.

        Returns:
            True if success.
            False if failed.
        """
        return self.network_switch_test(CARRIER_USCC)


""" Tests End """
