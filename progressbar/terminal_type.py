# -*- coding: utf-8 -*-

import os
import sys
import re


ANSI_TERMS = (
    '([xe]|bv)term',
    '(sco)?ansi',
    'cygwin',
    'konsole',
    'linux',
    'rxvt',
    'screen',
    'tmux',
    'vt(10[02]|220|320)',
)
ANSI_TERM_RE = re.compile('^({})'.format('|'.join(ANSI_TERMS)), re.IGNORECASE)


def is_ansi_terminal(handle):
    is_ansi = False

    if handle in (sys.__stdout__, sys.__stderr__):
        # This works for newer versions of pycharm only. older versions there
        # is no way to check.
        if (
            'PYCHARM_HOSTED' in os.environ and
            os.environ['PYCHARM_HOSTED'] == '1'
        ):
            is_ansi = True

        elif 'JPY_PARENT_PID' in os.environ:
            is_ansi = True

    # check if we are writing to a terminal or not. typically a file object is
    # going to return False if the instance has been overridden and isatty has
    # not been defined we have no way of knowing so we will not use ansi.
    # ansi terminals will typically define one of the 2 environment variables.

    if (
        hasattr(handle, "isatty") and handle.isatty() and (
            ANSI_TERM_RE.match(os.environ.get('TERM', '')) or
            'ANSICON' in os.environ
        )
    ):
        is_ansi = True

    return is_ansi


def is_windows_terminal(handle):
    return (
        not is_ansi_terminal(handle) and
        (
            sys.platform.startswith('win') and
            hasattr(handle, "isatty") and
            handle.isatty()
        )
    )

