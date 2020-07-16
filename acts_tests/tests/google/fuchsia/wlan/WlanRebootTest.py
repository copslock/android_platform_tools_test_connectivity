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

import os
import re
import time
from multiprocessing import Process
import itertools

from acts import asserts
from acts import context
from acts import utils
from acts.controllers import pdu
from acts.controllers import iperf_client
from acts.controllers import iperf_server
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib.radvd import Radvd
from acts.controllers.ap_lib import radvd_constants
from acts.controllers.ap_lib.radvd_config import RadvdConfig
from acts.test_utils.abstract_devices.wlan_device import create_wlan_device
from acts.test_utils.abstract_devices.utils_lib import wlan_utils
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

# TODO(46633): Add in policy layer stuff once its implemented (see SetupTest)

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

        self.android_devices = getattr(self, 'android_devices', [])
        self.fuchsia_devices = getattr(self, 'fuchsia_devices', [])

        self.access_point = self.access_points[0]
        self.pdus = self.register_controller(pdu)

        # IPerf Server is run on the AP and setup in the tests
        self.iperf_server = None
        self.iperf_client = self.iperf_clients[0]

        self.router_adv_daemon = None

        # Times (in seconds) to retry different stages of the reboot/reconnect
        # processes.
        wlan_reboot_params = self.user_params.get('wlan_reboot_params', None)
        if wlan_reboot_params:
            self.timeout_for_unreachable_ap = wlan_reboot_params.get(
                'timeout_for_unreachable_ap', 3)
            self.timeout_for_pingable_ap = wlan_reboot_params.get(
                'timeout_for_pingable_ap', 30)
            self.timeout_for_sshable_ap = wlan_reboot_params.get(
                'timeout_for_sshable_ap', 30)
            self.timeout_for_unreachable_dut = wlan_reboot_params.get(
                'timeout_for_unreachable_dut', 3)
            self.timeout_for_pingable_dut = wlan_reboot_params.get(
                'timeout_for_pingable_dut', 30)
            self.timeout_for_dut_network_connection = wlan_reboot_params.get(
                'timeout_for_dut_network_connection', 60)
            self.timeout_for_dut_can_ping = wlan_reboot_params.get(
                'timeout_for_dut_can_ping', 3)
            self.timeout_for_ip_address = wlan_reboot_params.get(
                'timeout_for_ip_address', 15)
            self.timeout_for_reinitialize_services = wlan_reboot_params.get(
                'timeout_for_reinitialize_services', 3)
        else:
            self.timeout_for_unreachable_ap = 3
            self.timeout_for_pingable_ap = 60
            self.timeout_for_sshable_ap = 30
            self.timeout_for_unreachable_dut = 3
            self.timeout_for_pingable_dut = 30
            self.timeout_for_dut_network_connection = 60
            self.timeout_for_dut_can_ping = 3
            self.timeout_for_ip_address = 15
            self.timeout_for_reinitialize_services = 3

    def setup_test(self):
        self.access_point.stop_all_aps()
        if self.router_adv_daemon:
            self.router_adv_daemon.stop()
        for ad in self.android_devices:
            ad.droid.wakeLockAcquireBright()
            ad.droid.wakeUpNow()
        self.dut.wifi_toggle_state(True)
        self.dut.disconnect()
        self.router_adv_daemon = None
        if self.user_params['dut'] == 'fuchsia_devices':
            self.dut.device.wlan_policy_lib.wlanCreateClientController()
            # TODO(52319): Clear the saved networks list once
            # removeSavedNetwork and clearSavedNetworks are implemented.
            self.dut.device.wlan_policy_lib.wlanStartClientConnections()
        self.ssid = utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G)

    def teardown_test(self):
        for ad in self.android_devices:
            ad.droid.wakeLockRelease()
            ad.droid.goToSleepNow()
        self.dut.turn_location_off_and_scan_toggle_off()
        self.dut.disconnect()
        self.dut.reset_wifi()
        self.access_point.stop_all_aps()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.get_log(test_name, begin_time)

    def setup_ap(self, band, ipv4=True, ipv6=False):
        """Setup ap with basic config.

        Args:
            band: string ('2g' or '5g') of band to setup.
            ipv4: True if using ipv4 (dhcp), else False.
            ipv6: True if using ipv6 (radvd), else False.
        """
        if band == BAND_2G:
            wlan_utils.setup_ap(access_point=self.access_point,
                                profile_name='whirlwind',
                                channel=11,
                                ssid=self.ssid)
        elif band == BAND_5G:
            wlan_utils.setup_ap(access_point=self.access_point,
                                profile_name='whirlwind',
                                channel=36,
                                ssid=self.ssid)

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

        self.log.info('Network (SSID: %s) is up.' % self.ssid)

    def associate_and_save(self):
        """Associates the dut with the network running on the AP and saves
        network to device.
        """
        wlan_utils.associate(client=self.dut, ssid=self.ssid)
        if self.user_params['dut'] == 'fuchsia_devices':
            response = self.dut.device.wlan_policy_lib.wlanSaveNetwork(
                self.ssid, 'None')
            if response.get('error'):
                raise EnvironmentError(
                    'Failed to save network %s for FuchsiaDevice %s: %s' %
                    (self.ssid, self.dut.device.ip, response.get('error')))

    def setup_ap_associate_and_save(self, band, ipv4=True, ipv6=False):
        """Setup ap with basic config and associates the dut with the network
        running on the AP and saves network.

        Args:
            band: string ('2g' or '5g') of band to setup.
            ipv4: True if using ipv4 (dhcp), else False.
            ipv6: True if using ipv6 (radvd), else False.
        """
        self.setup_ap(band, ipv4, ipv6)
        self.associate_and_save()

    def wait_until_dut_gets_ipv4_addr(self):
        """Checks if device has an ipv4 private address. Sleeps 1 second between
        retries.

        Raises:
            ConnectionError, if DUT does not have an ipv4 address after all
            timeout.
        """
        self.log.info(
            'Checking if DUT has received an ipv4 addr. Will retry for %s '
            'seconds.' % self.timeout_for_ip_address)
        timeout = time.time() + self.timeout_for_ip_address
        while time.time() < timeout:
            ip_addrs = self.dut.get_interface_ip_addresses(
                self.iperf_client.test_interface)
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

    def wait_until_dut_gets_ipv6_addr(self):
        """Checks if device has an ipv6 private local address. Sleeps 1 second
        between retries.

        Raises:
            ConnectionError, if DUT does not have an ipv6 address after all
            timeout.
        """
        self.log.info(
            'Checking if DUT has received an ipv6 addr. Will retry for %s '
            'seconds.' % self.timeout_for_ip_address)
        timeout = time.time() + self.timeout_for_ip_address
        while time.time() < timeout:
            ip_addrs = self.dut.get_interface_ip_addresses(
                self.iperf_client.test_interface)
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

    def setup_iperf_server(self, band):
        """Configures iperf server based on the tests band.

        Args:
            band: string ('2g' or '5g') of band to setup.
        """
        if self.iperf_server and self.iperf_server.started:
            self.iperf_server.stop()
        if band == BAND_2G:
            self.iperf_server = iperf_server.IPerfServerOverSsh(
                self.user_params['AccessPoint'][0]['ssh_config'],
                5201,
                test_interface=self.access_point.wlan_2g)
        elif band == BAND_5G:
            self.iperf_server = iperf_server.IPerfServerOverSsh(
                self.user_params['AccessPoint'][0]['ssh_config'],
                5201,
                test_interface=self.access_point.wlan_5g)

    def get_iperf_server_address(self, ip_version):
        """Retrieves the ip address of the iperf server.

        Args:
            ip_version: string, the ip version (ipv4 or ipv6)

        Returns:
            String, the ip address of the iperf_server
        """
        iperf_server_addresses = self.iperf_server.get_interface_ip_addresses(
            self.iperf_server.test_interface)
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
                                self.iperf_client.test_interface))
        else:
            raise ValueError('Invalid IP version: %s' % ip_version)

        return iperf_server_ip_address

    def verify_traffic(self, ip_version=IPV4):
        """Runs IPerf traffic from the iperf client (dut) and the iperf
        server (and vice versa) and verifies traffic was able to pass
        successfully.

        Args:
            ip_version: string, the ip version (ipv4 or ipv6)

        Raises:
            ValueError, if invalid ip_version is passed.
            ConnectionError, if traffic is not passed successfully in both
                directions.
        """
        dut_ip_addresses = self.dut.get_interface_ip_addresses(
            self.iperf_client.test_interface)

        iperf_server_ip_address = self.get_iperf_server_address(ip_version)

        self.log.info(
            'Attempting to pass traffic from DUT to IPerf server (%s).' %
            iperf_server_ip_address)
        tx_file = self.iperf_client.start(iperf_server_ip_address,
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
        rx_file = self.iperf_client.start(iperf_server_ip_address,
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

    def start_dut_ping_process(self, ip_version=IPV4):
        """Creates a  process that pings the AP from the DUT.

        Runs in parallel for 15 seconds, so it can be interrupted by a reboot.
        Sleeps for a few seconds to ensure pings have started.

        Args:
            ip_version: string, the ip version (ipv4 or ipv6)
        """
        ap_address = self.get_iperf_server_address(ip_version)
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

    def wait_for_unreachable_dut(self):
        """Checks if DUT is unreachable. Sleeps 1 second between retries.

        Raises:
            ConnectionError, if DUT is still pingable after all timeout.
        """
        self.log.info('Expecting unreachable DUT. Will retry for %s seconds.' %
                      self.timeout_for_unreachable_dut)
        timeout = time.time() + self.timeout_for_unreachable_dut
        while time.time() < timeout:
            if not utils.is_pingable(self.dut.device.ip):
                self.log.info('Success: DUT is unreachable.')
                break
            else:
                self.log.debug('DUT still pingable...retrying in 1 second.')
                time.sleep(1)
        else:
            raise ConnectionError('AP is still reachable.')

    def wait_for_pingable_dut(self):
        """Checks if DUT is pingable. Sleeps 1 second between retries.

        Raises:
            ConnectionError, if DUT is not pingable after all timeout.
        """
        self.log.info('Attempting to ping DUT. Will retry for %s seconds.' %
                      self.timeout_for_pingable_dut)
        timeout = time.time() + self.timeout_for_pingable_dut
        while time.time() < timeout:
            if utils.is_pingable(self.dut.device.ip):
                self.log.info('Success: DUT is pingable.')
                break
            else:
                self.log.debug('Could not ping DUT...retrying in 1 second.')
                time.sleep(1)
        else:
            raise ConnectionError('Failed to ping DUT.')

    def prepare_dut_object_after_hard_reboot(self):
        """Prepares DUT objects after a hard reboot has occurred.

        This essentially reinitializes SL4* on the DUT after it has been hard
        rebooted and ensures the device wifi is on. This may require some device
        specific logic.
        """
        # start_services has a backoff loop, but not long enough to accommodate
        # for a full boot time, so the additional loop is necessary.
        timeout = time.time() + self.timeout_for_reinitialize_services
        while time.time() < timeout:
            try:
                self.dut.device.reinitialize_services()
            except Exception as err:
                self.log.debug(
                    'Failed to reinitialize services. Retrying. Error: %s' %
                    err)
            else:
                self.log.info('Services successfully reinitialized.')
                break
        else:
            raise ConnectionError('Failed to reinitialize services, exiting.')

        self.dut.wifi_toggle_state(True)

    def prepare_dut_object_for_hard_reboot(self):
        """Prepares DUT objects for hard reboot.

        This is not to be confused with clean, soft reboot functionality, and
        should not prepare the device in any way, but can be used to clean up
        device objects so ACTS behaves with the upcoming reboot. This may
        require to have device specific logic.
        """
        if self.user_params['dut'] == 'fuchsia_devices':
            self.iperf_client.close_ssh()
            self.dut.device.clean_up()

    def hard_reboot_dut(self):
        """Hard reboots the DUT.
            - prepares the DUT object (not the hardware itself) for the reboot.
            - suppresses logs during reboot to allow for expected errors
            - abruptly kills power to the DUT
            - verifies the DUT is unreachable
            - restores power to the DUT
            - verifies the DUT comes back online

        If successful, prepare DUT object (i.e. reinitialize SL4*).

        If an exception occurs, still attempt to reinitialize SL4* so other
        tests can continue. This is only possible if the exception occurred
        before the power is killed. Otherwise, log that SL4* could not be reset.
        """
        # Clean up *Device controllers (not the devices themselves)
        self.prepare_dut_object_for_hard_reboot()
        # Suppress logs so that disconnect errors don't fail the test.
        self.log.info('Hard rebooting DUT, log output will be suppressed.')
        with utils.SuppressLogOutput():
            try:
                # Get PDU device and port for DUT
                dut_pdu_config = self.dut.device.conf_data['PduDevice']
                dut_pdu, dut_pdu_port = pdu.get_pdu_port_for_device(
                    dut_pdu_config, self.pdus)

                # Kill power to DUT
                self.log.info('Killing power to DUT...')
                dut_pdu.off(str(dut_pdu_port))

                # Verify DUT is unreachable
                self.wait_for_unreachable_dut()

                # Restore power to DUT
                self.log.info('Restoring power to DUT...')
                dut_pdu.on(str(dut_pdu_port))

                # Verify DUT is back online
                self.wait_for_pingable_dut()

            finally:
                # If something fails, attempt to restart services things so
                # tests can continue.
                try:
                    self.prepare_dut_object_after_hard_reboot()
                except:
                    self.log.info('Failed to restart services.')

        self.log.info('DUT is back up.')

    def wait_for_unreachable_ap(self):
        """Checks if AP is unreachable. Sleeps 1 second between retries.

        Raises:
            ConnectionError, if AP is still reachable after all timeout.
        """
        self.log.info('Expecting unreachable AP. Will retry for %s seconds.' %
                      self.timeout_for_unreachable_ap)
        timeout = time.time() + self.timeout_for_unreachable_ap
        while time.time() < timeout:
            if not self.access_point.is_pingable():
                self.log.info('Success: AP is unreachable.')
                break
            else:
                self.log.debug('AP is still pingable...retrying in 1 second.')
                time.sleep(1)
        else:
            raise ConnectionError('AP is still reachable.')

    def wait_for_pingable_ap(self):
        """Checks if AP is pingable. Sleeps 1 second between retries.

        Raises:
            ConnectionError, if AP is not pingable after all timeout.
        """
        self.log.info('Attempting to ping AP. Will retry for %s seconds.' %
                      self.timeout_for_pingable_ap)
        timeout = time.time() + self.timeout_for_pingable_ap
        while time.time() < timeout:
            if self.access_point.is_pingable():
                self.log.info('Success: AP is pingable.')
                break
            else:
                self.log.debug('Could not ping AP...retrying in 1 second.')
                time.sleep(1)
        else:
            raise ConnectionError('Failed to ping AP.')

    def wait_for_sshable_ap(self):
        """Checks if AP is sshable. Sleeps 1 second between retries.

        Raises:
            ConnectionError, if could not ssh to AP after all timeout.
        """
        self.log.info('Attempting to ssh to AP. Will retry for %s seconds.' %
                      self.timeout_for_sshable_ap)
        timeout = time.time() + self.timeout_for_sshable_ap
        while time.time() < timeout:
            if self.access_point.is_sshable():
                self.log.info('Success: AP is online.')
                break
            else:
                self.log.debug('Could not ssh to AP...retrying in 1 second.')
                time.sleep(1)
        else:
            raise ConnectionError('Failed to ssh to AP.')

    def hard_reboot_ap(self):
        """Hard reboot of AP.
            - abruptly kills the power to AP
            - verifies AP is unreachable
            - restores power to the AP
            - verifies AP comes back online
        """
        # Get PDU device and port for AP
        ap_pdu_config = self.user_params['AccessPoint'][0]['PduDevice']
        ap_pdu, ap_pdu_port = pdu.get_pdu_port_for_device(
            ap_pdu_config, self.pdus)

        # Stop iperf server
        self.iperf_server.close_ssh()

        # Kill power to AP
        self.log.info('Killing power to AP...')
        ap_pdu.off(str(ap_pdu_port))
        self.wait_for_unreachable_ap()

        # Clear AP settings
        self.access_point._aps.clear()

        # Restore power to AP
        self.log.info('Restoring power to AP...')
        ap_pdu.on(str(ap_pdu_port))
        self.wait_for_pingable_ap()
        self.wait_for_sshable_ap()

        # Restart hostapd stuff
        # Allow 5 seconds for OS to get set up.
        time.sleep(5)
        self.access_point._initial_ap()
        self.log.info('AP reboot successful.')

    def prepare_dut_for_reconnection(self):
        """Perform any actions to ready DUT for reconnection.

        These actions will vary depending on the DUT. eg. android devices may
        need to be woken up, ambient devices should not require any interaction,
        etc.
        """
        self.dut.wifi_toggle_state(True)
        for ad in self.android_devices:
            ad.droid.wakeUpNow()

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
            'seconds.' % (ssid, self.timeout_for_dut_network_connection))
        timeout = time.time() + self.timeout_for_dut_network_connection
        while time.time() < timeout:
            try:
                is_connected = self.dut.is_connected(ssid=ssid)
            except Exception as err:
                self.log.info('SL4* call failed. Retrying in 1 second.')
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
            run: the run number in a looped stress tested.
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
            1. Setups up a network and associates the dut.
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

        self.setup_ap_associate_and_save(band, ipv4=ipv4, ipv6=ipv6)

        if ipv4:
            self.wait_until_dut_gets_ipv4_addr()
        if ipv6:
            self.wait_until_dut_gets_ipv6_addr()

        self.setup_iperf_server(band)
        self.iperf_server.start()

        if ipv4:
            self.verify_traffic()
        if ipv6:
            self.verify_traffic(ip_version=IPV6)

        # Looping reboots for stress testing
        for run in range(loops):
            run += 1
            self.log.info('Starting run %s of %s.' % (run, loops))

            # Ping from DUT to AP during AP reboot
            if interrupt:
                if ipv4:
                    self.start_dut_ping_process()
                if ipv6:
                    self.start_dut_ping_process(ip_version=IPV6)

            # DUT reboots
            if reboot_device == DUT:
                if type(self.iperf_client) == iperf_client.IPerfClientOverSsh:
                    self.iperf_client.close_ssh()
                if reboot_type == SOFT:
                    self.dut.device.reboot()
                elif reboot_type == HARD:
                    self.hard_reboot_dut()

            # AP reboots
            elif reboot_device == AP:
                if reboot_type == SOFT:
                    self.log.info('Cleanly stopping ap.')
                    self.access_point.stop_all_aps()
                elif reboot_type == HARD:
                    self.hard_reboot_ap()
                self.setup_ap(band, ipv4=ipv4, ipv6=ipv6)

            self.prepare_dut_for_reconnection()
            uptime = time.time()
            try:
                self.wait_for_dut_network_connection(self.ssid)
                time_to_reconnect = time.time() - uptime
                if ipv4:
                    self.wait_until_dut_gets_ipv4_addr()
                if ipv6:
                    self.wait_until_dut_gets_ipv6_addr()
                self.iperf_server.start()
                if ipv4:
                    self.verify_traffic()
                if ipv6:
                    self.verify_traffic(ip_version=IPV6)
            except ConnectionError as err:
                self.log_and_continue(run, error=err)
            passed_count += 1
            self.log_and_continue(run, time_to_reconnect=time_to_reconnect)

        if passed_count == loops:
            asserts.explicit_pass(
                'Test Summary: device successfully reconnected to network %s '
                '%s/%s times.' % (self.ssid, passed_count, loops))

        else:
            asserts.fail(
                'Test Summary: device failed stress test. Reconnected to '
                'network %s %s/%s times.' %
                (self.ssid, loops - passed_count, loops))

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
