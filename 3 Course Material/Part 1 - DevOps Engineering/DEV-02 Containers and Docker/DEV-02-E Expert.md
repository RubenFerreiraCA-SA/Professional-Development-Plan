# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-007**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-007](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-02-E — CONTAINERS AND DOCKER — EXPERT

### 1. Topic and Scope

**In scope for this level:** Where the isolation boundary really is (user namespaces, seccomp, AppArmor/SELinux, capability dropping, sandboxed runtimes and micro-VMs); failure modes (zombie processes, ignored `SIGTERM`, disk exhaustion, noisy neighbours, cache poisoning, secrets in layers, registry deletion); reproducible builds; layer and cache economics; and policy enforcement for fleets of images (CI, registry and admission).

**Out of scope:** Introductory container concepts, Compose and single-image hardening (`DEV-02-B`, `DEV-02-I`, `DEV-02-P`), and implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Evaluate the container isolation boundary: explain what user namespaces, seccomp, Linux security modules and capability dropping each reduce, and decide by threat model when a sandboxed runtime or lightweight VM is justified.
2. Catalogue container failure modes (zombie accumulation, ignored `SIGTERM`, disk exhaustion from logs and layers, noisy neighbours, cache poisoning, secrets baked into layers, registry deletion) with a mechanism and a mitigation for each.
3. Design for reproducible builds: pin base images by digest, lock dependencies with hashes, avoid fetching `latest` during builds, normalise timestamps (`SOURCE_DATE_EPOCH`), and state the practical target (same behaviour, ability to rebuild a past release).
4. Reason about layer and cache economics: ordering instructions by change frequency, cache mounts, separating dependency resolution from code copy, and why deleting a file in a later layer neither shrinks the image nor removes it from earlier layers.
5. Design fleet policy enforced at several points (CI linter and scanner, registry policy for signed images and retention, orchestrator admission for digest-only, non-root, trusted registries) and a recovery plan for the loss of the registry that holds release digests.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-02-E — Containers and Docker — Expert](../../../5%20Textbook/Master%20Textbook.md#t-dev-02-e)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-02` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Containers and Docker — Expert** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write a threat-model comparison of three runtime configurations for a service that runs untrusted code: default runc, hardened runc (non-root, dropped caps, seccomp, read-only filesystem) and a sandboxed runtime or micro-VM. State what each does and does not protect and the cost.
2. Take three failure modes from the catalogue and reproduce or reason through each: give the observable symptom, the diagnostic command, the mitigation and the evidence that the mitigation worked.
3. Rebuild the same commit twice with `--no-cache`. Compare image IDs and behaviour, list every source of difference you find (timestamps, unpinned packages, base image drift) and the control that removes it.
4. Demonstrate that deleting a secret in a later layer leaves it recoverable from the earlier layer (on a throwaway image with a fake secret), and show the correct alternative (`RUN --mount=type=secret`).
5. Write a fleet policy table: for each rule (non-root, pinned digest, scanned, signed) name the enforcement points (CI, registry, admission) and what each point catches that the earlier ones miss. Add a registry-loss recovery plan.
6. Mentoring prompts, answered in writing: why is `docker` group membership a privilege-escalation path; when is a scanner's "critical" irrelevant and what evidence defends that; what does your organisation lose if the registry holding every release digest is deleted?

**Pass criteria — all of the following must hold:**

- The threat-model comparison ties each isolation mechanism to a specific attack class and names a real cost (performance, compatibility, operations).
- Failure-mode work includes observed or logically derived symptoms and a verification of the mitigation.
- Reproducibility differences are identified from evidence and each is matched to a pinning or normalising control; absolute bit-for-bit identity is not claimed without proof.
- The layer demonstration extracts the "deleted" secret and the fix uses a build secret.
- The fleet policy explains why multiple enforcement points are complementary, and the recovery plan includes mirroring or backup of release images.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-008 — Investigate failure and portability** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-008).

Evidence to record: the isolation comparison, the fault-injection record, the reproducibility experiment and the fleet policy ADR, plus every item under *Completion criteria* on that project step. Record **PRJ-008** as **Completed** in your progress record before opening the next module.
