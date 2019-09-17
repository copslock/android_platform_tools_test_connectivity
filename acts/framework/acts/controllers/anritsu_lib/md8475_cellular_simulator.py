#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import acts.controllers.cellular_simulator as cc
from acts.controllers.anritsu_lib import md8475a
from acts.controllers.anritsu_lib import _anritsu_utils as anritsu


class MD8475CellularSimulator(cc.AbstractCellularSimulator):

    MD8475_VERSION = 'A'

    def __init__(self, ip_address):
        try:
            self.anritsu = md8475a.MD8475A(ip_address,
                                           md8475_version=self.MD8475_VERSION)
        except anritsu.AnristuError:
            raise cc.CellularSimulatorError('Could not connect to MD8475.')

    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        self.anritsu.stop_simulation()
        self.anritsu.disconnect()


class MD8475BCellularSimulator(MD8475CellularSimulator):

    MD8475_VERSION = 'B'
