#!/usr/bin/env python
#
#   copyright 2017 - the android open source project
#
#   licensed under the apache license, version 2.0 (the "license");
#   you may not use this file except in compliance with the license.
#   you may obtain a copy of the license at
#
#       http://www.apache.org/licenses/license-2.0
#
#   unless required by applicable law or agreed to in writing, software
#   distributed under the license is distributed on an "as is" basis,
#   without warranties or conditions of any kind, either express or implied.
#   see the license for the specific language governing permissions and
#   limitations under the license.


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
