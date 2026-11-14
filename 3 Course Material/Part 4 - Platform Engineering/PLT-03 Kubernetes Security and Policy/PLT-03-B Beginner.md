# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-076**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-076](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-076](../../../4%20Project%20Document/Project.md#prj-076).

## MODULE PLT-03-B — KUBERNETES SECURITY AND POLICY — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Vocabulary and first practice for cluster access. You answer the three questions every API request faces (who are you, what may you do, is the object acceptable), read Roles, ClusterRoles and bindings, use `kubectl auth can-i`, explain what a Namespace does and does not isolate, and recognise the basic Pod hardening settings.

**Out of scope:** Creating unprivileged user credentials, quotas and NetworkPolicy (Intermediate), admission policy engines (Professional), threat modelling and multi-tenancy trade-offs (Expert), and the Harbour boundary-mapping steps (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-03--kubernetes-security-and-policy) when this matches your current ability: *Explain namespaces, RBAC and Pod Security basics.* Typical starting point: You know a cluster has users and namespaces but cannot say how an API request is authorised.

### 2. Learning Objectives

1. State the order of authentication, authorisation and admission for an API request and give one example of a denial at each stage.
2. Read a Role and RoleBinding and say precisely which verbs on which resources in which namespace they grant.
3. Use `kubectl auth can-i` (including `--as`) and a real request to prove what a ServiceAccount can and cannot do.
4. Explain why a Namespace scopes names and RBAC but is not a security boundary by itself, naming what must be added (quotas, network policy, Pod Security).
5. Prepare the evidence needed for **PRJ-077**: a map of namespaces, identities and resource ownership for the Harbour platform with the access each identity has.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-03-B — Kubernetes Security and Policy — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-plt-03-b) — Read the three request questions, the RBAC vocabulary, the first Role, proving access with commands, the namespace caveat and the Pod hardening basics.

Optional enrichment: the exercise in the same chapter that creates a read-only Role and proves it with `can-i`. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** On a practice cluster, create a namespace, a read-only Role and a RoleBinding for a ServiceAccount. Prove with `kubectl auth can-i` and a real call what is allowed and what returns Forbidden, and list three things the namespace alone does not protect.

**Pass criteria:** The Role grants exactly the intended verbs and no more; one allowed and one denied action are demonstrated with output; the limits of a namespace are named correctly; no cluster-admin binding was used for the test identity.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-077 — Identify cluster access boundaries** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-077).

Evidence to record: an access-boundary map (namespaces, identities, owners), `can-i` and real-request transcripts, and a list of what is not isolated. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
