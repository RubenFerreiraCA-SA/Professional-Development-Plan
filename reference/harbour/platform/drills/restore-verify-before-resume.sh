#!/usr/bin/env bash
# Shared restore-equivalence gate (H-01 / M-02).
# Call AFTER pg_restore and BEFORE clearing DB_UNSAFE / resuming Flux.
#
# Env:
#   NS, OUT (drill evidence dir), HARBOUR_ROOT optional
# Expects: $OUT/entries-at-backup.json
set -euo pipefail
NS="${NS:?set NS}"
OUT="${OUT:?set OUT}"
BIN="$(cd "$(dirname "$0")/../bin" && pwd)"
export PYTHONPATH="${BIN}${PYTHONPATH:+:$PYTHONPATH}"

[ -f "$OUT/entries-at-backup.json" ] \
  || { echo "FAIL: missing entries-at-backup.json — cannot authorise resume"; exit 1; }

"$BIN/db-export-json.sh" "$NS" > "$OUT/entries-restored-db.json"
python3 "$BIN/harbour-restore-compare.py" \
  "$OUT/entries-at-backup.json" \
  "$OUT/entries-restored-db.json" \
  --fields id,note,created_at \
  | tee -a "$OUT/restore-equivalence.txt"

echo "OK: DB equivalence proven while writers stopped — safe to clear DB_UNSAFE and resume"
