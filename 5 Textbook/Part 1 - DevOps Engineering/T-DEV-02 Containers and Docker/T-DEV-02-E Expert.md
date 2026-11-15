# T-DEV-02-E — Expert Depth

*Chapter: [T-DEV-02 — Containers and Docker](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-02-e"></a>
#### T-DEV-02-E — Expert Depth

## Why this level exists

Professional practice makes one image production-ready: non-root, minimal, pinned, scanned, signed, limited. Expert practice asks what those controls are *made of*, where they stop working, and how they behave across an organisation of many teams, many architectures, adversarial inputs and an orchestrator that reinterprets half of your Dockerfile. The skill is not recalling flags; it is predicting how an accepted practice fails — under a kernel bug, a compromised dependency, a different CPU architecture, a CPU quota or a deadline — and choosing the cheapest control that addresses the failure that matters.

This section assumes the earlier levels: layers, multi-stage builds, PID 1, health versus readiness, digests, SBOMs, limits. Everything uses the neutral `orders-api` service. Commands assume a Linux host with root access for inspection; outputs labelled *illustrative* show the *shape* you should expect, not measured results — reproduce them yourself before relying on them.

## What a container is made of

A "container" is not one kernel object. It is a *convention* — a process started with a particular combination of kernel features — assembled by a runtime. Seeing the parts is the foundation for judging every isolation claim.

### The runtime stack

```text
docker CLI ──► dockerd ──► containerd ──► containerd-shim ──► runc ──► your process (PID 1 in its namespaces)
 (client)     (engine API,   (image pull,    (keeps the process   (OCI runtime: creates
              build, network) snapshots,      alive if daemons     namespaces/cgroups from
                              lifecycle)      restart)             a config.json, then exits)
```

Two open specifications define the boundaries: the **OCI image specification** (what an image is: a manifest, a configuration, and layer blobs, optionally referenced by an index for several platforms) and the **OCI runtime specification** (what a runtime does with an unpacked root filesystem and a `config.json`). Because of that split you can swap components: an orchestrator may talk to containerd or CRI-O directly with no Docker engine present, and the low-level runtime can be `runc`, `crun`, or an isolating runtime such as gVisor's `runsc` or a Kata Containers runtime.

### Namespaces: what the process sees

| Namespace | Isolates | Practical effect |
| --- | --- | --- |
| `mnt` | Mount table | The container sees its own root filesystem and mounts |
| `pid` | Process IDs | The app is PID 1 inside; the host sees a different PID |
| `net` | Interfaces, routes, ports | Own `lo`, own IP; why `localhost` is the container |
| `uts` | Hostname | Container has its own hostname |
| `ipc` | System V IPC, POSIX message queues | Separate shared-memory segments |
| `user` | UID/GID mapping | Container root can map to an unprivileged host user (not Docker's default) |
| `cgroup` | View of the cgroup tree | The container sees its own cgroup as the root |
| `time` | Some clock offsets | Rarely used |

Look at them directly rather than trusting a diagram:

```bash
docker run -d --name web nginx:1.27
PID=$(docker inspect -f '{{.State.Pid}}' web)
sudo ls -l /proc/$PID/ns            # one symlink per namespace, e.g. net -> net:[4026532xxx]
sudo ls -l /proc/1/ns               # the host's namespaces: different inode numbers
sudo lsns -p $PID                   # a tabular summary
sudo nsenter -t $PID -n ss -ltnp    # run the HOST's ss inside the container's network namespace
```

Comparing the namespace identifiers of two processes tells you whether they share a view; that is exactly how two containers in one Pod share a network identity and how `--network container:<name>` works.

To feel what a namespace is, create one without Docker (as root; the exact output is illustrative):

```bash
sudo unshare --pid --fork --mount-proc --uts sh -c 'hostname demo; hostname; ps -ef'
# inside: hostname prints "demo", and ps lists only this shell and ps itself
hostname                             # back on the host: unchanged
```

(Unprivileged user namespaces, used by rootless tools, may be restricted by distribution policy; the root form above avoids that question.)

### cgroups: what the process may use

Control groups account for and limit resources. On a **cgroup v2** host (check with `stat -fc %T /sys/fs/cgroup`, which prints `cgroup2fs`), one unified hierarchy exposes files that Docker writes when you set a flag:

```bash
docker run -d --name lim --memory 128m --cpus 0.5 --pids-limit 50 alpine:3.20 sleep 600
docker exec lim sh -c 'cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max /sys/fs/cgroup/pids.max'
# illustrative output:
# 134217728
# 50000 100000
# 50
docker exec lim cat /sys/fs/cgroup/memory.events      # counters include oom and oom_kill
docker exec lim cat /sys/fs/cgroup/cpu.stat           # nr_throttled, throttled_usec
```

Reading these values:

- `memory.max` is a hard limit. Exceeding it, after the kernel reclaims what it can, invokes the OOM killer within the group.
- `cpu.max` of `50000 100000` means 50 ms of CPU time per 100 ms period — a **bandwidth quota**, not a reservation and not a pin to half a core. A multi-threaded process can burn its quota in the first part of a period and then be paused until the next one; latency spikes with no error anywhere.
- `pids.max` bounds the process-plus-thread count, stopping fork bombs and thread leaks.
- `memory.events`' `oom_kill` and `cpu.stat`'s `nr_throttled` are the first things to read in an incident; both are counters that survive a restart only if the cgroup does.

A page-cache subtlety: file-backed pages count toward the group's memory use but are reclaimable. A container can look "full" in a graph and be perfectly healthy, or be killed because *unreclaimable* memory (heap, anonymous mappings, tmpfs contents) hit the limit. Read `memory.stat`, not just a single usage number. Files in a `tmpfs` mount count as memory, which is a common surprise with read-only roots and generous `/tmp` sizes.

### Capabilities: root, divided

Traditional "root" is a bundle of dozens of distinct privileges called **capabilities**: bind low ports, change file ownership, load modules, administer mounts, use raw sockets, and so on. A container's root has only a subset; Docker's default set is deliberately modest but still includes things such as `CHOWN`, `SETUID`, `SETGID`, `NET_RAW` and `NET_BIND_SERVICE`.

```bash
docker run --rm alpine:3.20 sh -c 'grep Cap /proc/self/status'
docker run --rm --cap-drop=ALL alpine:3.20 sh -c 'grep CapEff /proc/self/status'   # illustrative: all zeros
docker run --rm --cap-drop=ALL alpine:3.20 chown nobody /tmp                         # illustrative: Operation not permitted
capsh --decode=<hex-value-from-above>                                                # translate the mask to names
```

The strongest posture is **deny by default, add by evidence**: `--cap-drop=ALL`, then add back the single capability whose absence breaks a test, and write the reason down. The most dangerous capability is `CAP_SYS_ADMIN`, so broad that it is often called "the new root"; a container that needs it is rarely a container you can treat as isolated. `--privileged` grants all capabilities, disables seccomp and AppArmor confinement, and exposes host devices.

### Copy-on-write filesystems and what "layer" means on disk

Docker's default storage driver on modern Linux is `overlay2` (OverlayFS). Each image layer is a directory (`lowerdir`s); the container adds an empty `upperdir` for writes and a `merged` view.

```bash
docker info -f '{{.Driver}}'                                 # overlay2 (typical)
docker inspect -f '{{json .GraphDriver.Data}}' web | jq .    # LowerDir / UpperDir / MergedDir
docker diff web                                              # what the upper layer holds
```

Consequences you can predict from the mechanism:

- **Copy-up.** Modifying a large file from a lower layer copies the whole file to the upper layer first. A write-heavy workload on image-layer files is slower and bigger than on a volume.
- **Whiteouts.** Deleting a lower-layer file creates a marker in the upper layer; the data stays in the image. This is the reason that "delete the secret in a later layer" fails.
- **Layer identity.** Layers are addressed by content digest, with a distinction between the *compressed* digest (what the registry stores and the manifest references) and the *uncompressed* `diff_id` (what the image config lists). Layer reuse depends on identical content, so a rebuild with a changed timestamp inside a copied file produces a new layer.
- **Volumes bypass the overlay**, giving direct host filesystem semantics; databases, queues and caches belong there.

You can inspect an image as plain files:

```bash
docker save orders-api:local -o orders-api.tar
mkdir x && tar -xf orders-api.tar -C x && ls x           # manifest.json, config, per-layer content
jq '.[0].Layers' x/manifest.json
```

Anything copied into any layer is recoverable from this archive. That is why secret handling is about *never letting the value enter a layer*, not about cleaning up later.

## The isolation boundary: layers of defence and their limits

Containers rely on kernel features shared with every other container on the host. Hardening layers reduce but do not remove that exposure: user namespaces map container root to an unprivileged host user; seccomp filters system calls; Linux security modules (AppArmor, SELinux) constrain file and process access; dropping capabilities removes specific privileges. For workloads that run untrusted code, stronger isolation (sandboxed runtimes with a user-space kernel, or lightweight virtual machines) trades performance and compatibility for a smaller shared-kernel surface. Choose by threat model, not by reflex.

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

### seccomp in practice

seccomp is a per-process filter on system calls. Docker applies a default profile that is an allow-list-with-exceptions: most syscalls permitted, a few dozen risky ones (those that mount filesystems, load modules, trace other processes, change namespaces without the right capability) denied. A denied call typically returns `EPERM` (or the kernel kills the process, depending on the profile action), which surfaces as a confusing "Operation not permitted" from an application that is not obviously doing anything privileged.

```bash
docker run --rm alpine:3.20 unshare -U true             # illustrative: Operation not permitted (blocked by default profile)
docker run --rm --security-opt seccomp=unconfined alpine:3.20 unshare -U true   # illustrative: may succeed; never ship this
```

A custom profile is a JSON document:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    { "names": ["read", "write", "openat", "close", "futex", "epoll_wait", "..."], "action": "SCMP_ACT_ALLOW" }
  ]
}
```

Writing a minimal allow-list by hand is error-prone; the safe workflow is to trace a real test run to collect the syscalls, start from the default profile, remove obviously unneeded calls, and re-run the full test suite, **including start-up, shutdown, error paths and health checks**, because rarely used paths are where a missing syscall bites in production. Review the profile when the runtime (language version, TLS library) changes. The risk of an over-tight profile is an outage; the risk of `unconfined` is giving up a real defence for convenience. The middle path — default profile, plus targeted additions — is right for most services.

### What none of this covers

| Threat | Why the container controls do not stop it | What does |
| --- | --- | --- |
| Kernel vulnerability reachable via an allowed syscall | The kernel is shared; seccomp only removes some entry points | Patching cadence; a sandboxed or VM-based runtime for untrusted code |
| Runtime vulnerability (the engine or `runc` itself) | The runtime runs with high privilege during container setup | Update the runtime; treat runtime CVEs as emergencies |
| Over-privileged configuration (socket mount, `--privileged`, host PID/network, sensitive host paths) | The operator removed the walls | Admission policy that rejects these settings |
| Side channels (shared CPU caches, memory bandwidth) | Hardware shared between tenants | Dedicated hosts or VM isolation for hostile tenants |
| Application-level compromise (SQL injection, stolen tokens) | Isolation protects the host, not the app's own data and credentials | Least-privilege credentials, network policy, application security |

Public history is instructive: container-escape vulnerabilities have been found in `runc` (for example CVE-2019-5736 and CVE-2024-21626) and kernel flaws reachable from containers (for example Dirty COW and Dirty Pipe). The lesson is not to avoid containers; it is that **host kernel and runtime patch cadence is part of your isolation**, and that "we run as non-root" never replaces it.

### Rootless and user-namespace remapping

The words "rootless" and "userns-remap" are often used loosely. They differ:

| Mode | Daemon runs as | Container root maps to | Notable constraints |
| --- | --- | --- | --- |
| Default rootful | root | host root (restricted by capabilities, seccomp, LSM) | A daemon or runtime flaw is a host-root flaw |
| `--userns-remap` | root | An unprivileged subordinate UID range | Some features (host namespaces, some volume sharing) conflict; shared volumes need ownership planning |
| Rootless engine | An unprivileged user | The user's subordinate UID range; the daemon itself holds no root | See below |

Rootless trade-offs:

- **Networking** goes through a user-space network stack (such as `slirp4netns` or `pasta`) rather than kernel bridges and NAT rules in the host namespace, with a throughput and latency cost and, in some setups, loss of the original client IP.
- **Low ports** are unavailable unless the host's `net.ipv4.ip_unprivileged_port_start` is lowered.
- **Resource limits** need cgroup v2 delegation to the user; without it, limit flags may be ignored or rejected.
- **Storage** may rely on native overlay support in a recent kernel or on `fuse-overlayfs`, with different performance.
- **Ping, some device access, and some volume-sharing patterns** behave differently.

Rootless is an excellent default for developer machines and CI runners that build untrusted code, because the cost of a daemon compromise drops sharply. In production orchestrated environments the same goal is usually pursued through the orchestrator's user-namespace support and node isolation instead.

Why membership of the `docker` group equals root: a user who can talk to the Docker daemon can run `docker run -v /:/host --rm -it alpine chroot /host sh` and obtain a root shell on the host filesystem. Treat that group as `sudo` without a password, audit its members, prefer rootless mode for developer machines and never mount the Docker socket into containers that handle untrusted input. A CI job that "just needs Docker" is the same risk: use rootless builders, a remote build service, or daemonless builders rather than handing a shared runner the host's socket.

### When to go beyond a shared kernel

Ask: who authors the code, and what is the worst thing it could do if hostile? Internal, reviewed services on a hardened host rarely justify more. Running customer-supplied code, plug-ins or build jobs from untrusted forks does: use a sandboxed runtime with a user-space kernel, or a lightweight VM per workload. The cost is startup time, memory overhead and compatibility gaps (some syscalls or device access will not work). Make the decision from a written threat model.

| Workload | Authors | Reasonable isolation | Why |
| --- | --- | --- | --- |
| Internal API, reviewed code | Your team | Hardened containers on patched hosts | Hostile code is not in the threat model; supply-chain controls matter more |
| Multi-tenant SaaS running tenant-written scripts | Customers | User-space-kernel sandbox or lightweight VM per tenant | A shared kernel is the main boundary between tenants |
| CI builders on pull requests from forks | Anyone | Ephemeral VM or rootless, ephemeral, network-restricted builders; no secrets | The job *is* untrusted code with a toolchain |
| Batch jobs processing user files with complex parsers | Your team, hostile *input* | Hardened container, seccomp, no network, short life | Parser bugs are the likely exploit path |

## Multi-platform images

Machines run more than one CPU architecture (`amd64`, `arm64`, and others). An **image index** (also called a manifest list) is a small document that maps platforms to per-platform manifests; the engine picks the entry that matches its own platform. Pulling `python:3.12-slim` on an Arm laptop and on an `amd64` server fetches different image content under one tag.

```bash
docker buildx create --name multi --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t registry.example.com/team/orders-api:1.4.2 --push .
docker buildx imagetools inspect registry.example.com/team/orders-api:1.4.2
# illustrative: lists the index digest and one manifest per platform
```

There are three ways to produce each platform's image, with different costs:

| Approach | How it works | Strength | Weakness |
| --- | --- | --- | --- |
| Emulation (QEMU) | Run foreign-architecture build steps in an emulator | Zero extra hardware; works for any Dockerfile | Slow (often an order of magnitude or more on compute-heavy steps), occasional emulator bugs |
| Native builders | One builder node per architecture, combined by buildx | Fast and faithful | Requires machines of each architecture and secure access to them |
| Cross-compilation | Compile *once* on the build platform, targeting another | Fast; no emulation | Only for toolchains that support it; native dependencies complicate it |

A cross-compiling Dockerfile for a compiled `orders-api` (the build stage runs on the builder's own architecture; only the final copy depends on the target):

```dockerfile
# syntax=docker/dockerfile:1.7
FROM --platform=$BUILDPLATFORM golang:1.23 AS build
ARG TARGETOS TARGETARCH
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=$TARGETOS GOARCH=$TARGETARCH go build -trimpath -o /out/orders-api ./cmd/orders-api

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/orders-api /orders-api
USER 65532:65532
ENTRYPOINT ["/orders-api"]
```

Pitfalls to design for:

- **Tag versus digest semantics.** A tag now points to an index; scanning, signing and recording must be explicit about whether you mean the index digest or a platform digest. Sign the index; scan every platform.
- **Untested architectures.** An image that builds for `arm64` has not been *run* there. Run the test suite per platform, at least a smoke test, on real or emulated hardware.
- **Dependencies with native code.** Language packages with compiled components may have prebuilt wheels or binaries only for some platforms, silently compiling from source (slowly, with a compiler you did not plan to ship) on others.
- **`musl` versus `glibc`.** Alpine-based images behave differently; a binary built for glibc fails with misleading "not found" errors on musl.
- **Attestations are extra manifests.** SBOM and provenance attached by the builder appear as additional entries in the index; some tools and registries display or copy them badly. Test your promotion pipeline with them present.
- **Cache keys per platform.** Registry-backed caches should be keyed so one platform's build does not evict another's.
- **Behavioural drift.** Differences in floating-point, memory ordering assumptions or page size can surface only on one architecture; treat "works on `amd64`" as untested for `arm64`.

## Supply-chain attacks on the container pipeline

Think of the pipeline as a graph of trusted inputs: base image, OS packages, language packages, build tools, build scripts, CI actions, the builder, the registry, the deploy tooling. An attacker needs to compromise one node that you trust more than you verify.

| Vector | Mechanism | Controls |
| --- | --- | --- |
| Mutable tag substitution | A tag you depend on is repointed (by compromise, by mistake, or by the publisher) | Pin by digest; mirror bases you rely on; verify signatures with pinned identity |
| Malicious or typosquatted base image | A look-alike repository publishes a trojaned image | Allow-list registries and namespaces; admission policy; prefer verified publishers |
| Dependency confusion and typosquatting | Package manager prefers a public package that shadows an internal name | Scoped/namespaced packages; index pinning; lock files with hashes; private-index-only builds |
| Compromised upstream release | A maintainer account or build process publishes a backdoored version (the 2024 `xz` backdoor, CVE-2024-3094, is the well-known example, caught before wide distribution in stable systems) | Delay adoption of brand-new versions; reproducible builds; behavioural diffs on upgrades; SBOM to find exposure quickly |
| Build-script and CI-action compromise | A third-party script or action is changed to exfiltrate secrets (compromised CI scripts and a widely used GitHub Action have both been publicly reported) | Pin actions and scripts by commit/digest; minimal secrets in CI; no secrets on untrusted triggers; egress control |
| Poisoned build cache | Cache content is attacker-controlled and reused | Cache keys that include inputs; scoped, write-restricted caches; never share caches between trust levels |
| Registry credential theft | A long-lived push token is stolen and used to overwrite or add images | Short-lived scoped credentials; CI-only push; immutable release tags; audit logs |
| Insider or bypass | A privileged human pushes outside the pipeline | Signature enforcement at admission; no manual push path for release repositories |
| Unsafe build commands | `curl … \| sh`, `ADD https://…`, unpinned downloads | Linter rules; pinned and checksummed downloads |

