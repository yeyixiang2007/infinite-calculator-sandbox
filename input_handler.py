import sys
import os

_key_buffer = []

if os.name == 'nt':
    import msvcrt

    def kbhit():
        return msvcrt.kbhit()

    def getch():
        return msvcrt.getch()
else:
    import termios
    import tty
    import select

    def kbhit():
        if _key_buffer:
            return True
        return select.select([sys.stdin], [], [], 0)[0] == [sys.stdin]

    def getch():
        global _key_buffer
        if _key_buffer:
            return _key_buffer.pop(0)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)

            # Handle escape sequences for arrow keys on Linux
            if ch == '\x1b':
                # Check if there's more to read (non-blocking check)
                if select.select([sys.stdin], [], [], 0.01)[0]:
                    next_ch = sys.stdin.read(1)
                    if next_ch == '[':
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            dir_ch = sys.stdin.read(1)
                            # Map Linux arrow keys to msvcrt-style bytes
                            # Up: \x1b[A -> b'H'
                            # Down: \x1b[B -> b'P'
                            # Left: \x1b[D -> b'K'
                            # Right: \x1b[C -> b'M'
                            mapping = {'A': b'H', 'B': b'P', 'D': b'K', 'C': b'M'}
                            if dir_ch in mapping:
                                _key_buffer.append(mapping[dir_ch])
                                return b'\xe0'

            return ch.encode('utf-8')
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def get_input():
    if kbhit():
        return getch()
    return None
