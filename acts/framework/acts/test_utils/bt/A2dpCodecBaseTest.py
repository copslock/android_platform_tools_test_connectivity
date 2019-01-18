#/usr/bin/env python3
#
# Copyright (C) 2018 The Android Open Source Project
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
"""Stream music through connected device from phone test implementation."""
import os

from acts import asserts
from acts.signals import TestPass
from acts.test_utils.abstract_devices.bluetooth_handsfree_abstract_device import BluetoothHandsfreeAbstractDeviceFactory as Factory
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import connect_phone_to_headset
from acts.test_utils.bt.bt_test_utils import set_bluetooth_codec
from acts.test_utils.coex.audio_test_utils import SshAudioCapture

ADB_FILE_EXISTS = 'test -e %s && echo True'


class A2dpCodecBaseTest(BluetoothBaseTest):
    """Stream audio file over desired Bluetooth codec configurations.

    Audio file should be a sine wave. Other audio files will not work for the
    test analysis metrics.

    Device under test is Android phone, connected to headset with a controller
    that can generate a BluetoothHandsfreeAbstractDevice from test_utils.
    abstract_devices.bluetooth_handsfree_abstract_device.
    BuetoothHandsfreeAbstractDeviceFactory.
    """

    def __init__(self, configs):
        super(A2dpCodecBaseTest, self).__init__(configs)
        required_params = ["audio_params", "dut", "codecs"]
        self.unpack_userparams(required_params)

        # Instantiate test devices
        self.android = self.android_devices[0]
        attr, idx = self.dut.split(":")
        dut_controller = getattr(self, attr)[int(idx)]
        self.bt_device = Factory().generate(dut_controller)
        if 'input_device' in self.audio_params:
            self.audio_output_path = ''
            self.mic = SshAudioCapture(self.audio_params,
                                       self.audio_output_path)
            self.log.info('Recording device %s initialized.' %
                          self.mic.input_device['name'])
        else:
            raise KeyError('Config audio_params specify input_device.')
        self.phone_music_file = os.path.join(
            self.user_params['phone_music_file_dir'],
            self.user_params['music_file_name'])
        self.host_music_file = os.path.join(
            self.user_params['host_music_file_dir'],
            self.user_params['music_file_name'])

        # Key test metrics to determine quality of recorded audio file.
        self.metrics = {"anomalies": [],
                        "dut_type": dut_controller.__class__.__name__,
                        "thdn": None}

    def setup_class(self):
        super().setup_class()
        self.bt_device.power_on()

    def teardown_class(self):
        super().teardown_class()
        self.android.droid.mediaPlayStop()

    def ensure_phone_has_music_file(self):
        """Make sure music file (based on config values) is on the phone."""
        if not self.android.adb.shell(ADB_FILE_EXISTS % self.phone_music_file):
            self.android.adb.push(self.host_music_file, self.phone_music_file)
            has_file = self.android.adb.shell(
                    ADB_FILE_EXISTS % self.phone_music_file)
            asserts.assert_true(has_file, 'Audio file not pushed to phone.',
                                extras=self.metrics)
            self.log.info('Music file successfully pushed to phone.')
        else:
            self.log.info(
                'Music file already on phone. Skipping file transfer.')

    @BluetoothBaseTest.bt_test_wrap
    def stream_music_on_codec(self,
                              codec_type,
                              sample_rate,
                              bits_per_sample,
                              channel_mode,
                              codec_specific_1=0):
        """Pair phone and headset, set codec, and stream music file.
        Ensure music actually plays and run audio analysis if desired.

        Args:
            codec_type (str): the desired codec type. For reference, see
                test_utils.bt.bt_constants.codec_types
            sample_rate (int|str): the desired sample rate. For reference, see
                test_utils.bt.bt_constants.sample_rates
            bits_per_sample (int|str): the desired bits per sample. For
                reference, see test_utils.bt.bt_constants.bits_per_samples
            channel_mode (str): the desired channel mode. For reference, see
                test_utils.bt.bt_constants.channel_modes
            codec_specific_1: any codec specific value, such as LDAC quality.
        """

        self.log.info('Pairing and connecting to headset...')
        asserts.assert_true(
            connect_phone_to_headset(self.android, self.bt_device, 600),
            'Could not connect to device at address %s'
            % self.bt_device.mac_address,
            extras=self.metrics)

        # Ensure audio file exists on phone.
        self.ensure_phone_has_music_file()

        self.log.info('Setting Bluetooth codec to %s...' % codec_type)
        codec_set = set_bluetooth_codec(android_device=self.android,
                                        codec_type=codec_type,
                                        sample_rate=sample_rate,
                                        bits_per_sample=bits_per_sample,
                                        channel_mode=channel_mode,
                                        codec_specific_1=codec_specific_1)
        asserts.assert_true(codec_set, 'Codec configuration failed.',
                            extras=self.metrics)

        playing = self.android.droid.mediaPlayOpen(
            'file://%s' % self.phone_music_file,
            'default',
            True)
        asserts.assert_true(playing,
                            'Failed to play file %s' % self.phone_music_file,
                            extras=self.metrics)

        looping = self.android.droid.mediaPlaySetLooping(True)
        if not looping:
            self.log.warning('Could not loop %s' % self.phone_music_file)

        try:
            self.log.info('Capturing audio through %s' %
                          self.mic.input_device['name'])
        except AttributeError as e:
            self.log.error('Mic not initialized correctly. Check your '
                           '"input_device" parameter in config.')
            raise e
        audio_captured = self.mic.capture_audio(self.audio_params['trim'])
        self.android.droid.mediaPlayStop()
        stopped = not self.android.droid.mediaIsPlaying()
        asserts.assert_true(audio_captured, 'Audio not recorded',
                            extras=self.metrics)

        # Calculate Total Harmonic Distortion + Noise
        thdn = self.mic.THDN(**self.audio_params['thdn_params'])
        for ch_no, t in thdn.items():
            self.log.info('THD+N percent for channel %s: %.4f%%' %
                          (ch_no, t * 100))
        self.metrics["thdn"] = thdn

        # Detect Anomalies
        anom = self.mic.detect_anomalies(**self.audio_params["anomaly_params"])
        for ch_no, anomalies in anom.items():
            for anomaly in anomalies:
                start, end = anomaly
                self.log.warning('Anomaly on channel {} at {}:{}. Duration '
                                 '{} sec'.format(ch_no,
                                                 start // 60,
                                                 start % 60,
                                                 end -start))
        else:
            self.log.info('No anomalies detected.')
        self.metrics["anomalies"] = anom

        if stopped:
            self.log.info('Finished playing audio.')
        else:
            self.log.warning('Failed to stop audio.')

        raise TestPass('Successfully recorded and analyzed audio.',
                       extras=self.metrics)
