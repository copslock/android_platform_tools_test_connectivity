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

from acts.signals import ControllerError


class MonsoonError(ControllerError):
    """Raised for exceptions encountered when interfacing with a Monsoon device.
    """


class PassthroughStates(object):
    """An enum containing the values for power monitor's passthrough states."""
    # "Off" or 0 means USB always off.
    OFF = 0
    # "On" or 1 means USB always on.
    ON = 1
    # "Auto" or 2 means USB is automatically turned off during sampling, and
    # turned back on after sampling.
    AUTO = 2


PASSTHROUGH_STATES = {
    'off': PassthroughStates.OFF,
    'on': PassthroughStates.ON,
    'auto': PassthroughStates.AUTO
}


class MonsoonData(object):
    """An object that contains aggregated data collected during sampling.

    Attributes:
        _num_samples: The number of samples gathered.
        _sum_currents: The total sum of all current values gathered, in amperes.
        _hz: The frequency sampling is being done at.
        _voltage: The voltage output during sampling.
    """

    # The number of decimal places to round a value to.
    ROUND_TO = 6

    def __init__(self, num_samples, sum_currents, hz, voltage, tag=None):
        self._num_samples = num_samples
        self._sum_currents = sum_currents
        self._hz = hz
        self._voltage = voltage
        self.tag = tag

    @property
    def average_current(self):
        """Average current in mA."""
        if self._num_samples == 0:
            return 0
        return round(self._sum_currents * 1000 / self._num_samples,
                     self.ROUND_TO)

    @property
    def total_charge(self):
        """Total charged used in the unit of mAh."""
        return round((self._sum_currents / self._hz) * 1000 / 3600,
                     self.ROUND_TO)

    @property
    def total_power(self):
        """Total power used."""
        return round(self.average_current * self._voltage, self.ROUND_TO)

    def __str__(self):
        return ('avg current: %s\n'
                'total charge: %s\n'
                'total power: %s' % (self.average_current, self.total_charge,
                                     self.total_power))
