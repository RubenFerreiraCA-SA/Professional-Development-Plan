# Chapter 3 — Docker and Containerization (D03)

*DevOps Engineering textbook · Chapter 3 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D03 course detail](../../3%20Course%20Detail/3.1%20DevOps/D03%20Docker%20and%20Containerization.md) for the current planning estimate (about 28–40 hours). |
| **Prerequisites** | [D01](D01%20Repository%20Fundamentals.md), [D02](D02%20Advanced%20Git.md), comfort with Linux processes and basic networking, and experience building a web service. |

## How to study this chapter

The purpose of this chapter is not to memorise Docker flags. It is to engineer a **reproducible, secure and operable container contract** that another team can build, run, troubleshoot and replace without knowing your framework internals.

Work through the sections in order. Each one follows **Concept → Worked example → Practice → Verify → Reflect**. Every section adds something to the same running project: **Harbour API** inside the `harbour-platform` repository from D01.

This text teaches the requirements in [D03 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D03%20Docker%20and%20Containerization.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) acceptance criterion for D03 is the integration bar: *someone unfamiliar with the stack builds and runs the service from repo instructions alone, gets a healthy response, and the image they run is identified by digest.*

> **Safety boundary:** Use disposable local resources and fabricated secrets only. Do not mount the Docker socket into workloads, do not run privileged containers for “convenience,” and do not push images that contain credentials. Prefer a local registry or a private training namespace.

### Learning outcomes

By the end of this chapter you should be able to:

1. Explain namespaces, cgroups, image layers, container processes and the shared-kernel security model with runtime evidence.
2. Produce small, repeatable, multi-stage images with locked dependencies, a non-root identity and sensible signal handling.
3. Evaluate supply-chain risk using provenance, SBOMs, vulnerability scanning and digest-pinned references.
4. Debug networking, DNS, health checks, resource limits, permissions and persistence.
5. Design a Compose stack with isolated services, readiness controls and reproducible startup/teardown.
6. Publish and inspect versioned images and document the runtime contract later modules (CI/CD, GitOps, Kubernetes) will consume.

### Before you begin

```bash
docker version
docker compose version
git -C "${HARBOUR_ROOT:-$HOME/harbour-platform}" rev-parse --show-toplevel 2>/dev/null || echo "Set HARBOUR_ROOT to your D01 training repo"
```

If Docker is missing, install an engine appropriate for your OS (Docker Engine, Docker Desktop, or a compatible alternative such as Colima + Docker CLI). The examples assume a rootful engine with Compose V2 (`docker compose`). Rootless setups are welcome; note differences when permissions or port publishing behave differently.

