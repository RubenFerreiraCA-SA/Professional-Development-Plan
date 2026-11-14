# T-PLT-03-P — Professional Engineering

*Chapter: [T-PLT-03 — Kubernetes Security and Policy](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-03-p"></a>
#### T-PLT-03-P — Professional Engineering

**Policy as code at admission.** Rules enforced where objects enter the cluster catch everything that bypassed CI. Kubernetes includes `ValidatingAdmissionPolicy` (CEL expressions, no extra controller in recent versions); policy engines such as Kyverno or OPA Gatekeeper add richer rules and mutation.

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

Pair it with a binding that selects namespaces. Design rules:

- Use the **same rules** in CI and at admission: CI gives fast feedback, admission is the backstop.
- Make policy messages actionable ("Use a digest; see docs page X").
- Start in audit or warn mode, measure impact, then enforce.
- Fail closed for security-critical rules, with a documented exception path and expiry.
- Test policies with positive and negative fixtures in CI, using offline evaluation with no cluster credentials.
- Distinguish messages from RBAC, Pod Security Admission and policy engines when diagnosing denials.

**Typical baseline rules.** No privileged containers or host namespaces; non-root; no privilege escalation; dropped capabilities; read-only root filesystem where feasible; resource requests and memory limits present; images by digest from approved registries; no `latest` tags; required labels (owner, service); no `hostPath`; restricted Service types and Ingress hosts; seccomp profile set.

**Securing the control plane and nodes.** Restrict API server exposure; require authentication through an identity provider; enable audit logging and ship logs off-cluster; encrypt etcd and protect its backups; keep kubelet authentication and authorisation on; patch nodes and the control plane on a schedule; harden node operating systems; and restrict the cloud metadata service from Pods.

**Secrets management.** External secret stores synchronised by an operator, or mounted by a CSI driver; short-lived credentials; per-workload access; rotation procedures tested; encryption at rest; RBAC to restrict reads; no secrets in manifests, Helm values in Git or images.

**Supply chain at the cluster.** Admit only images from approved registries, by digest, with verified signatures or attestations when you have them; scan images and rendered manifests; limit who can create privileged Pods; and treat controllers and operators (which hold powerful permissions) as high-value targets.

**Tenancy model.** Per-tenant namespace with quota, limit range, default-deny network policy, restricted Pod Security and a namespaced reconciler identity. Soft multi-tenancy (trusted teams) is common; for untrusted tenants consider separate clusters or sandboxed runtimes, because namespaces share a kernel and control plane.

**Auditing and evidence.** Weekly RBAC audit queries; review of `cluster-admin` bindings; record Forbidden transcripts; log policy denials; track exceptions with owners and expiry dates; keep an up-to-date limitations register (for example, "developer read role is cluster-wide", "kind does not encrypt secrets").

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Give a team access | Namespaced Role plus RoleBinding | ClusterRoleBinding for convenience |
| Stop unsafe Pods | Pod Security `restricted` plus policy | Relying on reviewers |
| Limit lateral movement | Default-deny NetworkPolicy, verified enforcement | Assuming the policy object works |
| Control images | Digest-only, approved registries, scanning | Tags and unscanned images |
| Handle secrets | External manager, restricted RBAC | Base64 in Git |
| Allow exceptions | Documented, time-boxed, owned | Permanent silent bypass |
