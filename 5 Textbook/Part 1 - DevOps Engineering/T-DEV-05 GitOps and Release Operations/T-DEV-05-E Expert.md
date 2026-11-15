# T-DEV-05-E — Expert Depth

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-e"></a>
#### T-DEV-05-E — Expert Depth

## Why this level exists

At Professional level you can run GitOps for a service. At Expert level the questions change in kind. What guarantees does a reconciler actually give, and where do they stop? If an attacker controls one component, what do they reach? How do you roll a change across forty clusters without a forty-way outage? Why does the controller sometimes fail in ways that retrying cannot fix? What does "recovered" mean after a regional loss, and what can Git never give back? And how do you organise people so that all of this stays understandable in three years?

This section answers with mechanisms, failure modes, and trade-offs rather than recipes. Where a claim depends on a particular tool version, it is flagged. The examples remain neutral (`orders-api`, `example-org`); outputs marked *illustrative* show shapes, not measurements. As in earlier sections, claim only what you have demonstrated: a recovery plan you have not rehearsed and a policy you have not seen block anything are hypotheses.

## Reconciliation theory, precisely

A GitOps controller is a **control loop**: observe, diff, act, repeat. Understanding its formal character explains most expert-level behaviour.

**Level-triggered, not edge-triggered.** The loop acts on the *current difference* between desired and actual, not on "an event happened". If a notification is lost, the next pass still finds the difference. This is why reconciliation recovers from missed webhooks and controller restarts, and why webhooks and `reconcile` commands are merely accelerators on top of a timer.

**Eventually consistent, not transactional.** The loop guarantees convergence *over time if conditions allow*, with none of the properties of a database transaction:

| Property | Reconciler | Transaction |
| --- | --- | --- |
| Atomicity across objects | No: objects are applied individually, in an order that is only partly controllable | Yes |
| Isolation | No: other writers, and users, see intermediate states | Yes |
| Rollback on failure | No: partial application persists; "undo" is a *new* desired state | Yes |
| Convergence | Yes, if nothing keeps it from converging | Not applicable |

Consequences: ordering across objects needs explicit expression (`dependsOn`, health-gated dependencies, Argo CD sync waves, or hooks); every action must be **idempotent** because failures are retried; and "Ready" means exactly what your health checks define, so weak checks yield false confidence.

**The diff is a function of three inputs**, and each can be wrong in a different way:

```text
 desired (rendered from Git)   ─┐
 live (read from the API)       ├─▶  diff  ─▶  plan  ─▶  apply  ─▶ new live
 last-applied / managed fields ─┘
```

The third input is easy to overlook. Modern controllers use **server-side apply** and compare using *managed fields*: for each field, Kubernetes records which manager (`kustomize-controller`, `kubectl`, an HPA, an operator) last set it. The controller will overwrite fields it manages and, by default, take ownership on conflict; it will *not* touch fields it never declared. This is both the mechanism that lets an autoscaler coexist with Git, and a source of subtle faults: an operator that writes a field Git also declares causes a perpetual tug-of-war ("flapping"), visible as a steady stream of reconcile events with no net change.

**Convergence time is a budget.** Time from merge to serving is the sum of: Git poll or webhook delay; artifact fetch; render; dry-run and diff; apply; image pull; Pod start; readiness; health-check wait. In a large fleet each stage has a distribution, and the *tail* determines how long an incident lasts. Measure it. A typical discipline is to emit a metric at each stage and set an objective, for example "99 percent of production merges serving within ten minutes".

**Thrash and amplification.** A controller that re-renders and re-applies thousands of objects every interval creates API-server load proportional to *objects times clusters*, even when nothing changes. Mitigations: longer intervals with webhook-triggered pulls for speed, one Kustomization per service rather than one per cluster, and server-side dry-run diffing (apply only when different) as the default. Watch API-server latency and controller work-queue depth as indicators.

**Health is a model of the world.** A health check approximates "the service works" using what the controller can see. It cannot see the database credential that was rotated, the downstream that is slow, or the customer-facing error rate. The deeper the check the better the signal, but the more it couples deployment to other systems. Decide which dependency failures should *block a rollout* (the new version cannot reach its database) and which should merely alert.

## Controller trust and security boundaries

The strongest property of pull-based delivery is that **production credentials stay inside the environment**. Expert design asks how to preserve that property and what else the model must trust.

