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
import logging
import os
import sys
from logging import FileHandler
from logging import Handler
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from acts import context
from acts.event import event_bus
from acts.event.decorators import subscribe_static


# yapf: disable
class LogStyles:
    NONE         = 0x00
    LOG_DEBUG    = 0x01
    LOG_INFO     = 0x02
    LOG_WARNING  = 0x04
    LOG_ERROR    = 0x08
    LOG_CRITICAL = 0x10

    DEFAULT_LEVELS = LOG_DEBUG + LOG_INFO + LOG_ERROR
    ALL_LEVELS = LOG_DEBUG + LOG_INFO + LOG_WARNING + LOG_ERROR + LOG_CRITICAL

    MONOLITH_LOG  = 0x0100
    TESTCLASS_LOG = 0x0200
    TESTCASE_LOG  = 0x0400
    TO_STDOUT     = 0x0800
    TO_ACTS_LOG   = 0x1000
    ROTATE_LOGS   = 0x2000

    ALL_FILE_LOGS = MONOLITH_LOG + TESTCLASS_LOG + TESTCASE_LOG

    LEVEL_NAMES = {
        LOG_DEBUG: 'debug',
        LOG_INFO: 'info',
        LOG_WARNING: 'warning',
        LOG_ERROR: 'error',
        LOG_CRITICAL: 'critical',
    }

    LOG_LEVELS = [
        LOG_DEBUG,
        LOG_INFO,
        LOG_WARNING,
        LOG_ERROR,
        LOG_CRITICAL,
    ]

    LOG_LOCATIONS = [
        TO_STDOUT,
        TO_ACTS_LOG,
        MONOLITH_LOG,
        TESTCLASS_LOG,
        TESTCASE_LOG
    ]

    LEVEL_TO_NO = {
        LOG_DEBUG: logging.DEBUG,
        LOG_INFO: logging.INFO,
        LOG_WARNING: logging.WARNING,
        LOG_ERROR: logging.ERROR,
        LOG_CRITICAL: logging.CRITICAL,
    }
# yapf: enable


_log_streams = dict()
_null_handler = logging.NullHandler()


@subscribe_static(context.NewContextEvent)
def _update_handlers(event):
    for log_stream in _log_streams.values():
        log_stream.update_handlers(event)


def create_logger(name, log_name=None, base_path='', subcontext='',
                  log_styles=LogStyles.NONE, stream_format=None,
                  file_format=None):
    """Creates a Python Logger object with the given attributes.

    Creation through this method will automatically manage the logger in the
    background for test-related events, such as TestCaseBegin and TestCaseEnd
    Events.

    Args:
        name: The name of the LogStream. Used as the file name prefix.
        log_name: The name of the underlying logger. Use LogStream name as
            default.
        base_path: The base path used by the logger.
        subcontext: Location of logs relative to the test context path.
        log_styles: An integer or array of integers that are the sum of
            corresponding flag values in LogStyles. Examples include:

            >>> LogStyles.LOG_INFO + LogStyles.TESTCASE_LOG

            >>> LogStyles.ALL_LEVELS + LogStyles.MONOLITH_LOG

            >>> [LogStyles.DEFAULT_LEVELS + LogStyles.MONOLITH_LOG]
            >>>  LogStyles.LOG_ERROR + LogStyles.TO_ACTS_LOG]
        stream_format: Format used for log output to stream
        file_format: Format used for log output to files
    """
    if name in _log_streams:
        _log_streams[name].cleanup()
    log_stream = _LogStream(name, log_name, base_path, subcontext, log_styles,
                            stream_format, file_format)
    _set_logger(log_stream)
    return log_stream.logger


def _set_logger(log_stream):
    _log_streams[log_stream.name] = log_stream
    return log_stream


event_bus.register_subscription(_update_handlers.subscription)


