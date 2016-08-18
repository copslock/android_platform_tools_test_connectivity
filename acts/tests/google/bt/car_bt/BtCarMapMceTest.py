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
Automated tests for the testing send and receive SMS commands in MAP profile.
"""

import time
import queue

import acts
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt import bt_test_utils
from acts.test_utils.bt import BtEnum
from acts.test_utils.tel.tel_defines import EventSmsReceived
from acts.test_utils.tel.tel_defines import EventSmsSentSuccess
from acts.test_utils.tel.tel_defines import EventSmsDeliverSuccess
EVENTMAPMESSAGERECEIVED = "MapMessageReceived"
TIMEOUT = 2000
MESSAGE_TO_SEND = "Don't text and Drive!"

SEND_FAILED_NO_MCE = 1
SEND_FAILED_NO_NETWORK = 2


class BtCarMapMceTest(BluetoothBaseTest):
    def setup_class(self):
        self.log.info("Setting up class")
        # MAP roles
        self.MCE = self.android_devices[0]
        self.MSE = self.android_devices[1]
        self.REMOTE = self.android_devices[1]

        # Reset bluetooth
        bt_test_utils.reset_bluetooth([self.MCE])

        # Pair and connect the devices.
        if not bt_test_utils.pair_pri_to_sec(self.MCE.droid, self.MSE.droid):
            self.log.error("Failed to pair")
            return False
        return True

    def setup_test(self):
        for d in self.android_devices:
            d.ed.clear_all_events()

    def teardown_test(self):
        self.toggle_airplane_mode(self.MSE, False)
        self.toggle_airplane_mode(self.MCE, False)

    def on_fail(self, test_name, begin_time):
        #Don't reset Bluetooth...
        return

    def toggle_airplane_mode(self, device, state):
        device.droid.connectivityToggleAirplaneMode(state)
        countdown = 15
        while countdown and not (
                device.droid.connectivityCheckAirplaneMode() == state):
            time.sleep(1)
            countdown -= 1
        return

    def message_delivered(self, device):
        try:
            self.MCE.ed.pop_event(EventSmsDeliverSuccess, 15)
        except queue.Empty:
            self.log.info("Message failed to be delivered.")
            return False
        return True

    def send_message(self, remotes):
        self.REMOTE.droid.smsStartTrackingIncomingSmsMessage()
        destinations = []
        for phone in remotes:
            destinations.append("tel:{} ".format(
                phone.droid.telephonyGetLine1Number()))
        self.log.info(destinations)
        self.MCE.droid.mapSendMessage(
            self.MSE.droid.bluetoothGetLocalAddress(), destinations,
            MESSAGE_TO_SEND)
        try:
            self.MCE.ed.pop_event(EventSmsSentSuccess, 15)
        except queue.Empty:
            self.log.info("Message failed to send.")
            return False

        try:
            receivedMessage = self.REMOTE.ed.pop_event(EventSmsReceived, 15)
            self.log.info("Received a message: {}".format(
                receivedMessage['data']['Text']))
        except queue.Empty:
            self.log.info("Remote did not receive message.")
            return False

        if MESSAGE_TO_SEND != receivedMessage['data']['Text']:
            self.log.error("Messages don't match")
            self.log.error("Sent     {}".format(MESSAGE_TO_SEND))
            self.log.error("Received {}".format(receivedMessage['data']['Text']))
            return False
        return True

    def test_send_message(self):
        bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        return self.send_message([self.REMOTE])

    def test_receive_message(self):
        bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        self.log.info("start Tracking SMS")
        self.MSE.droid.smsStartTrackingIncomingSmsMessage()
        self.log.info("Ready to send")
        self.REMOTE.droid.smsSendTextMessage(
            self.MSE.droid.telephonyGetLine1Number(), "test_receive_message",
            False)
        self.log.info("Check inbound Messages")
        receivedMessage = self.MCE.ed.pop_event(EVENTMAPMESSAGERECEIVED, 15)
        self.log.info(receivedMessage['data'])
        return True

    def test_send_message_failure_no_cellular(self):
        self.toggle_airplane_mode(self.MSE, True)
        bt_test_utils.reset_bluetooth([self.MSE])
        bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        return not self.send_message([self.REMOTE])

    def test_send_message_failure_no_map_connection(self):
        return not self.send_message([self.REMOTE])

    def test_send_message_failure_no_bluetooth(self):
        self.toggle_airplane_mode(self.MCE, True)
        try:
            bt_test_utils.connect_pri_to_sec(
                self.log, self.MCE, self.MSE.droid,
                set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        except acts.controllers.android.SL4AAPIError:
            self.log.info("Failed to connect as expected")
        return not self.send_message([self.REMOTE])

    def test_disconnect_failure_send_message(self):
        connected = bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        disconnected = bt_test_utils.disconnect_pri_from_sec(
            self.log, self.MCE, self.MSE.droid,
            [BtEnum.BluetoothProfile.MAP_MCE.value])
        self.log.info("Connected = {}, Disconnected = {}".format(connected,
                                                                 disconnected))
        return connected and disconnected and not self.send_message([self.REMOTE])

    def manual_test_send_message_to_contact(self):
        bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        contacts = self.MCE.droid.contactsGetContactIds()
        self.log.info(contacts)
        selected_contact = self.MCE.droid.contactsDisplayContactPickList()
        if selected_contact:
            return self.MCE.droid.mapSendMessage(
                self.MSE.droid.bluetoothGetLocalAddress(),
                selected_contact['data'], "Don't Text and Drive!")
        return False

    def test_send_message_to_multiple_phones(self):
        bt_test_utils.connect_pri_to_sec(
            self.log, self.MCE, self.MSE.droid,
            set([BtEnum.BluetoothProfile.MAP_MCE.value]))
        return self.send_message([self.REMOTE, self.REMOTE])
