#!/usr/bin/env python3.4
#
#   Copyright 2017 - The Android Open Source Project
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
import splinter
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from time import sleep

BROWSER_WAIT_SHORT = 1
BROWSER_WAIT_MED = 3
BROWSER_WAIT_LONG = 30
BROWSER_WAIT_EXTRA_LONG = 60


def create(configs):
    """ Factory method for retail AP class.

    Args:
        configs: list of dicts containing ap settings. ap settings must contain
        the following: brand, model, ip_address, username and password
    """
    SUPPORTED_APS = {
        ("Netgear", "R7000"): "NetgearR7000AP",
        ("Netgear", "R7500"): "NetgearR7500AP",
        ("Netgear", "R7800"): "NetgearR7800AP",
        ("Netgear", "R8000"): "NetgearR8000AP"
    }
    objs = []
    for config in configs:
        try:
            ap_class_name = SUPPORTED_APS[(config["brand"], config["model"])]
            ap_class = globals()[ap_class_name]
        except KeyError:
            raise KeyError("Invalid retail AP brand and model combination.")
        objs.append(ap_class(config))
    return objs


def detroy(objs):
    return


def visit_config_page(browser, url, page_load_timeout, num_tries):
    """ Method to visit Netgear AP webpages.

    This function visits a web page and checks the the resulting URL matches
    the intended URL, i.e. no redirects have happened

    Args:
        browser: the splinter browser object that will visit the URL
        url: the intended url
        num_tries: number of tries before url is declared unreachable
    """
    browser.driver.set_page_load_timeout(page_load_timeout)
    for idx in range(num_tries):
        try:
            browser.visit(url)
        except:
            browser.visit("https://www.google.com/")
        if browser.url.split("/")[-1] == url.split("/")[-1]:
            break
        if idx == num_tries - 1:
            raise RuntimeError("URL was unreachable.")


class WifiRetailAP(object):
    """ Base class implementation for retail ap.

    Base class provides functions whose implementation is shared by all aps.
    If some functions such as set_power not supported by ap, checks will raise
    exceptions.
    """

    def __init__(self, ap_settings):
        raise NotImplementedError

    def read_ap_settings(self):
        """ Function that reads current ap settings.

        Function implementation is AP dependent and thus base class raises exception
        if function not implemented in child class.
        """
        raise NotImplementedError

    def validate_ap_settings(self):
        """ Function to validate ap settings.

        This function compares the actual ap settings read from the web GUI
        with the assumed settings saved in the AP object. When called after AP
        configuration, this method helps ensure that our configuration was
        successful.

        Raises:
            ValueError: If read AP settings do not match stored settings.
        """
        assumed_ap_settings = self.ap_settings.copy()
        actual_ap_settings = self.read_ap_settings()
        if assumed_ap_settings != actual_ap_settings:
            raise ValueError(
                "Discrepancy in AP settings. Potential configuration error.")

    def configure_ap(self):
        """ Function that configures ap based on values of ap_settings.

        Function implementation is AP dependent and thus base class raises exception
        if function not implemented in child class.
        """
        raise NotImplementedError

    def set_radio_on_off(self, network, status):
        """ Function that turns the radio on or off.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            status: boolean indicating on or off (0: off, 1: on)
        """
        setting_to_update = {"status_{}".format(network): int(status)}
        self.update_ap_settings(setting_to_update)

    def set_ssid(self, network, ssid):
        """ Function that sets network SSID.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            ssid: string containing ssid
        """
        setting_to_update = {"ssid_{}".format(network): str(ssid)}
        self.update_ap_settings(setting_to_update)

    def set_channel(self, network, channel):
        """ Function that sets network channel.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            channel: string or int containing channel
        """
        setting_to_update = {"channel_{}".format(network): str(channel)}
        self.update_ap_settings(setting_to_update)

    def set_bandwidth(self, network, bandwidth):
        """ Function that sets network bandwidth/mode.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            bandwidth: string containing mode, e.g. 11g, VHT20, VHT40, VHT80.
        """
        setting_to_update = {"bandwidth_{}".format(network): str(bandwidth)}
        self.update_ap_settings(setting_to_update)

    def set_power(self, network, power):
        """ Function that sets network transmit power.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            power: string containing power level, e.g., 25%, 100%
        """
        setting_to_update = {"power_{}".format(network): str(power)}
        self.update_ap_settings(setting_to_update)

    def set_security(self, network, security_type, *password):
        """ Function that sets network security setting and password.

        Args:
            network: string containing network identifier (2G, 5G_1, 5G_2)
            security: string containing security setting, e.g., WPA2-PSK
            password: optional argument containing password
        """
        if (len(password) == 1) and (type(password[0]) == str):
            setting_to_update = {
                "security_type_{}".format(network): str(security_type),
                "password_{}".format(network): str(password[0])
            }
        else:
            setting_to_update = {
                "security_type_{}".format(network): str(security_type)
            }
        self.update_ap_settings(setting_to_update)

    def update_ap_settings(self, *dict_settings, **named_settings):
        """ Function to update settings of existing AP.

        Function copies arguments into ap_settings and calls configure_retail_ap
        to apply them.

        Args:
            *dict_settings accepts single dictionary of settings to update
            **named_settings accepts named settings to update
            Note: dict and named_settings cannot contain the same settings.
        """
        settings_to_update = {}
        if (len(dict_settings) == 1) and (type(dict_settings[0]) == dict):
            for key, value in dict_settings[0].items():
                if key in named_settings:
                    raise KeyError("{} was passed twice.".format(key))
                else:
                    settings_to_update[key] = value
        elif len(dict_settings) > 1:
            raise TypeError("Wrong number of positional arguments given")
            return

        for key, value in named_settings.items():
            settings_to_update[key] = value

        updates_requested = False
        for key, value in settings_to_update.items():
            if (key in self.ap_settings):
                if self.ap_settings[key] != value:
                    self.ap_settings[key] = value
                    updates_requested = True
            else:
                raise KeyError("Invalid setting passed to AP configuration.")

        if updates_requested:
            self.configure_ap()

    def band_lookup_by_channel(self, channel):
        """ Function that gives band name by channel number.

        Args:
            channel: channel number to lookup
        Returns:
            band: name of band which this channel belongs to on this ap
        """
        for key, value in self.CHANNEL_BAND_MAP.items():
            if channel in value:
                return key
        raise ValueError("Invalid channel passed in argument.")


