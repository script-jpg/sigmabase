#!/bin/bash

# ─── 1. Get Neo4j password ─────────────────────────────────────────────────────
# Try env var first, otherwise prompt securely
if [[ -n "${NEO4J_PASS-}" ]]; then
  PASS="$NEO4J_PASS"
else
  read -s -p "Neo4j password (env var NEO4J_PASS not set): " PASS
  echo
fi

# Quick check that we actually got something
if [[ -z "$PASS" ]]; then
  echo "❌  No password provided. Set NEO4J_PASS or enter it when prompted." >&2
  exit 1
fi

# ─── 2. Verify credentials before doing any work ──────────────────────────────
echo "🔑  Testing Neo4j credentials against database 'pkm'…"
if ! echo "RETURN 1;" \
     | cypher-shell -u neo4j -p "$PASS" --database pkm \
     > /dev/null 2>&1; then
  echo "❌  Authentication failed. Check your NEO4J_PASS and try again." >&2
  exit 1
fi

# ─── 3. Generate the Cypher script from facts.pl ──────────────────────────────
INPUT="facts.pl"
OUTPUT="prolog_notes_to_neo4j_updated.cypher"

python3 << 'PYCODE'
import re, textwrap

in_path  = 'facts.pl'
out_path = 'prolog_notes_to_neo4j_updated.cypher'

notes, rels = [], []
with open(in_path) as f:
    for L in f:
        L = L.strip()
        if L.startswith('note('):
            # Updated regex to handle both single and double quotes
            m = re.match(r'note\(([^,]+),\s*["\']([^"\']+)["\']\)\.', L)
            if m: notes.append((m.group(1), m.group(2)))
        elif L.startswith('rel('):
            # Updated regex to handle both single and double quotes
            m = re.match(r'rel\(([^,]+),\s*([^,]+),\s*["\']([^"\']*?)["\']\)\.', L)
            if m: rels.append((m.group(1), m.group(2), m.group(3)))

def rel_type(lbl):
    lbl = lbl.strip()
    return 'RELATED_TO' if not lbl else lbl.upper().replace(' ', '_').replace('-', '_')

lines = ["// Nodes"]
for nid, path in notes:
    esc = path.replace("'", "\\'")
    lines.append(f"MERGE (:Note {{id:'{nid}', path:'{esc}'}});")

lines.append("\n// Relationships")
for a, b, lbl in rels:
    lines.append(textwrap.dedent(f"""
        MATCH (a:Note {{id:'{a}'}}), (b:Note {{id:'{b}'}})
        MERGE (a)-[:{rel_type(lbl)}]->(b);
    """).strip())

with open(out_path, 'w') as f:
    f.write("\n".join(lines))

print(f"✔️  Generated {out_path} with {len(notes)} nodes & {len(rels)} relationships.")
PYCODE

# ─── 4. Load into Neo4j PKM database ───────────────────────────────────────────
echo "⏳  Importing into Neo4j (db: pkm)…"
cat "$OUTPUT" \
  | cypher-shell -u neo4j -p "$PASS" --database pkm

echo "✅  Done."
