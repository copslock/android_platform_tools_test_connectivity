#!/usr/bin/env python3
#
# Copyright (C) 2019 The Android Open Source Project
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
"""This is the PTS base class that is inherited from all PTS
Tests.
"""


import ctypes
import pprint
import random
import time

from ctypes import *
from datetime import datetime

from acts.base_test import BaseTestClass
from acts.controllers.bluetooth_pts_device import VERDICT_STRINGS
from acts.controllers.fuchsia_device import FuchsiaDevice
from acts.signals import TestSignal
from acts.test_utils.abstract_devices.bluetooth_device import create_bluetooth_device
from acts.test_utils.fuchsia.bt_test_utils import le_scan_for_device_by_name


class PtsBaseClass(BaseTestClass):
    """ Class for representing common functionality across all PTS tests.

    This includes the ability to rerun tests due to PTS instability,
    common PTS action mappings, and setup/teardown related devices.

    """
    scan_timeout_seconds = 10
    peer_identifier = None

    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        if 'dut' in self.user_params:
            if self.user_params['dut'] == 'fuchsia_devices':
                self.dut = create_bluetooth_device(self.fuchsia_devices[0])
            elif self.user_params['dut'] == 'android_devices':
                self.dut = create_bluetooth_device(self.android_devices[0])
            else:
                raise ValueError('Invalid DUT specified in config. (%s)' %
                                 self.user_params['dut'])
        else:
            # Default is an fuchsia device
            self.dut = create_bluetooth_device(self.fuchsia_devices[0])

        self.characteristic_read_not_permitted_uuid = self.user_params.get(
            "characteristic_read_not_permitted_uuid")
        self.characteristic_read_not_permitted_handle = self.user_params.get(
            "characteristic_read_not_permitted_handle")
        self.characteristic_read_invalid_handle = self.user_params.get(
            "characteristic_read_invalid_handle")
        self.characteristic_attribute_not_found_uuid = self.user_params.get(
            "characteristic_attribute_not_found_uuid")
        self.characteristic_write_not_permitted_handle = self.user_params.get(
            "characteristic_write_not_permitted_handle")

        self.pts = self.bluetooth_pts_device[0]
        self.pts_action_mapping = {
            2: self.perform_gatt_connection,
            3: self.perform_gatt_disconnection,
            10: self.discover_all_primary_services_on_peripheral,
            15: self.discover_all_services_on_peripheral,
            17: self.confirm_specific_primary_uuids_on_peripheral,
            24: self.confirm_included_services_on_peripheral,
            26: self.confirm_no_services_on_peripheral,
            29: self.discover_characteristic_by_uuid,
            48: self.read_characteristic_by_handle,
            110: self.enter_gatt_characteristic_read_not_permitted_handle,
            111: self.enter_gatt_characteristic_read_not_permitted_uuid,
            118: self.enter_gatt_characteristic_invalid_handle,
            119: self.enter_gatt_characteristic_attribute_not_found_uuid,
            120: self.enter_gatt_characteristic_write_not_permitted_handle,
            2000: self.enter_secure_id_from_dut,
        }

    def setup_class(self):
        self.pts.setup_pts()
        self.pts.bind_to(self.process_next_action)

    def teardown_class(self):
        self.pts.clean_up()

    def setup_test(self):
        # Always start the test with RESULT_INCOMP
        self.pts.pts_test_result = VERDICT_STRINGS['RESULT_INCOMP']

    def teardown_test(self):
        return True

    @staticmethod
    def pts_test_wrap(fn):
        def _safe_wrap_test_case(self, *args, **kwargs):
            test_id = "{}:{}:{}".format(self.__class__.__name__, fn.__name__,
                                        time.time())
            log_string = "[Test ID] {}".format(test_id)
            self.log.info(log_string)
            try:
                self.dut.log_info("Started " + log_string)
                result = fn(self, *args, **kwargs)
                self.dut.log_info("Finished " + log_string)
                rerun_count = self.user_params.get("pts_auto_rerun_count", 0)
                for i in range(int(rerun_count)):
                    print("MY RESULT {}".format(result))
                    if result is not True:
                        self.teardown_test()
                        log_string = "[Rerun Test ID] {}. Run #{} run failed... Retrying".format(
                            test_id, i + 1)
                        self.log.info(log_string)
                        self.setup_test()
                        self.dut.log_info("Rerun Started " + log_string)
                        result = fn(self, *args, **kwargs)
                    else:
                        return result
                return result
            except TestSignal:
                raise
            except Exception as e:
                self.log.error(traceback.format_exc())
                self.log.error(str(e))
                raise
            return fn(self, *args, **kwargs)

        return _safe_wrap_test_case

    def process_next_action(self, action):
        func = self.pts_action_mapping.get(action, "Nothing")
        if func is not 'Nothing':
            func()

    def enter_gatt_characteristic_read_not_permitted_uuid(self):
        self.pts.extra_answers.append(
            self.characteristic_read_not_permitted_uuid)

    def enter_gatt_characteristic_read_not_permitted_handle(self):
        self.pts.extra_answers.append(
            self.characteristic_read_not_permitted_handle)

    def enter_gatt_characteristic_invalid_handle(self):
        self.pts.extra_answers.append(self.characteristic_read_invalid_handle)

    def enter_gatt_characteristic_attribute_not_found_uuid(self):
        self.pts.extra_answers.append(
            self.characteristic_attribute_not_found_uuid)

    def enter_gatt_characteristic_write_not_permitted_handle(self):
        self.pts.extra_answers.append(
            self.characteristic_write_not_permitted_handle)

    def enter_secure_id_from_dut(self):
        self.pts.extra_answers.append(self.dut.get_pairing_pin())

    def discover_characteristic_by_uuid(self, uuid):
        self.dut.gatt_client_discover_characteristic_by_uuid(
            self.peer_identifier, uuid)

    def perform_gatt_connection(self):
        autoconnect = False
        transport = gatt_transport['le']
        self.peer_identifier = self.dut.le_scan_with_name_filter(
            adv_name, self.scan_timeout_seconds)
        if self.peer_identifier is None:
            raise signals.TestFailure("Scanner unable to find advertisement.")
        if not self.dut.gatt_connect(self.peer_identifier, transport,
                                     autoconnect):
            raise signals.TestFailure("Unable to connect to peripheral.")

    def perform_gatt_disconnection(self):
        if not self.dut.gatt_disconnect(self.peer_identifier):
            raise signals.TestFailure("Failed to disconnect from peer.")

    def discover_all_primary_services_on_peripheral(self):
        self.dut.gatt_refresh()

    def discover_all_services_on_peripheral(self):
        self.dut.gatt_refresh()

    def _run_test_with_input_gatt_server_db(self, test_name, gatt_database):
        # Setup Fuchsia Device for test.
        adv_data = {"name": self.dut_bluetooth_local_name}
        self.dut.start_le_advertisement(adv_data, self.ble_advertise_interval)
        self.dut.setup_gatt_server(gatt_database)

        test_result = self.pts.execute_test(test_name)
        self.dut.stop_le_advertisement()
        return test_result

    def confirm_specific_primary_uuids_on_peripheral(self):
        # TODO: Write verifyier that 1800 and 1801 exists. For now just pass.
        return True

    def confirm_no_services_on_peripheral(self):
        # TODO: Write verifyier that no services exist. For now just pass.
        return True

    def confirm_included_services_on_peripheral(self, uuid_description):
        # TODO: Write verifyier that input services exist. For now just pass.
        # Note: List comes in the form of a long string to parse:
        # Attribute Handle = '0002'O Included Service Attribute handle = '0080'O,End Group Handle = '0085'O,Service UUID = 'A00B'O
        # \n
        # Attribute Handle = '0021'O Included Service Attribute handle = '0001'O,End Group Handle = '0006'O,Service UUID = 'A00D'O
        # \n ...
        return True

    def read_characteristic_by_handle(self, handle):
        self.dut.gatt_client_ready_characteristic_by_handle(
            self.peer_identifier, handle)
