# T-DEV-05-P — Professional Engineering

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-p"></a>
#### T-DEV-05-P — Professional Engineering

## Why this matters

A working controller is the start of the job, not the end. Professional practice asks harder questions: who is *allowed* to change production and how is that enforced; how does a version travel from a build to a customer-facing environment with evidence at every step; where do secrets live; how do you release a risky change to five percent of traffic; how do you know a release is healthy; and what do you do when the answer to "can we roll back?" is "not entirely".

This section treats GitOps as an **operating system for change**: a set of ownership rules, review gates, automated verification and rehearsed procedures. Tools appear because they implement those rules. The examples continue with the neutral `orders-api` service, and use Flux with Argo CD equivalents noted where they differ. Outputs marked *illustrative* show expected shapes, not measured results.

## First principles: what a production release system must guarantee

Whatever tools you choose, a release system worth trusting provides six guarantees. Use this list to evaluate any design, including your own.

| Guarantee | Question it answers | Typical mechanism |
| --- | --- | --- |
| **Identity** | Exactly which artifact is running? | Digest pinning |
| **Authorisation** | Who may change this environment? | Path ownership, branch protection, scoped controller identity |
| **Verification** | Was this artifact built and checked by the process we trust? | Signatures, provenance, admission policy |
| **Observability** | What was applied, when, and did it become healthy? | Controller status, events, alerts |
| **Reversibility** | How do we return to the last good state? | Append-only history, `git revert`, rehearsed runbooks |
| **Containment** | If this release is bad, how many users does it reach? | Rolling update, canary, traffic shaping |

Each section below maps to one or more of these. Anywhere the table has an empty cell for your team, that is the next improvement.

## Repository topology and ownership

### Layout decisions

| Pattern | Pros | Cons |
| --- | --- | --- |
| Monorepo: `app/` plus `deploy/` | One clone, easy local demos, atomic app-and-config change | Permission coupling; application developers can edit production paths; wide blast radius |
| Separate desired-state repository | Clear production owners; CI proposes digest updates by pull request; different review rules | Two remotes; a change to app and config is two pull requests |
| App-of-apps or cluster tree | Scales to many services and clusters | More controller objects to understand; mistakes cascade |

For anything beyond one team, a **separate desired-state repository** is the usual choice, because its access rules can differ from the application's. A representative layout:

```text
platform-config/
  clusters/
    staging/                    # entry point for the staging cluster
      apps.yaml                 # Kustomization pointing at apps/overlays/staging
      infrastructure.yaml       # platform add-ons, owned by the platform team
    prod/
      apps.yaml
      infrastructure.yaml
  infrastructure/               # controllers, policies, CRDs (platform-owned)
  apps/
    orders-api/
      base/
      overlays/{staging,prod}/
    billing-api/
      …
  tenants/                      # namespaces, quotas, service accounts, RBAC per team
  CODEOWNERS
```

Record the following in the repository's README as an *operating agreement*: who approves production; whether auto-sync, prune and self-heal are on for each environment and why; how digests get updated; which resources each system owns; how to suspend reconciliation; and who is on call for the controller. If that page does not exist, the design lives in people's heads.

### Ownership list

Two controllers managing one object is a defect. Make ownership explicit:

| Resource | Owner | Notes |
| --- | --- | --- |
| Cluster, networks, identity, node pools | Infrastructure as code | GitOps never prunes these |
| Application namespaces | Infrastructure as code *or* GitOps — choose one | If GitOps owns namespaces, deleting a path deletes a namespace and everything in it |
| Deployments, Services, autoscalers, ConfigMaps | GitOps | One Kustomization per service per environment |
| Controllers, policies, CRDs | Platform GitOps tree | Different owner and approval path from applications |
| Persistent volume claims and databases | Explicit decision | Usually *not* pruned automatically |
| Secrets | See below | Never plain text in Git |

Ask the diagnostic question for every resource: *what happens if CI and the GitOps controller both manage this?* If the answer is "they fight," the ownership list has a hole.

### Protecting what must not be deleted

Pruning is powerful and dangerous: removing a file from Git deletes the object. Defend stateful and shared resources explicitly:

