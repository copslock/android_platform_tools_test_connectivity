#!/usr/bin/env python3
#
#   Copyright 2018 - Google, Inc.
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

from acts import logger
from acts.controllers.ap_lib.hostapd_constants import AP_DEFAULT_CHANNEL_2G
from acts.controllers.ap_lib.hostapd_constants import AP_DEFAULT_CHANNEL_5G
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings

import os
import threading
import time

ACTS_CONTROLLER_CONFIG_NAME = 'PacketCapture'
ACTS_CONTROLLER_REFERENCE_NAME = 'packet_capture'
BSS = 'BSS'
BSSID = 'BSSID'
FREQ = 'freq'
FREQUENCY = 'frequency'
LEVEL = 'level'
MON_2G = 'mon0'
MON_5G = 'mon1'
BAND_IFACE = {'2G' : MON_2G, '5G': MON_5G}
SCAN_IFACE = 'wlan2'
SCAN_TIMEOUT = 60
SEP = ':'
SIGNAL = 'signal'
SSID = 'SSID'


def create(configs):
    return [PacketCapture(c) for c in configs]

def destroy(pcaps):
    for pcap in pcaps:
        pcap.close()

def get_info(pcaps):
    return [pcap.ssh_settings.hostname for pcap in pcaps]


class PcapProperties(object):
    """Class to maintain packet capture properties after starting tcpdump.

    Attributes:
        pid: proccess id of tcpdump
        pcap_dir: tmp dir location where pcap files are saved
        pcap_file: pcap file name
        pcap_thread: thread used to push files to logpath
    """
    def __init__(self, pid, pcap_dir, pcap_file, pcap_thread):
        """Initialize object."""
        self.pid = pid
        self.pcap_dir = pcap_dir
        self.pcap_file = pcap_file
        self.pcap_thread = pcap_thread


class PacketCaptureError(Exception):
    """Error related to Packet capture."""


