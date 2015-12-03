#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
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

import random
import string
import time
import warnings

from acts.utils import rand_ascii_str
from acts.test_utils.tel.tel_defines import *
from acts.test_utils.tel.tel_test_utils import *

def wifi_tethering_cleanup(log, provider, client_list):
    """Clean up steps for WiFi Tethering.

    Make sure provider turn off tethering.
    Make sure clients reset WiFi and turn on cellular data.

    Args:
        log: log object.
        provider: android object provide WiFi tethering.
        client_list: a list of clients using tethered WiFi.

    Returns:
        True if no error happened. False otherwise.
    """
    for client in client_list:
        client.droid.toggleDataConnection(True)
        if not WifiUtils.wifi_reset(log, client):
            log.error("Reset client WiFi failed. {}".format(client.serial))
            return False
    if not provider.droid.wifiIsApEnabled():
        log.error("Provider WiFi tethering stopped.")
        return False
    if not WifiUtils.stop_wifi_tethering(log, provider):
        log.error("Provider strop WiFi tethering failed.")
        return False
    return True

def wifi_tethering_setup_teardown(log, provider, client_list,
                                  ap_band=WifiUtils.WIFI_CONFIG_APBAND_2G,
                                  check_interval=30, check_iteration=4,
                                  do_cleanup=True,
                                  ssid=None, password=None):
    """Test WiFi Tethering.

    Turn off WiFi on provider and clients.
    Turn off data and reset WiFi on clients.
    Verify no Internet access on clients.
    Turn on WiFi tethering on provider.
    Clients connect to provider's WiFI.
    Verify Internet on provider and clients.
    Tear down WiFi tethering setup and clean up.

    Args:
        log: log object.
        provider: android object provide WiFi tethering.
        client_list: a list of clients using tethered WiFi.
        ap_band: setup WiFi tethering on 2G or 5G.
            This is optional, default value is WifiUtils.WIFI_CONFIG_APBAND_2G
        check_interval: delay time between each around of Internet connection check.
            This is optional, default value is 30 (seconds).
        check_iteration: check Internet connection for how many times in total.
            This is optional, default value is 4 (4 times).
        do_cleanup: after WiFi tethering test, do clean up to tear down tethering
            setup or not. This is optional, default value is True.
        ssid: use this string as WiFi SSID to setup tethered WiFi network.
            This is optional. Default value is None.
            If it's None, a random string will be generated.
        password: use this string as WiFi password to setup tethered WiFi network.
            This is optional. Default value is None.
            If it's None, a random string will be generated.

    Returns:
        True if no error happened. False otherwise.
    """
    log.info("--->Start wifi_tethering_setup_teardown<---")
    log.info("Provider: {}".format(provider.serial))
    WifiUtils.wifi_toggle_state(log, provider, False)

    if ssid is None:
        ssid = rand_ascii_str(10)
    if password is None:
        password = rand_ascii_str(8)

    # No password
    if password == "":
        password = None

    try:
        for client in client_list:
            log.info("Client: {}".format(client.serial))
            WifiUtils.wifi_toggle_state(log, client, False)
            client.droid.toggleDataConnection(False)
        log.info("WiFI Tethering: Verify client have no Internet access.")
        for client in client_list:
            if verify_http_connection(log, client):
                log.error("Turn off Data on client fail. {}".format(client.serial))
                return False

        log.info("WiFI Tethering: Turn on WiFi tethering on {}. SSID: {}, password: {}".
                 format(provider.serial, ssid, password))

        if not WifiUtils.start_wifi_tethering(log, provider, ssid, password, ap_band):
            log.error("Provider start WiFi tethering failed.")
            return False
        time.sleep(WAIT_TIME_ANDROID_STATE_SETTLING)

        log.info("Provider {} check Internet connection.".
                 format(provider.serial))
        if not verify_http_connection(log, provider):
            return False
        for client in client_list:
            log.info("WiFI Tethering: {} connect to WiFi and verify AP band correct.".
                     format(client.serial))
            if not ensure_wifi_connected(log, client, ssid, password):
                log.error("Client connect to WiFi failed.")
                return False

            wifi_info = client.droid.wifiGetConnectionInfo()
            if ap_band == WifiUtils.WIFI_CONFIG_APBAND_5G:
                if wifi_info["is_24ghz"]:
                    log.error("Expected 5g network. WiFi Info: {}".
                              format(wifi_info))
                    return False
            else:
                if wifi_info["is_5ghz"]:
                    log.error("Expected 2g network. WiFi Info: {}".
                              format(wifi_info))
                    return False

            log.info("Client{} check Internet connection.".
                     format(client.serial))
            if (not wait_for_wifi_data_connection(log, client, True) or not
                    verify_http_connection(log, client)):
                log.error("No WiFi Data on client: {}.".format(client.serial))
                return False

        if not tethering_check_internet_connection(log, provider, client_list,
                                                   check_interval,
                                                   check_iteration):
            return False

    finally:
        if (do_cleanup and
            (not wifi_tethering_cleanup(log, provider, client_list))):
            return False
    return True

