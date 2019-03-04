from acts.controllers.android_lib.android_api import AndroidPlatform
from acts.controllers.android_lib.android_api import android_platform


@android_platform(AndroidPlatform.OLDEST, AndroidPlatform.P)
def set_location_service(ad, new_state):
    """Set Location service on/off in Settings->Location

    Args:
        ad: android device object.
        new_state: new state for "Location service".
            If new_state is False, turn off location service.
            If new_state if True, set location service to "High accuracy".
    """
    ad.adb.shell("content insert --uri "
                 " content://com.google.settings/partner --bind "
                 "name:s:network_location_opt_in --bind value:s:1")
    ad.adb.shell("content insert --uri "
                 " content://com.google.settings/partner --bind "
                 "name:s:use_location_for_services --bind value:s:1")
    if new_state:
        ad.adb.shell("settings put secure location_providers_allowed +gps")
        ad.adb.shell("settings put secure location_providers_allowed +network")
    else:
        ad.adb.shell("settings put secure location_providers_allowed -gps")
        ad.adb.shell("settings put secure location_providers_allowed -network")


@android_platform(AndroidPlatform.Q, AndroidPlatform.LATEST)
def set_location_service(ad, new_state):
    """Set Location service on/off in Settings->Location

    Args:
        ad: android device object.
        new_state: new state for "Location service".
            If new_state is False, turn off location service.
            If new_state if True, set location service to "High accuracy".
    """
    ad.adb.shell("content insert --uri "
                 " content://com.google.settings/partner --bind "
                 "name:s:network_location_opt_in --bind value:s:1")
    ad.adb.shell("content insert --uri "
                 " content://com.google.settings/partner --bind "
                 "name:s:use_location_for_services --bind value:s:1")
    if new_state:
        ad.adb.shell("settings put secure location_mode 3")
    else:
        ad.adb.shell("settings put secure location_mode 0")