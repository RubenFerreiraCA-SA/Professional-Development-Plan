# T-PLT-03-E — Expert Depth

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-e"></a>
#### T-PLT-03-E — Expert Depth

## Why this level exists

Professional practice builds a platform guarantee: restricted namespaces, admission policy, default-deny networking, evidence. Expert practice asks where each guarantee *stops* holding, how the controls fail when the things they depend on fail, and what you do on the day an adversary is already inside. The skill is not knowing more settings; it is predicting how an accepted practice breaks (a policy engine outage during an incident, a permission that is transitively a cluster takeover, a tenant who shares your kernel) and choosing the cheapest control that addresses the failure that matters.

This section assumes the earlier levels. Examples use the neutral service `orders-api` in the namespaces `orders-prod` and `orders-staging`. Commands assume a practice cluster you may break; outputs labelled *illustrative* show a shape to expect, not measured results. Several procedures below (break-glass, quarantine, credential rotation) are *drills*: rehearse them before you need them, and never test them first on production.

## Threat modelling a cluster

A threat model is a short, written answer to four questions: what are we protecting, from whom, how could they reach it, and what stops them. For a cluster the answer is structured by **assets**, **adversaries** and **trust boundaries**.

**Assets.** Workloads and the data they handle; credentials (ServiceAccount tokens, kubeconfigs, cloud identities, Secrets); the control plane and its database; the supply chain (images, manifests, pipelines, operators); and the *audit trail* itself, which is an asset because attackers want to edit it.

**Adversaries.** External attackers exploiting an application bug; malicious insiders or tenants; compromised CI or GitOps pipelines; malicious or compromised dependencies and images; and the well-meaning engineer whose mistake has the same effect as an attack. Different adversaries start at different places: an external attacker starts inside one Pod, a malicious tenant starts with a namespace and a kubeconfig, a compromised pipeline starts with the reconciler identity.

**Trust boundaries.** The lines from the Beginner section (outside → app, Pod → Pod, Pod → API, Pod → node, tenant → tenant, person → cluster), plus the less obvious ones: *platform team → tenants* (who can change the policies), *cluster → cloud account* (what a node or Pod identity can do outside Kubernetes), and *CI → cluster* (what a pipeline can apply).

A typical chain, and the defence that breaks each link:

```text
 1. Remote code execution in a Pod
 2. Read the ServiceAccount token, mounted Secrets, or cloud metadata credentials
 3. Query the API server, or the cloud, with those credentials
 4. Escalate through over-broad RBAC or by creating a privileged Pod
 5. Reach the node (hostPath, host namespaces, kernel exploit)
 6. Reach other tenants' Pods, node credentials, the control plane
```

| Link | Defence | Evidence it works |
| --- | --- | --- |
| 1. Code execution | Input handling, patching, minimal images, non-root, read-only root filesystem, seccomp | Image scan, `securityContext` audit, failing write test |
| 2. Credential theft | `automountServiceAccountToken: false`, projected short-lived tokens, metadata egress blocked, secrets by file with least access | Token path absent, metadata timeout transcript |
| 3. Use of credentials | Least-privilege RBAC; credentials useless off-cluster (audience-bound tokens, network allow-lists) | `can-i --list` output for the Pod's identity |
| 4. Escalation | Escalation-aware review, admission policy, Pod Security | Denied privileged Pod; RBAC graph analysis |
| 5. Node access | Restricted Pod Security, no host namespaces, sandboxed runtime for risky workloads | Denied hostPath; runtime class in use |
| 6. Lateral movement | Default-deny NetworkPolicy, node pools per trust level, node authorisation restrictions | Cross-namespace timeout; taint and RuntimeClass enforcement |
| All links | Runtime detection, audit logging off-cluster, rehearsed response | Alerts that fire in drills; queryable logs |

**Method, in practice.**

1. Draw the data-flow diagram of the platform, not the application: API server, kubelets, controllers, registries, pipelines, secret stores, identity provider, cloud account.
2. Mark the trust boundaries and the identity used to cross each one.
3. For each crossing, ask the six STRIDE-style questions: can an attacker *spoof* the caller, *tamper* with the data, *repudiate* the action (is it audited?), *disclose* information, *deny* service, or *elevate* privilege?
4. Record each threat in a register: description, entry point, impact, existing control, evidence, residual risk, owner, review date.
5. Rank by impact and by how few steps an attacker needs, not by how interesting the attack is.
6. Re-run the exercise when the architecture changes (a new operator, a new tenant type, a new pipeline) and after every incident.

The register is not a deliverable to file away; it is the input to the policy backlog, the detection rules, and the drill schedule.

## Escalation analysis in depth

The permission to create Pods in a namespace is effectively access to every Secret and ServiceAccount there. Permission to create privileged Pods or mount `hostPath` is node-level access. Permission to modify admission webhooks or policies is control over all future objects. Permission to create tokens for powerful ServiceAccounts or to impersonate is delegation of those identities. Walk each role through "what is the worst thing this can do transitively" and use graph-based analysis tools in CI.

### How Kubernetes itself limits RBAC escalation

