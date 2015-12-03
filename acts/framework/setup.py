#!/usr/bin/python3.4

from setuptools import setup
from setuptools import find_packages

setup(
    name='acts',
    version = '0.9',
    description = 'Android Comms Test Suite',
    license = 'Apache2.0',
    packages = find_packages(),
    include_package_data = False,
    install_requires = [
        'pyserial',
    ],
    scripts = ['acts/bin/act.py','acts/bin/monsoon.py'],
    url = "http://www.android.com/"
)
