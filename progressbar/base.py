# -*- mode: python; coding: utf-8 -*-
from __future__ import absolute_import
import six
import threading


class FalseMeta(type):
    def __bool__(self):  # pragma: no cover
        return False

    def __cmp__(self, other):  # pragma: no cover
        return -1

    __nonzero__ = __bool__


class UnknownLength(six.with_metaclass(FalseMeta, object)):
    pass


# Terminal size methods.
# there are several different ways to obtain the terminal size.
# each of these ways works depending on OS and python flavor. when the Cursor
# instance is constructed it will test and discover the way that works. once
# this discovery is done the method that works is stored and that method is
# what gets called from then on out.


def _GetConsoleScreenBufferInfo(handle):
    import ctypes
    from .windows_cursor import (
        CONSOLE_SCREEN_BUFFER_INFO,
        GetConsoleScreenBufferInfo
    )

    lpConsoleScreenBufferInfo = CONSOLE_SCREEN_BUFFER_INFO()
    GetConsoleScreenBufferInfo(
        handle,
        ctypes.byref(lpConsoleScreenBufferInfo)
    )
    return (
        lpConsoleScreenBufferInfo.dwSize.X,
        lpConsoleScreenBufferInfo.dwSize.Y
    )


def _ioctl_GWINSZ(handle):
    import fcntl
    import termios
    import struct
    import os

    fd_size = struct.unpack('hh', fcntl.ioctl(handle, termios.TIOCGWINSZ, '1234'))

    if fd_size:
        return int(fd_size[1]), int(fd_size[0])

    raise Exception


def _ipykernel(_):
    # Default to 79 characters for IPython notebooks
    ipython = globals().get('get_ipython')()
    from ipykernel import zmqshell

    if isinstance(ipython, zmqshell.ZMQInteractiveShell):
        return 79, 24

    raise Exception


def _shutil(_):
    # This works for Python 3, but not Pypy3. Probably the best method if
    # it's supported so let's always try
    import shutil

    w, h = shutil.get_terminal_size()
    if w and h:
        # The off by one is needed due to progressbars in some cases, for
        # safety we'll always substract it.
        return w - 1, h

    raise Exception


def _blessings(_):
    import blessings

    terminal = blessings.Terminal()
    w = terminal.width
    h = terminal.height
    return w, h


def _cygwin(_):
    # needed for window's python in cygwin's xterm!
    # get terminal width src: http://stackoverflow.com/questions/263890/
    import subprocess

    proc = subprocess.Popen(
        ['tput', 'cols'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output = proc.communicate()
    w = int(output[0])

    proc = subprocess.Popen(
        ['tput', 'lines'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output = proc.communicate()
    h = int(output[0])

    return w, h


def _os(_):
    import os

    w = int(os.environ.get('COLUMNS'))
    h = int(os.environ.get('LINES'))
    return w, h


def _default():
    return 79, 24


class CursorBase(object):

    def __init__(self, std):
        self._lock = threading.RLock()
        self._std = std

        self._handle = std.fileno()
        self._bold = False
        self._underscore = False
        self._color = None
        # we now call _get_size to set the method for getting the terminal size
        self.get_size()

    @property
    def handle(self):
        raise NotImplementedError

    def fileno(self):
        return self._std.fileno()

    def isatty(self):
        return self._std.isatty()

    def flush(self):
        self._std.flush()

    def get_position(self):
        raise NotImplementedError

    def set_position(self, new_x=None, new_y=None):
        raise NotImplementedError

    @property
    def width(self):
        return self.get_size()[0]

    @property
    def height(self):
        return self.get_size()[1]

    @property
    def x(self):
        position = self.get_position()

        if position is not None:
            return position[0]

    @x.setter
    def x(self, value):
        self.set_position(new_x=value)

    @property
    def y(self):
        position = self.get_position()

        if position is not None:
            return position[1]

    @y.setter
    def y(self, value):
        self.set_position(new_y=value)

    def get_size(self):
        """
        Get the current size of your terminal

        Multiple returns are not always a good idea, but in this case it greatly
        simplifies the code so I believe it's justified. It's not the prettiest
        function but that's never really possible with cross-platform code.

        Returns:
            width, height: Two integers containing width and height
        """

        with self._lock:
            if self.handle is None:
                self.get_size = _default
                return _default()

            funcs = [
                _ipykernel,
                _shutil,
                _blessings,
                _cygwin,
                _GetConsoleScreenBufferInfo,
                _ioctl_GWINSZ,
                _os,
            ]

            # this is where we test each of the methods to see which one works
            for func in funcs:
                # we use the try: except: here instead of in each method
                # because they are expensive to use. and there really is no
                # need to use them in the method once we discover that method
                # works.
                try:
                    w, h = func()
                except:
                    continue

                if not w and not h:
                    continue

                # we create a wrapper for the method. we do this so that the
                # threading.Lock instance does not get called a bunch of times
                # calls to a threading.Lock object are expensive.
                def wrapper():
                    with self._lock:
                        return func(self.handle)

                # we then set self._get_size to the method that works so
                # testing each of these ways each and every time we want to
                # get the terminal size does not get happen.
                self.get_size = wrapper

                return w, h

            self.get_size = _default
            return _default()

    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value

    @property
    def underscore(self):
        return self._underscore

    @underscore.setter
    def underscore(self, value):
        self._underscore = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value

    def write(
            self,
            text,
            x=None,
            y=None,
            text_attributes=None,
    ):
        raise NotImplementedError



