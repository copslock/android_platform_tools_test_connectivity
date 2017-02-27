#!/usr/bin/env python3.4
#
#   Copyright 2016 Google, Inc.
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

import logging
import time
import pprint

from enum import IntEnum
from queue import Empty

from acts import asserts
from acts import signals
from acts import utils
from acts.controllers import attenuator
from acts.test_utils.wifi import wifi_constants
from acts.test_utils.tel import tel_defines

# Number of seconds to wait for events that are supposed to happen quickly.
# Like onSuccess for start background scan and confirmation on wifi state
# change.
SHORT_TIMEOUT = 30

# The currently supported devices that existed before release
#TODO: (navtejsingh) Need to clean up the below lists going forward
K_DEVICES = ["hammerhead", "razor", "razorg"]
L_DEVICES = ["shamu", "ryu"]
L_TAP_DEVICES = ["volantis", "volantisg"]
M_DEVICES = ["angler"]

# Speed of light in m/s.
SPEED_OF_LIGHT = 299792458

DEFAULT_PING_ADDR = "http://www.google.com/robots.txt"


class WifiEnums():

    SSID_KEY = "SSID"
    BSSID_KEY = "BSSID"
    PWD_KEY = "password"
    frequency_key = "frequency"
    APBAND_KEY = "apBand"

    WIFI_CONFIG_APBAND_2G = 0
    WIFI_CONFIG_APBAND_5G = 1

    WIFI_WPS_INFO_PBC = 0
    WIFI_WPS_INFO_DISPLAY = 1
    WIFI_WPS_INFO_KEYPAD = 2
    WIFI_WPS_INFO_LABEL = 3
    WIFI_WPS_INFO_INVALID = 4

    class CountryCode():
        CHINA = "CN"
        JAPAN = "JP"
        UK = "GB"
        US = "US"
        UNKNOWN = "UNKNOWN"

    # Start of Macros for EAP
    # EAP types
    class Eap(IntEnum):
        NONE = -1
        PEAP = 0
        TLS = 1
        TTLS = 2
        PWD = 3
        SIM = 4
        AKA = 5
        AKA_PRIME = 6
        UNAUTH_TLS = 7

    # EAP Phase2 types
    class EapPhase2(IntEnum):
        NONE = 0
        PAP = 1
        MSCHAP = 2
        MSCHAPV2 = 3
        GTC = 4

    class Enterprise:
        # Enterprise Config Macros
        EMPTY_VALUE = "NULL"
        EAP = "eap"
        PHASE2 = "phase2"
        IDENTITY = "identity"
        ANON_IDENTITY = "anonymous_identity"
        PASSWORD = "password"
        SUBJECT_MATCH = "subject_match"
        ALTSUBJECT_MATCH = "altsubject_match"
        DOM_SUFFIX_MATCH = "domain_suffix_match"
        CLIENT_CERT = "client_cert"
        CA_CERT = "ca_cert"
        ENGINE = "engine"
        ENGINE_ID = "engine_id"
        PRIVATE_KEY_ID = "key_id"
        REALM = "realm"
        PLMN = "plmn"
        FQDN = "FQDN"
        FRIENDLY_NAME = "providerFriendlyName"
        ROAMING_IDS = "roamingConsortiumIds"
    # End of Macros for EAP

    # Macros for wifi p2p.
    WIFI_P2P_SERVICE_TYPE_ALL = 0
    WIFI_P2P_SERVICE_TYPE_BONJOUR = 1
    WIFI_P2P_SERVICE_TYPE_UPNP = 2
    WIFI_P2P_SERVICE_TYPE_VENDOR_SPECIFIC = 255

    class ScanResult:
        CHANNEL_WIDTH_20MHZ = 0
        CHANNEL_WIDTH_40MHZ = 1
        CHANNEL_WIDTH_80MHZ = 2
        CHANNEL_WIDTH_160MHZ = 3
        CHANNEL_WIDTH_80MHZ_PLUS_MHZ = 4

    # Macros for wifi rtt.
    class RttType(IntEnum):
        TYPE_ONE_SIDED = 1
        TYPE_TWO_SIDED = 2

    class RttPeerType(IntEnum):
        PEER_TYPE_AP = 1
        PEER_TYPE_STA = 2  # Requires NAN.
        PEER_P2P_GO = 3
        PEER_P2P_CLIENT = 4
        PEER_NAN = 5

    class RttPreamble(IntEnum):
        PREAMBLE_LEGACY = 0x01
        PREAMBLE_HT = 0x02
        PREAMBLE_VHT = 0x04

    class RttBW(IntEnum):
        BW_5_SUPPORT = 0x01
        BW_10_SUPPORT = 0x02
        BW_20_SUPPORT = 0x04
        BW_40_SUPPORT = 0x08
        BW_80_SUPPORT = 0x10
        BW_160_SUPPORT = 0x20

    class Rtt(IntEnum):
        STATUS_SUCCESS = 0
        STATUS_FAILURE = 1
        STATUS_FAIL_NO_RSP = 2
        STATUS_FAIL_REJECTED = 3
        STATUS_FAIL_NOT_SCHEDULED_YET = 4
        STATUS_FAIL_TM_TIMEOUT = 5
        STATUS_FAIL_AP_ON_DIFF_CHANNEL = 6
        STATUS_FAIL_NO_CAPABILITY = 7
        STATUS_ABORTED = 8
        STATUS_FAIL_INVALID_TS = 9
        STATUS_FAIL_PROTOCOL = 10
        STATUS_FAIL_SCHEDULE = 11
        STATUS_FAIL_BUSY_TRY_LATER = 12
        STATUS_INVALID_REQ = 13
        STATUS_NO_WIFI = 14
        STATUS_FAIL_FTM_PARAM_OVERRIDE = 15

        REASON_UNSPECIFIED = -1
        REASON_NOT_AVAILABLE = -2
        REASON_INVALID_LISTENER = -3
        REASON_INVALID_REQUEST = -4

    class RttParam:
        device_type = "deviceType"
        request_type = "requestType"
        BSSID = "bssid"
        channel_width = "channelWidth"
        frequency = "frequency"
        center_freq0 = "centerFreq0"
        center_freq1 = "centerFreq1"
        number_burst = "numberBurst"
        interval = "interval"
        num_samples_per_burst = "numSamplesPerBurst"
        num_retries_per_measurement_frame = "numRetriesPerMeasurementFrame"
        num_retries_per_FTMR = "numRetriesPerFTMR"
        lci_request = "LCIRequest"
        lcr_request = "LCRRequest"
        burst_timeout = "burstTimeout"
        preamble = "preamble"
        bandwidth = "bandwidth"
        margin = "margin"

    RTT_MARGIN_OF_ERROR = {
        RttBW.BW_80_SUPPORT: 2,
        RttBW.BW_40_SUPPORT: 5,
        RttBW.BW_20_SUPPORT: 5
    }

    # Macros as specified in the WifiScanner code.
    WIFI_BAND_UNSPECIFIED = 0  # not specified
    WIFI_BAND_24_GHZ = 1  # 2.4 GHz band
    WIFI_BAND_5_GHZ = 2  # 5 GHz band without DFS channels
    WIFI_BAND_5_GHZ_DFS_ONLY = 4  # 5 GHz band with DFS channels
    WIFI_BAND_5_GHZ_WITH_DFS = 6  # 5 GHz band with DFS channels
    WIFI_BAND_BOTH = 3  # both bands without DFS channels
    WIFI_BAND_BOTH_WITH_DFS = 7  # both bands with DFS channels

    REPORT_EVENT_AFTER_BUFFER_FULL = 0
    REPORT_EVENT_AFTER_EACH_SCAN = 1
    REPORT_EVENT_FULL_SCAN_RESULT = 2

    # US Wifi frequencies
    ALL_2G_FREQUENCIES = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452,
                          2457, 2462]
    DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520, 5540, 5560, 5580,
                          5600, 5620, 5640, 5660, 5680, 5700, 5720]
    NONE_DFS_5G_FREQUENCIES = [5180, 5200, 5220, 5240, 5745, 5765, 5785, 5805,
                               5825]
    ALL_5G_FREQUENCIES = DFS_5G_FREQUENCIES + NONE_DFS_5G_FREQUENCIES

    band_to_frequencies = {
        WIFI_BAND_24_GHZ: ALL_2G_FREQUENCIES,
        WIFI_BAND_5_GHZ: NONE_DFS_5G_FREQUENCIES,
        WIFI_BAND_5_GHZ_DFS_ONLY: DFS_5G_FREQUENCIES,
        WIFI_BAND_5_GHZ_WITH_DFS: ALL_5G_FREQUENCIES,
        WIFI_BAND_BOTH: ALL_2G_FREQUENCIES + NONE_DFS_5G_FREQUENCIES,
        WIFI_BAND_BOTH_WITH_DFS: ALL_5G_FREQUENCIES + ALL_2G_FREQUENCIES
    }

    # All Wifi frequencies to channels lookup.
    freq_to_channel = {
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
        2467: 12,
        2472: 13,
        2484: 14,
        4915: 183,
        4920: 184,
        4925: 185,
        4935: 187,
        4940: 188,
        4945: 189,
        4960: 192,
        4980: 196,
        5035: 7,
        5040: 8,
        5045: 9,
        5055: 11,
        5060: 12,
        5080: 16,
        5170: 34,
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
        5600: 120,
        5620: 124,
        5640: 128,
        5660: 132,
        5680: 136,
        5700: 140,
        5745: 149,
        5765: 153,
        5785: 157,
        5805: 161,
        5825: 165,
    }

    # All Wifi channels to frequencies lookup.
    channel_2G_to_freq = {
        1: 2412,
        2: 2417,
        3: 2422,
        4: 2427,
        5: 2432,
        6: 2437,
        7: 2442,
        8: 2447,
        9: 2452,
        10: 2457,
        11: 2462,
        12: 2467,
        13: 2472,
        14: 2484
    }

    channel_5G_to_freq = {
        183: 4915,
        184: 4920,
        185: 4925,
        187: 4935,
        188: 4940,
        189: 4945,
        192: 4960,
        196: 4980,
        7: 5035,
        8: 5040,
        9: 5045,
        11: 5055,
        12: 5060,
        16: 5080,
        34: 5170,
        36: 5180,
        38: 5190,
        40: 5200,
        42: 5210,
        44: 5220,
        46: 5230,
        48: 5240,
        52: 5260,
        56: 5280,
        60: 5300,
        64: 5320,
        100: 5500,
        104: 5520,
        108: 5540,
        112: 5560,
        116: 5580,
        120: 5600,
        124: 5620,
        128: 5640,
        132: 5660,
        136: 5680,
        140: 5700,
        149: 5745,
        153: 5765,
        157: 5785,
        161: 5805,
        165: 5825
    }


