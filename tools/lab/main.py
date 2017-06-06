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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

from runner import InstantRunner
from metrics.usb_metric import UsbMetric
from reporter import LoggerReporter


class RunnerFactory(object):
    _reporter_constructor = {
        'logger': lambda: LoggerReporter(),
    }

    _metric_constructor = {
        'usb_io': lambda param: UsbMetric(),
        'disk': lambda param: DiskMetric(),
        'uptime': lambda param: UptimeMetric(),
        'verify_devices': lambda param: VerifyMetric(),
        'ram': lambda param: RamMetric(),
        'cpu': lambda param: CpuMetric(),
    }

    @classmethod
    def create(cls, arguments):
        """ Creates the Runner Class that will take care of gather metrics
        and determining how to report those metrics.

        Args:
            arguments: The arguments passed in through command line, a dict.

        Returns:
            Returns a Runner that was created by passing in a list of
            metrics and list of reporters.
        """
        arg_dict = arguments
        metrics = []

        # If no reporter specified, default to logger.
        reporters = arg_dict.pop('reporter')
        if reporters is None:
            reporters = ['logger']

        # Check keys and values to see what metrics to include.
        for key in arg_dict:
            val = arg_dict[key]
            if val is not None:
                metrics.append(cls._metric_constructor[key](val))

        return InstantRunner(metrics, reporters)


def _argparse():
    parser = argparse.ArgumentParser(
        description='Tool for getting lab health of android testing lab',
        prog='Lab Health')

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s v0.1.0',
        help='specify version of program')
    parser.add_argument(
        '-i',
        '--usb-io',
        action='store_true',
        default=None,
        help='display recent USB I/O')
    parser.add_argument(
        '-u',
        '--uptime',
        action='store_true',
        default=None,
        help='display uptime of current lab station')
    parser.add_argument(
        '-d',
        '--disk',
        choices=['size', 'used', 'avail', 'percent'],
        nargs='*',
        help='display the disk space statistics')
    parser.add_argument(
        '-ra',
        '--ram',
        action='store_true',
        default=None,
        help='display the current RAM usage')
    parser.add_argument(
        '-c',
        '--cpu',
        action='count',
        default=None,
        help='display the current CPU usage as percent')
    parser.add_argument(
        '-vd',
        '--verify-devices',
        action='store_true',
        default=None,
        help='verify all devices connected are in \'device\' mode')
    parser.add_argument(
        '-r',
        '--reporter',
        choices=['logger', 'proto', 'json'],
        nargs='+',
        help='choose the reporting method needed')
    parser.add_argument(
        '-p',
        '--program',
        choices=['python', 'adb', 'fastboot', 'os', 'kernel'],
        nargs='*',
        help='display the versions of chosen programs (default = all)')

    return parser


def main():
    parser = _argparse()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    RunnerFactory().create(vars(parser.parse_args()))


if __name__ == '__main__':
    main()
