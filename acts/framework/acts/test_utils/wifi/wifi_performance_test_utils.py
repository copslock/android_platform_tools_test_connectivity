#!/usr/bin/env python3.4
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

import bokeh
import collections
import logging
import math
import re
import statistics
import time
from acts.controllers.android_device import AndroidDevice
from acts.controllers.utils_lib import ssh
from concurrent.futures import ThreadPoolExecutor

SHORT_SLEEP = 1
MED_SLEEP = 6
TEST_TIMEOUT = 10
STATION_DUMP = 'iw wlan0 station dump'
SCAN = 'wpa_cli scan'
SCAN_RESULTS = 'wpa_cli scan_results'
SIGNAL_POLL = 'wpa_cli signal_poll'
CONST_3dB = 3.01029995664
RSSI_ERROR_VAL = float('nan')


# Threading decorator
def nonblocking(f):
    """Creates a decorator transforming function calls to non-blocking"""

    def wrap(*args, **kwargs):
        executor = ThreadPoolExecutor(max_workers=1)
        thread_future = executor.submit(f, *args, **kwargs)
        # Ensure resources are freed up when executor ruturns or raises
        executor.shutdown(wait=False)
        return thread_future

    return wrap


# Plotting Utilities
def bokeh_plot(data_sets,
               legends,
               fig_property,
               shaded_region=None,
               output_file_path=None):
    """Plot bokeh figs.
        Args:
            data_sets: data sets including lists of x_data and lists of y_data
                       ex: [[[x_data1], [x_data2]], [[y_data1],[y_data2]]]
            legends: list of legend for each curve
            fig_property: dict containing the plot property, including title,
                      lables, linewidth, circle size, etc.
            shaded_region: optional dict containing data for plot shading
            output_file_path: optional path at which to save figure
        Returns:
            plot: bokeh plot figure object
    """
    TOOLS = ('box_zoom,box_select,pan,crosshair,redo,undo,reset,hover,save')
    plot = bokeh.plotting.figure(
        plot_width=1300,
        plot_height=700,
        title=fig_property['title'],
        tools=TOOLS,
        output_backend='webgl')
    plot.add_tools(bokeh.models.tools.WheelZoomTool(dimensions='width'))
    plot.add_tools(bokeh.models.tools.WheelZoomTool(dimensions='height'))
    colors = [
        'red', 'green', 'blue', 'olive', 'orange', 'salmon', 'black', 'navy',
        'yellow', 'darkred', 'goldenrod'
    ]
    if shaded_region:
        band_x = shaded_region['x_vector']
        band_x.extend(shaded_region['x_vector'][::-1])
        band_y = shaded_region['lower_limit']
        band_y.extend(shaded_region['upper_limit'][::-1])
        plot.patch(
            band_x, band_y, color='#7570B3', line_alpha=0.1, fill_alpha=0.1)

    for x_data, y_data, legend in zip(data_sets[0], data_sets[1], legends):
        index_now = legends.index(legend)
        color = colors[index_now % len(colors)]
        plot.line(
            x_data,
            y_data,
            legend=str(legend),
            line_width=fig_property['linewidth'],
            color=color)
        plot.circle(
            x_data,
            y_data,
            size=fig_property['markersize'],
            legend=str(legend),
            fill_color=color)

    #Plot properties
    plot.xaxis.axis_label = fig_property['x_label']
    plot.yaxis.axis_label = fig_property['y_label']
    plot.legend.location = 'top_right'
    plot.legend.click_policy = 'hide'
    plot.title.text_font_size = {'value': '15pt'}
    if output_file_path is not None:
        bokeh.plotting.output_file(output_file_path)
        bokeh.plotting.save(plot)
    return plot


def save_bokeh_plots(plot_array, output_file_path):
    all_plots = bokeh.layouts.column(children=plot_array)
    bokeh.plotting.output_file(output_file_path)
    bokeh.plotting.save(all_plots)


# Ping Utilities
@staticmethod
def disconnected_ping_result():
    return collections.OrderedDict([('connected', 0), ('rtt', [float('nan')]),
                                    ('packet_loss_percentage', 100)])


