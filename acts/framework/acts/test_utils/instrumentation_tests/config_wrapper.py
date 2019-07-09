#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import copy
import os


class InvalidParamError(Exception):
    pass


class ConfigWrapper(object):
    """Class representing a test or preparer config."""

    def __init__(self, config):
        """Initialize a InstrumentationTestConfig

        Args:
            config: A dict representing the preparer/test parameters
        """
        self._config = copy.deepcopy(config)

    def __getitem__(self, item):
        """Wrapper around self._config. In contrast to self.get, this method
        will raise a KeyError if the key is not found.
        """
        return self._config[item]

    def get(self, param_name, default=None, verify_fn=lambda _: True,
            failure_msg=''):
        """Get parameter from config, verifying that the value is valid
        with verify_fn.

        Args:
            param_name: Name of the param to fetch
            default: Default value of param.
            verify_fn: Callable to verify the param value. If it returns False,
                an exception will be raised.
            failure_msg: Exception message upon verify_fn failure.
        """
        result = self._config.get(param_name, default)
        if not verify_fn(result):
            raise InvalidParamError('Invalid value %s for param %s. %s'
                                    % (result, param_name, failure_msg))
        return result

    def get_int(self, param_name, default=None):
        """Get integer parameter from config. Will raise an exception
        if result is not of type int.
        """
        return self.get(param_name, default=default,
                        verify_fn=lambda val: type(val) is int,
                        failure_msg='Param must be of type int.')

    def get_float(self, param_name, default=None):
        """Get float parameter from config. Will raise an exception if
        result is not of type float.
        """
        return self.get(param_name, default=default,
                        verify_fn=lambda val: type(val) is float,
                        failure_msg='Param must be of type float.')

    def get_files(self, param_name):
        """Get list of file paths from config. Will raise an exception if any
        of the paths do not point to actual files/directories.
        """
        return self.get(param_name,
                        verify_fn=lambda l: all(map(os.path.exists, l)),
                        failure_msg='Cannot resolve one or more paths.')

    def get_file(self, param_name):
        """Get single file path from config."""
        return self.get_files(param_name)[0]
