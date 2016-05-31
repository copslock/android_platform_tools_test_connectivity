#/usr/bin/env python3.4
#
# Copyright (C) 2016 The Android Open Source Project
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
"""Compare_contacts accepts 2 vcf files, extracts full name, email, and
telephone numbers from each and reports how many unique cards it finds across
the two files.
"""

from mmap import ACCESS_READ
from mmap import mmap
import re

from acts.logger import LoggerProxy
from acts.utils import exe_cmd
log = LoggerProxy()

# Callback strings
CONTACTS_CHANGED_CALLBACK = "ContactsChanged"

# Paths for resources on device
CONTACTS_URI = "content://com.android.contacts/data/phones"
STORAGE_PATH = "/sdcard/Download/"


def _parse_contacts(file_name):
    """Read vcf file and generate a list of contacts.

    Contacts full name, prefered email, and all phone numbers are extracted.
    """

    vcard_regex = re.compile(b"^BEGIN:VCARD((\n*?.*?)*?)END:VCARD",
                             re.MULTILINE)
    fullname_regex = re.compile(b"^FN:(.*)", re.MULTILINE)
    email_regex = re.compile(b"^EMAIL;PREF:(.*)", re.MULTILINE)
    tel_regex = re.compile(b"^TEL;(.*):(.*)", re.MULTILINE)

    with open(file_name, "r") as contacts_file:
        contacts = []
        contacts_map = mmap(contacts_file.fileno(),
                            length=0,
                            access=ACCESS_READ)
        new_contact = None

        # find all VCARDs in the input file, then extract the first full name,
        # first email address, and all phone numbers from it.  If there is at
        # least a full name add it to the contact list.
        for current_vcard in vcard_regex.findall(contacts_map):
            fullname = fullname_regex.search(current_vcard[0])
            if fullname is None:
                continue
            new_contact = VCard(fullname.group(1))
            email = email_regex.search(current_vcard[0])
            if email is not None:
                new_contact.email = email.group(1)
            for phone_number in tel_regex.findall(current_vcard[0]):
                new_contact.add_phone_number(PhoneNumber(phone_number[0],
                                                         phone_number[1]))
            contacts.append(new_contact)

        return contacts


def compare_contacts(pce_contacts_file_name, pse_contacts_file_name):
    """ Compare two contact files and report the number of differences.

    Difference count is returned, and the differences are logged, this is order
    independent.
    """

    pce_contacts = _parse_contacts(pce_contacts_file_name)
    pse_contacts = _parse_contacts(pse_contacts_file_name)

    differences = set(pce_contacts).symmetric_difference(set(pse_contacts))
    if not differences:
        log.info("All {} contacts in the phonebooks match".format(str(len(
            pce_contacts))))
    else:
        log.info(str(len(set(pce_contacts).intersection(set(pse_contacts)))) +
                 " entries match, but...")
        log.info("The following {} entries don't match:".format(str(len(
            differences))))
        for current_vcard in differences:
            log.info(current_vcard)
    return len(differences)


class PhoneNumber(object):
    """Simple class for maintaining a phone number entry and type with only the
        digits.
    """

    def __init__(self, phone_type, phone_number):
        self.phone_type = phone_type
        # remove non digits from phone_number
        self.phone_number = re.sub(r"\D", "", str(phone_number))

    def __eq__(self, other):
        return (self.phone_type == other.phone_type and
                self.phone_number == other.phone_number)

    def __hash__(self):
        return hash(self.phone_type) ^ hash(self.phone_number)


class VCard(object):
    """Contains name, email, and phone numbers.
    """

    def __init__(self, name):
        self.name = name
        self.email = None
        self.phone_numbers = []

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        result = hash(self.name) ^ hash(self.email)
        for number in self.phone_numbers:
            result ^= hash(number)
        return result

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        result = str(self.name)
        if (self.email != None):
            result += "\n\t" + str(self.email)
        for number in self.phone_numbers:
            result += ("\n\t\t" + str(number.phone_type) + ":" +
                       str(number.phone_number))
        return result

    def add_phone_number(self, phone_number):
        if phone_number not in self.phone_numbers:
            self.phone_numbers.append(phone_number)


def get_contact_count(device):
    contact_list = device.droid.contactsQueryContent(
        CONTACTS_URI, ["display_name", "data1"], "", [], "display_name")
    return len(contact_list)


def add_contacts(device, file):
    exe_cmd("adb -s {} push {} {}{}"
            .format(device.serial, file, STORAGE_PATH, file))
    device.droid.importVcf("file://{}{}".format(STORAGE_PATH, file))
    return wait_for_contact_update_complete(device, 100)


def pull_contacts(device, file):
    device.droid.exportVcf("{}{}".format(STORAGE_PATH, file))
    try:
        exe_cmd("adb -s {} pull {}{}".format(device.serial, STORAGE_PATH, file))
        exe_cmd("adb -s {} shell rm {}{}"
                .format(device.serial, STORAGE_PATH, file))
    except OSError:
        self.log.error("Unable to pull or remove {}".format(file))
        return False
    return True


def erase_contacts(device):
    if get_contact_count(device):
        device.droid.contactsEraseAll()
        wait_for_contact_update_complete(device, 0)
        if get_contact_count(device):
            log.error("Phone book not empty.")
            return False
    return True


def wait_for_contact_update_complete(droid, expected_count):
    wait_for_update = 30
    try:
        while droid.ed.pop_event(CONTACTS_CHANGED_CALLBACK, wait_for_update):
            if get_contact_count(droid) == expected_count:
                log.info("Contacts ready")
                return True
    except Exception:
        log.error("Contacts failed to update.")
        return False

def set_logger(logger):
    global log
    log = logger
    log.info("Logger Set")