```yaml
metadata:
  annotations:
    kustomize.toolkit.fluxcd.io/prune: disabled      # Flux: never delete this object when it leaves Git
    # Argo CD equivalent:
    # argocd.argoproj.io/sync-options: Prune=false
```

Also keep the storage layer defensive: persistent volumes whose `reclaimPolicy` is `Retain`, and backups owned outside the cluster. A prune annotation is a last guard, not a backup plan.

### Who may merge what

Because merging *is* deploying, the repository's controls are deployment controls:

```text
# CODEOWNERS (illustrative)
/apps/*/overlays/staging/     @example-org/orders-developers
/apps/*/overlays/prod/        @example-org/orders-leads  @example-org/release-managers
/infrastructure/              @example-org/platform-team
/tenants/                     @example-org/platform-team
/clusters/prod/               @example-org/platform-team
```

Pair these with branch protection: required reviews and code-owner approval, required status checks (render and validate), no force-push, signed commits where feasible, and no bypass for administrators except a logged break-glass role. The pull-request check should run the same render the controller will, plus a schema validator and a policy check, so that errors surface before merge.

```bash
# Example CI checks on every pull request to the desired-state repository
kustomize build apps/orders-api/overlays/prod > /tmp/rendered.yaml
kubeconform -strict -summary /tmp/rendered.yaml        # schema validation
kyverno test policies/ || conftest test /tmp/rendered.yaml   # policy checks, whichever you use
flux diff kustomization orders-prod --path apps/orders-api/overlays/prod   # needs read access to the cluster
```

(The last command needs cluster credentials, which has a security cost; many teams run it from a restricted, read-only identity or skip it and rely on render plus policy.)

## Promoting by digest

### The principle

You build **once** and promote the **same immutable artifact** through environments. Promotion changes *which digest an environment points at*, nothing else. This ties together the identity and verification guarantees: the digest staging proved is the digest production runs.

### An end-to-end flow

```text
 commit ─▶ CI: build, test, scan ─▶ push image ─▶ sign + attach provenance
                                       │
                                       ▼ digest sha256:3f1c…
                              open PR: staging overlay digest ◀── bot identity (limited)
                                       │ review, required checks
                                       ▼ merge → controller applies → health OK
                              open PR: prod overlay digest ◀── same digest, evidence linked
                                       │ code-owner approval (human)
                                       ▼ merge → controller applies → health OK → verification
```

The pull request that changes a digest should be *self-explanatory*. A good template:

```markdown
## Promote orders-api to production
- Digest: registry.example.com/orders-api@sha256:3f1c…e9a0
- Source commit: <sha>   Build: <CI run URL>
- Staging evidence: running since <time>; error rate and latency unchanged (link)
- Signature and provenance verified: yes (link)
- Data changes: none | expand-only migration <id> already applied
- Rollback: revert this commit; no data rollback needed
```

### Updating the digest: by hand, by bot, or by controller

| Method | How | Trade-off |
| --- | --- | --- |
| Human edits overlay | Manual pull request | Slowest; most deliberate |
| CI opens the pull request | A job with a narrowly scoped token edits one file | Reviewable; token must be tightly limited to that repository and path |
| Image-update automation | Flux `ImageRepository`, `ImagePolicy` and `ImageUpdateAutomation` scan the registry and commit digests | Fewer moving parts outside the cluster; needs write access to Git; policy must select only trusted images |

Whichever you use, **a policy chooses what may be promoted**, not "the newest thing in the registry". For example, accept only images whose tags match a release pattern *and* which carry a valid signature. Image-update automation on production usually commits to a branch for pull-request review rather than directly to the watched branch.

### Verifying before and after

Verification belongs at two points. Before the pull request merges, check that the digest exists, was built by your pipeline, and is signed:

```bash
cosign verify \
  --certificate-identity-regexp 'https://github.com/example-org/orders-api/.github/workflows/release.yml@.*' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  registry.example.com/orders-api@sha256:3f1c…e9a0
```

