# -*- coding: utf-8 -*-

from __future__ import print_function
import sys

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
    import atexit
    from select import select

    fd = sys.stdin.fileno()

    # Save the terminal settings
    old_term = termios.tcgetattr(fd)

    def end_read():
        termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)
        atexit.unregister(end_read)

    def _getch():
        return sys.stdin.read(1)

    def _kbhit():
        dr, dw, de = select([sys.stdin], [], [], 0)
        return dr != []


    def start_read():
        new_term = termios.tcgetattr(fd)

        # New terminal setting unbuffered
        new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)

        # Support normal-terminal reset at exit
        atexit.register(end_read)


def read():
    data = ''

    while _kbhit():
        data += _getch()

    return data


# Test
if __name__ == "__main__":

    import time
    print('Testing for ANSI escape return value for cursor position.')
    print('sending ANSI code ' + repr('\x1B[6n'))
    print('Hit any key, or ESC to exit')

    start_read()
    sys.stdout.write('\x1B[6n')
    sys.stdout.flush()

    while True:
        in_data = read()
        if in_data:
            if len(in_data) == 1 and ord(in_data) == 27:  # ESC
                break

            print(repr(in_data))
        else:
            time.sleep(0.1)

    end_read()
