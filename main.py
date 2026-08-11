#!/usr/bin/env python3
"""Entry point: `python main.py <command>`.

Adds src/ to the import path so the project runs from a clone with no install
step, then hands over to pd.cli.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from pd.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
