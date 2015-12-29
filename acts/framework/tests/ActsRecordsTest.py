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
from acts.records import TestResult
from acts.records import TestResultEnums
from acts.records import TestResultRecord
from acts.signals import TestFailure
from acts.signals import TestPass
from acts.signals import TestSkip


class ActsRecordsTest(BaseTestClass):
    """This test class tests the implementation of classes in acts.records.
    """

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_result_record_pass_none",
            "test_result_record_pass_with_info",
            "test_result_record_fail_none",
            "test_result_record_fail_with_info",
            "test_result_record_skip_none",
            "test_result_record_skip_with_info"
        )
        self.tn = "test_name"
        self.details = "Some details about the test execution."
        self.code = 12345.56789

    def name_gen(self, param, extra_arg):
        return "test_generated_%s" % param

    def verify_record(self, record, result, details, code):
        # Verify each field.
        self.assert_true(record.test_name == self.tn, ("Expected test name %s,"
            " got %s") % (self.tn, record.test_name))
        self.assert_true(record.result == result, ("Expected test result %s, "
            "got %s") % (result, record.result))
        self.assert_true(record.details == details, ("Expected test details %s"
            ", got %s") % (details, record.details))
        self.assert_true(record.cause_code == code, ("Expected test cause code"
            " %s, got %s") % (code, record.cause_code))
        self.assert_true(record.begin_time, "begin time should not be empty.")
        self.assert_true(record.end_time, "end time should not be empty.")
        self.assert_true(record.uid == None, ("UID is not used at the moment, "
            "should always be None."))
        # Verify to_dict.
        d = {}
        d[TestResultEnums.RECORD_NAME] = self.tn
        d[TestResultEnums.RECORD_RESULT] = result
        d[TestResultEnums.RECORD_DETAILS] = details
        d[TestResultEnums.RECORD_CAUSE_CODE] = code
        d[TestResultEnums.RECORD_BEGIN_TIME] = record.begin_time
        d[TestResultEnums.RECORD_END_TIME] = record.end_time
        d[TestResultEnums.RECORD_UID] = None
        actual_d = record.to_dict()
        self.assert_true(set(actual_d.items()) == set(d.items()), ("Expected "
            "%s, got %s.") % (d, actual_d))
        # Verify that these code paths do not cause crashes and yield non-empty
        # results.
        self.assert_true(str(record), "str of the record should not be empty.")
        self.assert_true(repr(record), "the record's repr shouldn't be empty.")
        self.assert_true(record.json_str(), ("json str of the record should "
                         "not be empty."))

    """ Begin of Tests """
    def test_result_record_pass_none(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        record.test_pass()
        self.verify_record(record, TestResultEnums.TEST_RESULT_PASS, str(None),
                           None)
        return True

    def test_result_record_pass_with_info(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        s = TestPass(self.details, self.code)
        record.test_pass(s)
        self.verify_record(record, TestResultEnums.TEST_RESULT_PASS,
                           self.details, self.code)
        return True

    def test_result_record_fail_none(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        record.test_fail()
        self.verify_record(record, TestResultEnums.TEST_RESULT_FAIL, str(None),
                           None)
        return True

    def test_result_record_fail_with_info(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        s = TestFailure(self.details, self.code)
        record.test_fail(s)
        self.verify_record(record, TestResultEnums.TEST_RESULT_FAIL,
                           self.details, self.code)
        return True

    def test_result_record_skip_none(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        record.test_skip()
        self.verify_record(record, TestResultEnums.TEST_RESULT_SKIP, str(None),
                           None)
        return True

    def test_result_record_skip_with_info(self):
        record = TestResultRecord(self.tn)
        record.test_begin()
        s = TestSkip(self.details, self.code)
        record.test_skip(s)
        self.verify_record(record, TestResultEnums.TEST_RESULT_SKIP,
                           self.details, self.code)
        return True

    """ End of Tests """