At admission time, a policy engine (Kyverno or similar) can *refuse to run* any image that is not referenced by digest or lacks a valid signature. This catches the case where someone bypasses Git and applies an object by hand, and it remains effective if the desired-state repository is compromised. After the controller applies, verify what is *actually* running, because "applied" proves little:

```bash
kubectl -n orders-prod get pods -l app=orders-api \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}'
```

Every line should end with the promoted digest. A line with a different value means an old Pod, a failed rollout, or a bypass.

## The controller's own access

### Least privilege

The controller is a powerful principal: it can create objects across the cluster. Constrain it:

- **Namespaced reconciliation.** Use `serviceAccountName` on each Kustomization (or an Argo CD `AppProject`) so a team's reconciler can only create objects in its namespaces and of permitted kinds.
- **Read-only Git credentials** per repository, scoped to that one repository.
- **Separate production Kustomizations** with stronger code-owner rules than staging.
- **No administrator rights "for convenience"**, no cluster-wide RBAC granted to tenants' reconcilers.
- **Admission policy** (Kyverno, OPA Gatekeeper, or the built-in `ValidatingAdmissionPolicy`) as an independent layer: disallow privileged containers, require resource limits, deny images by tag, forbid cluster-scoped kinds in tenant paths.

```yaml
# A tenant reconciler: may manage workloads in its own namespace only (illustrative)
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: orders-reconciler, namespace: orders-prod }
roleRef: { apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: edit }   # namespaced use of a built-in role
subjects:
  - kind: ServiceAccount
    name: orders-prod-reconciler
    namespace: flux-system
```

A **negative test** proves the control: add a ClusterRole to the tenant's path in a branch and confirm the apply fails with `forbidden`. A permission you have never seen denied is a permission you cannot be sure exists.

### Controller health is production health

If the controller stops, nothing is promoted and nothing drifts back, silently. Treat it as production infrastructure: alert on Kustomizations that remain not-Ready beyond a threshold, on sources that have not updated, on suspension, and on controller restarts. Flux emits Prometheus metrics (for example `gotk_reconcile_condition`) and can send events to chat or incident tooling through `Provider` and `Alert` objects:

```yaml
apiVersion: notification.toolkit.fluxcd.io/v1beta3
kind: Alert
metadata: { name: prod-failures, namespace: flux-system }
spec:
  providerRef: { name: team-chat }
  eventSeverity: error
  eventSources:
    - { kind: Kustomization, name: orders-prod }
    - { kind: HelmRelease, name: '*' }
```

The test of an alert is the same as of a permission: induce the failure in staging and watch it fire.

## Secrets

Never commit plaintext `Secret` manifests; Git history is permanent and widely cloned. Reference secrets by *name* in workloads, and choose how the secret reaches the cluster:

| Approach | How it works | Use when | Watch for |
| --- | --- | --- | --- |
| Out-of-band Secret created by an operator | A human or script creates it in the cluster | Local practice only | Not reproducible; lost with the cluster |
| Sealed Secrets | Encrypt with a cluster key; commit the sealed form | Small teams; single cluster | Key backup; re-encrypting when the key is lost or rotated |
| SOPS with age or a KMS key | Encrypt values in files; controller decrypts at apply | Encrypted material may live in Git with managed keys | Key custody; reviewers see only ciphertext diffs |
| External Secrets Operator | An `ExternalSecret` object maps a cloud secret-manager entry into a Secret | A secret manager is the source of truth | Dependency on the manager's availability; access policy for the operator |

```yaml
# External Secrets Operator (API version varies by release)
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata: { name: orders-db, namespace: orders-prod }
spec:
  refreshInterval: 1h
  secretStoreRef: { kind: ClusterSecretStore, name: platform-secrets }
  target: { name: orders-db }
  data:
    - secretKey: password
      remoteRef: { key: orders/prod/db, property: password }
```

Whichever approach you choose, answer five questions in the runbook: *where does the secret live; who can read it; who rotates it and how often; how is rotation rolled out to running Pods; how do you verify it works?* Note that most applications read a mounted Secret at start-up, so rotation may need a restart (a Deployment annotation change, or a tool that triggers rollouts when a Secret changes).

