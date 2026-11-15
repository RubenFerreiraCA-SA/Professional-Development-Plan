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

**Versioning at scale: what is actually being versioned.** In a fleet there are at least six independently moving versions: the application image, the package (chart or base), the package's dependencies (subcharts, components), the Kubernetes API versions the manifests use, the CRDs and their controllers, and the cluster itself. Incidents come from combinations nobody tested. Treat the tuple as the unit of release and record it.

```yaml
# release-manifest.yaml: one record per environment per deploy
service: orders-api
image: registry.example.com/orders-api@sha256:7ab2...41cd
chart: { name: platform-service, version: 3.4.1, digest: sha256:19c0...d2e7 }
values_commit: 5f1e8c2
cluster: { name: prod-eu-1, kubernetes: v1.31.4 }
crd_versions: { servicemonitors.monitoring.coreos.com: v1, certificates.cert-manager.io: v1 }
rendered_sha256: 0c8a...7b31        # hash of the final YAML that was applied
```

The `rendered_sha256` field is the strongest single control: two environments with the same chart, values and cluster can still differ if a template function behaves differently across Helm versions. Pin the toolchain (Helm, Kustomize, kubeconform) in CI the same way you pin the chart.

**Package version strategy for a platform chart.**

| Question | Position | Why |
| --- | --- | --- |
| How many majors are supported at once | At most two | Each supported major multiplies test and support cost |
| What counts as breaking | Any change to rendered output that is not opt-in, any removed or renamed value, any change that recreates an object | Consumers judge breakage by effect, not by intent |
| How do consumers pin | Exact version in each service repository; bot proposes bumps | Updates are visible and reviewable; no silent upgrades |
| How is a security fix delivered | Backport patch release to every supported major | Forcing a major upgrade to receive a fix punishes the careful |
| What does a deprecation include | Warning surfaced at render time via `fail`/`NOTES.txt`, a dated removal version, an automated migration | Documentation alone is not read |

```yaml
# Render-time deprecation signal (chart helper)
{{- if .Values.replicaCount }}
{{- fail "values.replicaCount was removed in chart 4.0; use replicas.min (see MIGRATION.md#replicas)" }}
{{- end }}
```

Measure the fleet: percentage of services on the current major, on the previous, and on unsupported versions; median age of the pinned version; number of services with local patches or forked templates. These numbers tell you whether the chart is an API or a suggestion. A rising count of forks means the package is missing a capability, and the response is to add it or to expose a supported extension point, not to forbid forks by decree.

**Competing controllers and field ownership beyond replicas.** The three-writer replica conflict generalises. Any field may have several writers: the GitOps controller, an admission webhook that injects sidecars or resource defaults, a vertical autoscaler adjusting requests, a service mesh, a cost tool annotating Pods, and a human. Drift reports that show a permanent difference are usually a sign of two legitimate writers with no declared boundary.

| Field | Competing writers | Resolution |
| --- | --- | --- |
| `spec.replicas` | GitOps controller vs HPA | Omit from Git; or `ignoreDifferences` for that field |
| `resources.requests` | Git vs vertical autoscaler | Choose: VPA in recommendation mode, with Git updated from its output; or VPA owns the field and Git omits it |
| `spec.template.spec.containers[*]` (injected sidecar) | Git vs mutating webhook | Tell the GitOps diff to ignore injected containers, or render the sidecar into the manifest |
| `metadata.annotations["kubectl.kubernetes.io/restartedAt"]` | `rollout restart` vs Git | Expect it; exclude it from drift comparison |
| `caBundle` in webhook configurations | cert controller vs Git | Controller owns; ignore the field |
| `.status` | Controllers | Never in Git |

```yaml
# GitOps controller: declare the boundary instead of fighting it (Argo CD style)
ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers: [/spec/replicas]
  - group: admissionregistration.k8s.io
    kind: MutatingWebhookConfiguration
    jqPathExpressions: [".webhooks[]?.clientConfig.caBundle"]
syncPolicy:
  syncOptions: [ServerSideApply=true, RespectIgnoreDifferences=true]
```

