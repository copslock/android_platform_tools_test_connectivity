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

from bokeh.layouts import column, layout
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
        data=dict(x0=time_relative, y0=current_data, color=color))
    s2 = ColumnDataSource(
        data=dict(z0=[mon_info.duration],
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
                  tools=tools,
                  output_backend='webgl')
    plot.add_tools(bokeh_tools.WheelZoomTool(dimensions='width'))
    plot.add_tools(bokeh_tools.WheelZoomTool(dimensions='height'))
    plot.line('x0', 'y0', source=source, line_width=2)
    plot.circle('x0', 'y0', source=source, size=0.5, fill_color='color')
    plot.xaxis.axis_label = 'Time (s)'
    plot.yaxis.axis_label = 'Current (mA)'
    plot.title.text_font_size = {'value': '15pt'}

    # Callback JavaScript
    source.selected.js_on_change(
        "indices",
        CustomJS(args=dict(source=source, mytable=dt),
                 code="""
    var inds = cb_obj.indices;
    var d1 = source.data;
    var d2 = mytable.source.data;
    ym = 0
    ts = 0
    d2['x0'] = []
    d2['y0'] = []
    d2['z1'] = []
    d2['z2'] = []
    d2['z0'] = []
    min=max=d1['x0'][inds[0]]
    if (inds.length==0) {return;}
    for (i = 0; i < inds.length; i++) {
    ym += d1['y0'][inds[i]]
    d1['color'][inds[i]] = "red"
    if (d1['x0'][inds[i]] < min) {
      min = d1['x0'][inds[i]]}
    if (d1['x0'][inds[i]] > max) {
      max = d1['x0'][inds[i]]}
    }
    ym /= inds.length
    ts = max - min
    dx0 = Math.round(ym*4.2*100.0)/100.0
    dy0 = Math.round(ym*100.0)/100.0
    dz1 = Math.round(ym*4.2*ts*100.0)/100.0
    dz2 = Math.round(ym*ts*100.0)/100.0
    dz0 = Math.round(ts*1000.0)/1000.0
    d2['z0'].push(dz0)
    d2['x0'].push(dx0)
    d2['y0'].push(dy0)
    d2['z1'].push(dz1)
    d2['z2'].push(dz2)
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
