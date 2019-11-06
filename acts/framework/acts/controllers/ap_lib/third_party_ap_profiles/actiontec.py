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


def actiontec_pk5000(iface_wlan_2g=None,
                     channel=None,
                     security=None,
                     ssid=None):
    """A simulated implementation of what a Actiontec PK5000 AP
    Args:
        iface_wlan_2g: The 2.4 interface of the test AP.
        channel: What channel to use.  Only 2.4Ghz is supported for this profile
        security: A security profile.  Must be none or WPA2 as this is what is
            supported by the PK5000.
        ssid: Network name
    Returns:
        A hostapd config

    Differences from real pk5000:
        Supported Rates IE:
            PK5000: Supported: 1, 2, 5.5, 11
                    Extended: 6, 9, 12, 18, 24, 36, 48, 54
            Simulated: Supported: 1, 2, 5.5, 11, 6, 9, 12, 18
                       Extended: 24, 36, 48, 54
    """
    if channel > 11:
        # Technically this should be 14 but since the PK5000 is a US only AP,
        # 11 is the highest allowable channel.
        raise ValueError('The Actiontec PK5000 does not support 5Ghz. '
                         'Invalid channel (%s)' % channel)
    else:
        interface = iface_wlan_2g
        short_preamble = False
        force_wmm = False
        beacon_interval = 100
        dtim_period = 3
        # Sets the basic rates and supported rates of the PK5000
        additional_params = {
            'basic_rates': '10 20 55 110',
            'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'
        }

    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The Actiontec PK5000 only supports a WPA2 '
                                 'unicast and multicast cipher of CCMP. '
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
            # Fake WPS IE based on the PK5000
            additional_params['vendor_elements'] = 'dd0e0050f204104a00011010' \
                                                   '44000102'
        else:
            raise ValueError(
                'The Actiontec PK5000 only supports WPA2. Invalid security '
                'mode (%s)' % security.security_mode)
    elif security is None:
        pass
    else:
        raise ValueError('Only open or wpa2 are supported on the '
                         'Actiontec PK5000.')

    config = hostapd_config.HostapdConfig(
        ssid=ssid,
        channel=channel,
        hidden=False,
        security=security,
        interface=interface,
        mode=hostapd_constants.MODE_11G,
        force_wmm=force_wmm,
        beacon_interval=beacon_interval,
        dtim_period=dtim_period,
        short_preamble=short_preamble,
        additional_parameters=additional_params)

    return config


def actiontec_mi424wr(iface_wlan_2g=None,
                      channel=None,
                      security=None,
                      ssid=None):
    # TODO(b/143104825): Permit RIFS once it is supported
    """A simulated implementation of an Actiontec MI424WR AP.
    Args:
        iface_wlan_2g: The 2.4Ghz interface of the test AP.
        channel: What channel to use (2.4Ghz or 5Ghz).
        security: A security profile.
        ssid: The network name.
    Returns:
        A hostapd config.

    Differences from real MI424WR:
        HT Capabilities:
            MI424WR:
                HT Rx STBC: Support for 1, 2, and 3
            Simulated:
                HT Rx STBC: Support for 1
        HT Information:
            MI424WR:
                RIFS: Premitted
            Simulated:
                RIFS: Prohibited
    """
    if channel > 11:
        raise ValueError('The Actiontec MI424WR does not support 5Ghz. '
                         'Invalid channel (%s)' % channel)
    if (iface_wlan_2g not in hostapd_constants.INTERFACE_2G_LIST):
        raise ValueError('Invalid interface name was passed.')

    if security:
        if security.security_mode is hostapd_constants.WPA2:
            if not security.wpa2_cipher == 'CCMP':
                raise ValueError('The mock Actiontec MI424WR only supports a '
                                 'WPA2 unicast and multicast cipher of CCMP.'
                                 'Invalid cipher mode (%s)' %
                                 security.security.wpa2_cipher)
        else:
            raise ValueError('The mock Actiontec MI424WR only supports WPA2. '
                             'Invalid security mode (%s)' %
                             security.security_mode)

    n_capabilities = [
        hostapd_constants.N_CAPABILITY_TX_STBC,
        hostapd_constants.N_CAPABILITY_DSSS_CCK_40,
        hostapd_constants.N_CAPABILITY_RX_STBC1
    ]

    rates = {
        'basic_rates': '10 20 55 110',
        'supported_rates': '10 20 55 110 60 90 120 180 240 360 480 540'
    }

    # Proprietary Atheros Communication: Adv Capability IE
    # Proprietary Atheros Communication: Unknown IE
    # Country Info: US Only IE
    vendor_elements = {
        'vendor_elements':
        'dd0900037f01010000ff7f'
        'dd0a00037f04010000000000'
        '0706555320010b1b'
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
        dtim_period=1,
        short_preamble=True,
        n_capabilities=n_capabilities,
        additional_parameters=additional_params)

    return config
