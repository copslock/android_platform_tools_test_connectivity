#!/usr/bin/python3.4
#
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

import datetime
import logging
import sys

from test_utils.utils import create_dir

log_line_format = "%(asctime)s.%(msecs).03d %(levelname)s %(message)s"
# The micro seconds are added by the format string above,
# so the time format does not include ms.
log_line_time_format = "%m-%d %H:%M:%S"
log_line_timestamp_len = 18

def _parse_logline_timestamp(t):
    """Parses a logline timestamp into a tuple.

    Params:
        t: Timestamp in logline format.

    Returns:
        An iterable of date and time elements in the order of month, day, hour,
        minute, second, microsecond.
    """
    date, time = t.split(' ')
    month, day = date.split('-')
    h, m, s = time.split(':')
    s, ms = s.split('.')
    return (month, day, h, m, s, ms)

def logline_timestamp_comparator(t1, t2):
    """Comparator for timestamps in logline format.

    Params:
        t1: Timestamp in logline format.
        t2: Timestamp in logline format.

    Returns:
        -1 if t1 < t2; 1 if t1 > t2; 0 if t1 == t2.
    """
    dt1 = _parse_logline_timestamp(t1)
    dt2 = _parse_logline_timestamp(t2)
    for u1, u2 in zip(dt1, dt2):
        if u1 < u2:
            return -1
        elif u1 > u2:
            return 1
    return 0

def get_current_logline_timestamp():
    """Returns the current timestamp in the format used by log lines.
    """
    return datetime.datetime.now().strftime("%m-%d %H:%M:%S.%f")[:-3]

def get_log_file_timestamp():
    """Returns the current timestamp in the format used by log filenames.
    """
    return datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S-%f")[:-3]

def get_test_logger(log_path, TAG, filename=None):
    """Returns a logger object used for tests.

    The logger object has a stream handler and a file handler. The stream
    handler logs INFO level to the terminal, the file handler logs DEBUG
    level to files.

    Params:
        log_path: Location of the log file.
        TAG: Name of the logger's owner.
        filename: Name of the log file. The default is the time the logger
            is requested.

    Returns:
        A logger configured with one stream handler and one file handler
    """
    log = logging.getLogger(TAG)
    log.propagate = False
    log.setLevel(logging.DEBUG)
    c_formatter = logging.Formatter(log_line_format, log_line_time_format)
    # Log info to stream
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(c_formatter)
    ch.setLevel(logging.INFO)
    # Log everything to file
    f_formatter = logging.Formatter(log_line_format, log_line_time_format)
    # All the logs of this test class go into one directory
    if not filename:
        filename = get_log_file_timestamp()
        log_path = '/'.join((log_path, filename))
        create_dir(log_path)
    fh = logging.FileHandler(log_path + '/test_run_detailed.log')
    fh.setFormatter(f_formatter)
    fh.setLevel(logging.DEBUG)
    log.addHandler(ch)
    log.addHandler(fh)
    return log

def get_test_reporter(log_path, TAG, filename=None):
    """Returns a file object used for reports.

    Params:
        log_path: Location of the report file.
        TAG: Name of the logger's owner.
        filename: Name of the report file. The default is the time the reporter
            is requested.

    Returns:
        A file object.
    """
    # All the logs of this test class go into one directory
    if not filename:
        filename = get_log_file_timestamp()
        log_path = '/'.join((log_path, filename))
        create_dir(log_path)
    f = open(log_path + '/test_run_summary.log', 'w')
    return f

def get_test_logger_and_reporter(log_path, TAG, filename=None):
    """Returns a logger and a reporter of the same name.

    Params:
        log_path: Location of the report file.
        TAG: Name of the logger's owner.
        filename: Name of the files. The default is the time the objects
            are requested.

    Returns:
        A log object and a reporter object.
    """
    if not filename:
        filename = get_log_file_timestamp()
    log_path = '/'.join((log_path, filename))
    create_dir(log_path)
    logger = get_test_logger(log_path, TAG, filename)
    reporter = get_test_reporter(log_path, TAG, filename)
    return logger, reporter, filename
