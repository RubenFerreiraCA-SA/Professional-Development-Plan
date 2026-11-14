# T-PLT-03-I — Intermediate Practice

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-i"></a>
#### T-PLT-03-I — Intermediate Practice

**A real unprivileged identity.** On a practice cluster, create a user credential through a certificate signing request, bind the read-only Role and use a separate kubeconfig context:

```bash
openssl genrsa -out alice.key 2048
openssl req -new -key alice.key -subj "/CN=alice" -out alice.csr
# create a CertificateSigningRequest object containing alice.csr, approve it, fetch the cert
kubectl config set-credentials alice --client-certificate=alice.crt --client-key=alice.key
kubectl config set-context alice-staging --cluster=lab --user=alice --namespace=orders-staging
```

Deleting the CSR does not revoke an issued certificate; only expiry (or rotating the CA) does. Prefer short-lived tokens from an identity provider in real clusters.

**Escalation traps — audit for these**

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

**Workload identities.** Pods run as a ServiceAccount; give each workload its own and turn token automount off unless the workload calls the API. Automation (a GitOps controller, a CI job) gets its own identity with a namespaced Role. Prefer bounded tokens (`kubectl create token`, projected tokens) over long-lived token Secrets.

**Quotas, limits and Pod Security**

| Control | Protects against | Does not protect against |
| --- | --- | --- |
| ResourceQuota | A namespace consuming all CPU, memory, object counts | A single Pod hogging within its allowance |
| LimitRange | Pods without requests or limits; absurd sizes | Aggregate overuse |
| Pod Security Admission | Privileged, host-namespace, root-capable Pods | Application-layer flaws |
| NetworkPolicy | Lateral movement between Pods | Anything if the network plugin does not enforce it |
| Namespaces | Name and RBAC scoping | Not a security boundary alone |

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

**Test whether NetworkPolicy is enforced — before relying on it.** The API server accepts a NetworkPolicy even if nothing enforces it. Create two Pods, apply a deny-all policy and check whether traffic really stops. If not, the network plugin does not enforce; choose one that does.

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

**Exercise.** Create a namespace with quota, default-deny and allow rules, then show a denied connection, an allowed connection and a quota rejection.