class WifiChannelBase:
    ALL_2G_FREQUENCIES = []
    DFS_5G_FREQUENCIES = []
    NONE_DFS_5G_FREQUENCIES = []
    ALL_5G_FREQUENCIES = DFS_5G_FREQUENCIES + NONE_DFS_5G_FREQUENCIES
    MIX_CHANNEL_SCAN = []

    def band_to_freq(self, band):
        _band_to_frequencies = {
            WifiEnums.WIFI_BAND_24_GHZ: self.ALL_2G_FREQUENCIES,
            WifiEnums.WIFI_BAND_5_GHZ: self.NONE_DFS_5G_FREQUENCIES,
            WifiEnums.WIFI_BAND_5_GHZ_DFS_ONLY: self.DFS_5G_FREQUENCIES,
            WifiEnums.WIFI_BAND_5_GHZ_WITH_DFS: self.ALL_5G_FREQUENCIES,
            WifiEnums.WIFI_BAND_BOTH:
            self.ALL_2G_FREQUENCIES + self.NONE_DFS_5G_FREQUENCIES,
            WifiEnums.WIFI_BAND_BOTH_WITH_DFS:
            self.ALL_5G_FREQUENCIES + self.ALL_2G_FREQUENCIES
        }
        return _band_to_frequencies[band]


