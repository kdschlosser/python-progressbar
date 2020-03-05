# -*- coding: utf-8 -*-
import six
import threading
from . import terminal_type


# In order to make this library thread safe we have to ensure that
# only a single thread is able to write to a given file like object
# at a time. We have to think outside the box and what a user might
# try and do. I can see a user attempting to create multiple bars
# and passing the same file like object multiple times. Doing this
# would cause the library to look as tho it spewed data all over
# the place.

# so what I have created is an Instance Singleton this instance singleton
# checks if a file like object has been passed before and if it has not
# then we perform a few tests to see what exactly the object is and what
# mechanisms are supported for writing to it. Once we have that information
# we then know what class to construct.

# supported object types:
# Windows CMD shell
# Windows 3rd party shell with ANSI support
# NIX (Debian, Darwin, etc...) shell with ANSI support
# ANY other shell/terminal application that supports ANSI (including PyCharm)
# all other file like objects.

_instance_lock = threading.Lock()


class CursorMeta(type):
    def __init__(cls, name, bases, dct):
        super(CursorMeta, cls).__init__(name, bases, dct)
        cls._instances = {}

    def __call__(cls, std):
        with _instance_lock:
            if std not in cls._instances:
                if terminal_type.is_ansi_terminal(std):
                    from . import ansi_cursor
                    instance = ansi_cursor.Cursor(std)
                elif terminal_type.is_windows_terminal(std):
                    from . import windows_cursor
                    instance = windows_cursor.Cursor(std)
                else:
                    instance = super(CursorMeta, cls).__call__(std)

                cls._instances[std] = instance

            return cls._instances[std]


@six.add_metaclass(CursorMeta)
class Cursor(object):

    def __init__(self, std):
        self._lock = threading.RLock()
        self._std = std

    @property
    def handle(self):
        return self._std.fileno()

    def fileno(self):
        return self._std.fileno()

    def isatty(self):
        if hasattr(self._std, 'isatty'):
            return self._std.isatty()
        return False

    def flush(self):
        if hasattr(self._std, 'flush'):
            self._std.flush()

    def get_position(self):
        pass

    def set_position(self, new_x=None, new_y=None):
        pass

    @property
    def width(self):
        return 0

    @property
    def height(self):
        return 0

    @property
    def x(self):
        return None

    @x.setter
    def x(self, value):
        pass

    @property
    def y(self):
        return None

    @y.setter
    def y(self, value):
        pass

    def get_size(self):
        """
        Get the current size of your terminal

        Multiple returns are not always a good idea, but in this case it greatly
        simplifies the code so I believe it's justified. It's not the prettiest
        function but that's never really possible with cross-platform code.

        Returns:
            width, height: Two integers containing width and height
        """

        return 0, 0

    @property
    def bold(self):
        return False

    @bold.setter
    def bold(self, value):
        pass

    @property
    def underscore(self):
        return False

    @underscore.setter
    def underscore(self, value):
        pass

    @property
    def color(self):
        return None

    @color.setter
    def color(self, value):
        pass

    def write(
            self,
            text,
            x=None,
            y=None,
            text_attributes=None,
    ):
        with self._lock:
            self._std.write(text)
            self._std.flush()






