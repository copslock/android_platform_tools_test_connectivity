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
Sanity tests for voice tests in telephony
"""
import time
from queue import Empty
from base_test import BaseTestClass

from tel.md8475a import MD8475A
from tel.md8475a import BtsNumber
from tel.md8475a import BtsTechnology
from tel.md8475a import BtsServiceState
from tel.md8475a import TriggerMessageIDs
from tel.md8475a import TriggerMessageReply
from tel.md8475a import BtsAccessClassBarred
from tel.md8475a import VirtualPhoneStatus
import tel_utils


class TelephonyVoiceSanityTest(BaseTestClass):
    TAG = "TelephonyVoiceSanityTest"
    log_path = BaseTestClass.log_path + TAG + '/'

    def __init__(self, controllers):
        BaseTestClass.__init__(self, self.TAG, controllers)
        self.tests = (
                    "test_mo_voice_call_phone_hangup",
                    "test_mo_voice_call_remote_hangup",
                    "test_mt_voice_call_phone_hangup",
                    "test_mt_voice_call_remote_hangup",
                    "test_mo_voice_call_nw_info_check_ltewcdma",
                    "test_mt_voice_call_nw_info_check_ltewcdma",
                    )
        self.anritsu = MD8475A(tel_utils.MD8475A_IP_ADDRESS)

    def setup_test(self):
        self.lte_bts, self.wcdma_bts = tel_utils.set_system_model(self.anritsu,
                                                                  "LTE_WCDMA")
        tel_utils.init_phone(self.droid, self.ed)
        self.droid.phoneStartTrackingServiceStateChange()
        self.droid.phoneStartTrackingDataConnectionStateChange()
        self.droid.phoneStartTrackingCallState()
        self.droid.phoneAdjustPreciseCallStateListenLevel("Foreground", True)
        self.droid.phoneAdjustPreciseCallStateListenLevel("Ringing", True)
        # get a handle to virtual phone
        self.vp = self.anritsu.get_VirtualPhone()
        self.vp.auto_answer = ("ON", 5)
        self.vp.id = "16692269250"
        self.log.info("Starting Simulation")
        self.anritsu.start_simulation()
        return True

    def teardown_test(self):
        self.droid.phoneStopTrackingServiceStateChange()
        self.droid.phoneStopTrackingCallStateChange()
        self.droid.phoneStopTrackingDataConnectionStateChange()
        self.log.info("Stopping Simulation")
        self.anritsu.stop_simulation()
        # turn off modem
        tel_utils.turn_off_modem(self.droid)

    def teardown_class(self):
        self.anritsu.disconnect()

    def _wait_for_call_state(self, state, time_to_wait=15):
        status = "failed"
        event = None

        if state == "IDLE":
            call_state_event = "onCallStateChangedIdle"
        elif state == "OFFHOOK":
            call_state_event = "onCallStateChangedOffhook"
        elif state == "RINGING":
            call_state_event = "onCallStateChangedRinging"
        else:
            self.log.info("Wrong state value.")
            return status, event

        try:
            event = self.ed.pop_event(call_state_event, time_to_wait)
            status = "passed"
        except Empty:
            self.log.info("Timeout: Expected event is not received")
        return status, event

    def _wait_for_precisecall_state(self, state, time_to_wait=20):
        status = "failed"
        event = None

        if state == "ACTIVE":
            precise_state_event = "onPreciseStateChangedActive"
        elif state == "HOLDING":
            precise_state_event = "onPreciseStateChangedHolding"
        elif state == "DIALING":
            precise_state_event = "onPreciseStateChangedDialing"
        elif state == "ALERTING":
            precise_state_event = "onPreciseStateChangedAlerting"
        elif state == "INCOMING":
            precise_state_event = "onPreciseStateChangedIncoming"
        elif state == "WAITING":
            precise_state_event = "onPreciseStateChangedWaiting"
        elif state == "DISCONNECTED":
            precise_state_event = "onPreciseStateChangedDisconnected"
        elif state == "DISCONNECTING":
            precise_state_event = "onPreciseStateChangedDisconnecting"
        elif state == "IDLE":
            precise_state_event = "onPreciseStateChangedIdle"
        else:
            self.log.info("Wrong state value.")
            return status, event

        try:
            event = self.ed.pop_event(precise_state_event, time_to_wait)
            status = "passed"
        except Empty:
            self.log.info("Timeout: Expected event is not received")
        return status, event

    def _wait_for_bts_state(self, btsnumber, state, timeout=30):
        #  state value are "IN" and "OUT"
        status = "failed"
        sleep_interval = 2
        wait_time = timeout

        while wait_time > 0:
            if state == btsnumber.service_state:
                print(btsnumber.service_state)
                status = "passed"
                break
            time.sleep(sleep_interval)
            wait_time = wait_time - sleep_interval

        if status != "passed":
            self.log.info("Timeout: Expected state is not received.")
        return status

    def _wait_for_vp_state(self, vp_handle, state, timeout=10):
        status = "failed"
        sleep_interval = 1
        wait_time = timeout

        while wait_time > 0:
            if vp_handle.status == state:
                self.log.info(vp_handle.status)
                status = "passed"
                break
            time.sleep(sleep_interval)
            wait_time = wait_time - sleep_interval

        if status != "passed":
            self.log.info("Timeout: Expected state is not received.")
        return status

    def _wait_for_return_to_lte(self, timeout=60):
        # wait some time for the device to return to LTE(After CSFB)
        status = "failed"
        sleep_interval = 1
        wait_time = timeout

        while wait_time > 0:
            bts_number, rat_info = self.anritsu.get_camping_cell()
            if rat_info == BtsTechnology.LTE.value:
                status = "passed"
                break
            time.sleep(sleep_interval)
            wait_time = wait_time - sleep_interval

        if status != "passed":
            self.log.info("Timeout: Expected state is not received.")
        return status

    """ Tests Begin """
    def test_mo_voice_call_phone_hangup(self):
        '''
        Test ID: TEL-CS-01
        MO Call verification (Hangup at Phone)

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. Make a MO call, Answer the call at otherside
        3. disconnect the call from Phone
        3. verify the different call states- DIALING, ALERTING, ACTIVE, IDLE
        '''
        test_status = "failed"
        # turn on modem to start registration
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
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Making MO Call")
            self.droid.phoneCallNumber("1111111111")
            self.log.info("Waiting for call state: OFFHOOK")
            test_status, event = self._wait_for_call_state("OFFHOOK", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: DIALING")
            test_status, event = self._wait_for_precisecall_state("DIALING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ALERTING")
            test_status, event = self._wait_for_precisecall_state("ALERTING",
                                                                  45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for Call to be answered at remote")
            # check Virtual phone answered the call
            test_status = self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)
            self.log.info("Disconnecting the call from Phone")
            self.droid.telecomEndCall()
            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_call_state("IDLE")

        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE)
        # wait some time for the device to return to LTE if UE was camped on
        # LTE before call.Failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-01: MO Call verification"
                          " (Hangup at Phone): Passed")
            return True
        else:
            self.log.info("TEL-CS-01: MO Call verification:"
                          " (Hangup at Phone): Failed")
            return False

    def test_mo_voice_call_remote_hangup(self):
        '''
        Test ID: TEL-CS-01
        MO Call verification (Hangup at Remote)

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. Make a MO call, Answer the call at otherside
        3. disconnect the call from Phone
        3. verify the different call states- DIALING, ALERTING, ACTIVE, IDLE
        '''
        test_status = "failed"
        # turn on modem to start registration
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
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              20)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Making MO Call")
            self.droid.phoneCallNumber("111111111")
            self.log.info("Waiting for call state: OFFHOOK")
            test_status, event = self._wait_for_call_state("OFFHOOK", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: DIALING")
            test_status, event = self._wait_for_precisecall_state("DIALING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ALERTING")
            test_status, event = self._wait_for_precisecall_state("ALERTING",
                                                                  45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for Call to be answered at remote")
            # check Virtual phone answered the call
            test_status = self._wait_for_vp_state(self.vp,
                              VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)
            self.log.info("Disconnecting the call from Remote")
            self.vp.set_voice_on_hook()
            self.log.info("Waiting for call state: DISCONNECTED")
            test_status, event = self._wait_for_precisecall_state(
                                                        "DISCONNECTED")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_call_state("IDLE")

        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE,
                                20)
        # wait some time for the device to return to LTE(After CSFB)
        # failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-01: MO Call verification"
                          " (Hangup at Remote)): Passed")
            return True
        else:
            self.log.info("TEL-CS-01: MO Call verification:"
                          " (Hangup at Remote): Failed")
            return False

    def test_mt_voice_call_phone_hangup(self):
        '''
        Test ID: TEL-CS-02
        MT Call verification (Hangup at Phone)

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. Receive a call, Answer the call at Phone
        3. disconnect the call from Phone
        3. verify the different call states- DIALING, ALERTING, ACTIVE, IDLE
        '''
        test_status = "failed"
        # turn on modem to start registration
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
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Receive MT Call - Making a call to the"
                          " phone from remote")
            # This sleep is required.Sometimes Anritsu box doesn't behave as
            # expected in executing the commands send to it without this delay.
            # May be it is in state transition.so the test doesn't proceed.
            # hence introduced this delay.
            time.sleep(10)
            self.vp.set_voice_off_hook()
            self.log.info("Waiting for call state: RINGING")
            test_status, event = self._wait_for_call_state("RINGING", 45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: INCOMING")
            test_status, event = self._wait_for_precisecall_state("INCOMING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # wait for some time before answering the call at Phone side
            time.sleep(10)
            self.log.info("answer the incoming call")
            self.droid.telecomAcceptRingingCall()
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # check Virtual phone call status
            test_status = self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)
            self.log.info("Disconnecting the call from Phone")
            self.droid.telecomEndCall()
            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_call_state("IDLE")

        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE,
                                20)
        # wait some time for the device to return to LTE(After CSFB)
        # failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-02: MT Call verification"
                          " (Hangup at Phone)): Passed")
            return True
        else:
            self.log.info("TEL-CS-02: MT Call verification:"
                          " (Hangup at Phone): Failed")
            return False

    def test_mt_voice_call_remote_hangup(self):
        '''
        Test ID: TEL-CS-02
        MT Call verification (Hangup at Remote)

        Steps
        -----
        1. Get the device is IN_SERVICE state
        2. Receive a call, Answer the call at Phone
        3. disconnect the call from remote side
        3. verify the different call states- DIALING, ALERTING, ACTIVE, IDLE
        '''
        test_status = "failed"
        # turn on modem to start registration
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
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Receive MT Call - Making a call to the"
                          " phone from remote")
            # This sleep is required.Sometimes Anritsu box doesn't behave as
            # expected in executing the commands send to it without this delay.
            # May be it is in state transition.so the test doesn't proceed.
            # hence introduced this delay.
            time.sleep(10)
            self.vp.set_voice_off_hook()
            self.log.info("Waiting for call state: RINGING")
            test_status, event = self._wait_for_call_state("RINGING", 45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: INCOMING")
            test_status, event = self._wait_for_precisecall_state("INCOMING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # wait for some time before answering the call at Phone side
            time.sleep(10)
            self.log.info("answer the incoming call")
            self.droid.telecomAcceptRingingCall()
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # check Virtual phone call status
            test_status = self._wait_for_vp_state(self.vp,
                               VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)
            self.log.info("Disconnecting the call from Remote")
            self.vp.set_voice_on_hook()
            self.log.info("Waiting for call state: DISCONNECTED")
            test_status, event = self._wait_for_precisecall_state(
                                                               "DISCONNECTED")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_precisecall_state("IDLE")

        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE,
                                20)
        # wait some time for the device to return to LTE(After CSFB)
        # failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-02: MT Call verification"
                          " (Hangup at Remote)): Passed")
            return True
        else:
            self.log.info("TEL-CS-02: MT Call verification:"
                          " (Hangup at Remote): Failed")
            return False

    def test_mo_voice_call_nw_info_check_ltewcdma(self):
        '''
        Test ID: TEL-CS-04
        Network State during Phone call (LTE and WCDMA)

        Steps
        -----
        1. Get the device is IN_SERVICE state in LTE
        2. Make a MO call.
        3. check for network state(should indicate Network as WCDMA and
           data connected)
        4. Answer the call at otherside
        5. disconnect the call from Phone
        6. check for network state(should indicate Network as LTE and
           data connected)
        '''

        test_status = "failed"

        # This is to make sure that device camps on LTE first
        self.wcdma_bts.service_state = BtsServiceState.SERVICE_STATE_OUT
        # turn on modem to start registration
        tel_utils.turn_on_modem(self.droid)
        expected_nwtype = "LTE"
        self.log.info("Waiting for Network registration in " + expected_nwtype)
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log,
                                                                expected_nwtype)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # This sleep is required.Sometimes Anritsu box doesn't behave as
        # expected in executing the commands send to it without this delay.
        # May be it is in state transition.so the test doesn't proceed.
        # hence introduced this delay.
        time.sleep(5)
        self.wcdma_bts.service_state = BtsServiceState.SERVICE_STATE_IN
        # Wait for BTS to come to IN state
        self._wait_for_bts_state(self.wcdma_bts, "IN", 120)
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Making MO Call")
            self.droid.phoneCallNumber("111111111")
            self.log.info("Waiting for call state: OFFHOOK")
            test_status, event = self._wait_for_call_state("OFFHOOK", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: DIALING")
            test_status, event = self._wait_for_precisecall_state("DIALING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            expected_nwtype = "UMTS"
            self.log.info("Waiting for service state: IN_SERVICE in "
                          + expected_nwtype)
            test_status, event = tel_utils.wait_for_network_state(self.ed,
                                                                self.log,
                                                                "IN_SERVICE",
                                                                90,
                                                                expected_nwtype)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ALERTING")
            test_status, event = self._wait_for_precisecall_state("ALERTING",
                                                                  45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for Call to be answered at remote")
            # check Virtual phone answered the call
            test_status = self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)
            self.log.info("Disconnecting the call from Phone")
            self.droid.telecomEndCall()
            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_call_state("IDLE")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            expected_nwtype = "LTE"
            self.log.info("Waiting for service state: IN_SERVICE in "
                          + expected_nwtype)
            test_status, event = tel_utils.wait_for_network_state(self.ed,
                                                                self.log,
                                                                "IN_SERVICE",
                                                                90,
                                                                expected_nwtype)
        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE,
                                20)
        # wait some time for the device to return to LTE(After CSFB)
        # failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-04: Network state change during"
                          " MO call: Passed")
            return True
        else:
            self.log.info("TEL-CS-04: Network state change during"
                          " MO call: Failed")
            return False

    def test_mt_voice_call_nw_info_check_ltewcdma(self):
        '''
        Test ID: TEL-CS-04
        Network State during Phone call (LTE and WCDMA)

        Steps
        -----
        1. Get the device is IN_SERVICE state in LTE
        2. Make a MO call.
        3. check for network state(should indicate Network as WCDMA and
           data connected)
        4. Answer the call at otherside
        5. disconnect the call from Phone
        6. check for network state(should indicate Network as LTE and
           data connected)
        '''

        test_status = "failed"

        # This is to make sure that device camps on LTE first
        self.wcdma_bts.service_state = BtsServiceState.SERVICE_STATE_OUT
        # turn on modem to start registration
        tel_utils.turn_on_modem(self.droid)
        expected_nwtype = "LTE"
        self.log.info("Waiting for Network registration in " + expected_nwtype)
        test_status, event = tel_utils.wait_for_network_registration(self.ed,
                                                                self.anritsu,
                                                                self.log,
                                                                expected_nwtype)
        self.log.info("Waiting for data state: DATA_CONNECTED")
        test_status, event = tel_utils.wait_for_data_state(self.ed,
                                                           self.log,
                                                           "DATA_CONNECTED",
                                                           120)

        # This sleep is required.Sometimes Anritsu box doesn't behave as
        # expected in executing the commands send to it without this delay.
        # May be it is in state transition.so the test doesn't proceed.
        # hence introduced this delay.
        time.sleep(5)
        self.wcdma_bts.service_state = BtsServiceState.SERVICE_STATE_IN
        # Wait for BTS to come to IN state
        self._wait_for_bts_state(self.wcdma_bts, "IN", 60)
        # Make sure virtual phone is in IDLE state
        test_status = self._wait_for_vp_state(self.vp,
                                              VirtualPhoneStatus.STATUS_IDLE,
                                              30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            self.log.info("Receive MT Call")
            self.vp.set_voice_off_hook()
            self.log.info("Waiting for call state: RINGING")
            test_status, event = self._wait_for_call_state("RINGING", 45)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            self.log.info("Waiting for call state: INCOMING")
            test_status, event = self._wait_for_precisecall_state("INCOMING")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            expected_nwtype = "UMTS"
            self.log.info("Waiting for service state: IN_SERVICE in "
                          + expected_nwtype)
            test_status, event = tel_utils.wait_for_network_state(self.ed,
                                                                self.log,
                                                                "IN_SERVICE",
                                                                90,
                                                                expected_nwtype)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"
            # wait for before answering the call at Phone side
            time.sleep(10)
            self.droid.telecomAcceptRingingCall()
            self.log.info("Waiting for call state: ACTIVE")
            test_status, event = self._wait_for_precisecall_state("ACTIVE", 30)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            self.log.info("Waiting for Call to be answered at remote")
            # check Virtual phone answered the call
            test_status = self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_VOICECALL_INPROGRESS)

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            # This sleep is Call active time. required for to keep the
            # call in active state for some time
            time.sleep(20)

            self.log.info("Disconnecting the call from Phone")
            self.droid.telecomEndCall()

            self.log.info("Waiting for call state: IDLE")
            test_status, event = self._wait_for_call_state("IDLE")

        # proceed with next step only if previous step is success
        if test_status == "passed":
            test_status = "failed"

            expected_nwtype = "LTE"
            self.log.info("Waiting for service state: IN_SERVICE in "
                          + expected_nwtype)
            test_status, event = tel_utils.wait_for_network_state(self.ed,
                                                                self.log,
                                                                "IN_SERVICE",
                                                                90,
                                                                expected_nwtype)
        # Make sure virtual phone is in IDLE state
        self._wait_for_vp_state(self.vp,
                                VirtualPhoneStatus.STATUS_IDLE,
                                20)
        # wait some time for the device to return to LTE(After CSFB)
        # failure to do so is not a problem in this test case
        self._wait_for_return_to_lte()

        if test_status == "passed":
            self.log.info("TEL-CS-04: Network state change during "
                          "MT call: Passed")
            return True
        else:
            self.log.info("TEL-CS-04: Network state change during"
                          " MT call: Failed")
            return False

    """ Tests End """
