#!/usr/bin/env python3
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

import time
import acts.test_utils.wifi.wifi_test_utils as wutils

from acts import asserts
from acts import utils
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

DEFAULT_TIMEOUT = 30
DEFAULT_SLEEPTIME = 5

class WifiP2pManagerTest(WifiBaseTest):
    """Tests for APIs in Android's WifiP2pManager class.

    Test Bed Requirement:
    * Two Android devices
    """

    def __init__(self, controllers):
        WifiBaseTest.__init__(self, controllers)

    def setup_class(self):
        self.dut = self.android_devices[0]
        self.dut_client = self.android_devices[1]

        wutils.wifi_test_device_init(self.dut)
        self.dut.droid.wifiP2pInitialize()
        asserts.assert_true(self.dut.droid.wifiP2pIsEnabled(),
                            "DUT's p2p should be initialized but it didn't")
        self.dut_name = "Android_" + utils.rand_ascii_str(4)
        self.dut.droid.wifiP2pSetDeviceName(self.dut_name)
        wutils.wifi_test_device_init(self.dut_client)
        self.dut_client.droid.wifiP2pInitialize()
        asserts.assert_true(self.dut_client.droid.wifiP2pIsEnabled(),
                            "Peer's p2p should be initialized but it didn't")
        self.dut_client_name = "Android_" + utils.rand_ascii_str(4)
        self.dut_client.droid.wifiP2pSetDeviceName(self.dut_client_name)

    def teardown_class(self):
        self.dut.droid.wifiP2pClose()
        self.dut_client.droid.wifiP2pClose()

    def setup_test(self):
        for ad in self.android_devices:
            ad.droid.wakeLockAcquireBright()
            ad.droid.wakeUpNow()

    def teardown_test(self):
        # Clear p2p group info
        for ad in self.android_devices:
            ad.droid.wifiP2pRequestPersistentGroupInfo()
            event = ad.ed.pop_event("WifiP2pOnPersistentGroupInfoAvailable", DEFAULT_TIMEOUT)
            for network in event['data']:
                ad.droid.wifiP2pDeletePersistentGroup(network['NetworkId'])
            ad.droid.wakeLockRelease()
            ad.droid.goToSleepNow()

    def on_fail(self, test_name, begin_time):
        for ad in self.android_devices:
            ad.take_bug_report(test_name, begin_time)
            ad.cat_adb_log(test_name, begin_time)

    """Helper Functions"""

    def _is_discovered(self, event, device_name):
        for device in event['data']['Peers']:
            if device['Name'] == device_name:
                return True
        return False

    """Test Cases"""
    @test_tracker_info(uuid="28ddb16c-2ce4-44da-92f9-701d0dacc321")
    def test_p2p_discovery(self):
        """Verify the p2p discovery functionality

        Steps:
        1. Discover the target device
        """
        # Discover the target device
        self.log.info("Device discovery")
        self.dut.droid.wifiP2pDiscoverPeers()
        self.dut_client.droid.wifiP2pDiscoverPeers()
        dut_event = self.dut.ed.pop_event("WifiP2pOnPeersAvailable", DEFAULT_TIMEOUT)
        peer_event = self.dut_client.ed.pop_event("WifiP2pOnPeersAvailable", DEFAULT_TIMEOUT)
        asserts.assert_true(self._is_discovered(dut_event, self.dut_client_name),
                            "DUT didn't discovered peer device")
        asserts.assert_true(self._is_discovered(peer_event, self.dut_name),
                            "Peer didn't discovered DUT device")

    @test_tracker_info(uuid="708af645-6562-41da-9cd3-bdca428ac308")
    def test_p2p_connect(self):
        """Verify the p2p connect functionality

        Steps:
        1. Discover the target device
        2. Request the connection
        3. Disconnect
        """
        # Discover the target device
        self.log.info("Device discovery")
        self.dut.droid.wifiP2pDiscoverPeers()
        self.dut_client.droid.wifiP2pDiscoverPeers()
        dut_event = self.dut.ed.pop_event("WifiP2pOnPeersAvailable", DEFAULT_TIMEOUT)
        peer_event = self.dut_client.ed.pop_event("WifiP2pOnPeersAvailable", DEFAULT_TIMEOUT)
        asserts.assert_true(self._is_discovered(dut_event, self.dut_client_name),
                            "DUT didn't discovered peer device")
        asserts.assert_true(self._is_discovered(peer_event, self.dut_name),
                            "Peer didn't discovered DUT device")

        # Request the connection
        self.log.info("Create p2p connection")
        self.dut.droid.wifiP2pConnect(self.dut_client_name)
        time.sleep(DEFAULT_SLEEPTIME)
        self.dut_client.droid.wifiP2pAcceptConnection()
        self.dut.ed.pop_event("WifiP2pConnectOnSuccess", DEFAULT_TIMEOUT)

        # Disconnect
        self.log.info("Disconnect")
        self.dut.droid.wifiP2pRemoveGroup()
        self.dut.droid.wifiP2pRequestConnectionInfo()
        event = self.dut.ed.pop_event("WifiP2pOnConnectionInfoAvailable", DEFAULT_TIMEOUT)
        asserts.assert_false(event['data']['groupFormed'],
                             "P2P connection should be disconnected but it didn't")
