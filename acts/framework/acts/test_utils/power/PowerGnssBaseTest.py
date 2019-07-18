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

import logging

import acts.test_utils.power.PowerBaseTest as PBT

from acts import base_test
from acts.controllers import monsoon
from bokeh.layouts import column, layout
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.models import tools as bokeh_tools
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.plotting import figure, output_file, save


class PowerGnssBaseTest(PBT.PowerBaseTest):
    """
    Base Class for all GNSS Power related tests
    """

    def __init__(self, controllers):
        base_test.BaseTestClass.__init__(self, controllers)

    def collect_power_data(self):
        """Measure power and plot.

        """
        tag = '_Power'
        super().collect_power_data()
        self.monsoon_data_plot_power(self.mon_info, self.file_path, tag=tag)

    def monsoon_data_plot_power(self, mon_info, file_path, tag=""):
        """Plot the monsoon power data using bokeh interactive plotting tool.

        Args:
            mon_info: Dictionary with the monsoon packet config
            file_path: the path to the monsoon log file with current data

        """

        self.log.info("Plot the power measurement data")
        # Get results as monsoon data object from the input file
        results = monsoon.MonsoonData.from_text_file(file_path)
        # Decouple current and timestamp data from the monsoon object
        current_data = []
        timestamps = []
        voltage = results[0].voltage
        for result in results:
            current_data.extend(result.data_points)
            timestamps.extend(result.timestamps)
        period = 1 / mon_info.freq
        time_relative = [x * period for x in range(len(current_data))]
        # Calculate the average current for the test

        current_data = [x * 1000 for x in current_data]
        power_data = [x * voltage for x in current_data]
        avg_current = sum(current_data) / len(current_data)
        color = ['navy'] * len(current_data)

        # Preparing the data and source link for bokehn java callback
        source = ColumnDataSource(
            data=dict(x0=time_relative, y0=power_data, color=color))
        s2 = ColumnDataSource(
            data=dict(
                z0=[mon_info.duration],
                y0=[round(avg_current, 2)],
                x0=[round(avg_current * voltage, 2)],
                z1=[round(avg_current * voltage * mon_info.duration, 2)],
                z2=[round(avg_current * mon_info.duration, 2)]))
        # Setting up data table for the output
        columns = [
            TableColumn(field='z0', title='Total Duration (s)'),
            TableColumn(field='y0', title='Average Current (mA)'),
            TableColumn(field='x0', title='Average Power (4.2v) (mW)'),
            TableColumn(field='z1', title='Average Energy (mW*s)'),
            TableColumn(field='z2', title='Normalized Average Energy (mA*s)')
        ]
        dt = DataTable(
            source=s2, columns=columns, width=1300, height=60, editable=True)

        plot_title = file_path[file_path.rfind('/') + 1:-4] + tag
        output_file("%s/%s.html" % (mon_info.data_path, plot_title))
        TOOLS = 'box_zoom,box_select,pan,crosshair,redo,undo,reset,hover,save'
        # Create a new plot with the datatable above
        plot = figure(
            plot_width=1300,
            plot_height=700,
            title=plot_title,
            tools=TOOLS,
            output_backend="webgl")
        plot.add_tools(bokeh_tools.WheelZoomTool(dimensions="width"))
        plot.add_tools(bokeh_tools.WheelZoomTool(dimensions="height"))
        plot.line('x0', 'y0', source=source, line_width=2)
        plot.circle('x0', 'y0', source=source, size=0.5, fill_color='color')
        plot.xaxis.axis_label = 'Time (s)'
        plot.yaxis.axis_label = 'Power (mW)'
        plot.title.text_font_size = {'value': '15pt'}
        jsscript = open(self.customjsfile, 'r')
        customjsscript = jsscript.read()
        # Callback Java scripting
        source.callback = CustomJS(
            args=dict(mytable=dt),
            code=customjsscript)

        # Layout the plot and the datatable bar
        l = layout([[dt], [plot]])
        save(l)
