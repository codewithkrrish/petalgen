"""Entry point: `python -m petalgen`."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
