#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2015 - The Android Open Source Project
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

import acts.base_test
import acts.test_utils.wifi.wifi_test_utils as wutils

WifiChannelUS = wutils.WifiChannelUS
WifiEnums = wutils.WifiEnums

SCAN_EVENT_TAG = "WifiScannerScan"

class WifiScanResultEvents():
    """This class stores the setting of a scan, parameters generated
    from starting the scan, and events reported later from the scan
    for validation.

    Attributes:
        scan_setting: Setting used to perform the scan.
        scan_channels: Channels used for scanning.
        events: A list to store the scan result events.
    """

    def __init__(self, scan_setting, scan_channels):
        self.scan_setting = scan_setting
        self.scan_channels = scan_channels
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def check_interval(self, scan_setting, scan_result, scan_result_next):
        # Check if the time gap between two consecutive results is
        # within the range. Right now it is hard coded to be 10% of
        # the interval specified by scan setting. This threshold can
        # be imported from the configuration file in the future if it
        # turns out to be necessary.
        # Timestamp of scan result is in microseconds.
        assert abs((scan_result_next["timestamp"] - scan_result["timestamp"]) - \
                   (self.scan_setting['periodInMs'] * 1000)) < \
               (self.scan_setting['periodInMs'] * 100), \
               "The time interval between {} and {} is out of expected range {}ms". \
               format(scan_result, scan_result_next, self.scan_setting['periodInMs'])

    def check_scan_results(self):
        """Validate the reported scan results against the scan settings.
           Assert if any error detected in the results.

           1. For each scan setting there should be no less than 2 events received.
           2. For batch scan, the number of buffered results in each event should
              be exactly what the scan setting specified.
           3. Each scan result should contain no more BBSIDs than what scan setting
              specified.
           4. The frequency reported by each scan result should comply with its
              scan setting.
           5. The time gap between two consecutive scan results should be
              approximately equal to the scan interval specified by the scan
              setting.
        """
        num_events = len(self.events)

        assert num_events >=2, \
               "Not enough number of scan results events: {}".format(num_events)

        for snumber in range(0, num_events):
            # For batch scan mode, check if the number of buffered results matches the
            # scan setting.
            if self.scan_setting['reportEvents'] == WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL:
                assert len(self.events[snumber]["data"]["Results"]) == \
                       self.scan_setting['maxScansToCache'], \
                       "batch scan, {} Results, expect {}". \
                       format(len(self.events[snumber]["data"]["Results"]), \
                              self.scan_setting['maxScansToCache'])

            # Check if the number of BSSIDs and frequencies are within the range specified
            # by the scan setting
            for result in self.events[snumber]["data"]["Results"]:
                assert len(result["ScanResults"]) <= self.scan_setting['numBssidsPerScan'], \
                       "{} BSSIDs, expected no more than {}". \
                       format(len(result["ScanResults"]), self.scan_setting['numBssidsPerScan'])

                for scan_result in result["ScanResults"]:
                    assert scan_result["frequency"] in self.scan_channels, \
                           "The frequency of result event {} not in scan channels {}". \
                           format(self.events[snumber], self.scan_channels)

            # Check if the time gap between two consecutive results is
            # within the range.

            # Check the results within each event of batch scan
            if self.scan_setting['reportEvents'] == WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL:
                for rnumber in range(1, len(self.events[snumber]["data"]["Results"])):
                    self.check_interval(self.scan_setting,
                        self.events[snumber]["data"]["Results"][rnumber-1]["ScanResults"][0],
                        self.events[snumber]["data"]["Results"][rnumber]["ScanResults"][0])

            # Check the time gap between the first result of an event and
            # the last result of its previous event

            # Skip the very first event.
            if snumber >= 1:
                self.check_interval(self.scan_setting,
                    self.events[snumber-1]["data"]["Results"][-1]["ScanResults"][0],
                    self.events[snumber]["data"]["Results"][0]["ScanResults"][0])

            # Add more validations here in the future.


