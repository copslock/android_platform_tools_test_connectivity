#!/usr/bin/env python
#
#   Copyright 2017 - The Android Open Source Project
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


class FakeResult(object):
    """A fake version of the object returned from ShellCommand.run. """

    def __init__(self, exit_status=1, stdout='', stderr=''):
        self.exit_status = exit_status
        self.stdout = stdout
        self.stderr = stderr


class MockShellCommand(object):
    """A fake ShellCommand object.

    Attributes:
        fake_result: a FakeResult object
    """

    def __init__(self, fake_result):
        self._fake_result = fake_result

    """Returns a FakeResult object.

    Args:
        Same as ShellCommand.run, but none are used in function

    Returns:
        The FakeResult object it was initalized with
    """

    def run(self, command, timeout=3600):
        return self._fake_result
