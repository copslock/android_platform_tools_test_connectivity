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

from mobly import signals
import multiprocessing as mp
import time

from acts import utils
from acts import asserts
from acts.base_test import BaseTestClass
from acts.controllers import iperf_server
from acts.controllers import iperf_client
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib import hostapd_security
from acts.test_utils.abstract_devices.utils_lib import wlan_utils
from acts.test_utils.abstract_devices.wlan_device import create_wlan_device
from acts.test_utils.abstract_devices.utils_lib.wlan_utils import setup_ap_and_associate
from acts.test_utils.wifi.WifiBaseTest import WifiBaseTest

ANDROID_DEFAULT_WLAN_PORT = 'wlan0'
CONNECTIVITY_MODE_LOCAL = 'local_only'
CONNECTIVITY_MODE_UNRESTRICTED = 'unrestricted'
DEFAULT_IPERF_PORT = 5201
INTERFACE_ROLE_AP = 'Ap'
INTERFACE_ROLE_CLIENT = 'Client'
INTERFACE_ROLES = {INTERFACE_ROLE_AP, INTERFACE_ROLE_CLIENT}
OPERATING_BAND_2G = 'only_2_4_ghz'
OPERATING_BAND_5G = 'only_5_ghz'
OPERATING_BAND_ANY = 'any'
SECURITY_OPEN = 'none'
SECURITY_WEP = 'wep'
SECURITY_WPA = 'wpa'
SECURITY_WPA2 = 'wpa2'
SECURITY_WPA3 = 'wpa3'
TEST_TYPE_ASSOCIATE_ONLY = 'associate_only'
TEST_TYPE_ASSOCIATE_AND_PING = 'associate_and_ping'
TEST_TYPE_ASSOCIATE_AND_PASS_TRAFFIC = 'associate_and_pass_traffic'
TEST_TYPES = {
    TEST_TYPE_ASSOCIATE_ONLY, TEST_TYPE_ASSOCIATE_AND_PING,
    TEST_TYPE_ASSOCIATE_AND_PASS_TRAFFIC
}


def generate_test_name(settings):
    """Generates a string test name based on the channel and band.

    Args:
        settings A dict with the soft ap config parameteres.

    Returns:
        A string test case name.
    """
    return 'test_soft_ap_band_%s_security_%s_mode_%s_loops_%s' % (
        settings['operating_band'], settings['security_type'],
        settings['connectivity_mode'], settings['reconnect_loops'])


class SoftApClient(object):
    def __init__(self, device):
        self.w_device = create_wlan_device(device)
        self.ip_client = iperf_client.IPerfClientOverAdb(device.serial)


class WlanInterface(object):
    def __init__(self):
        self.name = None
        self.mac_addr = None
        self.ipv4 = None


