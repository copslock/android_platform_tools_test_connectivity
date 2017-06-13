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
import json
import queue
import statistics
from acts import asserts

# arbitrary timeout for events
EVENT_TIMEOUT = 10


def decorate_event(event_name, id):
  return '%s_%d' % (event_name, id)


def wait_for_event(ad, event_name, timeout=EVENT_TIMEOUT):
  """Wait for the specified event or timeout.

  Args:
    ad: The android device
    event_name: The event to wait on
    timeout: Number of seconds to wait
  Returns:
    The event (if available)
  """
  prefix = ''
  if hasattr(ad, 'pretty_name'):
    prefix = '[%s] ' % ad.pretty_name
  try:
    event = ad.ed.pop_event(event_name, timeout)
    ad.log.info('%s%s: %s', prefix, event_name, event['data'])
    return event
  except queue.Empty:
    ad.log.info('%sTimed out while waiting for %s', prefix, event_name)
    asserts.fail(event_name)

def wait_for_event_with_keys(ad, event_name, timeout=EVENT_TIMEOUT, *keyvalues):
  """Wait for the specified event contain the key/value pairs or timeout

  Args:
    ad: The android device
    event_name: The event to wait on
    timeout: Number of seconds to wait
    keyvalues: (kay, value) pairs
  Returns:
    The event (if available)
  """
  def filter_callbacks(event, keyvalues):
    for keyvalue in keyvalues:
      key, value = keyvalue
      if event['data'][key] != value:
        return False
    return True

  prefix = ''
  if hasattr(ad, 'pretty_name'):
    prefix = '[%s] ' % ad.pretty_name
  try:
    event = ad.ed.wait_for_event(event_name, filter_callbacks, timeout,
                                 keyvalues)
    ad.log.info('%s%s: %s', prefix, event_name, event['data'])
    return event
  except queue.Empty:
    ad.log.info('%sTimed out while waiting for %s (%s)', prefix, event_name,
                keyvalues)
    asserts.fail(event_name)

def fail_on_event(ad, event_name, timeout=EVENT_TIMEOUT):
  """Wait for a timeout period and looks for the specified event - fails if it
  is observed.

  Args:
    ad: The android device
    event_name: The event to wait for (and fail on its appearance)
  """
  prefix = ''
  if hasattr(ad, 'pretty_name'):
    prefix = '[%s] ' % ad.pretty_name
  try:
    event = ad.ed.pop_event(event_name, timeout)
    ad.log.info('%sReceived unwanted %s: %s', prefix, event_name, event['data'])
    asserts.fail(event_name, extras=event)
  except queue.Empty:
    ad.log.info('%s%s not seen (as expected)', prefix, event_name)
    return


def verify_no_more_events(ad, timeout=EVENT_TIMEOUT):
  """Verify that there are no more events in the queue.
  """
  prefix = ''
  if hasattr(ad, 'pretty_name'):
    prefix = '[%s] ' % ad.pretty_name
  should_fail = False
  try:
    while True:
      event = ad.ed.pop_events('.*', timeout, freq=0)
      ad.log.info('%sQueue contains %s', prefix, event)
      should_fail = True
  except queue.Empty:
    if should_fail:
      asserts.fail('%sEvent queue not empty' % prefix)
    ad.log.info('%sNo events in the queue (as expected)', prefix)
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
      encoded_list.append(base64.b64encode(bytes(obj, 'utf-8')).decode('utf-8'))
    else:
      encoded_list.append(base64.b64encode(obj).decode('utf-8'))
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


def construct_max_match_filter(max_size):
  """Constructs a maximum size match filter that fits into the 'max_size' bytes.

  Match filters are a set of LVs (Length, Value pairs) where L is 1 byte. The
  maximum size match filter will contain max_size/2 LVs with all Vs (except
  possibly the last one) of 1 byte, the last V may be 2 bytes for odd max_size.

  Args:
    max_size: Maximum size of the match filter.
  Returns: an array of bytearrays.
  """
  mf_list = []
  num_lvs = max_size // 2
  for i in range(num_lvs - 1):
    mf_list.append(bytes([i]))
  if (max_size % 2 == 0):
    mf_list.append(bytes([255]))
  else:
    mf_list.append(bytes([254, 255]))
  return mf_list


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


def get_aware_capabilities(ad):
  """Get the Wi-Fi Aware capabilities from the specified device. The
  capabilities are a dictionary keyed by aware_const.CAP_* keys.

  Args:
    ad: the Android device
  Returns: the capability dictionary.
  """
  return json.loads(ad.adb.shell('cmd wifiaware state_mgr get_capabilities'))

def get_wifi_mac_address(ad):
  """Get the Wi-Fi interface MAC address as a upper-case string of hex digits
  without any separators (e.g. ':').

  Args:
    ad: Device on which to run.
  """
  return ad.droid.wifiGetConnectionInfo()['mac_address'].upper().replace(
      ':', '')

def extract_stats(ad, data, results, key_prefix, log_prefix):
  """Extract statistics from the data, store in the results dictionary, and
  output to the info log.

  Args:
    ad: Android device (for logging)
    data: A list containing the data to be analyzed.
    results: A dictionary into which to place the statistics.
    key_prefix: A string prefix to use for the dict keys storing the
                extracted stats.
    log_prefix: A string prefix to use for the info log.
    include_data: If True includes the raw data in the dictionary,
                  otherwise just the stats.
  """
  num_samples = len(data)
  results['%snum_samples' % key_prefix] = num_samples

  if not data:
    return

  data_min = min(data)
  data_max = max(data)
  data_mean = statistics.mean(data)

  results['%smin' % key_prefix] = data_min
  results['%smax' % key_prefix] = data_max
  results['%smean' % key_prefix] = data_mean
  results['%sraw_data' % key_prefix] = data

  if num_samples > 1:
    data_stdev = statistics.stdev(data)
    results['%sstdev' % key_prefix] = data_stdev
    ad.log.info('%s: num_samples=%d, min=%.2f, max=%.2f, mean=%.2f, stdev=%.2f',
                log_prefix, num_samples, data_min, data_max, data_mean,
                data_stdev)
  else:
    ad.log.info('%s: num_samples=%d, min=%.2f, max=%.2f, mean=%.2f', log_prefix,
                num_samples, data_min, data_max, data_mean)
