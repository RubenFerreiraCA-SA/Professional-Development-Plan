# Gate 1 acceptance charter (frozen)

**Baseline SHA:** `d8573e168f7390fd104a9fa69dc33460601bdfb8`  
**Plan:** PDP Definitive Completion and Sign-off Plan v1.0 (14 Nov 2026)  
**Status register:** [review-status.yaml](review-status.yaml)

## Controlling decision

This is an educational programme. Documentation acceptance is **not** held hostage by unbounded hardening. A new issue blocks Gate 1 only if it demonstrably violates a frozen criterion below.

## Locked design choices

| Topic | Decision |
| --- | --- |
| `reference/harbour/` | Retained as canonical teaching subset (not a full Harbour monorepo) |
| Direct Pods in staging overlays | **Supported** — enumerated and provenance-checked like other workloads |
| Two image repos sharing one digest | **Unsupported in v1** — fail with a descriptive error |
| Stateful recovery script | One canonical `reference/harbour/platform/drills/stateful-drill.sh` |
| Kyverno pin | CLI `1.13.4` + Helm chart `3.3.6` (controller appVersion aligned) |

## Example classification

| Class | Meaning |
| --- | --- |
| **canonical** | File under `reference/harbour/`; textbooks cite it; covered by Gate 1 tests |
| **copy-and-run** | Textbook shows commands that assume a constructed Harbour workspace + prerequisites |
| **illustrative** | Shortened outline or pseudocode; must never claim omitted branches exist |

## Frozen work packages and tests

| Package | Tests | Blocks docs sign-off? |
| --- | --- | --- |
| G1-01 Tenant contract | T01–T09 | Yes |
| G1-02 Promotion provenance | P01–P09 | Yes (fixture/mock; live attestations = Gate 2) |
| G1-03 Kyverno evaluation | K01–K08 | Yes (live admission = Gate 2 S6) |
| G1-04 Restore teaching path | R01–R09 | Offline/mocked Gate 1; live R03–R08 = Gate 2 |
| G1-05 Tooling quality | Version/CI checks | Yes |
| G1-06 Status sync | Front-matter consistency | Yes |
| G1-07 Bounded review | ACCEPT/REJECT with IDs | Final decision |

## In scope / out of scope

**In:** Contradictions between P03/P04 and extracted reference; bypassable mandatory controls; tests that pass without exercising claimed checks; restore instruction determinism; accurate statuses/versions.

**Out:** Multi-tenant commercial IDP, production HA, expanded policy catalogues, every CRD, reopening approved DevOps/Cloud/AI chapters, Gate 2/3 as prerequisites for documentation sign-off.

## Stop rule

When all applicable Gate 1 tests pass, Platform documentation is **ACCEPTED** even if clean-room or independent trial has not run. Later discoveries that do not invalidate these criteria are backlog or Gate 2/3, not a moved finish line.