**If a secret is committed by mistake**, deleting the line does not remove it from history: treat it as compromised, rotate it, then clean history only as a secondary step. Monitor certificate expiry and assign an owner to renewal; expired certificates are among the most common causes of avoidable outages.

## Helm and Kustomize in a professional repository

| Need | Prefer |
| --- | --- |
| Thin environment differences on your own service | Kustomize overlays |
| Third-party software distributed as charts | Helm, with exact chart version pinned |
| A reusable, parameterised package for many teams | Helm or a higher-level template, with a documented values contract |
| Both | Helm for vendors, Kustomize for ours; document why, and keep the boundary |

Do not keep two parallel sources of truth for the same Deployment. A frequent pattern is a `HelmRelease` for a vendor chart *plus* a small Kustomize patch for local needs (post-rendering); it works, but each layer is a place for surprises, so render the final result in the pull-request check.

## Progressive delivery

Containment is how you limit the cost of a bad release. Strategies differ in what they require:

| Strategy | How it works | Platform need | Weakness |
| --- | --- | --- | --- |
| Rolling update | Replace Pods gradually; readiness gates traffic | Default Deployment | Old and new versions coexist; all users eventually get the new one |
| Blue/green | Run both versions; switch traffic | Two copies plus a traffic switch | Double capacity; switch is all-or-nothing |
| Canary | Send a small share to the new version; promote or abort on metrics | Controller (for example Flagger or Argo Rollouts), traffic shaping and metrics | Needs trustworthy telemetry and enough traffic |
| Feature flag | Ship dark, enable per cohort | Application support | Flag debt; two code paths |

### Making rolling updates safe

A rolling update is a sound baseline *if you configure it deliberately*:

```yaml
spec:
  replicas: 4
  minReadySeconds: 10                 # a Pod must stay ready this long before counting
  progressDeadlineSeconds: 300        # mark the rollout failed if it stalls
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }   # never drop below desired capacity
  template:
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: orders-api
          readinessProbe: { httpGet: { path: /ready, port: 8080 }, periodSeconds: 5, failureThreshold: 3 }
          lifecycle: { preStop: { exec: { command: ["sleep", "5"] } } }   # let load balancers drain
```

Add a `PodDisruptionBudget` so node maintenance cannot remove too many Pods at once. The readiness probe is the *gate*: if it returns success before the application can serve (for instance before a database connection is established), the rolling update will happily send traffic to a broken Pod and report success. T-DEV-02 treats health versus readiness in detail.

### A canary with automated analysis

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata: { name: orders-api, namespace: orders-prod }
spec:
  targetRef: { apiVersion: apps/v1, kind: Deployment, name: orders-api }
  service: { port: 8080 }
  analysis:
    interval: 1m
    threshold: 3                      # failed checks tolerated before rollback
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange: { min: 99 }
        interval: 1m
