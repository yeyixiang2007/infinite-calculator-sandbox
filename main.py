import os
import sys
import time
from engine import GameEngine

def main():
    old_settings = None
    if os.name != 'nt':
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        new_settings = termios.tcgetattr(fd)
        # Disable echo and canonical mode (line buffering)
        new_settings[3] = new_settings[3] & ~termios.ECHO & ~termios.ICANON
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)

    try:
        engine = GameEngine()
        engine.run()
    except KeyboardInterrupt:
        print("\nGame Over: Calculation Interrupted.")
    finally:
        if old_settings:
            import termios
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        sys.exit(0)

if __name__ == "__main__":
    main()
