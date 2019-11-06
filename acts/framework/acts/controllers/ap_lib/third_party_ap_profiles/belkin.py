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


def belkin_f9k1001v5(iface_wlan_2g=None,
                     channel=None,
                     security=None,
                     ssid=None):
    # TODO(b/143104825): Permit RIFS once it is supported
    """A simulated implementation of what a Belkin F9K1001v5 AP
    Args:
        iface_wlan_2g: The 2.4Ghz interface of the test AP.
        channel: What channel to use.
        security: A security profile (None or WPA2).
        ssid: The network name.
    Returns:
        A hostapd config.
    Differences from real F9K1001v5:
        Rates:
            F9K1001v5:
                Supported: 1, 2, 5.5, 11, 18, 24, 36, 54
                Extended: 6, 9, 12, 48
            Simulated:
                Supported: 1, 2, 5.5, 11, 6, 9, 12, 18
                Extended: 24, 36, 48, 54
        HT Info:
            F9K1001v5:
                RIFS: Permitted
            Simulated:
                RIFS: Prohibited
    """
    if channel > 11:
        raise ValueError('The Belkin F9k1001v5 does not support 5Ghz. '
                         'Invalid channel (%s)' % channel)
    if (iface_wlan_2g not in hostapd_constants.INTERFACE_2G_LIST):
        raise ValueError('Invalid interface name was passed.')

    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The mock Belkin F9k1001v5 only supports a '
                                 'WPA2 unicast and multicast cipher of CCMP.'
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
        else:
            raise ValueError('The mock Belkin F9k1001v5 only supports WPA2. '
                             'Invalid security mode (%s)' %
                             security.security_mode)

    n_capabilities = [
        hostapd_constants.N_CAPABILITY_SGI20,
        hostapd_constants.N_CAPABILITY_SGI40,
        hostapd_constants.N_CAPABILITY_TX_STBC,
        hostapd_constants.N_CAPABILITY_MAX_AMSDU_7935,
        hostapd_constants.N_CAPABILITY_DSSS_CCK_40
    ]

    rates = {
        'basic_rates': '10 20 55 110',
        'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'
    }

    # Broadcom IE
    # WPS IE
    vendor_elements = {
        'vendor_elements':
        'dd090010180200100c0000'
        'dd180050f204104a00011010440001021049000600372a000120'
    }

    additional_params = _merge_dicts(rates, vendor_elements)

    config = hostapd_config.HostapdConfig(
        ssid=ssid,
        channel=channel,
        hidden=False,
        security=security,
        interface=iface_wlan_2g,
        mode=hostapd_constants.MODE_11N_MIXED,
        force_wmm=True,
        beacon_interval=100,
        dtim_period=3,
        short_preamble=False,
        n_capabilities=n_capabilities,
        additional_parameters=additional_params)

    return config
