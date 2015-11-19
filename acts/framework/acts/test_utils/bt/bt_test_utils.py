# python3.4
# Copyright (C) 2014 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import random
import pprint
import string
import queue
import threading
import time

from contextlib import suppress

from acts.logger import LoggerProxy
from acts.test_utils.bt.BleEnum import *
from acts.test_utils.bt.BtEnum import *
from acts.utils import exe_cmd

default_timeout = 10
# bt discovery timeout
default_discovery_timeout = 3
log = LoggerProxy()

# Callback strings
characteristic_write_request = "GattServer{}onCharacteristicWriteRequest"
characteristic_write = "GattConnect{}onCharacteristicWrite"
descriptor_write_request = "GattServer{}onDescriptorWriteRequest"
descriptor_write = "GattConnect{}onDescriptorWrite"
read_remote_rssi = "GattConnect{}onReadRemoteRssi"
gatt_services_discovered = "GattConnect{}onServicesDiscovered"
scan_result = "BleScan{}onScanResults"
scan_failed = "BleScan{}onScanFailed"
service_added = "GattServer{}onServiceAdded"
batch_scan_result = "BleScan{}onBatchScanResult"
adv_fail = "BleAdvertise{}onFailure"
adv_succ = "BleAdvertise{}onSuccess"
bluetooth_off = "BluetoothStateChangedOff"
bluetooth_on = "BluetoothStateChangedOn"
mtu_changed = "GattConnect{}onMtuChanged"

# rfcomm test uuids
rfcomm_secure_uuid = "fa87c0d0-afac-11de-8a39-0800200c9a66"
rfcomm_insecure_uuid = "8ce255c0-200a-11e0-ac64-0800200c9a66"

advertisements_to_devices = {
    "Nexus 4": 0,
    "Nexus 5": 0,
    "Nexus 5X":15,
    "Nexus 7": 0,
    "Nexus Player": 1,
    "Nexus 6": 4,
    "Nexus 6P": 4,
    "AOSP on Shamu": 4,
    "Nexus 9": 4,
    "Sprout": 10,
    "Micromax AQ4501": 10,
    "4560MMX": 10,
    "G Watch R": 1,
    "Gear Live": 1,
    "SmartWatch 3": 1,
    "Zenwatch": 1,
    "AOSP on Shamu": 4,
    "MSM8992 for arm64": 9,
    "LG Watch Urbane": 1,
    "Pixel C":4,
    "angler": 4,
    "bullhead": 15,
}

batch_scan_supported_list = {
    "Nexus 4": False,
    "Nexus 5": False,
    "Nexus 7": False,
    "Nexus Player": True,
    "Nexus 6": True,
    "Nexus 6P": True,
    "Nexus 5X": True,
    "AOSP on Shamu": True,
    "Nexus 9": True,
    "Sprout": True,
    "Micromax AQ4501": True,
    "4560MMX": True,
    "Pixel C":True,
    "G Watch R": True,
    "Gear Live": True,
    "SmartWatch 3": True,
    "Zenwatch": True,
    "AOSP on Shamu": True,
    "MSM8992 for arm64": True,
    "LG Watch Urbane": True,
    "angler": True,
    "bullhead": True,
}


def generate_ble_scan_objects(droid):
    filter_list = droid.bleGenFilterList()
    scan_settings = droid.bleBuildScanSetting()
    scan_callback = droid.bleGenScanCallback()
    return filter_list, scan_settings, scan_callback


def generate_ble_advertise_objects(droid):
    advertise_callback = droid.bleGenBleAdvertiseCallback()
    advertise_data = droid.bleBuildAdvertiseData()
    advertise_settings = droid.bleBuildAdvertiseSettings()
    return advertise_callback, advertise_data, advertise_settings


def extract_string_from_byte_array(string_list):
    """Extract the string from array of string list
    """
    start = 1
    end = len(string_list) - 1
    extract_string = string_list[start:end]
    return extract_string


def extract_uuidlist_from_record(uuid_string_list):
    """Extract uuid from Service UUID List
    """
    start = 1
    end = len(uuid_string_list) - 1
    uuid_length = 36
    uuidlist = []
    while start < end:
        uuid = uuid_string_list[start:(start + uuid_length)]
        start += uuid_length + 1
        uuidlist.append(uuid)
    return uuidlist


