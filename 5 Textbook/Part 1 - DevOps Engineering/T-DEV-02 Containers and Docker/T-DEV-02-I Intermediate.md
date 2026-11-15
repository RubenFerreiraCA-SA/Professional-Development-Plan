# T-DEV-02-I — Intermediate Practice

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-i"></a>
#### T-DEV-02-I — Intermediate Practice

## Why this matters

At Beginner level a container is one process you start by hand. Real services are never that simple. They have a build that must be fast and small, a database that must start first and keep its data, configuration that differs between laptop and server, a shutdown that must not drop requests, and failures that must be diagnosed from outside the container because there is rarely a human inside it.

Intermediate practice is the set of habits that make a containerised service *repeatable, diagnosable and well-behaved*: a multi-stage Dockerfile, a Compose file that lets any colleague run the whole system with one command, deliberate choices between bind mounts and volumes, a clear picture of how names resolve between containers, honest health checks, and a reliable troubleshooting routine. This section assumes the Beginner material: image versus container, layers, `docker run`, ports, `localhost`, volumes.

The running example is a small `orders-api` service plus a Postgres database. Nothing depends on any other course material.

## Project layout used below

```text
orders-api/
├── app/
│   └── main.py
├── Dockerfile
├── .dockerignore
├── .env.example          # committed: names of variables, harmless placeholder values
├── .env                  # NOT committed: your real local values
├── requirements.txt
├── compose.yaml
└── compose.dev.yaml      # optional development overrides
```

## First principles: PID 1, signals and shutdown

The first process in a container is **PID 1**. Two kernel rules make PID 1 special:

1. **Signal defaults are different.** For an ordinary process, `SIGTERM` terminates it unless it installs a handler. For PID 1 inside a PID namespace, signals with the default action are *ignored* unless the program explicitly installs a handler. So a program that never thought about signals simply does not stop when asked politely.
2. **Orphans are adopted by PID 1.** When a child process's parent dies, the child is reparented to PID 1, which must `wait()` for it. A PID 1 that does not reap leaves *zombie* entries.

`docker stop` sends `SIGTERM`, waits a grace period (10 seconds by default, `-t` to change), then sends `SIGKILL`. If your app ignores `SIGTERM`, every deployment takes ten seconds longer and in-flight requests are cut off hard.

| Situation | What happens | Fix |
| --- | --- | --- |
| Shell-form `CMD python app.py` | Docker runs `/bin/sh -c "python app.py"`; the shell is PID 1 and may not forward signals | Use exec form: `CMD ["python", "app.py"]` |
| Exec form, app handles `SIGTERM` | Clean shutdown within the grace period | Nothing — this is the goal |
| Exec form, app has no handler (e.g. `sleep`) | `SIGTERM` ignored, `SIGKILL` after the timeout, exit code 137 | Add a handler, or run an init |
| App spawns children and never reaps | Zombie processes accumulate | `docker run --init` / Compose `init: true` (a tiny init such as `tini` becomes PID 1) |
| Entrypoint script ends with `python app.py` | The shell script stays PID 1 | End the script with `exec python app.py` |

Observe it:

```bash
docker run -d --name a alpine:3.20 sleep 300
time docker stop a            # illustrative: about 10 seconds, exit code 137
docker run -d --init --name b alpine:3.20 sleep 300
time docker stop b            # illustrative: well under a second
docker inspect -f '{{.State.ExitCode}}' a b
docker rm a b
```

## Multi-stage builds

A single-stage image that compiles dependencies contains the compiler, headers and caches forever. A **multi-stage build** uses one stage to build and a later stage that copies only the results. The final image is smaller, has fewer packages to patch and exposes less to an attacker.

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
RUN useradd --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels
COPY --chown=app:app app/ ./app/
USER app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Annotation:

