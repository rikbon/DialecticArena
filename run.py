#!/usr/bin/env python3
"""
Dialectic Arena: Claude Code vs Google Antigravity
Root entry point script for running the orchestrator CLI.
"""

import sys
from pathlib import Path

# Ensure src is in python path
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from agent_orchestrator.cli import app

if __name__ == "__main__":
    app()
