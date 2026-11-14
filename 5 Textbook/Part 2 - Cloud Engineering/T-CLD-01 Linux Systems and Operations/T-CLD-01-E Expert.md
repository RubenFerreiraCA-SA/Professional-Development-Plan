# T-CLD-01-E — Expert Depth

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-e"></a>
#### T-CLD-01-E — Expert Depth

**Kernel mechanics that explain production behaviour.**

- *Memory:* the page cache makes "free memory" a misleading number; look at available memory, major faults and the out-of-memory killer's scoring. Control groups (cgroups) enforce limits, and a container's limit can be lower than the host's total memory, so the in-container view and the host view differ.
- *Scheduling and CPU:* CPU limits via the completely fair scheduler quota throttle processes rather than kill them; throttling shows as latency, not errors. Check throttling counters.
- *I/O:* queue depth and the I/O scheduler determine tail latency on shared disks; "idle CPU, slow service" is often storage.
- *Networking stack:* connection tracking tables, ephemeral-port exhaustion, TCP backlog and `SYN` queues cause failures that look like network problems yet start on the host.
- *Namespaces and cgroups* are the basis of containers; understanding them removes the mystery from container behaviour (see T-DEV-02).

**Observability from the host.** Tools such as `perf`, eBPF-based tracers and `bpftrace` answer "where is time going" without changing the application. Treat them as read-mostly diagnostics with a cost; run with approval in production and record what you ran.

**Failure modes and cascading effects.**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Fork storm or process exhaustion | Runaway spawner, `TasksMax` unset | Limits, supervision |
| Log flood fills the disk | Unbounded logging | Rotation, rate limits, separate volumes |
| Clock skew | NTP failure | Time-sync monitoring; TLS and token failures often follow |
| Entropy or DNS resolver failures | Slow startups, hangs | Local caching resolver, health checks |
| Noisy neighbour | Shared host without limits | cgroup limits, dedicated nodes for critical workloads |
| Kernel or distribution update surprise | Behaviour change | Canary hosts, staged rollout, rollback images |

**Fleet-scale operations.** At scale you need a source of truth for hosts, automated provisioning, image pipelines with scanning, a patch cadence with staged rollout, and fast replacement. Prefer ephemeral, replaceable infrastructure and keep stateful data on managed or separately protected storage. Define maximum host age and enforce it.

**Evidence: OOM-kill with free memory on the host.** A container with a 512 MiB cgroup limit can be killed even when the host has gigabytes free, because the limit is enforced per cgroup.

```bash
cat /sys/fs/cgroup/<path>/memory.max          # the limit, in bytes (cgroup v2)
cat /sys/fs/cgroup/<path>/memory.current      # current use
cat /sys/fs/cgroup/<path>/memory.events       # oom and oom_kill counters
journalctl -k | grep -i -E 'oom|killed process'
# Memory cgroup out of memory: Killed process 4121 (python3) ... constraint=CONSTRAINT_MEMCG
free -h                                        # host shows plenty available
docker inspect <c> --format '{{.State.OOMKilled}} {{.HostConfig.Memory}}'
```

The tell-tale is `CONSTRAINT_MEMCG` in the kernel log together with a non-zero `oom_kill` counter, while `free -h` looks healthy. In Kubernetes the same event appears as `OOMKilled` with exit code 137 in the Pod's last state.

**CPU saturation versus CFS throttling.**

| Aspect | Saturation | Quota throttling |
| --- | --- | --- |
| Meaning | All CPUs busy; runnable tasks waiting | The cgroup used its quota for the period and is paused until the next one |
| Host CPU usage | High | Possibly low |
| Check | Run-queue length (`vmstat 1`, `uptime` load) | `cpu.stat`: `nr_throttled`, `throttled_usec` increasing |
| User symptom | Everything slow | Latency spikes, especially p99, at regular intervals |
| Fix | Add capacity or reduce work | Raise or remove the CPU limit (keep requests); fix bursts |

```bash
cat /sys/fs/cgroup/<path>/cpu.max     # e.g. "50000 100000" = 0.5 CPU per 100 ms period
cat /sys/fs/cgroup/<path>/cpu.stat
```

A service limited to 0.5 CPU that needs a 200 ms burst is paused for the rest of the 100 ms window after using 50 ms; requests that arrived during the pause wait. That produces latency without errors, which is why throttling is routinely misdiagnosed as "the network is slow".

**Other kernel limits that look like network problems**

| Symptom | Check | Cause and response |
| --- | --- | --- |
| Intermittent connection failures at high rate, `nf_conntrack: table full, dropping packet` in the kernel log | `sysctl net.netfilter.nf_conntrack_count` versus `…_max` | Connection tracking exhausted; raise the limit, shorten timeouts, or avoid tracking where possible |
| `Cannot assign requested address` on outbound calls | `ss -s`; count of `TIME_WAIT`; `sysctl net.ipv4.ip_local_port_range` | Ephemeral-port exhaustion between one client and one destination; reuse connections, widen the range, spread destinations |
| Clients timeout while the server is idle | `ss -ltn` Recv-Q at the listening socket; `nstat -az TcpExtListenOverflows` | Accept backlog full; fix slow accept loops or raise backlog |
| Idle CPU but slow service | `iostat -x 1` (`await`, `%util`), `pidstat -d` | Storage queueing; check disk, noisy neighbour, or log-flood writes |

**Hardening decisions with residual risk.** Run the scoring tools and then decide, finding by finding:

```bash
systemd-analyze security orders-api.service     # exposure score and per-setting findings
sshd -T | grep -E 'permitrootlogin|passwordauthentication|x11forwarding'
```

| Finding | Accept / remediate / automate | Reasoning |
| --- | --- | --- |
| Service runs with a writable `/home` | Remediate: `ProtectHome=true` | No need for home access; low risk to apply |
| `PrivateNetwork=` not set | Accept | The service needs the network; record why |
| `PasswordAuthentication yes` | Automate: configuration management plus a drift check | A recurring, mechanical fix; residual risk is drift |
| Kernel module loading allowed | Accept with compensating control | Needed by the platform; monitor changes |

Record owner, date and residual risk for each accepted finding. An unrecorded acceptance is indistinguishable from an oversight.

**Production diagnostics policy.** Classify tools by cost and risk, and decide in advance what needs approval:

| Class | Examples | Production policy |
| --- | --- | --- |
| Read-only, negligible cost | `ps`, `ss`, `df`, `journalctl` | Allowed |
| Sampling with modest overhead | `perf record -F 99 -g`, `pidstat`, `bpftrace` one-liners with short duration | Allowed with a time limit, an announcement and a record of the command |
| Potentially disruptive | `strace -f` on a busy process, heavy `tcpdump` to disk, `perf` at high frequency, `kill -STOP`, memory dumps containing secrets | Refuse without approval: they can slow the process, fill disks or expose sensitive data |

Record every non-trivial command in the incident timeline, with the reason.

**Fleet decisions.** An immutable-image strategy rebuilds and replaces hosts when patching; the trade-offs are build pipeline cost and the need for stateless hosts. A patch-in-place strategy is cheaper to start but accumulates drift. Whatever the choice, define a maximum host age (for example 30 days), a canary group that receives updates first, a rollback image and an alert for hosts exceeding the age.

**Mentoring prompts.** Explain why a container can be OOM-killed while the host reports plenty of free memory. What is the difference between CPU saturation and CPU throttling in the symptoms users see? Which diagnostics would you refuse to run on a production host without approval, and why?

---
