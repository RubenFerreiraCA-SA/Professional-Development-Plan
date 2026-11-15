# T-DEV-02-P — Professional Engineering

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-p"></a>
#### T-DEV-02-P — Professional Engineering

## Why this matters

An image that works on a laptop is a demo. An image that is *production-ready* has answered a set of questions that the demo never asked. Who does it run as, and what can that identity do if the application is compromised? What exactly is inside it, and which of those components have known vulnerabilities? How do we know the bytes running in production are the bytes CI built and tested? What happens when it runs out of memory, receives `SIGTERM` during a request, or fills a disk with logs? Can a person at 03:00 diagnose it without making things worse?

Professional practice turns those questions into **explicit, reviewable, enforceable decisions**: a hardened runtime configuration, a minimal and pinned image, an inventory (SBOM) and provenance attached to each release, registry controls that make mistakes hard, resource limits that make failures predictable, and a diagnostic routine. This section assumes the Beginner and Intermediate material (layers, multi-stage builds, Compose, PID 1 and signals, health versus readiness). The examples use the neutral `orders-api` service; registry names such as `registry.example.com` are placeholders.

A recurring theme: **each control reduces a specific risk and does not remove others.** Learn what each one does *not* do.

## First principles: what "production-ready" means for one container

Think of an image as a *contract with the runtime environment*. A production-ready image states, in files that are reviewed:

| Contract clause | Question it answers | Where it is expressed |
| --- | --- | --- |
| Identity | Which user and group; which capabilities | `USER`, runtime flags or orchestrator settings |
| Contents | What is installed, at which versions | Dockerfile, lock files, SBOM |
| Provenance | Who built it, from which commit, with which builder | Attestations, signatures, release record |
| Filesystem | Which paths are writable and why | Read-only root plus explicit volumes or `tmpfs` |
| Resources | How much CPU, memory and processes it may use | Limits |
| Lifecycle | How it starts, becomes ready, shuts down | Entrypoint, health endpoints, stop signal and grace period |
| Observability | Where logs and metrics go | Standard output and error; metrics endpoint |
| Trust | Which registry, which digests, which signers | Registry and admission policy |

If a clause is not written down and testable, assume it is unmet.

## Security posture of a container

The shared-kernel model is powerful and leaky: a kernel vulnerability, a privileged container or access to the container runtime socket can defeat isolation.

| Pattern | Meaning |
| --- | --- |
| Rootful engine, container runs as `root` | Broad privileges inside the shared-kernel model |
| Non-root `USER` in the image | Smaller blast radius after compromise; still not a VM boundary |
| Rootless engine | The daemon runs unprivileged; port and filesystem semantics change |
| Membership of the `docker` group | On typical rootful installs, effectively root on the host |
| `--privileged` | Nearly all isolation removed; almost never justified |
| Docker socket mounted into a container | The container can control the host's container engine, which is host-level control |

Never mount `/var/run/docker.sock` into a service for convenience. Run as a non-root user, drop capabilities, use a read-only root filesystem where possible (with explicit writable volumes), avoid `--privileged`, and set resource limits.

## Non-root, properly

"Add `USER`" is the start, not the end. A reliable pattern:

```dockerfile
FROM python:3.12-slim@sha256:<digest> AS runtime
# Fixed numeric IDs: orchestrators can verify "runs as non-root" only if the ID is numeric.
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build --chown=10001:10001 /opt/venv /opt/venv
COPY --chown=10001:10001 app/ ./app/
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Things that commonly go wrong after dropping root:

| Symptom | Cause | Right fix |
| --- | --- | --- |
| `Permission denied` writing a log, cache or temp file | App writes to a root-owned path | Write to `/tmp` (`tmpfs`) or a declared volume; fix ownership with `--chown`; do not return to root |
| Cannot bind port 80 or 443 | Low ports were historically privileged | Listen on 8000/8080 and map the port; recent engines relax the restriction inside container network namespaces, but do not depend on that |
| Volume mounted but unwritable | Volume created root-owned | Set ownership during image build for the path, or an init step that runs once; use `fsGroup`-style settings in an orchestrator |
| Works locally, fails in the cluster | Cluster enforces `runAsNonRoot` and your image has a named user | Use a numeric `USER` |
| Needs a privilege for a one-off task | Runtime step requires root (package install, `chown` of a mount) | Move it to build time or a separate one-shot job |

Runtime hardening for a single container, in one command:

```bash
docker run -d --name orders-api \
  --user 10001:10001 \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop=ALL \
  --security-opt no-new-privileges \
  --pids-limit 200 --memory 256m --memory-swap 256m --cpus 0.5 \
  --init --stop-timeout 20 \
  -p 8000:8000 \
  registry.example.com/team/orders-api@sha256:<digest>
