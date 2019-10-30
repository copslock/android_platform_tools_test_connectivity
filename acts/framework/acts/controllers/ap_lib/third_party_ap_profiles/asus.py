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


def asus_rtac66u(iface_wlan_2g=None,
                 iface_wlan_5g=None,
                 channel=None,
                 security=None,
                 ssid=None):
    # TODO(b/143104825): Permit RIFS once it is supported
    """A simulated implementation of an Asus RTAC66U AP.
    Args:
        iface_wlan_2g: The 2.4Ghz interface of the test AP.
        iface_wlan_5g: The 5Ghz interface of the test AP.
        channel: What channel to use.
        security: A security profile.  Must be none or WPA2 as this is what is
            supported by the RTAC66U.
        ssid: Network name
    Returns:
        A hostapd config
    Differences from real RTAC66U:
        2.4 GHz:
            Rates:
                RTAC66U:
                    Supported: 1, 2, 5.5, 11, 18, 24, 36, 54
                    Extended: 6, 9, 12, 48
                Simulated:
                    Supported: 1, 2, 5.5, 11, 6, 9, 12, 18
                    Extended: 24, 36, 48, 54
            HT Capab:
                Info
                    RTAC66U: Green Field supported
                    Simulated: Green Field not supported by driver
        5GHz:
            VHT Capab:
                RTAC66U:
                    SU Beamformer Supported,
                    SU Beamformee Supported,
                    Beamformee STS Capability: 3,
                    Number of Sounding Dimensions: 3,
                    VHT Link Adaptation: Both
                Simulated:
                    Above are not supported by driver
            VHT Operation Info:
                RTAC66U: Basic MCS Map (0x0000)
                Simulated: Basic MCS Map (0xfffc)
            VHT Tx Power Envelope:
                RTAC66U: Local Max Tx Pwr Constraint: 1.0 dBm
                Simulated: Local Max Tx Pwr Constraint: 23.0 dBm
        Both:
            HT Capab:
                A-MPDU
                    RTAC66U: MPDU Density 4
                    Simulated: MPDU Density 8
            HT Info:
                RTAC66U: RIFS Permitted
                Simulated: RIFS Prohibited
    """
    if not iface_wlan_2g or not iface_wlan_5g:
        raise ValueError('Wlan interface for 2G and/or 5G is missing.')
    if (iface_wlan_2g not in hostapd_constants.INTERFACE_2G_LIST
            or iface_wlan_5g not in hostapd_constants.INTERFACE_5G_LIST):
        raise ValueError('Invalid interface name was passed.')
    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The mock ASUS RT-AC66U only supports a WPA2 '
                                 'unicast and multicast cipher of CCMP. '
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
        else:
            raise ValueError(
                'The Asus RT-AC66U only supports WPA2 or open. Invalid '
                'security mode (%s)' % security.security_mode)

    # Common Parameters
    rates = {'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'}
    n_capabilities = [
        hostapd_constants.N_CAPABILITY_LDPC,
        hostapd_constants.N_CAPABILITY_TX_STBC,
        hostapd_constants.N_CAPABILITY_RX_STBC1,
        hostapd_constants.N_CAPABILITY_MAX_AMSDU_7935,
        hostapd_constants.N_CAPABILITY_DSSS_CCK_40,
        hostapd_constants.N_CAPABILITY_SGI20
    ]
    # WPS IE
    # Broadcom IE
    vendor_elements = {
        'vendor_elements':
        'dd310050f204104a00011010440001021047001093689729d373c26cb1563c6c570f33'
        'd7103c0001031049000600372a000120'
        'dd090010180200001c0000'
    }

    # 2.4GHz
    if channel <= 11:
        interface = iface_wlan_2g
        rates['basic_rates'] = '10 20 55 110'
        mode = hostapd_constants.MODE_11N_MIXED
        ac_capabilities = None
        vht_channel_width = None
        vht_center_channel = None

    # 5GHz
    else:
        interface = iface_wlan_5g
        rates['basic_rates'] = '60 120 240'
        mode = hostapd_constants.MODE_11AC_MIXED
        ac_capabilities = [
            hostapd_constants.AC_CAPABILITY_RXLDPC,
            hostapd_constants.AC_CAPABILITY_SHORT_GI_80,
            hostapd_constants.AC_CAPABILITY_TX_STBC_2BY1,
            hostapd_constants.AC_CAPABILITY_RX_STBC_1,
            hostapd_constants.AC_CAPABILITY_MAX_MPDU_11454,
            hostapd_constants.AC_CAPABILITY_MAX_A_MPDU_LEN_EXP7
        ]
        vht_channel_width = 40
        vht_center_channel = 36

    additional_params = _merge_dicts(rates, vendor_elements,
                                     hostapd_constants.UAPSD_ENABLED)

    config = hostapd_config.HostapdConfig(
        ssid=ssid,
        channel=channel,
        hidden=False,
        security=security,
        interface=interface,
        mode=mode,
        force_wmm=True,
        beacon_interval=100,
        dtim_period=3,
        short_preamble=False,
        n_capabilities=n_capabilities,
        ac_capabilities=ac_capabilities,
        vht_channel_width=vht_channel_width,
        vht_center_channel=vht_center_channel,
        additional_parameters=additional_params)

    return config


