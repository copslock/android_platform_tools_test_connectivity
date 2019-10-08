#!/usr/bin/env python3
#
# Copyright (C) 2019 The Android Open Source Project
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
"""Stream music through connected device from phone across different
attenuations."""

import time
from acts import asserts
from acts.signals import TestPass
from acts.test_utils.bt.A2dpCodecBaseTest import A2dpCodecBaseTest
from acts.test_utils.bt.A2dpCodecBaseTest import HEADSET_CONTROL_SLEEP_TIME
from acts.test_utils.bt import bt_constants
from acts.test_utils.bt.bt_test_utils import set_bluetooth_codec
from acts.test_utils.bt.loggers import bluetooth_metric_logger as log

DEFAULT_THDN_THRESHOLD = 0.9
PHONE_BT_ENABLE_WAITING_TIME = 10


class BtRangeCodecTest(A2dpCodecBaseTest):

    def setup_class(self):
        super().setup_class()
        self.bt_logger = log.BluetoothMetricLogger.for_test_case()
        self.start_time = time.time()
        self.attenuator = self.attenuators[0]
        req_params = [
            'bt_atten_start', 'bt_atten_stop',
            'bt_atten_step', 'codecs',
        ]
        opt_params = ['RelayDevice', 'required_devices', 'audio_params']
        self.unpack_userparams(req_params, opt_params)

        for codec_config in self.codecs:
            self.generate_test_case(codec_config)

    def generate_test_case(self, codec_config):
        def test_case_fn():
            self.stream_music_on_codec_vs_atten(codec_config)

        test_case_name = 'test_streaming_{}'.format('_'.join(
            str(codec_config[key])
            for key in sorted(codec_config.keys(), reverse=True)
        ))
        setattr(self, test_case_name, test_case_fn)

    def setup_test(self):
        self.attenuator.set_atten(0)

        # let phone undiscoverable before headset power cycle
        self.android.droid.bluetoothMakeUndiscoverable()

        # power cycle headset
        self.log.info('power down headset')
        self.bt_device.power_off()
        time.sleep(HEADSET_CONTROL_SLEEP_TIME)
        self.bt_device.power_on()
        self.log.info('headset is powered on')

        # enable phone BT discoverability after headset paging sequence is done
        # to keep phone at master role
        time.sleep(PHONE_BT_ENABLE_WAITING_TIME)
        self.log.info('Make phone BT in connectable mode')
        self.android.droid.bluetoothMakeConnectable()
        super().setup_test()

    def teardown_test(self):
        super().teardown_test()
        self.bt_device.power_off()
        # after the test, reset the attenuation
        self.attenuator.set_atten(0)

    def generate_proto(self, data_points, codec_type, sample_rate,
                       bits_per_sample, channel_mode):
        """Generate a results protobuf.

        Args:
            data_points: list of dicts representing info to go into
              AudioTestDataPoint protobuffer message.
            codec_type: The codec type config to store in the proto.
            sample_rate: The sample rate config to store in the proto.
            bits_per_sample: The bits per sample config to store in the proto.
            channel_mode: The channel mode config to store in the proto.
        Returns:
             dict: Dictionary with key 'proto' mapping to serialized protobuf,
               'proto_ascii' mapping to human readable protobuf info, and 'test'
               mapping to the test class name that generated the results.
        """

        # Populate protobuf
        test_case_proto = self.bt_logger.proto_module.BluetoothAudioTestResult()

        for data_point in data_points:
            audio_data_proto = test_case_proto.data_points.add()
            log.recursive_assign(audio_data_proto, data_point)

        codec_proto = test_case_proto.a2dp_codec_config
        codec_proto.codec_type = bt_constants.codec_types[codec_type]
        codec_proto.sample_rate = int(sample_rate)
        codec_proto.bits_per_sample = int(bits_per_sample)
        codec_proto.channel_mode = bt_constants.channel_modes[channel_mode]

        self.bt_logger.add_config_data_to_proto(test_case_proto,
                                                self.android,
                                                self.bt_device)

        self.bt_logger.add_proto_to_results(test_case_proto,
                                            self.__class__.__name__)

        proto_dict = self.bt_logger.get_proto_dict(self.__class__.__name__,
                                                   test_case_proto)
        del proto_dict["proto_ascii"]
        return proto_dict

    def stream_music_on_codec_vs_atten(self, codec_config):
        attenuation_range = range(self.bt_atten_start,
                                  self.bt_atten_stop + 1,
                                  self.bt_atten_step)

        data_points = []

        codec_set = set_bluetooth_codec(self.android, **codec_config)
        asserts.assert_true(codec_set, 'Codec configuration failed.')

        #loop RSSI with the same codec setting
        for atten in attenuation_range:
            self.attenuator.set_atten(atten)
            self.log.info('atten %d', atten)

            self.play_and_record_audio()
            time_from_start = int((time.time() - self.start_time) * 1000)

            thdns = self.run_thdn_analysis()
            stream_duration = int(self.mic.get_last_record_duration_millis())
            data_point = {
                'timestamp_since_beginning_of_test_millis': time_from_start,
                'audio_streaming_duration_millis': stream_duration,
                'attenuation_db': atten,
                'total_harmonic_distortion_plus_noise_percent': thdns[0] * 100
            }
            data_points.append(data_point)
            self.log.info('attenuation is %d', atten)
            self.log.info('THD+N result is %s', thdns)

            for thdn in thdns:
               if thdn >= self.user_params.get('thdn_threshold',
                                               DEFAULT_THDN_THRESHOLD):
                   self.log.info(
                        'stop increasing attenuation and '
                        'get into next codec test. THD+N=, %s', str(thdn)
                   )
                   proto_dict = self.generate_proto(data_points, **codec_config)
                   raise TestPass(
                         'test run through attenuations before audio is broken.'
                         'Successfully recorded and analyzed audio.',
                         extras=proto_dict)

        proto_dict = self.generate_proto(data_points, **codec_config)
        raise TestPass(
            'test run through all attenuations.'
            'Successfully recorded and analyzed audio.',
            extras=proto_dict)