RBAC has two built-in guards worth understanding exactly, because they define what a delegated administrator can and cannot do:

- **Creating or updating a Role** requires that you already hold every permission in it, unless you hold the `escalate` verb on `roles` (or `clusterroles`).
- **Creating a binding** requires that you already hold the permissions in the referenced role, unless you hold the `bind` verb on that role.

```bash
# alice administers RBAC in orders-staging but holds no permission on persistentvolumes
kubectl --as alice -n orders-staging create role pv-admin --verb='*' --resource=persistentvolumes
# illustrative: Error from server (Forbidden): roles.rbac.authorization.k8s.io "pv-admin" is forbidden:
#   user "alice" is attempting to grant RBAC permissions not currently held:
#   {APIGroups:[""], Resources:["persistentvolumes"], Verbs:["*"]}
```

These guards stop *direct* escalation through RBAC objects. They do nothing about **indirect** escalation: using one capability to acquire another through a different mechanism. That is where review effort belongs.

### Indirect escalation primitives

| Capability | Indirect path | Why RBAC guards do not help |
| --- | --- | --- |
| `create` on Pods (or any Pod-creating workload) | Mount any Secret or ServiceAccount in the namespace; use `hostPath` or privileged mode if admission allows | It is not a grant of RBAC permissions; it is code running with another identity |
| `get`/`list` on Secrets, including ServiceAccount token Secrets | Use the stolen identity | Reading is not granting |
| `create` on `serviceaccounts/token` | Mint a token for any ServiceAccount you name | The token carries that account's permissions, not yours |
| `impersonate` | Act as any user or group you may impersonate, including `system:masters` if allowed | It is delegation, by design |
| `pods/exec`, `pods/ephemeralcontainers` | Run commands as a Pod's ServiceAccount, with its mounted Secrets | Identity theft, not permission grant |
| `get` on `nodes/proxy` | Reach kubelet endpoints (including command-execution paths on some versions) on a node | The subresource maps to powerful kubelet operations |
| `create`/`update` on admission webhook or policy objects | Change or disable the rules for all future objects | The object *is* the control |
| `patch` on Namespaces | Relabel to switch off Pod Security or move a namespace into a policy exemption | Labels are policy inputs |
| `approve` on `certificatesigningrequests/approval` for a signer, plus `sign` | Mint client certificates with any `CN` and `O`, including privileged groups | Credential minting |
| `create` on PersistentVolumes with `hostPath` or local paths | Read or write node filesystem through a claim | Storage is a side door to the node |
| Write access to a custom resource consumed by a powerful operator | The operator performs privileged actions on your behalf (the "confused deputy") | The operator's permissions, not yours, are used |
| Membership of `system:masters` | Bypasses authorisation entirely | The API server skips RBAC for this group |

The last row deserves emphasis: a client certificate whose organisation field is `system:masters` is authorised for everything, **cannot be revoked** short of rotating the signing CA, and appears in no RBAC object you can list. Treat it as a break-glass credential held offline, and alert on its use in the audit log.

### A worked analysis: the "harmless" deployer

A team asks for a Role to deploy `orders-api` in `orders-prod`:

```yaml
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "pods/log", "configmaps", "services"]
    verbs: ["get", "list", "watch", "create", "update"]
```

Walk it transitively:

1. It can create Deployments, so it can create Pods with any `serviceAccountName` in the namespace and mount any Secret there. **Impact:** read every Secret in `orders-prod` (including the database credential), act as any ServiceAccount in the namespace.
2. If `orders-prod` contains a ServiceAccount bound to a powerful Role (a reconciler, a backup job), that identity is now reachable.
3. Whether it can reach the *node* depends on admission: with `restricted` Pod Security enforced it cannot request `hostPath` or privileged mode; without it, it can.
4. It cannot create RoleBindings, so no direct escalation, and cannot reach other namespaces.

Conclusion: this Role is safe **only** if (a) Pod Security `restricted` is enforced in the namespace, (b) no powerful ServiceAccount lives in the namespace, and (c) policy limits which Secrets and ServiceAccounts a Pod may use. Each of the three is a control to verify, and the Role's review should reference them. "It only deploys things" is not an analysis.

A query to find who can create Pods through the common routes, as a starting point for review:

```bash
kubectl get roles,clusterroles -A -o json | jq -r '
  .items[]
  | select(any(.rules[]?;
      ((.resources // []) | any(. == "pods" or . == "deployments" or . == "statefulsets" or . == "daemonsets" or . == "jobs" or . == "cronjobs" or . == "replicasets" or . == "*"))
      and ((.verbs // []) | any(. == "create" or . == "*"))))
  | "\(.kind) \(.metadata.namespace // "-")/\(.metadata.name)"'
```

Then join the result with bindings to get subjects. For repeatable analysis use a graph tool that models roles, bindings, ServiceAccounts, Pods and Secrets as a graph and answers "can subject X reach Secret Y, or node-level access, in N hops?"; run it in CI against exported RBAC and fail the pipeline when a new path to `cluster-admin` equivalents appears. The tool matters less than the discipline: escalation paths are properties of the whole graph, not of one Role.