def get_ping_stats(src_device, dest_address, ping_duration, ping_interval,
                   ping_size):
    """Run ping to or from the DUT.

    The function computes either pings the DUT or pings a remote ip from
    DUT.

    Args:
        src_device: object representing device to ping from
        dest_address: ip address to ping
        ping_duration: timeout to set on the the ping process (in seconds)
        ping_interval: time between pings (in seconds)
        ping_size: size of ping packet payload
    Returns:
        ping_result: dict containing ping results and other meta data
    """
    ping_cmd = 'ping -w {} -i {} -s {}'.format(
        ping_duration,
        ping_interval,
        ping_size,
    )
    if isinstance(src_device, AndroidDevice):
        ping_cmd = '{} {}'.format(ping_cmd, dest_address)
        ping_output = src_device.adb.shell(
            ping_cmd, timeout=ping_duration + TEST_TIMEOUT, ignore_status=True)
    elif isinstance(src_device, ssh.connection.SshConnection):
        ping_cmd = 'sudo {} {}'.format(ping_cmd, dest_address)
        ping_output = src_device.run(ping_cmd, ignore_status=True).stdout
    ping_output = ping_output.splitlines()

    if len(ping_output) == 1:
        ping_result = disconnected_ping_result()
    else:
        packet_loss_line = [line for line in ping_output if 'loss' in line]
        packet_loss_percentage = int(
            packet_loss_line[0].split('%')[0].split(' ')[-1])
        if packet_loss_percentage == 100:
            rtt = [float('nan')]
        else:
            rtt = [
                line.split('time=')[1] for line in ping_output
                if 'time=' in line
            ]
            rtt = [float(line.split(' ')[0]) for line in rtt]
        ping_result = {
            'connected': 1,
            'rtt': rtt,
            'packet_loss_percentage': packet_loss_percentage
        }
    return ping_result


@nonblocking
def get_ping_stats_nb(src_device, dest_address, ping_duration, ping_interval,
                      ping_size):
    return get_ping_stats(src_device, dest_address, ping_duration,
                          ping_interval, ping_size)


# Rssi Utilities
def empty_rssi_result():
    return collections.OrderedDict([('data', []), ('mean', None), ('stdev',
                                                                   None)])


def get_connected_rssi(dut,
                       num_measurements=1,
                       polling_frequency=SHORT_SLEEP,
                       first_measurement_delay=0):
    """Gets all RSSI values reported for the connected access point/BSSID.

    Args:
        dut: android device object from which to get RSSI
        num_measurements: number of scans done, and RSSIs collected
        polling_frequency: time to wait between RSSI measurements
    Returns:
        connected_rssi: dict containing the measurements results for
        all reported RSSI values (signal_poll, per chain, etc.) and their
        statistics
    """
    # yapf: disable
    connected_rssi = collections.OrderedDict(
        [('frequency', []),
         ('signal_poll_rssi', empty_rssi_result()),
         ('signal_poll_avg_rssi', empty_rssi_result()),
         ('chain_0_rssi', empty_rssi_result()),
         ('chain_1_rssi', empty_rssi_result())])
    # yapf: enable
    time.sleep(first_measurement_delay)
    for idx in range(num_measurements):
        measurement_start_time = time.time()
        # Get signal poll RSSI
        signal_poll_output = dut.adb.shell(SIGNAL_POLL)
        match = re.search('FREQUENCY=.*', signal_poll_output)
        if match:
            frequency = int(match.group(0).split('=')[1])
            connected_rssi['frequency'].append(frequency)
        else:
            connected_rssi['frequency'].append(RSSI_ERROR_VAL)
        match = re.search('RSSI=.*', signal_poll_output)
        if match:
            temp_rssi = int(match.group(0).split('=')[1])
            if temp_rssi == -9999:
                connected_rssi['signal_poll_rssi']['data'].append(
                    RSSI_ERROR_VAL)
            else:
                connected_rssi['signal_poll_rssi']['data'].append(temp_rssi)
        else:
            connected_rssi['signal_poll_rssi']['data'].append(RSSI_ERROR_VAL)
        match = re.search('AVG_RSSI=.*', signal_poll_output)
        if match:
            connected_rssi['signal_poll_avg_rssi']['data'].append(
                int(match.group(0).split('=')[1]))
        else:
            connected_rssi['signal_poll_avg_rssi']['data'].append(
                RSSI_ERROR_VAL)
        # Get per chain RSSI
        per_chain_rssi = dut.adb.shell(STATION_DUMP)
        match = re.search('.*signal avg:.*', per_chain_rssi)
        if match:
            per_chain_rssi = per_chain_rssi[per_chain_rssi.find('[') + 1:
                                            per_chain_rssi.find(']')]
            per_chain_rssi = per_chain_rssi.split(', ')
            connected_rssi['chain_0_rssi']['data'].append(
                int(per_chain_rssi[0]))
            connected_rssi['chain_1_rssi']['data'].append(
                int(per_chain_rssi[1]))
        else:
            connected_rssi['chain_0_rssi']['data'].append(RSSI_ERROR_VAL)
            connected_rssi['chain_1_rssi']['data'].append(RSSI_ERROR_VAL)
        measurement_elapsed_time = time.time() - measurement_start_time
        time.sleep(max(0, polling_frequency - measurement_elapsed_time))

    # Compute mean RSSIs. Only average valid readings.
    # Output RSSI_ERROR_VAL if no valid connected readings found.
    for key, val in connected_rssi.copy().items():
        if key == "frequency":
            continue
        filtered_rssi_values = [x for x in val['data'] if not math.isnan(x)]
        if filtered_rssi_values:
            connected_rssi[key]['mean'] = statistics.mean(filtered_rssi_values)
            if len(filtered_rssi_values) > 1:
                connected_rssi[key]['stdev'] = statistics.stdev(
                    filtered_rssi_values)
            else:
                connected_rssi[key]['stdev'] = 0
        else:
            connected_rssi[key]['mean'] = RSSI_ERROR_VAL
            connected_rssi[key]['stdev'] = RSSI_ERROR_VAL
    return connected_rssi