class WifiChannelUS(WifiChannelBase):
    # US Wifi frequencies
    ALL_2G_FREQUENCIES = [2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452,
                          2457, 2462]
    NONE_DFS_5G_FREQUENCIES = [5180, 5200, 5220, 5240, 5745, 5765, 5785, 5805,
                               5825]
    MIX_CHANNEL_SCAN = [2412, 2437, 2462, 5180, 5200, 5280, 5260, 5300, 5500,
                        5320, 5520, 5560, 5700, 5745, 5805]

    def __init__(self, model=None):
        if model and utils.trim_model_name(model) in K_DEVICES:
            self.DFS_5G_FREQUENCIES = []
            self.ALL_5G_FREQUENCIES = self.NONE_DFS_5G_FREQUENCIES
            self.MIX_CHANNEL_SCAN = [2412, 2437, 2462, 5180, 5200, 5240, 5745,
                                     5765]
        elif model and utils.trim_model_name(model) in L_DEVICES:
            self.DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520,
                                       5540, 5560, 5580, 5660, 5680, 5700]
            self.ALL_5G_FREQUENCIES = self.DFS_5G_FREQUENCIES + self.NONE_DFS_5G_FREQUENCIES
        elif model and utils.trim_model_name(model) in L_TAP_DEVICES:
            self.DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520,
                                       5540, 5560, 5580, 5660, 5680, 5700,
                                       5720]
            self.ALL_5G_FREQUENCIES = self.DFS_5G_FREQUENCIES + self.NONE_DFS_5G_FREQUENCIES
        elif model and utils.trim_model_name(model) in M_DEVICES:
            self.DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520,
                                       5540, 5560, 5580, 5600, 5620, 5640,
                                       5660, 5680, 5700]
            self.ALL_5G_FREQUENCIES = self.DFS_5G_FREQUENCIES + self.NONE_DFS_5G_FREQUENCIES
        else:
            self.DFS_5G_FREQUENCIES = [5260, 5280, 5300, 5320, 5500, 5520,
                                       5540, 5560, 5580, 5600, 5620, 5640,
                                       5660, 5680, 5700, 5720]
            self.ALL_5G_FREQUENCIES = self.DFS_5G_FREQUENCIES + self.NONE_DFS_5G_FREQUENCIES


