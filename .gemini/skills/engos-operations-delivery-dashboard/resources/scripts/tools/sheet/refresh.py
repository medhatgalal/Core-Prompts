#!/usr/bin/env python3
"""One-command refresh from a plain shell, no agent involved: python3 tools/sheet/refresh.py [--yes] [--from-saved] [--target real|scratch]"""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.run([sys.executable, os.path.join(here, "..", "skill", "dashboard.py"), "refresh"] + sys.argv[1:]).returncode)
