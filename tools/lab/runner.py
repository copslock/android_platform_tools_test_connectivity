#!/usr/bin/env python
#
#   Copyright 2017 - The Android Open Source Project
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


class Runner:
    """Calls metrics and passes response to reporters.

    Attributes:
        metric_list: a list of metric objects
        reporter_list: a list of reporter objects
        object and value is dictionary returned by that response
    """

    def __init__(self, metric_list, reporter_list):
        self.metric_list = metric_list
        self.reporter_list = reporter_list

    def run(self):
        """Calls metrics and passes response to reporters."""
        raise NotImplementedError()


class InstantRunner(Runner):
    def run(self):
        """Calls all metrics, passes responses to reporters."""
        responses = {}
        for metric in self.metric_list:
            responses[metric] = metric.gatherMetric()
        for reporter in self.reporter_list:
            reporter.report(responses)