class WifiScannerMultiScanTest(acts.base_test.BaseTestClass):
    """This class is the WiFi Scanner Multi-Scan Test suite.
    It collects a number of test cases, sets up and executes
    the tests, and validates the scan results.

    Attributes:
        tests: A collection of tests to excute.
        leeway: Scan interval drift time (in seconds).
        stime_channels: Dwell time plus 2ms.
        dut: Android device(s).
        wifi_chs: WiFi channels according to the device model.
        max_bugreports: Max number of bug reports allowed.
    """

    def __init__(self, controllers):
        acts.base_test.BaseTestClass.__init__(self, controllers)
        # A list of all test cases to be executed in this class.
        self.tests = ("test_wifi_two_scans_at_same_interval",
                      "test_wifi_two_scans_at_different_interval",
                      "test_wifi_scans_24GHz_and_both",
                      "test_wifi_scans_5GHz_and_both",
                      "test_wifi_scans_24GHz_5GHz_and_both",
                      "test_wifi_scans_batch_and_24GHz",
                      "test_wifi_scans_batch_and_5GHz",
                      "test_wifi_scans_24GHz_5GHz_full_result",)
        self.leeway = 5 # seconds, for event wait time computation
        self.stime_channel = 47 #dwell time plus 2ms

    def setup_class(self):
        self.dut = self.android_devices[0]
        wutils.wifi_test_device_init(self.dut)
        self.assert_true(self.dut.droid.wifiIsScannerSupported(),
            "Device %s doesn't support WifiScanner, abort." % self.dut.model)

        """ Setup the required dependencies and fetch the user params from
        config file.
        """
        req_params = ("bssid_2g", "bssid_5g", "bssid_dfs", "max_bugreports")
        self.wifi_chs = WifiChannelUS(self.dut.model)
        self.unpack_userparams(req_params)

    def on_fail(self, test_name, begin_time):
        if self.max_bugreports > 0:
            self.take_bug_reports(test_name, begin_time, self.android_devices)
            self.max_bugreports -= 1

    """ Helper Functions Begin """
    def start_scan(self, scan_setting):
        data = wutils.start_wifi_background_scan(self.dut, scan_setting)
        idx = data["Index"]
        # Calculate event wait time from scan setting plus leeway
        scan_time, scan_channels = wutils.get_scan_time_and_channels(self.wifi_chs,
                                                              scan_setting,
                                                              self.stime_channel)
        if scan_setting['reportEvents'] == WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL:
            scan_time += scan_setting['maxScansToCache'] * scan_setting['periodInMs']
        else:
            scan_time += scan_setting['periodInMs']

        wait_time = scan_time/1000 + self.leeway
        return idx, wait_time, scan_channels

    def validate_scan_results(self, scan_results_dict):
        # Sanity check to make sure the dict is not empty
        self.assert_true(scan_results_dict,
                         "Scan result dict is empty.")

        for key, scan_results in scan_results_dict.items():
            # Validate the results received for each scan setting
            scan_results.check_scan_results()

    def scan_and_validate_results(self, scan_settings):
        """Perform WifiScanner scans and check the scan results

        Procedures:
          * Start scans for each caller specified setting
          * Wait for at least two results for each scan
          * Check the results received for each scan
        """
        # Awlays get a clean start
        self.ed.clear_all_events()

        # Start scanning with the caller specified settings and
        # compute parameters for receiving events
        idx_list = []
        wait_time_list = []
        scan_results_dict = {}

        for scan_setting in scan_settings:
            self.log.debug("Scan setting: band {}, interval {}, reportEvents {},"
                           "numBssidsPerScan {}".format(scan_setting["band"],
                                                        scan_setting["periodInMs"],
                                                        scan_setting["reportEvents"],
                                                        scan_setting["numBssidsPerScan"]))
            idx, wait_time, scan_chan = self.start_scan(scan_setting)
            self.log.debug("Scan started for band {}: idx {}, wait_time {} s, scan_channels {}".
                           format(scan_setting["band"], idx, wait_time, scan_chan))
            idx_list.append(idx)
            wait_time_list.append(wait_time)
            if scan_setting['reportEvents'] == WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL:
                scan_results_dict_key = "{}{}onFullResults".format(SCAN_EVENT_TAG, idx)
            else:
                scan_results_dict_key = "{}{}onResults".format(SCAN_EVENT_TAG, idx)
            scan_results_dict_val = WifiScanResultEvents(scan_setting,
                                                         scan_chan)
            scan_results_dict[scan_results_dict_key] = scan_results_dict_val

        # Wait and receive the scan result events

        # Compute the event wait time
        event_wait_time = min(wait_time_list)

        # Compute the minimum number of wait loops needed. This is to
        # guarantee that even the scan which requires the most wait time
        # will receive at least two results.
        max_wait_time = max(wait_time_list)
        event_loop_count = int(max_wait_time * 2 / event_wait_time) + 1
        self.log.debug("Event wait time {} seconds, loop count {}".
                       format(event_wait_time, event_loop_count))

        try:
            # Wait for scan results on all the caller specified bands
            event_name = SCAN_EVENT_TAG
            for snumber in range(0, event_loop_count):
                self.log.debug("Waiting for events: {} for up to {} seconds".
                               format(event_name, event_wait_time))
                events = self.ed.pop_events(event_name, event_wait_time)
                for event in events:
                    self.log.debug("Event received: {}".format(event))
                    # Event name is the key to the scan results dictionary
                    scan_results_per_setting = scan_results_dict.get(event["name"])

                    self.assert_true(scan_results_per_setting != None,
                                     "Scan result event has invalid name, {}".format(event))

                    # Append the event
                    scan_results_per_setting.add_event(event)

        except queue.Empty:
            self.fail("Event did not trigger for {} in {} seconds".
                      format(event_name, event_wait_time))

        finally:
            # Validate the scan results
            self.validate_scan_results(scan_results_dict)

            # Tear down and clean up
            for idx in idx_list:
                self.droid.wifiScannerStopBackgroundScan(idx)
            self.ed.clear_all_events()

    """ Helper Functions End """


    """ Tests Begin """
    def test_wifi_two_scans_at_same_interval(self):
        """Perform two WifiScanner background scans, one at 2.4GHz and the other
        at 5GHz, the same interval and number of BSSIDs per scan.

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_two_scans_at_different_interval(self):
        """Perform two WifiScanner background scans, one at 2.4GHz and the other
        at 5GHz, different interval and number of BSSIDs per scan.

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 20},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 30000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_24GHz_and_both(self):
        """Perform two WifiScanner background scans, one at 2.4GHz and
           the other at both 2.4GHz and 5GHz

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_BOTH,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_5GHz_and_both(self):
        """Perform two WifiScanner scans, one at 5GHz and the other at both
           2.4GHz and 5GHz

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_BOTH,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_24GHz_5GHz_and_both(self):
        """Perform three WifiScanner scans, one at 5GHz, one at 2.4GHz and the
        other at both 2.4GHz and 5GHz

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_BOTH,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 20000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_batch_and_24GHz(self):
        """Perform two WifiScanner background scans, one in batch mode for both
        bands and the other in periodic mode at 2.4GHz

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of results in batch mode should match the setting
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_BOTH,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL,
                           "numBssidsPerScan": 24,
                           "maxScansToCache": 2},
                         { "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_batch_and_5GHz(self):
        """Perform two WifiScanner background scans, one in batch mode for both
        bands and the other in periodic mode at 5GHz

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of results in batch mode should match the setting
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_BOTH,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_BUFFER_FULL,
                           "numBssidsPerScan": 24,
                           "maxScansToCache": 2},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_AFTER_EACH_SCAN,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    def test_wifi_scans_24GHz_5GHz_full_result(self):
        """Perform two WifiScanner background scans, one at 2.4GHz and
           the other at 5GHz. Report full scan results.

        Initial Conditions:
          * Set multiple APs broadcasting 2.4GHz and 5GHz.

        Expected Results:
          * DUT reports success for starting both scans
          * Scan results for each callback contains only the results on the
            frequency scanned
          * Wait for at least two scan results and confirm that separation
            between them approximately equals to the expected interval
          * Number of BSSIDs doesn't exceed
        """
        scan_settings = [{ "band": WifiEnums.WIFI_BAND_24_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_FULL_SCAN_RESULT,
                           "numBssidsPerScan": 24},
                         { "band": WifiEnums.WIFI_BAND_5_GHZ,
                           "periodInMs": 10000, # ms
                           "reportEvents": WifiEnums.REPORT_EVENT_FULL_SCAN_RESULT,
                           "numBssidsPerScan": 24}]

        self.scan_and_validate_results(scan_settings)

    """ Tests End """
