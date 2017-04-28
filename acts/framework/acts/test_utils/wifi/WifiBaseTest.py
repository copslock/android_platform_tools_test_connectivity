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

from acts import asserts
from acts import utils
from acts.base_test import BaseTestClass
from acts.signals import TestSignal
from acts.controllers import android_device
from acts.controllers.ap_lib import hostapd_ap_preset
from acts.controllers.ap_lib import hostapd_bss_settings
from acts.controllers.ap_lib import hostapd_constants
from acts.controllers.ap_lib import hostapd_security


class WifiBaseTest(BaseTestClass):
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)

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
    ):
        asserts.assert_true(
            len(self.user_params["AccessPoint"]) == 2,
            "Exactly two access points must be specified. \
            If the access point has two radios, the configuration \
            can be repeated for the second radio.")
        network_list_2g = []
        network_list_5g = []
        self.access_point_2g = self.access_points[0]
        self.access_point_5g = self.access_points[1]
        network_list_2g.append({"channel": channel_2g})
        network_list_5g.append({"channel": channel_5g})

        if "reference_networks" in self.user_params:
            pass
        else:
            ref_5g_security = hostapd_constants.WPA2_STRING
            ref_2g_security = hostapd_constants.WPA2_STRING
            self.user_params["reference_networks"] = []
            for x in range(0, 2):
                ref_2g_ssid = '2g_%s' % utils.rand_ascii_str(ap_ssid_length_2g)
                ref_2g_passphrase = utils.rand_ascii_str(
                    ap_passphrase_length_2g)
                ref_5g_ssid = '5g_%s' % utils.rand_ascii_str(ap_ssid_length_5g)
                ref_5g_passphrase = utils.rand_ascii_str(
                    ap_passphrase_length_5g)
                network_list_2g.append({
                    "ssid": ref_2g_ssid,
                    "security": ref_2g_security,
                    "passphrase": ref_2g_passphrase
                })
                network_list_5g.append({
                    "ssid": ref_5g_ssid,
                    "security": ref_5g_security,
                    "passphrase": ref_5g_passphrase
                })
                self.user_params["reference_networks"].append({
                    "2g": {
                        "SSID": ref_2g_ssid,
                        "password": ref_2g_passphrase
                    },
                    "5g": {
                        "SSID": ref_5g_ssid,
                        "password": ref_5g_passphrase
                    }
                })
            self.reference_networks = self.user_params["reference_networks"]

        if "open_network" in self.user_params:
            pass
        else:
            self.user_params["open_network"] = []
            open_2g_ssid = '2g_%s' % utils.rand_ascii_str(8)
            network_list_2g.append({"ssid": open_2g_ssid, "security": 'none'})
            self.user_params["open_network"] = {"SSID": open_2g_ssid}
            self.open_network = self.user_params["open_network"]

        if "config_store_networks" in self.user_params:
            pass
        else:
            self.user_params["config_store_networks"] = []
            self.user_params["config_store_networks"].append(self.open_network)
            config_store_2g_security = 'wpa2'
            for x in range(0, 4):
                config_store_2g_ssid = '2g_%s' % utils.rand_ascii_str(8)
                config_store_2g_passphrase = utils.rand_ascii_str(10)
                network_list_2g.append({
                    "ssid": config_store_2g_ssid,
                    "security": config_store_2g_security,
                    "passphrase": config_store_2g_passphrase
                })
                self.user_params["config_store_networks"].append({
                    "SSID": config_store_2g_ssid,
                    "password": config_store_2g_passphrase
                })
            self.config_store_networks = self.user_params[
                "config_store_networks"]

        if "iot_networks" in self.user_params:
            pass
        else:
            self.user_params["iot_networks"] = []
            for iot_network in self.config_store_networks:
                if "password" in iot_network:
                    self.user_params["iot_networks"].append(iot_network)
            iot_2g_security = 'wpa2'
            for iot_network_2g in range(
                    0, (max_2g_networks - len(network_list_2g)) + 1):
                iot_2g_ssid = '2g_%s' % utils.rand_ascii_str(8)
                iot_2g_passphrase = utils.rand_ascii_str(10)
                network_list_2g.append({
                    "ssid": iot_2g_ssid,
                    "security": iot_2g_security,
                    "passphrase": iot_2g_passphrase
                })
                self.user_params["iot_networks"].append({
                    "SSID": iot_2g_ssid,
                    "password": iot_2g_passphrase
                })
            iot_5g_security = 'wpa2'
            for iot_network_5g in range(
                    0, (max_5g_networks - len(network_list_5g)) + 1):
                iot_5g_ssid = '5g_%s' % utils.rand_ascii_str(8)
                iot_5g_passphrase = utils.rand_ascii_str(10)
                network_list_5g.append({
                    "ssid": iot_5g_ssid,
                    "security": iot_5g_security,
                    "passphrase": iot_5g_passphrase
                })
                self.user_params["iot_networks"].append({
                    "SSID": iot_5g_ssid,
                    "password": iot_5g_passphrase
                })
            self.iot_networks = self.user_params["iot_networks"]

        if len(network_list_5g) > 1:
            self.config_5g = self._generate_legacy_ap_config(network_list_5g)
            self.access_point_5g.start_ap(self.config_5g)

        if len(network_list_2g) > 1:
            self.config_2g = self._generate_legacy_ap_config(network_list_2g)
            self.access_point_2g.start_ap(self.config_2g)

    def _generate_legacy_ap_config(self, network_list):
        bss_settings = []
        ap_settings = network_list.pop(0)
        hostapd_config_settings = network_list.pop(0)
        for network in network_list:
            if "passphrase" in network:
                bss_settings.append(
                    hostapd_bss_settings.BssSettings(
                        name=network["ssid"],
                        ssid=network["ssid"],
                        security=hostapd_security.Security(
                            security_mode=network["security"],
                            password=network["passphrase"])))
            else:
                bss_settings.append(
                    hostapd_bss_settings.BssSettings(
                        name=network["ssid"], ssid=network["ssid"]))
        if "passphrase" in hostapd_config_settings:
            config = hostapd_ap_preset.create_ap_preset(
                channel=ap_settings["channel"],
                ssid=hostapd_config_settings["ssid"],
                security=hostapd_security.Security(
                    security_mode=hostapd_config_settings["security"],
                    password=hostapd_config_settings["passphrase"]),
                bss_settings=bss_settings,
                profile_name='whirlwind')
        else:
            config = hostapd_ap_preset.create_ap_preset(
                channel=ap_settings["channel"],
                ssid=hostapd_config_settings["ssid"],
                bss_settings=bss_settings,
                profile_name='whirlwind')

        return config
