#!/usr/bin/env python3.4

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

import unittest

from acts.libs.proc import job


class JobTestCases(unittest.TestCase):
    def test_run_success(self):
        """Test running a simple shell command."""
        result = job.run('echo TEST')
        self.assertTrue(result.stdout.startswith('TEST'))

    def test_run_stderr(self):
        """Test that we can read process stderr."""
        result = job.run('echo TEST 1>&2')
        self.assertEqual(len(result.stdout), 0)
        self.assertTrue(result.stderr.startswith('TEST'))

    def test_run_error(self):
        """Test that we raise on non-zero exit statuses."""
        self.assertRaises(job.Error, job.run, 'exit 1')

    def test_run_error(self):
        """Test that we can ignore exit status on request."""
        result = job.run('exit 1', ignore_status=True)
        self.assertEqual(result.exit_status, 1)

    def test_run_timeout(self):
        """Test that we correctly implement command timeouts."""
        self.assertRaises(job.Error, job.run, 'sleep 5', timeout=0.1)

    def test_run_no_shell(self):
        """Test that we handle running without a wrapping shell."""
        echo_path = job.run('which echo').stdout.strip()
        result = job.run([echo_path, 'TEST'])
        self.assertTrue(result.stdout.startswith('TEST'))

    def test_job_env(self):
        """Test that we can set environment variables correctly."""
        result = job.run('printenv', env={'MYTESTVAR': '20'})
        self.assertIn('MYTESTVAR=20', result.stdout)


if __name__ == '__main__':
    unittest.main()