```

A canary compares the new version with the old on *measured signals* (error rate, latency percentiles) and aborts automatically on regression. Requirements are non-trivial: traffic management (a service mesh or ingress that supports weighted routing), reliable metrics with enough requests to be statistically meaningful, and a rollback cheaper than the failure. Without those, a canary is just a slow rollout. The honest professional position is to install what you need and *show it working*, or to document what you would add; do not claim a canary you have not exercised.

### How progressive delivery interacts with GitOps

The controller applies the *desired* Deployment; the progressive-delivery tool then manipulates *derived* objects (a primary and a canary Deployment, traffic weights). Two consequences: the GitOps controller must not fight the progressive-delivery tool over those derived objects (exclude them from drift correction), and the "revision applied" and "revision serving all traffic" become different moments. Your status checks and runbooks must name which one they mean.

## Health: knowing a release worked

"Applied" and "Ready" are controller words. Users care about whether *requests succeed*. Layer your evidence:

| Layer | Evidence | Limitation |
| --- | --- | --- |
| Controller | Revision applied; health checks pass | Only as strong as the probes |
| Workload | Rollout complete; Pods ready on the new digest | Does not exercise the dependency path |
| Synthetic | A scripted request against the live endpoint after deploy | Covers chosen paths only |
| Service-level | Error ratio and latency compared with the pre-release baseline (T-DEV-06) | Needs enough traffic and a time window |

A minimal **post-deploy verification** is a short script run by CI or an operator after each production change:

```bash
kubectl -n orders-prod rollout status deploy/orders-api --timeout=5m
curl -fsS https://orders.example.com/health | grep -q ok
# compare error ratio over the last ten minutes with the previous hour from your metrics system
```

Where you can, automate it: a controller-side `healthChecks` entry for the workload, an alert tied to the same service-level objective, and a rollout that holds when the signal degrades. Readiness that only checks "the process is up" produces *silent success*, the most expensive failure mode.

## Multi-environment operations

| Concern | Practice |
| --- | --- |
| **Promotion order** | Always through the lower environment first; the pull-request template asks for staging evidence |
| **Differences** | Allowed: replicas, resources, hostnames, digests during promotion. Everything else is a smell and needs a reason |
| **Cadence and freezes** | A freeze is a rule on the repository (a required label or a paused Kustomization), not a reminder in chat |
| **Hotfix path** | Documented: expedited review, same digest promotion, same verification; faster does not mean unrecorded |
| **Configuration drift between clusters** | Detect by rendering both overlays and diffing on a schedule |
| **Environment parity of dependencies** | Keep database versions, ingress, and policies close; a staging that differs structurally proves less |

For several clusters of the same environment (regions), use one overlay per environment and a small *cluster-specific* layer for names and endpoints, so a change is rolled region by region by sequencing pull requests, not by hand.

## Runbooks

A runbook is a rehearsed script for a bad moment. It should be short, executable, and tested. A fuller skeleton than the minimum:

```markdown
# orders-api runbook

## Failed rollout
- Detect: alert "orders-prod not Ready"; `flux get kustomizations`
- Classify: source / build / apply / health (see table)
- Act: `kubectl -n orders-prod describe deploy orders-api`; if release-caused,
  `git revert <recorded sha>`; `flux reconcile kustomization orders-prod --with-source`
- Verify: live digest equals previous; error ratio back to baseline
- Record: incident note, the reverted sha, the cause

## Stalled reconciliation
- Check: `flux get sources git` (source), `kubectl kustomize <path>` (build), events (apply), workload events (health)
- Act: fix path, credentials or YAML in Git; do not delete Pods to "unstick" it

## Emergency live change
- Approver: on-call lead. `flux suspend kustomization orders-prod`; time-box 2 hours; ticket required
- Make the minimal fix; commit it; `flux resume`; confirm no drift

## Secrets
- Where they live; who rotates; how rollout picks up rotation; how to verify

