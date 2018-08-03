#!/usr/bin/env python3.4
#
#   Copyright 2017 - Google
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
"""
    Base Class for Defining Common WiFi Test Functionality
"""

import copy
import itertools
import time

import acts.controllers.access_point as ap

from acts import asserts
from acts import utils
from acts.base_test import BaseTestClass
from acts.signals import TestSignal
from acts.controllers import android_device
from acts.controllers.ap_lib import hostapd_ap_preset
from acts.controllers.ap_lib import hostapd_bss_settings
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib import hostapd_security

AP_1 = 0
AP_2 = 1
MAX_AP_COUNT = 2

class WifiBaseTest(BaseTestClass):
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        if hasattr(self, 'attenuators') and self.attenuators:
            for attenuator in self.attenuators:
                attenuator.set_atten(0)

    def get_wpa2_network(
            self,
            mirror_ap,
            reference_networks,
            hidden=False,
            same_ssid=False,
            ssid_length_2g=hostapd_constants.AP_SSID_LENGTH_2G,
            ssid_length_5g=hostapd_constants.AP_SSID_LENGTH_5G,
            passphrase_length_2g=hostapd_constants.AP_PASSPHRASE_LENGTH_2G,
            passphrase_length_5g=hostapd_constants.AP_PASSPHRASE_LENGTH_5G):
        """Generates SSID and passphrase for a WPA2 network using random
           generator.

           Args:
               mirror_ap: Boolean, determines if both APs use the same hostapd
                          config or different configs.
               reference_networks: List of PSK networks.
               same_ssid: Boolean, determines if both bands on AP use the same
                          SSID.
               ssid_length_2gecond AP Int, number of characters to use for 2G SSID.
               ssid_length_5g: Int, number of characters to use for 5G SSID.
               passphrase_length_2g: Int, length of password for 2G network.
               passphrase_length_5g: Int, length of password for 5G network.

           Returns: A dict of 2G and 5G network lists for hostapd configuration.

        """
        network_dict_2g = {}
        network_dict_5g = {}
        ref_5g_security = hostapd_constants.WPA2_STRING
        ref_2g_security = hostapd_constants.WPA2_STRING

        if same_ssid:
            ref_2g_ssid = 'xg_%s' % utils.rand_ascii_str(ssid_length_2g)
            ref_5g_ssid = ref_2g_ssid

            ref_2g_passphrase = utils.rand_ascii_str(passphrase_length_2g)
            ref_5g_passphrase = ref_2g_passphrase

        else:
            ref_2g_ssid = '2g_%s' % utils.rand_ascii_str(ssid_length_2g)
            ref_2g_passphrase = utils.rand_ascii_str(passphrase_length_2g)

            ref_5g_ssid = '5g_%s' % utils.rand_ascii_str(ssid_length_5g)
            ref_5g_passphrase = utils.rand_ascii_str(passphrase_length_5g)

        network_dict_2g = {
            "SSID": ref_2g_ssid,
            "security": ref_2g_security,
            "password": ref_2g_passphrase,
            "hiddenSSID": hidden
        }

        network_dict_5g = {
            "SSID": ref_5g_ssid,
            "security": ref_5g_security,
            "password": ref_5g_passphrase,
            "hiddenSSID": hidden
        }

        ap = 0
        for ap in range(MAX_AP_COUNT):
            reference_networks.append({
                "2g": copy.copy(network_dict_2g),
                "5g": copy.copy(network_dict_5g)
            })
            if not mirror_ap:
                break
        return {"2g": network_dict_2g, "5g": network_dict_5g}

    def get_open_network(self,
                         mirror_ap,
                         open_network,
                         hidden=False,
                         same_ssid=False,
                         ssid_length_2g=hostapd_constants.AP_SSID_LENGTH_2G,
                         ssid_length_5g=hostapd_constants.AP_SSID_LENGTH_5G):
        """Generates SSIDs for a open network using a random generator.

        Args:
            mirror_ap: Boolean, determines if both APs use the same hostapd
                       config or different configs.
            open_network: List of open networks.
            same_ssid: Boolean, determines if both bands on AP use the same
                       SSID.
            ssid_length_2g: Int, number of characters to use for 2G SSID.
            ssid_length_5g: Int, number of characters to use for 5G SSID.

        Returns: A dict of 2G and 5G network lists for hostapd configuration.

        """
        network_dict_2g = {}
        network_dict_5g = {}

        if same_ssid:
            open_2g_ssid = 'xg_%s' % utils.rand_ascii_str(ssid_length_2g)
            open_5g_ssid = open_2g_ssid

        else:
            open_2g_ssid = '2g_%s' % utils.rand_ascii_str(ssid_length_2g)
            open_5g_ssid = '5g_%s' % utils.rand_ascii_str(ssid_length_5g)

        network_dict_2g = {
            "SSID": open_2g_ssid,
            "security": 'none',
            "hiddenSSID": hidden
        }

        network_dict_5g = {
            "SSID": open_5g_ssid,
            "security": 'none',
            "hiddenSSID": hidden
        }

        ap = 0
        for ap in range(MAX_AP_COUNT):
            open_network.append({
                "2g": copy.copy(network_dict_2g),
                "5g": copy.copy(network_dict_5g)
            })
            if not mirror_ap:
                break
        return {"2g": network_dict_2g, "5g": network_dict_5g}

    def update_bssid(self, ap_instance, ap, network, band):
        """Get bssid and update network dictionary.

        Args:
            ap_instance: Accesspoint index that was configured.
            ap: Accesspoint object corresponding to ap_instance.
            network: Network dictionary.
            band: Wifi networks' band.

        """
        bssid = ap.get_bssid_from_ssid(network["SSID"], band)

        if network["security"] == hostapd_constants.WPA2_STRING:
            # TODO:(bamahadev) Change all occurances of reference_networks
            # to wpa_networks.
            self.reference_networks[ap_instance][band]["bssid"] = bssid

        if network["security"] == 'none':
            self.open_network[ap_instance][band]["bssid"] = bssid

    def populate_bssid(self, ap_instance, ap, networks_5g, networks_2g):
        """Get bssid for a given SSID and add it to the network dictionary.

        Args:
            ap_instance: Accesspoint index that was configured.
            ap: Accesspoint object corresponding to ap_instance.
            networks_5g: List of 5g networks configured on the APs.
            networks_2g: List of 2g networks configured on the APs.

        """

        if not (networks_5g or networks_2g):
            return

        for network in networks_5g:
            if 'channel' in network:
                continue
            self.update_bssid(ap_instance, ap, network,
                hostapd_constants.BAND_5G)

        for network in networks_2g:
            if 'channel' in network:
                continue
            self.update_bssid(ap_instance, ap, network,
                hostapd_constants.BAND_2G)

    def legacy_configure_ap_and_start(
            self,
            channel_5g=hostapd_constants.AP_DEFAULT_CHANNEL_5G,
            channel_2g=hostapd_constants.AP_DEFAULT_CHANNEL_2G,
            max_2g_networks=hostapd_constants.AP_DEFAULT_MAX_SSIDS_2G,
            max_5g_networks=hostapd_constants.AP_DEFAULT_MAX_SSIDS_5G,
            ap_ssid_length_2g=hostapd_constants.AP_SSID_LENGTH_2G,
            ap_passphrase_length_2g=hostapd_constants.AP_PASSPHRASE_LENGTH_2G,
            ap_ssid_length_5g=hostapd_constants.AP_SSID_LENGTH_5G,
            ap_passphrase_length_5g=hostapd_constants.AP_PASSPHRASE_LENGTH_5G,
            hidden=False,
            same_ssid=False,
            mirror_ap=True,
            ap_count=1):
        asserts.assert_true(
            len(self.user_params["AccessPoint"]) == 2,
            "Exactly two access points must be specified. \
             Each access point has 2 radios, one each for 2.4GHZ \
             and 5GHz. A test can choose to use one or both APs.")

        config_count = 1
        count = 0

        # For example, the NetworkSelector tests use 2 APs and require that
        # both APs are not mirrored.
        if not mirror_ap and ap_count == 1:
             raise ValueError("ap_count cannot be 1 if mirror_ap is False.")

        if not mirror_ap:
            config_count = ap_count

        self.user_params["reference_networks"] = []
        self.user_params["open_network"] = []

        for count in range(config_count):

            network_list_2g = []
            network_list_5g = []

            orig_network_list_2g = []
            orig_network_list_5g = []

            network_list_2g.append({"channel": channel_2g})
            network_list_5g.append({"channel": channel_5g})

            networks_dict = self.get_wpa2_network(
                                mirror_ap,
                                self.user_params["reference_networks"],
                                hidden=hidden,
                                same_ssid=same_ssid)
            self.reference_networks = self.user_params["reference_networks"]

            network_list_2g.append(networks_dict["2g"])
            network_list_5g.append(networks_dict["5g"])

            # When same_ssid is set, only configure one set of WPA networks.
            # We cannot have more than one set because duplicate interface names
            # are not allowed.
            # TODO(bmahadev): Provide option to select the type of network,
            # instead of defaulting to WPA.
            if not same_ssid:
                networks_dict = self.get_open_network(
                                    mirror_ap,
                                    self.user_params["open_network"],
                                    hidden=hidden,
                                    same_ssid=same_ssid)
                self.open_network = self.user_params["open_network"]

                network_list_2g.append(networks_dict["2g"])
                network_list_5g.append(networks_dict["5g"])

            orig_network_list_5g = copy.copy(network_list_5g)
            orig_network_list_2g = copy.copy(network_list_2g)

            if len(network_list_5g) > 1:
                self.config_5g = self._generate_legacy_ap_config(network_list_5g)
            if len(network_list_2g) > 1:
                self.config_2g = self._generate_legacy_ap_config(network_list_2g)

            self.access_points[count].start_ap(self.config_2g)
            self.access_points[count].start_ap(self.config_5g)
            self.populate_bssid(count, self.access_points[count], orig_network_list_5g,
                                orig_network_list_2g)

        # Repeat configuration on the second router.
        if mirror_ap and ap_count == 2:
            self.access_points[AP_2].start_ap(self.config_2g)
            self.access_points[AP_2].start_ap(self.config_5g)
            self.populate_bssid(AP_2, self.access_points[AP_2],
                orig_network_list_5g, orig_network_list_2g)

    def _generate_legacy_ap_config(self, network_list):
        bss_settings = []
        ap_settings = network_list.pop(0)
        # TODO:(bmahadev) This is a bug. We should not have to pop the first
        # network in the list and treat it as a separate case. Instead,
        # create_ap_preset() should be able to take NULL ssid and security and
        # build config based on the bss_Settings alone.
        hostapd_config_settings = network_list.pop(0)
        for network in network_list:
            if "password" in network:
                bss_settings.append(
                    hostapd_bss_settings.BssSettings(
                        name=network["SSID"],
                        ssid=network["SSID"],
                        hidden=network["hiddenSSID"],
                        security=hostapd_security.Security(
                            security_mode=network["security"],
                            password=network["password"])))
            elif "password" not in network:
                bss_settings.append(
                    hostapd_bss_settings.BssSettings(
                        name=network["SSID"],
                        ssid=network["SSID"],
                        hidden=network["hiddenSSID"]))

        if "password" in hostapd_config_settings:
            config = hostapd_ap_preset.create_ap_preset(
                channel=ap_settings["channel"],
                ssid=hostapd_config_settings["SSID"],
                hidden=hostapd_config_settings["hiddenSSID"],
                security=hostapd_security.Security(
                    security_mode=hostapd_config_settings["security"],
                    password=hostapd_config_settings["password"]),
                bss_settings=bss_settings,
                profile_name='whirlwind')
        else:
            config = hostapd_ap_preset.create_ap_preset(
                channel=ap_settings["channel"],
                ssid=hostapd_config_settings["SSID"],
                hidden=hostapd_config_settings["hiddenSSID"],
                bss_settings=bss_settings,
                profile_name='whirlwind')
        return config
