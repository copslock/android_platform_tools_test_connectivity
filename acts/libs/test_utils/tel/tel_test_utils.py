#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
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

import android
import random
import string
import time
from queue import Empty
from test_utils.tel.tel_enum import TelEnums
from test_utils.utils import load_config
from test_utils.utils import rand_ascii_str
from test_utils.wifi_test_utils import wifi_toggle_state

class TelTestUtilsError(Exception):
    pass

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
    wait_time_event = 90;
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
        event = ed.pop_events(event_name, wait_time_event)
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
    """Accept incoming call or hangup ongoing call.

    Args:
        droid: SL4A session.
        ed_caller: Caller event dispatcher.
        ed_callee: Callee event dispatcher.
        action: The to-do action, either be "accept" or "hangup".

    Returns:
        result: True if operation succeed. False if unknown action.
    """
    wait_time_event = 30;
    event = None
    if action == "accept":
        droid.telecomAcceptRingingCall()
        event = "onPreciseStateChangedActive"
    elif action == "hangup":
        droid.telecomEndCall()
        event = "onCallStateChangedIdle"
    else:
        return False
    try:
        ed_callee.pop_event(event, wait_time_event)
        ed_caller.pop_event(event, wait_time_event)
    except Empty:
        if action == "accept" and not droid.telecomIsInCall():
            raise TelTestUtilsError("Accept call failed.")
        elif action == "hangup" and droid.telecomIsInCall():
            raise TelTestUtilsError("Hangup call failed.")
    return True

