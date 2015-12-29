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

"""
This test script exercises batch scanning scenarios.
"""

import pprint
from queue import Empty
import time
from contextlib import suppress

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import generate_ble_advertise_objects
from acts.test_utils.bt.bt_test_utils import scan_result

# TODO: (tturney) finish separating out testcases in various suits out to here.


class BatchingTest(BluetoothBaseTest):
    tests = None
    default_timeout = 10

    def __init__(self, controllers):
        BluetoothBaseTest.__init__(self, controllers)
        self.droid1, self.ed1 = self.droids[1], self.eds[1]
        self.tests = (
            "test_automatic_clearing_of_batch_data",
        )

    #TODO: (tturney) finish testcase.
    @BluetoothBaseTest.bt_test_wrap
    def test_automatic_clearing_of_batch_data(self):
        """Test automatic clearing of batch data.

        Test establishing a gatt connection between a GATT server and GATT
        client.

        Steps:
        1.

        Expected Result:

        Returns:
          Pass if True
          Fail if False

        TAGS: LE, Advertising, Scanning, Batch Scanning
        Priority: 3
        """
        scan_droid, scan_event_dispatcher = self.droid, self.ed
        advertise_droid, advertise_event_dispatcher = self.droid1, self.ed1
        ad_callback, ad_data, ad_settings = generate_ble_advertise_objects(
            advertise_droid)
        advertise_droid.bleStartBleAdvertising(
            ad_data, ad_settings, ad_callback)

        scan_filter_list = scan_droid.bleGenFilterList()
        scan_droid.bleBuildScanFilter(scan_filter_list)
        scan_droid.bleSetScanSettingsReportDelayMillis(1000)
        scan_settings = scan_droid.bleBuildScanSetting()
        scan_callback = scan_droid.bleGenScanCallback()
        system_time_nanos = scan_droid.getSystemElapsedRealtimeNanos()
        scan_droid.bleStartBleScan(
            scan_filter_list, scan_settings, scan_callback)
        expected_event = scan_result.format(scan_callback)
        scan_droid.pop_event(expected_event, self.default_timeout)
        return True