def tethering_check_internet_connection(log, provider, client_list,
                                        check_interval, check_iteration):
    """During tethering test, check client(s) and provider Internet connection.

    Do the following for <check_iteration> times:
        Delay <check_interval> seconds.
        Check Tethering provider's Internet connection.
        Check each client's Internet connection.

    Args:
        log: log object.
        provider: android object provide WiFi tethering.
        client_list: a list of clients using tethered WiFi.
        check_interval: delay time between each around of Internet connection check.
        check_iteration: check Internet connection for how many times in total.

    Returns:
        True if no error happened. False otherwise.
    """
    for i in range(1, check_iteration):
        time.sleep(check_interval)
        log.info("Provider {} check Internet connection after {} seconds.".
                      format(provider.serial, check_interval*i))
        if not verify_http_connection(log, provider):
            return False
        for client in client_list:
            log.info("Client {} check Internet connection after {} seconds.".
                          format(client.serial, check_interval*i))
            if not verify_http_connection(log, client):
                return False
    return True

def wifi_cell_switching(log, ad, wifi_network_ssid, wifi_network_pass,
                        nw_type=None):
    """Test data connection network switching when phone camped on <nw_type>.

    Ensure phone is camped on <nw_type>
    Ensure WiFi can connect to live network,
    Airplane mode is off, data connection is on, WiFi is on.
    Turn off WiFi, verify data is on cell and browse to google.com is OK.
    Turn on WiFi, verify data is on WiFi and browse to google.com is OK.
    Turn off WiFi, verify data is on cell and browse to google.com is OK.

    Args:
        log: log object.
        ad: android object.
        wifi_network_ssid: ssid for live wifi network.
        wifi_network_pass: password for live wifi network.
        nw_type: network rat the phone should be camped on.

    Returns:
        True if pass.
    """
    # TODO: take wifi_cell_switching out of tel_data_utils.py
    # b/23354769

    try:
        if not ensure_network_rat(log, ad, nw_type, WAIT_TIME_NW_SELECTION,
                                  NETWORK_SERVICE_DATA):
            log.error("Device failed to register in {}".format(nw_type))
            return False

        # Temporary hack to give phone enough time to register.
        # TODO: Proper check using SL4A API.
        time.sleep(WAIT_TIME_BETWEEN_REG_AND_CALL)

        # Ensure WiFi can connect to live network
        log.info("Make sure phone can connect to live network by WIFI")
        if not ensure_wifi_connected(log, ad,
                                     wifi_network_ssid, wifi_network_pass):
            log.error("WiFi connect fail.")
            return False
        log.info("Phone connected to WIFI.")

        log.info("Step1 Airplane Off, WiFi On, Data On.")
        toggle_airplane_mode(log, ad, False)
        WifiUtils.wifi_toggle_state(log, ad, True)
        ad.droid.toggleDataConnection(True)
        #TODO: Add a check to ensure data routes through wifi here

        log.info("Step2 WiFi is Off, Data is on Cell.")
        WifiUtils.wifi_toggle_state(log, ad, False)
        if (not wait_for_cell_data_connection(log, ad, True) or not
                verify_http_connection(log, ad)):
            log.error("Data did not return to cell")
            return False

        log.info("Step3 WiFi is On, Data is on WiFi.")
        WifiUtils.wifi_toggle_state(log, ad, True)
        if (not wait_for_wifi_data_connection(log, ad, True) or not
                verify_http_connection(log, ad)):
            log.error("Data did not return to WiFi")
            return False

        log.info("Step4 WiFi is Off, Data is on Cell.")
        WifiUtils.wifi_toggle_state(log, ad, False)
        if (not wait_for_cell_data_connection(log, ad, True) or not
                verify_http_connection(log, ad)):
            log.error("Data did not return to cell")
            return False
        return True

    finally:
        WifiUtils.wifi_toggle_state(log, ad, False)