def check_phone_number_match(number1, number2):
    """Check whether two input phone numbers match or not.

    Compare the two input phone numbers.
    If they match, return True; otherwise, return False.
    Currently only handle phone number with the following formats:
        (US phone number format)
        +1abcxxxyyyy
        1abcxxxyyyy
        abcxxxyyyy
        abc xxx yyyy
        abc.xxx.yyyy
        abc-xxx-yyyy

    Args:
        number1: 1st phone number to be compared.
        number2: 2nd phone number to be compared.

    Returns:
        True if two phone numbers match. Otherwise False.
    """
    # Remove "1"  or "+1"from front
    if number1[0] == "1":
        number1 = number1[1:]
    elif number1[0:2] == "+1":
        number1 = number1[2:]
    if number2[0] == "1":
        number2 = number2[1:]
    elif number2[0:2] == "+1":
        number2 = number2[2:]
    # Remove white spaces, dashes, dots
    number1 = number1.replace(" ","").replace("-","").replace(".","")
    number2 = number2.replace(" ","").replace("-","").replace(".","")
    return number1 == number2

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
        result: if phone call is received by callee and ringing successfully.
        """
    wait_time_event = 30
    droid_callee.phoneStartTrackingCallState()
    droid_callee.phoneAdjustPreciseCallStateListenLevel("Ringing", True)
    ed_callee.clear_all_events()
    droid_caller.phoneCallNumber(callee_number)
    event_ringing = None
    try:
        event_ringing = ed_callee.pop_event("onCallStateChangedRinging",
                                            wait_time_event)
    except Empty:
        log.exception("Did not get expected ringing event")
        log.debug("Call did not get through, end call on both side")
        droid_caller.telecomEndCall()
        droid_callee.telecomEndCall()
    finally:
        droid_callee.phoneStopTrackingCallStateChange()
    if not event_ringing:
        return False
    result = check_phone_number_match(event_ringing['data']['incomingNumber'],
                                    caller_number)
    if not result:
        log.error("Expected number:{}, actual number:{}".
                  format(caller_number,
                         event_ringing['data']['incomingNumber']))
    return result

def call_process(log, droid_caller, droid_callee, ed_caller, ed_callee,
                 delay_in_call,
                 caller_number=None, callee_number=None, delay_answer=1,
                 hangup=False, droid_hangup=None,
                 verify_call_mode_caller=False, verify_call_mode_callee=False,
                 caller_mode_VoLTE=None, callee_mode_VoLTE=None):
    """ Call process, including make a phone call from caller,
    accept from callee, and hang up.

    In call process, call from <droid_caller> to <droid_callee>,
    after ringing, wait <delay_answer> to accept the call,
    wait <delay_in_call> during the call process,
    (optional)then hang up from <droid_hangup>.

    Args:
        droid_caller: Caller Android Object.
        droid_callee: Callee Android Object.
        ed_caller: Caller event dispatcher.
        ed_callee: Callee event dispatcher.
        delay_in_call: Wait time in call process.
        caller_number: Optional, caller phone number.
            If None, will get number by SL4A.
        callee_number: Optional, callee phone number.
            if None, will get number by SL4A.
        delay_answer: After callee ringing state, wait time before accept.
            If None, default value is 1.
        hangup: Whether hangup in this function.
            Optional. Default value is False.
        droid_hangup: Android Object end the phone call.
            Optional. Default value is None.
        verify_call_mode_caller: Whether verify caller call mode (VoLTE or CS).
            Optional. Default value is False, not verify.
        verify_call_mode_callee: Whether verify callee call mode (VoLTE or CS).
            Optional. Default value is False, not verify.
        caller_mode_VoLTE: If verify_call_mode_caller is True,
            this is expected caller mode. True for VoLTE mode. False for CS mode.
            Optional. Default value is None.
        callee_mode_VoLTE: If verify_call_mode_callee is True,
            this is expected callee mode. True for VoLTE mode. False for CS mode.
            Optional. Default value is None.

    Returns:
        True if call process without any error.
        False if error happened.

    Raises:
        TelTestUtilsError if VoLTE check fail.
    """
    result = False
    if not caller_number:
        caller_number = droid_caller.getLine1Number()
    if not callee_number:
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
        # TODO(yangxliu): If delay == 0, accept will fail, need to fix.
        log.info("Accept on " + callee_number)
        toggle_call_state(droid_callee, ed_caller, ed_callee, "accept")
        time.sleep(delay_in_call)
        if (droid_caller.telecomIsInCall() and
            droid_callee.telecomIsInCall()):
            result = True
    if verify_call_mode_caller:
        network_type = get_network_type(droid_caller, "voice")
        if caller_mode_VoLTE and network_type != "lte":
            raise TelTestUtilsError("Error: Caller not in VoLTE. Expected VoLTE. Type:{}".
                                    format(network_type))
            return False
        if not caller_mode_VoLTE and network_type == "lte":
            raise TelTestUtilsError("Error: Caller in VoLTE. Expected not VoLTE. Type:{}".
                                    format(network_type))
            return False
    if verify_call_mode_callee:
        network_type = get_network_type(droid_callee, "voice")
        if callee_mode_VoLTE and network_type != "lte":
            raise TelTestUtilsError("Error: Callee not in VoLTE. Expected VoLTE. Type:{}".
                                    format(network_type))
            return False
        if not callee_mode_VoLTE and network_type == "lte":
            raise TelTestUtilsError("Error: Callee in VoLTE. Expected not VoLTE.. Type:{}".
                                    format(network_type))
            return False
    if not hangup:
        return True
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
    if not result:
        for droid in [droid_caller, droid_callee]:
            if droid.telecomIsInCall():
                droid.telecomEndCall()
    return result

def verify_internet_connection_type(log, droid, type):
    """Return if phone is connected to Internet and by specific type.

    Args:
        log: Log object.
        droid: SL4A session.
        type: Expected connection type. Either "MOBILE" or "WIFI".

    Returns:
        True if current active connection is connected to Internet and by <type>.
        False if not connected or type is not matched.
    """
    # Add delay here to make sure networkIsConnected will return correct value.
    # In network switch from WiFi to Mobile:
    # there is a time delay (less than 0.1 second) between
    # <connection status become to CONNECTED> and
    # <networkIsConnected become to True>
    # So add this delay to make sure the state transit time won't fail this case.
    time.sleep(0.1)
    result_internet = droid.networkIsConnected()
    if not result_internet:
        log.error("Internet not connected.")
        return False
    network_type = droid.networkGetActiveConnectionTypeName()
    if ((type == "WIFI" and network_type == "WIFI") or
        (type == "MOBILE" and
         (network_type == "Cellular" or network_type == "MOBILE"))):
        return True
    else:
        log.error("NetworkType:{}. Expected:{}".format(network_type, type))
        return False

def verify_http_connection(droid, url="http://www.google.com/"):
    """Make http request and return status.

    Make http request to url. If response message is "OK", return True;
    otherwise, return False.

    Args:
        droid: SL4A session.
        url: Optional. The http request will be made to this URL.
            Default Value is "http://www.google.com/".

    Raises:
        TelTestUtilsError if response is not "OK".
    """
    resp = droid.httpPing(url)
    if resp != "OK":
        raise TelTestUtilsError("Verify http connection failed.")

def wait_for_data_connection_status(log, droid, ed, state):
    """Wait for data connection status to be expected value.

    Wait for the data connection status to be "DATA_CONNECTED"
        or "DATA_DISCONNECTED".

    Args:
        log: Log object.
        droid: SL4A session.
        ed: Event dispatcher.
        state: Expected status: True or False.
            If True, it will wait for status to be "DATA_CONNECTED".
            If False, it will wait for status ti be "DATA_DISCONNECTED".

    Returns:
        True if success.
        False if failed.
    """
    current_state = droid.getDataConnectionState()
    result_internet = droid.networkIsConnected()
    if ((current_state == "DATA_CONNECTED" and state and result_internet) or
        (current_state == "DATA_DISCONNECTED" and not state)):
        log.debug("Expected state and current state is same, return directly.")
        return True
    event_name = None
    if state:
        event_name = "onDataConnectionStateChangedConnected"
    else:
        event_name = "onDataConnectionStateChangedDisconnected"
    try:
        event = ed.pop_event(event_name, 60)
    except Empty:
        log.debug("No expected event.")
        data_state = droid.getDataConnectionState()
        if ((state and data_state == "DATA_CONNECTED") or
            (not state and data_state == "DATA_DISCONNECTED")):
            return True
        else:
            return False
    log.debug("Expected event arrived, function return.")
    return True

def toggle_wifi_verify_data_connection(log, droid, ed, wifi_ON):
    """Toggle wifi status, verify data connection and internet connection.

    If wifi_ON is false, toggle wifi off, verify data connection on mobile,
    verify internet connection OK.
    If wifi_ON if true, toggle wifi on, verify data connection on wifi,
    verify internet connection OK.

    Args:
        log: Log object.
        droid: SL4A session.
        ed: Event dispatcher.
        wifi_ON: Wifi Status.
    """
    result = False
    wifi_state = wifi_ON
    mobile_state = not wifi_ON
    ed.clear_all_events()
    wifi_toggle_state(droid, ed, wifi_state)
    assert wait_for_data_connection_status(log, droid, ed, mobile_state)
    if wifi_ON:
        result = verify_internet_connection_type(log, droid, "WIFI")
    else:
        result = verify_internet_connection_type(log, droid, "MOBILE")
    assert result, "Failed in verify connection type."
    # Add delay to wait for the connection status to propagate in system,
    # so 'verify http' will not give wrong result.
    # TODO(yangxliu): Use SL4A event to replace hard coded wait time.
    time.sleep(0.5)
    verify_http_connection(droid)

def verify_incall_state(log, droids, expected_status):
    """Verify phones in incall state or not.

    Verify if all phones in the array <droids> are in <expected_status>.

    Args:
        log: Log object.
        droids: Array of SL4A sessions. All droid in this array will be tested.
        expected_status: If True, verify all Phones in incall state.
            If False, verify all Phones not in incall state.

    Raises:
        TelTestUtilsError if at least one phone not in expected status.
    """
    result = True
    for droid in droids:
        if droid.telecomIsInCall() is not expected_status:
            log.error("Not in expected status:{}".format(droid.getLine1Number()))
            result = False
    if not result:
        raise TelTestUtilsError("Not all Phones in expected status.")

def verify_active_call_number(droid, expected_number):
    """Verify the number of current active call.

    Verify if the number of current active call in <droid> is
        equal to <expected_number>.

    Args:
        droid: SL4A session.
        expected_number: Expected active call number.
    """
    calls = droid.telecomPhoneGetCallIds()
    if calls is None:
        actual_number = 0
    else:
        actual_number = len(calls)
    assert actual_number == expected_number, ("Expected:{}, Actual:{}".
                                              format(expected_number,
                                                     actual_number))

def toggle_volte(droid, new_state=None):
    """Toggle enable/disable VoLTE.

    Args:
        droid: SL4A session.
        new_state: VoLTE mode state to set to.
            True for enable, False for disable.
            If None, opposite of the current state.

    Raises:
        TelTestUtilsError if platform does not support VoLTE.
    """
    if not droid.imsIsEnhanced4gLteModeSettingEnabledByPlatform():
        raise TelTestUtilsError("VoLTE not supported by platform.")
    current_state = droid.imsIsEnhanced4gLteModeSettingEnabledByUser()
    if new_state is None:
        new_state = not current_state
    if new_state == current_state:
        return
    droid.imsSetAdvanced4gMode(new_state)

def set_preferred_network_type(droid, network_type):
    """Set preferred network type.

    Args:
        droid: SL4A session.
        network_type: Network type string. For example, "3G", "LTE", "2G".

    Raises:
        TelTestUtilsError if type is not supported.
    """
    if network_type == droid.phoneGetPreferredNetworkTypeString():
        return
    if not droid.phoneSetPreferredNetworkType(network_type):
        raise TelTestUtilsError("Type:{} is not supported on this phone: {}.".
                                format(network_type,droid))

def wait_for_droid_in_network_type(log, droids, max_time, network_type,
                                   voice_or_data="data"):
    """Wait for droid to be in certain connection mode (e.g. lte, 3g).

    Args:
        log: log object.
        droids: array of SL4A session.
        max_time: max number of seconds to wait (each droid in the droids list).
        network_type: expected connection network type. e.g. lte, 3g, 2g.
        voice_or_data: check droid's voice network type or data network type.
            Optional, default value is "data"

    Raise:
        TelTestUtilsError if droid not in expected network type when time out.
    """
    # TODO(yangxliu): replace loop time wait with SL4A event.
    fail= False
    for droid in droids:
        operator_name = get_operator_name(droid)
        network_type_string = TelEnums.network_type_name[voice_or_data][operator_name][network_type]
        while get_network_type(droid, voice_or_data) != network_type_string:
            time.sleep(1)
            max_time = max_time - 1
            if max_time <= 0:
                fail = True
                log.error("{}, expected:{}, actual:{}.".
                          format(droid, network_type_string,
                                 get_network_type(droid, voice_or_data)))
                break
    if fail:
        raise TelTestUtilsError("Not all droids in expected mode.")

def get_phone_number(droid,simconf):
    """Get phone number from simcard config JSON object.

    Args:
        droid: SL4A session.
        simconf: JSON object loaded from sim config file.

    Returns:
        Phone number.
    """
    number = None
    try:
        number = simconf[droid.getSimSerialNumber()]["phone_num"]
    except KeyError:
        number = droid.getLine1Number()
    return number

def get_operator_name(droid):
    """Get operator name (e.g. vzw, tmo) of droid.

    Args:
        droid: SL4A session.

    Returns:
        Operator name.
    """
    try:
        result = TelEnums.operator_id_to_name[droid.getSimOperator()]
    except KeyError:
        result = "unknown"
    return result

def sms_send_receive_verify(log, droid_tx, droid_rx,
                            phonenumber_tx, phonenumber_rx,
                            ed_tx, ed_rx, length):
    """Send SMS, receive SMS, and verify content and sender's number.

        Send SMS from droid_tx to droid_rx, with <length> characters random string.
        Verify SMS is sent, delivered and received.
        Verify received content and sender's number are correct.

    Args:
        log: Log object.
        droid_tx: Sender's SL4A session.
        droid_rx: Receiver's SL4A session.
        phonenumber_tx: Sender's phone number.
        phonenumber_rx: Receiver's phone number.
        ed_tx: Sender's event dispatcher.
        ed_rx: Receiver's event dispatcher.
        length: Length of message.
    """
    wait_time_sent_success = 60
    wait_time_receive = 120
    log.info("Sending SMS {} to {}, len {}".
             format(phonenumber_tx, phonenumber_rx, length))
    result = False
    droid_rx.smsStartTrackingIncomingMessage()
    text = rand_ascii_str(length)
    droid_tx.smsSendTextMessage(phonenumber_rx, text, True)
    event = None
    ed_tx.pop_event("onSmsSentSuccess", wait_time_sent_success)
    event = ed_rx.pop_event("onSmsReceived", wait_time_receive)
    if (check_phone_number_match(event['data']['Sender'], phonenumber_tx) and
        event['data']['Text'] == text):
        result = True
    else:
        log.error("Received message error.")
        log.error("Expected sender:" + phonenumber_tx)
        log.error("Received sender:" + event['data']['Sender'])
        log.error("Expected text:" + text)
        log.error("Received text:" + event['data']['Text'])
        result = False
    droid_rx.smsStopTrackingIncomingMessage()
    assert result, "Failed in verify receiving SMS."

def get_network_type(droid, voice_or_data):
    """Get current network type (Voice network type, or data network type)

    Args:
        droid: SL4A session.
        voice_or_data: Input parameter indicating to get voice network type or
            data network type.

    Returns:
        Current voice/data network type.
    """
    if voice_or_data == "voice":
        return droid.getVoiceNetworkType()
    elif voice_or_data == "data":
        return droid.getDataNetworkType()
    else:
        return droid.getNetworkType()