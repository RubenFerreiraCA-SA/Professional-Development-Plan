# T-PLT-03-I — Intermediate Practice

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-i"></a>
#### T-PLT-03-I — Intermediate Practice

## Why this matters

The Beginner section gave you the three gates (authentication, authorisation, admission) and a first Role. Real clusters fail in the *gaps between* controls: a Role that is narrow in one place and broad in another, a namespace with no quota, a NetworkPolicy object that nothing enforces, a Pod Security label applied to the wrong namespace. None of these produces an error. They produce a cluster that *looks* secure and is not.

This section turns the vocabulary into working configuration and, more importantly, into **evidence**. For each control you will build it, break it deliberately, and keep the output that shows it working. It assumes you can use `kubectl`, read YAML and have a **practice cluster** (a local `kind` or `minikube` cluster with a network plugin that enforces NetworkPolicy, discussed below). Do not run these exercises on shared or production clusters. Outputs labelled *illustrative* show the shape to expect; reproduce them yourself before relying on them.

All examples use the neutral service `orders-api`, the namespace `orders-staging` and the user `alice`.

## A real unprivileged identity

Testing with `--as alice` is useful, but it is still *you* asking the API server to pretend. To experience a restricted identity, create an actual credential and use it from a separate kubeconfig context. On a practice cluster, a client certificate is the quickest way to do that:

```bash
openssl genrsa -out alice.key 2048
openssl req -new -key alice.key -subj "/CN=alice" -out alice.csr
# create a CertificateSigningRequest object containing alice.csr, approve it, fetch the cert
kubectl config set-credentials alice --client-certificate=alice.crt --client-key=alice.key
kubectl config set-context alice-staging --cluster=lab --user=alice --namespace=orders-staging
```

The comment hides the middle step; spelled out, the CSR object looks like this:

```yaml
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata: { name: alice }
spec:
  request: "<paste the output of: base64 -w0 < alice.csr>"
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400        # one day; the signer may enforce a minimum
  usages: ["client auth"]
```

```bash
kubectl apply -f alice-csr.yaml
kubectl get csr alice                                # CONDITION: Pending
kubectl certificate approve alice                    # an administrator action
kubectl get csr alice -o jsonpath='{.status.certificate}' | base64 --decode > alice.crt
openssl x509 -in alice.crt -noout -subject -enddate  # subject=CN = alice, and when it expires
kubectl --context alice-staging auth whoami
kubectl --context alice-staging get pods             # allowed after the RoleBinding exists
kubectl --context alice-staging get secrets          # Forbidden
```

Three lessons: the certificate's `CN` becomes the user name (and `O` fields become groups), so whoever can approve CSRs can mint any identity; deleting the CSR does **not** revoke an issued certificate (only expiry or rotating the CA does, so prefer short-lived tokens from an identity provider); and a kubeconfig is a credential to store like a password. Delete the context, user entry and key files when the exercise is over.

## Roles and bindings, designed on purpose

### Writing rules with intent

A Role is a list of rules, and each rule is a triple: API groups, resources, verbs. Optional `resourceNames` narrows a rule to specific named objects.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: orders-deployer, namespace: orders-staging }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]     # no delete
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "configmaps", "events"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["orders-api-config"]
    verbs: ["update", "patch"]
```

Notes on what this does and does not do:

- The first rule lets the holder roll out and amend Deployments, but not remove them.
- The third rule uses `resourceNames`: updates are limited to one named ConfigMap. (`resourceNames` cannot restrict `create` or `list`, because the name is not known at the time of the request.)
- The Role says nothing about Secrets, `pods/exec`, Roles or other namespaces. In an additive system, *silence is denial*.

### Bind to groups, not people

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: orders-team-deployer, namespace: orders-staging }
subjects:
  - { kind: Group, name: orders-developers, apiGroup: rbac.authorization.k8s.io }
roleRef: { kind: Role, name: orders-deployer, apiGroup: rbac.authorization.k8s.io }
```