**Frameworks as vocabulary.** SLSA (Supply-chain Levels for Software Artifacts) describes progressively stronger guarantees about build integrity: that provenance exists, that it is generated by the build platform rather than by the build script, and that the build is isolated and cannot be influenced by other builds. Use it to *state what you guarantee* rather than as a badge. Attestations in the in-toto format are the common container for "a statement about this digest".

**A realistic hardening sequence**, ordered by cost-effectiveness:

1. Pin everything by digest or hash; add an *automated, reviewed* update path.
2. Build only in ephemeral, isolated builders; deny the build network except to declared mirrors where feasible.
3. Separate untrusted-code builds from release builds; release builds hold the only signing identity.
4. Generate SBOM and provenance in the builder, sign the index digest, store the evidence beside the release record.
5. Enforce at the boundary that matters: the orchestrator admits only digests signed by the release identity.
6. Plan for the day it fails: an inventory (SBOM store), a way to revoke and redeploy, and an incident runbook.

A control you cannot *verify* is a belief. After each step, attempt the attack on a staging environment (push an unsigned image; repoint a tag; add a package with a mismatched hash) and confirm it is stopped.

## Failure modes worth knowing

| Failure | Mechanism | Mitigation |
| --- | --- | --- |
| Zombie accumulation | PID 1 does not reap children | Init process (`tini`) or fix the application |
| Slow rollouts and dropped requests | `SIGTERM` ignored; shell-form `CMD` | Exec form, signal handling, drain window |
| Disk exhaustion | Unbounded logs, dangling layers, unpruned images | Log rotation limits, scheduled pruning |
| Noisy neighbour | Missing CPU and memory limits | Limits and monitoring |
| Cache poisoning of builds | Unpinned base or dependency fetched at build | Pin by digest, lock dependencies, verify |
| Secret in a layer | `COPY .env` or build argument, even if deleted later | Build secrets; layers are permanent and inspectable |
| Registry deletion | Digests become unresolvable | Mirror, retention policy, backups of release images |