## Admission control in depth

### Anatomy of a webhook, and what each field costs

A policy engine that uses admission webhooks makes the API server call an HTTPS service synchronously for each matching request. The configuration contains the security properties:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata: { name: policy-engine }
webhooks:
  - name: validate.policy.example.com
    admissionReviewVersions: ["v1"]
    sideEffects: None
    failurePolicy: Fail                  # fail closed: if the engine is unreachable, refuse
    timeoutSeconds: 3                    # latency budget the API server will wait
    matchPolicy: Equivalent              # also match equivalent API versions of the resource
    namespaceSelector:
      matchExpressions:
        - { key: kubernetes.io/metadata.name, operator: NotIn, values: ["kube-system", "policy-system"] }
    rules:
      - { apiGroups: [""], apiVersions: ["v1"], operations: ["CREATE", "UPDATE"], resources: ["pods"] }
    clientConfig:
      service: { name: policy-engine, namespace: policy-system, path: /validate }
      caBundle: <base64 CA certificate>
```

Fields that matter:

- `failurePolicy` decides what the API server does when the webhook errors or times out: `Fail` refuses the request, `Ignore` admits it.
- `timeoutSeconds` bounds added latency per request. Every matching create or update waits on the webhook, so a slow engine slows the whole API.
- `namespaceSelector` and `objectSelector` define scope. They are also how you *exclude* the engine's own namespace and critical system namespaces.
- `matchPolicy: Equivalent` prevents a bypass by sending the same resource through a different API version.
- Webhook configuration objects themselves are **not** sent to webhooks, which is what lets you repair a broken configuration even when the engine is down. That is the foundation of break-glass.
- Mutating webhooks run before validating ones, may be **re-invoked** if a later mutation changes the object (`reinvocationPolicy`), and must be idempotent. A validating policy sees the final, mutated object.

### Fail-open versus fail-closed

`failurePolicy: Fail` fails **closed**: during an engine outage, matching requests are refused, including your own repairs and controller activity. `Ignore` fails **open**: during an outage the rules silently stop applying, and an attacker (or an accident) can act freely while nobody is warned. Neither is "safe"; each trades one failure for another.

| Control | Fail closed means | Fail open means | Typical choice |
| --- | --- | --- | --- |
| Pod Security Admission (built in) | N/A: in-process, no external dependency | N/A | Always enforced |
| CEL `ValidatingAdmissionPolicy` | Errors in expression refuse requests | Errors skip the rule | `Fail`, with tested policies |
| Webhook: privileged Pods, host access | Outage blocks all Pod creation in scope | Outage permits dangerous Pods | Fail closed, HA, narrow scope, exclusions |
| Webhook: labels or hygiene rules | Outage blocks deployments | Outage permits unlabelled objects | Fail open, with alerting, plus a catch-up audit |
| Webhook: image signature verification | Outage blocks new rollouts | Outage permits unsigned images | Closed for production; open with alert for non-production |
| Network plugin enforcement | Policy agent down: depends on plugin (some drop, some allow) | Same | Know your plugin's failure mode; test it |
| Audit log shipping | Stop on failure (rarely) | Buffer then drop | Buffer, alert on gaps |

A mature design splits rules into **tiers** by consequence. Tier 1 rules (stop privileged and host-access Pods) are enforced by in-process mechanisms (Pod Security Admission, CEL policies), which have no availability dependency, so they can fail closed safely. Tier 2 rules (richer checks needing an external engine) fail closed only for narrow scopes and with a rehearsed break-glass; wider hygiene rules fail open with monitoring and a retrospective sweep (scan existing objects for violations afterwards).

### Engine outage: designing so it is survivable

Failure scenarios, and the design response:

| Scenario | Mechanism | Design response |
| --- | --- | --- |
| Engine Pods crash or are evicted | `Fail` webhook with no endpoints refuses Pod creation, including the engine's own replacement Pods | Exclude the engine's namespace; run replicas across zones; PodDisruptionBudget; high priority class |
| Deadlock at bootstrap | Webhook registered before the engine is running | Register webhooks last in the install order; use selectors that exclude the engine until healthy |
| Certificate expires | API server cannot verify the engine's TLS | Automate rotation; alert on expiry well in advance; test the rotation |
| Engine is slow, not down | Timeouts consume the API request budget | Latency SLO and alerts; keep `timeoutSeconds` low; shrink the matched scope |
| Bad policy deployed | A rule wrongly denies system components | Staged rollout, `Audit`/`Warn` first, canary namespaces, policy tests |
| Node pressure evicts engine | Resources starved | Requests/limits sized with headroom; dedicated or protected nodes |

Metrics to watch from the API server (names as exposed by recent versions; confirm on yours):

```text
apiserver_admission_webhook_admission_duration_seconds   # latency per webhook
apiserver_admission_webhook_rejection_count              # rejections, labelled by webhook and reason
apiserver_admission_webhook_fail_open_count              # how often an Ignore webhook failed and the request was admitted
apiserver_admission_webhook_request_total                # volume
```

A non-zero `fail_open_count` is the signal that your "fail-open" webhook is silently unprotecting the cluster. Alert on it.

### Break-glass: rehearsed, narrow, logged

When the engine is down and the failure policy blocks recovery, an authorised person needs a way to restore function without disabling security permanently. The procedure, in order:

1. Declare the incident and name the person authorised to use break-glass credentials (two-person rule where possible).
2. Use a separately held, audited identity with narrow permission to edit webhook configurations (not `cluster-admin`).
3. Prefer the smallest change: patch the **failure policy** or **namespace selector** of the affected webhook rather than deleting it.
4. Record the exact time and command.
5. Restore the engine, then **revert** the change, then verify with a denied test request.
6. Review the audit log for everything admitted during the window; schedule a sweep for violations that slipped through.

```bash
# Illustrative. Make the failing webhook fail open for the duration of the recovery.
kubectl patch validatingwebhookconfiguration policy-engine --type=json \
  -p='[{"op":"replace","path":"/webhooks/0/failurePolicy","value":"Ignore"}]'
