#!/usr/bin/env python3.4
#
#   Copyright 2017 Google, Inc.
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
import numpy as np
import os
import time
from acts import utils
from acts.controllers import monsoon
from acts.test_utils.wifi import wifi_test_utils as wutils
from bokeh.plotting import figure, output_file, save
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.layouts import layout
from acts.controllers.ap_lib import hostapd_security
from acts.controllers.ap_lib import hostapd_ap_preset

SETTINGS_PAGE = "am start -n com.android.settings/.Settings"
SCROLL_BOTTOM = "input swipe 0 2000 0 0"
UNLOCK_SCREEN = "input keyevent 82"
SCREENON_USB_DISABLE = "dumpsys battery unplug"
RESET_BATTERY_STATS = "dumpsys batterystats --reset"
AOD_OFF = "settings put secure doze_always_on 0"
MUSIC_IQ_OFF = "pm disable-user com.google.intelligence.sense"
# Command to disable gestures
LIFT = "settings put secure doze_pulse_on_pick_up 0"
DOUBLE_TAP = "settings put secure doze_pulse_on_double_tap 0"
JUMP_TO_CAMERA = "settings put secure camera_double_tap_power_gesture_disabled 1"
RAISE_TO_CAMERA = "settings put secure camera_lift_trigger_enabled 0"
FLIP_CAMERA = "settings put secure camera_double_twist_to_flip_enabled 0"
ASSIST_GESTURE = "settings put secure assist_gesture_enabled 0"
ASSIST_GESTURE_ALERT = "settings put secure assist_gesture_silence_alerts_enabled 0"
ASSIST_GESTURE_WAKE = "settings put secure assist_gesture_wake_enabled 0"
SYSTEM_NAVI = "settings put secure system_navigation_keys_enabled 0"
# End of command to disable gestures
AUTO_TIME_OFF = "settings put global auto_time 0"
AUTO_TIMEZONE_OFF = "settings put global auto_time_zone 0"
IPERF_TIMEOUT = 180


def dut_rockbottom(ad):
    """Set the phone into Rock-bottom state.

    Args:
        ad: the target android device, AndroidDevice object

    """
    ad.log.info("Now set the device to Rockbottom State")
    utils.require_sl4a((ad, ))
    utils.set_ambient_display(ad, False)
    utils.set_auto_rotate(ad, False)
    utils.set_adaptive_brightness(ad, False)
    utils.sync_device_time(ad)
    utils.set_location_service(ad, False)
    utils.set_mobile_data_always_on(ad, False)
    utils.disable_doze_light(ad)
    utils.disable_doze(ad)
    wutils.reset_wifi(ad)
    wutils.wifi_toggle_state(ad, False)
    ad.droid.connectivityToggleAirplaneMode(True)
    ad.droid.nfcDisable()
    ad.droid.setScreenBrightness(0)
    ad.adb.shell(AOD_OFF)
    ad.droid.setScreenTimeout(2200)
    ad.droid.goToSleepNow()
    ad.droid.wakeUpNow()
    ad.adb.shell(LIFT)
    ad.adb.shell(DOUBLE_TAP)
    ad.adb.shell(JUMP_TO_CAMERA)
    ad.adb.shell(RAISE_TO_CAMERA)
    ad.adb.shell(FLIP_CAMERA)
    ad.adb.shell(ASSIST_GESTURE)
    ad.adb.shell(ASSIST_GESTURE_ALERT)
    ad.adb.shell(ASSIST_GESTURE_WAKE)
    ad.adb.shell(SCREENON_USB_DISABLE)
    ad.adb.shell(UNLOCK_SCREEN)
    ad.adb.shell(SETTINGS_PAGE)
    ad.adb.shell(SCROLL_BOTTOM)
    ad.adb.shell(MUSIC_IQ_OFF)
    ad.adb.shell(AUTO_TIME_OFF)
    ad.adb.shell(AUTO_TIMEZONE_OFF)
    ad.log.info('Device has been set to Rockbottom state')


def monsoon_data_collect_save(ad, mon_info, test_name, bug_report):
    """Current measurement and save the log file.

    Collect current data using Monsoon box and return the path of the
    log file. Take bug report if requested.

    Args:
        ad: the android device under test
        mon_info: dict with information of monsoon measurement, including
                  monsoon device object, measurement frequency, duration and
                  offset etc.
        test_name: current test name, used to contruct the result file name
        bug_report: indicator to take bug report or not, 0 or 1
    Returns:
        data_path: the absolute path to the log file of monsoon current
                   measurement
        avg_current: the average current of the test
    """
    log = logging.getLogger()
    log.info("Starting power measurement with monsoon box")
    tag = (test_name + '_' + ad.model + '_' + ad.build_info['build_id'])
    #Resets the battery status right before the test started
    ad.adb.shell(RESET_BATTERY_STATS)
    begin_time = utils.get_current_human_time()
    #Start the power measurement using monsoon
    result = mon_info['dut'].measure_power(
        mon_info['freq'],
        mon_info['duration'],
        tag=tag,
        offset=mon_info['offset'])
    data_path = os.path.join(mon_info['data_path'], "%s.txt" % tag)
    avg_current = result.average_current
    monsoon.MonsoonData.save_to_text_file([result], data_path)
    log.info("Power measurement done")
    if bool(bug_report) == True:
        ad.take_bug_report(test_name, begin_time)
    return data_path, avg_current


