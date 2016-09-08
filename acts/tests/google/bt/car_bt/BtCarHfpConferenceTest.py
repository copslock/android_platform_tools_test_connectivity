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
Test the HFP profile for conference calling functionality.
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

class BtCarHfpConferenceTest(BluetoothBaseTest):
    def setup_class(self):
        self.hf = self.android_devices[0]
        self.ag = self.android_devices[1]
        self.re1 = self.android_devices[2]
        self.re2 = self.android_devices[3]
        self.ag_phone_number = "tel:{}".format(
            self.ag.droid.telephonyGetLine1Number())
        self.re1_phone_number = "tel:{}".format(
            self.re1.droid.telephonyGetLine1Number())
        self.re2_phone_number = "tel:{}".format(
            self.re2.droid.telephonyGetLine1Number())
        self.log.info("ag tel: {} re1 tel: {} re2 tel {}".format(
            self.ag_phone_number, self.re2_phone_number, self.re2_phone_number))

        # Setup includes pairing and connecting the devices.
        bt_test_utils.setup_multiple_devices_for_bt_test([self.hf, self.ag])
        bt_test_utils.reset_bluetooth([self.hf, self.ag])

        # Pair and connect the devices.
        if not bt_test_utils.pair_pri_to_sec(self.hf.droid, self.ag.droid):
            self.log.error("Failed to pair")
            return False

        # Connect the devices now, try twice.
        attempts = 2
        connected = False
        while attempts > 0 and not connected:
            connected = bt_test_utils.connect_pri_to_sec(
                self.log, self.hf, self.ag.droid,
                set([BtEnum.BluetoothProfile.HEADSET_CLIENT.value]))
            self.log.info("Connected {}".format(connected))
            attempts -= 1
        return connected

    #@BluetoothTest(UUID=a9657693-b534-4625-bf91-69a1d1b9a943)
    @BluetoothBaseTest.bt_test_wrap
    def test_multi_way_call_accept(self):
        """
        Tests if we can have a 3-way calling between RE1, RE2 and AG/HF.

        Precondition:
        1. Devices are connected over HFP.

        Steps:
        1. Make a call from RE1 to AG
        2. Wait for dialing on RE1 and ringing on HF/AG.
        3. Accept the call on HF
        4. Make a call on RE2 to AG
        5. Wait for dialing on RE1 and ringing on HF/AG.
        6. Accept the call on HF.
        7. See that HF/AG have one active and one held call.
        8. Merge the call on HF.
        9. Verify that we have a conference call on HF/AG.
        10. Hangup the call on HF.
        11. Wait for all devices to go back into stable state.

        Returns:
          Pass if True
          Fail if False

        Priority: 0
        """
        # Dial AG from RE1
        car_telecom_utils.dial_number(self.log, self.re1, self.ag_phone_number)

        # Wait for dialing/ringing
        ret = True
        ret &= car_telecom_utils.wait_for_dialing(self.log, self.re1)
        ret &= car_telecom_utils.wait_for_ringing(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_ringing(self.log, self.hf)

        if not ret:
            self.log.error("Failed to dial incoming number from")
            return False

        # Extract the call.
        call_1 = car_telecom_utils.get_calls_in_states(
            self.log, self.hf, [tel_defines.CALL_STATE_RINGING])
        if len(call_1) != 1:
            self.log.info("Call State in ringing failed {}".format(
                call_1))
            return False

        # Accept the call on HF
        if not car_telecom_utils.accept_call(
            self.log, self.hf, call_1[0]):
            self.log.info("Accepting call failed {}".format(
                self.hf.droid.getBuildSerial()))
            return False

        # Dial another call from RE2
        car_telecom_utils.dial_number(self.log, self.re2, self.ag_phone_number)

        # Wait for dialing/ringing
        ret &= car_telecom_utils.wait_for_dialing(self.log, self.re2)
        ret &= car_telecom_utils.wait_for_ringing(self.log, self.ag)
        ret &= car_telecom_utils.wait_for_ringing(self.log, self.hf)

        if not ret:
            self.log.error("Failed to dial second incoming number from")
            return False

        # Extract the call.
        call_2 = car_telecom_utils.get_calls_in_states(
            self.log, self.hf, [tel_defines.CALL_STATE_RINGING])
        if len(call_2) != 1:
            self.log.info("Call State in ringing failed {}".format(
                call_2))
            return False

        # Accept the call on HF
        if not car_telecom_utils.accept_call(
            self.log, self.hf, call_2[0]):
            self.log.info("Accepting call failed {} {}".format(
                calls_in_ringing, self.hf.droid.getBuildSerial()))
            return False

        # Merge the calls now.
        self.hf.droid.telecomCallJoinCallsInConf(call_1[0], call_2[0])

        # Check if we are in conference with call_1 and call_2
        conf_call_id = car_telecom_utils.wait_for_conference(
            self.log, self.hf, [call_1[0], call_2[0]])
        if conf_call_id == None:
            self.log.error("Did not get the conference setup correctly")
            return False

        # Now hangup the conference call.
        if not car_telecom_utils.hangup_conf(self.log, self.hf, conf_call_id):
            self.log.error("Could not hangup conference call {} droid {}!".format(
                conf_call_id, self.hf.droid.getBuildSerial()))
            return False

        return True