class NetgearR7000AP(WifiRetailAP):
    """ Class that implements Netgear R7500 AP."""

    def __init__(self, ap_settings):
        self.ap_settings = ap_settings.copy()
        self.CONFIG_PAGE = "{}://{}:{}@{}:{}/WLG_wireless_dual_band_r10.htm".format(
            self.ap_settings["protocol"], self.ap_settings["admin_username"],
            self.ap_settings["admin_password"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_NOLOGIN = "{}://{}:{}/WLG_wireless_dual_band_r10.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_ADVANCED = "{}://{}:{}/WLG_adv_dual_band2.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CHROME_OPTIONS = splinter.driver.webdriver.chrome.Options()
        self.CHROME_OPTIONS.add_argument("--no-proxy-server")
        self.CHROME_OPTIONS.add_argument("--no-sandbox")
        self.CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
        self.CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
        self.CHROME_CAPABILITIES = DesiredCapabilities.CHROME.copy()
        self.CHROME_CAPABILITIES["acceptSslCerts"] = True
        self.CHROME_CAPABILITIES["acceptInsecureCerts"] = True
        if self.ap_settings["headless_browser"]:
            self.CHROME_OPTIONS.add_argument("--headless")
            self.CHROME_OPTIONS.add_argument("--disable-gpu")
        self.NETWORKS = ["2G", "5G_1"]
        self.CHANNEL_BAND_MAP = {
            "2G": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "5G_1": [
                36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120,
                124, 128, 132, 136, 140, 149, 153, 157, 161, 165
            ]
        }
        self.REGION_MAP = {
            "1": "Africa",
            "2": "Asia",
            "3": "Australia",
            "4": "Canada",
            "5": "Europe",
            "6": "Israel",
            "7": "Japan",
            "8": "Korea",
            "9": "Mexico",
            "10": "South America",
            "11": "United States",
            "12": "Middle East(Algeria/Syria/Yemen)",
            "14": "Russia",
            "16": "China",
            "17": "India",
            "18": "Malaysia",
            "19": "Middle East(Iran/Labanon/Qatar)",
            "20": "Middle East(Turkey/Egypt/Tunisia/Kuwait)",
            "21": "Middle East(Saudi Arabia)",
            "22": "Middle East(United Arab Emirates)",
            "23": "Singapore",
            "24": "Taiwan"
        }
        self.CONFIG_PAGE_FIELDS = {
            "region": "WRegion",
            ("2G", "status"): "enable_ap",
            ("5G_1", "status"): "enable_ap_an",
            ("2G", "ssid"): "ssid",
            ("5G_1", "ssid"): "ssid_an",
            ("2G", "channel"): "w_channel",
            ("5G_1", "channel"): "w_channel_an",
            ("2G", "bandwidth"): "opmode",
            ("5G_1", "bandwidth"): "opmode_an",
            ("2G", "power"): "enable_tpc",
            ("5G_1", "power"): "enable_tpc_an",
            ("2G", "security_type"): "security_type",
            ("5G_1", "security_type"): "security_type_an",
            ("2G", "password"): "passphrase",
            ("5G_1", "password"): "passphrase_an"
        }
        self.BW_MODE_VALUES = {
            "g and b": "11g",
            "145Mbps": "VHT20",
            "300Mbps": "VHT40",
            "HT80": "VHT80"
        }
        self.POWER_MODE_VALUES = {
            "1": "100%",
            "2": "75%",
            "3": "50%",
            "4": "25%"
        }
        self.BW_MODE_TEXT = {
            "11g": "Up to 54 Mbps",
            "VHT20": "Up to 289 Mbps",
            "VHT40": "Up to 600 Mbps",
            "VHT80": "Up to 1300 Mbps"
        }
        self.read_ap_settings()
        if ap_settings.items() <= self.ap_settings.items():
            return
        else:
            self.update_ap_settings(ap_settings)

    def read_ap_settings(self):
        """ Function to read ap settings."""
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            # Visit URL
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE_NOLOGIN,
                              BROWSER_WAIT_MED, 10)

            for key, value in self.CONFIG_PAGE_FIELDS.items():
                if "status" in key:
                    visit_config_page(browser, self.CONFIG_PAGE_ADVANCED,
                                      BROWSER_WAIT_MED, 10)
                    config_item = browser.find_by_name(value)
                    self.ap_settings["{}_{}".format(key[1], key[0])] = int(
                        config_item.first.checked)
                    visit_config_page(browser, self.CONFIG_PAGE_NOLOGIN,
                                      BROWSER_WAIT_MED, 10)
                else:
                    config_item = browser.find_by_name(value)
                    if "bandwidth" in key:
                        self.ap_settings["{}_{}".format(key[1], key[
                            0])] = self.BW_MODE_VALUES[config_item.first.value]
                    elif "power" in key:
                        self.ap_settings["{}_{}".format(
                            key[1], key[0])] = self.POWER_MODE_VALUES[
                                config_item.first.value]
                    elif "region" in key:
                        self.ap_settings["region"] = self.REGION_MAP[
                            config_item.first.value]
                    elif "security_type" in key:
                        for item in config_item:
                            if item.checked:
                                self.ap_settings["{}_{}".format(
                                    key[1], key[0])] = item.value
                    else:
                        config_item = browser.find_by_name(value)
                        self.ap_settings["{}_{}".format(
                            key[1], key[0])] = config_item.first.value
        return self.ap_settings.copy()

    def configure_ap(self):
        """ Function to configure ap wireless settings."""
        # Turn radios on or off
        self.configure_radio_on_off()
        # Configure radios
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            # Visit URL
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE_NOLOGIN,
                              BROWSER_WAIT_MED, 10)

            # Update region, and power/bandwidth for each network
            for key, value in self.CONFIG_PAGE_FIELDS.items():
                if "power" in key:
                    config_item = browser.find_by_name(value).first
                    config_item.select_by_text(self.ap_settings["{}_{}".format(
                        key[1], key[0])])
                elif "region" in key:
                    config_item = browser.find_by_name(value).first
                    config_item.select_by_text(self.ap_settings["region"])
                elif "bandwidth" in key:
                    config_item = browser.find_by_name(value).first
                    config_item.select_by_text(
                        self.BW_MODE_TEXT[self.ap_settings["{}_{}".format(
                            key[1], key[0])]])

            # Update security settings (passwords updated only if applicable)
            for key, value in self.CONFIG_PAGE_FIELDS.items():
                if "security_type" in key:
                    browser.choose(value, self.ap_settings["{}_{}".format(
                        key[1], key[0])])
                    if self.ap_settings["{}_{}".format(key[1],
                                                       key[0])] == "WPA2-PSK":
                        config_item = browser.find_by_name(
                            self.CONFIG_PAGE_FIELDS[(key[0],
                                                     "password")]).first
                        config_item.fill(self.ap_settings["{}_{}".format(
                            "password", key[0])])

            # Update SSID and channel for each network
            # NOTE: Update ordering done as such as workaround for R8000
            # wherein channel and SSID get overwritten when some other
            # variables are changed. However, region does have to be set before
            # channel in all cases.
            for key, value in self.CONFIG_PAGE_FIELDS.items():
                if "ssid" in key:
                    config_item = browser.find_by_name(value).first
                    config_item.fill(self.ap_settings["{}_{}".format(
                        key[1], key[0])])
                elif "channel" in key:
                    config_item = browser.find_by_name(value).first
                    config_item.select(self.ap_settings["{}_{}".format(
                        key[1], key[0])])
                    sleep(BROWSER_WAIT_SHORT)
                    try:
                        alert = browser.get_alert()
                        alert.accept()
                    except:
                        pass

            sleep(BROWSER_WAIT_SHORT)
            browser.find_by_name("Apply").first.click()
            sleep(BROWSER_WAIT_SHORT)
            try:
                alert = browser.get_alert()
                alert.accept()
                sleep(BROWSER_WAIT_SHORT)
            except:
                sleep(BROWSER_WAIT_SHORT)
            visit_config_page(browser, self.CONFIG_PAGE,
                              BROWSER_WAIT_EXTRA_LONG, 10)
            self.validate_ap_settings()

    def configure_radio_on_off(self):
        """ Helper configuration function to turn radios on/off."""
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            # Visit URL
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE_ADVANCED,
                              BROWSER_WAIT_MED, 10)

            # Turn radios on or off
            status_toggled = False
            for key, value in self.CONFIG_PAGE_FIELDS.items():
                if "status" in key:
                    config_item = browser.find_by_name(value).first
                    current_status = int(config_item.checked)
                    if current_status != self.ap_settings["{}_{}".format(
                            key[1], key[0])]:
                        status_toggled = True
                        if self.ap_settings["{}_{}".format(key[1], key[0])]:
                            config_item.check()
                        else:
                            config_item.uncheck()

            if status_toggled:
                sleep(BROWSER_WAIT_SHORT)
                browser.find_by_name("Apply").first.click()
                sleep(BROWSER_WAIT_EXTRA_LONG)
                visit_config_page(browser, self.CONFIG_PAGE,
                                  BROWSER_WAIT_EXTRA_LONG, 10)


