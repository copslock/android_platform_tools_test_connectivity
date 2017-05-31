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


def _argparse():
    parser = argparse.ArgumentParser(
        description="Tool for getting lab health of android testing lab",
        prog="Lab Health")

    parser.add_argument(
        "-v",
        "--version",
        action='version',
        version='%(prog)s v0.1',
        help="specify version of program")
    parser.add_argument(
        "-u",
        "--uptime",
        action="store_true",
        help="display uptime of current lab station")
    parser.add_argument(
        "-d",
        "--disk",
        action="store_true",
        help="display the disk space statistics")
    parser.add_argument(
        "-r",
        "--ram",
        action="store_true",
        help="display the current RAM usage")
    parser.add_argument(
        "-c",
        "--cpu",
        action="store_true",
        help="display the current CPU usage as percent")
    parser.add_argument(
        "-vd",
        "--verify-devices",
        action="store_true",
        help="verify all devices connected are in 'device' mode")

    return parser


def main():
    args = _argparse().parse_args()
    #ReporterFactory.create(args) #Returns metrics based on args


if __name__ == '__main__':
    main()