Binding to a group means joining or leaving the team happens in the identity provider and takes effect without editing cluster objects. The trade-off: the *meaning* of the group now lives outside the cluster, so group membership must be reviewed as part of access reviews.

### Reuse ClusterRoles through RoleBindings

A **ClusterRole** is a reusable rule set. Binding it with a **RoleBinding** confines it to one namespace. This is the standard way to share definitions without handing out cluster-wide power:

```bash
kubectl create rolebinding alice-view --clusterrole=view --user=alice -n orders-staging
kubectl get clusterrole view -o yaml | head -n 30           # read what you are granting
```

Built-in user-facing ClusterRoles are `view` (read most namespaced objects, **not** Secrets), `edit` (read and write most namespaced objects, **including Secrets and the ability to create Pods**) and `admin` (edit plus managing Roles and RoleBindings within the namespace). Note the weight carried by `edit`: it is effectively "can read every Secret in this namespace". Hand it out knowingly.

These roles are *aggregated*: other ClusterRoles carrying a label such as `rbac.authorization.k8s.io/aggregate-to-view: "true"` are merged into them automatically. Installing a CRD-based tool that adds such a label silently changes what `view` means. Re-run `kubectl get clusterrole view -o yaml` after installing operators.

### Seeing effective permissions

```bash
kubectl auth can-i --list -n orders-staging --as alice          # everything alice may do here
kubectl auth can-i create pods/exec -n orders-staging --as alice
kubectl get rolebindings,clusterrolebindings -A -o wide | grep -E 'alice|orders-developers'
```

`can-i --list` answers "what can this identity do?". The harder question, "*who* can read Secrets in this namespace?", needs reading bindings or a helper tool (plugins such as `kubectl-who-can` or `rbac-tool` exist for this; evaluate any tool before running it against a real cluster). The JSON queries below do the job with only `kubectl` and `jq`.

## Escalation traps — audit for these

| Permission | Why it is dangerous |
| --- | --- |
| `get`, `list`, `watch` on Secrets | Reads credentials (`list` returns values) |
| `create` on Pods or Deployments in a namespace | Can mount any Secret or ServiceAccount in that namespace |
| `pods/exec`, `pods/attach` | Interactive access inside workloads |
| Write on Roles and RoleBindings | Grant more access (blocked unless you hold the verbs, except via `escalate` and `bind`) |
| `escalate`, `bind`, `impersonate` verbs | Explicit escalation primitives |
| Approving CertificateSigningRequests | Mint credentials |
| Wildcards in resources or verbs | Silently include future resources |
| `create` on `serviceaccounts/token` | Request tokens for other identities |
| Binding to `system:authenticated` or `system:unauthenticated` | Grants rights to everyone |

```bash
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | .metadata.name, (.subjects|tostring)'
kubectl get roles,clusterroles -A -o json | jq -r '.items[] | select(.rules[]?.verbs[]?=="*") | .metadata.name'
```

Built-in roles may contain wildcards; yours should not. `cluster-admin` should be bound only to system groups you can explain.

Two more audit queries that earn their keep:

```bash
# Every binding (any scope) that grants to everyone or to anonymous callers
kubectl get rolebindings,clusterrolebindings -A -o json | jq -r '
  .items[] | select(any(.subjects[]?; .name=="system:authenticated" or .name=="system:unauthenticated"))
  | "\(.kind) \(.metadata.namespace // "-")/\(.metadata.name) -> \(.roleRef.name)"'

# Roles that can read Secrets (in any namespace)
kubectl get roles,clusterroles -A -o json | jq -r '
  .items[] | select(any(.rules[]?; (.resources // []) | any(.=="secrets" or .=="*")))
  | "\(.kind) \(.metadata.namespace // "-")/\(.metadata.name)"'
```

