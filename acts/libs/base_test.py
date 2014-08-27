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
import traceback

from android_device import AndroidDevice
import logger
from test_utils.utils import get_current_human_time

class BaseTestClass():
  """Base class for all test classes.

  Initialize loggers.
  Initialize one android_device and event_dispatcher.
  Unpack controller objects from testbed.
  Handle test execution and clean up.
  """
  log_path = "../logs/"

  def __init__(self, tag, controllers):
    self.TAG = tag
    # Initialize loggers, logging to both console and file.
    self.log = logger.get_test_logger(self.log_path, self.TAG)
    self.reporter = logger.get_test_reporter(self.log_path, self.TAG)
    self.num_requested = 0
    self.num_executed = 0
    self.num_passed = 0
    # Unpack controller objects into instance variable lists
    if "android_devices" in controllers:
      # Initialize sl4a clients
      self.android_devices = controllers["android_devices"]
      self.droids = []
      self.eds = []
      for ad in self.android_devices:
        d,e = ad.get_droid()
        self.droids.append(d)
        self.eds.append(e)
        # Create separate references to first droid for convenience.
      self.droid = self.droids[0]
      self.ed = self.eds[0]
      self.ed.start()
    else:
      self.log.warning("No attached android device found.")
    if "access_points" in controllers:
      self.access_points = controllers["access_points"]
    if "attenuators" in controllers:
      self.attenuators = controllers["attenuators"]

  def setup_class(self):
    """Setup function that will be called before executing any test case in the
    test class.

    Implementation is optional.
    """
    return True

  def teardown_class(self):
    """Teardown function that will be called after all the selected test cases
    in the test class have been executed.

    Implementation is optional.
    """
    pass

  def setup_test(self):
    """Setup function that will be called every time before executing each test
    case in the test class.

    Implementation is optional.
    """
    return True

  def teardown_test(self):
    """Teardown function that will be called every time a test case has been
    executed.

    Implementation is optional.
    """
    pass

  def reset_env(self):
    """Resets the environment. Will be called after an exception has happened
    when executing a test case.

    Implementation is optional.
    """
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
      self.log.info("-"*5 + "> Test Case - " + test_name)
      verdict = None
      self.num_executed += 1
      if params:
        # The evil unexposed ability to pass parameters into each test case.
        verdict = test_func(*params)
      else:
        verdict = test_func()
      timestamp = get_current_human_time()
      msg = ' '.join((timestamp, test_name, " "*offset))
      if verdict:
        self.reporter.write(msg + " PASSED\n")
        self.log.info("PASSED")
        self.num_passed += 1
      else:
        self.reporter.write(msg + "FAILED\n")
        self.log.info("FAILED")
      return verdict
    except:
      timestamp = get_current_human_time()
      msg = ' '.join((timestamp, test_name, " "*offset))
      self.reporter.write(msg + " FAILED\n")
      self.log.exception("Exception in " + test_name)
      self.log.exception(traceback.format_exc())
      self._exec_func(self.reset_env)
      return False

  def run_generated_testcases(self, tag, test_func, settings, *args):
    """Runs generated test cases.

    Generated test cases are not written down as functions, but as a list of
    parameter sets. This way we reduce code repeatitiion and improve test case
    scalability.

    Args:
      tag: Name of this group of generated test cases.
      test_func: The common logic shared by all these genrated test cases. This
        function should take at least one argument, which is a parameter set.
      settings: A list of strings representing parameter sets. These are
        usually json strings that get loaded in the test_func.
      args: Additional args to be passed to the test_func.

    Returns:
      A list of settings that did not pass.
    """
    setting_strs = [str(s) for s in settings]
    name_max_len = max(len(s) for s in setting_strs) + len(tag)
    failed_settings = []
    for s, s_str in zip(settings, setting_strs):
      test_name = ' '.join((tag, s_str))
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
    """Checks if a test name is valid.

    To be valid, a test name needs to follow the naming convention: starts
    with "test_". Also, the test class needs to actually have a function named
    after the test.

    Params:
      name: name of a test case.

    Returns:
      True if the name is valid, False otherwise.
    """
    if name[:5] != "test_":
      self.log.error("Attempted to execute a test case with invalid name: "
                       + name)
      return False
    if name not in dir(self):
      self.log.error("Test class " + self.TAG + " does not have test case "
                     + name)
      return False
    return True

  def _exec_func(self, func, *args):
    """Executes a function with exception safeguard.

    Args:
      func: Function to be executed.
      args: Arguments to be passed to the function.

    Returns:
      Whatever the function returns.
    """
    try:
      return func(*args)
    except:
      msg = ' '.join(("Exception happened when executing", func.__name__, "in",
             self.TAG))
      timestamp = get_current_human_time()
      self.reporter.write(' '.join((timestamp, msg, "\n")))
      self.log.exception(msg)
      self.log.exception(traceback.format_exc())

  def _get_test_funcs(self, test_case_names):
    # All tests are selected if test_cases list is None.
    test_names = self.tests
    if test_case_names:
      test_names = test_case_names
    # Load functions based on test names. Also find the longest test name.
    test_funcs = []
    name_max_len = 0
    for test_name in test_names:
      if not self._is_test_name_valid(test_name):
        continue
      if len(test_name) > name_max_len:
        name_max_len = len(test_name)
      test_funcs.append((test_name, getattr(self, test_name)))
    return name_max_len, test_funcs

  def run(self, test_names=None):
    """Runs test cases within a test class by the order they
    appear in the test list.

    Being in the test_names list makes the test case "requested". If its name
    passes validation, then it'll be executed, otherwise the name will be
    skipped.

    Args:
      test_names: A list of names of the requested test cases. If None, all
        test cases in the class are considered requested.

    Returns:
      A tuple of: The number of requested test cases, the number of test cases
      executed, and the number of test cases passed.
    """
    # Setup for the class.
    if not self._exec_func(self.setup_class):
      self.log.error(''.join(("Failed to set up ", self.TAG, ", skipping.")))
      return 0, 0, 0
    self.log.info(''.join(("="*10, "> ", self.TAG, " < ", "="*10)))
    name_max_len, tests = self._get_test_funcs(test_names)
    # Total number of test cases requested by user.
    self.num_requested = len(test_names) if test_names else len(self.tests)
    # Run tests in order.
    for test_name,test_func in tests:
      if not self._exec_func(self.setup_test):
        self.log.error(' '.join(("Setup for", test_name, "failed, skipping.")))
        continue
      status = self.exec_one_testcase(test_name, test_func, name_max_len)
      self._exec_func(self.teardown_test)
    self._exec_func(self.teardown_class)
    summary = ''.join(("Result summary for tests in ", self.TAG,
               "\nExecuted:  ", str(self.num_executed),
               "\nPassed:    ", str(self.num_passed)))
    self.log.info(summary)
    self.reporter.write(summary)
    self._exec_func(self.clean_up)
    return self.num_requested, self.num_executed, self.num_passed

  def clean_up(self):
    """Cleans up objects initialized in the constructor.
    """
    for ad in self.android_devices:
      ad.kill_all_droids()
    for h in self.log.handlers:
      try:
        h.close()
      except:
        pass
      self.log.removeHandler(h)
    self.reporter.close()

