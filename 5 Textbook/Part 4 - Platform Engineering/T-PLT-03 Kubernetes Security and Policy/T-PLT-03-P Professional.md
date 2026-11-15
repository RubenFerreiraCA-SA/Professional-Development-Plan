# T-PLT-03-P — Professional Engineering

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-p"></a>
#### T-PLT-03-P — Professional Engineering

## Why this matters

At Intermediate level you secured one namespace by hand and proved it. Professional practice secures *many* namespaces owned by *many* teams, continuously, without relying on every team remembering the same twenty settings. The unit of work changes from "a correct manifest" to "a platform guarantee": a statement such as *no workload in a tenant namespace can run privileged, pull from an unapproved registry, or reach another tenant's network*, enforced where objects enter the cluster, rolled out without breaking anyone, and backed by evidence an auditor can read.

That requires four skills: writing policy as code, rolling it out progressively, packaging a tenant baseline so every new namespace starts safe, and producing evidence that the controls work and are reviewed. It also requires honesty about limits: every control below has a bypass or a failure mode, and the Expert section examines them. Here we build the working system.

The section assumes the earlier levels: RBAC, ServiceAccounts, quotas, Pod Security Admission and NetworkPolicy. Examples use the neutral service `orders-api`, a fictional registry `registry.example.com` and placeholder digests. Anything labelled *illustrative* shows the expected shape; reproduce it on a practice cluster before relying on it, and check API versions against the Kubernetes release you actually run.

## First principles: where policy decisions live

Several mechanisms can say "no" to a request. Knowing which is which is what lets you diagnose a denial and choose the right tool.

| Mechanism | Judges | Strength | Weakness |
| --- | --- | --- | --- |
| RBAC | Who may perform which verb on which resource | Always on; simple to reason about | Cannot inspect object *content* (an image name, a label) |
| Pod Security Admission | Pod specs against three fixed standards | Built in; no extra components | Fixed rules; cannot express "approved registries" |
| ValidatingAdmissionPolicy (CEL) | Any object field, with expressions you write | In-process; no webhook to fail; versioned with the cluster | Cannot call external systems; no mutation in older releases |
| Admission webhooks (policy engines such as Kyverno or OPA Gatekeeper) | Anything the engine supports, including external data, mutation and image-signature checks | Richest features | An extra service to run; availability becomes a security question |
| CI checks | Manifests before they merge | Fast feedback for authors | Bypassed by anything that does not use CI |

**Policy as code at admission.** Rules enforced where objects enter the cluster catch everything that bypassed CI: a hurried `kubectl apply`, a controller creating Pods, an operator's template. Kubernetes includes `ValidatingAdmissionPolicy` (CEL expressions, no extra controller in recent versions); policy engines such as Kyverno or OPA Gatekeeper add richer rules and mutation. This chapter uses `ValidatingAdmissionPolicy` for examples because it has the fewest moving parts; the design rules carry over to any engine.

## A first admission policy

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: require-image-digest }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  validations:
    - expression: "object.spec.template.spec.containers.all(c, c.image.contains('@sha256:'))"
      message: "Images must be referenced by digest, not tag."
```

A policy does nothing until a **binding** selects where it applies and what happens on violation:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata: { name: require-image-digest-tenants }
spec:
  policyName: require-image-digest
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchLabels: { platform.example.com/tenant: "true" }
```

Reading the pieces: `matchConstraints` says which requests the policy sees; `validations` are CEL expressions that must evaluate to `true`; `failurePolicy` says what happens when the *policy itself* cannot be evaluated (for example a type error), not when a request violates it; `validationActions` decides the consequence of a violation; the binding's `namespaceSelector` scopes it to tenant namespaces, leaving system namespaces alone.

This first policy has a design flaw worth finding before anyone else does: it only inspects **Deployments**. A bare Pod, a Job, a CronJob or a StatefulSet passes untouched. Because every workload eventually becomes a **Pod**, the more robust place to enforce is the Pod itself.

### A Pod-level policy with parameters

