# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-004**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-004](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-02-B — CONTAINERS AND DOCKER — BEGINNER

### 1. Topic and Scope

**In scope for this level:** What a container is (a process with restricted visibility and resource use sharing the host kernel), images and layers, the writable container layer, the first Docker commands, a minimal Dockerfile, layer-cache ordering and the `localhost` pitfall inside a container.

**Out of scope:** Multi-stage builds, Compose, PID 1 and signal handling, hardening, image signing and runtime isolation internals. These belong to `DEV-02-I`, `DEV-02-P` and `DEV-02-E`; step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Explain a container as a process (tree) with namespaces limiting what it can see, cgroups limiting what it can use, and a shared host kernel, and say why that makes it different from a virtual machine.
2. Distinguish an image (immutable layers plus configuration such as entrypoint, environment and user) from a container (an image plus a thin writable layer), and state what happens to data when the container is removed.
3. Use `docker run --rm -p`, `docker ps`, `docker logs`, `docker exec`, `docker stop` and `docker images` correctly, and explain what `docker stop` sends (SIGTERM, then SIGKILL after a grace period).
4. Read and write a minimal Dockerfile (`FROM`, `WORKDIR`, `COPY`, `RUN`, `USER`, `EXPOSE`, `CMD`), explain why dependency files are copied and installed before source code (layer cache), and build, run and health-check the image.
5. Explain why `127.0.0.1` inside a container is the container itself, and prepare the evidence for **PRJ-005** (a container definition for a small web service that starts and answers a health request).

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-02-B — Containers and Docker — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-dev-02-b)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-02` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Containers and Docker — Beginner** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Write a Dockerfile for a small web application (any language), build it, run it with a published port and show `curl -fsS http://127.0.0.1:<port>/health` succeeding. Paste `docker ps` and `docker logs` output.
2. Edit one source file and rebuild twice: once with dependency installation placed before `COPY . .` and once after. Show which build steps were cached and explain the difference in two sentences.
3. Create a file inside a running container with `docker exec`, remove and recreate the container, and show the file is gone. Name two ways to keep data that must survive container replacement.
4. Time `docker stop` on your container. Explain what the time tells you about signal handling and which signal was sent first.
5. Answer in writing: from inside container A, can `curl http://127.0.0.1:5432` reach a database in container B? Why or why not, and what name would you use on a user-defined network?

**Pass criteria — all of the following must hold:**

- The Dockerfile builds, the service answers the health request, and the evidence includes real command output.
- The cache comparison correctly identifies that ordering dependencies first avoids reinstalling on source edits.
- The writable-layer demonstration shows data loss on removal, and the answer names a named volume or an external service.
- The stop-time explanation links ~10 seconds to a process ignoring SIGTERM (or a fast stop to graceful handling).
- The `localhost` answer states it refers to the container itself and names service-name DNS on a user-defined network.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-005 — Containerise the sample service** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-005).

Evidence to record: the Dockerfile, the build and run output and the health-check response, plus every item under *Completion criteria* on that project step. Record **PRJ-005** as **Completed** in your progress record before opening the next module.
