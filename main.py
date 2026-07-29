"""Example entry point.

Kept as a thin shim for ``python main.py``; the real logic lives in
``geosocialpy.cli`` and is also installed as the ``geosocialpy`` console script.
Run ``python main.py --help`` for options.
"""

import sys

from geosocialpy.cli import main

if __name__ == "__main__":
    sys.exit(main())
