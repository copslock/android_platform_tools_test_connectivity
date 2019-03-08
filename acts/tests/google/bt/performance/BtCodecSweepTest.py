import time

from acts.test_utils.bt.A2dpCodecBaseTest import A2dpCodecBaseTest


class BtCodecSweepTest(A2dpCodecBaseTest):

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
        # TODO (aidanhb): Modify abstract device classes to make this generic.
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

    def test_SBC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='SBC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()

    def test_AAC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='AAC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()

    def test_APTX_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='APTX',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()

    def test_APTX_HD_48000_24_STEREO(self):
        self.stream_music_on_codec(codec_type='APTX-HD',
                                   sample_rate=48000,
                                   bits_per_sample=24,
                                   channel_mode='STEREO')
        self.analyze()

    def test_LDAC_44100_16_STEREO(self):
        self.stream_music_on_codec(codec_type='LDAC',
                                   sample_rate=44100,
                                   bits_per_sample=16,
                                   channel_mode='STEREO')
        self.analyze()