**Failure modes: detection and fix.**

| Failure | How to detect | Fix and prevention |
| --- | --- | --- |
| Ignored `SIGTERM` | `docker stop` takes the full grace period (default 10 s); exit code 137 | Exec-form `CMD`, handle the signal, drain in-flight work; `docker run --init` |
| Zombie processes | `ps -eo pid,ppid,stat,cmd \| awk '$3 ~ /Z/'` inside the container | Run an init (`tini`) as PID 1, or reap children in the application |
| Disk full | `docker system df`; large `*-json.log` files | `--log-opt max-size=10m --log-opt max-file=3`; scheduled `docker image prune`; separate disk for `/var/lib/docker` |
| Secret in a layer | `docker history --no-trunc <image>`; secret scanners over layers | Use build secrets (`--mount=type=secret`) so values never enter a layer; rotate any exposed secret |
| Build-time poisoning | Build output differs for the same commit | Pin base by digest; lock dependencies with hashes; build in a clean builder |
| Registry loss | Digests in the release record stop resolving | Mirror to a second registry; retention that never deletes released digests; backup of the release manifest |
| Silent CPU throttling | Latency up, CPU flat at limit; `nr_throttled` rising in `cpu.stat` | Raise or remove the CPU limit (keep a request); size worker counts to the quota |
| Page-cache or `tmpfs` OOM | `memory.events` shows `oom_kill`; `tmpfs` usage in `memory.stat` | Account for tmpfs in the budget; cap tmpfs size; investigate with `memory.stat` |

