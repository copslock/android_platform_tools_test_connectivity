#!/usr/bin/env python3
#
# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Script for verifying that we can invoke the SetRegion API of the
RegulatoryRegionService.

"""
from acts.base_test import BaseTestClass
from acts import asserts, signals

class RegulatoryRegionFacadeTest(BaseTestClass):

    def setup_class(self):
        super().setup_class()
        if len(self.fuchsia_devices) < 1:
            raise signals.TestAbortClass("Sorry, please try verifying FuchsiaDevice is in your "
                   "config file and try again.")

    def test_set_region(self):
        result = self.fuchsia_devices[0].regulatory_region_lib.setRegion("JP")
        error = result['error']
        asserts.assert_true(error is None, error)
        return True
