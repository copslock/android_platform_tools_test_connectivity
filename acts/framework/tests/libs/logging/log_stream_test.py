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
import unittest

import mock

from acts import context
from acts.libs.logging import log_stream
from acts.libs.logging.log_stream import AlsoToLogHandler
from acts.libs.logging.log_stream import _LogStream
from acts.libs.logging.log_stream import InvalidStyleSetError
from acts.libs.logging.log_stream import LogStyles


class TestClass(object):
    """Dummy class for TestEvents"""
    def __init__(self):
        self.test_name = self.test_case.__name__

    def test_case(self):
        """Dummy test case for test events."""


class LogStreamTest(unittest.TestCase):
    """Tests the _LogStream class in acts.libs.logging.log_stream."""

    @staticmethod
    def patch(imported_name, *args, **kwargs):
        return mock.patch('acts.libs.logging.log_stream.%s' % imported_name,
                          *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        # logging.log_path only exists if logger._setup_test_logger is called.
        # Here we set it to a value that is likely to not exist so file IO is
        # not executed (an error is raised instead of creating the file).
        logging.log_path = '/f/a/i/l/p/a/t/h'

    def setUp(self):
        log_stream._log_streams = dict()

    # __init__

    @mock.patch('os.makedirs')
    def test_init_adds_null_handler(self, *_):
        """Tests that a NullHandler is added to the logger upon initialization.
        This ensures that no log output is generated when a test class is not
        running.
        """
        debug_monolith_log = LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG
        with self.patch('FileHandler'):
            log = log_stream.create_logger(self._testMethodName,
                                           log_styles=debug_monolith_log)

        self.assertTrue(isinstance(log.handlers[0], logging.NullHandler))

    # __validate_style

    @mock.patch('os.makedirs')
    def test_validate_styles_raises_when_same_location_set_multiple_times(
            self, *_):
        """Tests that a style is invalid if it sets the same handler twice.

        If the error is NOT raised, then a LogStream can create a Logger that
        has multiple LogHandlers trying to write to the same file.
        """
        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(
                self._testMethodName,
                log_styles=[LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG,
                            LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG])
        self.assertTrue(
            'has been set multiple' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

    @mock.patch('os.makedirs')
    def test_validate_styles_raises_when_multiple_file_outputs_set(
            self, *_):
        """Tests that a style is invalid if more than one of MONOLITH_LOG,
        TESTCLASS_LOG, and TESTCASE_LOG is set for the same log level.

        If the error is NOT raised, then a LogStream can create a Logger that
        has multiple LogHandlers trying to write to the same file.
        """
        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(
                self._testMethodName,
                log_styles=[LogStyles.LOG_DEBUG | LogStyles.TESTCASE_LOG,
                            LogStyles.LOG_DEBUG | LogStyles.TESTCLASS_LOG])
        self.assertTrue(
            'More than one of' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(
                self._testMethodName,
                log_styles=[LogStyles.LOG_DEBUG | LogStyles.TESTCASE_LOG,
                            LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG])
        self.assertTrue(
            'More than one of' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(
                self._testMethodName,
                log_styles=[LogStyles.LOG_DEBUG | LogStyles.TESTCASE_LOG,
                            LogStyles.LOG_DEBUG | LogStyles.TESTCLASS_LOG,
                            LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG])
        self.assertTrue(
            'More than one of' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

    @mock.patch('os.makedirs')
    def test_validate_styles_raises_when_no_level_exists(self, *_):
        """Tests that a style is invalid if it does not contain a log level.

        If the style does not contain a log level, then there is no way to
        pass the information coming from the logger to the correct file.
        """
        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(self._testMethodName,
                                     log_styles=[LogStyles.MONOLITH_LOG])

        self.assertTrue(
            'log level' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

    @mock.patch('os.makedirs')
    def test_validate_styles_raises_when_no_location_exists(self, *_):
        """Tests that a style is invalid if it does not contain a log level.

        If the style does not contain a log level, then there is no way to
        pass the information coming from the logger to the correct file.
        """
        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(self._testMethodName,
                                     log_styles=[LogStyles.LOG_INFO])

        self.assertTrue(
            'log location' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

    @mock.patch('os.makedirs')
    def test_validate_styles_raises_when_rotate_logs_no_file_handler(self, *_):
        """Tests that a LogStyle cannot set ROTATE_LOGS without *_LOG flag.

        If the LogStyle contains ROTATE_LOGS, it must be associated with a log
        that is rotatable. TO_ACTS_LOG and TO_STDOUT are not rotatable logs,
        since those are both controlled by another object/process. The user
        must specify MONOLITHIC_LOG or TESTCASE_LOG.
        """
        with self.assertRaises(InvalidStyleSetError) as catch:
            log_stream.create_logger(
                self._testMethodName,
                # Added LOG_DEBUG here to prevent the no_level_exists raise from
                # occurring.
                log_styles=[LogStyles.LOG_DEBUG + LogStyles.ROTATE_LOGS])

        self.assertTrue(
            'log type' in catch.exception.args[0],
            msg='__validate_styles did not raise the expected error message')

    # __handle_style

    @mock.patch('os.makedirs')
    def test_handle_style_create_monolith_descriptors(self, *_):
        """Tests that handle_style creates the correct monolith descriptors.

        The above descriptors are only created on MONOLITH_LOG logstyles.
        """
        info_monolith_log = LogStyles.LOG_INFO + LogStyles.MONOLITH_LOG

        with self.patch('FileHandler'):
            log_stream.create_logger(self._testMethodName,
                                     log_styles=info_monolith_log)

        created_stream = log_stream._log_streams[self._testMethodName]
        monolith_descriptors = created_stream._monolith_descriptors

        self.assertEqual(len(monolith_descriptors), 1,
                         'There should be exactly 1 test class handler'
                         'descriptor created.')
        self.assertEqual(monolith_descriptors[0]._level, logging.INFO)

    @mock.patch('os.makedirs')
    def test_handle_style_create_test_class_descriptors(self, *_):
        """Tests that handle_style creates the correct test class descriptors.

        The above descriptors are only created on TESTCLASS_LOG logstyles.
        """
        info_testclass_log = LogStyles.LOG_INFO + LogStyles.TESTCLASS_LOG

        with self.patch('FileHandler'):
            log_stream.create_logger(self._testMethodName,
                                     log_styles=info_testclass_log)

        created_stream = log_stream._log_streams[self._testMethodName]
        class_descriptors = created_stream._testclass_descriptors

        self.assertEqual(len(class_descriptors), 1,
                         'There should be exactly 1 test class handler'
                         'descriptor created.')
        self.assertEqual(class_descriptors[0]._level, logging.INFO)

    @mock.patch('os.makedirs')
    def test_handle_style_create_test_case_descriptors(self, *_):
        """Tests that handle_style creates the correct test case descriptors.

        The above descriptors are only created on TESTCASE_LOG logstyles.
        """
        info_testcase_log = LogStyles.LOG_INFO + LogStyles.TESTCASE_LOG

        with self.patch('FileHandler'):
            log_stream.create_logger(self._testMethodName,
                                     log_styles=info_testcase_log)

        created_stream = log_stream._log_streams[self._testMethodName]
        case_descriptors = created_stream._testcase_descriptors

        self.assertEqual(len(case_descriptors), 1,
                         'There should be exactly 1 testcase handler'
                         'descriptor created.')
        self.assertEqual(case_descriptors[0]._level, logging.INFO)

    @mock.patch('os.makedirs')
    def test_handle_style_to_acts_log_creates_handler(self, *_):
        """Tests that using the flag TO_ACTS_LOG creates an AlsoToLogHandler."""
        info_acts_log = LogStyles.LOG_INFO + LogStyles.TO_ACTS_LOG

        log = log_stream.create_logger(self._testMethodName,
                                       log_styles=info_acts_log)

        self.assertTrue(isinstance(log.handlers[1], AlsoToLogHandler))

    @mock.patch('os.makedirs')
    def test_handle_style_to_acts_log_creates_handler_is_lowest_level(self, *_):
        """Tests that using the flag TO_ACTS_LOG creates an AlsoToLogHandler
        that is set to the lowest LogStyles level."""
        info_acts_log = (LogStyles.LOG_DEBUG + LogStyles.LOG_INFO +
                         LogStyles.TO_ACTS_LOG)

        log = log_stream.create_logger(self._testMethodName,
                                       log_styles=info_acts_log)

        self.assertTrue(isinstance(log.handlers[1], AlsoToLogHandler))
        self.assertEqual(log.handlers[1].level, logging.DEBUG)

    @mock.patch('os.makedirs')
    def test_handle_style_to_stdout_creates_stream_handler(self, *_):
        """Tests that using the flag TO_STDOUT creates a StreamHandler."""
        info_acts_log = LogStyles.LOG_INFO + LogStyles.TO_STDOUT

        log = log_stream.create_logger(self._testMethodName,
                                       log_styles=info_acts_log)

        self.assertTrue(isinstance(log.handlers[1], logging.StreamHandler))

    @mock.patch('os.makedirs')
    def test_handle_style_creates_file_handler(self, *_):
        """Tests handle_style creates a FileHandler for the MONOLITH_LOG."""
        info_acts_log = LogStyles.LOG_INFO + LogStyles.MONOLITH_LOG

        expected = mock.MagicMock()
        with self.patch('FileHandler', return_value=expected):
            log = log_stream.create_logger(self._testMethodName,
                                           log_styles=info_acts_log)

        self.assertEqual(log.handlers[1], expected)

    @mock.patch('os.makedirs')
    def test_handle_style_creates_rotating_file_handler(self, *_):
        """Tests handle_style creates a FileHandler for the ROTATE_LOGS."""
        info_acts_log = (LogStyles.LOG_INFO + LogStyles.ROTATE_LOGS +
                         LogStyles.MONOLITH_LOG)

        expected = mock.MagicMock()
        with self.patch('RotatingFileHandler', return_value=expected):
            log = log_stream.create_logger(self._testMethodName,
                                           log_styles=info_acts_log)

        self.assertEqual(log.handlers[1], expected)

    # __create_rotating_file_handler

    @mock.patch('os.makedirs')
    def test_create_rotating_file_handler_does_what_it_says_it_does(self, *_):
        """Tests that __create_rotating_file_handler does exactly that."""
        expected = mock.MagicMock()

        with self.patch('RotatingFileHandler', return_value=expected):
            # Through name-mangling, this function is automatically renamed. See
            # https://docs.python.org/3/tutorial/classes.html#private-variables
            fh = _LogStream._LogStream__create_rotating_file_handler('')

        self.assertEqual(expected, fh,
                         'The function did not return a RotatingFileHandler.')

    # __get_file_handler_creator

    @mock.patch('os.makedirs')
    def test_get_file_handler_creator_returns_rotating_file_handler(self, *_):
        """Tests the function returns a RotatingFileHandler when the log_style
        has LogStyle.ROTATE_LOGS."""
        expected = mock.MagicMock()

        with self.patch('_LogStream._LogStream__create_rotating_file_handler',
                        return_value=expected):
            # Through name-mangling, this function is automatically renamed. See
            # https://docs.python.org/3/tutorial/classes.html#private-variables
            fh_creator = _LogStream._LogStream__get_file_handler_creator(
                LogStyles.ROTATE_LOGS)

        self.assertEqual(expected, fh_creator('/d/u/m/m/y/p/a/t/h'),
                         'The function did not return a RotatingFileHandler.')

    @mock.patch('os.makedirs')
    def test_get_file_handler_creator_returns_file_handler(self, *_):
        """Tests the function returns a FileHandler when the log_style does NOT
        have LogStyle.ROTATE_LOGS."""
        expected = mock.MagicMock()

        with self.patch('FileHandler', return_value=expected):
            # Through name-mangling, this function is automatically renamed. See
            # https://docs.python.org/3/tutorial/classes.html#private-variables
            handler = _LogStream._LogStream__get_file_handler_creator(
                LogStyles.NONE)()

        self.assertTrue(isinstance(handler, mock.Mock))

    # __get_lowest_log_level

    @mock.patch('os.makedirs')
    def test_get_lowest_level_gets_lowest_level(self, *_):
        """Tests __get_lowest_level returns the lowest LogStyle level given."""
        level = _LogStream._LogStream__get_lowest_log_level(
            LogStyles.ALL_LEVELS)
        self.assertEqual(level, LogStyles.LOG_DEBUG)

    # __remove_handler

    @mock.patch('os.makedirs')
    def test_remove_handler_removes_a_handler(self, *_):
        dummy_obj = mock.Mock()
        dummy_obj.logger = mock.Mock()
        handler = mock.Mock()
        _LogStream._LogStream__remove_handler(dummy_obj, handler)

        self.assertTrue(dummy_obj.logger.removeHandler.called)
        self.assertTrue(handler.close.called)

    # __create_handlers_from_descriptors

    @mock.patch('os.makedirs')
    def test_create_handlers_from_descriptors(self, *_):
        """Tests that the handlers generated from the descriptors are added
        to the associated logger and the given handlers list."""
        info_testcase_log = LogStyles.LOG_INFO + LogStyles.TESTCASE_LOG
        with self.patch('FileHandler',
                        side_effect=[mock.MagicMock(name='handler1'),
                                     mock.MagicMock(name='handler2')]):
            log_stream.create_logger(self._testMethodName,
                                     log_styles=info_testcase_log)

        created_log_stream = log_stream._log_streams[self._testMethodName]
        descriptors = created_log_stream._testcase_descriptors
        testcase_handlers = []
        num_logger_handlers = len(created_log_stream.logger.handlers)
        created_log_stream._LogStream__create_handlers_from_descriptors(
            descriptors, testcase_handlers)

        self.assertGreater(len(created_log_stream.logger.handlers),
                           num_logger_handlers,
                           'No handlers added to the logger')
        self.assertGreater(len(testcase_handlers), 0,
                           'Handler list not populated.')

    # cleanup

    @mock.patch('os.makedirs')
    def test_cleanup_removes_all_handlers(self, *_):
        """ Tests that cleanup removes all handlers in the logger, except
        the NullHandler.
        """
        info_testcase_log = LogStyles.LOG_INFO + LogStyles.MONOLITH_LOG
        with self.patch('FileHandler'):
            log_stream.create_logger(self._testMethodName,
                                     log_styles=info_testcase_log)

        created_log_stream = log_stream._log_streams[self._testMethodName]
        created_log_stream.cleanup()

        self.assertEqual(len(created_log_stream.logger.handlers), 1)


class LogStreamModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # logging.log_path only exists if logger._setup_test_logger is called.
        # Here we set it to a value that is likely to not exist so file IO is
        # not executed (an error is raised instead of creating the file).
        logging.log_path = '/f/a/i/l/p/a/t/h'

    def setUp(self):
        log_stream._log_streams = {}

    # _update_handlers

    @staticmethod
    def create_new_context_event():
        return context.NewContextEvent()

    def test_update_handlers_delegates_calls_to_log_streams(self):
        """Tests _update_handlers calls update_handlers on each log_stream.
        """
        log_stream._log_streams = {
            'a': mock.Mock(),
            'b': mock.Mock()
        }

        log_stream._update_handlers(self.create_new_context_event())

        self.assertTrue(log_stream._log_streams['a'].update_handlers.called)
        self.assertTrue(log_stream._log_streams['b'].update_handlers.called)

    # _set_logger

    def test_set_logger_overwrites_previous_logger(self):
        """Tests that calling set_logger overwrites the previous logger within
        log_stream._log_streams.
        """
        previous = mock.Mock()
        log_stream._log_streams = {
            'a': previous
        }
        expected = mock.Mock()
        expected.name = 'a'
        log_stream._set_logger(expected)

        self.assertEqual(log_stream._log_streams['a'], expected)


if __name__ == '__main__':
    unittest.main()
