"""Keep ``facts.pl`` in lock-step with the contents of the ``files`` folder.

Adds a note when a new file appears (created or moved in), rewrites the note
when a file is renamed inside the folder, and removes the note when a file is
deleted or moved out.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileMovedEvent,
    FileDeletedEvent,
)
from watchdog.observers import Observer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
KNOWLEDGE_DIR = Path(__file__).with_name("files")   # folder to watch
FACTS_FILE = Path(__file__).with_name("facts.pl")   # Prolog knowledge base

# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------
NOTE_RE = re.compile(r"note\([^,]+,\s*'([^']+)'\)\.")

LOWER_CASE = re.compile(r"[a-z]")


def _to_snake_case(s: str) -> str:
    return re.sub(r"\W+", "_", s).strip("_").lower()


def format(name: str) -> str:
    """Convert to snake_case; prepend 'nn_' if it doesn't start with a-z."""
    assert name
    snaked = _to_snake_case(name)
    return "nn_" + snaked if not LOWER_CASE.match(snaked[0]) else snaked


# ---------------------------------------------------------------------------
# facts.pl helpers
# ---------------------------------------------------------------------------
def load_known_files() -> set[str]:
    """Return a set of 'files/<name>' already present in facts.pl."""
    known: set[str] = set()
    if FACTS_FILE.exists():
        for line in FACTS_FILE.read_text().splitlines():
            m = NOTE_RE.match(line.strip())
            if m:
                known.add(m.group(1))
    return known


def append_note(file_name: str) -> None:
    """Append a note line for ``file_name`` to facts.pl."""
    note_name = format(Path(file_name).stem)
    entry = f"note({note_name}, 'files/{file_name}').\n"
    with FACTS_FILE.open("a") as f:
        f.write(entry)
    print(f"Appended: {entry.strip()}")


def remove_note(file_name: str) -> None:
    """Remove the note line whose second arg is 'files/<file_name>'."""
    target = f"files/{file_name}"
    if not FACTS_FILE.exists():
        return
    lines = FACTS_FILE.read_text().splitlines(keepends=True)
    with FACTS_FILE.open("w") as f:
        for line in lines:
            if target not in line:
                f.write(line)
    print(f"Removed: note(_, '{target}').")


def sync_existing(known: set[str]) -> None:
    """Ensure facts.pl has notes for every current file in the folder."""
    for path in KNOWLEDGE_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith(("._", ".DS_Store")):
            continue
        rel = f"files/{path.name}"
        if rel not in known:
            append_note(path.name)
            known.add(rel)


# ---------------------------------------------------------------------------
# Watchdog handler
# ---------------------------------------------------------------------------
class Handler(FileSystemEventHandler):
    """Respond to filesystem changes and keep facts.pl up to date."""

    def __init__(self, known: set[str]):
        self.known = known

    # ------------- internal helpers ---------------------------------
    def _ignore(self, path: Path) -> bool:
        return path.name.startswith(("._", ".DS_Store"))

    def _maybe_add(self, path: Path) -> None:
        if self._ignore(path):
            return
        rel = f"files/{path.name}"
        if rel not in self.known:
            append_note(path.name)
            self.known.add(rel)

    def _maybe_remove(self, path: Path) -> None:
        if self._ignore(path):
            return
        rel = f"files/{path.name}"
        if rel in self.known:
            remove_note(path.name)
            self.known.remove(rel)

    # ------------- event callbacks ----------------------------------
    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._maybe_add(Path(event.src_path))

    def on_deleted(self, event: FileDeletedEvent) -> None:  # type: ignore[override]
        if not event.is_directory:
            self._maybe_remove(Path(event.src_path))

    def on_moved(self, event: FileMovedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return

        src = Path(event.src_path)
        dst = Path(event.dest_path)

        # Case A: rename/move *inside* the watched folder
        if src.parent == KNOWLEDGE_DIR and dst.parent == KNOWLEDGE_DIR:
            self._maybe_remove(src)
            self._maybe_add(dst)
            return

        # Case B: moved *into* the folder
        if dst.parent == KNOWLEDGE_DIR:
            self._maybe_add(dst)

        # Case C: moved *out of* the folder
        if src.parent == KNOWLEDGE_DIR:
            self._maybe_remove(src)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    known = load_known_files()
    sync_existing(known)

    print(f"Watching {KNOWLEDGE_DIR} for changes. Press Ctrl+C to stop.")
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