Diagnose a fight by observation, not theory. If an object's `metadata.generation` or `resourceVersion` climbs continuously while nothing deploys, two controllers are alternately overwriting each other. Look at the managed fields to find the two names, then at each one's logs.

```bash
kubectl get deploy orders-api -n orders-prod -o json --show-managed-fields \
  | jq -r '.metadata.managedFields[] | "\(.manager)\t\(.operation)\t\(.time)\t\(.fieldsV1|keys|join(","))"'
kubectl get deploy orders-api -n orders-prod -w -o jsonpath='{.metadata.generation}{"\t"}{.metadata.resourceVersion}{"\n"}'   # rising with no deploys = a fight
```

A field-manager conflict is cheap compared with an uncontrolled loop: reconcile loops that write on every pass generate API load, audit-log volume and, for Pod-template fields, rolling restarts. A flapping replica count produces a restart on every scale event only if the template changes; a controller that writes a timestamp annotation into the template restarts the Deployment on every reconcile.

**Pruning and ownership across systems.** Pruning ("delete what Git no longer declares") is the most dangerous capability a deployment controller has, because correctness depends on the label or inventory that defines "what I own". Failures to design out: two applications whose selectors overlap, so one deletes the other's objects; a rename that is interpreted as delete-and-create, dropping a PersistentVolumeClaim with it; an inventory that is lost when the controller is reinstalled.

| Control | How |
| --- | --- |
| Narrow ownership | Inventory-based pruning (an ownership object that lists exactly what was applied) rather than label-based |
| Protect stateful objects | `argocd.argoproj.io/sync-options: Prune=false` or `kustomize.toolkit.fluxcd.io/prune: disabled` on PVCs, CRDs and namespaces |
| Reclaim policy | StorageClass `reclaimPolicy: Retain` for data that matters, so deleting the claim does not delete the volume |
| Dry-run prune | Review the deletion list before the first prune in a new environment |
| Deletion guard | Admission rule rejecting deletion of annotated objects, or a finalizer owned by the platform |

**Stateful constraints that packaging cannot hide.** A StatefulSet changes what a "release" means.

| Property | Consequence for packaging and upgrade |
| --- | --- |
| `volumeClaimTemplates` is immutable | Resizing or changing the storage class is not a template edit. Expand each PVC in place (if the class allows expansion), then recreate the StatefulSet with `--cascade=orphan` so Pods and volumes stay |
| `serviceName` and selector are immutable | A rename is a migration, not a patch |
| Ordered, one-at-a-time update (`RollingUpdate`) | A broken new version at ordinal 2 halts the update there; the lower ordinals are unaffected only if you also use a `partition` |
| `podManagementPolicy: Parallel` | Faster start; unsafe for systems that need quorum order |
| Storage is zone-bound | A replacement Pod may be unschedulable if its volume lives in a zone with no capacity |
| `persistentVolumeClaimRetentionPolicy` | Decides whether scaling down or deleting deletes the claims; the default retains them (and incurs cost) |

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate: { partition: 2 }      # only ordinal >= 2 updates; lower ordinals stay on the old version
  persistentVolumeClaimRetentionPolicy: { whenDeleted: Retain, whenScaled: Retain }
