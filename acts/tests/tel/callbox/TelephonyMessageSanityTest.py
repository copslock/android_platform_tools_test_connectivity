#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (C) 2014- The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sanity tests for connectivity tests in telephony
"""

import time
from queue import Empty
from base_test import BaseTestClass

from tel.md8475a import MD8475A
from tel.md8475a import BtsNumber
from tel.md8475a import VirtualPhoneStatus
import tel_utils


class TelephonyMessageSanityTest(BaseTestClass):
    TAG = "TelephonyMessageSanityTest"
    log_path = BaseTestClass.log_path + TAG + '/'

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.tests = (
                   "test_send_sms_lessthan_160",
                   "test_send_sms_morethan_160",
                   "test_receive_sms_lessthan_160",
                   "test_receive_sms_morethan_160",
                   )
        self.anritsu = MD8475A(tel_utils.MD8475A_IP_ADDRESS)

    def setup_test(self):
        self.lte_bts, self.wcdma_bts = tel_utils.set_system_model(self.anritsu,
                                                                  "LTE_WCDMA")
        self.droid.phoneStartTrackingServiceStateChange()
        self.droid.phoneStartTrackingDataConnectionStateChange()
        self.droid.smsStartTrackingIncomingMessage()
        tel_utils.init_phone(self.droid, self.ed)
        self.log.info("Starting Simulation")
        self.anritsu.start_simulation()
        return True

    def teardown_test(self):
        self.droid.phoneStopTrackingServiceStateChange()
        self.droid.phoneStopTrackingDataConnectionStateChange()
        self.droid.smsStopTrackingIncomingMessage()
        self.log.info("Stopping Simulation")
        self.anritsu.stop_simulation()
        # turn off modem
        tel_utils.turn_off_modem(self.droid)

    def teardown_class(self):
        self.anritsu.disconnect()

    def _wait_for_sms_deliver_success(self, time_to_wait=60):
        sms_deliver_event = "onSmsDeliverSuccess"
        sleep_interval = 2
        status = "failed"
        event = None

        try:
            event = self.ed.pop_event(sms_deliver_event, time_to_wait)
            status = "passed"
        except Empty:
            self.log.info("Timeout: Expected event is not received.")
        return status, event

    def _wait_for_sms_sent_success(self, time_to_wait=30):
        sms_sent_event = "onSmsSentSuccess"
        sleep_interval = 2
        status = "failed"
        event = None

        try:
            event = self.ed.pop_event(sms_sent_event, time_to_wait)
            status = "passed"
        except Empty:
            self.log.info("Timeout: Expected event is not received.")
        return status, event

    def _wait_for_incoming_sms(self, time_to_wait=120):
        sms_received_event = "onSmsReceived"
        sleep_interval = 2
        status = "failed"
        event = None

        try:
            event = self.ed.pop_event(sms_received_event, time_to_wait)
            status = "passed"
        except Empty:
            self.log.info("Timeout: Expected event is not received.")
        return status, event

    def _wait_for_bts_state(self, btsnumber, state, timeout=30):
        '''  state value are "IN" and "OUT" '''
        sleep_interval = 2
        wait_time = timeout
        start_time = time.time()
        end_time = start_time + wait_time

        while True:
            if state == btsnumber.service_state:
                break
            if time.time() <= end_time:
                    time.sleep(sleep_interval)
                    wait_time = end_time - time.time()
            else:
                self.log.info("Timeout: Expected state is not received.")
                break

    def _wait_for_vp_state(self, vp_handle, state, timeout=10):
        status = "failed"
        sleep_interval = 1
        wait_time = timeout

        while wait_time > 0:
            if vp_handle.status == state:
                status = "passed"
                break
            time.sleep(sleep_interval)
            wait_time = wait_time - sleep_interval

        if status != "passed":
            self.log.info("Timeout: Expected state is not received.")
        return status

    """ Tests Begin """
    def test_send_sms_lessthan_160(self):
        '''
        Verify sending a SMS with character length less than 160

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. send a SMS with character length less than 160
        '''
        test_status = "failed"
        # turn on modem to start registration
        self.log.info("Turning on Modem")
        tel_utils.turn_on_modem(self.droid)
        self.log.info("Waiting for Network registration")
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # get a handle to virtual phone
        vp = self.anritsu.get_VirtualPhone()
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              20)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            phoneNumber = "+16692269250"
            message = "FromShabeer"
            self.log.info("Sending SMS")
            self.droid.smsSendTextMessage(phoneNumber, message, False)
            self.log.info("Waiting for SMS sent event")
            test_status, event = self._wait_for_sms_sent_success()
            # TODO : Need to check delivery status:
            # Can't automate delivery report from Anritsu as of now
            # self.log.info("Waiting for SMS delivered event")
            # test_status, event = self._wait_for_sms_deliver_success()

        if test_status == "passed":
            self.log.info("Sending SMS (<160): Passed")
            return True
        else:
            self.log.info("Sending SMS (<160): Failed")
            return False

    def test_send_sms_morethan_160(self):
        '''
        Verify sending a SMS with character more than 160

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. send a SMS with character length more than 160
        '''
        test_status = "failed"
        # turn on modem to start registration
        self.log.info("Turning on Modem")
        tel_utils.turn_on_modem(self.droid)
        self.log.info("Waiting for Network registration")
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # get a handle to virtual phone
        vp = self.anritsu.get_VirtualPhone()
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              20)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            phoneNumber = "+16692269250"
            message = ("qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnmqwertyuiopasfgdhjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnm-qwertyuiopasdfghjklzxcvbn"
                       "From Phone")
            self.log.info("Sending SMS")
            self.droid.smsSendTextMessage(phoneNumber, message, False)
            self.log.info("Waiting for SMS sent event")
            test_status, event = self._wait_for_sms_sent_success()
            # TODO : Need to check delivery status:
            # Can't automate delivery report from Anritsu as of now
            # self.log.info("Waiting for SMS delivered event")
            # test_status, event = self._wait_for_sms_deliver_success()

        if test_status == "passed":
            self.log.info("Sending SMS (>160): Passed")
            return True
        else:
            self.log.info("Sending SMS (>160): Failed")
            return False

    def test_receive_sms_lessthan_160(self):
        '''
        Verify receiving a SMS with character length less than 160

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. receive a SMS with character length less than 160
        '''
        test_status = "failed"
        # turn on modem to start registration
        self.log.info("Turning on Modem")
        tel_utils.turn_on_modem(self.droid)
        self.log.info("Waiting for Network registration")
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # get a handle to virtual phone
        vp = self.anritsu.get_VirtualPhone()
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              20)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            phoneNumber = "6692269250"
            message = "FromAnritus"
            vp.sendSms(phoneNumber, message)
            self.log.info("Waiting for incoming SMS")
            test_status, event = self._wait_for_incoming_sms()
            if test_status == "passed":
                self.log.info("Incoming SMS: Sender " + event['data']['Sender'])
                self.log.info("Incoming SMS: Message " + event['data']['Text'])

        if test_status == "passed":
            self.log.info("Receiving SMS (<160) Test: Passed")
            return True
        else:
            self.log.info("Receiving SMS (<160) Test: Failed")
            return False

    def test_receive_sms_morethan_160(self):
        '''
        Verify receiving a SMS with character length more than 160

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. receive a SMS with character length more than 160
        '''
        test_status = "failed"
        # turn on modem to start registration
        self.log.info("Turning on Modem")
        tel_utils.turn_on_modem(self.droid)
        self.log.info("Waiting for Network registration")
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # get a handle to virtual phone
        vp = self.anritsu.get_VirtualPhone()

        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              20)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            phoneNumber = "6692269250"
            message = ("qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnmqwertyuiopasfgdhjklzxcvbnm"
                       "qwertyuiopasdfghjklzxcvbnm-qwertyuiopasdfghjklzxcvbn"
                       "From Anritsu")

            vp.sendSms(phoneNumber, message)

            self.log.info("Waiting for incoming SMS")

            test_status, event = self._wait_for_incoming_sms()
            if test_status == "passed":
                self.log.info("Incoming SMS: Sender " + event['data']['Sender'])
                self.log.info("Incoming SMS: Message " + event['data']['Text'])

        if test_status == "passed":
            self.log.info("Receiving SMS (>160) Test: Passed")
            return True
        else:
            self.log.info("Receiving SMS (>160) Test: Failed")
            return False

    """ Tests End """
