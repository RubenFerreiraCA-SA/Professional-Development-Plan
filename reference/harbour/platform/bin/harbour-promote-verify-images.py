#!/usr/bin/env python3
"""Render-first promotion image enumeration (G1-02).

Supported runnable kinds: Deployment, StatefulSet, DaemonSet, Job, CronJob,
ReplicaSet, and direct Pods (charter option A).

Unsupported in v1: two different repository image refs sharing one digest —
fail with a descriptive error (charter option B).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

SENTINEL = "sha256:0000000000000000000000000000000000000000000000000000000000000000"
CONTROLLER_KINDS = {
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "Job",
    "CronJob",
    "ReplicaSet",
}
WORKLOAD_KINDS = CONTROLLER_KINDS | {"Pod"}


def _pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    if kind == "Pod":
        return doc.get("spec") or {}
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
    if kind == "Pod":
        return 1
    if kind in {"Deployment", "StatefulSet", "ReplicaSet"}:
        return int(spec.get("replicas", 1))
    if kind == "DaemonSet":
        return 1
    if kind in {"Job", "CronJob"}:
        if spec.get("suspend"):
            return 0
        return 1
    return None


def _container_images(spec: dict) -> list[dict]:
    refs = []
    for c in (spec.get("containers") or []) + (spec.get("initContainers") or []):
        img = c.get("image") or ""
        if "@sha256:" not in img:
            raise SystemExit(f"FAIL: image not digest-pinned: {img}")
        image_name, digest = img.rsplit("@", 1)
        refs.append({"image": image_name, "digest": digest, "ref": img})
    return refs


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
        images = _container_images(spec)
        # Ephemeral containers on a Pod template are not primary runtime images
        # for promotion provenance of the service release; still reject undigested.
        for c in spec.get("ephemeralContainers") or []:
            img = c.get("image") or ""
            if img and "@sha256:" not in img:
                raise SystemExit(
                    f"FAIL: ephemeral image not digest-pinned on {kind}/{name}: {img}"
                )
        workloads.append(
            {
                "kind": kind,
                "name": name,
                "replicas": reps,
                "runnable": reps is None or reps > 0,
                "images": images,
            }
        )
        refs.extend(images)

    if not workloads:
        raise SystemExit("FAIL: no supported workload kinds in rendered overlay")

    runnable = [w for w in workloads if w["runnable"]]
    if not runnable:
        digests = {r["digest"] for r in refs}
        if digests and digests != {SENTINEL}:
            raise SystemExit(
                "FAIL: disabled workloads still reference non-sentinel digests"
            )
        return {
            "action": "skip",
            "reason": "all workloads replicas=0/suspended",
            "refs": [],
            "verified_refs": [],
            "workloads": workloads,
        }

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

    by_ref = {r["ref"]: r for r in runnable_refs}
    # P08: reject same digest across distinct image repositories (unsupported v1).
    by_digest: dict[str, set[str]] = defaultdict(set)
    for r in by_ref.values():
        by_digest[r["digest"]].add(r["image"])
    for dig, images in by_digest.items():
        if len(images) > 1:
            raise SystemExit(
                "FAIL: unsupported in v1 — same digest used by multiple image "
                f"repositories: digest={dig} images={sorted(images)}. "
                "Publish distinct digests or a single repository ref."
            )

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
    print(json.dumps(extract(Path(argv[0]))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
