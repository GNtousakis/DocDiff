"""PyInstaller / double-click entry point."""
import sys

from docdiff.app import main

if __name__ == "__main__":
    sys.exit(main())
