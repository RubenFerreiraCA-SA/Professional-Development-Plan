# Platform documentation re-review request

**Audit baseline:** `c37e25d` (14 November 2026)  
**Authoritative status:** [review-status.yaml](review-status.yaml)  
**Canonical examples:** [reference/harbour/](../reference/harbour/)

## Request

Please re-review the Platform Engineering textbook (P01–P04) and course detail for **documentation sign-off** against Gate 1 remediations. Do **not** treat this as operational or clean-room verification.

## Gate 1 findings addressed

| ID | Fix location |
| --- | --- |
| C-01 | `reference/harbour/.github/workflows/policy.yml` + `harbour-check-service` |
| C-02 / H-02 | `harbour-promote-verify-images.py` + `promotion-verify.yml` |
| H-01 / M-02 | `restore-verify-before-resume.sh` + `harbour-restore-compare.py` |
| H-03 | `kyverno_deny.py` + `tests/test_kyverno_deny.py` |
| H-04 / M-01 | `TOOLCHAIN.md` + pinned Helm 3.3.4 + pullable admit env |
| M-03 | This status record |

## Still withheld

- Clean-room full Harbour execution (Gate 2) — protocol in `CLEANROOM.md`; offline unit suite green
- Independent learner / operator acceptance (Gate 3) — protocol in `INDEPENDENT-TRIAL.md`
- Stateful recovery: **author-verified-only** until independent operator trial
- Full programme operational sign-off
