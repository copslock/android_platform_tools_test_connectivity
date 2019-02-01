#!/usr/bin/env python3.5
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

import time
import re
import os
import logging
from multiprocessing import Process

from acts import utils
from acts.base_test import BaseTestClass
from acts.controllers.android_device import list_adb_devices
from acts.controllers.android_device import list_fastboot_devices
from acts.controllers.android_device import DEFAULT_QXDM_LOG_PATH
from acts.controllers.android_device import SL4A_APK_NAME
from acts.test_decorators import test_tracker_info
from acts.test_utils.wifi import wifi_test_utils as wutils
from acts.test_utils.tel import tel_test_utils as tutils
from acts.utils import get_current_epoch_time

WifiEnums = wutils.WifiEnums


class GNSSSanityTest(BaseTestClass):
    """ GNSS Function Sanity Tests"""
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.ad = self.android_devices[0]
        req_params = ["pixel_lab_network", "qxdm_masks",
                      "standalone_cs_criteria", "supl_cs_criteria",
                      "xtra_ws_criteria", "xtra_cs_criteria",
                      "weak_signal_supl_cs_criteria",
                      "weak_signal_xtra_ws_criteria",
                      "weak_signal_xtra_cs_criteria",
                      "default_gnss_signal_attenuation",
                      "weak_gnss_signal_attenuation",
                      "no_gnss_signal_attenuation", "pull_timeout", ]
        self.unpack_userparams(req_param_names=req_params)
        # create hashmap for SSID
        self.ssid_map = {}
        for network in self.pixel_lab_network:
            SSID = network['SSID'].replace('-', '_')
            self.ssid_map[SSID] = network

    def setup_class(self):
        self.ad.droid.wakeLockAcquireBright()
        self.ad.droid.wakeUpNow()
        self.set_attenuator_gnss_signal(self.default_gnss_signal_attenuation)
        self._init_device()
        if not tutils.verify_internet_connection(self.ad.log,
                                                 self.ad,
                                                 retries=3,
                                                 expected_state=True):
            tutils.abort_all_tests(self.ad.log,
                                   "Fail to connect to LTE network")
        if not self.verify_location_service():
            tutils.abort_all_tests(self.ad.log, "Fail to switch Location on")

    def setup_test(self):
        self.clear_logd_gnss_qxdm_log()

    def teardown_class(self):
        self.ad.droid.wakeLockRelease()
        self.ad.droid.goToSleepNow()

    def teardown_test(self):
        tutils.stop_qxdm_logger(self.ad)

    def on_fail(self, test_name, begin_time):
        self.get_gnss_qxdm_log(test_name)
        self.ad.take_bug_report(test_name, begin_time)

    """Helper functions"""

    def remount_device(self):
        """Remount device file system to read and write."""
        self.ad.root_adb()
        remount_result = self.ad.adb.remount()
        self.ad.log.info("%s" % remount_result)
        if self.ad.adb.getprop("ro.boot.veritymode") == "enforcing":
            disable_verity_result = self.ad.adb.disable_verity()
            self.ad.log.info("%s" % disable_verity_result)
            self.ad.reboot()
            self.ad.unlock_screen(password=None)
            self.remount_device()

    def enable_gnss_verbose_logging(self):
        """Enable GNSS VERBOSE Logging and logd."""
        self.remount_device()
        self.ad.log.info("Enable GNSS VERBOSE Logging and logd.")
        self.ad.adb.shell("echo log.tag.LocationManagerService=VERBOSE "
                          ">> /data/local.prop")
        self.ad.adb.shell("echo log.tag.GnssLocationProvider=VERBOSE "
                          ">> /data/local.prop")
        self.ad.adb.shell("echo log.tag.GnssMeasurementsProvider=VERBOSE "
                          ">> /data/local.prop")
        self.ad.adb.shell("chmod 644 /data/local.prop")
        self.ad.adb.shell("setprop persist.logd.logpersistd logcatd")
        self.ad.adb.shell("setprop persist.vendor.radio.adb_log_on 1")
        self.ad.adb.shell("sync")

    def disable_xtra_throttle(self):
        """Disable XTRA throttle will have no limit to download XTRA data."""
        self.remount_device()
        self.ad.log.info("Disable XTRA Throttle.")
        self.ad.adb.shell("echo DEBUG_LEVEL = 5 >> /vendor/etc/gps.conf")
        self.ad.adb.shell("echo XTRA_TEST_ENABLED=1 >> /vendor/etc/gps.conf")
        self.ad.adb.shell("echo XTRA_THROTTLE_ENABLED=0 >> "
                          "/vendor/etc/gps.conf")

    def enable_supl_mode(self):
        """Enable SUPL back on for next test item."""
        self.remount_device()
        self.ad.log.info("Enable SUPL mode.")
        self.ad.adb.shell("echo SUPL_MODE=1 >> /etc/gps_debug.conf")

    def disable_supl_mode(self):
        """Kill SUPL to test XTRA only test item."""
        self.remount_device()
        self.ad.log.info("Disable SUPL mode.")
        self.ad.adb.shell("echo SUPL_MODE=0 >> /etc/gps_debug.conf")
        self.ad.log.info("Reboot device to make changes take effect.")
        self.ad.reboot()
        self.ad.unlock_screen(password=None)

    def kill_xtra_daemon(self):
        """Kill XTRA daemon to test SUPL only test item."""
        self.ad.root_adb()
        self.ad.log.info("Disable XTRA-daemon until next reboot.")
        self.ad.adb.shell("killall xtra-daemon")

    def disable_private_dns_mode(self):
        """Due to b/118365122, it's better to disable private DNS mode while
           testing. 8.8.8.8 private dns sever is unstable now, sometimes server
           will not response dns query suddenly.
        """
        tutils.get_operator_name(self.ad.log, self.ad, subId=None)
        if self.ad.adb.shell("settings get global private_dns_mode") != "off":
            self.ad.log.info("Disable Private DNS mode.")
            self.ad.adb.shell("settings put global private_dns_mode off")

    def _init_device(self):
        """Init GNSS test devices."""
        self.enable_gnss_verbose_logging()
        self.disable_xtra_throttle()
        self.enable_supl_mode()
        utils.set_location_service(self.ad, True)
        self.ad.adb.shell("svc power stayon true")
        wutils.wifi_toggle_state(self.ad, False)
        self.ad.log.info("Setting Bluetooth state to False")
        self.ad.droid.bluetoothToggleState(False)
        tutils.synchronize_device_time(self.ad)
        tutils.print_radio_info(self.ad)
        for mask in self.qxdm_masks:
            if not tutils.find_qxdm_log_mask(self.ad, mask):
                continue
            tutils.set_qxdm_logger_command(self.ad, mask)
            break
        self.disable_private_dns_mode()
        self.ad.reboot()
        self.ad.unlock_screen(password=None)

    def connect_to_wifi_network(self, network):
        """Connection logic for open and psk wifi networks.

        Args:
            network: Dictionary with network info.
        """
        SSID = network[WifiEnums.SSID_KEY]
        self.ad.ed.clear_all_events()
        wutils.start_wifi_connection_scan(self.ad)
        scan_results = self.ad.droid.wifiGetScanResults()
        wutils.assert_network_in_list({WifiEnums.SSID_KEY: SSID}, scan_results)
        wutils.wifi_connect(self.ad, network, num_of_tries=5)

    def verify_location_service(self):
        """Set location service on.
           Verify if location service is available.

        Return:
            True : location service is on.
            False : location service is off.
        """
        utils.set_location_service(self.ad, True)
        out = self.ad.adb.shell("settings get secure "
                                "location_providers_allowed")
        self.ad.log.info("Current Location Provider >> %s" % out)
        if out == "gps,network":
            return True
        return False

    def clear_logd_gnss_qxdm_log(self):
        """Clear /data/misc/logd, /storage/emulated/0/gnssstatus_log and
        /data/vendor/radio/diag_logs/logs from previous test item then reboot.
        """
        self.remount_device()
        self.ad.log.info("Clear Logd, GNSS and QXDM Log from previous test "
                         "item.")
        self.ad.adb.shell("rm -r /data/misc/logd", ignore_status=True)
        self.ad.adb.shell("rm -r /storage/emulated/0/gnssstatus_log",
                          ignore_status=True)
        output_path = os.path.join(DEFAULT_QXDM_LOG_PATH, "logs")
        self.ad.adb.shell("rm -r %s" % output_path, ignore_status=True)
        self.ad.reboot()
        self.ad.unlock_screen(password=None)

    def get_gnss_qxdm_log(self, test_name=""):
        """Get /storage/emulated/0/GnssStatus_log and
        /data/vendor/radio/diag_logs/logs for failed test item.
        """
        log_path_base = getattr(logging, "log_path", "/tmp/logs")
        log_path = os.path.join(log_path_base, "AndroidDevice%s"
                                % self.ad.serial)
        utils.create_dir(log_path)
        gnss_log_path = os.path.join(log_path, test_name, "gnssstatus_log_%s_%s"
                                     % (self.ad.model, self.ad.serial))
        utils.create_dir(gnss_log_path)
        self.ad.log.info("Pull GnssStatus Log to %s" % gnss_log_path)
        self.ad.adb.pull("/storage/emulated/0/gnssstatus_log %s"
                         % gnss_log_path,
                         timeout=self.pull_timeout, ignore_status=True)
        logcat_results = self.ad.search_logcat("Diag_Lib:  creating new file")
        if logcat_results:
            qxdm_log_path = os.path.join(log_path, test_name, "QXDM_%s_%s"
                                         % (self.ad.model, self.ad.serial))
            utils.create_dir(qxdm_log_path)
            output_path = os.path.join(DEFAULT_QXDM_LOG_PATH, "logs")
            self.ad.log.info("Pull QXDM Log %s to %s"
                             % (output_path, qxdm_log_path))
            self.ad.adb.pull("%s %s" % (output_path, qxdm_log_path),
                             timeout=self.pull_timeout, ignore_status=True)
            if self.ad.model == "sailfish" or self.ad.model == "marlin":
                self.ad.adb.pull("/firmware/radio/qdsp6m.qdb %s"
                                 % qxdm_log_path,
                                 timeout=self.pull_timeout, ignore_status=True)
            elif self.ad.model == "walleye":
                self.ad.adb.pull("/firmware/image/qdsp6m.qdb %s"
                                 % qxdm_log_path,
                                 timeout=self.pull_timeout, ignore_status=True)
            else:
                self.ad.adb.pull("/vendor/firmware_mnt/image/qdsp6m.qdb %s"
                                 % qxdm_log_path,
                                 timeout=self.pull_timeout, ignore_status=True)
        else:
            self.ad.log.error("There is no QXDM log on device.")

    def start_youtube_video(self, url=None, retries=0):
        """Start youtube video and verify if audio is in music state.

        Args:
            url: Website for youtube video
            retries: Retry times if audio is not in music state.

        Returns:
            True if youtube video is playing normally.
            False if youtube video is not playing properly.
        """
        for i in range(retries):
            self.ad.log.info("Open an youtube video - attempt %d" % (i+1))
            self.ad.adb.shell("am start -a android.intent.action.VIEW "
                              "-d \"%s\"" % url)
            time.sleep(1)
            out = self.ad.adb.shell("dumpsys activity | grep "
                                    "\"NewVersionAvailableActivity\"")
            if out:
                self.ad.log.info("Skip Youtube New Version Update.")
                self.ad.send_keycode("BACK")
            if tutils.wait_for_state(self.ad.droid.audioIsMusicActive,
                                     True, 15, 1):
                self.ad.log.info("Started a video in youtube, "
                                 "audio is in MUSIC state")
                return True
            self.ad.log.info("Force-Stop youtube and reopen youtube again.")
            self.ad.force_stop_apk("com.google.android.youtube")
            time.sleep(1)
        self.ad.log.error("Started a video in youtube, "
                          "but audio is not in MUSIC state")
        return False

    def mobile_radio_power(self):
        """Turn radio power on or off and check service state."""
        self.ad.adb.shell("service call phone 27")
        time.sleep(5)
        tutils.get_service_state_by_adb(self.ad.log, self.ad)

    def modem_ssr_check(self):
        """Check current modem SSR crash count.

        Returns:
            Times of current modem SSR crash count
        """
        crash_count = 0
        self.ad.send_keycode("HOME")
        self.ad.log.info("Check modem SSR crash count...")
        total_subsys = self.ad.adb.shell("ls /sys/bus/msm_subsys/devices/")
        for i in range(0, len(total_subsys.split())):
            crash_count = int(self.ad.adb.shell("cat /sys/bus/msm_subsys/"
                                                "devices/subsys%d/crash_count"
                                                % i))
            self.ad.log.info("subsys%d crash_count is %d" % (i, crash_count))
            if crash_count != 0:
                return crash_count
        return crash_count

    def xtra_download_logcat_check(self, begin_time):
        """Verify XTRA download success log message in logcat.

        Args:
            begin_time: test begin time

        Returns:
            True: xtra_download if XTRA downloaded and injected successfully
            otherwise return False.
        """
        self.ad.send_keycode("HOME")
        logcat_results = self.ad.search_logcat("XTRA download success. "
                                               "inject data into modem",
                                               begin_time)
        if logcat_results:
            self.ad.log.info("%s" % logcat_results[-1]["log_message"])
            self.ad.log.info("XTRA downloaded and injected successfully.")
            return True
        self.ad.log.error("XTRA downloaded FAIL.")
        return False

    def pull_gtw_gpstool(self):
        """Pull GTW_GPSTool apk from device."""
        out = self.ad.adb.shell("pm path com.android.gpstool")
        result = re.search(r"package:(.*)", out)
        if not result:
            tutils.abort_all_tests(self.ad.log, "Couldn't find GTW GPSTool apk")
        else:
            GTW_GPSTool_apk = result.group(1)
            self.ad.log.info("Get GTW GPSTool apk from %s" % GTW_GPSTool_apk)
            apkdir = "/tmp/GNSS/"
            utils.create_dir(apkdir)
            self.ad.pull_files([GTW_GPSTool_apk], apkdir)

    def reinstall_gtw_gpstool(self):
        """Reinstall GTW_GPSTool apk."""
        self.ad.log.info("Re-install GTW GPSTool")
        self.ad.adb.install("-r -g /tmp/GNSS/base.apk")

    def fastboot_factory_reset(self):
        """Factory reset the device in fastboot mode.
           Pull sl4a apk from device. Terminate all sl4a sessions,
           Reboot the device to bootloader,
           factory reset the device by fastboot.
           Reboot the device. wait for device to complete booting
           Re-install and start an sl4a session.
        """
        status = True
        skip_setup_wizard = True
        out = self.ad.adb.shell("pm path %s" % SL4A_APK_NAME)
        result = re.search(r"package:(.*)", out)
        if not result:
            tutils.abort_all_tests(self.ad.log, "Couldn't find sl4a apk")
        else:
            sl4a_apk = result.group(1)
            self.ad.log.info("Get sl4a apk from %s" % sl4a_apk)
            self.ad.pull_files([sl4a_apk], "/tmp/")
        self.pull_gtw_gpstool()
        tutils.stop_qxdm_logger(self.ad)
        self.ad.stop_services()
        attempts = 3
        for i in range(1, attempts + 1):
            try:
                if self.ad.serial in list_adb_devices():
                    self.ad.log.info("Reboot to bootloader")
                    self.ad.adb.reboot("bootloader", ignore_status=True)
                    time.sleep(10)
                if self.ad.serial in list_fastboot_devices():
                    self.ad.log.info("Factory reset in fastboot")
                    self.ad.fastboot._w(timeout=300, ignore_status=True)
                    time.sleep(30)
                    self.ad.log.info("Reboot in fastboot")
                    self.ad.fastboot.reboot()
                self.ad.wait_for_boot_completion()
                self.ad.root_adb()
                if self.ad.skip_sl4a:
                    break
                if self.ad.is_sl4a_installed():
                    break
                self.ad.log.info("Re-install sl4a")
                self.ad.adb.shell("settings put global package_verifier_enable"
                                  " 0")
                self.ad.adb.install("-r -g /tmp/base.apk")
                self.reinstall_gtw_gpstool()
                time.sleep(10)
                break
            except Exception as e:
                self.ad.log.error(e)
                if i == attempts:
                    tutils.abort_all_tests(self.ad.log, str(e))
                time.sleep(5)
        try:
            self.ad.start_adb_logcat()
        except Exception as e:
            self.ad.log.error(e)
        if skip_setup_wizard:
            self.ad.exit_setup_wizard()
        if self.ad.skip_sl4a:
            return status
        tutils.bring_up_sl4a(self.ad)
        for mask in self.qxdm_masks:
            if not tutils.find_qxdm_log_mask(self.ad, mask):
                continue
            tutils.set_qxdm_logger_command(self.ad, mask)
            break
        return status

    def gtw_gpstool_clear_aiding_data(self):
        """Launch GTW GPSTool and Clear all GNSS aiding data.
           Wait 5 seconds for GTW GPStool to clear all GNSS aiding
           data properly.
        """
        self.ad.log.info("Launch GTW GPSTool and Clear all GNSS aiding data")
        self.ad.adb.shell("am start -S -n com.android.gpstool/.GPSTool --es "
                          "mode clear")
        time.sleep(10)

    def gtw_gpstool_start_gnss(self, state):
        """Start or stop GNSS on GTW_GPSTool.

        Args:
            state: True to start GNSS. False to Stop GNSS.
        """
        if state:
            self.ad.adb.shell("am start -S -n com.android.gpstool/.GPSTool "
                              "--es mode gps")
        if not state:
            self.ad.log.info("Stop GNSS on GTW_GPSTool.")
            self.ad.adb.shell("am broadcast -a "
                              "com.android.gpstool.stop_gps_action")
        time.sleep(3)

    def gtw_gpstool_gnss_process(self, criteria):
        """Launch GTW GPSTool and Clear all GNSS aiding data
           Start GNSS tracking on GTW_GPSTool.

        Args:
            criteria: Criteria for current test item.

        Returns:
            True: First fix TTFF are within criteria.
            False: First fix TTFF exceed criteria.
        """
        retries = 3
        for i in range(retries):
            begin_time = get_current_epoch_time()
            self.gtw_gpstool_clear_aiding_data()
            self.ad.log.info("Start GNSS on GTW_GPSTool - attempt %d" % (i+1))
            self.gtw_gpstool_start_gnss(True)
            for _ in range(10 + criteria):
                logcat_results = self.ad.search_logcat("First fixed",
                                                       begin_time)
                if logcat_results:
                    first_fixed = int(logcat_results[-1]["log_message"]
                                      .split()[-1])
                    self.ad.log.info("GNSS First fixed = %.3f seconds"
                                     % (first_fixed / 1000))
                    if (first_fixed / 1000) <= criteria:
                        return True
                    self.ad.log.error("DUT takes more than %d seconds to get "
                                      "location fixed. Test Abort and Close "
                                      "GPS for next test item." % criteria)
                    self.gtw_gpstool_start_gnss(False)
                    return False
                time.sleep(1)
            self.gtw_gpstool_start_gnss(False)
            if not self.ad.is_adb_logcat_on:
                self.ad.start_adb_logcat()
        self.ad.log.error("Test Abort. DUT can't get location fixed within "
                          "%d attempts." % retries)
        return False

    def gtw_gpstool_start_ttff(self, ttff_mode, iteration):
        """Identify which TTFF mode for different test items.

        Args:
            ttff_mode: TTFF Test mode for current test item.
            iteration: Iteration of TTFF cycles.
        """
        if ttff_mode == "ws":
            self.ad.log.info("Wait 5 minutes to start TTFF Warm Start...")
            time.sleep(300)
        if ttff_mode == "cs":
            self.ad.log.info("Start TTFF Cold Start...")
            time.sleep(3)
        self.ad.adb.shell("am broadcast -a com.android.gpstool.ttff_action "
                          "--es ttff %s --es cycle %d" % (ttff_mode, iteration))

    def gtw_gpstool_ttff_process(self, begin_time):
        """Process and save TTFF results.

        Returns:
            ttff_result: A list of saved TTFF seconds.
        """
        loop = 1
        ttff_result = []
        ttff_log_loop = []
        while True:
            stop_gps_results = self.ad.search_logcat("stop gps test()",
                                                     begin_time)
            if stop_gps_results:
                self.ad.send_keycode("HOME")
                break
            crash_result = self.ad.search_logcat("Force finishing activity "
                                                 "com.android.gpstool/.GPSTool",
                                                 begin_time)
            if crash_result:
                self.ad.log.error("GPSTool crashed. Abort test.")
                break
            logcat_results = self.ad.search_logcat("write TTFF log", begin_time)
            if logcat_results:
                ttff_log = logcat_results[-1]["log_message"].split()
                if not ttff_log_loop:
                    ttff_log_loop.append(ttff_log[8].split(":")[-1])
                elif ttff_log[8].split(":")[-1] == ttff_log_loop[loop-1]:
                    continue
                if ttff_log[11] == "0.0":
                    self.ad.log.error("Iteration %d = Timeout" % loop)
                else:
                    self.ad.log.info("Iteration %d = %s seconds"
                                     % (loop, ttff_log[11]))
                ttff_log_loop.append(ttff_log[8].split(":")[-1])
                ttff_result.append(float(ttff_log[11]))
                loop += 1
            if not self.ad.is_adb_logcat_on:
                self.ad.start_adb_logcat()
        return ttff_result

    def verify_ttff_result(self, ttff_result, ttff_mode, criteria):
        """Verify all TTFF results.

        Args:
            ttff_result: A list of saved TTFF seconds.
            ttff_mode: TTFF Test mode for current test item.
            criteria: Criteria for current test item.

        Returns:
            True: All TTFF results are within criteria.
            False: One or more TTFF results exceed criteria or Timeout.
        """
        self.ad.log.info("%d iterations of TTFF %s tests finished."
                         % (len(ttff_result), ttff_mode))
        self.ad.log.info("%s PASS criteria is %d seconds"
                         % (ttff_mode, criteria))
        if len(ttff_result) == 0:
            self.ad.log.error("GTW_GPSTool didn't process TTFF properly.")
            return False
        elif any(float(ttff_result[i]) == 0.0 for i in range(len(ttff_result))):
            self.ad.log.error("One or more TTFF %s Timeout" % ttff_mode)
            return False
        elif any(float(ttff_result[i]) >= criteria
                 for i in range(len(ttff_result))):
            self.ad.log.error("One or more TTFF %s are over test criteria "
                              "%d seconds" % (ttff_mode, criteria))
            return False
        self.ad.log.info("All TTFF %s are within test criteria %d seconds."
                         % (ttff_mode, criteria))
        return True

    def launch_google_map(self):
        """Launch Google Map via intent"""
        self.ad.log.info("Launch Google Map.")
        self.ad.adb.shell("am start -S -n com.google.android.apps.maps/"
                          "com.google.android.maps.MapsActivity")
        self.ad.send_keycode("BACK")
        self.ad.force_stop_apk("com.google.android.apps.maps")
        self.ad.adb.shell("am start -S -n com.google.android.apps.maps/"
                          "com.google.android.maps.MapsActivity")

    def verify_location_api(self, retries):
        """Verify if GnssLocationProvider API reports location.

        Args:
            retries: Retry time.

        Returns:
            True: GnssLocationProvider API reports location.
            otherwise return False.
        """
        for i in range(retries):
            begin_time = get_current_epoch_time()
            self.ad.log.info("Try to get location report from "
                             "GnssLocationProvider API - attempt %d" % (i+1))
            while get_current_epoch_time() - begin_time <= 30000:
                logcat_results = self.ad.search_logcat("REPORT_LOCATION",
                                                       begin_time)
                if logcat_results:
                    self.ad.log.info("%s" % logcat_results[-1]["log_message"])
                    self.ad.log.info("GnssLocationProvider reports location "
                                     "successfully.")
                    return True
            if not self.ad.is_adb_logcat_on:
                self.ad.start_adb_logcat()
        self.ad.log.error("GnssLocationProvider is unable to report location.")
        return False

    def verify_network_location(self, retries):
        """Verify if NLP reports location after requesting via GPSTool.

        Args:
            retries: Retry time.

        Returns:
            True: NLP reports location.
            otherwise return False.
        """
        for i in range(retries):
            begin_time = get_current_epoch_time()
            time.sleep(1)
            self.ad.log.info("Try to get NLP status - attempt %d" % (i+1))
            self.ad.adb.shell("am start -S -n com.android.gpstool/.GPSTool "
                              "--es mode nlp")
            while get_current_epoch_time() - begin_time <= 25000:
                logcat_results = self.ad.search_logcat("GPSTool : Location",
                                                       begin_time)
                if logcat_results:
                    for logcat_result in logcat_results:
                        if "network" in logcat_result["log_message"]:
                            self.ad.log.info(logcat_result["log_message"])
                            return True
            if not self.ad.is_adb_logcat_on:
                self.ad.start_adb_logcat()
            self.ad.send_keycode("BACK")
        self.ad.log.error("Unable to report network location.")
        return False

    def set_attenuator_gnss_signal(self, atten_value):
        """Set attenuation value for different GNSS signal.

        Args:
            atten_value: attenuation value
        """
        self.ad.log.info("Set attenuation value to \"%d\" for GNSS signal."
                         % atten_value)
        self.attenuators[0].set_atten(atten_value)
        time.sleep(3)
        atten_val_str = self.attenuators[0].get_atten()
        atten_val = int(atten_val_str)
        self.ad.log.info("Current attenuation value is \"%d\"" % atten_val)

    """ Test Cases """

    @test_tracker_info(uuid="ff318483-411c-411a-8b1a-422bd54f4a3f")
    def test_supl_capabilities(self):
        """Verify SUPL capabilities.

        Steps:
            1. Root DUT.
            2. Check SUPL capabilities.

        Expected Results:
            CAPABILITIES=0x37 which supports MSA + MSB.

        Return:
            True if PASS, False if FAIL.
        """
        capabilities_state = str(self.ad.adb.shell("cat vendor/etc/gps.conf | "
                                                   "grep CAPABILITIES"))
        self.ad.log.info("SUPL capabilities - %s" % capabilities_state)
        if capabilities_state == "CAPABILITIES=0x37":
            return True
        return False

    @test_tracker_info(uuid="dcae6979-ddb4-4cad-9d14-fbdd9439cf42")
    def test_sap_valid_modes(self):
        """Verify SAP Valid Modes.

        Steps:
            1. Root DUT.
            2. Check SAP Valid Modes.

        Expected Results:
            SAP=PREMIUM

        Return:
            True if PASS, False if FAIL.
        """
        sap_state = str(self.ad.adb.shell("cat vendor/etc/izat.conf | grep "
                                          "SAP="))
        self.ad.log.info("SAP Valid Modes - %s" % sap_state)
        if sap_state == "SAP=PREMIUM":
            return True
        return False

    @test_tracker_info(uuid="14daaaba-35b4-42d9-8d2c-2a803dd746a6")
    def test_network_location_provider(self):
        """Verify addLocationUpdatesListener API reports Network Location.

        Steps:
            1. GPS and NLP are on.
            2. Launch GTW_GPSTool.
            3. Verify whether test devices could report Network Location.
            4. Repeat Step 2. to Step 3. for 5 times.

        Expected Results:
            Test devices could report Network Location.

        Return:
            True if PASS, False if FAIL.
        """
        test_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        for i in range(1, 6):
            test_result = self.verify_network_location(retries=3)
            test_result_all.append(test_result)
            self.ad.log.info("Iteraion %d => %s" % (i, test_result))
        return all(test_result_all)

    @test_tracker_info(uuid="0919d375-baf2-4fe7-b66b-3f72d386f791")
    def test_gmap_location_report_gps_network(self):
        """Verify GnssLocationProvider API reports location to Google Map
           when GPS and Location Accuracy are on.

        Steps:
            1. GPS and NLP are on.
            2. Launch Google Map.
            3. Verify whether test devices could report location.
            4. Repeat Step 2. to Step 3. for 5 times.

        Expected Results:
            Test devices could report location to Google Map.

        Return:
            True if PASS, False if FAIL.
        """
        test_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        for i in range(1, 6):
            self.launch_google_map()
            test_result = self.verify_location_api(retries=3)
            self.ad.send_keycode("HOME")
            test_result_all.append(test_result)
            self.ad.log.info("Iteraion %d => %s" % (i, test_result))
        return all(test_result_all)

    @test_tracker_info(uuid="513361d2-7d72-41b0-a944-fb259c606b81")
    def test_gmap_location_report_gps(self):
        """Verify GnssLocationProvider API reports location to Google Map
           when GPS is on and Location Accuracy is off.

        Steps:
            1. GPS is on.
            2. Location Accuracy is off.
            3. Launch Google Map.
            4. Verify whether test devices could report location.
            5. Repeat Step 3. to Step 4. for 5 times.

        Expected Results:
            Test devices could report location to Google Map.

        Return:
            True if PASS, False if FAIL.
        """
        test_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        self.ad.adb.shell("settings put secure location_providers_allowed "
                          "-network")
        out = self.ad.adb.shell("settings get secure "
                                "location_providers_allowed")
        self.ad.log.info("Modify current Location Provider to %s" % out)
        for i in range(1, 6):
            self.launch_google_map()
            test_result = self.verify_location_api(retries=3)
            self.ad.send_keycode("HOME")
            test_result_all.append(test_result)
            self.ad.log.info("Iteraion %d => %s" % (i, test_result))
        self.ad.adb.shell("settings put secure location_providers_allowed "
                          "+network")
        out = self.ad.adb.shell("settings get secure "
                                "location_providers_allowed")
        self.ad.log.info("Modify current Location Provider to %s" % out)
        return all(test_result_all)

    @test_tracker_info(uuid="60c0aeec-0c8f-4a96-bc6c-05cba1260e73")
    def test_supl_ongoing_call(self):
        """Verify SUPL functionality during phone call.

        Steps:
            1. Kill XTRA daemon to support SUPL only case.
            2. Initiate call on DUT.
            3. SUPL TTFF Cold Start for 10 iteration.
            4. DUT hang up call.

        Expected Results:
            All SUPL TTFF Cold Start results should be less than
            supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.kill_xtra_daemon()
        tutils.initiate_call(self.ad.log, self.ad, "99117")
        time.sleep(5)
        if tutils.check_call_state_idle_by_adb(self.ad):
            self.ad.log.error("Call is not connected.")
            return False
        if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
            tutils.hangup_call(self.ad.log, self.ad)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        tutils.hangup_call(self.ad.log, self.ad)
        return self.verify_ttff_result(ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.supl_cs_criteria)

    @test_tracker_info(uuid="df605509-328f-43e8-b6d8-00635bf701ef")
    def test_supl_downloading_files(self):
        """Verify SUPL functionality when downloading files.

        Steps:
            1. Kill XTRA daemon to support SUPL only case.
            2. DUT start downloading files by sl4a.
            3. SUPL TTFF Cold Start for 10 iteration.
            4. DUT cancel downloading files.

        Expected Results:
            All SUPL TTFF Cold Start results should be within supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.kill_xtra_daemon()
        download = Process(target=tutils.http_file_download_by_sl4a,
                           args=(self.ad, "https://speed.hetzner.de/10GB.bin",
                                 None, None, True, 3600))
        download.start()
        time.sleep(10)
        if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
            download.terminate()
            time.sleep(3)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        download.terminate()
        time.sleep(3)
        return self.verify_ttff_result(ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.supl_cs_criteria)

    @test_tracker_info(uuid="66b9f9d4-1397-4da7-9e55-8b89b1732017")
    def test_supl_watching_youtube(self):
        """Verify SUPL functionality when watching video on youtube.

        Steps:
            1. Kill XTRA daemon to support SUPL only case.
            2. DUT start watching video on youtube.
            3. SUPL TTFF Cold Start for 10 iteration at the background.
            4. DUT stop watching video on youtube.

        Expected Results:
            All SUPL TTFF Cold Start results should be within supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.kill_xtra_daemon()
        if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        if not self.start_youtube_video("https://www.youtube.com/"
                                        "watch?v=AbdVsi1VjQY", retries=3):
            return False
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        return self.verify_ttff_result(ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.supl_cs_criteria)

    @test_tracker_info(uuid="a748af8b-e1eb-4ec6-bde3-74bcefa1c680")
    def test_supl_modem_ssr(self):
        """Verify SUPL functionality after modem silent reboot.

        Steps:
            1. Trigger modem crash by adb.
            2. Wait 1 minute for modem to recover.
            3. SUPL TTFF Cold Start for 3 iteration.
            4. Repeat Step 1. to Step 3. for 5 times.

        Expected Results:
            All SUPL TTFF Cold Start results should be within supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        supl_ssr_test_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        self.kill_xtra_daemon()
        for times in range(1, 6):
            begin_time = get_current_epoch_time()
            before_modem_ssr = self.modem_ssr_check()
            tutils.trigger_modem_crash(self.ad, timeout=60)
            after_modem_ssr = self.modem_ssr_check()
            if not int(after_modem_ssr) == int(before_modem_ssr) + 1:
                self.ad.log.error("Simulated Modem SSR Failed.")
                return False
            if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
                return False
            self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=3)
            ttff_result = self.gtw_gpstool_ttff_process(begin_time)
            supl_ssr_test_result = \
                self.verify_ttff_result(ttff_result, "Cold Start",
                                        self.supl_cs_criteria)
            self.ad.log.info("SUPL after Modem SSR test %d times -> %s"
                             % (times, supl_ssr_test_result))
            supl_ssr_test_result_all.append(supl_ssr_test_result)
        return all(supl_ssr_test_result_all)

    @test_tracker_info(uuid="01602e65-8ded-4459-8df1-7df70a1bfe8a")
    def test_gnss_airplane_mode_on(self):
        """Verify Standalone GNSS functionality while airplane mode is on.

        Steps:
            1. Turn on airplane mode.
            2. TTFF Cold Start for 10 iteration.
            3. Turn off airplane mode.

        Expected Results:
            All Standalone TTFF Cold Start results should be within
            standalone_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.ad.log.info("Turn airplane mode on")
        utils.force_airplane_mode(self.ad, True)
        if not self.gtw_gpstool_gnss_process(self.standalone_cs_criteria):
            self.ad.log.info("Turn airplane mode off due to test abort")
            utils.force_airplane_mode(self.ad, False)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        self.ad.log.info("Turn airplane mode off")
        utils.force_airplane_mode(self.ad, False)
        return self.verify_ttff_result(ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.standalone_cs_criteria)

    @test_tracker_info(uuid="23731b0d-cb80-4c79-a877-cfe7c2faa447")
    def test_gnss_radio_power_off(self):
        """Verify Standalone GNSS functionality while mobile radio is off.

        Steps:
            1. Turn off mobile radio power.
            2. TTFF Cold Start for 10 iteration.
            3. Turn on mobile radio power.

        Expected Results:
            All Standalone TTFF Cold Start results should be within
            standalone_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.mobile_radio_power()
        if not self.gtw_gpstool_gnss_process(self.standalone_cs_criteria):
            self.mobile_radio_power()
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        self.mobile_radio_power()
        return self.verify_ttff_result(ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.standalone_cs_criteria)

    @test_tracker_info(uuid="085b86a9-0212-4c0f-8ca1-2e467a0a2e6e")
    def test_supl_without_gnss_signal(self):
        """Verify SUPL functionality after no GNSS signal for awhile.

        Steps:
            1. Get location fixed.
            2  Let device do GNSS tracking for 1 minute.
            3. Set attenuation value to 60 to block GNSS signal.
            4. Let DUT stay in no GNSS signal for 5 minutes.
            5. Set attenuation value to 10 to regain GNSS signal.
            6. Try to get location reported again.
            7. Repeat Step 1. to Step 6. for 5 times.

        Expected Results:
            After setting attenuation value to 10 (GPS signal regain),
            DUT could get location fixed again.

        Return:
            True if PASS, False if FAIL.
        """
        supl_no_gnss_signal_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        for times in range(1, 6):
            if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
                return False
            self.ad.log.info("Let device do GNSS tracking for 1 minute.")
            time.sleep(60)
            self.set_attenuator_gnss_signal(self.no_gnss_signal_attenuation)
            self.ad.log.info("Let device stay in no GNSS signal for 5 minutes.")
            time.sleep(300)
            self.set_attenuator_gnss_signal(
                self.default_gnss_signal_attenuation)
            supl_no_gnss_signal = self.verify_location_api(retries=3)
            self.gtw_gpstool_start_gnss(False)
            self.ad.log.info("SUPL without GNSS signal test %d times -> %s"
                             % (times, supl_no_gnss_signal))
            supl_no_gnss_signal_all.append(supl_no_gnss_signal)
        return all(supl_no_gnss_signal_all)

    @test_tracker_info(uuid="3ff2f2fa-42d8-47fa-91de-060816cca9df")
    def test_supl_weak_gnss_signal(self):
        """Verify SUPL TTFF functionality under weak GNSS signal.

        Steps:
            1. Set attenuation value to 27 to set weak GNSS signal.
            2. Kill XTRA daemon to support SUPL only case.
            3. SUPL TTFF Cold Start for 10 iteration.
            4. Set attenuation value to 10 to set default GNSS signal.

        Expected Results:
            All SUPL TTFF Cold Start results should be less than
            weak_signal_supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        self.set_attenuator_gnss_signal(self.weak_gnss_signal_attenuation)
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.kill_xtra_daemon()
        if not self.gtw_gpstool_gnss_process(self.weak_signal_supl_cs_criteria):
            self.set_attenuator_gnss_signal(
                self.default_gnss_signal_attenuation)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        self.set_attenuator_gnss_signal(self.default_gnss_signal_attenuation)
        return self.verify_ttff_result(ttff_result, "Cold Start",
                                       self.weak_signal_supl_cs_criteria)

    @test_tracker_info(uuid="4ad4a371-949a-42e1-b1f4-628c79fa8ddc")
    def test_supl_factory_reset(self):
        """Verify SUPL functionality after factory reset.

        Steps:
            1. Factory reset device.
            2. Kill XTRA daemon to support SUPL only case.
            3. SUPL TTFF Cold Start for 10 iteration.
            4. Repeat Step 1. to Step 3. for 3 times.

        Expected Results:
            All SUPL TTFF Cold Start results should be within supl_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        for times in range(1, 4):
            self.fastboot_factory_reset()
            self.ad.unlock_screen(password=None)
            self._init_device()
            if not self.verify_location_service():
                return False
            begin_time = get_current_epoch_time()
            tutils.start_qxdm_logger(self.ad, begin_time)
            self.kill_xtra_daemon()
            if not self.gtw_gpstool_gnss_process(self.supl_cs_criteria):
                return False
            self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
            ttff_result = self.gtw_gpstool_ttff_process(begin_time)
            if not self.verify_ttff_result(ttff_result,
                                           ttff_mode="Cold Start",
                                           criteria=self.supl_cs_criteria):
                self.ad.log.error("SUPL after Factory Reset test %d times "
                                  "-> FAIL" % times)
                return False
            self.ad.log.info("SUPL after Factory Reset test %d times -> "
                             "PASS" % times)
        return True

    @test_tracker_info(uuid="ea3096cf-4f72-4e91-bfb3-0bcbfe865ab4")
    def test_xtra_ttff_mobile_data(self):
        """Verify XTRA TTFF functionality with mobile data.

        Steps:
            1. Disable SUPL mode.
            2. TTFF Warm Start for 10 iteration.
            3. TTFF Cold Start for 10 iteration.

        Expected Results:
            XTRA TTFF Warm Start results should be within xtra_ws_criteria.
            XTRA TTFF Cold Start results should be within xtra_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        self.disable_supl_mode()
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        if not self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="ws", iteration=10)
        ws_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        if not self.verify_ttff_result(ws_ttff_result,
                                       ttff_mode="Warm Start",
                                       criteria=self.xtra_ws_criteria):
            return False
        begin_time = get_current_epoch_time()
        if not self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        cs_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        return self.verify_ttff_result(cs_ttff_result,
                                       ttff_mode="Cold Start",
                                       criteria=self.xtra_cs_criteria)

    @test_tracker_info(uuid="c91ba740-220e-41de-81e5-43af31f63907")
    def test_xtra_ttff_weak_gnss_signal(self):
        """Verify XTRA TTFF functionality under weak GNSS signal.

        Steps:
            1. Set attenuation value to 27 to set weak GNSS signal.
            2. TTFF Warm Start for 10 iteration.
            3. TTFF Cold Start for 10 iteration.
            4. Set attenuation value to 10 to set default GNSS signal.

        Expected Results:
            XTRA TTFF Warm Start results should be within
            weak_signal_xtra_ws_criteria.
            XTRA TTFF Cold Start results should be within
            weak_signal_xtra_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        self.set_attenuator_gnss_signal(self.weak_gnss_signal_attenuation)
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        if not self.gtw_gpstool_gnss_process(self.weak_signal_xtra_cs_criteria):
            self.set_attenuator_gnss_signal(
                self.default_gnss_signal_attenuation)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="ws", iteration=10)
        ws_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        if not self.verify_ttff_result(ws_ttff_result, "Warm Start",
                                       self.weak_signal_xtra_ws_criteria):
            self.set_attenuator_gnss_signal(
                self.default_gnss_signal_attenuation)
            return False
        begin_time = get_current_epoch_time()
        if not self.gtw_gpstool_gnss_process(self.weak_signal_xtra_cs_criteria):
            self.set_attenuator_gnss_signal(
                self.default_gnss_signal_attenuation)
            return False
        self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
        cs_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
        self.set_attenuator_gnss_signal(self.default_gnss_signal_attenuation)
        return self.verify_ttff_result(cs_ttff_result, "Cold Start",
                                       self.weak_signal_xtra_cs_criteria)

    @test_tracker_info(uuid="beeb3454-bcb2-451e-83fb-26289e89b515")
    def test_xtra_ttff_wifi(self):
        """Verify XTRA TTFF functionality with WiFi.

        Steps:
            1. Disable SUPL mode and turn airplane mode on.
            2. Connect to WiFi.
            3. TTFF Warm Start for 10 iteration.
            4. TTFF Cold Start for 10 iteration.

        Expected Results:
            XTRA TTFF Warm Start results should be within xtra_ws_criteria.
            XTRA TTFF Cold Start results should be within xtra_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        begin_time = get_current_epoch_time()
        tutils.start_qxdm_logger(self.ad, begin_time)
        self.ad.log.info("Turn airplane mode on")
        utils.force_airplane_mode(self.ad, True)
        wutils.wifi_toggle_state(self.ad, True)
        self.connect_to_wifi_network(self.ssid_map
                                     [self.pixel_lab_network[0]["SSID"]])
        if self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
            self.gtw_gpstool_start_ttff(ttff_mode="ws", iteration=10)
            ws_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
            if self.verify_ttff_result(ws_ttff_result, ttff_mode="Warm Start",
                                       criteria=self.xtra_ws_criteria):
                begin_time = get_current_epoch_time()
                if self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
                    self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=10)
                    cs_ttff_result = self.gtw_gpstool_ttff_process(begin_time)
                    self.ad.log.info("Turn airplane mode off")
                    utils.force_airplane_mode(self.ad, False)
                    wutils.wifi_toggle_state(self.ad, False)
                    return self.verify_ttff_result(cs_ttff_result, "Cold Start",
                                                   self.xtra_cs_criteria)
        self.ad.log.info("Turn airplane mode off")
        utils.force_airplane_mode(self.ad, False)
        wutils.wifi_toggle_state(self.ad, False)
        return False

    @test_tracker_info(uuid="1745b8a4-5925-4aa0-809a-1b17e848dc9c")
    def test_xtra_modem_ssr(self):
        """Verify XTRA functionality after modem silent reboot.

        Steps:
            1. Trigger modem crash by adb.
            2. Wait 1 minute for modem to recover.
            3. XTRA TTFF Cold Start for 3 iteration.
            4. Repeat Step1. to Step 3. for 5 times.

        Expected Results:
            All XTRA TTFF Cold Start results should be within xtra_cs_criteria.

        Return:
            True if PASS, False if FAIL.
        """
        xtra_ssr_test_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        for times in range(1, 6):
            begin_time = get_current_epoch_time()
            before_modem_ssr = self.modem_ssr_check()
            tutils.trigger_modem_crash(self.ad, timeout=60)
            after_modem_ssr = self.modem_ssr_check()
            if not int(after_modem_ssr) == int(before_modem_ssr) + 1:
                self.ad.log.error("Simulated Modem SSR Failed.")
                return False
            if not self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
                return False
            self.gtw_gpstool_start_ttff(ttff_mode="cs", iteration=3)
            ttff_result = self.gtw_gpstool_ttff_process(begin_time)
            xtra_ssr_test_result = \
                self.verify_ttff_result(ttff_result, "Cold Start",
                                        self.xtra_cs_criteria)
            self.ad.log.info("XTRA after Modem SSR test %d times -> %s"
                             % (times, xtra_ssr_test_result))
            xtra_ssr_test_result_all.append(xtra_ssr_test_result)
        return all(xtra_ssr_test_result_all)

    @test_tracker_info(uuid="4d6e81e1-3abb-4e03-b732-7b6b497a2258")
    def test_xtra_download_mobile_data(self):
        """Verify XTRA data could be downloaded via mobile data.

        Steps:
            1. Delete all GNSS aiding data.
            2. Get location fixed.
            3. Verify whether XTRA is downloaded and injected.
            4. Repeat Step 1. to Step 3. for 5 times.

        Expected Results:
            XTRA data is properly downloaded and injected via mobile data.

        Return:
            True if PASS, False if FAIL.
        """
        mobile_xtra_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        for i in range(1, 6):
            begin_time = get_current_epoch_time()
            if not self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
                return False
            time.sleep(5)
            self.gtw_gpstool_start_gnss(False)
            mobile_xtra_result = self.xtra_download_logcat_check(begin_time)
            self.ad.log.info("Iteration %d => %s" % (i, mobile_xtra_result))
            mobile_xtra_result_all.append(mobile_xtra_result)
        return all(mobile_xtra_result_all)

    @test_tracker_info(uuid="625ac665-1446-4406-a722-e6a19645222c")
    def test_xtra_download_wifi(self):
        """Verify XTRA data could be downloaded via WiFi.

        Steps:
            1. Connect to WiFi.
            2. Delete all GNSS aiding data.
            3. Get location fixed.
            4. Verify whether XTRA is downloaded and injected.
            5. Repeat Step 2. to Step 4. for 5 times.

        Expected Results:
            XTRA data is properly downloaded and injected via WiFi.

        Return:
            True if PASS, False if FAIL.
        """
        wifi_xtra_result_all = []
        tutils.start_qxdm_logger(self.ad, get_current_epoch_time())
        self.ad.log.info("Turn airplane mode on")
        utils.force_airplane_mode(self.ad, True)
        wutils.wifi_toggle_state(self.ad, True)
        self.connect_to_wifi_network(self.ssid_map
                                     [self.pixel_lab_network[0]["SSID"]])
        for i in range(1, 6):
            begin_time = get_current_epoch_time()
            if not self.gtw_gpstool_gnss_process(self.xtra_cs_criteria):
                self.ad.log.info("Turn airplane mode off")
                utils.force_airplane_mode(self.ad, False)
                wutils.wifi_toggle_state(self.ad, False)
                return False
            time.sleep(5)
            self.gtw_gpstool_start_gnss(False)
            wifi_xtra_result = self.xtra_download_logcat_check(begin_time)
            wifi_xtra_result_all.append(wifi_xtra_result)
            self.ad.log.info("Iteraion %d => %s" % (i, wifi_xtra_result))
        self.ad.log.info("Turn airplane mode off")
        utils.force_airplane_mode(self.ad, False)
        wutils.wifi_toggle_state(self.ad, False)
        return all(wifi_xtra_result_all)
