#!/usr/bin/python3.4
#
#   Copyright 2015 - The Android Open Source Project
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

import pprint
import time

from queue import Empty
from random import shuffle

from acts.base_test import BaseTestClass
from acts.test_utils.wifi_test_utils import eap_connect
from acts.test_utils.wifi_test_utils import expand_enterprise_config_by_phase2
from acts.test_utils.wifi_test_utils import reset_droid_wifi
from acts.test_utils.wifi_test_utils import start_wifi_connection_scan
from acts.test_utils.wifi_test_utils import wifi_test_device_init
from acts.test_utils.wifi_test_utils import WifiEnums
from acts.test_utils.wifi_test_utils import WifiEventNames

# EAP Macros
EAP = WifiEnums.Eap
EapPhase2 = WifiEnums.EapPhase2

# Enterprise Config Macros
Ent = WifiEnums.Enterprise
# Event name macros
Event = WifiEventNames


class WifiEnterpriseTest(BaseTestClass):

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.tests = (
            "test_eap_connect",
            "test_eap_connect_negative",
            # "test_passpoint_connect",
            # "test_passpoint_connect_negative"
        )

    def setup_class(self):
        self.dut = self.android_devices[0]
        wifi_test_device_init(self.dut)
        required_userparam_names = (
            "ca_cert",
            "client_cert",
            "client_key",
            "passpoint_ca_cert",
            "passpoint_client_cert",
            "passpoint_client_key",
            "eap_identity",
            "eap_password",
            "invalid_ca_cert",
            "invalid_client_cert",
            "invalid_client_key",
            "fqdn",
            "provider_friendly_name",
            "realm",
            "ssid_peap",
            "ssid_tls",
            "ssid_ttls",
            "ssid_sim",
            "ssid_passpoint",
            "device_password",
            "ping_addr"
        )
        optional_userparam_names = (
            "roaming_consortium_ids",
            "plmn"
        )
        assert self.unpack_userparams(required_userparam_names,
                    opt_param_names = optional_userparam_names)
        # Default configs for EAP networks.
        self.config_peap = {
            Ent.EAP: EAP.PEAP,
            Ent.CA_CERT: self.ca_cert,
            Ent.IDENTITY: self.eap_identity,
            Ent.PASSWORD: self.eap_password,
            Ent.PHASE2: EapPhase2.MSCHAPV2,
            WifiEnums.SSID_KEY: self.ssid_peap
        }
        self.config_tls = {
            Ent.EAP: EAP.TLS,
            Ent.CA_CERT: self.ca_cert,
            WifiEnums.SSID_KEY: self.ssid_tls,
            Ent.CLIENT_CERT: self.client_cert,
            Ent.PRIVATE_KEY_ID: self.client_key,
            Ent.IDENTITY: self.eap_identity,
        }
        self.config_ttls = {
            Ent.EAP: EAP.TTLS,
            Ent.CA_CERT: self.ca_cert,
            Ent.IDENTITY: self.eap_identity,
            Ent.PASSWORD: self.eap_password,
            Ent.PHASE2: EapPhase2.MSCHAPV2,
            WifiEnums.SSID_KEY: self.ssid_ttls
        }
        self.config_sim = {
            Ent.EAP: EAP.SIM,
            WifiEnums.SSID_KEY: self.ssid_sim,
        }

        # Base config for passpoint networks.
        self.config_passpoint = {
            Ent.FQDN: self.fqdn,
            Ent.FRIENDLY_NAME: self.provider_friendly_name,
            Ent.REALM: self.realm,
            Ent.CA_CERT: self.passpoint_ca_cert
        }
        if hasattr(self, "plmn"):
            self.config_passpoint[Ent.PLMN] = self.plmn
        if hasattr(self, "roaming_consortium_ids"):
            self.config_passpoint[Ent.ROAMING_IDS] = self.roaming_consortium_ids

        # Default configs for passpoint networks.
        self.config_passpoint_tls = dict(self.config_tls)
        self.config_passpoint_tls.update(self.config_passpoint)
        self.config_passpoint_tls[Ent.CLIENT_CERT] = self.passpoint_client_cert
        self.config_passpoint_tls[Ent.PRIVATE_KEY_ID] = self.passpoint_client_key
        del self.config_passpoint_tls[WifiEnums.SSID_KEY]
        self.config_passpoint_ttls = dict(self.config_ttls)
        self.config_passpoint_ttls.update(self.config_passpoint)
        del self.config_passpoint_ttls[WifiEnums.SSID_KEY]
        # Set screen lock password so ConfigStore is unlocked.
        self.droid.setDevicePassword(self.device_password)
        return True

    def teardown_class(self):
        reset_droid_wifi(self.droid, self.ed)
        self.droid.disableDevicePassword()
        self.ed.clear_all_events()

    def setup_test(self):
        self.droid.wifiStartTrackingStateChange()
        self.droid.wakeLockAcquireBright()
        self.droid.wakeUpNow()
        reset_droid_wifi(self.droid, self.ed)
        self.ed.clear_all_events()
        return True

    def teardown_test(self):
        self.droid.wakeLockRelease()
        self.droid.goToSleepNow()
        self.droid.wifiStopTrackingStateChange()

    """Helper Functions"""

    def eap_negative_connect_logic(self, config, ad):
        """Tries to connect to an enterprise network with invalid credentials
        and expect a failure.

        Args:
            config: A dict representing an invalid EAP credential.

        Returns:
            True if connection failed as expected, False otherwise.
        """
        verdict = eap_connect(config, ad)
        self.assert_true(not verdict, "Connection should have failed.")
        self.log.info("Connection failed as expected.")
        return True

    def expand_config_by_phase2(self, config):
        """Take an enterprise config and generate a list of configs, each with
        a different phase2 auth type.

        Args:
            config: A dict representing enterprise config.

        Returns
            A list of enterprise configs.
        """
        results = []
        for phase2_type in EapPhase2:
            # Skip a special case for passpoint TTLS.
            if Ent.FQDN in config and phase2_type == EapPhase2.GTC:
                continue
            c = dict(config)
            c[Ent.PHASE2] = phase2_type
            results.append(c)
        return results

    def gen_eap_configs(self):
        """Generates configurations for different EAP authentication types.

        Returns:
            A list of dicts each representing an EAP configuration.
        """
        configs = [self.config_tls]
                   # self.config_sim
        configs += expand_enterprise_config_by_phase2(self.config_ttls)
        configs += expand_enterprise_config_by_phase2(self.config_peap)
        return configs

    def gen_passpoint_configs(self):
        """Generates passpoint configurations for different EAP authentication
        types.

        Returns:
            A list of dicts each representing an EAP configuration for
            passpoint networks.
        """
        configs = [self.config_passpoint_tls]
        configs += expand_enterprise_config_by_phase2(self.config_passpoint_ttls)
        return configs

    def gen_negative_configs(self, configs, neg_params):
        """Generic function used to generate negative configs.

        For all the valid configurations, if a param in the neg_params also
        exists in a config, a copy of the config is made with an invalid value
        of the param.

        Args:
            configs: A list of valid configurations.
            neg_params: A dict that has all the invalid values.

        Returns:
            A list of invalid configurations generated based on the valid
            configurations. Each invalid configuration has a different invalid
            field.
        """
        results = []
        for c in configs:
            for k, v in neg_params.items():
                # Skip negative test for TLS's identity field since it's not
                # used for auth.
                if c[Ent.EAP] == EAP.TLS and k == Ent.IDENTITY:
                    continue
                if k in c:
                    nc = dict(c)
                    nc[k] = v
                    nc["invalid_field"] = k
                    results.append(nc)
        return results

    def gen_negative_eap_configs(self):
        """Generates invalid configurations for different EAP authentication
        types.

        For all the valid EAP configurations, if a param that is part of the
        authentication info exists in a config, a copy of the config is made
        with an invalid value of the param.

        Returns:
            A list of dicts each representing an invalid EAP configuration.
        """
        neg_params = {
            Ent.CLIENT_CERT: self.invalid_client_cert,
            Ent.CA_CERT: self.invalid_ca_cert,
            Ent.PRIVATE_KEY_ID: self.invalid_client_key,
            Ent.IDENTITY: "fake_identity",
            Ent.PASSWORD: "wrong_password"
        }
        configs = self.gen_eap_configs()
        return self.gen_negative_configs(configs, neg_params)

    def gen_negative_passpoint_configs(self):
        """Generates invalid configurations for different EAP authentication
        types with passpoint support.

        Returns:
            A list of dicts each representing an invalid EAP configuration
            with passpoint fields.
        """
        neg_params = {
            Ent.CLIENT_CERT: self.invalid_client_cert,
            Ent.CA_CERT: self.invalid_ca_cert,
            Ent.PRIVATE_KEY_ID: self.invalid_client_key,
            Ent.IDENTITY: "fake_identity",
            Ent.PASSWORD: "wrong_password",
            Ent.FQDN: "fake_fqdn",
            Ent.REALM: "where_no_one_has_gone_before",
            Ent.PLMN: "fake_plmn",
            Ent.ROAMING_IDS: [1234567890, 9876543210]
        }
        configs = self.gen_passpoint_configs()
        return self.gen_negative_configs(configs, neg_params)

    def gen_eap_test_name(self, config, ad):
        """Generates a test case name based on an EAP configuration.

        Args:
            config: A dict representing an EAP credential.
            ad: Discarded. This is here because name function signature needs
                to be consistent with logic function signature for generated
                test cases.

        Returns:
            A string representing the name of a generated EAP test case.
        """
        name = "test_connect-%s" % config[Ent.EAP].name
        if Ent.PHASE2 in config:
            name += "-{}".format(config[Ent.PHASE2].name)
        return name

    def gen_passpoint_test_name(self, config, ad):
        """Generates a test case name based on an EAP passpoint configuration.

        Args:
            config: A dict representing an EAP passpoint credential.
            ad: Discarded. This is here because name function signature needs
                to be consistent with logic function signature for generated
                test cases.

        Returns:
            A string representing the name of a generated EAP passpoint connect
            test case.
        """
        name = self.gen_eap_test_name(config, ad)
        name = name.replace("connect", "passpoint_connect")
        return name

    """Tests"""
    def test_eap_connect(self):
        """Test connecting to enterprise networks of different authentication
        types.

        The authentication types tested are:
            EAP-TLS
            EAP-PEAP with different phase2 types.
            EAP-TTLS with different phase2 types.

        Procedures:
            For each enterprise wifi network
            1. Connect to the network.
            2. Send a GET request to a website and check response.

        Expect:
            Successful connection and Internet access through the enterprise
            networks.
        """
        eap_configs = self.gen_eap_configs()
        self.log.info("Testing %d different configs." % len(eap_configs))
        shuffle(eap_configs)
        failed = self.run_generated_testcases(
            eap_connect,
            eap_configs,
            self.dut,
            name_func=self.gen_eap_test_name)
        msg = ("The following configs failed EAP connect test: %s" %
               pprint.pformat(failed))
        self.assert_true(len(failed) == 0, msg)
        return True

    def test_eap_connect_negative(self):
        """Test connecting to enterprise networks.

        Procedures:
            For each enterprise wifi network
            1. Connect to the network with invalid credentials.

        Expect:
            Fail to establish connection.
        """
        neg_eap_configs = self.gen_negative_eap_configs()
        self.log.info("Testing %d different configs." % len(neg_eap_configs))
        shuffle(neg_eap_configs)
        def name_gen(config, ad):
            name = self.gen_eap_test_name(config, ad)
            name += "-with_wrong-{}".format(config["invalid_field"])
            return name
        failed = self.run_generated_testcases(
            self.eap_negative_connect_logic,
            neg_eap_configs,
            self.dut,
            name_func=name_gen)
        msg = ("The following configs failed negative EAP connect test: %s" %
               pprint.pformat(failed))
        self.assert_true(len(failed) == 0, msg)
        return True

    def test_passpoint_connect(self):
        """Test connecting to enterprise networks of different authentication
        types with passpoint support.

        The authentication types tested are:
            EAP-TLS
            EAP-TTLS with MSCHAPV2 as phase2.

        Procedures:
            For each enterprise wifi network
            1. Connect to the network.
            2. Send a GET request to a website and check response.

        Expect:
            Successful connection and Internet access through the enterprise
            networks with passpoint support.
        """
        self.skip_if(not self.dut.droid.wifiIsPasspointSupported(),
            "Passpoint is not supported on device %s" % self.dut.model)
        passpoint_configs = self.gen_passpoint_configs()
        self.log.info("Testing %d different configs." % len(passpoint_configs))
        shuffle(passpoint_configs)
        failed = self.run_generated_testcases(
            eap_connect,
            passpoint_configs,
            self.dut,
            name_func=self.gen_passpoint_test_name)
        msg = ("The following configs failed passpoint connect test: %s" %
               pprint.pformat(failed))
        self.assert_true(len(failed) == 0, msg)
        return True

    def test_passpoint_connect_negative(self):
        """Test connecting to enterprise networks.

        Procedures:
            For each enterprise wifi network
            1. Connect to the network with invalid credentials.

        Expect:
            Fail to establish connection.
        """
        self.skip_if(not self.dut.droid.wifiIsPasspointSupported(),
            "Passpoint is not supported on device %s" % self.dut.model)
        neg_passpoint_configs = self.gen_negative_passpoint_configs()
        self.log.info("Testing %d different configs." % len(neg_passpoint_configs))
        shuffle(neg_passpoint_configs)
        def name_gen(config, ad):
            name = self.gen_passpoint_test_name(config, ad)
            name += "-with_wrong-{}".format(config["invalid_field"])
            return name
        failed = self.run_generated_testcases(
            self.eap_negative_connect_logic,
            neg_passpoint_configs,
            self.dut,
            name_func=name_gen)
        msg = ("The following configs failed negative passpoint connect test: "
               "%s") % pprint.pformat(failed)
        self.assert_true(len(failed) == 0, msg)
        return True

if __name__ == "__main__":
    pass
