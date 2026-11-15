# T-PLT-04-P — Professional Engineering

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-p"></a>
#### T-PLT-04-P — Professional Engineering

## Why this matters

At the Professional level the question changes from "can I fix this?" to "can the organisation operate this reliably, repeatedly and when I am not there?" A cluster that is run by one expert's memory is a liability. Professional operations means **claims you can prove**: recovery levels demonstrated by drills, upgrades planned and rehearsed rather than hoped for, backup boundaries that are explicit about what is *not* covered, an incident process with named roles, and playbooks that have been executed by someone who did not write them.

This section covers upgrade and change planning, backup and restore boundaries, incident command, resilience exercises, telling cluster failures from application failures, and building tested playbooks. The language is deliberately that of commitments and evidence: state the target, measure the result, record the gap. Examples use the neutral `orders-api` service, a staging and a production cluster, and a platform team that also serves other product teams. Outputs marked *illustrative* are shapes, not measurements.

## First principles: operations is risk management with feedback

Every operational action trades risk now against risk later. Patching removes known vulnerabilities and adds change risk; an extra replica adds cost and removes failure risk; a rehearsal costs engineer time and removes surprise. Three ideas organise the Professional approach:

1. **Blast radius.** For every change or failure, ask how much is affected: one Pod, one node, one namespace, one cluster, every cluster. Operations design is largely the shrinking and sequencing of blast radius.
2. **Reversibility.** Classify actions as *easily reversible* (scale, Git revert of a Deployment), *reversible with effort* (restore from backup), or *irreversible* (control-plane upgrade, data deletion, key destruction). Spend review effort in proportion to irreversibility.
3. **Evidence over assurance.** "We have backups" and "disaster recovery works" are assertions. A restore drill with timings is evidence. Report the level you *proved* and the date you proved it.

A small vocabulary keeps conversations precise. **RPO** (recovery point objective) is how much data loss is acceptable, measured in time; **RTO** (recovery time objective) is how long recovery may take; **MTTD/MTTR** are time to detect and to restore service, useful as trends and misleading as targets; a **runbook** is a procedure, a **playbook** a decision structure for a scenario, and a **game day** a deliberate exercise of either.

## Recovery levels: claim only what you proved

| Level | What must work after a rebuild | Evidence |
| --- | --- | --- |
| Workload | Application Ready and serving | Deployment Available; client probe |
| Cluster configuration | Access control, admission, quotas and network policy restored | Access tests, policy denials |
| GitOps | Controller installed, sources reachable, everything reconciled, no hand-applied objects | `flux check`; all Kustomizations Ready |
| Platform | Tenant provisioning and the golden path work again | A new service is created end to end |

Do not call a manual `kubectl apply -k` of the app "GitOps recovered". Each level includes the one above it; a report that says "recovered" without naming the level invites the wrong assumption. Record the measured time per level, including human waiting time, not only machine time.

## Cluster failure versus application failure