**Why deleting a file in a later layer does not help.**

```dockerfile
COPY id_rsa /root/.ssh/id_rsa        # layer 5 contains the key
RUN git clone ... && rm /root/.ssh/id_rsa   # layer 6 hides it, layer 5 still has it
```

Anyone with the image can extract layer 5 (`docker save` and untar). The same applies to large temporary files: the image does not shrink. Combine create-and-delete in one `RUN`, use multi-stage builds, or use build secrets.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm@sha256:<digest> AS build
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

## Reproducible builds, with a verification step

Identical input should produce identical output: pin base image digests, lock dependency versions (with hashes), avoid fetching "latest" in build steps, normalise timestamps (`SOURCE_DATE_EPOCH`), and use a builder that supports deterministic layer ordering. Full bit-for-bit reproducibility is hard; the practical target is that the same commit always yields the same *behaviour*, and that you can rebuild a past release.

Verify, do not assume. Build twice from the same commit on clean builders and compare: `docker buildx build --output type=oci,dest=a.tar` twice, then compare image digests. If they differ, find the nondeterminism.

```bash
docker buildx build --provenance=false --sbom=false \
  --build-arg SOURCE_DATE_EPOCH=1700000000 \
  --output type=oci,dest=a.tar,rewrite-timestamp=true .
docker buildx build --no-cache --provenance=false --sbom=false \
  --build-arg SOURCE_DATE_EPOCH=1700000000 \
  --output type=oci,dest=b.tar,rewrite-timestamp=true .
sha256sum a.tar b.tar                      # tar files can differ for trivial reasons; compare the manifests
mkdir a b && tar -xf a.tar -C a && tar -xf b.tar -C b
diff <(jq -S . a/index.json) <(jq -S . b/index.json) && echo "same top-level digest"
```