def monsoon_data_plot(mon_info, file_path, tag=""):
    """Plot the monsoon current data using bokeh interactive plotting tool.

    Plotting power measurement data with bokeh to generate interactive plots.
    You can do interactive data analysis on the plot after generating with the
    provided widgets, which make the debugging much easier. To realize that,
    bokeh callback java scripting is used. View a sample html output file:
    https://drive.google.com/open?id=0Bwp8Cq841VnpT2dGUUxLYWZvVjA

    Args:
        mon_info: dict with information of monsoon measurement, including
                  monsoon device object, measurement frequency, duration and
                  offset etc.
        file_path: the path to the monsoon log file with current data

    Returns:
        plot: the plotting object of bokeh, optional, will be needed if multiple
           plots will be combined to one html file.
        dt: the datatable object of bokeh, optional, will be needed if multiple
           datatables will be combined to one html file.
    """

    log = logging.getLogger()
    log.info("Plot the power measurement data")
    #Get results as monsoon data object from the input file
    results = monsoon.MonsoonData.from_text_file(file_path)
    #Decouple current and timestamp data from the monsoon object
    current_data = []
    timestamps = []
    voltage = results[0].voltage
    [current_data.extend(x.data_points) for x in results]
    [timestamps.extend(x.timestamps) for x in results]
    period = 1 / float(mon_info['freq'])
    time_relative = [x * period for x in range(len(current_data))]
    #Calculate the average current for the test
    current_data = [x * 1000 for x in current_data]
    avg_current = np.average(current_data)
    color = ['navy'] * len(current_data)

    #Preparing the data and source link for bokehn java callback
    source = ColumnDataSource(data=dict(
        x0=time_relative, y0=current_data, color=color))
    s2 = ColumnDataSource(data=dict(
        z0=[mon_info['duration']],
        y0=[round(avg_current, 2)],
        x0=[round(avg_current * voltage, 2)],
        z1=[round(avg_current * voltage * mon_info['duration'], 2)],
        z2=[round(avg_current * mon_info['duration'], 2)]))
    #Setting up data table for the output
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
    output_file("%s/%s.html" % (mon_info['data_path'], plot_title))
    TOOLS = ('box_zoom,box_select,pan,crosshair,redo,undo,resize,reset,'
             'hover,xwheel_zoom,ywheel_zoom,save')
    # Create a new plot with the datatable above
    plot = figure(
        plot_width=1300,
        plot_height=700,
        title=plot_title,
        tools=TOOLS,
        webgl=True)
    plot.line('x0', 'y0', source=source, line_width=2)
    plot.circle('x0', 'y0', source=source, size=0.5, fill_color='color')
    plot.xaxis.axis_label = 'Time (s)'
    plot.yaxis.axis_label = 'Current (mA)'
    plot.title.text_font_size = {'value': '15pt'}

    #Callback Java scripting
    source.callback = CustomJS(
        args=dict(mytable=dt),
        code="""
    var inds = cb_obj.get('selected')['1d'].indices;
    var d1 = cb_obj.get('data');
    var d2 = mytable.get('source').get('data');
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
    mytable.trigger('change');
    """)

    #Layout the plot and the datatable bar
    l = layout([[dt], [plot]])
    save(l)
    return [plot, dt]


