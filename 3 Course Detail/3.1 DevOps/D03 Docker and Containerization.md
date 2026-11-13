# D03 — Docker and Containerization

| | Details |
| --- | --- |
| **Estimated study time** | 28–40 hours |
| **Prerequisites** | [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md), [D02 — Advanced Git](D02%20Advanced%20Git.md), Linux processes and networking, and experience building a web service. |

## Objective

Engineer **reproducible, secure and operable container workloads** rather than merely learning Docker commands. Understand the isolation model, build pipeline, runtime failure modes and security boundaries that a Platform Engineer must account for when providing a container-based developer platform.

Use the same application throughout: an API with a database and, optionally, a small frontend. Select a familiar stack; the engineering decisions matter more than the programming language.

## Outcomes

1. Explain namespaces, cgroups, image layers, container processes and the shared-kernel security model.
2. Produce small, repeatable, multi-stage images with explicit runtime dependencies, a non-root identity and a sensible signal-handling strategy.
3. Evaluate supply-chain risk using image provenance, dependency inventories, vulnerability scanning and pinned base-image references.
4. Debug container networking, DNS, health checks, resource limits, file permissions and persistent storage.
5. Design a Compose environment with isolated services, secrets handling, readiness controls and reproducible startup/teardown.
6. Publish and inspect versioned images, then define the runtime contract needed by Kubernetes and later platform services.

## Learning and engineering activities

| Activity | Estimated hours |
| --- | ---: |
| Isolation model, Docker engine and runtime investigation | 4–5 |
| Image engineering, reproducibility and build optimisation | 6–8 |
| Network, storage and process troubleshooting | 5–7 |
| Supply-chain security and runtime hardening | 5–8 |
| Multi-service platform contract and Practical Assessment | 8–12 |
| **Working estimate** | **28–40** |

These are planning estimates, **not time-boxes**. Stop only when the practical acceptance criteria are met. Cloud expenditure, extra reading and remediation can increase actual effort.

## 1. Understand the container execution model

Explore **process isolation, not virtual-machine emulation**:

- Use `docker inspect`, `docker top`, `docker stats`, `docker events` and `docker info` to understand the engine and workloads.
- Compare PID, mount, network and user namespaces; explain how cgroups constrain CPU and memory.
- Demonstrate that a container has a root filesystem assembled from image layers plus a writable layer. Explain why ephemeral runtime data should not be stored there.
- Investigate PID 1, signal delivery, graceful shutdown and zombie reaping. Decide whether the application handles signals itself or requires a minimal init process.
- Compare rootless Docker, non-root container users, user namespace remapping and Docker socket access. Explain why a user in the `docker` group can effectively obtain broad host privileges on typical rootful installations.

**Experiment:** Run a container with a deliberately low memory limit, drive its memory usage past the limit and inspect exit status, OOM evidence and restart behaviour. Use a disposable service. Distinguish application crashes, health-check failures and memory termination.

## 2. Build secure, reproducible images

Build an application using a **multi-stage Dockerfile**. The build stage installs dependencies and produces artifacts; the runtime stage contains only what is needed to run.

Required decisions:

- Use a supported, maintained base image. Pin a digest for reproducibility and document how it will be updated; digest pinning does not replace patch management.
- Choose a runtime user and file ownership deliberately. Avoid capabilities and writable paths unless necessary.
- Use a reproducible package install (lockfile and deterministic install mode). Compare build-cache behaviour when code changes versus when dependency manifests change.
- Configure `WORKDIR`, `USER`, a sensible `ENTRYPOINT`/`CMD`, a `.dockerignore` and signal-aware application shutdown.
- Prevent credentials from entering build arguments, layers, logs and image history. Use BuildKit secret mounts for build-time secrets if necessary.
- Compare Dockerfile `HEALTHCHECK` with application readiness: a healthy process is not automatically ready to accept traffic.

**Investigation commands:**

```bash
docker build -t platform-api:local .
docker image inspect platform-api:local
docker history platform-api:local
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges platform-api:local
```

The last command is a **hardening test**, not a universal run command. Add narrowly scoped writable mounts, user permissions or allowed capabilities only if your application's actual requirements justify them. Record failures and remedies.