class NetgearR7500AP(WifiRetailAP):
    """ Class that implements Netgear R7500 AP."""

    def __init__(self, ap_settings):
        self.ap_settings = ap_settings.copy()
        self.CONFIG_PAGE = "{}://{}:{}@{}:{}/index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["admin_username"],
            self.ap_settings["admin_password"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_NOLOGIN = "{}://{}:{}/index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_ADVANCED = "{}://{}:{}/adv_index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CHROME_OPTIONS = splinter.driver.webdriver.chrome.Options()
        self.CHROME_OPTIONS.add_argument("--no-proxy-server")
        self.CHROME_OPTIONS.add_argument("--no-sandbox")
        self.CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
        self.CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
        self.CHROME_CAPABILITIES = DesiredCapabilities.CHROME.copy()
        self.CHROME_CAPABILITIES["acceptSslCerts"] = True
        self.CHROME_CAPABILITIES["acceptInsecureCerts"] = True
        if self.ap_settings["headless_browser"]:
            self.CHROME_OPTIONS.add_argument("--headless")
            self.CHROME_OPTIONS.add_argument("--disable-gpu")
        self.NETWORKS = ["2G", "5G_1"]
        self.CHANNEL_BAND_MAP = {
            "2G": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "5G_1": [
                36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120,
                124, 128, 132, 136, 140, 149, 153, 157, 161, 165
            ]
        }
        self.CONFIG_PAGE_FIELDS = {
            "region": "WRegion",
            ("2G", "status"): "enable_ap",
            ("5G_1", "status"): "enable_ap_an",
            ("2G", "ssid"): "ssid",
            ("5G_1", "ssid"): "ssid_an",
            ("2G", "channel"): "w_channel",
            ("5G_1", "channel"): "w_channel_an",
            ("2G", "bandwidth"): "opmode",
            ("5G_1", "bandwidth"): "opmode_an",
            ("2G", "security_type"): "security_type",
            ("5G_1", "security_type"): "security_type_an",
            ("2G", "password"): "passphrase",
            ("5G_1", "password"): "passphrase_an"
        }
        self.REGION_MAP = {
            "0": "Africa",
            "1": "Asia",
            "2": "Australia",
            "3": "Canada",
            "4": "Europe",
            "5": "Israel",
            "6": "Japan",
            "7": "Korea",
            "8": "Mexico",
            "9": "South America",
            "10": "United States",
            "11": "China",
            "12": "India",
            "13": "Malaysia",
            "14": "Middle East(Algeria/Syria/Yemen)",
            "15": "Middle East(Iran/Labanon/Qatar)",
            "16": "Middle East(Turkey/Egypt/Tunisia/Kuwait)",
            "17": "Middle East(Saudi Arabia)",
            "18": "Middle East(United Arab Emirates)",
            "19": "Russia",
            "20": "Singapore",
            "21": "Taiwan"
        }
        self.BW_MODE_TEXT_2G = {
            "11g": "Up to 54 Mbps",
            "VHT20": "Up to 289 Mbps",
            "VHT40": "Up to 600 Mbps"
        }
        self.BW_MODE_TEXT_5G = {
            "VHT20": "Up to 347 Mbps",
            "VHT40": "Up to 800 Mbps",
            "VHT80": "Up to 1733 Mbps"
        }
        self.BW_MODE_VALUES = {
            "1": "11g",
            "2": "VHT20",
            "3": "VHT40",
            "7": "VHT20",
            "8": "VHT40",
            "9": "VHT80"
        }
        self.read_ap_settings()
        if ap_settings.items() <= self.ap_settings.items():
            return
        else:
            self.update_ap_settings(ap_settings)

    def read_ap_settings(self):
        """ Function to read ap wireless settings."""
        # Get radio status (on/off)
        self.read_radio_on_off()
        # Get radio configuration. Note that if both radios are off, the below
        # code will result in an error
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            sleep(BROWSER_WAIT_SHORT)
            wireless_button = browser.find_by_id("wireless").first
            wireless_button.click()
            sleep(BROWSER_WAIT_MED)

            with browser.get_iframe("formframe") as iframe:
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "bandwidth" in key:
                        config_item = iframe.find_by_name(value).first
                        self.ap_settings["{}_{}".format(
                            key[1],
                            key[0])] = self.BW_MODE_VALUES[config_item.value]
                    elif "region" in key:
                        config_item = iframe.find_by_name(value).first
                        self.ap_settings["region"] = self.REGION_MAP[
                            config_item.value]
                    elif "password" in key:
                        try:
                            config_item = iframe.find_by_name(value).first
                            self.ap_settings["{}_{}".format(
                                key[1], key[0])] = config_item.value
                            self.ap_settings["{}_{}".format(
                                "security_type", key[0])] = "WPA2-PSK"
                        except:
                            self.ap_settings["{}_{}".format(
                                key[1], key[0])] = "defaultpassword"
                            self.ap_settings["{}_{}".format(
                                "security_type", key[0])] = "Disable"
                    elif ("channel" in key) or ("ssid" in key):
                        config_item = iframe.find_by_name(value).first
                        self.ap_settings["{}_{}".format(
                            key[1], key[0])] = config_item.value
                    else:
                        pass
        return self.ap_settings.copy()

    def configure_ap(self):
        """ Function to configure ap wireless settings."""
        # Turn radios on or off
        self.configure_radio_on_off()
        # Configure radios
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            sleep(BROWSER_WAIT_SHORT)
            wireless_button = browser.find_by_id("wireless").first
            wireless_button.click()
            sleep(BROWSER_WAIT_MED)

            with browser.get_iframe("formframe") as iframe:
                # Update AP region. Must be done before channel setting
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "region" in key:
                        config_item = iframe.find_by_name(value).first
                        config_item.select_by_text(self.ap_settings["region"])
                # Update wireless settings for each network
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "ssid" in key:
                        config_item = iframe.find_by_name(value).first
                        config_item.fill(self.ap_settings["{}_{}".format(
                            key[1], key[0])])
                    elif "channel" in key:
                        channel_string = "0" * (int(
                            self.ap_settings["{}_{}".format(key[1], key[0])]
                        ) < 10) + str(self.ap_settings["{}_{}".format(
                            key[1], key[0])]) + "(DFS)" * (
                                48 < int(self.ap_settings["{}_{}".format(
                                    key[1], key[0])]) < 149)
                        config_item = iframe.find_by_name(value).first
                        config_item.select_by_text(channel_string)
                    elif key == ("2G", "bandwidth"):
                        config_item = iframe.find_by_name(value).first
                        config_item.select_by_text(
                            str(self.BW_MODE_TEXT_2G[self.ap_settings[
                                "{}_{}".format(key[1], key[0])]]))
                    elif key == ("5G_1", "bandwidth"):
                        config_item = iframe.find_by_name(value).first
                        config_item.select_by_text(
                            str(self.BW_MODE_TEXT_5G[self.ap_settings[
                                "{}_{}".format(key[1], key[0])]]))

                # Update passwords for WPA2-PSK protected networks
                # (Must be done after security type is selected)
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "security_type" in key:
                        iframe.choose(value, self.ap_settings["{}_{}".format(
                            key[1], key[0])])
                        if self.ap_settings["{}_{}".format(
                                key[1], key[0])] == "WPA2-PSK":
                            config_item = iframe.find_by_name(
                                self.CONFIG_PAGE_FIELDS[(key[0],
                                                         "password")]).first
                            config_item.fill(self.ap_settings["{}_{}".format(
                                "password", key[0])])

                apply_button = iframe.find_by_name("Apply")
                apply_button[0].click()
                sleep(BROWSER_WAIT_SHORT)
                try:
                    alert = browser.get_alert()
                    alert.accept()
                except:
                    pass
                sleep(BROWSER_WAIT_SHORT)
                try:
                    alert = browser.get_alert()
                    alert.accept()
                except:
                    pass
                sleep(BROWSER_WAIT_SHORT)
            sleep(BROWSER_WAIT_EXTRA_LONG)
            visit_config_page(browser, self.CONFIG_PAGE,
                              BROWSER_WAIT_EXTRA_LONG, 10)
            self.validate_ap_settings()

    def configure_radio_on_off(self):
        """ Helper configuration function to turn radios on/off."""
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE_ADVANCED,
                              BROWSER_WAIT_MED, 10)
            sleep(BROWSER_WAIT_SHORT)
            wireless_button = browser.find_by_id("advanced_bt").first
            wireless_button.click()
            sleep(BROWSER_WAIT_SHORT)
            wireless_button = browser.find_by_id("wladv").first
            wireless_button.click()
            sleep(BROWSER_WAIT_MED)

            with browser.get_iframe("formframe") as iframe:
                # Turn radios on or off
                status_toggled = False
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "status" in key:
                        config_item = iframe.find_by_name(value).first
                        current_status = int(config_item.checked)
                        if current_status != self.ap_settings["{}_{}".format(
                                key[1], key[0])]:
                            status_toggled = True
                            if self.ap_settings["{}_{}".format(key[1],
                                                               key[0])]:
                                config_item.check()
                            else:
                                config_item.uncheck()

                if status_toggled:
                    sleep(BROWSER_WAIT_SHORT)
                    browser.find_by_name("Apply").first.click()
                    sleep(BROWSER_WAIT_EXTRA_LONG)
                    visit_config_page(browser, self.CONFIG_PAGE,
                                      BROWSER_WAIT_EXTRA_LONG, 10)

    def read_radio_on_off(self):
        """ Helper configuration function to read radio status."""
        with splinter.Browser(
                "chrome",
                options=self.CHROME_OPTIONS,
                desired_capabilities=self.CHROME_CAPABILITIES) as browser:
            visit_config_page(browser, self.CONFIG_PAGE, BROWSER_WAIT_MED, 10)
            visit_config_page(browser, self.CONFIG_PAGE_ADVANCED,
                              BROWSER_WAIT_MED, 10)
            wireless_button = browser.find_by_id("advanced_bt").first
            wireless_button.click()
            sleep(BROWSER_WAIT_SHORT)
            wireless_button = browser.find_by_id("wladv").first
            wireless_button.click()
            sleep(BROWSER_WAIT_MED)

            with browser.get_iframe("formframe") as iframe:
                # Turn radios on or off
                for key, value in self.CONFIG_PAGE_FIELDS.items():
                    if "status" in key:
                        config_item = iframe.find_by_name(value).first
                        self.ap_settings["{}_{}".format(key[1], key[0])] = int(
                            config_item.checked)