class SoftApTest(BaseTestClass):
    """Tests for Fuchsia SoftAP

    Testbed requirement:
    * One Fuchsia Device
    * One Client (Android) Device
    """
    def setup_class(self):
        self.dut = create_wlan_device(self.fuchsia_devices[0])
        self.dut.device.netstack_lib.init()

        # TODO(fxb/51313): Add in device agnosticity for clients
        self.clients = []
        for device in self.android_devices:
            self.clients.append(SoftApClient(device))
        self.primary_client = self.clients[0]

        self.iperf_server_config = {
            'user': self.dut.device.ssh_username,
            'host': self.dut.device.ip,
            'ssh_config': self.dut.device.ssh_config
        }
        self.iperf_server = iperf_server.IPerfServerOverSsh(
            self.iperf_server_config, DEFAULT_IPERF_PORT, use_killall=True)
        self.iperf_server.start()

        try:
            self.access_point = self.access_points[0]
        except AttributeError:
            self.access_point = None

    def teardown_class(self):
        # Because this is using killall, it will stop all iperf processes,
        # making it a great teardown cleanup
        self.iperf_server.stop()

    def setup_test(self):
        for ad in self.android_devices:
            ad.droid.wakeLockAcquireBright()
            ad.droid.wakeUpNow()
        for client in self.clients:
            client.w_device.disconnect()
            client.w_device.reset_wifi()
            client.w_device.wifi_toggle_state(True)
        self.dut.device.wlan_ap_policy_lib.wlanStopAllAccessPoint()
        if self.access_point:
            self.access_point.stop_all_aps()
        self.dut.disconnect()

    def teardown_test(self):
        for client in self.clients:
            client.w_device.disconnect()
        for ad in self.android_devices:
            ad.droid.wakeLockRelease()
            ad.droid.goToSleepNow()
        self.dut.device.wlan_ap_policy_lib.wlanStopAllAccessPoint()
        if self.access_point:
            self.access_point.stop_all_aps()
        self.dut.disconnect()

    def on_fail(self, test_name, begin_time):
        self.dut.take_bug_report(test_name, begin_time)
        self.dut.get_log(test_name, begin_time)

    def start_soft_ap(self, settings):
        """Starts a softAP on Fuchsia device.

        Args:
            settings: a dict containing softAP configuration params
                ssid: string, SSID of softAP network
                security_type: string, security type of softAP network
                    - 'none', 'wep', 'wpa', 'wpa2', 'wpa3'
                password: string, password if applicable
                connectivity_mode: string, connecitivity_mode for softAP
                    - 'local_only', 'unrestricted'
                operating_band: string, band for softAP network
                    - 'any', 'only_5_ghz', 'only_2_4_ghz'
        """
        ssid = settings['ssid']
        security_type = settings['security_type']
        password = settings.get('password', '')
        connectivity_mode = settings['connectivity_mode']
        operating_band = settings['operating_band']

        self.log.info('Attempting to start SoftAP on DUT with settings: %s' %
                      settings)

        response = self.dut.device.wlan_ap_policy_lib.wlanStartAccessPoint(
            ssid, security_type, password, connectivity_mode, operating_band)
        if response.get('error'):
            raise EnvironmentError('Failed to setup SoftAP. Err: %s' %
                                   response['error'])

        self.log.info('SoftAp network (%s) is up.' % ssid)

    def associate_with_soft_ap(self, w_device, settings):
        """Associates client device with softAP on Fuchsia device.

        Args:
            w_device: wlan_device to associate with the softAP
            settings: a dict containing softAP config params (see start_soft_ap)
                for details

        Raises:
            TestFailure, if association fails
        """
        self.log.info(
            'Attempting to associate client %s with SoftAP on FuchsiaDevice '
            '(%s).' % (w_device.device.serial, self.dut.device.ip))

        check_connectivity = settings[
            'connectivity_mode'] == CONNECTIVITY_MODE_UNRESTRICTED
        associated = wlan_utils.associate(
            w_device,
            settings['ssid'],
            password=settings.get('password'),
            check_connectivity=check_connectivity)

        if not associated:
            asserts.fail('Failed to connect to SoftAP.')

        self.log.info('Client successfully associated with SoftAP.')

    def disconnect_from_soft_ap(self, w_device):
        """Disconnects client device from SoftAP.

        Args:
            w_device: wlan_device to disconnect from SoftAP
        """
        self.log.info('Disconnecting device %s from SoftAP.' %
                      w_device.device.serial)
        w_device.disconnect()

    def get_dut_interface_by_role(self, role):
        """Retrieves interface information from the FuchsiaDevice DUT based
        on the role.

        Args:
            role: string, the role of the interface to seek (e.g. Client or Ap)

        Raises:
            ConnectionError, if SL4F calls fail
            AttributeError, if device does not have an interface matching role

        Returns:
            WlanInterface object representing the interface matching role
        """
        if not role in INTERFACE_ROLES:
            raise ValueError('Unsupported interface role %s' % role)

        self.log.info('Getting %s interface info from DUT.' % role)
        interface = WlanInterface()

        # Determine WLAN interface with role
        wlan_ifaces = self.dut.device.wlan_lib.wlanGetIfaceIdList()
        if wlan_ifaces.get('error'):
            raise ConnectionError('Failed to get wlan interface IDs: %s' %
                                  wlan_ifaces['error'])

        for wlan_iface in wlan_ifaces['result']:
            iface_info = self.dut.device.wlan_lib.wlanQueryInterface(
                wlan_iface)
            if iface_info.get('error'):
                raise ConnectionError('Failed to query wlan iface: %s' %
                                      iface_info['error'])

            if iface_info['result']['role'] == role:
                interface.mac_addr = iface_info['result']['mac_addr']
                break
        else:
            raise AttributeError('Failed to find a %s interface.' % role)

        # Retrieve interface info from netstack
        netstack_ifaces = self.dut.device.netstack_lib.netstackListInterfaces()
        if netstack_ifaces.get('error'):
            raise ConnectionError('Failed to get netstack ifaces: %s' %
                                  netstack_ifaces['error'])

        # TODO(fxb/51315): Once subnet information is available in
        # netstackListInterfaces store it to verify the clients ip address.
        for netstack_iface in netstack_ifaces['result']:
            if netstack_iface['mac'] == interface.mac_addr:
                interface.name = netstack_iface['name']
                if len(netstack_iface['ipv4_addresses']) > 0:
                    interface.ipv4 = '.'.join(
                        str(byte)
                        for byte in netstack_iface['ipv4_addresses'][0])
                else:
                    interface.ipv4 = self.wait_for_ipv4_address(
                        self.dut, interface.name)
        self.log.info('DUT %s interface: %s. Has ipv4 address %s' %
                      (role, interface.name, interface.ipv4))
        return interface

    def wait_for_ipv4_address(self, w_device, interface_name, timeout=10):
        # TODO(fxb/51315): Once subnet information is available in netstack, add a
        # subnet verification here.
        """ Waits for interface on a wlan_device to get an ipv4 address.

        Args:
            w_device: wlan_device to check interface
            interface_name: name of the interface to check
            timeout: seconds to wait before raising an error

        Raises:
            ValueError, if interface does not have an ipv4 address after timeout
        """
        self.log.info(
            'Checking if device %s interface %s has an ipv4 address. '
            'Will retrying for %s seconds.' %
            (w_device.device.serial, interface_name, timeout))

        end_time = time.time() + timeout
        while time.time() < end_time:
            ips = w_device.get_interface_ip_addresses(interface_name)
            if len(ips['ipv4_private']) > 0:
                self.log.info('Device %s interface %s has ipv4 address %s' %
                              (w_device.device.serial, interface_name,
                               ips['ipv4_private'][0]))
                return ips['ipv4_private'][0]
            else:
                time.sleep(1)
        raise ValueError(
            'After %s seconds, device %s still doesn not have an ipv4 address '
            'on interface %s.' %
            (timeout, w_device.device.serial, interface_name))

    def verify_ping(self, w_device, dest_ip):
        """ Verify wlan_device can ping a destination ip.

        Args:
            w_device: wlan_device to initiate ping
            dest_ip: ip to ping from wlan_device

        Raises:
            TestFailure, if ping fails
        """
        self.log.info('Attempting to ping from device %s to dest ip %s' %
                      (w_device.device.serial, dest_ip))
        if not w_device.ping(dest_ip):
            asserts.fail('Device %s could not ping dest ip %s' %
                         (w_device.device.serial, dest_ip))
        self.log.info('Ping successful.')

    def run_iperf_traffic(self, ip_client, server_address, server_port=5201):
        """Runs traffic between client and ap an verifies throughput.

        Args:
            ip_client: iperf client to use
            server_address: ipv4 address of the iperf server to use
            server_port: port of the iperf server

        Raises:
            TestFailure, if no traffic passes in either direction
        """
        ip_client_identifier = self.get_iperf_client_identifier(ip_client)
        self.log.info(
            'Running traffic from iperf client %s to iperf server %s.' %
            (ip_client_identifier, server_address))
        client_to_ap_path = ip_client.start(
            server_address, '-i 1 -t 10 -J -p %s' % server_port,
            'client_to_soft_ap')

        self.log.info(
            'Running traffic from iperf server %s to iperf client %s.' %
            (server_address, ip_client_identifier))
        ap_to_client_path = ip_client.start(
            server_address, '-i 1 -t 10 -R -J -p %s' % server_port,
            'soft_ap_to_client')
        self.log.info('Getting iperf results')

        client_to_ap_result = iperf_server.IPerfResult(client_to_ap_path)
        ap_to_client_result = iperf_server.IPerfResult(ap_to_client_path)

        if (not client_to_ap_result.avg_receive_rate):
            asserts.fail(
                'Failed to pass traffic from iperf client %s to iperf server %s.'
                % (ip_client_identifier, server_address))

        self.log.info(
            'Passed traffic from iperf client %s to iperf server %s with avg '
            'rate of %s MB/s.' % (ip_client_identifier, server_address,
                                  client_to_ap_result.avg_receive_rate))

        if (not ap_to_client_result.avg_receive_rate):
            asserts.fail(
                'Failed to pass traffic from iperf server %s to iperf client %s.'
                % (server_address, ip_client_identifier))

        self.log.info(
            'Passed traffic from iperf server %s to iperf client %s with avg '
            'rate of %s MB/s.' % (server_address, ip_client_identifier,
                                  ap_to_client_result.avg_receive_rate))

    def run_iperf_traffic_parallel_process(self,
                                           ip_client,
                                           server_address,
                                           error_queue,
                                           server_port=5201):
        """ Executes run_iperf_traffic using a queue to capture errors. Used
        when running iperf in a parallel process.

        Args:
            ip_client: iperf client to use
            server_address: ipv4 address of the iperf server to use
            error_queue: multiprocessing queue to capture errors
            server_port: port of the iperf server
        """
        try:
            self.run_iperf_traffic(ip_client,
                                   server_address,
                                   server_port=server_port)
        except Exception as err:
            error_queue.put('In iperf process from %s to %s: %s' %
                            (self.get_iperf_client_identifier(ip_client),
                             server_address, err))

    def get_iperf_client_identifier(self, ip_client):
        """ Retrieves an indentifer string from iperf client, for logging.

        Args:
            ip_client: iperf client to grab identifier from
        """
        if type(ip_client) == iperf_client.IPerfClientOverAdb:
            return ip_client._android_device_or_serial
        return ip_client._ssh_settings.hostname

    def run_config_stress_test(self, settings):
        """Runs test based on config parameters.

        Args:
            settings: test configuration settings, see
                test_soft_ap_stress_from_config for details
        """
        client = settings['client']
        test_type = settings['test_type']
        if not test_type in TEST_TYPES:
            raise ValueError('Unrecognized test type %s' % test_type)
        reconnect_loops = settings['reconnect_loops']
        self.log.info('Running test type %s in loop %s times' %
                      (test_type, reconnect_loops))

        self.start_soft_ap(settings)

        passed_count = 0
        for run in range(reconnect_loops):
            try:
                # Associate with SoftAp
                self.log.info('Starting SoftApTest run %s' % str(run + 1))
                self.associate_with_soft_ap(client.w_device, settings)

                if test_type != TEST_TYPE_ASSOCIATE_ONLY:
                    # Verify client and SoftAP can ping
                    dut_ap_interface = self.get_dut_interface_by_role(
                        INTERFACE_ROLE_AP)
                    client_ipv4 = self.wait_for_ipv4_address(
                        client.w_device, ANDROID_DEFAULT_WLAN_PORT)
                    self.verify_ping(client.w_device, dut_ap_interface.ipv4)
                    self.verify_ping(self.dut, client_ipv4)

                    if test_type != TEST_TYPE_ASSOCIATE_AND_PING:
                        # Run traffic between client and SoftAp
                        self.run_iperf_traffic(client.ip_client,
                                               dut_ap_interface.ipv4)
                # Disconnect
                self.disconnect_from_soft_ap(client.w_device)

            except signals.TestFailure as err:
                self.log.error('SoftApTest run %s failed. Err: %s' %
                               (str(run + 1), err.details))
            else:
                self.log.info('SoftApTest run %s successful.' % run)
                passed_count += 1

        if passed_count < reconnect_loops:
            asserts.fail('SoftAp reconnect test passed on %s/%s runs.' %
                         (passed_count, reconnect_loops))

        asserts.explicit_pass('SoftAp reconnect test passed on %s/%s runs.' %
                              (passed_count, reconnect_loops))

    # Test helper functions
    def verify_soft_ap_associate_only(self, client, settings):
        self.start_soft_ap(settings)
        self.associate_with_soft_ap(client.w_device, settings)

    def verify_soft_ap_associate_and_ping(self, client, settings):
        self.start_soft_ap(settings)
        self.associate_with_soft_ap(client.w_device, settings)
        dut_ap_interface = self.get_dut_interface_by_role(INTERFACE_ROLE_AP)
        client_ipv4 = self.wait_for_ipv4_address(self.primary_client.w_device,
                                                 ANDROID_DEFAULT_WLAN_PORT)
        self.verify_ping(client.w_device, dut_ap_interface.ipv4)
        self.verify_ping(self.dut, client_ipv4)

    def verify_soft_ap_associate_and_pass_traffic(self, client, settings):
        self.start_soft_ap(settings)
        self.associate_with_soft_ap(client.w_device, settings)
        dut_ap_interface = self.get_dut_interface_by_role(INTERFACE_ROLE_AP)
        client_ipv4 = self.wait_for_ipv4_address(self.primary_client.w_device,
                                                 ANDROID_DEFAULT_WLAN_PORT)
        self.verify_ping(client.w_device, dut_ap_interface.ipv4)
        self.verify_ping(self.dut, client_ipv4)
        self.run_iperf_traffic(client.ip_client, dut_ap_interface.ipv4)