class AlsoToLogHandler(Handler):
    """Logs a message at a given level also to another logger.

    Used for logging messages at a high enough level to the main log, or another
    logger.
    """

    def __init__(self, to_logger=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = logging.getLogger(to_logger)

    def emit(self, record):
        self._log.log(record.levelno, record.message)


class InvalidStyleSetError(Exception):
    """Raised when the given LogStyles are an invalid set."""


class _LogStream(object):
    """A class that sets up a logging.Logger object.

    The LogStream class creates a logging.Logger object. LogStream is also
    responsible for managing the logger when events take place, such as
    TestCaseEndedEvents and TestCaseBeginEvents.

    Attributes:
        name: The name of the LogStream.
        logger: The logger created by this LogStream.
        base_path: The base path used by the logger. Use logging.log_path
            as default.
        subcontext: Location of logs relative to the test context path.
        stream_format: Format used for log output to stream
        file_format: Format used for log output to files

        _test_case_handler_descriptors: The list of HandlerDescriptors that are
            used to create LogHandlers for each new test case.
        _test_case_log_handlers: The list of current LogHandlers for the current
            test case.
    """

    class HandlerDescriptor(object):
        """A object that describes how to create a LogHandler.

        Attributes:
            _base_name: The name of the file generated by the FileLogHandler.
            _creator: The callable that creates the FileLogHandler.
            _level: The logging level (INFO, DEBUG, etc) for this handler.
            _file_format: Format of generated log strings
        """

        def __init__(self, creator, level, name, file_format=None):
            self._base_name = '%s_%s.txt' % (name, LogStyles.LEVEL_NAMES[level])
            self._creator = creator
            self._level = LogStyles.LEVEL_TO_NO[level]
            self._file_format = file_format

        def create(self, directory=''):
            """Creates the FileLogHandler described by this HandlerDescriptor.

            Args:
                directory: The directory name for the file to be created under.
            """
            os.makedirs(directory, exist_ok=True)
            handler = self._creator(os.path.join(directory, self._base_name))
            handler.setLevel(self._level)
            if self._file_format:
                handler.setFormatter(self._file_format)
            return handler

    def __init__(self, name, log_name=None, base_path='', subcontext='',
                 log_styles=LogStyles.NONE, stream_format=None,
                 file_format=None):
        """Creates a LogStream.

        Args:
            name: The name of the LogStream. Used as the file name prefix.
            log_name: The name of the underlying logger. Use LogStream name
                as default.
            base_path: The base path used by the logger. Use logging.log_path
                as default.
            subcontext: Location of logs relative to the test context path.
            log_styles: An integer or array of integers that are the sum of
                corresponding flag values in LogStyles. Examples include:

                >>> LogStyles.LOG_INFO + LogStyles.TESTCASE_LOG

                >>> LogStyles.ALL_LEVELS + LogStyles.MONOLITH_LOG

                >>> [LogStyles.DEFAULT_LEVELS + LogStyles.MONOLITH_LOG]
                >>>  LogStyles.LOG_ERROR + LogStyles.TO_ACTS_LOG]
            stream_format: Format used for log output to stream
            file_format: Format used for log output to files
        """
        self.name = name
        if log_name is not None:
            self.logger = logging.getLogger(log_name)
        else:
            self.logger = logging.getLogger(name)
        # Add a NullHandler to suppress unwanted console output
        self.logger.addHandler(_null_handler)
        self.logger.propagate = False
        self.base_path = base_path or logging.log_path
        self.subcontext = subcontext
        context.TestContext.add_base_output_path(self.logger.name, self.base_path)
        context.TestContext.add_subcontext(self.logger.name, self.subcontext)
        self.stream_format = stream_format
        self.file_format = file_format
        self._monolith_descriptors = []
        self._monolith_handlers = []
        self._testclass_descriptors = []
        self._testclass_handlers = []
        self._testcase_descriptors = []
        self._testcase_handlers = []
        if not isinstance(log_styles, list):
            log_styles = [log_styles]
        self.__validate_styles(log_styles)
        for log_style in log_styles:
            self.__handle_style(log_style)
        self.__create_handlers_from_descriptors(
            self._monolith_descriptors, self._monolith_handlers)
        self.__create_handlers_from_descriptors(
            self._testclass_descriptors, self._testclass_handlers)
        self.__create_handlers_from_descriptors(
            self._testcase_descriptors, self._testcase_handlers)

    @staticmethod
    def __validate_styles(_log_styles_list):
        """Determines if the given list of styles is valid.

        Terminology:
            Log-level: any of [DEBUG, INFO, WARNING, ERROR, CRITICAL].
            Log Location: any of [MONOLITH_LOG, TESTCLASS_LOG,
                                  TESTCASE_LOG, TO_STDOUT, TO_ACTS_LOG].

        Styles are invalid when any of the below criteria are met:
            A log-level is not set within an element of the list.
            A log location is not set within an element of the list.
            A log-level, log location pair appears twice within the list.
            A log-level has both TESTCLASS and TESTCASE locations set
                within the list.
            ROTATE_LOGS is set without MONOLITH_LOG,
                TESTCLASS_LOG, or TESTCASE_LOG.

        Raises:
            InvalidStyleSetError if the given style cannot be achieved.
        """

        def invalid_style_error(message):
            raise InvalidStyleSetError('{LogStyle Set: %s} %s' %
                                       (_log_styles_list, message))

        # Store the log locations that have already been set per level.
        levels_dict = {}
        for log_style in _log_styles_list:
            for level in LogStyles.LOG_LEVELS:
                if log_style & level:
                    levels_dict[level] = levels_dict.get(level, LogStyles.NONE)
                    # Check that a log-level, log location pair has not yet
                    # been set.
                    for log_location in LogStyles.LOG_LOCATIONS:
                        if log_style & log_location:
                            if log_location & levels_dict[level]:
                                invalid_style_error(
                                    'The log location %s for log level %s has '
                                    'been set multiple times' %
                                    (log_location, level))
                            else:
                                levels_dict[level] |= log_location
                    # Check that for a given log-level, not more than one
                    # of MONOLITH_LOG, TESTCLASS_LOG, TESTCASE_LOG is set.
                    locations = levels_dict[level] & LogStyles.ALL_FILE_LOGS
                    valid_locations = [
                        LogStyles.TESTCASE_LOG, LogStyles.TESTCLASS_LOG,
                        LogStyles.MONOLITH_LOG, LogStyles.NONE]
                    if locations not in valid_locations:
                        invalid_style_error(
                            'More than one of MONOLITH_LOG, TESTCLASS_LOG, '
                            'TESTCASE_LOG is set for log level %s.' % level)
            if log_style & LogStyles.ALL_LEVELS == 0:
                invalid_style_error('LogStyle %s needs to set a log '
                                    'level.' % log_style)
            if log_style & ~LogStyles.ALL_LEVELS == 0:
                invalid_style_error('LogStyle %s needs to set a log '
                                    'location.' % log_style)
            if log_style & LogStyles.ROTATE_LOGS and not log_style & (
                    LogStyles.MONOLITH_LOG | LogStyles.TESTCLASS_LOG |
                    LogStyles.TESTCASE_LOG):
                invalid_style_error('LogStyle %s has ROTATE_LOGS set, but does '
                                    'not specify a log type.' % log_style)

    @staticmethod
    def __create_rotating_file_handler(filename):
        """Generates a callable to create an appropriate RotatingFileHandler."""
        # Magic number explanation: 10485760 == 10MB
        return RotatingFileHandler(filename, maxBytes=10485760)

    @staticmethod
    def __get_file_handler_creator(log_style):
        """Gets the callable to create the correct FileLogHandler."""
        create_file_handler = FileHandler
        if log_style & LogStyles.ROTATE_LOGS:
            create_file_handler = _LogStream.__create_rotating_file_handler
        return create_file_handler

    @staticmethod
    def __get_lowest_log_level(log_style):
        """Returns the lowest log level's LogStyle for the given log_style."""
        for log_level in LogStyles.LOG_LEVELS:
            if log_level & log_style:
                return log_level
        return LogStyles.NONE

    def __handle_style(self, log_style):
        """Creates the handlers described in the given log_style."""
        handler_creator = self.__get_file_handler_creator(log_style)

        # Handle streaming logs to STDOUT or the ACTS Logger
        if log_style & (LogStyles.TO_ACTS_LOG | LogStyles.TO_STDOUT):
            lowest_log_level = self.__get_lowest_log_level(log_style)

            if log_style & LogStyles.TO_ACTS_LOG:
                handler = AlsoToLogHandler()
            else:  # LogStyles.TO_STDOUT:
                handler = StreamHandler(sys.stdout)
                if self.stream_format:
                    handler.setFormatter(self.stream_format)

            handler.setLevel(LogStyles.LEVEL_TO_NO[lowest_log_level])
            self.logger.addHandler(handler)

        # Handle streaming logs to log-level files
        for log_level in LogStyles.LOG_LEVELS:
            if not (log_style & log_level and
                    log_style & LogStyles.ALL_FILE_LOGS):
                continue
            descriptor = self.HandlerDescriptor(handler_creator, log_level,
                                                self.name, self.file_format)

            if log_style & LogStyles.MONOLITH_LOG:
                self._monolith_descriptors.append(descriptor)
            if log_style & LogStyles.TESTCLASS_LOG:
                self._testclass_descriptors.append(descriptor)
            if log_style & LogStyles.TESTCASE_LOG:
                self._testcase_descriptors.append(descriptor)

    def __remove_handler(self, handler):
        """Removes a handler from the logger, unless it's a NullHandler."""
        if handler is not _null_handler:
            handler.close()
            self.logger.removeHandler(handler)

    def __create_handlers_from_descriptors(self, descriptors, handlers):
        """Create new handlers as described in the descriptors list"""
        if descriptors:
            curr_context = context.get_current_context()
            if curr_context is None:
                output_path = os.path.join(self.base_path, self.subcontext)
            else:
                output_path = curr_context.get_full_output_path(self.logger.name)
            for descriptor in descriptors:
                handler = descriptor.create(output_path)
                self.logger.addHandler(handler)
                handlers.append(handler)

    def __clear_handlers(self, handlers):
        """Close and remove all handlers"""
        for log_handler in handlers:
            self.__remove_handler(log_handler)
        handlers.clear()

    def update_handlers(self, event):
        """Update the output file paths for log handlers upon a change in
        the test context.

        Args:
            event: An instance of NewContextEvent.
        """
        if isinstance(event, context.NewTestClassContextEvent):
            self.__clear_handlers(self._testclass_handlers)
            self.__create_handlers_from_descriptors(
                self._testclass_descriptors, self._testclass_handlers)
            self.__clear_handlers(self._testcase_handlers)
            self.__create_handlers_from_descriptors(
                self._testcase_descriptors, self._testcase_handlers)
        if isinstance(event, context.NewTestCaseContextEvent):
            self.__clear_handlers(self._testcase_handlers)
            self.__create_handlers_from_descriptors(
                self._testcase_descriptors, self._testcase_handlers)

    def cleanup(self):
        """Removes all LogHandlers from the logger."""
        for handler in self.logger.handlers:
            self.__remove_handler(handler)