## Data
- What is durable; who restores; why `git revert` does not restore data; the latest verified backup
```

Test the runbook by *using* it in staging during a game day: break a release, follow the steps literally, and fix whatever is unclear. A runbook that has never been executed is a hypothesis.

## The hard limit: rollback and data

Reverting manifests reverts what is *declared*: images, configuration, replica counts. It does not reverse **effects** that the new version already had on the world: rows migrated, files written, messages published, emails sent, payments captured, caches filled with a new format. This is the most important limit of GitOps rollback, and the most commonly forgotten.

### Expand and contract

Make schema and format changes *compatible with both versions* so that either can run during and after a rollout. The standard method has phases, each released separately:

| Phase | Change | Safe to roll back application to previous version? |
| --- | --- | --- |
| 1. Expand | Add the new column or table; keep the old; the application still writes the old | Yes |
| 2. Dual-write / backfill | Application writes both; a job backfills old rows | Yes: old version ignores the new column |
| 3. Switch reads | Application reads the new column | Yes, while the old column is still being written |
| 4. Contract | Stop writing the old column | Only until this moment; after it, rollback needs care |
| 5. Remove | Drop the old column (a later release) | No for the previous version; take a verified backup first |

Each phase is a separate, reversible deployment, and the *destructive* step is isolated, delayed, and preceded by a restore test.

### Practices that help

- Put migrations in a separate, explicit step (a job run before the rollout, with its own review), not hidden in application start-up where a restart re-runs it.
- Make migrations **idempotent and forward-only**, and keep the previous application version compatible with the schema for one release.
- Use **feature flags** to separate deploying code from enabling behaviour; turning a flag off is faster and safer than a redeploy.
- Take and test **backups of data owned outside the Deployment**. A backup you have not restored is a belief.
- Ask in every production pull request: *"Does this release change data in a way the previous version cannot read?"* If yes, the rollback section must say what you will do instead.

## Day-two operations

**Pod and node failure.** Kill a Pod under client load and measure *client-visible* impact (error count, latency), not whether a new Pod appeared. A replacement Pod is not proof of no downtime: connection draining, readiness and disruption budgets decide that.

```bash
# in one terminal: a steady client loop recording failures
while true; do curl -s -o /dev/null -w '%{http_code} %{time_total}\n' https://orders.example.com/health; sleep 0.2; done | tee /tmp/client.log
# in another: kubectl -n orders-prod delete pod <one pod>
# afterwards: count non-200 lines in /tmp/client.log
```

**Autoscaling.** A HorizontalPodAutoscaler with real metrics should be *demonstrated* under controlled load. Configured targets and observed scaling are separate evidence. Remember the ownership rule: remove `replicas` from Git when an autoscaler owns it.

**Backup and recovery order.** After a major loss, recover in dependency order: first restore cluster capability (infrastructure as code), then controller credentials and the controller itself, then let the controller **reconcile from Git**, and *finally* restore application data. Doing it in this order avoids restoring data into an application that does not exist yet, and makes the reconcile step a test of your repository.

**Version upgrades of the controller.** Upgrade the controller through its own Git directory in staging first; read the release notes for API version changes; keep a rollback plan for the controller itself. A controller upgrade is a change to your deployment mechanism and deserves the same care as a database upgrade.

## Argo CD mapping, with the organisational features

The same desired-state tree works with Argo CD. Beyond the table in the Intermediate section:

- An **`AppProject`** restricts source repositories, destination namespaces and allowed resource kinds. It is Argo's analogue of scoped service accounts and is the main tenancy boundary.
- An **`ApplicationSet`** generates many `Application` objects from a template and a generator (a list of clusters, directories in Git, or pull requests). It is the main tool for fleets.
- **Sync waves and hooks** (`argocd.argoproj.io/sync-wave`, resource hooks) order operations and run jobs such as migrations before or after a sync.
- **`ignoreDifferences`** declares fields that other writers legitimately own.
- The UI shows live state, diffs and history, which is excellent for investigation but must not become a place where manual syncs replace Git review.

## Professional trade-offs

| Decision | Option A | Option B | Reasonable default |
| --- | --- | --- | --- |
| Automated production sync | Fully automatic on merge | Manual sync gate | Automatic with strong merge controls; manual gate where regulation or risk requires |
| Self-heal | On everywhere | Off in production | On, with documented suspension for emergencies |
| Prune | On | Off | On, with protected stateful resources and reviewed removals |
| Digest bot | Direct commit | Pull request | Pull request for production |
| Secrets | Encrypted in Git | External manager | Whichever your platform already operates; do not run both without reason |
| Canary | Always | Only for risky changes | Rolling with strong readiness for most services; canary where telemetry supports it |

## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Deploy a new digest | A pull request to the overlay | `kubectl set image` as a permanent fix |
| Debug sync | Controller status, logs, events by stage | Only deleting pods |
| Handle drift | Reconcile, or suspend with a ticket | Silent console edits |
| Roll back | `git revert <recorded sha>` | A blind revert of HEAD |
| Own a resource | One owner per resource | Dual controllers |
| Prove availability | A client loop during a pod kill | Equating a new pod with zero downtime |
| Keep secrets | A managed approach, rotation owner named | Plaintext in Git, or "temporary" secrets |
| Limit blast radius | Scoped service account, rolling update or canary | Cluster-admin reconcilers |
| Change a schema | Expand and contract, separate releases | A migration that only moves forward with the release |

## Knowledge consolidation

- A trustworthy release system gives **identity, authorisation, verification, observability, reversibility and containment**; evaluate designs against all six.
- A **separate desired-state repository** with path-based code owners and branch protection makes merging a controlled act. Write down the operating agreement.
- **Build once, promote the same digest.** The pull request carries evidence; policy decides what may be promoted; admission control enforces it independently of Git.
- Give the controller **least privilege**, test denials, and **monitor the controller** as production infrastructure.
- Choose a **secrets approach** deliberately; name where they live, who rotates, and how rotation reaches running Pods. A leaked secret is rotated, not merely deleted.
- Rolling updates are safe only with **good readiness**; canaries need telemetry; claim only what you have exercised.
- Prove health with **layers of evidence**, ending in service-level signals.
- A **runbook is tested** by use.
- **`git revert` does not revert data.** Use expand/contract, separate destructive steps, feature flags and restore-tested backups.

## Exercises

**Exercise 1 — Operating agreement.** Write the operating agreement for a desired-state repository serving two teams and two environments: code owners per path, branch protection, sync/prune/self-heal settings per environment, and the suspension rule. Review it against the six guarantees and mark any that are weak.

**Exercise 2 — End-to-end promotion.** Take one digest through staging and production using pull requests. Attach evidence to each. After each apply, list the `imageID` of every Pod and show they equal the promoted digest. Try to promote an unsigned or wrongly built image and record where it is stopped.

**Exercise 3 — Scoped reconciler.** Create a reconciler with permissions limited to one namespace. Demonstrate success for an in-scope object and a `forbidden` failure for a ClusterRole placed in its path. Explain which two layers (RBAC and admission policy) would each independently catch it.

**Exercise 4 — Secrets and rotation.** Implement one approach (SOPS or External Secrets in a lab). Rotate the secret and show how the running workload picks up the new value. Write the five-question record.

**Exercise 5 — Unsafe migration.** Design a change that renames a database column. Write the phases using expand/contract, state for each phase whether the previous application version can run, and say what you would do if the contract phase went wrong.

**Exercise 6 — Failure drill.** In staging, kill a Pod under a steady client loop and report the non-success count. Then adjust `maxUnavailable`, readiness and `preStop` and repeat three times each. Report ranges, not single runs.

**Exercise 7 — Alert test.** Induce a health failure in staging and show an alert firing within your stated threshold. Record time-to-detect.

**Exercise 8 — Runbook game day.** Hand your runbook to a colleague who did not write it, break a release in staging and observe without helping. List every step they could not follow.

**Solution notes.**

*Exercise 1.* A strong answer names a specific owner group per path, requires code-owner approval for production, forbids administrator bypass except a logged break-glass role, and states a time limit for suspension. Weak spots usually appear under *containment* and *verification*; a design with strong review but no admission policy trusts the repository entirely.

*Exercise 2.* Expect every Pod `imageID` to end in the promoted digest. An unsigned image should be stopped before merge (the verification step) and, independently, at admission if you enforce it. If it was stopped only at one point, note the layer you are missing.

*Exercise 3.* RBAC denial appears as `forbidden: … cannot create resource clusterroles`. An admission policy that forbids cluster-scoped kinds in tenant namespaces gives a second, independent block. If only one catches it, the other is a gap to fix.

*Exercise 4.* After rotation most applications still hold the old value until a restart; either trigger a rollout or use an application that reloads. Your five-question record should name an owner and a verification command. The key custody answer is where most designs are weakest.

*Exercise 5.* A good sequence: add the new column (expand); write both and backfill; switch reads; stop writing the old column; drop it later after a restore test. The previous application version stays compatible until the contract phase. If contract goes wrong, restore from the verified backup into a scratch environment first; do not assume `git revert` helps.

*Exercise 6.* With `maxUnavailable: 0`, a correct readiness probe and a short `preStop`, expect zero or near-zero client errors; removing any one often produces a few failures. Report the range across runs and avoid claiming zero downtime from one run.

*Exercise 7.* The detection time is the interval plus threshold you configured; if it is longer than your objective, tighten the alert or the probe. An alert you have never seen fire is untested.

*Exercise 8.* Common gaps: commands with unexplained placeholders, missing permissions, no "how do I know it worked", and steps that assume knowledge of the system. Fix each and repeat.
