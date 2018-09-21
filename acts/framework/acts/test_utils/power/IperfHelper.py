#!/usr/bin/env python3.4
#
#   Copyright 2018 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import math

import acts.controllers.iperf_server as ipf


class IperfHelper(object):
    """ Helps with iperf config and processing the results
    
    This class can be used to process the results of multiple iperf servers
    (for example, dual traffic scenarios). It also helps in setting the
    correct arguments for when using the phone as an iperf server
    """
    IPERF_CLIENT_RESULT_FILE_LOC_PHONE = '/sdcard/Download/'

    def __init__(self, config):
        self.traffic_type = config['traffic_type']
        self.traffic_direction = config['traffic_direction']
        self.duration = config['duration']
        self.port = config['port']
        self.server_idx = config['server_idx']
        self.use_client_output = False
        if 'bandwidth' in config:
            self.bandwidth = config['bandwidth']
        else:
            self.bandwidth = None
        if 'start_meas_time' in config:
            self.start_meas_time = config['start_meas_time']
        else:
            self.start_meas_time = 0

        iperf_args = '-i 1 -t {} -p {} -J'.format(self.duration, self.port)

        if self.traffic_type == "UDP":
            iperf_args = iperf_args + ' -u'
        if self.traffic_direction == "DL":
            iperf_args = iperf_args + ' -R'
            self.use_client_output = True
        # Set bandwidth in Mbit/s
        if self.bandwidth is not None:
            iperf_args = iperf_args + ' -b {}M'.format(self.bandwidth)

        # Parse the client side data to a file saved on the phone
        self.results_filename_phone = self.IPERF_CLIENT_RESULT_FILE_LOC_PHONE \
                                      + 'iperf_client_port_{}_{}.log'.format( \
                                      self.port, self.traffic_direction)
        iperf_args = iperf_args + ' > %s' % self.results_filename_phone

        self.iperf_args = iperf_args

    def process_iperf_results(self, dut, log, iperf_servers, test_name):
        """Gets the iperf results from the phone and computes the average rate

        Returns:
             throughput: the average throughput (Mbit/s).
        """
        # Get IPERF results and add this to the plot title
        RESULTS_DESTINATION = os.path.join(
            iperf_servers[self.server_idx].log_path,
            'iperf_client_output_{}.log'.format(test_name))

        PULL_FILE = '{} {}'.format(self.results_filename_phone,
                                   RESULTS_DESTINATION)
        dut.adb.pull(PULL_FILE)

        # Calculate the average throughput
        if self.use_client_output:
            iperf_file = RESULTS_DESTINATION
        else:
            iperf_file = iperf_servers[self.server_idx].log_files[-1]
        try:
            iperf_result = ipf.IPerfResult(iperf_file)

            # Compute the throughput in Mbit/s
            throughput = (math.fsum(
                iperf_result.instantaneous_rates[self.start_meas_time:-1]
            ) / len(iperf_result.instantaneous_rates[self.start_meas_time:-1])
                          ) * 8 * (1.024**2)

            log.info('The average throughput is {}'.format(throughput))

        except ValueError:
            log.warning('Cannot get iperf result. Setting to 0')
            throughput = 0
        return throughput
