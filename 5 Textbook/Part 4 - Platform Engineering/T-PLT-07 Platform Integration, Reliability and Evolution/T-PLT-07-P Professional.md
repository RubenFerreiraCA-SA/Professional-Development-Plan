# T-PLT-07-P — Professional Engineering

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-p"></a>
#### T-PLT-07-P — Professional Engineering

**Reliability, cost and improvement.** Turn evidence into a backlog; do not leave it as notes.

| Source | Example finding | Platform change |
| --- | --- | --- |
| Acceptance stuck point | The participant could not find the digest after merge | The release summary prints the digest and the next command |
| Stateful drill | Status says HEALTHY while data is wrong | Add a backup-age and data-freshness check; document limits |
| Policy denial | The error did not say how to fix it | Improve the message with a documentation link |
| Game day | The runbook assumed operator access | Split developer and operator runbooks |

**Failure-injection menu — pick, do not do all:** Pod kill; bad promotion (recover with a previous digest); expired or rotated secret; quota exhaustion; missing backup (suspended job triggers a freshness alert); reconciliation suspended (drift); policy engine unavailable; node loss.

**Game days.** Someone other than the author injects a failure from a card; you respond using only the runbook. Convert each confusion into a platform fix and record it. Add a cost line: practice clusters cost no compute, but any cloud-based path needs an estimate, a budget alarm and a teardown.

**SLOs for the platform itself.** The platform is a service with its own reliability: availability of the status command and the delivery path, success rate and latency of promotions and of template generation, freshness of the catalogue, time to first deploy for a new service, and support response time. Measure and publish them; apply the error-budget discipline from T-DEV-06.

**Integration seams — the checklist**

| Seam | What commonly goes wrong |
| --- | --- |
| Template ↔ policy | Generated manifests violate admission rules |
| CI ↔ registry | Digest not recorded or recorded for a different build |
| Promotion ↔ verification | Verification checks the attestation but not the source commit |
| Controller ↔ ownership | Pruning removes something Terraform or a human owns |
| Policy ↔ Pod Security ↔ network policy | Stateful component blocked by default-deny or restricted policy |
| Status ↔ reality | Status reports healthy because it checks too little |
| Backup ↔ restore | Backups never restored; restore command undocumented |

Test each seam with a deliberate negative case.

**The demonstration run.** Map each required demonstration point to evidence; rehearse a run of show (about thirty minutes); run a pre-demonstration checklist (every evidence link resolves, the environment is clean, backups exist, secrets are not in Git, the limitations register is current); prepare for a defence (see T-PLT-05).

**Reflection record.** *Achieved* (with evidence links), *Deferred* (what, why, what it would take), *Learn next* (three items tied to findings), *What surprised me / what I would do differently*. A good reflection is specific and linked to evidence.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Prove integration | End-to-end run with evidence at each seam | Component-level demos only |
| Improve reliably | Backlog from drills, acceptance and support | Notes that never become work |
| Keep honest | Claims ledger and limitations register | Optimistic summaries |
| Control cost | Budgets, teardown, idle policy | Leaving environments running |
| Hand over | Runbooks tested by someone new | Knowledge in one head |
