#!/usr/bin/python3.4
#
#   Copyright 2014 - Google
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

class TelEnums():
    # Operator id mapping to operator name
    operator_id_to_name = {
        "311480": "vzw",
        "310260": "tmo"
    }

    # Lookup network type name
    network_type_name = {
        "voice":{
                "tmo": {
                        "2g": "none",
                        "3g": "umts",
                        "lte": "lte",
                        "unknown": "unknown"
                },
                "vzw": {
                        "2g": "1xrtt",
                        "3g": "1xrtt",
                        "lte": "lte",
                        "unknown": "unknown"
                }
        },
        "data":{
                "tmo": {
                        "2g": "edge",
                        "3g": "hspa",
                        "lte": "lte",
                        "unknown": "unknown"
                },
                "vzw": {
                        "2g": "1xrtt",
                        "3g": "ehrpd",
                        "lte": "lte",
                        "unknown": "unknown"
                }
        }
    }

    # Network mapping tbl look up
    network_tbl = {
        "tmo": {
                "2g": "gsm/edge",
                "3g": "wcdma",
                "4g": "lte"
        },
        "vzw": {
                "2g": "1x",
                "3g": "do",
                "4g": "lte"
        },
        "unknown": {
                "2g": "unknown",
                "3g": "unknown",
                "4g": "unknown"
        }
    }

    # Test case mapping tbl look up
    test_tbl = {
        "verify data during call": {
                                    "wcdma": True,
                                    "gsm/edge": False,
                                    "lte": True,
                                    "1x": False,
                                    "do": False,
                                    "unknown": False
        }
    }