def _assert_on_fail_handler(func, assert_on_fail, *args, **kwargs):
    """Wrapper function that handles the bahevior of assert_on_fail.

    When assert_on_fail is True, let all test signals through, which can
    terminate test cases directly. When assert_on_fail is False, the wrapper
    raises no test signals and reports operation status by returning True or
    False.

    Args:
        func: The function to wrap. This function reports operation status by
              raising test signals.
        assert_on_fail: A boolean that specifies if the output of the wrapper
                        is test signal based or return value based.
        args: Positional args for func.
        kwargs: Name args for func.

    Returns:
        If assert_on_fail is True, returns True/False to signal operation
        status, otherwise return nothing.
    """
    try:
        func(*args, **kwargs)
        if not assert_on_fail:
            return True
    except signals.TestSignal:
        if assert_on_fail:
            raise
        return False


def assert_network_in_list(target, network_list):
    """Makes sure a specified target Wi-Fi network exists in a list of Wi-Fi
    networks.

    Args:
        target: A dict representing a Wi-Fi network.
                E.g. {WifiEnums.SSID_KEY: "SomeNetwork"}
        network_list: A list of dicts, each representing a Wi-Fi network.
    """
    match_results = match_networks(target, network_list)
    asserts.assert_true(
        match_results, "Target network %s, does not exist in network list %s" %
        (target, network_list))


def match_networks(target_params, networks):
    """Finds the WiFi networks that match a given set of parameters in a list
    of WiFi networks.

    To be considered a match, the network should contain every key-value pair
    of target_params

    Args:
        target_params: A dict with 1 or more key-value pairs representing a Wi-Fi network.
                       E.g { 'SSID': 'wh_ap1_5g', 'BSSID': '30:b5:c2:33:e4:47' }
        networks: A list of dict objects representing WiFi networks.

    Returns:
        The networks that match the target parameters.
    """
    results = []
    asserts.assert_true(target_params, "Expected networks object 'target_params' is empty")
    for n in networks:
        add_network = 1
        for k, v in target_params.items():
            if k not in n:
                add_network = 0
                break
            if n[k] != v:
                add_network = 0
                break
        if add_network:
            results.append(n)
    return results


def wifi_toggle_state(ad, new_state=None, assert_on_fail=True):
    """Toggles the state of wifi.

    Args:
        ad: An AndroidDevice object.
        new_state: Wifi state to set to. If None, opposite of the current state.
        assert_on_fail: If True, error checks in this function will raise test
                        failure signals.

    Returns:
        If assert_on_fail is False, function returns True if the toggle was
        successful, False otherwise. If assert_on_fail is True, no return value.
    """
    _assert_on_fail_handler(_wifi_toggle_state, assert_on_fail, ad, new_state)


def _wifi_toggle_state(ad, new_state=None):
    """Toggles the state of wifi.

    TestFailure signals are raised when something goes wrong.

    Args:
        ad: An AndroidDevice object.
        new_state: The state to set Wi-Fi to. If None, opposite of the current
                   state will be set.
    """
    if new_state is None:
        new_state = not ad.droid.wifiCheckState()
    elif new_state == ad.droid.wifiCheckState():
        # Check if the new_state is already achieved, so we don't wait for the
        # state change event by mistake.
        return
    ad.droid.wifiStartTrackingStateChange()
    ad.log.info("Setting Wi-Fi state to %s.", new_state)
    # Setting wifi state.
    ad.droid.wifiToggleState(new_state)
    fail_msg = "Failed to set Wi-Fi state to %s on %s." % (new_state,
                                                           ad.serial)
    try:
        event = ad.ed.pop_event(wifi_constants.SUPPLICANT_CON_CHANGED,
                                SHORT_TIMEOUT)
        asserts.assert_equal(event['data']['Connected'], new_state, fail_msg)
    except Empty:
        # Supplicant connection event is not always reliable. We double check
        # here and call it a success as long as the new state equals the
        # expected state.
        time.sleep(5)
        asserts.assert_equal(new_state, ad.droid.wifiCheckState(), fail_msg)
    finally:
        ad.droid.wifiStopTrackingStateChange()


def reset_wifi(ad):
    """Clears all saved Wi-Fi networks on a device.

    This will turn Wi-Fi on.

    Args:
        ad: An AndroidDevice object.

    """
    # TODO(gmoturu): need to remove wifi_toggle_state() in reset_wifi() when
    # bug: 32809235 is fixed
    wifi_toggle_state(ad, True)
    networks = ad.droid.wifiGetConfiguredNetworks()
    if not networks:
        return
    for n in networks:
        ad.droid.wifiForgetNetwork(n['networkId'])
        try:
            event = ad.ed.pop_event(wifi_constants.WIFI_FORGET_NW_SUCCESS,
                                    SHORT_TIMEOUT)
        except Empty:
            logging.warning("Could not confirm the removal of network %s.", n)
    # Check again to see if there's any network left.
    asserts.assert_true(not ad.droid.wifiGetConfiguredNetworks(),
                        "Failed to remove these configured Wi-Fi networks: %s" % networks)


