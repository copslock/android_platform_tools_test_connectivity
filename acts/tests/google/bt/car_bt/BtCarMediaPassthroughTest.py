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
Automated tests for the testing passthrough commands in Avrcp/A2dp profile.
"""

import time

from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt import bt_test_utils
from acts.test_utils.bt import BtEnum
from acts.test_utils.car import car_media_utils

DEFAULT_WAIT_TIME = 1.0
DEFAULT_EVENT_TIMEOUT = 1.0


class BtCarMediaPassthroughTest(BluetoothBaseTest):
    def setup_class(self):
        # AVRCP roles
        self.CT = self.android_devices[0]
        self.TG = self.android_devices[1]
        # A2DP roles for the same devices
        self.SNK = self.CT
        self.SRC = self.TG
        # To keep track of the state of the MediaBrowserService
        self.mediaBrowserServiceRunning = False
        self.btAddrCT = self.CT.droid.bluetoothGetLocalAddress()
        self.btAddrTG = self.TG.droid.bluetoothGetLocalAddress()

        # Reset bluetooth
        bt_test_utils.setup_multiple_devices_for_bt_test([self.CT, self.TG])
        bt_test_utils.reset_bluetooth([self.CT, self.TG])

        # Pair and connect the devices.
        if not bt_test_utils.pair_pri_to_sec(self.CT.droid, self.TG.droid):
            self.log.error("Failed to pair")
            return False

        # TODO - check for Avrcp Connection state as well.
        # For now, the passthrough tests will catch Avrcp Connection failures
        # But add an explicit test for it.
        if not bt_test_utils.connect_pri_to_sec(
            self.log, self.SNK, self.SRC.droid,
            set([BtEnum.BluetoothProfile.A2DP_SINK.value])):
            return False

        return True

    def initMBS(self):
        """
        This is required to be done before running any of the passthrough
        commands.
        1. Starts up the AvrcpMediaBrowserService on the TG.
           This MediaBrowserService is part of the SL4A app
        2. Connects a MediaBrowser to the Carkitt's A2dpMediaBrowserService
        """
        if (not self.mediaBrowserServiceRunning):
            self.log.info("Starting MBS")
            self.TG.droid.bluetoothMediaAvrcpMediaBrowserServiceStart()
            # TODO - Wait for an event back instead of sleep
            time.sleep(DEFAULT_WAIT_TIME)
            self.mediaBrowserServiceRunning = True

        self.CT.droid.bluetoothMediaConnectToA2dpMediaBrowserService()
        #TODO - Wait for an event back instead of sleep
        time.sleep(DEFAULT_WAIT_TIME)

    def setup_test(self):
        for d in self.android_devices:
            d.ed.clear_all_events()

    def on_fail(self, test_name, begin_time):
        self.log.debug("Test {} failed.".format(test_name))

    def teardown_test(self):
        def cleanup():
            """
            Stop the browser service if it is running to clean up the slate.
            """
            if (self.mediaBrowserServiceRunning):
                self.log.info("Stopping MBS")
                self.TG.droid.bluetoothMediaAvrcpMediaBrowserServiceStop()
                self.mediaBrowserServiceRunning = False

        cleanup()

    def test_play_pause(self):
        """
        Test the Play and Pause passthrough commands

        Pre-Condition:
        1. Devices previously bonded & Connected

        Steps:
        1. Invoke Play, Pause from CT
        2. Wait to receive the corresponding received event from TG

        Returns:
        True    if the event was received
        False   if the event was not received

        Priority: 0
        """
        # Set up the MediaBrowserService
        self.initMBS()
        if not car_media_utils.send_media_passthrough_cmd(
                self.log, self.CT, self.TG, car_media_utils.CMD_MEDIA_PLAY,
                car_media_utils.EVENT_PLAY_RECEIVED, DEFAULT_EVENT_TIMEOUT):
            return False
        if not car_media_utils.send_media_passthrough_cmd(
                self.log, self.CT, self.TG, car_media_utils.CMD_MEDIA_PAUSE,
                car_media_utils.EVENT_PAUSE_RECEIVED, DEFAULT_EVENT_TIMEOUT):
            return False
        return True

    def test_passthrough(self):
        """
        Test the Skip Next & Skip Previous passthrough commands

        Pre-Condition:
        1. Devices previously bonded & Connected

        Steps:
        1. Invoke other passthrough commands (skip >> & <<) from CT
        2. Wait to receive the corresponding received event from TG

        Returns:
        True    if the event was received
        False   if the event was not received

        Priority: 0
        """
        # Set up the MediaBrowserService
        self.initMBS()
        if not car_media_utils.send_media_passthrough_cmd(
                self.log, self.CT, self.TG,
                car_media_utils.CMD_MEDIA_SKIP_NEXT,
                car_media_utils.EVENT_SKIPNEXT_RECEIVED,
                DEFAULT_EVENT_TIMEOUT):
            return False
        if not car_media_utils.send_media_passthrough_cmd(
                self.log, self.CT, self.TG,
                car_media_utils.CMD_MEDIA_SKIP_PREV,
                car_media_utils.EVENT_SKIPPREV_RECEIVED,
                DEFAULT_EVENT_TIMEOUT):
            return False

        # Just pause media before test ends
        if not car_media_utils.send_media_passthrough_cmd(
                self.log, self.CT, self.TG, car_media_utils.CMD_MEDIA_PAUSE,
                car_media_utils.EVENT_PAUSE_RECEIVED):
            return False

        return True
