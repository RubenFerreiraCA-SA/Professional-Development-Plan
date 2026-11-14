# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-078**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-078](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-078](../../../4%20Project%20Document/Project.md#prj-078).

## MODULE PLT-03-P — KUBERNETES SECURITY AND POLICY — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing least-privilege and enforceable policy. You use admission-time policy (ValidatingAdmissionPolicy, Kyverno or Gatekeeper) to reject unsafe objects, test policies before enforcing them, define baseline rules, plan secrets handling, restrict images to approved sources, design a tenancy template, and keep audit evidence.

**Out of scope:** Creating basic Roles and quotas (Intermediate), threat modelling, runtime detection and sandbox-runtime trade-offs (Expert), and the Harbour denial demonstration steps (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-03--kubernetes-security-and-policy) when this matches your current ability: *Design least-privilege and enforceable cluster policy.* Typical starting point: You can apply controls by hand and now need to make them automatic, testable and auditable.

### 2. Learning Objectives

1. Write an admission policy that rejects a privileged container or a mutable `latest` image tag, and explain why enforcing at admission catches what CI missed.
2. Run a policy in audit or warn mode first, review its results, then switch to enforce, and describe how you would prevent breaking existing workloads.
3. Define a baseline rule set (non-root, no privilege escalation, dropped capabilities, approved registries, resource limits) and map each rule to the risk it reduces.
4. Design a per-tenant namespace template with quota, LimitRange, default-deny NetworkPolicy, restricted Pod Security and a scoped RoleBinding, and name its residual gaps.
5. Prepare the evidence needed for **PRJ-079**: one recorded access or admission denial with the exact error message and an explanation of which rule caused it.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-03-P — Kubernetes Security and Policy — Professional](../../../5%20Textbook/Master%20Textbook.md#t-plt-03-p) — Study policy as code at admission, typical baseline rules, securing the control plane and nodes, secrets management, supply chain at the cluster, tenancy and auditing evidence.

Optional enrichment: the decision guide in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Install or enable one admission policy mechanism on a practice cluster. Submit an unsafe Deployment, capture the rejection, fix the manifest, show it admitted, and describe how the policy is versioned, tested and rolled out progressively.

**Pass criteria:** The denial message is captured verbatim and explained; the fixed manifest is admitted; audit-before-enforce is described; a bypass or gap is identified honestly; no real credentials appear in the evidence.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-079 — Demonstrate a denied unsafe request** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-079).

Evidence to record: the policy source, a denial transcript, the corrected manifest and a short rollout plan for the policy. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
