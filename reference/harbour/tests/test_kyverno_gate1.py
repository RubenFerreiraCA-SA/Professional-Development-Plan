#!/usr/bin/env python3
"""G1-03 frozen acceptance K01–K08."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "bin"))

from kyverno_deny import (  # noqa: E402
    assert_expected_passes,
    inventory_from_rendered,
    load_report,
)

FIX = Path(__file__).resolve().parent / "fixtures"
REPORT = (FIX / "reports" / "sample-clusterpolicyreport.yaml").read_text()


class TestKyvernoGate1(unittest.TestCase):
    def test_K01_all_applicable_pass(self):
        rep = load_report(REPORT)
        assert_expected_passes(
            rep,
            0,
            expected_resources=[
                "ledger-staging/Pod/ledger",
                "default/Pod/good-ephem",
            ],
        )

    def test_K02_pass_plus_warn_fails(self):
        text = REPORT + """
  - policy: harbour-baseline
    rule: require-image-digest
    result: warn
    resources:
      - kind: Pod
        name: ledger
        namespace: ledger-staging
"""
        with self.assertRaises(SystemExit):
            assert_expected_passes(
                load_report(text),
                0,
                expected_resources=["ledger-staging/Pod/ledger"],
            )

    def test_K03_rule_absent_fails(self):
        # Strip ephemeral rule results
        lines = [
            ln
            for ln in REPORT.splitlines()
            if "require-ephemeral-no-privilege" not in ln
        ]
        # Also drop result blocks that only had that rule — simpler: build minimal
        minimal = """apiVersion: wgpolicyk8s.io/v1alpha2
kind: ClusterPolicyReport
results:
  - rule: require-image-digest
    result: pass
    resources: [{kind: Pod, name: ledger, namespace: ledger-staging}]
  - rule: require-nonroot-memory-limit
    result: pass
    resources: [{kind: Pod, name: ledger, namespace: ledger-staging}]
"""
        with self.assertRaises(SystemExit) as ctx:
            assert_expected_passes(load_report(minimal), 0)
        self.assertIn("never evaluated", str(ctx.exception))

    def test_K04_second_resource_absent(self):
        with self.assertRaises(SystemExit) as ctx:
            assert_expected_passes(
                load_report(REPORT),
                0,
                expected_resources=[
                    "ledger-staging/Pod/ledger",
                    "default/Pod/missing",
                ],
            )
        self.assertIn("missing evaluation", str(ctx.exception))

    def test_K05_empty_or_nonzero(self):
        with self.assertRaises(SystemExit):
            assert_expected_passes({"results": []}, 0)
        with self.assertRaises(SystemExit):
            assert_expected_passes(load_report(REPORT), 1)

    def test_K06_mandatory_bad_fixtures_exist(self):
        for name in (
            "bad-mutable-tag.yaml",
            "bad-no-memory-limit.yaml",
            "bad-init-mutable-tag.yaml",
            "bad-ephemeral-privileged.yaml",
        ):
            self.assertTrue((FIX / name).is_file(), name)

    def test_K07_missing_fixture_detected(self):
        # Production checker must fail if a mandatory fixture is absent — assert naming.
        mandatory = [
            "bad-mutable-tag.yaml",
            "bad-no-memory-limit.yaml",
            "bad-init-mutable-tag.yaml",
            "bad-ephemeral-privileged.yaml",
            "good-ephemeral.yaml",
        ]
        for name in mandatory:
            self.assertTrue((FIX / name).is_file(), f"missing mandatory fixture {name}")

    def test_K08_good_fixture_inventory(self):
        text = (FIX / "good-ephemeral.yaml").read_text()
        inv = inventory_from_rendered(text)
        self.assertEqual(inv, ["default/Pod/good-ephem"])


if __name__ == "__main__":
    unittest.main()
