# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-079**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-079](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-079](../../../4%20Project%20Document/Project.md#prj-079).

## MODULE PLT-03-E — KUBERNETES SECURITY AND POLICY — EXPERT

### 1. Topic and Scope

**In scope for this level:** Evaluating multi-tenant and policy lifecycle trade-offs. You build a threat model for a cluster, analyse privilege-escalation paths (for example create-Pod to read-Secret), design policy-engine rollout at scale, weigh runtime detection and sandboxed runtimes, and reason about workload identity and zero trust.

**Out of scope:** Basic RBAC and Pod Security usage (Beginner to Intermediate), writing individual policies (Professional), tooling-specific tutorials and compliance certification.

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-03--kubernetes-security-and-policy) when this matches your current ability: *Evaluate multi-tenant and policy lifecycle trade-offs.* Typical starting point: You can enforce policy and want to judge whether a framework, tenancy model or runtime defence is adequate.

### 2. Learning Objectives

1. Build a threat model for a shared cluster listing assets, adversaries, entry points and one control for each, and rank the risks.
2. Explain why the permission to create Pods in a namespace is effectively access to every Secret and ServiceAccount token there, and list the controls that reduce that exposure.
3. Compare admission policy, NetworkPolicy, RBAC, namespace tenancy and audit logging by what each prevents, detects or cannot see, and show where they overlap.
4. Evaluate the maintenance risk of a policy framework (exceptions, versioning, test coverage, false positives, owner fatigue) and design a lifecycle for it.
5. Prepare the evidence needed for **PRJ-080**: a written critique of a policy framework comparing admission, NetworkPolicy, RBAC, tenancy, audit and maintenance risk.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-03-E — Kubernetes Security and Policy — Expert](../../../5%20Textbook/Master%20Textbook.md#t-plt-03-e) — Read the cluster threat model, escalation analysis, policy engine design at scale, runtime security, isolation strength, identity and zero trust, and the failure catalogue.

Optional enrichment: the mentoring prompts at the end of the same section. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** A company wants to host three teams plus a vendor in one cluster. Recommend a tenancy and policy model, name the strongest attack path that remains, and state which controls you would pay to add first.

**Pass criteria:** The threat model is specific to the scenario; the escalation reasoning is correct; trade-offs include operational cost; at least one control is explicitly rejected with reasons; the recommendation names what it does not protect against.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-080 — Critique a policy framework** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-080).

Evidence to record: a ranked threat model, a control-coverage matrix and a policy-lifecycle plan with owners. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
