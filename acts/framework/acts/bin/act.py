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

from builtins import str

import argparse
import multiprocessing
import signal
import sys
import traceback

from acts.keys import Config
from acts.signals import TestAbortAll
from acts.test_runner import TestRunner
from acts.test_runner import USERError
from acts.utils import abs_path
from acts.utils import load_config
from acts.utils import valid_filename_chars


def _validate_test_config(test_config):
    """Validates the raw configuration loaded from the config file.

    Making sure all the required fields exist.
    """
    for k in Config.reserved_keys.value:
        if k not in test_config:
            raise USERError(("Required key {} missing in test "
            "config.").format(k))

def _validate_testbed_name(name):
    """Validates the name of a test bed.

    Since test bed names are used as part of the test run id, it needs to meet
    certain requirements.

    Args:
        name: The test bed's name specified in config file.

    Raises:
        If the name does not meet any criteria, USERError is raised.
    """
    if not name:
        raise USERError("Test bed names can't be empty.")
    if not isinstance(name, str):
        raise USERError("Test bed names have to be string.")
    for l in name:
        if l not in valid_filename_chars:
            raise USERError("Char '%s' is not allowed in test bed names." % l)

def _validate_testbed_configs(testbed_configs):
    """Validates the testbed configurations.

    Args:
        testbed_configs: A list of testbed configuration json objects.

    Raises:
        If any part of the configuration is invalid, USERError is raised.
    """
    seen_names = set()
    # Cross checks testbed configs for resource conflicts.
    for config in testbed_configs:
        # Check for conflicts between multiple concurrent testbed configs.
        # No need to call it if there's only one testbed config.
        name = config[Config.key_testbed_name.value]
        _validate_testbed_name(name)
        # Test bed names should be unique.
        if name in seen_names:
            raise USERError("Duplicate testbed name {} found.".format(name))
        seen_names.add(name)

def _verify_test_class_name(test_cls_name):
    if not test_cls_name.endswith("Test"):
        raise USERError(("Requested test class '%s' does not follow the test "
                         "class naming convention *Test.") % test_cls_name)

def _parse_one_test_specifier(item):
    """Parse one test specifier from command line input.

    This also verifies that the test class name and test case names follow
    ACTS's naming conventions. A test class name has to end with "Test"; a test
    case name has to start with "test".

    Args:
        item: A string that specifies a test class or test cases in one test
            class to run.

    Returns:
        A tuple of a string and a list of strings. The string is the test class
        name, the list of strings is a list of test case names. The list can be
        None.
    """
    tokens = item.split(':')
    if len(tokens) > 2:
        raise USERError("Syntax error in test specifier %s" % item)
    if len(tokens) == 1:
        # This should be considered a test class name
        test_cls_name = tokens[0]
        _verify_test_class_name(test_cls_name)
        return (test_cls_name, None)
    elif len(tokens) == 2:
        # This should be considered a test class name followed by
        # a list of test case names.
        test_cls_name, test_case_names = tokens
        clean_names = []
        _verify_test_class_name(test_cls_name)
        for elem in test_case_names.split(','):
            test_case_name = elem.strip()
            if not test_case_name.startswith("test_"):
                    raise USERError(("Requested test case '%s' in test class "
                                    "'%s' does not follow the test case "
                                    "naming convention test_*.") % (
                                    test_case_name, test_cls_name))
            clean_names.append(test_case_name)
        return (test_cls_name, clean_names)

def parse_test_list(test_list):
    """Parse user provided test list into internal format for test_runner.

    Args:
        test_list: A list of test classes/cases.
    """
    result = []
    for elem in test_list:
        result.append(_parse_one_test_specifier(elem))
    return result

def load_test_config_file(test_config_path, tb_filters=None):
    """Processes the test configuration file provied by user.

    Loads the configuration file into a json object, unpacks each testbed
    config into its own json object, and validate the configuration in the
    process.

    Args:
        test_config_path: Path to the test configuration file.

    Returns:
        A list of test configuration json objects to be passed to TestRunner.
    """
    try:
        configs = load_config(test_config_path)
        if tb_filters:
            tbs = []
            for tb in configs[Config.key_testbed.value]:
                if tb[Config.key_testbed_name.value] in tb_filters:
                    tbs.append(tb)
            if len(tbs) != len(tb_filters):
                print("Expect to find %d test bed configs, found %d." % (
                    len(tb_filters), len(tbs)))
                print("Check if you have the correct test bed names.")
                return None
            configs[Config.key_testbed.value] = tbs
        _validate_test_config(configs)
        _validate_testbed_configs(configs[Config.key_testbed.value])
        k_log_path = Config.key_log_path.value
        configs[k_log_path] = abs_path(configs[k_log_path])
        tps = configs[Config.key_test_paths.value]
    except USERError as e:
        print("Something is wrong in the test configurations.")
        print(str(e))
        return None
    except Exception as e:
        print("Error loading test config {}".format(test_config_path))
        print(traceback.format_exc())
        return None
    # Unpack testbeds into separate json objects.
    beds = configs.pop(Config.key_testbed.value)
    config_jsons = []
    for original_bed_config in beds:
        new_test_config = dict(configs)
        new_test_config[Config.key_testbed.value] = original_bed_config
        # Keys in each test bed config will be copied to a level up to be
        # picked up for user_params. If the key already exists in the upper
        # level, the local one defined in test bed config overwrites the
        # general one.
        new_test_config.update(original_bed_config)
        config_jsons.append(new_test_config)
    return config_jsons