- `AS build` / `AS runtime` name the stages. Only the **last** stage becomes the image unless you pick another with `--target`.
- `COPY --from=build` is the only bridge between stages; everything else in the build stage is discarded.
- `rm -rf /wheels` in the same `RUN` that used the wheels keeps them out of the layer. (The earlier `COPY --from=build /wheels` layer still holds them; see the note below on how much a multi-stage build really saves here.)
- `--chown=app:app` gives the runtime user ownership at copy time; no separate `chown` layer is needed.
- `ENTRYPOINT` in exec form makes the app PID 1 and fixes the program; `CMD` can then supply default arguments that a user may override.

A cleaner way to avoid carrying wheels is to install into a virtual environment in the build stage and copy that directory across:

```dockerfile
FROM python:3.12-slim AS build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
```

Compare sizes yourself instead of trusting claims: `docker build --target build -t orders-api:build .` and `docker build -t orders-api:slim .`, then `docker images orders-api`.

`ENTRYPOINT` and `CMD` interact like this:

| Dockerfile | `docker run image` runs | `docker run image --port 9000` runs |
| --- | --- | --- |
| `CMD ["prog", "--port", "8000"]` | `prog --port 8000` | `--port 9000` (tries to execute it as a program — the whole `CMD` is replaced) |
| `ENTRYPOINT ["prog"]` + `CMD ["--port", "8000"]` | `prog --port 8000` | `prog --port 9000` |

## `.dockerignore` and the build context

When you run `docker build .`, the directory is sent to the builder. Everything in it can be copied into an image, and the more you send, the slower each build. A `.dockerignore` file excludes paths from the context entirely.

```text
.git
.env
.env.*
!.env.example
.venv/
__pycache__/
*.pyc
tests/output/
*.pem
*.key
compose*.yaml
```

Two benefits: secrets never enter the image, and editing an ignored file (a test log, for example) no longer invalidates the `COPY . .` cache. If a build fails with `file not found` for a path you can see locally, check whether `.dockerignore` excluded it.

## Environment variables and configuration

| Mechanism | Where it applies | Visible in the image? | Typical use |
| --- | --- | --- | --- |
| `ENV` in Dockerfile | Build **and** run | Yes (`docker image inspect`) | Non-secret defaults (`PYTHONUNBUFFERED=1`) |
| `ARG` in Dockerfile | Build time only | Recorded in image history | Version numbers, build flags — **never secrets** |
| `docker run -e NAME=value` / `--env-file` | Run time | No | Per-environment configuration |
| Compose `environment:` | Run time | No | Literal values and interpolations |
| Compose `env_file:` | Run time | No | Larger sets kept out of the YAML |
| `.env` in the Compose project directory | **Compose file interpolation** (`${VAR}`) | No | Values substituted into `compose.yaml` itself |

Compose's two uses of "env file" confuse many people: a file named `.env` in the project directory is read automatically to fill `${VAR}` placeholders *inside the Compose file*; it is not passed to containers unless you also list it under `env_file:` or reference the variables under `environment:`. When values collide, Compose precedence runs, roughly from strongest to weakest: `docker compose run -e`, then `environment:` in the file, then `env_file:`, then `ENV` in the image. Never guess — look at the resolved result:

```bash
docker compose config                    # rendered file with interpolation applied
docker compose exec api env | sort       # what the process really sees
docker inspect -f '{{json .Config.Env}}' <container>
```

Important: environment variables are visible to anyone who can run `docker inspect` on the host and to child processes. They are acceptable for local development and for non-secret settings. For production secrets use a secret store or mounted files (covered in the Professional section).

## Compose as a local contract