The built-in system roles will appear in some results (the cluster's own components need them). The skill is to explain each line you see: who is the subject, why do they need it, and who owns that decision?

**Why "create Pods" equals "read Secrets" — demonstrated.** Grant a ServiceAccount permission to create Pods but not read Secrets; it can still obtain a Secret's value:

```yaml
apiVersion: v1
kind: Pod
metadata: { name: secret-reader, namespace: orders-staging }
spec:
  restartPolicy: Never
  containers:
    - name: c
      image: busybox:1.36
      command: ["sh", "-c", "cat /creds/password"]
      volumeMounts: [{ name: s, mountPath: /creds }]
  volumes: [{ name: s, secret: { secretName: demo-credentials } }]
```

Then `kubectl logs secret-reader` prints the value, although the creator's Role has no `secrets` rule. The defence is not a better Role; it is admission policy and separation of who may create workloads where, which the Professional section covers.

## Workload identities

Pods run as a ServiceAccount; give each workload its own and turn token automount off unless the workload calls the API. Automation (a GitOps controller, a CI job) gets its own identity with a namespaced Role. Prefer bounded tokens (`kubectl create token`, projected tokens) over long-lived token Secrets.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: orders-api, namespace: orders-staging }
automountServiceAccountToken: false          # default for Pods that use this account
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: orders-api, namespace: orders-staging }
spec:
  replicas: 2
  selector: { matchLabels: { app: orders-api } }
  template:
    metadata: { labels: { app: orders-api } }
    spec:
      serviceAccountName: orders-api
      automountServiceAccountToken: false    # state it on the Pod as well; the Pod setting wins
      containers:
        - name: app
          image: registry.example.com/orders/orders-api@sha256:0000000000000000000000000000000000000000000000000000000000000000
          ports: [{ containerPort: 8000 }]
```

(The digest above is a placeholder; use your own image.) How to *verify* the token is absent, and what changes when the workload does need the API:

```bash
kubectl exec -n orders-staging deploy/orders-api -- ls /var/run/secrets/kubernetes.io/serviceaccount
# illustrative: ls: cannot access ... No such file or directory     (token not mounted: good)

# A workload that genuinely needs the API: a projected, audience-bound, expiring token
#   volumes:
#     - name: api-token
#       projected:
#         sources:
#           - serviceAccountToken: { path: token, expirationSeconds: 3600, audience: orders-api }

kubectl create token orders-api -n orders-staging --duration=10m    # short-lived token, for a human or a test
```

Points to remember:

- Since modern versions, creating a ServiceAccount no longer creates a never-expiring token Secret. Treat any `kubernetes.io/service-account-token` Secret you find as a long-lived credential to replace or justify.
- The kubelet refreshes projected tokens before they expire; the application must re-read the file rather than cache the value forever.
- A token is only as safe as the Pod holding it: anyone who can `exec` into the Pod or read its filesystem can use it.

## Quotas, limits and Pod Security

| Control | Protects against | Does not protect against |
| --- | --- | --- |
| ResourceQuota | A namespace consuming all CPU, memory, object counts | A single Pod hogging within its allowance |
| LimitRange | Pods without requests or limits; absurd sizes | Aggregate overuse |
| Pod Security Admission | Privileged, host-namespace, root-capable Pods | Application-layer flaws |
| NetworkPolicy | Lateral movement between Pods | Anything if the network plugin does not enforce it |
| Namespaces | Name and RBAC scoping | Not a security boundary alone |

### ResourceQuota and LimitRange

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: compute, namespace: orders-staging }
spec:
  hard:
    requests.cpu: "2"
    requests.memory: 4Gi
    limits.cpu: "4"
    limits.memory: 8Gi
    pods: "20"
    persistentvolumeclaims: "5"
    services.loadbalancers: "0"
    count/secrets: "50"
---
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: orders-staging }
spec:
  limits:
    - type: Container
      defaultRequest: { cpu: 100m, memory: 128Mi }
      default: { cpu: 500m, memory: 256Mi }
      max: { cpu: "2", memory: 2Gi }
```

