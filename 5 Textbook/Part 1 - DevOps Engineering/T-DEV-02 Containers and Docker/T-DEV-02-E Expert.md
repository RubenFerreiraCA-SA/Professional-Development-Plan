# T-DEV-02-E — Expert Depth

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-e"></a>
#### T-DEV-02-E — Expert Depth

**Where the isolation boundary really is.** Containers rely on kernel features shared with every other container on the host. Hardening layers reduce but do not remove that exposure: user namespaces map container root to an unprivileged host user; seccomp filters system calls; Linux security modules (AppArmor, SELinux) constrain file and process access; dropping capabilities removes specific privileges. For workloads that run untrusted code, stronger isolation (sandboxed runtimes with a user-space kernel, or lightweight virtual machines) trades performance and compatibility for a smaller shared-kernel surface. Choose by threat model, not by reflex.

**Failure modes worth knowing**

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Zombie accumulation | PID 1 does not reap children | Init process (`tini`) or fix the application |
| Slow rollouts and dropped requests | `SIGTERM` ignored; shell-form `CMD` | Exec form, signal handling, drain window |
| Disk exhaustion | Unbounded logs, dangling layers, unpruned images | Log rotation limits, scheduled pruning |
| Noisy neighbour | Missing CPU and memory limits | Limits and monitoring |
| Cache poisoning of builds | Unpinned base or dependency fetched at build | Pin by digest, lock dependencies, verify |
| Secret in a layer | `COPY .env` or build argument, even if deleted later | Build secrets; layers are permanent and inspectable |
| Registry deletion | Digests become unresolvable | Mirror, retention policy, backups of release images |

**Reproducible builds.** Identical input should produce identical output: pin base image digests, lock dependency versions (with hashes), avoid fetching "latest" in build steps, normalise timestamps (`SOURCE_DATE_EPOCH`), and use a builder that supports deterministic layer ordering. Full bit-for-bit reproducibility is hard; the practical target is that the same commit always yields the same *behaviour*, and that you can rebuild a past release.

**Layer and cache economics.** Layers are shared by digest, so a small change near the top of a Dockerfile invalidates everything below it. Order instructions from least to most frequently changing; use cache mounts for package managers; separate dependency resolution from code copy; and measure build time in CI rather than assuming caches help. Remember that deleting a file in a later layer does not shrink the image or remove the content from earlier layers.

**Policy for fleets.** At scale, put image rules where they cannot be skipped: CI checks (a linter and a scanner), a registry policy (only signed images, retention) and an admission policy in the orchestrator (digest-only, non-root, trusted registries). Enforcing the same rule at more than one point is not duplication; each point catches what the earlier ones miss.

**Isolation layers: what each one reduces, shown with commands.**

| Control | Reduces | Does not reduce | Example |
| --- | --- | --- | --- |
| User namespaces | Impact of a container-root escape (host UID is unprivileged) | Kernel vulnerabilities reachable by unprivileged users | `dockerd --userns-remap=default` |
| Capability dropping | Privileged operations (raw sockets, mounting, changing ownership) | Bugs in permitted syscalls | `--cap-drop=ALL --cap-add=NET_BIND_SERVICE` |
| seccomp | Reachable kernel attack surface (blocks syscalls such as `mount`, `ptrace`) | Logic flaws in allowed calls | default profile, or a custom allow-list |
| AppArmor / SELinux | File and process access, even for root in the container | Exploits that gain kernel code execution | `--security-opt apparmor=profile` |
| Read-only root filesystem and `no-new-privileges` | Persistence and setuid privilege gain | Memory-only attacks | `--read-only --security-opt no-new-privileges` |

```bash
docker run --rm --read-only --tmpfs /tmp --cap-drop=ALL --security-opt no-new-privileges \
  --user 10001:10001 --memory 256m --pids-limit 100 orders-api@sha256:<digest>
```

**When to go beyond a shared kernel.** Ask: who authors the code, and what is the worst thing it could do if hostile? Internal, reviewed services on a hardened host rarely justify more. Running customer-supplied code, plug-ins or build jobs from untrusted forks does: use a sandboxed runtime with a user-space kernel, or a lightweight VM per workload. The cost is startup time, memory overhead and compatibility gaps (some syscalls or device access will not work). Make the decision from a written threat model.

