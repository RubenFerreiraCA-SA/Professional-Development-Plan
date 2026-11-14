#!/usr/bin/env python3
"""Shared restore-equivalence comparison (H-01 / M-02).

Compare typed JSON datasets. Prefer PostgreSQL JSON export or application
HTTP JSON — never lossy TSV with strip().

Usage:
  harbour-restore-compare.py want.json got.json
  harbour-restore-compare.py --from-pg-json want.json pg_rows.json

Exit 0 on full equivalence of application-relevant fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_FIELDS = ("id", "note", "created_at")


def _load(path: Path) -> Any:
    return json.loads(path.read_text())


def _entries(payload: Any) -> list[dict]:
    if isinstance(payload, dict) and "entries" in payload:
        return list(payload["entries"])
    if isinstance(payload, list):
        return list(payload)
    raise SystemExit("FAIL: payload must be {entries:[...]} or a JSON array")


def _row_key(row: dict, fields: tuple[str, ...]) -> tuple:
    missing = [f for f in fields if f not in row]
    if missing:
        raise SystemExit(f"FAIL: row missing fields {missing}: {row!r}")
    out = []
    for f in fields:
        v = row[f]
        if f == "id":
            v = int(v)
        elif isinstance(v, str):
            v = v  # preserve trailing whitespace; do not strip
        out.append(v)
    return tuple(out)


def compare(want_payload: Any, got_payload: Any, fields: tuple[str, ...] = DEFAULT_FIELDS) -> str:
    want = {_row_key(e, fields) for e in _entries(want_payload)}
    got = {_row_key(e, fields) for e in _entries(got_payload)}
    if want != got:
        print("FAIL restore set mismatch", file=sys.stderr)
        print("missing", sorted(want - got)[:10], file=sys.stderr)
        print("extra", sorted(got - want)[:10], file=sys.stderr)
        raise SystemExit(1)
    blob = json.dumps(sorted(want), sort_keys=True, default=str).encode()
    fp = hashlib.sha256(blob).hexdigest()[:16]
    return f"OK full snapshot equivalence n={len(got)} fingerprint={fp} fields={list(fields)}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("want")
    p.add_argument("got")
    p.add_argument(
        "--fields",
        default=",".join(DEFAULT_FIELDS),
        help="comma-separated fields to compare (default: id,note,created_at)",
    )
    args = p.parse_args(argv)
    fields = tuple(f.strip() for f in args.fields.split(",") if f.strip())
    msg = compare(_load(Path(args.want)), _load(Path(args.got)), fields)
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
