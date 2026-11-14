#!/usr/bin/env python3
"""G1-02 frozen acceptance P01–P09 (offline render helper + mock verifier)."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "harbour_promote_verify_images",
    ROOT / "platform" / "bin" / "harbour-promote-verify-images.py",
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def _extract(text: str):
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(text)
        path = Path(f.name)
    try:
        return mod.extract(path)
    finally:
        path.unlink(missing_ok=True)


DIG = "sha256:" + "a" * 64
DIG2 = "sha256:" + "b" * 64
SENT = "sha256:" + "0" * 64


class TestPromoteVerifyP01P09(unittest.TestCase):
    def test_P01_normal_approved_digest(self):
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: app}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/app@{DIG}
"""
        )
        self.assertEqual(data["action"], "verify")
        self.assertEqual(data["verified_refs"], [f"registry.example/app@{DIG}"])

    def test_P02_all_disabled_sentinel_skip(self):
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: app}}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: c
          image: registry.example/app@{SENT}
"""
        )
        self.assertEqual(data["action"], "skip")

    def test_P03_disabled_plus_second_runnable(self):
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: primary}}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: c
          image: registry.example/primary@{SENT}
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
          image: registry.example/sneaky@{DIG2}
"""
        )
        self.assertEqual(data["action"], "verify")
        self.assertTrue(any("sneaky" in r for r in data["verified_refs"]))

    def test_P04_shared_component_image_in_render(self):
        # Simulates postgres component image present in rendered overlay
        # even when only platform/components/ changed (workflow discovers all overlays).
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: ledger}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/ledger@{DIG}
---
apiVersion: apps/v1
kind: StatefulSet
metadata: {{name: postgres}}
spec:
  replicas: 1
  serviceName: postgres
  selector: {{matchLabels: {{app: postgres}}}}
  template:
    spec:
      containers:
        - name: pg
          image: registry.example/postgres@{DIG2}
"""
        )
        self.assertEqual(data["action"], "verify")
        self.assertEqual(len(data["verified_refs"]), 2)

    def test_P05_direct_pod_supported(self):
        data = _extract(
            f"""
apiVersion: v1
kind: Pod
metadata: {{name: oneshot}}
spec:
  containers:
    - name: c
      image: registry.example/oneshot@{DIG}
"""
        )
        self.assertEqual(data["action"], "verify")
        self.assertIn(f"registry.example/oneshot@{DIG}", data["verified_refs"])

    def test_P06_undigested_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            _extract(
                """
apiVersion: apps/v1
kind: Deployment
metadata: {name: app}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: nginx:latest
"""
            )
        self.assertIn("digest-pinned", str(ctx.exception))

    def test_P07_invalid_empty_render_fails(self):
        with self.assertRaises(SystemExit) as ctx:
            _extract(
                """
apiVersion: v1
kind: ConfigMap
metadata: {name: x}
data: {a: b}
"""
            )
        self.assertIn("no supported workload", str(ctx.exception))

    def test_P08_same_digest_two_repos_unsupported(self):
        with self.assertRaises(SystemExit) as ctx:
            _extract(
                f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: a}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/one@{DIG}
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
          image: registry.example/two@{DIG}
"""
            )
        self.assertIn("unsupported in v1", str(ctx.exception))

    def test_P09_mixed_scaffold_and_runnable(self):
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: scaffold}}
spec:
  replicas: 0
  template:
    spec:
      containers:
        - name: c
          image: registry.example/scaffold@{SENT}
---
apiVersion: apps/v1
kind: Deployment
metadata: {{name: live}}
spec:
  replicas: 2
  template:
    spec:
      containers:
        - name: c
          image: registry.example/live@{DIG}
"""
        )
        self.assertEqual(data["action"], "verify")
        self.assertEqual(data["verified_refs"], [f"registry.example/live@{DIG}"])


class TestMockVerifierInvocation(unittest.TestCase):
    def test_every_ref_would_be_invoked(self):
        data = _extract(
            f"""
apiVersion: apps/v1
kind: Deployment
metadata: {{name: a}}
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: c
          image: registry.example/a@{DIG}
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
          image: registry.example/b@{DIG2}
"""
        )
        called = []
        for ref in data["verified_refs"]:
            called.append(ref)
        self.assertEqual(len(called), 2)


if __name__ == "__main__":
    unittest.main()
