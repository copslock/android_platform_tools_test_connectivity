#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

from acts.base_test import BaseTestClass
from acts.signals import generated_test
from acts.signals import TestSignal
from acts.signals import TestSignalError

class Something:
    """Empty class used to test json serialization check."""

class ActsBaseClassTest(BaseTestClass):
    """This test class tests the implementation of BaseTestClass.

    Including:
    - Different ways to mark the result of a test case.
    - Test case name convention enforcement
    - None existent test case handling.
    """
    EXTRA_ARG = "An extra arg"

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_none_existent",
            "invalid_test_name",
            "test_current_test_case_name",
            "test_setup_test_fail_by_exception",
            "test_setup_test_fail_by_test_signal",
            "test_setup_test_fail_by_return_False",
            "test_uncaught_exception",
            "test_return_True",
            "test_implicit_pass",
            "test_return_False",
            "test_fail",
            "test_fail_with_int_extra",
            "test_explicit_pass",
            "test_explicit_pass_with_str_extra",
            "test_assert_true",
            "test_assert_true_with_extras",
            "test_skip",
            "test_skip_with_extras",
            "test_skip_if",
            "test_generated_tests",
            "test_never"
        )

    def setup_class(self):
        self.log.info("In setup_class.")

    def setup_test(self):
        """Make sure empty setup_test does not block.
        """
        if "setup_test_fail_by_exception" in self.current_test_name:
            raise Exception("Expected failure because setup_test failed by "
                            "uncaught exception.")
        elif "setup_test_fail_by_test_signal" in self.current_test_name:
            self.fail("Excepted failure because setup_test failed by test "
                      "signal.")
        elif "setup_test_fail_by_return_False" in self.current_test_name:
            return False

    def on_pass(self, test_name, begin_time):
        self.log.info("In on_pass.")
        msg = "%s should not have passed." % test_name
        expected_success = (
            "test_return_True",
            "test_generated_return_True",
            "test_generated_tests",
            "test_implicit_pass",
            "test_explicit_pass_with_str_extra",
            "test_generated_implicit_pass",
            "test_generated_explicit_pass_with_str_extra",
            "test_test_args",
            "test_explicit_pass",
            "test_unpack_userparams_required",
            "test_unpack_userparams_optional",
            "test_unpack_userparams_default",
            "test_unpack_userparams_default_overwrite",
            "test_unpack_userparams_default_None",
            "test_generated_explicit_pass",
            "test_invalid_signal_details",
            "test_invalid_signal_extras",
            "test_generated_test_with_kwargs_case",
            "test_current_test_case_name"
        )
        assert test_name in expected_success, msg

    def on_fail(self, test_name, begin_time):
        self.log.info("In on_fail.")
        if test_name == "test_assert_true":
            msg = ("Raising an exception to make sure exceptions in procedure "
                "functions don't crash the test framework.")
            self.log.info(msg)
            raise Exception("Excepted exception.")

    def on_skip(self, test_name, begin_time):
        self.log.info("In on_skip")
        msg = "%s should not have been skipped." % test_name
        expected_skip = (
            "test_skip",
            "test_skip_with_extras",
            "test_skip_if",
            "test_generated_skip",
            "test_generated_skip_if",
            "test_generated_skip_with_extras",
            "test_unsolicited_test_args",
            "test_explicit_test_args_skip"
        )
        assert test_name in expected_skip, msg

    def on_exception(self, test_name, begin_time):
        self.log.info("In on_exception")
        msg = "%s should not have thrown exception." % test_name
        expected_exception = (
            "test_uncaught_exception",
            "test_generated_uncaught_exception",
            "test_setup_test_fail_by_exception",
            "test_generated_setup_test_fail_by_exception"
        )
        assert test_name in expected_exception , msg

    def generated_test_logic(self, param, extra_arg):
        """Execute all the test_ functions in the generated test case.

        Args:
            param: The partial name of the test function to executed.
            extra_arg: An extra arg added to make sure passing extra args work.
        """
        self.log.info("This is a generated test case with param %s" % param)
        assert extra_arg == self.EXTRA_ARG, "Wrong extra arg %s" % extra_arg
        # In case we want to add more fields to param, using a local var here.
        t = param
        test_func = getattr(self, "test_%s" % t)
        return test_func()

    def name_gen(self, param, extra_arg):
        return "test_generated_%s" % param

    """ Begin of Tests """

    def invalid_test_name(self):
        assert False, "This should never be executed!"

    def test_current_test_case_name(self):
        my_name = "test_current_test_case_name"
        self.assert_true(self.current_test_name == my_name,
            "Expected current_test_name to be %s, got %s" % (
                my_name, self.current_test_name))

    def test_setup_test_fail_by_exception(self):
        self.fail("This line should not have been executed!")

    def test_setup_test_fail_by_test_signal(self):
        self.fail("This line should not have been executed!")

    def test_setup_test_fail_by_return_False(self):
        self.fail("This line should not have been executed!")


    def test_uncaught_exception(self):
        raise Exception("This should fail because of uncaught exception.")

    def test_return_True(self):
        self.log.info("This should pass because return True.")
        return True

    def test_implicit_pass(self):
        self.log.info("This should pass because no error happened.")

    def test_return_False(self):
        self.log.info("This should fail because returned False.")
        return False

    def test_fail(self):
        self.fail("Expected failure with explicit fail.")

    def test_explicit_pass(self):
        self.explicit_pass("Expected pass with explicit pass.")

    def test_explicit_pass_with_str_extra(self):
        self.explicit_pass("Should fail because asserting True on False.",
                  extras="This is a string extra.")

    def test_assert_true(self):
        self.assert_true(False, "Should fail because asserting True on False.")

    def test_assert_true_with_extras(self):
        self.assert_true(False, "Should fail because asserting True on False.",
                         extras={
                             "what is this": "An extra!",
                             "what happened": "I failed!",
                             "cause_code": "haha"
                         })

    def test_fail_with_int_extra(self):
        self.fail("Should fail because asserting True on False.", extras=0)

    def test_skip(self):
        self.skip("Expected skip.")

    def test_skip_with_extras(self):
        self.skip("Expected skip.",
                  extras={
                      "what is this": "An extra!",
                      "what happened": "I skipped!",
                      "cause_code": "haha"
                  })

    def test_skip_if(self):
        self.skip_if(True, "Expected skip.")

    def test_abort_class(self):
        self.abort_class("Expected abortion of this test class.")

    def test_abort_class_if(self):
        self.abort_class_if(True, "This is expected to abort this test class.")

    def test_abort_all(self):
        self.abort_all("This is expected to abort all remaining tests.")

    def test_abort_all_if(self):
        msg = "This is expected to abort all remaining tests."
        self.abort_all_if(True, msg)

    def test_never(self):
        self.log.error("This test should never happen.")
        self.assert_true(False, "BAD!!")

    def test_test_args(self, *args):
        self.log.info("Got cli args: {}".format(args))
        self.assert_true(args, ("You should specify at least one arg with "
            "--test_args for this test."))

    def test_explicit_test_args_skip(self, one_arg):
        self.log.error("Got cli arg: {}. This test should have been skipped. "
            "You should either specify more than one for --test_args, or no "
            "--test_args at all.".format(one_arg))
        self.assert_true(False, "BAD!!")

    def test_unpack_userparams_required(self):
        required_param = "something"
        required = [required_param]
        self.assert_true(not self.unpack_userparams(required), ("Required "
                         "param '%s' missing, unpack funtion should have "
                         "returned False.") % required_param)

    def test_unpack_userparams_optional(self):
        optional_param = "something"
        opt = [optional_param]
        self.assert_true(self.unpack_userparams(opt_param_names=opt),
                        ("Optional param '%s' missing, unpack function should"
                         "have returned True.") % optional_param)

    def test_unpack_userparams_default(self):
        arg = "haha"
        self.unpack_userparams(arg1=arg)
        self.assert_true(self.arg1 == arg,
                         ("Expected to have self.arg1 set to %s on the test "
                         "class, got %s") % (arg, self.arg1))

    def test_unpack_userparams_default_overwrite(self):
        default_arg_val = "haha"
        actual_arg_val = "wawa"
        arg_name = "arg1"
        self.user_params[arg_name] = actual_arg_val
        self.unpack_userparams(opt_param_names=[arg_name],
                               arg1=default_arg_val)
        self.assert_true(self.arg1 == actual_arg_val,
                         ("Expected to have self.arg1 set to %s on the test "
                         "class, got %s") % (actual_arg_val, self.arg1))

    def test_unpack_userparams_default_None(self):
        self.unpack_userparams(arg1=None)
        self.assert_true(self.arg1 is None,
                         ("Expected to have self.arg1 set to None on the test "
                         "class, got %s") % self.arg1)

    def test_unsolicited_test_args(self):
        self.log.error("This test should have been skipped. Did you run with "
            "--test_args specified?")
        self.assert_true(False, "BAD!!")

    def test_invalid_signal_details(self):
        sth = Something()
        try:
            TestSignal(sth)
        except TestSignalError:
            self.explicit_pass("Got expected exception TestSignalError.")
        self.fail("This line should not have executed.")

    def test_invalid_signal_extras(self):
        sth = Something()
        try:
            TestSignal("test", extras=sth)
        except TestSignalError:
            self.explicit_pass("Got expected exception TestSignalError.")
        self.fail("This line should not have executed.")

    @generated_test
    def test_generated_tests(self):
        params = [
            "return_False",
            "setup_test_fail_by_exception",
            "setup_test_fail_by_test_signal",
            "setup_test_fail_by_return_False",
            "assert_true",
            "assert_true_with_extras",
            "implicit_pass",
            "explicit_pass",
            "explicit_pass_with_str_extra",
            "fail",
            "fail_with_int_extra",
            "skip",
            "skip_with_extras",
            "skip_if",
            "uncaught_exception",
            "abort_class",
            "never"
        ]
        failed = self.run_generated_testcases(
            self.generated_test_logic,
            params, self.EXTRA_ARG,
            name_func=self.name_gen)

    @generated_test
    def test_generated_test_with_kwargs(self):
        kwarg1_name = "kwarg_1"
        kwarg1_val = "whatever"
        kwarg2_name = "kwarg_2"
        kwarg2_val = "whateverAgain"
        param = "I'm a param."
        def func(p, extra, **kwargs):
            self.assert_true(p == param, ("Expected to get param '%s', got "
                                          "'%s'") % (param, p))
            self.assert_true(kwarg1_name in kwargs,
                             "Missing expected kwarg %s." % kwarg1_name)
            self.assert_true(kwargs[kwarg1_name] == kwarg1_val,
                             "Expected %s to be %s, got %s" % (
                                kwarg1_name,
                                kwarg1_val,
                                kwargs[kwarg1_name]))
            self.assert_true(kwarg2_name in kwargs,
                             "Missing expected kwarg %s." % kwarg2_name)
            self.assert_true(kwargs[kwarg2_name] == kwarg2_val,
                             "Expected %s to be %s, got %s" % (
                                kwarg2_name,
                                kwarg2_val,
                                kwargs[kwarg2_name]))
            self.log.info(("Got expected param '%s', arg '%s', and kwarg '%s'."
                          ) % (p, extra, kwargs))
        def name_func(p, extra, **kwargs):
            func(p, extra, **kwargs)
            return "test_generated_test_with_kwargs_case"
        self.run_generated_testcases(
            func,
            [param],
            kwarg_2=kwarg2_val,
            name_func=name_func,
            extra=self.EXTRA_ARG,
            kwarg_1=kwarg1_val)

    """ End of Tests """
