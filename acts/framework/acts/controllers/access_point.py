#!/usr/bin/env python3.4
#
#   Copyright 2016 - Google, Inc.
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

import ipaddress
import logging

from acts.controllers.ap_lib import dhcp_config
from acts.controllers.ap_lib import dhcp_server
from acts.controllers.ap_lib import hostapd
from acts.controllers.ap_lib import hostapd_config
from acts.controllers.utils_lib.commands import ip
from acts.controllers.utils_lib.commands import route
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings

ACTS_CONTROLLER_CONFIG_NAME = 'AccessPoint'
ACTS_CONTROLLER_REFERENCE_NAME = 'access_points'

HOSTNAME_KEY = 'hostname'
USERNAME_KEY = 'user'
PORT_KEY = 'port'


def create(configs):
    """Creates ap controllers from a json config.

    Creates an ap controller from either a list, or a single
    element. The element can either be just the hostname or a dictionary
    containing the hostname and username of the ap to connect to over ssh.

    Args:
        The json configs that represent this controller.

    Returns:
        A new AccessPoint.
    """
    results = []
    for c in configs:
        return AccessPoint(configuration[HOSTNAME_KEY],
                           configuration.get(USERNAME_KEY),
                           configuration.get(PORT_KEY))

    return results


def destroy(aps):
    """Destroys a list of access points.

    Args:
        aps: The list of access points to destroy.
    """
    for ap in aps:
        ap.close()


def get_info(aps):
    """Get information on a list of access points.

    Args:
        aps: A list of AccessPoints.

    Returns:
        A list of all aps hostname.
    """
    return [ap.hostname for ap in aps]


class Error(Exception):
    """Error raised when there is a problem with the access point."""


class AccessPoint(object):
    """An access point controller.

    Attributes:
        hostname: The hostname of the ap.
        ssh: The ssh connection to this ap.
        ssh_settings: The ssh settings being used by the ssh conneciton.
        dhcp_settings: The dhcp server settings being used.
    """

    AP_2GHZ_INTERFACE = 'wlan0'
    AP_5GHZ_INTERFACE = 'wlan1'

    AP_2GHZ_SUBNET = dhcp_config.Subnet(ipaddress.ip_network('192.168.1.0/24'))
    AP_5GHZ_SUBNET = dhcp_config.Subnet(ipaddress.ip_network('192.168.2.0/24'))

    def __init__(self, hostname, username=None, port=None):
        """
        Args:
            hostname: The hostname of the access point.
            username: The username to connect with.
            port: The port to connect with.
        """
        if port is None:
            # TODO: Change settings to do this.
            port = 22

        if username is None:
            username = 'root'

        self.hostname = hostname
        self.ssh_settings = settings.SshSettings(hostname, username, port=port)
        self.ssh = connection.SshConnection(self.ssh_settings)

        # Spawn interface for dhcp server.
        self.dhcp_settings = dhcp_config.DhcpConfig(
            [self.AP_2GHZ_SUBNET, self.AP_5GHZ_SUBNET])
        self._dhcp = dhcp_server.DhcpServer(self.ssh)

        # Spawn interfaces for hostapd on both of the interfaces.
        self._hostapd_2ghz = hostapd.Hostapd(self.ssh, self.AP_2GHZ_INTERFACE)
        self._hostapd_5ghz = hostapd.Hostapd(self.ssh, self.AP_5GHZ_SUBNET)

        self._ip_cmd = ip.LinuxIpCommand(self.ssh)
        self._route_cmd = route.LinuxRouteCommand(self.ssh)

    def __del__(self):
        self.close()

    def start_ap(self, hostapd_config):
        """Starts as an ap using a set of configurations.

        This will start an ap on this host. To start an ap the controller
        selects a network interface to use based on the configs given. It then
        will start up hostapd on that interface. Next a subnet is created for
        the network interface and dhcp server is refreshed to give out ips
        for that subnet for any device that connects through that interface.

        Args:
            hostapd_config: hostapd_config.HostapdConfig, The configurations
                            to use when starting up the ap.

        Returns:
            An identifier for the ap being run. This identifier can be used
            later by this controller to control the ap.

        Raises:
            Error: When the ap can't be brought up.
        """
        if hostapd_config.frequency < 5000:
            if self._hostapd_2ghz.is_alive():
                raise Error('2GHz ap already up.')
            identifier = self.AP_2GHZ_INTERFACE
            subnet = self.AP_2GHZ_SUBNET
            apd = self._hostapd_2ghz
        else:
            if self._hostapd_5ghz.is_alive():
                raise Error('5GHz ap already up.')
            identifier = self.AP_5GHZ_INTERFACE
            subnet = self.AP_5GHZ_SUBNET
            apd = self._hostapd_5ghz

        apd.start(hostapd_config)

        # Clear all routes to prevent old routes from interfering.
        self._route_cmd.clear_routes(net_interface=identifier)

        # dhcp server requires interfaces to have ips and routes before coming
        # up.
        router_address = subnet.router
        network = subnet.network
        router_interface = ipaddress.ip_interface('%s/%s' % (router_address,
                                                             network.netmask))
        self._ip_cmd.set_ipv4_address(identifier, router_interface)

        # DHCP server needs to restart to take into account any Interface
        # change.
        self._dhcp.start(self.dhcp_settings)

        return identifier

    def stop_ap(self, identifier):
        """Stops a running ap on this controller.

        Args:
            identifier: The identify of the ap that should be taken down.
        """
        if identifier == self.AP_5GHZ_INTERFACE:
            apd = self._hostapd_5ghz
        elif identifier == self.AP_2GHZ_INTERFACE:
            apd = self._hostapd_2ghz
        else:
            raise ValueError('Invalid identifer %s given' % identifier)

        apd.stop()

        self._ip_cmd.clear_ipv4_addresses(identifier)

        # DHCP server needs to refresh in order to tear down the subnet no
        # longer being used. In the event that all interfaces are torn down
        # then an exception gets thrown. We need to catch this exception and
        # check that all interfaces should actually be down.
        try:
            self._dhcp.start(self.dhcp_settings)
        except dhcp_server.NoInterfaceError:
            if self._hostapd_2ghz.is_alive() or self._hostapd_5ghz.is_alive():
                raise

    def stop_all_aps(self):
        """Stops all running aps on this device."""
        self.stop_ap(self.AP_2GHZ_INTERFACE)
        self.stop_ap(self.AP_5GHZ_INTERFACE)

    def close(self):
        """Called to take down the entire access point.

        When called will stop all aps running on this host, shutdown the dhcp
        server, and stop the ssh conneciton.
        """
        self.stop_all_aps()
        self._dhcp.stop()

        self.ssh.close()