```

Use `partition` for a canary on stateful systems: set it to `replicas - 1`, update, verify replication health for a defined period, then lower it step by step. A StatefulSet upgrade is safe only if the application's replication protocol tolerates mixed versions. Read the vendor's upgrade matrix, and test the rollback of data, not only of Pods: a downgrade after the new version has migrated on-disk format is usually impossible. State the point of no return explicitly in the runbook.

**Complex upgrades: choosing the order.** An upgrade that spans the cluster, an operator, CRDs and workloads has a dependency order, and reversing any step creates a failure that is hard to attribute.

```text
1. Read deprecations:   which API versions used by manifests are removed in the target Kubernetes version?
2. Upgrade tooling:     controllers (GitOps, cert, ingress, operators) to versions that support BOTH old and new APIs
3. Migrate manifests:   to the new API versions (rendered, committed, rolled out) while still on the old cluster
4. Upgrade cluster:     control plane, then node pools one at a time; PDBs and spread constraints are what protect workloads
5. Upgrade CRDs:        separately, additive-first; conversion webhooks tested; storage version migrated
6. Remove compatibility shims and old values after one stable cycle
```

```bash
# Find removed APIs before the upgrade, from manifests and from live objects
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis           # live requests to deprecated APIs
kubectl-convert -f old-ingress.yaml --output-version networking.k8s.io/v1       # mechanical migration
pluto detect-files -d rendered/ --target-versions k8s=v1.32.0                   # scan rendered output
```

CRD upgrades deserve a standing rule: Helm installs CRDs from the `crds/` directory once and never upgrades or deletes them, which means that a chart upgrade can deploy controllers that expect a schema the cluster does not have. Manage CRDs in a separate pipeline, version them with the controller, and never delete a CRD without first confirming that no custom resource instances exist: deleting the definition deletes every object of that kind, in every namespace.

```bash
kubectl get crd certificates.cert-manager.io -o jsonpath='{.status.storedVersions}'   # versions present in etcd
kubectl get certificates.cert-manager.io -A --no-headers | wc -l                       # instances that deletion would destroy
```

**Cost and availability: the same knobs.** Requests determine what you pay for (the scheduler reserves them); limits determine what you can lose; replica counts and spread determine availability. Optimising one affects the others.

| Decision | Cost effect | Availability effect | Trade-off to state |
| --- | --- | --- | --- |
| Lower CPU/memory requests to match usage | Fewer nodes | Less headroom for bursts; higher eviction risk if too low | Use p90 plus margin, and verify under load |
| Higher memory request equal to limit (Guaranteed QoS) | More reserved capacity | Last to be evicted under node pressure | Reserve for critical, small workloads |
| `maxSurge: 25%` vs `0` | Needs surge capacity | Zero capacity loss during rollout | Surge cost is brief; unavailability cost is not |
| Three zones with `minReplicas: 3` | More nodes in more zones; cross-zone traffic charges | Survives a zone loss | Compute the traffic charge before declaring it free |
| Spot / preemptible nodes for stateless tiers | Large saving | Sudden loss of nodes | Requires PDB, spread, graceful shutdown under 30 seconds, and an on-demand floor |
| Aggressive autoscaler scale-down | Lower idle cost | Cold capacity when load returns | Longer `scaleDown` window; keep minimum |
| Retained PVCs after scale-down | Orphaned storage cost | Faster scale-up with data in place | Inventory and expire unneeded claims |

Express the availability target in numbers and test it. For example: "survive loss of one zone with at most 5% additional error rate for two minutes" implies three zones, a spread constraint, requests that leave 50% headroom per remaining zone, and a readiness-driven rollout. Then drain a zone in a game day and record what actually happened. Capacity arithmetic: with N zones and R replicas evenly spread, losing one zone leaves `R × (N−1)/N` replicas; the remaining replicas must absorb `R / (R × (N−1)/N)` times the load, so with three zones each Pod must handle 50% more traffic than before. If the autoscaler targets 60% CPU utilisation, post-failure utilisation approaches 90%, which is close to saturation. The target utilisation is therefore an availability setting, not only a cost setting.

**Fleet failures: patterns and defences.** Fleet incidents have a shared structure: one change reaches many clusters or services faster than the signal that it is bad.

| Failure | Mechanism | Defence |
| --- | --- | --- |
| A chart default change rolls out to 300 services in one sync wave | Everyone consumes `latest` or a range; GitOps syncs automatically | Exact pins; bumps by bot in waves; rendered-diff budget per wave |
| A shared ConfigMap edit restarts 80 Deployments | Shared object plus checksum annotation | Per-workload config; `maxUnavailable`/`maxSurge` plus rollout concurrency limits in the controller |
| Cluster-wide webhook outage blocks all Pod creation | `failurePolicy: Fail` on a webhook with no redundancy; namespace selector includes `kube-system` | Exclude system namespaces; replicas and PDB for the webhook; `failurePolicy: Ignore` for non-critical rules; alert on webhook latency |
| Image registry outage or rate limit stops scale-out | Every new node pulls the same images | Internal mirror or pull-through cache; `imagePullPolicy: IfNotPresent` with digests; pre-pulled critical images |
| A GitOps controller upgrade mass-prunes | Inventory format changed | Test controller upgrades on a canary cluster with real inventory; pruning disabled during the upgrade |
| Certificate expires everywhere at once | One renewal job, one expiry date | Stagger issuance; alert at 21 and 7 days; test renewal in staging |
| Rollout storm after a node-pool upgrade | Many Pods rescheduled simultaneously, pulling images and warming caches | PDBs, `maxSurge`, node-pool surge limits, per-cluster rollout concurrency |
| Misapplied manifest to the wrong cluster | Wrong kubeconfig context | Controllers pull per cluster; no human credentials with write access to production; context in the prompt and guarded in scripts |

```text
Staged fleet rollout (waves by blast radius, not by team)
wave 0   canary cluster, synthetic traffic            watch 30 min
wave 1   2 small production clusters in one region    watch 1 h; auto-halt on SLO burn or crash-loop rate
wave 2   one region                                   watch 2 h
wave 3   remaining regions, one at a time             halt switch tested; no wave starts in a change freeze
```

The defence that works at fleet scale is a *halt condition evaluated automatically between waves*: error-budget burn rate, `CrashLoopBackOff` count, `kube_deployment_status_replicas_unavailable`, and admission webhook latency. A human reading a dashboard is too slow when a bad change reaches hundreds of objects in minutes. Equally, rehearse the *stop*: a fleet that can roll out in 20 minutes but takes two hours to freeze has a design flaw. Keep an emergency path that can pause reconciliation for all clusters without needing the clusters themselves to be healthy.

**Postmortem exemplar: one default, forty services.** A platform chart minor release changed the default `terminationGracePeriodSeconds` from 60 to 30 as part of tidying. Services consumed `^3.4` and synced automatically. Nothing failed health checks; Deployments rolled out normally. Over the next two days, services with long batch handlers began dropping requests during routine deploys, because `SIGKILL` arrived after 30 seconds. Contributing factors: the version range allowed silent bumps, the change was not classified as breaking although rendered output changed, rendered-diff review existed only for values and not for chart upgrades, and no load test ran during a rollout. Corrective actions, in order of leverage: exact pins with automated bump proposals that include the rendered diff; define "changes any rendered output" as a minor-at-least and "changes runtime behaviour" as breaking; add a chart test that asserts defaults against a golden file; add a termination test to the release gate. Notice that none of the fixes is "be more careful".

**Design review questions for an expert.** For any packaging or workload design, ask: Which fields have more than one writer, and where is the boundary documented? What happens if the controller that applies this is down, or reinstalled, or upgraded? Which of these objects can be destroyed by a prune, a rename or a CRD deletion? What is the largest set of services a single change can touch, and what limits it? Where is the point of no return in an upgrade, and have we rehearsed everything before it? What does availability cost in the number that finance sees, and what does the cheaper option cost in the number the on-call engineer sees?

**Exercise 1 (field ownership).** On a test cluster run a GitOps controller, an HPA and a mutating webhook that injects a sidecar. Produce the managed-fields report, identify each owner, and configure the controller so that the live state is stable with no drift reported.

**Exercise 2 (stateful upgrade).** Upgrade a three-replica StatefulSet using `partition` as a canary. Demonstrate that ordinal 2 runs the new version while 0 and 1 run the old, verify replication, and document the point of no return.

**Exercise 3 (API removal).** Take a repository of rendered manifests and scan it against the next Kubernetes version. Produce the migration plan in dependency order, including CRDs and controllers.

**Exercise 4 (fleet design).** Design a four-wave rollout of a chart major version across 120 services and 6 clusters. Specify the halt conditions with metric names and thresholds, the pause mechanism, and how you prove that the pause works.

**Exercise 5 (capacity arithmetic).** For a service with 6 replicas across 3 zones and a 60% CPU utilisation target, calculate utilisation after losing a zone, state whether the service is safe, and choose a new target or replica count.

**Mentoring prompts.** When is a typed configuration language worth the learning cost over Helm? How would you migrate a hundred services from one chart major version to the next without a flag day? What breaks if an autoscaler and a GitOps controller both set replicas?

---
