#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- Google, Inc.
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
# The following frequency lists are for US

from queue import Empty
import time

def toggle_airplane_mode(log, droid, ed, new_state=None):
    """ Toggle the state of airplane mode.

    Args:
        droid: Sl4a session to use.
        ed: Event_dispatcher associated with the sl4a session.
        new_state: Airplane mode state to set to.
            If None, opposite of the current state.

    Returns:
        result: True if operation succeed. False if error happens.
    """
    phone_number = droid.getLine1Number()
    cur_state = droid.checkAirplaneMode()
    if cur_state == new_state:
        log.info("Airplane mode already <{}> on {}".format(new_state,
                                                            phone_number))
        return True
    if not new_state:
        new_state = not cur_state
    event_name = None
    if new_state:
        event_name = "onServiceStateChangedPowerOff"
        log.info("Turn on airplane mode: " + phone_number)
    else:
        event_name = "onServiceStateChangedInService"
        log.info("Turn off airplane mode: " + phone_number)
    droid.phoneStartTrackingServiceStateChange()
    ed.clear_all_events()
    droid.toggleAirplaneMode(new_state)
    event = None
    try:
        event = ed.pop_event(event_name, 30)
    except Empty:
        log.exception("Did not get expected " + event_name)
    finally:
        droid.phoneStopTrackingServiceStateChange()
    if new_state:
        if (not droid.checkAirplaneMode() or
            droid.wifiCheckState() or
            droid.bluetoothCheckState()):
            log.error("Airplane mode ON fail")
            return False
    return True

def toggle_call_state(droid, ed_caller, ed_callee, action):
    """Accept incoming call or hangup onging call.

    Args:
        droid: SL4A session.
        ed_caller: Caller event dispatcher.
        ed_callee: Callee event dispatcher.
        action: The to-do action, either be "accept" or "hangup".

    Returns:
        result: True if operation succeed. False if unknow action.
    """
    event = None
    if action == "accept":
        droid.telecomAcceptRingingCall()
        event = "onPreciseStateChangedActive"
    elif action == "hangup":
        droid.telecomEndCall()
        event = "onCallStateChangedIdle"
    else:
        return False
    ed_callee.pop_event(event, 30)
    ed_caller.pop_event(event, 30)
    return True

def initiate_call(log, droid_caller, droid_callee, ed_callee,
                  caller_number, callee_number):
    """Make phone call from caller to callee.

    Args:
        droid_caller: Caller sl4a session.
        droid_callee: Callee sl4a session.
        ed_callee: Callee event dispatcher.
        caller_number: Caller phone number.
        callee_number: Callee phone number.

    Returns:
        result: if phone call is received by callee and ringring successfully.
        """
    result = False
    droid_callee.phoneStartTrackingCallState()
    droid_callee.phoneAdjustPreciseCallStateListenLevel("Ringing", True)
    ed_callee.clear_all_events()
    droid_caller.phoneCallNumber(callee_number)
    event_ringing = None
    event_incoming = None
    try:
        event_ringing = ed_callee.pop_event("onCallStateChangedRinging", 30)
    except Empty:
        log.exception("Did not get expected event")
        log.debug("Call did not get through, end call on both side")
        droid_caller.telecomEndCall()
        droid_callee.telecomEndCall()
    finally:
        droid_callee.phoneStopTrackingCallStateChange()
    if (event_ringing['data']['incomingNumber'] == caller_number):
        result = True
    return result

def call_process(log, droid_caller, droid_callee, droid_hangup, ed_caller,
                 ed_callee, delay_in_call,
                 caller_number=None, callee_number=None, delay_answer=1):
    """ Call process, including make a phone call from caller,
    accept from callee, and hang up.

    In call process, call from <droid_caller> to <droid_callee>,
    after ringring, wait <delay_answer> to accept the call,
    wait <delay_in_call> during the call process,
    then hang up from <droid_hangup>.

    Args:
        droid_caller: Caller Android Object.
        droid_callee: Callee Android Object.
        droid_hangup: Android Object end the phone call.
        ed_callee: Callee event dispatcher.
        delay_in_call: Wait time in call process.
        calller_number: Optional, caller phone number.
            If None, will get number by SL4A.
        callee_number: Optional, callee phone number.
            if None, will get number by SL4A.
        delay_answer: After callee ringring state, wait time before accept.
            If None, default value is 1.

    Returns:
        True if call process without any error.
        Flase if error happened.
    """
    result = False
    if caller_number is None:
        caller_number = droid_caller.getLine1Number()
    if callee_number is None:
        callee_number = droid_callee.getLine1Number()
    log.info("call from {} to {}".format(caller_number, callee_number))
    result = initiate_call(log, droid_caller, droid_callee, ed_callee,
                           caller_number, callee_number)
    droid_callee.phoneStartTrackingCallState()
    droid_callee.phoneAdjustPreciseCallStateListenLevel("Foreground", True)
    droid_caller.phoneStartTrackingCallState()
    droid_caller.phoneAdjustPreciseCallStateListenLevel("Foreground", True)
    ed_callee.clear_all_events()
    ed_caller.clear_all_events()
    if result:
        result = False
        time.sleep(delay_answer)
        #TODO(yangxliu): If delay == 0, accept will fail, need to fix.
        log.info("Accept on " + callee_number)
        toggle_call_state(droid_callee, ed_caller, ed_callee, "accept")
        time.sleep(delay_in_call)
        if (droid_caller.telecomIsInCall() and
            droid_callee.telecomIsInCall()):
            result = True
    if result:
        result = False
        hangup_number = droid_hangup.getLine1Number()
        if hangup_number is None:
            log.info("Hang up")
        else:
            log.info("Hang up on " + hangup_number)
        result = toggle_call_state(droid_hangup, ed_caller, ed_callee, "hangup")
    droid_callee.phoneStopTrackingCallStateChange()
    droid_caller.phoneStopTrackingCallStateChange()
    return result
