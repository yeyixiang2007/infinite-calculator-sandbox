import os
import sys
import time
from engine import GameEngine
import input_handler as input_h

def main():
    # Initialize input handler (sets raw mode on Linux for proper input handling)
    input_h.init()

    try:
        engine = GameEngine()
        engine.run()
    except KeyboardInterrupt:
        print("\nGame Over: Calculation Interrupted.")
    finally:
        # Restore terminal settings
        input_h.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
