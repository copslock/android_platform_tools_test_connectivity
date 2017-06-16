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


class ZombieMetric(Metric):
    COMMAND = 'ps -eo pid,stat,comm,args | awk \'$2~/^Z/ { print }\''

    def gather_metric(self):
        """Gathers the pids, process names, and serial numbers of processes.

        If process does not have serial, None is returned instead.

        Returns:
            A dictionary where the keys are the pids of the processes, and the
            value is a tuple of (process name, serial number|None)
        """
        response = {}
        result = self._shell.run(self.COMMAND).stdout
        # Example stdout:
        # 30797 Z+   adb <defunct> adb -s AHDLSERIAL0001
        # 30798 Z+   adb <defunct> /usr/bin/adb

        output = result.splitlines()
        for ln in output:
            spl_ln = ln.split()
            # spl_ln looks like ['1xx', 'Z+', 'adb', '<defunct'>, ...]
            pid, state, name = spl_ln[:3]

            if '-s' in spl_ln:
                # Finds the '-s' flag, the index after that is the serial.
                sn_idx = spl_ln.index('-s')
                if sn_idx + 1 >= len(spl_ln):
                    sn = None
                else:
                    sn = spl_ln[sn_idx + 1]
                response[pid] = (name, sn)
            else:
                response[pid] = (name, None)

        return response
