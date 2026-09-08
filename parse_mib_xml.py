#!/usr/bin/env python3
"""Standalone entry. Defaults: mib-xml/ in, entities/ out. Optional -i / -o."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mibxml.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
