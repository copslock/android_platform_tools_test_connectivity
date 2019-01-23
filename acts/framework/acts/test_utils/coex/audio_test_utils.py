#!/usr/bin/env python3
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

import functools
import logging
import os
from soundfile import SoundFile

from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings
from acts.test_utils.audio_analysis_lib import audio_analysis
from acts.test_utils.audio_analysis_lib.check_quality import quality_analysis
from acts.test_utils.coex.audio_capture import AudioCapture
from acts.test_utils.coex.audio_capture import RECORD_FILE_TEMPLATE

ANOMALY_DETECTION_BLOCK_SIZE = audio_analysis.ANOMALY_DETECTION_BLOCK_SIZE
ANOMALY_GROUPING_TOLERANCE = audio_analysis.ANOMALY_GROUPING_TOLERANCE
PATTERN_MATCHING_THRESHOLD = audio_analysis.PATTERN_MATCHING_THRESHOLD
ANALYSIS_FILE_TEMPLATE = "audio_analysis_%s.txt"
bits_per_sample = 32


class SshAudioCapture(AudioCapture):

    def __init__(self, test_params, path):
        super(SshAudioCapture, self).__init__(test_params, path)
        self.remote_path = path

    def capture_audio(self, trim_beginning=0, trim_end=0):
        if self.audio_params["ssh_config"]:
            ssh_settings = settings.from_config(
                self.audio_params["ssh_config"])
            self.ssh_session = connection.SshConnection(ssh_settings)
            self.ssh_session.send_file(self.audio_params["src_path"],
                                       self.audio_params["dest_path"])
            path = self.audio_params["dest_path"]
            test_params = str(self.audio_params).replace("\'", "\"")
            self.cmd = "python3 audio_capture.py -p '{}' -t '{}'".format(
                path, test_params)
            job_result = self.ssh_session.run(self.cmd)
            logging.debug("Job Result {}".format(job_result.stdout))
            result = self.ssh_session.run("ls")
            for res in result.stdout.split():
                if ".wav" in res:
                    self.ssh_session.run("scp *.wav %s@%s:%s" % (
                        self.audio_params["user_name"],
                        self.audio_params["ip_address"],
                        self.remote_path))
            return bool(job_result.stdout)
        else:
            return self.capture_and_store_audio(trim_beginning, trim_end)

    def terminate_and_store_audio_results(self):
        """Terminates audio and stores audio files."""
        if self.audio_params["ssh_config"]:
            self.ssh_session.run("rm *.wav")
        else:
            self.terminate_audio()

    def THDN(self, win_size=None, step_size=None, q=1, fund_freq=None):
        """Calculate THD+N value for most recently recorded file.
        Args:
            win_size: analysis window size (must be less than length of
                signal). Used with step size to analyze signal piece by
                piece. If not specified, entire signal will be analyzed.
            step_size: number of samples to move window per-analysis. If not
                specified, entire signal will be analyzed.
            q: quality factor for the notch filter used to remove fundamental
                frequency from signal to isolate noise.
            fund_freq: the fundamental frequency to remove from the signal.
                If not specified, will be detected using FFT.
        Returns:
            channel_results: dict containing THD+N values for each channel in
                latest recorded file.
        """
        if not (win_size and step_size):
            fn = audio_analysis.THDN
        else:
            fn = functools.partial(audio_analysis.max_THDN,
                                   window_size=win_size,
                                   step_size=step_size)
        latest_file_path = self.record_file_template % self.last_fileno()
        wave_file = SoundFile(latest_file_path)
        signal = wave_file.read()
        channels = wave_file.channels
        sample_rate = wave_file.samplerate
        channel_results = {}
        if channels == 1:
            channel_results[0] = fn(signal=signal, sample_rate=sample_rate,
                                    q=q, fund_freq=fund_freq)
        else:
            for ch_no, channel in enumerate(signal.transpose()):
                channel_results[ch_no] = fn(signal=channel,
                                            sample_rate=sample_rate,
                                            q=q, fund_freq=fund_freq)
        return channel_results

    def detect_anomalies(self, block_size=ANOMALY_DETECTION_BLOCK_SIZE,
                         threshold=PATTERN_MATCHING_THRESHOLD,
                         tolerance=ANOMALY_GROUPING_TOLERANCE):
        """Detect anomalies in most recently recorded file.

        An anomaly is defined as a sample in a recorded sine wave that differs
        by at least the value defined by the threshold parameter from a golden
        generated sine wave of the same amplitude, sample rate, and frequency.

        Args:
            block_size (int): the number of samples to analyze at a time in the
                anomaly detection algorithm.
            threshold (float): the threshold of the correlation index to
                determine if two sample values match.
            tolerance (float): the sample tolerance for anomaly time values
                to be grouped as the same anomaly
        Returns:
            channel_results (dict): dictionary mapping each channel index to a
                list of anomaly (start_time, end_time) tuples.
        """
        latest_file_path = self.record_file_template % self.last_fileno()
        wave_file = SoundFile(latest_file_path)
        signal = wave_file.read()
        channels = wave_file.channels
        sample_rate = wave_file.samplerate
        fundamental_freq = audio_analysis.fundamental_freq(signal, sample_rate)
        channel_results = {}
        if channels == 1:
            channel_results[0] = audio_analysis.get_anomaly_durations(
                signal=signal,
                rate=sample_rate,
                freq=fundamental_freq,
                block_size=block_size,
                threshold=threshold,
                tolerance=tolerance)
        else:
            for ch_no, channel in enumerate(signal.transpose()):
                channel_results[ch_no] = audio_analysis.get_anomaly_durations(
                    signal=channel,
                    rate=sample_rate,
                    freq=fundamental_freq,
                    block_size=block_size,
                    threshold=threshold,
                    tolerance=tolerance)
        return channel_results

    def audio_quality_analysis(self, path):
        """Measures audio quality based on the audio file given as input."""
        dest_file_path = os.path.join(path,
                RECORD_FILE_TEMPLATE % self.last_fileno())
        analysis_path = os.path.join(path,
                ANALYSIS_FILE_TEMPLATE % self.last_fileno())
        try:
            quality_analysis(
                filename=dest_file_path,
                output_file=analysis_path,
                bit_width=bits_per_sample,
                rate=self.audio_params["sample_rate"],
                channel=self.audio_params["channel"],
                spectral_only=False)
        except Exception as err:
            logging.exception("Failed to analyze raw audio: %s" % err)
        return analysis_path
