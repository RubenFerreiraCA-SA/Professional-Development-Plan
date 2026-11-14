# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-006**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-006](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-02-P — CONTAINERS AND DOCKER — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Security posture of a container (rootful versus rootless engines, non-root `USER`, the `docker` group and `docker.sock` risk, capabilities, read-only filesystems), resource limits and restart behaviour (including proving an OOM kill), image engineering rules, image identity (local image ID, tag, registry digest), supply-chain evidence (SBOM, scanning the deployed digest, signing limits) and the runtime contract with a graceful-shutdown drill.

**Out of scope:** Isolation internals (user namespaces, seccomp profiles, sandboxed runtimes), reproducible-build theory and fleet-wide policy (`DEV-02-E`), and basic container or Compose usage (`DEV-02-B`, `DEV-02-I`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Assess the security posture of a container: explain why membership of the `docker` group and mounting `/var/run/docker.sock` are effectively host root, and apply a non-root `USER`, dropped capabilities, `no-new-privileges`, a read-only root filesystem with explicit writable paths and no `--privileged`.
2. Set memory and CPU limits and a restart policy, verify they are actually applied by the engine (`docker inspect`), and prove an out-of-memory kill by retaining memory in the process and reading `State.OOMKilled` and exit code 137.
3. Keep local image ID, tag and registry manifest digest distinct, record the chain commit → image ID → registry digest, deploy by digest rather than `:latest`, and apply image rules (multi-stage, pinned base, locked dependencies, build secrets, one process per container, logs to stdout/stderr).
4. Produce an SBOM and scan the exact digest you deploy, interpret findings with judgement (runtime versus build stage, reachability, compensating controls), and state what image signing proves and does not prove.
5. Write a runtime contract (user, capabilities, secrets, writable paths, signals and shutdown, health endpoints, limits, registry trust) and demonstrate a graceful-shutdown drill that drains an in-flight request before the deadline.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-02-P — Containers and Docker — Professional](../../../5%20Textbook/Master%20Textbook.md#t-dev-02-p)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-02` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Containers and Docker — Professional** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Show the before/after of a hardened image: base pinned by version and digest, non-root user (`docker run --rm <image> id`), `--cap-drop ALL`, `--read-only` with a tmpfs for `/tmp`, `no-new-privileges`, and a memory limit. Prove each setting with `docker inspect` output.
2. Prove an OOM kill: run a memory-retaining process under a low `--memory` limit and show `State.OOMKilled=true` and exit code 137. Explain why writing to `/dev/null` would not have triggered it.
3. Record the identity chain for one image: git commit, local image ID, tag, and registry digest after pushing to a registry (a local `registry:2` is acceptable). Run the container by digest.
4. Generate an SBOM and a vulnerability scan for that digest. Choose two findings: classify one as relevant and one as not relevant to this workload, with evidence, and name the compensating control you rely on.
5. Write the runtime contract and run a shutdown drill with `docker stop -t 10` during a request in flight; show the application exiting before the deadline with the request completed.
6. Answer in writing: what does a Cosign signature prove about a digest, and what does it not prove?

**Pass criteria — all of the following must hold:**

- Each hardening control is verified by an inspected value, not asserted. If Compose ignores a limit locally, the gap is recorded and shown with `docker run`.
- The OOM proof shows `OOMKilled` and exit code 137, and the explanation covers resident memory.
- The identity chain is complete and the container is run by digest; `:latest` is not used.
- Findings are judged by reachability and layer (runtime or build stage), and the scan targets the deployed digest.
- The contract covers all listed items, the drill output shows a clean drain, and the signing answer states that signatures do not prove the code is safe or that a scan happened.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-007 — Harden and identify the application image** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-007).

Evidence to record: before/after image properties, the OOM proof, the identity chain, SBOM/scan results for the digest and the runtime contract, plus every item under *Completion criteria* on that project step. Record **PRJ-007** as **Completed** in your progress record before opening the next module.
