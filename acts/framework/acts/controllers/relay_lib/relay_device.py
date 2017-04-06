#!/usr/bin/env python
#
#   Copyright 2016 - The Android Open Source Project
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

from acts.controllers.relay_lib.errors import RelayConfigError
from acts.controllers.relay_lib.helpers import validate_key


class RelayDevice(object):
    """The base class for all relay devices.

    RelayDevice has access to both its relays as well as the relay rig it is
    a part of. Note that you can receive references to the relay_boards
    through relays[0...n].board. The relays are not guaranteed to be on
    the same relay board.
    """

    def __init__(self, config, relay_rig):
        """Creates a RelayDevice.

        Args:
            config: The dictionary found in the config file for this device.
            You can add your own params to the config file if needed, and they
            will be found in this dictionary.
            relay_rig: The RelayRig the device is attached to. This won't be
            useful for classes that inherit from RelayDevice, so just pass it
            down to this __init__.
        """
        self.rig = relay_rig
        self.relays = dict()

        validate_key('name', config, str, '"devices" element')
        self.name = config['name']

        validate_key('relays', config, list, '"devices list element')
        if len(config['relays']) < 1:
            raise RelayConfigError(
                'Key "relays" must have at least 1 element.')

        for relay_config in config['relays']:
            if isinstance(relay_config, dict):
                name = validate_key('name', relay_config, str,
                                    '"relays" element in "devices"')
                if 'pos' in relay_config:
                    self.relays[name] = relay_rig.relays[relay_config['pos']]
                else:
                    validate_key('pos', relay_config, int,
                                 '"relays" element in "devices"')
            else:
                raise TypeError('Key "relay" is of type {}. Expecting {}. '
                                'Offending object:\n {}'.format(
                                    type(relay_config['relay']), dict,
                                    relay_config))

    def setup(self):
        """Sets up the relay device to be ready for commands."""
        pass

    def clean_up(self):
        """Sets the relay device back to its inert state."""
        pass
