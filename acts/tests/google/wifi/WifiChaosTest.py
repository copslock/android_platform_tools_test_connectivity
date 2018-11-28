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

import re
import sys
import time

import acts.controllers.packet_capture as packet_capture
import acts.signals as signals
import acts.test_utils.wifi.rpm_controller_utils as rutils
import acts.test_utils.wifi.wifi_datastore_utils as dutils
import acts.test_utils.wifi.wifi_test_utils as wutils

from acts import asserts
from acts.base_test import BaseTestClass
from acts.controllers.ap_lib import hostapd_constants
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

WifiEnums = wutils.WifiEnums

WAIT_BEFORE_CONNECTION = 1
SINGLE_BAND = 1
DUAL_BAND = 2

TIMEOUT = 60
PING_ADDR = 'www.google.com'


class WifiChaosTest(WifiBaseTest):
    """ Tests for wifi IOT

        Test Bed Requirement:
          * One Android device
          * Wi-Fi IOT networks visible to the device
    """

    def __init__(self, configs):
        BaseTestClass.__init__(self, configs)
        self.generate_interop_tests()

    def generate_interop_testcase(self, base_test, testcase_name, ssid_dict):
        """Generates a single test case from the given data.

        Args:
            base_test: The base test case function to run.
            testcase_name: The name of the test case.
            ssid_dict: The information about the network under test.
        """
        ssid = testcase_name
        test_tracker_uuid = ssid_dict[testcase_name]['uuid']
        hostname = ssid_dict[testcase_name]['host']
        if not testcase_name.startswith('test_'):
            testcase_name = 'test_%s' % testcase_name
        test_case = test_tracker_info(uuid=test_tracker_uuid)(
            lambda: base_test(ssid, hostname))
        setattr(self, testcase_name, test_case)
        self.tests.append(testcase_name)

    def generate_interop_tests(self):
        for ssid_dict in self.user_params['interop_ssid']:
            testcase_name = list(ssid_dict)[0]
            self.generate_interop_testcase(self.interop_base_test,
                                           testcase_name, ssid_dict)

    def setup_class(self):
        self.dut = self.android_devices[0]
        wutils.wifi_test_device_init(self.dut)
        # Set country code explicitly to "US".
        self.dut.droid.wifiSetCountryCode(wutils.WifiEnums.CountryCode.US)

        asserts.assert_true(
            self.lock_pcap(),
            "Could not lock a Packet Capture. Aborting Interop test.")

        wutils.wifi_toggle_state(self.dut, True)

    def lock_pcap(self):
        """Lock a Packet Capturere to use for the test."""

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
            return False

        pcap_config = {'ssh_config':{'user':'root'} }
        pcap_config['ssh_config']['host'] = host

        self.pcap = packet_capture.PacketCapture(pcap_config)
        return True

    def setup_test(self):
        self.dut.droid.wakeLockAcquireBright()
        self.dut.droid.wakeUpNow()

    def on_pass(self, test_name, begin_time):
        wutils.stop_pcap(self.pcap, self.pcap_pid, True)

    def on_fail(self, test_name, begin_time):
        wutils.stop_pcap(self.pcap, self.pcap_pid, False)
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.cat_adb_log(test_name, begin_time)

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
                                    timeout=sec + 1)
        self.log.debug("Ping Result = %s" % result)
        if "100% packet loss" in result:
            raise signals.TestFailure("100% packet loss during ping")

    def unlock_and_turn_off_ap(self, hostname, rpm_port, rpm_ip):
        """UNlock the AP in datastore and turn off the AP.

        Args:
            hostname: Hostname of the AP.
            rpm_port: Port number on the RPM for the AP.
            rpm_ip: RPM's IP address.

        """
        # Un-Lock AP in datastore.
        self.log.debug("Un-lock AP in datastore")
        if not dutils.unlock_device(hostname):
            self.log.warning("Failed to unlock %s AP. Check AP in datastore.")
        # Turn OFF AP from the RPM port.
        rutils.turn_off_ap(rpm_port, rpm_ip)

    def run_connect_disconnect(self, network, hostname, rpm_port, rpm_ip,
                               release_ap):
        """Run connect/disconnect to a given network in loop.

           Args:
               network: Dict, network information.
               hostname: Hostanme of the AP to connect to.
               rpm_port: Port number on the RPM for the AP.
               rpm_ip: Port number on the RPM for the AP.
               release_ap: Flag to determine if we should turn off the AP yet.

           Raises: TestFailure if the network connection fails.

        """
        for attempt in range(1):
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
                # TODO:(bmahadev) Uncomment after scan issue is fixed.
                # self.dut.take_bug_report(ssid, begin_time)
                # self.dut.cat_adb_log(ssid, begin_time)
                if release_ap:
                    self.unlock_and_turn_off_ap(hostname, rpm_port, rpm_ip)
                raise signals.TestFailure("Failed to connect to %s" % ssid)

    def get_band_and_chan(self, ssid):
        """Get the band and channel information from SSID.

        Args:
            ssid: SSID of the network.

        """
        ssid_info = ssid.split('_')
        self.band = ssid_info[-1]
        for item in ssid_info:
            # Skip over the router model part.
            if 'ch' in item and item != ssid_info[0]:
                self.chan = re.search(r'(\d+)',item).group(0)
                return
        raise signals.TestFailure("Channel information not found in SSID.")

    def interop_base_test(self, ssid, hostname):
        """Base test for all the connect-disconnect interop tests.

        Args:
            ssid: string, SSID of the network to connect to.
            hostname: string, hostname of the AP.

        Steps:
            1. Lock AP in datstore.
            2. Turn on AP on the rpm switch.
            3. Run connect-disconnect in loop.
            4. Turn off AP on the rpm switch.
            5. Unlock AP in datastore.

        """
        network = {}
        network['password'] = 'password'
        network['SSID'] = ssid
        release_ap = False
        wutils.reset_wifi(self.dut)

        # Lock AP in datastore.
        self.log.info("Lock AP in datastore")
        if not dutils.lock_device(hostname):
            self.log.warning("Failed to lock %s AP. Unlock AP in datastore"
                             " and try again.")
            raise signals.TestFailure("Failed to lock AP")

        ap_info = dutils.show_device(hostname)

        band = SINGLE_BAND
        if ('ssid_2g' in ap_info) and ('ssid_5g' in ap_info):
            band = DUAL_BAND
        if (band == SINGLE_BAND) or (
                band == DUAL_BAND and '5G' in ssid):
            release_ap = True

        # Get AP RPM attributes and Turn ON AP.
        rpm_ip = ap_info['rpm_ip']
        rpm_port = ap_info['rpm_port']

        rutils.turn_on_ap(self.pcap, ssid, rpm_port, rpm_ip=rpm_ip)
        self.log.info("Finished turning ON AP.")
        # Experimental. Some APs take upto a min to come online.
        time.sleep(60)

        self.get_band_and_chan(ssid)
        self.pcap.configure_monitor_mode(self.band, self.chan)
        self.pcap_pid = wutils.start_pcap(
                self.pcap, self.band.lower(), self.log_path, self.test_name)
        self.run_connect_disconnect(network, hostname, rpm_port, rpm_ip,
                                    release_ap)

        # Un-lock only if it's a single band AP or we are running the last band.
        if release_ap:
            self.unlock_and_turn_off_ap(hostname, rpm_port, rpm_ip)