# ... recover the engine ...
kubectl patch validatingwebhookconfiguration policy-engine --type=json \
  -p='[{"op":"replace","path":"/webhooks/0/failurePolicy","value":"Fail"}]'
kubectl apply --dry-run=server -f policy-tests/deny/pod-privileged.yaml   # must be refused again
```

Drill this quarterly: scale the engine to zero in a practice cluster and time how long recovery takes with the procedure as written. Documents untested under pressure are fiction.

### Policy engineering at scale

Policies are code: version them, test them, review them, roll them out progressively. Consider performance and availability of webhook-based admission: a failing webhook with `failurePolicy: Fail` can block all changes (including recovery), whereas `Ignore` silently disables enforcement. Exclude the policy engine's own namespace and critical system namespaces carefully, keep break-glass procedures, monitor webhook latency and errors, and prefer in-process mechanisms (CEL policies) for simple rules to reduce failure modes.

More principles that separate a maintainable policy estate from a fragile one:

- **One concern per policy**, named for the concern, with an owner. Staging, exceptions and messages are then per rule.
- **Policy interactions are untested by default.** A mutating policy that sets a field can make a validating rule pass or fail; test the whole chain, not each policy alone.
- **Cost of CEL.** The API server limits expression cost; deep iteration over large lists in a rule can be rejected or slow. Prefer simple predicates and test with maximum-size objects.
- **Version skew.** Policies written for one API version can miss requests sent through another; use `matchPolicy: Equivalent` and test with each served version.
- **Policy as an attack surface.** Whoever can edit policy controls the cluster. Restrict write access to policy namespaces and objects, require review, and audit changes at `RequestResponse` level.
- **Report what policy cannot see.** Admission checks objects when they are created or updated. Existing objects and cluster state drift, so a periodic background scan is part of the design.

## Runtime security

Admission is static; attackers act at runtime. Complement with runtime detection (syscall and network anomaly detection through eBPF-based tools), read-only filesystems, minimal images, seccomp and AppArmor or SELinux profiles, and alerting on suspicious behaviours (shell in a container, unexpected outbound connections, credential file reads). Define response playbooks: isolate the Pod with a network policy, capture evidence, rotate exposed credentials, replace the workload.

### Detection engineering

A runtime sensor (an eBPF- or kernel-module-based agent running on each node) observes system calls, process starts, file access and network connections and matches them against rules. The tools differ; the engineering problems are the same:

| Signal | Why it matters | False-positive risk |
| --- | --- | --- |
| Shell spawned in a production container | Interactive access, often post-exploitation | Legitimate debugging; mitigate with a tagged break-glass debug path |
| Read of the ServiceAccount token path by a process that is not the application | Credential theft | Sidecars that legitimately use the API |
| Unexpected outbound connection (destination not in the service's profile) | Command and control, data exfiltration | New dependencies after releases |
| Write to a binary directory, or a new executable appearing | Persistence | Package managers in poorly built images |
| `ptrace`, `mount` or namespace changes from a container | Breakout attempts | Debuggers, some init processes |
| Access to the cloud metadata address | Credential theft from the node identity | Platform components |

An illustrative rule in the syntax of a popular open-source engine, scoped to the production namespace and written to be reviewable:

```yaml
- rule: Shell started in orders-prod container
  desc: A shell was started inside a container in the orders-prod namespace
  condition: >
    spawned_process and container and k8s.ns.name = "orders-prod"
    and proc.name in (sh, bash, ash, dash)
  output: >
    Shell in container (ns=%k8s.ns.name pod=%k8s.pod.name container=%container.name
    user=%user.name cmd=%proc.cmdline)
  priority: WARNING
  tags: [orders, runtime]
