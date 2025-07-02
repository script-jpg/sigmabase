#!/usr/bin/env python3
"""
Merged watcher: keeps ``facts.pl`` in sync with the ``files/`` directory
**and** runs ``viz`` from ``rules.pl`` whenever ``facts.pl`` changes,
without polling.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileMovedEvent,
    FileDeletedEvent,
)
from watchdog.observers import Observer
import subprocess

# ── paths ────────────────────────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).with_name("files")
FACTS_FILE    = Path(__file__).with_name("facts.pl")
RULES_FILE    = Path(__file__).with_name("rules.pl")

# ── regex helpers ────────────────────────────────────────────────────────────
NOTE_RE   = re.compile(r"note\([^,]+,\s*'([^']+)'\)\.")
LOWERCASE = re.compile(r"[a-z]")

def _to_snake_case(s: str) -> str:
    return re.sub(r"\W+", "_", s).strip("_").lower()

def format_note_name(name: str) -> str:
    snaked = _to_snake_case(name)
    return f"nn_{snaked}" if not LOWERCASE.match(snaked[0]) else snaked

# ── facts.pl helpers ─────────────────────────────────────────────────────────
def load_known_notes() -> set[str]:
    known: set[str] = set()
    if FACTS_FILE.exists():
        for line in FACTS_FILE.read_text().splitlines():
            m = NOTE_RE.match(line.strip())
            if m:
                known.add(m.group(1))
    return known

def append_note(file_name: str) -> None:
    note_name = format_note_name(Path(file_name).stem)
    with FACTS_FILE.open("a", encoding="utf-8") as f:
        f.write(f"note({note_name}, 'files/{file_name}').\n")
    print(f"[knowledge] added    → files/{file_name}")

def remove_note(file_name: str) -> None:
    target = f"files/{file_name}"
    if not FACTS_FILE.exists():
        return
    with FACTS_FILE.open("r+", encoding="utf-8") as f:
        lines = f.readlines(); f.seek(0)
        for line in lines:
            if target not in line:
                f.write(line)
        f.truncate()
    print(f"[knowledge] removed  → {target}")

def update_rels(old: str, new: str) -> None:
    if not FACTS_FILE.exists():
        return
    pat, changed = re.compile(rf"\b{re.escape(old)}\b"), False
    with FACTS_FILE.open("r+", encoding="utf-8") as f:
        lines = f.readlines(); f.seek(0)
        for line in lines:
            if line.startswith("rel(") and pat.search(line):
                line, changed = pat.sub(new, line), True
            f.write(line)
        f.truncate()
    if changed:
        print(f"[knowledge] rels     → {old} → {new}")

# ── watcher 1: files/  →  facts.pl ──────────────────────────────────────────
class KnowledgeHandler(FileSystemEventHandler):
    def __init__(self, known: set[str]) -> None:
        self.known = known

    @staticmethod
    def _ignore(p: Path) -> bool:
        return p.name.startswith(("._", ".DS_Store"))

    # file added / removed ----------------------------------------------------
    def _maybe_add(self, p: Path) -> None:
        if self._ignore(p): return
        rel = f"files/{p.name}"
        if rel not in self.known:
            append_note(p.name); self.known.add(rel)

    def _maybe_remove(self, p: Path) -> None:
        if self._ignore(p): return
        rel = f"files/{p.name}"
        if rel in self.known:
            remove_note(p.name); self.known.remove(rel)

    # watchdog callbacks ------------------------------------------------------
    def on_created(self, e: FileCreatedEvent):  # type: ignore[override]
        if not e.is_directory: self._maybe_add(Path(e.src_path))

    def on_deleted(self, e: FileDeletedEvent):  # type: ignore[override]
        if not e.is_directory: self._maybe_remove(Path(e.src_path))

    def on_moved(self, e: FileMovedEvent):      # type: ignore[override]
        if e.is_directory: return
        src, dst = Path(e.src_path), Path(e.dest_path)

        # rename within folder
        if src.parent == KNOWLEDGE_DIR and dst.parent == KNOWLEDGE_DIR:
            old, new = format_note_name(src.stem), format_note_name(dst.stem)
            self._maybe_remove(src); update_rels(old, new); self._maybe_add(dst)
            return
        # moved in
        if dst.parent == KNOWLEDGE_DIR: self._maybe_add(dst)
        # moved out
        if src.parent == KNOWLEDGE_DIR: self._maybe_remove(src)

# ── watcher 2: facts.pl  →  viz ──────────────────────────────────────────────
def run_viz() -> None:
    # subprocess.run(
    #     ["swipl", "-q", "-s", str(RULES_FILE), "-g", "viz", "-t", "halt"],
    #     check=False,
    # )
    subprocess.run(["./load_notes.sh"])
    pass

class FactsHandler(FileSystemEventHandler):
    def _maybe_viz(self, p: Path) -> None:
        if p == FACTS_FILE:
            print(f"[viz] {p.name} changed → running viz…")
            run_viz()

    def on_modified(self, e):  # type: ignore[override]
        if not e.is_directory: self._maybe_viz(Path(e.src_path))

    def on_created(self, e):   # type: ignore[override]
        if not e.is_directory: self._maybe_viz(Path(e.src_path))

# ── entry point ──────────────────────────────────────────────────────────────
def main() -> None:
    known = load_known_notes()
    observer = Observer()
    observer.schedule(KnowledgeHandler(known), str(KNOWLEDGE_DIR), recursive=False)
    observer.schedule(FactsHandler(),              str(FACTS_FILE.parent), recursive=False)

    print(f"Watching {KNOWLEDGE_DIR} and {FACTS_FILE} …  Ctrl-C to exit.")
    observer.start()
    try:
        observer.join()          # blocks; no polling
    except KeyboardInterrupt:
        observer.stop(); observer.join()

if __name__ == "__main__":
    main()