The version below inspects Pods (so it covers every controller), includes init containers, takes the approved registry prefix from a *parameter object* so each tenant can differ, and builds an actionable message:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: pods-approved-images }
spec:
  failurePolicy: Fail
  paramKind: { apiVersion: v1, kind: ConfigMap }
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["pods"]
  variables:
    - name: containers
      expression: >-
        object.spec.containers +
        (has(object.spec.initContainers) ? object.spec.initContainers : [])
  validations:
    - expression: "variables.containers.all(c, c.image.contains('@sha256:'))"
      messageExpression: >-
        'Pin images by digest (name@sha256:...). Offending: ' +
        variables.containers.filter(c, !c.image.contains('@sha256:')).map(c, c.image).join(', ')
      reason: Invalid
    - expression: "variables.containers.all(c, c.image.startsWith(params.data.registryPrefix))"
      messageExpression: "'Images must come from ' + params.data.registryPrefix + ' (see the platform docs, section Registries).'"
      reason: Invalid
---
apiVersion: v1
kind: ConfigMap
metadata: { name: orders-registry, namespace: platform-policy }
data:
  registryPrefix: "registry.example.com/orders/"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata: { name: pods-approved-images-orders }
spec:
  policyName: pods-approved-images
  validationActions: [Warn, Audit]          # stage 1; see progressive enforcement
  paramRef:
    name: orders-registry
    namespace: platform-policy
    parameterNotFoundAction: Deny           # a missing parameter must not silently disable the rule
  matchResources:
    namespaceSelector:
      matchLabels: { platform.example.com/tenant: orders }
```

Choices worth defending in review:

- **Validate Pods, not only their owners.** The Pod is the choke point. (Ephemeral containers used for debugging are a separate field and a separate request; decide explicitly whether to cover them.)
- **`parameterNotFoundAction: Deny`.** If the parameter object is deleted, the safe behaviour is refusal, not an unchecked cluster.
- **Messages that tell the author what to do next** and where to read more. A denial that says only "forbidden by policy" generates a support ticket; one that names the offending image and the rule generates a fix.
- **`reason`** controls the HTTP status the client sees (`Invalid` is a 422-style validation failure; `Forbidden` is a 403). Use them consistently so tooling can interpret denials.

A denial then looks like this (*illustrative*):

```text
Error from server (Invalid): error when creating "pod.yaml": pods "demo" is invalid: ValidatingAdmissionPolicy 'pods-approved-images' with binding 'pods-approved-images-orders' denied request: Pin images by digest (name@sha256:...). Offending: busybox:1.36
```

The text identifies policy *and* binding, which separates it from an RBAC `Forbidden` and from a Pod Security `violates PodSecurity` message. Teach teams to read that first line.

## Progressive enforcement

A new mandatory rule applied as `Deny` on day one is an outage with a nice name. The professional pattern is to move through stages and let data decide when to advance.

| Stage | `validationActions` | Effect on teams | Advance when |
| --- | --- | --- | --- |
| 0. Author and test | (not bound; fixtures only) | None | Positive and negative fixtures pass in CI |
| 1. Observe | `[Audit]` | None visible | Audit events show the violation count and *who* creates violators |
| 2. Warn | `[Warn, Audit]` | `kubectl` prints a warning at apply time | Violation rate trends to near zero, owners notified |
| 3. Enforce in a pilot | `[Deny]` on a few volunteer namespaces | Real denials, small blast radius | Pilot teams report no unexplained blockers |
| 4. Enforce broadly | `[Deny]` on all tenants | All new violations refused | Exception process is live and tested |
| 5. Sustain | `[Deny]` + review | Exceptions expire | Quarterly review of rules, messages and exceptions |

How to measure in stage 1 and 2: with audit logging on, admission policy results are recorded as annotations on audit events (look for annotation keys beginning `validation.policy.admission.k8s.io`). Pod Security Admission does the same with its `audit` mode. Ship the audit log somewhere queryable and build a simple report: violations per namespace, per policy, per week. Without a measurement, "teams are ready" is an opinion.

Communication is part of the technique:

- Announce the rule, the date of each stage, and the *fix*, before stage 2.
- Give every denial message a link or a short instruction.
- Provide a **fix path** (a template, a linter, a one-line migration) alongside the rule.
- Expect long-tail owners: for each remaining violator, name a human, not a team alias.

**Exceptions** are a feature of the design, not a failure of it. A workable mechanism: a Git-tracked exceptions file listing namespace (or workload), policy, owner, reason, and an expiry date; automation renders it into binding selectors (for example excluding namespaces carrying a label) and *removes* the exception when it expires. A label added by hand has no expiry; the file and the job that enforces it do.

```yaml
# policy-exceptions.yaml — illustrative structure, reviewed like code
- policy: pods-approved-images
  scope: { namespace: legacy-reports }
  owner: team-reporting
  reason: "Vendor image not yet mirrored; ticket PLAT-1234"
  expires: 2027-02-28
