#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

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
import json
import os
import sys
import time
import traceback

from android_device import AndroidDevice
from ap.access_point import AP
from test_utils.utils import *

test_paths = [os.path.dirname(os.path.abspath(__file__)) + "/tests"]
testbed_config_path = "testbed.config"

class TestRunner():
    TAG = "TestRunner"

    def __init__(self, testbed_config, run_list = None):
        self.controllers = {}
        self.parse_config(testbed_config)
        self.test_classes = TestRunner.find_test_files()
        self.run_list = [x for x in run_list if x]

    def parse_config(self, testbed_config):
        """ This is not used because we only need the android device atm,
            which can be auto detected and added. Will need it soon though
        """
        android_devices = AndroidDevice.get_all()
        if android_devices:
            self.controllers["android_devices"] = android_devices
        data = load_config(testbed_config)
        if "AP" in data:
            controllers = []
            for ap in data["AP"]:
                controllers.append(AP(ap['Address'], ap['Port']))
            self.controllers["access_points"] = controllers
        # if "Attenuator" in data:
        #     for ap in data["AP"]
        #         self.aps.append(Attenuator(ap['Address'])

    @staticmethod
    def find_test_files():
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
        # Each entry of test class info follows:
        # (TestClassName, path/to/test/class/file) both are strings
        # will add more info later; the info may be based on testbed config
        m = __import__(test_cls_name)
        test_cls = getattr(m, test_cls_name)
        test_cls_instance = test_cls(self.controllers)
        test_cls_instance.run(test_cases)

    def parse_run_list(self):
        results = {}
        for item in run_list:
            tokens = item.split('.')
            if len(tokens) == 1:
                results[tokens[0]] = None
            elif len(tokens) == 2:
                test_cls_name = tokens[0]
                if test_cls_name in results:
                    results[test_cls_name].append(tokens[1])
                else:
                    results[test_cls_name] = [tokens[1]]
        return results

    def run(self):
        if self.run_list:
            for test_name in self.run_list:
                tokens = test_name.split(':')
                if len(tokens) == 1:
                    # This should be considered a test class name
                    test_cls_name = tokens[0]
                    self.run_test_class(test_cls_name)
                elif len(tokens) == 2:
                    # This should be considered a test class name followed by
                    # a list of test case names.
                    test_cls_name, test_case_names = tokens
                    names = [n.strip() for n in test_case_names.split(',') if n]
                    self.run_test_class(test_cls_name, names)
        else:
            for test_cls_name in self.test_classes:
                self.run_test_class(test_cls_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Specify tests to run. If "
                 "nothing specified, run all test cases found."))
    parser.add_argument('-tb', '--testbed', nargs='+', type=str,
                        help=("Path to a file containing a json object that "
                              "represents the testbed configuration."))
    parser.add_argument('-tf', '--testfile', nargs='+', type=str,
                        help=("Path to a file containing a comma delimited list"
                              " of test classes to run."))
    parser.add_argument('-tc', '--testclass', nargs='+', type=str,
                        help=("List of test classes to run. Ignored if "
                              "testfile is set."))
    parser.add_argument('-r', '--repeat', type=int, help=("Number of times to "
                        "run the specified test cases."))
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
