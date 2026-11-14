#!/usr/bin/env python3
"""Offline C-01 negative checks for tenant PSA / NetworkPolicy contract."""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

FIX = Path(__file__).resolve().parent / "fixtures"


def tenant_contract_ok(path: Path) -> list[str]:
    docs = list(yaml.safe_load_all(path.read_text()))
    errors = []
    nps = [d for d in docs if d and d.get("kind") == "NetworkPolicy"]
    deny = [n for n in nps if (n.get("metadata") or {}).get("name") == "default-deny-all"]
    if not deny:
        errors.append("missing NetworkPolicy default-deny-all")
    ns_ok = False
    for d in docs:
        if not d or d.get("kind") != "Namespace":
            continue
        labels = (d.get("metadata") or {}).get("labels") or {}
        if labels.get("pod-security.kubernetes.io/enforce") == "restricted":
            ns_ok = True
    if not ns_ok:
        errors.append("missing PSA enforce=restricted on Namespace")
    return errors


class TestTenantContract(unittest.TestCase):
    def test_negative_fixture_fails(self):
        errs = tenant_contract_ok(FIX / "tenant-missing-deny.yaml")
        self.assertTrue(errs)
        self.assertTrue(any("default-deny-all" in e for e in errs))
        self.assertTrue(any("PSA" in e for e in errs))

    def test_good_tenant_passes(self):
        good = FIX / "tenant-good.yaml"
        self.assertEqual(tenant_contract_ok(good), [])


if __name__ == "__main__":
    unittest.main()
