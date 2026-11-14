# T-PLT-07-I — Intermediate Practice

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-i"></a>
#### T-PLT-07-I — Intermediate Practice

**Integrated demonstration plan.** Choose one runtime and record it. Then build and demonstrate each outcome in order, committing the evidence:

1. **Create:** run the scaffold on a branch, open a pull request, observe the required review (a platform-owned path triggers a platform reviewer — a documented human gate; record the wait). After merge the catalogue lists the service; the status command reports `UNKNOWN` or `DOWN` (nothing promoted), not a false `HEALTHY`.
2. **Reviewed change, trusted build:** open a pull request that breaks a test and show it unmergeable; fix and merge; record commit, run URL, digest and attestation; verify the artefact before promotion.
3. **Self-service deploy:** promote the verified digest to staging by pull request; the required `promotion-verify` and `policy` checks pass; the controller reconciles; confirm that the *running* image digest equals the promoted digest equals the attested digest.
4. **Health, failure, recovery:** kill a Pod; run a drill that breaks a release and recover through Git; if state is in scope, run a restore drill.
5. **Independent acceptance:** a person who did not build the platform does the path with no help (see T-PLT-06).

**Acceptance tasks**

| Task | Standard |
| --- | --- |
| Create and deploy a service | Completed with no undocumented help |
| Make and promote a change | Review, build, promotion all via the documented path |
| Investigate and recover a planted failure | Recovery via the runbook and a pull request |
| Explain the controls | The participant states what blocked an unsafe action and why |

Record findings with severity, and treat any severe finding as a backlog item to fix and re-verify.

**Stateful drills (if state is in scope)**

| Drill | Injection | Evidence |
| --- | --- | --- |
| S1 | Kill an application Pod | Timeline to Ready; client impact |
| S2 | Kill the database Pod | Data survived; time to `query_ok` |
| S3 | Logical damage (delete rows) | Restore from backup; compare fingerprints; recovery-point exposure |
| S4 (optional) | Rebuild: delete the volume and Pod, recreate empty, restore from an off-cluster copy | Counts match; total recovery time |

Fingerprint data before and after (row count and a checksum) so you can show what was and was not recovered.

**Backups that survive the cluster.** Copy a dump *out* of the cluster (not into Git) and test restoring from the copy. A backup that lives only in the cluster dies with it.

**Runbooks for someone who is not you.** A developer runbook ("Not Ready and `database: unreachable` → status → documented first action") and an operator runbook (decision tree: Pod down versus data wrong; exact restore command; verification query; who approves; "do not delete the volume to fix this"). Record which runbook version was used in each drill.

**Exercise.** Run drill S1 and S2 on a practice platform, record the timelines and improve one runbook based on what confused you.
