"""Keep ``facts.pl`` synchronized with the ``files`` folder.

*  add / remove   → keeps the corresponding ``note(...)`` lines in sync  
*  rename inside  → rewrites the old ``note(...)`` line, **updates any
   matching ``rel(...)`` lines**, and appends a new ``note(...)``  
*  move in / out  → handled as add / remove
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

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).with_name("files")   # folder to watch
FACTS_FILE = Path(__file__).with_name("facts.pl")   # Prolog knowledge base

# ─────────────────────────────────────────────────────────────────────────────
# Regex helpers
# ─────────────────────────────────────────────────────────────────────────────
NOTE_RE = re.compile(r"note\([^,]+,\s*'([^']+)'\)\.")
LOWER_CASE = re.compile(r"[a-z]")


def _to_snake_case(s: str) -> str:
    return re.sub(r"\W+", "_", s).strip("_").lower()


def format(name: str) -> str:
    """Convert to snake_case; prepend 'nn_' if it doesn't start with a-z."""
    snaked = _to_snake_case(name)
    return "nn_" + snaked if not LOWER_CASE.match(snaked[0]) else snaked


# ─────────────────────────────────────────────────────────────────────────────
# facts.pl helpers
# ─────────────────────────────────────────────────────────────────────────────
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
    note_name = format(Path(file_name).stem)
    entry = f"note({note_name}, 'files/{file_name}').\n"
    with FACTS_FILE.open("a") as f:
        f.write(entry)
    print(f"Appended: {entry.strip()}")


def remove_note(file_name: str) -> None:
    target = f"files/{file_name}"
    if not FACTS_FILE.exists():
        return
    with FACTS_FILE.open("r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if target not in line:
                f.write(line)
        f.truncate()
    print(f"Removed note for: {target}")


def update_rels(old_note: str, new_note: str) -> None:
    """Replace occurrences of old_note with new_note in rel(...) lines."""
    if not FACTS_FILE.exists():
        return
    pattern = re.compile(rf"\b{re.escape(old_note)}\b")
    changed = False
    with FACTS_FILE.open("r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.strip().startswith("rel(") and pattern.search(line):
                line = pattern.sub(new_note, line)
                changed = True
            f.write(line)
        f.truncate()
    if changed:
        print(f"Updated rels: {old_note} → {new_note}")


def sync_existing(known: set[str]) -> None:
    for path in KNOWLEDGE_DIR.iterdir():
        if path.is_file() and not path.name.startswith(("._", ".DS_Store")):
            rel = f"files/{path.name}"
            if rel not in known:
                append_note(path.name)
                known.add(rel)


# ─────────────────────────────────────────────────────────────────────────────
# Watchdog handler
# ─────────────────────────────────────────────────────────────────────────────
class Handler(FileSystemEventHandler):
    def __init__(self, known: set[str]):
        self.known = known

    # ---------- helpers -----------------------------------------------------
    @staticmethod
    def _ignore(path: Path) -> bool:
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

    # ---------- watchdog callbacks -----------------------------------------
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

        # ── rename within the folder ───────────────────────────────────────
        if src.parent == KNOWLEDGE_DIR and dst.parent == KNOWLEDGE_DIR:
            old_note = format(src.stem)
            new_note = format(dst.stem)
            self._maybe_remove(src)
            update_rels(old_note, new_note)
            self._maybe_add(dst)
            return

        # ── moved in ───────────────────────────────────────────────────────
        if dst.parent == KNOWLEDGE_DIR:
            self._maybe_add(dst)

        # ── moved out ──────────────────────────────────────────────────────
        if src.parent == KNOWLEDGE_DIR:
            self._maybe_remove(src)


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    known = load_known_files()
    sync_existing(known)

    print(f"Watching {KNOWLEDGE_DIR} …  Ctrl-C to exit.")
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