def wifi_forget_network(ad, net_ssid):
    """Remove configured Wifi network on an android device.

    Args:
        ad: android_device object for forget network.
        net_ssid: ssid of network to be forget

    """
    ad.droid.wifiToggleState(True)
    networks = ad.droid.wifiGetConfiguredNetworks()
    if not networks:
        return
    for n in networks:
        if net_ssid in n[WifiEnums.SSID_KEY]:
            ad.droid.wifiForgetNetwork(n['networkId'])
            try:
                event = ad.ed.pop_event(wifi_constants.WIFI_FORGET_NW_SUCCESS,
                                     SHORT_TIMEOUT)
            except Empty:
                asserts.fail("Failed to remove network %s." % n)


def wifi_test_device_init(ad):
    """Initializes an android device for wifi testing.

    0. Make sure SL4A connection is established on the android device.
    1. Disable location service's WiFi scan.
    2. Turn WiFi on.
    3. Clear all saved networks.
    4. Set country code to US.
    5. Enable WiFi verbose logging.
    6. Sync device time with computer time.
    7. Turn off cellular data.
    8. Turn off ambient display.
    """
    utils.require_sl4a((ad, ))
    ad.droid.wifiScannerToggleAlwaysAvailable(False)
    msg = "Failed to turn off location service's scan."
    asserts.assert_true(not ad.droid.wifiScannerIsAlwaysAvailable(), msg)
    wifi_toggle_state(ad, True)
    reset_wifi(ad)
    ad.droid.wifiEnableVerboseLogging(1)
    msg = "Failed to enable WiFi verbose logging."
    asserts.assert_equal(ad.droid.wifiGetVerboseLoggingLevel(), 1, msg)
    # We don't verify the following settings since they are not critical.
    # Set wpa_supplicant log level to EXCESSIVE.
    output = ad.adb.shell("wpa_cli -i wlan0 -p -g@android:wpa_wlan0 IFNAME="
                          "wlan0 log_level EXCESSIVE")
    ad.log.info("wpa_supplicant log change status: %s", output)
    utils.sync_device_time(ad)
    ad.droid.telephonyToggleDataConnection(False)
    # TODO(angli): need to verify the country code was actually set. No generic
    # way to check right now.
    ad.adb.shell("halutil -country %s" % WifiEnums.CountryCode.US)
    utils.set_ambient_display(ad, False)


def start_wifi_connection_scan(ad):
    """Starts a wifi connection scan and wait for results to become available.

    Args:
        ad: An AndroidDevice object.
    """
    ad.droid.wifiStartScan()
    try:
        ad.ed.pop_event("WifiManagerScanResultsAvailable", 60)
    except Empty:
        asserts.fail("Wi-Fi results did not become available within 60s.")


def start_wifi_background_scan(ad, scan_setting):
    """Starts wifi background scan.

    Args:
        ad: android_device object to initiate connection on.
        scan_setting: A dict representing the settings of the scan.

    Returns:
        If scan was started successfully, event data of success event is returned.
    """
    idx = ad.droid.wifiScannerStartBackgroundScan(scan_setting)
    event = ad.ed.pop_event("WifiScannerScan{}onSuccess".format(idx),
                         SHORT_TIMEOUT)
    return event['data']


def start_wifi_tethering(ad, ssid, password, band=None):
    """Starts wifi tethering on an android_device.

    Args:
        ad: android_device to start wifi tethering on.
        ssid: The SSID the soft AP should broadcast.
        password: The password the soft AP should use.
        band: The band the soft AP should be set on. It should be either
            WifiEnums.WIFI_CONFIG_APBAND_2G or WifiEnums.WIFI_CONFIG_APBAND_5G.

    Returns:
        No return value. Error checks in this function will raise test failure signals
    """
    config = {WifiEnums.SSID_KEY: ssid}
    if password:
        config[WifiEnums.PWD_KEY] = password
    if band:
        config[WifiEnums.APBAND_KEY] = band
    asserts.assert_true(ad.droid.wifiSetWifiApConfiguration(config),
                        "Failed to update WifiAp Configuration")
    ad.droid.wifiStartTrackingTetherStateChange()
    ad.droid.connectivityStartTethering(tel_defines.TETHERING_WIFI, False)
    try:
        ad.ed.pop_event("ConnectivityManagerOnTetheringStarted")
        ad.ed.wait_for_event("TetherStateChanged",
                          lambda x : x["data"]["ACTIVE_TETHER"], 30)
        ad.log.debug("Tethering started successfully.")
    except Empty:
        msg = "Failed to receive confirmation of wifi tethering starting"
        asserts.fail(msg)
    finally:
        ad.droid.wifiStopTrackingTetherStateChange()


def stop_wifi_tethering(ad):
    """Stops wifi tethering on an android_device.

    Args:
        ad: android_device to stop wifi tethering on.
    """
    ad.droid.wifiStartTrackingTetherStateChange()
    ad.droid.connectivityStopTethering(tel_defines.TETHERING_WIFI)
    ad.droid.wifiSetApEnabled(False, None)
    try:
        ad.ed.pop_event("WifiManagerApDisabled", 30)
        ad.ed.wait_for_event("TetherStateChanged",
                          lambda x : not x["data"]["ACTIVE_TETHER"], 30)
    except Empty:
        msg = "Failed to receive confirmation of wifi tethering stopping"
        asserts.fail(msg)
    finally:
        ad.droid.wifiStopTrackingTetherStateChange()


