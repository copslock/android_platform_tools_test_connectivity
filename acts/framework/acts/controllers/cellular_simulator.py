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


class AbstractCellularSimulator:
    """ A generic cellular simulator controller class that can be derived to
    implement equipment specific classes and allows the tests to be implemented
    without depending on a singular instrument model.

    This class defines the interface that every cellular simulator controller
    needs to implement and shouldn't be instantiated by itself. """
    def destroy(self):
        """ Sends finalization commands to the cellular equipment and closes
        the connection. """
        raise NotImplementedError()


class CellularSimulatorError(Exception):
    """ Exceptions thrown when the cellular equipment is unreachable or it
    returns an error after receiving a command. """
    pass
