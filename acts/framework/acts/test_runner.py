#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

from future import standard_library
standard_library.install_aliases()

import argparse
import functools
import importlib
import inspect
import os
import pkgutil
import sys
from urllib.error import URLError

from acts import logger
from acts.keys import Config
from acts.keys import get_internal_value
from acts.keys import get_module_name
from acts.records import TestResult
from acts.signals import TestAbortAll
from acts.utils import create_dir
from acts.utils import find_files
from acts.utils import load_config
from acts.utils import start_standing_subprocess
from acts.utils import stop_standing_subprocess

adb_logcat_tag = "adb_logcat"

class USERError(Exception):
    """Raised when a problem is caused by user mistake, e.g. wrong command,
    misformatted config, test info, wrong test paths etc.
    """

class TestRunner(object):
    """The class that instantiates test classes, executes test cases, and
    report results.
        Attrubutes:
        self.configs: A dictionary containing the configurations for this test
            run. This is populated during instantiation.
        self.procs: A dictionary keeping track of processes started by this
            test run.
        self.id: A string that is the unique identifier of this test run.
        self.log_path: A string representing the path of the dir under which
            all logs from this test run should be written.
        self.log: The logger object used throughout this test run.
        self.controller_destructors: A dictionary that holds the controller
            distructors. Keys are controllers' names.
        self.test_classes: A dictionary where we can look up the test classes
            by name to instantiate.
        self.run_list: A list of tuples specifying what tests to run.
        self.results: The test result object used to record the results of
            this test run.
        self.running: A boolean signifies whether this test run is ongoing or
            not.
    """
    def __init__(self, test_configs, run_list):
        self.configs = {}
        self.procs = {}
        tb = test_configs[Config.key_testbed.value]
        self.testbed_name = tb[Config.key_testbed_name.value]
        start_time = logger.get_log_file_timestamp()
        self.id = "{}@{}".format(self.testbed_name, start_time)
        # log_path should be set before parsing configs.
        l_path = os.path.join(test_configs[Config.key_log_path.value],
            self.testbed_name, start_time)
        self.log_path = os.path.abspath(l_path)
        self.log, self.log_name = logger.get_test_logger(self.log_path,
                                                         self.id,
                                                         self.testbed_name)
        self.controller_destructors = {}
        self.run_list = run_list
        try:
            # self.parse_config initializes controllers. If anything happens in
            # __init__ after controllers are initialized, controllers should be
            # cleaned up.
            self.parse_config(test_configs)
            t_configs = test_configs[Config.key_test_paths.value]
            self.test_classes = self.import_test_modules(t_configs)
            self.set_test_util_logs()
        except:
            self.clean_up()
            raise
        self.results = TestResult()
        self.running = False

    def import_test_modules(self, test_paths):
        """Imports test classes from test scripts.

        1. Locate all .py files under test paths.
        2. Import the .py files as modules.
        3. Find the module members that are test classes.
        4. Categorize the test classes by name.

        Args:
            test_paths: A list of directory paths where the test files reside.

        Returns:
            A dictionary where keys are test class name strings, values are
            actual test classes that can be instantiated.
        """
        def is_testfile_name(name, ext):
            if ext == ".py":
                if name.endswith("Test") or name.endswith("_test"):
                    return True
            return False
        file_list = find_files(test_paths, is_testfile_name)
        test_classes = {}
        for path, name, _ in file_list:
            sys.path.append(path)
            try:
                module = importlib.import_module(name)
            except:
                for test_cls_name, _ in self.run_list:
                    alt_name = name.replace('_', '').lower()
                    alt_cls_name = test_cls_name.lower()
                    # Only block if a test class on the run list causes an
                    # import error. We need to check against both naming
                    # conventions: AaaBbb and aaa_bbb.
                    if name == test_cls_name or alt_name == alt_cls_name:
                        msg = ("Encountered error importing test class %s, "
                               "abort.") % test_cls_name
                        # This exception is logged here to help with debugging
                        # under py2, because "raise X from Y" syntax is only
                        # supported under py3.
                        self.log.exception(msg)
                        raise USERError(msg)
                continue
            for member_name in dir(module):
                if not member_name.startswith("__"):
                    if member_name.endswith("Test"):
                        test_class = getattr(module, member_name)
                        if inspect.isclass(test_class):
                            test_classes[member_name] = test_class
        return test_classes

    def parse_config(self, test_configs):
        """Parses the test configuration and unpacks objects and parameters
        into a dictionary to be passed to test classes.

        Args:
            test_configs: A json object representing the test configurations.
        """
        data = test_configs[Config.key_testbed.value]
        testbed_configs = data[Config.key_testbed_name.value]
        self.configs[Config.ikey_testbed_name.value] = testbed_configs
        # Unpack controllers
        for ctrl_name in Config.controller_names.value:
            if ctrl_name in data:
                module_name = get_module_name(ctrl_name)
                module = importlib.import_module("acts.controllers.%s" %
                    module_name)
                # Create controller objects.
                create = getattr(module, "create")
                try:
                    objects = create(data[ctrl_name], self.log)
                    controller_var_name = get_internal_value(ctrl_name)
                    self.configs[controller_var_name] = objects
                    self.log.debug("Found %d objects for controller %s" %
                        (len(objects), module_name))
                    # Bind controller objects to their destructors.
                    destroy_func = getattr(module, "destroy")
                    self.controller_destructors[controller_var_name] = destroy_func
                except:
                    msg = ("Failed to initialize objects for controller {}, "
                        "abort!").format(module_name)
                    self.log.error(msg)
                    raise
        test_runner_keys = (Config.key_adb_logcat_param.value,)
        for key in test_runner_keys:
            if key in test_configs:
                setattr(self, key, test_configs[key])
        # Unpack other params.
        self.configs[Config.ikey_logpath.value] = self.log_path
        self.configs[Config.ikey_logger.value] = self.log
        cli_args = test_configs[Config.ikey_cli_args.value]
        self.configs[Config.ikey_cli_args.value] = cli_args
        user_param_pairs = []
        for item in test_configs.items():
            if item[0] not in Config.reserved_keys.value:
                user_param_pairs.append(item)
        self.configs[Config.ikey_user_param.value] = dict(user_param_pairs)

    def set_test_util_logs(self, module=None):
        """Sets the log object to each test util module.

        This recursively include all modules under acts.test_utils and sets the
        main test logger to each module.

        Args:
            module: A module under acts.test_utils.
        """
        # Initial condition of recursion.
        if not module:
            module = importlib.import_module("acts.test_utils")
        # Somehow pkgutil.walk_packages is not working for me.
        # Using iter_modules for now.
        pkg_iter = pkgutil.iter_modules(module.__path__, module.__name__ + '.')
        for _, module_name, ispkg in pkg_iter:
            m = importlib.import_module(module_name)
            if ispkg:
                self.set_test_util_logs(module=m)
            else:
                msg = "Setting logger to test util module %s" % module_name
                self.log.debug(msg)
                setattr(m, "log", self.log)

    def run_test_class(self, test_cls_name, test_cases=None):
        """Instantiates and executes a test class.

        If test_cases is None, the test cases listed by self.tests will be
        executed instead. If self.tests is empty as well, no test case in this
        test class will be executed.

        Args:
            test_cls_name: Name of the test class to execute.
            test_cases: List of test case names to execute within the class.

        Returns:
            A tuple, with the number of cases passed at index 0, and the total
            number of test cases at index 1.
        """
        try:
            test_cls = self.test_classes[test_cls_name]
        except KeyError:
            raise USERError(("Unable to locate class %s in any of the test "
                "paths specified.") % test_cls_name)

        with test_cls(self.configs) as test_cls_instance:
            try:
                cls_result = test_cls_instance.run(test_cases)
                self.results += cls_result
            except TestAbortAll as e:
                self.results += e.results
                raise e

    def run(self):
        if not self.running:
            # Only do these if this is the first iteration.
            self.start_adb_logcat()
            self.running = True
        self.log.debug("Executing run list {}.".format(self.run_list))
        for test_cls_name, test_case_names in self.run_list:
            if not self.running:
                break
            if test_case_names:
                self.log.debug(("Executing test cases {} in test class {}."
                                ).format(test_case_names, test_cls_name))
            else:
                self.log.debug("Executing test class {}".format(
                    test_cls_name))
            try:
                self.run_test_class(test_cls_name, test_case_names)
            except TestAbortAll as e:
                msg = "Abort all subsequent test classes. Reason: %s" % str(e)
                self.log.warning(msg)
                raise

    def stop(self):
        """Releases resources from test run. Should be called right after run()
        finishes.
        """
        if self.running:
            msg = "\nSummary for test run %s: %s\n" % (self.id,
                self.results.summary_str())
            self._write_results_json_str()
            self.log.info(msg.strip())
            self.clean_up()
            logger.kill_test_logger(self.log)
            self.stop_adb_logcat()
            self.running = False

    def clean_up(self):
        for name, destroy in self.controller_destructors.items():
            try:
                self.log.debug("Destroying %s." % name)
                destroy(self.configs[name])
            except:
                self.log.exception("Exception occurred destroying %s." % name)

    def start_adb_logcat(self):
        """Starts adb logcat for each device in separate subprocesses and save
        the logs in files.
        """
        if Config.ikey_android_device.value not in self.configs:
            self.log.debug("No android device available, skipping adb logcat.")
            return
        devices = self.configs[Config.ikey_android_device.value]
        file_list = []
        for d in devices:
            # Disable adb log spam filter.
            d.adb.shell("logpersist.start")
            serial = d.serial
            extra_param = ""
            f_name = "adblog,{},{}.txt".format(d.model, serial)
            if hasattr(self, Config.key_adb_logcat_param.value):
                extra_param = getattr(self, Config.key_adb_logcat_param.value)
            cmd = "adb -s {} logcat -v threadtime {} > {}".format(
                serial, extra_param, os.path.join(self.log_path, f_name))
            p = start_standing_subprocess(cmd)
            self.procs[serial + adb_logcat_tag] = p
            file_list.append(f_name)
        if file_list:
            self.configs[Config.ikey_adb_log_path.value] = self.log_path
            self.configs[Config.ikey_adb_log_files.value] = file_list

    def stop_adb_logcat(self):
        """Stops all adb logcat subprocesses.
        """
        for k, p in self.procs.items():
            if k[-len(adb_logcat_tag):] == adb_logcat_tag:
                stop_standing_subprocess(p)

    def _write_results_json_str(self):
        """Writes out a json file with the test result info for easy parsing.

        TODO(angli): This should be replaced by standard log record mechanism.
        """
        path = os.path.join(self.log_path, "test_run_summary.json")
        with open(path, 'w') as f:
            f.write(self.results.json_str())

if __name__ == "__main__":
    pass