### What the controller trusts

```text
 Git (desired state) ─┐
 Registry (artifacts)  ├─▶ controller ─▶ cluster API (with some identity)
 Secret manager (keys) ┘
```

Every arrow is trust. A reconciler will faithfully apply *anything* that arrives through them with the privileges of its identity. The questions:

| Component | If an attacker controls it… | Controls |
| --- | --- | --- |
| Desired-state repository (write) | They deploy anything the controller's identity may create | Branch protection, code owners, signed commits, required checks; admission policy that does not trust the repository |
| A maintainer's account | Same, with legitimate-looking history | Phishing-resistant authentication, mandatory review by a second person, alerts on bypass |
| Registry (write) | They swap an artifact behind a tag | Digest pinning; signature verification at admission |
| Build system | They publish a malicious image with valid-looking provenance | Isolated builders, short-lived credentials, provenance bound to a specific workflow identity (T-DEV-03) |
| The controller's service account | They apply anything that account may | Least privilege per tenant; no cluster-admin; audit logging of the controller's actions |
| The controller process or image | They read credentials and act as the controller | Pinned, verified controller images; network policy; minimal secrets mounted; control-plane isolation |
| The cluster API | Out-of-band changes bypass Git | Restrict direct write; audit; detect drift and alert; admission |
| Secret manager | They read or alter secrets | Strong access policy; audit; short-lived credentials |

A recurring insight: **merging to the desired-state repository is a production deployment**, so the repository deserves *stricter* controls than application code, not weaker. Review of that repository should check *effects* (what objects will exist) rather than only text, which is why rendered diffs in pull requests matter.

### Verifying what the controller consumes

Flux can verify signatures on what it fetches, so that a compromised network path or mirror is not enough:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: { name: orders-platform, namespace: flux-system }
spec:
  interval: 1m
  url: ssh://git@github.com/example-org/orders-platform
  ref: { branch: main }
  verify:
    mode: head                         # require a valid signature on the commit
    secretRef: { name: trusted-signers }   # public keys that are allowed
```

For OCI artifacts the analogue is verifying a cosign signature on the configuration artifact (field names and supported methods vary by version; check the documentation for yours). Signed commits protect against a *stolen read/write token* but not against a *legitimate maintainer making a bad change*; combine with review.

### Defence in depth when the repository is compromised

Suppose an attacker obtains write access to the desired-state repository. What still stops them?

1. **Required review.** If a compromised account can merge alone, nothing else matters, so require a second approver for protected paths and alert on administrator bypass.
2. **Admission policy independent of Git.** Reject privileged Pods, host mounts, unsigned images, images not from your registry, and cluster-scoped kinds from tenant reconcilers. The attacker must now defeat a separate system with separate owners.
3. **Scoped identities.** A tenant's reconciler cannot create cluster roles even if told to.
4. **Egress and network policy.** An applied malicious workload cannot exfiltrate freely.
5. **Detection.** Alerts on new privileged workloads, on suspension, on changes to controller or policy objects, and on unusual image sources.

Draw the same table for each *independent* control and ask: does it share an owner, credential or failure mode with the thing it is protecting? If so, it is not independent.

### The bootstrap problem

Something must install the controller and give it its first credentials. That "something" (a person, a script, infrastructure as code) holds elevated power briefly. Treat the bootstrap path as a high-risk, logged procedure: use short-lived credentials, run it from a controlled environment, record it, and have the controller manage its own upgrades afterwards. Conversely, when the cluster is destroyed and rebuilt, the same bootstrap must work *from nothing*, which is why it must be scripted and tested rather than remembered.

## Multi-cluster and fleet operations

### Topologies

| Topology | How it works | Strengths | Weaknesses |
| --- | --- | --- | --- |
| **Controller per cluster (pull)** | Each cluster runs its own controller reading Git | Credentials stay local; a cluster operates if the control plane or Git is down; failures isolated | Many controllers to upgrade; no single view without extra tooling |
| **Hub and spoke** | A management cluster runs controllers that apply to many clusters | Single view; central policy; fewer controllers | Hub holds credentials for every spoke; hub failure stops *changes*; hub compromise is fleet compromise |
| **Hybrid** | Per-cluster controllers for workloads; hub for fleet inventory, observation and rollout orchestration | Balances isolation and visibility | More concepts; orchestration layer must itself be reliable |

The security argument usually favours per-cluster pull for production, with a separate observation layer. The operational argument favours a hub for visibility. Choose consciously and write down which failure you accept.

### Layering configuration across a fleet

A fleet needs a *hierarchy of defaults* with controlled overrides:

```text
 fleet-wide base            (policies, add-ons, baseline limits)
   └── environment layer    (staging vs production settings)
         └── region/cloud layer   (endpoints, storage classes)
               └── cluster layer  (identity, name, small exceptions)
