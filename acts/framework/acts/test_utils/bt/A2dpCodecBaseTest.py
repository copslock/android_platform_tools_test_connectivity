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
import functools
import os
import time

from acts import asserts
from acts.test_utils.bt.BluetoothBaseTest import BluetoothBaseTest
from acts.test_utils.bt.bt_test_utils import connect_phone_to_headset
from acts.test_utils.bt.bt_test_utils import set_bluetooth_codec
from acts.test_utils.coex.audio_test_utils import SshAudioCapture

ADB_FILE_EXISTS_CMD = 'test -e %s && echo True'


class A2dpCodecBaseTest(BluetoothBaseTest):
    """Stream music file over desired Bluetooth codec configurations.
    Device under test is Android phone, connected to headset controlled by a
    RelayDevice.

    Config file should have a key "codecs" mapping to an array with >=1 codec
    configs.
        Example codec config: {"codec_type": "SBC",
                               "sample_rate": 44100,
                               "bits_per_sample": 16,
                               "channel_mode": "STEREO"}
    A test method will be generated for each codec config in "codecs".
    """

    def __init__(self, configs):
        super(A2dpCodecBaseTest, self).__init__(configs)
        self.dut = self.android_devices[0]
        self.headset = self.relay_devices[0]
        self.mic = None
        self.audio_params = self.user_params['audio_params']
        if 'input_device' in self.audio_params:
            self.audio_output_path = ''
            self.mic = SshAudioCapture(self.audio_params,
                                       self.audio_output_path)
        self.phone_music_file = os.path.join(
            self.user_params['phone_music_file_dir'],
            self.user_params['music_file_name'])
        self.host_music_file = os.path.join(
            self.user_params['host_music_file_dir'],
            self.user_params['music_file_name'])

    def setup_class(self):
        super().setup_class()
        self.headset.power_on()

    def teardown_class(self):
        super().teardown_class()
        media_tag = self.phone_music_file.split('.')[0]
        self.dut.droid.mediaPlayStop(media_tag)

    def ensure_phone_has_music_file(self):
        """Make sure music file (based on config values) is on the phone.

        Returns:
            bool: True if file is on phone, False if file could not be pushed.
        """
        if not bool(self.dut.adb.shell(ADB_FILE_EXISTS_CMD %
                                       self.phone_music_file)):
            self.dut.adb.push(self.host_music_file, self.phone_music_file)
            self.log.info('Music file successfully pushed to phone.')
        else:
            self.log.info(
                'Music file already on phone. Skipping file transfer.')
        return True

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
            connect_phone_to_headset(self.dut, self.headset, 600),
            'Could not connect to device at address %s'
            % self.headset.mac_address)

        # Ensure audio file exists on phone.
        self.ensure_phone_has_music_file()

        self.log.info('Setting Bluetooth codec to %s...' % codec_type)
        codec_set = set_bluetooth_codec(android_device=self.dut,
                                        codec_type=codec_type,
                                        sample_rate=sample_rate,
                                        bits_per_sample=bits_per_sample,
                                        channel_mode=channel_mode,
                                        codec_specific_1=codec_specific_1)
        asserts.assert_true(codec_set, 'Codec configuration failed.')

        media_tag = self.phone_music_file.split('.')[0]
        playing = self.dut.droid.mediaPlayOpen(
            'file://%s' % self.phone_music_file,
            media_tag,
            True)
        asserts.assert_true(playing,
                            'Failed to play file %s' % self.phone_music_file)

        looping = self.dut.droid.mediaPlaySetLooping(True,
                                                     media_tag)
        if not looping:
            self.log.warning('Could not loop %s' % self.phone_music_file)

        if self.mic is not None:
            self.log.info('Capturing audio through %s' %
                          self.mic.input_device['name'])
            audio_captured = self.mic.capture_audio(self.audio_params['trim'])
            stopped = self.dut.droid.mediaPlayStop(media_tag)
            asserts.assert_true(audio_captured, 'Audio not recorded')
            thdn = self.mic.THDN(**self.audio_params['thdn_params'])
            for ch_no, t in thdn.items():
                asserts.assert_true(
                    (t <= self.audio_params['threshold']),
                    'Total Harmonic Distortion + Noise too high: %.4f%%' %
                    t * 100)
                self.log.info('THD+N percent for channel %s: %.4f%%' %
                              (ch_no, t * 100))
        else:
            time.sleep(self.audio_params['record_duration'])
            stopped = self.dut.droid.mediaPlayStop(media_tag)

        if stopped:
            self.log.info('Finished playing audio.')
        else:
            self.log.warning('Failed to stop audio.')