Compose describes a multi-container application in a single file, so that "how do I run this?" has one answer.

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_HOST: db
      DATABASE_USER: orders
      DATABASE_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD in .env}
    depends_on:
      db: { condition: service_healthy }
    init: true
    restart: unless-stopped
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: orders
      POSTGRES_PASSWORD: ${DB_PASSWORD:?set DB_PASSWORD in .env}
    volumes: [pg_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orders"]
      interval: 5s
      timeout: 3s
      retries: 10
volumes:
  pg_data:
```

`.env.example` (committed) and `.env` (gitignored, created from it):

```text
DB_PASSWORD=change-me-locally
```

Reading the file:

- `${DB_PASSWORD:?message}` makes Compose refuse to start with a clear message when the variable is missing, rather than starting a database with an empty password.
- The database has **no `ports:` entry**, so it is not published to the host. The API reaches it at `db:5432` over the project's private network.
- `depends_on` with `service_healthy` delays the API until the database's health check passes **at start-up**. It does not keep the dependency healthy later. Clients must still retry connections.
- `init: true` is Compose's equivalent of `docker run --init`.
- `restart: unless-stopped` brings the container back after a crash or reboot, but not after you stopped it on purpose.

Daily commands:

```bash
docker compose up --build -d             # build if needed, start in background
docker compose ps                        # state and health of each service
docker compose logs -f --tail=100 api    # follow recent logs of one service
docker compose exec db psql -U orders    # run a command in a running service
docker compose down                      # stop and remove containers and networks (volumes stay)
docker compose down -v                   # ... AND delete named volumes (data!)
```

**Restart policies.**

| Policy | Behaviour |
| --- | --- |
| `no` | Never restart (default) |
| `on-failure[:N]` | Restart on non-zero exit, optionally at most N times |
| `always` | Always restart; a container you stopped by hand is started again when the Docker daemon restarts |
| `unless-stopped` | Like `always`, but respects an explicit manual stop |

A restart policy hides crash loops from a casual glance: check `docker compose ps` for a growing restart count and read the logs, rather than assuming "it's up".

## Volumes versus bind mounts, properly

| Aspect | Named volume | Bind mount |
| --- | --- | --- |
| Managed by | Docker (under its data directory) | You (a host path) |
| Created | Automatically on first use | Host path must exist (with `--mount`; `-v` silently creates a root-owned directory) |
| Initial content | Copied from the image's content at that path when the volume is empty | Whatever the host directory contains — it **hides** the image's content at that path |
| Ownership | Follows container writes | Host file ownership; UID mismatches show up as `Permission denied` on Linux |
| Portability | Works the same everywhere | Depends on host layout; slow on some desktop file-sharing setups |
| Best for | Databases and other state | Development: editing source live |
| Backup | Back up via a helper container | Back up the host directory |

A development override that bind-mounts source and enables reload:

```yaml
# compose.dev.yaml — use with: docker compose -f compose.yaml -f compose.dev.yaml up
services:
  api:
    volumes:
      - ./app:/app/app:ro
    command: ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

Use `--mount` for clarity when running by hand:

```bash
docker run --rm --mount type=bind,source="$(pwd)/app",target=/app/app,readonly orders-api:local
docker run --rm --mount type=volume,source=pg_data,target=/var/lib/postgresql/data postgres:16-alpine
```

Beware of the shadowing trap: if the image contains `/app/app` and you bind-mount an empty or different directory there, the container sees *your directory*, not the image's files. "It works in the image but not in dev" is often this.

Back up a named volume with a throwaway container (the backup file lands in the current directory):

```bash
docker run --rm -v pg_data:/data:ro -v "$(pwd)":/backup alpine:3.20 \
  tar czf /backup/pg_data.tgz -C /data .
```

For a *running* database a file copy of the data directory is not guaranteed to be consistent; prefer the database's own dump tool (`pg_dump`) and test restores.

## Networks and DNS

Compose creates one user-defined network per project and attaches every service to it. On a user-defined network:

- Docker runs an embedded DNS resolver (at `127.0.0.11` inside each container).
- A service is reachable by its **service name** (`db`) and also by network aliases.
- Different Compose projects have different networks, so they cannot reach each other by name unless you attach a shared network on purpose.

```bash
docker compose exec api getent hosts db           # name resolution from inside the API container
docker network ls
docker network inspect orders-api_default          # attached containers and their IPs
docker compose port api 8000                       # which host port maps to the container port
```

Three different addresses you must keep apart:

| You use | From | Meaning |
| --- | --- | --- |
| `db:5432` | another container on the same network | The database container's own port |
| `127.0.0.1:8000` | the host | The **published** port of `api` |
| `127.0.0.1:5432` | inside the `api` container | The `api` container itself — there is no database there |

Reaching a service on the host machine *from* a container is a different problem; on Linux you typically add `extra_hosts: ["host.docker.internal:host-gateway"]` and the service must listen on an interface reachable from the Docker bridge. Treat host access as an exception and say why in a comment.

## Health versus readiness

A health check is a command Docker runs periodically inside the container. The container's status moves through `starting`, `healthy` and `unhealthy`.

```bash
docker inspect -f '{{json .State.Health}}' <container>   # status and recent probe results
docker ps                                                 # STATUS shows (healthy) / (unhealthy)
```

Important limits:

- Plain Docker **records** an unhealthy status but does not restart the container for it. An orchestrator may act on health; plain `docker run` and Compose do not on their own.
- `start_period` (Compose) / `--start-period` (Dockerfile) gives slow starters a window where failures do not count.
- **Liveness** ("the process is not wedged") and **readiness** ("dependencies work, send me traffic") are different questions. Give the application two endpoints: `/health` and `/ready`.

A readiness check that only opens a TCP connection to the database proves a listener exists, not that authentication and queries work. Prefer a real `SELECT 1` through the same connection pool the application uses. Test the check by *breaking* the dependency (wrong password) and confirming `/ready` fails while `/health` still passes.

```python
# illustrative readiness handler (framework details vary)
@app.get("/ready")
def ready():
    try:
        with pool.connection() as c:
            c.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
```

## Troubleshooting routine: logs, exec, inspect

When something is wrong, move from the outside in. Do not restart until you know what you are looking at; restarting destroys evidence.

1. **Is it running?** `docker compose ps` (or `docker ps -a`).
2. **What did it say?** `docker compose logs --tail=200 <service>`.
3. **How did it end?** `docker inspect -f '{{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}}' <c>`.
4. **What does it think its configuration is?** `docker compose exec <svc> env`, `docker compose config`.
5. **Can it reach what it needs?** `getent hosts db`, `nc -vz db 5432`, from the container's own network namespace.
6. **What changed in the filesystem?** `docker diff <c>`; copy files out with `docker cp <c>:/path ./path`.
7. **What does the engine say?** `docker events --since 10m`, `docker stats --no-stream`.

| Symptom | Likely causes | First checks |
| --- | --- | --- |
| Exits immediately, exit code 1 | Application error, missing config | `docker logs`, `docker inspect` |
| Exit code 137 | `SIGKILL`: out-of-memory kill or ignored `SIGTERM` | `OOMKilled` flag, memory limit, shutdown time |
| Exit code 126/127 | Entry point not executable / not found (bad path, wrong architecture, CRLF line endings in script) | `docker run --entrypoint sh -it image`, `ls -l`, `file` |
| "Connection refused" to a dependency | Wrong host (`localhost`), dependency not ready, wrong port | `getent hosts`, `docker compose ps`, dependency logs |
| Works from the host, not from another container | Listening on `127.0.0.1` | Bind to `0.0.0.0` |
| `Permission denied` writing a file | Non-root user, bind-mount ownership, read-only mount | `id`, `ls -ln`, mount options |
| Container "healthy" but app broken | Health check too shallow | Compare `/health` with `/ready` |
| Restarting repeatedly | Crash loop under `restart: always` | `RestartCount`, logs of earlier runs |

Minimal images often have no shell or tools. Instead of rebuilding with a shell, attach a *debug container* to the target's network namespace:

```bash
docker run --rm -it --network container:orders-api-api-1 nicolaka/netshoot \
  sh -c 'ss -ltnp; getent hosts db'
```

(Replace the container name with the one from `docker ps`; `netshoot` is a widely used community toolbox image — pin and review any image you run this way.)

## Caching, build speed and layer discipline

Build speed is a developer-experience and CI-cost issue. The rules:

1. Order instructions from least to most frequently changing.
2. Separate dependency installation from source copy.
3. Keep the build context small (`.dockerignore`).
4. Combine commands that must succeed together, and clean up in the same `RUN`:

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
```

Never put `apt-get update` in its own `RUN`: a cached stale package index followed by a later `install` is a classic source of "404 Not Found" build failures.

5. Use BuildKit cache mounts so package downloads persist between builds without ending up in a layer:

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

6. Remember that **any change to an instruction, or to a file it copies, invalidates that layer and everything after it.** Placing an `ARG BUILD_DATE` early is a well-known way to defeat the cache for the whole build.
7. Fresh CI runners have no cache. To reuse it across runs, export and import it explicitly:

```bash
docker buildx build \
  --cache-from type=registry,ref=registry.example.com/team/orders-api:buildcache \
  --cache-to   type=registry,ref=registry.example.com/team/orders-api:buildcache,mode=max \
  -t registry.example.com/team/orders-api:ci-123 .
```

Measure rather than assume: run the build twice in CI and compare durations. A cache that is slower to restore than the step it saves is a net loss.

## Build failures and how to read them

Use plain progress output to see everything: `docker build --progress=plain .`. Force a rebuild without any cache with `--no-cache` to separate "cache confusion" from a real error. To inspect a failing multi-stage build, build up to a stage and open a shell in it:

```bash
docker build --target build -t orders-api:debug .
docker run --rm -it orders-api:debug sh
```

| Message (shape) | Meaning | Fix |
| --- | --- | --- |
| `failed to compute cache key: ... not found` for a `COPY` | Path missing from context or excluded by `.dockerignore` | Check the path relative to the context; check `.dockerignore` |
| `pip` compile errors in a slim image | Package needs a compiler or system headers that slim images lack | Install build tools in the **build** stage only, or choose a package with wheels |
| `no matching manifest for linux/arm64/v8` | Image has no build for your CPU architecture | Choose another image or use a multi-platform one (see Expert) |
| `404` during `apt-get install` | Stale cached package index | Combine `update` and `install` in one `RUN`; rebuild without cache |
| `Could not resolve host` during build | Build network or DNS problem | Check proxy settings and daemon DNS |
| `exec format error` at run | Binary built for a different architecture, or script missing a shebang | Check `docker image inspect -f '{{.Architecture}}'` |
| App starts but wrong dependency version | Unpinned requirement resolved to a new release | Pin and lock dependencies |

## Reproducibility at the Intermediate level

Reproducibility means a colleague (or CI, or you in six months) gets the *same behaviour* from the same commit.

- Pin base images by version tag (`python:3.12-slim`, not `python` or `latest`); Professional practice goes further and pins by digest.
- Pin application dependencies exactly (`==`) and keep a lock file; avoid "latest compatible" resolution at build time.
- Keep configuration in committed files (`compose.yaml`, `.env.example`), not in anyone's memory.
- Make bring-up a documented single command, and test it from a clean checkout: `git clone … && cp .env.example .env && docker compose up --build`.
- Record, in the README, what a healthy start looks like: which URL to open, what `docker compose ps` should show.
- Prefer rebuilding images from source over passing image tarballs around.

## What can go wrong: a short catalogue

| Failure | Why it happens | Prevention |
| --- | --- | --- |
| "Works with Compose, fails in CI" | Local `.env` or bind mount differs; cache differs | Run the clean-checkout bring-up in CI |
| Data vanished after `compose down -v` | `-v` removes named volumes | Know the flag; keep backups |
| Database password change ignored | Postgres only initialises users on **first** start of an empty data directory | Recreate the volume deliberately, or alter the user in SQL |
| API starts before the DB accepts logins | Dependency order is not readiness | Healthcheck plus client retry with backoff |
| Image grows with every build | Temporary files kept in layers, no multi-stage | Clean in the same `RUN`; multi-stage |
| Secrets in `docker inspect` output | Passed as environment variables | Non-secret config only; secret mechanisms later |
| Disk fills with logs | Default `json-file` logging has no rotation limit | Configure `max-size`/`max-file` or use the `local` driver |

## Knowledge consolidation

- PID 1 behaves differently: use **exec form**, handle `SIGTERM`, or add an **init**; confirm with a timed `docker stop`.
- **Multi-stage builds** keep compilers and caches out of the runtime image; only `COPY --from` crosses the boundary.
- **Compose** makes the multi-container system a committed, reviewable contract. `depends_on: service_healthy` is a start-up ordering aid, not a guarantee.
- **Volumes** hold state; **bind mounts** serve development and can hide image contents.
- On a user-defined network, **the service name is the host name**; `localhost` is always yourself.
- **Health** is "alive"; **readiness** is "dependencies work". Plain Docker records health but does not heal.
- Troubleshoot **outside in**: state, logs, exit code and OOM flag, configuration, connectivity — before restarting.
- Cache-friendly Dockerfiles order from stable to volatile, separate dependencies from code and use cache mounts.
- Reproducibility is pinned inputs, committed configuration and a tested one-command bring-up.

## Exercises

**Exercise 1 — Multi-stage.** Take your Beginner `orders-api` Dockerfile and convert it to a multi-stage build. Record `docker images` sizes for the single-stage and multi-stage versions and list which packages or files are present in one but not the other.

**Exercise 2 — Compose and persistence.** Run the Compose stack. Create a row in the database (any table), `docker compose down` (no `-v`), `up` again and confirm the row remains. Then run `down -v`, `up`, and confirm it is gone.

**Exercise 3 — Break readiness on purpose.** Add `/ready` that runs `SELECT 1`. Stop `db`, call `/health` and `/ready`, restart `db`, and call them again. Then change the API's database password to a wrong value and compare the result with merely stopping the database.

**Exercise 4 — Signals.** Write down the time `docker compose stop api` takes with and without `init: true` and with shell-form versus exec-form entrypoints. Explain every difference you see using PID 1 behaviour.

**Exercise 5 — Cache.** In CI or locally with `--progress=plain`, make three edits: (a) a source file, (b) `requirements.txt`, (c) an early `ARG`. Record which steps re-run each time and why.

**Exercise 6 — Diagnose.** Have a partner (or a script) break your stack in one of three ways: wrong service name in `DATABASE_HOST`, API bound to `127.0.0.1`, memory limit of `32m`. Using only the troubleshooting routine, identify each cause and quote the evidence (log line, exit code, `OOMKilled` flag, DNS output).

**Solution notes.**

*Exercise 1.* Illustrative expectation: the runtime image should lack compilers, `pip` caches and wheel files that the build stage held. If sizes barely differ, check whether you copied the whole build stage's filesystem or only the installed packages, and whether the base image itself dominates the size.

*Exercise 2.* After `down` the named volume `pg_data` survives, so the row should persist. After `down -v` the volume is deleted and the database initialises empty. A surprise here usually means the data was written to a path that is not the volume mount point; check the `volumes:` target.

*Exercise 3.* With the database stopped both endpoints behave differently: `/health` should still return success (the process is alive), while `/ready` should return an error status. With a wrong password the TCP port is open and a naive TCP-based check would pass; the `SELECT 1` check should fail. That difference is the point of the exercise.

*Exercise 4.* With exec form, a handled `SIGTERM` should give a stop of about a second or less. With shell form, or an app that does not install a handler, expect to wait for the grace period and see exit code 137. `init: true` should help the second case because the init forwards the signal and the default action then applies to the child. Record your own measurements; do not copy numbers from this text.

*Exercise 5.* An edit to source should re-run `COPY` of source and later layers only. An edit to `requirements.txt` should re-run the install step and everything after it. An `ARG` placed early and given a new value should invalidate everything after the `ARG` — which is why such arguments belong as late as possible.

*Exercise 6.* Expected evidence: a wrong service name shows a resolver error in the application log and empty output from `getent hosts`; a `127.0.0.1` bind works from inside the container but fails from the host or other containers; a very small memory limit shows exit code 137 and `OOMKilled=true` in `docker inspect` (if the process is actually killed for memory rather than for another reason — verify, do not assume).
