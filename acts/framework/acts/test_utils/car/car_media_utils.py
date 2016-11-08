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

#   Utilities that can be used for testing media related usecases.

# Events dispatched from the RPC Server
EVENT_PLAY_RECEIVED = "playReceived"
EVENT_PAUSE_RECEIVED = "pauseReceived"
EVENT_SKIPNEXT_RECEIVED = "skipNextReceived"
EVENT_SKIPPREV_RECEIVED = "skipPrevReceived"

# Passthrough Commands sent to the RPC Server
CMD_MEDIA_PLAY = "play"
CMD_MEDIA_PAUSE = "pause"
CMD_MEDIA_SKIP_NEXT = "skipNext"
CMD_MEDIA_SKIP_PREV = "skipPrev"


def verifyEventReceived(log, device, event, timeout):
    """
    Verify if the event was received from the given device.
    When a fromDevice talks to a toDevice and expects an event back,
    this util function can be used to see if the toDevice posted it.
    Args:
        log:        The logging object
        device:     The device to pop the event from
        event:      The event we are interested in.
        timeout:    The time in seconds before we timeout
    Returns:
        True        if the event was received
        False       if we timed out waiting for the event
    """
    try:
        device.ed.pop_event(event, timeout)
    except Exception:
        log.info(" {} Event Not received".format(event))
        return False
    log.info("Event Received : {}".format(event))
    return True


def send_media_passthrough_cmd(log,
                               fromDevice,
                               toDevice,
                               cmd,
                               expctEvent,
                               timeout=1.0):
    """
    Send a media passthrough command from one device to another
    via bluetooth.
    Args:
        log:        The logging object
        fromDevice: The device to send the command from
        toDevice:   The device the command is sent to
        cmd:        The passthrough command to send
        expctEvent: The expected event
        timeout:    The time in seconds before we timeout, deafult = 1sec
    Returns:
        True        if the event was received
        False       if we timed out waiting for the event
    """
    log.info("Sending passthru : {}".format(cmd))
    fromDevice.droid.bluetoothMediaPassthrough(cmd)
    if not verifyEventReceived(log, toDevice, expctEvent, timeout):
        return False
    return True
