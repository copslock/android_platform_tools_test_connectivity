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

from acts.metrics.core import ProtoMetric
from acts.metrics.logger import MetricLogger


class BlackboxMetricLogger(MetricLogger):
    """A MetricLogger for logging and publishing Blackbox metrics.

    The logger will publish an ActsBlackboxMetricResult message, containing
    data intended to be uploaded to Blackbox. The message itself contains only
    minimal information specific to the metric, with the intention being that
    all other metadata is extracted from the test_run_summary.json.

    This logger will extract an attribute from the test class as the metric
    result. The metric key will be either the context's identifier or a custom
    value assigned to this class.

    Attributes:
        proto_module: The proto module for ActsBlackboxMetricResult.
        metric_name: The name of the metric, used to determine output filename.
        result_attr: The name of the attribute of the test class where the
                     result is stored.
        metric_key: The metric key to use. If unset, the logger will use the
                    context's identifier.
    """

    PROTO_FILE = 'protos/acts_blackbox.proto'

    def __init__(self,
                 metric_name,
                 result_attr='result',
                 metric_key=None,
                 event=None):
        """Initializes a logger for Blackbox metrics.

        Args:
            metric_name: The name of the metric.
            result_attr: The name of the attribute of the test class where the
                         result is stored.
            metric_key: The metric key to use. If unset, the logger will use
                        the context's identifier.
            event: The event triggering the creation of this logger.
        """
        super().__init__(event=event)
        self.proto_module = self._compile_proto(self.PROTO_FILE)
        if not metric_name:
            raise ValueError("metric_name must be supplied.")
        self.metric_name = metric_name
        self.result_attr = result_attr
        self.metric_key = metric_key

    def _get_metric_value(self):
        """Extracts the metric value from the current context."""
        return getattr(self.context.test_class, self.result_attr)

    def _get_metric_key(self):
        """Gets the metric key to use.

        If the metric_key is explicitly set, returns that value. Otherwise,
        extracts an identifier from the context.
        """
        if self.metric_key:
            return self.metric_key
        return self.context.identifier

    def _get_file_name(self):
        """Gets the base file name to publish to."""
        return 'blackbox_%s' % self.metric_name

    def end(self, event):
        """Creates and publishes a ProtoMetric with blackbox data.

        Builds an ActsBlackboxMetricResult message based on the result
        generated, and passes it off to the publisher.

        Args:
            event: The triggering event.
        """
        result = self.proto_module.ActsBlackboxMetricResult()
        result.test_identifier = self.context.identifier
        result.metric_key = self._get_metric_key()
        result.metric_value = self._get_metric_value()

        metric = ProtoMetric(
            name=self._get_file_name(),
            data=result)
        return self.publisher.publish(metric)