How the two cooperate: once a quota covers `requests` or `limits` for CPU or memory, every new Pod *must* declare them or be rejected. The LimitRange fills in defaults for Pods that omit them, so well-meaning teams are not blocked by paperwork, and `max` stops one container from claiming the whole allowance.

Prove it, in both directions:

```bash
kubectl describe resourcequota compute -n orders-staging       # Used versus Hard
kubectl run big -n orders-staging --image=busybox:1.36 --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"big","image":"busybox:1.36","command":["sleep","60"],"resources":{"limits":{"memory":"16Gi"}}}]}}'
# illustrative: Error from server (Forbidden): pods "big" is forbidden: maximum memory usage per Container is 2Gi, but limit is 16Gi
```

A frequent surprise: a **Deployment** that exceeds quota is *accepted*, because the Deployment object itself is fine. The failure happens later, when the ReplicaSet tries to create Pods. The symptom is "0 of 3 replicas ready" and the evidence is in events:

```bash
kubectl get events -n orders-staging --field-selector reason=FailedCreate
# illustrative: Error creating: pods "orders-api-…" is forbidden: exceeded quota: compute, requested: requests.cpu=500m, used: requests.cpu=1800m, limited: requests.cpu=2
```

### Pod Security Admission

Pod Security Admission (PSA) is built into the API server and is configured with **labels on a namespace**:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orders-staging
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Levels are `privileged`, `baseline` and `restricted`; modes are `enforce`, `audit` and `warn`. Roll out as **warn → audit → enforce** so you can see what would break first.

| Level | Intent | Typical content |
| --- | --- | --- |
| `privileged` | No restrictions | System and infrastructure components that genuinely need host access |
| `baseline` | Blocks known privilege escalations; minimal friction | Blocks privileged containers, host namespaces, `hostPath`, most added capabilities |
| `restricted` | Current hardening best practice | Adds: non-root, no privilege escalation, drop `ALL` capabilities, seccomp `RuntimeDefault` or `Localhost`, limited volume types |

Modes: `enforce` rejects the Pod; `audit` admits it and annotates the audit log; `warn` admits it and sends the client a warning.

Mind these details:

- `enforce` applies to **Pods**. For Deployments, Jobs and similar, `warn` and `audit` evaluate the Pod template, but `enforce` acts when the Pod is created, so the Deployment is accepted and its ReplicaSet fails later (the same shape as the quota failure above).
- `restricted` does **not** require `readOnlyRootFilesystem`. That is a good extra control, but it is yours to add through policy.
- Labels can pin a version (`pod-security.kubernetes.io/enforce-version: v1.30`) so the *meaning* of a level does not change when the cluster upgrades; `latest` follows the cluster.
- Who may *edit namespace labels* decides who may turn the control off. Restrict it.

The safe rollout recipe uses a server-side dry run, which reports what *existing* Pods would violate without changing anything:

```bash
kubectl label --dry-run=server --overwrite namespace orders-staging \
  pod-security.kubernetes.io/enforce=restricted
# illustrative output lists each existing violator:
# Warning: orders-api-6d9f…: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
# namespace/orders-staging labeled (server dry run)
```

Then label with `warn` and `audit` first, let teams fix manifests, and only afterwards add `enforce`.

## NetworkPolicy: from object to enforced behaviour

By default, every Pod can talk to every other Pod in the cluster, in any namespace. A **NetworkPolicy** selects Pods and describes the traffic allowed to and from them. Four facts drive everything:

1. A Pod is *unrestricted* until some policy **selects** it (through `podSelector`) for a direction (`Ingress` or `Egress`).
2. Once selected for a direction, the Pod accepts **only** what the union of selecting policies allows in that direction.
3. Policies are **additive**. There are no deny rules, and one policy cannot override another's allow.
4. Policies describe layer 3 and 4 traffic (IP addresses and ports). They do not understand HTTP paths or identities, and standard policies cannot log denials.

