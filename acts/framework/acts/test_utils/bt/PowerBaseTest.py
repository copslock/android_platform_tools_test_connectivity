#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
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
"""
This test script is the base class for Bluetooth power testing
"""

import json
import os
import statistics

from acts import asserts
from acts import utils
from acts.controllers import monsoon
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import bluetooth_enabled_check
from acts.test_utils.tel.tel_test_utils import set_phone_screen_on
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.utils import create_dir
from acts.utils import force_airplane_mode
from acts.utils import get_current_human_time
from acts.utils import set_adaptive_brightness
from acts.utils import set_ambient_display
from acts.utils import set_auto_rotate
from acts.utils import set_location_service
from acts.utils import sync_device_time


class PowerBaseTest(BluetoothBaseTest):
    # Monsoon output Voltage in V
    MONSOON_OUTPUT_VOLTAGE = 4.2
    # Monsoon output max current in A
    MONSOON_MAX_CURRENT = 7.8
    # Power mesaurement sampling rate in Hz
    POWER_SAMPLING_RATE = 20
    SCREEN_TIME_OFF = 10
    # Accuracy for current and power data
    ACCURACY = 4
    THOUSAND = 1000

    START_PMC_CMD = ("am start -n com.android.pmc/com.android.pmc."
                     "PMCMainActivity")
    PMC_VERBOSE_CMD = "setprop log.tag.PMC VERBOSE"

    def setup_class(self):
        # Not to call Base class setup_class()
        # since it removes the bonded devices
        for ad in self.android_devices:
            sync_device_time(ad)
        self.ad = self.android_devices[0]
        self.mon = self.monsoons[0]
        self.mon.set_voltage(self.MONSOON_OUTPUT_VOLTAGE)
        self.mon.set_max_current(self.MONSOON_MAX_CURRENT)
        # Monsoon phone
        self.mon.attach_device(self.ad)
        self.monsoon_log_path = os.path.join(self.log_path, "MonsoonLog")
        create_dir(self.monsoon_log_path)

        asserts.assert_true(
            self.mon.usb("auto"),
            "Failed to turn USB mode to auto on monsoon.")

        asserts.assert_true(
            force_airplane_mode(self.ad, True),
            "Can not turn on airplane mode on: %s" % self.ad.serial)
        asserts.assert_true(
            bluetooth_enabled_check(self.ad),
            "Failed to set Bluetooth state to enabled")
        set_location_service(self.ad, False)
        set_adaptive_brightness(self.ad, False)
        set_ambient_display(self.ad, False)
        self.ad.adb.shell("settings put system screen_brightness 0")
        set_auto_rotate(self.ad, False)
        set_phone_screen_on(self.log, self.ad, self.SCREEN_TIME_OFF)

        # Start PMC app.
        self.log.info("Start PMC app...")
        self.ad.adb.shell(self.START_PMC_CMD)
        self.ad.adb.shell(self.PMC_VERBOSE_CMD)
        wutils.wifi_toggle_state(self.ad, False)

    def save_logs_for_power_test(self, monsoon_result, measure_time,
                                 idle_time):
        """Utility function to save power data into log file.

        Steps:
        1. Save power data into a file if being configed.
        2. Create a bug report if being configured

        Args:
            monsoon_result: power data object
            measure_time: time duration (sec) for measure power
            idle_time: time duration (sec) which is not counted toward
                       power measurement

        Returns:
            None
        """
        current_time = get_current_human_time()
        file_name = "{}_{}".format(self.current_test_name, current_time)
        self.save_to_text_file(monsoon_result,
                               os.path.join(self.monsoon_log_path, file_name),
                               measure_time, idle_time)

        self.ad.take_bug_report(self.current_test_name, current_time)

    def _calculate_average_current_n_std_dev(self, monsoon_data, measure_time,
                                             idle_time):
        """Utility function to calculate average current and standard deviation
           in the unit of mA.

        Args:
            monsoon_result: power data object
            measure_time: time duration (sec) when power data is counted toward
                          calculation of average and std deviation
            idle_time: time duration (sec) when power data is not counted
                       toward calculation of average and std deviation

        Returns:
            A tuple of average current and std dev as float
        """
        if idle_time == 0:
            # if idle time is 0 use Monsoon calculation
            # in this case standard deviation is 0
            return round(monsoon_data.average_current, self.ACCURACY), 0

        self.log.info(
            "Measure time: {} Idle time: {} Total Data Points: {}".format(
                measure_time, idle_time, len(monsoon_data.data_points)))

        # The base time to be used to calculate the relative time
        base_time = monsoon_data.timestamps[0]

        # Index for measure and idle cycle index
        measure_cycle_index = 0
        # Measure end time of measure cycle
        measure_end_time = measure_time
        # Idle end time of measure cycle
        idle_end_time = measure_time + idle_time
        # Sum of current data points for a measure cycle
        current_sum = 0
        # Number of current data points for a measure cycle
        data_point_count = 0
        average_60_sec = []
        # Total number of measure data point
        total_measured_data_point_count = 0

        # Flag to indicate whether the average is calculated for this cycle
        # For 1 second there are multiple data points
        # so time comparison will yield to multiple cases
        done_average = False

        for t, d in zip(monsoon_data.timestamps, monsoon_data.data_points):
            relative_timepoint = t - base_time
            # When time exceeds 1 cycle of measurement update 2 end times
            if relative_timepoint > idle_end_time:
                measure_cycle_index += 1
                measure_end_time = measure_cycle_index * (
                    measure_time + idle_time) + measure_time
                idle_end_time = measure_end_time + idle_time
                done_average = False

            # Within measure time sum the current
            if relative_timepoint <= measure_end_time:
                current_sum += d
                data_point_count += 1
            elif not done_average:
                # Calculate the average current for this cycle
                average_60_sec.append(current_sum / data_point_count)
                total_measured_data_point_count += data_point_count
                current_sum = 0
                data_point_count = 0
                done_average = True

        # Calculate the average current and convert it into mA
        current_avg = round(
            statistics.mean(average_60_sec) * self.THOUSAND, self.ACCURACY)
        # Calculate the min and max current and convert it into mA
        current_min = round(min(average_60_sec) * self.THOUSAND, self.ACCURACY)
        current_max = round(max(average_60_sec) * self.THOUSAND, self.ACCURACY)

        # Calculate the standard deviation and convert it into mA
        stdev = round(
            statistics.stdev(average_60_sec) * self.THOUSAND, self.ACCURACY)
        self.log.info("Total Counted Data Points: {}".format(
            total_measured_data_point_count))
        self.log.info("Average Current: {} mA ".format(current_avg))
        self.log.info("Standard Deviation: {} mA".format(stdev))
        self.log.info("Min Current: {} mA ".format(current_min))
        self.log.info("Max Current: {} mA".format(current_max))

        return current_avg, stdev

    def _format_header(self, monsoon_data, measure_time, idle_time):
        """Utility function to write the header info to the file.
           The data is formated as tab delimited for spreadsheets.

        Args:
            monsoon_result: power data object
            measure_time: time duration (sec) when power data is counted toward
                          calculation of average and std deviation
            idle_time: time duration (sec) when power data is not counted
                       toward calculation of average and std deviation

        Returns:
            None
        """
        strs = [""]
        if monsoon_data.tag:
            strs.append("\t\t" + monsoon_data.tag)
        else:
            strs.append("\t\tMonsoon Measurement Data")
        average_cur, stdev = self._calculate_average_current_n_std_dev(
            monsoon_data, measure_time, idle_time)
        total_power = round(average_cur * monsoon_data.voltage, self.ACCURACY)

        strs.append("\t\tAverage Current: {} mA.".format(average_cur))
        strs.append("\t\tSTD DEV Current: {} mA.".format(stdev))
        strs.append("\t\tVoltage: {} V.".format(monsoon_data.voltage))
        strs.append("\t\tTotal Power: {} mW.".format(total_power))
        strs.append((
            "\t\t{} samples taken at {}Hz, with an offset of {} samples."
        ).format(
            len(monsoon_data._data_points), monsoon_data.hz,
            monsoon_data.offset))
        return "\n".join(strs)

    def _format_data_point(self, monsoon_data, measure_time, idle_time):
        """Utility function to format the data into a string.
           The data is formated as tab delimited for spreadsheets.

        Args:
            monsoon_result: power data object
            measure_time: time duration (sec) when power data is counted toward
                          calculation of average and std deviation
            idle_time: time duration (sec) when power data is not counted
                       toward calculation of average and std deviation

        Returns:
            Average current as float
        """
        strs = []
        strs.append(self._format_header(monsoon_data, measure_time, idle_time))
        strs.append("\t\tTime\tAmp")
        # Get the relative time
        start_time = monsoon_data.timestamps[0]
        for t, d in zip(monsoon_data.timestamps, monsoon_data.data_points):
            strs.append("{}\t{}".format(
                round((t - start_time), 0), round(d, self.ACCURACY)))

        return "\n".join(strs)

    def save_to_text_file(self, monsoon_data, file_path, measure_time,
                          idle_time):
        """Save multiple MonsoonData objects to a text file.
           The data is formated as tab delimited for spreadsheets.

        Args:
            monsoon_data: A list of MonsoonData objects to write to a text
                file.
            file_path: The full path of the file to save to, including the file
                name.
        """
        if not monsoon_data:
            self.log.error("Attempting to write empty Monsoon data to "
                           "file, abort")
            return

        utils.create_dir(os.path.dirname(file_path))
        try:
            with open(file_path, 'w') as f:
                f.write(self._format_data_point(monsoon_data, measure_time,
                                                idle_time))
                f.write("\t\t" + monsoon_data.delimiter)
        except IOError:
            self.log.error("Fail to write power data into file")
