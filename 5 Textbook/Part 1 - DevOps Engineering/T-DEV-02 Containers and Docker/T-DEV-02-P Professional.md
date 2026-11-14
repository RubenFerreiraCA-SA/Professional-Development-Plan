# T-DEV-02-P — Professional Engineering

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-p"></a>
#### T-DEV-02-P — Professional Engineering

**Security posture of a container.** The shared-kernel model is powerful and leaky: a kernel vulnerability, a privileged container or access to the container runtime socket can defeat isolation.

| Pattern | Meaning |
| --- | --- |
| Rootful engine, container runs as `root` | Broad privileges inside the shared-kernel model |
| Non-root `USER` in the image | Smaller blast radius after compromise; still not a VM boundary |
| Rootless engine | The daemon runs unprivileged; port and filesystem semantics change |
| Membership of the `docker` group | On typical rootful installs, effectively root on the host |

Never mount `/var/run/docker.sock` into a service for convenience; it grants control of the host's container engine. Run as a non-root user, drop capabilities, use a read-only root filesystem where possible (with explicit writable volumes), avoid `--privileged`, and set resource limits.

**Resource limits and restart behaviour.** Set memory and CPU limits and a restart policy. Compose `deploy.resources` is interpreted differently across engines; if limits are ignored locally, demonstrate them with `docker run --memory 256m` and record the gap rather than shipping unverified configuration. To prove an out-of-memory kill, allocate and *retain* memory in the process (writing to `/dev/null` does not grow resident memory) and inspect `State.OOMKilled`.

**Image engineering rules**

- Use multi-stage builds; the runtime stage should contain only runtime needs.
- Pin base images by version, and by digest for releases.
- Install dependencies from pinned, reproducible inputs.
- Keep secrets out of build arguments, layers and the build context; use build secrets (`RUN --mount=type=secret`) when a build needs one.
- One process concern per container; log to standard output and error.
- Prefer minimal runtime bases, and keep the number of installed packages low.

**Identity: tags lie.** Keep three identifiers distinct.

| Identifier | What it is | When you have it |
| --- | --- | --- |
| Local image ID | Content-addressed ID on this engine | Immediately after build |
| Tag | A mutable name (`:1.2.0`, `:latest`) | Whenever you name an image |
| Registry manifest digest | Digest of the image as stored in a registry (`repo@sha256:…`) | After push or pull |

A freshly built, never-pushed image usually has no `RepoDigests` entry. Record the chain *commit → local image ID → registry digest*, deploy by digest, and never rely on `:latest` in production.

**Supply chain.** Generate a software bill of materials (SBOM) and scan the *same artifact you deploy*, preferably by registry digest after push. Interpret results with judgement:

| Question | Why it matters |
| --- | --- |
| Is the package in the runtime image or only the build stage? | Build-stage-only findings do not ship |
| Is there a plausible exploit path for this workload? | A version match is not a reachable vulnerability |
| What compensating control exists? | Network policy, non-root user, read-only filesystem — none are magic |
| Which digest was scanned? | Scanning one build and deploying another proves nothing |

Image signing (for example Sigstore's Cosign) proves who signed which digest under a key or identity model. It does not prove the code is correct, the Dockerfile is safe or a scan occurred. Combine signing with review, CI policy and digest-based promotion.

**Runtime contract document.** Record: user and capabilities, secrets handling, writable paths, signals and shutdown behaviour, health endpoints, resource limits and registry trust. Include a newcomer section: how to build, run, test, and read logs.

**Graceful shutdown drill.** Send `SIGTERM` to the container (`docker stop -t 10`) while a request is in flight and confirm the process drains and exits before the deadline. If it does not, fix signal handling or the entrypoint before calling the image production-ready.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See why a container died | `docker inspect`, `docker events`, exit code, OOM flag | Restarting until it looks fine |
| Shrink and harden an image | Multi-stage, `.dockerignore`, non-root, fewer packages | Building and running as root |
| Debug "connection refused" | Who is localhost? DNS name? Published ports? | Opening every port |
| Keep data | Named volumes plus a backup story | Trusting the writable layer |
| Trust what you deploy | Digest, commit and a scan of that digest | Deploying `:latest` |
| Prove readiness | Separate `/health` and `/ready`, authenticated query | Treating a TCP connect as ready |
