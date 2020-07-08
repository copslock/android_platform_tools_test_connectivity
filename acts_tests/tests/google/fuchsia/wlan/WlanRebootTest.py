#!/usr/bin/env python3
#
#   Copyright 2020 - The Android Open Source Project
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
import os
import re
import time

from multiprocessing import Process

from acts import asserts
from acts import context
from acts import utils
from acts.controllers import iperf_client
from acts.controllers import iperf_server
from acts.controllers import pdu
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib.radvd import Radvd
from acts.controllers.ap_lib import radvd_constants
from acts.controllers.ap_lib.radvd_config import RadvdConfig
from acts.test_utils.abstract_devices.wlan_device import create_wlan_device
from acts.test_utils.abstract_devices.utils_lib import wlan_utils
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

# Constants, for readibility
AP = 'ap'
DUT = 'dut'
SOFT = 'soft'
HARD = 'hard'
BAND_2G = '2g'
BAND_5G = '5g'
BANDS = [BAND_2G, BAND_5G]
IPV4 = 'ipv4'
IPV6 = 'ipv6'
IP_VERSIONS = [{
    IPV4: True,
    IPV6: False
}, {
    IPV4: False,
    IPV6: True
}, {
    IPV4: True,
    IPV6: True
}]
INTERRUPTS = [True, False]

DUT_NETWORK_CONNECTION_TIMEOUT = 60
DUT_IP_ADDRESS_TIMEOUT = 15


def get_test_name(settings):
    """Generates a test name from test settings. If a test_name is present
    in settings, that is returned.

    Args:
        settings: a dictionary containing test setting (see run_reboot_test)
    Returns:
        A string test name. E.g test_soft_reboot_ap_ipv4_ipv6_5g
    """
    if 'test_name' in settings:
        return settings['test_name']
    else:
        test_name = 'test_%s_reboot_%s' % (settings['reboot_type'],
                                           settings['reboot_device'])
        if settings.get('interrupt', None):
            test_name += '_interrupt'
        if settings['ipv4']:
            test_name += '_%s' % IPV4
        if settings['ipv6']:
            test_name += '_%s' % IPV6
        test_name += '_%s' % settings['band']
        if 'loops' in settings:
            test_name += '_loops_%s' % settings['loops']
    return test_name


