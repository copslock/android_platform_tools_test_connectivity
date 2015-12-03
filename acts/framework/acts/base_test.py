#!/usr/bin/python3.4
#
# Copyright 2014 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import acts.logger as logger

from acts.keys import Config
from acts.records import TestResult
from acts.records import TestResultRecord
from acts.signals import TestAbortClass
from acts.signals import TestAbortAll
from acts.signals import TestFailure
from acts.signals import TestPass
from acts.signals import TestSkip
from acts.signals import TestSilent
from acts.utils import concurrent_exec
from acts.utils import create_dir
from acts.utils import get_current_human_time

MAX_FILENAME_LEN = 255
DEFAULT_ADB_LOG_OFFSET = 5

# Macro strings for test result reporting
TEST_CASE_TOKEN = "[Test Case]"
RESULT_LINE_TEMPLATE = TEST_CASE_TOKEN + " %s %s"

def validate_test_name(name):
    """Checks if a test name is valid.

    To be valid, a test name needs to follow the naming convention: starts
    with "test_". Also, the test class needs to actually have a function
    named after the test.

    Args:
        name: name of a test case.

    Raises:
        BaseTestError is raised if the name is invalid.
    """
    if len(name) < 5 or name[:5] != "test_":
        raise BaseTestError("Invalid test case name found: {}.".format(name))

class BaseTestError(Exception):
    """Raised for exceptions that occured in BaseTestClass."""