class NetgearR7800AP(NetgearR7500AP):
    """ Class that implements Netgear R7800 AP."""

    def __init__(self, ap_settings):
        self.ap_settings = ap_settings.copy()
        self.CONFIG_PAGE = "{}://{}:{}@{}:{}/index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["admin_username"],
            self.ap_settings["admin_password"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_NOLOGIN = "{}://{}:{}/index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CONFIG_PAGE_ADVANCED = "{}://{}:{}/adv_index.htm".format(
            self.ap_settings["protocol"], self.ap_settings["ip_address"],
            self.ap_settings["port"])
        self.CHROME_OPTIONS = splinter.driver.webdriver.chrome.Options()
        self.CHROME_OPTIONS.add_argument("--no-proxy-server")
        self.CHROME_OPTIONS.add_argument("--no-sandbox")
        self.CHROME_OPTIONS.add_argument("--allow-running-insecure-content")
        self.CHROME_OPTIONS.add_argument("--ignore-certificate-errors")
        self.CHROME_CAPABILITIES = DesiredCapabilities.CHROME.copy()
        self.CHROME_CAPABILITIES["acceptSslCerts"] = True
        self.CHROME_CAPABILITIES["acceptInsecureCerts"] = True
        if self.ap_settings["headless_browser"]:
            self.CHROME_OPTIONS.add_argument("--headless")
            self.CHROME_OPTIONS.add_argument("--disable-gpu")
        self.NETWORKS = ["2G", "5G_1"]
        self.CHANNEL_BAND_MAP = {
            "2G": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "5G_1": [
                36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120,
                124, 128, 132, 136, 140, 149, 153, 157, 161, 165
            ]
        }
        self.CONFIG_PAGE_FIELDS = {
            "region": "WRegion",
            ("2G", "status"): "enable_ap",
            ("5G_1", "status"): "enable_ap_an",
            ("2G", "ssid"): "ssid",
            ("5G_1", "ssid"): "ssid_an",
            ("2G", "channel"): "w_channel",
            ("5G_1", "channel"): "w_channel_an",
            ("2G", "bandwidth"): "opmode",
            ("5G_1", "bandwidth"): "opmode_an",
            ("2G", "security_type"): "security_type",
            ("5G_1", "security_type"): "security_type_an",
            ("2G", "password"): "passphrase",
            ("5G_1", "password"): "passphrase_an"
        }
        self.REGION_MAP = {
            "0": "Africa",
            "1": "Asia",
            "2": "Australia",
            "3": "Canada",
            "4": "Europe",
            "5": "Israel",
            "6": "Japan",
            "7": "Korea",
            "8": "Mexico",
            "9": "South America",
            "10": "United States",
            "11": "China",
            "12": "India",
            "13": "Malaysia",
            "14": "Middle East(Algeria/Syria/Yemen)",
            "15": "Middle East(Iran/Labanon/Qatar)",
            "16": "Middle East(Turkey/Egypt/Tunisia/Kuwait)",
            "17": "Middle East(Saudi Arabia)",
            "18": "Middle East(United Arab Emirates)",
            "19": "Russia",
            "20": "Singapore",
            "21": "Taiwan"
        }
        self.BW_MODE_TEXT_2G = {
            "11g": "Up to 54 Mbps",
            "VHT20": "Up to 347 Mbps",
            "VHT40": "Up to 600 Mbps"
        }
        self.BW_MODE_TEXT_5G = {
            "VHT20": "Up to 347 Mbps",
            "VHT40": "Up to 800 Mbps",
            "VHT80": "Up to 1733 Mbps"
        }
        self.BW_MODE_VALUES = {
            "1": "11g",
            "2": "VHT20",
            "3": "VHT40",
            "7": "VHT20",
            "8": "VHT40",
            "9": "VHT80"
        }
        self.read_ap_settings()
        if ap_settings.items() <= self.ap_settings.items():
            return
        else:
            self.update_ap_settings(ap_settings)


