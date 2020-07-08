#!/usr/bin/env python3
#
#   Copyright 2020 - The Android Open Source Project
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


class ResourcesRegistryError(Exception):
    pass


_REGISTRY = {}


def update_registry(registry):
    """Updates the registry with the one passed.

    Overriding a previous value is not allowed.

    Args:
        registry: A dictionary.
    Raises:
        ResourceRegistryError if a property is updated with a different value.
    """
    for k, v in registry.items():
        if k in _REGISTRY:
            if v == _REGISTRY[k]:
                continue
            raise ResourcesRegistryError(
                'Overwriting resources_registry fields is not allowed. %s was '
                'already defined as %s and was attempted to be overwritten '
                'with %s.' % (k, _REGISTRY[k], v))
        _REGISTRY[k] = v


def get_registry():
    return _REGISTRY
