# Harbour reference examples

**Classification:** files in this tree are **canonical** (Gate 1 tested). Textbook fences that only summarise behaviour are **illustrative**. Commands that require a constructed Harbour workspace are **copy-and-run with prerequisites**.

This tree is a **teaching subset**, not a full Harbour monorepo. Gate 2 builds a complete workspace from the textbooks.

| Path | Purpose | Class |
| --- | --- | --- |
| `platform/bin/` | Tenant, policy, promotion, restore helpers | canonical |
| `.github/workflows/` | Required PR `policy` and `promotion-verify` | canonical |
| `platform/policy/` | Baseline ClusterPolicy | canonical |
| `platform/drills/stateful-drill.sh` | Full stateful recovery drill | canonical |
| `tests/` | Offline unit/fixture tests (T/P/K/R suites) | canonical |
| `TOOLCHAIN.md` | Pinned versions | canonical |
| `CLEANROOM.md` / `INDEPENDENT-TRIAL.md` | Gate 2 / Gate 3 protocols | copy-and-run |

**Locked choices:** direct Pods supported; same digest across two image repos = unsupported v1; Kyverno chart `3.3.6` + CLI `1.13.4`.

Disposition: [`review-status.yaml`](../../1%20Foundational%20Documents/review-status.yaml) · Charter: [`GATE1-ACCEPTANCE-CHARTER.md`](../../1%20Foundational%20Documents/GATE1-ACCEPTANCE-CHARTER.md).
