# T-DEV-05-P — Professional Engineering

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-p"></a>
#### T-DEV-05-P — Professional Engineering

**Repository layout decisions.**

| Pattern | Pros | Cons |
| --- | --- | --- |
| Monorepo: `app/` plus `deploy/` | One clone, easy local demos | Permission coupling, wider blast radius |
| Separate desired-state repository | Clear production owners; CI proposes digest updates by pull request | Two remotes to wire |
| App-of-apps or cluster tree | Scales to many services | More controller objects to understand |

Record the choice, who approves production, whether auto-sync, prune and self-heal are on, how digests get updated and which resources each system owns. Two controllers managing one object is a defect: ask what happens if CI and the GitOps controller both manage the same Deployment.

**Ownership list.**

| Resource | Owner |
| --- | --- |
| Cluster, networks, identity, node pools | Infrastructure as code |
| Application namespaces | Infrastructure as code *or* GitOps — choose one |
| Deployments, Services, autoscalers | GitOps |
| Persistent volume claims | Explicit decision; prune carefully |

Never let GitOps prune infrastructure-managed or stateful resources. Mark sensitive objects so the controller will not delete them.

**Helm versus Kustomize.**

| Need | Prefer |
| --- | --- |
| Thin environment differences on your own service | Kustomize overlays |
| Third-party software distributed as charts | Helm |
| Reusable parameterised package for many teams | Helm or a higher-level template |
| Both | Helm for vendors, Kustomize for ours; document why |

Do not keep two parallel sources of truth for the same Deployment.

**Least privilege for the controller.** Namespaced permissions for application reconciliation, read-only Git credentials, a separate production Kustomization with stronger code-owner rules, no administrator rights "for convenience", and admission policy (Kyverno or OPA) as an additional layer.

**Secrets.** Never commit plaintext Secret manifests.

| Approach | Use when |
| --- | --- |
| Out-of-band Secret created by an operator | Local practice only |
| Sealed Secrets or SOPS | Encrypted material may live in Git with key management |
| External Secrets Operator | A cloud secret manager is the source of truth |

Reference a Secret by name in manifests, not by value. Monitor certificate expiry and assign an owner to renewal.

**Data and migrations — a hard limit.** Reverting manifests does not reverse an incompatible database migration. Use expand/contract migrations so old and new versions can coexist during a rollout. GitOps rollback is not data rollback.

**Progressive delivery.**

| Strategy | Platform need |
| --- | --- |
| Rolling update | Default Deployment; readiness gates traffic |
| Blue/green | Two versions plus a traffic switch |
| Canary | A controller (for example Flagger) plus metrics |

A healthy rolling update plus Git rollback is a sound baseline; document what you would add for canaries without pretending you installed it.

**Day-two operations.** Kill a pod under client load and measure client-visible impact (do not equate "a new pod appeared" with "no downtime"). Configure an autoscaler with real metrics and *demonstrate* scale-out under controlled load; configured targets and observed scaling are separate evidence. Back up data owned outside the Deployment; recovery order is: restore cluster capability, restore controller credentials, reconcile from Git, then restore application data.

**Runbook skeleton**

```markdown
# orders-api runbook
## Failed rollout       - check: flux get; kubectl rollout status; action: git revert <sha>
## Stalled reconciliation - check: source vs build vs health; action: fix path/auth/YAML
## Secrets              - where they live, who rotates, how to verify
## Data                 - what is durable, who restores, why git revert does not restore data
```

**Argo CD mapping.** The same desired-state tree works with Argo CD: a `GitRepository` plus `Kustomization` corresponds to an `Application` with `source.path`; `prune: true` to `syncPolicy.automated.prune`; self-heal to `selfHeal`; `flux reconcile` to `argocd app sync`; suspension to disabling auto-sync.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Deploy a new digest | A pull request to the overlay | `kubectl set image` as a permanent fix |
| Debug sync | Controller status, logs, events | Only deleting pods |
| Handle drift | Reconcile, or suspend with a ticket | Silent console edits |
| Roll back | `git revert <recorded sha>` | A blind revert of HEAD |
| Own a resource | One owner per resource | Dual controllers |
| Prove availability | A client loop during a pod kill | Equating a new pod with zero downtime |