```

Each layer is a Kustomize base or a Helm values file. Rules that keep it sane: lower layers may *override* but not *delete* upper-layer policy; every cluster-level exception is a file with an owner and an expiry; and a periodic job renders every cluster and reports which clusters differ from the fleet baseline and why. When a cluster's rendering cannot be explained by layers, you have an undocumented snowflake.

### Generating many Applications

With Argo CD, an `ApplicationSet` stamps out one application per cluster or per directory:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: { name: orders-api, namespace: argocd }
spec:
  generators:
    - clusters:
        selector: { matchLabels: { env: prod } }
  template:
    metadata: { name: 'orders-api-{{name}}' }
    spec:
      project: orders
      source:
        repoURL: https://github.com/example-org/platform-config
        targetRevision: main
        path: 'apps/orders-api/overlays/prod'
      destination: { server: '{{server}}', namespace: orders-prod }
      syncPolicy: { automated: { prune: true, selfHeal: true } }
```

This is powerful and dangerous in the same way: one commit can change every selected cluster at once. A fleet that applies a merge to all clusters simultaneously has *no containment*. Expert practice puts a rollout structure around generators.

### Progressive rollout across clusters (rings)

```text
 ring 0: canary cluster (internal traffic only)      ← first, always
 ring 1: one low-risk production cluster             ← after soak, automated checks pass
 ring 2: 10% of production clusters, mixed regions
 ring 3: the rest, region by region
```

Implement rings by giving each cluster a ring label and having each ring track a *different revision* of the desired state:

- **Branch or tag per ring**: ring 0 follows `main`; ring 1 follows tag `ring1`, which an automated job advances only after ring 0's checks pass for a soak period; and so on.
- **Per-ring digest files**: the overlay for ring N references a digest that a promotion job writes after the previous ring is healthy.

An automated promotion job needs three things: a *health definition* it can compute (error ratio, saturation, controller Ready), a *soak time*, and a *halt* that is cheaper than the fault. If any ring's signal degrades, the job stops advancing rings and pages a human; it does not roll back *clusters it cannot understand*. Record each ring's revision in a fleet inventory so "which clusters run which release?" is a query, not an investigation.

### Skew and drift between clusters

Fleets accumulate **version skew** (controller versions, add-ons, Kubernetes versions) and **configuration drift** (exceptions). Control them with: a supported-skew policy (for example no more than two versions behind), a dashboard of versions per cluster, a rule that clusters out of policy are blocked from receiving new releases of components that depend on the missing features, and scheduled upgrades with owners. Remember that **controller versions affect API behaviour**: a CRD API version present in one cluster may be absent in another, and the same manifest can succeed in one and fail in the other.

### Fleet identity and inventory

Clusters should have stable identities (name, environment, region, ring, owner) stored as data, and credentials *per cluster*, rotated independently. When one cluster's credentials leak, you want a one-cluster incident. A central inventory (itself in Git, or generated from infrastructure as code) lets generators and rollout tools select clusters by label rather than by hand-maintained lists.

## Reconciliation failures at depth

Basic failures (bad YAML, bad credentials, failed health) are covered earlier. Expert failures come from interactions.

