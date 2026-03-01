import os
import sys
import time
from engine import GameEngine

def main():
    try:
        engine = GameEngine()
        engine.run()
    except KeyboardInterrupt:
        print("\nGame Over: Calculation Interrupted.")
        sys.exit(0)

if __name__ == "__main__":
    main()