class NetgearR8000AP(NetgearR7000AP):
    """ Class that implements Netgear R8000 AP.

    Since most of the class' implementation is shared with the R7000, this
    class inherits from NetgearR7000AP and simply redifines config parameters
    """

    def __init__(self, ap_settings):
        self.ap_settings = ap_settings.copy()
        self.CONFIG_PAGE = "http://{}:{}@{}/WLG_wireless_dual_band_r8000.htm".format(
            self.ap_settings["admin_username"],
            self.ap_settings["admin_password"], self.ap_settings["ip_address"])
        self.CONFIG_PAGE_NOLOGIN = "http://{}/WLG_wireless_dual_band_r8000.htm".format(
            self.ap_settings["ip_address"])
        self.CONFIG_PAGE_ADVANCED = "http://{}/WLG_adv_dual_band2_r8000.htm".format(
            self.ap_settings["ip_address"])
        self.CHROME_OPTIONS = splinter.driver.webdriver.chrome.Options()
        self.CHROME_OPTIONS.add_argument("--no-proxy-server")
        self.CHROME_OPTIONS.add_argument("--no-sandbox")
        if self.ap_settings["headless_browser"]:
            self.CHROME_OPTIONS.add_argument("--headless")
            self.CHROME_OPTIONS.add_argument("--disable-gpu")
        self.NETWORKS = ["2G", "5G_1", "5G_2"]
        self.CHANNEL_BAND_MAP = {
            "2G": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "5G_1": [36, 40, 44, 48],
            "5G_2": [149, 153, 157, 161, 165]
        }
        self.REGION_MAP = {
            "1": "Africa",
            "2": "Asia",
            "3": "Australia",
            "4": "Canada",
            "5": "Europe",
            "6": "Israel",
            "7": "Japan",
            "8": "Korea",
            "9": "Mexico",
            "10": "South America",
            "11": "United States",
            "12": "Middle East(Algeria/Syria/Yemen)",
            "14": "Russia",
            "16": "China",
            "17": "India",
            "18": "Malaysia",
            "19": "Middle East(Iran/Labanon/Qatar)",
            "20": "Middle East(Turkey/Egypt/Tunisia/Kuwait)",
            "21": "Middle East(Saudi Arabia)",
            "22": "Middle East(United Arab Emirates)",
            "23": "Singapore",
            "24": "Taiwan"
        }
        self.CONFIG_PAGE_FIELDS = {
            "region": "WRegion",
            ("2G", "status"): "enable_ap",
            ("5G_1", "status"): "enable_ap_an",
            ("5G_2", "status"): "enable_ap_an_2",
            ("2G", "ssid"): "ssid",
            ("5G_1", "ssid"): "ssid_an",
            ("5G_2", "ssid"): "ssid_an_2",
            ("2G", "channel"): "w_channel",
            ("5G_1", "channel"): "w_channel_an",
            ("5G_2", "channel"): "w_channel_an_2",
            ("2G", "bandwidth"): "opmode",
            ("5G_1", "bandwidth"): "opmode_an",
            ("5G_2", "bandwidth"): "opmode_an_2",
            ("2G", "security_type"): "security_type",
            ("5G_1", "security_type"): "security_type_an",
            ("5G_2", "security_type"): "security_type_an_2",
            ("2G", "password"): "passphrase",
            ("5G_1", "password"): "passphrase_an",
            ("5G_2", "password"): "passphrase_an_2"
        }
        self.read_ap_settings()
        if ap_settings.items() <= self.ap_settings.items():
            return
        else:
            self.update_ap_settings(ap_settings)
