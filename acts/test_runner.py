#!/usr/bin/python3.4
#
#   Copyright 2014 - The Android Open Source Project
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

import argparse
import os
import subprocess
import sys

from android_device import AndroidDevice
from ap.access_point import AP
import attenuator.minicircuits.telnet as mctelnet
import logger
from test_utils.utils import create_dir
from test_utils.utils import load_config

test_paths = [os.path.dirname(os.path.abspath(__file__)) + "/tests"]
testbed_config_path = "testbed.config"
adb_logcat_path = "../logs/AdbLogcat/"
adb_logcat_tag = "adb_logcat"

class TestRunner():
    TAG = "TestRunner"

    def __init__(self, testbed_config, run_list=None):
        self.controllers = {}
        self.procs = {}
        self.log = logger.get_test_logger("../logs/TestRunner/",
                                                 self.TAG)
        self.reporter = logger.get_test_reporter("../logs/TestRunner/",
                                                 self.TAG)
        self.parse_config(testbed_config)
        self.test_classes = TestRunner.find_test_files(test_paths)
        self.run_list = [x for x in run_list if x]
        self.num_requested = 0
        self.num_executed = 0
        self.num_passed = 0

    def parse_config(self, testbed_config):
        """ This is not used because we only need the android device atm,
            which can be auto detected and added. Will need it soon though
        """
        android_devices = AndroidDevice.get_all()
        if android_devices:
            self.log.debug(' '.join(("Found", str(len(android_devices)),
                                     "android devices.")))
            self.controllers["android_devices"] = android_devices
        data = None
        try:
            data = load_config(testbed_config)
        except:
            self.log.error("ERROR: Failed to load testbed config.")
        if "AndroidDevice" in data:
            # If user specified devices in testbed config, the specified
            # devices will be in the front of the list.
            user_specified = data["AndroidDevice"]
            former = []
            latter = []
            for ad in android_devices:
                if ad.device_id in user_specified:
                    former.append(ad)
                else:
                    latter.append(ad)
            android_devices = former + latter
            self.controllers["android_devices"] = android_devices
        if "AP" in data:
            aps = []
            for ap in data["AP"]:
                aps.append(AP(ap['Address'], ap['Port']))
            self.controllers["access_points"] = aps
            self.log.debug(' '.join(("Found", str(len(aps)),
                                     "access points.")))
        if "Attenuator" in data:
            attns = []
            for attenuator in data["Attenuator"]:
                attn = mctelnet.AttenuatorInstrument(1)
                attn.open(attenuator['Address'], attenuator['Port'])
                attn.set_atten(0, 0)
                attns.append(attn)
            self.controllers["attenuators"] = attns
            self.log.debug(' '.join(("Found", str(len(attns)),
                                     "access points.")))

    @staticmethod
    def find_test_files(test_paths):
        """Locate python files that match the test naming convention in
        directories specified by test_paths.

        All python files whose name ends with "Test" are considered a test
        file.

        Params:
            test_paths: A list of directory paths where the test files reside.

        Returns:
            A list of python files that match the test file naming convention.
        """
        file_list = []
        for path in test_paths:
            for dirPath, subdirList, fileList in os.walk(path):
                for fname in fileList:
                    name, ext = os.path.splitext(fname)
                    if ext == ".py" and name[-4:] == "Test":
                      fileFullPath = os.path.join(dirPath, fname)
                      sys.path.append(dirPath)
                      file_list.append(name)
        return file_list

    def run_test_class(self, test_cls_name, test_cases=None):
        """Instantiates and executes a test class.

        If the test cases list is not None, all the test cases in the test
        class should be executed.

        Args:
            test_cls_name: Name of the test class to execute.
            test_cases: List of test case names to execute within the class.

        Returns:
            A tuple, with the number of cases passed at index 0, and the total
            number of test cases at index 1.
        """
        m = __import__(test_cls_name)
        test_cls = getattr(m, test_cls_name)
        test_cls_instance = test_cls(self.controllers)
        r,e,p = test_cls_instance.run(test_cases)
        self.num_requested += r
        self.num_executed += e
        self.num_passed += p

    def run(self):
        """Run test classes/cases.

        This is the method that takes a list of test classes/cases and execute
        them accordingly.
        """
        self.start_adb_logcat()
        if self.run_list:
            self.log.debug("Executing run list " + str(self.run_list))
            for test_name in self.run_list:
                tokens = test_name.split(':')
                if len(tokens) == 1:
                    # This should be considered a test class name
                    test_cls_name = tokens[0]
                    self.log.debug("Executing test class {}".format(test_cls_name))
                    self.run_test_class(test_cls_name)
                elif len(tokens) == 2:
                    # This should be considered a test class name followed by
                    # a list of test case names.
                    test_cls_name, test_case_names = tokens
                    ns = [n.strip() for n in test_case_names.split(',') if n]
                    self.log.debug(' '.join(("Executing test cases ", str(ns),
                                             "in test class", test_cls_name)))
                    self.run_test_class(test_cls_name, ns)
        else:
            self.log.debug("No run list provided by user, running everything.")
            for test_cls_name in self.test_classes:
                self.run_test_class(test_cls_name)
        self.reporter.write(''.join(("Executed: ", str(self.num_executed),
                            "\nPassed: ", str(self.num_passed), "\n")))
        self.reporter.close()
        self.stop_adb_logcat()

    def start_adb_logcat(self):
        """Starts adb logcat for each device in separate subprocesses and save
        the logs in files.
        """
        if "android_devices" not in self.controllers:
            return
        devices = self.controllers["android_devices"]
        create_dir(adb_logcat_path)
        file_list = []
        for d in devices:
            serial = d.device_id
            f_name = ''.join((logger.get_log_file_timestamp(), ',',
                d.get_model(), ',', serial, '.log'))
            cmd = ''.join(("adb -s ", serial, " logcat -v threadtime > ",
                adb_logcat_path, f_name))
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            self.procs[serial + adb_logcat_tag] = p
            file_list.append(f_name)
        if file_list:
            self.controllers[adb_logcat_tag] = (adb_logcat_path, file_list)

    def stop_adb_logcat(self):
        """Stops all adb logcat subprocesses.
        """
        for k,p in self.procs.items():
            if k[-len(adb_logcat_tag):] == adb_logcat_tag:
                p.kill()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Specify tests to run. If "
                 "nothing specified, run all test cases found."))
    parser.add_argument('-r', '--repeat', type=int, help=("Number of times to "
                        "run the specified test cases."))
    parser.add_argument('-tb', '--testbed', nargs='+', type=str,
                        help=("Path to a file containing a json object that "
                              "represents the testbed configuration."))
    parser.add_argument('-tf', '--testfile', nargs='+', type=str,
                        help=("Path to a file containing a comma delimited "
                              "list of test classes to run."))
    parser.add_argument('-tc', '--testclass', nargs='+', type=str,
                        help=("List of test classes to run. Ignored if "
                              "testfile is set."))
    args = parser.parse_args()
    test_list = []
    repeat = 1
    if args.testfile:
        for fpath in args.testfile:
            tf = None
            with open(fpath, 'r') as f:
                tf = f.read().replace('\n', ' ')
        test_list += tf.split(' ')
    elif args.testclass:
            test_list = args.testclass
    if args.repeat:
        repeat = args.repeat
    for i in range(repeat):
        t = TestRunner(testbed_config_path, test_list)
        t.run()
    os._exit(0)
