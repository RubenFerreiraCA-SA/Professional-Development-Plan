#!/usr/bin/env python3
"""G1-01 frozen acceptance: T01–T09 against production tenant_contract.py."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "platform" / "bin"
FIX = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location("tenant_contract", BIN / "tenant_contract.py")
tc = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(tc)


def _write(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
    f.write(text)
    f.close()
    return Path(f.name)


GOOD = (FIX / "tenant-good.yaml").read_text()


class TestTenantContractT01T09(unittest.TestCase):
    def tearDown(self):
        pass

    def test_T01_valid(self):
        tc.validate_tenant_file(FIX / "tenant-good.yaml", "ledger")

    def test_T02_psa_missing(self):
        text = """apiVersion: v1
kind: Namespace
metadata:
  name: ledger-staging
  labels:
    app: ledger
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ledger-staging
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ledger-quota
  namespace: ledger-staging
spec:
  hard:
    pods: "8"
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.memory: 2Gi
"""
        path = _write(text)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("PSA", str(ctx.exception))
        path.unlink(missing_ok=True)

    def test_T03_psa_only_in_comment(self):
        # Comment contains the string; Namespace labels do not.
        text = """apiVersion: v1
kind: Namespace
metadata:
  name: ledger-staging
  labels:
    app: ledger
  # pod-security.kubernetes.io/enforce: restricted
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ledger-staging
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ledger-quota
  namespace: ledger-staging
spec:
  hard:
    pods: "8"
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.memory: 2Gi
"""
        path = _write(text)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("PSA", str(ctx.exception))
        path.unlink(missing_ok=True)

    def test_T04_deny_missing(self):
        text = GOOD.replace("name: default-deny-all", "name: deny-some")
        path = _write(text)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("default-deny-all", str(ctx.exception))
        path.unlink(missing_ok=True)

    def test_T05_pod_selector_not_all(self):
        text = GOOD.replace("podSelector: {}", "podSelector: {matchLabels: {app: x}}")
        path = _write(text)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("podSelector", str(ctx.exception))
        path.unlink(missing_ok=True)

    def test_T06_ingress_only(self):
        text = GOOD.replace(
            "policyTypes: [Ingress, Egress]",
            "policyTypes: [Ingress]",
        )
        path = _write(text)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("Egress", str(ctx.exception))
        path.unlink(missing_ok=True)

    def test_T07_wrong_namespace(self):
        text = GOOD.replace(
            "namespace: ledger-staging",
            "namespace: other-staging",
            1,  # NetworkPolicy only first occurrence after name
        )
        # Also change ResourceQuota namespace
        text = text.replace(
            "name: ledger-quota\n  namespace: ledger-staging",
            "name: ledger-quota\n  namespace: other-staging",
        )
        path = _write(text)
        with self.assertRaises(tc.TenantContractError):
            tc.validate_tenant_file(path, "ledger")
        path.unlink(missing_ok=True)

    def test_T08_missing_quota_and_invalid_yaml(self):
        no_quota = """apiVersion: v1
kind: Namespace
metadata:
  name: ledger-staging
  labels:
    pod-security.kubernetes.io/enforce: restricted
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: ledger-staging
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
"""
        path = _write(no_quota)
        with self.assertRaises(tc.TenantContractError) as ctx:
            tc.validate_tenant_file(path, "ledger")
        self.assertIn("ResourceQuota", str(ctx.exception))
        path.unlink(missing_ok=True)

        bad_yaml = _write(":\n  - not: valid: yaml: [[[")
        with self.assertRaises(tc.TenantContractError):
            tc.validate_tenant_file(bad_yaml, "ledger")
        bad_yaml.unlink(missing_ok=True)

        missing = Path("/tmp/harbour-no-such-tenant-file.yaml")
        with self.assertRaises(tc.TenantContractError):
            tc.validate_tenant_file(missing, "ledger")

    def test_T09_cli_nonzero_on_weakened_fixture(self):
        """CLI smoke: production path fails tenant-missing-deny (policy job would fail)."""
        proc = subprocess.run(
            [
                sys.executable,
                str(BIN / "tenant_contract.py"),
                str(FIX / "tenant-missing-deny.yaml"),
                "sneaky",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertTrue(
            "PSA" in proc.stderr or "default-deny" in proc.stderr,
            proc.stderr,
        )

        ok = subprocess.run(
            [
                sys.executable,
                str(BIN / "tenant_contract.py"),
                str(FIX / "tenant-good.yaml"),
                "ledger",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(ok.returncode, 0, ok.stderr)


if __name__ == "__main__":
    unittest.main()
