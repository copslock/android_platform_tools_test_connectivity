#   Copyright 2016 - The Android Open Source Project
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

import enum
import logging
import os
import collections
import itertools


class WpaSecurityMode(enum.IntEnum):
    WPA1 = 1
    WPA2 = 2
    MIXED = 3


class Security(object):
    """Base class for security settings."""


class WpaPskSecurity(Security):
    """Security info that uses WPA encryption with a predefined psk.

    Attributes:
        mode: WpaSecurityMode, The type of WPA to use.
        psk: A predefined psk for authentication.
    """

    def __init__(self, mode, psk):
        """
        Args:
            mode: WpaSecurityMode, The type of WPA to use.
            psk: A predefined psk for authentication.
        """
        self.mode = mode
        self.psk = psk

    def generate_dict(self):
        """Returns: an ordered dictionary of settings"""
        settings = collections.OrderedDict()
        settings['wpa'] = self.mode
        settings['wpa_psk'] = self.psk

        return settings


class WpaPassphraseSecurity(Security):
    """Security settings that uses a WPA passpharse.

    Attributes:
        name: SSID brodcast name.
        mode: WpaSecurityMode, The type of WPA to use.
        passphrase: The passphrase to use for authentication.
    """

    def __init__(self, mode, passphrase):
        """
        Args:
            mode: The type of WPA to use (1, 2, or 3).
            psk: A passphrase to use for authentication
        """
        self.mode = mode
        self.passphrase = passphrase

    def generate_dict(self):
        """Returns: An ordered dictionary of settings."""
        settings = collections.OrderedDict()
        settings['wpa'] = self.mode
        settings['wpa_passphrase'] = self.passphrase

        return settings


class BssSettings(object):
    """Settings for a bss.

    Settings for a bss to allow multiple network on a single device.

    Attributes:
        name: string, The name that this bss will go by.
        ssid: string, The name of the ssid to brodcast.
        hidden: bool, If true then the ssid will be hidden.
        security: Security, The security settings to use.
    """

    def __init__(self, name, ssid=None, hidden=False, security=None):
        self.name = name
        self.ssid = ssid
        self.hidden = hidden
        self.security = security

    def generate_dict(self):
        """Returns: A dictionary of bss settings."""
        settings = collections.OrderedDict()
        settings['bss'] = self.name
        if self.ssid:
            settings['ssid'] = self.ssid
            settings['ignore_broadcast_ssid'] = 1 if self.hidden else 0

        if self.security:
            security_settings = self.security.generate_dict()
            for k, v in security_settings.items():
                settings[k] = v

        return settings


