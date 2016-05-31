#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Test script to test PBAP contact download between two devices which can run SL4A.

The script does the following:
    Setup:
        Clear up the bonded devices on both bluetooth adapters and bond
            the DUTs to each other.
"""

from os.path import exists

from acts.base_test import BaseTestClass
from acts.test_utils.bt.bt_test_utils import pair_pri_to_sec
from acts.test_utils.bt.bt_test_utils import reset_bluetooth
from acts.test_utils.bt.bt_test_utils import take_btsnoop_logs
from acts.utils import exe_cmd
import acts.test_utils.bt.bt_contacts_utils as bt_contacts_utils

# PBAP Server is profile 6
PBAP_SERVER_PROFILE = 6
# Access Levels from BluetoothDevice
ACCESS_ALLOWED = 1

#file names for contacts cards
PSE_CONTACTS_FILE = "psecontacts.vcf"
PCE_CONTACTS_FILE = "pcecontacts.vcf"
PCE_CONTACTS_ON_DEVICE= "/sdcard/Download/pcecontacts.vcf"

class BtCarPbapTest(BaseTestClass):
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.pce = self.android_devices[0]
        self.pse = self.android_devices[1]

    def setup_class(self):
        # Reset the devices in a clean state.
        reset_bluetooth(self.android_devices)

        for a in self.android_devices:
            a.ed.clear_all_events()

        # Pair the devices.
        # This call may block until some specified timeout in bt_test_utils.py.
        if not pair_pri_to_sec(self.pce.droid, self.pse.droid):
            self.log.error("pair_pri_to_sec returned false.")
            return False
        self.pse.droid.bluetoothChangeProfileAccessPermission(
            self.pse.droid.bluetoothGetBondedDevices()[0]["address"],
            PBAP_SERVER_PROFILE, ACCESS_ALLOWED)

        return True

    def setup_test(self):
        bt_contacts_utils.set_logger(self.log)
        if not exists(PSE_CONTACTS_FILE):
            self.log.error("ERROR, file {} does not exist in cwd"
                           .format(PSE_CONTACTS_FILE))
            return False
        return True

    def teardown_test(self):
        return True

    def on_fail(self, test_name, begin_time):
        take_btsnoop_logs(self.android_devices, self, test_name)

    def _verify_contacts_match(self):
        bt_contacts_utils.pull_contacts(self.pce, PCE_CONTACTS_FILE)
        return bt_contacts_utils.compare_contacts(PCE_CONTACTS_FILE,
                                                  PSE_CONTACTS_FILE) == 0

    def test_contact_download(self):
        """Test Contact Download

        Test download of contacts from a clean state.

            1. Erase contacts from PSE.
            2. Add a predefined list of contacts to PSE.
            3. Connect PCE to PSE to perform transfer.
            4. Compare transfered contacts.
            5. Disconnect.
            6. Verify PCE cleaned up contact list.

            Returns:
                Pass if True
                Fail if False
        """
        passing = True
        passing &= bt_contacts_utils.erase_contacts(self.pse)
        passing &= bt_contacts_utils.erase_contacts(self.pce)
        bt_contacts_utils.add_contacts(self.pse, PSE_CONTACTS_FILE)
        self.pce.droid.bluetoothPbapClientConnect(
            self.pse.droid.bluetoothGetLocalAddress())
        bt_contacts_utils.wait_for_contact_update_complete(self.pce, 100)
        passing &= self._verify_contacts_match()
        self.pce.droid.bluetoothPbapClientDisconnect(
            self.pse.droid.bluetoothGetLocalAddress())
        passing &= bt_contacts_utils.wait_for_contact_update_complete(self.pce,
                                                                      0)
        bt_contacts_utils.erase_contacts(self.pse)
        return passing
