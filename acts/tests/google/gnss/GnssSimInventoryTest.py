import time
from acts import utils
from acts import signals
from acts.base_test import BaseTestClass
from acts.utils import get_current_epoch_time
from acts.test_utils.tel.tel_test_utils import get_iccid_by_adb
from acts.test_utils.tel.tel_test_utils import is_sim_ready_by_adb


class GnssSimInventoryTest(BaseTestClass):
    """ GNSS SIM Inventory Tests"""
    def __init__(self, controllers):
        BaseTestClass.__init__(self, controllers)
        self.ad = self.android_devices[0]
        req_params = ["sim_inventory_recipient", "sim_inventory_ldap"]
        self.unpack_userparams(req_param_names=req_params)

    def check_device_status(self):
        if not int(self.ad.adb.shell("settings get global airplane_mode_on")) == 0:
            self.ad.log.info("Force airplane mode off")
            utils.force_airplane_mode(self.ad, False)
        if not is_sim_ready_by_adb(self.ad.log, self.ad):
            raise signals.TestFailure("SIM card is not loaded and ready.")

    def check_sms_send_logcat_by_sl4a(self, begin_time):
        for i in range(10):
            logcat_results = self.ad.search_logcat("sl4a", begin_time)
            if logcat_results:
                for sl4a_message in logcat_results:
                    if "SMS Message send failed" in sl4a_message["log_message"]:
                        self.ad.log.error(sl4a_message["log_message"])
                        return False
            if not self.ad.is_adb_logcat_on:
                self.ad.start_adb_logcat()
            time.sleep(1)
        self.ad.log.info("SMS is successfully sent to %s." %
                         self.sim_inventory_recipient)
        return True

    def test_gnss_sim_inventory(self):
        begin_time = get_current_epoch_time()
        self.check_device_status()
        imsi = str(self.ad.adb.shell("service call iphonesubinfo 7"))
        if not imsi:
            raise signals.TestFailure("Couldn't get imsi")
        iccid = str(get_iccid_by_adb(self.ad))
        if not iccid:
            raise signals.TestFailure("Couldn't get iccid")
        sms_message = "imsi: %s, iccid: %s, ldap: %s, model: %s, sn: %s" % \
                      (imsi, iccid, self.sim_inventory_ldap, self.ad.model,
                       self.ad.serial)
        self.ad.log.info(sms_message)
        try:
            self.ad.log.info("Send SMS by SL4A.")
            self.ad.droid.smsSendTextMessage(self.sim_inventory_recipient,
                                             sms_message, True)
        except Exception as e:
            raise signals.TestError(e)
        return self.check_sms_send_logcat_by_sl4a(begin_time)