| Failure | Mechanism | Detection | Mitigation |
| --- | --- | --- | --- |
| **Prune deletes the wrong thing** | Ownership overlap, a path moved, or a Kustomization removed with prune and cascade enabled | Review of removals; inventory diff; alerts on mass deletion | Ownership lists, prune exclusions, a "deletion budget" check in CI, retained storage |
| **Flapping** | Two writers for one field (operator, autoscaler, admission mutation) | Constant reconcile events without net change; managed fields show two managers | Single owner; remove field from Git; `ignoreDifferences` or equivalent |
| **Stuck reconciliation** | Failed health check, dependency never Ready, wait timeout | Alert on not-Ready duration; controller status | Timeouts and alerts; break dependency cycles; repair the dependency |
| **CRD ordering failure** | Custom resource applied before its CRD exists | `no matches for kind` | Separate Kustomizations with `dependsOn`; install CRDs first; health-check the CRD |
| **Webhook deadlock** | An admission webhook's backing Pod is itself managed by this controller; the webhook is down so the Pod cannot be created | Apply errors referencing the webhook; controller cannot heal what it needs | `failurePolicy: Ignore` for infrastructure webhooks, namespace exclusion, order dependencies, break-glass procedure |
| **Terminating namespace** | A finalizer waits on something that cannot finish; prune or deletion hangs | Namespace stuck `Terminating` | Identify blocking finalizers; fix the cause; manual finalizer removal as a last, logged resort |
| **Silent success** | Health check too weak | Post-deploy verification disagrees with controller | Application-level readiness; synthetic checks; service-level gates |
| **Credential sprawl** | Many deploy keys, tokens | Inventory shows unknown credentials | Central identity, short lifetimes, rotation, minimal scope |
| **Rollback ineffective** | Data migration, external side effects, cache format | Previous version fails against current data | Expand/contract, feature flags, restore-tested backups |
| **Git outage** | Source unreachable | Source not-ready alerts | The controller keeps last state running; avoid emergency changes that need Git; mirror Git for critical paths |
| **Reconcile storm** | A shared dependency changes and every Kustomization re-renders | API latency and queue depth spike | Stagger intervals; webhooks; shared artifacts |
| **Stale or partial render** | Generated manifests drift from templates; environment variable unset | Rendered diff in pull request; strict substitution | Render in CI; fail on unset variables |
| **Immutable field change** | Selector or volume claim template edited | Apply error "field is immutable" | Planned replacement with controlled downtime; naming to avoid |

Three of these deserve a closer look.

**Deletion cascades.** Deleting a Kustomization (or Application with a cascade finalizer) with prune enabled deletes *every object it manages*. A refactor that renames a Kustomization looks innocuous in review and can delete a production namespace. Defences: protect stateful objects with prune-disable annotations; restrict who can delete controller objects; use deletion policies the tool provides to orphan rather than delete (check your version); and require a second approver for any change touching controller objects. Treat `kustomizations/*` and `applications/*` as the highest-risk files in the repository.

**The self-hosting loop.** If the controller manages its own configuration, a bad commit to that configuration can disable the thing that would fix it. Use a *separate* root Kustomization for the controller with the most conservative review, avoid pruning it, and keep a documented out-of-band path (re-run bootstrap from a known good commit) that has been tested.

**Admission mutations and apparent drift.** Mutating webhooks add fields (sidecars, default labels). The controller sees live objects with fields Git never declared; with field-aware diffing this is fine, but an old, whole-object comparison reports permanent drift. Know which diff strategy your tool uses, and test with the mutations your cluster applies.

## Complex rollouts

### Coupled changes across services

Real releases span services: a producer adds a field, consumers must accept it; a new service version requires a new CRD. Rules:

1. **Make each change independently safe.** Services should tolerate both the old and the new message shape for at least one release (tolerant readers, additive-only changes).
2. **Order by dependency, enforce by data.** If B needs A first, either use `dependsOn` for infrastructure-type prerequisites, or encode compatibility in the application (feature negotiation) so that order does not matter. Encoding it in the application is more robust, because rollbacks also reorder.
3. **Roll out consumers first, producers last** for additive changes; roll **producers back first** on failure.

### Schema, CRD and API upgrades

CRD changes are among the riskiest: removing a stored version can strand objects, and conversion webhooks can fail. Practice: add new versions alongside old ones, migrate stored objects, wait a soak period, then remove. Test upgrades on a copy of production objects. Keep controllers that depend on a CRD pinned until the CRD upgrade has landed everywhere, and make "CRD present at version X" a health check of the Kustomization that installs it.

### Upgrading the platform under the workloads

Kubernetes and add-on upgrades are releases too. Sequence them through rings; drain with disruption budgets; verify workloads' readiness before proceeding to the next node pool; and keep a way to pause. A GitOps repository that also declares the cluster version (through infrastructure as code) can express the plan as reviewed changes, but remember that **node replacement is stateful**: local volumes and caches vanish.

