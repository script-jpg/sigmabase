#!/usr/bin/env python3
"""
run_services.py  –  launch filewatcher.py + neo4j_to_filesystem_watcher.py + simple HTTP server

Usage:
    python3 run_services.py          # serves cwd on :8000
"""

import subprocess
import sys
from pathlib import Path

WATCHER = Path(__file__).with_name("filewatcher.py")
NEO4J_WATCHER = Path(__file__).with_name("neo4j_to_filesystem_watcher.py")

def main() -> None:
    # start both watchers in the background
    watcher_proc = subprocess.Popen([sys.executable, str(WATCHER)])
    neo4j_proc = subprocess.Popen([sys.executable, str(NEO4J_WATCHER)])
    try:
        # run the blocking HTTP server in the foreground
        subprocess.run([sys.executable, "-m", "http.server", "8000"], check=False)
    finally:
        # ensure both watchers exit when the server stops / user hits Ctrl-C
        watcher_proc.terminate()
        neo4j_proc.terminate()
        watcher_proc.wait()
        neo4j_proc.wait()

if __name__ == "__main__":
    main()