**Test whether NetworkPolicy is enforced — before relying on it.** The API server accepts a NetworkPolicy even if nothing enforces it. Create two Pods, apply a deny-all policy and check whether traffic really stops. If not, the network plugin does not enforce; choose one that does.

Use a separate lab namespace, because the test image runs as root and would be refused under `restricted`:

```bash
kubectl create namespace netpol-lab
kubectl run server -n netpol-lab --image=nginx:1.27 --port=80 --labels app=server
kubectl expose pod server -n netpol-lab --port 80
kubectl run client -n netpol-lab --image=busybox:1.36 --restart=Never --labels app=client -- sleep 3600
kubectl wait -n netpol-lab --for=condition=Ready pod/server pod/client --timeout=90s

kubectl exec -n netpol-lab client -- wget -qO- -T 3 http://server        # BEFORE: returns the nginx page
cat <<'EOF' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: deny-all, namespace: netpol-lab }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
EOF
kubectl exec -n netpol-lab client -- wget -qO- -T 3 http://server        # AFTER: should time out
# illustrative: wget: download timed out     <- enforced.  If the page still arrives, NOT enforced.
```

A kind cluster with its default network plugin may *not* enforce policies; installing one that does (for example Calico or Cilium) is the usual fix. The *timeout after the policy* is the proof; keep it.

**Default deny, then allow what is needed**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny, namespace: orders-staging }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-api, namespace: orders-staging }
spec:
  podSelector: { matchLabels: { app: orders-api } }
  policyTypes: [Ingress, Egress]
  ingress:
    - from: [{ namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: ingress } } }]
      ports: [{ port: 8000 }]
  egress:
    - to: [{ namespaceSelector: {}, podSelector: { matchLabels: { k8s-app: kube-dns } } }]
      ports: [{ port: 53, protocol: UDP }]
    - to: [{ podSelector: { matchLabels: { app: orders-db } } }]
      ports: [{ port: 5432 }]
```

Forgetting the DNS egress rule is the classic cause of "everything times out but Pods are Ready".

Details that cause real incidents:

- **Selector shape matters.** In `to: [{ namespaceSelector: {}, podSelector: {...} }]` both selectors are in *one* list item, which means *AND*: Pods matching the label, in any namespace. Written as two list items (`- namespaceSelector: {}` and `- podSelector: {...}`) it means *OR*, which is far broader. One dash changes the meaning.
- **DNS uses TCP as well as UDP.** Large responses fall back to TCP; allow port 53 on both to avoid intermittent failures.
- **Namespaces are matched by label.** Recent versions label every namespace with `kubernetes.io/metadata.name`, which is why the selector above works. Custom labels must be applied and protected from unreviewed edits.
Egress to the cloud *metadata service* deserves its own rule, because a stolen Pod can otherwise ask the node's identity for credentials. A policy that permits general egress but excludes that single address (`169.254.169.254` on most clouds) looks like this:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-internet-not-metadata, namespace: orders-staging }
spec:
  podSelector: { matchLabels: { app: orders-api } }
  policyTypes: [Egress]
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except: ["169.254.169.254/32", "10.0.0.0/8"]
```

(The `10.0.0.0/8` exclusion is illustrative: it stops "internet" egress from also reaching private ranges. Adjust to your network.) Verify with a request from a Pod: `wget -qO- -T 3 http://169.254.169.254/` should time out.

## A catalogue of misconfigurations and how to spot them