def toggle_wifi_and_wait_for_reconnection(ad,
                                          network,
                                          num_of_tries=1,
                                          assert_on_fail=True):
    """Toggle wifi state and then wait for Android device to reconnect to
    the provided wifi network.

    This expects the device to be already connected to the provided network.

    Logic steps are
     1. Ensure that we're connected to the network.
     2. Turn wifi off.
     3. Wait for 10 seconds.
     4. Turn wifi on.
     5. Wait for the "connected" event, then confirm the connected ssid is the
        one requested.

    Args:
        ad: android_device object to initiate connection on.
        network: A dictionary representing the network to await connection. The
                 dictionary must have the key "SSID".
        num_of_tries: An integer that is the number of times to try before
                      delaring failure. Default is 1.
        assert_on_fail: If True, error checks in this function will raise test
                        failure signals.

    Returns:
        If assert_on_fail is False, function returns True if the toggle was
        successful, False otherwise. If assert_on_fail is True, no return value.
    """
    _assert_on_fail_handler(_toggle_wifi_and_wait_for_reconnection,
                            assert_on_fail, ad, network, num_of_tries)


def _toggle_wifi_and_wait_for_reconnection(ad, network, num_of_tries=1):
    """Toggle wifi state and then wait for Android device to reconnect to
    the provided wifi network.

    This expects the device to be already connected to the provided network.

    Logic steps are
     1. Ensure that we're connected to the network.
     2. Turn wifi off.
     3. Wait for 10 seconds.
     4. Turn wifi on.
     5. Wait for the "connected" event, then confirm the connected ssid is the
        one requested.

    This will directly fail a test if anything goes wrong.

    Args:
        ad: android_device object to initiate connection on.
        network: A dictionary representing the network to await connection. The
                 dictionary must have the key "SSID".
        num_of_tries: An integer that is the number of times to try before
                      delaring failure. Default is 1.
    """
    expected_ssid = network[WifiEnums.SSID_KEY]
    # First ensure that we're already connected to the provided network.
    verify_con = {WifiEnums.SSID_KEY: expected_ssid}
    verify_wifi_connection_info(ad, verify_con)
    # Now toggle wifi state and wait for the connection event.
    wifi_toggle_state(ad, False)
    time.sleep(10)
    wifi_toggle_state(ad, True)
    ad.droid.wifiStartTrackingStateChange()
    try:
        connect_result = None
        for i in range(num_of_tries):
            try:
                connect_result = ad.ed.pop_event(wifi_constants.WIFI_CONNECTED,
                                                 30)
                break
            except Empty:
                pass
        asserts.assert_true(connect_result,
                            "Failed to connect to Wi-Fi network %s on %s" %
                            (network, ad.serial))
        logging.debug("Connection result on %s: %s.", ad.serial, connect_result)
        actual_ssid = connect_result['data'][WifiEnums.SSID_KEY]
        asserts.assert_equal(actual_ssid, expected_ssid,
                             "Connected to the wrong network on %s."
                             "Expected %s, but got %s." %
                             (ad.serial, expected_ssid, actual_ssid))
        logging.info("Connected to Wi-Fi network %s on %s", actual_ssid, ad.serial)
    finally:
        ad.droid.wifiStopTrackingStateChange()


def wifi_connect(ad, network, num_of_tries=1, assert_on_fail=True):
    """Connect an Android device to a wifi network.

    Initiate connection to a wifi network, wait for the "connected" event, then
    confirm the connected ssid is the one requested.

    This will directly fail a test if anything goes wrong.

    Args:
        ad: android_device object to initiate connection on.
        network: A dictionary representing the network to connect to. The
                 dictionary must have the key "SSID".
        num_of_tries: An integer that is the number of times to try before
                      delaring failure. Default is 1.
        assert_on_fail: If True, error checks in this function will raise test
                        failure signals.

    Returns:
        If assert_on_fail is False, function returns True if the toggle was
        successful, False otherwise. If assert_on_fail is True, no return value.
    """
    _assert_on_fail_handler(_wifi_connect, assert_on_fail, ad, network,
                            num_of_tries)


