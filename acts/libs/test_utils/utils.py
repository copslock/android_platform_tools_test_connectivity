#!/usr/bin/python3.4
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

#   Copyright 2014 - The Android Open Source Project
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

import json
import os
import subprocess
import time

def create_dir(path):
    """Creates a directory if it does not exist already.

    Params:
        path: The path of the directory to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def exe_cmd(*cmds):
  cmd = ' '.join(cmds)
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
  (out, err) = proc.communicate()
  if not err:
    return out
  raise Exception(err)

def get_current_human_time():
  """Returns the current time in human readable format.

  Returns:
  	The current time stamp in Month-Day-Year Hour:Min:Sec format.
  """
  return time.strftime("%m-%d-%Y %H:%M:%S ")

def find_files(paths, file_predicate):
    """Locate files whose names and extensions match the given predicate in
    the specified directories.

    Params:
        paths: A list of directory paths where to find the files.
        file_predicate: A function that returns True if the file name and
          extension are desired.

    Returns:
        A list of files that match the predicate.
    """
    file_list = []
    for path in paths:
        for dirPath, subdirList, fileList in os.walk(path):
            for fname in fileList:
                name, ext = os.path.splitext(fname)
                if file_predicate(name, ext):
                  fileFullPath = os.path.join(dirPath, fname)
                  file_list.append(name)
    return file_list

def load_config(file_full_path):
  """Loads a JSON config file.

  Returns:
  	A JSON object.
  """
  f = open(file_full_path, 'r')
  conf = json.load(f)
  f.close()
  return conf

def find_field(item_list, cond, comparator, target_field):
  """Finds the value of a field in a dict object that satisfies certain
  conditions.

  Params:
  	item_list: A list of dict objects.
  	cond: A param that defines the condition.
  	comparator: A function that checks if an dict satisfies the condition.
  	target_field: Name of the field whose value to be returned if an item
  		satisfies the condition.

  Returns:
  	Target value or None if no item satisfies the condition.
  """
  for item in item_list:
    if comparator(item, cond) and target_field in item:
      return item[target_field]
  return None