def build_advertise_settings(droid, mode, txpower, type):
    """Build Advertise Settings
    """
    droid.bleSetAdvertiseSettingsAdvertiseMode(mode)
    droid.bleSetAdvertiseSettingsTxPowerLevel(txpower)
    droid.bleSetAdvertiseSettingsIsConnectable(type)
    settings = droid.bleBuildAdvertiseSettings()
    return settings

def setup_multiple_devices_for_bt_test(droids, eds):
    log.info("Setting up Android Devices")
    threads = []
    for i in range(len(droids)):
        thread = threading.Thread(target=reset_bluetooth,
                                      args=([droids[i]],[eds[i]]))
        threads.append(thread)
        thread.start()
    for t in threads:
        t.join()

    for d in droids:
        setup_result = d.bluetoothSetLocalName(generate_id_by_size(4))
        if not setup_result:
            return setup_result
        d.bluetoothDisableBLE()
        bonded_devices = d.bluetoothGetBondedDevices()
        for b in bonded_devices:
            d.bluetoothUnbond(b['address'])
    for x in range(len(droids)):
        droid, ed = droids[x], eds[x]
        setup_result = droid.bluetoothConfigHciSnoopLog(True)
        if not setup_result:
            return setup_result
    return setup_result


def reset_bluetooth(droids, eds):
    """Resets bluetooth on the list of android devices passed into the function.
    :param android_devices: list of android devices
    :return: bool
    """
    for x in range(len(droids)):
        droid, ed = droids[x], eds[x]
        log.info(
            "Reset state of bluetooth on device: {}".format(
                droid.getBuildSerial()))
        if droid.bluetoothCheckState() is True:
            droid.bluetoothToggleState(False)
            expected_bluetooth_off_event_name = bluetooth_off
            try:
                ed.pop_event(
                    expected_bluetooth_off_event_name, default_timeout)
            except Exception:
                log.info("Failed to toggle Bluetooth off.")
                return False
        # temp sleep for b/17723234
        time.sleep(3)
        droid.bluetoothToggleState(True)
        expected_bluetooth_on_event_name = bluetooth_on
        try:
            ed.pop_event(expected_bluetooth_on_event_name, default_timeout)
        except Exception:
            log.info("Failed to toggle Bluetooth on.")
            return False
    return True


def get_advanced_droid_list(droids, eds):
    droid_list = []
    for i in range(len(droids)):
        d = droids[i]
        e = eds[i]
        model = d.getBuildModel()
        print (model)
        max_advertisements = 0
        batch_scan_supported = True
        if model in advertisements_to_devices.keys():
            max_advertisements = advertisements_to_devices[model]
        if model in batch_scan_supported_list.keys():
            batch_scan_supported = batch_scan_supported_list[model]
        role = {
            'droid': d,
            'ed': e,
            'max_advertisements': max_advertisements,
            'batch_scan_supported': batch_scan_supported
        }
        droid_list.append(role)
    return droid_list


def generate_id_by_size(size,
                        chars=(string.ascii_lowercase +
                               string.ascii_uppercase + string.digits)):
    return ''.join(random.choice(chars) for _ in range(size))


def cleanup_scanners_and_advertisers(scan_droid, scan_ed, scan_callback_list,
                                     adv_droid, adv_ed, adv_callback_list):
    """
    Try to gracefully stop all scanning and advertising instances.
    """
    try:
        for scan_callback in scan_callback_list:
            scan_droid.bleStopBleScan(scan_callback)
    except Exception:
        reset_bluetooth([scan_droid], [scan_ed])
    try:
        for adv_callback in adv_callback_list:
            adv_droid.bleStopBleAdvertising(adv_callback)
    except Exception:
        reset_bluetooth([adv_droid], [adv_ed])


def setup_gatt_characteristics(droid, input):
    characteristic_list = []
    for item in input:
        index = droid.gattServerCreateBluetoothGattCharacteristic(
            item['uuid'],
            item['property'],
            item['permission'])
        characteristic_list.append(index)
    return characteristic_list


