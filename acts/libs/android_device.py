#!/usr/bin/python3.4
#
#   Copyright 2014 - The Android Open Source Project
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

import time

import android
from event_dispatcher import EventDispatcher
from test_utils.utils import exe_cmd

class AndroidDeviceException(Exception):
    pass

class DoesNotExistError(AndroidDeviceException):
    """Raised when something that does not exist is referenced """

def list_devices():
    """List all android devices connected to the computer

    Returns:
      A list of serials representing the attached android devices.
      Empty if there's none.
    """
    out = exe_cmd("adb devices")
    clean_lines = str(out,'utf-8').strip().split('\n')[1:]
    results = []
    for line in clean_lines:
        tokens = line.strip().split('\t')
        if len(tokens) == 2 and tokens[1] == 'device':
            results.append(tokens[0])
    return results

def get_all_instances():
    """Create AndroidDevice instances for all attached android devices.

    Returns:
        A list of AndroidDevice objects each representing an android device
        attached to the computer.
    """
    h_port = 9999
    results = []
    for s in list_devices():
        results.append(AndroidDevice(s, host_port=h_port))
        h_port -= 1
    return results

class AndroidDevice:
    """Class representing an android device """
    def __init__(self, device_id="", host_port=9999, device_port=8080,
        number=None):
        self.device_id = device_id
        self.number = number
        self.h_port = host_port
        self.d_port = device_port
        self._droid_sessions = {}
        self._event_dispatchers = {}
        android.start_forwarding(self.d_port, localport=self.h_port,
            serial=self.device_id)

    def get_model(self):
        """Get the Google Android code name for the device.

        Returns:
            The device's Google code name.
        """
        cmd = 'adb -s {} shell cat /system/build.prop | grep "product.name"'
        out = exe_cmd(cmd.format(self.device_id))
        model = out.decode("utf-8").split('=')[-1].strip().lower().strip()
        if "aosp_" == model[:5]:
            model = model[5:]
        return model

    def get_droid(self, handle_event=True):
        """Create an sl4a connection to the device.

        Return the connection handler 'droid'. By default, another connection
        on the same session is made for EventDispatcher, and the dispatcher is
        returned to the caller as well.
        If sl4a server is not started on the device, try to start it.

        Parameters:
            handle_event: True if this droid session will need to handle
                events.

        Returns:
            droid: Android object used to communicate with sl4a on the android
                device.
            ed: An optional EventDispatcher to organize events for this droid.

        Examples:
            Don't need event handling:
            >>> ad = AndroidDevice()
            >>> droid = ad.get_droid(False)

            Need event handling:
            >>> ad = AndroidDevice()
            >>> droid,EventDispatcher = ad.get_droid()
        """
        android.start_sl4a(serial=self.device_id)
        #TODO(angli) Replace sleep with a proper wait on sl4a's startup.
        time.sleep(2.5)
        droid = self.start_new_session()
        if handle_event:
            ed = self.get_dispatcher(droid)
            return droid, ed
        return droid

    def get_dispatcher(self, droid):
        """Return an EventDispatcher for an sl4a session

        Parameters:
            droid: Session to create EventDispatcher for.

        Returns:
            ed: An EventDispatcher for specified session.
        """
        ed_key = self.device_id + str(droid.uid)
        if ed_key in self._event_dispatchers:
            return self._event_dispatchers[ed_key]
        event_droid = self.add_new_connection_to_session(droid.uid)
        ed = EventDispatcher(event_droid)
        self._event_dispatchers[ed_key] = ed
        return ed

    def start_new_session(self):
        """Start a new session in sl4a.

        Also caches the droid in a dict with its uid being the key.

        Returns:
            An Android object used to communicate with sl4a on the android
                device.

        Raises:
            SL4AException: Something is wrong with sl4a and it returned an
            existing uid to a new session.
        """
        droid = android.Android(port=self.h_port)
        if droid.uid in self._droid_sessions:
            raise android.SL4AException(("SL4A returned an existing uid for a "
                "new session. Abort."))
        self._droid_sessions[droid.uid] = [droid]
        return droid

    def add_new_connection_to_session(self, session_id):
        """Create a new connection to an existing sl4a session.

        Parameters:
            session_id: UID of the sl4a session to add connection to.

        Returns:
            An Android object used to communicate with sl4a on the android
                device.

        Raises:
            DoesNotExistError: Raised if the session it's trying to connect to
            does not exist.
        """
        if session_id not in self._droid_sessions:
            raise DoesNotExistError(' '.join(("Session", str(session_id),
                "does not exist.")))
        droid = android.Android(cmd='continue', uid=session_id,
            port=self.h_port)
        self._droid_sessions[session_id].append(droid)
        return droid

    def terminate_session(self, session_id):
        """Terminate a session in sl4a.

        Send terminate signal to sl4a server; stop dispatcher associated with
        the session. Clear corresponding droids and dispatchers from cache.

        Parameters:
            session_id: UID of the sl4a session to terminate.
        """
        android.Android(cmd='terminate', port=self.h_port, uid=session_id)
        del self._droid_sessions[session_id]
        if session_id in self._event_dispatchers:
            self._event_dispatchers[session_id].stop()
            self._event_dispatchers[session_id].clear_all_events()
            del self._event_dispatchers[session_id]

    def terminate_all_sessions(self):
        """Terminate all sl4a sessions on the AndroidDevice instance.

        Terminate all sessions and clear caches.
        """
        if self._droid_sessions:
            session_ids = list(self._droid_sessions.keys())
            for session_id in session_ids:
                self.terminate_session(session_id)

    def start_iperf(self, server_host):
        """Start iperf client on the device.

        Return status as true if iperf client start successfully.
        And data flow information as results.

        Parameters:
            server_host: host where iperf server is running.

        Returns:
            status: true if iperf client start successfully.
            results: results have data flow information
        """
        results = android.start_iperf(server_host,serial=self.device_id)
        if "error" in results[0]:
            return False, results
        return True, results