Choose a language you already know for Harbour API. The worked examples use **Python 3.12** because it is widely readable. The engineering decisions — multi-stage builds, non-root users, digests, health, networking — transfer to Go, Node, Java and others.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
pwd
```

---

## Section 3.1 — Containers are isolated processes, not tiny VMs

### 3.1.1 The shared-kernel model

A **container** packages a process (or process tree) with a filesystem view, resource limits and network identity. Unlike a virtual machine, it normally shares the **host kernel**. Isolation comes from Linux features:

| Mechanism | What it isolates or limits |
| --- | --- |
| **Namespaces** | What the process can *see* (PID, mount, network, UTS, IPC, user, …) |
| **cgroups** | What resources the process may *consume* (CPU, memory, I/O, …) |
| **Capabilities / seccomp / LSM** | What privileged operations remain possible |

This model is powerful and leaky. A kernel vulnerability, a privileged container, or access to the Docker socket can undermine the illusion of a “safe sandbox.” Platform engineers must design for that reality.

**Worked example — observe a container as a process:**

```bash
docker run --name harbour-sleep -d registry.hub.docker.com/library/busybox:1.36 sleep 3600
docker top harbour-sleep
docker inspect harbour-sleep --format 'Pid={{.State.Pid}} GraphDriver={{.Driver}}'
ps -o pid,ppid,cmd -p "$(docker inspect harbour-sleep --format '{{.State.Pid}}')"
docker rm -f harbour-sleep
```

**What happened?** The container’s main process is a real host PID (in rootful Docker). `docker top` shows processes inside the container’s PID namespace; on the host you still see the runtime’s managed process. There is no separate guest kernel.

### 3.1.2 Image layers and the writable container layer

An **image** is an immutable stack of filesystem layers plus config (entrypoint, env, user, …). A **container** adds a thin writable layer on top. Delete the container and that writable layer is gone unless you persisted data elsewhere.

```bash
docker pull busybox:1.36
docker image inspect busybox:1.36 --format 'Id={{.Id}} Size={{.Size}} RootFS.Layers={{len .RootFS.Layers}}'
docker history busybox:1.36
```

Ephemeral runtime data (caches, temp files, SQLite you care about) must not live only in the writable layer if you expect it to survive replacement.

### 3.1.3 PID 1, signals and shutdown

Process **PID 1** inside a container receives signals differently from a normal Unix process and is responsible for reaping children. If your app ignores `SIGTERM`, orchestrators will eventually `SIGKILL` it.

Decide deliberately:

- Application handles `SIGTERM` and exits promptly, **or**
- A minimal init (e.g. `tini`) is PID 1 and forwards signals.

### 3.1.4 Who is “root,” and who can talk to Docker?

| Pattern | Meaning |
| --- | --- |
| Rootful engine + container `USER root` | Broad privileges inside the shared-kernel model |
| Non-root `USER` in the image | Reduces blast radius after compromise; still not a VM boundary |
| Rootless engine | Daemon runs as an unprivileged user; port and filesystem semantics change |
| Membership of the `docker` group | On typical rootful installs, equivalent to broad host control via the API socket |

**Never** mount `/var/run/docker.sock` into Harbour for convenience. That grants container breakout to host Docker control.

**Practice 1:** Run a container with `--memory=64m`, then drive memory usage (for example a small stress image or a throwaway Python allocator) until it is killed. Record exit code, `docker inspect` OOM fields and whether a restart policy hid the failure.

```bash
docker run --rm --memory=64m --memory-swap=64m busybox:1.36 sh -c 'dd if=/dev/zero of=/dev/null bs=1M'
# or use a dedicated stress tool if available; capture inspect/events output
docker events --since 5m --until 0s 2>/dev/null | tail -n 20 || true
```

**Verify:** You can explain the difference between an application crash, a failed health check and an OOM kill using evidence.

**Reflect:** If a platform offers “just add your Dockerfile,” what default memory/CPU limits and what identity model should it impose — and why?

---

## Section 3.2 — Harbour API: first runnable service

### 3.2.1 Application contract

Harbour API exposes:

| Endpoint | Behaviour |
| --- | --- |
| `GET /health` | Liveness: process is up |
| `GET /ready` | Readiness: dependencies are usable (database when configured) |
| `GET /v1/info` | Small JSON payload identifying the service |

Create the application under `app/`:

```bash
cd "$HARBOUR_ROOT"
mkdir -p app/harbour_api
```

`app/harbour_api/__init__.py` (empty is fine):

```python
# Harbour API package
```

`app/harbour_api/main.py`:

```python
import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

SERVICE_NAME = "harbour-api"
SERVICE_VERSION = os.getenv("HARBOUR_VERSION", "0.1.0")
DATABASE_HOST = os.getenv("DATABASE_HOST", "")
DATABASE_PORT = int(os.getenv("DATABASE_PORT", "5432"))


def database_reachable() -> bool:
    if not DATABASE_HOST:
        return True
    try:
        with socket.create_connection((DATABASE_HOST, DATABASE_PORT), timeout=1.5):
            return True
    except OSError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=SERVICE_NAME, lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/ready")
def ready(response: Response):
    if not database_reachable():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": "unreachable"}
    return {"status": "ready", "database": "ok" if DATABASE_HOST else "unconfigured"}


@app.get("/v1/info")
def info():
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "commit": os.getenv("HARBOUR_COMMIT", "unknown"),
    }
```

`app/requirements.txt` (pin exact versions; regenerate with your tool of choice later):

```text
fastapi==0.115.6
uvicorn[standard]==0.34.0
```

`app/README.md`:

```markdown
# Harbour API

Training service for the Platform Engineering PDP Final Project.

## Local (without Docker)

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn harbour_api.main:app --app-dir . --host 127.0.0.1 --port 8000

## Container