class BaseTestClass(object):
    """Base class for all test classes to inherit from.

    This class gets all the controller objects from test_runner and executes
    the test cases requested within itself.

    Most attributes of this class are set at runtime based on the configuration
    provided.

    Attributes:
        tests: A list of strings, each representing a test case name.
        TAG: A string used to refer to a test class. Default is the test class
            name.
        droids: A list of SL4A client objects for convenience. Do NOT use, to
            be deprecated.
        eds: A list of event_dispatcher objects. Do NOT use, to be deprecated.
        log: A logger object used for logging.
        results: A TestResult object for aggregating test results from the
            execution of test cases.
    """

    TAG = None

    def __init__(self, configs):
        self.tests = []
        if not self.TAG:
            self.TAG = self.__class__.__name__
        # Set default value for optional config params.
        if Config.key_adb_log_time_offset.value not in configs:
            configs[Config.key_adb_log_time_offset.value] = DEFAULT_ADB_LOG_OFFSET
        # Set all the controller objects and params.
        for name, value in configs.items():
            setattr(self, name, value)
        # Set convenience references for android_device objects.
        # TODO(angli): remove these and force tests to use the droids in ad
        # objs directly.
        if Config.ikey_android_device.value in configs:
            self.droids = []
            self.eds = []
            for ad in self.android_devices:
                self.droids.append(ad.droid)
                self.eds.append(ad.ed)
            if self.android_devices:
                self.droid = self.droids[0]
                self.ed = self.eds[0]
        else:
            self.log.warning("No attached android device found.")
        self.results = TestResult()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._exec_func(self.clean_up)

    def unpack_userparams(self, req_param_names, opt_param_names=[]):
        """Unpacks user defined parameters in test config into individual
        variables.

        Instead of accessing the user param with self.user_params["xxx"], the
        variable can be directly accessed with self.xxx.

        All missing required params will be logged in error. If an optional
        param is missing, log a note and continue. You can assert on the return
        value of this funtion in setup_class to ensure the required user params
        are found in test config and set.

        Args:
            req_param_names: A list of names of the required user params.
            opt_param_names: A list of names of the optional user params.

        Returns:
            True if all required user params were set. False otherwise.
        """
        missing = False
        for name in req_param_names:
            if name not in self.user_params:
                missing = True
                self.log.error(("Missing required user param '%s' in "
                    "configuration!") % name)
                continue
            setattr(self, name, self.user_params[name])
        for name in opt_param_names:
            if name not in self.user_params:
                self.log.info(("Missing optional user param '%s' in "
                    "configuration, continue.") % name)
            else:
                setattr(self, name, self.user_params[name])
        return not missing

    def _setup_class(self):
        """Proxy function to guarantee the base implementation of setup_class
        is called.
        """
        try:
            return self.setup_class()
        except TestAbortClass:
            return False

    def setup_class(self):
        """Setup function that will be called before executing any test case in
        the test class.

        Implementation is optional.
        """
        return True

    def teardown_class(self):
        """Teardown function that will be called after all the selected test
        cases in the test class have been executed.

        Implementation is optional.
        """
        pass

    def _setup_test(self, test_name):
        """Proxy function to guarantee the base implementation of setup_test is
        called.
        """
        try:
            # Write test start token to adb log if android device is attached.
            for ad in self.android_devices:
                ad.droid.logV("%s BEGIN %s" % (TEST_CASE_TOKEN, test_name))
        except:
            pass
        return self.setup_test()

    def setup_test(self):
        """Setup function that will be called every time before executing each
        test case in the test class.

        Implementation is optional.
        """
        return True

    def _teardown_test(self, test_name):
        """Proxy function to guarantee the base implementation of teardown_test
        is called.
        """
        try:
            # Write test end token to adb log if android device is attached.
            for ad in self.android_devices:
                ad.droid.logV("%s END %s" % (TEST_CASE_TOKEN, test_name))
        except:
            pass
        return self.teardown_test()

    def teardown_test(self):
        """Teardown function that will be called every time a test case has
        been executed.

        Implementation is optional.
        """
        pass

    def _on_fail(self, record):
        """Proxy function to guarantee the base implementation of on_fail is
        called.

        Args:
            record: The TestResultRecord object for the failed test case.
        """
        test_name = record.test_name
        begin_time = logger.epoch_to_log_line_timestamp(record.begin_time)
        end_time = logger.get_log_line_timestamp(self.adb_log_time_offset)
        self.log.error(record.details)
        self.log.info(RESULT_LINE_TEMPLATE % (test_name, record.result))
        try:
            self.cat_adb_log(test_name, begin_time, end_time)
        except AttributeError:
            pass
        self.on_fail(test_name, begin_time)

    def on_fail(self, test_name, begin_time):
        """A function that is executed upon a test case failure.

        User implementation is optional.

        This should be the primary place to call take_bug_reports, e.g.
        self.take_bug_reports(test_name, self.android_devices[0])

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """
        pass

    def _on_success(self, record):
        """Proxy function to guarantee the base implementation of on_success is
        called.

        Args:
            record: The TestResultRecord object for the passed test case.
        """
        test_name = record.test_name
        begin_time = logger.epoch_to_log_line_timestamp(record.begin_time)
        msg = record.details
        if msg:
            self.log.info(msg)
        self.log.info(RESULT_LINE_TEMPLATE % (test_name, record.result))
        self.on_success(test_name, begin_time)

    def on_success(self, test_name, begin_time):
        """A function that is executed upon a test case passing.

        Implementation is optional.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """
        pass

    def _on_skip(self, record):
        """Proxy function to guarantee the base implementation of on_skip is
        called.

        Args:
            record: The TestResultRecord object for the skipped test case.
        """
        test_name = record.test_name
        begin_time = logger.epoch_to_log_line_timestamp(record.begin_time)
        self.log.info(RESULT_LINE_TEMPLATE % (test_name, record.result))
        self.log.info("Reason to skip: %s" % record.details)
        self.on_skip(test_name, begin_time)

    def on_skip(self, test_name, begin_time):
        """A function that is executed upon a test case being skipped.

        Implementation is optional.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """
        pass

    def on_exception(self, test_name, begin_time):
        """A function that is executed upon an unhandled exception from a test
        case.

        Implementation is optional.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """
        pass

    def fail(self, msg, extras=None):
        """Explicitly fail a test case.

        Args:
            msg: A string explaining the datails of the failure.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestFailure is raised to mark a test case as failed.
        """
        raise TestFailure(msg, extras)

    def explicit_pass(self, msg, extras=None):
        """Explicitly pass a test case.

        A test with not uncaught exception will pass implicitly so the usage of
        this is optional. It is intended for reporting extra information when a
        test passes.

        Args:
            msg: A string explaining the details of the passed test.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestPass is raised to mark a test case as passed.
        """
        raise TestPass(msg, extras)

    def assert_true(self, expr, msg, extras=None):
        """Assert an expression evaluates to true, otherwise fail the test.

        Args:
            expr: The expression that is evaluated.
            msg: A string explaining the datails in case of failure.
            extras: An optional field for extra information to be included in
                test result.
        """
        if not expr:
            self.fail(msg, extras)

    def skip(self, reason, extras=None):
        """Skip a test case.

        Args:
            reason: The reason this test is skipped.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestSkip is raised to mark a test case as skipped.
        """
        raise TestSkip(reason, extras)

    def skip_if(self, expr, reason, extras=None):
        """Skip a test case if expression evaluates to True.

        Args:
            expr: The expression that is evaluated.
            reason: The reason this test is skipped.
            extras: An optional field for extra information to be included in
                test result.
        """
        if expr:
            self.skip(reason, extras)

    def abort_class(self, reason, extras=None):
        """Abort all subsequent test cases within the same test class in one
        iteration.

        If one test class is requested multiple times in a test run, this can
        only abort one of the requested executions, NOT all.

        Args:
            reason: The reason to abort.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestAbortClass is raised to abort all subsequent tests in the test
            class.
        """
        self.log.warning(("Abort %s, remaining test cases within the class"
                " will not be executed. Reason: %s") % (self.TAG, str(reason)))
        raise TestAbortClass(reason, extras)

    def abort_class_if(self, expr, reason, extras=None):
        """Abort all subsequent test cases within the same test class in one
        iteration, if expression evaluates to True.

        If one test class is requested multiple times in a test run, this can
        only abort one of the requested executions, NOT all.

        Args:
            expr: The expression that is evaluated.
            reason: The reason to abort.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestAbortClass is raised to abort all subsequent tests in the test
            class.
        """
        if expr:
            self.abort_class(reason, extras)

    def abort_all(self, reason, extras=None):
        """Abort all subsequent test cases, including the ones not in this test
        class or iteration.

        Args:
            reason: The reason to abort.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestAbortAll is raised to abort all subsequent tests.
        """
        self.log.warning(("Abort test run, remaining test cases will not be "
                "executed. Reason: %s") % (str(reason)))
        raise TestAbortAll(reason, extras)

    def abort_all_if(self, expr, reason, extras=None):
        """Abort all subsequent test cases, if the expression evaluates to
        True.

        Args:
            expr: The expression that is evaluated.
            reason: The reason to abort.
            extras: An optional field for extra information to be included in
                test result.

        Raises:
            TestAbortAll is raised to abort all subsequent tests.
        """
        if expr:
            self.abort_all(reason, extras)

    def _is_timestamp_in_range(self, target, begin_time, end_time):
        low = logger.logline_timestamp_comparator(begin_time, target) <= 0
        high = logger.logline_timestamp_comparator(end_time, target) >= 0
        return low and high

    def cat_adb_log(self, tag, begin_time, end_time):
        """Takes logs from adb logcat log.

        Goes through adb logcat log and excerpt the log lines recorded during a
        certain time period. The lines are saved into a file in the test
        class's log directory.

        Args:
            tag: An identifier of the time period, usualy the name of a test.
            begin_time: Logline format timestamp of the beginning of the time
                period.
            end_time: Logline format timestamp of the end of the time period.
        """
        self.log.debug("Extracting adb log from logcat.")
        adb_excerpt_path = os.path.join(self.log_path, "AdbLogExcerpts")
        create_dir(adb_excerpt_path)
        for f_name in self.adb_logcat_files:
            out_name = f_name.replace("adblog,", "").replace(".txt", "")
            out_name = ",{},{}.txt".format(begin_time, out_name)
            tag_len = MAX_FILENAME_LEN - len(out_name)
            tag = tag[:tag_len]
            out_name = tag + out_name
            full_adblog_path = os.path.join(adb_excerpt_path, out_name)
            with open(full_adblog_path, 'w', encoding='utf-8') as out:
                in_file = os.path.join(self.adb_logcat_path, f_name)
                with open(in_file, 'r', encoding='utf-8', errors='replace') as f:
                    in_range = False
                    while True:
                        line = None
                        try:
                            line = f.readline()
                            if not line:
                                break
                        except:
                            continue
                        line_time = line[:logger.log_line_timestamp_len]
                        if not logger.is_valid_logline_timestamp(line_time):
                            continue
                        if self._is_timestamp_in_range(line_time, begin_time,
                            end_time):
                            in_range = True
                            out.write(line + '\n')
                        else:
                            if in_range:
                                break

    def take_bug_reports(self, test_name, begin_time, android_devices):
        """Takes bug report on a list of devices and stores it in the log
        directory of the test class.

        If you want to take a bug report, call this function with a list of
        android_device objects in on_fail. But reports will be taken on all the
        devices in the list concurrently. Bug report takes a relative long
        time to take, so use this cautiously.

        Args:
            test_name: Name of the test case that triggered this bug report.
            begin_time: Logline format timestamp taken when the test started.
            android_devices: android_device instances to take bugreport on.
        """
        br_path = os.path.join(self.log_path, "BugReports")
        begin_time = logger.normalize_log_line_timestamp(begin_time)
        create_dir(br_path)
        args = [(test_name, begin_time, ad) for ad in android_devices]
        concurrent_exec(self._take_bug_report, args)

    def _take_bug_report(self, test_name, begin_time, ad):
        """Takes a bug report on a device and stores it in the log directory of
        the test class.

        Args:
            test_name: Name of the test case that triggered this bug report.
            begin_time: Logline format timestamp taken when the test started.
            ad: The AndroidDevice instance to take bugreport on.
        """
        serial = ad.serial
        br_path = os.path.join(self.log_path, "BugReports")
        base_name = ",{},{}.txt".format(begin_time, serial)
        test_name_len = MAX_FILENAME_LEN - len(base_name)
        out_name = test_name[:test_name_len] + base_name
        full_out_path = os.path.join(br_path, out_name.replace(' ', '\ '))
        self.log.info("Taking bugreport for test case {} on {}".
            format(test_name, serial))
        ad.adb.bugreport(" > %s" % full_out_path)
        self.log.info("Finished taking bugreport on {}".format(serial))

    def exec_one_testcase(self, test_name, test_func, pms=None):
        """Executes one test case and update test results.

        Executes one test case, create a TestResultRecord object with the
        execution information, and add the record to the test class's test
        results.

        Args:
            test_name: Name of the test.
            test_func: The test function.
            pms: Params to be passed to the test function.
        """
        is_generate_trigger = False
        tr_record = TestResultRecord(test_name)
        tr_record.test_begin()
        self.log.info("[Test Case] %s" % test_name)
        verdict = None
        try:
            self.skip_if(not self._exec_func(self._setup_test, test_name),
                "Setup for %s failed." % test_name)
            try:
                if pms:
                        verdict = test_func(*pms)
                else:
                    verdict = test_func()
            except TypeError as e:
                e_str = str(e)
                if test_name in e_str:
                    raise TestSkip(e_str + ". Got args: {}".format(pms))
                raise e
        except (TestFailure, AssertionError) as e:
            tr_record.test_fail(e)
            self._exec_func(self._on_fail, tr_record)
        except TestSkip as e:
            # Test skipped.
            tr_record.test_skip(e)
            self._exec_func(self._on_skip, tr_record)
        except (TestAbortClass, TestAbortAll) as e:
            # Abort signals, pass along.
            tr_record.test_skip(e)
            raise e
        except TestPass as e:
            # Explicit test pass.
            tr_record.test_pass(e)
            self._exec_func(self._on_success, tr_record)
        except TestSilent as e:
            # This is a trigger test for generated tests, suppress reporting.
            is_generate_trigger = True
            self.results.requested.remove(test_name)
        except Exception as e:
            # Exception happened during test.
            self.log.exception("Exception in " + test_name)
            tr_record.test_fail(e)
            bt = logger.epoch_to_log_line_timestamp(tr_record.begin_time)
            self._exec_func(self.on_exception, tr_record.test_name, bt)
            self._exec_func(self._on_fail, tr_record)
        else:
            # Keep supporting return False for now.
            # TODO(angli): Deprecate return False support.
            if verdict or (verdict is None):
                # Test passed.
                tr_record.test_pass()
                self._exec_func(self._on_success, tr_record)
                return
            # Test failed because it didn't return True.
            # This should be removed eventually.
            tr_record.test_fail()
            self._exec_func(self._on_fail, tr_record)
        finally:
            self._exec_func(self._teardown_test, test_name)
            if not is_generate_trigger:
                self.results.add_record(tr_record)
                self.reporter.write(repr(tr_record) + '\n')

    def run_generated_testcases(self, test_func, settings, *args, tag="",
                                name_func=None):
        """Runs generated test cases.

        Generated test cases are not written down as functions, but as a list
        of parameter sets. This way we reduce code repetition and improve
        test case scalability.

        Args:
            test_func: The common logic shared by all these generated test
                cases. This function should take at least one argument, which
                is a parameter set.
            settings: A list of strings representing parameter sets. These are
                usually json strings that get loaded in the test_func.
            args: Additional args to be passed to the test_func.
            tag: Name of this group of generated test cases. Ignored if
                name_func is provided and operate properly
            name_func: A function that takes a test setting and generates a
                proper test name. The test name should be shorter than
                MAX_FILENAME_LEN. Names over the limit will be truncated.

        Returns:
            A list of settings that did not pass.
        """
        failed_settings = []
        for s in settings:
            test_name = "{} {}".format(tag, s)
            if name_func:
                try:
                    test_name = name_func(s, *args)
                except:
                    msg = ("Failed to get test name from test_func. Fall back "
                        "to default %s") % test_name
                    self.log.exception(msg)
            self.results.requested.append(test_name)
            if len(test_name) > MAX_FILENAME_LEN:
                test_name = test_name[:MAX_FILENAME_LEN]
            previous_success_cnt = len(self.results.passed)
            self.exec_one_testcase(test_name, test_func, (s,) + args)
            if len(self.results.passed) - previous_success_cnt != 1:
                failed_settings.append(s)
        return failed_settings

    def _exec_func(self, func, *args):
        """Executes a function with exception safeguard.

        This will let TestAbortAll through so abort_all works in all procedure
        functions.

        Args:
            func: Function to be executed.
            args: Arguments to be passed to the function.

        Returns:
            Whatever the function returns, or False if unhandled exception
            occured.
        """
        try:
            return func(*args)
        except TestAbortAll:
            raise
        except:
            msg = "Exception happened when executing {} in {}.".format(
                func.__name__, self.TAG)
            self.log.exception(msg)
            return False

    def _get_test_funcs(self, test_case_names):
        # All tests are selected if test_cases list is None.
        test_names = self.tests
        if test_case_names:
            test_names = test_case_names
        # Load functions based on test names. Also find the longest test name.
        test_funcs = []
        for test_name in test_names:
            try:
                # Validate test_name's format.
                validate_test_name(test_name)
                test_funcs.append((test_name, getattr(self, test_name)))
            except AttributeError:
                self.log.warning("%s does not have test case %s." % (
                    self.TAG, test_name))
            except BaseTestError as e:
                self.log.warning(str(e))
        return test_funcs

    def run(self, test_names=None):
        """Runs test cases within a test class by the order they
        appear in the test list.

        Being in the test_names list makes the test case "requested". If its
        name passes validation, then it'll be executed, otherwise the name will
        be skipped.

        Args:
            test_names: A list of names of the requested test cases. If None,
                all test cases in the class are considered requested.

        Returns:
            A tuple of: The number of requested test cases, the number of test
            cases executed, and the number of test cases passed.
        """
        # Total number of test cases requested by user.
        if test_names:
            self.results.requested = list(test_names)
        elif self.tests:
            self.results.requested = list(self.tests)
        else:
            # No test case specified and no default list, abort.
            return self.results
        # Setup for the class.
        if not self._exec_func(self._setup_class):
            self.log.error("Failed to setup {}, skipping.".format(self.TAG))
            skip_signal = TestSkip("Test class %s failed to setup." % self.TAG)
            self.results.skip_all(skip_signal)
            self._exec_func(self.teardown_class)
            return self.results
        self.log.info("==========> %s <==========" % self.TAG)
        tests = self._get_test_funcs(test_names)

        # Run tests in order.
        try:
            for test_name, test_func in tests:
                self.exec_one_testcase(test_name, test_func, self.cli_args)
            return self.results
        except TestAbortClass:
            return self.results
        except TestAbortAll as e:
            # Piggy-back test results on this exception object so we don't lose
            # results from this test class.
            setattr(e, "results", self.results)
            raise e
        finally:
            self._exec_func(self.teardown_class)
            self.log.info("Summary for test class %s: %s" % (self.TAG,
                self.results.summary_str()))

    def clean_up(self):
        """A function that is executed upon completion of all tests cases
        selected in the test class.

        This function should clean up objects initialized in the constructor by
        user.
        """
        pass
