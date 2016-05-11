#!/usr/bin/python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

import queue

from acts import asserts
from acts import base_test
from acts.test_utils.wifi import wifi_test_utils as wutils

WIFI_NAN_ENABLED = "WifiNanEnabled"
WIFI_NAN_DISABLED = "WifiNanDisabled"
ON_CONNECT_SUCCESS = "WifiNanOnConnectSuccess"
ON_NAN_DOWN = "WifiNanOnNanDown"
ON_MATCH = "WifiNanSessionOnMatch"
ON_MESSAGE_RX = "WifiNanSessionOnMessageReceived"
ON_MESSAGE_TX_FAIL = "WifiNanSessionOnMessageSendFail"
ON_MESSAGE_TX_OK = "WifiNanSessionOnMessageSendSuccess"
ON_RANGING_SUCCESS = "WifiNanRangingListenerOnSuccess"
ON_RANGING_FAILURE = "WifiNanRangingListenerOnFailure"
ON_RANGING_ABORTED = "WifiNanRangingListenerOnAborted"


class WifiNanManagerTest(base_test.BaseTestClass):
    def setup_test(self):
        for ad in self.android_devices:
            asserts.assert_true(
                wutils.wifi_toggle_state(ad, True),
                "Failed enabling Wi-Fi interface")
            nan_usage_enabled = ad.droid.wifiIsNanUsageEnabled()
            if not nan_usage_enabled:
                self.log.info('NAN not enabled. Waiting for %s',
                              WIFI_NAN_ENABLED)
                try:
                    ad.ed.pop_event(WIFI_NAN_ENABLED, 10)
                    self.log.info(WIFI_NAN_ENABLED)
                except queue.Empty:
                    asserts.fail('Timed out while waiting for %s' %
                                 WIFI_NAN_ENABLED)

    def teardown_test(self):
        for ad in self.android_devices:
            ad.droid.wifiNanDisconnect()
            asserts.assert_true(
                wutils.wifi_toggle_state(ad, False),
                "Failed disabling Wi-Fi interface")

    def exec_connect(self, device, config_request, name):
        device.droid.wifiNanConnect(config_request)
        try:
            event = device.ed.pop_event(ON_CONNECT_SUCCESS, 30)
            self.log.info('%s: %s', ON_CONNECT_SUCCESS, event['data'])
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on %s' %
                         ON_CONNECT_SUCCESS, name)
        self.log.debug(event)

    def reliable_tx(self, device, session_id, peer, msg):
        num_tries = 0
        max_num_tries = 10
        events_regex = '%s|%s' % (ON_MESSAGE_TX_FAIL, ON_MESSAGE_TX_OK)
        self.msg_id = self.msg_id + 1

        while True:
            try:
                num_tries += 1
                device.droid.wifiNanSendMessage(session_id, peer, msg,
                                                self.msg_id)
                events = device.ed.pop_events(events_regex, 30)
                for event in events:
                    self.log.info('%s: %s', event['name'], event['data'])
                    if event['data']['messageId'] != self.msg_id:
                        continue
                    if event['name'] == ON_MESSAGE_TX_OK:
                        return True
                    if num_tries == max_num_tries:
                        self.log.info("Max number of retries reached")
                        return False
            except queue.Empty:
                self.log.info('Timed out while waiting for %s', events_regex)
                return False

    def exec_rtt(self, device, session_id, peer_id, rtt_param):
        rtt_param['bssid'] = peer_id
        device.droid.wifiNanStartRanging(0, session_id, [rtt_param])

        events_regex = '%s|%s|%s' % (ON_RANGING_SUCCESS, ON_RANGING_FAILURE,
                                     ON_RANGING_ABORTED)
        try:
            events_pub_range = device.ed.pop_events(events_regex, 30)
            for event in events_pub_range:
                self.log.info('%s: %s', event['name'], event['data'])
        except queue.Empty:
            self.log.info('Timed out while waiting for RTT events %s',
                          events_regex)

    def test_nan_discovery_session(self):
        """Perform NAN configuration, discovery, and message exchange.

        Configuration: 2 devices, one acting as Publisher (P) and the
        other as Subscriber (S)

        Logical steps:
          * P & S connect to NAN
          * P & S wait for NAN connection confirmation
          * P starts publishing
          * S starts subscribing
          * S waits for a match (discovery) notification
          * S sends a message to P, confirming that sent successfully
          * P waits for a message and confirms that received (uncorrupted)
          * P sends a message to S, confirming that sent successfully
          * S waits for a message and confirms that received (uncorrupted)
        """
        # Configure Test
        self.publisher = self.android_devices[0]
        self.subscriber = self.android_devices[1]
        required_params = ("config_request1", "config_request2",
                           "publish_config", "subscribe_config")
        self.unpack_userparams(required_params)
        self.msg_id = 10

        sub2pub_msg = "How are you doing?"
        pub2sub_msg = "Doing ok - thanks!"

        # Start Test
        self.exec_connect(self.publisher, self.config_request1, "publisher")
        self.exec_connect(self.subscriber, self.config_request2, "subscriber")

        pub_id = self.publisher.droid.wifiNanPublish(0, self.publish_config)
        sub_id = self.subscriber.droid.wifiNanSubscribe(0,
                                                        self.subscribe_config)

        try:
            event_sub_match = self.subscriber.ed.pop_event(ON_MATCH, 30)
            self.log.info('%s: %s', ON_MATCH, event_sub_match['data'])
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on Subscriber' %
                         ON_MATCH)
        self.log.debug(event_sub_match)

        asserts.assert_true(
            self.reliable_tx(self.subscriber, sub_id,
                             event_sub_match['data']['peerId'], sub2pub_msg),
            "Failed to transmit from subscriber")

        try:
            event_pub_rx = self.publisher.ed.pop_event(ON_MESSAGE_RX, 10)
            self.log.info('%s: %s', ON_MESSAGE_RX, event_pub_rx['data'])
            asserts.assert_equal(event_pub_rx['data']['messageAsString'],
                                 sub2pub_msg,
                                 "Subscriber -> publisher message corrupted")
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on publisher' %
                         ON_MESSAGE_RX)

        asserts.assert_true(
            self.reliable_tx(self.publisher, pub_id,
                             event_pub_rx['data']['peerId'], pub2sub_msg),
            "Failed to transmit from publisher")

        try:
            event_sub_rx = self.subscriber.ed.pop_event(ON_MESSAGE_RX, 10)
            self.log.info('%s: %s', ON_MESSAGE_RX, event_sub_rx['data'])
            asserts.assert_equal(event_sub_rx['data']['messageAsString'],
                                 pub2sub_msg,
                                 "Publisher -> subscriber message corrupted")
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on subscriber' %
                         ON_MESSAGE_RX)

        self.publisher.droid.wifiNanTerminateSession(pub_id)
        self.subscriber.droid.wifiNanTerminateSession(sub_id)

    def test_nan_rtt(self):
        """Perform NAN configuration, discovery, and RTT.

        Configuration: 2 devices, one acting as Publisher (P) and the
        other as Subscriber (S)

        Logical steps:
          * P & S connect to NAN
          * P & S wait for NAN connection confirmation
          * P starts publishing
          * S starts subscribing
          * S waits for a match (discovery) notification
          * S performs 3 RTT measurements with P
        """
        # Configure Test
        self.publisher = self.android_devices[0]
        self.subscriber = self.android_devices[1]
        required_params = ("config_request1", "config_request2",
                           "publish_config", "subscribe_config", "rtt_24_20",
                           "rtt_50_40", "rtt_50_80")
        self.unpack_userparams(required_params)

        # Start Test
        self.exec_connect(self.publisher, self.config_request1, "publisher")
        self.exec_connect(self.subscriber, self.config_request2, "subscriber")

        pub_id = self.publisher.droid.wifiNanPublish(0, self.publish_config)
        sub_id = self.subscriber.droid.wifiNanSubscribe(0,
                                                        self.subscribe_config)

        try:
            event_sub_match = self.subscriber.ed.pop_event(ON_MATCH, 30)
            self.log.info('%s: %s', ON_MATCH, event_sub_match['data'])
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on Subscriber' %
                         ON_MATCH)
        self.log.debug(event_sub_match)

        self.exec_rtt(self.subscriber, sub_id,
                      event_sub_match['data']['peerId'], self.rtt_24_20)
        self.exec_rtt(self.subscriber, sub_id,
                      event_sub_match['data']['peerId'], self.rtt_50_40)
        self.exec_rtt(self.subscriber, sub_id,
                      event_sub_match['data']['peerId'], self.rtt_50_80)

    def test_disable_wifi_during_connection(self):
        """Validate behavior when Wi-Fi is disabled during an active NAN
        connection. Expected behavior: receive an onNanDown(1002) event.

        Configuration: 1 device - the DUT.

        Logical steps:
          * DUT connect to NAN
          * DUT waits for NAN connection confirmation
          * DUT starts publishing
          * Disable Wi-Fi
          * DUT waits for an onNanDown(1002) event and confirms that received
        """
        # Configure Test
        self.dut = self.android_devices[0]
        required_params = ("config_request1", "publish_config")
        self.unpack_userparams(required_params)

        # Start Test
        self.dut.droid.wifiNanConnect(self.config_request1)

        try:
            event = self.dut.ed.pop_event(ON_CONNECT_SUCCESS, 30)
            self.log.info('%s: %s', ON_CONNECT_SUCCESS, event['data'])
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on dut' %
                         ON_CONNECT_SUCCESS)
        self.log.debug(event)

        pub_id = self.dut.droid.wifiNanPublish(0, self.publish_config)

        asserts.assert_true(
            wutils.wifi_toggle_state(self.dut, False),
            "Failed disabling Wi-Fi interface on dut")

        try:
            event = self.dut.ed.pop_event(WIFI_NAN_DISABLED, 30)
            self.log.info(WIFI_NAN_DISABLED)
        except queue.Empty:
            asserts.fail('Timed out while waiting for %s on dut' %
                         WIFI_NAN_DISABLED)
        self.log.debug(event)
