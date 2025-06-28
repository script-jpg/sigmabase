"""Auto-append new knowledge files to ``facts.pl``."""

from __future__ import annotations

import re
import time
from pathlib import Path
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Directory containing knowledge files
KNOWLEDGE_DIR = Path(__file__).with_name("files")
# Facts file to update
FACTS_FILE = Path(__file__).with_name("facts.pl")

NOTE_RE = re.compile(r"note\([^,]+,\s*'([^']+)'\)\.")

def format(name: str) -> str:
    """Converts to snake case and then prepends 'nn' if result doesn't start with lowercase letter."""
    assert name
    LOWER_CASE = re.compile(r"[a-z]")
    to_snake_case = lambda s: re.sub(r"\W+", "_", s).strip("_").lower()
    append_nn = lambda s: "nn_" + s if not LOWER_CASE.match(s[0]) else s
    return append_nn(to_snake_case(name)) 


def load_known_files() -> set[str]:
    """Return set of file paths already referenced in facts.pl."""
    known: set[str] = set()
    if FACTS_FILE.exists():
        for line in FACTS_FILE.read_text().splitlines():
            m = NOTE_RE.match(line.strip())
            if m:
                known.add(m.group(1))
    return known


def append_note(file_name: str) -> None:
    """Append a note line for the given file name."""
    note_name = format(Path(file_name).stem)
    entry = f"note({note_name}, 'files/{file_name}').\n"
    with FACTS_FILE.open("a") as f:
        f.write(entry)
    print(f"Appended: {entry.strip()}")


def sync_existing(known: set[str]) -> None:
    """Ensure ``facts.pl`` has entries for all existing files."""
    for path in KNOWLEDGE_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith("._") or path.name == ".DS_Store":
            continue
        rel = f"files/{path.name}"
        if rel not in known:
            append_note(path.name)
            known.add(rel)


class Handler(FileSystemEventHandler):
    """Watchdog handler that appends facts on new files."""

    def __init__(self, known: set[str]):
        self.known = known

    def on_created(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.name.startswith("._") or file_path.name == ".DS_Store":
            return
        rel = f"files/{file_path.name}"
        if rel not in self.known:
            append_note(file_path.name)
            self.known.add(rel)


def main() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    known = load_known_files()
    sync_existing(known)

    print(f"Watching {KNOWLEDGE_DIR} for new files. Press Ctrl+C to stop.")
    observer = Observer()
    observer.schedule(Handler(known), str(KNOWLEDGE_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
