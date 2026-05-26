#!/usr/bin/env python3
"""Thin wrapper for the local Falsiflow CLI."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from falsiflow.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
