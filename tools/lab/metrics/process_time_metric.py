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

import itertools
from metrics.metric import Metric


class ProcessTimeMetric(Metric):
    TIME_COMMAND = 'ps -p %s -o etime='

    # Fields for response dictionary
    PID_TIMES = 'pid_times'

    def gather_metric(self):
        """Returns ADB and Fastboot processes and their time elapsed

        Returns:
            A dict with the following fields:
              pid_times: a list of (time, PID) tuples where time is a string
              representing time elapsed in D-HR:MM:SS format and PID is a string
              representing the pid
        """
        # Get the process ids
        pids = self.get_adb_fastboot_pids()

        # Get elapsed time for selected pids
        times = []
        for pid in pids:
            time = self._shell.run(self.TIME_COMMAND % pid).stdout
            times.append((time, pid))

        # Create response dictionary
        response = {self.PID_TIMES: times}
        return response

    def get_adb_fastboot_pids(self):
        """Finds a list of ADB and Fastboot process ids.

        Returns:
          A list of PID strings
        """
        # Get ids of processes with 'adb' or 'fastboot' in name
        adb_result = self._shell.get_pids('adb')
        fastboot_result = self._shell.get_pids('fastboot')
        # concatenate two generator objects, return as list
        return list(itertools.chain(adb_result, fastboot_result))
