# T-PLT-02-E — Expert Depth

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-e"></a>
#### T-PLT-02-E — Expert Depth

**Templating pitfalls and alternatives.** Text templating over YAML is fragile: indentation, quoting and type errors appear at render time; complex conditionals hide behaviour; and Go-template charts can become unreadable programs. Alternatives: typed configuration languages that generate manifests (CUE, Jsonnet, Pkl and similar), higher-level abstractions (a custom resource that expands into several objects, reconciled by a controller), and plain overlays. Choose based on who authors and who reviews: platform authors can use richer tools; application teams generally need a small, safe surface.

**Custom resources and controllers.** A custom resource definition lets the platform offer domain objects ("a Service with database and dashboard") reconciled by a controller. Benefits: a stable, validated API; policy and ownership are centralised; upgrades roll out by changing the controller. Costs: you now run software with its own bugs, upgrade path and permissions. Prefer an existing, well-maintained operator over writing your own; when you write one, invest in conditions, status, finalizers, idempotence and observability.

**Server-side apply and field ownership.** Multiple writers (a controller, a human, an autoscaler adjusting replicas) can conflict. Server-side apply tracks field managers so each writer owns specific fields. Understand conflicts: an autoscaler-managed replica count that is also set in Git will flap unless the field is omitted from the desired state.

**Supply chain for packages.** Charts and overlays are code that can introduce privilege. Pin versions or digests, review upstream changes, verify signatures and provenance, scan rendered output with policy, mirror critical charts into an internal registry, and keep a reproducible record of what was deployed.

**Failure modes**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Value typo silently ignored | No schema | Strict schema, `required`, rendering tests |
| Unreviewed change via default values | Defaults change in a chart upgrade | Diff rendered manifests on upgrade |
| Two owners fight | Controller and human or two controllers | Single-owner policy, SSA field management |
| Chart upgrade breaks live objects | Immutable field changed | Upgrade tests, `--dry-run`, staged rollout |
| Pruning removes stateful objects | Ownership overlap | Prune exclusions and ownership list |
| Hash-triggered rollout storms | Shared ConfigMap changes touch many Deployments | Scope config per workload; staged rollouts |

**Designing for many teams.** A shared "golden" chart or template reduces variation but creates a coupling point; give it an owner, a support route, semantic versions, a deprecation process and an escape hatch for teams with unusual needs (with that team taking on the extra responsibility). Measure adoption and deviations.

**Choosing the controller: four workloads, four decisions.**

| Workload | Controller | Reasoning |
| --- | --- | --- |
| Stateless `orders-api` | Deployment | Interchangeable Pods; rolling update; scale freely |
| Three-node clustered database | StatefulSet | Stable names (`db-0`), stable storage per replica, ordered start and update |
| Log shipper on every node | DaemonSet | One Pod per node; follows node membership |
| Nightly invoice export | Job / CronJob | Runs to completion; retries on failure; must not keep running |

| Property | Deployment | StatefulSet | DaemonSet | Job |
| --- | --- | --- | --- | --- |
| Identity | Random Pod names | Ordinal, stable DNS | Per node | Per completion |
| Storage | Shared or none | `volumeClaimTemplates` per replica | Usually host paths (review risk) | Ephemeral |
| Update order | Rolling, any order | Ordered, one at a time by default | Rolling per node | Not updated; recreated |
| Failure semantics | Replace and reschedule | Replace *with the same identity*; PVC retained | Reschedule on the node | Retry up to `backoffLimit` |

A StatefulSet gives identity and storage but does not make the application safe: replication, backup and failover remain your problem. For databases, prefer a mature operator or a managed service, and write down who owns upgrades and restores.

**Server-side apply: the three-writer conflict.**

```yaml
# Git (via the GitOps controller) says:
spec: { replicas: 3 }
# The HorizontalPodAutoscaler scales to 8; the next reconcile sets it back to 3 -> flapping.
```

```bash
kubectl apply --server-side --field-manager=gitops -f deployment.yaml
kubectl get deployment orders-api -o yaml --show-managed-fields | less    # who owns spec.replicas?
# Conflict message when two managers write the same field:
# Apply failed with 1 conflict: conflict with "hpa-controller" using apps/v1: .spec.replicas
```

Resolutions: remove `replicas` from the Git-managed manifest when an autoscaler owns it; or deliberately take ownership with `--force-conflicts` and remove the autoscaler. Either way, state *one* owner per field and document it. Humans using `kubectl edit` become a third writer; policy should prevent or at least alert on manual edits to controller-managed fields.

**Helm, Kustomize and typed configuration: a comparison**

| Dimension | Helm | Kustomize | Typed language (CUE, Jsonnet, Pkl) |
| --- | --- | --- | --- |
| Templating fragility | High: text over YAML, indentation errors | Low: patches on valid YAML | Low: types catch errors early |
| Drift visibility | Moderate: render and diff needed | High: output is plain YAML | High: compiled output is plain |
| Reviewability | Diff of values plus templates | Diff of overlays reads naturally | Good once reviewers know the language |
| Reuse of third-party software | Excellent (large chart ecosystem) | Possible; fewer packages | Limited; needs wrappers |
| Learning cost | Moderate | Low | High |
| Best fit | Distribution of reusable packages | Environment variants of your own manifests | Large platforms with many generated objects |

A defensible recommendation for a single organisation: Kustomize overlays for first-party services; Helm only to consume third-party charts, rendered and committed or pinned; consider a typed language when you generate hundreds of near-identical manifests. State the caveat: when a team's needs outgrow patches (many conditional resources), reconsider.

**Third-party chart review checklist.**

```bash
helm pull <repo>/<chart> --version 1.4.2 --untar          # review a pinned version, not "latest"
helm template rel ./chart -f values.yaml | tee rendered.yaml
kubectl apply --dry-run=server -f rendered.yaml
grep -nE 'privileged|hostPath|hostNetwork|runAsUser: 0|cluster-admin|ClusterRoleBinding|helm.sh/hook' rendered.yaml
```

| Risk | What to look for | Control |
| --- | --- | --- |
| Unpinned versions | Image tags or chart dependencies using `latest` or ranges | Pin to digest and exact version |
| Privileged defaults | Root, host access, wide RBAC | Override values; admission policy rejects them |
| Hooks | Pre/post-install Jobs running arbitrary images | Read them; run in staging first |
| CRDs | Cluster-wide API changes; Helm does not upgrade or delete them by default | Manage CRDs separately with a documented upgrade path |
| Provenance | Unsigned chart from an unknown source | Verify signatures; mirror to an internal registry |

**Migrating 100 services across a chart major version without a flag day.** Publish the new major alongside the old; provide a compatibility values mapping and a rendered-manifest diff tool; migrate in waves (pilot services, then volunteers, then the rest) with a deadline and deprecation notices; gate each wave on identical rendered output or an explained diff; keep the old major supported for a defined period; measure progress per team. A flag day concentrates all risk in one night and is almost never necessary.

**Mentoring prompts.** When is a typed configuration language worth the learning cost over Helm? How would you migrate a hundred services from one chart major version to the next without a flag day? What breaks if an autoscaler and a GitOps controller both set replicas?

---
