# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import os
import atexit


read_started = False

try:
    # Windows
    import msvcrt

    def _getch():
        return msvcrt.getch().decode('utf-8')

    def _kbhit():
        return msvcrt.kbhit()

    def end_read():
        pass

    def start_read():
        pass

except ImportError:
    # Posix (Linux, OS X)
    import termios

    # Save the terminal settings
    old_term = termios.tcgetattr(sys.stdin)

    def end_read():
        global read_started

        if read_started:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_term)

        read_started = False

    def _getch():
        return os.read(sys.stdin.fileno(), 1)

    def _kbhit():
        pass

    def start_read():
        new_term = termios.tcgetattr(sys.stdin)

        # New terminal setting unbuffered
        new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)
        new_term[6][termios.VMIN] = 0
        new_term[6][termios.VTIME] = 0
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_term)

        global read_started

        # Support normal-terminal reset at exit
        read_started = True


atexit.register(end_read)


def read():
    data = ''

    if sys.platform.startswith('win'):
        while _kbhit():
            data += _getch()
    else:
        key = _getch()
        while key is not None and len(key) > 0:
            data += key
            key = _getch()

    return data


# Test
if __name__ == "__main__":

    import time
    print('Testing for ANSI escape return value for cursor position.')
    print('sending ANSI code ' + repr('\x1B[6n'))
    print('press Spacebar to exit')

    start_read()
    sys.stdout.write('\x1B[6n')
    sys.stdout.flush()

    while True:
        in_data = read()
        if in_data:
            if len(in_data) == 1 and ord(in_data) == 32:  # Space
                break

            print(repr(in_data))
        else:
            time.sleep(0.1)

    end_read()
