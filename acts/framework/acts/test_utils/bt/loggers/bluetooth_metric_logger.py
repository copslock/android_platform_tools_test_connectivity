# /usr/bin/env python3
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

import os

from acts.metrics.core import ProtoMetric
from acts.metrics.logger import MetricLogger

PROTO_PATH = os.path.join(os.path.dirname(__file__),
                          'protos',
                          'bluetooth_metric.proto')


class BluetoothMetricLogger(MetricLogger):
    """A logger for gathering Bluetooth test metrics

    Attributes:
        proto_module: Module used to store Bluetooth metrics in a proto
        results: Stores ProtoMetrics to be published for each logger context
        proto_map: Maps test case names to the appropriate protos for each case
    """

    def __init__(self, event):
        super().__init__(event=event)
        self.proto_module = self._compile_proto(PROTO_PATH)
        self.results = []

        self.proto_map = {'BluetoothPairAndConnectTest': self.proto_module
                              .BluetoothPairAndConnectTestResult(),
                          'BluetoothReconnectTest': self.proto_module
                              .BluetoothReconnectTestResult(),
                          'BluetoothThroughputTest': self.proto_module
                              .BluetoothDataTestResult(),
                          'BluetoothLatencyTest': self.proto_module
                              .BluetoothDataTestResult()
                          }

    @staticmethod
    def get_configuration_data(device):
        """Gets the configuration data of an Android device.

        Gets the configuration data of an Android device and organizes it in a
        dictionary.

        Args:
            device: The AndroidDevice to get the configuration data from

        Returns:
            A dictionary containing configuration data of an Android Device.
        """

        # TODO(b/124066126): Add remaining config data
        data = {'device_class': device.__class__.__name__,
                'device_model': device.model,
                'software_version': device.build_info['build_id'],
                'android_build_type': device.build_info['build_type'],
                'android_build_number': device.build_info[
                    'incremental_build_id']}

        return data

    def get_results(self, results, test, pri_device, conn_device=None):
        """Gets the metrics associated with each test case.

        Gets the test case metrics and configuration data for each test case and
        stores them for publishing.

        Args:
            results: A dictionary containing test metrics.
            test: The name of the test case associated with these results.
            pri_device: The primary AndroidDevice object for the test.
            conn_device: The connected AndroidDevice object for the test, if
                applicable.

        """

        result = self.proto_map[test]
        pri_device_proto = result.configuration_data.primary_device
        conn_device_proto = result.configuration_data.connected_device

        for metric in dir(result):
            if metric in results:
                setattr(result, metric, results[metric])

        pri_config = self.get_configuration_data(pri_device)

        for metric in dir(pri_device_proto):
            if metric in pri_config:
                setattr(pri_device_proto, metric, pri_config[metric])

        if conn_device:
            conn_config = self.get_configuration_data(conn_device)

            for metric in dir(conn_device_proto):
                if metric in conn_config:
                    setattr(conn_device_proto, metric, conn_config[metric])

        self.results.append(ProtoMetric(test, result))

    def end(self, event):
        return self.publisher.publish(self.results)
