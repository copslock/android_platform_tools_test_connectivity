#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the 'License');
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an 'AS IS' BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import tempfile

from acts.test_utils.instrumentation.proto.gen import instrumentation_data_pb2

DEFAULT_INST_LOG_DIR = 'instrument-logs'


def pull_proto(ad, dest_dir, source_path=None):
    """Pull latest instrumentation result proto from device.

    Args:
        ad: AndroidDevice object
        dest_dir: Directory on the host where the proto will be sent
        source_path: Path on the device where the proto is generated. If None,
            pull the latest proto from DEFAULT_INST_PROTO_DIR.

    Returns: Path to the retrieved proto file
    """
    if source_path:
        filename = os.path.basename(source_path)
    else:
        default_full_proto_dir = os.path.join(
            ad.adb.shell('echo $EXTERNAL_STORAGE'), DEFAULT_INST_LOG_DIR)
        filename = ad.adb.shell('ls %s -t | head -n1' % default_full_proto_dir)
        if not filename:
            ad.log.warning('No instrumentation result protos found at default '
                           'location.')
            return ''
        source_path = os.path.join(default_full_proto_dir, filename)
    ad.pull_files(source_path, dest_dir)
    dest_path = os.path.join(dest_dir, filename)
    if not os.path.exists(dest_path):
        ad.log.warning('Failed to pull instrumentation result proto: %s -> %s'
                       % (source_path, dest_path))
        return ''
    return dest_path


def get_session_from_local_file(proto_file):
    """Get a instrumentation_data.Session object from a proto file on the host.

    Args:
        proto_file: Path to the proto file (on host)

    Returns: A instrumentation_data_pb2.Session
    """
    with open(proto_file, 'rb') as f:
        return instrumentation_data_pb2.Session.FromString(f.read())


def get_session_from_device(ad, proto_file=None):
    """Get a instrumentation_data.Session object from a proto file on device.

    Args:
        ad: AndroidDevice object
        proto_file: Path to the proto file (on device). If None, defaults to
            latest proto from DEFAULT_INST_PROTO_DIR.

    Returns: A instrumentation_data_pb2.Session
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        pulled_proto = pull_proto(ad, tmp_dir, proto_file)
        return get_session_from_local_file(pulled_proto)