def setup_gatt_descriptors(droid, input):
    descriptor_list = []
    for item in input:
        index = droid.gattServerCreateBluetoothGattDescriptor(
            item['uuid'],
            item['property'],
        )
        descriptor_list.append(index)
    log.info("setup descriptor list: {}".format(descriptor_list))
    return descriptor_list


def get_mac_address_of_generic_advertisement(scan_droid, scan_ed, adv_droid,
                                             adv_ed):
    adv_droid.bleSetAdvertiseDataIncludeDeviceName(True)
    adv_droid.bleSetAdvertiseSettingsAdvertiseMode(
        AdvertiseSettingsAdvertiseMode.ADVERTISE_MODE_LOW_LATENCY.value)
    adv_droid.bleSetAdvertiseSettingsIsConnectable(True)
    adv_droid.bleSetAdvertiseSettingsTxPowerLevel(
        AdvertiseSettingsAdvertiseTxPower.ADVERTISE_TX_POWER_HIGH.value)
    advertise_callback, advertise_data, advertise_settings = (
        generate_ble_advertise_objects(adv_droid))
    adv_droid.bleStartBleAdvertising(
        advertise_callback, advertise_data, advertise_settings)
    adv_ed.pop_event("BleAdvertise{}onSuccess".format(
        advertise_callback), default_timeout)
    filter_list = scan_droid.bleGenFilterList()
    scan_settings = scan_droid.bleBuildScanSetting()
    scan_callback = scan_droid.bleGenScanCallback()
    scan_droid.bleSetScanFilterDeviceName(adv_droid.bluetoothGetLocalName())
    scan_droid.bleBuildScanFilter(filter_list)
    scan_droid.bleStartBleScan(filter_list, scan_settings, scan_callback)
    event = scan_ed.pop_event(
        "BleScan{}onScanResults".format(scan_callback), default_timeout)
    mac_address = event['data']['Result']['deviceInfo']['address']
    scan_droid.bleStopBleScan(scan_callback)
    return mac_address, advertise_callback


def setup_gatt_connection(cen_droid, cen_ed, mac_address, autoconnect):
    test_result = True
    gatt_callback = cen_droid.gattCreateGattCallback()
    log.info("Gatt Connect to mac address {}.".format(mac_address))
    bluetooth_gatt = cen_droid.gattClientConnectGatt(
        gatt_callback, mac_address,
        autoconnect)
    event = cen_ed.pop_event(
        "GattConnect{}onConnectionStateChange".format(gatt_callback),
        default_timeout)
    if event['data']['State'] != GattConnectionState.STATE_CONNECTED.value:
        log.info("Could not establish a connection to peripheral. Event "
                 "Details:".format(pprint.pformat(event)))
        test_result = False
    # To avoid race condition of quick connect/disconnect
    time.sleep(1)
    return test_result, bluetooth_gatt, gatt_callback


def disconnect_gatt_connection(cen_droid, cen_ed, bluetooth_gatt, gatt_callback):
    cen_droid.gattClientDisconnect(bluetooth_gatt)
    event = cen_ed.pop_event(
        "GattConnect{}onConnectionStateChange".format(gatt_callback),
        default_timeout)
    if event['data']['State'] != GattConnectionState.STATE_DISCONNECTED.value:
        return False
    return True


def orchestrate_gatt_connection(cen_droid, cen_ed, per_droid, per_ed, le=True,
                                mac_address=None):
    adv_callback = None
    if mac_address is None:
        if le:
            mac_address, adv_callback = (
                get_mac_address_of_generic_advertisement(cen_droid, cen_ed,
                                                         per_droid, per_ed))
        else:
            mac_address = get_bt_mac_address(cen_droid, per_droid, le)
            adv_callback = None
    autoconnect = False
    test_result, bluetooth_gatt, gatt_callback = setup_gatt_connection(
        cen_droid, cen_ed, mac_address, autoconnect)
    if not test_result:
        log.info("Could not connect to peripheral.")
        return False
    return bluetooth_gatt, gatt_callback, adv_callback


