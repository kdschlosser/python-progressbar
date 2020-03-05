# -*- coding: utf-8 -*-

import sys
import ctypes
from ctypes.wintypes import (
    BOOL,
    HANDLE,
    DWORD,
    _COORD,
    WORD,
    SMALL_RECT,
)

from .base import CursorBase
from .constants import *

ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
STD_OUTPUT_HANDLE = -11
STD_ERROR_HANDLE = -12

COORD = _COORD
POINTER = ctypes.POINTER

kernel32 = ctypes.windll.Kernel32

GetStdHandle = kernel32.GetStdHandle
GetStdHandle.restype = HANDLE

# BOOL WINAPI SetConsoleCursorPosition(
#   _In_ HANDLE hConsoleOutput,
#   _In_ COORD  dwCursorPosition
# );
SetConsoleCursorPosition = kernel32.SetConsoleCursorPosition
SetConsoleCursorPosition.restype = BOOL

# BOOL WINAPI GetConsoleScreenBufferInfo(
#   _In_  HANDLE                      hConsoleOutput,
#   _Out_ PCONSOLE_SCREEN_BUFFER_INFO lpConsoleScreenBufferInfo
# );
GetConsoleScreenBufferInfo = kernel32.GetConsoleScreenBufferInfo
GetConsoleScreenBufferInfo.restype = BOOL


class _CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ('dwSize', COORD),
        ('dwCursorPosition', COORD),
        ('wAttributes', WORD),
        ('srWindow', SMALL_RECT),
        ('dwMaximumWindowSize', COORD)
    ]


CONSOLE_SCREEN_BUFFER_INFO = _CONSOLE_SCREEN_BUFFER_INFO


class _CONSOLE_CURSOR_INFO(ctypes.Structure):
    _fields_ = [
        ('dwSize', DWORD),
        ('bVisible', BOOL)
    ]


CONSOLE_CURSOR_INFO = _CONSOLE_CURSOR_INFO
PCONSOLE_CURSOR_INFO = POINTER(_CONSOLE_CURSOR_INFO)

# BOOL WINAPI GetConsoleCursorInfo(
#   _In_  HANDLE               hConsoleOutput,
#   _Out_ PCONSOLE_CURSOR_INFO lpConsoleCursorInfo
# );
GetConsoleCursorInfo = kernel32.GetConsoleCursorInfo
GetConsoleCursorInfo.restype = BOOL

# BOOL WINAPI SetConsoleCursorInfo(
#   _In_       HANDLE              hConsoleOutput,
#   _In_ const CONSOLE_CURSOR_INFO *lpConsoleCursorInfo
# );
SetConsoleCursorInfo = kernel32.SetConsoleCursorInfo
SetConsoleCursorInfo.restype = BOOL

# BOOL WINAPI SetConsoleTextAttribute(
#   _In_ HANDLE hConsoleOutput,
#   _In_ WORD   wAttributes
# );
SetConsoleTextAttribute = kernel32.SetConsoleTextAttribute
SetConsoleTextAttribute.restype = BOOL


class Cursor(CursorBase):

    @property
    def handle(self):
        if self._std == sys.__stderr__:
            return GetStdHandle(DWORD(STD_ERROR_HANDLE))

        if self._std == sys.__stdout__:
            return GetStdHandle(DWORD(STD_OUTPUT_HANDLE))

    def get_position(self):
        with self._lock:
            if self.handle is None:
                return

            lpConsoleScreenBufferInfo = CONSOLE_SCREEN_BUFFER_INFO()
            GetConsoleScreenBufferInfo(
                self._handle,
                ctypes.byref(lpConsoleScreenBufferInfo)
            )
            return (
                lpConsoleScreenBufferInfo.dwCursorPosition.X,
                lpConsoleScreenBufferInfo.dwCursorPosition.Y
            )

    def set_position(self, new_x=None, new_y=None):
        with self._lock:
            if self.handle is None:
                return

            old_x, old_y = self.get_position()

            if new_x is None:
                new_x = old_x

            if new_y is None:
                new_y = old_y

            coord = COORD()
            coord.X = new_x
            coord.Y = new_y
            SetConsoleCursorPosition(self._handle, coord)

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

            if text_attributes is None:
                text_attributes = 0

                if self._underscore:
                    text_attributes |= UNDERSCORE

                if self._color:
                    text_attributes |= self._color

            if text_attributes & BOLD:
                text_attributes ^= BOLD

            if not text_attributes & UNDERSCORE and self._underscore:
                text_attributes |= UNDERSCORE

            if (text_attributes == 0 or text_attributes == UNDERSCORE) and self._color:

                text_attributes |= self._color

            self.set_position(x, y)
            SetConsoleTextAttribute(self._handle, WORD(text_attributes))

            self._std.write(text)
            self._std.flush()

            if text_attributes != 0:
                SetConsoleTextAttribute(self._handle, WORD(0))
