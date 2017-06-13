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

from metrics.metric import Metric


class RamMetric(Metric):

    COMMAND = "free"
    # Fields for response dictionary
    TOTAL = 'total'
    USED = 'used'
    FREE = 'free'
    BUFFERS = 'buffers'
    CACHED = 'cached'

    def gather_metric(self):
        """Finds RAM statistics in mb

        Returns:
            A dict with the following fields:
                total: int representing total physical RAM available in KB
                used: int representing total RAM used by system in KB
                free: int representing total RAM free for new process in KB
                buffers: total RAM buffered by different applications in KB
                cached: total RAM for caching of data in KB
        """
        # Run shell command
        result = self._shell.run(self.COMMAND)
        # Example stdout:
        # total       used       free     shared    buffers     cached
        # Mem:     65894480  35218588  30675892    309024   1779900  24321888
        # -/+ buffers/cache:    9116800   56777680
        # Swap:     67031036          0   67031036

        # Get only second line
        output = result.stdout.splitlines()[1]
        # Split by space
        fields = output.split()
        # Create response dictionary
        response = {
            self.TOTAL: int(fields[1]),
            self.USED: int(fields[2]),
            self.FREE: int(fields[3]),
            # Skip shared column, since obsolete
            self.BUFFERS: int(fields[5]),
            self.CACHED: int(fields[6]),
        }
        return (response)
