# T-PLT-02-P — Professional Engineering

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-p"></a>
#### T-PLT-02-P — Professional Engineering

**What changes at this level.** A professional owns the manifests as a long-lived production asset, not as the output of one deployment. The questions shift from "does it run" to: can it be changed safely by someone else at 03:00, who owns each object, what happens when a node drains, what exactly is deployed, and how do we know a change is safe before it reaches users? The sections below cover manifest security and reliability, ownership, immutable delivery, lifecycle and health design, release design, and configuration governance.

**Packaging as a platform API.** The package a team consumes *is* the interface to the platform. Design it like an API: a small, documented set of values; safe defaults; validation; versioning with a changelog; deprecation policy; and tests. Hide complexity that teams should not decide (security contexts, probes, labels) and expose decisions that belong to them (replicas, resource sizes within limits, environment variables).

A useful test of a package interface is to count what a team must write to deploy a conforming service:

```yaml
# The whole consumer-facing surface of a hypothetical platform chart
name: orders-api
image: { repository: registry.example.com/orders-api, digest: "sha256:7ab2...41cd" }
replicas: { min: 3, max: 12 }
resources: { cpu: 250m, memory: 384Mi }
ports: { http: 8000 }
health: { readyPath: /ready, livePath: /health }
config: { LOG_LEVEL: info }
secrets: [ { name: orders-db, key: password, env: DB_PASSWORD } ]
```

If a team needs to write more than this for a normal service, the interface is leaking; if the platform team must approve a change to this file for routine work, the interface is too narrow. Every field you expose is a compatibility promise.

**Security of manifests**

| Control | Setting | Failure it prevents |
| --- | --- | --- |
| Non-root | `runAsNonRoot: true`, explicit `runAsUser` | Root inside the container turning a file-write bug into host-level impact |
| No privilege escalation | `allowPrivilegeEscalation: false` | setuid binaries gaining capabilities |
| Capabilities | `drop: ["ALL"]`, add back only what is justified | Network and mount operations the app never needs |
| Filesystem | `readOnlyRootFilesystem: true` with explicit `emptyDir` | Persistence of attacker-written binaries |
| Syscalls | `seccompProfile: RuntimeDefault` | Rarely used kernel attack surface |
| Service account | `automountServiceAccountToken: false` unless the app calls the API | Stolen token giving API access |
| Host access | No `hostNetwork`, `hostPID`, `hostPath` | Node-level exposure |
| Image | Digest-pinned from an approved registry | Tag mutation, unreviewed images |
| Secrets | Mounted or referenced from an external store, never in Git | Credential exposure in history |

```yaml
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: api
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities: { drop: ["ALL"] }
      volumeMounts:
        - { name: tmp, mountPath: /tmp }
  volumes:
    - { name: tmp, emptyDir: { sizeLimit: 64Mi } }
```

The built-in Pod Security Standards (restricted profile) express most of this as namespace labels (`pod-security.kubernetes.io/enforce: restricted`). Enforce there, but also keep the settings in the package so that the manifest is correct without depending on a cluster-side check. Defence in depth means the chart is secure by default and the cluster rejects anything that is not.

**Reliability of manifests: what happens during disruption.** Most outages that involve "Kubernetes did something" are voluntary disruptions that the manifest did not anticipate: node drains, cluster upgrades, autoscaler consolidation.

| Mechanism | Purpose | Common error |
| --- | --- | --- |
| PodDisruptionBudget | Limits how many Pods a *voluntary* eviction may remove at once | `minAvailable` equal to `replicas` blocks every drain; no PDB at all lets a drain remove everything |
| Topology spread constraints | Spread replicas across zones and nodes | Soft constraint ignored; all replicas land on one node |
| Anti-affinity | Keep replicas on different nodes | Hard required rule with more replicas than nodes leaves Pods Pending |
| Priority class | Decide who is evicted or preempted first | Everything marked critical, so nothing is |
| Requests = limits (memory) | Predictable eviction order under node pressure | Memory request far below real use makes the Pod an early eviction candidate |
| Graceful termination | In-flight requests complete | `SIGTERM` ignored; grace period shorter than longest request |

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: orders-api }
spec:
  maxUnavailable: 1
  selector: { matchLabels: { app.kubernetes.io/name: orders-api } }
