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


import inspect
import logging

from queue import Empty

from acts.controllers.android_device import AndroidDevice
from acts.controllers.fuchsia_device import FuchsiaDevice
from acts.test_utils.bt.bt_constants import ble_scan_settings_modes
from acts.test_utils.bt.bt_constants import scan_result
from acts.test_utils.bt.bt_gatt_utils import GattTestUtilsError
from acts.test_utils.bt.bt_gatt_utils import disconnect_gatt_connection
from acts.test_utils.bt.bt_gatt_utils import setup_gatt_connection
from acts.test_utils.fuchsia.bt_test_utils import le_scan_for_device_by_name

import acts.test_utils.bt.bt_test_utils as bt_test_utils


def create_bluetooth_device(hardware_device):
    """Creates a generic Bluetooth device based on type of device that is sent
    to the functions.

    Args:
        hardware_device: A Bluetooth hardware device that is supported by ACTS.
    """
    if isinstance(hardware_device, FuchsiaDevice):
        return FuchsiaBluetoothDevice(hardware_device)
    elif isinstance(hardware_device, AndroidDevice):
        return AndroidBluetoothDevice(hardware_device)
    else:
        raise ValueError('Unable to create BluetoothDevice for type %s' %
                         type(hardware_device))


class BluetoothDevice(object):
    """Class representing a generic Bluetooth device.

    Each object of this class represents a generic Bluetooth device.
    Android device and Fuchsia devices are the currently supported devices.

    Attributes:
        device: A generic Bluetooth device.
    """

    def __init__(self, device):
        self.device = device
        self.log = logging

    def start_pairing_helper(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def bluetooth_toggle_state(self, state):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def gatt_client_discover_characteristic_by_uuid(self, peer_identifier,
                                                    uuid):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def initialize_bluetooth_controller(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def get_pairing_pin(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def input_pairing_pin(self, pin):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def get_bluetooth_local_address(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def gatt_connect(self, peer_identifier, transport, autoconnect):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def gatt_client_ready_characteristic_by_handle(self, peer_identifier,
                                                   handle):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def gatt_disconnect(self, peer_identifier):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def gatt_client_refresh(self, peer_identifier):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def le_scan_with_name_filter(self, name, timeout):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def log_info(self, log):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def reset_bluetooth(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def start_le_advertisement(self, adv_data, adv_interval):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def stop_le_advertisement(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def set_bluetooth_local_name(self, name):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def setup_gatt_server(self, database):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def close_gatt_server(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def unbond_device(self, peer_identifier):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))

    def unbond_all_known_devices(self):
        """Base generic Bluetooth interface.  Only called if not overridden by
        another supported device.
        """
        raise NotImplementedError("{} must be defined.".format(
            inspect.currentframe().f_code.co_name))


class AndroidBluetoothDevice(BluetoothDevice):
    """Class wrapper for an Android Bluetooth device.

    Each object of this class represents a generic Bluetooth device.
    Android device and Fuchsia devices are the currently supported devices/

    Attributes:
        android_device: An Android Bluetooth device.
    """

    def __init__(self, android_device):
        super().__init__(android_device)
        self.peer_mapping = {}

    def bluetooth_toggle_state(self, state):
        self.device.droid.bluetoothToggleState(state)

    def initialize_bluetooth(self):
        pass

    def start_pairing_helper(self):
        """ Starts the Android pairing helper.
        """
        self.device.droid.bluetoothStartPairingHelper(True)

    def gatt_connect(self, peer_identifier, transport, autoconnect=False):
        """ Perform a GATT connection to a perihperal.

        Args:
            peer_identifier: The mac address to connect to.
            transport: Which transport to use.
            autoconnect: Set autocnnect to True or False.
        Returns:
            True if success, False if failure.
        """
        try:
            bluetooth_gatt, gatt_callback = setup_gatt_connection(
                self.device, peer_identifier, autoconnect, transport)
            self.peer_mapping[peer_identifier] = {
                "bluetooth_gatt": bluetooth_gatt,
                "gatt_callback": gatt_callback
            }
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        return True

    def gatt_disconnect(self, peer_identifier):
        """ Perform a GATT disconnect from a perihperal.

        Args:
            peer_identifier: The peer to disconnect from.
        Returns:
            True if success, False if failure.
        """
        peer_info = self.peer_mapping.get(peer_identifier)
        if not peer_info:
            self.log.error(
                "No previous connections made to {}".format(peer_identifier))
            return False

        try:
            disconnect_gatt_connection(self.device,
                                       peer_info.get("bluetooth_gatt"),
                                       peer_info.get("gatt_callback"))
            self.cen_ad.droid.gattClientClose(peer_info.get("bluetooth_gatt"))
        except GattTestUtilsError as err:
            self.log.error(err)
            return False
        self.cen_ad.droid.gattClientClose(peer_info.get("bluetooth_gatt"))

    def gatt_client_refresh(self, peer_identifier):
        """ Perform a GATT Client Refresh of a perihperal.

        Clears the internal cache and forces a refresh of the services from the
        remote device.

        Args:
            peer_identifier: The peer to refresh.
        """
        peer_info = self.peer_mapping.get(peer_identifier)
        if not peer_info:
            self.log.error(
                "No previous connections made to {}".format(peer_identifier))
            return False
        self.device.droid.gattClientRefresh(peer_info["bluetooth_gatt"])

    def le_scan_with_name_filter(self, name, timeout):
        """ Scan over LE for a specific device name.

         Args:
            name: The name filter to set.
            timeout: The timeout to wait to find the advertisement.
        Returns:
            Discovered mac address or None
        """
        self.device.droid.bleSetScanSettingsScanMode(
            ble_scan_settings_modes['low_latency'])
        filter_list = self.device.droid.bleGenFilterList()
        scan_settings = self.device.droid.bleBuildScanSetting()
        scan_callback = self.device.droid.bleGenScanCallback()
        self.device.droid.bleSetScanFilterDeviceName(name)
        self.device.droid.bleBuildScanFilter(filter_list)
        self.device.droid.bleSetScanFilterDeviceName(self.name)
        self.device.droid.bleStartBleScan(filter_list, scan_settings,
                                          scan_callback)
        try:
            event = self.device.ed.pop_event(scan_result.format(scan_callback),
                                             timeout)
            return event['data']['Result']['deviceInfo']['address']
        except Empty as err:
            self.log.info("Scanner did not find advertisement {}".format(err))
            return None

    def log_info(self, log):
        """ Log directly onto the device.

        Args:
            log: The informative log.
        """
        self.device.droid.log.logI(log)

    def set_bluetooth_local_name(self, name):
        """ Sets the Bluetooth controller's local name
        Args:
            name: The name to set.
        """
        self.device.droid.bluetoothSetLocalName(name)

    def get_local_bluetooth_address(self):
        """ Returns the Bluetooth local address.
        """
        self.device.droid.bluetoothGetLocalAddress()

    def reset_bluetooth(self):
        """ Resets Bluetooth on the Android Device.
        """
        bt_test_utils.reset_bluetooth([self.device])

    def unbond_all_known_devices(self):
        """ Unbond all known remote devices.
        """
        self.device.droid.bluetoothFactoryReset()

    def unbond_device(self, peer_identifier):
        """ Unbond peer identifier.

        Args:
            peer_identifier: The mac address for the peer to unbond.

        """
        self.device.droid.bluetoothUnbond(peer_identifier)


class FuchsiaBluetoothDevice(BluetoothDevice):
    """Class wrapper for an Fuchsia Bluetooth device.

    Each object of this class represents a generic luetooth device.
    Android device and Fuchsia devices are the currently supported devices/

    Attributes:
        fuchsia_device: A Fuchsia Bluetooth device.
    """

    def __init__(self, fuchsia_device):
        super().__init__(fuchsia_device)

    def start_pairing_helper(self):
        self.device.btc_lib.acceptPairing()

    def bluetooth_toggle_state(self, state):
        """Stub for Fuchsia implementation."""
        pass

    def get_pairing_pin(self):
        """ Get the pairing pin from the active pairing delegate.
        """
        return self.device.btc_lib.getPairingPin()['result']

    def input_pairing_pin(self, pin):
        """ Input pairing pin to active pairing delegate.

        Args:
            pin: The pin to input.
        """
        self.device.btc_lib.inputPairingPin(pin)

    def initialize_bluetooth_controller(self):
        """ Initialize Bluetooth controller for first time use.
        """
        self.device.btc_lib.initBluetoothControl()

    def get_local_bluetooth_address(self):
        """ Returns the Bluetooth local address.
        """
        return self.device.btc_lib.getActiveAdapterAddress().get("result")

    def set_bluetooth_local_name(self, name):
        """ Sets the Bluetooth controller's local name
        Args:
            name: The name to set.
        """
        self.device.btc_lib.setName(name)

    def gatt_connect(self, peer_identifier, transport, autoconnect):
        """ Perform a GATT connection to a perihperal.

        Args:
            peer_identifier: The peer to connect to.
            transport: Not implemented.
            autoconnect: Not implemented.
        Returns:
            True if success, False if failure.
        """
        connection_result = self.device.gattc_lib.bleConnectToPeripheral(
            peer_identifier)
        if connection_result.get("error") is None:
            self.log.error("Failed to connect to peer id {}: {}".format(
                peer_identifier, connection_result.get("error")))
            return False
        return True

    def gatt_client_refresh(self, peer_identifier):
        """ Perform a GATT Client Refresh of a perihperal.

        Clears the internal cache and forces a refresh of the services from the
        remote device. In Fuchsia there is no FIDL api to automatically do this
        yet. Therefore just read all Characteristics which satisfies the same
        requirements.

        Args:
            peer_identifier: The peer to refresh.
        """
        self._read_all_characteristics(peer_identifier)

    def gatt_client_discover_characteristic_by_uuid(self, peer_identifier,
                                                    uuid):
        """ Perform a GATT Client Refresh of a perihperal.

        Clears the internal cache and forces a refresh of the services from the
        remote device. In Fuchsia there is no FIDL api to automatically do this
        yet. Therefore just read all Characteristics which satisfies the same
        requirements.

        Args:
            peer_identifier: The peer to refresh.
        """
        self._read_all_characteristics(peer_identifier, uuid)

    def gatt_disconnect(self, peer_identifier):
        """ Perform a GATT disconnect from a perihperal.

        Args:
            peer_identifier: The peer to disconnect from.
        Returns:
            True if success, False if failure.
        """
        disconnect_result = self.device.gattc_lib.bleDisconnectPeripheral(
            peer_identifier)
        if disconnect_result.get("error") is None:
            self.log.error("Failed to disconnect from peer id {}: {}".format(
                peer_identifier, disconnect_result.get("error")))
            return False
        return True

    def reset_bluetooth(self):
        """Stub for Fuchsia implementation."""
        pass

    def start_le_advertisement(self, adv_data, adv_interval):
        """ Starts an LE advertisement

        Args:
            adv_data: Advertisement data.
            adv_interval: Advertisement interval.
        """
        self.device.ble_lib.bleStartBleAdvertising(adv_data, adv_interval)

    def stop_le_advertisement(self):
        """ Stop active LE advertisement.
        """
        self.device.ble_lib.bleStopBleAdvertising()

    def setup_gatt_server(self, database):
        """ Sets up an input GATT server.

        Args:
            database: A dictionary representing the GATT database to setup.
        """
        self.device.gatts_lib.publishServer(database)

    def close_gatt_server(self):
        """ Closes an existing GATT server.
        """
        self.device.gatts_lib.closeServer()

    def le_scan_with_name_filter(self, name, timeout):
        """ Scan over LE for a specific device name.

        Args:
            name: The name filter to set.
            timeout: The timeout to wait to find the advertisement.
        Returns:
            Discovered device id or None
        """
        return le_scan_for_device_by_name(self.device, self.device.log, name,
                                          timeout)

    def log_info(self, log):
        """ Log directly onto the device.

        Args:
            log: The informative log.
        """
        self.device.logging_lib.logI(log)
        pass

    def unbond_all_known_devices(self):
        """ Unbond all known remote devices.
        """
        try:
            device_list = self.device.btc_lib.getKnownRemoteDevices()['result']
            for device_info in device_list:
                device = device_list[device_info]
                if device['bonded']:
                    self.device.btc_lib.forgetDevice(device['id'])
        except Exception as err:
            self.log.err("Unable to unbond all devices: {}".format(err))

    def unbond_device(self, peer_identifier):
        """ Unbond peer identifier.

        Args:
            peer_identifier: The peer identifier for the peer to unbond.

        """
        self.device.btc_lib.forgetDevice(peer_identifier)

    def _read_all_characteristics(self, peer_identifier, uuid=None):
        fail_err = "Failed to read all characteristics with: {}"
        try:
            services = self.device.gattc_lib.listServices(peer_identifier)
            for service in services['result']:
                service_id = service['id']
                service_uuid = service['uuid_type']
                self.device.gattc_lib.connectToService(peer_identifier,
                                                       service_id)
                chars = self.device.gattc_lib.discoverCharacteristics()
                self.log.info(
                    "Reading chars in service uuid: {}".format(service_uuid))

                for char in chars['result']:
                    char_id = char['id']
                    char_uuid = char['uuid_type']
                    if uuid and uuid.lower() not in char_uuid.lower():
                        continue
                    try:
                        read_val =  \
                            self.device.gattc_lib.readCharacteristicById(
                                char_id)
                        self.log.info(
                            "\tCharacteristic uuid / Value: {} / {}".format(
                                char_uuid, read_val['result']))
                        str_value = ""
                        for val in read_val['result']:
                            str_value += chr(val)
                        self.log.info("\t\tstr val: {}".format(str_value))
                    except Exception as err:
                        self.log.error(err)
                        pass
        except Exception as err:
            self.log.error(fail_err.forma(err))

    def _perform_read_all_descriptors(self, peer_identifier):
        fail_err = "Failed to read all characteristics with: {}"
        try:
            services = self.device.gattc_lib.listServices(peer_identifier)
            for service in services['result']:
                service_id = service['id']
                service_uuid = service['uuid_type']
                self.device.gattc_lib.connectToService(peer_identifier,
                                                       service_id)
                chars = self.device.gattc_lib.discoverCharacteristics()
                self.log.info(
                    "Reading descs in service uuid: {}".format(service_uuid))

                for char in chars['result']:
                    char_id = char['id']
                    char_uuid = char['uuid_type']
                    descriptors = char['descriptors']
                    self.log.info(
                        "\tReading descs in char uuid: {}".format(char_uuid))
                    for desc in descriptors:
                        desc_id = desc["id"]
                        desc_uuid = desc["uuid_type"]
                    try:
                        read_val = self.device.gattc_lib.readDescriptorById(
                            desc_id)
                        self.log.info(
                            "\t\tDescriptor uuid / Value: {} / {}".format(
                                desc_uuid, read_val['result']))
                    except Exception as err:
                        pass
        except Exception as err:
            self.log.error(fail_err.format(err))
