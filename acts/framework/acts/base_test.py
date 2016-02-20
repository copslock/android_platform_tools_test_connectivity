#!/usr/bin/env python3.4
#
# Copyright 2016 - The Android Open Source Project
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

from builtins import open

import os

import acts.logger as logger

from acts import test_runner
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
        current_test_name: A string that's the name of the test case currently
            being executed. If no test is executing, this should be None.
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
        self.results = TestResult()
        self.current_test_name = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._exec_func(self.clean_up)

    def unpack_userparams(self, req_param_names=[], opt_param_names=[],
                          **kwargs):
        """Unpacks user defined parameters in test config into individual
        variables.

        Instead of accessing the user param with self.user_params["xxx"], the
        variable can be directly accessed with self.xxx.

        A missing required param will raise an exception. If an optional param
        is missing, an INFO line will be logged.

        Args:
            req_param_names: A list of names of the required user params.
            opt_param_names: A list of names of the optional user params.
            **kwargs: Arguments that provide default values.
                e.g. unpack_userparams(required_list, opt_list, arg_a="hello")
                     self.arg_a will be "hello" unless it is specified again in
                     required_list or opt_list.

        Raises:
            BaseTestError is raised if a required user params is missing from test
            config.
        """
        for k, v in kwargs.items():
            setattr(self, k, v)
        for name in req_param_names:
            if name not in self.user_params:
                raise BaseTestError(("Missing required user param '%s' in test"
                    " configuration.") % name)
            setattr(self, name, self.user_params[name])
        for name in opt_param_names:
            if name not in self.user_params:
                self.log.info(("Missing optional user param '%s' in "
                    "configuration, continue.") % name)
            else:
                setattr(self, name, self.user_params[name])

    def _setup_class(self):
        """Proxy function to guarantee the base implementation of setup_class
        is called.
        """
        return self.setup_class()

    def setup_class(self):
        """Setup function that will be called before executing any test case in
        the test class.

        To signal setup failure, return False or raise an exception. If
        exceptions were raised, the stack trace would appear in log, but the
        exceptions would not propagate to upper levels.

        Implementation is optional.
        """

    def teardown_class(self):
        """Teardown function that will be called after all the selected test
        cases in the test class have been executed.

        Implementation is optional.
        """

    def _setup_test(self, test_name):
        """Proxy function to guarantee the base implementation of setup_test is
        called.
        """
        self.current_test_name = test_name
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

        To signal setup failure, return False or raise an exception. If
        exceptions were raised, the stack trace would appear in log, but the
        exceptions would not propagate to upper levels.

        Implementation is optional.
        """

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
        try:
            self.teardown_test()
        finally:
            self.current_test_name = None

    def teardown_test(self):
        """Teardown function that will be called every time a test case has
        been executed.

        Implementation is optional.
        """

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

    def _on_pass(self, record):
        """Proxy function to guarantee the base implementation of on_pass is
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
        self.on_pass(test_name, begin_time)

    def on_pass(self, test_name, begin_time):
        """A function that is executed upon a test case passing.

        Implementation is optional.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """

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

    def on_exception(self, test_name, begin_time):
        """A function that is executed upon an unhandled exception from a test
        case.

        Implementation is optional.

        Args:
            test_name: Name of the test that triggered this function.
            begin_time: Logline format timestamp taken when the test started.
        """

    def fail(self, msg, extras=None):
        """Explicitly fail a test case.

        Args:
            msg: A string explaining the details of the failure.
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

    def exec_one_testcase(self, test_name, test_func, args, **kwargs):
        """Executes one test case and update test results.

        Executes one test case, create a TestResultRecord object with the
        execution information, and add the record to the test class's test
        results.

        Args:
            test_name: Name of the test.
            test_func: The test function.
            args: A tuple of params.
            kwargs: Extra kwargs.
        """
        is_generate_trigger = False
        tr_record = TestResultRecord(test_name, self.TAG)
        tr_record.test_begin()
        self.log.info("[Test Case] %s" % test_name)
        verdict = None
        try:
            ret = self._setup_test(test_name)
            self.assert_true(ret is not False,
                             "Setup for %s failed." % test_name)
            try:
                if args or kwargs:
                    verdict = test_func(*args, **kwargs)
                else:
                    verdict = test_func()
            except TypeError as e:
                e_str = str(e)
                if test_name in e_str:
                    raise TestSkip("%s. Got args: %s, kwargs %s." % (e_str,
                                                                    args,
                                                                    kwargs))
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
            self._exec_func(self._on_pass, tr_record)
        except TestSilent as e:
            # This is a trigger test for generated tests, suppress reporting.
            is_generate_trigger = True
            self.results.requested.remove(test_name)
        except Exception as e:
            # Exception happened during test.
            self.log.exception("Uncaught exception in " + test_name)
            tr_record.test_unknown(e)
            bt = logger.epoch_to_log_line_timestamp(tr_record.begin_time)
            self._exec_func(self.on_exception, tr_record.test_name, bt)
            self._exec_func(self._on_fail, tr_record)
        else:
            # Keep supporting return False for now.
            # TODO(angli): Deprecate return False support.
            if verdict or (verdict is None):
                # Test passed.
                tr_record.test_pass()
                self._exec_func(self._on_pass, tr_record)
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

    def run_generated_testcases(self, test_func, settings,
                                args=None, kwargs=None,
                                tag="", name_func=None):
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
            args: Iterable of additional position args to be passed to test_func
            kwargs: Dict of additional keyword args to be passed to test_func
            tag: Name of this group of generated test cases. Ignored if
                name_func is provided and operates properly.
            name_func: A function that takes a test setting and generates a
                proper test name. The test name should be shorter than
                MAX_FILENAME_LEN. Names over the limit will be truncated.

        Returns:
            A list of settings that did not pass.
        """
        args = args or ()
        kwargs = kwargs or {}
        failed_settings = []
        for s in settings:
            test_name = "{} {}".format(tag, s)
            if name_func:
                try:
                    test_name = name_func(s, *args, **kwargs)
                except:
                    msg = ("Failed to get test name from test_func. Fall back "
                        "to default %s") % test_name
                    self.log.exception(msg)
            self.results.requested.append(test_name)
            if len(test_name) > MAX_FILENAME_LEN:
                test_name = test_name[:MAX_FILENAME_LEN]
            previous_success_cnt = len(self.results.passed)
            self.exec_one_testcase(test_name, test_func, (s,) + args, **kwargs)
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

    def _get_all_test_names(self):
        """Finds all the function names that match the test case naming
        convention in this class.

        Returns:
            A list of strings, each is a test case name.
        """
        test_names = []
        for name in dir(self):
            if name.startswith("test_"):
                test_names.append(name)
        return test_names

    def _get_test_funcs(self, test_names):
        """Obtain the actual functions of test cases based on test names.

        Args:
            test_names: A list of strings, each string is a test case name.

        Returns:
            A list of tuples of (string, function). String is the test case
            name, function is the actual test case function.

        Raises:
            test_runner.USERError is raised if the test name does not follow
            naming convention "test_*". This can only be caused by user input
            here.
        """
        test_funcs = []
        for test_name in test_names:
            if not test_name.startswith("test_"):
                msg = ("Test case name %s does not follow naming convention "
                       "test_*, abort.") % test_name
                raise test_runner.USERError(msg)
            try:
                test_funcs.append((test_name, getattr(self, test_name)))
            except AttributeError:
                self.log.warning("%s does not have test case %s." % (
                    self.TAG, test_name))
            except BaseTestError as e:
                self.log.warning(str(e))
        return test_funcs

    def run(self, test_names=None):
        """Runs test cases within a test class by the order they appear in the
        execution list.

        One of these test cases lists will be executed, shown here in priority
        order:
        1. The test_names list, which is passed from cmd line. Invalid names
           are guarded by cmd line arg parsing.
        2. The self.tests list defined in test class. Invalid names are
           ignored.
        3. All function that matches test case naming convention in the test
           class.

        Args:
            test_names: A list of string that are test case names requested in
                cmd line.

        Returns:
            The test results object of this class.
        """
        self.log.info("==========> %s <==========" % self.TAG)
        # Devise the actual test cases to run in the test class.
        if not test_names:
            if self.tests:
                # Specified by run list in class.
                test_names = list(self.tests)
            else:
                # No test case specified by user, execute all in the test class.
                test_names = self._get_all_test_names()
        self.results.requested = test_names
        tests = self._get_test_funcs(test_names)
        # Setup for the class.
        try:
            if self._setup_class() is False:
                raise TestFailure("Failed to setup %s." % self.TAG)
        except Exception as e:
            self.log.exception("Failed to setup %s." % self.TAG)
            self.results.fail_class(self.TAG, e)
            self._exec_func(self.teardown_class)
            return self.results
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
