#!/usr/bin/env python3
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

import shutil
import tempfile
import unittest
import warnings
from unittest import TestCase

from mobly.config_parser import TestRunConfig
from mock import Mock
from mock import PropertyMock
from mock import patch

from acts.base_test import BaseTestClass
from acts.metrics.loggers.bounded_metrics import BoundedMetricsLogger
from acts.test_runner import TestRunner

GET_CONTEXT_FOR_EVENT = 'acts.metrics.logger.get_context_for_event'
PROTO_METRIC_PUBLISHER = 'acts.metrics.logger.ProtoMetricPublisher'


class BoundedMetricsLoggerTest(TestCase):
    """Unit tests for BoundedMetricsLogger."""

    def setUp(self):
        self.event = Mock()
        self.context = Mock()
        self.publisher = Mock()

    @patch(PROTO_METRIC_PUBLISHER)
    @patch(GET_CONTEXT_FOR_EVENT)
    def test_init_with_event(self, get_context, publisher_cls):
        logger = BoundedMetricsLogger(event=self.event)

        self.assertIsNotNone(logger.context)
        self.assertIsNotNone(logger.publisher)

    @patch(GET_CONTEXT_FOR_EVENT)
    @patch('acts.metrics.loggers.protos.gen.metrics_pb2.BoundedMetric')
    def test_add_generates_messages(self, mock_metric, get_context):
        result = Mock()
        mock_metric.return_value = result

        logger = BoundedMetricsLogger(event=self.event)
        logger.context = self.context
        logger.publisher = self.publisher
        logger.context.identifier = 'Class.test'

        logger.add('towels_metric', 123, lower_limit=1, upper_limit=2,
                   unit='towels')

        self.assertEqual(result.test_class, 'Class')
        self.assertEqual(result.test_method, 'test')
        self.assertEqual(result.value, 123)
        self.assertEqual(result.lower_limit.value, 1)
        self.assertEqual(result.upper_limit.value, 2)
        self.assertEqual(result.metric, 'towels_metric')
        self.assertEqual(result.unit, 'towels')

    @patch(GET_CONTEXT_FOR_EVENT)
    @patch('acts.metrics.loggers.protos.gen.metrics_pb2.BoundedMetric')
    def test_add_without_limits_does_not_populate_limits(self, mock_metric,
        get_context):
        result = Mock()
        mock_metric.return_value = result

        logger = BoundedMetricsLogger(event=self.event)
        logger.context = self.context
        logger.publisher = self.publisher
        logger.context.identifier = 'Class.test'

        logger.add('limitless_metric', 123, unit='skies')

        self.assertEqual(result.test_class, 'Class')

        self.assertEqual(result.test_method, 'test')
        self.assertEqual(result.value, 123)
        self.assertEqual(result.metric, 'limitless_metric')
        self.assertEqual(result.unit, 'skies')
        result.lower_limit.assert_not_called()
        result.upper_limit.assert_not_called()

    @patch(GET_CONTEXT_FOR_EVENT)
    @patch('acts.metrics.loggers.protos.gen.metrics_pb2.BoundedMetric')
    def test_test_method_and_test_class_get_set_if_test_method_identifier(self,
        mock_metric, get_context):
        result = Mock()
        test_method = PropertyMock()
        test_class = PropertyMock()
        type(result).test_method = test_method
        type(result).test_class = test_class
        test_method = PropertyMock()
        type(result).test_method = test_method
        mock_metric.return_value = result
        logger = BoundedMetricsLogger(event=self.event)
        logger.context = self.context
        logger.publisher = self.publisher
        logger.context.identifier = 'AwesomeClass.incredible_test'

        logger.add('limitless_metric', 123, unit='skies')

        test_class.assert_called_with('AwesomeClass')
        test_method.assert_called_with('incredible_test')

    @patch(GET_CONTEXT_FOR_EVENT)
    @patch('acts.metrics.loggers.protos.gen.metrics_pb2.BoundedMetric')
    def test_only_test_class_gets_set_if_not_test_identifier(self, mock_metric,
        get_context):
        result = Mock()
        test_method = PropertyMock()
        test_class = PropertyMock()
        type(result).test_method = test_method
        type(result).test_class = test_class
        mock_metric.return_value = result
        logger = BoundedMetricsLogger(event=self.event)
        logger.context = self.context
        logger.publisher = self.publisher
        logger.context.identifier = 'BestClass'

        logger.add('limitless_metric', 123, unit='skies')

        test_class.assert_called_with('BestClass')
        test_method.assert_not_called()

    @patch('acts.metrics.loggers.bounded_metrics.ProtoMetric')
    @patch('acts.metrics.loggers.protos.gen.metrics_pb2.BoundedMetric')
    @patch(GET_CONTEXT_FOR_EVENT)
    def test_end_does_publish(self, get_context, mock_metric, proto_metric_cls):
        result = Mock()

        logger = BoundedMetricsLogger(self.event)
        logger.context = self.context
        logger.publisher = self.publisher
        logger._metric_map = {'some_metric_name': result}

        logger.end(self.event)

        proto_metric_cls.assert_called_once_with(
            name='bounded_metric_some_metric_name',
            data=result)
        self.publisher.publish.assert_called_once_with(
            [proto_metric_cls.return_value])


