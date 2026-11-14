# T-PLT-02-P — Professional Engineering

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-p"></a>
#### T-PLT-02-P — Professional Engineering

**Packaging as a platform API.** The package a team consumes *is* the interface to the platform. Design it like an API: a small, documented set of values; safe defaults; validation; versioning with a changelog; deprecation policy; and tests. Hide complexity that teams should not decide (security contexts, probes, labels) and expose decisions that belong to them (replicas, resource sizes within limits, environment variables).

**Quality gates for manifests**

| Gate | Tools or checks |
| --- | --- |
| Syntax and schema | `kubectl --dry-run=server`, schema validators |
| Policy | Admission policy rules evaluated offline in CI (no cluster credentials) |
| Security | Non-root, no privilege escalation, dropped capabilities, no host namespaces, memory limits, digest-pinned images |
| Diff review | Rendered output diffs on pull requests |
| Rollout safety | Probes present, disruption budget sized, resource requests set |

Render in CI and diff against the previous version so reviewers see the effect of a values change, not just the values.

**Ownership and drift.** One owner per object; reconcile through a controller; avoid mixing imperative changes. Annotate ownership (`app.kubernetes.io/managed-by`) and keep an ownership table that says which system manages which resources. Never let a pruning controller delete objects owned by another system.

**Upgrade and compatibility policy for charts.** Semantic versioning; breaking value changes need a migration note and, when possible, backward-compatible aliases for a deprecation period; test upgrades from the previous release as well as fresh installs; pin chart and image versions in environments; roll out changes through staging first.

**Configuration management rules**

| Rule | Reason |
| --- | --- |
| Same image across environments; config injected | Promote the artefact, not a rebuild |
| Keep secrets out of values files in Git | Leakage |
| Separate environment-specific values from shared defaults | Reviewable differences |
| Use content hashes to trigger rollouts | Predictable behaviour |
| Document every value with its default and constraints | Usability |

**Autoscaling in production.** Pair the horizontal autoscaler with correct requests, a sensible minimum for availability, a maximum for cost, stabilisation windows to avoid flapping, and a node-level autoscaler. Consider custom metrics (queue depth, request rate) for workloads where CPU does not track load. Verify behaviour with a load test, and watch scale-in for dropped requests (graceful termination).

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Reviewable environment differences | Kustomize overlays or rendered diffs | Copy-pasted YAML per environment |
| Third-party software | Helm chart with pinned version and reviewed values | Hand-written clones of vendor manifests |
| Reusable team package | Chart with schema, defaults, tests, changelog | Unvalidated free-form values |
| Predictable config rollouts | Hash-named ConfigMaps or checksum annotations | Editing live ConfigMaps |
| Scale safely | Requests, min and max, stabilisation, drain | Autoscaling without resource requests |
