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

import metric


class ZombieMetric(metric.Metric):

    COMMAND = "ps axo pid=,stat=,comm= | awk '$2~/^Z { print }'"
    # Fields for response dictionary
    ADB_ZOMBIES = 'adb_zombies'
    FASTBOOT_ZOMBIES = 'fastboot_zombies'
    OTHER_ZOMBIES = 'other_zombies'

    def gather_metric(self):
        """finds PIDs and command names for zombie processes

        Returns:
            A dict with the following fields:
                adb_zombies: list of zombie processes w/ 'adb' in command name
                fastboot_zombies: list of zombie processes w/ 'fastboot'
                  in command name
                other_zombies: list of zombie processes w/o 'adb'or 'fastboot
                  in command name
            all elements in list are formatted as (PID, state, name) tuples
        """
        # Initialize empty lists
        adb_zombies, fastboot_zombies, other_zombies = [], [], []
        # Run shell command
        result = self._shell.run(self.COMMAND)
        """Example stdout:
        30797 Z+   adb <defunct>
        30798 Z+   adb <defunct>
        """
        # Split output into lines
        output = result.stdout.splitlines()
        for ln in output:
            # Get first two parts of output
            pid, state = ln.split()[:2]
            # Rest of line will be the command name, may have spaces
            name = ' '.join(ln.split()[2:])
            # Create zombie and append to proper list
            zombie = (int(pid), state, name)
            if 'adb' in name:
                adb_zombies.append(zombie)
            elif 'fastboot' in name:
                fastboot_zombies.append(zombie)
            else:
                other_zombies.append(zombie)

        # Create response dictionary
        response = {
            self.ADB_ZOMBIES: adb_zombies,
            self.FASTBOOT_ZOMBIES: fastboot_zombies,
            self.OTHER_ZOMBIES: other_zombies
        }
        return response