### Blue/green at cluster level

For high-risk platform changes, build a *new* cluster from Git, shift traffic gradually, and keep the old cluster until confidence is high. This converts an in-place upgrade (where rollback is hard) into a traffic move (where rollback is a weight change). It requires that the cluster can be created *entirely* from code, that data stores are shared or replicated sensibly, and that cost of overlap is accepted. It is also the strongest test of whether "Git is the source of truth" is true.

### Controlled halting and the cost of rollback

Automated rollouts should have a *halt* that stops advancement and a *human decision* about rollback. Automatic rollback is attractive but dangerous when the fault is shared state, because rolling back a service onto data it cannot read converts one incident into two. Prefer automated halt, automated rollback only for failures known to be stateless (a failed readiness at startup), and human judgement otherwise.

## Governance

Governance answers "who may do what, and how do we prove it?" without making delivery slow. The aim is **continuous, mechanical compliance** rather than periodic inspection.

| Control | Mechanism | Evidence |
| --- | --- | --- |
| Separation of duties | The author of a production change cannot be its only approver; the bot that proposes digests cannot approve | Branch protection and code-owner settings, exported as data |
| Change classification | Standard changes (digest bump, scaling) are pre-approved paths; normal changes need review; emergency changes use the documented exception | Labels on pull requests; policy by path |
| Policy as code | Admission policies in Git, tested, versioned | Policy test results; violation reports |
| Evidence retention | Commit history, controller events, signed artifacts, approvals, kept for the retention period | Exports of events and approval records to durable storage |
| Exceptions | Time-limited, owned, recorded: suspensions, policy waivers, long-lived cluster-level overrides | An exception register with expiry dates and a report of expired entries |
| Drift reporting | Periodic comparison of live state with Git and policy | A report that is reviewed by an owner |
| Auditability | Answer "what ran, when, who approved?" in minutes | A tested query combining Git history and controller events |

An **audit query** is worth rehearsing:

```text
Question:  Which image was serving orders-prod at 14:20 UTC on 3 March, and who approved it?
Step 1:    Controller events/history -> the revision applied before 14:20 (commit sha)
Step 2:    `git show <sha>` -> the overlay digest; pull request -> approvers and evidence
Step 3:    Registry/provenance -> build, source commit, builder identity for that digest
Step 4:    Compare with runtime records (Pod imageID history from the observability system)
```

If any step needs a person's memory, retention or access is inadequate. Note that **controller events are often short-lived** by default; export them, or you will lose half the answer.

Governance has a cost: every control adds friction and an owner. A mature design makes the *safe path the easy path* (automated pull requests, pre-approved standard changes, clear templates) so that people do not route around controls. Measure bypasses; a rising bypass rate means the controls are mismatched with the work.

## State and data recovery

GitOps restores **configuration**. Recovery of a real system needs more. Distinguish recovery levels and claim only the ones you have demonstrated:

| Level | Meaning | Evidence you can claim |
| --- | --- | --- |
| **Workload** | The application is serving again | Health and service-level checks pass |
| **Cluster configuration** | Access control, policy, quotas and namespaces are restored | Policy tests pass; tenants can deploy |
| **GitOps** | Controller installed, sources reachable, everything reconciled with no hand-applied objects | Zero unmanaged objects in the inventory; zero drift |
| **Data** | Durable state restored to a known point | Restore tests with row counts or checksums; stated recovery point |
| **Platform** | Tenant provisioning, secrets issuance, identity and certificates all work | A new tenant is onboarded successfully |

### What Git cannot restore

- **Data**: databases, queues, uploaded files, ledger entries.
- **Secrets without their keys**: sealed or encrypted secrets are useless if the decryption key died with the cluster.
- **Identities issued by a certificate authority that no longer exists**, and cluster-issued certificates.
- **Registry contents** if the registry was the only copy (see T-DEV-02, registry-loss plan).
- **External resources**: DNS records, cloud load balancers, queues created outside the tree, unless infrastructure as code also covers them.
- **Operational state**: scaling history, schedule positions, in-flight work.

### A recovery order that works

