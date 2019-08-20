#!/usr/bin/env python3
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

from acts.controllers.monsoon_lib.api.hvpm.monsoon import Monsoon as HvpmMonsoon
from acts.controllers.monsoon_lib.api.lvpm_stock.monsoon import Monsoon as LvpmStockMonsoon

ACTS_CONTROLLER_CONFIG_NAME = 'Monsoon'
ACTS_CONTROLLER_REFERENCE_NAME = 'monsoons'


def create(configs):
    objs = []
    for serial in configs:
        serial_number = int(serial)
        if serial_number < 20000:
            # This code assumes the LVPM has not been updated to have a
            # non-stock firmware. If someone has updated the firmware,
            # power measurement will fail.
            objs.append(LvpmStockMonsoon(serial=serial_number))
        else:
            objs.append(HvpmMonsoon(serial=serial_number))
    return objs


def destroy(monsoons):
    for monsoon in monsoons:
        monsoon.release_monsoon_connection()