The first branch in any serious incident is whether the fault is in the **application** (one workload, one team's change) or in the **platform** (something shared). The branch decides who leads, how wide the communication goes and which playbook applies.

| Question | Points to application | Points to platform |
| --- | --- | --- |
| How many workloads are affected? | One service or one team | Several unrelated services at once |
| Did a change precede it? | That service's rollout | Cluster upgrade, node pool, policy, controller, certificate |
| Do other namespaces behave normally? | Yes | No: Pending Pods, slow API, DNS errors across namespaces |
| Where do symptoms cluster? | One Deployment, its dependencies | One node, one zone, one node pool, one add-on |
| Does `kubectl` itself work, and how fast? | Normally | Slow, timing out, or returning 429/5xx |
| Is the control plane healthy? | Yes | `readyz` degraded, webhook errors, etcd latency |

Checks that discriminate quickly, all read-only:

```bash
kubectl get --raw='/readyz?verbose' | head -40                       # API server readiness checks
kubectl get nodes                                                    # how many NotReady, and are they clustered?
kubectl get pods -A --field-selector=status.phase!=Running,status.phase!=Succeeded | head -30
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp | tail -30
kubectl get apiservices | grep -v True                               # unavailable aggregated APIs
kubectl -n kube-system get pods -o wide                              # DNS, CNI, proxy health
kubectl get --raw='/metrics' | grep -E 'apiserver_request_duration_seconds_count|apiserver_flowcontrol_rejected' | head
```

Typical **cross-cutting platform symptoms** and what they imply:

| Symptom across many workloads | Candidate shared cause | First evidence |
| --- | --- | --- |
| Name-resolution timeouts | CoreDNS overloaded or down; network policy; node-local cache | CoreDNS Pods, latency, `kubectl run` DNS test |
| New Pods stay `ContainerCreating` | CNI failure, image registry outage, CSI driver down | Events: `FailedCreatePodSandBox`, pull errors |
| Creates and updates rejected | Admission webhook down or slow | Error naming a webhook; webhook Pods; `failurePolicy` |
| Everything slow, `kubectl` slow | API server or etcd saturation | API latency, etcd metrics, 429s |
| Nodes `NotReady` together | Control-plane connectivity, certificate expiry, bad node image | Node conditions; kubelet logs; time correlation |
| Pods `Pending` everywhere | Capacity cliff, autoscaler stuck, quota | `FailedScheduling` messages; autoscaler events |

Avoid both errors: blaming the platform for an application regression (it follows a deploy), and blaming the application for a platform fault (it is unrelated to any of its changes). When unclear, assign the investigation to both in parallel with a time limit, rather than debating.

## Upgrade and change planning

### Version policy

| Rule | Detail (check the current version-skew policy) |
| --- | --- |
| One minor version at a time | Never skip minors on the control plane |
| Control plane first, then nodes | The kubelet must not be newer than the API server |
| Client skew | `kubectl` within one minor of the API server |
| Read release notes and the deprecation guide | Removed APIs break manifests when applied |
| Add-ons (network plugin, ingress, policy engine) | Have their own compatibility matrices |
| Support window | Minor versions are supported for a limited period; plan a cadence |

Kubernetes ships a new minor version several times a year, and each is supported for a limited period; falling behind forces a multi-step catch-up under time pressure. A cadence (for example, every cluster within N minors of current, upgraded each quarter) is cheaper than periodic emergencies.

### Pre-flight evidence

Plan an upgrade as a **change with a checklist and an owner**, not a command.

| Check | How | Pass condition |
| --- | --- | --- |
| Deprecated or removed APIs in use | `apiserver_requested_deprecated_apis` metric; scanning the Git repository for old `apiVersion`s; running a manifest linter | No workload or controller uses an API removed in the target version |
| Add-on compatibility | Vendor matrices for the CNI, ingress, CSI, service mesh, policy engine, cert-manager, GitOps controller | Every add-on supports the target version, or is upgraded first |
| Chart and operator support | Release notes for each chart/operator | Supported on the target version |
| Disruption budgets | `kubectl get pdb -A` | No budget with `ALLOWED DISRUPTIONS 0` for production workloads |
| Capacity for surge | Allocatable minus requests | Enough headroom to drain one node (or one surge node) at a time |
| Backup and restore point | Fresh etcd snapshot (if self-managed); data backups verified | Restore test is recent; snapshot is off-cluster |
| Webhooks | Compatibility and `failurePolicy` review | A down webhook will not block the upgrade |
| Long-running Jobs and stateful sets | Inventory | Owners notified; windows agreed |
| Rollback plan | Written | See below; includes decision points |

```bash
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis | head
kubectl get deploy,sts,ds -A -o json | jq -r '.items[] | "\(.apiVersion) \(.kind) \(.metadata.namespace)/\(.metadata.name)"' | sort | uniq -c
grep -R --include='*.yaml' -nE 'apiVersion: (extensions/v1beta1|policy/v1beta1|batch/v1beta1)' deploy/
```

### Sequencing the change

```text
1. Freeze unrelated changes (announce the window; agree who may stop it)
2. Upgrade a non-production cluster that mirrors production; run the test suite and soak
3. Take backups; record versions and a baseline (error rate, latency, scheduling latency)
4. Upgrade the control plane (one minor), one control-plane instance at a time where self-managed
5. Verify: API health, controllers, add-ons, workloads, webhook calls
6. Upgrade node pools in waves: canary pool -> a fraction -> the rest, using surge and drain with budgets
7. Verify after each wave against the baseline; pause on regression
8. Upgrade add-ons to their post-upgrade versions; remove deprecated usage
9. Record outcome, time, surprises, and update the checklist
```

For clusters that cannot be upgraded in place, or where rollback certainty is paramount, use **blue/green clusters**: build the new version, deploy the same definitions, shift traffic gradually, and retire the old cluster. It costs duplicate capacity and needs data and DNS strategy; it buys an almost instant rollback.

### Rollback realism

| Component | Rollback reality |
| --- | --- |
| Workload release | Easy: revert desired state |
| Node pool | Usually: add a pool at the old version, drain the new one, if the skew policy allows |
| Add-on | Depends: CRD and storage-version changes may not downgrade cleanly |
| Control plane | **Generally not reversible** after the new version has written data; plan forward fixes and restore from backup only as a last resort |

State this in the plan before starting: "Past step 4 we fix forward. Decision to abort is taken before step 4, on the pre-flight evidence."

### The change record

Every manual intervention and every planned change gets a record; it is the artefact that makes incidents shorter later.

```markdown
## Change record
- **ID / title:** CH-2026-114 — Upgrade prod-eu-1 control plane to the next minor
- **Owner / approver:** <names>   **Window:** Sat 06:00–10:00, comms in #platform-changes
- **Risk and blast radius:** shared control plane; all tenants
- **Pre-flight evidence:** links (deprecation scan, add-on matrix, backup verification, PDB report)
- **Steps and verification after each**
- **Abort criteria and decision point**
- **Rollback / fix-forward plan**
- **Outcome:** times, observations, deviations, follow-ups
```

## The operating cadence

| Frequency | Activity |
| --- | --- |
| Per change | Server-side dry-run, review of platform manifests |
| Weekly | RBAC audit, expired identities, quota headroom |
| Monthly | Namespace rebuild drill; image and vulnerability re-scan |
| Per release or quarterly | Upgrade rehearsal; review of the version-support window |
| Annually | Re-test the runbook with someone who did not write it |

The cadence is a commitment of capacity: if nobody owns the calendar, the drills quietly stop and the claims silently expire. Put each item in a tracker with an owner and a "last done" date, and report overdue items alongside incidents.

## Backup and restore boundaries

A backup is only meaningful when you can state **what it covers, what it does not, where it lives, and how long a restore takes**. Kubernetes makes the boundaries easy to blur, so write them down.

| Concern | Practice |
| --- | --- |
| Definitions and policy | In Git; the primary disaster-recovery path |
| Persistent data | Application-consistent backups; test restore; off-cluster copy |
| etcd | Regular snapshots, protected, restore drills (if self-managed) |
| Secrets | Recovery means reconnecting the external source, not restoring from Git |
| Identities | Re-issue after rebuild; know what died with the CA |
| Registry | Mirror or back up release images; digests need the registry |

State **RPO and RTO targets** first, then measure. A backup that lives only in the cluster dies with the cluster; keep a copy outside it. Do not delete a data volume to "fix" a database; restore through the documented procedure.

### What each mechanism does and does not cover

| Mechanism | Covers | Does not cover |
| --- | --- | --- |
| Git (desired state) | Deployments, Services, policies, RBAC definitions | Data, runtime-created objects, Secrets held outside Git, anything applied by hand |
| etcd snapshot | The whole API object store at one instant | Volume contents, external resources, anything created after the snapshot; restoring rewinds all of it |
| CSI volume snapshot | A point-in-time copy of a volume (often in the same storage system and failure domain) | Application consistency unless quiesced; protection from storage-system loss unless replicated elsewhere |
| Application backup (for example database dump or continuous archive) | Consistent data, point-in-time recovery | Cluster configuration |
| Cluster-level backup tool (object plus volume) | Selected namespaces and resources, with volume snapshots | Cluster-scoped secrets of trust, cloud resources, what you excluded |
| Provider-managed backup | Control plane state per provider terms | Your data, your workloads; terms and retention vary |

The boundary questions to settle in writing:

- **Consistency.** A volume snapshot of a running database may be crash-consistent only. Which workloads need quiescing or an application-native backup?
- **Location and blast radius.** Is the copy in another account, region or failure domain? Is it **immutable or access-separated** so that an attacker or a bad script cannot delete it along with the original?
- **Restore ordering.** Namespaces, CRDs, storage classes and secrets before workloads; data before the application that expects it.
- **Dependencies.** Restoring a Deployment does not restore the DNS record, the load balancer, the certificate issuer or the identity provider federation it depends on.
- **Time.** Restores are slower than backups. Measure restore throughput for your data size before promising an RTO.
- **Verification.** A restore test that includes a query proving data integrity, and an application-level smoke test, not just "the files exist".

A restore drill pattern:

```bash
# 1. Restore into an isolated namespace or cluster, never over the live one
# 2. Restore data from the latest backup and record the elapsed time
time restore-orders-db --from latest --target orders-restore-test
# 3. Verify
kubectl -n orders-restore-test exec deploy/orders-db -- psql -c "select count(*), max(created_at) from orders;"
# 4. Compare against the expected RPO: how old is max(created_at)?
# 5. Record: restore time, data age, issues, who needed to be involved
```

## Incident command

During a serious incident the technical problem competes with a coordination problem. Structure removes the second so people can work on the first.

### Roles

| Role | Responsibility | Not responsible for |
| --- | --- | --- |
| **Incident commander** | Owns the incident: sets priorities, assigns tasks, decides on risky actions, declares start and resolution | Hands-on debugging (delegate) |
| **Operations lead / responders** | Investigate and change systems, report findings and actions to the commander | Customer communication |
| **Communications lead** | Status updates to stakeholders and customers on a regular cadence | Technical decisions |
| **Scribe** | Keeps the timeline: time, observation, action, who | Anything else |
| **Subject-matter experts** | Called in for specific systems (storage, networking, application) | Running the incident |

In a small team, one person may hold two roles, but **the commander and the primary debugger should be different people**: the person with their head inside a terminal cannot also watch the clock and the customers. Handover is explicit: "I am handing command to Sam; current state is ...; open actions are ...".

### Severity and cadence

| Severity | Example | Response |
| --- | --- | --- |
| SEV1 | Production unavailable or data at risk | Page immediately; commander assigned; updates every 15–30 minutes |
| SEV2 | Major degradation, workaround exists | Page; commander; updates hourly |
| SEV3 | Minor impact | Ticket; handled in hours |
| Near miss | No impact, but could have | Review, no page |

Severity is **declared early and revised freely**; under-declaring costs more than over-declaring.

### The flow

```text
Detect -> Declare (severity, commander, channel) -> Stabilise -> Diagnose -> Fix -> Verify -> Resolve -> Review
```

1. **Declare.** Open one channel, name the commander, state the symptom, the start time and the impact.
2. **Stabilise before diagnosing deeply.** Prefer reversible actions that stop the bleeding: revert the last change through Git, scale up, shift traffic, disable a feature, cordon a bad node, pause a rollout. Understand later.
3. **Diagnose with the evidence loop.** Assign hypotheses to responders; each reports back with evidence, not opinion.
4. **Decide risky actions explicitly.** The commander states the action, its blast radius, its reversal and who executes it. Say it aloud in the channel before doing it.
5. **Verify with the customer's view.** Resolution is declared on evidence (error rate, a client probe), not when the last command finished.
6. **Communicate on a clock.** A short, honest update on schedule is better than silence. Use the format: *what we know, what we are doing, what we do not know yet, next update at HH:MM*.
7. **Review.** Blameless, within days, with a timeline and tracked actions.

Prefer fixing through Git so the record and the cluster agree. When an emergency requires a live change, record it and **backport it to the source of truth immediately**; otherwise the controller reverts it, or the defect returns on the next sync.

### Communications template

```text
[HH:MM] SEV2 — orders checkout degraded (started 08:30)
Impact: ~30% of checkout requests fail; browsing unaffected.
Status: investigating; a deployment at 08:25 is the suspected trigger.
Actions: reverting the 08:25 change; verifying error rate.
Next update: 09:00 or on change.
```

### Blameless review

A good review is built on a timeline, not on verdicts. It asks **how the system allowed a reasonable person to make that decision**, not who to blame. Include detection (how long before we knew, and how), the response (what slowed us down), contributing factors, what went well, and actions with owners and dates. Reviews that produce no tracked actions, or actions that are never completed, are theatre. Track the closure rate.

## Resilience exercises

Practice is the only way to know whether the playbooks and the people work.

| Exercise | What it tests | Scope and safety |
| --- | --- | --- |
| **Tabletop** | Roles, communication, decision-making, playbook clarity | Discussion only; walk a scenario with an inject every few minutes |
| **Blind drill** | Diagnosis skill using only the runbook | Staging; someone else injects a known fault |
| **Namespace rebuild** | Definitions in Git, ordering, guardrails | Practice namespace; stopwatch |
| **Node drain and loss** | PDBs, spreading, time to reschedule | Staging; measured client loop |
| **Restore drill** | RPO/RTO, backup integrity, application recovery | Isolated target; never over production |
| **Upgrade rehearsal** | Pre-flight checklist, timing, rollback decisions | Production-like non-production cluster |
| **Game day** | Whole system, including people, alerts, communication | Pre-agreed scope, abort criteria and an observer |
| **Chaos experiment** | A specific hypothesis about resilience | Small blast radius, steady-state metric, abort switch |

An experiment is structured like a test:

```markdown
## Experiment: lose one node pool zone in staging
**Hypothesis:** orders-api stays above 99% success and recovers capacity within 10 minutes if one zone's nodes are cordoned and drained.
**Steady state:** success rate ≥ 99.5%, p95 < 300 ms, all Deployments Available.
**Blast radius:** staging only; stop if success < 95% for 2 minutes.
**Method:** cordon and drain all nodes in zone a; observe.
**Observers:** two; one watching dashboards, one logging a timeline.
**Result:** (measured) …
**Gaps found → actions:** …
```

Run exercises with someone who did not write the playbook driving it; the aim is to find the places where the document assumed knowledge. Record **every surprise** as an action. An exercise that finds nothing was either too easy or too gentle.

## Tested playbooks

A playbook is a scenario-driven decision structure. Its value comes from being **tested**, so keep an inventory with a last-tested date.

| Playbook | Trigger | Key decisions | Last tested |
| --- | --- | --- | --- |
| Stalled rollout | `ProgressDeadlineExceeded` | Revert or fix forward; scope of impact | Record the date |
| Node loss | Node(s) `NotReady` | Wait, replace, or investigate common cause | |
| Namespace deletion | Namespace missing | Rebuild from Git; data restore | |
| Certificate expiry | Alert or `x509` errors | Renew, restart components, verify | |
| DNS failure | Cluster-wide resolution errors | Scale CoreDNS, check policy, fail over | |
| Capacity cliff | Widespread `Pending` | Add capacity, shed load, adjust priorities | |
| Webhook outage | Creates rejected | Restore, or temporarily relax policy with approval | |
| Credential compromise | Alert or report | Revoke, rotate, review audit logs | |
| Failed upgrade | Control-plane or add-on regressions | Pause, fix forward, restore | |

Playbook skeleton (extends the runbook skeleton below):

```markdown
# Playbook: <scenario>
## Trigger and how to confirm   - alerts, symptoms, discriminating checks
## Severity and who leads        - default severity; commander; experts to page
## Stabilise                     - reversible actions first
## Diagnose                      - hypotheses and the checks that separate them
## Fix and verify                - procedures; the customer-view verification
## Do not                        - dangerous shortcuts specific to this scenario
## Communicate                   - template and cadence
## Evidence to preserve          - logs, events, snapshots before they expire
## Last tested / by whom / gaps
```

**Keep the playbooks where you can read them when the cluster is down.** A runbook hosted only on the failing platform is useless; keep copies in a separate system, and test that responders can reach them with only their break-glass access.

### Runbook skeleton

```markdown
# Cluster runbook
## Scope and limits   - what this covers, what it does not
## Access             - how to get in, break-glass procedure, how to revoke
## Triage             - the ladder; symptom → first check table
## Procedures         - drain, restore namespace, rotate credentials, upgrade
## Known gaps         - honest list (single node, unencrypted secrets on practice cluster, ...)
## Escalation         - who, when
```

Keep an operation record template (what changed, who approved, evidence, rollback) for every manual intervention.

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Take a node out | Cordon, drain with a measured client loop | Deleting Pods directly |
| Recover from a bad release | Revert desired state in Git | Live edits that Git will undo |
| Back up | Definitions in Git; data via application backups; copy off-cluster | "PVC equals backup" |
| Upgrade | Rehearse, one minor at a time, check deprecations | Skipping versions |
| Claim recovery | State the level you proved | "Disaster recovery works" without a drill |
| Decide cluster or app fault | Count affected workloads; check what changed; test shared components | Debating before checking |
| Run an incident | Name a commander; stabilise first; communicate on a clock | Everyone debugging in parallel without a lead |
| Write a playbook | Trigger, stabilise, diagnose, verify, do-not, last-tested | Essays no one has executed |

## Professional trade-offs

| Trade-off | Options | Guidance |
| --- | --- | --- |
| In-place upgrade versus blue/green cluster | Cost and speed versus rollback certainty | In place with rehearsal for most; blue/green for high-risk or regulated systems |
| Frequent small upgrades versus rare large ones | Steady effort versus big-bang risk | Prefer frequent: smaller diffs, practised procedure |
| Strict PDBs versus maintenance ease | Availability versus operability | Size budgets to replicas; test drains in CI |
| Many drills versus delivery time | Reliability versus features | Fund drills as capacity, tied to the risks you own |
| Centralised on-call versus team ownership | Consistency versus context | Platform owns cluster; teams own applications; clear hand-off criteria |
| Aggressive automation versus human approval | Speed versus blast radius | Automate reversible steps; gate irreversible ones |

## What can go wrong: a short catalogue

| Failure | Why it happens | Prevention |
| --- | --- | --- |
| Upgrade breaks workloads | Removed API in use; add-on incompatibility | Deprecation scan; rehearsal; canary pool |
| Backup restore fails | Never tested; snapshot only crash-consistent | Scheduled restore drills with verification |
| Backup deleted with the cluster | Stored only in the failure domain | Off-cluster, access-separated copies |
| Everyone debugging, nobody leading | No commander | Named roles; commander is not the debugger |
| Fix undone by the controller | Live edit of a Git-managed object | Revert in Git; backport emergency edits |
| Runbook unreachable in the outage | Hosted on the failing cluster | Independent copies; break-glass test |
| "Recovered" without proof | Claim without a level | State the level and the evidence |
| Action items never close | No owner or tracking | Owners, dates and a closure report |

## Knowledge consolidation

- Professional operations is risk management with feedback: blast radius, reversibility, evidence over assurance.
- Recovery claims name a **level** (workload, configuration, GitOps, platform) and the evidence.
- Decide **application versus platform** by counting affected workloads, checking what changed and testing shared components.
- Upgrades are planned changes: pre-flight evidence, one minor at a time, canary node waves, a stated point beyond which you fix forward.
- Control-plane upgrades are generally not reversible; rollback realism belongs in the plan.
- Backup boundaries are explicit: what each mechanism covers and does not; consistency; location; ordering; restore time measured.
- Incidents need named roles, severity, stabilise-first, a communication cadence and a blameless review with tracked actions.
- Exercises (tabletop, drill, restore, rehearsal, game day) are the only evidence that playbooks work; each surprise becomes an action.
- Keep recovery documents and break-glass access outside the failure domain.

## Exercises

**Exercise 1 — Recovery level audit.** For your practice platform, state for each of the four recovery levels whether you have *proved* it, when and how long it took. Mark each unproved level as a gap with an owner.

**Exercise 2 — Upgrade plan.** Write a change record for the next minor upgrade of a staging cluster: pre-flight evidence, sequence with verification points, abort criteria, and rollback realism. Run the deprecation scan and attach its output.

**Exercise 3 — Backup boundary table.** For `orders-api` and its database, fill the covers/does-not-cover table for each mechanism you use. Identify one failure that none of them covers.

**Exercise 4 — Restore drill.** Restore the database into an isolated namespace. Record restore time, the age of the newest row (actual RPO) and an integrity query result. Compare with your stated RPO and RTO.

**Exercise 5 — Tabletop.** Run a 45-minute tabletop with four people: "nodes become NotReady across two zones after a pool image update". Assign commander, scribe and comms; inject a new fact every ten minutes. Write down every decision that lacked an owner.

**Exercise 6 — Application or platform?** Given three scenarios (one service fails after its deploy; DNS fails for all namespaces; Pods Pending in every namespace), list the first three checks for each and the evidence that would change your answer.

**Exercise 7 — Playbook cold read.** Write a playbook for certificate expiry, then have a colleague execute it in staging with you silent. Count the questions they asked; each is a defect.

**Solution notes.**

*Exercise 1.* Expect the Workload level to be proved, Cluster configuration partially, and GitOps and Platform often unproved. The honest result is a gap list, not a green table.

*Exercise 2.* A strong plan has a decision point before the control-plane step, per-wave verification against a baseline, and a statement that after the control plane is upgraded the response is fix forward. Weak plans list commands without verification or abort criteria.

*Exercise 3.* Typical gaps: volume snapshots in the same failure domain as the volume; secrets referenced from Git but not recoverable; DNS and certificate-issuer configuration outside any backup.

*Exercise 4.* Compare the measured RPO with the stated one; when the newest row is older than the objective, either the backup schedule or the objective must change. Restore time scales with data size; record the size.

*Exercise 5.* Typical findings: unclear who may stop a rollout, no one tracking time, comms drifting to speculation, and the playbook living on the affected platform.

*Exercise 6.* Scenario 1: that Deployment's history, events and logs; other namespaces fine. Scenario 2: CoreDNS Pods, DNS test from a Pod in two namespaces, recent policy or CoreDNS change. Scenario 3: `FailedScheduling` messages, node conditions, autoscaler and quota. Evidence that would change the answer: a platform change just before an apparent application fault, or a single namespace's quota behind an apparent cluster-wide problem.

*Exercise 7.* Each question is a missing instruction: unclear command context, missing permission, unstated expiry date source, or no verification step. Fix the document, then repeat with another colleague.
