#!/usr/bin/env python3
"""
neo4j_to_filesystem_watcher.py
──────────────────────────────
Watches Neo4j for changes and syncs them to:
  • files/     → creates/deletes/renames files based on (:Note) nodes
  • facts.pl   → updates relationships and node entries

Uses polling to detect Neo4j changes.
"""

import os
import re
import time
from pathlib import Path
from threading import Thread, Event
from typing import Set, Dict, Tuple, Optional

from neo4j import GraphDatabase, basic_auth

# ── paths ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
KNOWLEDGE   = ROOT / "files"
FACTS_FILE  = ROOT / "facts.pl"

# ── Neo4j connection ────────────────────────────────────────────────────────
URI   = os.getenv("NEO4J_URI",  "bolt://localhost:7687")
USER  = os.getenv("NEO4J_USER", "neo4j")
PASS  = os.getenv("NEO4J_PASS", "neo4j")
DB    = os.getenv("NEO4J_DB",   "pkm")

driver = GraphDatabase.driver(URI, auth=basic_auth(USER, PASS))

# ── helpers ─────────────────────────────────────────────────────────────────
LOWERCASE = re.compile(r"[a-z]")

def _snake(s: str) -> str:
    """`My-File.txt` → `my_file` ; `2025-06-30.txt` → `nn_2025_06_30`"""
    snake = re.sub(r"\W+", "_", s).strip("_").lower()
    return f"nn_{snake}" if not LOWERCASE.match(snake[0]) else snake

def _unsnake_to_filename(id: str, existing_path: Optional[str] = None) -> str:
    """Convert snake_case id back to filename, preserving extension if known."""
    # If we have an existing path, extract the extension
    ext = ""
    if existing_path:
        path = Path(existing_path)
        ext = path.suffix
    
    # Remove nn_ prefix if present
    name = id[3:] if id.startswith("nn_") else id
    
    # Try to restore original casing (basic heuristic)
    # This is imperfect but helps with common patterns
    parts = name.split("_")
    
    # If it looks like a date (e.g., "2025_01_15"), keep underscores
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        name = "-".join(parts)
    else:
        # Otherwise, capitalize words
        name = " ".join(p.capitalize() for p in parts)
    
    return f"{name}{ext}" if ext else f"{name}.txt"

