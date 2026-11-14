# Gate 2 — Clean-room Harbour protocol

Build Harbour from an empty checkout using only documented instructions. Record everything.

## Preconditions

- Toolchain pins from [TOOLCHAIN.md](TOOLCHAIN.md)
- Fresh machine or disposable VM/container
- No prior Harbour state; empty `$HARBOUR_ROOT`

## Deviation log template

| Step | Command | Expected | Actual | Manual intervention? | Pass? |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Mandatory scenarios

Each failure path must exit **nonzero** with a Harbour-specific message — not an unrelated tool crash mistaken for policy denial.

| ID | Scenario | Expected |
| --- | --- | --- |
| S1 | Normal first deployment | Service HEALTHY; digest matches |
| S2 | Policy-compliant promotion | `promotion-verify` + `policy` pass |
| S3 | Forbidden tenant change (remove default-deny / PSA) | `policy` fails (C-01) |
| S4 | Base-only second runnable workload, unapproved digest | `promotion-verify` fails (C-02) |
| S5 | Missing attestation / release manifest | `promotion-verify` fails |
| S6 | Live ephemeralcontainers privileged debug | Kyverno denial (admit script) |
| S7 | DB damage → successful restore | Equivalence **before** Flux resume (H-01) |
| S8 | Deliberately failed restore (`HARBOUR_RESTORE_FAIL_AFTER=pg_restore`) | Writers stay stopped; operator path |

## Offline subset (this PDP repo)

From `reference/harbour/`:

```bash
python3 -m unittest discover -s tests -v
```

Record results in [`evidence-register.yaml`](../../1%20Foundational%20Documents/evidence-register.yaml).

## Full cluster clean-room

Follow P01–P04 textbooks with scripts copied from this tree into `$HARBOUR_ROOT`. Do **not** mark Final Project Checklist Platform rows complete from this protocol alone — Gate 3 still required for independent acceptance.
