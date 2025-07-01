#!/usr/bin/env python3
"""
run_services.py – launch filewatcher.py, neo4j_to_filesystem_watcher.py,
periodically run load_notes.sh every 10 s, and start a simple HTTP server.

Usage:
    python3 run_services.py          # serves cwd on :8000 and refreshes Neo4j ↔︎ files
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
WATCHER = HERE / "filewatcher.py"
NEO4J_WATCHER = HERE / "neo4j_to_filesystem_watcher.py"
LOAD_NOTES = HERE / "load_notes.sh"  # make sure this is executable (chmod +x)

# ── Periodic loader thread ────────────────────────────────────────────────────

def _periodic_loader(interval: int = 20) -> None:
    """Run load_notes.sh every *interval* seconds until the program exits."""
    while True:
        try:
            subprocess.run([str(LOAD_NOTES)], check=False)
        except FileNotFoundError:
            # fail fast if the script is missing so the user knows why
            sys.stderr.write(f"⚠️  {LOAD_NOTES} not found. Skipping…\n")
        time.sleep(interval)

# ── Main entry ────────────────────────────────────────────────────────────────

def main() -> None:
    # Start the periodic loader in the background (daemon thread so it stops
    # automatically when the main program exits).
    threading.Thread(target=_periodic_loader, daemon=True).start()

    # Launch both watchers in the background.
    watcher_proc = subprocess.Popen([sys.executable, str(WATCHER)])
    neo4j_proc = subprocess.Popen([sys.executable, str(NEO4J_WATCHER)])

    try:
        # Run the blocking HTTP server in the foreground.
        subprocess.run([sys.executable, "-m", "http.server", "8000"], check=False)
    finally:
        # Ensure both watchers exit when the server stops / user hits Ctrl‑C.
        watcher_proc.terminate()
        neo4j_proc.terminate()
        watcher_proc.wait()
        neo4j_proc.wait()

if __name__ == "__main__":
    main()