See the repository root `README` / Compose instructions once D03 files are added.
```

Quick sanity check on the host:

```bash
cd "$HARBOUR_ROOT/app"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn harbour_api.main:app --app-dir . --host 127.0.0.1 --port 8000 &
sleep 2
curl -s http://127.0.0.1:8000/health
kill %1 2>/dev/null || true
deactivate
```

Commit the application source (still no Dockerfile):

```bash
cd "$HARBOUR_ROOT"
git add app
git commit -m "feat(app): add Harbour API health and readiness endpoints"
```

---

## Section 3.3 — Image engineering: multi-stage, small, repeatable

### 3.3.1 Why multi-stage builds

A **build stage** contains compilers, headers and package managers. A **runtime stage** should contain only what runs the service. Copying artifacts between stages keeps images smaller, reduces vulnerability surface and makes intent obvious.

### 3.3.2 Dockerfile for Harbour

Create `app/Dockerfile`:

```dockerfile
# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

FROM ${PYTHON_IMAGE} AS build
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM ${PYTHON_IMAGE} AS runtime
ARG HARBOUR_COMMIT=unknown
WORKDIR /srv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HARBOUR_VERSION=0.1.0 \
    HARBOUR_COMMIT=$HARBOUR_COMMIT

RUN useradd --create-home --uid 10001 harbour \
    && mkdir -p /srv \
    && chown -R harbour:harbour /srv

COPY --from=build /opt/venv /opt/venv
COPY --chown=harbour:harbour harbour_api ./harbour_api

