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

import os
import logging

from acts.event.event import TestCaseEvent
from acts.event.event import TestClassEvent


def get_context_for_event(event):
    if isinstance(event, TestCaseEvent):
        return _get_context_for_test_case_event(event)
    if isinstance(event, TestClassEvent):
        return _get_context_for_test_class_event(event)
    raise TypeError('Unrecognized event type: %s %s', event, event.__class__)

def _get_context_for_test_case_event(event):
    return TestCaseContext(event.test_class, event.test_case)


def _get_context_for_test_class_event(event):
    return TestClassContext(event.test_class)


class TestContext(object):
    """An object representing the current context in which a test is executing.

    The context encodes the current state of the test runner with respect to a
    particular scenario in which code is being executed. For example, if some
    code is being executed as part of a test case, then the context should
    encode information about that test case such as its name or enclosing
    class.

    Attributes:
        _base_output_path_override: an override of the base output path to use.
        _output_dir_override: an override of the output directory specific to
                              the represented context.
    """

    def __init__(self):
        self._base_output_path_override = None
        self._output_dir_override = None

    def get_base_output_path(self):
        """Gets the base output path for this context.

        The base output path is interpreted as the reporting root for the
        entire test runner.

        If a path has been set by set_base_output_path, it is returned.
        Otherwise, a default is determined by _get_default_base_output_path().

        Returns:
              The output path.
        """
        if self._base_output_path_override:
            return self._base_output_path_override
        return self._get_default_base_output_path()

    def set_base_output_path(self, base_output_path):
        """Sets the base output path for this context.

        The base output path is interpreted as the reporting root for the
        entire test runner. However, setting this value here will not affect
        the test runner itself in any way, only the interpretation of this
        context object.

        Args:
            base_output_path: The path to set.
        """
        self._base_output_path_override = base_output_path

    def get_output_dir(self):
        """Gets the output directory for this context.

        This represents the directory for all outputs specific to this context.
        This directory will be interpreted as being relative to the base output
        path as determined by get_base_output_path.

        Returns:
            The output directory.
        """
        if self._output_dir_override:
            return self._output_dir_override
        return self._get_default_output_dir()

    def set_output_dir(self, output_dir):
        """Sets the output directory for this context.

        This represents the directory for all outputs specific to this context.
        This directory will be interpreted as being relative to the base output
        path as determined by get_base_output_path.

        Args:
            output_dir: The directory to set.
        """
        self._output_dir_override = output_dir

    def get_full_output_path(self):
        """Gets the full output path for this context.

        This is the absolute path to the context specific output directory
        provided by get_output_dir().

        Returns:
            The output path.
        """
        path = os.path.join(self.get_base_output_path(), self.get_output_dir())
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    @property
    def identifier(self):
        raise NotImplementedError()

    def _get_default_base_output_path(self):
        """Gets the default base output path.

        This will attempt to use the ACTS logging path set up in the global
        logger.

        Returns:
            The logging path.

        Raises:
            EnvironmentError: If the ACTS logger has not been initialized.
        """
        try:
            return logging.log_path
        except AttributeError as e:
            raise EnvironmentError(
                'The ACTS logger has not been set up and'
                ' "base_output_path" has not been set.') from e

    def _get_default_output_dir(self):
        """Gets the default output directory for this context."""
        raise NotImplementedError()


class TestClassContext(TestContext):
    """A TestContext that represents a test class.

    Attributes:
        test_class: The test class instance that this context represents.
    """

    def __init__(self, test_class):
        """Initializes a TestClassContext for the given test class.

        Args:
            test_class: A test class object. Must be an instance of the test
                        class, not the class object itself.
        """
        super().__init__()
        self.test_class = test_class

    @property
    def test_class_name(self):
        return self.test_class.__class__.__name__

    @property
    def identifier(self):
        return self.test_class_name

    def _get_default_output_dir(self):
        """Gets the default output directory for this context.

        For TestClassContexts, this will be the name of the test class. This is
        in line with the ACTS logger itself.
        """
        return self.test_class_name


class TestCaseContext(TestContext):
    """A TestContext that represents a test case.

    Attributes:
        test_case: The method object of the test case.
        test_class: The test class instance enclosing the test case.
    """

    def __init__(self, test_class, test_case):
        """Initializes a TestCaseContext for the given test case.

        Args:
            test_class: A test class object. Must be an instance of the test
                        class, not the class object itself.
            test_case: The string name of the test case.
        """
        super().__init__()
        self.test_class = test_class
        self.test_case = test_case

    @property
    def test_case_name(self):
        return self.test_class.test_name

    @property
    def test_class_name(self):
        return self.test_class.__class__.__name__

    @property
    def identifier(self):
        return '%s.%s' % (self.test_class_name, self.test_case_name)

    def _get_default_output_dir(self):
        """Gets the default output directory for this context.

        For TestCaseContexts, this will be the name of the test class followed
        by the name of the test case. This is in line with the ACTS logger
        itself.
        """
        return os.path.join(
            self.test_class_name,
            self.test_case_name)
