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

import queue
from acts import asserts

# arbitrary timeout for events
EVENT_TIMEOUT = 10


def wait_for_event(ad, event_name, message=None):
  """Wait for the specified event or timeout.

  Args:
    ad: The android device
    event_name: The event to wait on
    message: Optional message to print out on error (should include '%s' for the
    event name)
  Returns:
    The event (if available)
  """
  try:
    event = ad.ed.pop_event(event_name, EVENT_TIMEOUT)
    ad.log.info('%s: %s', event_name, event['data'])
    return event
  except queue.Empty:
    if message is None:
      message = "Timed out while waiting for %s"
    ad.log.info(message % event_name)
    asserts.fail(event_name)


def fail_on_event(ad, event_name, message=None):
  """Wait for a timeout period and looks for the specified event - fails if it
  is observed.

  Args:
    ad: The android device
    event_name: The event to wait for (and fail on its appearance)
    message: Optional message to print out on error (should include 2 '%s'
    place-holders for the event name and the event data)
  """
  try:
    event = ad.ed.pop_event(event_name, EVENT_TIMEOUT)
    if message is None:
      message = "Received unwanted %s: %s"
    ad.log.info(message, event_name, event['data'])
    asserts.fail(event_name, extras=event)
  except queue.Empty:
    ad.log.info('%s not seen (as expected)', event_name)
    return
