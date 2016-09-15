# Copyright 2016 - The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import enum
import os
import string

# safe characters for the shell (do not need quoting)
SHELL_QUOTING_WHITELIST = frozenset(string.ascii_letters + string.digits +
                                    '_-+=')


class _SplitCommandState(enum.IntEnum):
    """Enum of states that the split_command_line function can be in.

    STATE_BASIC: The normal and default parsing state.
    STATE_ESC: State when an escape character is encountered.
    STATE_SINGLEQUOTE: State when inside a single quoted block of text.
    STATE_DOUBLEQUOTE: State when inside a double quoted block of text.
    STATE_WHITESPACE: State when white space is encountered.
    """

    STATE_BASIC = 0
    STATE_ESC = 1
    STATE_SINGLEQUOTE = 2
    STATE_DOUBLEQUOTE = 3
    STATE_WHITESPACE = 4


def sh_escape(command):
    """
    Escape special characters from a command so that it can be passed
    as a double quoted (" ") string in a (ba)sh command.

    Args:
        command: the command string to escape.

    Returns:
        The escaped command string. The required englobing double
        quotes are NOT added and so should be added at some point by
        the caller.

    See also: http://www.tldp.org/LDP/abs/html/escapingsection.html
    """
    command = command.replace('\\', '\\\\')
    command = command.replace("$", r'\$')
    command = command.replace('"', r'\"')
    command = command.replace('`', r'\`')
    return command


def sh_quote_word(text, whitelist=SHELL_QUOTING_WHITELIST):
    r"""Quote a string to make it safe as a single word in a shell command.

    POSIX shell syntax recognizes no escape characters inside a single-quoted
    string.  So, single quotes can safely quote any string of characters except
    a string with a single quote character.  A single quote character must be
    quoted with the sequence '\'' which translates to:
        '  -> close current quote
        \' -> insert a literal single quote
        '  -> reopen quoting again.

    This is safe for all combinations of characters, including embedded and
    trailing backslashes in odd or even numbers.

    This is also safe for nesting, e.g. the following is a valid use:

        adb_command = 'adb shell %s' % (
                sh_quote_word('echo %s' % sh_quote_word('hello world')))

    Args:
        text: The string to be quoted into a single word for the shell.
        whitelist: Optional list of characters that do not need quoting.
                   Defaults to a known good list of characters.

    Returns:
        A string, possibly quoted, safe as a single word for a shell.
    """
    if all(c in whitelist for c in text):
        return text

    return "'%s'" % text.replace("'", r"'\''")


def split_command_line(command_line):
    """Splits a command line into an array.

    Splits up a command line string to execute a program into an array containing
    the command and all arguments.

    Example:
        'python my_test_file.py -h' -> ['python', 'my_test_file.py', '-h']

    Args:
        command_line: The command line to split.

    Returns:
        The split array.
    """

    arg_list = []
    arg = ''

    state = _SplitCommandState.STATE_BASIC

    for c in command_line:
        if state == _SplitCommandState.STATE_BASIC or state == _SplitCommandState.STATE_WHITESPACE:
            if c == '\\':  # Escape the next character
                state = _SplitCommandState.STATE_ESC
            elif c == r"'":  # Handle single quote
                state = _SplitCommandState.STATE_SINGLEQUOTE
            elif c == r'"':  # Handle double quote
                state = _SplitCommandState.STATE_DOUBLEQUOTE
            elif c.isspace():
                # Add arg to arg_list if we aren't in the middle of whitespace.
                if state != _SplitCommandState.STATE_WHITESPACE:
                    arg_list.append(arg)
                    arg = ''
                    state = _SplitCommandState.STATE_WHITESPACE
            else:
                arg = arg + c
                state = _SplitCommandState.STATE_BASIC
        elif state == _SplitCommandState.STATE_ESC:
            arg = arg + c
            state = _SplitCommandState.STATE_BASIC
        elif state == _SplitCommandState.STATE_SINGLEQUOTE:
            if c == r"'":
                state = _SplitCommandState.STATE_BASIC
            else:
                arg = arg + c
        elif state == _SplitCommandState.STATE_DOUBLEQUOTE:
            if c == r'"':
                state = _SplitCommandState.STATE_BASIC
            else:
                arg = arg + c

    if arg != '':
        arg_list.append(arg)
    return arg_list