def change_dtim(ad, gEnableModulatedDTIM, gMaxLIModulatedDTIM=6):
    """Function to change the DTIM setting in the phone.

    Args:
        ad: the target android device, AndroidDevice object
        gEnableModulatedDTIM: Modulated DTIM, int
        gMaxLIModulatedDTIM: Maximum modulated DTIM, int
    """
    serial = ad.serial
    ini_file_phone = 'vendor/firmware/wlan/qca_cld/WCNSS_qcom_cfg.ini'
    ini_file_local = 'local_ini_file.ini'
    ini_pull_cmd = 'adb -s %s pull %s %s' % (serial, ini_file_phone,
                                             ini_file_local)
    ini_push_cmd = 'adb -s %s push %s %s' % (serial, ini_file_local,
                                             ini_file_phone)
    utils.exe_cmd(ini_pull_cmd)

    with open(ini_file_local, 'r') as fin:
        for line in fin:
            if 'gEnableModulatedDTIM=' in line:
                gEDTIM_old = line.strip('gEnableModulatedDTIM=').strip('\n')
            if 'gMaxLIModulatedDTIM=' in line:
                gMDTIM_old = line.strip('gMaxLIModulatedDTIM=').strip('\n')
    if int(gEDTIM_old) == gEnableModulatedDTIM:
        ad.log.info('Current DTIM is already the desired value,'
                    'no need to reset it')
        return

    gE_old = 'gEnableModulatedDTIM=' + gEDTIM_old
    gM_old = 'gMaxLIModulatedDTIM=' + gMDTIM_old
    gE_new = 'gEnableModulatedDTIM=' + str(gEnableModulatedDTIM)
    gM_new = 'gMaxLIModulatedDTIM=' + str(gMaxLIModulatedDTIM)

    sed_gE = 'sed -i \'s/%s/%s/g\' %s' % (gE_old, gE_new, ini_file_local)
    sed_gM = 'sed -i \'s/%s/%s/g\' %s' % (gM_old, gM_new, ini_file_local)
    utils.exe_cmd(sed_gE)
    utils.exe_cmd(sed_gM)

    utils.exe_cmd('adb -s {} root'.format(serial))
    cmd_out = utils.exe_cmd('adb -s {} remount'.format(serial))
    if ("Permission denied").encode() in cmd_out:
        ad.log.info('Need to disable verity first and reboot')
        utils.exe_cmd('adb -s {} disable-verity'.format(serial))
        time.sleep(1)
        ad.reboot()
        ad.log.info('Verity disabled and device back from reboot')
        utils.exe_cmd('adb -s {} root'.format(serial))
        utils.exe_cmd('adb -s {} remount'.format(serial))
    time.sleep(1)
    utils.exe_cmd(ini_push_cmd)
    ad.log.info('ini file changes checked in and rebooting...')
    ad.reboot()
    ad.log.info('DTIM updated and device back from reboot')


def ap_setup(ap, network):
    """Set up the whirlwind AP with provided network info.

    Args:
        ap: access_point object of the AP
        network: dict with information of the network, including ssid, password
                 bssid, channel etc.
    """

    log = logging.getLogger()
    bss_settings = []
    ssid = network[wutils.WifiEnums.SSID_KEY]
    password = network["password"]
    channel = network["channel"]
    security = hostapd_security.Security(
        security_mode="wpa", password=password)
    config = hostapd_ap_preset.create_ap_preset(
        channel=channel,
        ssid=ssid,
        security=security,
        bss_settings=bss_settings,
        profile_name='whirlwind')
    ap.start_ap(config)
    log.info("AP started on channel {} with SSID {}".format(channel, ssid))


def bokeh_plot(data_sets, legends, fig_property):
    """Plot bokeh figs.
        Args:
            data_sets: data sets including lists of x_data and lists of y_data
                       ex: [[[x_data1], [x_data2]], [[y_data1],[y_data2]]]
            legends: list of legend for each curve
            fig_property: dict containing the plot property, including title,
                      lables, linewidth, circle size, etc.
        Returns:
            plot: bokeh plot figure object
    """
    TOOLS = ('box_zoom,box_select,pan,crosshair,redo,undo,resize,reset,'
             'hover,xwheel_zoom,ywheel_zoom,save')
    plot = figure(
        plot_width=1300,
        plot_height=700,
        title=fig_property['title'],
        tools=TOOLS,
        webgl=True)
    colors = [
        'red', 'green', 'blue', 'olive', 'orange', 'salmon', 'black', 'navy',
        'yellow', 'darkred', 'goldenrod'
    ]
    for x_data, y_data, legend in zip(data_sets[0], data_sets[1], legends):
        index_now = legends.index(legend)
        color = colors[index_now % len(colors)]
        plot.line(
            x_data, y_data, legend=str(legend), line_width=3, color=color)
        plot.circle(
            x_data, y_data, size=10, legend=str(legend), fill_color=color)
    #Plot properties
    plot.xaxis.axis_label = fig_property['x_label']
    plot.yaxis.axis_label = fig_property['y_label']
    plot.legend.location = "top_right"
    plot.legend.click_policy = "hide"
    plot.title.text_font_size = {'value': '15pt'}
    return plot


def run_iperf_client_nonblocking(ad, server_host, extra_args=""):
    """Start iperf client on the device with nohup.

    Return status as true if iperf client start successfully.
    And data flow information as results.

    Args:
        ad: the android device under test
        server_host: Address of the iperf server.
        extra_args: A string representing extra arguments for iperf client,
            e.g. "-i 1 -t 30".

    """
    log = logging.getLogger()
    ad.adb.shell_nb("nohup iperf3 -c {} {} &".format(server_host, extra_args))
    log.info("IPerf client started")


def get_wifi_rssi(ad):
    """Get the RSSI of the device.

    Args:
        ad: the android device under test
    Returns:
        RSSI: the rssi level of the device
    """
    RSSI = ad.droid.wifiGetConnectionInfo()['rssi']
    return RSSI