@nonblocking
def get_connected_rssi_nb(dut,
                          num_measurements=1,
                          polling_frequency=SHORT_SLEEP,
                          first_measurement_delay=0):
    return get_connected_rssi(dut, num_measurements, polling_frequency,
                              first_measurement_delay)


def get_scan_rssi(dut, tracked_bssids, num_measurements=1):
    """Gets scan RSSI for specified BSSIDs.

    Args:
        dut: android device object from which to get RSSI
        tracked_bssids: array of BSSIDs to gather RSSI data for
        num_measurements: number of scans done, and RSSIs collected
    Returns:
        scan_rssi: dict containing the measurement results as well as the
        statistics of the scan RSSI for all BSSIDs in tracked_bssids
    """
    scan_rssi = collections.OrderedDict()
    for bssid in tracked_bssids:
        scan_rssi[bssid] = empty_rssi_result()
    for idx in range(num_measurements):
        scan_output = dut.adb.shell(SCAN)
        time.sleep(MED_SLEEP)
        scan_output = dut.adb.shell(SCAN_RESULTS)
        for bssid in tracked_bssids:
            bssid_result = re.search(
                bssid + '.*', scan_output, flags=re.IGNORECASE)
            if bssid_result:
                bssid_result = bssid_result.group(0).split('\t')
                scan_rssi[bssid]['data'].append(int(bssid_result[2]))
            else:
                scan_rssi[bssid]['data'].append(RSSI_ERROR_VAL)
    # Compute mean RSSIs. Only average valid readings.
    # Output RSSI_ERROR_VAL if no readings found.
    for key, val in scan_rssi.items():
        filtered_rssi_values = [x for x in val['data'] if not math.isnan(x)]
        if filtered_rssi_values:
            scan_rssi[key]['mean'] = statistics.mean(filtered_rssi_values)
            if len(filtered_rssi_values) > 1:
                scan_rssi[key]['stdev'] = statistics.stdev(
                    filtered_rssi_values)
            else:
                scan_rssi[key]['stdev'] = 0
        else:
            scan_rssi[key]['mean'] = RSSI_ERROR_VAL
            scan_rssi[key]['stdev'] = RSSI_ERROR_VAL
    return scan_rssi


@nonblocking
def get_scan_rssi_nb(dut, tracked_bssids, num_measurements=1):
    return get_scan_rssi(dut, tracked_bssids, num_measurements)


## Attenuator Utilities
def atten_by_label(atten_list, path_label, atten_level):
    """Attenuate signals according to their path label.

    Args:
        atten_list: list of attenuators to iterate over
        path_label: path label on which to set desired attenuation
        atten_level: attenuation desired on path
    """
    for atten in atten_list:
        if path_label in atten.path:
            atten.set_atten(atten_level)


def get_server_address(ssh_connection, subnet):
    """Get server address on a specific subnet

    Args:
        ssh_connection: object representing server for which we want an ip
        subnet: string in ip address format, i.e., xxx.xxx.xxx.xxx,
        representing the subnet of interest.
    """
    subnet_str = subnet.split('.')[:-1]
    subnet_str = ".".join(subnet_str)
    cmd = "ifconfig | grep 'inet addr:{}'".format(subnet_str)
    try:
        if_output = ssh_connection.run(cmd).stdout
        ip_line = if_output.split('inet addr:')[1]
        ip_address = ip_line.split(" ")[0]
    except:
        logging.warning("Could not find ip in requested subnet.")
    return ip_address
