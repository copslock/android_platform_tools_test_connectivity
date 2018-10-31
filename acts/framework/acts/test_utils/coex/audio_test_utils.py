# /usr/bin/env python3
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

import logging
import os

from acts.controllers.utils_lib.ssh import connection
from acts.controllers.utils_lib.ssh import settings
from acts.test_utils.audio_analysis_lib.check_quality import quality_analysis
from acts.test_utils.coex.audio_capture import AudioCapture

bits_per_sample = 32


class SshAudioCapture(AudioCapture):

    def __init__(self, test_params, path):
        super().__init__(test_params, path)
        self.remote_path = path

    def capture_audio(self):
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
            return self.capture_and_store_audio()

    def terminate_and_store_audio_results(self):
        """Terminates audio and stores audio files."""
        if self.audio_params["ssh_config"]:
            self.ssh_session.run("rm *.wav")
        else:
            self.terminate_audio()

    def audio_quality_analysis(self, path):
        """Measures audio quality based on the audio file given as input."""
        dest_file_path = os.path.join(path,
                "recorded_audio_%s.wav" % self.file_counter)
        analysis_path = os.path.join(path,
                "audio_analysis_%s.txt" % self.file_counter)
        self.file_counter += 1
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
