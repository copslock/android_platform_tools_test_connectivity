#
#   Copyright 2018 - The Android Open Source Project
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
import os
import random
import socket
import threading
import time

from acts import asserts
from acts import base_test
from acts import test_runner
from acts.controllers import adb
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.tel_data_utils import wait_for_cell_data_connection
from acts.test_utils.tel.tel_test_utils import verify_http_connection
from acts.test_utils.tel.tel_test_utils import _check_file_existance
from acts.test_utils.tel.tel_test_utils import _generate_file_directory_and_file_name
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.net.connectivity_const import MULTIPATH_PREFERENCE_NONE as NONE
from acts.test_utils.net.connectivity_const import MULTIPATH_PREFERENCE_HANDOVER as HANDOVER
from acts.test_utils.net.connectivity_const import MULTIPATH_PREFERENCE_RELIABILITY as RELIABILITY
from acts.test_utils.net.connectivity_const import MULTIPATH_PREFERENCE_PERFORMANCE as PERFORMANCE

DOWNLOAD_PATH = "/sdcard/Download/"
RELIABLE = RELIABILITY | HANDOVER

class DataCostTest(base_test.BaseTestClass):
    """ Tests for Wifi Tethering """

    def setup_class(self):
        """ Setup devices for tethering and unpack params """

        self.dut = self.android_devices[0]
        req_params = ("wifi_network", "download_file")
        self.unpack_userparams(req_params)
        wutils.reset_wifi(self.dut)
        self.dut.droid.telephonyToggleDataConnection(True)
        wait_for_cell_data_connection(self.log, self.dut, True)
        asserts.assert_true(
            verify_http_connection(self.log, self.dut),
            "HTTP verification failed on cell data connection")
        self.cell_network = self.dut.droid.connectivityGetActiveNetwork()
        self.log.info("cell network %s" % self.cell_network)
        wutils.wifi_connect(self.dut, self.wifi_network)
        self.wifi_network = self.dut.droid.connectivityGetActiveNetwork()
        self.log.info("wifi network %s" % self.wifi_network)
        self.sub_id = str(self.dut.droid.telephonyGetSubscriberId())

    def teardown_class(self):
        wutils.reset_wifi(self.dut)
        self.dut.droid.telephonyToggleDataConnection(True)

    """ Helper functions """

    def _get_total_data_usage_for_device(self, conn_type):
        """ Get total data usage in MB for device

        Args:
            1. conn_type - MOBILE/WIFI data usage

        Returns:
            Data usage in MB
        """
        # end time should be in milli seconds and at least 2 hours more than the
        # actual end time. NetStats:bucket is of size 2 hours and to ensure to
        # get the most recent data usage, end_time should be +2hours
        end_time = int(time.time() * 1000) + 2 * 1000 * 60 * 60
        data_usage = self.dut.droid.connectivityQuerySummaryForDevice(
            conn_type, self.sub_id, 0, end_time)
        data_usage /= 1000.0 * 1000.0 # convert data_usage to MB
        self.log.info("Total data usage is: %s" % data_usage)
        return data_usage

    def _check_if_multipath_preference_valid(self, val, exp):
        """ Check if multipath value is same as expected

        Args:
            1. val - multipath preference for the network
            2. exp - expected multipath preference value
        """
        if exp == NONE:
            asserts.assert_true(val == exp, "Multipath value should be 0")
        else:
            asserts.assert_true(val >= exp,
                                "Multipath value should be at least %s" % exp)

    def _verify_multipath_preferences(self, wifi_pref, cell_pref):
        """ Verify mutlipath preferences for wifi and cell networks

        Args:
            wifi_pref: Expected multipath value for wifi network
            cell_pref: Expected multipath value for cell network
        """
        wifi_multipath = \
            self.dut.droid.connectivityGetMultipathPreferenceForNetwork(
                self.wifi_network)
        cell_multipath = \
            self.dut.droid.connectivityGetMultipathPreferenceForNetwork(
                self.cell_network)
        self.log.info("WiFi multipath preference: %s" % wifi_multipath)
        self.log.info("Cell multipath preference: %s" % cell_multipath)
        self.log.info("Checking multipath preference for wifi")
        self._check_if_multipath_preference_valid(wifi_multipath, wifi_pref)
        self.log.info("Checking multipath preference for cell")
        self._check_if_multipath_preference_valid(cell_multipath, cell_pref)

    """ Test Cases """

    @test_tracker_info(uuid="e86c8108-3e84-4668-bae4-e5d2c8c27910")
    def test_multipath_preference_low_data_limit(self):
        """ Verify multipath preference when mobile data limit is low

        Steps:
            1. DUT has WiFi and LTE data
            2. Set mobile data usage limit to low value
            3. Verify that multipath preference is 0 for cell network
        """
        # verify multipath preference values
        self._verify_multipath_preferences(RELIABLE, RELIABLE)

        # set low data limit on mobile data
        total_pre = self._get_total_data_usage_for_device(0)
        self.log.info("Setting data usage limit to %sMB" % (total_pre + 5))
        self.dut.droid.connectivitySetDataUsageLimit(
            self.sub_id, str(int((total_pre + 5) * 1000.0 * 1000.0)))

        # reset data limit
        self.dut.droid.connectivityFactoryResetNetworkPolicies(self.sub_id)

        # verify multipath preference values
        self._verify_multipath_preferences(RELIABLE, NONE)

    @test_tracker_info(uuid="a2781411-d880-476a-9f40-2c67e0f97db9")
    def test_multipath_preference_data_download(self):
        """ Verify multipath preference when large file is downloaded

        Steps:
            1. DUT has WiFi and LTE data
            2. WiFi is active network
            3. Download large file over cell network
            4. Verify multipath preference on cell network is 0
        """
        # verify multipath preference for wifi and cell networks
        self._verify_multipath_preferences(RELIABLE, RELIABLE)

        # download file with cell network
        self.dut.droid.connectivityNetworkOpenConnection(self.cell_network,
                                                         self.download_file)
        file_folder, file_name = _generate_file_directory_and_file_name(
            self.download_file, DOWNLOAD_PATH)
        file_path = os.path.join(file_folder, file_name)
        self.log.info("File path: %s" % file_path)
        if _check_file_existance(self.dut, file_path):
            self.log.info("File exists. Removing file %s" % file_name)
            self.dut.adb.shell("rm -rf %s%s" % (DOWNLOAD_PATH, file_name))

        #  verify multipath preference values
        self._verify_multipath_preferences(RELIABLE, NONE)

    # TODO gmoturu@: Need to add tests that use the mobility rig and test when
    # the WiFi signal is poor and data signal is good.
