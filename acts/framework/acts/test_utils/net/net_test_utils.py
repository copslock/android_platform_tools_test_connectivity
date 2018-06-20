#!/usr/bin/env python3.4
#
#   Copyright 2018 Google, Inc.
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

from acts import asserts
from acts.test_utils.net import connectivity_const as cconst
from acts.test_utils.tel.tel_data_utils import wait_for_cell_data_connection
from acts.test_utils.tel.tel_test_utils import verify_http_connection
from acts.test_utils.wifi import wifi_test_utils as wutils

import os
import re
import time
import urllib.request

VPN_CONST = cconst.VpnProfile
VPN_TYPE = cconst.VpnProfileType
VPN_PARAMS = cconst.VpnReqParams
VPN_PING_ADDR = "10.10.10.1"

def verify_lte_data_and_tethering_supported(ad):
    """Verify if LTE data is enabled and tethering supported"""
    wutils.wifi_toggle_state(ad, False)
    ad.droid.telephonyToggleDataConnection(True)
    wait_for_cell_data_connection(ad.log, ad, True)
    asserts.assert_true(
        verify_http_connection(ad.log, ad),
        "HTTP verification failed on cell data connection")
    asserts.assert_true(
        ad.droid.connectivityIsTetheringSupported(),
        "Tethering is not supported for the provider")
    wutils.wifi_toggle_state(ad, True)

def set_chrome_browser_permissions(ad):
    """Set chrome browser start with no-first-run verification.
    Give permission to read from and write to storage
    """
    commands = ["pm grant com.android.chrome "
                "android.permission.READ_EXTERNAL_STORAGE",
                "pm grant com.android.chrome "
                "android.permission.WRITE_EXTERNAL_STORAGE",
                "rm /data/local/chrome-command-line",
                "am set-debug-app --persistent com.android.chrome",
                'echo "chrome --no-default-browser-check --no-first-run '
                '--disable-fre" > /data/local/tmp/chrome-command-line']
    for cmd in commands:
        try:
            ad.adb.shell(cmd)
        except adb.AdbError:
            self.log.warn("adb command %s failed on %s" % (cmd, ad.serial))

def verify_ping_to_vpn_ip(ad):
    """ Verify if IP behind VPN server is pingable.
    Ping should pass, if VPN is connected.
    Ping should fail, if VPN is disconnected.

    Args:
      ad: android device object
    """
    ping_result = None
    pkt_loss = "100% packet loss"
    try:
        ping_result = ad.adb.shell("ping -c 3 -W 2 %s" % VPN_PING_ADDR)
    except adb.AdbError:
        pass
    return ping_result and pkt_loss not in ping_result

def legacy_vpn_connection_test_logic(ad, vpn_profile):
    """ Test logic for each legacy VPN connection

    Steps:
      1. Generate profile for the VPN type
      2. Establish connection to the server
      3. Verify that connection is established using LegacyVpnInfo
      4. Verify the connection by pinging the IP behind VPN
      5. Stop the VPN connection
      6. Check the connection status
      7. Verify that ping to IP behind VPN fails

    Args:
      1. ad: Android device object
      2. VpnProfileType (1 of the 6 types supported by Android)
    """
    # Wait for sometime so that VPN server flushes all interfaces and
    # connections after graceful termination
    time.sleep(10)

    ad.adb.shell("ip xfrm state flush")
    ad.log.info("Connecting to: %s", vpn_profile)
    ad.droid.vpnStartLegacyVpn(vpn_profile)
    time.sleep(cconst.VPN_TIMEOUT)

    connected_vpn_info = ad.droid.vpnGetLegacyVpnInfo()
    asserts.assert_equal(connected_vpn_info["state"],
                         cconst.VPN_STATE_CONNECTED,
                         "Unable to establish VPN connection for %s"
                         % vpn_profile)

    ping_result = verify_ping_to_vpn_ip(ad)
    ip_xfrm_state = ad.adb.shell("ip xfrm state")
    match_obj = re.search(r'hmac(.*)', "%s" % ip_xfrm_state)
    if match_obj:
        ip_xfrm_state = format(match_obj.group(0)).split()
        ad.log.info("HMAC for ESP is %s " % ip_xfrm_state[0])

    ad.droid.vpnStopLegacyVpn()
    asserts.assert_true(ping_result,
                        "Ping to the internal IP failed. "
                        "Expected to pass as VPN is connected")

    connected_vpn_info = ad.droid.vpnGetLegacyVpnInfo()
    asserts.assert_true(not connected_vpn_info,
                        "Unable to terminate VPN connection for %s"
                        % vpn_profile)