```text
 1. Restore capability       infrastructure as code: networks, cluster, nodes, identity foundations
 2. Restore trust            controller credentials, decryption keys, secret-manager access
 3. Reinstate the controller bootstrap from a known good commit
 4. Reconcile from Git       policies and platform first, then tenants and applications
 5. Restore data             databases and volumes from verified backups to a stated recovery point
 6. Verify                   health, synthetic checks, data integrity, then reopen traffic
```

The order matters: restoring data first usually restores it into a schema-compatible *nothing*; restoring applications before policy skips guardrails. **Rehearse by rebuilding a cluster from Git and timing it.** The first rehearsal always finds hand-applied objects, an undocumented secret, a bootstrap step that was only ever done once and a dependency on the dead cluster. Those findings are the product of the exercise.

### Data recovery that interacts with rollback

When a release corrupts data, the instinct is "revert". The correct sequence is:

1. **Stop the damage.** Halt the release (suspend promotion, scale down the writer, disable the feature flag).
2. **Assess**: what was written, by which version, between which times.
3. **Decide a recovery point.** Options: point-in-time restore to just before the release; a forward fix that repairs data; a targeted correction of affected rows.
4. **Restore into a scratch environment first** and compare.
5. **Only then** roll back or forward the application, in line with the data's state.

Snapshot-based tools (volume snapshots, cluster backup tools) restore objects and volumes consistently only if the application is *quiesced* or the backup is application-aware; a crash-consistent snapshot of a database may need recovery on restart. State which consistency you tested.

## Organisation and operating models

Technology works only inside an operating model. Common patterns:

| Model | Description | Works when | Fails when |
| --- | --- | --- | --- |
| **Central platform team owns everything** | The platform team edits all desired state | Few services, small organisation | The team becomes a bottleneck; product teams are disengaged |
| **Platform provides paved road; teams own their services** | Platform maintains controllers, policy, templates; teams own their paths with scoped reconcilers | Dozens of teams; clear contracts | Platform ignores user needs; paved road is inflexible or unreliable |
| **Federated** | Each business unit runs its own platform | Strong autonomy, regulatory separation | Duplicated cost; divergent standards |
| **Self-service with guardrails** | Teams create environments from templates through pull requests | Mature platform and policy | Policies are not tested; exceptions pile up |

Questions to settle explicitly:

