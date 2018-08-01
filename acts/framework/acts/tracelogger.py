#!/usr/bin/env python3
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

import inspect
import logging
import os


class TraceLogger(object):
    def __init__(self, logger):
        self._logger = logger

    @staticmethod
    def _get_trace_info(level=1, offset=2):
        # We want the stack frame above this and above the error/warning/info
        inspect_stack = inspect.stack()
        trace_info = ''
        for i in range(level):
            try:
                stack_frames = inspect_stack[offset + i]
                info = inspect.getframeinfo(stack_frames[0])
                trace_info = '%s[%s:%s:%s]' % (trace_info,
                                               os.path.basename(info.filename),
                                               info.function, info.lineno)
            except IndexError:
                break
        return trace_info

    def _log_with(self, logging_lambda, trace_level, msg, *args, **kwargs):
        trace_info = TraceLogger._get_trace_info(level=trace_level, offset=3)
        logging_lambda('%s %s' % (msg, trace_info), *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log_with(self._logger.exception, 5, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log_with(self._logger.debug, 3, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with(self._logger.error, 3, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._log_with(self._logger.warn, 1, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_with(self._logger.warning, 1, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_with(self._logger.info, 1, msg, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._logger, name)


class TakoTraceLogger(TraceLogger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.d = self.debug
        self.e = self.error
        self.i = self.info
        self.t = self.step
        self.w = self.warning

    def _logger_level(self, level_name):
        level = logging.getLevelName(level_name)
        return lambda *args, **kwargs: self._logger.log(level, *args, **kwargs)

    def step(self, msg, *args, **kwargs):
        """Delegate a step call to the underlying logger."""
        self._log_with(self._logger_level('STEP'), 1, msg, *args, **kwargs)

    def device(self, msg, *args, **kwargs):
        """Delegate a device call to the underlying logger."""
        self._log_with(self._logger_level('DEVICE'), 1, msg, *args, **kwargs)

    def suite(self, msg, *args, **kwargs):
        """Delegate a device call to the underlying logger."""
        self._log_with(self._logger_level('SUITE'), 1, msg, *args, **kwargs)

    def case(self, msg, *args, **kwargs):
        """Delegate a case call to the underlying logger."""
        self._log_with(self._logger_level('CASE'), 1, msg, *args, **kwargs)

    def flush_log(self):
        """This function exists for compatibility with Tako's logserial module.

        Note that flushing the log is handled automatically by python's logging
        module.
        """
        pass
