# -*- coding: utf-8 -*-

import sys
from . import stdin
from .base import CursorBase
from .constants import *


_MODES_OFF = '\x1B[0m'  # Turn off character attributes
_LOW_INTENSITY = '\x1B[2m'  # Turn low intensity mode on
_BLINK = '\x1B[5m'  # Turn blinking mode on

_CURSOR_HOME = '\x1B[H'  # Move cursor to upper left corner
_CURSOR_POS = '\x1B[{y};{x}H'  # Move cursor to screen location v,h

_CURSOR_UP = '\x1B[{count}A'   # Move cursor up n lines
_CURSOR_DOWN = '\x1B[{count}B'  # Move cursor down n lines
_CURSOR_RIGHT = '\x1B[{count}C'  # Move cursor right n lines
_CURSOR_LEFT = '\x1B[{count}D'  # Move cursor left n lines

_CLEAR_TO_EOL = '\x1B[0K'  # Clear line from cursor right
_CLEAR_LINE = '\x1B[2K'  # Clear entire line

_GET_CURSOR = '\x1B[6n'  # Get cursor position


_COLOR_XREF = {
    FOREGROUND_DARK_BLACK: '\x1B[30m',
    FOREGROUND_DARK_RED: '\x1B[31m',
    FOREGROUND_DARK_GREEN: '\x1B[32m',
    FOREGROUND_DARK_BLUE: '\x1B[34m',
    FOREGROUND_DARK_YELLOW: '\x1B[33m',
    FOREGROUND_DARK_MAGENTA: '\x1B[35m',
    FOREGROUND_DARK_CYAN: '\x1B[36m',
    FOREGROUND_DARK_WHITE: '\x1B[37m',
    FOREGROUND_BRIGHT_BLACK: '\x1B[30m;1m',
    FOREGROUND_BRIGHT_RED: '\x1B[31m;1m',
    FOREGROUND_BRIGHT_GREEN: '\x1B[32m;1m',
    FOREGROUND_BRIGHT_BLUE: '\x1B[34m;1m',
    FOREGROUND_BRIGHT_YELLOW: '\x1B[33m;1m',
    FOREGROUND_BRIGHT_MAGENTA: '\x1B[35m;1m',
    FOREGROUND_BRIGHT_CYAN: '\x1B[36m;1m',
    FOREGROUND_BRIGHT_WHITE: '\x1B[37m;1m',
    BACKGROUND_DARK_BLACK: '\x1B[40m',
    BACKGROUND_DARK_RED: '\x1B[41m',
    BACKGROUND_DARK_GREEN: '\x1B[42m',
    BACKGROUND_DARK_BLUE: '\x1B[44m',
    BACKGROUND_DARK_YELLOW: '\x1B[43m',
    BACKGROUND_DARK_MAGENTA: '\x1B[45m',
    BACKGROUND_DARK_CYAN: '\x1B[46m',
    BACKGROUND_DARK_WHITE: '\x1B[47m',
    BACKGROUND_BRIGHT_BLACK: '\x1B[40m;1m',
    BACKGROUND_BRIGHT_RED: '\x1B[41m;1m',
    BACKGROUND_BRIGHT_GREEN: '\x1B[42m;1m',
    BACKGROUND_BRIGHT_BLUE: '\x1B[44m;1m',
    BACKGROUND_BRIGHT_YELLOW: '\x1B[43m;1m',
    BACKGROUND_BRIGHT_MAGENTA: '\x1B[45m;1m',
    BACKGROUND_BRIGHT_CYAN: '\x1B[46m;1m',
    BACKGROUND_BRIGHT_WHITE: '\x1B[47m;1m',
    BOLD: '\x1B[1m',
    UNDERSCORE: '\x1B[4m',
}


class Cursor(CursorBase):

    @property
    def handle(self):
        if self._std in (sys.__stderr__, sys.__stdout__):
            return self._std.fileno()

    def get_position(self):
        with self._lock:
            if self.handle is None:
                return

            stdin.start_read()
            self._std.write('\x1B[6n')
            self._std.flush()
            in_data = stdin.read()

            while 'R' not in in_data:
                in_data = stdin.read()

            stdin.end_read()

            if not in_data.endswith('R'):
                in_data = in_data.split('R', 1)[0] + 'R'
            y, x = list(int(item) for item in in_data[2:-1].split(';'))
            return x, y

    def set_position(self, new_x=None, new_y=None):
        with self._lock:
            if self.handle is None:
                return

            old_x, old_y = self.get_position()

            if new_x is None:
                new_x = old_x

            if new_y is None:
                new_y = old_y

            if (new_x, new_y) != (old_x, old_y):
                self._std.write(_CURSOR_POS.format(x=new_x, y=new_y))
                self._std.flush()

    def write(
        self,
        text,
        x=None,
        y=None,
        text_attributes=None,
    ):
        with self._lock:
            if self.handle is None:
                self._std.write(text)
                self._std.flush()
                return

            attr = ''

            if text_attributes is None and (self._color or self._bold or self._underscore):
                text_attributes = 0
                if self._bold:
                    text_attributes |= BOLD

                if self._underscore:
                    text_attributes |= UNDERSCORE

                if self._color:
                    text_attributes |= self._color

            if text_attributes is not None:
                if text_attributes & BOLD:
                    text_attributes ^= BOLD
                    attr += _COLOR_XREF[BOLD]
                elif self._bold:
                    attr += _COLOR_XREF[BOLD]

                if text_attributes & UNDERSCORE:
                    text_attributes ^= UNDERSCORE
                    attr += _COLOR_XREF[UNDERSCORE]
                elif self._underscore:
                    attr += _COLOR_XREF[UNDERSCORE]

                if text_attributes:
                    attr += _COLOR_XREF[text_attributes]
                elif self._color:
                    attr += _COLOR_XREF[self._color]

            self.set_position(x, y)
            if attr:
                self._std.write(attr)
                self._std.flush()

            self._std.write(text)
            self._std.flush()

            if attr:
                self._std.write(_MODES_OFF)
                self._std.flush()