def _run_test(parsed_config, test_identifiers, repeat=1):
    """Instantiate and runs TestRunner.

    This is the function to start separate processes with.

    Args:
        parsed_config: A dict that is a set of configs for one TestRunner.
        test_identifiers: A list of tuples, each identifies what test case to
                          run on what test class.
        repeat: Number of times to iterate the specified tests.
    """
    test_runner = _create_test_runner(parsed_config, test_identifiers)
    ok = True
    try:
        for i in range(repeat):
            test_runner.run()
    except TestAbortAll:
        return
    except:
        print("Exception when executing {}, iteration {}.".format(
            test_runner.testbed_name, i))
        print(traceback.format_exc())
        ok = False
    finally:
        test_runner.stop()
        return ok and test_runner.results.is_all_pass

def _gen_term_signal_handler(test_runners):
    def termination_sig_handler(signal_num, frame):
        for t in test_runners:
            t.stop()
        sys.exit(1)
    return termination_sig_handler

def _create_test_runner(parsed_config, test_identifiers):
    """Instantiates one TestRunner object and register termination signal
    handlers that properly shut down the TestRunner run.

    Args:
        parsed_config: A dict that is a set of configs for one TestRunner.
        test_identifiers: A list of tuples, each identifies what test case to
                          run on what test class.

    Returns:
        A TestRunner object.
    """
    try:
        t = TestRunner(parsed_config, test_identifiers)
    except:
        print("Failed to instantiate test runner, abort.")
        print(traceback.format_exc())
        sys.exit(1)
    # Register handler for termination signals.
    handler = _gen_term_signal_handler([t])
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    return t

def _run_tests_parallel(parsed_configs, test_identifiers, repeat):
    """Executes requested tests in parallel.

    Each test run will be in its own process.

    Args:
        parsed_config: A list of dicts, each is a set of configs for one
                       TestRunner.
        test_identifiers: A list of tuples, each identifies what test case to
                          run on what test class.
        repeat: Number of times to iterate the specified tests.

    Returns:
        True if all test runs executed successfully, False otherwise.
    """
    print("Executing {} concurrent test runs.".format(len(parsed_configs)))
    arg_list = [(c, test_identifiers, repeat) for c in parsed_configs]
    results = []
    with multiprocessing.Pool(processes=len(parsed_configs)) as pool:
        # Can't use starmap for py2 compatibility. One day, one day......
        for args in arg_list:
            results.append(pool.apply_async(_run_test, args))
        pool.close()
        pool.join()
    for r in results:
        if r.get() is False or isinstance(r, Exception):
            return False

def _run_tests_sequential(parsed_configs, test_identifiers, repeat):
    """Executes requested tests sequentially.

    Requested test runs will commence one after another according to the order
    of their corresponding configs.

    Args:
        parsed_config: A list of dicts, each is a set of configs for one
                       TestRunner.
        test_identifiers: A list of tuples, each identifies what test case to
                          run on what test class.
        repeat: Number of times to iterate the specified tests.

    Returns:
        True if all test runs executed successfully, False otherwise.
    """
    ok = True
    for c in parsed_configs:
        ret = _run_test(c, test_identifiers, repeat)
        if ret is False:
            ok = False
    return ok

def _parse_test_file(fpath):
    """Parses a test file that contains test specifiers.

    Args:
        fpath: A string that is the path to the test file to parse.

    Returns:
        A list of strings, each is a test specifier.
    """
    try:
        with open(fpath, 'r') as f:
            tf = []
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if len(tf) and (tf[-1].endswith(':') or tf[-1].endswith(',')):
                    tf[-1] += line
                else:
                    tf.append(line)
            return tf
    except:
        print("Error loading test file.")
        raise

def main(argv):
    parser = argparse.ArgumentParser(description=("Specify tests to run. If "
                 "nothing specified, run all test cases found."))
    parser.add_argument('-c', '--config', nargs=1, type=str, required=True,
        metavar="<PATH>", help="Path to the test configuration file.")
    parser.add_argument('--test_args', nargs='+', type=str,
        metavar="Arg1 Arg2 ...",
        help=("Command-line arguments to be passed to every test case in a "
              "test run. Use with caution."))
    parser.add_argument('-p', '--parallel', action="store_true",
        help=("If set, tests will be executed on all testbeds in parallel. "
              "Otherwise, tests are executed iteratively testbed by testbed."))
    parser.add_argument('-r', '--repeat', type=int,
        metavar="<NUMBER>",
        help="Number of times to run the specified test cases.")
    parser.add_argument('-tb', '--testbed', nargs='+', type=str,
        metavar="[<TEST BED NAME1> <TEST BED NAME2> ...]",
        help="Specify which test beds to run tests on.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-tc', '--testclass', nargs='+', type=str,
        metavar="[TestClass1 TestClass2:test_xxx ...]",
        help="A list of test classes/cases to run.")
    group.add_argument('-tf', '--testfile', nargs=1, type=str,
        metavar="<PATH>",
        help=("Path to a file containing a comma delimited list of test "
              "classes to run."))

    args = parser.parse_args(argv)
    test_list = None
    repeat = 1
    if args.testfile:
        test_list = _parse_test_file(args.testfile[0])
    elif args.testclass:
        test_list = args.testclass
    if args.repeat:
        repeat = args.repeat
    parsed_configs = load_test_config_file(args.config[0], args.testbed)
    if not parsed_configs:
        print("Encountered error when parsing the config file, abort!")
        sys.exit(1)
    for c in parsed_configs:
        c[Config.ikey_cli_args.value] = args.test_args
    # Prepare args for test runs
    test_identifiers = parse_test_list(test_list)
    # Execute test runners.
    if args.parallel and len(parsed_configs) > 1:
        exec_result = _run_tests_parallel(parsed_configs, test_identifiers, repeat)
    else:
        exec_result = _run_tests_sequential(parsed_configs, test_identifiers, repeat)
    if exec_result is False:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv[1:])