USER harbour
EXPOSE 8000
ENTRYPOINT ["uvicorn", "harbour_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `app/.dockerignore`:

```text
.venv
__pycache__
*.pyc
.pytest_cache
.env
.env.*
!.env.example
README.md
Dockerfile*
```

> **Digest pinning:** For real platforms, resolve `python:3.12-slim-bookworm` to a digest (`python@sha256:…`) and document how you refresh it. Tags move; digests do not. Pinning does **not** replace patch management — it makes rebuilds reproducible.

### 3.3.3 Build, inspect, harden-test

```bash
cd "$HARBOUR_ROOT/app"
docker build --build-arg HARBOUR_COMMIT="$(git rev-parse HEAD)" -t harbour-api:local .
docker image inspect harbour-api:local --format 'Id={{.Id}} Size={{.Size}} User={{.Config.User}}'
docker history harbour-api:local
docker run --rm -d --name harbour-api -p 8000:8000 harbour-api:local
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/v1/info
docker rm -f harbour-api
```

**Hardening test** (expect failures until you add justified exceptions):

```bash
docker run --rm --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  -p 8000:8000 harbour-api:local
```

Uvicorn may need a writable temp dir. If it fails, add a narrow `tmpfs` mount in Compose later — do **not** drop `--read-only` without recording why.

**Naive vs improved comparison:** Build a deliberately fat single-stage image (install build tools in runtime, copy venv source trees, run as root) in a throwaway tag `harbour-api:naive`. Compare size, `docker history` length and scanner results (Section 3.5). Prefer a defensible design over chasing an arbitrary percentage reduction.

**Practice 2:** Change only application code and rebuild with BuildKit; then change only `requirements.txt` and rebuild. Explain which layers cache and why lockfiles / ordered `COPY` matter.

**Verify:** `docker image inspect` shows non-root `User`, and `/health` works from a published port.

**Reflect:** What belongs in the image versus configuration injected at runtime? What must CI later prove before anyone trusts `harbour-api:local`?

---

## Section 3.4 — Networking, persistence and a database dependency

### 3.4.1 Compose as a local platform contract

Create `app/docker-compose.yml`:

```yaml
name: harbour

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        HARBOUR_COMMIT: ${HARBOUR_COMMIT:-unknown}
    image: harbour-api:${HARBOUR_TAG:-local}
    user: "10001:10001"
    environment:
      DATABASE_HOST: db
      DATABASE_PORT: "5432"
      HARBOUR_VERSION: "0.1.0"
      HARBOUR_COMMIT: ${HARBOUR_COMMIT:-unknown}
    ports:
      - "8000:8000"
    networks:
      - harbour_app
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
    read_only: true
    tmpfs:
      - /tmp
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: harbour
      POSTGRES_PASSWORD: harbour-training-only
      POSTGRES_DB: harbour
    volumes:
      - harbour_pg:/var/lib/postgresql/data
    networks:
      - harbour_app
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U harbour -d harbour"]
      interval: 5s
      timeout: 3s
      retries: 10
    # No host ports — database stays off the laptop attack surface

networks:
  harbour_app:
    driver: bridge

volumes:
  harbour_pg:
```

Create `app/.env.example` (fabricated values only):

```text
HARBOUR_TAG=local
HARBOUR_COMMIT=replace-with-git-sha
# Compose reads POSTGRES_* from the compose file for training.
# Real secrets belong in a secret manager — never commit .env with production values.
```

Update root or `app` docs so a newcomer can run:

```bash
cd "$HARBOUR_ROOT/app"
export HARBOUR_COMMIT="$(git rev-parse HEAD)"
docker compose up --build -d
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/ready
docker compose ps
docker compose logs api --tail 50
```

### 3.4.2 DNS, localhost and segmentation

On the Compose network, service name `db` resolves to the database container. Inside the API container, `127.0.0.1` is **the API container itself**, not your laptop and not Postgres.

| Destination | From host | From `api` container |
| --- | --- | --- |
| Harbour HTTP | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| Postgres | not published (by design) | `db:5432` |

`depends_on` with `condition: service_healthy` waits for Postgres readiness. Clients should still retry — readiness is not a distributed lock.

### 3.4.3 Volumes versus bind mounts

| Mechanism | Typical use | Survives container delete? |
| --- | --- | --- |
| Writable container layer | Temp only | No |
| Named volume | Database data | Yes, until volume removed |
| Bind mount | Live-editing source in dev | Depends on host path |

**Failure drills (disposable):**

```bash
# 1) Database stopped
docker compose stop db
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/ready
docker compose start db

# 2) Broken DNS / wrong host
docker compose exec api python -c "import socket; print(socket.getaddrinfo('db', 5432))"

# 3) Persistence across API replacement
docker compose up -d --force-recreate api
# volume harbour_pg should still exist:
docker volume ls | grep harbour

# 4) Lost volume (destructive — training only)
docker compose down
# docker volume rm harbour_harbour_pg   # only if you accept data loss
```

**Practice 3:** Remove the database host port if you added one while debugging. Prove the API can still reach `db` and that the host cannot connect to Postgres without `docker compose exec`.

**Verify:** `/ready` returns ready when DB is healthy and 503 when DB is stopped; DB has no published host port.

**Reflect:** Which failure modes should a platform’s default Compose/Helm templates already handle for application teams?

---

## Section 3.5 — Supply chain: SBOM, scan, digest, trust

### 3.5.1 Tags lie; digests identify

```bash
cd "$HARBOUR_ROOT/app"
DIGEST="$(docker image inspect harbour-api:local --format '{{index .RepoDigests 0}}')"
# Local tags may lack RepoDigests until pushed. Prefer:
IMAGE_ID="$(docker image inspect harbour-api:local --format '{{.Id}}')"
echo "Image ID: $IMAGE_ID"
docker build -t harbour-api:local --build-arg HARBOUR_COMMIT="$(git rev-parse HEAD)" .
# After push to a registry:
# docker push your-registry.example/harbour-api:0.1.0
# docker buildx imagetools inspect your-registry.example/harbour-api:0.1.0
```

Record in `docs/decisions/` or release notes:

- Source commit SHA
- Image ID / registry digest
- Scanner results summary
- Who is allowed to publish

Mutable tags (`:latest`, `:local`) are convenient locally and dangerous as deployment pins. Later modules (D04, D06) must promote **digests**.

### 3.5.2 SBOM and vulnerabilities

Install scanners as CLI tools on the host (versions change — follow current project docs):

```bash
# Examples — pick tools available to you:
# syft harbour-api:local -o syft-json > /tmp/harbour-sbom.json
# grype harbour-api:local
# trivy image harbour-api:local
```

Interpret findings with judgement:

| Question | Why it matters |
| --- | --- |
| Is the package present in the **runtime** image? | Build-stage-only CVEs differ from runtime CVEs |
| Is there a known exploit path for *this* workload? | Version match ≠ reachable RCE |
| What is the compensating control? | Network policy, non-root, read-only rootfs, WAF — none are magic |
| What digest was scanned? | Scanning `:local` then deploying another build is theatre |

**Exercise:** In a disposable branch, add an intentionally old vulnerable package to a throwaway image, show the scanner finding, remove it and record before/after. Do not publish that image.

### 3.5.3 Signatures and what they do not prove

Image signing (e.g. Cosign/Sigstore) can prove **who signed which digest** under a given key/identity model. It does not prove the code is correct, the Dockerfile is safe or the scanner was run. Combine signing with review, CI policy and digest promotion.

### 3.5.4 Publish a non-secret sample

Push to a training registry namespace you control (GHCR, Docker Hub private, or `localhost:5000`):

```bash
# Local registry example
docker run -d --name registry -p 5000:5000 registry:2
docker tag harbour-api:local localhost:5000/harbour-api:0.1.0
docker push localhost:5000/harbour-api:0.1.0
docker buildx imagetools inspect localhost:5000/harbour-api:0.1.0
```

Capture the **registry digest** from inspect output and store it beside the commit SHA in your evidence notes.

**Practice 4:** Write `docs/decisions/0003-container-runtime-contract.md` covering non-root execution, secrets, writable paths, signals and registry trust.

**Verify:** You can point to one digest that was scanned and would be the digest you deploy.

**Reflect:** Where should a platform enforce “no mutable tags in production” — developer docs, CI, admission policy, or all three?

---

## Section 3.6 — Operability: limits, logs, shutdown, onboarding

### 3.6.1 Resource limits and restart behaviour

Add to the `api` service when your engine supports it:

```yaml
    deploy:
      resources:
        limits:
          cpus: "0.50"
          memory: 256M
```

Compose `deploy.resources` is interpreted differently across engines (Swarm vs local Compose). If limits are ignored locally, demonstrate them with `docker run --memory` and document the gap — honesty beats fake YAML.

### 3.6.2 Logs and events

```bash
docker compose logs api --since 10m
docker events --filter container="$(docker compose ps -q api)" --since 10m
```

Structured application logs come in D07; for now, ensure failures are visible without attaching a debugger.

### 3.6.3 Graceful shutdown drill

```bash
API_CID="$(docker compose ps -q api)"
docker stop -t 15 "$API_CID"
docker compose ps -a
docker compose up -d
```

Confirm uvicorn exits on `SIGTERM` within the grace period. If not, fix signal handling or entrypoint before claiming production readiness.

### 3.6.4 Newcomer instructions

Your `app/README.md` (or root README section) must include:

1. Prerequisites (Docker, Compose, ports)
2. `cp .env.example` guidance (no real secrets)
3. `docker compose up --build -d` with `HARBOUR_COMMIT`
4. How to hit `/health` and `/ready`
5. How to view logs, stop and wipe (including volume warning)
6. How to find the image digest after build/push
7. At least two failure drills and expected symptoms

**Practice 5:** Ask a colleague — or wait overnight and use a fresh clone yourself — to bring the stack up using **only** the repository docs. Fix every ambiguity they hit.

---

## Section 3.7 — Looking ahead to CI/CD and Kubernetes

Compose proves a **local multi-service contract**. It is not a cluster.

| Concern | Compose (D03) | Later modules |
| --- | --- | --- |
| Build & prove artifact | Local `docker build` | D04 pipelines, provenance, promotion |
| Desired state at scale | `docker-compose.yml` | D06 GitOps manifests |
| Scheduling / healing | Restart policies | P01–P02 Kubernetes controllers |
| Identity & secrets | Env files (training only) | D05/D06/platform secret patterns |
| Observability | `logs` / `events` | D07–D08 telemetry |

Write a short note in `docs/architecture.md`: the image digest + health/ready endpoints are the interface the platform will automate next.

---

## Practical Assessment — Chapter 3 — production-ready container contract

**Scenario:** Another team must deploy Harbour API without knowing FastAPI. Deliver an artifact and operating instructions they can trust.

Align with [D03 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D03%20Docker%20and%20Containerization.md) and the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D03 row.

### Required deliverables

1. **Repository:** multi-stage `Dockerfile`, `.dockerignore`, Compose stack, health/ready endpoints, reproducible docs.
2. **Provenance:** published (or registry-local) image reference including **digest**, tied to a Git commit SHA.
3. **Supply chain:** before/after image comparison (size/history/scan) and an SBOM or dependency inventory with vulnerability review notes.
4. **Runtime:** isolated DB networking (no unnecessary host port), persistence across API recreate, clean startup with readiness.
5. **Failure drills:** at least two of: broken connectivity, memory exhaustion, read-only filesystem surprises, unready database, lost volume, failed shutdown — with symptoms and fixes.
6. **Design record:** non-root user, secrets handling, writable storage, signals, registry trust.
7. **Onboarding test:** second developer (or cold self-run) succeeds using only repo instructions.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Isolation model | Runs containers by habit | Explains namespaces/cgroups/layers with inspect evidence | Designs defaults that assume shared-kernel failure modes |
| Image engineering | Single-stage root image works | Multi-stage, pinned deps, non-root, sensible entrypoint | Cache strategy, digest pinning policy, minimal attack surface |
| Networking & state | Ports everywhere; data in container layer | Service DNS, segmented DB, volumes, readiness | Clear backup vs persistence story; failure drills documented |
| Supply chain | Scanner output pasted raw | Digest-correlated SBOM/scan with prioritised remediation | Signing/admission story and honest limits of each control |
| Operability | “It starts on my machine” | Second person reproduces; limits/logs/shutdown tested | Platform-ready contract (health/ready/digest) for D04+ |
| Communication | Dockerfile only | README + ADR + evidence notes | Ambiguities found in onboarding are fixed in-repo |

**Completion standard:** **Competent** on every row. Do not claim production readiness solely because the container starts.

### Self-check

- Can a stranger build and run from docs alone?
- Is the running identity non-root by default?
- Can you name the digest you would deploy and the commit that built it?
- Does `/ready` fail when Postgres is down?
- Did you test at least two failure drills with recorded evidence?
- Are secrets absent from image layers and git history?

### Example assessment conclusion (evidence still required)

> Harbour API ships as a multi-stage non-root image. Compose attaches the API to an internal bridge network with Postgres; the database is not published to the host. Readiness fails when Postgres is stopped. Image `localhost:5000/harbour-api@sha256:…` traces to commit `abc123`. Syft/Grype results for that digest are filed with two accepted risks and one patched dependency. A colleague brought the stack up from the README without pair programming.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See why a container died | `docker inspect`, `docker events`, exit codes, OOM fields | Restarting until it “looks fine” |
| Shrink/safe the image | Multi-stage, `.dockerignore`, non-root, fewer packages | Running builds as root in runtime |
| Debug “connection refused” | Who is localhost? DNS name? Published ports? | Opening every port to the host |
| Keep data | Named volumes + backup story | Assuming the writable layer persists |
| Trust what you deploy | Digest + commit + scan of *that* digest | Deploying `:latest` because it worked locally |
| Prove readiness | Separate `/health` vs `/ready` | Treating process up as dependency up |

## Glossary

| Term | Definition |
| --- | --- |
| Image | Immutable layered filesystem + config |
| Container | Running (or created) instance with a writable layer |
| Namespace | Isolation of names (PID, net, mount, …) |
| cgroup | Resource limitation/accounting |
| Digest | Content-addressed image identifier (`sha256:…`) |
| Tag | Mutable pointer to an image |
| Multi-stage build | Dockerfile with multiple `FROM` stages; copy artifacts forward |
| SBOM | Inventory of components in an artifact |
| Liveness | Process should be restarted if failing |
| Readiness | Process should receive traffic only if dependencies are usable |
| Rootless | Engine or workload without root privileges |
| Compose | Declarative multi-container local runtime |

## References

- [Docker — Build best practices](https://docs.docker.com/build/building/best-practices/)
- [Docker — Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker — Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [Docker — Container security](https://docs.docker.com/engine/security/)
- [OCI image specification](https://github.com/opencontainers/image-spec)
- [SLSA](https://slsa.dev/)
- [Syft](https://github.com/anchore/syft) · [Grype](https://github.com/anchore/grype) · [Trivy](https://github.com/aquasecurity/trivy)

**Previous chapter:** [Chapter 2 — Advanced Git](D02%20Advanced%20Git.md) · **Course detail:** [D03 — Docker and Containerization](../../3%20Course%20Detail/3.1%20DevOps/D03%20Docker%20and%20Containerization.md) · **Next chapter:** Chapter 4 — CI/CD and Build Automation (not yet authored) · **Checklist:** [Final Project Checklist · D03](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
