#/usr/bin/env python3
#
# Copyright (C) 2018 The Android Open Source Project
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
"""Bluetooth 1st time force pair and connect test implementation."""
# Quick way to get the Apollo serial number:
# python3.5 -c "from acts.controllers.buds_lib.apollo_lib import get_devices; [print(d['serial_number']) for d in get_devices()]"

import os
import time
import traceback
import uuid

from acts.base_test import BaseTestClass
from acts.base_test import Error
from acts.controllers.buds_lib.apollo_lib import DeviceError, ParentDevice as ApolloDevice
#from acts.controllers.buds_lib.data_storage.bigquery import bigquery_buffer as bq
from acts.controllers.buds_lib.test_actions.apollo_acts import ApolloTestActions
from acts.test_utils.bt.bt_test_utils import clear_bonded_devices
from acts.test_utils.bt.bt_test_utils import enable_bluetooth
from acts.utils import set_location_service

# Save to both x20 and big query
DEFAULT_BIGQUERY_DATASET_ID = 'apollo'
DEFAULT_BIGQUERY_SUMMARY_TABLE = 'bluetooth_pair_connect_summary_v0_2'
DEFAULT_BIGQUERY_MEASUREMENT_TABLE = 'bluetooth_pair_connect_measurement_v0_2'

# define CSV headers.
APOLLO_BTSTATUS_CONVERSION = {
    # Below is from GetConnDevices
    'btdevs_HFP': 'HFP Pri',
    'btdevs_A2DP': 'A2DP Pri',
    'btdevs_RFCOMM_CTRL': 'CTRL',
    'btdevs_RFCOMM_AUDIO': 'AUDIO',
    'btdevs_RFCOMM_DEBUG': 'DEBUG',
    'btdevs_RFCOMM_TRANS': 'TRANS'
}


def get_uuid():
    """Get a UUID for the test."""
    return str(uuid.uuid1())


class BluetoothDeviceNotFound(Error):
    pass


class BluetoothTestException(Error):
    pass