class BoundedMetricsLoggerIntegrationTest(TestCase):
    """Integration tests for BoundedMetricLogger."""

    def setUp(self):
        warnings.simplefilter('ignore', ResourceWarning)

    @patch('acts.test_runner.sys')
    @patch('acts.test_runner.utils')
    @patch('acts.test_runner.importlib')
    def run_acts_test(self, test_class, importlib, utils, sys):
        test_run_config = TestRunConfig()
        test_run_config.testbed_name = 'SampleTestBed'
        test_run_config.log_path = tempfile.mkdtemp()
        test_run_config.controller_configs = {'testpaths': ['./']}

        mock_module = Mock()
        setattr(mock_module, test_class.__name__, test_class)
        utils.find_files.return_value = [(None, None, None)]
        importlib.import_module.return_value = mock_module
        runner = TestRunner(test_run_config, [(
            test_class.__name__,
            None,
        )])

        runner.run()
        runner.stop()
        shutil.rmtree(test_run_config.log_path)
        return runner

    def __get_only_arg(self, call_args):
        self.assertEqual(len(call_args[0]) + len(call_args[1]), 1)
        if len(call_args[0]) == 1:
            return call_args[0][0]
        return next(iter(call_args[1].values()))

    @patch('acts.metrics.logger.ProtoMetricPublisher')
    def test_test_case_metric(self, publisher_cls):
        class FantasticTest(BaseTestClass):
            def __init__(self, controllers):
                super().__init__(controllers)
                self.tests = ('test_magnificent',)
                self.bounded_metrics = BoundedMetricsLogger.for_test_case()

            def test_magnificent(self):
                self.bounded_metrics.add('galaxies', 1234, lower_limit=-5,
                                         upper_limit=15, unit='towels')

        self.run_acts_test(FantasticTest)

        args_list = publisher_cls().publish.call_args_list
        self.assertEqual(len(args_list), 1)
        published = self.__get_only_arg(args_list[0])[0]
        self.assertEqual(published.name, 'bounded_metric_galaxies')
        self.assertEqual(published.data.test_method, 'test_magnificent')
        self.assertEqual(published.data.test_class, 'FantasticTest')
        self.assertEqual(published.data.value, 1234)
        self.assertEqual(published.data.lower_limit.value, -5)
        self.assertEqual(published.data.upper_limit.value, 15)
        self.assertEqual(published.data.unit, 'towels')

    @patch('acts.metrics.logger.ProtoMetricPublisher')
    def test_test_class_metric(self, publisher_cls):
        publisher_cls().publish = Mock()

        class RickAstleyTest(BaseTestClass):
            def __init__(self, controllers):
                super().__init__(controllers)
                self.tests = (
                    'test_never_gonna_make_you_cry',
                    'test_never_gonna_say_good_bye',
                )
                self.bounded_metric = BoundedMetricsLogger.for_test_class()

            def setup_class(self):
                self.bounded_metric.add('never_gonna_give_you_up', 1)

            def test_never_gonna_make_you_cry(self):
                self.bounded_metric.add('never_gonna_let_you_down', 2)

            def test_never_gonna_say_good_bye(self):
                self.bounded_metric.add('never_gonna_run_around_and_desert_you',
                                        3)

        self.run_acts_test(RickAstleyTest)

        args_list = publisher_cls().publish.call_args_list
        self.assertEqual(len(args_list), 1)
        published1 = self.__get_only_arg(args_list[0])[0]
        published2 = self.__get_only_arg(args_list[0])[1]
        published3 = self.__get_only_arg(args_list[0])[2]

        self.assertIn('bounded_metric_never_gonna_give_you_up',
                      [published1.name, published2.name, published3.name])
        self.assertIn('bounded_metric_never_gonna_let_you_down',
                      [published1.name, published2.name, published3.name])
        self.assertIn('bounded_metric_never_gonna_run_around_and_desert_you',
                      [published1.name, published2.name, published3.name])

        self.assertEqual(published1.data.test_method, '')
        self.assertEqual(published2.data.test_method, '')
        self.assertEqual(published3.data.test_method, '')

        self.assertEqual(published1.data.test_class, 'RickAstleyTest')
        self.assertEqual(published2.data.test_class, 'RickAstleyTest')
        self.assertEqual(published3.data.test_class, 'RickAstleyTest')

        self.assertIn(1, [published1.data.value, published2.data.value,
                          published3.data.value])
        self.assertIn(2, [published1.data.value, published2.data.value,
                          published3.data.value])
        self.assertIn(3, [published1.data.value, published2.data.value,
                          published3.data.value])


if __name__ == '__main__':
    unittest.main()