```

## Allowed registries, digests and signatures

Controlling where images come from reduces three risks at once: a typo-squatted image, a compromised public tag, and an unscanned artefact. The layers, in increasing strength:

1. **Allow-list prefix**: images must start with `registry.example.com/<tenant>/`. Cheap, catches most mistakes, shown above.
2. **Digest pinning**: the image reference is immutable content (`@sha256:…`), so what you reviewed is what runs. Tags can move; digests cannot.
3. **Signature or attestation verification**: the image was signed by your build pipeline's identity, or carries an attestation (such as an SBOM or provenance statement) your policy requires. This is usually done by a policy engine or an admission controller built for it, because it needs to fetch and verify signatures from the registry, which in-process CEL cannot.
4. **Pull-through mirrors**: tenants pull from your registry, which proxies or mirrors approved upstream images after scanning. Allow-listing then means "our registry only".

Operational details that decide whether this works:

- Include `initContainers` (as above) and think about sidecars injected by tooling *after* your policy runs, which may use images you do not control.
- Mind `imagePullPolicy` and pull secrets: a digest-pinned image already present on a node runs without a registry check, so node-level image cleanup and registry credentials are part of the picture.
- Keep emergency access: a documented way to deploy a patched image while the registry or signing service is unavailable, with the exception file, an owner and a short expiry.
- Test a *denied* image on every change to the policy. A registry rule that was never seen denying anything is unproven.

## Denied unsafe requests: fixtures and proof

Every policy ships with **fixtures**: small manifests that must be accepted and must be refused, each with the expected reason. They are the unit tests of your platform.

```text
policy-tests/
  allow/
    pod-digest-approved-registry.yaml
    pod-hardened-minimal.yaml
  deny/
    pod-tag-only.yaml                  pod-tag-only.expect       (text: "Pin images by digest")
    pod-unapproved-registry.yaml       pod-unapproved-registry.expect
    pod-privileged.yaml                pod-privileged.expect     (text: "violates PodSecurity")
    pod-hostpath.yaml                  pod-hostpath.expect
    pod-run-as-root.yaml               pod-run-as-root.expect
