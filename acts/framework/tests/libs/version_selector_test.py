#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
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
import numbers

from acts.libs import version_selector
from tests.libs import test_module


def version_api(min_api=0, max_api=99999999999999):
    """Decorates a function to only be called for the given API level.

    Only gets called if the AndroidDevice in the args is within the specified
    API range. Otherwise, a different function may be called instead. If the
    API level is out of range, and no other function handles that API level, an
    error is raise instead.

    Note: In Python3.5 and below, the order of kwargs is not preserved. If your
          function contains multiple AndroidDevices within the kwargs, and no
          AndroidDevices within args, you are NOT guaranteed the first
          AndroidDevice is the same one chosen each time the function runs. Due
          to this, we do not check for AndroidDevices in kwargs.

    Args:
         min_api: The minimum API level. Can be an int or an AndroidApi value.
         max_api: The maximum API level. Can be an int or an AndroidApi value.
    """
    def get_api_level(*args, **kwargs):
        # raise ValueError(
        #     'No AndroidDevice found within the function parameters.')
        for arg in args:
            if isinstance(arg, numbers.Number):
                return arg
        for kwarg, value in kwargs:
            if isinstance(value, numbers.Number):
                return value

    return version_selector.set_version(get_api_level, min_api, max_api)


@version_api(min_api=1, max_api=1)
def test2(arg1):
    print('1: %s' % arg1)


@version_api(min_api=2, max_api=2)
def test2(arg1):
    print('2: %s' % arg1)


class TestClass(object):
    class Inner(object):
        @android_api(min_api=4, max_api=4)
        def test(self):
            print('self: %s' % self)

    @staticmethod
    @version_api(0, 0)
    def test_static(arg1):
        print('Static1: %s' % arg1)

    @staticmethod
    @version_api(1, 2)
    def test_static(arg1):
        print('Static2: %s' % arg1)

    @staticmethod
    @version_api(5, 8)
    def test_static(arg1):
        print('Static3: %s' % arg1)

    @classmethod
    @version_api(1, 1)
    def test_class(cls, arg1):
        print('Class1: %s, %s' % (cls, arg1))

    @classmethod
    @version_api(2, 2)
    def test_class(cls, arg1):
        print('Class2: %s, %s' % (cls, arg1))

    @version_api(1, 1)
    def test_instance(self, arg1):
        print('Self1: %s, %s' % (self, arg1))

    @version_api(2, 2)
    def test_instance(self, arg1):
        print('Self2: %s, %s' % (self, arg1))

    @version_api(3, 3)
    def test_instance(self, arg1):
        print('Self3: %s, %s' % (self, arg1))


if __name__ == '__main__':
    tc = TestClass()
    tc.test_static(1)
    tc.test_static(2)
    tc.test_static(5)

    tc.test_class(1)
    tc.test_class(2)

    tc.test_instance(1)
    tc.test_instance(2)
    tc.test_instance(3)

    test2(1, 'a')
    test2(2, 'b')

    test_module.test2(1, 'a')
    test_module.test2(2, 'b')

    tc2 = test_module.TestClass()
    tc2.test_static(1)
    tc2.test_static(2)
    tc2.test_static(3)

    tc2.test_class(1)
    tc2.test_class(2)

    tc2.test_instance(1)
    tc2.test_instance(2)
    tc2.test_instance(3)