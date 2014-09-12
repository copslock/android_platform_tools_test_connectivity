#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014 - The Android Open Source Project
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

import logging
import sys
import time

from test_utils.utils import create_dir

def get_test_logger(log_path, TAG):
    """Returns a logger object used for tests.

    The logger object has a stream handler and a file handler. The stream
    handler logs INFO level to the terminal, the file handler logs DEBUG
    level to files.

    Params:
        log_path: Location of the log file.
        TAG: Name of the logger's owner.

    Returns:
        A logger configured with one stream handler and one file handler
    """
    log = logging.getLogger(TAG)
    log.propagate = False
    log.setLevel(logging.DEBUG)
    c_formatter = logging.Formatter(('%(asctime)s - %(levelname)s - '
                                     '%(message)s'))
    # Log info to stream
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(c_formatter)
    ch.setLevel(logging.INFO)
    # Log everything to file
    f_formatter = logging.Formatter('%(asctime)s - %(message)s')
    create_dir(log_path)
    fh = logging.FileHandler(''.join((log_path, TAG, "_",
                             time.strftime("%m-%d-%Y_%H-%M-%S"), '.log')))
    fh.setFormatter(f_formatter)
    fh.setLevel(logging.DEBUG)
    log.addHandler(ch)
    log.addHandler(fh)
    return log

def get_test_reporter(log_path, TAG):
    """Returns a file object used for reports.

    Params:
        log_path: Location of the report file.
        TAG: Name of the logger's owner.

    Returns:
        A file object.
    """
    create_dir(log_path)
    f = open(''.join((log_path, TAG, "_", time.strftime("%m-%d-%Y_%H-%M-%S"),
             '.report')), 'w')
    return f