```

Two test modes serve different purposes. A **live** test against a throwaway cluster uses server-side dry run, which runs the whole admission chain without storing anything:

```bash
#!/usr/bin/env bash
# run-policy-tests.sh — illustrative; run against a lab cluster with the policies installed
set -u; RC=0
for f in policy-tests/allow/*.yaml; do
  kubectl apply --dry-run=server -n policy-lab -f "$f" >/dev/null 2>&1 \
    && echo "ok     accept $f" || { echo "FAIL   should accept $f"; RC=1; }
done
for f in policy-tests/deny/*.yaml; do
  out=$(kubectl apply --dry-run=server -n policy-lab -f "$f" 2>&1) && { echo "FAIL   should deny $f"; RC=1; continue; }
  printf '%s' "$out" | grep -qF "$(cat "${f%.yaml}.expect")" && echo "ok     deny   $f" || { echo "FAIL   wrong reason for $f"; RC=1; }
done
exit $RC
```

An **offline** test evaluates policies against fixtures without any cluster credentials, using the policy engine's command-line tool or a CEL test harness. It runs in every pull request, keeps secrets out of CI, and gives fast feedback; the live test confirms the installed reality. Do both: offline for speed, live for truth.

The table below is the minimum set of "denied unsafe request" proofs for a tenant namespace. Each row should have a stored transcript.

| Unsafe request | Denied by | Typical message fragment |
| --- | --- | --- |
| Pod with `privileged: true` | Pod Security (restricted/baseline) | `violates PodSecurity` … `privileged` |
| Pod mounting `hostPath` | Pod Security or policy | `hostPath volumes` |
| Pod running as root | Pod Security (restricted) | `runAsNonRoot != true` |
| Image by tag from the internet | Admission policy | `Pin images by digest` |
| Image from an unapproved registry | Admission policy | `Images must come from` |
| `exec` into a Pod without the right | RBAC | `cannot create resource "pods/exec"` |
| Tenant editing its own quota | RBAC | `resourcequotas is forbidden` |
| Tenant creating a ClusterRoleBinding | RBAC | `clusterrolebindings.rbac.authorization.k8s.io is forbidden` |
| Service of type LoadBalancer in a tenant | Quota (`services.loadbalancers: 0`) or policy | `exceeded quota` |

## Tenant baselines

A **tenant baseline** is the bundle every new namespace receives automatically, so safety is the default and not an achievement. Rendering it from one template (Helm, Kustomize or a controller) keeps a hundred namespaces identical.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orders-staging
  labels:
    platform.example.com/tenant: orders
    platform.example.com/owner: team-orders
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.30
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: compute, namespace: orders-staging }
spec:
  hard: { requests.cpu: "4", requests.memory: 8Gi, limits.memory: 16Gi, pods: "40", services.loadbalancers: "0", count/secrets: "100" }
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: orders-staging }
spec:
  limits:
    - { type: Container, defaultRequest: { cpu: 100m, memory: 128Mi }, default: { memory: 256Mi } }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: orders-staging }
spec: { podSelector: {}, policyTypes: [Ingress, Egress] }
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: orders-staging }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to: [{ namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }, podSelector: { matchLabels: { k8s-app: kube-dns } } }]
      ports: [{ port: 53, protocol: UDP }, { port: 53, protocol: TCP }]
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: tenant-reconciler, namespace: orders-staging }
automountServiceAccountToken: false
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: tenant-reconciler, namespace: orders-staging }
subjects: [{ kind: ServiceAccount, name: tenant-reconciler, namespace: orders-staging }]
roleRef: { kind: ClusterRole, name: tenant-deployer, apiGroup: rbac.authorization.k8s.io }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: tenant-developers, namespace: orders-staging }
subjects: [{ kind: Group, name: orders-developers, apiGroup: rbac.authorization.k8s.io }]
roleRef: { kind: ClusterRole, name: tenant-readonly, apiGroup: rbac.authorization.k8s.io }
```

(`tenant-deployer` and `tenant-readonly` are platform-owned ClusterRoles you define, bound here by RoleBindings so they apply only in this namespace. `tenant-readonly` deliberately excludes Secrets. The GitOps controller that applies tenant manifests uses `tenant-reconciler`, a namespaced identity, so a compromise of one tenant's pipeline cannot touch another's.)

What the baseline guarantees, and what it leaves to the tenant:

| Platform guarantees | Tenant is responsible for |
| --- | --- |
| Restricted Pod Security, versioned | Correct `securityContext` in their manifests |
| Quota and defaults | Right-sizing requests and limits |
| Default-deny plus DNS | Writing the allow rules their service needs |
| Namespaced identities, no cluster-wide grants | Not sharing credentials; reviewing their group membership |
| Approved registries and digests | Building and promoting images through the pipeline |
| Audit and policy logs | Responding to warnings and denials for their namespaces |

Two operational rules complete the design. **Who may create namespaces** matters: if tenants can create arbitrary namespaces, they can create ones without the baseline, so namespace creation goes through the platform (a request, or a controller), and policy requires the tenant labels. And **who may change namespace labels** decides who can disable Pod Security and policy selection, so reserve it to the platform identity.

## Auditing and evidence

Audit logging is the record of *who did what to the API*. Without it, you can configure controls but cannot show they were used, nor reconstruct an incident. On clusters you operate yourself, the API server reads an **audit policy**; managed services expose equivalent settings through their own interfaces.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages: ["RequestReceived"]
rules:
  - level: None                                   # drop high-volume, low-value noise
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources: [{ group: "", resources: ["endpoints", "services", "services/status"] }]
  - level: Metadata                               # Secrets: who and when, NEVER the body
    resources: [{ group: "", resources: ["secrets", "configmaps", "serviceaccounts/token"] }]
  - level: Metadata                               # interactive access to workloads
    resources: [{ group: "", resources: ["pods/exec", "pods/attach", "pods/portforward"] }]
  - level: RequestResponse                        # authorisation and policy changes, in full
    resources:
      - { group: "rbac.authorization.k8s.io" }
      - { group: "admissionregistration.k8s.io" }
  - level: Request                                # other writes: what was asked
    verbs: ["create", "update", "patch", "delete"]
  - level: Metadata                               # everything else
```

Rules are evaluated in order and the **first match wins**, so the order above is deliberate: Secrets are matched before the generic write rule, because recording a Secret's request or response body would copy the credential into the logs, creating a second, less protected copy.

What to keep, and for how long:

| Evidence | Source | Why it matters |
| --- | --- | --- |
| API audit events (shipped off-cluster) | API server | Reconstruct who changed what; prove policy denials |
| Policy denial and warning counts | Audit annotations, policy engine reports | Show enforcement is real and trending |
| RBAC audit queries output (weekly) | `kubectl` + `jq` jobs | Show least privilege is maintained |
| `cluster-admin` binding review | Query plus sign-off | Show privileged access is justified |
| Forbidden and denial transcripts | Test scripts | Show negative controls were tested |
| Exceptions register | Git | Show every bypass has an owner and an expiry |
| Limitations register | Git | Show what is *not* covered, honestly |

Ship audit logs **off the cluster** to storage that cluster administrators cannot quietly edit. A control plane that holds its own only copy of the evidence is a weak witness. Set retention to the longest of your incident-investigation and compliance needs, and test that you can actually query an event by user and time.

A **limitations register** records known gaps next to each control, for example: "Developer read role is cluster-wide on a legacy cluster", "kind practice cluster does not encrypt Secrets", "NetworkPolicy does not cover host-network Pods". Auditors and incident responders trust a document that names its own weak points more than one claiming completeness.

## Secrets management

Kubernetes Secrets are a *delivery* mechanism and a *convenient* store, not a vault. A professional design answers five questions: where is the source of truth, how does the value reach the Pod, who may read it, how does it rotate, and what happens if it leaks.

| Pattern | Source of truth | How it arrives | Strengths | Costs |
| --- | --- | --- | --- | --- |
| Native Secret, created by hand | The cluster | Mounted or env | Simple | No audit trail of values, hard rotation, risk of copies in Git |
| External store synchronised by an operator | Cloud or vault secret manager | Operator creates a Kubernetes Secret | Central rotation and audit; apps unchanged | Secret still lands in etcd; operator is high-value |
| CSI driver mount | External store | Mounted straight into the Pod as a file | Value need not exist as an API object (optional sync) | Driver on every node; mount-time failures |
| Encrypted-in-Git (sealed) | Git, encrypted | Controller decrypts in cluster | GitOps friendly | Key management; rotation of the sealing key |

A synchronised external secret, with the API version depending on the operator release you install:

```yaml
apiVersion: external-secrets.io/v1beta1        # check the version served by your installed operator
kind: ExternalSecret
metadata: { name: orders-db, namespace: orders-staging }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: platform-store, kind: SecretStore }
  target: { name: orders-db }
  data:
    - secretKey: password
      remoteRef: { key: orders/staging/db, property: password }
```

Rules that apply to any pattern:

- **Per-workload access.** The store grants each ServiceAccount identity access only to its own paths; a tenant cannot read another tenant's secrets by naming them.
- **Short-lived where possible.** Dynamic, expiring database credentials beat long-lived passwords.
- **Rotation is a tested procedure**, with a measured time to rotate everything after a suspected leak.
- **No secrets in manifests, Helm values in Git or images.** Scan commits and images for secret patterns, and treat a leaked value as compromised even after the commit is removed.
- **Restrict reads** with RBAC (no `list` on Secrets for developers), and remember the "create Pods reads Secrets" equivalence: admission policy should stop tenants mounting Secrets they do not own.
- **Encrypt at rest** and protect backups.

Encryption of Secrets in etcd is configured on the API server (where you control it) with an `EncryptionConfiguration`:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: ["secrets"]
    providers:
      - kms:                               # keys held outside the cluster
          apiVersion: v2
          name: platform-kms
          endpoint: unix:///var/run/kms/socket.sock
          timeout: 3s
      - identity: {}                       # last: lets the server still read data written before encryption
```

The first provider encrypts new writes; existing Secrets stay in plaintext until rewritten (the documented approach is to read and replace all Secrets after enabling), and you must keep the old key available until that completes. Verification is direct: read a Secret's raw record from etcd and confirm it begins with an encryption-provider prefix rather than readable JSON. Where a managed service handles this, record *how* it is configured and who controls the key in your limitations register. Encryption at rest protects disks and backups; it does **not** protect a Secret from anyone who can read it through the API.

## Securing the control plane and nodes

Restrict API server exposure; require authentication through an identity provider; enable audit logging and ship logs off-cluster; encrypt etcd and protect its backups; keep kubelet authentication and authorisation on; patch nodes and the control plane on a schedule; harden node operating systems; and restrict the cloud metadata service from Pods.

Concrete checks worth automating:

- Anonymous requests are denied: `curl -k https://<api>/api` should return `401` or `403`, and no binding should grant rights to `system:unauthenticated`.
- Kubelet read-write port is closed and kubelet authentication is `webhook`-based, not anonymous.
- Nodes use the `Node` authoriser and the `NodeRestriction` admission plugin, so a compromised kubelet can only touch objects for its own node.
- Control-plane versions are within the supported window, and upgrades are rehearsed.
- Etcd is reachable only from the API server, over mutual TLS, and backups are encrypted and access-controlled.

## Supply chain at the cluster

Admit only images from approved registries, by digest, with verified signatures or attestations when you have them; scan images and rendered manifests; limit who can create privileged Pods; and treat controllers and operators (which hold powerful permissions) as high-value targets. When adopting an operator, read its ClusterRoles first: a controller that can create Pods and read Secrets across all namespaces is, for security purposes, a cluster administrator with a nicer name.

## Tenancy model

Per-tenant namespace with quota, limit range, default-deny network policy, restricted Pod Security and a namespaced reconciler identity. Soft multi-tenancy (trusted teams) is common; for untrusted tenants consider separate clusters or sandboxed runtimes, because namespaces share a kernel and control plane. Be explicit with leadership about which kind you offer: "tenants are trusted teams of one company" is a legitimate design with legitimate limits, and the limits belong in the limitations register.

## Professional trade-offs

| Decision | Benefit | Cost | Typical choice |
| --- | --- | --- | --- |
| In-process CEL policy vs webhook engine | No new availability dependency | Fewer features (no external data, limited mutation) | CEL for simple rules; engine where needed |
| `Fail` vs `Ignore` on policy errors | Safety vs availability | Outage risk vs silent gaps | `Fail` for security-critical, tested, with break-glass |
| Strict `restricted` PSA everywhere | Strong default | Migration cost for legacy workloads | Enforce for tenants; scoped exceptions with expiry |
| Many small policies vs few large ones | Clear messages, easier staging | More objects to manage | Small, named, individually stageable |
| Central platform team owns policy | Consistency | Bottleneck risk | Platform owns baseline; teams propose changes by pull request |

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Give a team access | Namespaced Role plus RoleBinding | ClusterRoleBinding for convenience |
| Stop unsafe Pods | Pod Security `restricted` plus policy | Relying on reviewers |
| Limit lateral movement | Default-deny NetworkPolicy, verified enforcement | Assuming the policy object works |
| Control images | Digest-only, approved registries, scanning | Tags and unscanned images |
| Handle secrets | External manager, restricted RBAC | Base64 in Git |
| Allow exceptions | Documented, time-boxed, owned | Permanent silent bypass |
| Roll out a new rule | Observe → warn → pilot → enforce, with measurements | Enforcing on day one |

## Knowledge consolidation

- **Policy as code at admission** catches what bypassed CI; enforce on **Pods**, not only on the objects that create them.
- A `ValidatingAdmissionPolicy` needs a **binding**; `validationActions` (`Audit`, `Warn`, `Deny`) is the dial for progressive rollout; `failurePolicy` governs policy *errors*, not violations.
- **Parameters** make one policy serve many tenants; `parameterNotFoundAction: Deny` stops a deleted parameter from disabling it.
- **Stage every rule**: fixtures → observe → warn → pilot → enforce, measuring violations from audit annotations.
- **Exceptions** live in reviewed files with owners and expiries, enforced by automation.
- Combine **prefix allow-lists, digests, signatures and mirrors** for image control, and test a *denied* image.
- A **tenant baseline** (Pod Security, quota, default-deny, namespaced identities) makes safe the default; control who creates namespaces and edits their labels.
- **Audit policy order matters** (first match wins); never record Secret bodies; ship logs off-cluster.
- Treat Secrets as a **delivery mechanism**; external stores give rotation and audit; encryption at rest does not stop API reads.
- Keep a **limitations register**; honesty is evidence.

## Exercises

**Exercise 1 — Stage a policy.** Install the Pod-level `pods-approved-images` policy, its ConfigMap parameter and a binding with `[Audit]`. Create a violating Pod and find the audit annotation (or the policy engine report). Change the binding to `[Warn, Audit]` and observe the client warning, then to `[Deny]` and capture the denial. Keep all three transcripts.

**Exercise 2 — Find the gap.** Apply the Deployment-only `require-image-digest` policy and prove that a bare Pod with a tag-only image is accepted. Then show the Pod-level policy closes the gap. Write one sentence on why enforcing at the Pod matters.

**Exercise 3 — Fixtures.** Build a `policy-tests/` directory with at least three accept and five deny fixtures (privileged, hostPath, root, tag-only, unapproved registry), with `.expect` files, and run the live script. Then break the policy on purpose (loosen the prefix) and show the suite catching it.

**Exercise 4 — A baseline.** Render the tenant baseline for a new namespace `billing-staging` from a template (Kustomize or Helm) with the tenant name as a variable. Prove, with transcripts: the namespace rejects a root Pod, refuses a tag-only image, blocks a cross-namespace connection, and rejects an extra `LoadBalancer` Service.

**Exercise 5 — Evidence pack.** Enable an audit policy equal to the one above on a practice cluster (a `kind` configuration can mount the policy file). Perform an `exec`, a Secret read and a RoleBinding change. Show from the log that the exec and the Secret read were recorded at `Metadata` level with no body, and the binding change with the full request and response.

**Exercise 6 — Secrets rotation drill.** Using any available mechanism (an external store, or a simulated one with a script), rotate a database password and show how the Pod picks it up. Measure the time from rotation to the new value being in use, and write down what must happen if the old value is suspected leaked.

**Exercise 7 — Exceptions with expiry.** Create an exceptions file and a small job or script that removes an expired exception from the binding selector. Demonstrate that after the expiry date the previously allowed Pod is denied.

**Solution notes.**

*Exercise 1.* Stage 1 produces no client output; the evidence is the audit annotation (or engine report) naming the policy and message. Stage 2 prints a warning on `kubectl apply`. Stage 3 returns an `Invalid` error whose first line names the policy and binding. If nothing is recorded in stage 1, check that audit logging is on and that the binding's `namespaceSelector` really matches your namespace label.

*Exercise 2.* The Deployment-only policy refuses a tag-only Deployment but accepts a tag-only Pod, Job and CronJob. With the Pod-level policy, all of them are caught at Pod creation. Controllers surface the failure in ReplicaSet or Job events, not in the original `kubectl apply`, so teach people where to look.

*Exercise 3.* Expect every `allow/` fixture to be accepted and every `deny/` fixture to be refused with its expected fragment. When you loosen the prefix, the "unapproved registry" fixture should flip to an unexpected accept. That is the point: the suite detects policy regression.

*Exercise 4.* The root Pod is refused by Pod Security; the tag-only image by the admission policy; the cross-namespace connection times out only if your network plugin enforces policy; the extra LoadBalancer Service is refused with `exceeded quota`. If any transcript shows an accept, trace which layer of the baseline was not applied (labels are the usual culprit).

*Exercise 5.* Because Secrets match the `Metadata` rule before the generic write rule, the log shows user, verb, resource and time but no data. If you find Secret contents in the log, your rule order is wrong. The binding change appears at `RequestResponse`, including the subjects granted.

*Exercise 6.* The time depends on the refresh interval and on whether the application re-reads files (mounted Secrets update with a delay; environment variables need a restart). The honest answer for a leak is a number you measured, and the steps: rotate at the source, force refresh, restart consumers, review audit logs for use of the old credential.

*Exercise 7.* After the expiry the job removes the exemption; the previously accepted Pod is denied on its next create (existing Pods keep running, so also decide how the expiry handles them). Capture both the before and after transcripts.
