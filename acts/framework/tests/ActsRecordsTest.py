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

import acts.base_test

from acts import records
from acts import signals


class ActsRecordsTest(acts.base_test.BaseTestClass):
    """This test class tests the implementation of classes in acts.records.
    """

    def __init__(self, controllers):
        acts.base_test.BaseTestClass.__init__(self, controllers)
        self.tn = "test_name"
        self.details = "Some details about the test execution."
        self.float_extra = 12345.56789
        self.json_extra = {"ha": "whatever"}

    def verify_record(self, record, result, details, extras):
        # Verify each field.
        self.assert_true(record.test_name == self.tn, ("Expected test name %s,"
            " got %s") % (self.tn, record.test_name))
        self.assert_true(record.result == result, ("Expected test result %s, "
            "got %s") % (result, record.result))
        self.assert_true(record.details == details, ("Expected test details %s"
            ":%s, got %s:%s") % (type(details), details, type(record.details),
                                 record.details))
        self.assert_true(record.extras == extras, ("Expected test record extras"
            " %s, got %s") % (extras, record.extras))
        self.assert_true(record.begin_time, "begin time should not be empty.")
        self.assert_true(record.end_time, "end time should not be empty.")
        self.assert_true(record.uid == None, ("UID is not used at the moment, "
            "should always be None."))
        # Verify to_dict.
        d = {}
        d[records.TestResultEnums.RECORD_NAME] = self.tn
        d[records.TestResultEnums.RECORD_RESULT] = result
        d[records.TestResultEnums.RECORD_DETAILS] = details
        d[records.TestResultEnums.RECORD_EXTRAS] = extras
        d[records.TestResultEnums.RECORD_BEGIN_TIME] = record.begin_time
        d[records.TestResultEnums.RECORD_END_TIME] = record.end_time
        d[records.TestResultEnums.RECORD_UID] = None
        d[records.TestResultEnums.RECORD_CLASS] = None
        actual_d = record.to_dict()
        self.assert_true(len(actual_d) == len(d), ("Expected dict length %d, "
                         "got %d.") % (len(d), len(actual_d)))
        for k, v in d.items():
            self.assert_true(k in actual_d,
                             "to_dict output missing expected key %s" % k)
            self.assert_true(actual_d[k] == v, "Expected the value of %s to be"
                             " %s in to_dict output, got %s." % (k,
                                                                 v,
                                                                 actual_d[k]))
        # Verify that these code paths do not cause crashes and yield non-empty
        # results.
        self.assert_true(str(record), "str of the record should not be empty.")
        self.assert_true(repr(record), "the record's repr shouldn't be empty.")
        self.assert_true(record.json_str(), ("json str of the record should "
                         "not be empty."))

    """ Begin of Tests """
    def test_result_record_pass_none(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        record.test_pass()
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_PASS, None,
                           None)

    def test_result_record_pass_with_float_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestPass(self.details, self.float_extra)
        record.test_pass(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_PASS,
                           self.details, self.float_extra)

    def test_result_record_pass_with_json_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestPass(self.details, self.json_extra)
        record.test_pass(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_PASS,
                           self.details, self.json_extra)

    def test_result_record_fail_none(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        record.test_fail()
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_FAIL, None,
                           None)

    def test_result_record_fail_with_float_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestFailure(self.details, self.float_extra)
        record.test_fail(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_FAIL,
                           self.details, self.float_extra)

    def test_result_record_fail_with_json_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestFailure(self.details, self.json_extra)
        record.test_fail(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_FAIL,
                           self.details, self.json_extra)

    def test_result_record_skip_none(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        record.test_skip()
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_SKIP, None,
                           None)

    def test_result_record_skip_with_float_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestSkip(self.details, self.float_extra)
        record.test_skip(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_SKIP,
                           self.details, self.float_extra)

    def test_result_record_skip_with_json_extra(self):
        record = records.TestResultRecord(self.tn)
        record.test_begin()
        s = signals.TestSkip(self.details, self.json_extra)
        record.test_skip(s)
        self.verify_record(record, records.TestResultEnums.TEST_RESULT_SKIP,
                           self.details, self.json_extra)
    """ End of Tests """
