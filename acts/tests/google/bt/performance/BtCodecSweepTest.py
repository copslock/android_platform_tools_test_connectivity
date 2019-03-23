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
"""Run sine wave audio quality test from Android to headset over 5 codecs."""
import time

from acts import asserts
from acts.signals import TestPass
from acts.test_utils.bt.A2dpCodecBaseTest import A2dpCodecBaseTest
from acts.test_utils.bt.loggers.bluetooth_metric_logger import BluetoothMetricLogger

DEFAULT_THDN_THRESHOLD = .1
DEFAULT_ANOMALIES_THRESHOLD = 0


class BtCodecSweepTest(A2dpCodecBaseTest):

    def __init__(self, configs):
        super().__init__(configs)
        self.bt_logger = BluetoothMetricLogger.for_test_case()

    def setup_test(self):
        super().setup_test()
        req_params = ['dut',
                      'phone_music_file_dir',
                      'host_music_file_dir',
                      'music_file_name',
                      'audio_params']
        opt_params = ['RelayDevice', 'codecs']
        self.unpack_userparams(req_params, opt_params)
        for codec in self.user_params.get('codecs', []):
            self.generate_test_case(codec)
        self.log.info('Sleep to ensure connection...')
        time.sleep(30)

    def teardown_test(self):
        # TODO(aidanhb): Modify abstract device classes to make this generic.
        self.bt_device.earstudio_controller.clean_up()

    def analyze(self):
        self.run_thdn_analysis()
        thdn_results = self.metrics['thdn']
        self.run_anomaly_detection()
        anomaly_results = self.metrics['anomalies']
        channnel_results = zip(thdn_results, anomaly_results)
        for ch_no, result in enumerate(channnel_results):
            self.log.info('======CHANNEL %s RESULTS======' % ch_no)
            self.log.info('\tTHD+N: %s%%' % (result[0] * 100))
            self.log.info('\tANOMALIES: %s' % len(result[1]))
            for anom in result[1]:
                self.log.info('\t\tAnomaly from %s to %s of duration %s' % (
                    anom[0], anom[1], anom[1] - anom[0]
                ))

    def generate_test_case(self, codec_config):
        def test_case_fn(inst):
            inst.stream_music_on_codec(**codec_config)
            inst.analyze()
            proto = inst.generate_metrics_proto()
            inst.raise_pass_fail(proto)
        test_case_name = 'test_{}'.format(
            '_'.join([str(codec_config[key]) for key in [
                'codec_type',
                'sample_rate',
                'bits_per_sample',
                'channel_mode',
                'codec_specific_1'
            ] if key in codec_config])
        )
        if hasattr(self, test_case_name):
            self.log.warning('Test case %s already defined. Skipping '
                             'assignment...')
        else:
            bound_test_case = test_case_fn.__get__(self, BtCodecSweepTest)
            setattr(self, test_case_name, bound_test_case)

    def generate_metrics_proto(self):
        """Create BluetoothAudioTestResult protobuf."""
        try:
            anomalies = self.metrics['anomalies']
            # Get number of audio glitches on first channel
            self.metrics['audio_glitches_count'] = len(anomalies[0])
            # Get distortion for channnel one
            thdn = self.metrics['thdn']
            self.metrics['total_harmonic_distortion_plus_noise'] = thdn[0]
            duration = int(self.mic.get_last_record_duration_millis())
            self.metrics['audio_streaming_duration_millis'] = duration
        except IndexError:
            self.log.warning('self.generate_metrics_proto called before self.an'
                             'alyze. Anomaly and THD+N results not populated.')
        proto = self.bt_logger.get_results(self.metrics,
                                           self.__class__.__name__,
                                           self.android)
        return proto

    def raise_pass_fail(self, extras=None):
        """Raise pass or fail test signal based on analysis results."""
        try:
            anomalies_threshold = self.user_params.get(
                'anomalies_threshold', DEFAULT_ANOMALIES_THRESHOLD)
            asserts.assert_true(len(self.metrics['anomalies'][0]) <=
                                anomalies_threshold,
                                'Number of glitches exceeds threshold.',
                                extras=extras)
            thdn_threshold = self.user_params.get('thdn_threshold',
                                                  DEFAULT_THDN_THRESHOLD)
            asserts.assert_true(self.metrics['thdn'][0] <= thdn_threshold,
                                'THD+N exceeds threshold.',
                                extras=extras)
        except IndexError as e:
            self.log.error('self.raise_pass_fail called before self.analyze. '
                           'Anomaly and THD+N results not populated.')
            raise e
        raise TestPass('Test passed.', extras=extras)

    def test_SBC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='SBC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()
        proto = self.generate_metrics_proto()
        self.raise_pass_fail(proto)

    def test_AAC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='AAC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()
        proto = self.generate_metrics_proto()
        self.raise_pass_fail(proto)

    def test_APTX_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='APTX',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()
        proto = self.generate_metrics_proto()
        self.raise_pass_fail(proto)

    def test_APTX_HD_48000_24_STEREO(self):
        self.stream_music_on_codec(codec_type='APTX-HD',
                                   sample_rate=48000,
                                   bits_per_sample=24,
                                   channel_mode='STEREO')
        self.analyze()
        proto = self.generate_metrics_proto()
        self.raise_pass_fail(proto)

    def test_LDAC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='LDAC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()
        proto = self.generate_metrics_proto()
        self.raise_pass_fail(proto)
