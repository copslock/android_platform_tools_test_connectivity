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

import base64
import queue
from acts import asserts

# arbitrary timeout for events
EVENT_TIMEOUT = 10


def decorate_event(event_name, id):
  return "%s_%d" % (event_name, id)

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
      message = 'Timed out while waiting for %s'
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
      message = 'Received unwanted %s: %s'
    ad.log.info(message, event_name, event['data'])
    asserts.fail(event_name, extras=event)
  except queue.Empty:
    ad.log.info('%s not seen (as expected)', event_name)
    return

def encode_list(list_of_objects):
  """Converts the list of strings or bytearrays to a list of b64 encoded
  bytearrays.

  A None object is treated as a zero-length bytearray.

  Args:
    list_of_objects: A list of strings or bytearray objects
  Returns: A list of the same objects, converted to bytes and b64 encoded.
  """
  encoded_list = []
  for obj in list_of_objects:
    if obj is None:
      obj = bytes()
    if isinstance(obj, str):
      encoded_list.append(base64.b64encode(bytes(obj, 'utf-8')).decode("utf-8"))
    else:
      encoded_list.append(base64.b64encode(obj).decode("utf-8"))
  return encoded_list

def decode_list(list_of_b64_strings):
  """Converts the list of b64 encoded strings to a list of bytearray.

  Args:
    list_of_b64_strings: list of strings, each of which is b64 encoded array
  Returns: a list of bytearrays.
  """
  decoded_list = []
  for str in list_of_b64_strings:
    decoded_list.append(base64.b64decode(str))
  return decoded_list

def assert_equal_strings(first, second, msg=None, extras=None):
  """Assert equality of the string operands - where None is treated as equal to
  an empty string (''), otherwise fail the test.

  Error message is "first != second" by default. Additional explanation can
  be supplied in the message.

  Args:
      first, seconds: The strings that are evaluated for equality.
      msg: A string that adds additional info about the failure.
      extras: An optional field for extra information to be included in
              test result.
  """
  if first == None:
    first = ''
  if second == None:
    second = ''
  asserts.assert_equal(first, second, msg, extras)
