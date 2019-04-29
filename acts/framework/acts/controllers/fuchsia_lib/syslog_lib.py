#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

from acts.libs.proc.process import Process
from acts.libs.logging import log_stream
from acts.libs.logging.log_stream import LogStyles
from acts.controllers.android_lib.logcat import TimestampTracker

TIMESTAMP_REGEX = r'((?:\d+-)?\d+-\d+ \d+:\d+:\d+.\d+)'


def _get_log_level(message):
    """Returns the log level for the given message."""
    if message.startswith('-') or len(message) < 37:
        return logging.ERROR
    else:
        log_level = message[36]
        if log_level in ('V', 'D'):
            return logging.DEBUG
        elif log_level == 'I':
            return logging.INFO
        elif log_level == 'W':
            return logging.WARNING
        elif log_level == 'E':
            return logging.ERROR
    return logging.NOTSET


def _log_line_func(log, timestamp_tracker):
    """Returns a lambda that logs a message to the given logger."""

    def log_line(message):
        timestamp_tracker.read_output(message)
        log.log(_get_log_level(message), message)

    return log_line


def _on_retry(ip_address, ssh_config, extra_params, timestamp_tracker):
    def on_retry(_):
        additional_params = extra_params or ''

        return 'ssh -F %s %s \'log_listener %s\'' % (ssh_config,
                                                     ip_address,
                                                     additional_params)

    return on_retry


def start_syslog(serial, base_path, ip_address, ssh_config, extra_params=''):
    """Creates a ssh syslog Process that automatically attempts to reconnect.

    Args:
        serial: The unique identifier for the device.
        base_path: The base directory used for syslog file output.
        ip_address: The ip address of the device to get the syslog.
        ssh_config: Location of the ssh_config for connecting to the remote
            device
        extra_params: Any additional params to be added to the syslog cmdline.

    Returns:
        A acts.libs.proc.process.Process object.
    """
    logger = log_stream.create_logger(
        'fuchsia_log_%s' % serial, base_path=base_path,
        log_styles=(LogStyles.LOG_DEBUG | LogStyles.MONOLITH_LOG))
    process = Process('ssh -F %s %s \'log_listener %s\'' % (ssh_config,
                                                            ip_address,
                                                            extra_params))
    timestamp_tracker = TimestampTracker()
    process.set_on_output_callback(_log_line_func(logger, timestamp_tracker))
    process.set_on_terminate_callback(
        _on_retry(ip_address, ssh_config, extra_params, timestamp_tracker))
    return process
