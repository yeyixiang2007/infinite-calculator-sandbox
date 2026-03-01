import sys
import os

# Global buffer for multi-byte sequences
_key_buffer = []

if os.name == 'nt':
    import msvcrt

    def init():
        """Initialize input handling (no-op on Windows)"""
        pass

    def cleanup():
        """Cleanup input handling (no-op on Windows)"""
        pass

    def kbhit():
        return msvcrt.kbhit()

    def getch():
        return msvcrt.getch()

else:
    import termios
    import tty
    import select
    import time

    _old_settings = None

    def init():
        """Set terminal to raw mode"""
        global _old_settings
        try:
            fd = sys.stdin.fileno()
            _old_settings = termios.tcgetattr(fd)
            # Use cbreak mode instead of raw for slightly better behavior on some shells
            tty.setcbreak(fd)
        except Exception:
            pass

    def cleanup():
        """Restore terminal settings"""
        global _old_settings
        if _old_settings:
            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, _old_settings)
            except Exception:
                pass

    def kbhit():
        if _key_buffer:
            return True
        # Check if data is available on stdin file descriptor
        r, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(r)

    def getch():
        global _key_buffer
        if _key_buffer:
            return _key_buffer.pop(0)

        fd = sys.stdin.fileno()

        try:
            # Read 1 byte
            b = os.read(fd, 1)
            if not b:
                return b''

            # ESC sequence
            if b == b'\x1b':
                # Check if there's more data (timeout 0.1s)
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not r:
                    return b'\x1b' # Just ESC key

                # Read the rest of the sequence
                seq = ""
                while True:
                    r, _, _ = select.select([sys.stdin], [], [], 0.01)
                    if r:
                        b_next = os.read(fd, 1)
                        if not b_next: break
                        c = b_next.decode('latin-1')
                        seq += c
                        # End of sequence markers
                        if c.isalpha() or c == '~':
                            break
                    else:
                        break

                # Map ANSI escape sequences to Windows-style msvcrt bytes
                # Arrow keys
                if seq == '[A' or seq == 'OA': # Up
                    _key_buffer.append(b'H')
                    return b'\xe0'
                elif seq == '[B' or seq == 'OB': # Down
                    _key_buffer.append(b'P')
                    return b'\xe0'
                elif seq == '[C' or seq == 'OC': # Right
                    _key_buffer.append(b'M')
                    return b'\xe0'
                elif seq == '[D' or seq == 'OD': # Left
                    _key_buffer.append(b'K')
                    return b'\xe0'

                return b'\x1b' # Unrecognized sequence

            return b
        except Exception:
            return b''

    def get_input():
        if kbhit():
            return getch()
        return None
