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
    note_name = Path(file_name).stem
    if not note_name.startswith("nn_"):
        note_name = "nn_" + note_name
    entry = f"note({note_name}, 'files/{file_name}').\n"
    with FACTS_FILE.open("a") as f:
        f.write(entry)
    print(f"Appended: {entry.strip()}")


def sync_existing(known: set[str]) -> None:
    """Ensure facts.pl has entries for all existing files."""
    for path in KNOWLEDGE_DIR.iterdir():
        if path.is_file():
            rel = f"files/{path.name}"
            if rel not in known:
                append_note(path.name)
                known.add(rel)


class Handler(FileSystemEventHandler):
    """Watchdog handler that appends facts on new files."""

    def __init__(self, known: set[str]):
        self.known = known

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
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
