#!/usr/bin/env python3
#
#   Copyright 2019 - The Android Open Source Project
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

from acts.controllers.fuchsia_lib.base_lib import BaseLib


class FuchsiaProfileServerLib(BaseLib):

    def __init__(self, addr, tc, client_id):
        self.address = addr
        self.test_counter = tc
        self.client_id = client_id

    def addService(self, record):
        """Publishes an SDP service record specified by input args

        Args:
            record: A database that represents an SDP record to
                be published.

        Returns:
            Dictionary, service id if success, error if error.
        """
        test_cmd = "profile_server_facade.ProfileServerAddService"
        test_args = {
            "record": record,
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def addSearch(self, attribute_list, profile_id):
        """Publishes services specified by input args

        Args:
            attribute_list: The list of attributes to set
            profile_id: The profile ID to set.
        Returns:
            Dictionary, None if success, error if error.
        """
        test_cmd = "profile_server_facade.ProfileServerAddSearch"
        test_args = {
            "attribute_list": attribute_list,
            "profile_id": profile_id
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def removeService(self, service_id):
        """Removes a service.

        Args:
            record: A database that represents an SDP record to
                be published.

        Returns:
            Dictionary, None if success, error if error.
        """
        test_cmd = "profile_server_facade.ProfileServerRemoveService"
        test_args = {
            "service_id": service_id,
        }
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def init(self):
        """Initializes the ProfileServerFacade's proxy object.

        No operations for SDP can be performed until this is initialized.

        Returns:
            Dictionary, None if success, error if error.
        """
        test_cmd = "profile_server_facade.ProfileServerInit"
        test_args = {}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)

    def cleanUp(self):
        """Cleans up all objects related to SDP.

        Returns:
            Dictionary, None if success, error if error.
        """
        test_cmd = "profile_server_facade.ProfileServerCleanup"
        test_args = {}
        test_id = self.build_id(self.test_counter)
        self.test_counter += 1

        return self.send_command(test_id, test_cmd, test_args)
