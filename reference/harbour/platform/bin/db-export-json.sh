#!/usr/bin/env bash
# Export ledger_entries as JSON for restore comparison (M-02).
# Usage: db-export-json.sh <namespace> > entries.json
set -euo pipefail
NS="${1:?namespace}"
kubectl -n "$NS" exec postgres-0 -- psql -U harbour -d harbour -v ON_ERROR_STOP=1 -tAc \
  "SELECT COALESCE(json_agg(row_to_json(t) ORDER BY id), '[]'::json)
   FROM (
     SELECT id, note, created_at
     FROM ledger_entries
   ) t;" | python3 -c '
import json, sys
raw = sys.stdin.read().strip() or "[]"
rows = json.loads(raw)
print(json.dumps({"entries": rows, "count": len(rows)}))
'