**Performance requirement:** Compare a naive image and the improved version: size, number of packages, build time with warm and cold caches and vulnerability findings. An arbitrary percentage reduction is less important than repeatability and a defensible design.

## 3. Diagnose networking and persistence

Build a controlled test environment with an API and database on a dedicated network.

Investigate:

- Bridge networking, service-name DNS, host-to-container port publishing and differences between `127.0.0.1` inside a container and on the host.
- Network segmentation and attack surface: the database need not expose a host port.
- Bind mounts versus named volumes; ownership, durability and the distinction between backup and persistence.
- Layered configuration: environment variables, mounted config files and secrets; a `.env` file is **not** a secure secret store.
- Readiness and startup ordering: `depends_on` ordering alone does not guarantee a usable dependency; use health checks and resilient client retries.

**Failure drills:** break DNS resolution, stop the database, remove the volume in a disposable environment and restrict filesystem permissions. Capture symptoms, diagnostics and corrective action. Confirm data survives container replacement **when the volume is retained**, but not deletion of the actual volume.

## 4. Container supply-chain and runtime security

Trace a container image from source commit to registry and runtime:

- Produce a dependency inventory or **SBOM** (for example using Syft) and evaluate vulnerabilities using a scanner (for example Trivy or Grype).
- Differentiate a finding with a reachable exploit path from a package-version match; apply severity, exploitability and compensating-control reasoning.
- Compare mutable tags with immutable digests. Document the image digest that was scanned and the digest that was deployed.
- Assess image-signing and verification options (for example Sigstore/Cosign), and what signatures do **not** prove.
- Explain the threat posed by privileged containers, mounting `/var/run/docker.sock`, running as root, host networking and broad filesystem permissions.
- Discuss registry permissions, retention, credentials, rate limits and image updates.

**Exercise:** Introduce a known vulnerable dependency in a disposable test image, demonstrate a scanner finding, patch it and record before/after results. Do not intentionally deploy vulnerable code to public services.

## 5. Orchestrate a realistic local stack

Create a Compose-based development environment consisting of an API, a database and optionally a frontend/worker:

- Use distinct networks if different tiers have different trust requirements.
- Add health checks, resource limits where your engine supports them, safe restart behaviour and persisted database data.
- Keep environment-specific configuration outside the image, with a documented `.env.example` using fake placeholders.
- Make a new developer's first run repeatable and provide `up`, `down`, logs, troubleshooting and cleanup instructions.
- Version the application image with a meaningful immutable identifier and push a **non-secret** sample to a registry.
- Compare Compose's local orchestration scope with what Kubernetes must later add: scheduling, service discovery, controllers, readiness and workload identity.

## Practical Assessment — production-ready container contract

**Scenario:** Another team wants to deploy your API without knowing its framework or runtime internals. Deliver an artifact and operating instructions that let that team build, run, validate, troubleshoot and replace it.

**Required evidence:**

1. Repository changes containing a multi-stage Dockerfile, `.dockerignore`, Compose stack, health endpoint and reproducible build instructions.
2. A published image reference including its **digest**, plus a build/release trace to the originating commit.
3. A before/after image comparison and an SBOM or documented dependency inventory with vulnerability review.
4. Successful demonstration of isolated database networking, persistence across application replacement and a clean startup.
5. A failure drill covering at least two of: broken connectivity, exhausted memory, read-only filesystem, unready database, lost volume or failed shutdown.
6. A short design record covering non-root execution, secrets, writable storage, signals and registry trust.

**Acceptance:** A second developer can reproduce the stack and its key failure tests using only the repository instructions. The image is non-root by default; exceptions are explicit and justified. Do not claim production readiness solely because the container starts.

## Further study

- [Docker — Build best practices](https://docs.docker.com/build/building/best-practices/)
- [Docker — Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker — Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [Docker — Container security](https://docs.docker.com/engine/security/)
- [OCI image specification](https://github.com/opencontainers/image-spec)
- [SLSA supply-chain framework](https://slsa.dev/)

**Textbook:** [Chapter 3 — Docker and Containerization](../../4%20Study%20Materials/4.1%20DevOps/D03%20Docker%20and%20Containerization.md)

**Previous:** [D02 — Advanced Git](D02%20Advanced%20Git.md) · **Next:** [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md)
