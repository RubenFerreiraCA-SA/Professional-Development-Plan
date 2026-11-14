#!/usr/bin/env python3
"""Parse Kyverno --policy-report YAML; decide pass/denial outcomes.

Fail-closed: positive checks accept only result=pass (warn is a failure).
Multi-document reports are merged. Per-resource coverage is required when
expected_resources is supplied.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import yaml

# Every rule declared in harbour-baseline.yaml must appear here.
EXPECTED_RULES = (
    "require-image-digest",
    "require-nonroot-memory-limit",
    "require-ephemeral-no-privilege",
)

POLICY_REPORT_KINDS = {"PolicyReport", "ClusterPolicyReport"}


def result_of(r: dict) -> str:
    return str(r.get("result") or r.get("status") or "").lower()


def _resource_keys(r: dict) -> list[str]:
    """Return all resource keys listed on a PolicyReport result entry."""
    res = r.get("resources") or r.get("resource")
    items: list = []
    if isinstance(res, list):
        items = res
    elif isinstance(res, dict):
        items = [res]
    keys = []
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind") or ""
        name = item.get("name") or ""
        ns = item.get("namespace") or ""
        if not kind and not name:
            continue
        keys.append(f"{ns}/{kind}/{name}".strip("/"))
    return keys


def _resource_key(r: dict) -> str | None:
    keys = _resource_keys(r)
    return keys[0] if keys else None


def load_report(text: str) -> dict:
    """Load and merge all PolicyReport / ClusterPolicyReport documents."""
    if not (text or "").strip():
        raise ValueError("empty report")
    idx = text.find("apiVersion:")
    if idx < 0:
        raise ValueError("no PolicyReport YAML")
    docs = list(yaml.safe_load_all(text[idx:]))
    reports = [
        d
        for d in docs
        if isinstance(d, dict)
        and (d.get("kind") in POLICY_REPORT_KINDS or "results" in d)
    ]
    if not reports:
        raise ValueError("unparseable report")
    if len(reports) == 1:
        return reports[0]
    # Merge: concatenate results; keep first metadata.
    merged = dict(reports[0])
    results: list = []
    for rep in reports:
        results.extend(rep.get("results") or [])
    merged["results"] = results
    merged["_merged_report_count"] = len(reports)
    return merged


def outcomes(rep: dict) -> list[tuple[str, str]]:
    out = []
    for r in rep.get("results") or []:
        if not isinstance(r, dict):
            continue
        rule = str(r.get("rule") or r.get("policy") or "")
        result = result_of(r)
        if rule and result in {"pass", "fail", "skip", "warn", "error"}:
            out.append((rule, result))
    return out


def outcomes_with_resource(rep: dict) -> list[tuple[str, str, str | None]]:
    out = []
    for r in rep.get("results") or []:
        if not isinstance(r, dict):
            continue
        rule = str(r.get("rule") or r.get("policy") or "")
        result = result_of(r)
        if not (rule and result in {"pass", "fail", "skip", "warn", "error"}):
            continue
        keys = _resource_keys(r)
        if keys:
            for key in keys:
                out.append((rule, result, key))
        else:
            out.append((rule, result, None))
    return out


def inventory_from_rendered(rendered_yaml: str) -> list[str]:
    """Applicable Pod-shaped resources from rendered manifests (baseline match kinds)."""
    docs = list(yaml.safe_load_all(rendered_yaml or ""))
    keys = []
    for d in docs:
        if not isinstance(d, dict):
            continue
        kind = d.get("kind")
        meta = d.get("metadata") or {}
        name = meta.get("name") or "?"
        ns = meta.get("namespace") or "default"
        if kind == "Pod":
            keys.append(f"{ns}/Pod/{name}")
        elif kind in {
            "Deployment",
            "StatefulSet",
            "DaemonSet",
            "Job",
            "ReplicaSet",
            "CronJob",
        }:
            # Kyverno Pod-controller autogen evaluates Pod templates as Pod results.
            keys.append(f"{ns}/Pod/{name}")
    return sorted(set(keys))


def _rule_matches(observed: str, expected: str) -> bool:
    return observed == expected or expected in observed


def denial_verdict(want: str, rep: dict) -> str:
    """accept | reject-missing | reject-mixed — fail alone is a clean denial."""
    found_fail, has_pass, bad = False, False, []
    for rule, result in outcomes(rep):
        if want not in rule:
            continue
        if result == "fail":
            found_fail = True
        elif result == "pass":
            has_pass = True
        elif result in {"error", "skip", "warn"}:
            bad.append(result)
    if found_fail and (bad or has_pass):
        return "reject-mixed"
    if bad:
        return "reject-mixed"
    if not found_fail:
        return "reject-missing"
    return "accept"


def assert_expected_passes(
    rep: dict,
    apply_rc: int,
    expected: Iterable[str] = EXPECTED_RULES,
    expected_resources: Iterable[str] | None = None,
) -> None:
    """Positive evaluation: only pass is acceptable; warn/fail/error/skip fail closed.

    When expected_resources is set, every (resource, rule) pair must have at least
    one pass result. When unset, every expected rule must have ≥1 pass and no
    non-pass outcomes for that rule.
    """
    expected_list = list(expected)
    got = outcomes_with_resource(rep)
    if not got:
        raise SystemExit(
            "FAIL: PolicyReport.results empty — pin CLI and capture a real report sample"
        )

    by_rule: dict[str, list[str]] = {r: [] for r in expected_list}
    by_pair: dict[tuple[str, str], list[str]] = defaultdict(list)

    for rule, result, res_key in got:
        for exp in expected_list:
            if _rule_matches(rule, exp):
                by_rule[exp].append(result)
                if res_key:
                    by_pair[(res_key, exp)].append(result)

    for exp in expected_list:
        vals = by_rule[exp]
        if not vals:
            raise SystemExit(f"FAIL: expected rule {exp} never evaluated")
        # Fail closed: warn is not a pass.
        if any(r in {"fail", "error", "skip", "warn"} for r in vals):
            raise SystemExit(f"FAIL: rule {exp} results={vals} (only pass accepted)")
        if not any(r == "pass" for r in vals):
            raise SystemExit(f"FAIL: rule {exp} has no pass result: {vals}")

    if expected_resources is not None:
        resources = list(expected_resources)
        if not resources:
            raise SystemExit("FAIL: expected_resources empty")
        for res in resources:
            for exp in expected_list:
                vals = by_pair.get((res, exp), [])
                if not vals:
                    raise SystemExit(
                        f"FAIL: missing evaluation for resource={res} rule={exp}"
                    )
                if any(r != "pass" for r in vals):
                    raise SystemExit(
                        f"FAIL: resource={res} rule={exp} results={vals}"
                    )

    if apply_rc != 0:
        raise SystemExit(f"FAIL: kyverno apply exited {apply_rc}")


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if len(argv) < 1:
        print("usage: kyverno_deny.py <report.yaml>", file=sys.stderr)
        return 2
    rep = load_report(Path(argv[0]).read_text())
    assert_expected_passes(rep, 0)
    print("OK: assert_expected_passes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
