#!/usr/bin/env python
#
#   copyright 2017 - the android open source project
#
#   licensed under the apache license, version 2.0 (the "license");
#   you may not use this file except in compliance with the license.
#   you may obtain a copy of the license at
#
#       http://www.apache.org/licenses/license-2.0
#
#   unless required by applicable law or agreed to in writing, software
#   distributed under the license is distributed on an "as is" basis,
#   without warranties or conditions of any kind, either express or implied.
#   see the license for the specific language governing permissions and
#   limitations under the license.

from StringIO import StringIO
import unittest

import fake
from metrics.usb_metric import Device
from metrics.usb_metric import UsbMetric
from mock import mock


class UsbMetricTest(unittest.TestCase):
    def test_check_usbmon_install_t(self):
        pass

    def test_check_usbmon_install_f(self):
        pass

    def test_check_get_bytes_2(self):
        with mock.patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.stdout = StringIO(
                'x x C Ii:2:003:1 0:8 8 = x x\nx x S Ii:2:004:1 -115:8 8 <')

            self.assertEquals(UsbMetric().get_bytes(0),
                              {'2:003': 8,
                               '2:004': 8})

    def test_check_get_bytes_empty(self):
        with mock.patch('subprocess.Popen') as mock_popen:
            mock_popen.return_value.stdout = StringIO('')
            self.assertEquals(UsbMetric().get_bytes(0), {})

    def test_match_device_id(self):
        mock_lsusb = 'Bus 003 Device 047: ID 18d1:d00d Device 0\nBus 003 Device 001: ID 1d6b:0002 Device 1'
        exp_res = {'3:047': 'Device 0', '3:001': 'Device 1'}
        fake_result = fake.FakeResult(stdout=mock_lsusb)
        fake_shell = fake.MockShellCommand(fake_result=fake_result)
        m = UsbMetric(shell=fake_shell)
        self.assertEquals(m.match_device_id(), exp_res)

    def test_match_device_id_empty(self):
        mock_lsusb = ''
        exp_res = {}
        fake_result = fake.FakeResult(stdout=mock_lsusb)
        fake_shell = fake.MockShellCommand(fake_result=fake_result)
        m = UsbMetric(shell=fake_shell)
        self.assertEquals(m.match_device_id(), exp_res)

    def test_gen_output(self):
        dev_name_dict = {'1:001': 'Device 1', '1:002': 'Device 2'}
        dev_byte_dict = {'1:001': 256, '1:002': 200}

        exp_res = [
            Device('1:002', 200, 'Device 2'),
            Device('1:001', 256, 'Device 1'),
        ]

        act_out = UsbMetric().gen_output(dev_name_dict, dev_byte_dict)
        self.assertListEqual(exp_res, act_out)
