# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-077**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-077](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-077](../../../4%20Project%20Document/Project.md#prj-077).

## MODULE PLT-03-I — KUBERNETES SECURITY AND POLICY — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Applying a baseline access model in a disposable namespace. You create an unprivileged identity and bind a minimal Role, give each workload its own ServiceAccount with token automount off by default, set ResourceQuota and LimitRange, label namespaces for Pod Security Admission, add `securityContext` settings, and write NetworkPolicy default-deny plus targeted allows.

**Out of scope:** Vocabulary recognition (Beginner), admission engines and policy-as-code pipelines (Professional), runtime security and zero-trust design (Expert), and the written Harbour baseline (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-03--kubernetes-security-and-policy) when this matches your current ability: *Use access roles and routine security controls.* Typical starting point: You understand RBAC vocabulary and now need to configure access, quotas and network restrictions that actually work.

### 2. Learning Objectives

1. Create a namespace-scoped Role, RoleBinding and ServiceAccount for a workload and verify its access boundary with `kubectl auth can-i --as=system:serviceaccount:<ns>:<name>`.
2. Identify three escalation traps (for example permission to create Pods, bind roles or read Secrets) and audit a Role for them.
3. Set a ResourceQuota, LimitRange and Pod Security Admission labels (`pod-security.kubernetes.io/enforce`) on a namespace and show an over-quota or non-compliant Pod being rejected.
4. Write a default-deny NetworkPolicy plus one allow rule, and first prove the cluster's network plugin actually enforces NetworkPolicy before relying on it.
5. Prepare the evidence needed for **PRJ-078**: a role, quota or workload security restriction applied in a disposable namespace, with before-and-after proof.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-03-I — Kubernetes Security and Policy — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-03-i) — Work through the unprivileged identity, escalation traps, workload identities, quotas, limits and Pod Security, NetworkPolicy testing and the default-deny exercise.

Optional enrichment: the certificate-signing-request example for creating a real user identity. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** In a fresh namespace, apply a quota, a restricted Pod Security label, a minimal Role and a default-deny NetworkPolicy. Show one rejected Pod, one denied connection and one allowed connection, and explain how you knew NetworkPolicy was enforced.

**Pass criteria:** Each restriction is demonstrated by a failing action and a succeeding action; the enforcement test of the network plugin is recorded; no wildcard or cluster-admin permissions were granted; the namespace is cleaned up.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-078 — Apply a baseline access model** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-078).

Evidence to record: manifests, command transcripts showing denial and success, and a note on NetworkPolicy enforcement. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
