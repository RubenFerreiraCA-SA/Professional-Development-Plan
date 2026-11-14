#!/usr/bin/env python3
"""Offline unit tests for kyverno_deny.py, promote-verify, restore-compare (H-02/H-03/M-02)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "bin"))

from kyverno_deny import (  # noqa: E402
    assert_expected_passes,
    denial_verdict,
    load_report,
)


def _load_hyphen_module(name: str, filename: str):
    path = ROOT / "platform" / "bin" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


_promote = _load_hyphen_module("harbour_promote_verify_images", "harbour-promote-verify-images.py")
_restore = _load_hyphen_module("harbour_restore_compare", "harbour-restore-compare.py")


def _extract_from_yaml(text: str):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(text)
        path = Path(f.name)
    try:
        return _promote.extract(path)
    finally:
        path.unlink(missing_ok=True)


def _rep(results, *, kind="ClusterPolicyReport"):
    return {
        "apiVersion": "wgpolicyk8s.io/v1alpha2",
        "kind": kind,
        "results": results,
    }


class TestDenialVerdict(unittest.TestCase):
    def test_fail_only(self):
        self.assertEqual(
            denial_verdict(
                "require-image-digest",
                _rep([{"rule": "require-image-digest", "result": "fail"}]),
            ),
            "accept",
        )

    def test_pass_only_missing(self):
        self.assertEqual(
            denial_verdict(
                "require-image-digest",
                _rep([{"rule": "require-image-digest", "result": "pass"}]),
            ),
            "reject-missing",
        )

    def test_mixed_fail_warn(self):
        self.assertEqual(
            denial_verdict(
                "require-image-digest",
                _rep(
                    [
                        {"rule": "require-image-digest", "result": "fail"},
                        {"rule": "require-image-digest", "result": "warn"},
                    ]
                ),
            ),
            "reject-mixed",
        )


class TestAssertExpectedPasses(unittest.TestCase):
    def _all_pass(self):
        return _rep(
            [
                {
                    "rule": "require-image-digest",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
                {
                    "rule": "require-nonroot-memory-limit",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
                {
                    "rule": "require-ephemeral-no-privilege",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
            ]
        )

    def test_all_pass(self):
        assert_expected_passes(self._all_pass(), 0)

    def test_reject_warn(self):
        rep = self._all_pass()
        rep["results"].append({"rule": "require-image-digest", "result": "warn"})
        with self.assertRaises(SystemExit):
            assert_expected_passes(rep, 0)

    def test_missing_rule(self):
        with self.assertRaises(SystemExit):
            assert_expected_passes(
                _rep([{"rule": "require-image-digest", "result": "pass"}]), 0
            )

    def test_empty_results(self):
        with self.assertRaises(SystemExit):
            assert_expected_passes(_rep([]), 0)

    def test_per_resource_coverage(self):
        rep = _rep(
            [
                {
                    "rule": "require-image-digest",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
                {
                    "rule": "require-nonroot-memory-limit",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
                {
                    "rule": "require-ephemeral-no-privilege",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "a", "namespace": "ns"}],
                },
                {
                    "rule": "require-image-digest",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "b", "namespace": "ns"}],
                },
                {
                    "rule": "require-nonroot-memory-limit",
                    "result": "pass",
                    "resources": [{"kind": "Pod", "name": "b", "namespace": "ns"}],
                },
            ]
        )
        with self.assertRaises(SystemExit):
            assert_expected_passes(
                rep, 0, expected_resources=["ns/Pod/a", "ns/Pod/b"]
            )

    def test_merge_multiple_reports(self):
        text = """apiVersion: wgpolicyk8s.io/v1alpha2
kind: ClusterPolicyReport
results:
  - rule: require-image-digest
    result: pass
---
apiVersion: wgpolicyk8s.io/v1alpha2
kind: ClusterPolicyReport
results:
  - rule: require-nonroot-memory-limit
    result: pass
  - rule: require-ephemeral-no-privilege
    result: pass
"""
        rep = load_report(text)
        assert_expected_passes(rep, 0)
        self.assertEqual(rep.get("_merged_report_count"), 2)


class TestPromoteVerifyImages(unittest.TestCase):
    def test_shared_digest_two_refs_unsupported_v1(self):
        dig = "sha256:" + "a" * 64
        yaml_text = f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: a}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/one@{dig}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: b}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/two@{dig}
"""
        with self.assertRaises(SystemExit) as ctx:
            _extract_from_yaml(yaml_text)
        self.assertIn("unsupported in v1", str(ctx.exception))

    def test_base_second_workload_not_skipped(self):
        dig = "sha256:" + "b" * 64
        sentinel = "sha256:" + "0" * 64
        yaml_text = f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: primary}}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: c
          image: registry.example/primary@{sentinel}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: sneaky}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/sneaky@{dig}
"""
        data = _extract_from_yaml(yaml_text)
        self.assertEqual(data["action"], "verify")
        self.assertTrue(any("sneaky" in r for r in data["verified_refs"]))

    def test_all_disabled_skips(self):
        sentinel = "sha256:" + "0" * 64
        yaml_text = f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: primary}}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: c
          image: registry.example/primary@{sentinel}
"""
        data = _extract_from_yaml(yaml_text)
        self.assertEqual(data["action"], "skip")


class TestRestoreCompare(unittest.TestCase):
    def test_equivalence_and_whitespace(self):
        want = {
            "entries": [
                {"id": 1, "note": "hello ", "created_at": "2026-01-01T00:00:00Z"},
                {"id": 2, "note": "line\nbreak", "created_at": "2026-01-01T00:00:01Z"},
            ]
        }
        got = {
            "entries": [
                {"id": 2, "note": "line\nbreak", "created_at": "2026-01-01T00:00:01Z"},
                {"id": 1, "note": "hello ", "created_at": "2026-01-01T00:00:00Z"},
            ]
        }
        msg = _restore.compare(want, got)
        self.assertIn("OK full snapshot equivalence", msg)

    def test_mismatch(self):
        with self.assertRaises(SystemExit):
            _restore.compare(
                {"entries": [{"id": 1, "note": "a", "created_at": "t"}]},
                {"entries": [{"id": 1, "note": "b", "created_at": "t"}]},
            )


if __name__ == "__main__":
    unittest.main()
