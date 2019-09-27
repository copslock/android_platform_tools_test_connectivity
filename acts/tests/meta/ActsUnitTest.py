#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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
import logging
import os
import subprocess

import acts
from acts import base_test
from acts import signals

# The files under acts/framework to consider as unit tests.
UNITTEST_FILES = [
    'tests/acts_adb_test.py',
    'tests/acts_android_device_test.py',
    'tests/acts_asserts_test.py',
    'tests/acts_base_class_test.py',
    'tests/config/unittest_bundle.py',
    'tests/acts_context_test.py',
    'tests/acts_error_test.py',
    'tests/acts_host_utils_test.py',
    'tests/acts_import_test_utils_test.py',
    'tests/acts_import_unit_test.py',
    'tests/acts_job_test.py',
    'tests/libs/ota/unittest_bundle.py',
    'tests/acts_logger_test.py',
    'tests/libs/metrics/unittest_bundle.py',
    'tests/acts_records_test.py',
    'tests/acts_relay_controller_test.py',
    'tests/acts_test_runner_test.py',
    'tests/acts_unittest_suite.py',
    'tests/acts_utils_test.py',
    'tests/controllers/android_lib/android_lib_unittest_bundle.py',
    'tests/event/event_unittest_bundle.py',
    'tests/test_utils/instrumentation/unit_test_suite.py',
    'tests/libs/logging/logging_unittest_bundle.py',
    'tests/metrics/unittest_bundle.py',
    'tests/libs/proc/proc_unittest_bundle.py',
    'tests/controllers/sl4a_lib/test_suite.py',
    'tests/test_runner_test.py',
    'tests/libs/version_selector_test.py',
]

# The number of seconds to wait before considering the unit test to have timed
# out.
UNITTEST_TIMEOUT = 60


class ActsUnitTest(base_test.BaseTestClass):
    """A class to run the ACTS unit tests in parallel.

    This is a hack to run the ACTS unit tests through CI. Please use the main
    function below if you need to run these tests.
    """

    def test_units(self):
        """Runs all the ACTS unit tests in parallel."""
        acts_unittest_path = os.path.dirname(acts.__path__[0])
        test_processes = []

        fail_test = False

        for unittest_file in UNITTEST_FILES:
            file_path = os.path.join(acts_unittest_path, unittest_file)
            test_processes.append(
                subprocess.Popen(
                    file_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT))

        for test_process in test_processes:
            killed = False
            try:
                stdout, _ = test_process.communicate(timeout=UNITTEST_TIMEOUT)
            except subprocess.TimeoutExpired:
                killed = True
                self.log.error('Unit test %s timed out after %s seconds.' %
                               (test_process.args, UNITTEST_TIMEOUT))
                test_process.kill()
                stdout, _ = test_process.communicate()
            if test_process.returncode != 0 or killed:
                self.log.error('=' * 79)
                self.log.error('Unit Test %s failed with error %s.' %
                               (test_process.args, test_process.returncode))
                self.log.error('=' * 79)
                self.log.error(stdout.decode('utf-8', errors='replace'))
                fail_test = True
            else:
                self.log.debug(stdout.decode('utf-8', errors='replace'))

        if fail_test:
            raise signals.TestFailure(
                'One or more unit tests failed. See the logs.')


def main():
    ActsUnitTest({'log': logging.getLogger()}).test_units()


if __name__ == '__main__':
    main()
