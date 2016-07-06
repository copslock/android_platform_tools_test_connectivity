#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Test the HFP profile for calling and connection management.
"""

import time

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt import BtEnum
from acts.test_utils.bt import bt_test_utils
from acts.test_utils.car import car_telecom_utils
from acts.test_utils.tel import tel_defines

BLUETOOTH_PKG_NAME = "com.android.bluetooth"
CALL_TYPE_OUTGOING = "CALL_TYPE_OUTGOING"
CALL_TYPE_INCOMING = "CALL_TYPE_INCOMING"
default_timeout = 20

class BtCarHfpConnectionTest(BluetoothBaseTest):

    def setup_class(self):
        # HF : HandsFree (CarKitt role)
        self.hf = self.android_devices[0]
        # AG : Audio Gateway (Phone role)
        self.ag = self.android_devices[1]
        # RE : Remote Device (Phone being talked to role)
        self.re = self.android_devices[2]
        self.ag_phone_number = "tel:{}".format(
            self.ag.droid.telephonyGetLine1Number())
        self.re_phone_number = "tel:{}".format(
            self.re.droid.telephonyGetLine1Number())
        self.log.info("ag tel: {} re tel: {}".format(self.ag_phone_number,
                                                     self.re_phone_number))

        # Setup includes pairing and connecting the devices.
        bt_test_utils.setup_multiple_devices_for_bt_test([self.hf, self.ag])
        bt_test_utils.reset_bluetooth([self.hf, self.ag])

        # Pair and connect the devices.
        if not bt_test_utils.pair_pri_to_sec(self.hf.droid, self.ag.droid):
            self.log.error("Failed to pair")
            return False
        return True

    def setup_test(self):
        self.log.debug(
            bt_test_utils.log_energy_info(self.android_devices, "Start"))
        for d in self.android_devices:
            d.ed.clear_all_events()
        self.hf.droid.bluetoothDisconnectConnected(
            self.ag.droid.bluetoothGetLocalAddress())

    def on_fail(self, test_name, begin_time):
        self.log.debug("Test {} failed.".format(test_name))

    def teardown_test(self):
        self.log.debug(
            bt_test_utils.log_energy_info(self.android_devices, "End"))

    @BluetoothBaseTest.bt_test_wrap
    def test_call_transfer_disconnect_connect(self):
        """
        Tests that after we connect when an active call is in progress,
        we show the call.

        Precondition:
        1. AG & HF are disconnected but paired.

        Steps:
        1. Make a call from AG role (since disconnected)
        2. Accept from RE role and transition the call to Active
        3. Connect AG & HF
        4. HF should transition into Active call state.

        Returns:
          Pass if True
          Fail if False

        Priority: 1
        """
        # make a call on AG
        if not car_telecom_utils.dial_number(self.log, self.ag,
                                             self.re_phone_number):
            self.log.error("AG not in dialing {}".format(
                self.ag.droid.getBuildSerial()))
            return False

        # Wait for both AG and RE to be in ringing
        if not car_telecom_utils.wait_for_dialing(self.log, self.ag):
            self.log.error("AG not in ringing {}".format(
                self.ag.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_ringing(self.log, self.re):
            self.log.error("RE not in ringing {}".format(
                self.re.droid.getBuildSerial()))
            return False

        # Accept the call on RE
        self.re.droid.telecomAcceptRingingCall()

        # Wait for AG, RE to go into an Active state.
        if not car_telecom_utils.wait_for_active(self.log, self.ag):
            self.log.error("AG not in Active {}".format(
                self.ag.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_active(self.log, self.re):
            self.log.error("RE not in Active {}".format(
                self.re.droid.getBuildSerial()))
            return False

        # Now connect the devices.
        if not bt_test_utils.connect_pri_to_sec(
            self.log, self.hf, self.ag.droid,
            set([BtEnum.BluetoothProfile.HEADSET_CLIENT.value])):
            self.log.error("Could not connect HF and AG {} {}".format(
                self.hf.droid.getBuildSerial(), self.ag.droid.getBuildSerial()))
            return False

        # Check that HF is in active state
        if not car_telecom_utils.wait_for_active(self.log, self.hf):
            self.log.error("HF not in Active {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Hangup the call and check all devices are clean
        self.hf.droid.telecomEndCall()
        ret = True
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.hf)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.re)

        return ret

    @BluetoothBaseTest.bt_test_wrap
    def test_call_transfer_off_on(self):
        """
        Tests that after we turn adapter on when an active call is in
        progress, we show the call.

        Precondition:
        1. AG & HF are disconnected but paired.
        2. HF's adapter is OFF

        Steps:
        1. Make a call from AG role (since disconnected)
        2. Accept from RE role and transition the call to Active
        3. Turn HF's adapter ON
        4. HF should transition into Active call state.

        Returns:
          Pass if True
          Fail if False

        Priority: 1
        """
        # Connect HF & AG
        if not bt_test_utils.connect_pri_to_sec(
            self.log, self.hf, self.ag.droid,
            set([BtEnum.BluetoothProfile.HEADSET_CLIENT.value])):
            self.log.error("Could not connect HF and AG {} {}".format(
                self.hf.droid.getBuildSerial(), self.ag.droid.getBuildSerial()))
            return False

        # make a call on AG
        if not car_telecom_utils.dial_number(self.log, self.ag,
                                             self.re_phone_number):
            self.log.error("AG not in dialing {}".format(
                self.ag.droid.getBuildSerial()))
            return False

        # Wait for all HF, AG and RE to be in ringing
        if not car_telecom_utils.wait_for_dialing(self.log, self.hf):
            self.log.error("HF not in ringing {}".format(
                self.hf.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_dialing(self.log, self.ag):
            self.log.error("AG not in ringing {}".format(
                self.ag.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_ringing(self.log, self.re):
            self.log.error("RE not in ringing {}".format(
                self.re.droid.getBuildSerial()))
            return False

        # Accept the call on RE
        self.re.droid.telecomAcceptRingingCall()

        # Wait for all HF, AG, RE to go into an Active state.
        if not car_telecom_utils.wait_for_active(self.log, self.ag):
            self.log.error("AG not in Active {}".format(
                self.hf.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_active(self.log, self.ag):
            self.log.error("AG not in Active {}".format(
                self.ag.droid.getBuildSerial()))
            return False
        if not car_telecom_utils.wait_for_active(self.log, self.re):
            self.log.error("RE not in Active {}".format(
                self.re.droid.getBuildSerial()))
            return False

        # Turn the adapter OFF on HF
        if not bt_test_utils.disable_bluetooth(self.hf.droid):
            self.log.error("Failed to turn BT off on HF {}".format(
                self.hf.droid.getBuildSerial()))
            return False


        # Turn adapter ON on HF
        if not bt_test_utils.enable_bluetooth(self.hf.droid, self.hf.ed):
            self.log.error("Failed to turn BT ON after call on HF {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Check that HF is in active state
        if not car_telecom_utils.wait_for_active(self.log, self.hf):
            self.log.error("HF not in Active {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Hangup the call and check all devices are clean
        self.hf.droid.telecomEndCall()
        ret = True
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.hf)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.re)

        return ret

    @BluetoothBaseTest.bt_test_wrap
    def test_call_transfer_connect_disconnect_connect(self):
        """
        Test that when we go from connect -> disconnect -> connect on an active
        call then the call is restored on HF.

        Precondition:
        1. AG & HF are paired

        Steps:
        0. Connect AG & HF
        1. Make a call from HF role
        2. Accept from RE role and transition the call to Active
        3. Disconnect AG & HF
        4. Verify that we don't have any calls on HF
        5. Connect AG & HF
        6. Verify that HF gets the call back.

        Returns:
          Pass if True
          Fail if False

        Priority: 1
        """
        # Now connect the devices.
        if not bt_test_utils.connect_pri_to_sec(
            self.log, self.hf, self.ag.droid,
            set([BtEnum.BluetoothProfile.HEADSET_CLIENT.value])):
            self.log.error("Could not connect HF and AG {} {}".format(
                self.hf.droid.getBuildSerial(), self.ag.droid.getBuildSerial()))
            return False

        # make a call on HF
        if not car_telecom_utils.dial_number(self.log, self.hf,
                                             self.re_phone_number):
            self.log.error("HF not in dialing {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Wait for HF, AG to be dialing and RE to be ringing
        ret = True
        ret &= car_telecom_utils.wait_for_dialing(self.log, self.hf)
        ret &= car_telecom_utils.wait_for_dialing(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_ringing(self.log, self.re)

        if not ret:
            self.log.error("Outgoing call did not get established")
            return False

        # Accept call on RE.
        self.re.droid.telecomAcceptRingingCall()

        ret &= car_telecom_utils.wait_for_active(self.log, self.hf)
        ret &= car_telecom_utils.wait_for_active(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_active(self.log, self.re)

        if not ret:
            self.log.error("Outgoing call did not transition to active")
            return False

        # Disconnect HF & AG
        self.hf.droid.bluetoothDisconnectConnected(
            self.ag.droid.bluetoothGetLocalAddress())

        # We use the proxy of the Call going away as HF disconnected
        if not car_telecom_utils.wait_for_not_in_call(self.log, self.hf):
            self.log.error("HF still in call after disconnection {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Now connect the devices.
        if not bt_test_utils.connect_pri_to_sec(
            self.log, self.hf, self.ag.droid,
            set([BtEnum.BluetoothProfile.HEADSET_CLIENT.value])):
            self.log.error("Could not connect HF and AG {} {}".format(
                self.hf.droid.getBuildSerial(), self.ag.droid.getBuildSerial()))
            return False

        # Check that HF is in active state
        if not car_telecom_utils.wait_for_active(self.log, self.hf):
            self.log.error("HF not in Active {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Hangup the call and check all devices are clean
        self.hf.droid.telecomEndCall()
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.hf)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_not_in_call(self.log, self.re)

        return ret