def airplane_mode_test(log, ad):
    """ Test airplane mode basic on Phone and Live SIM.

    Ensure phone attach, data on, WiFi off and verify Internet.
    Turn on airplane mode to make sure detach.
    Turn off airplane mode to make sure attach.
    Verify Internet connection.

    Args:
        log: log object.
        ad: android object.

    Returns:
        True if pass; False if fail.
    """
    if not ensure_phones_idle(log, [ad]):
        log.error("Failed to return phones to idle.")
        return False

    try:
        ad.droid.toggleDataConnection(True)
        WifiUtils.wifi_toggle_state(log, ad, False)

        log.info("Step1: ensure attach")
        if not toggle_airplane_mode(log, ad, False):
            log.error("Failed initial attach")
            return False
        if not verify_http_connection(log, ad):
            log.error("Data not available on cell.")
            return False

        log.info("Step2: enable airplane mode and ensure detach")
        if not toggle_airplane_mode(log, ad, True):
            log.error("Failed to enable Airplane Mode")
            return False
        if not wait_for_cell_data_connection(log, ad, False):
            log.error("Failed to disable cell data connection")
            return False
        if verify_http_connection(log, ad):
            log.error("Data available in airplane mode.")
            return False

        log.info("Step3: disable airplane mode and ensure attach")
        if not toggle_airplane_mode(log, ad, False):
            log.error("Failed to disable Airplane Mode")
            return False

        if not wait_for_cell_data_connection(log, ad, True):
            log.error("Failed to enable cell data connection")
            return False

        time.sleep(WAIT_TIME_ANDROID_STATE_SETTLING)

        log.info("Step4 verify internet")
        return verify_http_connection(log, ad)
    finally:
        toggle_airplane_mode(log, ad, False)

def data_connectivity_single_bearer(log, ad, nw_gen):
    """Test data connection: single-bearer (no voice).

    Turn off airplane mode, enable Cellular Data.
    Ensure phone data generation is expected.
    Verify Internet.
    Disable Cellular Data, verify Internet is inaccessible.
    Enable Cellular Data, verify Internet.

    Args:
        log: log object.
        ad: android object.
        nw_gen: network generation the phone should on.

    Returns:
        True if success.
        False if failed.
    """
    ensure_phones_idle(log, [ad])

    if not ensure_network_generation(log, ad, nw_gen,
            WAIT_TIME_NW_SELECTION, NETWORK_SERVICE_DATA):

        log.error("Device failed to reselect in {}s.".format(
            WAIT_TIME_NW_SELECTION))
        return False

    # Temporary hack to give phone enough time to register.
    # TODO: Proper check using SL4A API.
    time.sleep(5)

    try:
        log.info("Step1 Airplane Off, Data On.")
        toggle_airplane_mode(log, ad, False)
        ad.droid.toggleDataConnection(True)
        if not wait_for_cell_data_connection(log, ad, True):
            log.error("Failed to enable data connection.")
            return False

        log.info("Step2 Verify internet")
        if not verify_http_connection(log, ad):
            log.error("Data not available on cell.")
            return False

        log.info("Step3 Turn off data and verify not connected.")
        ad.droid.toggleDataConnection(False)
        if not wait_for_cell_data_connection(log, ad, False):
            log.error("Step3 Failed to disable data connection.")
            return False

        if verify_http_connection(log, ad):
            log.error("Step3 Data still available when disabled.")
            return False

        log.info("Step4 Re-enable data.")
        ad.droid.toggleDataConnection(True)
        if not wait_for_cell_data_connection(log, ad, True):
            log.error("Step4 failed to re-enable data.")
            return False
        if not verify_http_connection(log, ad):
            log.error("Data not available on cell.")
            return False

        if not is_droid_in_network_generation(
                log, ad, nw_gen,
                NETWORK_SERVICE_DATA):
            log.error("Failed: droid is no longer on correct network")
            log.info("Expected:{}, Current:{}".format(nw_gen,
                rat_generation_from_type(
                    get_network_rat_for_subscription(log, ad,
                    ad.droid.subscriptionGetDefaultSubId(),
                    NETWORK_SERVICE_DATA))))
            return False
        return True
    finally:
        ad.droid.toggleDataConnection(True)
