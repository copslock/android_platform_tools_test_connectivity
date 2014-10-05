# python3.4
# Copyright (C) 2009 Google Inc.
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

import argparse
import concurrent.futures
import json
import os
import subprocess
import threading
import time
import traceback

import android_device
from test_utils.utils import create_dir
from test_utils.utils import find_files

cmd_fetch_latest = ("/google/data/ro/projects/android/fetch_artifact --latest "
                    "--branch {branch} --target {target} '*-{type}-*.zip'")
cmd_fetch_bid = ("/google/data/ro/projects/android/fetch_artifact --bid {bid} "
                 "--branch {branch} --target {target} '*-{type}-*.zip'")
wipe = False

class FetchError(Exception):
  pass

def exe_cmd(*cmds):
  cmd = ' '.join(cmds)
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  (out, err) = proc.communicate()
  if not err:
    return out
  raise Exception(err)

def exec_tool_with_serial(tool, cmd, serial=None):
  tool_cmd = None
  if serial:
    tool_cmd = ' '.join((tool, "-s", serial, cmd))
  else:
    tool_cmd = ' '.join((tool, cmd))
  return exe_cmd(tool_cmd)

def exec_adb(cmd, serial=None):
  return exec_tool_with_serial("adb", cmd, serial)

def exec_fastboot(cmd, serial=None):
  return exec_tool_with_serial("fastboot", cmd, serial)

def skip_setup_wizard(serial):
  exec_adb("root", serial)
  exec_adb("wait-for-device", serial)
  exec_adb("remount", serial)
  exec_adb(("shell am start -n com.google.android.setupwizard/"
            ".SetupWizardExitActivity"), serial)

def _fetch_file(cmd_str, params):
  exe_cmd(cmd_str.format(**params))
  target = params["target"].split('-')[0]
  files = os.listdir('.')
  for f in files:
    if f.endswith(".zip") and target in f and params["type"] in f:
      fname = f.split('.')[0]
      tokens = fname.split('-')
      dir_name = ''.join((tokens[0], '-', tokens[2]))
      if dir_name in files:
        exe_cmd("rm -rf " + dir_name)
      create_dir(dir_name)
      exe_cmd(' '.join(("mv", f, dir_name)))
      print(' '.join(("Fetched", f, "at", dir_name)))
      return dir_name, f

def wait_for_boot_completion(serial):
  print(' '.join(("Waiting for", serial, "to finish booting...")))
  timeout = time.time() + 60*15 # wait for 15 minutes
  while True:
    completed = exec_adb(("shell getprop "
                        "sys.boot_completed"), serial).decode('utf-8').strip()
    if completed == '1':
      return True
    if time.time() > timeout:
      print(' '.join(("Error: waiting for", serial, "to boot timed out.")))
      return False
    time.sleep(20)
  print(serial + " finished booting.")

# Mock for _fetch_file.
# def _fetch_file(cmd_str, params):
#   return '.', "hammerhead-img-1393691.zip"

def find_devices(target):
  results = []
  android_devices = android_device.get_all_instances()
  for a in android_devices:
    if a.get_model().lower() == target.lower():
      results.append(a.device_id)
  return results

def unzip(path, fname):
  fpath = '/'.join((path, fname))
  dest = '/'.join((path, fname.split('.')[0]))
  exe_cmd("unzip -o {} -d {}".format(fpath, dest))
  return dest

def exe_concurrent(func, param_list):
  with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    # Start the load operations and mark each future with its URL
    future_to_params = {executor.submit(func, *p): p for p in param_list}
    for future in concurrent.futures.as_completed(future_to_params):
        params = future_to_params[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s'
                   % (params, traceback.format_exc()))
        else:
            print('%r executed successfully: %s' % (params, data))

def flash_build(img_path, serial, stand_alone=False):
  img_list = ["boot", "system"]
  if stand_alone:
    img_list = find_files([img_path], lambda name, ext : ext == ".img")
  exec_adb("reboot bootloader", serial)
  if wipe:
    exec_fastboot("-w", serial)
  for f in img_list:
    cmd = ''.join(("flash ", f, " ", img_path, "/", f, ".img"))
    exec_fastboot(cmd, serial)
  exec_fastboot("reboot", serial)

