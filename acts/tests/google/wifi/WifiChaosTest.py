#!/usr/bin/env python3.4
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

import itertools
import pprint
import time

import acts.controllers.packet_capture as packet_capture
import acts.signals as signals
import acts.test_utils.wifi.wifi_test_utils as wutils
import acts.test_utils.wifi.wifi_datastore_utils as dutils
import acts.test_utils.wifi.rpm_controller_utils as rutils

from acts import asserts
from acts.controllers.ap_lib import hostapd_constants
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

WifiEnums = wutils.WifiEnums

WAIT_BEFORE_CONNECTION = 1
SINGLE_BAND = 1
DUAL_BAND = 2

TIMEOUT = 1
PING_ADDR = 'www.google.com'

class WifiChaosTest(WifiBaseTest):
    """ Tests for wifi IOT

        Test Bed Requirement:
          * One Android device
          * Wi-Fi IOT networks visible to the device
    """

    def setup_class(self):
        self.dut = self.android_devices[0]
        wutils.wifi_test_device_init(self.dut)

        req_params = ["wpa2_hosts"]
        self.unpack_userparams(req_param_names=req_params)

        asserts.assert_true(
            len(self.wpa2_hosts) > 0,
            "Need at least one iot network with psk.")

        wutils.wifi_toggle_state(self.dut, True)

    def setup_test(self):
        self.dut.droid.wakeLockAcquireBright()
        self.dut.droid.wakeUpNow()

    def teardown_test(self):
        self.dut.droid.wakeLockRelease()
        self.dut.droid.goToSleepNow()
        wutils.reset_wifi(self.dut)


    """Helper Functions"""

    def scan_and_connect_by_id(self, network, net_id):
        """Scan for network and connect using network id.

        Args:
            net_id: Integer specifying the network id of the network.

        """
        ssid = network[WifiEnums.SSID_KEY]
        wutils.start_wifi_connection_scan_and_ensure_network_found(self.dut,
            ssid)
        wutils.wifi_connect_by_id(self.dut, net_id)

    def run_ping(self, sec):
        """Run ping for given number of seconds.

        Args:
            sec: Time in seconds to run teh ping traffic.

        """
        self.log.info("Running ping for %d seconds" % sec)
        result = self.dut.adb.shell("ping -w %d %s" % (sec, PING_ADDR),
            timeout=sec+1)
        self.log.debug("Ping Result = %s" % result)
        if "100% packet loss" in result:
            raise signals.TestFailure("100% packet loss during ping")

    def run_connect_disconnect(self, network):
        for attempt in range(2):
            # TODO:(bmahadev) Change it to 5 or more attempts later.
                try:
                    begin_time = time.time()
                    ssid = network[WifiEnums.SSID_KEY]
                    net_id = self.dut.droid.wifiAddNetwork(network)
                    asserts.assert_true(net_id != -1, "Add network %s failed" % network)
                    self.log.info("Connecting to %s" % ssid)
                    self.scan_and_connect_by_id(network, net_id)
                    self.run_ping(1)
                    wutils.wifi_forget_network(self.dut, ssid)
                    time.sleep(WAIT_BEFORE_CONNECTION)
                except:
                    self.log.error("Connection to %s network failed on the %d "
                                   "attempt." % (ssid, attempt))
                    self.dut.take_bug_report(ssid, begin_time)
                    self.dut.cat_adb_log(ssid, begin_time)

    """Tests"""

    def test_interop_wpa2(self):
        """Test to iterate through al the APs and test interop.

        Steps:
            1. Lock a Packet Capturer in datastore.
            2. Lock AP in datstore.
            3. Turn on AP on the rpm switch.
            4. Run connect-disconnect in loop.
            5. Turn off AP on the rpm switch.
            6. Unlock AP in datastore.
            7. Unlock Packet Capturere in datastore.

        """
        # Get list of devices from the datastore.
        locked_pcap = False
        devices = dutils.get_devices()

        for device in devices:

            device_name = device['hostname']
            device_type = device['ap_label']
            if device_type == 'PCAP'and dutils.lock_device(device_name):
                host = device['ip_address']
                self.log.info("Locked Packet Capture device: %s" % device_name)
                locked_pcap = True
                break

            elif device_type == 'PCAP':
                self.log.warning("Failed to lock %s PCAP.")

        if not locked_pcap:
            raise signals.TestFailure("Could not lock a Packet Capture. Aborting Interop test.")

        pcap_config = {'ssh_config':{'user':'root'} }
        pcap_config['ssh_config']['host'] = host

        pcap = packet_capture.PacketCapture(pcap_config)
        network = {"password": "password"}

        for ap in self.wpa2_hosts:

            wutils.reset_wifi(self.dut)

            ap_info = dutils.show_device(ap)
            ssid_2g = ssid_5g = None

            if 'ssid_2g' in ap_info:
                ssid_2g = ap_info['ssid_2g']
            if 'ssid_5g' in ap_info:
                ssid_5g = ap_info['ssid_5g']
            name = ap_info["hostname"]

            # Lock AP in datastore.
            self.log.info("Lock AP in datastore")
            if not dutils.lock_device(name):
                self.log.warning("Failed to lock %s AP. Unlock AP in datastore"
                                 " and try again.")
                continue

            # Get AP RPM attributes and Turn ON AP.
            rpm_ip = ap_info['rpm_ip']
            rpm_port = ap_info['rpm_port']

            if ssid_2g:
                scan_ssid = ssid_2g
            else:
                scan_ssid = ssid_5g

            rutils.turn_on_ap(pcap, scan_ssid, rpm_port, rpm_ip=rpm_ip)
            self.log.info("Finished turning ON AP.")
            time.sleep(10)

            if ssid_2g:
                network["SSID"] = ssid_2g
                self.run_connect_disconnect(network)

            if ssid_5g:
                network["SSID"] = ssid_5g
                self.run_connect_disconnect(network)

            # Un-Lock AP in datastore.
            self.log.debug("Un-lock AP in datastore")
            if not dutils.unlock_device(name):
                self.log.warning("Failed to unlock %s AP. Check AP in datastore.")

            # Turn OFF AP from the RPM port.
            rutils.turn_off_ap(rpm_port, rpm_ip)