---
# in the Deployment's Pod template
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector: { matchLabels: { app.kubernetes.io/name: orders-api } }
```

A PDB protects only against evictions that go through the eviction API. It does not protect against a node crash, an OOM kill, or a `kubectl delete pod`. Availability against involuntary failure comes from replica count, spread and fast, correct readiness.

**Quality gates for manifests**

| Gate | Tools or checks |
| --- | --- |
| Syntax and schema | `kubectl --dry-run=server`, schema validators |
| Policy | Admission policy rules evaluated offline in CI (no cluster credentials) |
| Security | Non-root, no privilege escalation, dropped capabilities, no host namespaces, memory limits, digest-pinned images |
| Diff review | Rendered output diffs on pull requests |
| Rollout safety | Probes present, disruption budget sized, resource requests set |

Render in CI and diff against the previous version so reviewers see the effect of a values change, not just the values.

```bash
# CI job (no cluster credentials required for the first four steps)
helm template orders-api ./chart -f values/production.yaml > rendered/production.yaml
kubeconform -strict -summary rendered/production.yaml            # schema
conftest test rendered/production.yaml --policy policy/          # policy as code
git diff --no-index --stat rendered-main/production.yaml rendered/production.yaml   # blast radius
# Gated to a protected job with read-only cluster access:
kubectl diff -f rendered/production.yaml
```

Policy rules need an owner and a waiver route. A rule with no exception process gets bypassed informally; an exception with no expiry date becomes permanent. Record each waiver with the owner, the reason and a review date.

**Ownership and drift.** One owner per object; reconcile through a controller; avoid mixing imperative changes. Annotate ownership (`app.kubernetes.io/managed-by`) and keep an ownership table that says which system manages which resources. Never let a pruning controller delete objects owned by another system.

| Object | Owner | Writer allowed | Notes |
| --- | --- | --- | --- |
| Namespace, quota, network policy | Platform team via cluster repository | GitOps controller | Application teams request changes by pull request |
| Deployment, Service, ConfigMap | Application team via service repository | GitOps controller | Humans do not `kubectl edit` |
| `spec.replicas` of an HPA-managed Deployment | HPA | HPA | Field omitted from Git |
| CRDs for third-party operators | Platform team | Separate pipeline | Never part of an app release |
| Secrets | External secret store | Secret operator | Only references in Git |

```bash
kubectl get deploy orders-api -n orders-prod -o jsonpath='{.metadata.annotations}' | tr ',' '\n' | grep -E 'managed-by|argocd|flux|helm'
kubectl get deploy -n orders-prod -o json | jq -r '.items[] | select(.metadata.labels["app.kubernetes.io/managed-by"]==null) | .metadata.name'   # unowned objects
```

Drift has two sources: people changing live objects and controllers mutating fields. Detect drift continuously (the GitOps controller's "out of sync" status, or a scheduled `kubectl diff`), and decide per field whether the live value or the Git value wins. Alerting on drift without a documented policy produces noise that nobody acts on.

**Immutable delivery.** The thing promoted between environments must be the same bytes. That requires immutability at three layers.

| Layer | Mutable (avoid) | Immutable (use) |
| --- | --- | --- |
| Image | Tag `1.8` or `latest`, which can be re-pushed | Digest `@sha256:...`, with the tag kept for humans |
| Package | Chart range `^1.4`, or a Git branch | Exact chart version or a Git commit SHA |
| Configuration | ConfigMap edited in place | Hash-named generated object, committed to Git |

```text
build ──▶ image@sha256:7ab2…        (once, signed, scanned)
  └──▶ commit "bump orders-api digest" in the environment repository
          staging  ──(same digest, staging overlay)──▶ verified
          production ──(same digest, production overlay)──▶ promoted by pull request