class BluetoothPairAndConnectTest(BaseTestClass):
    """Class representing a TestCase object for handling execution of tests."""

    def __init__(self, configs):
        BaseTestClass.__init__(self, configs)
        # sanity check of the dut devices.
        # TODO: is it possible to move this sanity check to a device config validator?
        if not self.android_devices:
            raise BluetoothDeviceNotFound(
                'Cannot find android phone (need at least one).')
        self.phone = self.android_devices[0]

        if not self.buds_devices:
            raise BluetoothDeviceNotFound(
                'Cannot find apollo device (need at least one).')
        self.apollo = self.buds_devices[0]
        self.log.info('Successfully found needed devices.')

        # some default values
        self.result_name = 'Undefined'
        self.result_path = 'Undefined'
        self.t_test_start_time = 'Undefined'
        self.t_test_uuid = get_uuid()

        # Staging the test, create result object, etc.
        self.apollo_act = ApolloTestActions(self.apollo, self.log)
        self.dut_bt_addr = self.apollo.bluetooth_address
        self.iteration = 1

    def setup_test(self):
        # Get device fw build info for output directory.
        # TODO: find a better way to put them into a library.
        retry = 0
        version = 'Unknown'
        while retry < 3:
            try:
                success, info = self.apollo.get_version()
                if success and 'Fw Build Label' in info:
                    version = info['Fw Build Label']
                    # strip quotation
                    if version.startswith('"') and version.endswith('"'):
                        version = version[1:-1]
                    break
                else:
                    retry += 1
                    time.sleep(1)
            except DeviceError:
                self.log.warning(
                    'Failed to read apollo build label, retrying...')
        phone_model = self.phone.model
        phone_os_version = self.phone.adb.getprop('ro.build.version.release')
        t_test_start_time = time.strftime('%Y_%m_%d-%H_%M_%S')
        self.t_test_start_time = t_test_start_time
        result_dir = "wearables_logs"
        result_path = os.path.join(self.log_path, result_dir)
        self.log.info('Test result path: %s' % result_path)
        try:
            os.makedirs(result_path)
        except os.error as ex:
            self.log.warning('Cannot create result log path %s.' % result_path)
            raise ex
        self.result_name = result_dir
        self.result_path = result_path

        # Get the metadata
        metadata = self.get_metadata_info()
        # dump metadata to BQ, one record per test
        #bq.log(DEFAULT_BIGQUERY_DATASET_ID, DEFAULT_BIGQUERY_SUMMARY_TABLE,
        #       metadata)

        # make sure bluetooth is on
        enable_bluetooth(self.phone.droid, self.phone.ed)
        set_location_service(self.phone, True)
        self.log.info('===== START BLUETOOTH CONNECTION TEST  =====')
        return True

    def teardown_test(self):
        self.log.info('Teardown test, shutting down all services...')
        self.apollo.close()
        return True

    def test_bluetooth_connect(self):
        """Main test method."""
        # for now let's handle all exception here
        is_success = False
        try:
            # Actual test steps:
            clear_bonded_devices(self.phone)
            self.apollo_act.factory_reset()
            time.sleep(5)
            self.phone.droid.bluetoothDiscoverAndBond(self.dut_bt_addr)
            is_success = self.apollo_act.wait_for_bluetooth_a2dp_hfp()

            # Done, write results.
            apollo_res = self.apollo_act.measurement_timer.elapsed()
            # TODO: Investigate import errors, skip for now
            #phone_res = self.phone_act.measurement_timer.elapsed()
            #self._write_results(phone_res, apollo_res)

        # TODO: figure out what exception should be handled, what should be raised.
        except DeviceError as ex:
            # Apollo gave us an error. Report and skip to next iteration.
            # TODO: add recovery/reset code in post test?
            self.log.warning('Apollo reporting error: %s' % ex)
        except Error as ex:
            # should only catch test related exception
            self.log.warning('Error executing test case: %s' % ex)
        except Exception as ex:
            # now we have a problem.
            self.log.warning('Error executing test case: %s' % ex)
            self.log.warning('Abort.')
            #traceback.print_exc()
        return is_success

    def get_metadata_info(self):
        metadata = dict()
        metadata['uuid'] = self.t_test_uuid
        metadata['start_time'] = self.t_test_start_time
        # Merge device metadata into master metadata.
        phone_metadata = self.phone.device_info
        for key in phone_metadata:
            metadata['phone_' + key] = phone_metadata[key]
        apollo_metadata = self.apollo.get_info()
        for key in apollo_metadata:
            metadata['apollo_' + key] = apollo_metadata[key]
        return metadata

    def _write_results(self, phone_res, apollo_res):
        """Custom logic to parse and save the time measurements.

        Save the measurements to x20 and big query.

        Args:
          phone_res: time measurement from the phone, should only contain bond time
          apollo_res: time measurements from Apollo, should contain profile
                      connection time.
        """
        all_cols = []
        all_vals = []
        # profile connect time. Add header text conversion here.
        sorted_header_keys = sorted(APOLLO_BTSTATUS_CONVERSION.keys())
        for key in sorted_header_keys:
            # header names in CSV
            all_cols.append(key)
            profile_name = APOLLO_BTSTATUS_CONVERSION[key]
            if profile_name in apollo_res:
                all_vals.append(apollo_res[profile_name])
            else:
                all_vals.append(0)

        # Now get all bond/connect time.
        all_conn_time = max(all_vals)
        all_cols.insert(0, 'all_connect')
        all_vals.insert(0, all_conn_time)

        if 'bond' in phone_res:
            all_bond_time = phone_res['bond']
            self.log.info('bond %f' % all_bond_time)
        else:
            all_bond_time = 0
            self.log.warning('Cannot find bond time, set bond time to 0.')
        all_cols.insert(0, 'all_bond')
        all_vals.insert(0, all_bond_time)

        all_cols.insert(0, 'Timestamps')
        all_vals.insert(0, time.strftime('%Y_%m_%d-%H_%M_%S'))
        all_cols.insert(0, 'Iteration')
        all_vals.insert(0, self.iteration)

        # Write to BQ
        res_dict = dict(zip(all_cols, all_vals))
        res_dict['uuid'] = self.t_test_uuid
        #bq.log(DEFAULT_BIGQUERY_DATASET_ID, DEFAULT_BIGQUERY_MEASUREMENT_TABLE,
        #       res_dict)

        # Now write to x20.
        res_path = os.path.join(self.result_path, 'bt_time_record.csv')
        # write the header only when creating new file.
        write_header = False
        if not os.path.isfile(res_path):
            write_header = True
        try:
            self.log.info('Writing to %s...' % res_path)
            self.log.info(','.join(all_cols))
            self.log.info(','.join(str(x) for x in all_vals))

            with open(res_path, 'ab') as file_handle:
                if write_header:
                    file_handle.write(','.join(all_cols))
                    file_handle.write('\n')
                file_handle.write(','.join(str(x) for x in all_vals))
                file_handle.write('\n')
            self.log.info('Result file updated in x20.')
        except IOError as ex:
            self.log.warning(ex.message)
            raise ex
