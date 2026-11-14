# Harbour reference examples

Canonical scripts, workflows and offline tests for the Platform Engineering textbook (P03–P04).

**Source of truth:** files in this tree. Textbooks cite these paths; do not treat fenced textbook copies as authoritative when they diverge.

| Path | Purpose |
| --- | --- |
| `platform/bin/` | Conformance, policy, promotion helpers, restore compare |
| `.github/workflows/` | Required PR `policy` and `promotion-verify` |
| `platform/policy/` | Baseline ClusterPolicy + fixtures |
| `platform/drills/` | Stateful restore drill |
| `tests/` | Offline unit/fixture tests (no cluster) |
| `TOOLCHAIN.md` | Pinned versions for teaching |
| `CLEANROOM.md` | Gate 2 clean-room protocol |
| `INDEPENDENT-TRIAL.md` | Gate 3 trial protocol |

Disposition: see [`review-status.yaml`](../../1%20Foundational%20Documents/review-status.yaml). This tree is **not** a complete Harbour monorepo — it is the verified teaching subset for Gate 1 controls.
