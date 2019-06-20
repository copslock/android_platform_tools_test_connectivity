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

import acts.test_utils.wifi.wifi_test_utils as wutils

from acts.controllers.fuchsia_device import FuchsiaDevice
from acts.controllers.android_device import AndroidDevice


def create_wlan_device(hardware_device):
    """Creates a generic WLAN device based on type of device that is sent to
    the functions.

    Args:
        hardware_device: A WLAN hardware device that is supported by ACTS.
    """
    if isinstance(hardware_device, FuchsiaDevice):
        return FuchsiaWlanDevice(hardware_device)
    elif isinstance(hardware_device, AndroidDevice):
        return AndroidWlanDevice(hardware_device)
    else:
        raise ValueError('Unable to create WlanDevice for type %s' %
                         type(hardware_device))


class WlanDevice(object):
    """Class representing a generic WLAN device.

    Each object of this class represents a generic WLAN device.
    Android device and Fuchsia devices are the currently supported devices/

    Attributes:
        device: A generic WLAN device.
    """
    def __init__(self, device):
        self.device = device

    def wifi_toggle_state(self, state):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('wifi_toggle_state must be defined.')

    def reset_wifi(self):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('reset_wifi must be defined.')

    def take_bug_report(self, test_name, begin_time):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('take_bug_report must be defined.')

    def get_log(self, test_name, begin_time):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('get_log( must be defined.')

    def turn_location_off_and_scan_toggle_off(self):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('turn_location_off_and_scan_toggle_off'
                                  ' must be defined.')

    def associate(self,
                  target_ssid,
                  target_pwd=None,
                  check_connectivity=True,
                  hidden=False):
        """Base generic WLAN interface.  Only called if not overriden by
        another supported device.
        """
        raise NotImplementedError('associate must be defined.')

    def disconnect(self):
        """Base generic WLAN interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError('disconnect must be defined.')


class AndroidWlanDevice(WlanDevice):
    """Class wrapper for an Android WLAN device.

    Each object of this class represents a generic WLAN device.
    Android device and Fuchsia devices are the currently supported devices/

    Attributes:
        android_device: An Android WLAN device.
    """
    def __init__(self, android_device):
        super().__init__(android_device)

    def wifi_toggle_state(self, state):
        wutils.wifi_toggle_state(self.device, state)

    def reset_wifi(self):
        wutils.reset_wifi(self.device)

    def take_bug_report(self, test_name, begin_time):
        self.device.take_bug_report(test_name, begin_time)


    def get_log(self, test_name, begin_time):
        self.device.cat_adb_log(test_name, begin_time)

    def turn_location_off_and_scan_toggle_off(self):
        wutils.turn_location_off_and_scan_toggle_off(self.device)

    def associate(self,
                  target_ssid,
                  target_pwd=None,
                  check_connectivity=True,
                  hidden=False):
        """Function to associate an Android WLAN device.

        Args:
            target_ssid: SSID to associate to.
            target_pwd: Password for the SSID, if necessary.
            check_connectivity: Whether to check for internet connectivity.
            hidden: Whether the network is hidden.
        Returns:
            True if successfully connected to WLAN, False if not.
        """
        if target_pwd:
            network = {'SSID': target_ssid,
                       'password': target_pwd,
                       'hiddenSSID': hidden}
        else:
            network = {'SSID': target_ssid,
                       'hiddenSSID': hidden}
        try:
            wutils.connect_to_wifi_network(self.device,
                                           network,
                                           check_connectivity=
                                           check_connectivity,
                                           hidden=hidden)
            return True
        except Exception as e:
            self.device.log.info('Failed to associated (%s)' % e)
            return False

    def disconnect(self):
        wutils.turn_location_off_and_scan_toggle_off(self.device)


class FuchsiaWlanDevice(WlanDevice):
    """Class wrapper for an Fuchsia WLAN device.

    Each object of this class represents a generic WLAN device.
    Android device and Fuchsia devices are the currently supported devices/

    Attributes:
        fuchsia_device: A Fuchsia WLAN device.
    """
    def __init__(self, fuchsia_device):
        super().__init__(fuchsia_device)

    def wifi_toggle_state(self, state):
        """Stub for Fuchsia implementation."""
        pass

    def reset_wifi(self):
        """Stub for Fuchsia implementation."""
        pass

    def take_bug_report(self, test_name, begin_time):
        """Stub for Fuchsia implementation."""
        pass

    def get_log(self, test_name, begin_time):
        """Stub for Fuchsia implementation."""
        pass

    def turn_location_off_and_scan_toggle_off(self):
        """Stub for Fuchsia implementation."""
        pass

    def associate(self,
                  target_ssid,
                  target_pwd=None,
                  check_connectivity=True,
                  hidden=False):
        """Function to associate an Android WLAN device.

        Args:
            target_ssid: SSID to associate to.
            target_pwd: Password for the SSID, if necessary.
            check_connectivity: Whether to check for internet connectivity.
            hidden: Whether the network is hidden.
        Returns:
            True if successfully connected to WLAN, False if not.
        """
        connection_response = self.device.wlan_lib.wlanConnectToNetwork(
            target_ssid, target_pwd=target_pwd)
        return self.device.check_connection_for_response(
            connection_response)

    def disconnect(self):
        return self.device.wlan_lib.wlanDisconnect()

    def status(self):
        return self.device.wlan_lib.wlanStatus()
