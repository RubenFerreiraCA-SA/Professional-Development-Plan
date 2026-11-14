#!/usr/bin/env python3
"""Production tenant security contract validator (G1-01).

Validates platform/tenants/<name>/tenant.yaml:
- exactly one Namespace named <name>-staging with PSA enforce=restricted on labels
- NetworkPolicy default-deny-all: podSelector {}, policyTypes Ingress+Egress,
  empty/absent ingress and egress
- ResourceQuota in the same namespace without hard limits.cpu
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PSA_ENFORCE = "pod-security.kubernetes.io/enforce"


class TenantContractError(Exception):
    """Contract violation with a specific message."""


def _load_docs(path: Path) -> list[dict[str, Any]]:
    try:
        raw = path.read_text()
    except OSError as e:
        raise TenantContractError(f"missing or unreadable tenant file: {path}") from e
    if not raw.strip():
        raise TenantContractError(f"empty tenant file: {path}")
    try:
        docs = list(yaml.safe_load_all(raw))
    except yaml.YAMLError as e:
        raise TenantContractError(f"invalid YAML in {path}: {e}") from e
    out = [d for d in docs if d is not None]
    if not out:
        raise TenantContractError(f"no YAML documents in {path}")
    for i, d in enumerate(out):
        if not isinstance(d, dict):
            raise TenantContractError(f"document {i} is not a mapping")
        if "kind" not in d:
            raise TenantContractError(f"document {i} missing kind")
    return out


def _meta_ns(doc: dict) -> str | None:
    return (doc.get("metadata") or {}).get("namespace")


def _meta_name(doc: dict) -> str | None:
    return (doc.get("metadata") or {}).get("name")


def validate_tenant_docs(docs: list[dict[str, Any]], service: str) -> None:
    expected_ns = f"{service}-staging"
    namespaces = [d for d in docs if d.get("kind") == "Namespace"]
    nps = [d for d in docs if d.get("kind") == "NetworkPolicy"]
    quotas = [d for d in docs if d.get("kind") == "ResourceQuota"]

    if len(namespaces) != 1:
        raise TenantContractError(
            f"expected exactly one Namespace, found {len(namespaces)}"
        )
    ns = namespaces[0]
    ns_name = _meta_name(ns)
    if ns_name != expected_ns:
        raise TenantContractError(
            f"Namespace name must be {expected_ns!r}, got {ns_name!r}"
        )
    labels = (ns.get("metadata") or {}).get("labels") or {}
    if not isinstance(labels, dict):
        raise TenantContractError("Namespace metadata.labels must be a mapping")
    if labels.get(PSA_ENFORCE) != "restricted":
        raise TenantContractError(
            f"PSA enforce label missing or wrong on Namespace {expected_ns}: "
            f"require labels[{PSA_ENFORCE!r}] == 'restricted'"
        )

    deny = [n for n in nps if _meta_name(n) == "default-deny-all"]
    if not deny:
        raise TenantContractError("missing NetworkPolicy named default-deny-all")
    if len(deny) > 1:
        raise TenantContractError("duplicate NetworkPolicy default-deny-all")
    np = deny[0]
    np_ns = _meta_ns(np)
    if np_ns not in (None, expected_ns):
        # Namespaced objects in a tenant file should target the tenant namespace.
        # None is allowed for single-ns apply contexts; prefer explicit match.
        raise TenantContractError(
            f"default-deny-all NetworkPolicy namespace {np_ns!r} != {expected_ns!r}"
        )
    if np_ns is None:
        # Prefer explicit namespace for teaching clarity — still accept if name matches
        # when the file is applied into the correct namespace by Flux.
        pass
    else:
        if np_ns != expected_ns:
            raise TenantContractError(
                f"NetworkPolicy bound to wrong namespace {np_ns!r}"
            )

    spec = np.get("spec") or {}
    if not isinstance(spec, dict):
        raise TenantContractError("default-deny-all spec must be a mapping")
    pod_selector = spec.get("podSelector", None)
    if pod_selector != {}:
        raise TenantContractError(
            "default-deny-all must have spec.podSelector: {} (all Pods)"
        )
    types = list(spec.get("policyTypes") or [])
    if "Ingress" not in types or "Egress" not in types:
        raise TenantContractError(
            "default-deny-all must include policyTypes Ingress and Egress"
        )
    for direction in ("ingress", "egress"):
        rules = spec.get(direction)
        if rules is None:
            continue
        if rules != []:
            raise TenantContractError(
                f"default-deny-all must not allow {direction} rules "
                f"(got nonempty {direction})"
            )

    if not quotas:
        raise TenantContractError("missing ResourceQuota in tenant manifest")
    for q in quotas:
        q_ns = _meta_ns(q)
        if q_ns is not None and q_ns != expected_ns:
            raise TenantContractError(
                f"ResourceQuota {_meta_name(q)!r} bound to wrong namespace {q_ns!r}"
            )
        hard = (q.get("spec") or {}).get("hard") or {}
        if not isinstance(hard, dict):
            raise TenantContractError("ResourceQuota spec.hard must be a mapping")
        if "limits.cpu" in hard:
            raise TenantContractError(
                f"ResourceQuota {_meta_name(q)!r} sets hard[limits.cpu] "
                f"(forbidden by teaching contract)"
            )
        for key in ("pods", "requests.cpu", "requests.memory", "limits.memory"):
            if key not in hard:
                raise TenantContractError(
                    f"ResourceQuota {_meta_name(q)!r} missing hard[{key}]"
                )


def validate_tenant_file(path: Path, service: str) -> None:
    validate_tenant_docs(_load_docs(path), service)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("tenant_yaml", type=Path)
    p.add_argument("service")
    args = p.parse_args(argv)
    try:
        validate_tenant_file(args.tenant_yaml, args.service)
    except TenantContractError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"OK: tenant contract for {args.service}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
