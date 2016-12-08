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
import time

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

    START_PMC_CMD = ("am start -n com.android.pmc/com.android.pmc."
                     "PMCMainActivity")

    def setup_class(self):
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

        sync_device_time(self.ad)

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
        self.ad.adb.shell(self.START_PMC_CMD)
        self.ad.adb.shell("setprop log.tag.PMC VERBOSE")
        wutils.wifi_toggle_state(self.ad, False)

    def save_logs_for_power_test(self, monsoon_result, measure_time,
                                 idle_time):
        """Utility function to save power data into log file.

        Steps:
        1. Save power data into a file if being configed.
        2. Create a bug report if being configured

        Args:
            monsoon_result: power data object
            measure_time: time duration for measure power
            idle_time: time duration which is not count for power measurement

        Returns:
            None
        """
        current_time = get_current_human_time()
        file_name = "{}_{}".format(self.current_test_name, current_time)
        self.save_to_text_file(monsoon_result,
                               os.path.join(self.monsoon_log_path, file_name),
                               measure_time, idle_time)

        self.ad.take_bug_report(self.current_test_name, current_time)

    def average_current(self, monsoon_data, measure_time, idle_time):
        """Utility function to calculate average current in the unit of mA.

        Args:
            monsoon_result: power data object
            measure_time: time duration when current is measured for measure cycle
            idle_time: time duration when  current is not count for power measurement

        Returns:
            average current as float
        """
        if idle_time == 0:
            return round(monsoon_data.average_current, self.ACCURACY)
        self.log.info(
            "===measure time: {} idle time: {} total data points: {}".format(
                measure_time, idle_time, len(monsoon_data.data_points)))

        # The base time to be used to calculate the relative time
        base_time = monsoon_data.timestamps[0]

        # Index for measure and idle cycle index
        measure_cycle_index = 0
        # measure end time of measure cycle
        measure_end_time = measure_time
        # idle end time of measure cycle
        idle_end_time = measure_time + idle_time
        # sum of currenct data points
        current_sum = 0
        # number of current data points
        data_point_count = 0
        for t, d in zip(monsoon_data.timestamps, monsoon_data.data_points):
            relative_timepoint = t - base_time
            # when time exceeds 1 cycle of measurement update 2 end times
            if relative_timepoint > idle_end_time:
                measure_cycle_index += 1
                measure_end_time = measure_cycle_index * (
                    measure_time + idle_time) + measure_time
                idle_end_time = measure_end_time + idle_time

            # within measure time sum the current
            if relative_timepoint <= measure_end_time:
                current_sum += d
                data_point_count += 1

        self.log.info("===count: {} sum: {}".format(data_point_count,
                                                    current_sum))
        # calculate the average current and convert it into mA
        cur = current_sum * 1000 / data_point_count
        return round(cur, self.ACCURACY)

    def format_header(self, monsoon_data, measure_time, idle_time):
        """Utility function to write the header info to the file.

        Args:
            monsoon_result: power data object
            measure_time: time duration for measure power
            idle_time: time duration which is not count for power measurement

        Returns:
            None
        """
        strs = [""]
        if monsoon_data.tag:
            strs.append("\t\t" + monsoon_data.tag)
        else:
            strs.append("\t\tMonsoon Measurement Data")
        average_cur = self.average_current(monsoon_data, measure_time,
                                           idle_time)
        self.log.info("=== Average Current: {} mA ===".format(average_cur))

        total_power = round(average_cur * monsoon_data.voltage, self.ACCURACY)

        strs.append("\t\tAverage Current: {}mA.".format(average_cur))
        strs.append("\t\tVoltage: {}V.".format(monsoon_data.voltage))
        strs.append("\t\tTotal Power: {}mW.".format(total_power))
        strs.append((
            "\t\t{} samples taken at {}Hz, with an offset of {} samples."
        ).format(
            len(monsoon_data._data_points), monsoon_data.hz,
            monsoon_data.offset))
        return "\n".join(strs)

    def format_data_point(self, monsoon_data, measure_time, idle_time):
        """Utility function to format the data into a string.

        Args:
            monsoon_result: power data object
            measure_time: time duration for measure power
            idle_time: time duration which is not count for power measurement

        Returns:
            Average current as float
        """
        strs = []
        strs.append(self.format_header(monsoon_data, measure_time, idle_time))
        strs.append("\t\tTime" + ' ' * 7 + "Amp")
        # get the relative time
        start_time = monsoon_data.timestamps[0]
        for t, d in zip(monsoon_data.timestamps, monsoon_data.data_points):
            strs.append("{}\t{}".format(
                round((t - start_time), 0), round(d, self.ACCURACY)))

        return "\n".join(strs)

    def save_to_text_file(self, monsoon_data, file_path, measure_time,
                          idle_time):
        """Save multiple MonsoonData objects to a text file.

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
        with open(file_path, 'w') as f:
            f.write(self.format_data_point(monsoon_data, measure_time,
                                           idle_time))
            f.write("\t\t" + monsoon_data.delimiter)
