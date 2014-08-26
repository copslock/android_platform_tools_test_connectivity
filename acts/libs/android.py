# python3.4
# Copyright (C) 2009 Google Inc.
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

"""
JSON RPC interface to android scripting engine.
"""

import os, subprocess
import json
import socket


HOST = os.environ.get('AP_HOST', None)
PORT = os.environ.get('AP_PORT', 9999)

LAUNCH_CMD=("adb {} shell am start -a com.googlecode.android_scripting.action.LAUNCH_SERVER "
        "-n com.googlecode.android_scripting/.activity.ScriptingLayerServiceLauncher "
        "--ei com.googlecode.android_scripting.extra.USE_SERVICE_PORT {}")

class SL4AException(Exception):
    pass

class SL4AAPIError(SL4AException):
    """Raised when remote API reports an error."""

class SL4AProtocolError(SL4AException):
    """Raised when there is some error in exchanging data with server on device."""

class AdbError(Exception):
    """Raised when there is an error in adb operations."""

def IDCounter():
    i = 0
    while True:
        yield i
        i += 1

class Android(object):
    COUNTER = IDCounter()

    def __init__(self, cmd='initiate', uid=-1, port=PORT, addr=HOST):
        self.client = None # prevent close errors on connect failure
        self.uid = None
        conn = socket.create_connection((addr, port))
        self.client = conn.makefile(mode="brw")
        handshake = {'cmd':cmd, 'uid':uid}
        self.client.write(json.dumps(handshake).encode("utf8")+b'\n')
        self.client.flush()
        resp = self.client.readline()
        if not resp:
            raise SL4AProtocolError("No response from handshake.")
        result = json.loads(str(resp, encoding="utf8"))
        if result['status']:
          self.uid = result['uid']
        else:
          self.uid = -1

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None

    def __del__(self):
        self.close()

    def _rpc(self, method, *args):
        apiid = next(Android.COUNTER)
        data = {'id': apiid,
                    'method': method,
                    'params': args}
        request = json.dumps(data)
        self.client.write(request.encode("utf8")+b'\n')
        self.client.flush()
        response = self.client.readline()
        if not response:
            raise SL4AProtocolError("No response from server.")
        result = json.loads(str(response, encoding="utf8"))
        if result['error']:
            raise SL4AAPIError(result['error'])
        if result['id'] != apiid:
            raise SL4AProtocolError("Mismatched API id")
        return result['result']

    def __getattr__(self, name):
        def rpc_call(*args):
            return self._rpc(name, *args)
        return rpc_call

def _extract_device_list(lines):
    results = []
    for line in lines:
        tokens = line.strip().split('\t')
        if len(tokens) == 2 and tokens[1] == 'device':
            results.append(tokens[0])
    return results

def _exe_cmd(cmd):
    proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    if not err:
        return out
    raise AdbError(err)

def list_devices():
    out = _exe_cmd("adb devices")
    clean_out = str(out,'utf-8').strip().split('\n')[1:]
    return _extract_device_list(clean_out)

def start_forwarding(port, localport=PORT, serial=""):
    if serial:
        serial = " -s " + serial
    _exe_cmd("adb {} forward tcp:{} tcp:{}".format(serial, localport, port))

def kill_adb_server(serial=""):
    if serial:
        serial = " -s " + serial
    _exe_cmd("adb {} kill-server".format(serial))

def start_adb_server(serial=""):
    if serial:
        serial = " -s "+serial
    _exe_cmd("adb {} start-server".format(serial))

def start_sl4a(port=8080,serial=""):
    if is_sl4a_running(serial):
        return
    start_adb_server(serial)
    if serial:
        serial = " -s " + serial
    _exe_cmd(LAUNCH_CMD.format(serial,port))

def is_sl4a_running(serial=""):
    if serial:
      serial = " -s " + serial
    out = _exe_cmd("adb {} shell ps | grep com.googlecode.android_scripting".format(serial))
    if len(out)==0:
      return False
    return True

def start_iperf(server_host, serial=""):
    if serial:
      serial = " -s " + serial
    out = _exe_cmd("adb {} shell iperf3 -c {}".format(serial, server_host))
    clean_out = str(out,'utf-8').strip().split('\n')
    return clean_out
