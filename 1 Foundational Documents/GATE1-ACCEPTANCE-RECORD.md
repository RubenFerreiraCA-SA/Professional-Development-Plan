# Gate 1 acceptance record

| Field | Value |
| --- | --- |
| Baseline | `d8573e168f7390fd104a9fa69dc33460601bdfb8` |
| Candidate sign-off SHA | _(set after merge of this remediation wave)_ |
| Documentation QA URL | _(set after green `docs-qa` on candidate SHA)_ |
| Charter | [GATE1-ACCEPTANCE-CHARTER.md](GATE1-ACCEPTANCE-CHARTER.md) |
| Status register | [review-status.yaml](review-status.yaml) |

## Frozen suite results (author self-check before G1-07 reviewer)

Run: `python3 -m unittest discover -s reference/harbour/tests -v`

| Suite | IDs | Result |
| --- | --- | --- |
| Tenant | T01–T09 | **PASS** (offline; T09 CLI smoke) |
| Promotion | P01–P09 | **PASS** (fixture/mock; live attestations = Gate 2) |
| Kyverno | K01–K08 | **PASS** (offline + sample report; live admission = Gate 2 S6) |
| Restore instructional | R01–R02, R09 + script presence / inject / order | **PASS** offline; **R03–R08 live = NOT RUN** (Gate 2) |
| Version/CI checks | Helm 3.3.6 pin, bash -n, compileall, docs-qa | **PASS** locally for unit/syntax; Actions URL pending merge |

## Accepted limitations

- Harbour full clean-room (Gate 2) and independent learner trials (Gate 3) are **not** implied.
- `harbour-verify-artifact` remains a Gate 2 dependency when constructing the full Harbour workspace.
- Sample PolicyReport fixture is representative of CLI 1.13.4 schema; replace with a machine-captured sample when Kyverno CLI is available in CI.

## Reviewer verdict (G1-07)

| Field | Value |
| --- | --- |
| Result | `PENDING REVIEW` — author evidence ready; reviewer fills ACCEPT/REJECT |
| If rejected, exact failed IDs | |
| Reviewer | |
| Date | |

> Platform documentation may be **ACCEPTED** when the reviewer confirms all applicable Gate 1 tests above. Do not reopen for backlog hardening ideas.