```

Rendered output can also be committed ("rendered manifests pattern"): the repository then contains exactly what will be applied and the review shows the true change. The cost is a CI step that must keep it in sync; the benefit is that a template-engine upgrade cannot silently change production output without appearing in a diff.

Record at deploy time which digest, chart version, values commit and overlay commit produced each environment. Without that record, "what is running in production" is an investigation instead of a lookup.

**Lifecycle and health design.** Probes are a contract between the application and the platform; a wrong contract causes outages that look like application bugs.

| Probe | Should check | Must not check | Typical settings |
| --- | --- | --- | --- |
| Startup | Process finished initialising (migrations applied, caches warm enough) | Downstream dependencies | `failureThreshold × periodSeconds` ≥ worst observed start time with margin |
| Readiness | Can serve a request now: local state, required config, and critical dependencies *the Pod can recover from by waiting* | Optional dependencies; anything that fails for every Pod at once | `periodSeconds: 5`, `failureThreshold: 2`, `timeoutSeconds` above p99 of the endpoint |
| Liveness | The process is not deadlocked | Any dependency; anything slow | `periodSeconds: 10`, `failureThreshold: 3`, generous `timeoutSeconds` |

The rule that matters: a readiness check that fails for *all* Pods at once (a shared database outage) removes every endpoint and converts a partial degradation into a total outage. Decide per dependency whether the application should serve degraded responses instead; report the dependency state in metrics, not in readiness. Then test the decision by stopping the dependency in staging.

```yaml
          startupProbe:
            httpGet: { path: /health, port: 8000 }
            periodSeconds: 2
            failureThreshold: 60            # up to 120 s to start
          readinessProbe:
            httpGet: { path: /ready, port: 8000 }
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
          livenessProbe:
            httpGet: { path: /health, port: 8000 }
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
```

Lifecycle events also include init containers (run to completion before the app starts; use for waiting on a prerequisite that never changes, not for schema migrations that other replicas race to run), `preStop` hooks, and termination. Database migrations deserve their own mechanism: a Job run before the rollout, with an expand-and-contract schema policy so that the old and new application versions both work against the intermediate schema during the rollout.

**Release design.** Choose a release strategy by the failure you must survive, not by fashion.

| Strategy | Mechanism | Strength | Cost / limit |
| --- | --- | --- | --- |
| Rolling update | One Deployment, new ReplicaSet scales up | Simple, built in | Old and new run together; rollback is another rollout |
| Blue/green | Two Deployments; flip the Service selector or route | Instant switch and rollback | Double capacity during the window; state must be compatible |
| Canary | Small fraction of traffic to the new version, then widen | Real-traffic verification | Needs traffic splitting and automated analysis; metrics must be good |
| Recreate | Stop old, start new | Never two versions at once | Downtime |

A release is safe when all of these are answerable before it starts: What is the success signal and how long do we watch it? What is the rollback trigger, and is it automated? Can old and new versions coexist (schema, message formats, cache keys)? Is capacity sufficient for the surge? Who is on call?

```bash
# A rollout gate in a pipeline: wait for availability, then confirm the SLI before widening
kubectl rollout status deploy/orders-api -n orders-prod --timeout=10m
curl -s "$PROM/api/v1/query" --data-urlencode 'query=sum(rate(http_requests_total{app="orders-api",code=~"5.."}[5m]))/sum(rate(http_requests_total{app="orders-api"}[5m]))' | jq -r '.data.result[0].value[1]'
# threshold breach -> kubectl rollout undo, then page the owner
```

Rollback is not free. A rollback of the Deployment does not roll back the database schema, queued messages written by the new version, or an irreversible ConfigMap or Secret change. State the rollback boundary in the release record.

**Configuration governance.** Configuration changes cause a large share of incidents because they bypass the review a code change receives.

| Control | Practice |
| --- | --- |
| Same path as code | Configuration changes via pull request, rendered diff, and the same promotion path |
| Typed and validated | Schema for values; admission policy for the result |
| Scoped | One ConfigMap per workload; avoid a shared "global config" that can change fifty services at once |
| Classified | Public, internal, secret; secrets never in Git and never in `values.yaml` |
| Attributable | Every change traceable to a person, a ticket and a time |
| Reversible | A hash-named ConfigMap or Git revert restores the previous state |
| Rotated | Credentials have owners and rotation dates; rotation is rehearsed |

Secrets deserve their own design. Prefer a reference to an external secret store, synchronised into a Kubernetes Secret by an operator, over committing encrypted blobs; if sealed or encrypted secrets are used, record who holds the decryption key and how it is rotated. Enable encryption at rest for Secrets in etcd, restrict `get` and `list` on Secrets with RBAC (a `list` permission reveals every value), and rotate by writing a new version and rolling Pods, as environment variables do not update in running Pods.

**Upgrade and compatibility policy for charts.** Semantic versioning; breaking value changes need a migration note and, when possible, backward-compatible aliases for a deprecation period; test upgrades from the previous release as well as fresh installs; pin chart and image versions in environments; roll out changes through staging first.

```yaml
# templates/_helpers.tpl: accept the old value name for one major version
{{- define "orders-api.replicas" -}}
{{- coalesce .Values.replicas.min .Values.replicaCount 2 -}}
{{- end -}}
```

```bash
helm template rel ./chart-prev -f values/prod.yaml > /tmp/prev.yaml
helm template rel ./chart-next -f values/prod.yaml > /tmp/next.yaml
diff /tmp/prev.yaml /tmp/next.yaml        # expectation: empty, or an explained and approved diff
```

A chart release should ship a changelog entry that states: what changed in the rendered output, which values were added, deprecated or removed, whether any object will be recreated (immutable fields), and whether CRDs need a separate step.

**Configuration management rules**

| Rule | Reason |
| --- | --- |
| Same image across environments; config injected | Promote the artefact, not a rebuild |
| Keep secrets out of values files in Git | Leakage |
| Separate environment-specific values from shared defaults | Reviewable differences |
| Use content hashes to trigger rollouts | Predictable behaviour |
| Document every value with its default and constraints | Usability |

**Autoscaling in production.** Pair the horizontal autoscaler with correct requests, a sensible minimum for availability, a maximum for cost, stabilisation windows to avoid flapping, and a node-level autoscaler. Consider custom metrics (queue depth, request rate) for workloads where CPU does not track load. Verify behaviour with a load test, and watch scale-in for dropped requests (graceful termination).

```yaml
spec:
  minReplicas: 3                     # availability floor: survives one node loss
  maxReplicas: 12                    # cost ceiling; alert when pinned at max
  behavior:
    scaleUp:   { stabilizationWindowSeconds: 0,   policies: [ { type: Percent, value: 100, periodSeconds: 60 } ] }
    scaleDown: { stabilizationWindowSeconds: 300, policies: [ { type: Pods,    value: 1,   periodSeconds: 60 } ] }
