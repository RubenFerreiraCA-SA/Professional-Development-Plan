#!/usr/bin/env python3
"""Render-first promotion image enumeration (C-02 / H-02).

Always inspect kubectl-kustomize output. An unpromoted scaffold may be skipped
only when every runnable workload is disabled (replicas==0 / Job suspended) and
no non-sentinel digest remains on a runnable workload.

Emits JSON:
  {"action":"skip"|"verify","refs":[{"ref":"...","image":"...","digest":"..."}],
   "verified_refs":[...], "reason":"..."}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

SENTINEL = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob", "ReplicaSet"}


def _pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    if kind == "CronJob":
        return (
            (((doc.get("spec") or {}).get("jobTemplate") or {}).get("spec") or {})
            .get("template", {})
            .get("spec")
            or {}
        )
    return ((doc.get("spec") or {}).get("template") or {}).get("spec") or {}


def _replicas(doc: dict) -> int | None:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind in {"Deployment", "StatefulSet", "ReplicaSet"}:
        return int(spec.get("replicas", 1))
    if kind == "DaemonSet":
        # DaemonSets are always "runnable" if present.
        return 1
    if kind == "Job":
        if spec.get("suspend"):
            return 0
        return 1
    if kind == "CronJob":
        if spec.get("suspend"):
            return 0
        return 1
    return None


def extract(rendered_path: Path) -> dict:
    docs = list(yaml.safe_load_all(rendered_path.read_text()))
    workloads = []
    refs = []
    for d in docs:
        if not d or d.get("kind") not in WORKLOAD_KINDS:
            continue
        kind = d["kind"]
        name = (d.get("metadata") or {}).get("name") or "?"
        reps = _replicas(d)
        spec = _pod_spec(d)
        images = []
        for c in (spec.get("containers") or []) + (spec.get("initContainers") or []):
            img = c.get("image") or ""
            if "@sha256:" not in img:
                raise SystemExit(
                    f"FAIL: rendered {kind}/{name} image not digest-pinned: {img}"
                )
            image_name, digest = img.rsplit("@", 1)
            rec = {"image": image_name, "digest": digest, "ref": img}
            images.append(rec)
            refs.append(rec)
        workloads.append(
            {
                "kind": kind,
                "name": name,
                "replicas": reps,
                "runnable": reps is None or reps > 0,
                "images": images,
            }
        )

    if not workloads:
        raise SystemExit("FAIL: no workload controllers in rendered overlay")

    runnable = [w for w in workloads if w["runnable"]]
    if not runnable:
        # All workloads disabled — safe skip only if every image is sentinel or empty.
        digests = {r["digest"] for r in refs}
        if digests and digests != {SENTINEL}:
            raise SystemExit(
                "FAIL: disabled workloads still reference non-sentinel digests — verify required"
            )
        return {
            "action": "skip",
            "reason": "all workloads replicas=0/suspended",
            "refs": [],
            "verified_refs": [],
            "workloads": workloads,
        }

    # Fail closed: any runnable workload with sentinel or undigested already rejected.
    runnable_refs = []
    for w in runnable:
        for r in w["images"]:
            if r["digest"] == SENTINEL:
                raise SystemExit(
                    f"FAIL: runnable {w['kind']}/{w['name']} still has UNPROMOTED sentinel"
                )
            runnable_refs.append(r)

    if not runnable_refs:
        raise SystemExit("FAIL: runnable workloads have no containers")

    # Distinct complete image references (not digests alone).
    by_ref = {r["ref"]: r for r in runnable_refs}
    verified_refs = sorted(by_ref.keys())
    return {
        "action": "verify",
        "reason": "runnable workloads present",
        "refs": list(by_ref.values()),
        "verified_refs": verified_refs,
        "workloads": workloads,
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print(f"usage: {sys.argv[0]} <rendered.yaml>", file=sys.stderr)
        return 2
    data = extract(Path(argv[0]))
    print(json.dumps(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
