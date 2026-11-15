# T-PLT-03-B — Beginner Foundations

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-b"></a>
#### T-PLT-03-B — Beginner Foundations

## Why this matters

A Kubernetes cluster is a shared machine. Many teams, many applications and many automated tools all ask the same control plane to run things, read things and change things. Without rules about *who may do what, where*, the first mistake (a leaked credential, a copy-pasted manifest, a Pod that runs as root) can reach everything else in the cluster.

Security in Kubernetes is not one feature. It is a small number of layers, each answering one question, and each of which can be bypassed if the layer next to it is missing. This Beginner section teaches the vocabulary and the habit that matters most: **never assume a control works; prove it with a command and keep the output**.

You need `kubectl` and a *practice* cluster you may break (a local `kind` or `minikube` cluster); never run the exercises on shared or production clusters. Examples use a fictional service `orders-api`, a namespace `orders-staging` and a person `alice`. Outputs labelled *illustrative* show the expected shape, not measured results.

## First principles: everything goes through the API server

Kubernetes keeps its state (what should run, who may do what, which secrets exist) behind one front door: the **API server**. `kubectl`, the scheduler, the kubelet on each node, controllers, CI jobs and your applications all talk to it over HTTPS. That single entry point is what makes cluster security tractable: if you control who gets in and what they may ask for, you control the cluster.

```text
 person / CI job / Pod
          │  HTTPS request: "create Pod orders-api in orders-staging"
          ▼
 ┌───────────────────────────────────────────────────────────────┐
 │ API server                                                    │
 │  1. Authentication  → who is this?            (else 401)      │
 │  2. Authorisation   → may they do this?       (else 403)      │
 │  3. Admission       → is this object OK?      (else rejected) │
 │  4. Validation + store in etcd                                │
 └───────────────────────────────────────────────────────────────┘
          │
          ▼
 controllers and kubelets act on what was stored
```

The order is fixed: a request that fails at step 1 never reaches step 2, and each step says *no* for a different reason. Controls below the API (network rules, node hardening) exist too, but most permission decisions are made here.

## The three questions every request answers

| Step | Question | Mechanism |
| --- | --- | --- |
| Authentication | Who are you? | Client certificate, OIDC token, ServiceAccount token. There is no `User` object |
| Authorisation | May you do this? | RBAC (Role-based access control) |
| Admission | Is this *object* acceptable? | Pod Security Admission and validating or mutating policies |

Keep this table in your head. Almost every "permission denied" you meet in this chapter is the answer to exactly one of these questions.

### Authentication: who are you?

