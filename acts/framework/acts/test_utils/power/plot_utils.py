#!/usr/bin/env python3
#
#   Copyright 2020 Google, Inc.
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

import os
import logging
import numpy
import math

from bokeh.layouts import layout
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.models import tools as bokeh_tools
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.plotting import figure, output_file, save


def monsoon_data_plot(mon_info, monsoon_results, tag=''):
    """Plot the monsoon current data using bokeh interactive plotting tool.

    Plotting power measurement data with bokeh to generate interactive plots.
    You can do interactive data analysis on the plot after generating with the
    provided widgets, which make the debugging much easier. To realize that,
    bokeh callback java scripting is used. View a sample html output file:
    https://drive.google.com/open?id=0Bwp8Cq841VnpT2dGUUxLYWZvVjA

    Args:
        mon_info: obj with information of monsoon measurement, including
            monsoon device object, measurement frequency, duration, etc.
        monsoon_results: a MonsoonResult or list of MonsoonResult objects to
                         to plot.
        tag: an extra tag to append to the resulting filename.

    Returns:
        plot: the plotting object of bokeh, optional, will be needed if multiple
           plots will be combined to one html file.
        dt: the datatable object of bokeh, optional, will be needed if multiple
           datatables will be combined to one html file.
    """
    if not isinstance(monsoon_results, list):
        monsoon_results = [monsoon_results]
    logging.info('Plotting the power measurement data.')

    voltage = monsoon_results[0].voltage

    total_current = 0
    total_samples = 0
    for result in monsoon_results:
        total_current += result.average_current * result.num_samples
        total_samples += result.num_samples
    avg_current = total_current / total_samples

    time_relative = [
        data_point.time for monsoon_result in monsoon_results
        for data_point in monsoon_result.get_data_points()
    ]

    current_data = [
        data_point.current * 1000 for monsoon_result in monsoon_results
        for data_point in monsoon_result.get_data_points()
    ]

    total_data_points = sum(result.num_samples for result in monsoon_results)
    color = ['navy'] * total_data_points

    # Preparing the data and source link for bokehn java callback
    source = ColumnDataSource(
        data=dict(x=time_relative, y=current_data, color=color))
    s2 = ColumnDataSource(
        data=dict(a=[mon_info.duration],
                  b=[round(avg_current, 2)],
                  c=[round(avg_current * voltage, 2)],
                  d=[round(avg_current * voltage * mon_info.duration, 2)],
                  e=[round(avg_current * mon_info.duration, 2)]))
    # Setting up data table for the output
    columns = [
        TableColumn(field='a', title='Total Duration (s)'),
        TableColumn(field='b', title='Average Current (mA)'),
        TableColumn(field='c', title='Average Power (4.2v) (mW)'),
        TableColumn(field='d', title='Average Energy (mW*s)'),
        TableColumn(field='e', title='Normalized Average Energy (mA*s)')
    ]
    dt = DataTable(source=s2,
                   columns=columns,
                   width=1300,
                   height=60,
                   editable=True)

    plot_title = (
        os.path.basename(os.path.splitext(monsoon_results[0].tag)[0]) + tag)
    output_file(os.path.join(mon_info.data_path, plot_title + '.html'))
    tools = 'box_zoom,box_select,pan,crosshair,redo,undo,reset,hover,save'
    # Create a new plot with the datatable above
    plot = figure(plot_width=1300,
                  plot_height=700,
                  title=plot_title,
                  tools=tools)
    plot.add_tools(bokeh_tools.WheelZoomTool(dimensions='width'))
    plot.add_tools(bokeh_tools.WheelZoomTool(dimensions='height'))
    plot.line('x', 'y', source=source, line_width=2)
    plot.circle('x', 'y', source=source, size=0.5, fill_color='color')
    plot.xaxis.axis_label = 'Time (s)'
    plot.yaxis.axis_label = 'Current (mA)'
    plot.title.text_font_size = {'value': '15pt'}

    # Callback JavaScript
    source.selected.js_on_change(
        "indices",
        CustomJS(args=dict(source=source, mytable=dt),
                 code="""
        const inds = source.selected.indices;
        const d1 = source.data;
        const d2 = mytable.source.data;
        var ym = 0
        var ts = 0
        var min=d1['x'][inds[0]]
        var max=d1['x'][inds[0]]
        d2['a'] = []
        d2['b'] = []
        d2['c'] = []
        d2['d'] = []
        d2['e'] = []
        if (inds.length==0) {return;}
        for (var i = 0; i < inds.length; i++) {
        ym += d1['y'][inds[i]]
        d1['color'][inds[i]] = "red"
        if (d1['x'][inds[i]] < min) {
          min = d1['x'][inds[i]]}
        if (d1['x'][inds[i]] > max) {
          max = d1['x'][inds[i]]}
        }
        ym /= inds.length
        ts = max - min
        d2['a'].push(Math.round(ts*1000.0)/1000.0)
        d2['b'].push(Math.round(ym*100.0)/100.0)
        d2['c'].push(Math.round(ym*4.2*100.0)/100.0)
        d2['d'].push(Math.round(ym*4.2*ts*100.0)/100.0)
        d2['e'].push(Math.round(ym*ts*100.0)/100.0)
        source.change.emit();
        mytable.change.emit();
    """))

    # Layout the plot and the datatable bar
    save(layout([[dt], [plot]]))
    return plot, dt


def monsoon_histogram_plot(mon_info, monsoon_result):
    """ Creates a histogram from a monsoon result object.

    Args:
        mon_info: obj with information of monsoon measurement, including
            monsoon device object, measurement frequency, duration, etc.
        monsoon_result: a MonsoonResult object from which to obtain the
            current histogram.
    Returns:
        a tuple of arrays containing the values of the histogram and the
        bin edges.
    """
    current_data = [
        data_point.current * 1000
        for data_point in monsoon_result.get_data_points()
    ]
    hist, edges = numpy.histogram(current_data,
                                  bins=math.ceil(max(current_data)),
                                  range=(0, max(current_data)))

    plot_title = (os.path.basename(os.path.splitext(monsoon_result.tag)[0]) +
                  '_histogram')

    output_file(os.path.join(mon_info.data_path, plot_title + '.html'))

    plot = figure(title=plot_title,
                  y_axis_type='log',
                  background_fill_color='#fafafa')

    plot.quad(top=hist,
              bottom=0,
              left=edges[:-1],
              right=edges[1:],
              fill_color='navy')

    plot.y_range.start = 0
    plot.xaxis.axis_label = 'Instantaneous current [mA]'
    plot.yaxis.axis_label = 'Count'
    plot.grid.grid_line_color = 'white'

    save(plot)

    return hist, edges

def monsoon_tx_power_sweep_plot(mon_info, tag, currents, txs):
    """ Creates average current vs tx power plot

    Args:
        currents: List of average currents measured during power sweep
        txs: List of uplink input power levels specified for each measurement
    """

    plot_title = tag + '_tx_power_sweep'

    output_file(os.path.join(mon_info.data_path, plot_title + '.html'))

    plot = figure(title=plot_title,
                  y_axis_label='Average Current [mA]',
                  x_axis_label='Tx Power [dBm]',
                  background_fill_color='#fafafa')

    plot.line(txs, currents)
    plot.circle(txs, currents, fill_color='white', size=8)
    plot.y_range.start = 0

    save(plot)