def _wifi_connect(ad, network, num_of_tries=1):
    """Connect an Android device to a wifi network.

    Initiate connection to a wifi network, wait for the "connected" event, then
    confirm the connected ssid is the one requested.

    This will directly fail a test if anything goes wrong.

    Args:
        ad: android_device object to initiate connection on.
        network: A dictionary representing the network to connect to. The
                 dictionary must have the key "SSID".
        num_of_tries: An integer that is the number of times to try before
                      delaring failure. Default is 1.
    """
    asserts.assert_true(WifiEnums.SSID_KEY in network,
                        "Key '%s' must be present in network definition." %
                        WifiEnums.SSID_KEY)
    ad.droid.wifiStartTrackingStateChange()
    expected_ssid = network[WifiEnums.SSID_KEY]
    ad.droid.wifiConnectByConfig(network)
    ad.log.info("Starting connection process to %s", expected_ssid)
    try:
        event = ad.ed.pop_event(wifi_constants.CONNECT_BY_CONFIG_SUCCESS, 30)
        connect_result = None
        for i in range(num_of_tries):
            try:
                connect_result = ad.ed.pop_event(wifi_constants.WIFI_CONNECTED,
                                                 30)
                break
            except Empty:
                pass
        asserts.assert_true(connect_result,
                            "Failed to connect to Wi-Fi network %s on %s" %
                            (network, ad.serial))
        ad.log.debug("Wi-Fi connection result: %s.", connect_result)
        actual_ssid = connect_result['data'][WifiEnums.SSID_KEY]
        asserts.assert_equal(actual_ssid, expected_ssid,
                             "Connected to the wrong network on %s." % ad.serial)
        ad.log.info("Connected to Wi-Fi network %s.", actual_ssid)

        # Wait for data connection to stabilize.
        time.sleep(5)

        internet = validate_connection(ad, DEFAULT_PING_ADDR)
        if not internet:
            raise signals.TestFailure("Failed to connect to internet on %s" %
                                      expected_ssid)
    except Empty:
        asserts.fail("Failed to start connection process to %s on %s" %
                     (network, ad.serial))
    except Exception as error:
        ad.log.error("Failed to connect to %s with error %s", expected_ssid,
                     error)
        raise signals.TestFailure("Failed to connect to %s network" % network)

    finally:
        ad.droid.wifiStopTrackingStateChange()


def start_wifi_single_scan(ad, scan_setting):
    """Starts wifi single shot scan.

    Args:
        ad: android_device object to initiate connection on.
        scan_setting: A dict representing the settings of the scan.

    Returns:
        If scan was started successfully, event data of success event is returned.
    """
    idx = ad.droid.wifiScannerStartScan(scan_setting)
    event = ad.ed.pop_event("WifiScannerScan%sonSuccess" % idx, SHORT_TIMEOUT)
    ad.log.debug("Got event %s", event)
    return event['data']


def track_connection(ad, network_ssid, check_connection_count):
    """Track wifi connection to network changes for given number of counts

    Args:
        ad: android_device object for forget network.
        network_ssid: network ssid to which connection would be tracked
        check_connection_count: Integer for maximum number network connection
                                check.
    Returns:
        True if connection to given network happen, else return False.
    """
    ad.droid.wifiStartTrackingStateChange()
    while check_connection_count > 0:
        connect_network = ad.ed.pop_event("WifiNetworkConnected", 120)
        ad.log.info("Connected to network %s", connect_network)
        if (WifiEnums.SSID_KEY in connect_network['data'] and
                connect_network['data'][WifiEnums.SSID_KEY] == network_ssid):
            return True
        check_connection_count -= 1
    ad.droid.wifiStopTrackingStateChange()
    return False


def get_scan_time_and_channels(wifi_chs, scan_setting, stime_channel):
    """Calculate the scan time required based on the band or channels in scan
    setting

    Args:
        wifi_chs: Object of channels supported
        scan_setting: scan setting used for start scan
        stime_channel: scan time per channel

    Returns:
        scan_time: time required for completing a scan
        scan_channels: channel used for scanning
    """
    scan_time = 0
    scan_channels = []
    if "band" in scan_setting and "channels" not in scan_setting:
        scan_channels = wifi_chs.band_to_freq(scan_setting["band"])
    elif "channels" in scan_setting and "band" not in scan_setting:
        scan_channels = scan_setting["channels"]
    scan_time = len(scan_channels) * stime_channel
    for channel in scan_channels:
        if channel in WifiEnums.DFS_5G_FREQUENCIES:
            scan_time += 132  #passive scan time on DFS
    return scan_time, scan_channels


def start_wifi_track_bssid(ad, track_setting):
    """Start tracking Bssid for the given settings.

    Args:
      ad: android_device object.
      track_setting: Setting for which the bssid tracking should be started

    Returns:
      If tracking started successfully, event data of success event is returned.
    """
    idx = ad.droid.wifiScannerStartTrackingBssids(
        track_setting["bssidInfos"], track_setting["apLostThreshold"])
    event = ad.ed.pop_event("WifiScannerBssid{}onSuccess".format(idx),
                         SHORT_TIMEOUT)
    return event['data']


def convert_pem_key_to_pkcs8(in_file, out_file):
    """Converts the key file generated by us to the format required by
    Android using openssl.

    The input file must have the extension "pem". The output file must
    have the extension "der".

    Args:
        in_file: The original key file.
        out_file: The full path to the converted key file, including
        filename.
    """
    asserts.assert_true(in_file.endswith(".pem"), "Input file has to be .pem.")
    asserts.assert_true(
        out_file.endswith(".der"), "Output file has to be .der.")
    cmd = ("openssl pkcs8 -inform PEM -in {} -outform DER -out {} -nocrypt"
           " -topk8").format(in_file, out_file)
    utils.exe_cmd(cmd)


