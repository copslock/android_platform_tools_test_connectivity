#!/usr/bin/env python3.4
#
#   Copyright 2016 - Google
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

# This is test util for subscription setup.
# It will be deleted once we have better solution for subscription ids.
from future import standard_library
standard_library.install_aliases()
from acts.test_utils.tel.tel_test_utils import get_subid_from_slot_index
from acts.test_utils.tel.tel_test_utils import set_subid_for_data
from acts.test_utils.tel.tel_test_utils import set_subid_for_message
from acts.test_utils.tel.tel_test_utils import set_subid_for_outgoing_call

def initial_set_up_for_subid_infomation(log, ad):
    """Initial subid setup for voice, message and data according to ad's
    attribute.

    Setup sub id properties for android device. Including the followings:
        incoming_voice_sub_id
        incoming_message_sub_id
        outgoing_voice_sub_id
        outgoing_message_sub_id
        default_data_sub_id

    Args:
        log: log object
        ad: android device object

    Returns:
        None
    """
    # outgoing_voice_sub_id
    # If default_voice_sim_slot_index is set in config file, then use sub_id
    # of this SIM as default_outgoing_sub_id. If default_voice_sim_slot_index
    # is not set, then use default voice sub_id as default_outgoing_sub_id.
    # Outgoing voice call will be made on default_outgoing_sub_id by default.
    if hasattr(ad, "default_voice_sim_slot_index"):
        outgoing_voice_sub_id = get_subid_from_slot_index(log, ad,
            ad.default_voice_sim_slot_index)
        set_subid_for_outgoing_call(ad, outgoing_voice_sub_id)
    else:
        outgoing_voice_sub_id = ad.droid.subscriptionGetDefaultVoiceSubId()
    setattr(ad, "outgoing_voice_sub_id", outgoing_voice_sub_id)

    # outgoing_message_sub_id
    # If default_message_sim_slot_index is set in config file, then use sub_id
    # of this SIM as outgoing_message_sub_id. If default_message_sim_slot_index
    # is not set, then use default Sms sub_id as outgoing_message_sub_id.
    # Outgoing SMS will be sent on outgoing_message_sub_id by default.
    if hasattr(ad, "default_message_sim_slot_index"):
        outgoing_message_sub_id = get_subid_from_slot_index(log, ad,
            ad.default_message_sim_slot_index)
        set_subid_for_message(ad, outgoing_message_sub_id)
    else:
        outgoing_message_sub_id = ad.droid.subscriptionGetDefaultSmsSubId()
    setattr(ad, "outgoing_message_sub_id", outgoing_message_sub_id)

    # default_data_sub_id
    # If default_data_sim_slot_index is set in config file, then use sub_id
    # of this SIM as default_data_sub_id. If default_data_sim_slot_index
    # is not set, then use default Data sub_id as default_data_sub_id.
    # Data connection will be established on default_data_sub_id by default.
    if hasattr(ad, "default_data_sim_slot_index"):
        default_data_sub_id = get_subid_from_slot_index(log, ad,
            ad.default_data_sim_slot_index)
        set_subid_for_data(ad, default_data_sub_id, 0)
    else:
        default_data_sub_id = ad.droid.subscriptionGetDefaultDataSubId()
    setattr(ad, "default_data_sub_id", default_data_sub_id)

    # This is for Incoming Voice Sub ID
    # If "incoming_voice_sim_slot_index" is set in config file, then
    # incoming voice call will call to the phone number of the SIM in
    # "incoming_voice_sim_slot_index".
    # If "incoming_voice_sim_slot_index" is NOT set in config file,
    # then incoming voice call will call to the phone number of default
    # subId.
    if hasattr(ad, "incoming_voice_sim_slot_index"):
        incoming_voice_sub_id = get_subid_from_slot_index(
            log, ad, ad.incoming_voice_sim_slot_index)
    else:
        incoming_voice_sub_id = ad.droid.subscriptionGetDefaultVoiceSubId()
    setattr(ad, "incoming_voice_sub_id", incoming_voice_sub_id)

    # This is for Incoming SMS Sub ID
    # If "incoming_message_sim_slot_index" is set in config file, then
    # incoming SMS be sent to the phone number of the SIM in
    # "incoming_message_sim_slot_index".
    # If "incoming_message_sim_slot_index" is NOT set in config file,
    # then incoming SMS be sent to the phone number of default
    # subId.
    if hasattr(ad, "incoming_message_sim_slot_index"):
        incoming_message_sub_id = get_subid_from_slot_index(
            log, ad, ad.incoming_message_sim_slot_index)
    else:
        incoming_message_sub_id = ad.droid.subscriptionGetDefaultSmsSubId()
    setattr(ad, "incoming_message_sub_id", incoming_message_sub_id)

def get_default_data_sub_id(ad):
    """ Get default data subscription id
    """
    if hasattr(ad, "default_data_sub_id"):
        return ad.default_data_sub_id
    else:
        return ad.droid.subscriptionGetDefaultDataSubId()

def get_outgoing_message_sub_id(ad):
    """ Get outgoing message subscription id
    """
    if hasattr(ad, "outgoing_message_sub_id"):
        return ad.outgoing_message_sub_id
    else:
        return ad.droid.subscriptionGetDefaultSmsSubId()

def get_outgoing_voice_sub_id(ad):
    """ Get outgoing voice subscription id
    """
    if hasattr(ad, "outgoing_voice_sub_id"):
        return ad.outgoing_voice_sub_id
    else:
        return ad.droid.subscriptionGetDefaultVoiceSubId()

def get_incoming_voice_sub_id(ad):
    """ Get incoming voice subscription id
    """
    if hasattr(ad, "incoming_voice_sub_id"):
        return ad.incoming_voice_sub_id
    else:
        return ad.droid.subscriptionGetDefaultVoiceSubId()

def get_incoming_message_sub_id(ad):
    """ Get incoming message subscription id
    """
    if hasattr(ad, "incoming_message_sub_id"):
        return ad.incoming_message_sub_id
    else:
        return ad.droid.subscriptionGetDefaultSmsSubId()