```

Detection is a product with a lifecycle, not an installation:

1. **Baseline first.** Run in alert-only mode and learn what normal looks like; tune out legitimate patterns *with justification*, not by deleting the rule.
2. **Route by severity.** Credential-theft signals page someone; hygiene signals create tickets. A sensor that pages for everything is soon muted.
3. **Test the detection.** In a practice cluster, perform the behaviour (start a shell, read the token) and confirm the alert fires, reaches the destination and is understandable. A rule never seen firing is unproven.
4. **Respect the cost.** Sensors consume CPU and memory on every node, add kernel-level risk, and produce data you must store and protect (logs of commands can contain secrets). Budget these, and protect the sensor itself: it is a privileged component and a high-value target.
5. **Know what it cannot see.** Memory-only attacks, kernel exploits that disable the sensor, and encrypted outbound channels to allowed destinations can all pass. Detection reduces dwell time; it is not prevention.

## Isolation strength and multitenancy

Containers share a kernel; for untrusted workloads consider sandboxed runtimes (user-space kernels or micro-VMs), dedicated node pools with taints, and separate clusters. Weigh performance overhead, compatibility and operational cost against risk.

The spectrum, from weakest to strongest isolation:

| Level | What is shared | Appropriate for | Main costs |
| --- | --- | --- | --- |
| Namespace per tenant (with quota, policies) | Control plane, nodes, kernel, cluster-scoped objects | Trusted teams of one organisation ("soft" multitenancy) | Cheapest; weakest |
| Dedicated node pool per tenant (taints, selectors, enforced by policy) | Control plane | Teams with different sensitivity, noisy workloads | Idle capacity; policy to *force* use of the pool |
| Sandboxed runtime (RuntimeClass) | Control plane; nodes but not the host kernel directly | Running third-party or untrusted code | Overhead, compatibility limits, operational skill |
| Virtual cluster per tenant | Nodes (and kernel) but not the API server | Tenants who need their own CRDs, admission, cluster-scoped objects | Another control plane to run and secure |
| Separate cluster per tenant (or per trust level) | Only the cloud account (or less) | Untrusted tenants, regulated data | Highest cost; management at scale |

Sandboxed runtimes are selected per Pod through a `RuntimeClass`; policy must then ensure that sensitive tenants *cannot opt out*:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata: { name: sandboxed }
handler: runsc                           # must match a handler configured on the nodes' container runtime
scheduling:
  nodeSelector: { sandbox.example.com/enabled: "true" }
```

```yaml
# Pod fragment for an untrusted workload
spec:
  runtimeClassName: sandboxed
```

Dedicated nodes only isolate if the scheduler *and* the tenant cooperate: taints keep other tenants off, but nothing forces a tenant onto its pool unless a policy (or mutation) sets the selector and toleration. Enforce both directions with admission policy, then test by trying to schedule outside the pool.

What namespaces **cannot** isolate even with perfect baselines:

- **The kernel.** A kernel vulnerability reachable from a container is reachable from every tenant on the node.
- **The control plane.** One tenant's heavy list-and-watch pattern consumes API server capacity; API Priority and Fairness mitigates but does not make this free. Etcd storage is shared, so object-count quotas matter (`count/...` quotas).
- **Cluster-scoped resources.** CRDs, ClusterRoles, admission webhooks, StorageClasses and Nodes are global; a tenant who can create one affects everyone.
- **Shared services.** Cluster DNS, ingress controllers, service-mesh control planes, logging and monitoring agents. A noisy or malicious tenant can degrade or observe through them.
- **Side channels.** CPU caches, shared storage throughput and network bandwidth leak timing and contention.
- **Metadata about others.** Tenants can often list namespace names, Node details and API discovery information.

The honest decision statement is a pair: *which tenants we treat as adversarial*, and *which controls make that safe*. "Hard multitenancy on a shared cluster" is a claim that requires every row of the table above to be addressed in writing; most organisations are better served by trusted-tenant namespaces for internal teams and separate clusters for genuinely untrusted workloads.

## Identity and zero trust

Workload identity (short-lived, attested identities per Pod), mutual TLS between services, authorisation policies at the mesh or application layer, and no long-lived static credentials. A service mesh adds these capabilities and costs: complexity, resource overhead, new failure modes and upgrade burden. Adopt when requirements justify it.

The expert view of "zero trust" in a cluster is concrete:

- **Identity per workload, not per network location.** An IP address is not an identity; Pods come and go. Use attested identities (projected ServiceAccount tokens with a specific audience; certificate identities issued per workload).
- **Authenticate both ends.** Mutual TLS proves *which workload* is calling, and authorisation rules (at the mesh or in the application) decide whether that workload may call *this* endpoint. NetworkPolicy alone only says which *addresses* may connect.
- **Federate to the cloud, do not store keys.** Pods exchange their projected, audience-bound token for short-lived cloud credentials through the cloud's workload identity federation, so there is no cloud access key to leak.
- **Make credentials useless when stolen.** Short expiry, narrow audience, binding to the Pod object (so deleting the Pod invalidates its token), network allow-lists for the destination.
- **Count the cost.** A mesh adds sidecars or per-node proxies (CPU, memory, latency), a new control plane that must be upgraded and secured, and new failure modes (certificate expiry, proxy bugs, misconfigured authorisation policy refusing legitimate traffic). Adopt it for the properties you need, not for fashion; plain mutual TLS in the application library or a lighter mechanism may be enough.

Every extra identity layer is also a fail-open or fail-closed decision. If the identity issuer is down, do workloads keep running with cached certificates (open for a while) or stop talking (closed)? Decide, document and test.

