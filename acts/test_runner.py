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

import time
import os, sys, json, traceback, argparse
from android_device import AndroidDevice
from ap.access_point import AP
from test_utils.utils import *

test_paths = [os.path.dirname(os.path.abspath(__file__)) + "/tests"]

class TestRunner():
    TAG = "TestRunner"

    def __init__(self, testbed_config, run_list = None):
        self.controllers = {}
        self.parse_config(testbed_config)
        self.test_classes = TestRunner.find_test_files()
        self.run_list = run_list

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
                      file_list.append((name,fileFullPath))
        return file_list

    def run_test_class(self, test_cls_info):
        # Each entry of test class info follows:
        # (TestClassName, path/to/test/class/file) both are strings
        # will add more info later; the info may be based on testbed config
        m = __import__(test_cls_info[0])
        test_cls = getattr(m, test_cls_info[0])
        test_cls_instance = test_cls(self.controllers)
        test_cls_instance.run()

    def run(self):
        for test_cls_info in self.test_classes:
            if not self.run_list or test_cls_info[0] in self.run_list:
                self.run_test_class(test_cls_info)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-tc', '--testclass', nargs='+', type=str,
                        help="List of test classes to run.If not specified, run all test classes found.")
    args = parser.parse_args()
    t = TestRunner("testbed.config", args.testclass)
    t.run()
    os._exit(0)
