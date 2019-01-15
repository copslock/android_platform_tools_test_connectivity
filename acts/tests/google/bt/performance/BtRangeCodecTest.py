from acts.test_utils.bt.A2dpCodecBaseTest import A2dpCodecBaseTest


# For more intuitive parameter parsing.
#  If we are able to 'step' to end value, include it in the range.
def inclusive_range(start, stop, step):
    for i in range(start, stop, step):
        yield i
    if stop % step == 0:
        yield stop


class BtRangeCodecTest(A2dpCodecBaseTest):

    def __init__(self, configs):
        super().__init__(configs)
        self.attenuator = self.attenuators[0]
        req_params = ["bt_atten_start", "bt_atten_stop", "bt_atten_step",
                      "codecs"]
        opt_params = ["RelayDevice", "required_devices", "audio_params"]
        self.unpack_userparams(req_params, opt_params)
        attenuation_range = inclusive_range(self.bt_atten_start,
                                            self.bt_atten_stop,
                                            self.bt_atten_step)
        for attenuation in attenuation_range:
            for codec_config in self.codecs:
                self.generate_test_case(codec_config, attenuation)

    def generate_test_case(self, codec_config, attenuation):
        def test_case_fn():
            self.attenuator.set_atten(attenuation)
            self.log.info("Setting bt attenuation to %s" % attenuation)
            self.stream_music_on_codec(**codec_config)
        test_case_name = "test_streaming_{}".format(
            "_".join([str(codec_config[key]) for key in sorted(
                      codec_config.keys(), reverse=True)] + [str(attenuation)])
        )
        setattr(self, test_case_name, test_case_fn)
