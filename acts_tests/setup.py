#!/usr/bin/env python3
#
# Copyright 2017 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import shutil
import subprocess
import sys
from distutils import cmd
from distutils import log

import setuptools
from setuptools.command.install import install

FRAMEWORK_DIR = 'acts_framework'

acts_tests_dir = os.path.abspath(os.path.dirname(__file__))

install_requires = [
    # Future needs to have a newer version that contains urllib.
    'future>=0.16.0',
    # Latest version of mock (4.0.0b) causes a number of compatibility issues
    # with ACTS unit tests (b/148695846, b/148814743)
    'mock==3.0.5',
    'numpy',
    'pyserial',
    'pyyaml>=5.1',
    'protobuf>=3.11.3',
    'requests',
    'scapy',
    'xlsxwriter',
    'mobly>=1.10.0',
]

if sys.version_info < (3, ):
    install_requires.append('enum34')
    install_requires.append('statistics')
    # "futures" is needed for py2 compatibility and it only works in 2.7
    install_requires.append('futures')
    install_requires.append('subprocess32')


class ActsContribInstall(install):
    """Custom installation of the acts_contrib package.

    First installs the required ACTS framework via its own setup.py script,
    before proceeding with the rest of the installation.

    The installation requires the ACTS framework to exist under the
    "acts_framework" directory.
    """
    def run(self):
        acts_framework_dir = os.path.join(acts_tests_dir, FRAMEWORK_DIR)
        if not os.path.isdir(acts_framework_dir):
            logging.error('Cannot install ACTS framework. Framework dir '
                          '"%s" not found' % acts_framework_dir)
            exit(1)
        acts_setup_bin = os.path.join(acts_framework_dir, 'setup.py')
        if not os.path.isfile(acts_setup_bin):
            logging.error('Cannot install ACTS framework. Setup script not '
                          'found.')
            exit(1)
        command = [sys.executable, acts_setup_bin, 'install']
        subprocess.check_call(command, cwd=acts_framework_dir)
        super().run()


class ActsContribInstallDependencies(cmd.Command):
    """Installs only required packages

    Installs all required packages for acts_contrib to work. Rather than using
    the normal install system which creates links with the python egg, pip is
    used to install the packages.
    """

    description = 'Install dependencies needed for acts_contrib packages.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        install_args = [sys.executable, '-m', 'pip', 'install']
        subprocess.check_call(install_args + ['--upgrade', 'pip'])
        required_packages = self.distribution.install_requires

        for package in required_packages:
            self.announce('Installing %s...' % package, log.INFO)
            subprocess.check_call(install_args +
                                  ['-v', '--no-cache-dir', package])

        self.announce('Dependencies installed.')


class ActsContribUninstall(cmd.Command):
    """acts_contrib uninstaller.

    Uninstalls acts_contrib from the current version of python. This will
    attempt to import acts_contrib from any of the python egg locations. If it
    finds an import it will use the modules file location to delete it. This is
    repeated until acts_contrib can no longer be imported and thus is
    uninstalled.
    """

    description = 'Uninstall acts_contrib from the local machine.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def uninstall_acts_contrib_module(self, acts_contrib_module):
        """Uninstalls acts_contrib from a module.

        Args:
            acts_contrib_module: The acts_contrib module to uninstall.
        """
        for acts_contrib_install_dir in acts_contrib_module.__path__:
            self.announce('Deleting acts_contrib from: %s'
                          % acts_contrib_install_dir, log.INFO)
            shutil.rmtree(acts_contrib_install_dir)

    def run(self):
        """Entry point for the uninstaller."""
        # Remove the working directory from the python path. This ensures that
        # Source code is not accidentally targeted.
        our_dir = os.path.abspath(os.path.dirname(__file__))
        if our_dir in sys.path:
            sys.path.remove(our_dir)

        if os.getcwd() in sys.path:
            sys.path.remove(os.getcwd())

        try:
            import acts_contrib as acts_contrib_module
        except ImportError:
            self.announce('acts_contrib is not installed, nothing to uninstall.',
                          level=log.ERROR)
            return

        while acts_contrib_module:
            self.uninstall_acts_contrib_module(acts_contrib_module)
            try:
                del sys.modules['acts_contrib']
                import acts_contrib as acts_contrib_module
            except ImportError:
                acts_contrib_module = None

        self.announce('Finished uninstalling acts_contrib.')


def main():
    os.chdir(acts_tests_dir)
    packages = setuptools.find_packages(include=('acts_contrib*',))
    setuptools.setup(name='acts_contrib',
                     version='0.9',
                     description='Android Comms Test Suite',
                     license='Apache2.0',
                     packages=packages,
                     include_package_data=True,
                     install_requires=install_requires,
                     cmdclass={
                         'install': ActsContribInstall,
                         'install_deps': ActsContribInstallDependencies,
                         'uninstall': ActsContribUninstall
                     },
                     url="http://www.android.com/")


if __name__ == '__main__':
    main()