**Why `docker` group membership equals root.** A user who can talk to the Docker daemon can run `docker run -v /:/host --rm -it alpine chroot /host sh` and obtain a root shell on the host filesystem. Treat that group as `sudo` without a password, audit its members, prefer rootless mode for developer machines and never mount the Docker socket into containers that handle untrusted input.

**Failure modes: detection and fix.**

| Failure | How to detect | Fix and prevention |
| --- | --- | --- |
| Ignored `SIGTERM` | `docker stop` takes the full grace period (default 10 s); exit code 137 | Exec-form `CMD`, handle the signal, drain in-flight work; `docker run --init` |
| Zombie processes | `ps -eo pid,ppid,stat,cmd \| awk '$3 ~ /Z/'` inside the container | Run an init (`tini`) as PID 1, or reap children in the application |
| Disk full | `docker system df`; large `*-json.log` files | `--log-opt max-size=10m --log-opt max-file=3`; scheduled `docker image prune`; separate disk for `/var/lib/docker` |
| Secret in a layer | `docker history --no-trunc <image>`; secret scanners over layers | Use build secrets (`--mount=type=secret`) so values never enter a layer; rotate any exposed secret |
| Build-time poisoning | Build output differs for the same commit | Pin base by digest; lock dependencies with hashes; build in a clean builder |
| Registry loss | Digests in the release record stop resolving | Mirror to a second registry; retention that never deletes released digests; backup of the release manifest |

**Why deleting a file in a later layer does not help.**

```dockerfile
COPY id_rsa /root/.ssh/id_rsa        # layer 5 contains the key
RUN git clone ... && rm /root/.ssh/id_rsa   # layer 6 hides it, layer 5 still has it
```

Anyone with the image can extract layer 5 (`docker save` and untar). The same applies to large temporary files: the image does not shrink. Combine create-and-delete in one `RUN`, use multi-stage builds, or use build secrets.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim@sha256:<digest> AS build
COPY requirements.lock .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --require-hashes -r requirements.lock --target /deps
FROM gcr.io/distroless/python3-debian12@sha256:<digest>
COPY --from=build /deps /deps
COPY app /app
ENV PYTHONPATH=/deps SOURCE_DATE_EPOCH=1700000000
USER 10001
CMD ["/app/main.py"]
```

**Reproducibility, with a verification step.** Build twice from the same commit on clean builders and compare: `docker buildx build --output type=oci,dest=a.tar` twice, then compare image digests. If they differ, find the nondeterminism (timestamps, unsorted file lists, network fetches). A practical goal is "rebuild a past release and behave identically", with the lock file, base digest and builder version all recorded.

**Scanner findings: when "critical" does not apply.** A finding is irrelevant if the vulnerable component is absent at run time (build-stage only), the vulnerable code path cannot be reached, a compensating control blocks the exploit (no network exposure, seccomp denies the syscall), or the finding is a false positive. Defend it with evidence: show the package is not present in the final image (`docker run --rm <image> sh -c 'dpkg -l | grep libx'`), document the reachability analysis, and record an expiry so the decision is revisited. Treat unexplained dismissals as defects.

**Policy points and what each catches.**

| Point | Example rule | Catches what earlier points miss |
| --- | --- | --- |
| Developer machine / CI linter | No `latest`, non-root user, no `ADD` from URLs | Mistakes early |
| CI scanner and signing | Block critical fixable CVEs; sign with identity | Vulnerabilities and provenance |
| Registry | Only signed images; immutable tags; retention | Manual pushes and tag changes |
| Admission in the orchestrator | Digest-only, trusted registries, non-root | Anything deployed outside the pipeline |

**Registry-loss recovery plan.** Keep a release manifest (digest, commit, build time) in Git; mirror release images to a second registry on promotion; test a rebuild-from-source path quarterly; restore by re-pointing the pull source and verifying digests match the manifest.

**Mentoring prompts.** Explain why membership of the `docker` group is a privilege-escalation path. When is a vulnerability scanner's "critical" finding irrelevant to a particular workload, and what evidence would let you defend that claim? What does your organisation lose if the single registry holding all release digests is deleted, and what is the recovery plan?

---
