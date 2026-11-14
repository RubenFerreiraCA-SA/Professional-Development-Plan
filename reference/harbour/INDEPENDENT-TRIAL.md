# Gate 3 — Independent learner / platform-user trial

Use existing P03 trial protocol and P04 Gate-5 / ACCEPT-001. Participants must **not** be the material author.

## Participant brief

1. Create a service from the golden path (docs only).
2. Obtain a reviewed, traceable release (digest + provenance).
3. Promote to staging via PR.
4. Diagnose a planted failure using published runbooks.
5. Recover (stateless required; stateful if in scope).

## Metrics to record

| Metric | Value |
| --- | --- |
| Participant role (not name) | |
| Planned hours (module) | |
| Actual completion time | |
| Undocumented assists (count + nature) | |
| Blocked steps | |
| Evidence quality (ACCEPT-001 checklist) | |
| Disposition of findings | |

## Stateful recovery classification

Until an independent operator completes S7/S8 from [CLEANROOM.md](CLEANROOM.md):

- Record `stateful-recovery` in [`evidence-register.yaml`](../../1%20Foundational%20Documents/evidence-register.yaml) as **`author-verified-only`**.
- Do not claim programme operational sign-off for stateful recovery as independently proven.

## Unlock rule

Programme operational sign-off becomes **eligible** only when:

1. Gate 1 documentation re-review accepts Platform textbook.
2. Gate 2 clean-room suite passes (evidence register).
3. This Gate 3 trial passes for P03 + P04 ACCEPT-001 (stateful either independently verified or explicitly footnoted).