def run_continuous_write_descriptor(
        cen_droid, cen_ed, per_droid, per_ed, gatt_server, gatt_server_callback,
        bluetooth_gatt, services_count, discovered_services_index):
    log.info("starting continuous write")
    bt_device_id = 0
    status = 1
    offset = 1
    test_value = "1,2,3,4,5,6,7"
    test_value_return = "1,2,3"
    from contextlib import suppress
    with suppress(Exception):
        for x in range(100000):
            for i in range(services_count):
                characteristic_uuids = (
                    cen_droid.gattClientGetDiscoveredCharacteristicUuids(
                        discovered_services_index, i))
                log.info(characteristic_uuids)
                for characteristic in characteristic_uuids:
                    descriptor_uuids = (
                        cen_droid.gattClientGetDiscoveredDescriptorUuids(
                            discovered_services_index, i, characteristic))
                    log.info(descriptor_uuids)
                    for descriptor in descriptor_uuids:
                        log.info(
                            "descriptor to be written {}".format(descriptor))
                        cen_droid.gattClientDescriptorSetValue(
                            bluetooth_gatt, discovered_services_index,
                            i, characteristic, descriptor, test_value)
                        cen_droid.gattClientWriteDescriptor(
                            bluetooth_gatt, discovered_services_index,
                            i, characteristic, descriptor)
                        event = per_ed.pop_event(
                            descriptor_write_request.format(
                                gatt_server_callback), default_timeout)
                        log.info(
                            "onDescriptorWriteRequest event found: {}".format(
                                event))
                        request_id = event['data']['requestId']
                        found_value = event['data']['value']
                        if found_value != test_value:
                            log.info(
                                "Values didn't match. Found: {}, Expected: "
                                "{}".format(found_value, test_value))
                        per_droid.gattServerSendResponse(
                            gatt_server, bt_device_id, request_id, status,
                            offset, test_value_return)
                        log.info("onDescriptorWrite event found: {}".format(
                            cen_ed.pop_event(
                                descriptor_write.format(bluetooth_gatt),
                                default_timeout)))


def setup_characteristics_and_descriptors(droid):
    characteristic_input = [
        {
            'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
            'property': BluetoothGattCharacteristic.PROPERTY_WRITE.value |
                    BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE.value,
            'permission': BluetoothGattCharacteristic.PROPERTY_WRITE.value
        },
        {
            'uuid': "21c0a0bf-ad51-4a2d-8124-b74003e4e8c8",
            'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
                    BluetoothGattCharacteristic.PROPERTY_READ.value,
            'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
        },
        {
            'uuid': "6774191f-6ec3-4aa2-b8a8-cf830e41fda6",
            'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
                    BluetoothGattCharacteristic.PROPERTY_READ.value,
            'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
        },
    ]
    descriptor_input = [
        {
            'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
            'property': BluetoothGattDescriptor.PERMISSION_READ.value |
                    BluetoothGattDescriptor.PERMISSION_WRITE.value,
        },
        {
            'uuid': "76d5ed92-ca81-4edb-bb6b-9f019665fb32",
            'property': BluetoothGattDescriptor.PERMISSION_READ.value |
                    BluetoothGattCharacteristic.PERMISSION_WRITE.value,
        }
    ]
    characteristic_list = setup_gatt_characteristics(
        droid, characteristic_input)
    descriptor_list = setup_gatt_descriptors(droid, descriptor_input)
    return characteristic_list, descriptor_list