def load_sl4a(tests_path, serial):
  wait_for_boot_completion(serial)
  skip_setup_wizard(serial)
  sl4a_path = '/'.join((tests_path, "DATA", "priv-app", "sl4a", "sl4a.apk"))
  exe_cmd("adb -s {} install -r {}".format(serial, sl4a_path))

def fetch_and_load(fetch_cmd, fetch_params, load_func):
  path, zip_name = _fetch_file(fetch_cmd, fetch_params)
  file_path = unzip(path, zip_name)
  fname = zip_name.split('.')[0]
  device_type, _, build_number = fname.split('-')
  device_serials = find_devices(device_type)
  flash_list =  [(file_path, s) for s in device_serials]
  out_info = {"path": file_path,
              "serials": device_serials,
              "build": build_number,
              "target": device_type}
  info_fname = ''.join((device_type, '_', fetch_params["branch"], ".info"))
  with open(info_fname, 'w') as out_f:
    json.dump(out_info, out_f)
  exe_concurrent(load_func, flash_list)

def fetch_flash_and_load(target, branch):
  fetch_and_flash(target, branch)
  fetch_and_load_sl4a(target, branch)

def fetch_and_flash(target, branch):
  img_param = {"target": target, "branch": branch, "type": "img"}
  fetch_and_load(cmd_fetch_latest, img_param, flash_build)

def fetch_and_load_sl4a(target, branch):
  info = None
  target_name, *_ = target.split('-')
  info_fname = ''.join((target_name, '_', branch, '.info'))
  with open(info_fname, 'r') as info_f:
    info = json.load(info_f)
  fetch_tests_param = {"bid": info["build"],
                       "branch": branch,
                       "target": target,
                       "type": "tests"}
  fetch_and_load(cmd_fetch_bid, fetch_tests_param, load_sl4a)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=("Flash all authorized devices "
                  "discoverable through adb to the latest build of a branch."
                  "To use, you need to have ACTS setup and have prodaccess."))
  parser.add_argument('-b', '--branch', nargs=1, type=str,
                        help=("The branch to flash, default is lmp-release."))
  parser.add_argument('-bt', '--buildtype', nargs=1, type=str,
                        help=("Type of the build to flash, default is "
                              "userdebug."))
  parser.add_argument('-sl4a', '--loadsl4a', action="store_true",
                        help=("After flashing, run the script again with this "
                              "tag to load sl4a to the devices."))
  parser.add_argument('-fo', '--flashonly', type=str,
                        help=("Flash images found in the specified dir to "
                              "a device."))
  parser.add_argument('-ff', '--fetchflash', type=str,
                        help=("Fetch images and flash them without loading "
                              "sl4a."))
  parser.add_argument('-w', '--wipe', action="store_true",
                        help="Wipe the devices before flashing.")
  parser.add_argument('-sw', '--skipwizard', action="store_true",
                        help=("Skip the setup wizard on a currently connected "
                              "device."))
  args = parser.parse_args()

  # Default values of build_type and branch
  build_type = "-userdebug"
  branch = "lmp-release"

  if args.wipe:
    wipe = True
  if args.flashonly:
    flash_build(args.flashonly, None, True)
    exit(0)
  if args.skipwizard:
    skip_setup_wizard(None)
    exit(0)
  if args.buildtype:
    build_type = '-' + args.buildtype[0]
  if args.branch:
    branch = args.branch[0]
  targets = {}
  android_devices = android_device.get_all_instances()
  for a in android_devices:
    model = a.get_model()
    targets[model] = (model + build_type, branch)
  target_builds = list(targets.values())

  if args.loadsl4a:
    exe_concurrent(fetch_and_load_sl4a, target_builds)
  elif args.fetchflash:
    exe_concurrent(fetch_and_flash, target_builds)
  else:
    exe_concurrent(fetch_flash_and_load, target_builds)
