#!/usr/bin/env python3.4
#
#   Copyright 2016 - The Android Open Source Project
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

import logging
import os
import sys
from acts.libs.proc import job

COMMIT_KEYWORDS_FILEPATH = '../../../../../master/vendor/google_testing/' \
                           'comms/framework/etc/commit_keywords'

FIND_COMMIT_KEYWORDS = 'git log @{u}..| grep -i %s'
GET_EMAIL_ADDRESS = 'git log --format=%ce -1'


def main(argv):
    file_path = os.path.join(
        os.path.dirname(__file__), COMMIT_KEYWORDS_FILEPATH)

    if not os.path.isfile(file_path):
        logging.error('No file "{}" found.'.format(file_path))
        exit(0)

    grep_args = ''

    with open(file_path) as file:
        keyword_list = file.read().splitlines()

    for keyword in keyword_list:
        grep_args = grep_args + '-e "' + keyword + '" '

    result = job.run(FIND_COMMIT_KEYWORDS % grep_args, ignore_status=True)

    if result.stderr:
        logging.error(result.stderr)
        exit(1)

    if result.stdout:
        logging.error('Your commit message contains at least one keyword.')
        logging.error('Keyword(s) found:')
        logging.error(result.stdout)
        logging.error('Please fix/remove these before committing.')
        exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