## Incident response for a compromised workload

The plan must exist before the incident. The objectives, in order: **stop the harm, preserve evidence, remove the adversary's access, restore service, learn.** A frequent error is to delete the suspicious Pod immediately, which feels decisive and destroys the evidence while leaving the adversary's stolen credentials valid.

### Phase 1: Detect and triage (minutes)

Inputs: a runtime alert, an audit-log anomaly, a cloud-provider alert, a vulnerability report, or an external notification. First questions: which workload, which namespace, which identity, since when, and what can that identity do? The last question is answerable immediately from the RBAC analysis you did in advance:

```bash
kubectl auth can-i --list -n orders-prod --as system:serviceaccount:orders-prod:orders-api
kubectl get pod orders-api-7d9f5 -n orders-prod -o jsonpath='{.spec.serviceAccountName}{"\n"}{.spec.nodeName}{"\n"}'
```

### Phase 2: Contain (without destroying evidence)

Containment goals: cut the Pod off from the network and from being scheduled new work, while keeping it alive for inspection.

**Quarantine by relabelling.** NetworkPolicies are *additive*, so adding a "deny" policy cannot override an existing allow policy that already selects the Pod. The reliable technique is to change the Pod's labels so that **no allow policy selects it**, and a quarantine policy does:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: quarantine, namespace: orders-prod }
spec:
  podSelector: { matchLabels: { quarantine: "true" } }
  policyTypes: [Ingress, Egress]          # no rules: nothing in, nothing out
```

```bash
kubectl label pod orders-api-7d9f5 -n orders-prod app- quarantine=true
# Removing the `app` label disowns the Pod from its ReplicaSet (a replacement starts) and from Services,
# and stops the allow-api policy from selecting it. The quarantine policy now applies.
```

Caveats to verify in a drill:

- With a namespace-wide `default-deny`, the relabelled Pod falls back to default-deny plus the quarantine policy, which is what you want. Without one, quarantine still works, but only because the quarantine policy selects the Pod.
- Whether **already-established connections** are cut depends on the network plugin; some apply policy only to new flows. If the attacker holds an open connection, plan to end it (capture evidence, then remove the Pod or its network namespace).
- The relabelled Pod is **still running with its credentials mounted**. Network isolation stops it talking out; it does not invalidate its token.

Other containment actions, chosen by what was compromised:

| Compromise | Action |
| --- | --- |
| One Pod, low privilege | Quarantine; revoke its ServiceAccount's permissions if it had any |
| A ServiceAccount token | Remove the ServiceAccount's bindings; delete the Pod (bound tokens die with it); for `create token` tokens, they live until expiry, so keep durations short and rotate if the account is deleted and recreated |
| A node | `kubectl cordon <node>` to stop scheduling; cut node credentials; treat every Pod and node-held secret on it as exposed |
| A powerful operator or controller | Scale it down, remove its bindings; review everything it created |
| A pipeline identity | Disable the pipeline; rotate its credentials; review applied manifests in audit logs |
| A tenant | Quarantine the namespace with a deny-all policy and suspend its identities; review other tenants' exposure |

### Phase 3: Preserve evidence

Order of volatility: memory and process state first, then network state, then disk, then logs, then configuration.

```bash
# Metadata and configuration
kubectl get pod orders-api-7d9f5 -n orders-prod -o yaml > evidence/pod.yaml
kubectl describe pod orders-api-7d9f5 -n orders-prod > evidence/describe.txt
kubectl logs orders-api-7d9f5 -n orders-prod --all-containers --timestamps > evidence/logs.txt
kubectl logs orders-api-7d9f5 -n orders-prod --all-containers --previous --timestamps > evidence/logs-previous.txt 2>/dev/null

# Live inspection, without altering the original container, using an ephemeral debug container
kubectl debug -n orders-prod orders-api-7d9f5 -it --image=registry.example.com/platform/forensics@sha256:<digest> --target=app

