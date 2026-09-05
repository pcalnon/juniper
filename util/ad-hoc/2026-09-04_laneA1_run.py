#!/usr/bin/env python3
"""Runner for the Lane A1 independent-verification module (name starts with a digit)."""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
M = importlib.import_module("2026-09-04_laneA1_independent_verify")
getattr(M, sys.argv[1])(*sys.argv[2:])