def validate_connection(ad, ping_addr):
    """Validate internet connection by pinging the address provided.

    Args:
        ad: android_device object.
        ping_addr: address on internet for pinging.

    Returns:
        ping output if successful, NULL otherwise.
    """
    ping = ad.droid.httpPing(ping_addr)
    ad.log.info("Http ping result: %s.", ping)
    return ping


#TODO(angli): This can only verify if an actual value is exactly the same.
# Would be nice to be able to verify an actual value is one of serveral.
def verify_wifi_connection_info(ad, expected_con):
    """Verifies that the information of the currently connected wifi network is
    as expected.

    Args:
        expected_con: A dict representing expected key-value pairs for wifi
            connection. e.g. {"SSID": "test_wifi"}
    """
    current_con = ad.droid.wifiGetConnectionInfo()
    case_insensitive = ["BSSID", "supplicant_state"]
    ad.log.debug("Current connection: %s", current_con)
    for k, expected_v in expected_con.items():
        # Do not verify authentication related fields.
        if k == "password":
            continue
        msg = "Field %s does not exist in wifi connection info %s." % (
            k, current_con)
        if k not in current_con:
            raise signals.TestFailure(msg)
        actual_v = current_con[k]
        if k in case_insensitive:
            actual_v = actual_v.lower()
            expected_v = expected_v.lower()
        msg = "Expected %s to be %s, actual %s is %s." % (k, expected_v, k,
                                                          actual_v)
        if actual_v != expected_v:
            raise signals.TestFailure(msg)


def expand_enterprise_config_by_phase2(config):
    """Take an enterprise config and generate a list of configs, each with
    a different phase2 auth type.

    Args:
        config: A dict representing enterprise config.

    Returns
        A list of enterprise configs.
    """
    results = []
    phase2_types = WifiEnums.EapPhase2
    if config[WifiEnums.Enterprise.EAP] == WifiEnums.Eap.PEAP:
        # Skip unsupported phase2 types for PEAP.
        phase2_types = [WifiEnums.EapPhase2.GTC, WifiEnums.EapPhase2.MSCHAPV2]
    for phase2_type in phase2_types:
        # Skip a special case for passpoint TTLS.
        if (WifiEnums.Enterprise.FQDN in config and
                phase2_type == WifiEnums.EapPhase2.GTC):
            continue
        c = dict(config)
        c[WifiEnums.Enterprise.PHASE2] = phase2_type.value
        results.append(c)
    return results


def generate_eap_test_name(config, ad=None):
    """ Generates a test case name based on an EAP configuration.

    Args:
        config: A dict representing an EAP credential.
        ad object: Redundant but required as the same param is passed
                   to test_func in run_generated_tests

    Returns:
        A string representing the name of a generated EAP test case.
    """
    eap = WifiEnums.Eap
    eap_phase2 = WifiEnums.EapPhase2
    Ent = WifiEnums.Enterprise
    name = "test_connect-"
    eap_name = ""
    for e in eap:
        if e.value == config[Ent.EAP]:
            eap_name = e.name
            break
    if "peap0" in config[WifiEnums.SSID_KEY].lower():
        eap_name = "PEAP0"
    if "peap1" in config[WifiEnums.SSID_KEY].lower():
        eap_name = "PEAP1"
    name += eap_name
    if Ent.PHASE2 in config:
        for e in eap_phase2:
            if e.value == config[Ent.PHASE2]:
                name += "-{}".format(e.name)
                break
    return name


def group_attenuators(attenuators):
    """Groups a list of attenuators into attenuator groups for backward
    compatibility reasons.

    Most legacy Wi-Fi setups have two attenuators each connected to a separate
    AP. The new Wi-Fi setup has four attenuators, each connected to one channel
    on an AP, so two of them are connected to one AP.

    To make the existing scripts work in the new setup, when the script needs
    to attenuate one AP, it needs to set attenuation on both attenuators
    connected to the same AP.

    This function groups attenuators properly so the scripts work in both
    legacy and new Wi-Fi setups.

    Args:
        attenuators: A list of attenuator objects, either two or four in length.

    Raises:
        signals.TestFailure is raised if the attenuator list does not have two
        or four objects.
    """
    attn0 = attenuator.AttenuatorGroup("AP0")
    attn1 = attenuator.AttenuatorGroup("AP1")
    # Legacy testbed setup has two attenuation channels.
    num_of_attns = len(attenuators)
    if num_of_attns == 2:
        attn0.add(attenuators[0])
        attn1.add(attenuators[1])
    elif num_of_attns == 4:
        attn0.add(attenuators[0])
        attn0.add(attenuators[1])
        attn1.add(attenuators[2])
        attn1.add(attenuators[3])
    else:
        asserts.fail(("Either two or four attenuators are required for this "
                      "test, but found %s") % num_of_attns)
    return [attn0, attn1]