def asus_rtac86u(iface_wlan_2g=None,
                 iface_wlan_5g=None,
                 channel=None,
                 security=None,
                 ssid=None):
    """A simulated implementation of an Asus RTAC86U AP.
    Args:
        iface_wlan_2g: The 2.4Ghz interface of the test AP.
        iface_wlan_5g: The 5Ghz interface of the test AP.
        channel: What channel to use.
        security: A security profile.  Must be none or WPA2 as this is what is
            supported by the RTAC86U.
        ssid: Network name
    Returns:
        A hostapd config
    Differences from real RTAC86U:
        2.4GHz:
            Rates:
                RTAC86U:
                    Supported: 1, 2, 5.5, 11, 18, 24, 36, 54
                    Extended: 6, 9, 12, 48
                Simulated:
                    Supported: 1, 2, 5.5, 11, 6, 9, 12, 18
                    Extended: 24, 36, 48, 54
        5GHz:
            Country Code:
                Simulated: Has two country code IEs, one that matches
                the actual, and another explicit IE that was required for
                hostapd's 802.11d to work.
        Both (w/ WPA2):
            RSN Capabilities:
                RTA86U: 0x000c (RSN PTKSA Replay Counter Capab: 16)
                Simulated: 0x0000
    """
    if not iface_wlan_2g or not iface_wlan_5g:
        raise ValueError('Wlan interface for 2G and/or 5G is missing.')
    if (iface_wlan_2g not in hostapd_constants.INTERFACE_2G_LIST
            or iface_wlan_5g not in hostapd_constants.INTERFACE_5G_LIST):
        raise ValueError('Invalid interface name was passed.')
    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The mock ASUS RTAC86U only supports a WPA2 '
                                 'unicast and multicast cipher of CCMP. '
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
        else:
            raise ValueError(
                'The Asus RTAC86U only supports WPA2 or open. Invalid '
                'security mode (%s)' % security.security_mode)

    # Common Parameters
    rates = {'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'}
    qbss = {'bss_load_update_period': 50, 'chan_util_avg_period': 600}

    # 2.4GHz
    if channel <= 11:
        interface = iface_wlan_2g
        mode = hostapd_constants.MODE_11G
        rates['basic_rates'] = '10 20 55 110'
        spectrum_mgmt = False
        # Measurement Pilot Transmission IE
        vendor_elements = {'vendor_elements': '42020000'}

    # 5GHz
    else:
        interface = iface_wlan_5g
        mode = hostapd_constants.MODE_11A
        rates['basic_rates'] = '60 120 240'
        spectrum_mgmt = True,
        # Country Information IE (w/ individual channel info)
        # TPC Report Transmit Power IE
        # Measurement Pilot Transmission IE
        vendor_elements = {
            'vendor_elements':
            '074255532024011e28011e2c011e30011e34011e38011e3c011e40011e64011e'
            '68011e6c011e70011e74011e84011e88011e8c011e95011e99011e9d011ea1011e'
            'a5011e'
            '23021300'
            '42020000'
        }

    additional_params = _merge_dicts(rates, qbss, vendor_elements)

    config = hostapd_config.HostapdConfig(
        ssid=ssid,
        channel=channel,
        hidden=False,
        security=security,
        interface=interface,
        mode=mode,
        force_wmm=False,
        beacon_interval=100,
        dtim_period=3,
        short_preamble=False,
        spectrum_mgmt_required=spectrum_mgmt,
        additional_parameters=additional_params)
    return config