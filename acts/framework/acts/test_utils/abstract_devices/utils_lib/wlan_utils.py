#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

from acts import signals
from acts.controllers.ap_lib import hostapd_ap_preset


def setup_ap_and_associate(access_point,
                           client,
                           profile_name,
                           channel,
                           ssid,
                           mode=None,
                           preamble=None,
                           beacon_interval=None,
                           dtim_period=None,
                           frag_threshold=None,
                           rts_threshold=None,
                           force_wmm=None,
                           hidden=False,
                           security=None,
                           additional_ap_parameters=None,
                           password=None,
                           check_connectivity=False,
                           n_capabilities=None,
                           ac_capabilities=None,
                           vht_bandwidth=None):
    """Sets up the AP and associates a client.

    Args:
        access_point: An ACTS access_point controller
        client: A WlanDevice.
        profile_name: The profile name of one of the hostapd ap presets.
        channel: What channel to set the AP to.
        preamble: Whether to set short or long preamble (True or False)
        beacon_interval: The beacon interval (int)
        dtim_period: Length of dtim period (int)
        frag_threshold: Fragmentation threshold (int)
        rts_threshold: RTS threshold (int)
        force_wmm: Enable WMM or not (True or False)
        hidden: Advertise the SSID or not (True or False)
        security: What security to enable.
        additional_ap_parameters: Additional parameters to send the AP.
        password: Password to connect to WLAN if necessary.
        check_connectivity: Whether to check for internet connectivity.
    """
    ap = hostapd_ap_preset.create_ap_preset(
        profile_name=profile_name,
        iface_wlan_2g=access_point.wlan_2g,
        iface_wlan_5g=access_point.wlan_5g,
        channel=channel,
        ssid=ssid,
        mode=mode,
        short_preamble=preamble,
        beacon_interval=beacon_interval,
        dtim_period=dtim_period,
        frag_threshold=frag_threshold,
        rts_threshold=rts_threshold,
        force_wmm=force_wmm,
        hidden=hidden,
        bss_settings=[],
        security=security,
        n_capabilities=n_capabilities,
        ac_capabilities=ac_capabilities,
        vht_bandwidth=vht_bandwidth)
    access_point.start_ap(
        hostapd_config=ap,
        additional_parameters=additional_ap_parameters)
    associate(client,
              ssid,
              password,
              check_connectivity=check_connectivity,
              hidden=hidden)


def associate(client,
              ssid,
              password=None,
              check_connectivity=True,
              hidden=False):
    """Associates a client to a WLAN network.

    Args:
        client: A WlanDevice
        ssid: SSID of the ap we are looking for.
        password: The password for the WLAN, if applicable.
        check_connectivity: Whether to check internet connectivity.
        hidden: If the WLAN is hidden or not.
    """
    if client.associate(ssid,
                        password,
                        check_connectivity=check_connectivity,
                        hidden=hidden):
        raise signals.TestPass("Successfully associated.")
    else:
        raise signals.TestFailure("Failed to associate.")