def download_load_certs(ad, vpn_params, vpn_type, vpn_server_addr,
                        ipsec_server_type, log_path):
    """ Download the certificates from VPN server and push to sdcard of DUT

    Args:
      ad: android device object
      vpn_params: vpn params from config file
      vpn_type: 1 of the 6 VPN types
      vpn_server_addr: server addr to connect to
      ipsec_server_type: ipsec version - strongswan or openswan
      log_path: log path to download cert

    Returns:
      Client cert file name on DUT's sdcard
    """
    url = "http://%s%s%s" % (vpn_server_addr,
                             vpn_params['cert_path_vpnserver'],
                             vpn_params['client_pkcs_file_name'])
    local_cert_name = "%s_%s_%s" % (vpn_type.name,
                                    ipsec_server_type,
                                    vpn_params['client_pkcs_file_name'])
    ad.adb.push("%s sdcard/" % local_cert_name)
    return local_cert_name

    local_file_path = os.path.join(log_path, local_cert_name)
    try:
        ret = urllib.request.urlopen(url)
        with open(local_file_path, "wb") as f:
            f.write(ret.read())
    except:
        asserts.fail("Unable to download certificate from the server")

    f.close()
    ad.adb.push("%s sdcard/" % local_file_path)
    return local_cert_name

def generate_legacy_vpn_profile(ad,
                                vpn_params,
                                vpn_type,
                                vpn_server_addr,
                                ipsec_server_type,
                                log_path):
    """ Generate legacy VPN profile for a VPN

    Args:
      ad: android device object
      vpn_params: vpn params from config file
      vpn_type: 1 of the 6 VPN types
      vpn_server_addr: server addr to connect to
      ipsec_server_type: ipsec version - strongswan or openswan
      log_path: log path to download cert

    Returns:
      Vpn profile
    """
    vpn_profile = {VPN_CONST.USER: vpn_params['vpn_username'],
                   VPN_CONST.PWD: vpn_params['vpn_password'],
                   VPN_CONST.TYPE: vpn_type.value,
                   VPN_CONST.SERVER: vpn_server_addr,}
    vpn_profile[VPN_CONST.NAME] = "test_%s_%s" % (vpn_type.name,
                                                  ipsec_server_type)
    if vpn_type.name == "PPTP":
        vpn_profile[VPN_CONST.NAME] = "test_%s" % vpn_type.name

    psk_set = set(["L2TP_IPSEC_PSK", "IPSEC_XAUTH_PSK"])
    rsa_set = set(["L2TP_IPSEC_RSA", "IPSEC_XAUTH_RSA", "IPSEC_HYBRID_RSA"])

    if vpn_type.name in psk_set:
        vpn_profile[VPN_CONST.IPSEC_SECRET] = vpn_params['psk_secret']
    elif vpn_type.name in rsa_set:
        cert_name = download_load_certs(ad,
                                        vpn_params,
                                        vpn_type,
                                        vpn_server_addr,
                                        ipsec_server_type,
                                        log_path)
        vpn_profile[VPN_CONST.IPSEC_USER_CERT] = cert_name.split('.')[0]
        vpn_profile[VPN_CONST.IPSEC_CA_CERT] = cert_name.split('.')[0]
        ad.droid.installCertificate(vpn_profile, cert_name,
                                    vpn_params['cert_password'])
    else:
        vpn_profile[VPN_CONST.MPPE] = "mppe"

    return vpn_profile
