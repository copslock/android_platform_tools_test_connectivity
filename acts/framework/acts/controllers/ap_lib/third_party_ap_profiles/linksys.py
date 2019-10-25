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

from acts.controllers.ap_lib import hostapd_config
from acts.controllers.ap_lib import hostapd_constants


def _merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def linksys_ea4500(iface_wlan_2g=None,
                   iface_wlan_5g=None,
                   channel=None,
                   security=None,
                   ssid=None):
    # TODO(b/143104825): Permit RIFS once it is supported
    """A simulated implementation of what a Linksys EA4500 AP
    Args:
        iface_wlan_2g: The 2.4Ghz interface of the test AP.
        iface_wlan_5g: The 5GHz interface of the test AP.
        channel: What channel to use.
        security: A security profile (None or WPA2).
        ssid: The network name.
    Returns:
        A hostapd config.
    Differences from real EA4500:
        CF (Contention-Free) Parameter IE:
            EA4500: has CF Parameter IE
            Simulated: does not have CF Parameter IE
        HT Capab:
            Info:
                EA4500: Green Field supported
                Simulated: Green Field not supported by driver
            A-MPDU
                RTAC66U: MPDU Density 4
                Simulated: MPDU Density 8
        RSN Capab (only w/ WPA):
            EA4500:
                RSN PTKSA Replay Counter capab: 16
            Simulated:
                RSN PTKSA Replay Counter capab: 1

    """
    if not iface_wlan_2g or not iface_wlan_5g:
        raise ValueError('Wlan interface for 2G and/or 5G is missing.')
    if (iface_wlan_2g not in hostapd_constants.INTERFACE_2G_LIST
            or iface_wlan_5g not in hostapd_constants.INTERFACE_5G_LIST):
        raise ValueError('Invalid interface name was passed.')

    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The mock Linksys EA4500 only supports a '
                                 'WPA2 unicast and multicast cipher of CCMP.'
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
        else:
            raise ValueError('The mock Linksys EA4500 only supports WPA2. '
                             'Invalid security mode (%s)' %
                             security.security_mode)

    # Common Parameters
    rates = {'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'}

    n_capabilities = [
        hostapd_constants.N_CAPABILITY_SGI20,
        hostapd_constants.N_CAPABILITY_SGI40,
        hostapd_constants.N_CAPABILITY_TX_STBC,
        hostapd_constants.N_CAPABILITY_RX_STBC1,
        hostapd_constants.N_CAPABILITY_DSSS_CCK_40
    ]

    # Epigram HT Capabilities IE
    # Epigram HT Additional Capabilities IE
    # Marvell Semiconductor, Inc. IE
    vendor_elements = {
        'vendor_elements':
        'dd1e00904c33fc0117ffffff0000000000000000000000000000000000000000'
        'dd1a00904c3424000000000000000000000000000000000000000000'
        'dd06005043030000'
    }

    # 2.4GHz
    if channel <= 11:
        interface = iface_wlan_2g
        rates['basic_rates'] = '10 20 55 110'
        obss_interval = 180
        n_capabilities.append(hostapd_constants.N_CAPABILITY_HT40_PLUS)

    # 5GHz
    else:
        interface = iface_wlan_5g
        rates['basic_rates'] = '60 120 240'
        obss_interval = None

    additional_params = _merge_dicts(rates, vendor_elements,
                                     hostapd_constants.UAPSD_ENABLED)

    config = hostapd_config.HostapdConfig(
        ssid=ssid,
        channel=channel,
        hidden=False,
        security=security,
        interface=interface,
        mode=hostapd_constants.MODE_11N_MIXED,
        force_wmm=True,
        beacon_interval=100,
        dtim_period=1,
        short_preamble=True,
        obss_interval=obss_interval,
        n_capabilities=n_capabilities,
        additional_parameters=additional_params)

    return config