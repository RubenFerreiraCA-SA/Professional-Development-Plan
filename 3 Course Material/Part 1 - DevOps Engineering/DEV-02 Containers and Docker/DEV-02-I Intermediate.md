# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-005**.

The gate is satisfied only when **each** required project step is recorded in your progress record as **Completed**, or as **Out of scope**. A step may be recorded **Out of scope** only when the *whole optional track* that contains it (for example Datadog or AI) was excluded in your personal PDP. You may never skip, bypass or mark Out of scope an individual step inside a track that is active in your PDP.

If any required step is neither **Completed** nor validly **Out of scope**, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record the result, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-005](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE DEV-02-I — CONTAINERS AND DOCKER — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** PID 1 and signal handling (exec versus shell form, `tini`), multi-stage builds and `.dockerignore`, Compose as a local contract (networks, `env_file`, healthchecks, `depends_on` with `service_healthy`), health versus readiness, persistence options (writable layer, named volume, bind mount) and diagnosing connectivity and exit-code failures.

**Out of scope:** Security hardening, image identity by digest, SBOM/scanning and signing (`DEV-02-P`), and isolation boundaries, reproducible builds and fleet policy (`DEV-02-E`). Step-by-step instructions belong only in the Project Document.

### 2. Learning Objectives

1. Explain PID 1 behaviour in a container (signal defaults, orphan reaping), why shell-form `CMD` can prevent `SIGTERM` reaching the application, and fix it with exec form, application signal handling or an init process such as `tini`.
2. Build a multi-stage image that keeps compilers and package managers out of the runtime stage, and use `.dockerignore` to keep `.git`, `.env` and virtual environments out of the build context.
3. Write a Compose file that runs an API with a database on a private network: service-name DNS, an unpublished database port, a gitignored `env_file`, `${VAR:?message}` for required secrets, a database healthcheck and `depends_on: condition: service_healthy`.
4. Distinguish `/health` (process alive) from `/ready` (dependencies work), explain why a TCP connect is not readiness, and choose the right persistence mechanism (writable layer, named volume or bind mount) for a stated need.
5. Diagnose "connection refused" and early container exits using `docker compose ps/logs`, `docker exec ... getent hosts`, `docker inspect` (`ExitCode`, `OOMKilled`) and exit code 137, and prepare the evidence for **PRJ-006**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-DEV-02-I — Containers and Docker — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-dev-02-i)

Optional enrichment: the decision guide or mentoring prompts at the end of the same topic chapter, and the adjacent level of `DEV-02` if a term in this level is unfamiliar. Optional reading never replaces the required section above.

### 4. Knowledge Assessment

Complete **all** of the following tasks for **Containers and Docker — Intermediate** in your own words, without undocumented help, and keep the outputs with your progress record.

1. Take a Dockerfile using shell-form `CMD` and demonstrate that `docker stop` takes about the full grace period; fix it (exec form, signal handler or `tini`) and show the improved stop time.
2. Convert a single-stage Dockerfile to multi-stage. Report image sizes before and after and list what is absent from the runtime stage. Show the `.dockerignore` and prove `.env` is not in the build context.
3. Run a Compose stack with an API and Postgres. Show `docker compose ps` with the database healthy, `/health` and `/ready` responses, then stop `db` and show how both endpoints behave. Restart it and show recovery.
4. Introduce "connection refused" by setting the database host to `localhost`. Diagnose it with at least three commands, write the cause, the fix and one prevention measure.
5. Delete and recreate the `api` container and show that data stored in the named volume survived, while a file written to the container's writable layer did not.

**Pass criteria — all of the following must hold:**

- The signal-handling fix produces a measurably faster stop and the explanation names PID 1 and `SIGTERM`.
- The runtime image excludes build tools; the build context excludes secrets; sizes are reported with real numbers.
- The readiness endpoint performs a real dependency query; behaviour during a database outage matches the explanation.
- The diagnosis uses evidence (DNS lookup, container status, logs) rather than guessing, and states cause, fix and prevention.
- Persistence behaviour is demonstrated for both the volume and the writable layer.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-006 — Run the service with a dependency** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-006).

Evidence to record: the Compose file, the successful startup output and the written diagnosis of a deliberate connectivity failure, plus every item under *Completion criteria* on that project step. Record **PRJ-006** as **Completed** in your progress record before opening the next module.
