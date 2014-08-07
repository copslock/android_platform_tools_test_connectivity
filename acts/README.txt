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
python module “requests” http://docs.python-requests.org/en/latest/

Setup:
1. Install the dependencies.
2. add the absolute path to “libs” directory to your $PYTHONPATH. You probably want to add the export statement in your ~/.bash_profile file.

To run the included sample tests in command line:
python3 test_runner.py
