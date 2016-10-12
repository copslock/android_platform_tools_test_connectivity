#!/usr/bin/env python3.4

from distutils import cmd
from distutils import log
import os
import shutil
import setuptools
from setuptools.command import test
import sys


install_requires = [
    'contextlib2',
    'future',
    # mock-1.0.1 is the last version compatible with setuptools <17.1,
    # which is what comes with Ubuntu 14.04 LTS.
    'mock<=1.0.1',
    'pyserial',
]
if sys.version_info < (3,):
    install_requires.append('enum34')
    # "futures" is needed for py2 compatibility and it only works in 2.7
    install_requires.append('futures')


class PyTest(test.test):
    """Class used to execute unit tests using PyTest. This allows us to execute
    unit tests without having to install the package.
    """

    def finalize_options(self):
        test.test.finalize_options(self)
        self.test_args = ['-x', "tests"]
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


class ActsUninstall(cmd.Command):
    """Acts uninstaller.

    Uninstalls acts from the current version of python. This will attempt to
    import acts from any of the python egg locations. If it finds an import
    it will use the modules file location to delete it. This is repeated until
    acts can no longer be imported and thus is uninstalled.
    """

    description = 'Uninstall acts from the local machine.'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def uninstall_acts_module(self, acts_module):
        """Uninstalls acts from a module.

        Args:
            acts_module: The acts module to uninstall.
        """
        acts_install_dir = os.path.dirname(acts_module.__file__)

        self.announce('Deleting acts from: %s' % acts_install_dir, log.INFO)
        shutil.rmtree(acts_install_dir)

    def run(self):
        """Entry point for the uninstaller."""
        # Remove the working directory from the python path. This ensures that
        # Source code is not accidently tarageted.
        if os.getcwd() in sys.path:
            sys.path.remove(os.getcwd())

        try:
            import acts as acts_module
        except ImportError:
            self.announce('Acts is not installed, nothing to uninstall.',
                          level=log.ERROR)
            return

        while acts_module:
            self.uninstall_acts_module(acts_module)
            try:
                del sys.modules['acts']
                import acts as acts_module
            except ImportError:
                acts_module = None

        self.announce('Finished uninstalling acts.')


setuptools.setup(name='acts',
                 version='0.9',
                 description='Android Comms Test Suite',
                 license='Apache2.0',
                 packages=setuptools.find_packages(),
                 include_package_data=False,
                 tests_require=['pytest'],
                 install_requires=install_requires,
                 scripts=['acts/bin/act.py', 'acts/bin/monsoon.py'],
                 cmdclass={'test': PyTest,
                           'uninstall': ActsUninstall},
                 url="http://www.android.com/")
