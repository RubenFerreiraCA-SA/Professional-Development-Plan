#!/usr/bin/env python3
"""G1-04 offline acceptance: R01–R02/R09 + injection name validation + script presence."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRILL = ROOT / "platform" / "drills" / "stateful-drill.sh"
COMPARE = ROOT / "platform" / "bin" / "harbour-restore-compare.py"
VERIFY = ROOT / "platform" / "drills" / "restore-verify-before-resume.sh"

spec = importlib.util.spec_from_file_location("harbour_restore_compare", COMPARE)
cmp_mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(cmp_mod)


class TestRestoreGate1(unittest.TestCase):
    def test_canonical_scripts_exist(self):
        self.assertTrue(DRILL.is_file())
        self.assertTrue(VERIFY.is_file())
        self.assertTrue(COMPARE.is_file())
        # bash -n syntax
        subprocess.check_call(["bash", "-n", str(DRILL)])
        subprocess.check_call(["bash", "-n", str(VERIFY)])

    def test_R01_R02_checksum_logic_documented(self):
        text = DRILL.read_text()
        self.assertIn("backup.sha256", text)
        self.assertIn("checksum changed since copy", text)
        self.assertIn("abort before DB modify", text)

    def test_injection_stages_present(self):
        text = DRILL.read_text()
        for stage in ("suspend", "copy", "pg_restore"):
            self.assertIn(stage, text)
        self.assertIn("unknown HARBOUR_RESTORE_FAIL_AFTER", text)

    def test_equivalence_before_resume(self):
        text = DRILL.read_text()
        # restore-verify must appear before DB_UNSAFE=0 after pg_restore
        restore_section = text.split('restore)', 1)[1]
        idx_verify = restore_section.find("restore-verify-before-resume")
        idx_clear = restore_section.find("DB_UNSAFE=0", restore_section.find("DB_UNSAFE=1"))
        self.assertGreater(idx_verify, 0)
        self.assertGreater(idx_clear, idx_verify)

    def test_R09_json_comparator(self):
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
        msg = cmp_mod.compare(want, got)
        self.assertIn("OK full snapshot equivalence", msg)
        with self.assertRaises(SystemExit):
            cmp_mod.compare(
                {"entries": [{"id": 1, "note": "a", "created_at": "t"}]},
                {"entries": [{"id": 1, "note": "b", "created_at": "t"}]},
            )

    def test_requires_operator_marker_on_unsafe_path(self):
        text = DRILL.read_text()
        self.assertIn("REQUIRES_OPERATOR", text)
        self.assertIn("DB_UNSAFE=1", text)


if __name__ == "__main__":
    unittest.main()