- **Who is on call for the controller, and who for a service's rollout?** Ambiguity here becomes a Saturday outage nobody owns.
- **What is the contract of the paved road?** Supported versions, supported chart and template shapes, response times for requests, deprecation policy.
- **How do teams request exceptions?** A visible, time-limited route with an owner.
- **How are costs attributed?** Per-namespace labels and quotas make desired state a source of cost data.
- **What is the unit of ownership?** A service, a namespace, a directory, a team. The repository layout should mirror it (Conway's law applies to desired-state repositories too).
- **How do we onboard a team in a day?** Template, scoped reconciler, quota, alerts, runbook skeleton, all generated.

A useful maturity ladder is *manual → scripted → declarative → reconciled → verified → governed*. Skipping stages produces brittle systems: governance on top of weak reconciliation is paperwork; progressive delivery on top of weak telemetry is ceremony.

## Case catalogue

### Case 1 — The refactor that deleted a namespace

A platform engineer renames a Kustomization for clarity. The old object is removed, and with `prune: true` the controller deletes everything it inventoried, including a namespace whose storage claims had a `Delete` reclaim policy. The cluster rebuilt the workloads within minutes; the data did not return. *Lesson:* treat controller objects as the most dangerous files; protect stateful objects with retained storage and prune exclusions; require a second approver for controller-object changes.

### Case 2 — The controller that could not heal itself

A bad admission webhook configuration is merged. Its backing Pods are managed by the same controller, and now every create request is rejected, including the Pods that would fix the webhook. *Lesson:* infrastructure webhooks should fail open or exclude their own namespace; the controller needs a break-glass path that bypasses the webhook; changes to webhook configuration are reviewed like database migrations.

### Case 3 — Green dashboards, failing customers

A rollout reports Ready everywhere. Readiness checks a TCP port; a rotated secret means every request fails at the database. *Lesson:* readiness must exercise the dependency path; automated promotion needs service-level gates; "applied" and "Ready" are not "working".

### Case 4 — The fleet-wide merge

An ApplicationSet targets all production clusters; one merge updates thirty clusters at the same minute and a bad configuration reaches every region. *Lesson:* generators need rollout structure; rings and soak times are part of the design, and a change that touches every cluster at once should be impossible by default.

### Case 5 — The two writers

An operator injects a default annotation that Git also declares; the controller overwrites it, the operator rewrites it, repeat. API-server load rises; unrelated reconciles slow. *Lesson:* one writer per field; alert on reconcile rate with no revision change; read managed fields when behaviour looks like a loop.

### Case 6 — The keys that died with the cluster

Secrets are stored encrypted in Git with a key held only inside the cluster. After a cluster loss, the repository reconciles perfectly and every secret is unreadable. *Lesson:* the decryption key is part of recovery; back it up separately, test recovery of it, and treat key custody as a recovery dependency.

### Case 7 — The rollback onto the wrong data

A release applies an irreversible migration; the health check fails; automation rolls back the application image. The old version cannot read the new schema and crash-loops; the incident doubles. *Lesson:* automatic rollback is safe only for stateless failures; migrations are separate, compatible releases.

## Expert trade-offs

| Tension | Option A | Option B | A defensible position |
| --- | --- | --- | --- |
| Control versus speed | Manual approvals everywhere | Fully automated promotion | Automate evidence gathering and standard changes; keep human approval for production and novel risk |
| Isolation versus visibility | Per-cluster controllers only | Central hub | Per-cluster pull for production with a read-only observation layer |
| Self-heal versus incident flexibility | Always on | Off in production | On, with a logged suspension path |
| Prune versus safety | Always prune | Never prune | Prune on, with protected stateful objects and review of removals |
| Uniformity versus autonomy | One fleet baseline | Per-team freedom | Strong defaults, documented exits with owners and expiry |
| Rich health checks versus coupling | Deep checks | Shallow checks | Deep for dependencies that make a release unusable; shallow plus alerts for the rest |
| Automatic rollback versus data safety | Roll back automatically | Halt and decide | Automate halt; automate rollback only for stateless failures |
| Mono-repo versus many repos | One tree, shared tooling | Per-team repositories | One platform repository for shared policy; teams own their application paths with scoped access |

A useful habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete the sentence, the control is ritual.

## Knowledge consolidation

- A reconciler is a **level-triggered control loop** with eventual, non-transactional guarantees. Ordering, idempotence and the meaning of "Ready" are your design responsibilities.
- The diff uses **managed fields**; one writer per field prevents flapping; convergence time is a budget you should measure.
- **Trust is a graph**: Git, registry, controller identity, secret manager, cluster API. Make controls independent of the thing they protect, and stricter on the desired-state repository than on application code.
- Fleets need **topology choices, layered configuration, rings, and inventory**. A generator without rollout structure is a fleet-wide outage waiting for a merge.
- Many expert failures are **interactions**: deletion cascades, webhook deadlocks, CRD ordering, self-hosting loops, mutation versus drift.
- Complex rollouts are built from **independently safe changes**; automate halt, not blind rollback.
- Governance is **mechanical compliance**: separation of duties, policy as code, exception registers, retained evidence, and an audit query you have rehearsed.
- GitOps restores configuration. **Data, keys, identities, registry contents and external resources need their own recovery**, in a rehearsed order.
- The operating model decides whether any of this lasts: ownership, on-call, paved-road contracts and exception routes.

## Exercises

**Exercise 1 — Trace a convergence budget.** For one production-like environment, instrument or estimate each stage from merge to serving. Produce a table with median and worst observed times, identify the largest contributor, and propose one change with its trade-off.

**Exercise 2 — Find the flapper.** Create two writers for one field (a Deployment's `replicas` in Git and an autoscaler, or an annotation set by a mutating webhook). Detect it from controller events and managed fields, measure the extra API activity, and fix it two ways. Describe which fix you would choose and why.

**Exercise 3 — Compromise tabletop.** For (a) a stolen maintainer token, (b) a compromised build, (c) a poisoned registry tag, and (d) a leaked controller credential, list what the attacker can reach in your design, which independent controls stop them, and which controls share a failure mode with the compromised component.

**Exercise 4 — Ring design.** Design a four-ring rollout for twelve clusters across three regions: how rings are labelled, how revisions are advanced, what health signal gates each step, the soak time, and what happens if ring 2 degrades after ring 3 has begun.

**Exercise 5 — Deletion drill.** In a lab, rename a Kustomization with prune enabled and observe what is deleted. Then add protections (prune exclusions, retained storage, orphaning policy) and repeat. Report what survived each time.

**Exercise 6 — Webhook deadlock.** In a lab, deploy a validating webhook that fails closed, managed by the same controller as its backing Pods, then break it. Show the deadlock, and design and test the recovery path and the prevention.

**Exercise 7 — Rebuild from Git.** Destroy a lab cluster and rebuild it from code and Git. Time each phase of the recovery order, list every hand-applied object, secret or step you discovered, and fix the repository so a second rebuild needs none of them.

**Exercise 8 — Audit query.** Pick a production change from the past month and answer: what ran, when, who approved it, what evidence supported it, and which artifact it was. Record how long it took and which steps needed a person's memory.

**Exercise 9 — Operating model memo.** For an organisation of thirty teams, write a one-page operating model: what the platform team provides, what teams own, the on-call split, the exception route, and the three metrics you would use to tell if it works.

**Solution notes.**

*Exercise 1.* Common findings: image pull and Pod start dominate, not Git or render time; the polling interval is a hidden half-interval of delay on average; health-check wait adds a fixed floor. Improvements include image pre-pulling, webhooks to trigger sources, and shorter `minReadySeconds`, each trading speed against safety or load. Report distributions, not single timings.

*Exercise 2.* Expect a high rate of reconcile events with an unchanged revision and two managers in `managedFields`. Fix one: remove the field from Git (autoscaler or webhook owns it). Fix two: declare the field as ignored or owned by the other writer in the controller. Prefer the first where Git need not control the value, because it removes the ambiguity entirely.

*Exercise 3.* Stolen token: stopped by required review, signatures and admission policy, unless the token belongs to an approver. Compromised build: provenance bound to workflow identity limits it, but a trusted builder that is itself compromised defeats provenance, so isolation of builders matters. Poisoned tag: digest pinning and signature checks stop it. Leaked controller credential: scope and audit limit it. A control that is administered by the same team using the same credentials as the thing it guards is not independent.

*Exercise 4.* A good answer defines a computed health signal (error ratio, saturation, controller Ready), a soak that exceeds the longest known failure latency (for example a daily batch), a halt rather than an automatic cluster rollback, and a plan that prefers rolling *forward* with a fix to rolling back across rings if data has been written. Rings 0 and 1 should be diverse enough to expose regional dependency differences.

*Exercise 5.* Without protection, objects deleted include the namespace's workloads and, depending on reclaim policy, volumes. With retained storage and prune exclusions, workloads are recreated by the new object and data survives. With an orphaning policy, objects stay but become unmanaged; note that unmanaged objects need adoption. Behaviour depends on the controller version; verify.

*Exercise 6.* The deadlock shows apply errors referencing the webhook while the backing Pod cannot be created. Recovery usually requires deleting or disabling the webhook configuration out of band, then reconciling. Prevention: fail-open for infrastructure webhooks, exclude the webhook's namespace from its own rules, and order dependencies.

*Exercise 7.* Expect findings such as a secret created by hand, a bootstrap step only in someone's notes, a registry credential missing, a DNS record outside the tree, a CRD installed too late. A successful second run with no intervention is the evidence for the GitOps recovery level; data recovery is a separate claim.

*Exercise 8.* If events have expired or approvals live only in chat, retention is the finding. The goal is a query anyone on the team can run in minutes.

*Exercise 9.* A strong memo names measurable outcomes: time to onboard a team, change failure rate, mean time to restore, fraction of changes through the standard path, number and age of exceptions. It states who is paged for the controller versus a service and what the platform promises.

## Mentoring prompts

Why is "Git is the source of truth" false during an incident, and how do you restore it afterwards? Which of your controls would still protect production if the desired-state repository's maintainer account were compromised, and which share a failure mode with the repository itself? How would you design the exception process for suspending reconciliation so that it is fast during an emergency and cannot be forgotten afterwards? When would you choose a hub-and-spoke topology over per-cluster controllers, and what failure are you accepting? What can you prove you restored after your last rebuild, and what did you only assume? Pick one control in your delivery system and state its cost, the risk it reduces and the signal that would tell you it had failed.

---