class HostapdConfig(object):
    """The root settings for the router.

    All the settings for a router that are not part of an ssid.
    """

    # A mapping of frequency to channel number.  This includes some
    # frequencies used outside the US.
    CHANNEL_MAP = {
        2412: 1,
        2417: 2,
        2422: 3,
        2427: 4,
        2432: 5,
        2437: 6,
        2442: 7,
        2447: 8,
        2452: 9,
        2457: 10,
        2462: 11,
        # 12, 13 are only legitimate outside the US.
        2467: 12,
        2472: 13,
        # 14 is for Japan, DSSS and CCK only.
        2484: 14,
        # 34 valid in Japan.
        5170: 34,
        # 36-116 valid in the US, except 38, 42, and 46, which have
        # mixed international support.
        5180: 36,
        5190: 38,
        5200: 40,
        5210: 42,
        5220: 44,
        5230: 46,
        5240: 48,
        5260: 52,
        5280: 56,
        5300: 60,
        5320: 64,
        5500: 100,
        5520: 104,
        5540: 108,
        5560: 112,
        5580: 116,
        # 120, 124, 128 valid in Europe/Japan.
        5600: 120,
        5620: 124,
        5640: 128,
        # 132+ valid in US.
        5660: 132,
        5680: 136,
        5700: 140,
        # 144 is supported by a subset of WiFi chips
        # (e.g. bcm4354, but not ath9k).
        5720: 144,
        5745: 149,
        5765: 153,
        5785: 157,
        5805: 161,
        5825: 165
    }

    MODE_11A = 'a'
    MODE_11B = 'b'
    MODE_11G = 'g'
    MODE_11N_MIXED = 'n-mixed'
    MODE_11N_PURE = 'n-only'
    MODE_11AC_MIXED = 'ac-mixed'
    MODE_11AC_PURE = 'ac-only'

    N_CAPABILITY_HT20 = object()
    N_CAPABILITY_HT40 = object()
    N_CAPABILITY_HT40_PLUS = object()
    N_CAPABILITY_HT40_MINUS = object()
    N_CAPABILITY_GREENFIELD = object()
    N_CAPABILITY_SGI20 = object()
    N_CAPABILITY_SGI40 = object()
    ALL_N_CAPABILITIES = [N_CAPABILITY_HT20,
                          N_CAPABILITY_HT40,
                          N_CAPABILITY_HT40_PLUS,
                          N_CAPABILITY_HT40_MINUS,
                          N_CAPABILITY_GREENFIELD,
                          N_CAPABILITY_SGI20,
                          N_CAPABILITY_SGI40] # yapf: disable

    AC_CAPABILITY_VHT160 = object()
    AC_CAPABILITY_VHT160_80PLUS80 = object()
    AC_CAPABILITY_RXLDPC = object()
    AC_CAPABILITY_SHORT_GI_80 = object()
    AC_CAPABILITY_SHORT_GI_160 = object()
    AC_CAPABILITY_TX_STBC_2BY1 = object()
    AC_CAPABILITY_RX_STBC_1 = object()
    AC_CAPABILITY_RX_STBC_12 = object()
    AC_CAPABILITY_RX_STBC_123 = object()
    AC_CAPABILITY_RX_STBC_1234 = object()
    AC_CAPABILITY_SU_BEAMFORMER = object()
    AC_CAPABILITY_SU_BEAMFORMEE = object()
    AC_CAPABILITY_BF_ANTENNA_2 = object()
    AC_CAPABILITY_SOUNDING_DIMENSION_2 = object()
    AC_CAPABILITY_MU_BEAMFORMER = object()
    AC_CAPABILITY_MU_BEAMFORMEE = object()
    AC_CAPABILITY_VHT_TXOP_PS = object()
    AC_CAPABILITY_HTC_VHT = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP0 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP1 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP2 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP3 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP4 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP5 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP6 = object()
    AC_CAPABILITY_MAX_A_MPDU_LEN_EXP7 = object()
    AC_CAPABILITY_VHT_LINK_ADAPT2 = object()
    AC_CAPABILITY_VHT_LINK_ADAPT3 = object()
    AC_CAPABILITY_RX_ANTENNA_PATTERN = object()
    AC_CAPABILITY_TX_ANTENNA_PATTERN = object()
    AC_CAPABILITIES_MAPPING = {
        AC_CAPABILITY_VHT160: '[VHT160]',
        AC_CAPABILITY_VHT160_80PLUS80: '[VHT160_80PLUS80]',
        AC_CAPABILITY_RXLDPC: '[RXLDPC]',
        AC_CAPABILITY_SHORT_GI_80: '[SHORT_GI_80]',
        AC_CAPABILITY_SHORT_GI_160: '[SHORT_GI_160]',
        AC_CAPABILITY_TX_STBC_2BY1: '[TX_STBC_2BY1',
        AC_CAPABILITY_RX_STBC_1: '[RX_STBC_1]',
        AC_CAPABILITY_RX_STBC_12: '[RX_STBC_12]',
        AC_CAPABILITY_RX_STBC_123: '[RX_STBC_123]',
        AC_CAPABILITY_RX_STBC_1234: '[RX_STBC_1234]',
        AC_CAPABILITY_SU_BEAMFORMER: '[SU_BEAMFORMER]',
        AC_CAPABILITY_SU_BEAMFORMEE: '[SU_BEAMFORMEE]',
        AC_CAPABILITY_BF_ANTENNA_2: '[BF_ANTENNA_2]',
        AC_CAPABILITY_SOUNDING_DIMENSION_2: '[SOUNDING_DIMENSION_2]',
        AC_CAPABILITY_MU_BEAMFORMER: '[MU_BEAMFORMER]',
        AC_CAPABILITY_MU_BEAMFORMEE: '[MU_BEAMFORMEE]',
        AC_CAPABILITY_VHT_TXOP_PS: '[VHT_TXOP_PS]',
        AC_CAPABILITY_HTC_VHT: '[HTC_VHT]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP0: '[MAX_A_MPDU_LEN_EXP0]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP1: '[MAX_A_MPDU_LEN_EXP1]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP2: '[MAX_A_MPDU_LEN_EXP2]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP3: '[MAX_A_MPDU_LEN_EXP3]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP4: '[MAX_A_MPDU_LEN_EXP4]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP5: '[MAX_A_MPDU_LEN_EXP5]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP6: '[MAX_A_MPDU_LEN_EXP6]',
        AC_CAPABILITY_MAX_A_MPDU_LEN_EXP7: '[MAX_A_MPDU_LEN_EXP7]',
        AC_CAPABILITY_VHT_LINK_ADAPT2: '[VHT_LINK_ADAPT2]',
        AC_CAPABILITY_VHT_LINK_ADAPT3: '[VHT_LINK_ADAPT3]',
        AC_CAPABILITY_RX_ANTENNA_PATTERN: '[RX_ANTENNA_PATTERN]',
        AC_CAPABILITY_TX_ANTENNA_PATTERN: '[TX_ANTENNA_PATTERN]'
    }

    VHT_CHANNEL_WIDTH_40 = object()
    VHT_CHANNEL_WIDTH_80 = object()
    VHT_CHANNEL_WIDTH_160 = object()
    VHT_CHANNEL_WIDTH_80_80 = object()

    # This is a loose merging of the rules for US and EU regulatory
    # domains as taken from IEEE Std 802.11-2012 Appendix E.  For instance,
    # we tolerate HT40 in channels 149-161 (not allowed in EU), but also
    # tolerate HT40+ on channel 7 (not allowed in the US).  We take the loose
    # definition so that we don't prohibit testing in either domain.
    HT40_ALLOW_MAP = {
        N_CAPABILITY_HT40_MINUS: tuple(
            itertools.chain(
                range(6, 14), range(40, 65, 8), range(104, 137, 8), [153, 161
                                                                     ])),
        N_CAPABILITY_HT40_PLUS: tuple(
            itertools.chain(
                range(1, 8), range(36, 61, 8), range(100, 133, 8), [149, 157]))
    }

    PMF_SUPPORT_DISABLED = 0
    PMF_SUPPORT_ENABLED = 1
    PMF_SUPPORT_REQUIRED = 2
    PMF_SUPPORT_VALUES = (PMF_SUPPORT_DISABLED, PMF_SUPPORT_ENABLED,
                          PMF_SUPPORT_REQUIRED)

    DRIVER_NAME = 'nl80211'

    @staticmethod
    def get_channel_for_frequency(frequency):
        """The channel number associated with a given frequency.

        Args:
            value: int frequency in MHz.

        Returns:
            int, frequency associated with the channel.

        """
        return HostapdConfig.CHANNEL_MAP[frequency]

    @staticmethod
    def get_frequency_for_channel(channel):
        """The frequency associated with a given channel number.

        Args:
            value: int channel number.

        Returns:
            int, frequency in MHz associated with the channel.

        """
        for frequency, channel_iter in \
            HostapdConfig.CHANNEL_MAP.items():
            if channel == channel_iter:
                return frequency
        else:
            raise ValueError('Unknown channel value: %r.' % channel)

    @property
    def _get_default_config(self):
        """Returns: dict of default options for hostapd."""
        return collections.OrderedDict([
            ('logger_syslog', '-1'),
            ('logger_syslog_level', '0'),
            # default RTS and frag threshold to ``off''
            ('rts_threshold', '2347'),
            ('fragm_threshold', '2346'),
            ('driver', self.DRIVER_NAME)
        ])

    @property
    def _ht40_plus_allowed(self):
        """Returns: True iff HT40+ is enabled for this configuration."""
        channel_supported = (
            self.channel in self.HT40_ALLOW_MAP[self.N_CAPABILITY_HT40_PLUS])
        return ((self.N_CAPABILITY_HT40_PLUS in self._n_capabilities or
                 self.N_CAPABILITY_HT40 in self._n_capabilities) and
                channel_supported)

    @property
    def _ht40_minus_allowed(self):
        """Returns: True iff HT40- is enabled for this configuration."""
        channel_supported = (
            self.channel in self.HT40_ALLOW_MAP[self.N_CAPABILITY_HT40_MINUS])
        return ((self.N_CAPABILITY_HT40_MINUS in self._n_capabilities or
                 self.N_CAPABILITY_HT40 in self._n_capabilities) and
                channel_supported)

    @property
    def _hostapd_ht_capabilities(self):
        """Returns: string suitable for the ht_capab= line in a hostapd config"""
        ret = []
        if self._ht40_plus_allowed:
            ret.append('[HT40+]')
        elif self._ht40_minus_allowed:
            ret.append('[HT40-]')
        if self.N_CAPABILITY_GREENFIELD in self._n_capabilities:
            logging.warning('Greenfield flag is ignored for hostap...')
        if self.N_CAPABILITY_SGI20 in self._n_capabilities:
            ret.append('[SHORT-GI-20]')
        if self.N_CAPABILITY_SGI40 in self._n_capabilities:
            ret.append('[SHORT-GI-40]')
        return ''.join(ret)

    @property
    def _hostapd_vht_capabilities(self):
        """Returns: string suitable for the vht_capab= line in a hostapd config.
        """
        ret = []
        for cap in self.AC_CAPABILITIES_MAPPING.keys():
            if cap in self._ac_capabilities:
                ret.append(self.AC_CAPABILITIES_MAPPING[cap])
        return ''.join(ret)

    @property
    def _require_ht(self):
        """Returns: True iff clients should be required to support HT."""
        # TODO(wiley) Why? (crbug.com/237370)
        # DOES THIS APPLY TO US?
        logging.warning('Not enforcing pure N mode because Snow does '
                        'not seem to support it...')
        return False

    @property
    def _require_vht(self):
        """Returns: True if clients should be required to support VHT."""
        return self._mode == self.MODE_11AC_PURE

    @property
    def hw_mode(self):
        """Returns: string hardware mode understood by hostapd."""
        if self._mode == self.MODE_11A:
            return self.MODE_11A
        if self._mode == self.MODE_11B:
            return self.MODE_11B
        if self._mode == self.MODE_11G:
            return self.MODE_11G
        if self.is_11n or self.is_11ac:
            # For their own historical reasons, hostapd wants it this way.
            if self._frequency > 5000:
                return self.MODE_11A

            return self.MODE_11G

        raise ValueError('Invalid mode.')

    @property
    def is_11n(self):
        """Returns: True if we're trying to host an 802.11n network."""
        return self._mode in (self.MODE_11N_MIXED, self.MODE_11N_PURE)

    @property
    def is_11ac(self):
        """Returns: True if we're trying to host an 802.11ac network."""
        return self._mode in (self.MODE_11AC_MIXED, self.MODE_11AC_PURE)

    @property
    def channel(self):
        """Returns: int channel number for self.frequency."""
        return self.get_channel_for_frequency(self.frequency)

    @channel.setter
    def channel(self, value):
        """Sets the channel number to configure hostapd to listen on.

        Args:
            value: int, channel number.

        """
        self.frequency = self.get_frequency_for_channel(value)

    @property
    def bssid(self):
        return self._bssid

    @bssid.setter
    def bssid(self, value):
        self._bssid = value

    @property
    def frequency(self):
        """Returns: int, frequency for hostapd to listen on."""
        return self._frequency

    @frequency.setter
    def frequency(self, value):
        """Sets the frequency for hostapd to listen on.

        Args:
            value: int, frequency in MHz.

        """
        if value not in self.CHANNEL_MAP or not self.supports_frequency(value):
            raise ValueError('Tried to set an invalid frequency: %r.' % value)

        self._frequency = value

    @property
    def bss_lookup(self):
        return self._bss_lookup

    @property
    def ssid(self):
        """Returns: SsidSettings, The root Ssid settings being used."""
        return self._ssid

    @ssid.setter
    def ssid(self, value):
        """Sets the ssid for the hostapd.

        Args:
            value: SsidSettings, new ssid settings to use.

        """
        self._ssid = value

    @property
    def hidden(self):
        """Returns: bool, True if the ssid is hidden, false otherwise."""
        return self._hidden

    @hidden.setter
    def hidden(self, value):
        """Sets if this ssid is hidden.

        Args:
            value: bool, If true the ssid will be hidden.
        """
        self.hidden = value

    @property
    def security(self):
        """Returns: The security type being used."""
        return self._security

    @security.setter
    def security(self, value):
        """Sets the security options to use.

        Args:
            value: Security, The type of security to use.
        """
        self._security = value

    @property
    def ht_packet_capture_mode(self):
        """Get an appropriate packet capture HT parameter.

        When we go to configure a raw monitor we need to configure
        the phy to listen on the correct channel.  Part of doing
        so is to specify the channel width for HT channels.  In the
        case that the AP is configured to be either HT40+ or HT40-,
        we could return the wrong parameter because we don't know which
        configuration will be chosen by hostap.

        Returns:
            string, HT parameter for frequency configuration.

        """
        if not self.is_11n:
            return None

        if self._ht40_plus_allowed:
            return 'HT40+'

        if self._ht40_minus_allowed:
            return 'HT40-'

        return 'HT20'

    @property
    def beacon_footer(self):
        """Returns: bool _beacon_footer value."""
        return self._beacon_footer

    def beacon_footer(self, value):
        """Changes the beacon footer.

        Args:
            value: bool, The beacon footer vlaue.
        """
        self._beacon_footer = value

    @property
    def scenario_name(self):
        """Returns: string _scenario_name value, or None."""
        return self._scenario_name

    @property
    def min_streams(self):
        """Returns: int, _min_streams value, or None."""
        return self._min_streams

    def __init__(self,
                 mode=MODE_11B,
                 channel=None,
                 frequency=None,
                 n_capabilities=[],
                 beacon_interval=None,
                 dtim_period=None,
                 frag_threshold=None,
                 ssid=None,
                 hidden=False,
                 security=None,
                 bssid=None,
                 force_wmm=None,
                 pmf_support=PMF_SUPPORT_DISABLED,
                 obss_interval=None,
                 vht_channel_width=None,
                 vht_center_channel=None,
                 ac_capabilities=[],
                 beacon_footer='',
                 spectrum_mgmt_required=None,
                 scenario_name=None,
                 min_streams=None,
                 bss_settings=[]):
        """Construct a HostapdConfig.

        You may specify channel or frequency, but not both.  Both options
        are checked for validity (i.e. you can't specify an invalid channel
        or a frequency that will not be accepted).

        Args:
            interface: string, The name of the interface to use.
            mode: string, MODE_11x defined above.
            channel: int, channel number.
            frequency: int, frequency of channel.
            n_capabilities: list of N_CAPABILITY_x defined above.
            beacon_interval: int, beacon interval of AP.
            dtim_period: int, include a DTIM every |dtim_period| beacons.
            frag_threshold: int, maximum outgoing data frame size.
            ssid: string, The name of the ssid to brodcast.
            hidden: bool, Should the ssid be hidden.
            security: Security, the secuirty settings to use.
            bssid: string, a MAC address like string for the BSSID.
            force_wmm: True if we should force WMM on, False if we should
                force it off, None if we shouldn't force anything.
            pmf_support: one of PMF_SUPPORT_* above.  Controls whether the
                client supports/must support 802.11w.
            obss_interval: int, interval in seconds that client should be
                required to do background scans for overlapping BSSes.
            vht_channel_width: object channel width
            vht_center_channel: int, center channel of segment 0.
            ac_capabilities: list of AC_CAPABILITY_x defined above.
            beacon_footer: string, containing (unvalidated) IE data to be
                placed at the end of the beacon.
            spectrum_mgmt_required: True if we require the DUT to support
                spectrum management.
            scenario_name: string to be included in file names, instead
                of the interface name.
            min_streams: int, number of spatial streams required.
            control_interface: The file name to use as the control interface.
            bss_settings: The settings for all bss.
        """
        if channel is not None and frequency is not None:
            raise ValueError('Specify either frequency or channel '
                             'but not both.')

        self._wmm_enabled = False
        unknown_caps = [
            cap for cap in n_capabilities if cap not in self.ALL_N_CAPABILITIES
        ]
        if unknown_caps:
            raise ValueError('Unknown capabilities: %r' % unknown_caps)

        self._n_capabilities = set(n_capabilities)
        if self._n_capabilities:
            self._wmm_enabled = True
        if self._n_capabilities and mode is None:
            mode = self.MODE_11N_PURE
        self._mode = mode

        self._frequency = None
        if channel:
            self.channel = channel
        elif frequency:
            self.frequency = frequency
        else:
            raise ValueError('Specify either frequency or channel.')

        if not self.supports_frequency(self.frequency):
            raise ValueError('Configured a mode %s that does not support '
                             'frequency %d' % (self._mode, self.frequency))

        self._beacon_interval = beacon_interval
        self._dtim_period = dtim_period
        self._frag_threshold = frag_threshold

        self._ssid = ssid
        self._hidden = hidden
        self._security = security
        self._bssid = bssid
        if force_wmm is not None:
            self._wmm_enabled = force_wmm
        if pmf_support not in self.PMF_SUPPORT_VALUES:
            raise ValueError('Invalid value for pmf_support: %r' % pmf_support)

        self._pmf_support = pmf_support
        self._obss_interval = obss_interval
        if vht_channel_width == self.VHT_CHANNEL_WIDTH_40:
            self._vht_oper_chwidth = 0
        elif vht_channel_width == self.VHT_CHANNEL_WIDTH_80:
            self._vht_oper_chwidth = 1
        elif vht_channel_width == self.VHT_CHANNEL_WIDTH_160:
            self._vht_oper_chwidth = 2
        elif vht_channel_width == self.VHT_CHANNEL_WIDTH_80_80:
            self._vht_oper_chwidth = 3
        elif vht_channel_width is not None:
            raise ValueError('Invalid channel width')
        # TODO(zqiu) Add checking for center channel based on the channel width
        # and operating channel.
        self._vht_oper_centr_freq_seg0_idx = vht_center_channel
        self._ac_capabilities = set(ac_capabilities)
        self._beacon_footer = beacon_footer
        self._spectrum_mgmt_required = spectrum_mgmt_required
        self._scenario_name = scenario_name
        self._min_streams = min_streams

        self._bss_lookup = {}
        for bss in bss_settings:
            if bss.name in self._bss_lookup:
                raise ValueError('Cannot have multiple bss settings with the'
                                 ' same name.')
            self._bss_lookup[bss.name] = bss

    def __repr__(self):
        return (
            '%s(mode=%r, channel=%r, frequency=%r, '
            'n_capabilities=%r, beacon_interval=%r, '
            'dtim_period=%r, frag_threshold=%r, ssid=%r, bssid=%r, '
            'wmm_enabled=%r, security_config=%r, '
            'spectrum_mgmt_required=%r)' %
            (self.__class__.__name__, self._mode, self.channel, self.frequency,
             self._n_capabilities, self._beacon_interval, self._dtim_period,
             self._frag_threshold, self._ssid, self._bssid, self._wmm_enabled,
             self._security, self._spectrum_mgmt_required))

    def supports_channel(self, value):
        """Check whether channel is supported by the current hardware mode.

        @param value: int channel to check.
        @return True iff the current mode supports the band of the channel.

        """
        for freq, channel in self.CHANNEL_MAP.iteritems():
            if channel == value:
                return self.supports_frequency(freq)

        return False

    def supports_frequency(self, frequency):
        """Check whether frequency is supported by the current hardware mode.

        @param frequency: int frequency to check.
        @return True iff the current mode supports the band of the frequency.

        """
        if self._mode == self.MODE_11A and frequency < 5000:
            return False

        if self._mode in (self.MODE_11B, self.MODE_11G) and frequency > 5000:
            return False

        if frequency not in self.CHANNEL_MAP:
            return False

        channel = self.CHANNEL_MAP[frequency]
        supports_plus = (
            channel in self.HT40_ALLOW_MAP[self.N_CAPABILITY_HT40_PLUS])
        supports_minus = (
            channel in self.HT40_ALLOW_MAP[self.N_CAPABILITY_HT40_MINUS])
        if (self.N_CAPABILITY_HT40_PLUS in self._n_capabilities and
                not supports_plus):
            return False

        if (self.N_CAPABILITY_HT40_MINUS in self._n_capabilities and
                not supports_minus):
            return False

        if (self.N_CAPABILITY_HT40 in self._n_capabilities and
                not supports_plus and not supports_minus):
            return False

        return True

    def add_bss(self, bss):
        """Adds a new bss setting.

        Args:
            bss: The bss settings to add.
        """
        if bss.name in self._bss_lookup:
            raise ValueError('A bss with the same name already exists.')

        self._bss_lookup[bss.name] = bss

    def remove_bss(self, bss_name):
        """Removes a bss setting from the config."""
        del self._bss_lookup[bss_name]

    def package_configs(self):
        """Package the configs.

        Returns:
            A list of dictionaries, one dictionary for each section of the
            config.
        """
        # Start with the default config parameters.
        conf = self._get_default_config
        if self._bssid:
            conf['bssid'] = self._bssid
        if self._ssid:
            conf['ssid'] = self._ssid
            conf['ignore_broadcast_ssid'] = 1 if self._hidden else 0
        conf['channel'] = self.channel
        conf['hw_mode'] = self.hw_mode
        if self.is_11n or self.is_11ac:
            conf['ieee80211n'] = 1
            conf['ht_capab'] = self._hostapd_ht_capabilities
        if self.is_11ac:
            conf['ieee80211ac'] = 1
            conf['vht_oper_chwidth'] = self._vht_oper_chwidth
            conf['vht_oper_centr_freq_seg0_idx'] = \
                    self._vht_oper_centr_freq_seg0_idx
            conf['vht_capab'] = self._hostapd_vht_capabilities
        if self._wmm_enabled:
            conf['wmm_enabled'] = 1
        if self._require_ht:
            conf['require_ht'] = 1
        if self._require_vht:
            conf['require_vht'] = 1
        if self._beacon_interval:
            conf['beacon_int'] = self._beacon_interval
        if self._dtim_period:
            conf['dtim_period'] = self._dtim_period
        if self._frag_threshold:
            conf['fragm_threshold'] = self._frag_threshold
        if self._pmf_support:
            conf['ieee80211w'] = self._pmf_support
        if self._obss_interval:
            conf['obss_interval'] = self._obss_interval
        if self._spectrum_mgmt_required:
            # To set spectrum_mgmt_required, we must first set
            # local_pwr_constraint. And to set local_pwr_constraint,
            # we must first set ieee80211d. And to set ieee80211d, ...
            # Point being: order matters here.
            conf['country_code'] = 'US'  # Required for local_pwr_constraint
            conf['ieee80211d'] = 1  # Required for local_pwr_constraint
            conf['local_pwr_constraint'] = 0  # No local constraint
            conf['spectrum_mgmt_required'] = 1  # Requires local_pwr_constraint

        if self._security:
            for k, v in self._security.generate_dict().items():
                conf[k] = v

        all_conf = [conf]

        for bss in self._bss_lookup.values():
            bss_conf = collections.OrderedDict()
            for k, v in (bss.generate_dict()).items():
                bss_conf[k] = v
            all_conf.append(bss_conf)

        return all_conf
