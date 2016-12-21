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

import os
import re
import sys
import unittest
import uuid

if sys.version_info < (3,):
    import imp

    def load_module(name, path):
        return imp.load_source(name, path)
    import_module = load_module
else:
    import importlib.machinery

    def load_module(name, path):
        return importlib.machinery.SourceFileLoader(name, path).load_module()
    import_module = load_module


PY_FILE_REGEX = re.compile('.+\.py$')

BLACKLIST = ['acts/controllers/native.py',
             'acts/controllers/native_android_device.py']


class ActsImportTestUtilsTest(unittest.TestCase):
    """Test that all acts framework imports work.
    """

    def test_import_acts_successful(self):
        """ Test that importing acts works.
        """
        acts = importlib.import_module('acts')
        self.assertIsNotNone(acts)

    def test_import_framework_successful(self):
        """ Dynamically test all imports from the framework.
        """
        acts = importlib.import_module('acts')
        if hasattr(acts, '__path__') and len(acts.__path__) > 0:
            acts_path = acts.__path__[0]
        else:
            acts_path = os.path.dirname(acts.__file__)

        for root, _, files in os.walk(acts_path):
            for f in files:
                full_path = os.path.join(root, f)
                if any(full_path.endswith(e) for e in BLACKLIST):
                    continue

                path = os.path.relpath(os.path.join(root, f), os.getcwd())

                if PY_FILE_REGEX.match(full_path):
                    with self.subTest(msg='import %s' % path):
                        fake_module_name = str(uuid.uuid4())
                        module = load_module(fake_module_name, path)

                        self.assertIsNotNone(module)


if __name__ == "__main__":
    unittest.main()