class Neo4jWatcher:
    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self.stop_event = Event()
        
        # State tracking
        self.last_nodes: Dict[str, Dict] = {}  # id -> {path, ...}
        self.last_rels: Set[Tuple[str, str, str]] = set()  # (from_id, to_id, type)
        
        # Initialize state
        self._update_state()
    
    def _query_nodes(self) -> Dict[str, Dict]:
        """Get all Note nodes from Neo4j."""
        with driver.session(database=DB) as session:
            result = session.run(
                "MATCH (n:Note) "
                "RETURN n.id AS id, n.path AS path, "
                "properties(n) AS props"
            )
            return {
                record["id"]: {
                    "path": record["path"],
                    "props": record["props"]
                }
                for record in result
            }
    
    def _query_relationships(self) -> Set[Tuple[str, str, str]]:
        """Get all relationships between Note nodes."""
        with driver.session(database=DB) as session:
            result = session.run(
                "MATCH (a:Note)-[r]->(b:Note) "
                "RETURN a.id AS from_id, b.id AS to_id, type(r) AS rel_type"
            )
            return {
                (record["from_id"], record["to_id"], record["rel_type"])
                for record in result
            }
    
    def _update_state(self):
        """Update internal state from Neo4j."""
        try:
            self.last_nodes = self._query_nodes()
            self.last_rels = self._query_relationships()
        except Exception as e:
            print(f"[neo4j-watcher] Error updating state: {e}")
    
    def _sync_files(self, current_nodes: Dict[str, Dict], previous_nodes: Dict[str, Dict]):
        """Sync file system based on node changes."""
        # Ensure files directory exists
        KNOWLEDGE.mkdir(exist_ok=True)
        
        # Track which files should exist
        expected_files = set()
        
        # Handle new and modified nodes
        for node_id, node_data in current_nodes.items():
            path = node_data.get("path")
            
            if not path:
                # Node exists but has no path - create a file for it
                filename = _unsnake_to_filename(node_id)
                path = f"files/{filename}"
                # Update Neo4j with the path
                with driver.session(database=DB) as session:
                    session.run(
                        "MATCH (n:Note {id: $id}) SET n.path = $path",
                        id=node_id, path=path
                    )
                print(f"[neo4j-watcher] Added path to node {node_id}: {path}")
            
            file_path = ROOT / path
            expected_files.add(file_path)
            
            # Create file if it doesn't exist
            if not file_path.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.touch()
                print(f"[neo4j-watcher] Created file: {path}")
            
            # Handle renames (same id, different path)
            if node_id in previous_nodes:
                old_path = previous_nodes[node_id].get("path")
                if old_path and old_path != path:
                    old_file = ROOT / old_path
                    if old_file.exists() and not file_path.exists():
                        old_file.rename(file_path)
                        print(f"[neo4j-watcher] Renamed: {old_path} → {path}")
        
        # Handle deleted nodes
        for node_id, node_data in previous_nodes.items():
            if node_id not in current_nodes:
                path = node_data.get("path")
                if path:
                    file_path = ROOT / path
                    if file_path.exists():
                        file_path.unlink()
                        print(f"[neo4j-watcher] Deleted file: {path}")
    
    def _sync_facts_pl(self, current_nodes: Dict[str, Dict], current_rels: Set[Tuple[str, str, str]]):
        """Update facts.pl with current state."""
        lines = []
        
        # Add directives
        lines.append(":- discontiguous note/2.")
        lines.append(":- discontiguous rel/3.")
        lines.append("")
        
        # Add note facts
        for node_id, node_data in sorted(current_nodes.items()):
            path = node_data.get("path", f"files/{_unsnake_to_filename(node_id)}")
            lines.append(f"note({node_id}, '{path}').")
        
        if current_nodes and current_rels:
            lines.append("")
        
        # Add relationship facts
        for from_id, to_id, rel_type in sorted(current_rels):
            # Convert NEO4J_STYLE to 'neo4j style'
            rel_label = rel_type.lower().replace("_", " ")
            lines.append(f"rel({from_id}, {to_id}, '{rel_label}').")
        
        # Write to file
        new_content = "\n".join(lines) + "\n" if lines else ""
        
        try:
            current_content = FACTS_FILE.read_text() if FACTS_FILE.exists() else ""
            if current_content.strip() != new_content.strip():
                FACTS_FILE.write_text(new_content)
                print(f"[neo4j-watcher] Updated facts.pl")
        except Exception as e:
            print(f"[neo4j-watcher] Error updating facts.pl: {e}")
    
    def _poll_loop(self):
        """Main polling loop."""
        print(f"[neo4j-watcher] Started watching Neo4j (polling every {self.poll_interval}s)")
        
        while not self.stop_event.is_set():
            try:
                # Get current state
                current_nodes = self._query_nodes()
                current_rels = self._query_relationships()
                
                # Check for changes
                nodes_changed = current_nodes != self.last_nodes
                rels_changed = current_rels != self.last_rels
                
                if nodes_changed or rels_changed:
                    print("[neo4j-watcher] Detected changes in Neo4j")
                    
                    # Sync files if nodes changed
                    if nodes_changed:
                        self._sync_files(current_nodes, self.last_nodes)
                    
                    # Always update facts.pl if anything changed
                    self._sync_facts_pl(current_nodes, current_rels)
                    
                    # Update state
                    self.last_nodes = current_nodes
                    self.last_rels = current_rels
                
            except Exception as e:
                print(f"[neo4j-watcher] Error in poll loop: {e}")
            
            # Wait for next poll
            self.stop_event.wait(self.poll_interval)
    
    def start(self):
        """Start the watcher in a background thread."""
        self.thread = Thread(target=self._poll_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the watcher."""
        print("[neo4j-watcher] Stopping...")
        self.stop_event.set()
        if hasattr(self, 'thread'):
            self.thread.join()

def main():
    """Run the Neo4j watcher."""
    watcher = Neo4jWatcher(poll_interval=2.0)
    
    try:
        watcher.start()
        print("Neo4j watcher running. Press Ctrl-C to stop.")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        watcher.stop()
        driver.close()

if __name__ == "__main__":
    main()