def setup_multiple_services(per_droid, per_ed):
    gatt_server_callback = per_droid.gattServerCreateGattServerCallback()
    gatt_server = per_droid.gattServerOpenGattServer(gatt_server_callback)
    characteristic_list, descriptor_list = (
        setup_characteristics_and_descriptors(per_droid))
    per_droid.gattServerCharacteristicAddDescriptor(
        characteristic_list[1], descriptor_list[0])
    per_droid.gattServerCharacteristicAddDescriptor(
        characteristic_list[2], descriptor_list[1])
    gattService = per_droid.gattServerCreateService(
        "00000000-0000-1000-8000-00805f9b34fb",
        BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
    gattService2 = per_droid.gattServerCreateService(
        "FFFFFFFF-0000-1000-8000-00805f9b34fb",
        BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
    gattService3 = per_droid.gattServerCreateService(
        "3846D7A0-69C8-11E4-BA00-0002A5D5C51B",
        BluetoothGattService.SERVICE_TYPE_PRIMARY.value)
    for characteristic in characteristic_list:
        per_droid.gattServerAddCharacteristicToService(
            gattService, characteristic)
    per_droid.gattServerAddService(gatt_server, gattService)
    per_ed.pop_event(service_added.format(gatt_server_callback),
                     default_timeout)
    for characteristic in characteristic_list:
        per_droid.gattServerAddCharacteristicToService(
            gattService2, characteristic)
    per_droid.gattServerAddService(gatt_server, gattService2)
    per_ed.pop_event(service_added.format(gatt_server_callback),
                     default_timeout)
    for characteristic in characteristic_list:
        per_droid.gattServerAddCharacteristicToService(gattService3,
                                                       characteristic)
    per_droid.gattServerAddService(gatt_server, gattService3)
    per_ed.pop_event(service_added.format(gatt_server_callback),
                     default_timeout)
    return gatt_server_callback, gatt_server


def setup_characteristics_and_descriptors(droid):
    characteristic_input = [
        {
            'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
            'property': BluetoothGattCharacteristic.PROPERTY_WRITE.value |
            BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE.value,
            'permission': BluetoothGattCharacteristic.PROPERTY_WRITE.value
        },
        {
            'uuid': "21c0a0bf-ad51-4a2d-8124-b74003e4e8c8",
            'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
            BluetoothGattCharacteristic.PROPERTY_READ.value,
            'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
        },
        {
            'uuid': "6774191f-6ec3-4aa2-b8a8-cf830e41fda6",
            'property': BluetoothGattCharacteristic.PROPERTY_NOTIFY.value |
            BluetoothGattCharacteristic.PROPERTY_READ.value,
            'permission': BluetoothGattCharacteristic.PERMISSION_READ.value
        },
    ]
    descriptor_input = [
        {
            'uuid': "aa7edd5a-4d1d-4f0e-883a-d145616a1630",
            'property': BluetoothGattDescriptor.PERMISSION_READ.value |
            BluetoothGattDescriptor.PERMISSION_WRITE.value,
        },
        {
            'uuid': "76d5ed92-ca81-4edb-bb6b-9f019665fb32",
            'property': BluetoothGattDescriptor.PERMISSION_READ.value |
            BluetoothGattCharacteristic.PERMISSION_WRITE.value,
        }
    ]
    characteristic_list = setup_gatt_characteristics(
        droid, characteristic_input)
    descriptor_list = setup_gatt_descriptors(droid, descriptor_input)
    return characteristic_list, descriptor_list


def get_device_local_info(droid):
    local_info_dict = {}
    local_info_dict['name'] = droid.bluetoothGetLocalName()
    local_info_dict['uuids'] = droid.bluetoothGetLocalUuids()
    return local_info_dict


def enable_bluetooth(droid, ed):
    if droid.bluetoothCheckState() is False:
        droid.bluetoothToggleState(True)
        if droid.bluetoothCheckState() is False:
            return False
    return True


def disable_bluetooth(droid, ed):
    if droid.bluetoothCheckState() is True:
        droid.bluetoothToggleState(False)
        if droid.bluetoothCheckState() is True:
            return False
    return True


def set_bt_scan_mode(droid, ed, scan_mode_value):
    if scan_mode_value == BluetoothScanModeType.STATE_OFF.value:
        disable_bluetooth(droid, ed)
        scan_mode = droid.bluetoothGetScanMode()
        reset_bluetooth([droid], [ed])
        if scan_mode != scan_mode_value:
            return False
    elif scan_mode_value == BluetoothScanModeType.SCAN_MODE_NONE.value:
        droid.bluetoothMakeUndiscoverable()
        scan_mode = droid.bluetoothGetScanMode()
        if scan_mode != scan_mode_value:
            return False
    elif scan_mode_value == BluetoothScanModeType.SCAN_MODE_CONNECTABLE.value:
        droid.bluetoothMakeUndiscoverable()
        droid.bluetoothMakeConnectable()
        scan_mode = droid.bluetoothGetScanMode()
        if scan_mode != scan_mode_value:
            return False
    elif (scan_mode_value ==
              BluetoothScanModeType.SCAN_MODE_CONNECTABLE_DISCOVERABLE.value):
        droid.bluetoothMakeDiscoverable()
        scan_mode = droid.bluetoothGetScanMode()
        if scan_mode != scan_mode_value:
            return False
    else:
        # invalid scan mode
        return False
    return True


def set_device_name(droid, name):
    droid.bluetoothSetLocalName(name)
    # temporary (todo:tturney fix)
    time.sleep(2)
    droid_name = droid.bluetoothGetLocalName()
    if droid_name != name:
        return False
    return True


def check_device_supported_profiles(droid):
    profile_dict = {}
    profile_dict['hid'] = droid.bluetoothHidIsReady()
    profile_dict['hsp'] = droid.bluetoothHspIsReady()
    profile_dict['a2dp'] = droid.bluetoothA2dpIsReady()
    profile_dict['avrcp'] = droid.bluetoothAvrcpIsReady()
    return profile_dict


def log_energy_info(droids, state):
    return_string = "{} Energy info collection:\n".format(state)
    for d in droids:
        with suppress(Exception):
            if (d.getBuildModel() == "Nexus 6" or d.getBuildModel() == "Nexus 9"
                or d.getBuildModel() == "Nexus 6P"
                or d.getBuildModel() == "Nexus5X"):

                description = ("Device: {}\tEnergyStatus: {}\n".format(
                    d.getBuildSerial(),
                    d.bluetoothGetControllerActivityEnergyInfo(1)))
                return_string = return_string + description
    return return_string


def pair_pri_to_sec(pri_droid, sec_droid):
    sec_droid.bluetoothMakeDiscoverable(default_timeout)
    pri_droid.bluetoothStartDiscovery()
    target_name = sec_droid.bluetoothGetLocalName()
    time.sleep(default_discovery_timeout)
    discovered_devices = pri_droid.bluetoothGetDiscoveredDevices()
    discovered = False
    for device in discovered_devices:
        log.info(device)
        if 'name' in device and target_name == device['name']:
            discovered = True
            continue
    if not discovered:
        return False
    pri_droid.bluetoothStartPairingHelper()
    sec_droid.bluetoothStartPairingHelper()
    result = pri_droid.bluetoothDiscoverAndBond(target_name)
    return result


def get_bt_mac_address(droid, droid1, make_undisocverable=True):
    droid1.bluetoothMakeDiscoverable(default_timeout)
    droid.bluetoothStartDiscovery()
    mac = ""
    target_name = droid1.bluetoothGetLocalName()
    time.sleep(default_discovery_timeout)
    discovered_devices = droid.bluetoothGetDiscoveredDevices()
    for device in discovered_devices:
        if 'name' in device.keys() and target_name == device['name']:
            mac = device['address']
            continue
    if make_undisocverable:
        droid1.bluetoothMakeUndiscoverable()
    droid.bluetoothCancelDiscovery()
    if mac == "":
        return False
    return mac


def get_client_server_bt_mac_address(droid, droid1):
    return get_bt_mac_address(droid, droid1), get_bt_mac_address(droid1, droid)


def take_btsnoop_logs(droids, testcase, testname):
    for d in droids:
        take_btsnoop_log(d, testcase, testname)

# TODO (tturney): Fix this.


def take_btsnoop_log(droid, testcase, test_name):
    """Grabs the btsnoop_hci log on a device and stores it in the log directory
    of the test class.

    If you want grab the btsnoop_hci log, call this function with android_device
    objects in on_fail. Bug report takes a relative long time to take, so use
    this cautiously.

    Params:
      test_name: Name of the test case that triggered this bug report.
      android_device: The android_device instance to take bugreport on.
    """
    test_name = "".join(x for x in test_name if x.isalnum())
    with suppress(Exception):
        serial = droid.getBuildSerial()
        device_model = droid.getBuildModel()
        device_model = device_model.replace(" ", "")
        out_name = ','.join((test_name, device_model, serial))
        cmd = ''.join(("adb -s ", serial, " pull /sdcard/btsnoop_hci.log > ",
                       testcase.log_path + "/" + out_name,
                       ".btsnoop_hci.log"))
        testcase.log.info("Test failed, grabbing the bt_snoop logs on {} {}."
                          .format(device_model, serial))
        exe_cmd(cmd)


def rfcomm_connect(droid, device_address):
    droid.bluetoothRfcommConnect(device_address)


def rfcomm_accept(droid):
    droid.bluetoothRfcommAccept()