# Test Cases

    def test_soft_ap_2g_open_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_LOCAL,
                'operating_band': OPERATING_BAND_2G
            })

    def test_soft_ap_5g_open_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_LOCAL,
                'operating_band': OPERATING_BAND_5G
            })

    def test_soft_ap_any_open_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_LOCAL,
                'operating_band': OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wep_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wep_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wep_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wpa_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa2_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa2_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wpa2_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa3_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa3_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_any_wpa3_local(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_LOCAL,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_open_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band': OPERATING_BAND_2G
            })

    def test_soft_ap_5g_open_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band': OPERATING_BAND_5G
            })

    def test_soft_ap_any_open_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid': utils.rand_ascii_str(
                    hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type': SECURITY_OPEN,
                'connectivity_mode': CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band': OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wep_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wep_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wep_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WEP,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wpa_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa2_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa2_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_5G
            })

    def test_soft_ap_any_wpa2_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA2,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_2g_wpa3_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_2G
            })

    def test_soft_ap_5g_wpa3_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_soft_ap_any_wpa3_unrestricted(self):
        self.verify_soft_ap_associate_and_pass_traffic(
            self.primary_client, {
                'ssid':
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_5G),
                'security_type':
                SECURITY_WPA3,
                'password':
                utils.rand_ascii_str(hostapd_constants.MIN_WPA_PSK_LENGTH),
                'connectivity_mode':
                CONNECTIVITY_MODE_UNRESTRICTED,
                'operating_band':
                OPERATING_BAND_ANY
            })

    def test_multi_client_open(self):
        """Tests multi-client association with a single soft AP network.

        This tests associates a variable length list of clients, verfying it can
        can ping the SoftAP and pass traffic, and then verfies all previously
        associated clients can still ping and pass traffic.

        The same occurs in reverse for disassocations.
        """
        asserts.skip_if(
            len(self.clients) < 2, 'Test requires at least 2 SoftAPClients')

        settings = {
            'ssid': utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
            'security_type': SECURITY_OPEN,
            'connectivity_mode': CONNECTIVITY_MODE_LOCAL,
            'operating_band': OPERATING_BAND_ANY
        }
        self.start_soft_ap(settings)

        dut_ap_interface = self.get_dut_interface_by_role(INTERFACE_ROLE_AP)
        associated = []

        for client in self.clients:
            # Associate new client
            self.associate_with_soft_ap(client.w_device, settings)
            client_ipv4 = self.wait_for_ipv4_address(
                client.w_device, ANDROID_DEFAULT_WLAN_PORT)
            self.run_iperf_traffic(client.ip_client, dut_ap_interface.ipv4)

            # Verify previously associated clients still behave as expected
            for client_map in associated:
                associated_client = client_map['client']
                associated_client_ipv4 = client_map['ipv4']
                self.log.info(
                    'Verifying previously associated client %s still functions correctly.'
                    % associated_client.w_device.device.serial)
                try:
                    self.verify_ping(self.dut, associated_client_ipv4)
                    self.verify_ping(associated_client.w_device,
                                     dut_ap_interface.ipv4)
                    self.run_iperf_traffic(associated_client.ip_client,
                                           dut_ap_interface.ipv4)
                except signals.TestFailure as err:
                    asserts.fail(
                        'Previously associated client %s failed checks after '
                        'client %s associated. Error: %s' %
                        (associated_client.w_device.device.serial,
                         client.w_device.device.serial, err))

            associated.append({'client': client, 'ipv4': client_ipv4})

        self.log.info(
            'All devices successfully associated. Beginning disassociations.')

        while len(associated) > 0:
            # Disassociate client
            client = associated.pop()['client']
            self.disconnect_from_soft_ap(client.w_device)

            # Verify still connected clients still behave as expected
            for client_map in associated:
                associated_client = client_map['client']
                associated_client_ipv4 = client_map['ipv4']
                try:
                    self.log.info(
                        'Verifying still associated client %s still functions '
                        'correctly.' %
                        associated_client.w_device.device.serial)
                    self.verify_ping(self.dut, associated_client_ipv4)
                    self.verify_ping(associated_client.w_device,
                                     dut_ap_interface.ipv4)
                    self.run_iperf_traffic(associated_client.ip_client,
                                           dut_ap_interface.ipv4)
                except signals.TestFailure as err:
                    asserts.fail(
                        'Previously associated client %s failed checks after'
                        ' client %s disassociated. Error: %s' %
                        (associated_client.w_device.device.serial,
                         client.w_device.device.serial, err))

        self.log.info('All disassociations occurred smoothly.')

    def test_soft_ap_and_client(self):
        """ Tests FuchsiaDevice DUT can act as a client and a SoftAP
        simultaneously.

        Raises:
            ConnectionError: if DUT fails to connect as client
            RuntimeError: if parallel processes fail to join
            TestFailure: if DUT fails to pass traffic as either a client or an
                AP
        """
        asserts.skip_if(not self.access_point, 'No access point provided.')

        self.log.info('Setting up AP using hostapd.')

        # Configure AP
        ap_params = self.user_params.get('soft_ap_test_params',
                                         {}).get('ap_params', {})
        channel = ap_params.get('channel', 11)
        ssid = ap_params.get('ssid', 'apnet')
        security_mode = ap_params.get('security_mode', None)
        password = ap_params.get('password', None)
        if security_mode:
            security = hostapd_security.Security(security_mode, password)
        else:
            security = None

        # Setup AP and associate DUT
        if not setup_ap_and_associate(access_point=self.access_point,
                                      client=self.dut,
                                      profile_name='whirlwind',
                                      channel=channel,
                                      security=security,
                                      password=password,
                                      ssid=ssid):
            raise ConnectionError(
                'FuchsiaDevice DUT failed to connect as client to AP.')
        self.log.info('DUT successfully associated to AP network.')

        # Verify FuchsiaDevice's client interface has an ip address from AP
        dut_client_interface = self.get_dut_interface_by_role(
            INTERFACE_ROLE_CLIENT)

        # Verify FuchsiaDevice can ping AP
        lowest_5ghz_channel = 36
        if channel < lowest_5ghz_channel:
            ap_interface = self.access_point.wlan_2g
        else:
            ap_interface = self.access_point.wlan_5g
        ap_ipv4 = utils.get_interface_ip_addresses(
            self.access_point.ssh, ap_interface)['ipv4_private'][0]

        self.verify_ping(self.dut, ap_ipv4)

        # Setup SoftAP
        soft_ap_settings = {
            'ssid': utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G),
            'security_type': SECURITY_OPEN,
            'connectivity_mode': CONNECTIVITY_MODE_LOCAL,
            'operating_band': OPERATING_BAND_2G
        }
        self.start_soft_ap(soft_ap_settings)

        # Get FuchsiaDevice's AP interface info
        dut_ap_interface = self.get_dut_interface_by_role(INTERFACE_ROLE_AP)

        # Associate primary client with SoftAP
        self.associate_with_soft_ap(self.primary_client.w_device,
                                    soft_ap_settings)

        # Verify primary client has an ip address from SoftAP
        client_ipv4 = self.wait_for_ipv4_address(self.primary_client.w_device,
                                                 ANDROID_DEFAULT_WLAN_PORT)

        # Verify primary client can ping SoftAP, and reverse
        self.verify_ping(self.primary_client.w_device, dut_ap_interface.ipv4)
        self.verify_ping(self.dut, client_ipv4)

        # Set up secondary iperf server of FuchsiaDevice
        self.log.info('Setting up second iperf server on FuchsiaDevice DUT.')
        secondary_iperf_server = iperf_server.IPerfServerOverSsh(
            self.iperf_server_config, DEFAULT_IPERF_PORT + 1, use_killall=True)
        secondary_iperf_server.start()

        # Set up iperf client on AP
        self.log.info('Setting up iperf client on AP.')
        ap_iperf_client = iperf_client.IPerfClientOverSsh(
            self.user_params['AccessPoint'][0]['ssh_config'])

        # Setup iperf processes:
        #     Primary client <-> SoftAP interface on FuchsiaDevice
        #     AP <-> Client interface on FuchsiaDevice
        process_errors = mp.Queue()
        iperf_soft_ap = mp.Process(
            target=self.run_iperf_traffic_parallel_process,
            args=[
                self.primary_client.ip_client, dut_ap_interface.ipv4,
                process_errors
            ])

        iperf_fuchsia_client = mp.Process(
            target=self.run_iperf_traffic_parallel_process,
            args=[ap_iperf_client, dut_client_interface.ipv4, process_errors],
            kwargs={'server_port': 5202})

        # Run iperf processes simultaneously
        self.log.info('Running simultaneous iperf traffic: between AP and DUT '
                      'client interface, and DUT AP interface and client.')
        iperf_soft_ap.start()
        iperf_fuchsia_client.start()

        # Block until processes can join or timeout
        for proc in [iperf_soft_ap, iperf_fuchsia_client]:
            proc.join(timeout=30)
            if proc.is_alive():
                raise RuntimeError('Failed to join process %s' % proc)

        # Stop iperf server (also stopped in teardown class as failsafe)
        secondary_iperf_server.stop()

        # Check errors from parallel processes
        if process_errors.empty():
            asserts.explicit_pass(
                'FuchsiaDevice was successfully able to pass traffic as a '
                'client and an AP simultaneously.')
        else:
            while not process_errors.empty():
                self.log.error('Error in iperf process: %s' %
                               process_errors.get())
            asserts.fail(
                'FuchsiaDevice failed to pass traffic as a client and an AP '
                'simultaneously.')

    def test_soft_ap_stress_from_config(self):
        """ Runs tests from ACTS config file.

        Example Config
        "soft_ap_test_params" : {
            "soft_ap_tests": [
                {
                    "ssid": "test_network",
                    "security_type": "wpa2",
                    "password": "password",
                    "connectivity_mode": "local_only",
                    "operating_band": "only_2_4_ghz",
                    "reconnect_loops": 10
                }
            ]
        }
        """
        tests = self.user_params.get('soft_ap_test_params',
                                     {}).get('soft_ap_tests')
        asserts.skip_if(not tests, 'No soft ap tests in the ACTS config.')

        test_settings_list = []
        for config_settings in self.user_params['soft_ap_test_params'][
                'soft_ap_tests']:
            ssid = config_settings.get(
                'ssid',
                utils.rand_ascii_str(hostapd_constants.AP_SSID_LENGTH_2G))
            security_type = config_settings.get('security_type', SECURITY_OPEN)
            password = config_settings.get('password', '')
            connectivity_mode = config_settings.get('connectivity_mode',
                                                    CONNECTIVITY_MODE_LOCAL)
            operating_band = config_settings.get('operating_band',
                                                 OPERATING_BAND_ANY)
            test_type = config_settings.get('test_type',
                                            'associate_and_pass_traffic')
            reconnect_loops = config_settings.get('reconnect_loops', 1)
            test_settings = {
                'client': self.primary_client,
                'ssid': ssid,
                'security_type': security_type,
                'password': password,
                'connectivity_mode': connectivity_mode,
                'operating_band': operating_band,
                'test_type': test_type,
                'reconnect_loops': reconnect_loops
            }
            test_settings_list.append(test_settings)

        self.run_generated_testcases(self.run_config_stress_test,
                                     test_settings_list,
                                     name_func=generate_test_name)