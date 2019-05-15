#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
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

import json
import logging
import os
import random
import re
import requests
import subprocess
import time

from acts import context
from acts import logger as acts_logger
from acts import signals

from acts.controllers.fuchsia_lib.bt.ble_lib import FuchsiaBleLib
from acts.controllers.fuchsia_lib.bt.btc_lib import FuchsiaBtcLib
from acts.controllers.fuchsia_lib.bt.gattc_lib import FuchsiaGattcLib
from acts.controllers.fuchsia_lib.bt.gatts_lib import FuchsiaGattsLib
from acts.controllers.fuchsia_lib.netstack.netstack_lib import FuchsiaNetstackLib
from acts.controllers.fuchsia_lib.syslog_lib import start_syslog
from acts.controllers.fuchsia_lib.wlan_lib import FuchsiaWlanLib
from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings
from acts.libs.proc.job import Error
from acts.utils import is_valid_ipv4_address
from acts.utils import is_valid_ipv6_address
from acts.utils import SuppressLogOutput


ACTS_CONTROLLER_CONFIG_NAME = "FuchsiaDevice"
ACTS_CONTROLLER_REFERENCE_NAME = "fuchsia_devices"

FUCHSIA_DEVICE_EMPTY_CONFIG_MSG = "Configuration is empty, abort!"
FUCHSIA_DEVICE_NOT_LIST_CONFIG_MSG = "Configuration should be a list, abort!"
FUCHSIA_DEVICE_INVALID_CONFIG = ("Fuchsia device config must be either a str "
                                 "or dict. abort! Invalid element %i in %r")
FUCHSIA_DEVICE_NO_IP_MSG = "No IP address specified, abort!"
FUCHSIA_COULD_NOT_GET_DESIRED_STATE = "Could not %s SL4F."
FUCHSIA_INVALID_CONTROL_STATE = "Invalid control state (%s). abort!"
FUCHSIA_SSH_CONFIG_NOT_DEFINED = ("Cannot send ssh commands since the "
                                  "ssh_config was not specified in the Fuchsia"
                                  "device config.")

FUCHSIA_SSH_USERNAME = "fuchsia"

SL4F_APK_NAME = "com.googlecode.android_scripting"
SL4F_INIT_TIMEOUT_SEC = 1

SL4F_ACTIVATED_STATES = ["running", "start"]
SL4F_DEACTIVATED_STATES = ["stop", "stopped"]

FUCHSIA_DEFAULT_LOG_CMD = 'iquery --absolute_paths --cat --format= --recursive'
FUCHSIA_DEFAULT_LOG_ITEMS = ['/hub/c/scenic.cmx/[0-9]*/out/objects',
                             '/hub/c/root_presenter.cmx/[0-9]*/out/objects',
                             '/hub/c/wlanstack2.cmx/[0-9]*/out/public',
                             '/hub/c/basemgr.cmx/[0-9]*/out/objects']

FUCHSIA_RECONNECT_AFTER_REBOOT_TIME = 5


class FuchsiaDeviceError(signals.ControllerError):
    pass


def create(configs):
    if not configs:
        raise FuchsiaDeviceError(FUCHSIA_DEVICE_EMPTY_CONFIG_MSG)
    elif not isinstance(configs, list):
        raise FuchsiaDeviceError(FUCHSIA_DEVICE_NOT_LIST_CONFIG_MSG)
    for index, config in enumerate(configs):
        if isinstance(config, str):
            configs[index] = {"ip": config}
        elif not isinstance(config, dict):
            raise FuchsiaDeviceError(FUCHSIA_DEVICE_INVALID_CONFIG %
                                     (index, configs))
    return get_instances(configs)


def destroy(fds):
    for fd in fds:
        fd.clean_up()
        del fd


def get_info(fds):
    """Get information on a list of FuchsiaDevice objects.

    Args:
        fds: A list of FuchsiaDevice objects.

    Returns:
        A list of dict, each representing info for FuchsiaDevice objects.
    """
    device_info = []
    for fd in fds:
        info = {"ip": fd.ip}
        device_info.append(info)
    return device_info


def get_instances(fds_conf_data):
    """Create FuchsiaDevice instances from a list of Fuchsia ips.

    Args:
        fds_conf_data: A list of dicts that contain Fuchsia device info.

    Returns:
        A list of FuchsiaDevice objects.
    """

    return [FuchsiaDevice(fd_conf_data) for fd_conf_data in fds_conf_data]


