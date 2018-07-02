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

from acts import asserts
from acts import base_test
from acts.controllers import adb
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings
from acts.test_decorators import test_tracker_info
from acts.test_utils.tel.tel_test_utils import start_adb_tcpdump
from acts.test_utils.tel.tel_test_utils import stop_adb_tcpdump
from acts.test_utils.net import connectivity_test_utils as cutils
from acts.test_utils.wifi import wifi_test_utils as wutils

import random
import time

WLAN = "wlan0"
PKTS = 5
SERVER_UDP_KEEPALIVE = "python /root/udp_nat_keepalive.py"
KEEPALIVE_DATA = "ff"


class NattKeepAliveTest(base_test.BaseTestClass):
    """ Tests for NATT keepalive """

    def setup_class(self):
        """ Setup devices for tests and unpack params """

        self.dut = self.android_devices[0]
        req_params = ("wifi_network", "remote_server", "server_ssh_config")
        self.unpack_userparams(req_params)

        wutils.wifi_connect(self.dut, self.wifi_network)

        self.ip_a = self.dut.droid.connectivityGetIPv4Addresses(WLAN)[0]
        self.ip_b = self.remote_server
        self.log.info("DUT IP addr: %s" % self.ip_a)
        self.log.info("Remote server IP addr: %s" % self.ip_b)

        self.ssh_settings = settings.from_config(self.server_ssh_config)
        self.ssh = connection.SshConnection(self.ssh_settings)

        self.tcpdump_pid_a = None
        self.tcpdump_file_a = None

    def teardown_class(self):
        wutils.reset_wifi(self.dut)

    def setup_test(self):
        self.tcpdump_pid_a = start_adb_tcpdump(
            self.dut, self.test_name, mask='all')

    def teardown_test(self):
        if self.tcpdump_pid_a:
            stop_adb_tcpdump(
                self.dut, self.tcpdump_pid_a, pull_tcpdump=True)
        self.tcpdump_pid_a = None

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)

    """ Helper functions """

    def _verify_time_interval(self, time_interval, cmd_out):
        """ Verify time diff between packets is equal to time interval """

        self.log.info("Packet Info: \n%s\n" % cmd_out)
        pkts = cmd_out.split("\n")

        prev = 0
        for i in range(len(pkts)):
            interval, data = pkts[i][1:-1].split(',')

            # verify data
            if data.lstrip().rstrip()[1:-1] != KEEPALIVE_DATA:
                self.log.error("Server received invalid data %s" % data)
                return False

            # verify time interval
            curr = int(interval)
            if i == 0:
                prev = curr
                continue
            if curr - prev != time_interval:
                self.log.error("Keepalive time interval is %s, expected %s"
                               % (curr-prev, time_interval))
                return False
            prev = curr

        return True

    """ Tests begin """

    @test_tracker_info(uuid="c9012da2-656f-44ef-bad6-26892335d4bd")
    def test_natt_keepalive_ipv4(self):
        """ Test natt keepalive over wifi

        Steps:
          1. Open a UDP port 4500 on linux host
          2. Start NATT keepalive packets on DUT and send 5 packets
          3. Verify that 5 keepalive packets reached host with data '0xff'
        """

        # set a time interval
        result = True
        time_interval = random.randint(10, 60)
        port = random.randint(8000, 9000)
        self.log.info("NATT keepalive time interval is %s" % time_interval)
        self.log.info("Source port is %s" % port)
        time_out = time_interval * PKTS + 6

        # start NATT keep alive
        nka_key = cutils.start_natt_keepalive(
            self.dut, self.ip_a, port, self.ip_b, time_interval)
        asserts.assert_true(nka_key, "Failed to start NATT keepalive")

        # capture packets on server
        self.log.info("Capturing keepalive packets on %s" % self.ip_b)
        cmd_out = None
        try:
            cmd_out = self.ssh.run(SERVER_UDP_KEEPALIVE, timeout = time_out)
        except Exception as e:
            self.log.error("Failed to capture packets on server: %s" % e)
            result = False

        # verify packets received
        if cmd_out:
            result = self._verify_time_interval(time_interval, cmd_out.stdout)

        # stop NATT keep alive
        status = cutils.stop_natt_keepalive(self.dut, nka_key)
        asserts.assert_true(status, "Failed to stop NATT keepalive")

        return result

    @test_tracker_info(uuid="8ab20733-4a9e-4e4d-a46f-4d32a9f221c5")
    def test_natt_keepalive_ipv4_invalid_interval(self):
        """ Test invalid natt keepalive time interval

        Steps:
          1. Start NATT keepalive with time interval less than 10 seconds
          2. API should return invalid interval
        """

        # start NATT keep alive
        port = random.randint(8000, 9000)
        nka_key = cutils.start_natt_keepalive(
            self.dut, self.ip_a, port, self.ip_b, 2)
        asserts.assert_true(not nka_key,
                            "Started NATT keepalive with invalid interval")

    """ Tests end """
