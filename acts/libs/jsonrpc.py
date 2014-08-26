#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014- Google, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
JSON-RPC over HTTP. Basic handler using pycurl.
"""
import json
import logging
import time
from urllib import request

class HTTPError(Exception):
    pass

class RemoteError(Exception):
    pass

def JSONCounter():
    i = 0
    while True:
        yield i
        i += 1

class JSONRPCClient:
    COUNTER = JSONCounter()
    headers = {'content-type': 'application/json'}
    def __init__(self, baseurl):
        self._baseurl = baseurl
    def call(self, path, methodname=None, *args):
        try:
            return self._call(path, methodname, *args)
        except:
            # Take five and try again
            time.sleep(5)
            return self._call(path, methodname, *args)

    def _post_json(self, url, payload):
        req = request.Request(url)
        req.add_header('Content-Type', 'application/json')
        resp = request.urlopen(req, data=payload.encode("utf-8"))
        txt = resp.read()
        return resp.code, txt.decode('utf-8')

    def _call(self, path, methodname=None, *args):
        """Perform a POST to baseurl path,
           with method and params packaged in a JSON object as the payload.
        """
        jsonid = next(JSONRPCClient.COUNTER)
        payload = json.dumps({"method": methodname,
                              "params": args,
                              "id": jsonid})
        url = self._baseurl + path
        status_code, text = self._post_json(url, payload)
        if status_code != 200:
            raise HTTPError(text)
        r = json.loads(text)
        if r['error']:
            raise RemoteError(r['error'])
        return r['result']

    def sys(self, *args):
        return self.call("sys", *args)

    def __getattr__(self, name):
        def rpc_call(*args):
            return self.call('uci', name, *args)
        return rpc_call