| Misconfiguration | How it looks | Detect with | Fix |
| --- | --- | --- | --- |
| `cluster-admin` bound to a team group | Everyone "just has access" | `get clusterrolebindings` query above | Namespaced Role; remove binding |
| `edit` or `admin` granted widely | Teams read each other's Secrets | `get rolebindings -A -o wide` | Grant `view`; use per-team namespaces |
| Wildcard verbs or resources | New CRDs silently covered | wildcard `jq` query | List resources explicitly |
| Default ServiceAccount used and mounted | Every Pod carries a token | `kubectl get pod -o yaml` and look for `serviceAccountName: default` | Dedicated account; `automountServiceAccountToken: false` |
| No quota or limits | One bug starves the cluster | `kubectl get resourcequota -A` shows gaps | Quota and LimitRange per namespace |
| PSA labels missing | Privileged Pods accepted | `kubectl get ns --show-labels` | Label namespaces; start with `warn` |
| NetworkPolicy present, not enforced | Policy objects exist; traffic still flows | The deny-all test | Use an enforcing network plugin |
| Privileged or `hostPath` workloads | Node-level access | PSA `audit` or the audit query | Restrict by policy, with exceptions owned |

## Verifying controls: a test matrix

Every control gets two tests: a **positive** one (the intended action works) and a **negative** one (the unintended action is refused). Keep both outputs. A control with only a positive test could be doing nothing.

| Control | Positive test | Negative test | Evidence to keep |
| --- | --- | --- | --- |
| Read-only Role | `can-i list pods --as alice` → yes | `get secrets --as alice` → Forbidden | The `Forbidden` message |
| ServiceAccount token off | App starts and serves | `ls` of the token path fails | Command output |
| ResourceQuota | A Pod within quota runs | A Pod beyond quota is rejected | `describe resourcequota`, rejection text |
| Pod Security `restricted` | The hardened Pod is accepted | The root Pod is rejected | Both messages |
| Default-deny NetworkPolicy | Allowed path works (`wget` to `orders-db` port) | Unlisted path times out | Both results, with timestamps |
| Metadata blocked | Normal internet egress works | Request to `169.254.169.254` times out | Timeout output |

A small script keeps such checks repeatable. Save it with your manifests and run it after every change to the controls:

```bash
#!/usr/bin/env bash
# verify-orders-staging.sh — illustrative; adapt names to your cluster
NS=orders-staging; FAILED=0
check() { if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; FAILED=1; fi; }
check "alice can list pods"        '[ "$(kubectl auth can-i list pods -n $NS --as alice)" = yes ]'
check "alice cannot read secrets"  '[ "$(kubectl auth can-i get secrets -n $NS --as alice)" = no ]'
check "PSA enforce=restricted"     'kubectl get ns $NS -o jsonpath="{.metadata.labels.pod-security\.kubernetes\.io/enforce}" | grep -qx restricted'
check "default-deny exists"        'kubectl get networkpolicy default-deny -n $NS'
check "quota exists"               'kubectl get resourcequota compute -n $NS'
exit $FAILED
```

Note what this script does *not* prove: that the network plugin enforces the policy. That needs the live traffic test. Existence checks are cheap and useful, but they are not behaviour checks.

## Knowledge consolidation

- Build a real unprivileged identity once; it makes every later `Forbidden` message real. Certificates are credentials and cannot be revoked by deleting the CSR.
- Roles are **rule triples** (groups, resources, verbs), additive and silent-by-default; bind **groups**, and reuse **ClusterRoles through RoleBindings**.
- `edit` and `admin` include Secrets; `view` does not. Aggregation means built-in roles can change when operators are installed.
- Audit with queries: `cluster-admin` bindings, wildcards, bindings to `system:authenticated`, roles that read Secrets, and ServiceAccounts with powerful bindings.
- **Create Pods ≈ read Secrets** in a namespace; the answer is admission policy, not another Role.
- Workloads get their **own ServiceAccount**, **no token** unless needed, and **bounded tokens** when needed.
- **Quota + LimitRange** work as a pair; Deployments exceeding quota fail at the ReplicaSet, visible in events.
- **PSA**: `warn → audit → enforce`, server-side dry run first; `restricted` does not imply read-only root filesystem.
- **NetworkPolicy** must be tested for enforcement; mind the AND/OR selector shape, DNS and metadata egress.
- Every control gets a **positive and a negative test** and saved evidence.