```

Scale up quickly and scale down slowly. If the maximum is reached, the system is at the capacity limit you chose; alert on it, as it is a decision point and not a steady state.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Reviewable environment differences | Kustomize overlays or rendered diffs | Copy-pasted YAML per environment |
| Third-party software | Helm chart with pinned version and reviewed values | Hand-written clones of vendor manifests |
| Reusable team package | Chart with schema, defaults, tests, changelog | Unvalidated free-form values |
| Predictable config rollouts | Hash-named ConfigMaps or checksum annotations | Editing live ConfigMaps |
| Scale safely | Requests, min and max, stabilisation, drain | Autoscaling without resource requests |
| Survive node drains | PDB with `maxUnavailable`, spread constraints, graceful shutdown | `minAvailable` equal to replicas |
| Know what runs | Digest, chart version and commit recorded per deploy | Tags and version ranges |

**Worked review: a manifest change that looked small.** A pull request changes one value: `resources.limits.memory` from `256Mi` to `128Mi` for cost reasons. The rendered diff shows the Deployment's Pod template changed, so a rollout will occur in every environment that consumes the chart. A reviewer checks: observed peak memory (from metrics: 190Mi, so the new limit would OOM-kill), whether a PDB limits the damage (it does not limit OOM kills), and whether staging load matches production (it does not). The review comment is a decision with evidence, not "looks fine": reject the change, request a staged test at production-like load, and attach the usage graph. This is the practice that rendering and reviewing the effect of a change, rather than the diff of a value, enables.

**Operational checklist before a workload is called production-ready**

| Area | Evidence required |
| --- | --- |
| Identity and ownership | Labels, owner annotation, on-call route |
| Security | Restricted profile passes; digest-pinned; no Secrets in Git |
| Availability | At least 3 replicas or an explicit exception; PDB; spread across zones |
| Health | Startup, readiness, liveness defined with a documented contract |
| Resources | Requests and memory limit from measured data; autoscaler bounds justified |
| Delivery | Same digest promoted through environments; rollback tested; rendered diff reviewed |
| Configuration | Hash-named or checksum-triggered; schema validated; secrets via external source |
| Termination | Load test during a rollout shows no dropped requests |

**Exercise 1 (security review).** Take a vendor chart's rendered output and produce a table of every privileged setting, host access, wide RBAC rule and unpinned image, with the override or policy that addresses each.

**Exercise 2 (disruption).** Drain a node holding two replicas of a three-replica service with and without a PDB and spread constraints. Record the minimum available replicas observed in each case.

**Exercise 3 (immutable delivery).** Promote one digest through staging to production with only overlay differences, and write the record that shows which digest, chart version and commit are running in each.

**Exercise 4 (health contract).** Stop the database in staging. Show what readiness and liveness do for each probe design (dependency in readiness, in liveness, in neither), and choose one with a written justification.

**Exercise 5 (policy).** Write one offline policy rule that rejects a Deployment with a mutable image tag, test it on a passing and a failing manifest, and define the waiver route.
