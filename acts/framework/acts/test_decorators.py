#!/usr/bin/env python3.4
#
# Copyright 2017 - The Android Open Source Project
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

from acts import signals


def test_info(**keyed_info):
    """Adds info about test.

    Extra Info to include about the test. This info will be available in the
    test output.

    Example:
        # This test will have a variable my_var
        @test_info(my_var='THIS IS MY TEST')
        def my_test(self):
            return False

    Args:
        func: The test case to wrap around.
        **keyed_info: The key, value info to include in the extras for this
                      test.
    """

    def test_info_decoractor(func):
        def func_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if result or result is None:
                    new_signal = signals.TestPass('')
                else:
                    new_signal = signals.TestFailure('')
            except signals.TestSignal as signal:
                new_signal = signal

            if not isinstance(new_signal.extras, dict) and new_signal.extras:
                raise ValueError('test_info can only append to signal data '
                                 'that has a dict as the extra value.')
            elif not new_signal.extras:
                new_signal.extras = {}

            for k, v in keyed_info.items():
                if k not in new_signal.extras:
                    new_signal.extras[k] = v

            raise new_signal

        return func_wrapper

    return test_info_decoractor


def test_tracker_info(uuid):
    """Decorator for adding test tracker info to tests results.

    Will add test tracker info inside of Extras/test_tracker_info.

    Example:
        # This test will be linked to test tracker uuid abcd
        @test_tracker_info(uuid='abcd')
        def my_test(self):
            return False

    Args:
        uuid: The uuid of the test case in test tracker.
    """
    tt_info = {'test_tracker_uuid': uuid}
    return test_info(test_tracker_info=tt_info)