```

The Compose equivalent, as a reviewable artifact:

```yaml
services:
  api:
    image: registry.example.com/team/orders-api@sha256:<digest>
    user: "10001:10001"
    read_only: true
    tmpfs: ["/tmp:rw,noexec,nosuid,size=64m"]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    pids_limit: 200
    mem_limit: 256m
    cpus: 0.5
    init: true
    stop_grace_period: 20s
    restart: unless-stopped
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"]
      interval: 15s
      timeout: 3s
      retries: 3
      start_period: 10s
```

Whatever flags you adopt, **verify they took effect** rather than trusting the file: `docker inspect -f '{{.HostConfig.ReadonlyRootfs}} {{.Config.User}} {{.HostConfig.CapDrop}} {{.HostConfig.Memory}}' orders-api`, and test one expected failure (`docker exec orders-api touch /app/x` should fail on a read-only root).

## Minimal images: choosing a base

Every package in an image is code you must patch, scan and explain. Minimal images shrink that surface, with costs.

| Base | Typical content | Benefits | Costs and traps |
| --- | --- | --- | --- |
| Full distribution image | Shell, package manager, many tools | Easy debugging; familiar | Large, many packages and findings |
| `-slim` variants | Distribution minus documentation and many tools | Good default; glibc compatibility | Still has a shell and package manager |
| Alpine-based | musl libc, BusyBox | Small | musl differs from glibc: some prebuilt wheels and binaries are missing or slower; DNS and locale quirks |
| Distroless | Runtime and libraries only; no shell, no package manager | Very few packages; fewer findings; harder for an attacker to use | Cannot `exec` a shell; debugging needs another technique |
| `scratch` (empty) | Nothing; you supply a static binary | Smallest possible | You must add CA certificates, time-zone data and a non-root user yourself; no debug tools |

A representative multi-stage build to a minimal runtime (digests and paths are placeholders):

```dockerfile
# syntax=docker/dockerfile:1.7
# Build stage uses the SAME Python minor version (3.11) that the distroless Debian 12 runtime ships.
FROM python:3.11-slim-bookworm@sha256:<digest> AS build
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.lock .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --require-hashes --no-deps -r requirements.lock
COPY app/ ./app/

