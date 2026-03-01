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

    _old_settings = None

    def init():
        """Set terminal to raw mode"""
        global _old_settings
        try:
            fd = sys.stdin.fileno()
            _old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
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
            # Read 1 byte directly from file descriptor to bypass Python buffering
            # This is blocking if no data, but usually called after kbhit()
            # or we want it to block if we are waiting for input.
            # However, for the game loop, we rely on kbhit.
            # If kbhit is false, engine loop continues.
            # If kbhit is true, we read.

            # Using os.read instead of sys.stdin.read for raw mode reliability
            b = os.read(fd, 1)
            if not b:
                return b''

            ch = b.decode('latin-1') # Decode raw byte

            if ch == '\x1b':
                # Escape sequence started
                seq = ""
                # Try to read rest of sequence with a short timeout
                import time
                start = time.time()
                while time.time() - start < 0.05:
                    r, _, _ = select.select([sys.stdin], [], [], 0)
                    if r:
                        b_next = os.read(fd, 1)
                        if b_next:
                            c = b_next.decode('latin-1')
                            seq += c
                            # Common sequence terminators
                            if c.isalpha() or c == '~':
                                break
                    else:
                        # If we have a partial sequence like '[', wait a bit more?
                        # But 0.05s is plenty for local terminal.
                        pass

                # Parse sequence
                # Arrow keys: ^[[A, ^[OA, ^[A
                if seq.endswith('A'): # Up
                    _key_buffer.append(b'H')
                    return b'\xe0'
                elif seq.endswith('B'): # Down
                    _key_buffer.append(b'P')
                    return b'\xe0'
                elif seq.endswith('C'): # Right
                    _key_buffer.append(b'M')
                    return b'\xe0'
                elif seq.endswith('D'): # Left
                    _key_buffer.append(b'K')
                    return b'\xe0'

                # Unhandled sequence or just ESC
                return b'\x1b'

            return b
        except Exception:
            return b''

    def get_input():
        if kbhit():
            return getch()
        return None