Kubernetes does **not** store people. There is no `kubectl create user`. A person authenticates through something outside the cluster (an identity provider using OIDC, or a client certificate signed by the cluster's certificate authority), and the API server learns a **user name** and a list of **groups** from that credential. Pods and automation use **ServiceAccounts**, which *are* real objects.

You can ask the cluster who it thinks you are:

```bash
kubectl auth whoami
# illustrative output (the exact format differs by version and credential type)
# ATTRIBUTE   VALUE
# Username    kubernetes-admin
# Groups      [system:masters system:authenticated]
```

(`kubectl auth whoami` needs a recent client and cluster.)

A kubeconfig file ties together a **cluster**, a **user** (the credential) and a **context** (a named pairing, with an optional default namespace). `kubectl config current-context` shows which one you are using.

Habit: read `kubectl config current-context` before every state-changing command; many incidents are "right command, wrong cluster".

### Authorisation: may you do this?

Once the API server knows who you are, **RBAC** decides what you may do. RBAC works with a small vocabulary:

| Object | Scope | Use |
| --- | --- | --- |
| Role + RoleBinding | One namespace | Default for teams and workloads |
| ClusterRole + RoleBinding | Reusable rules granted per namespace | Share a rule set without cluster-wide grants |
| ClusterRole + ClusterRoleBinding | Whole cluster | Platform operators only; review every one |

- A **Role** (or **ClusterRole**) is a list of permissions: *these verbs, on these resources*.
- A **RoleBinding** (or **ClusterRoleBinding**) attaches a Role to **subjects** (users, groups or ServiceAccounts).
- A ClusterRole is only a *definition*. It grants nothing until something binds it, and a **RoleBinding** to a ClusterRole confines that ClusterRole's permissions to the binding's namespace.

RBAC is *additive*: there are no deny rules. A subject's permissions are the union of every rule in every binding that names them (directly, or through a group). So you cannot "forbid Alice from reading Secrets" by adding a rule; you can only make sure *no binding grants it*. Least privilege therefore means granting small Roles in namespaces rather than cluster-wide roles, and reviewing what exists, not what you intended to create.

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

**Reading a Role precisely.** Take the `developer-readonly` Role above. It grants `get`, `list` and `watch` on `pods`, `pods/log`, `services` and `events`, only in `orders-staging`. It does not grant `secrets`, `deployments` (which live in the `apps` API group, not the core `""` group), `exec` (`pods/exec`) or anything in other namespaces. A rule reads: *these verbs, on these resources, in these API groups*. Wildcards (`*`) broaden all three dimensions; review them closely.

A few details that surprise newcomers:

- **Subresources are separate.** `pods` and `pods/log` and `pods/exec` are three different resources. Reading logs does not grant `exec`, and the reverse.
- **API groups matter.** The empty string means the *core* group (Pods, Services, Secrets, ConfigMaps). Deployments are in `apps`; Ingresses and NetworkPolicies are in `networking.k8s.io`; Roles themselves are in `rbac.authorization.k8s.io`.
```bash
kubectl api-resources --namespaced=true | head -n 20     # resource names and API groups
kubectl get role,rolebinding -n orders-staging
kubectl describe rolebinding alice-readonly -n orders-staging
kubectl describe role developer-readonly -n orders-staging
```

**Prove access with real commands.**

```bash
kubectl auth can-i list pods -n orders-staging --as alice          # yes
kubectl auth can-i delete deployments -n orders-staging --as alice # no
kubectl auth can-i get secrets -n orders-staging --as alice        # no
kubectl --as alice -n orders-staging get secrets                   # shows the real Forbidden message
```

`--as alice` asks the API server to evaluate the request as alice; it works for you only because administrators hold the `impersonate` permission.

Keep the actual `Forbidden` output as evidence, not only the yes/no:

```text
Error from server (Forbidden): secrets is forbidden: User "alice" cannot list resource "secrets" in API group "" in the namespace "orders-staging"
```

Read the message as a sentence: *which user*, *which verb*, *which resource*, *which API group*, *which namespace*. Each piece tells you what a missing rule would have to say.

### Admission: is this object acceptable?

Authorisation judges the *person and the action*; admission judges the *object*. A user allowed to create Pods can still be refused when the Pod asks to run as root or mount the host's filesystem. Kubernetes includes **Pod Security Admission**, and clusters add policy mechanisms of their own (the Professional section).

## Where a denial comes from

A request such as "create a Pod in `orders-staging`" passes three gates in order. A failure at an earlier gate means later gates are never reached.

| Gate | Example denial | Message shape | What to check |
| --- | --- | --- | --- |
| Authentication | Expired token or unknown client certificate | `Unauthorized` (401) | The kubeconfig user and credentials |
| Authorisation | Alice may list Pods but not delete them | `Forbidden: User "alice" cannot delete resource "pods" …` (403) | Roles and bindings; `kubectl auth can-i` |
| Admission | The Pod runs as root where the namespace forbids it | `violates PodSecurity "restricted:latest"` or a policy message | Pod spec against the namespace's Pod Security level and policies |

Diagnosis is therefore a matter of reading the first words of the message and going to the right layer. Changing a Role will never fix an admission denial, and loosening a policy will never fix a 401.

## Subjects: users, groups and ServiceAccounts

People authenticate through an external identity (OIDC or certificate); Kubernetes has no user database. *ServiceAccounts* are identities for Pods and automation, and they are real objects in a namespace. A Pod uses the ServiceAccount named in `spec.serviceAccountName` (or the namespace's `default` one) and receives a short-lived token for it, mounted as a file inside the container.

**Binding a ServiceAccount, and testing as it.**

```bash
kubectl create serviceaccount orders-reader -n orders-staging
kubectl create rolebinding orders-reader-view \
  --clusterrole=view --serviceaccount=orders-staging:orders-reader -n orders-staging
kubectl auth can-i list pods   -n orders-staging --as system:serviceaccount:orders-staging:orders-reader   # yes
kubectl auth can-i get secrets -n orders-staging --as system:serviceaccount:orders-staging:orders-reader   # no
kubectl auth can-i --list      -n orders-staging --as system:serviceaccount:orders-staging:orders-reader
```

The built-in `view` ClusterRole is bound with a RoleBinding here, so its permissions apply only inside `orders-staging`. Note the long identity: `system:serviceaccount:<namespace>:<name>`. The `--list` form prints everything the identity may do in that namespace, which is the quickest way to see what a binding really granted.

Two rules of thumb for workloads:

- **One ServiceAccount per workload.** If everything uses `default`, everything shares one identity, and any permission you give one application is given to all of them.
- **Most applications never call the Kubernetes API.** A web service that only serves HTTP does not need an API token. The Intermediate section shows how to switch the token off.

## What a Namespace does and does not do

**Namespaces are not security boundaries by themselves.** They scope names and RBAC. Isolation needs quotas, network policy, admission policy and per-namespace roles.

| It provides | It does not provide |
| --- | --- |
| Separate name scope (two `orders-api` Services can coexist) | Network isolation: Pods in any namespace can talk to each other unless a NetworkPolicy blocks it |
| A unit for RBAC, quotas and policies | Node isolation: Pods from different namespaces share nodes and a kernel |
| A convenient unit for deletion and ownership | Protection from cluster-scoped objects such as Nodes, ClusterRoles and CRDs |

```bash
kubectl create namespace orders-staging
kubectl delete namespace orders-staging        # deletes EVERYTHING inside it; practice cluster only
```

Deleting a namespace deletes everything in it (Secrets, claims, Roles), which is why you read your current context first.

## Secrets: what they are and what they are not

A **Secret** is a Kubernetes object that holds small pieces of sensitive data (a password, a token, a certificate) so they do not have to be baked into an image or a manifest. Two facts must be understood before using one:

1. **Base64 is encoding, not encryption.** The values in a Secret's `data` field are base64 text. Anyone who can read the Secret can decode it in one command.
2. **Reading a Secret is an RBAC permission like any other.** Whoever has `get` or `list` on Secrets in a namespace can read the values. `list` returns the data, not just names.

Create and read a *harmless* Secret on your practice cluster:

```bash
kubectl create secret generic demo-credentials -n orders-staging \
  --from-literal=username=demo --from-literal=password='not-a-real-password'
kubectl get secret demo-credentials -n orders-staging -o yaml        # note the base64 values
kubectl get secret demo-credentials -n orders-staging \
  -o jsonpath='{.data.password}' | base64 --decode; echo             # prints: not-a-real-password
```

Use dummy values only; never paste real credentials into examples or chat.

A Pod can consume a Secret as environment variables or as files (files are usually better: they can be permissioned and refreshed). Important consequence for access control: **a person who may create Pods in a namespace can mount any Secret in that namespace**, even if their Role does not allow them to read Secrets directly. "Can create Pods" and "can read Secrets here" are, for practical purposes, the same privilege. The Intermediate and Expert sections build on this.

Finally, a Secret lives in the cluster's database (etcd). Whether it is *encrypted at rest* depends on configuration (see the Professional section); treat every Secret as readable by anyone with the right API permission or access to the database and its backups.

## Threat boundaries: where one thing can hurt another

A **threat boundary** is a line across which one party should not be able to affect another. Drawing them is the first step of security thinking. For a cluster, the useful lines are:

```text
Internet ──► Ingress / Load balancer ──► Pod (your application)
                                            │  ▲
        namespace A ◄─────────────────────► │  │  namespace B
                                            ▼  │
                                     Node (shared kernel)
                                            │
                                     API server / etcd (control plane)
                                            │
                                     Cloud account / secrets stores
```

| Boundary | What protects it | What does *not* protect it |
| --- | --- | --- |
| Pod → Pod | NetworkPolicy (if enforced), mutual authentication | Namespaces alone |
| Pod → API server | ServiceAccount permissions, token handling | The Pod's own good intentions |
| Pod → node | Pod Security settings, seccomp, non-root | Namespaces; quotas |
| Person → cluster | Identity provider, RBAC, audit log | A shared admin kubeconfig |

A simple story shows how the layers connect. An attacker finds a bug in `orders-api` and runs commands inside its container. What can they do next? They can read the files the container can see (including a mounted ServiceAccount token and Secrets), connect to anything the network allows, and call the API with the Pod's token. Each later section of this chapter shortens that list: a ServiceAccount with no permissions makes the token useless; a network policy limits where connections go; a hardened Pod cannot reach the node; admission policy refuses the Pods that would have made this easy.

## Pod hardening basics

Run as non-root; disallow privilege escalation; drop all capabilities; use the runtime's default seccomp profile; avoid host networking, host paths and privileged containers.

```yaml
securityContext:           # container level
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities: { drop: ["ALL"] }
  seccompProfile: { type: RuntimeDefault }
```

In short: refuse to start as root, block setuid-style escalation, stop the application writing to its own filesystem, remove root's finer-grained powers, and block risky system calls.

A complete, safe example Pod that follows these settings (writes only to a scratch volume):

```yaml
apiVersion: v1
kind: Pod
metadata: { name: hardened-demo, namespace: orders-staging, labels: { app: orders-api } }
spec:
  serviceAccountName: orders-reader
  automountServiceAccountToken: false
  securityContext:         # pod level
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "touch /scratch/ok && sleep 3600"]
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities: { drop: ["ALL"] }
      volumeMounts:
        - { name: scratch, mountPath: /scratch }
  volumes:
    - { name: scratch, emptyDir: {} }
```

Namespaces can enforce a Pod Security Standard with labels such as `pod-security.kubernetes.io/enforce: restricted`. Try applying a root-running Pod to such a namespace and read the rejection message; that is admission control working.

```bash
kubectl label namespace orders-staging pod-security.kubernetes.io/enforce=restricted --overwrite
kubectl run root-demo -n orders-staging --image=busybox:1.36 --restart=Never -- sleep 60
# illustrative: Error from server (Forbidden): pods "root-demo" is forbidden: violates PodSecurity "restricted:latest":
#   allowPrivilegeEscalation != false (container "root-demo" must set securityContext.allowPrivilegeEscalation=false),
#   unrestricted capabilities (container "root-demo" must set securityContext.capabilities.drop=["ALL"]),
#   runAsNonRoot != true (pod or container "root-demo" must set securityContext.runAsNonRoot=true),
#   seccompProfile (pod or container "root-demo" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
kubectl apply -f hardened-demo.yaml        # the hardened Pod above is accepted
```

The message lists *every* violation at once, each with the field to set. That makes admission denials one of the friendlier errors in Kubernetes: read it as a to-do list.

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Granting `cluster-admin` "temporarily" and leaving it in place | Everything works, so nobody notices | Use a time-boxed, namespaced Role; list `cluster-admin` bindings regularly |
| Believing a Secret is protected because it is in a different namespace, while the Role grants `get secrets` cluster-wide | Alice reads another team's Secret | Replace the ClusterRoleBinding with a namespaced RoleBinding |
| Testing access with your own admin credentials and concluding that a ServiceAccount "should work" | The application gets `Forbidden` in production | Test with `--as system:serviceaccount:<ns>:<name>` |
| Forgetting that `list` on Secrets reveals their values, because list returns the data | A "list-only" role still leaks passwords | Treat `list` and `watch` on Secrets as `get` |
| Copying a `ClusterRoleBinding` from the internet without reading what it grants | An unknown subject holds broad rights | Read `roleRef` and `subjects`, then `kubectl describe` the role |

## Knowledge consolidation

- Every request passes **authentication → authorisation → admission**, in that order; the error message says which gate refused.
- Kubernetes has **no User objects**; people come from an external identity, workloads use **ServiceAccounts**.
- **RBAC is additive.** There are no deny rules; least privilege means small Roles in namespaces and reviewing what is actually bound.
- **Subresources and API groups** are part of every rule; `pods/exec` and `deployments` do not come with `pods`.
- **Base64 is not encryption.** Anyone who can `get` or `list` Secrets can read values, and anyone who can create Pods in a namespace can mount its Secrets.
- A **namespace** scopes names and RBAC; it is not a network, node or kernel boundary.
- **Pod hardening** removes attacker options: non-root, no escalation, dropped capabilities, default seccomp, no host access.
- **Prove controls** with `kubectl auth can-i`, real requests and saved output, in both the allowed and the denied direction.

## Exercises

**Exercise 1 — Role, binding, proof.** On a practice cluster create the namespace `orders-staging`, the `developer-readonly` Role and the `alice-readonly` binding. Run the four commands from the proof section and save the output. Then run `kubectl describe` on the Role and binding and write one sentence for each rule explaining it in plain words.

**Exercise 2 — The missing group.** Alice is told she can "see the Deployments" but `kubectl --as alice get deployments -n orders-staging` fails. Find the exact message, identify the missing API group, add it to a *new* Role (not the existing one) and prove the change. Then prove she still cannot delete anything.

**Exercise 3 — A ServiceAccount under test.** Create the `orders-reader` ServiceAccount and bind `view` to it in `orders-staging` only. Use `kubectl auth can-i --list` as that identity. Then try to list Pods in the `default` namespace as the same identity and record the result.

**Exercise 4 — Secrets are readable.** Create `demo-credentials` with dummy values and decode it. Give Alice a Role allowing only `list` on Secrets and show she still obtains the values with `kubectl --as alice get secrets -o yaml`. Remove the grant.

**Exercise 5 — Three denials.** Produce one real denial at each gate: a 401 (use a kubeconfig with an invalid token on a practice cluster), a 403 (a request Alice may not make) and an admission rejection (the root Pod into a `restricted` namespace). For each, note the first words of the message and which layer you would fix.

**Solution notes.**

*Exercise 1.* `can-i list pods` answers `yes`; `can-i get secrets` answers `no`, and the real request prints a `Forbidden` message naming `alice`, `list`, `secrets` and `orders-staging`. If `can-i` unexpectedly says `yes`, look for another binding that names `alice` or one of her groups; RBAC is additive, so one binding is enough.

*Exercise 2.* The message names `deployments` in API group `apps`; the core `""` group did not cover it. A new Role with that group, resource and the read verbs fixes it, and `can-i delete deployments` stays `no`.

*Exercise 3.* The identity can list most namespaced objects in `orders-staging` but `--list` should not show Secrets, and requests in `default` should be `Forbidden`. If you see access in `default`, look for a ClusterRoleBinding naming the ServiceAccount.

*Exercise 4.* `list` returns full content, so Alice sees and can decode the values: "list but not get" is no protection for Secrets. After removing the grant, keep the `Forbidden` transcript.

*Exercise 5.* The 401 reads `Unauthorized`; the 403 reads `Forbidden: User "alice" cannot …`; the admission rejection reads `violates PodSecurity "restricted:latest": …`. The fixes are credentials, a Role or binding (or a decision *not* to grant), and the Pod's `securityContext`. Do not treat all three as "RBAC problems".