FROM gcr.io/distroless/python3-debian12@sha256:<digest> AS runtime
COPY --from=build /opt/venv /opt/venv
COPY --from=build /src/app /app
ENV PYTHONPATH=/opt/venv/lib/python3.11/site-packages
USER 65532:65532
WORKDIR /app
ENTRYPOINT ["/usr/bin/python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Note the sharp edge: the Python **minor version of the build stage must match the runtime's** (distroless Debian 12 ships Python 3.11; a venv built with 3.12 will not work reliably, which is why the build stage above uses 3.11; check the current runtime image's version before copying this pattern). Mismatches like this are why a minimal image needs a test that actually *starts* it.

How to debug something with no shell:

```bash
# Join the target's network and PID namespaces with a tools image (pin and review that image):
docker run --rm -it --pid=container:orders-api --network container:orders-api nicolaka/netshoot
# Or copy a file out:
docker cp orders-api:/app/app/main.py ./main.py
```

In an orchestrator the same idea is an *ephemeral debug container* attached to the running workload. Plan this **before** you adopt distroless; discovering at 03:00 that no shell exists is a poor time.

## Resource limits and restart behaviour

Set memory and CPU limits and a restart policy. Compose `deploy.resources` is interpreted differently across engines and Compose versions; if limits are ignored locally, demonstrate them with `docker run --memory 256m` and record the gap rather than shipping unverified configuration. Always confirm what the engine actually applied:

```bash
docker inspect -f 'mem={{.HostConfig.Memory}} cpus={{.HostConfig.NanoCpus}} pids={{.HostConfig.PidsLimit}}' orders-api
docker stats --no-stream orders-api
```

What each limit does:

| Limit | Effect when exceeded | Operational meaning |
| --- | --- | --- |
| Memory | The kernel's OOM killer terminates a process in the group (`State.OOMKilled=true`, exit 137) | Hard failure; no graceful path |
| CPU (`--cpus`) | The process is **throttled**, not killed | Latency rises, no error is logged — hard to notice |
| PIDs | `fork` fails | Protects against fork bombs and thread leaks |
| Open files (`--ulimit nofile`) | `Too many open files` errors | Check connection and file-descriptor leaks |
| Disk (log size, volume quota) | Writes fail or host disk fills | Cap logs; monitor volumes |

To prove an out-of-memory kill, allocate and *retain* memory in the process (writing to `/dev/null` does not grow resident memory) and inspect `State.OOMKilled`:

```bash
docker run --name oom-test --memory 64m --memory-swap 64m python:3.12-slim \
  python -c "a=[]
while True: a.append(bytearray(10_000_000))"
docker inspect -f 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' oom-test   # illustrative: exit=137 oom=true
docker rm oom-test
```

Setting `--memory-swap` equal to `--memory` prevents the container from using swap, which makes the test deterministic. Runtimes need to know the limit: set heap or worker settings explicitly (for example worker counts and pool sizes) rather than assuming the process will size itself from the cgroup. Treat a limit as a *budget the application is designed for*, not a ceiling to discover by crashing.

Restart policy is a safety net, not a design: a service in a crash loop under `restart: always` looks "up" most of the time. Alert on restart counts, not just on container state.

## Image engineering rules

- Use multi-stage builds; the runtime stage should contain only runtime needs.
- Pin base images by version, and by digest for releases.
- Install dependencies from pinned, reproducible inputs (lock file with hashes).
- Keep secrets out of build arguments, layers and the build context; use build secrets (`RUN --mount=type=secret`) when a build needs one.
- One process concern per container; log to standard output and error.
- Prefer minimal runtime bases, and keep the number of installed packages low.
- Do not run `apt-get upgrade` in a Dockerfile as a substitute for updating the pinned base: it makes builds non-repeatable.
- Never `curl | sh` in a build; download a pinned artifact and verify its checksum.
- Prefer `COPY` to `ADD`; `ADD` with a URL fetches mutable content.

Build secrets, the right way:

```dockerfile
# syntax=docker/dockerfile:1.7
RUN --mount=type=secret,id=pip_index_token,required=true \
    PIP_INDEX_URL="https://__token__:$(cat /run/secrets/pip_index_token)@pypi.example.com/simple" \
    pip install -r requirements.lock
```

```bash
docker build --secret id=pip_index_token,src="$HOME/.secrets/pip_token" -t orders-api:local .
```

The secret exists only for that `RUN` step and is not stored in any layer. Verify with `docker history --no-trunc orders-api:local` and by searching the exported image for the token value. Remember the token may still appear in a build log if a command echoes it.

## Identity: tags lie

Keep three identifiers distinct.

| Identifier | What it is | When you have it |
| --- | --- | --- |
| Local image ID | Content-addressed ID on this engine | Immediately after build |
| Tag | A mutable name (`:1.2.0`, `:latest`) | Whenever you name an image |
| Registry manifest digest | Digest of the image as stored in a registry (`repo@sha256:…`) | After push or pull |

A freshly built, never-pushed image usually has no `RepoDigests` entry. Record the chain *commit → local image ID → registry digest*, deploy by digest, and never rely on `:latest` in production.

```bash
docker build -t registry.example.com/team/orders-api:1.4.2 .
docker image inspect -f '{{.Id}}' registry.example.com/team/orders-api:1.4.2           # local ID
docker push registry.example.com/team/orders-api:1.4.2                                  # output includes: digest: sha256:...
docker image inspect -f '{{index .RepoDigests 0}}' registry.example.com/team/orders-api:1.4.2
docker buildx imagetools inspect registry.example.com/team/orders-api:1.4.2             # shows manifest list and platforms
```

Two subtleties:

- For a multi-platform image the tag points at an **index** (manifest list) with its own digest; each platform has a separate manifest digest. Say which one you record. Deploying by the index digest lets each node pull its own architecture.
- Re-pushing the same tag with different content gives a **new digest under the old name**. Digests expose this; tags hide it.

### Pinning by digest in a Dockerfile and in deployment

```dockerfile
FROM python:3.12-slim@sha256:<digest>      # tag kept for humans, digest enforced
```

Pinning by digest makes builds repeatable but also **freezes security fixes out**. Use an automated update mechanism (a dependency-update bot that opens reviewable pull requests for new digests) with a rebuild-and-scan pipeline, and set a maximum age for base images. A digest without an update process is a slowly ageing vulnerability.

A release record kept in Git gives you a timeline and a rollback target:

```yaml
# releases/orders-api-1.4.2.yaml
version: 1.4.2
commit: 9f2c1e7
image: registry.example.com/team/orders-api@sha256:<digest>
built_at: 2026-11-10T09:14:00Z
sbom: registry.example.com/team/orders-api@sha256:<sbom-digest>
signed_by: ci-release-identity
```

(Values are illustrative placeholders.)

## Vulnerabilities and scanning

A scanner compares package inventories against vulnerability databases. It reports *matches*, not *exploitability*.

```bash
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 \
  registry.example.com/team/orders-api@sha256:<digest>
```

Rules that keep scanning useful:

1. **Scan the artifact you will deploy**, by registry digest, after push. Scanning one build and deploying another proves nothing.
2. **Scan on a schedule as well as on build.** An image does not change but the vulnerability database does; yesterday's clean image can fail today.
3. **Triage; do not just count.** Interpret results with judgement:

| Question | Why it matters |
| --- | --- |
| Is the package in the runtime image or only the build stage? | Build-stage-only findings do not ship |
| Is there a plausible exploit path for this workload? | A version match is not a reachable vulnerability |
| Is a fix available and compatible? | "Unfixed" findings need a different response than fixable ones |
| What compensating control exists? | Network policy, non-root user, read-only filesystem — none are magic |
| Which digest was scanned? | Scanning one build and deploying another proves nothing |

4. **Record exceptions with an owner, a reason and an expiry date**, in a file under review. An exception with no expiry is a permanent unreviewed decision.
5. **Gate on a policy**, such as "no fixable critical findings in the runtime image", rather than "zero findings".

## SBOM: an inventory you can query

A **software bill of materials** lists the components in an image. It lets you answer "are we affected by the new vulnerability in library X?" in minutes, by querying stored SBOMs, instead of rebuilding and scanning everything.

```bash
syft registry:registry.example.com/team/orders-api@sha256:<digest> -o spdx-json > sbom.spdx.json
grype sbom:./sbom.spdx.json --fail-on high
jq '[.packages[] | select(.name=="libssl3")] | length' sbom.spdx.json   # is a package present?
```

Practical points: generate the SBOM from the *same digest* you deploy; store it next to the release record or attach it to the image as an attestation; remember that SBOM completeness depends on the tool's ability to see language packages and statically linked components, so treat it as strong evidence rather than proof of completeness.

## Provenance and signing

**Provenance** is a statement of *how* an artifact was produced: source repository, commit, builder, build parameters. A **signature** binds an identity to a digest. They answer different questions.

```bash
# Build, push and attach an SBOM and provenance attestation in one step (recent BuildKit/buildx):
docker buildx build --platform linux/amd64 \
  --sbom=true --provenance=mode=max \
  -t registry.example.com/team/orders-api:1.4.2 --push .

# Inspect attached provenance:
docker buildx imagetools inspect registry.example.com/team/orders-api:1.4.2 \
  --format '{{ json .Provenance }}'

# Sign the digest with an identity-based (keyless) flow:
cosign sign --yes registry.example.com/team/orders-api@sha256:<digest>

# Verify, pinning both the signer identity and the issuer:
cosign verify registry.example.com/team/orders-api@sha256:<digest> \
  --certificate-identity "https://ci.example.com/workflows/release@refs/heads/main" \
  --certificate-oidc-issuer "https://ci.example.com"
```

Image signing (for example Sigstore's Cosign) proves who signed which digest under a key or identity model. It does not prove the code is correct, the Dockerfile is safe or a scan occurred. Combine signing with review, CI policy and digest-based promotion. A signature verification that does not pin *which identity* may sign accepts any validly signed image — pin the identity.

Provenance is only as trustworthy as the system that produced it: a build that runs untrusted pull-request code with release credentials can produce a perfectly formed, perfectly false attestation. Separate "build for review" from "build for release", and give the release builder a narrowly scoped identity.

## Registry controls

The registry is where artifacts become shared truth, so it deserves policy.

| Control | Reduces | Notes |
| --- | --- | --- |
| Separate repositories (or namespaces) per environment or per trust level | Accidental promotion; blast radius | Release images live in a repository only CI can write |
| Push permission only for CI identities | Manual pushes; "hotfix from a laptop" | Humans get pull access; break-glass is logged |
| Short-lived, repository-scoped credentials | Credential theft impact | Avoid long-lived registry passwords in CI variables |
| Immutable tags for releases | Silent tag replacement | Mutable tags (`main`, `dev`) are allowed only in dev repositories |
| Retention that never deletes released digests | Un-resolvable rollbacks | Delete untagged build leftovers, never anything in the release record |
| Scan on push and scheduled re-scan | Late-discovered CVEs | Findings feed the same triage process |
| Pull-through cache / mirror | Upstream outages, rate limits, upstream tag changes | Mirror the base images you rely on |
| Promotion by digest between repositories | "Rebuilt a different thing for production" | Copy, then verify digest equality |

```bash
# Promote exactly what was tested; do not rebuild.
docker buildx imagetools create \
  --tag registry.example.com/team-prod/orders-api:1.4.2 \
  registry.example.com/team-staging/orders-api@sha256:<digest>
docker buildx imagetools inspect registry.example.com/team-prod/orders-api:1.4.2   # confirm same digest
```

Rule: **promote, do not rebuild.** A rebuild produces a different artifact, even from the same commit, unless your build is bit-for-bit reproducible.

## Production diagnostics

In production you usually cannot attach a debugger and you must not make things worse. A routine:

1. **Preserve evidence before changing anything.** Capture `docker inspect <c>`, `docker logs --since 30m <c> > logs.txt`, `docker events --since 30m`, `docker stats --no-stream`, and note the image digest. A restart erases process state and often the writable layer.
2. **Classify the failure.**

| Observation | Hypothesis | Confirm with |
| --- | --- | --- |
| `OOMKilled=true`, exit 137 | Memory limit too low or leak | Memory graph over time, `docker stats`, heap profile |
| Exit 137, `OOMKilled=false`, stop took the full timeout | `SIGTERM` ignored | Shutdown drill; check PID 1 |
| Exit 139 | Segmentation fault (128 + 11) | Core dump settings, native dependency versions |
| Latency up, CPU graph flat at the limit | CPU throttling | cgroup `cpu.stat` throttled counters (`nr_throttled`) |
| `Too many open files` | Descriptor leak or low `ulimit` | `ls /proc/<pid>/fd \| wc -l`, `--ulimit` |
| Healthy container, failing requests | Dependency failure, readiness too shallow | `/ready` result, dependency logs |
| Random restarts | Crash loop, failing health in an orchestrator, node pressure | `RestartCount`, events, host logs (`dmesg`/journal for OOM) |
| Disk full on host | Log growth, images, volumes | `docker system df -v`, log file sizes |

3. **Look from outside the container first** (host metrics, `docker stats`, `docker inspect`) because it works for any image. **Then look inside** with `docker exec` or a debug container.
4. **Reproduce with the exact digest**, same limits and same user, in a safe environment. A repro on a different image tag is not a repro.
5. **Prefer rollback to live patching.** Because you deploy by digest, rollback is "deploy the previous digest from the release record".
6. **Write the contract change.** If the incident exposed an unwritten clause (no memory budget, no drain), put it in the runtime contract below.

Host-level views (Linux):

```bash
PID=$(docker inspect -f '{{.State.Pid}}' orders-api)
sudo nsenter -t "$PID" -n ss -ltnp          # sockets from the container's network namespace, using host tools
cat /proc/"$PID"/status | grep -E 'VmRSS|Threads|CapEff'
docker exec orders-api cat /sys/fs/cgroup/memory.events     # cgroup v2: oom and oom_kill counters (path may vary by setup)
```

Logging hygiene: log to standard output and error as structured lines (JSON), include a request or correlation ID, and never log secrets. Configure rotation (`max-size`, `max-file`, or the `local` driver) so a noisy container cannot fill the host disk.

## Runtime contract document

Record, in the repository next to the Dockerfile: user and capabilities, secrets handling, writable paths, signals and shutdown behaviour, health endpoints, resource limits and registry trust. Include a newcomer section: how to build, run, test, and read logs.

```markdown
# orders-api runtime contract
- Identity: UID/GID 10001, all capabilities dropped, no-new-privileges.
- Filesystem: read-only root; writable: /tmp (tmpfs 64 MiB).
- Secrets: mounted files under /run/secrets/*, never env vars or build args.
- Shutdown: handles SIGTERM, drains within 20 s; stop grace period 30 s.
- Health: GET /health (liveness), GET /ready (dependencies, SELECT 1).
- Resources: 256 MiB memory, 0.5 CPU, 200 PIDs; justification: <load test link>.
- Trust: image pulled only by digest from registry.example.com/team-prod; signed by release identity.
- Newcomer: `docker compose up --build`; logs via `docker compose logs -f api`.
```

## Graceful shutdown drill

Send `SIGTERM` to the container (`docker stop -t 10`) while a request is in flight and confirm the process drains and exits before the deadline. If it does not, fix signal handling or the entrypoint before calling the image production-ready.

```bash
# terminal 1: a slow request (the endpoint sleeps for 5 s in a test build)
curl -sS -m 20 http://127.0.0.1:8000/slow &
# terminal 2:
time docker stop -t 10 orders-api
wait                              # the curl should have received a full response
docker inspect -f '{{.State.ExitCode}}' orders-api    # expect 0 or 143, not 137
```

## Professional trade-offs

| Decision | Benefit | Cost | When to accept the cost |
| --- | --- | --- | --- |
| Distroless / minimal runtime | Fewer packages and findings | No shell; slower first-time debugging; version-matching pitfalls | Network-facing services with a mature debug procedure |
| Digest pinning | Repeatability; tamper evidence | Needs automated update flow; stale if neglected | Always for releases; set an update SLA |
| Read-only root filesystem | Hinders persistence of an attacker | Apps that write unexpectedly break | Services where writable paths are known; test thoroughly |
| Tight memory limits | Predictable blast radius | OOM kills if sized wrongly | After load testing, with headroom and alerting |
| Strict scan gate | Stops known-bad releases | Pipeline blocks; pressure to bypass | With a fast exception process that has expiries |
| Signing and verification | Provenance, tamper evidence | Key or identity management; policy upkeep | Anything that crosses a trust boundary |
| Promote-not-rebuild | The tested artifact is the deployed one | Requires immutable repositories and tooling | Always for production |
| Private mirror of bases | Resilience, control | Operational cost, staleness | Teams that deploy frequently or have upstream rate limits |

## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| See why a container died | `docker inspect`, `docker events`, exit code, OOM flag | Restarting until it looks fine |
| Shrink and harden an image | Multi-stage, `.dockerignore`, non-root, fewer packages | Building and running as root |
| Debug "connection refused" | Who is localhost? DNS name? Published ports? | Opening every port |
| Keep data | Named volumes plus a backup story | Trusting the writable layer |
| Trust what you deploy | Digest, commit and a scan of that digest | Deploying `:latest` |
| Prove readiness | Separate `/health` and `/ready`, authenticated query | Treating a TCP connect as ready |
| Answer "are we affected by CVE-X?" | Query stored SBOMs by digest | Rescanning everything ad hoc |
| Ship a build credential | `RUN --mount=type=secret` | `ARG`, `ENV` or `COPY` of the credential |
| Release to production | Promote the tested digest | Rebuilding "the same" commit |
| Debug a shell-less image | Debug container joined to its namespaces | Adding a shell to the production image |

## Knowledge consolidation

- Treat the image as a **contract**: identity, contents, provenance, filesystem, resources, lifecycle, observability, trust. Write each clause down and test it.
- **Non-root with numeric IDs**, dropped capabilities, `no-new-privileges` and a read-only root reduce the blast radius; none makes the container a VM boundary.
- **Minimal images** reduce what you patch and explain; they cost debuggability, and version mismatches between build and runtime stages are a classic failure.
- **Tags move, digests do not.** Record commit → image ID → registry digest and deploy by digest; keep an update process so pinned bases do not rot.
- **Scanners find matches, not exploits.** Scan the deployed digest, re-scan on a schedule, triage with evidence, and record expiring exceptions.
- **SBOMs** make "are we affected?" a query. **Provenance** says how it was built; **signatures** say who vouches for which digest; neither says it is correct.
- **Registries** need policy: CI-only push, immutable release tags, retention that protects released digests, promotion by digest.
- **Limits** convert unknown failure into predictable failure: memory kills, CPU throttles silently, PIDs and file descriptors are finite.
- **Diagnose from the outside in**, preserve evidence before restarting, and prefer rollback by digest.

## Exercises

**Exercise 1 — Harden and verify.** Take your `orders-api` image and run it with the hardened flags above. Use `docker inspect` to prove the user, read-only root, dropped capabilities and limits took effect. Then deliberately violate each (write to `/app`, bind to port 80, fork a process loop) and record the failure messages.

**Exercise 2 — Identity chain.** Build, push to any registry (a local registry container is fine), and record commit → local image ID → registry digest. Re-tag different content with the same tag and show that the tag changed while the old digest still resolves.

**Exercise 3 — SBOM and scan.** Generate an SBOM for the pushed digest, scan the SBOM and the image, and write a triage table for the top five findings: package, in runtime image or build stage only, fix available, decision, expiry.

**Exercise 4 — OOM and CPU.** Reproduce an out-of-memory kill with a memory limit, then reproduce CPU throttling with `--cpus 0.2` and a busy loop. For each, list the evidence that distinguishes it from an application bug.

**Exercise 5 — Shutdown drill.** Implement a slow endpoint, run the drill above, and make it pass with an exec-form entrypoint and a handler. Then break it (shell-form `CMD`) and capture the failure.

**Exercise 6 — Write the contract.** Fill in the runtime contract for your service, and have a colleague who has never seen it start the service and read its logs using only that document.

**Solution notes.**

*Exercise 1.* Illustrative expectations: writing to `/app` fails with a read-only filesystem error; with all capabilities dropped and a non-root user, operations such as changing ownership fail with "Operation not permitted"; a process loop stops at the `--pids-limit` with `fork` errors. If a violation *succeeds*, a flag did not apply — read the `docker inspect` output rather than the command you typed.

*Exercise 2.* The local image ID exists before any push and does not equal the registry digest. After re-pushing different content under the same tag, the tag resolves to a new digest while `repo@sha256:<old>` still pulls the old image, until retention deletes it. That is the argument for digests plus a no-delete retention rule on released digests.

*Exercise 3.* A good triage table sorts findings by "present at run time and reachable" first. Findings only in the build stage should be marked non-shipping (and ideally disappear once the runtime stage is minimal). Each accepted exception needs an owner and a future date. Your numbers will depend on the base image and the date; do not expect to match anyone else's list.

*Exercise 4.* An OOM kill shows exit 137 and `OOMKilled=true`. CPU throttling shows *no* exit, a flat CPU use at the limit and rising latency; the throttled counters in the cgroup statistics increase. An application bug usually shows an error in the logs or a specific exit code instead.

*Exercise 5.* With exec form and a handler, the in-flight request completes and the container stops before the timeout with exit code 0 or 143. With shell-form `CMD` or no handler you typically see the full timeout elapse and exit code 137, and the request is cut off. Record your observed durations; these are illustrations, not guarantees.

*Exercise 6.* The test is the newcomer's success without verbal help. Every question they have to ask is a missing line in the document.
