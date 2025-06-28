"""Watch ``facts.pl`` and run ``viz`` from ``rules.pl`` when it changes."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

FACTS_FILE = Path(__file__).with_name("facts.pl")
RULES_FILE = Path(__file__).with_name("rules.pl")


def run_viz() -> None:
    """Invoke ``viz`` in ``rules.pl`` via SWI-Prolog."""
    subprocess.run([
        "swipl",
        "-q",
        "-s",
        str(RULES_FILE),
        "-g",
        "viz",
        "-t",
        "halt",
    ])


class Handler(FileSystemEventHandler):
    """Runs ``viz`` whenever ``facts.pl`` is modified."""

    def on_modified(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        if Path(event.src_path) == FACTS_FILE:
            print(f"{FACTS_FILE} changed, running viz...")
            run_viz()

    # Also handle newly created file (e.g. first run)
    def on_created(self, event) -> None:  # type: ignore[override]
        self.on_modified(event)


def main() -> None:
    observer = Observer()
    observer.schedule(Handler(), str(FACTS_FILE.parent), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