## Exercises

**Exercise 1 — Real Alice.** Create the certificate-based identity, approve its CSR, bind `developer-readonly` and use the `alice-staging` context. Record `auth whoami`, an allowed request and a denied request. Then delete the CSR and show that the certificate still authenticates; note its expiry from `openssl x509`.

**Exercise 2 — Audit your own cluster.** Run the three audit queries and the `cluster-admin` query on your practice cluster. For each line of output, write down subject, purpose and owner, or mark it "unexplained". Remove (or at least flag) one unexplained item.

**Exercise 3 — Create Pods, read Secrets.** Create the `demo-credentials` Secret. Grant a ServiceAccount only `create` on Pods and `get` on Pods and `pods/log`. Using that identity, obtain the Secret value through a Pod. Write down two controls that would have prevented it.

**Exercise 4 — Quota and limits.** Apply the quota and LimitRange. Create a Pod without resources and show the defaults were injected. Create a Pod beyond the maximum and record the rejection. Create a Deployment whose replicas exceed the quota and capture the `FailedCreate` event.

**Exercise 5 — Pod Security rollout.** In a fresh namespace, deploy a root-running Deployment. Run the server-side dry run for `restricted`, then apply `warn` and `audit`, deploy again and note the warnings. Fix the manifest to pass, then apply `enforce` and show a non-compliant Pod being refused.

**Exercise 6 — Default deny, proven.** In `netpol-lab`, show the client reaching the server, apply `deny-all`, show the timeout, then add the *narrowest* allow policy (one client label to one server port) and show success again. Include one test showing a Pod *without* the client label is still refused. If your plugin does not enforce, record that finding and fix it.

**Solution notes.**

*Exercise 1.* After approval, `kubectl --context alice-staging auth whoami` should show username `alice`. Allowed and denied requests behave as for `--as`. After `kubectl delete csr alice`, the issued certificate continues to work until its expiry (the `notAfter` date), which is the evidence for "deleting the CSR is not revocation". If the CSR is rejected on a managed cluster, that provider may restrict the signer; use `--as` and record why.

*Exercise 2.* A fresh cluster shows `cluster-admin` bound to `system:masters` and system components, plus wildcards and Secret rules inside built-in roles. The deliverable is the *table with owners*, not a clean result.

*Exercise 3.* The mounted Pod prints the value. Preventive controls include: policy that forbids Pods from mounting Secrets not owned by the same workload (admission, Professional level), limiting who may create Pods in the namespace (RBAC), and splitting sensitive Secrets into namespaces that unprivileged identities cannot create Pods in.

*Exercise 4.* Defaults appear under `kubectl get pod -o yaml` as `resources.requests` and `limits` that you did not write. The over-max Pod is refused by the LimitRange at creation. The over-quota Deployment is accepted, with replicas below desired and `FailedCreate` events mentioning `exceeded quota`. Exact numbers depend on your quota; keep your own.

*Exercise 5.* The dry-run warnings list the violations of existing Pods; `warn` shows warnings on `kubectl apply`; `audit` shows nothing to the client but annotates audit events. Under `enforce`, a Deployment may still be created while its Pods are refused: look at the ReplicaSet's events rather than the Deployment's. A passing manifest sets non-root, no escalation, dropped capabilities and seccomp.

*Exercise 6.* Before the policy, the request succeeds; after `deny-all`, `wget` times out (if it succeeds, your plugin does not enforce NetworkPolicy). After the narrow allow, only Pods with the client label succeed; an unlabelled Pod still times out. Remember that the allow policy needs *both* an ingress rule for the server and, because `deny-all` also denies egress, an egress rule for the client (including DNS) if you resolve by Service name.
