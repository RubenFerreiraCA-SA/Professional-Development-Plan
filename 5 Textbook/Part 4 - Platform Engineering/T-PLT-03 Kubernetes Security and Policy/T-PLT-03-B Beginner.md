# T-PLT-03-B — Beginner Foundations

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-b"></a>
#### T-PLT-03-B — Beginner Foundations

**Three questions every API request answers.**

| Step | Question | Mechanism |
| --- | --- | --- |
| Authentication | Who are you? | Client certificate, OIDC token, ServiceAccount token. There is no `User` object |
| Authorisation | May you do this? | RBAC (Role-based access control) |
| Admission | Is this *object* acceptable? | Pod Security Admission and validating or mutating policies |

**RBAC vocabulary**

| Object | Scope | Use |
| --- | --- | --- |
| Role + RoleBinding | One namespace | Default for teams and workloads |
| ClusterRole + RoleBinding | Reusable rules granted per namespace | Share a rule set without cluster-wide grants |
| ClusterRole + ClusterRoleBinding | Whole cluster | Platform operators only; review every one |

RBAC is *additive*: there are no deny rules. Least privilege means granting small Roles in namespaces rather than cluster-wide roles.

**A first Role**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: developer-readonly, namespace: orders-staging }
rules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "events"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: alice-readonly, namespace: orders-staging }
subjects:
  - { kind: User, name: alice, apiGroup: rbac.authorization.k8s.io }
roleRef: { kind: Role, name: developer-readonly, apiGroup: rbac.authorization.k8s.io }
```

**Prove access with real commands.**

```bash
kubectl auth can-i list pods -n orders-staging --as alice          # yes
kubectl auth can-i delete deployments -n orders-staging --as alice # no
kubectl auth can-i get secrets -n orders-staging --as alice        # no
kubectl --as alice -n orders-staging get secrets                   # shows the real Forbidden message
```

Keep the actual `Forbidden` output as evidence, not only the yes/no.

**Namespaces are not security boundaries by themselves.** They scope names and RBAC. Isolation needs quotas, network policy, admission policy and per-namespace roles.

**Pod hardening basics.** Run as non-root; disallow privilege escalation; drop all capabilities; use the runtime's default seccomp profile; avoid host networking, host paths and privileged containers.

**Where a denial comes from.** A request such as "create a Pod in `orders-staging`" passes three gates in order. A failure at an earlier gate means later gates are never reached.

| Gate | Example denial | Message shape | What to check |
| --- | --- | --- | --- |
| Authentication | Expired token or unknown client certificate | `Unauthorized` (401) | The kubeconfig user and credentials |
| Authorisation | Alice may list Pods but not delete them | `Forbidden: User "alice" cannot delete resource "pods" …` (403) | Roles and bindings; `kubectl auth can-i` |
| Admission | The Pod runs as root where the namespace forbids it | `violates PodSecurity "restricted:latest"` or a policy message | Pod spec against the namespace's Pod Security level and policies |

**Subjects: users, groups and ServiceAccounts.** People authenticate through an external identity (OIDC or certificate); Kubernetes has no user database. *ServiceAccounts* are identities for Pods and automation, and they are real objects in a namespace. A Pod uses the ServiceAccount named in `spec.serviceAccountName` (or the namespace's `default` one) and receives a short-lived token for it.

**Reading a Role precisely.** Take the `developer-readonly` Role above. It grants `get`, `list` and `watch` on `pods`, `pods/log`, `services` and `events`, only in `orders-staging`. It does not grant `secrets`, `deployments` (which live in the `apps` API group, not the core `""` group), `exec` (`pods/exec`) or anything in other namespaces. A rule reads: *these verbs, on these resources, in these API groups*. Wildcards (`*`) broaden all three dimensions; review them closely.

```bash
kubectl api-resources --namespaced=true | head -n 20     # resource names and API groups
kubectl get role,rolebinding -n orders-staging
kubectl describe rolebinding alice-readonly -n orders-staging
```

**Binding a ServiceAccount, and testing as it.**

```bash
kubectl create serviceaccount orders-reader -n orders-staging
kubectl create rolebinding orders-reader-view \
  --clusterrole=view --serviceaccount=orders-staging:orders-reader -n orders-staging
kubectl auth can-i list pods   -n orders-staging --as system:serviceaccount:orders-staging:orders-reader   # yes
kubectl auth can-i get secrets -n orders-staging --as system:serviceaccount:orders-staging:orders-reader   # no
kubectl auth can-i --list      -n orders-staging --as system:serviceaccount:orders-staging:orders-reader
```

The built-in `view` ClusterRole is bound with a RoleBinding here, so its permissions apply only inside `orders-staging`.

**What a Namespace does and does not do**

| It provides | It does not provide |
| --- | --- |
| Separate name scope (two `orders-api` Services can coexist) | Network isolation: Pods in any namespace can talk to each other unless a NetworkPolicy blocks it |
| A unit for RBAC, quotas and policies | Node isolation: Pods from different namespaces share nodes and a kernel |
| A convenient unit for deletion and ownership | Protection from cluster-scoped objects such as Nodes, ClusterRoles and CRDs |

**Pod Security in practice.** A hardened container spec looks like this:

```yaml
securityContext:           # container level
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities: { drop: ["ALL"] }
  seccompProfile: { type: RuntimeDefault }
```

Namespaces can enforce a Pod Security Standard with labels such as `pod-security.kubernetes.io/enforce: restricted`. Try applying a root-running Pod to such a namespace and read the rejection message; that is admission control working.

**Common mistakes**

- Granting `cluster-admin` "temporarily" and leaving it in place.
- Believing a Secret is protected because it is in a different namespace, while the Role grants `get secrets` cluster-wide.
- Testing access with your own admin credentials and concluding that a ServiceAccount "should work".
- Forgetting that `list` on Secrets reveals their values, because list returns the data.
- Copying a `ClusterRoleBinding` from the internet without reading what it grants.

**Exercise.** Create a namespace, a read-only Role and a binding, then prove with `can-i` and a real request what is allowed and denied.
