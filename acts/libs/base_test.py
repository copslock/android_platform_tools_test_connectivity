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

import os
import sys
import time
import traceback

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

  def setup_class(self):
    """Setup function that will be called before executing any test case in the
    test class.

    Implementation is optional.
    """
    self.log.debug("Setting up for the test class " + self.TAG)
    pass

  def teardown_class(self):
    """Teardown function that will be called after all the selected test cases
    in the test class have been executed.

    Implementation is optional.
    """
    self.log.debug("Tearing down the test class " + self.TAG)
    pass

  def setup_test(self):
    """Setup function that will be called every time before executing each test
    case in the test class.

    Implementation is optional.
    """
    self.log.debug("Setting up before a test...")
    pass

  def teardown_test(self):
    """Teardown function that will be called every time a test case has been
    executed.

    Implementation is optional.
    """
    self.log.debug("Tearing down after a test...")
    pass

  def reset_env(self):
    """Resets the environment. Will be called after an exception has happened
    when executing a test case.

    Implementation is optional.
    """
    self.log.debug("Resetting the environment after an exception in a test...")
    pass

  def exec_one_testcase(self, test_name, test_func, name_max_len, params=None):
    """Executes one test case.

    Catches unhandled exceptions and report results.

    Args:
      test_name: Name of the test.
      test_func: The test function.
      name_max_len: Max length of test case names among all the test cases
        specified in this test class.
      params: Params to be passed to the test function.

    Returns:
      True if the test passes, False otherwise.
    """
    offset = name_max_len - len(test_name) + 5
    try:
      self.log.info("="*10 + "> Running - " + test_name)
      verdict = None
      if params:
        # The evil unexposed ability to pass parameters into each test case.
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
      self._exec_func(self.reset_env)
    return False

  def run_generated_testcases(self, tag, test_func, setting_strs, *args):
    """Runs generated test cases.

    Generated test cases are not written down as functions, but as a list of
    parameter sets. This way we reduce code repeatitiion and improve test case
    scalability.

    Args:
      tag: Overall name of this group of generated test cases.
      test_func: The common logic shared by all these genrated test cases. This
        function should take at least one argument, which is a parameter set.
      setting_strs: A list of strings representing parameter sets. These are
        usually json strings that get loaded in the test_func.
      args: Additional args to be passed to the test_func.
    """
    name_max_len = max(len(s) for s in setting_strs) + len(tag)
    failed_settings = []
    for s in setting_strs:
      test_name = tag + "\n" + s
      self._exec_func(self.setup_test)
      result = self.exec_one_testcase(test_name,
                                      test_func,
                                      name_max_len,
                                      (s,) + args)
      self._exec_func(self.teardown_test)
      if not result:
        failed_settings.append(s)
    return failed_settings

  def _is_test_name_valid(self, name):
    """Checks if a test name follows the convention.

    Params:
      name: name of a test case.

    Returns:
      True if the name follows the convention, False otherwise.
    """
    return name[:5] == "test_"

  def _exec_func(self, func, *args):
    """Executes a function with exception safeguard.

    Args:
      func: Function to be executed.
      args: arguments to be passed to the function

    Returns:
      Whatever the function returns.
    """
    try:
      return func(*args)
    except:
      msg = ("Exception happened when executing " + func.__name__ + " in "
             + self.TAG)
      timestamp = time.strftime("%m-%d-%Y %H:%M:%S ")
      self.reporter.write(timestamp  + " " + msg + "\n")
      self.log.exception(msg)
      self.log.exception(traceback.format_exc())

  def run(self, test_cases=None):
    """Runs test cases within a test class by the order they
    appear in the test list.

    Args:
      test_cases: Test cases to be executed; all if set to None.
    """
    self._exec_func(self.setup_class)
    tests = self.tests
    if test_cases:
      ts = []
      for test_name in test_cases:
        ts.append(getattr(self, test_name))
      tests = ts
    # Length of the longest test name for report formatting
    name_max_len = max(len(t.__name__) for t in tests)
    # Run tests in order
    for test_func in tests:
      test_name = test_func.__name__
      if self._is_test_name_valid(test_name):
        self._exec_func(self.setup_test)
        self.exec_one_testcase(test_name, test_func, name_max_len)
        self._exec_func(self.teardown_test)
      else:
        self.log.error("Attempted to execute a test case with invalid name: "
                       + test_name)
    self._exec_func(self.teardown_class)
    self._exec_func(self.clean_up)

  def clean_up(self):
    """Cleans up objects initialized in the constructor.
    """
    self.mdevice.kill_all_droids()
    for h in self.log.handlers:
      try:
        h.close()
      except:
        pass
      self.log.removeHandler(h)
    self.reporter.close()

