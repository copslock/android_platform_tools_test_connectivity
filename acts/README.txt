This package includes the Android Comms Testing Suite (ACTS) alpha release

==== test_runner.py ====
The script that loads testbed config and execute test classes.

==== testbed.config ====
File containing the testbed configuration, which is in json.

==== tests ====
Sample test scripts.

==== libs ====
Library files.

Dependencies:
adb
python3.4

Setup:
1. Install the dependencies.
2. Prepend the absolute path to “libs” directory to your $PYTHONPATH. You probably want to add the export statement in your ~/.bash_profile file.

To run the included sample WifiManager tests in command line, connect an android device with proper sl4a installed,
then:
python3 test_runner.py -tc WifiManagerTest

For details of how to use the framework, refer to the quick start guide.