(Support for timestamp rewriting depends on the BuildKit version; consult your builder's documentation. Attestations are disabled above because provenance includes build-specific data and would differ by design.)

Typical sources of difference: timestamps in files and archives, unsorted directory listings or archive entries, package manager metadata (apt lists), compiled-in build paths and times, random identifiers, network fetches that returned different content, locale and time zone. Fix them one at a time: sort inputs, clean metadata, remove the fetch (vendor or pin it), pass `-trimpath`-style flags to compilers. Keep a log of what you fixed; the next regression will have the same suspects.

When bit-for-bit is not reachable, record enough to rebuild *behaviourally*: lock file, base digest, builder version, build arguments, commit. "Rebuild a past release and behave identically" is a testable property; run it quarterly.

## Layer and cache economics

Layers are shared by digest, so a small change near the top of a Dockerfile invalidates everything below it. Order instructions from least to most frequently changing; use cache mounts for package managers; separate dependency resolution from code copy; and measure build time in CI rather than assuming caches help. Remember that deleting a file in a later layer does not shrink the image or remove the content from earlier layers.

At fleet scale, caching is an architecture decision:

- **Shared cache is a trust boundary.** A cache populated by untrusted builds and read by release builds is a poisoning path. Keep separate caches per trust level and restrict write access.
- **Layer granularity versus pull time.** Many tiny layers add per-layer overhead; one huge layer defeats reuse when a small thing changes. Group by change frequency: OS, language runtime, dependencies, application.
- **Base-image fan-out.** If hundreds of images share one base, a base update triggers hundreds of rebuilds. Schedule and rate-limit them, and make "rebuild all consumers of base X" a tooling operation rather than a project.
- **Measure the pipeline, not the Dockerfile.** Time per stage in CI, cache hit rate, bytes transferred. Publish the numbers; engineers optimise what they can see.

## Performance and footprint

Footprint is not only the number in `docker images`. Think in the phases of a cold start: **pull** (network and decompression), **unpack** (filesystem work), **runtime start-up** (language and framework initialisation), **application warm-up** (connections, caches, JIT). Each phase is optimised differently, and the right target depends on which dominates your deployments.

| Lever | Helps | Costs / risks |
| --- | --- | --- |
| Smaller runtime image | Pull and unpack time, patch surface | Debuggability; compatibility (`musl`) |
| Fewer, better-ordered layers | Cache reuse, pull parallelism | Build-file complexity |
| Static binary on distroless or `scratch` | Smallest footprint, few findings | You own CA certificates, time-zone data, user; no shell |
| Lazy-loading image formats (such as eStargz or SOCI-style indexes) | Start before the whole image is downloaded | Requires snapshotter and registry support; first-run reads are slower |
| Pre-pulled or cached images on nodes | Removes pull time from the critical path | Staleness; node storage |
| Application start-up optimisation (class data sharing, ahead-of-time compilation, lazy imports) | Start-up latency | Build complexity; risk of stale caches |
| Volumes or `tmpfs` for hot writes | Avoids copy-up and overlay overhead | Persistence and memory accounting considerations |
| Host networking | Removes NAT and bridge overhead | Loses network isolation and port independence; avoid for untrusted workloads |

Runtime-awareness problems are the most common hidden performance bug:

- **CPU count.** Many runtimes size thread pools and worker counts from the number of CPUs they can see, which on a container is often the *host's* count rather than the quota. Twenty workers sharing half a CPU of quota throttle each other. Set concurrency explicitly from the quota (or use a runtime version that understands cgroup limits) and verify under load.
- **Memory.** Garbage-collected runtimes need headroom between heap and the cgroup limit for non-heap memory, thread stacks and native allocations. Set heap limits relative to the container limit, not equal to it.
- **Thread and connection pools** multiplied by replica count can exhaust a database. Size them as a fleet-level budget.
- **Logging** to a slow driver can block application threads; the non-blocking logging mode avoids this at the cost of possible log loss when the buffer fills. Choose consciously.

How to measure without fooling yourself: record the environment (kernel, engine version, storage driver, CPU, cold versus warm cache), repeat runs, report ranges rather than a single best time, and compare variants **on the same host in the same session**. Publish neither numbers you did not measure nor numbers measured on a laptop as if they described production. The tools are plain: `docker image inspect -f '{{.Size}}'`, `docker history`, `docker stats`, timing `docker run` to the first successful health response, and the cgroup files above.

## Orchestrators: what changes when something else runs your container

An orchestrator schedules containers onto machines, restarts them, connects them and rolls out new versions. It reinterprets parts of what you wrote for a single engine, so know the mapping and the gaps.

| Single engine / Compose | Kubernetes-style orchestrator | Gotcha |
| --- | --- | --- |
| `docker run` flags (`--user`, `--cap-drop`, `--read-only`) | `securityContext` fields on the Pod and containers | Image defaults do not enforce policy; admission rules do |
| `HEALTHCHECK` in the Dockerfile | Liveness, readiness and startup probes defined on the workload | The Docker `HEALTHCHECK` is generally **ignored** by Kubernetes |
| `restart:` policy | Controller-managed replicas plus per-Pod restart policy | Crash-loop back-off appears as increasing delays between restarts |
| `--memory`, `--cpus` | Resource requests and limits | Requests drive scheduling; limits drive cgroup enforcement; QoS class affects eviction order |
| `stop_grace_period` | `terminationGracePeriodSeconds` and optional `preStop` hook | Endpoint removal and `SIGTERM` happen concurrently; a draining server must keep serving briefly |
| Named volume | PersistentVolumeClaim | Ownership via `fsGroup`; different access modes |
| Compose project network | Cluster networking plus network policies | Names resolve through cluster DNS and Services, not container names |
| Environment and secrets | ConfigMaps and Secrets | Secrets as environment variables share the same leakage routes as before |
| Single container | A **Pod**: containers sharing network and IPC namespaces (and optionally others) | Sidecars share `localhost` and the Pod's lifecycle |

An illustrative Pod fragment expressing the same runtime contract as the Professional section:

```yaml
spec:
  terminationGracePeriodSeconds: 30
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: api
      image: registry.example.com/team/orders-api@sha256:<digest>
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities: { drop: ["ALL"] }
      resources:
        requests: { cpu: "250m", memory: "192Mi" }
        limits:   { memory: "256Mi" }
      readinessProbe: { httpGet: { path: /ready, port: 8000 }, periodSeconds: 5 }
      livenessProbe:  { httpGet: { path: /health, port: 8000 }, periodSeconds: 15 }
      lifecycle:
        preStop: { exec: { command: ["sleep", "5"] } }   # let load balancers stop sending new requests
```

Points an expert holds in mind:

- **The orchestrator does not make an image safe.** It makes policy *enforceable*. Admission controls (digest-only, signed, non-root, no privileged, trusted registries) are where earlier controls become unskippable.
- **Request versus limit is a policy choice.** Requests schedule; limits throttle (CPU) or kill (memory). Many teams set memory limits equal to requests, and CPU requests without CPU limits, to avoid silent throttling while keeping fairness through shares. Decide per workload and justify it.
- **Liveness probes can cause outages.** A liveness probe that depends on a slow dependency restarts healthy processes during a dependency blip. Liveness should test the process, not its dependencies; readiness tests dependencies.
- **Rollouts rely on your shutdown behaviour.** `SIGTERM` handling, grace periods and readiness flip are your contract with the rollout controller. The shutdown drill is a prerequisite for safe automated deploys.
- **Scale multiplies small mistakes.** A retry without back-off, a connection pool of 50, a base-image rebuild — multiplied by replicas, they become incidents.
- **Kubernetes does not need Docker Engine.** It talks to a CRI runtime such as containerd or CRI-O. Debugging then uses the runtime's tools and the orchestrator's debug features (ephemeral containers) rather than `docker` commands on the node.
- **Compose is not a miniature cluster.** It is an excellent local contract; do not equate "works in Compose" with "works under an orchestrator".

## Policy for fleets

At scale, put image rules where they cannot be skipped: CI checks (a linter and a scanner), a registry policy (only signed images, retention) and an admission policy in the orchestrator (digest-only, non-root, trusted registries). Enforcing the same rule at more than one point is not duplication; each point catches what the earlier ones miss.

| Point | Example rule | Catches what earlier points miss |
| --- | --- | --- |
| Developer machine / CI linter | No `latest`, non-root user, no `ADD` from URLs | Mistakes early |
| CI scanner and signing | Block critical fixable CVEs; sign with identity | Vulnerabilities and provenance |
| Registry | Only signed images; immutable tags; retention | Manual pushes and tag changes |
| Admission in the orchestrator | Digest-only, trusted registries, non-root | Anything deployed outside the pipeline |

Policy design principles for experts:

1. **Make the safe path the easy path.** A paved road (templated Dockerfiles, a blessed base image, a reusable pipeline) beats a rulebook.
2. **Every rule has an exception process with an expiry.** Without one, teams route around the rule invisibly.
3. **Roll out in audit mode first.** Measure how many existing workloads would be rejected before enforcing; announce the date; enforce.
4. **Version your policy and test it.** Policy is code: unit-test it with images that must pass and images that must fail.
5. **Measure drift.** Report workloads running by tag, as root, unsigned, or older than the maximum base-image age.

## Scanner findings: when "critical" does not apply

A finding is irrelevant if the vulnerable component is absent at run time (build-stage only), the vulnerable code path cannot be reached, a compensating control blocks the exploit (no network exposure, seccomp denies the syscall), or the finding is a false positive. Defend it with evidence: show the package is not present in the final image (`docker run --rm <image> sh -c 'dpkg -l | grep libx'`), document the reachability analysis, and record an expiry so the decision is revisited. Treat unexplained dismissals as defects. Machine-readable exceptions (such as a VEX statement saying "not affected" with a justification) let the decision travel with the artifact and be audited.

## Case catalogue

### Case 1 — The clean scan and the compromised build

A team gates on a scanner and still ships a backdoored dependency, because the vulnerability database had no entry for it. The scan answered "known vulnerabilities", not "trustworthy provenance". Lesson: scanning and provenance are complementary; hash-locked dependencies, delayed adoption of new versions and behavioural diffing on upgrade address the unknown.

### Case 2 — The tag that moved on Friday

A deployment manifest references `orders-api:1.4`. A rebuild for an unrelated patch re-pushes the same tag with a changed base layer; nodes that pulled earlier and nodes that pull now run different code. Lesson: immutable tags in release repositories and digest-only admission make "which version is running?" answerable from the manifest.

### Case 3 — The healthy container that lied

Rollouts succeed because the readiness probe checks a TCP port. The database credentials were rotated; every request fails while the Pods are "ready". Lesson: readiness must exercise the dependency path; test readiness by breaking the dependency in staging.

### Case 4 — Latency spikes with no errors

A service with a half-core CPU limit and twenty worker threads shows periodic latency bursts. `cpu.stat` shows rising throttling; reducing workers to match the quota or removing the CPU limit (keeping a request) removes the bursts. Lesson: quota is a bandwidth limit; concurrency must be sized to it.

### Case 5 — The registry that was also the backup

All release digests live in one registry account. A mistaken retention rule deletes untagged manifests, which includes the older releases referenced only by digest. Rollback fails. Lesson: retention must protect everything in the release record, and a second copy must exist elsewhere.

## Registry-loss recovery plan

Keep a release manifest (digest, commit, build time) in Git; mirror release images to a second registry on promotion; test a rebuild-from-source path quarterly; restore by re-pointing the pull source and verifying digests match the manifest.

```bash
# Quarterly drill (illustrative): can we restore from the mirror and verify?
docker buildx imagetools inspect mirror.example.net/team/orders-api@sha256:<digest> > /dev/null && echo "mirror resolves"
docker pull mirror.example.net/team/orders-api@sha256:<digest>
docker image inspect -f '{{index .RepoDigests 0}}' mirror.example.net/team/orders-api@sha256:<digest>
```

## Expert trade-offs

There is no best configuration; there are trade-offs you can state and defend.

| Axis | One end | Other end | How an expert decides |
| --- | --- | --- | --- |
| Isolation versus performance and compatibility | Shared-kernel hardened containers | VM or user-space-kernel sandbox | Threat model: who authors the code and what input is hostile |
| Minimalism versus debuggability | `scratch` or distroless | Full distribution image | Existence of a rehearsed debug procedure; incident cost of blindness |
| Pinning versus freshness | Everything by digest | Floating tags | Update automation and maximum age; never floating in production |
| Strict policy versus delivery speed | Block on any finding | Advisory only | Gate on *fixable, reachable, severe*; fast expiring exceptions |
| Rootless versus compatibility | Rootless everywhere | Rootful with controls | Rootless for untrusted-build hosts and developer machines; evaluate network and storage costs |
| Reproducibility versus effort | Bit-for-bit builds | Behavioural reproducibility | Regulated or high-trust software justifies the effort; otherwise record inputs and test rebuilds |
| Shared caches versus integrity | One fast shared cache | Isolated caches per trust level | Never share between untrusted and release builds |
| Fleet uniformity versus team autonomy | One paved road | Everyone chooses | Strong defaults, documented exits with owners |
| Limits versus availability | Tight limits everywhere | No limits | Memory limits with headroom, CPU requests without blanket limits, measured under load |
| Multi-platform breadth versus test cost | Every architecture, always | Only what you run | Support what you deploy and test; remove what you do not |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the control is cargo cult.

## Knowledge consolidation

- A container is a **convention** assembled by a runtime from namespaces (view), cgroups (budget), capabilities, seccomp and an LSM (privileges), and an overlay filesystem (layers). Each part can be inspected on the host.
- **cgroup limits behave differently**: memory kills, CPU throttles silently, PIDs fail forks. Read `memory.events`, `memory.stat` and `cpu.stat` first.
- Isolation controls **reduce reachable surface**; none removes the shared kernel. Runtime and kernel patching are part of your boundary. Choose stronger isolation by **threat model**.
- `docker` group membership and a mounted socket are **host root**. Rootless reduces the cost of a daemon compromise but changes networking, ports, storage and limits.
- A multi-platform tag is an **index**; scan, test and record per platform, and sign the index deliberately.
- Supply-chain defence is a **graph problem**: pin, isolate builders, separate trust levels, generate and verify provenance, enforce at admission, and rehearse recovery.
- **Reproducibility** is verified by rebuilding and comparing; record inputs even when bit-for-bit is out of reach.
- Footprint is **cold-start phases and runtime awareness**, not just image size; measure honestly.
- An orchestrator makes policy **enforceable** and reinterprets parts of your contract (health checks, limits, shutdown). Know the mapping.
- Every control has a cost and a failure signal; state both.

## Exercises

**Exercise 1 — Map the container by hand.** Start `orders-api` with a memory limit, CPU limit and PID limit. From the host, list its namespaces, find its cgroup directory, read `memory.max`, `cpu.max` and `pids.max`, decode its effective capabilities, and show the overlay directories. Produce a one-page table linking each Docker flag you used to the kernel object it changed.

**Exercise 2 — Threat-model three workloads.** For (a) an internal API, (b) a service running customer-supplied scripts, and (c) a CI runner building forks, write a half-page threat model each: assets, attacker, entry points, the boundary you rely on. Choose isolation (hardened container, rootless, sandbox runtime, VM) and justify the cost.

**Exercise 3 — Seccomp trace.** Run the service with a profile-tracing approach or by temporarily switching to a deliberately minimal profile in a test environment. Identify two syscalls your service uses at start-up and two used only on error paths. Explain why testing only the happy path would have missed the latter.

**Exercise 4 — Multi-platform.** Build and push an index for two architectures. Record the index digest and each platform digest, run a smoke test for each platform, and describe what you would sign and what you would scan.

**Exercise 5 — Reproducibility experiment.** Build the same commit twice on clean builders. Report whether manifests match. If not, list differences and the fix for each. If you cannot make them match, describe the behavioural-reproducibility evidence you will keep instead.

**Exercise 6 — Attack your own pipeline.** In a staging environment, try each of: pushing an unsigned image, repointing a release tag, adding a dependency whose hash does not match the lock file, and building with a modified base digest. For each, record whether it was stopped, *where*, and what evidence proves it.

**Exercise 7 — Throttling hunt.** Run a multi-worker service under a CPU limit, generate load, and show latency bursts alongside `nr_throttled`. Fix it two ways (fewer workers; different limit strategy) and compare tail latency across at least five runs per variant.

**Exercise 8 — Registry-loss tabletop.** Walk through the loss of the primary registry: who declares the incident, which release record you use, how you restore from the mirror, how you verify digests, and what you do about images built after the last mirror sync.

**Solution notes.**

*Exercise 1.* Expected mapping: `--memory` → `memory.max`; `--cpus` → `cpu.max` (quota and period); `--pids-limit` → `pids.max`; `--cap-drop` → capability masks in `/proc/<pid>/status`; image layers and writable layer → the overlay `LowerDir`/`UpperDir`; network flags → a network namespace visible through `/proc/<pid>/ns/net`. Paths and driver names differ by host (cgroup v1 versus v2, systemd versus cgroupfs driver); if a file is missing, check the cgroup version first.

*Exercise 2.* A strong answer states the *attacker's capability* before the control. For (a) hardened containers on patched hosts plus supply-chain controls is usually proportionate. For (b) a shared kernel is the tenant boundary, so a user-space-kernel sandbox or lightweight VM is justified despite compatibility cost. For (c) ephemeral, isolated builders with no long-lived secrets matter more than any single flag. Marks go for naming the cost accepted, not for choosing the strongest option.

*Exercise 3.* Typical start-up syscalls involve opening files, memory mapping, creating sockets and threads; error paths may involve unusual file operations, signal handling or diagnostic calls. Your lists will depend on the runtime version; the finding that matters is that rare paths exist and must be exercised in testing before a tight profile ships.

*Exercise 4.* You should see one index digest and one manifest digest per platform. Signing the index covers the tag consumers pull; scanning must cover each platform because package sets can differ. If the smoke test on one platform fails while the build succeeded, that is the point of the exercise.

*Exercise 5.* Common differences are timestamps, ordering of archive entries and package-manager metadata. A "no difference" result on the first attempt is possible for a simple static binary; a difference you cannot remove is a legitimate outcome if you document the cause and your compensating evidence. Do not claim reproducibility you have not demonstrated.

*Exercise 6.* Each attack should be stopped at the earliest point that has the information to stop it: unsigned push at the registry or admission, tag repoint at immutability rules, hash mismatch at the dependency installer, modified base at review or a digest allow-list. If one attack succeeds, that is a finding, not a failure of the exercise; record which layer needs the rule.

*Exercise 7.* Expect throttling counters to rise during the bursts and fall away once concurrency matches the quota, or once the CPU limit is replaced by a request. Tail latency (not the mean) is where the difference shows; report ranges across runs and avoid single-run conclusions.

*Exercise 8.* Look for: a release record held outside the registry, a second registry with a verified copy, a rule to treat images newer than the last sync as rebuild-from-source with the recorded inputs, and an explicit statement that every restored digest is compared to the manifest before deployment.

## Mentoring prompts

Explain why membership of the `docker` group is a privilege-escalation path. When is a vulnerability scanner's "critical" finding irrelevant to a particular workload, and what evidence would let you defend that claim? What does your organisation lose if the single registry holding all release digests is deleted, and what is the recovery plan? Which of your controls would still hold if a kernel vulnerability reachable from an unprivileged container were announced tomorrow, and which depend on the shared kernel being trustworthy? Pick one rule from your fleet policy and explain what it costs a team that follows it correctly.

---