class PacketCapture(object):
    """Class representing packet capturer.

    An instance of this class creates and configures two interfaces for monitor
    mode; 'mon0' for 2G and 'mon1' for 5G and one interface for scanning for
    wifi networks; 'wlan2' which is a dual band interface.

    Attributes:
        pcap: dict that specifies packet capture properties for a band.
        tmp_dirs: list of tmp directories created for pcap files.
    """
    def __init__(self, configs):
        """Initialize objects.

        Args:
            configs: config for the packet capture.
        """
        self.ssh_settings = settings.from_config(configs['ssh_config'])
        self.ssh = connection.SshConnection(self.ssh_settings)
        self.log = logger.create_logger(lambda msg: '[%s|%s] %s' % (
            ACTS_CONTROLLER_CONFIG_NAME, self.ssh_settings.hostname, msg))

        self._create_interface(MON_2G, 'monitor')
        self._create_interface(MON_5G, 'monitor')
        self._create_interface(SCAN_IFACE, 'managed')

        self.pcap_properties = dict()
        self._pcap_stop_lock = threading.Lock()
        self.tmp_dirs = []

    def _create_interface(self, iface, mode):
        """Create interface of monitor/managed mode.

        Create mon0/mon1 for 2G/5G monitor mode and wlan2 for managed mode.
        """
        self.ssh.run('iw dev %s del' % iface, ignore_status=True)
        self.ssh.run('iw phy%s interface add %s type %s'
                     % (iface[-1], iface, mode), ignore_status=True)
        self.ssh.run('ip link set %s up' % iface, ignore_status=True)
        result = self.ssh.run('iw dev %s info' % iface, ignore_status=True)
        if result.stderr or iface not in result.stdout:
            raise PacketCaptureError('Failed to configure interface %s' % iface)

    def _cleanup_interface(self, iface):
        """Clean up monitor mode interfaces."""
        self.ssh.run('iw dev %s del' % iface, ignore_status=True)
        result = self.ssh.run('iw dev %s info' % iface, ignore_status=True)
        if not result.stderr or 'No such device' not in result.stderr:
            raise PacketCaptureError('Failed to cleanup monitor mode for %s'
                                     % iface)

    def _parse_scan_results(self, scan_result):
        """Parses the scan dump output and returns list of dictionaries.

        Args:
            scan_result: scan dump output from scan on mon interface.

        Returns:
            Dictionary of found network in the scan.
            The attributes returned are
                a.) SSID - SSID of the network.
                b.) LEVEL - signal level.
                c.) FREQUENCY - WiFi band the network is on.
                d.) BSSID - BSSID of the network.
        """
        scan_networks = []
        network = {}
        for line in scan_result.splitlines():
            if SEP not in line:
                continue
            if BSS in line:
                network[BSSID] = line.split('(')[0].split()[-1]
            field, value = line.lstrip().rstrip().split(SEP)[0:2]
            value = value.lstrip()
            if SIGNAL in line:
                network[LEVEL] = int(float(value.split()[0]))
            elif FREQ in line:
                network[FREQUENCY] = int(value)
            elif SSID in line:
                network[SSID] = value
                scan_networks.append(network)
                network = {}
        return scan_networks

    def _check_if_tcpdump_started(self, pcap_log):
        """Check if tcpdump started.

        This method ensures that tcpdump has started successfully.
        We look for 'listening on' from the stdout indicating that tcpdump
        is started.

        Args:
            pcap_log: log file that has redirected output of starting tcpdump.

        Returns:
            True/False if tcpdump is started or not.
        """
        curr_time = time.time()
        timeout = 3
        find_str = 'listening on'
        while time.time() < curr_time + timeout:
            result = self.ssh.run('grep "%s" %s' % (find_str, pcap_log),
                                  ignore_status=True)
            if result.stdout and find_str in result.stdout:
                return True
            time.sleep(1)
        return False

    def _pull_pcap(self, band, pcap_file, log_path):
        """Pulls pcap files to test log path from onhub.

        Called by start_packet_capture(). This method moves a pcap file to log
        path once it has reached 50MB.

        Args:
            index: param that indicates if the tcpdump is stopped.
            pcap_file: pcap file to move.
            log_path: log path to move the pcap file to.
        """
        curr_no = 0
        while True:
            next_no = curr_no + 1
            curr_fno = '%02i' % curr_no
            next_fno = '%02i' % next_no
            curr_file = '%s%s' % (pcap_file, curr_fno)
            next_file = '%s%s' % (pcap_file, next_fno)

            result = self.ssh.run('ls %s' % next_file, ignore_status=True)
            if not result.stderr and next_file in result.stdout:
                self.ssh.pull_file(log_path, curr_file)
                self.ssh.run('rm -rf %s' % curr_file, ignore_status=True)
                curr_no += 1
                continue

            with self._pcap_stop_lock:
                if band not in self.pcap_properties:
                    self.ssh.pull_file(log_path, curr_file)
                    break
            time.sleep(2) # wait before looking for file again

    def get_wifi_scan_results(self):
        """Starts a wifi scan on wlan2 interface.

        Returns:
            List of dictionaries each representing a found network.
        """
        result = self.ssh.run('iw dev %s scan' % SCAN_IFACE)
        if result.stderr:
            raise PacketCaptureError('Failed to get scan dump')
        if not result.stdout:
            return []
        return self._parse_scan_results(result.stdout)

    def start_scan_and_find_network(self, ssid):
        """Start a wifi scan on wlan2 interface and find network.

        Args:
            ssid: SSID of the network.

        Returns:
            True/False if the network if found or not.
        """
        curr_time = time.time()
        while time.time() < curr_time + SCAN_TIMEOUT:
            found_networks = self.get_wifi_scan_results()
            for network in found_networks:
                if network[SSID] == ssid:
                    return True
            time.sleep(3) # sleep before next scan
        return False

    def configure_monitor_mode(self, band, channel):
        """Configure monitor mode.

        Args:
            band: band to configure monitor mode for.
            channel: channel to set for the interface.

        Returns:
            True if configure successful.
            False if not successful.
        """
        band = band.upper()
        if band not in BAND_IFACE:
            self.log.error('Invalid band. Must be 2g/2G or 5g/5G')
            return False

        iface = BAND_IFACE[band]
        self.ssh.run('iw dev %s set channel %s' %
                     (iface, channel), ignore_status=True)
        result = self.ssh.run('iw dev %s info' % iface, ignore_status=True)
        if result.stderr or 'channel %s' % channel not in result.stdout:
            self.log.error("Failed to configure monitor mode for %s" % band)
            return False
        return True

    def start_packet_capture(self, band, log_path, pcap_file):
        """Start packet capture for band.

        band = 2G starts tcpdump on 'mon0' interface.
        band = 5G starts tcpdump on 'mon1' interface.

        This method splits the pcap file every 50MB for 100 files.
        Since, the size of the pcap file could become large, each split file
        is moved to log_path once a new file is generated. This ensures that
        there is no crash on the onhub router due to lack of space.

        Args:
            band: '2g' or '2G' and '5g' or '5G'.
            log_path: test log path to save the pcap file.
            pcap_file: name of the pcap file.

        Returns:
            pid: process id of the tcpdump.
        """
        band = band.upper()
        if band not in BAND_IFACE.keys() or band in self.pcap_properties:
            self.log.error("Invalid band or packet capture already running")
            return None

        pcap_dir = self.ssh.run('mktemp -d', ignore_status=True).stdout.rstrip()
        self.tmp_dirs.append(pcap_dir)
        pcap_file = os.path.join(pcap_dir, "%s_%s.pcap" % (pcap_file, band))
        pcap_log = os.path.join(pcap_dir, "%s.log" % pcap_file)

        cmd = 'tcpdump -i %s -W 100 -C 50 -w %s > %s 2>&1 & echo $!' % (
            BAND_IFACE[band], pcap_file, pcap_log)
        result = self.ssh.run(cmd, ignore_status=True)
        if not self._check_if_tcpdump_started(pcap_log):
            self.log.error("Failed to start packet capture")
            return None

        pcap_thread = threading.Thread(target=self._pull_pcap,
                                       args=(band, pcap_file, log_path))
        pcap_thread.start()

        pid = int(result.stdout)
        self.pcap_properties[band] = PcapProperties(
            pid, pcap_dir, pcap_file, pcap_thread)
        return pid

    def stop_packet_capture(self, pid):
        """Stop the packet capture.

        Args:
            pid: process id of tcpdump to kill.
        """
        for key, val in self.pcap_properties.items():
            if val.pid == pid:
                break
        else:
            self.log.error("Failed to stop tcpdump. Invalid PID %s" % pid)
            return

        pcap_dir = val.pcap_dir
        pcap_thread = val.pcap_thread
        self.ssh.run('kill %s' % pid, ignore_status=True)
        with self._pcap_stop_lock:
            del self.pcap_properties[key]
        pcap_thread.join()
        self.ssh.run('rm -rf %s' % pcap_dir, ignore_status=True)
        self.tmp_dirs.remove(pcap_dir)

    def close(self):
        """Cleanup.

        Cleans up all the monitor mode interfaces and closes ssh connections.
        """
        self._cleanup_interface(MON_2G)
        self._cleanup_interface(MON_5G)
        for tmp_dir in self.tmp_dirs:
            self.ssh.run('rm -rf %s' % tmp_dir, ignore_status=True)
        self.ssh.close()
