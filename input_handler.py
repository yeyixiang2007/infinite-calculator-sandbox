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
        # Non-blocking read check
        if not select.select([sys.stdin], [], [], 0.05)[0]:
            return b''

        # We already disabled echo and canonical mode in main.py,
        # so read(1) should work as expected.
        ch = sys.stdin.read(1)

        # Handle escape sequences for arrow keys on Linux (\x1b[A, \x1b[[A, \x1bOA, etc.)
        if ch == '\x1b':
            # Escape sequence started
            seq = ""
            # Try to read up to 3 more characters of the sequence
            for _ in range(3):
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    c = sys.stdin.read(1)
                    seq += c
                    # Common endings for arrow keys
                    if c in 'ABCD':
                        break
                else:
                    break

            # Handle common sequences
            # [A, [[A, OA are all possible for "Up"
            if seq.endswith('A'): # Up
                _key_buffer.append(b'H')
                return b'\xe0'
            elif seq.endswith('B'): # Down
                _key_buffer.append(b'P')
                return b'\xe0'
            elif seq.endswith('D'): # Left
                _key_buffer.append(b'K')
                return b'\xe0'
            elif seq.endswith('C'): # Right
                _key_buffer.append(b'M')
                return b'\xe0'

            # If we didn't recognize it, we might have swallowed some chars
            return b'\x1b'

        return ch.encode('utf-8')

def get_input():
    if kbhit():
        return getch()
    return None
