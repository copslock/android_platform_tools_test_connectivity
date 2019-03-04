#!/usr/bin/env python3
#
#   Copyright 2018 - The Android Open Source Project
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
import enum
from distutils.version import LooseVersion
import logging
import sys

from acts.controllers.android_device import AndroidDevice
from acts.libs import version_selector


class AndroidApi:
    OLDEST = 0
    MINIMUM = 0
    L = 21
    L_MR1 = 22
    M = 23
    N = 24
    N_MR1 = 25
    O = 26
    O_MR1 = 27
    P = 28
    LATEST = sys.maxsize
    MAX = sys.maxsize


class AndroidPlatform(enum.Enum):
    OLDEST = LooseVersion('0')
    MIN = OLDEST
    MINIMUM = OLDEST
    A = LooseVersion('1')
    B = LooseVersion('1.1')
    C = LooseVersion('1.5')
    D = LooseVersion('1.6')
    E = LooseVersion('2')
    F = LooseVersion('2.2')
    G = LooseVersion('2.3')
    H = LooseVersion('3')
    I = LooseVersion('4')
    J = LooseVersion('4.1')
    K = LooseVersion('4.4')
    L = LooseVersion('5')
    M = LooseVersion('6')
    N = LooseVersion('7')
    O = LooseVersion('8')
    P = LooseVersion('9')
    Q = LooseVersion('10')
    LATEST = LooseVersion('9999.9.9')
    MAX = LATEST
    MAXIMUM = LATEST


def classify_platform(version):
    """Returns enum of platform release corresponding to a release version id.

    Example, passing '5.1.8' to this function will return AndroidPlatform.L.

    Args:
        version (str): The id string composed of 1 or more integers
            joined by decimal points.
    Returns:
        min_release_id (int): The AndroidPlatform letter for this version.
    """
    # Find the 'bin' for this id number and return the platform id.
    min_release_id = AndroidPlatform.OLDEST
    loose_ver = LooseVersion(version)
    for enumeration in AndroidPlatform:
        if loose_ver < enumeration.value:
            return min_release_id
        min_release_id = enumeration
    return min_release_id


def android_api(min_api=AndroidApi.OLDEST,
                max_api=AndroidApi.LATEST):
    """Decorates a function to only be called for the given API range.

    Only gets called if the AndroidDevice in the args is within the specified
    API range. Otherwise, a different function may be called instead. If the
    API level is out of range, and no other function handles that API level, an
    error is raise instead.

    Note: In Python3.5 and below, the order of kwargs is not preserved. If your
          function contains multiple AndroidDevices within the kwargs, and no
          AndroidDevices within args, you are NOT guaranteed the first
          AndroidDevice is the same one chosen each time the function runs. Due
          to this, we do not check for AndroidDevices in kwargs.

    Args:
         min_api: The minimum API level. Can be an int or an AndroidApi value.
         max_api: The maximum API level. Can be an int or an AndroidApi value.
    """
    def get_api_level(*args, **_):
        for arg in args:
            if isinstance(arg, AndroidDevice):
                return arg.sdk_api_level()
        logging.getLogger().error('An AndroidDevice was not found in the given '
                                  'arguments.')

    return version_selector.set_version(get_api_level, min_api, max_api)


def android_platform(min_platform=AndroidPlatform.OLDEST,
                     max_platform=AndroidPlatform.LATEST):
    """Decorates a function to only be called for the given platform range.

    Only gets called if the AndroidDevice in the args is within the specified
    platform version range. Otherwise, a different function may be called
    instead. If the platform level is out of range, and no other function
    handles that level, an error is raised.

    Note: In Python3.5 and below, the order of kwargs is not preserved. If your
          function contains multiple AndroidDevices within the kwargs, and no
          AndroidDevices within args, you are NOT guaranteed the first
          AndroidDevice is the same one chosen each time the function runs. Due
          to this, we do not check for AndroidDevices in kwargs.

    Args:
         min_platform: The minimum platform level. Can be an int, float, or an
            AndroidPlatform value.
         max_platform: The maximum platform level. Can be an int, float, or an
            AndroidPlatform value.
    """
    def get_platform_enumeration_value(*args, **_):
        for arg in args:
            if isinstance(arg, AndroidDevice):
                platform = arg.adb.shell('getprop ro.build.version.release')
                # The above adb command can return a letter or version id.
                # If it's a letter, we can getattr from AndroidPlatform, but if
                # it's a version id we need to classify which platform it is.
                try:
                    return getattr(AndroidPlatform, platform.upper()).value
                except AttributeError:
                    return classify_platform(platform).value
        logging.getLogger().error('An AndroidDevice was not found in the given '
                                  'arguments.')

    return version_selector.set_version(get_platform_enumeration_value,
                                        min_platform.value,
                                        max_platform.value)
