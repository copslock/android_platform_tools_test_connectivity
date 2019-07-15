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

import flow
import time
from acts import logger
from acts import utils

CHAMBER_SLEEP = 30


def create(configs):
    """Factory method for OTA chambers.

    Args:
        configs: list of dicts with chamber settings. settings must contain the
        following: type (string denoting type of chamber)
    """
    objs = []
    for config in configs:
        try:
            chamber_class = globals()[config['model']]
        except KeyError:
            raise KeyError('Invalid chamber configuration.')
        objs.append(chamber_class(config))
    return objs


def detroy(objs):
    return


class OtaChamber(object):
    """Base class implementation for OTA chamber.

    Base class provides functions whose implementation is shared by all
    chambers.
    """

    def reset_chamber(self):
        """Resets the chamber to its zero/home state."""
        raise NotImplementedError

    def set_orientation(self, orientation):
        """Set orientation for turn table in OTA chamber.

        Args:
            angle: desired turn table orientation in degrees
        """
        raise NotImplementedError

    def set_stirrer_pos(self, stirrer_id, position):
        """Starts turntables and stirrers in OTA chamber."""
        raise NotImplementedError

    def start_continuous_stirrers(self):
        """Starts turntables and stirrers in OTA chamber."""
        raise NotImplementedError

    def stop_continuous_stirrers(self):
        """Stops turntables and stirrers in OTA chamber."""
        raise NotImplementedError


class MockChamber(OtaChamber):
    """Class that implements mock chamber for test development and debug."""

    def __init__(self, config):
        self.config = config.copy()
        self.device_id = self.config['device_id']
        self.log = logger.create_tagged_trace_logger('OtaChamber|{}'.format(
            self.device_id))

    def set_orientation(self, orientation):
        self.log.info('Setting orientation to {} degrees.'.format(orientation))

    def reset_chamber(self, orientation):
        self.log.info('Resetting chamber to home state')

    def set_stirrer_pos(self, stirrer_id, position):
        """Starts turntables and stirrers in OTA chamber."""
        self.log.info('Setting stirrer {} to {}.'.format(stirrer_id, position))

    def start_continuous_stirrers(self):
        """Starts turntables and stirrers in OTA chamber."""
        self.log.info('Starting continuous stirrer motion')

    def stop_continuous_stirrers(self):
        """Stops turntables and stirrers in OTA chamber."""
        self.log.info('Stopping continuous stirrer motion')


class OctoboxChamber(OtaChamber):
    """Class that implements Octobox chamber."""

    def __init__(self, config):
        self.config = config.copy()
        self.device_id = self.config['device_id']
        self.log = logger.create_tagged_trace_logger('OtaChamber|{}'.format(
            self.device_id))
        self.TURNTABLE_FILE_PATH = '/usr/local/bin/fnPerformaxCmd'
        utils.exe_cmd('sudo {} -d {} -i 0'.format(self.TURNTABLE_FILE_PATH,
                                                  self.device_id))

    def set_orientation(self, orientation):
        self.log.info('Setting orientation to {} degrees.'.format(orientation))
        utils.exe_cmd('sudo {} -d {} -p {}'.format(
            self.TURNTABLE_FILE_PATH, self.device_id, orientation))

    def reset_chamber(self):
        self.log.info('Resetting chamber to home state')
        self.set_orientation(0)


class ChamberAutoConnect(object):
    def __init__(self, chamber, chamber_config):
        self._chamber = chamber
        self._config = chamber_config

    def __getattr__(self, item):
        def chamber_call(*args, **kwargs):
            self._chamber.connect(self._config['ip_address'],
                                  self._config['username'],
                                  self._config['password'])
            return getattr(self._chamber, item)(*args, **kwargs)

        return chamber_call


class BluetestChamber(OtaChamber):
    """Class that implements Octobox chamber."""

    def __init__(self, config):
        self.config = config.copy()
        self.log = logger.create_tagged_trace_logger('OtaChamber|{}'.format(
            self.config['ip_address']))
        self.chamber = ChamberAutoConnect(flow.Flow(), self.config)
        self.stirrer_ids = [0, 1, 2]
        self.current_mode = None

    def _connect(self):
        self.chamber.connect(self.config['ip_address'],
                             self.config['username'], self.config['password'])

    def _init_manual_mode(self):
        self.current_mode = 'manual'
        for stirrer_id in self.stirrer_ids:
            self.chamber.chamber_stirring_manual_init(stirrer_id)
        time.sleep(CHAMBER_SLEEP)

    def _init_continuous_mode(self):
        self.current_mode = 'continuous'
        self.chamber.chamber_stirring_continous_init()

    def set_stirrer_pos(self, stirrer_id, position):
        if self.current_mode != 'manual':
            self._init_manual_mode()
        self.log.info('Setting stirrer {} to {}.'.format(stirrer_id, position))
        self.chamber.chamber_stirring_manual_set_pos(stirrer_id, position)

    def set_orientation(self, orientation):
        self.set_stirrer_pos(2, orientation * 100 / 360)

    def start_continuous_stirrers(self):
        if self.current_mode != 'continuous':
            self._init_continuous_mode()
        self.chamber.chamber_stirring_continous_start()

    def stop_continuous_stirrers(self):
        self.chamber.chamber_stirring_continous_stop()

    def reset_chamber(self):
        if self.current_mode == 'continuous':
            self._init_continuous_mode()
        elif self.current_mode == 'manual':
            self._init_manual_mode()
