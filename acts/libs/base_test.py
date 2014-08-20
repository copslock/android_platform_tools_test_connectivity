#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- The Android Open Source Project
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

import time, os, traceback
import logger
from android_device import AndroidDevice

class BaseTestClass():
  """Base class for all test classes.

  Initialize loggers.
  Initialize one android_device and event_dispatcher.
  Unpack controller objects from testbed.
  Handle test execution and clean up.
  """
  log_path = "../logs/"
  TAG = None
  tests = None

  def __init__(self, tag, controllers):
    # Initialize loggers, logging to both console and file.
    self.log = logger.get_test_logger(self.log_path, self.TAG)
    self.reporter = logger.get_test_reporter(self.log_path, self.TAG)

    # Unpack controller objects into instance variable lists
    if "android_devices" in controllers:
      self.android_devices = controllers["android_devices"]
    else:
      self.log.warning("No attached android device found.")
    if "access_points" in controllers:
      self.access_points = controllers["access_points"]

    # Initialize sl4a client
    self.TAG = tag
    self.mdevice = self.android_devices[0]
    self.droid, self.ed = self.mdevice.get_droid()
    self.ed.start()

  def exec_one_testcase(self, test_name, test_func, name_max_len, params=None):
    offset = name_max_len - len(test_name) + 5
    try:
      self.log.info("="*10 + "> Running - " + test_name)
      verdict = None
      if params:
        verdict = test_func(*params)
      else:
        verdict = test_func()
      timestamp = time.strftime("%m-%d-%Y %H:%M:%S ")
      if verdict:
        self.reporter.write(timestamp + test_name + " "*offset + "PASSED\n")
        self.log.info("PASSED")
        return True
      else:
        self.reporter.write(timestamp + test_name + " "*offset + "FAILED\n")
        self.log.info("FAILED")
        return False
    except:
      timestamp = time.strftime("%m-%d-%Y %H:%M:%S ")
      self.reporter.write(timestamp + test_name + " "*offset + "FAILED\n")
      self.log.exception("Exception in " + test_name)
      self.log.exception(traceback.format_exc())
    return False

  def run_generated_testcases(self, tag, test_func, setting_strs, *args):
    name_max_len = max(len(s) for s in setting_strs) + len(tag)
    failed_settings = []
    for s in setting_strs:
      test_name = tag + "\n" + s
      result = self.exec_one_testcase(test_name,
                                      test_func,
                                      name_max_len,
                                      (s,) + args)
      if not result:
        failed_settings.append(s)
    return failed_settings

  def run(self):
    """Runs test cases within a test class by the order they
       appear in the test list.
    """
    # Length of the longest test name for report formatting
    name_max_len = max(len(t.__name__) for t in self.tests)
    # Run tests in order
    for test_func in self.tests:
      test_name = test_func.__name__
      self.exec_one_testcase(test_name, test_func, name_max_len)
    self.clean_up()

  def clean_up(self):
    self.mdevice.kill_all_droids()
    for h in self.log.handlers:
      try:
        h.close()
      except:
        pass
      self.log.removeHandler(h)
    self.reporter.close()