class FuchsiaDevice:
    """Class representing a Fuchsia device.

    Each object of this class represents one Fuchsia device in ACTS.

    Attributes:
        address: The full address to contact the Fuchsia device at
        log: A logger object.
        port: The TCP port number of the Fuchsia device.
    """

    def __init__(self, fd_conf_data):
        """
        Args:
            fd_conf_data: A dict of a fuchsia device configuration data
                Required keys:
                    ip: IP address of fuchsia device
                optional key:
                    port: Port for the sl4f web server on the fuchsia device
                        (Default: 80)
                    ssh_config: Location of the ssh_config file to connect to
                        the fuchsia device
                        (Default: None)
        """
        if "ip" not in fd_conf_data:
            raise FuchsiaDeviceError(FUCHSIA_DEVICE_NO_IP_MSG)
        self.ip = fd_conf_data["ip"]
        self.port = fd_conf_data.get("port", 80)
        self.ssh_config = fd_conf_data.get("ssh_config", None)
        self.ssh_username = fd_conf_data.get("ssh_username",
                                             FUCHSIA_SSH_USERNAME)
        self.sl4f_ssh_conn = None

        self.log = acts_logger.create_tagged_trace_logger(
            "FuchsiaDevice | %s" % self.ip)

        if is_valid_ipv4_address(self.ip):
            self.address = "http://{}:{}".format(self.ip, self.port)
        elif is_valid_ipv6_address(self.ip):
            self.address = "http://[{}]:{}".format(self.ip, self.port)
        else:
            raise ValueError('Invalid IP: %s' % self.ip)

        self.init_address = self.address + "/init"
        self.cleanup_address = self.address + "/cleanup"
        self.print_address = self.address + "/print_clients"
        self.ping_rtt_match = re.compile(r'RTT Min/Max/Avg '
                                         r'= \[ (.*?) / (.*?) / (.*?) \] ms')

        # TODO(): Come up with better client numbering system
        self.client_id = "FuchsiaClient" + str(random.randint(0, 1000000))
        self.test_counter = 0

        self.serial = self.ip.replace('.', '_').replace(':', '_')
        log_path_base = getattr(logging, 'log_path', '/tmp/logs')
        self.log_path = os.path.join(log_path_base,
                                     'FuchsiaDevice%s' % self.serial)
        self.fuchsia_log_file_path = os.path.join(
            self.log_path, "fuchsialog_%s_debug.txt" % self.serial)
        self.log_process = None

        # Grab commands from FuchsiaBleLib
        self.ble_lib = FuchsiaBleLib(self.address, self.test_counter,
                                     self.client_id)
        # Grab commands from FuchsiaBtcLib
        self.btc_lib = FuchsiaBtcLib(self.address, self.test_counter,
                                     self.client_id)
        # Grab commands from FuchsiaGattcLib
        self.gattc_lib = FuchsiaGattcLib(self.address, self.test_counter,
                                         self.client_id)
        # Grab commands from FuchsiaGattsLib
        self.gatts_lib = FuchsiaGattsLib(self.address, self.test_counter,
                                         self.client_id)

        # Grab commands from FuchsiaNetstackLib
        self.netstack_lib = FuchsiaNetstackLib(self.address, self.test_counter,
                                               self.client_id)
        # Grab commands from FuchsiaWlanLib
        self.wlan_lib = FuchsiaWlanLib(self.address, self.test_counter,
                                       self.client_id)
        # Start sl4f on device
        self.start_services()
        # Init server
        self.init_server_connection()

    def init_server_connection(self):
        """Initializes HTTP connection with SL4F server."""
        self.log.debug("Initialziing server connection")
        init_data = json.dumps({
            "jsonrpc": "2.0",
            "id": self.build_id(self.test_counter),
            "method": "sl4f.sl4f_init",
            "params": {
                "client_id": self.client_id
            }
        })
        requests.get(url=self.init_address, data=init_data)
        self.test_counter += 1

    def build_id(self, test_id):
        """Concatenates client_id and test_id to form a command_id

        Args:
            test_id: string, unique identifier of test command
        """
        return self.client_id + "." + str(test_id)

    def send_command_sl4f(self, test_id, test_cmd, test_args):
        """Builds and sends a JSON command to SL4F server.

        Args:
            test_id: string, unique identifier of test command.
            test_cmd: string, sl4f method name of command.
            test_args: dictionary, arguments required to execute test_cmd.

        Returns:
            Dictionary, Result of sl4f command executed.
        """
        test_data = json.dumps({
            "jsonrpc": "2.0",
            "id": self.build_id(self.test_counter),
            "method": test_cmd,
            "params": test_args
        })
        return requests.get(url=self.address, data=test_data).json()

    def reboot(self, timeout=60):
        """Reboot a Fuchsia device and restablish all the services after reboot

        Args:
            timeout: How long to wait for the device to reboot.

              Disables the logging when sending the reboot command
              because the ssh session does not disconnect cleanly and therefore
              would throw an error.  This is expected and thus the error logging
              is disabled for this call.
        """
        ping_command = ['ping', '-t', '1', '-c', '1', self.ip]
        self.clean_up()
        self.log.info('Rebooting FuchsiaDevice %s' % self.ip)
        # Disables the logging when sending the reboot command
        # because the ssh session does not disconnect cleanly and therefore
        # would throw an error.  This is expected and thus the error logging
        # is disabled for this call to not confuse the user.
        with SuppressLogOutput():
            self.send_command_ssh('dm reboot',
                                  timeout=FUCHSIA_RECONNECT_AFTER_REBOOT_TIME)
        start_time = time.time()
        self.log.info('Waiting for FuchsiaDevice %s to come back up.' % self.ip)
        while not subprocess.call(ping_command,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.STDOUT) == 0:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                raise TimeoutError('Waited %s seconds, and FuchsiaDevice %s'
                                   'did not come back up.' % (elapsed_time,
                                                              self.ip))
        # Wait another 5 seconds after receiving a ping packet to just to let
        # the OS get everything up and running.
        time.sleep(5)
        # Start sl4f on device
        self.start_services()
        # Init server
        self.init_server_connection()

    def send_command_ssh(self,
                         test_cmd,
                         connect_timeout=30,
                         timeout=3600):
        """Sends an SSH command to a Fuchsia device

        Args:
            test_cmd: string, command to send to Fuchsia device over SSH.
            connect_timeout: Timeout to wait for connecting via SSH.
            timeout: Timeout to wait for a command to complete.

        Returns:
            A job.Result containing the results of the ssh command.
        """
        command_result = False
        ssh_conn = None
        if not self.ssh_config:
            self.log.warning(FUCHSIA_SSH_CONFIG_NOT_DEFINED)
        else:
            try:
                ssh_conn = self.create_ssh_connection(
                    connect_timeout=connect_timeout)
                command_result = ssh_conn.run(test_cmd, timeout=timeout)
            except Exception as e:
                self.log.warning("Problem running ssh command: %s"
                                 "\n Exception: %s" % (test_cmd, e))
                return e
            finally:
                ssh_conn.close()
        return command_result

    def ping(self, dest_ip, count=3, interval=1000, timeout=1000, size=25):
        """Pings from a Fuchsia device to an IPv4 address or hostname

        Args:
            dest_ip: (str) The ip or hostname to ping.
            count: (int) How many icmp packets to send.
            interval: (int) How long to wait between pings (ms)
            timeout: (int) How long to wait before having the icmp packet
                timeout (ms).
            size: (int) Size of the icmp packet.

        Returns:
            A dictionary for the results of the ping.  The dictionary contains
            the following items:
                status: Whether the ping was successful.
                rtt_min: The minimum round trip time of the ping.
                rtt_max: The minimum round trip time of the ping.
                rtt_avg: The avg round trip time of the ping.
                stdout: The standard out of the ping command.
                stderr: The standard error of the ping command.
        """
        rtt_min = None
        rtt_max = None
        rtt_avg = None
        self.log.info("Pinging %s...", dest_ip)
        ping_result = self.send_command_ssh(
            'ping -c %s -i %s -t %s -s %s %s' % (count,
                                                 interval,
                                                 timeout,
                                                 size,
                                                 dest_ip))
        if isinstance(ping_result, Error):
            ping_result = ping_result.result

        if ping_result.stderr:
            status = False
        else:
            status = True
            rtt_stats = re.search(self.ping_rtt_match,
                                  ping_result.stdout.split('\n')[-1])
            rtt_min = rtt_stats.group(1)
            rtt_max = rtt_stats.group(2)
            rtt_avg = rtt_stats.group(3)
        return {'status': status,
                'rtt_min': rtt_min,
                'rtt_max': rtt_max,
                'rtt_avg': rtt_avg,
                'stdout': ping_result.stdout,
                'stderr': ping_result.stderr}

    def print_clients(self):
        """Gets connected clients from SL4F server"""
        self.log.debug("Request to print clients")
        print_id = self.build_id(self.test_counter)
        print_args = {}
        print_method = "sl4f.sl4f_print_clients"
        data = json.dumps({
            "jsonrpc": "2.0",
            "id": print_id,
            "method": print_method,
            "params": print_args
        })

        r = requests.get(url=self.print_address, data=data).json()
        self.test_counter += 1

        return r

    def clean_up(self):
        """Cleans up the FuchsiaDevice object and releases any resources it
        claimed.
        """
        cleanup_id = self.build_id(self.test_counter)
        cleanup_args = {}
        cleanup_method = "sl4f.sl4f_cleanup"
        data = json.dumps({
            "jsonrpc": "2.0",
            "id": cleanup_id,
            "method": cleanup_method,
            "params": cleanup_args
        })

        r = requests.get(url=self.cleanup_address, data=data).json()
        self.test_counter += 1

        self.log.debug("Cleaned up with status: {}".format(r))
        self.stop_services()
        return r

    def create_ssh_connection(self,
                              connect_timeout=30):
        """Creates and ssh connection to a Fuchsia device

        Returns:
            An ssh connection object
        """
        ssh_settings = settings.from_config({
            "host": self.ip,
            "user": self.ssh_username,
            "ssh_config": self.ssh_config,
            "connect_timeout": connect_timeout
        })
        return connection.SshConnection(ssh_settings)

    @staticmethod
    def check_sl4f_state(ssh_connection):
        """Checks the state of sl4f on the Fuchsia device

        Args:
            ssh_connection: An ssh connection object with a valid ssh
                connection established
        Returns:
            True if sl4f is running
            False if sl4f is not running
        """
        ps_cmd = ssh_connection.run("ps")
        return "sl4f.cmx" in ps_cmd.stdout

    def check_sl4f_with_expectation(self, ssh_connection, expectation=None):
        """Checks the state of sl4f on the Fuchsia device and returns true or
           or false depending the stated expectation

        Args:
            ssh_connection: An ssh connection object with a valid ssh
                connection established
            expectation: The state expectation of state of sl4f
        Returns:
            True if the state of sl4f matches the expectation
            False if the state of sl4f does not match the expectation
        """
        sl4f_state = self.check_sl4f_state(ssh_connection)
        if expectation in SL4F_ACTIVATED_STATES:
            return sl4f_state
        elif expectation in SL4F_DEACTIVATED_STATES:
            return not sl4f_state
        else:
            raise ValueError("Invalid expectation value (%s). abort!" %
                             expectation)

    def control_sl4f(self, action):
        """Starts or stops sl4f on a Fuchsia device

        Args:
            action: specify whether to start or stop sl4f
        """
        ssh_conn = None
        unable_to_connect_msg = None
        sl4f_state = False
        try:
            if not self.sl4f_ssh_conn:
                self.sl4f_ssh_conn = self.create_ssh_connection()
            self.sl4f_ssh_conn.run_async("killall sl4f.cmx")
            # This command will effectively stop sl4f but should
            # be used as a cleanup before starting sl4f.  It is a bit
            # confusing to have the msg saying "attempting to stop
            # sl4f" after the command already tried but since both start
            # and stop need to run this command, this is the best place
            # for the command.
            if action in SL4F_ACTIVATED_STATES:
                self.log.debug("Attempting to start Fuchsia "
                               "devices services.")
                self.sl4f_ssh_conn.run_async("run fuchsia-pkg://"
                                             "fuchsia.com/sl4f#meta/sl4f.cmx &")
                sl4f_initial_msg = ("SL4F has not started yet. "
                                    "Waiting %i second and checking "
                                    "again." % SL4F_INIT_TIMEOUT_SEC)
                sl4f_timeout_msg = "Timed out waiting for SL4F to start."
                unable_to_connect_msg = ("Unable to connect to Fuchsia "
                                         "device via SSH. SL4F may not "
                                         "be started.")
            elif action in SL4F_DEACTIVATED_STATES:
                sl4f_initial_msg = ("SL4F is running. "
                                    "Waiting %i second and checking "
                                    "again." % SL4F_INIT_TIMEOUT_SEC)
                sl4f_timeout_msg = ("Timed out waiting "
                                    "trying to kill SL4F.")
                unable_to_connect_msg = ("Unable to connect to Fuchsia "
                                         "device via SSH. SL4F may "
                                         "still be running.")
            else:
                raise FuchsiaDeviceError(FUCHSIA_INVALID_CONTROL_STATE %
                                         action)
            timeout_counter = 0
            while not sl4f_state:
                self.log.debug(sl4f_initial_msg)
                time.sleep(SL4F_INIT_TIMEOUT_SEC)
                timeout_counter += 1
                sl4f_state = self.check_sl4f_with_expectation(
                    ssh_connection=self.sl4f_ssh_conn, expectation=action)
                if timeout_counter == (SL4F_INIT_TIMEOUT_SEC * 3):
                    self.log.error(sl4f_timeout_msg)
                    break
            if not sl4f_state:
                raise FuchsiaDeviceError(FUCHSIA_COULD_NOT_GET_DESIRED_STATE %
                                         action)
        except Exception as e:
            self.log.error(unable_to_connect_msg)
            raise e
        finally:
            if action == 'stop':
                self.sl4f_ssh_conn.close()
                self.sl4f_ssh_conn = None

    def check_connection_for_response(self, connection_response):
        if connection_response.get("error") is None:
            # Checks the response from SL4F and if there is no error, check
            # the result.
            connection_result = connection_response.get("result")
            if not connection_result:
                # Ideally the error would be present but just outputting a log
                # message until available.
                self.log.error("Connect call failed, aborting!")
                return False
            else:
                # Returns True if connection was successful.
                return True
        else:
            # the response indicates an error - log and raise failure
            self.log.error("Aborting! - Connect call failed with error: %s"
                           % connection_response.get("error"))
            return False

    def start_services(self, skip_sl4f=False):
        """Starts long running services on the Fuchsia device.

        1. Start SL4F if not skipped.

        Args:
            skip_sl4f: Does not attempt to start SL4F if True.
        """
        self.log.debug("Attempting to start Fuchsia device services on %s." %
                       self.ip)
        if self.ssh_config:
            """
            self.log_process = start_syslog(self.serial,
                                            self.log_path,
                                            self.ip,
                                            self.ssh_config)
            self.log_process.start()
            """
            if not skip_sl4f:
                self.control_sl4f("start")

    def stop_services(self):
        """Stops long running services on the android device.

        Terminate sl4f sessions if exist.
        """
        self.log.debug("Attempting to stop Fuchsia device services on %s." %
                       self.ip)
        if self.ssh_config:
            self.control_sl4f("stop")
            if self.log_process:
                self.log_process.stop()

    def load_config(self, config):
        pass

    def take_bug_report(self,
                        test_name,
                        begin_time,
                        additional_log_objects=None):
        """Takes a bug report on the device and stores it in a file.

        Args:
            test_name: Name of the test case that triggered this bug report.
            begin_time: Epoch time when the test started.
            additional_log_objects: A list of additional objects in Fuchsia to
                query in the bug report.  Must be in the following format:
                /hub/c/scenic.cmx/[0-9]*/out/objects
        """
        if not additional_log_objects:
            additional_log_objects = []
        log_items = []
        matching_log_items = FUCHSIA_DEFAULT_LOG_ITEMS
        for additional_log_object in additional_log_objects:
            if additional_log_object not in matching_log_items:
                matching_log_items.append(additional_log_object)
        br_path = context.get_current_context().get_full_output_path()
        os.makedirs(br_path, exist_ok=True)
        time_stamp = acts_logger.normalize_log_line_timestamp(
            acts_logger.epoch_to_log_line_timestamp(begin_time))
        out_name = "FuchsiaDevice%s_%s" % (
            self.serial, time_stamp.replace(" ", "_").replace(":", "-"))
        out_name = "%s.txt" % out_name
        full_out_path = os.path.join(br_path, out_name)
        self.log.info("Taking bugreport for %s on FuchsiaDevice%s."
                      % (test_name, self.serial))
        system_objects = self.send_command_ssh('iquery --find /hub').stdout
        system_objects = system_objects.split()

        for matching_log_item in matching_log_items:
            for system_object in system_objects:
                if re.match(matching_log_item, system_object):
                    log_items.append(system_object)

        log_command = '%s %s' % (FUCHSIA_DEFAULT_LOG_CMD,
                                 ' '.join(log_items))
        bug_report_data = self.send_command_ssh(log_command).stdout

        bug_report_file = open(full_out_path,'w')
        bug_report_file.write(bug_report_data)
        bug_report_file.close()


class FuchsiaDeviceLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        msg = "[FuchsiaDevice|%s] %s" % (self.extra["ip"], msg)
        return msg, kwargs
