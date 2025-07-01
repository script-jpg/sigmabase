#!/usr/bin/env python3
"""
run_services.py  –  launch filewatcher.py + simple HTTP server

Usage:
    python3 run_services.py          # serves cwd on :8000
"""

import subprocess
import sys
from pathlib import Path

WATCHER = Path(__file__).with_name("filewatcher.py")

def main() -> None:
    # start the watcher in the background
    watcher_proc = subprocess.Popen([sys.executable, str(WATCHER)])
    try:
        # run the blocking HTTP server in the foreground
        subprocess.run([sys.executable, "-m", "http.server", "8000"], check=False)
    finally:
        # ensure the watcher exits when the server stops / user hits Ctrl-C
        watcher_proc.terminate()
        watcher_proc.wait()

if __name__ == "__main__":
    main()