# Who did what: audit events for the identity in the window (query your log store)
#   user.username == "system:serviceaccount:orders-prod:orders-api"
```

Practical notes:

- **Ephemeral containers need RBAC** (`pods/ephemeralcontainers`) and must pass admission policy; decide in advance which identities may do this and where the forensic image is hosted.
- **Record hashes** of the evidence files and who handled them, and store them where cluster administrators cannot alter them quietly.
- **Cloud-side evidence** matters: cloud audit logs for credentials that the Pod could reach, node snapshots for disk forensics, load-balancer logs for network history.
- **Do not log into the node casually**; node access is itself an escalation, and in a real investigation every action should be recorded and approved.

### Phase 4: Eradicate and recover

1. **Rotate everything the workload could reach**, ordered by blast radius: cloud credentials and API keys; database and queue credentials; Secrets mounted in the namespace (remember the "create Pods reads Secrets" equivalence: if the attacker could create Pods, assume *all* Secrets in the namespace are compromised); then tokens and certificates.
2. **Replace, do not repair.** Rebuild the workload from a known-good digest through the normal pipeline. Never "clean" a compromised container.
3. **Close the entry point.** Patch the vulnerability, tighten the policy that would have prevented the escalation, and add the detection that would have caught it sooner.
4. **Verify.** Run the negative tests for the control that failed; confirm the old credentials no longer work; confirm no unexpected objects remain (new Roles, bindings, ServiceAccounts, CronJobs, webhook configurations) by diffing against the Git source of truth.

```bash
# Look for persistence the attacker may have created: anything not in Git
kubectl get cronjobs,jobs,daemonsets,deployments -n orders-prod --sort-by=.metadata.creationTimestamp
kubectl get rolebindings,clusterrolebindings -A --sort-by=.metadata.creationTimestamp | tail -n 20
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
```

### Phase 5: Learn

A blameless post-incident review answers: how did the attacker get in, what let them go further, how did we detect (or not detect), how long was the dwell time, what controls worked, what did we *believe* worked that did not. Output: changes to policy, detection rules, runbooks and the threat register, each with an owner and a date. Re-run the drill that matches the incident within a quarter.

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Policy engine outage blocks recovery | `failurePolicy: Fail` with a down webhook | HA deployment, exclusions, break-glass, simple CEL policies |
| Silent policy bypass | `Ignore` webhook failing open; no alert on `fail_open_count` | Alert on fail-open metric, background sweep |
| Over-permissive operator | Operator granted cluster-admin | Review operator RBAC, namespace scope, vendor assessment |
| Secrets in etcd backups | Backups unencrypted | Encrypt, restrict, test restore |
| Stale exceptions | Exceptions never expire | Expiry and quarterly review |
| Token theft | Long-lived tokens, automount default | Bounded tokens, automount off, metadata blocking |
| Escape via privileged tooling | CI or debug Pods run privileged | Separate debug procedures, ephemeral containers with RBAC and policy |
| Label-based bypass | Tenant can edit namespace labels and disable Pod Security or policy selection | Restrict namespace patching; policy on label changes |
| Parameter deletion | Policy parameter object removed | `parameterNotFoundAction: Deny`; protect policy namespaces |
| `system:masters` credential leaked | Hard-coded superuser group, no revocation | Offline break-glass only; alert on use; rotate CA if exposed |
| Quarantine ineffective | Additive policies still select the Pod; established flows survive | Relabel to drop selection; drill the plugin's behaviour |
| Admission-only security | No runtime detection, drift undiscovered | Detection plus periodic background scans |
| Shared-kernel escape | Kernel vulnerability reachable from a container | Sandboxed runtimes, node-pool isolation, rapid node patching |
| Audit log tampering | Logs only on the control plane | Ship off-cluster to protected storage |

## Expert trade-offs

| Decision | Choose the strong option when | Choose the cheaper option when |
| --- | --- | --- |
| Separate clusters per tenant | Tenants are untrusted or regulated | Tenants are internal teams with shared incentives |
| Sandboxed runtime | Running third-party code, or high-value data | Workloads are your own, hardened and scanned |
| Webhook engine for signature verification | Supply-chain risk is a primary threat | Digest pinning plus an approved registry already addresses the risk |
| Fail closed everywhere | Consequences of an unsafe object outweigh outage cost | Availability matters more and detection compensates |
| Service mesh with mutual TLS | You need workload identity across many services and teams | A few services can use library-level TLS |
| Heavy runtime detection | Handling sensitive data, or a mature response capability exists | Nobody can triage alerts; start with audit-log detection |

## Knowledge consolidation

- A **threat model** is assets, adversaries and trust boundaries turned into a *register* with controls, evidence and owners; rank by attacker effort and impact.
- **RBAC guards stop direct escalation, not indirect**: creating Pods, minting tokens, impersonating, exec, `nodes/proxy`, editing policy objects, relabelling namespaces, and operator confused deputies all escalate around them.
- **`system:masters` bypasses RBAC** and cannot be revoked short of rotating the CA.
- **Fail-open versus fail-closed** is a per-rule decision tied to consequence; put critical rules in in-process mechanisms, and alert on webhook fail-open counts.
- **Engine outages** need exclusions, HA, certificate automation, latency budgets and a **rehearsed break-glass** that is narrow, logged and reverted.
- **Runtime detection** is a lifecycle (baseline, route, test, budget), and it reduces dwell time rather than preventing attacks.
- **Multitenancy** is a spectrum; namespaces share kernel, control plane, cluster-scoped objects and shared services. State which tenants you treat as adversarial.
- **Zero trust** means per-workload identity, mutual authentication, short-lived credentials and federation, with explicit failure behaviour.
- **Incident response**: contain without destroying evidence; quarantine by *relabelling* because policies are additive; rotate by blast radius; replace, do not repair; verify against Git.

## Exercises

**Exercise 1 — Threat register.** Draw the data-flow diagram of a small cluster you know, mark the trust boundaries, and write ten register entries (adversary, entry point, impact, control, evidence, residual risk, owner). Mark the three entries with the weakest evidence and propose the test that would produce it.

**Exercise 2 — Transitive Role review.** Take the "harmless deployer" Role and, on a practice cluster, demonstrate each transitive consequence: read a Secret via a Pod, act as another ServiceAccount, and (in a namespace *without* Pod Security) mount `hostPath`. Then add the three compensating controls and show each attempt failing.

**Exercise 3 — RBAC guards.** Give `alice` the ability to manage Roles and RoleBindings in one namespace without `escalate` or `bind`. Show she cannot create a Role with permissions she lacks, and cannot bind `cluster-admin`. Then grant `bind` on a single ClusterRole and show exactly what changes.

**Exercise 4 — Break the engine on purpose.** Install a webhook-based policy with `failurePolicy: Fail` and no exclusions, scale the engine to zero, and try to recover. Record what blocks you, then apply the exclusions, HA, PDB and the break-glass procedure. Repeat and time the recovery.

**Exercise 5 — Fail-open evidence.** Switch the same webhook to `Ignore`, scale the engine to zero, and show that a privileged Pod is admitted. Find the signal in metrics or audit that reveals it. Write the alert rule you would deploy.

**Exercise 6 — Detect and prove.** Deploy a runtime detection rule for a shell in a container and one for reading the ServiceAccount token path. Perform both actions, confirm the alerts fire, and note one legitimate behaviour that would cause a false positive and how you would handle it.

**Exercise 7 — Isolation choice.** Given two tenants, one a partner running arbitrary customer code and one an internal team, write the isolation design for each (which row of the spectrum, which controls), and name two attacks the design does *not* address.

**Exercise 8 — Tabletop incident.** Run a one-hour tabletop for the scenario "alert: shell in `orders-prod` and outbound connection to an unknown address". Use the phases above. At each step record the decision, the command you would run, and the evidence you would capture. Then run the quarantine step on a practice cluster and show whether established connections survive on your network plugin.

**Solution notes.**

*Exercise 1.* Good registers have entries that name a *specific* path ("token mounted in `orders-api` Pods can list Secrets in `orders-prod`") rather than a category ("credential theft"). Weakest-evidence entries usually involve controls that were configured but never negative-tested (network enforcement, metadata blocking, alert delivery). The deliverable is the register with tests, not a perfect diagram.

*Exercise 2.* Expected: the Pod prints a Secret value; a Pod using a more privileged ServiceAccount in the same namespace can call the API as that account; `hostPath` is accepted only where Pod Security is absent or `privileged`. After adding `restricted` enforcement, a policy limiting which Secrets and ServiceAccounts Pods may reference, and removing powerful ServiceAccounts from the namespace, each attempt fails with a message from a *different* layer (Pod Security, policy, RBAC). Record which.

*Exercise 3.* The attempt to create a role with unheld permissions fails with "attempting to grant RBAC permissions not currently held"; binding a role you do not hold fails similarly. With `bind` on one named ClusterRole she can bind exactly that role and nothing else. If she can do more, look for a second binding granting `escalate` or a wildcard on `roles`.

*Exercise 4.* Typical blockers: the engine's own Pods cannot be recreated because the webhook refuses Pod creation and the engine is down; and the webhook cannot be removed by a tenant-level identity. The fixes are namespace exclusion for the engine, replicas with a PDB, and an authorised identity that can patch the webhook configuration (which is exempt from webhooks). Timings are yours to measure; the second run should be markedly shorter.

*Exercise 5.* The privileged Pod is admitted while the engine is down. The evidence is a non-zero fail-open count for the webhook and, where logged, audit events showing the creation with no policy annotation. A reasonable alert fires when the fail-open counter increases at all, for a webhook in a protected scope, and pages for tier-1 rules.

*Exercise 6.* Both alerts should fire within seconds of the action; if the token-read alert does not, your rule is probably matching the wrong process or path. Legitimate shells usually come from debugging: route them through a tagged break-glass path that suppresses the alert but records who and why.

*Exercise 7.* A reasonable design: the partner gets a separate cluster (or at minimum a virtual cluster on dedicated, sandboxed nodes), restricted egress and no shared services; the internal team gets a namespace on the shared cluster with the Professional baseline. Attacks not addressed typically include side channels on shared hardware, supply-chain compromise of images the tenant brings, and compromise of the cloud account that hosts both. Naming them is part of the answer.

*Exercise 8.* Expect to discover gaps: nobody knows who may use break-glass, the forensic image is not mirrored internally, the audit log query for the ServiceAccount takes too long, or established connections survive the policy on your plugin. Each gap becomes a backlog item with an owner. If established connections survive, record the extra step (capturing evidence then removing the Pod) in the runbook.

## Mentoring prompts

Why is "can create Pods" nearly equivalent to "can read all Secrets in the namespace", and which three controls reduce the equivalence? How would you roll out a new mandatory policy to a hundred teams without causing an incident, and what would make you stop the rollout? What are the trade-offs of fail-open versus fail-closed admission, and how do you mitigate each? If your policy engine were unavailable for an hour during a security incident, which of your controls would still hold and which would not? Which tenants in your organisation do you treat as adversarial, and does your isolation design match that answer? What evidence would convince you that your runtime detection works, and when did you last collect it? If a `system:masters` certificate leaked tomorrow, what is your plan?

---
