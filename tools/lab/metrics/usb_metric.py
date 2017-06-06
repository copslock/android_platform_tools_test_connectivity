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
import job


class UsbMetric(Metric):
    def check_usbmon(self):
        try:
            job.run('grep usbmon /proc/modules')
        except job.Error:
            print('Kernel module not loaded, attempting to load usbmon')
            result = job.run('modprobe usbmon', ignore_status=True)
            if result.exit_status != 0:
                print result.stderr

    def gather_metric(self):
        self.check_usbmon()