class WlanRebootTest(WifiBaseTest):
    """Tests wlan reconnects in different reboot scenarios.

    Testbed Requirement:
    * One ACTS compatible device (dut)
    * One Whirlwind Access Point (will also serve as iperf server)
    * One PduDevice
    """
    def __init__(self, controllers):
        WifiBaseTest.__init__(self, controllers)
        self.tests = [
            'test_soft_reboot_ap_ipv4_ipv6_2g_5g',
            'test_hard_reboot_ap_ipv4_ipv6_2g_5g',
            'test_soft_reboot_dut_ipv4_ipv6_2g_5g',
            'test_hard_reboot_dut_ipv4_ipv6_2g_5g'
        ]
        if 'reboot_stress_tests' in self.user_params:
            self.tests.append('test_reboot_stress')

    def setup_class(self):
        super().setup_class()

        self.android_devices = getattr(self, 'android_devices', [])
        self.fuchsia_devices = getattr(self, 'fuchsia_devices', [])

        if 'dut' in self.user_params:
            if self.user_params['dut'] == 'fuchsia_devices':
                self.dut = create_wlan_device(self.fuchsia_devices[0])
            elif self.user_params['dut'] == 'android_devices':
                self.dut = create_wlan_device(self.android_devices[0])
            else:
                raise ValueError('Invalid DUT specified in config. (%s)' %
                                 self.user_params['dut'])
        else:
            # Default is an android device, just like the other tests
            self.dut = create_wlan_device(self.android_devices[0])

        self.access_point = self.access_points[0]

        # IPerf Server is run on the AP and setup in the tests
        self.iperf_server_on_ap = None
        self.iperf_client_on_dut = self.iperf_clients[0]

        self.router_adv_daemon = None

        # Times (in seconds) to wait for DUT network connection and assigning an
        # ip address to the wlan interface.
        wlan_reboot_params = self.user_params.get('wlan_reboot_params', {})
        self.dut_network_connection_timeout = wlan_reboot_params.get(
            'dut_network_connection_timeout', DUT_NETWORK_CONNECTION_TIMEOUT)
        self.dut_ip_address_timeout = wlan_reboot_params.get(
            'dut_ip_address_timeout', DUT_IP_ADDRESS_TIMEOUT)

    def setup_test(self):
        self.access_point.stop_all_aps()
        if self.router_adv_daemon:
            self.router_adv_daemon.stop()
        self.dut.wifi_toggle_state(True)
        for ad in self.android_devices:
            ad.droid.wakeLockAcquireBright()
            ad.droid.wakeUpNow()
        for fd in self.fuchsia_devices:
            fd.wlan_policy_lib.wlanCreateClientController()
            fd.wlan_policy_lib.wlanStartClientConnections()
        self.dut.clear_saved_networks()
        self.dut.disconnect()
        self.router_adv_daemon = None
        self.ssid = utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G)

    def teardown_test(self):
        self.access_point.stop_all_aps()
        self.dut.clear_saved_networks()
        for fd in self.fuchsia_devices:
            fd.wlan_policy_lib.wlanStopClientConnections()
        self.dut.disconnect()
        for ad in self.android_devices:
            ad.droid.wakeLockRelease()
            ad.droid.goToSleepNow()
        self.dut.turn_location_off_and_scan_toggle_off()
        self.dut.reset_wifi()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.get_log(test_name, begin_time)

    def setup_ap(self, ssid, band, ipv4=True, ipv6=False):
        """Setup ap with basic config.

        Args:
            ssid: string, ssid to setup on ap
            band: string ('2g' or '5g') of band to setup.
            ipv4: True if using ipv4 (dhcp), else False.
            ipv6: True if using ipv6 (radvd), else False.
        """
        if band == BAND_2G:
            wlan_utils.setup_ap(access_point=self.access_point,
                                profile_name='whirlwind',
                                channel=11,
                                ssid=ssid)
        elif band == BAND_5G:
            wlan_utils.setup_ap(access_point=self.access_point,
                                profile_name='whirlwind',
                                channel=36,
                                ssid=ssid)

        if not ipv4:
            self.access_point.stop_dhcp()
        if ipv6:
            radvd_config = RadvdConfig(
                prefix='fd00::/64',
                adv_send_advert=radvd_constants.ADV_SEND_ADVERT_ON,
                adv_on_link=radvd_constants.ADV_ON_LINK_ON,
                adv_autonomous=radvd_constants.ADV_AUTONOMOUS_ON)

            if band == BAND_2G:
                self.router_adv_daemon = Radvd(self.access_point.ssh,
                                               self.access_point.wlan_2g)
            elif band == BAND_5G:
                self.router_adv_daemon = Radvd(self.access_point.ssh,
                                               self.access_point.wlan_5g)
            self.router_adv_daemon.start(radvd_config)

        self.log.info('Network (SSID: %s) is up.' % ssid)

    def save_and_connect(self, ssid):
        """Associates the dut with the network running on the AP and saves
        network to device.

        Args:
            ssid: string, ssid to connect DUT to

        Raises:
            EnvironmentError, if saving network fails
            ConnectionError, if device fails to connect to network
        """
        self.dut.save_network(self.ssid)
        self.dut.associate(self.ssid)

    def setup_save_and_connect_to_network(self,
                                          ssid,
                                          band,
                                          ipv4=True,
                                          ipv6=False):
        """Setup ap with passed params, saves network, and connects the dut with
        the network running on the AP and saves network.

        Args:
            ssid: string, ssid to setup and connect to
            band: string ('2g' or '5g') of band to setup.
            ipv4: True if using ipv4 (dhcp), else False.
            ipv6: True if using ipv6 (radvd), else False.
        """
        self.setup_ap(ssid, band, ipv4, ipv6)
        self.save_and_connect(ssid)

    def wait_until_dut_gets_ipv4_addr(self, interface):
        """Checks if device has an ipv4 private address. Sleeps 1 second between
        retries.

        Args:
            interface: string, name of interface from which to get ipv4 address.

        Raises:
            ConnectionError, if DUT does not have an ipv4 address after all
            timeout.
        """
        self.log.info(
            'Checking if DUT has received an ipv4 addr. Will retry for %s '
            'seconds.' % self.dut_ip_address_timeout)
        timeout = time.time() + self.dut_ip_address_timeout
        while time.time() < timeout:
            ip_addrs = self.dut.get_interface_ip_addresses(interface)

            if len(ip_addrs['ipv4_private']) > 0:
                self.log.info('DUT has an ipv4 address: %s' %
                              ip_addrs['ipv4_private'][0])
                break
            else:
                self.log.debug(
                    'DUT does not yet have an ipv4 address...retrying in 1 '
                    'second.')
                time.sleep(1)
        else:
            raise ConnectionError('DUT failed to get an ipv4 address.')

    def wait_until_dut_gets_ipv6_addr(self, interface):
        """Checks if device has an ipv6 private local address. Sleeps 1 second
        between retries.

        Args:
            interface: string, name of interface from which to get ipv6 address.

        Raises:
            ConnectionError, if DUT does not have an ipv6 address after all
            timeout.
        """
        self.log.info(
            'Checking if DUT has received an ipv6 addr. Will retry for %s '
            'seconds.' % self.dut_ip_address_timeout)
        timeout = time.time() + self.dut_ip_address_timeout
        while time.time() < timeout:
            ip_addrs = self.dut.get_interface_ip_addresses(interface)
            if len(ip_addrs['ipv6_private_local']) > 0:
                self.log.info('DUT has an ipv6 private local address: %s' %
                              ip_addrs['ipv6_private_local'][0])
                break
            else:
                self.log.debug(
                    'DUT does not yet have an ipv6 address...retrying in 1 '
                    'second.')
                time.sleep(1)
        else:
            raise ConnectionError('DUT failed to get an ipv6 address.')

    def setup_iperf_server_on_ap(self, band):
        """Configures iperf server based on the tests band.

        Args:
            band: string ('2g' or '5g') of band to setup.
        """
        if band == BAND_2G:
            return iperf_server.IPerfServerOverSsh(
                self.user_params['AccessPoint'][0]['ssh_config'],
                5201,
                test_interface=self.access_point.wlan_2g)
        elif band == BAND_5G:
            return iperf_server.IPerfServerOverSsh(
                self.user_params['AccessPoint'][0]['ssh_config'],
                5201,
                test_interface=self.access_point.wlan_5g)

    def get_iperf_server_address(self, iperf_server_on_ap, ip_version):
        """Retrieves the ip address of the iperf server.

        Args:
            iperf_server_on_ap: IPerfServer object, linked to AP
            ip_version: string, the ip version (ipv4 or ipv6)

        Returns:
            String, the ip address of the iperf_server
        """
        iperf_server_addresses = iperf_server_on_ap.get_interface_ip_addresses(
            iperf_server_on_ap.test_interface)
        if ip_version == IPV4:
            iperf_server_ip_address = (
                iperf_server_addresses['ipv4_private'][0])
        elif ip_version == IPV6:
            if iperf_server_addresses['ipv6_private_local']:
                iperf_server_ip_address = (
                    iperf_server_addresses['ipv6_private_local'][0])
            else:
                iperf_server_ip_address = (
                    '%s%%%s' % (iperf_server_addresses['ipv6_link_local'][0],
                                self.iperf_client_on_dut.test_interface))
        else:
            raise ValueError('Invalid IP version: %s' % ip_version)

        return iperf_server_ip_address

    def verify_traffic_between_dut_and_ap(self,
                                          iperf_server_on_ap,
                                          iperf_client_on_dut,
                                          ip_version=IPV4):
        """Runs IPerf traffic from the iperf client (dut) and the iperf
        server (and vice versa) and verifies traffic was able to pass
        successfully.

        Args:
            iperf_server_on_ap: IPerfServer object, linked to AP
            iperf_client_on_dut: IPerfClient object, linked to DUT
            ip_version: string, the ip version (ipv4 or ipv6)

        Raises:
            ValueError, if invalid ip_version is passed.
            ConnectionError, if traffic is not passed successfully in both
                directions.
        """
        dut_ip_addresses = self.dut.get_interface_ip_addresses(
            iperf_client_on_dut.test_interface)

        iperf_server_ip_address = self.get_iperf_server_address(
            iperf_server_on_ap, ip_version)

        self.log.info(
            'Attempting to pass traffic from DUT to IPerf server (%s).' %
            iperf_server_ip_address)
        tx_file = iperf_client_on_dut.start(iperf_server_ip_address,
                                            '-i 1 -t 10 -J', 'reboot_tx')
        tx_results = iperf_server.IPerfResult(tx_file)
        if not tx_results.avg_receive_rate or tx_results.avg_receive_rate == 0:
            raise ConnectionError(
                'Failed to pass IPerf traffic from DUT to server (%s). TX '
                'Average Receive Rate: %s' %
                (iperf_server_ip_address, tx_results.avg_receive_rate))
        else:
            self.log.info(
                'Success: Traffic passed from DUT to IPerf server (%s).' %
                iperf_server_ip_address)
        self.log.info(
            'Attempting to pass traffic from IPerf server (%s) to DUT.' %
            iperf_server_ip_address)
        rx_file = iperf_client_on_dut.start(iperf_server_ip_address,
                                            '-i 1 -t 10 -R -J', 'reboot_rx')
        rx_results = iperf_server.IPerfResult(rx_file)
        if not rx_results.avg_receive_rate or rx_results.avg_receive_rate == 0:
            raise ConnectionError(
                'Failed to pass IPerf traffic from server (%s) to DUT. RX '
                'Average Receive Rate: %s' %
                (iperf_server_ip_address, rx_results.avg_receive_rate))
        else:
            self.log.info(
                'Success: Traffic passed from IPerf server (%s) to DUT.' %
                iperf_server_ip_address)

    def start_dut_ping_process(self, iperf_server_on_ap, ip_version=IPV4):
        """Creates a  process that pings the AP from the DUT.

        Runs in parallel for 15 seconds, so it can be interrupted by a reboot.
        Sleeps for a few seconds to ensure pings have started.

        Args:
            iperf_server_on_ap: IPerfServer object, linked to AP
            ip_version: string, the ip version (ipv4 or ipv6)
        """
        ap_address = self.get_iperf_server_address(iperf_server_on_ap,
                                                   ip_version)
        if ap_address:
            self.log.info(
                'Starting ping process to %s in parallel. Logs from this '
                'process will be suppressed, since it will be intentionally '
                'interrupted.' % ap_address)
            ping_proc = Process(target=self.dut.ping,
                                args=[ap_address],
                                kwargs={'count': 15})
            with utils.SuppressLogOutput():
                ping_proc.start()
            # Allow for a few seconds of pinging before allowing it to be
            # interrupted.
            time.sleep(3)
        else:
            raise ConnectionError('Failed to retrieve APs iperf address.')

    def prepare_dut_for_reconnection(self):
        """Perform any actions to ready DUT for reconnection.

        These actions will vary depending on the DUT. eg. android devices may
        need to be woken up, ambient devices should not require any interaction,
        etc.
        """
        self.dut.wifi_toggle_state(True)
        for ad in self.android_devices:
            ad.droid.wakeUpNow()
        for fd in self.fuchsia_devices:
            fd.wlan_policy_lib.wlanCreateClientController()

    def wait_for_dut_network_connection(self, ssid):
        """Checks if device is connected to given network. Sleeps 1 second
        between retries.

        Args:
            ssid: string of ssid
        Raises:
            ConnectionError, if DUT is not connected after all timeout.
        """
        self.log.info(
            'Checking if DUT is connected to %s network. Will retry for %s '
            'seconds.' % (ssid, self.dut_network_connection_timeout))
        timeout = time.time() + self.dut_network_connection_timeout
        while time.time() < timeout:
            try:
                is_connected = self.dut.is_connected(ssid=ssid)
            except Exception as err:
                self.log.debug('SL4* call failed. Retrying in 1 second.')
                is_connected = False
            finally:
                if is_connected:
                    self.log.info('Success: DUT has connected.')
                    break
                else:
                    self.log.debug(
                        'DUT not connected to network %s...retrying in 1 second.'
                        % ssid)
                    time.sleep(1)
        else:
            raise ConnectionError('DUT failed to connect to the network.')

    def write_csv_time_to_reconnect(self, test_name, time_to_reconnect):
        """Writes the time to reconnect to a csv file.
        Args:
            test_name: the name of the test case
            time_to_reconnect: the time from when the rebooted device came back
                up to when it reassociated (or 'FAIL'), if it failed to
                reconnect.
        """
        log_context = context.get_current_context()
        log_path = os.path.join(log_context.get_base_output_path(),
                                'WlanRebootTest/')
        csv_file_name = '%stime_to_reconnect.csv' % log_path
        self.log.info('Writing to %s' % csv_file_name)
        with open(csv_file_name, 'a') as csv_file:
            csv_file.write('%s,%s\n' % (test_name, time_to_reconnect))

    def log_and_continue(self, run, time_to_reconnect=None, error=None):
        """Writes the time to reconnect to the csv file before continuing, used
        in stress tests runs.

        Args:
            time_to_reconnect: the time from when the rebooted device came back
                ip to when reassociation occurred.
            run: the run number in a looped stress tested.,
            error: string, error message to log before continuing with the test
        """
        if error:
            self.log.info(
                'Device failed to reconnect to network %s on run %s. Error: %s'
                % (self.ssid, run, error))
            self.write_csv_time_to_reconnect(
                '%s_run_%s' % (self.test_name, run), 'FAIL')

        else:
            self.log.info(
                'Device successfully reconnected to network %s after %s seconds'
                ' on run %s.' % (self.ssid, time_to_reconnect, run))
            self.write_csv_time_to_reconnect(
                '%s_run_%s' % (self.test_name, run), time_to_reconnect)

    def run_reboot_test(self, settings):
        """Runs a reboot test based on a given config.
            1. Setups up a network, associates the dut, and saves the network.
            2. Verifies the dut receives ip address(es).
            3. Verifies traffic between DUT and AP (IPerf client and server).
            4. Reboots (hard or soft) the device (dut or ap).
                - If the ap was rebooted, setup the same network again.
            5. Wait for reassociation or timeout.
            6. If reassocation occurs:
                - Verifies the dut receives ip address(es).
                - Verifies traffic between DUT and AP (IPerf client and server).
            7. Logs time to reconnect (or failure to reconnect)
            8. If stress testing, repeats steps 4 - 7 for N loops.

        Args:
            settings: dictionary containing the following values:
                reboot_device: string ('dut' or 'ap') of the device to reboot.
                reboot_type: string ('soft' or 'hard') of how to reboot the
                    reboot_device.
                band: string ('2g' or '5g') of band to setup.
                ipv4: True if using ipv4 (dhcp), else False.
                ipv6: True if using ipv6 (radvd), else False.

                Optional:
                    interrupt: if True, the DUT will be pinging the AP in a
                        parallel process when the reboot occurs. This is used to
                        compare reconnect times when idle to active.
                    test_name: name of the test, used when stress testing.
                    loops: number of times to perform test, used when stress
                        testing.

        Raises:
            ValueError, if ipv4 and ipv6 are both False
            ValueError, if band is not '2g' or '5g'
            ValueError, if reboot_device is not 'dut' or 'ap'
            ValueError, if reboot_type is not 'soft' or 'hard'

        """
        loops = settings.get('loops', 1)
        passed_count = 0
        ipv4 = settings['ipv4']
        ipv6 = settings['ipv6']
        reboot_device = settings['reboot_device']
        reboot_type = settings['reboot_type']
        band = settings['band']
        interrupt = settings.get('interrupt', None)

        # Validate test settings.
        if not ipv4 and not ipv6:
            raise ValueError('Either ipv4, ipv6, or both must be True.')
        if reboot_device != DUT and reboot_device != AP:
            raise ValueError('Invalid reboot device: %s' % reboot_device)
        if reboot_type != SOFT and reboot_type != HARD:
            raise ValueError('Invalid reboot type: %s' % reboot_type)
        if band != BAND_2G and band != BAND_5G:
            raise ValueError('Invalid band: %s' % band)

        self.setup_save_and_connect_to_network(self.ssid,
                                               band,
                                               ipv4=ipv4,
                                               ipv6=ipv6)
        self.wait_for_dut_network_connection(self.ssid)

        dut_test_interface = self.iperf_client_on_dut.test_interface
        if ipv4:
            self.wait_until_dut_gets_ipv4_addr(dut_test_interface)
        if ipv6:
            self.wait_until_dut_gets_ipv6_addr(dut_test_interface)

        self.iperf_server_on_ap = self.setup_iperf_server_on_ap(band)
        self.iperf_server_on_ap.start()

        if ipv4:
            self.verify_traffic_between_dut_and_ap(self.iperf_server_on_ap,
                                                   self.iperf_client_on_dut)
        if ipv6:
            self.verify_traffic_between_dut_and_ap(self.iperf_server_on_ap,
                                                   self.iperf_client_on_dut,
                                                   ip_version=IPV6)

        # Looping reboots for stress testing
        for run in range(loops):
            run += 1
            self.log.info('Starting run %s of %s.' % (run, loops))

            # Ping from DUT to AP during AP reboot
            if interrupt:
                if ipv4:
                    self.start_dut_ping_process(self.iperf_server_on_ap)
                if ipv6:
                    self.start_dut_ping_process(self.iperf_server_on_ap,
                                                ip_version=IPV6)

            # DUT reboots
            if reboot_device == DUT:
                if type(self.iperf_client_on_dut
                        ) == iperf_client.IPerfClientOverSsh:
                    self.iperf_client_on_dut.close_ssh()
                if reboot_type == SOFT:
                    self.dut.device.reboot()
                elif reboot_type == HARD:
                    self.dut.hard_power_cycle(self.pdu_devices)

            # AP reboots
            elif reboot_device == AP:
                if reboot_type == SOFT:
                    self.log.info('Cleanly stopping ap.')
                    self.access_point.stop_all_aps()
                elif reboot_type == HARD:
                    self.iperf_server_on_ap.close_ssh()
                    self.access_point.hard_power_cycle(self.pdu_devices)
                self.setup_ap(self.ssid, band, ipv4=ipv4, ipv6=ipv6)

            self.prepare_dut_for_reconnection()
            uptime = time.time()
            try:
                self.wait_for_dut_network_connection(self.ssid)
                time_to_reconnect = time.time() - uptime
                if ipv4:
                    self.wait_until_dut_gets_ipv4_addr(dut_test_interface)
                if ipv6:
                    self.wait_until_dut_gets_ipv6_addr(dut_test_interface)
                self.iperf_server_on_ap.start()

                if ipv4:
                    self.verify_traffic_between_dut_and_ap(
                        self.iperf_server_on_ap, self.iperf_client_on_dut)
                if ipv6:
                    self.verify_traffic_between_dut_and_ap(
                        self.iperf_server_on_ap,
                        self.iperf_client_on_dut,
                        ip_version=IPV6)

            except ConnectionError as err:
                self.log_and_continue(run, error=err)
            else:
                passed_count += 1
                self.log_and_continue(run, time_to_reconnect=time_to_reconnect)

        if passed_count == loops:
            asserts.explicit_pass(
                'Test Summary: device successfully reconnected to network %s '
                '%s/%s times.' % (self.ssid, passed_count, loops))

        else:
            asserts.fail(
                'Test Summary: device failed reconnection test. Reconnected to '
                'network %s %s/%s times.' % (self.ssid, passed_count, loops))

    # 12 test cases
    def test_soft_reboot_ap_ipv4_ipv6_2g_5g(self):
        test_list = []
        for combination in itertools.product(IP_VERSIONS, BANDS, INTERRUPTS):
            test_settings = {
                'reboot_device': AP,
                'reboot_type': SOFT,
                'ipv4': combination[0][IPV4],
                'ipv6': combination[0][IPV6],
                'band': combination[1],
                'interrupt': combination[2]
            }
            test_list.append(test_settings)

        self.run_generated_testcases(self.run_reboot_test,
                                     settings=test_list,
                                     name_func=get_test_name)

    # 12 test cases
    def test_hard_reboot_ap_ipv4_ipv6_2g_5g(self):
        test_list = []
        for combination in itertools.product(IP_VERSIONS, BANDS, INTERRUPTS):
            test_settings = {
                'reboot_device': AP,
                'reboot_type': HARD,
                'ipv4': combination[0][IPV4],
                'ipv6': combination[0][IPV6],
                'band': combination[1],
                'interrupt': combination[2]
            }
            test_list.append(test_settings)

        self.run_generated_testcases(self.run_reboot_test,
                                     settings=test_list,
                                     name_func=get_test_name)

    # 6 test cases
    def test_soft_reboot_dut_ipv4_ipv6_2g_5g(self):
        test_list = []
        for combination in itertools.product(IP_VERSIONS, BANDS):
            test_settings = {
                'reboot_device': DUT,
                'reboot_type': SOFT,
                'ipv4': combination[0][IPV4],
                'ipv6': combination[0][IPV6],
                'band': combination[1]
            }
            test_list.append(test_settings)

        self.run_generated_testcases(self.run_reboot_test,
                                     settings=test_list,
                                     name_func=get_test_name)

    # 6 test cases
    def test_hard_reboot_dut_ipv4_ipv6_2g_5g(self):
        # Note: This may need to be removed if non-battery android devices
        # are added.
        asserts.skip_if(self.user_params['dut'] == 'android_devices',
                        'No hard reboots for android battery devices.')
        test_list = []
        for combination in itertools.product(IP_VERSIONS, BANDS):
            test_settings = {
                'reboot_device': DUT,
                'reboot_type': HARD,
                'ipv4': combination[0][IPV4],
                'ipv6': combination[0][IPV6],
                'band': combination[1]
            }
            test_list.append(test_settings)

        self.run_generated_testcases(self.run_reboot_test,
                                     settings=test_list,
                                     name_func=get_test_name)

    def test_reboot_stress(self):
        """Creates reboot test(s) and runs it repeatedly. Setup in config file.
        Eg.
            'reboot_stress_tests': ['test_soft_reboot_ap_ipv4_2g_loop_10]
                will run a a soft reboot ap test, using ipv4 on 2g, 10 times
                repeatedly. Time_to_reconnect logs occur after each run and will
                write to the same csv file with '<test_name>_run_N' as the tests
                name.
        """
        pattern = re.compile(
            r'.*?(hard|soft)_reboot_(dut|ap)_(interrupt_)?(ipv4_ipv6|ipv4|ipv6)_(2g|5g)(_loops?_([0-9]*))?',
            re.IGNORECASE)
        test_list = []
        for test_name in self.user_params['reboot_stress_tests']:
            test_match = re.match(pattern, test_name)
            if test_match:
                reboot_type = test_match.group(1)
                reboot_device = test_match.group(2)
                interrupt = True if test_match.group(3) else False
                ip_version = test_match.group(4)
                ipv4 = 'ipv4' in ip_version
                ipv6 = 'ipv6' in ip_version
                band = test_match.group(5)
                if test_match.group(6):
                    loops = test_match.group(7)
                else:
                    loops = 1
                settings = {
                    'test_name': test_name,
                    'reboot_type': reboot_type,
                    'reboot_device': reboot_device,
                    'band': band,
                    'ipv4': ipv4,
                    'ipv6': ipv6,
                    'interrupt': interrupt,
                    'loops': int(loops)
                }
                test_list.append(settings)
            else:
                self.log.info('Invalid test name: %s. Ignoring.' % test_name)
        self.run_generated_testcases(self.run_reboot_test,
                                     settings=test_list,
                                     name_func=get_test_name)
