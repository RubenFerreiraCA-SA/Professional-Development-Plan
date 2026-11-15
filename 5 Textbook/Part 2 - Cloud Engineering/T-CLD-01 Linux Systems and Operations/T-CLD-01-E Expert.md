# T-CLD-01-E — Expert Depth

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-e"></a>
#### T-CLD-01-E — Expert Depth

## Why this level exists

At Professional level you operate hosts with baselines, limits, backups and runbooks. Expert practice starts when the runbook does not match the symptom: latency spikes while every dashboard is green, a container is killed with gigabytes free on the host, load is high and CPU idle, a service stalls for exactly one second at regular intervals. These cases are solved by a **mental model of what the kernel is doing** and by choosing measurements that falsify hypotheses cheaply.

This section builds that model: the kernel and user-space boundary, scheduling, memory, control groups and namespaces, storage and network I/O, profiling with `perf`, flame graphs and system metrics, eBPF as a way to ask the kernel questions safely, a catalogue of hard incidents with the evidence that identifies each, and the trade-offs of tuning. Commands are for a Linux host you own or are authorised to diagnose. Examples use the neutral `orders-api` service. Outputs marked *illustrative* show expected shapes, not measured results; kernel versions and distributions differ in counter names, defaults and tool availability, so verify on your own systems.

## What a process is, from the kernel's side

A process is a set of kernel objects: a task (or several threads, each a task), an address space (page tables), a table of open file descriptors, credentials, namespace memberships and a cgroup. User code runs in **user mode**; to do anything privileged (read a file, send a packet, allocate pages) it makes a **system call**, a controlled transition into the kernel on the same CPU, executed in the context of the calling task.

| Cost event | Rough cost | Consequence |
| --- | --- | --- |
| Function call in user space | Nanoseconds | Free at the scale of requests |
| System call (cheap, such as `getpid`) | Hundreds of nanoseconds | Millions per second per core is possible, thousands of heavy ones are not free |
| Context switch | Microseconds, plus cache and TLB loss | Many runnable threads reduce useful work |
| Minor page fault (page in memory, mapping needed) | Roughly a microsecond | Frequent on start-up and on large allocations |
| Major page fault (page must be read from disk) | Disk latency: from a hundred microseconds to milliseconds | Looks like a random stall |
| Network round trip in a data centre | Tens to hundreds of microseconds | Dominates chatty protocols |

These orders of magnitude are approximate and hardware-dependent; their value is in knowing which tier a symptom belongs to. A process that is slow *and* spends its time in the kernel (high `sy`) suggests system-call or network volume, lock contention or memory management; slow in user mode (`us`) suggests application compute.

```bash
strace -c -f -p <pid>                       # sample system-call counts and time: heavy; short duration only
cat /proc/<pid>/status | grep -E 'voluntary_ctxt_switches|nonvoluntary'
# voluntary_ctxt_switches:  81234   (task blocked: waiting for I/O or a lock)
# nonvoluntary_ctxt_switches: 9021  (task was preempted: competing for CPU)      (illustrative)
cat /proc/<pid>/stat | awk '{print "minflt="$10, "majflt="$12}'
```

The ratio of voluntary to non-voluntary context switches is a useful first split: mostly voluntary means the task waits for something; mostly non-voluntary means it wants CPU and does not get enough.

## Scheduling and the CPU

The default scheduler for ordinary tasks decides who runs on each CPU by tracking how much CPU each task has received relative to its weight (the Completely Fair Scheduler family, replaced in newer kernels by EEVDF with the same user-visible controls). `nice` values change weights; real-time policies (`SCHED_FIFO`, `SCHED_RR`) run ahead of normal tasks and can starve them if misused.

| Concept | What it means | Where you see it |
| --- | --- | --- |
| Run queue | Tasks ready to run on a CPU | `vmstat r`; `/proc/pressure/cpu` |
| Weight and `nice` | Share of CPU under contention | `nice -n 10 cmd`; cgroup `cpu.weight` |
| Quota | Hard cap per period; the group is paused when used up | cgroup `cpu.max` and `cpu.stat` |
| Affinity and cpuset | Which CPUs a task may use | `taskset -cp <pid>`, `cpuset.cpus` |
| NUMA | Memory is closer to some CPUs than others | `numactl -H`, `numastat` |
| Idle states, frequency scaling | Latency to wake a sleeping core | `cpupower frequency-info` |
| Steal time | The hypervisor ran another guest | `st` in `top` and `vmstat` |

**Why CPU is not one number.** "CPU at 40%" can hide a saturated single thread on a many-core host (`mpstat -P ALL 1` shows one CPU at 100%), a cgroup throttled at its quota while the host is idle, or a mixture of `us`, `sy`, `si` (soft interrupts) and `st`. Latency under CPU competition comes from **run-queue delay**, the time a runnable task waits before it gets a CPU; the kernel can report it per task.

```bash
cat /proc/<pid>/schedstat                    # run time, time spent waiting on a run queue, timeslices
# 98234000000 4123000000 53102              run_ns, wait_ns, timeslices          (illustrative)
pidstat -w -u -p <pid> 1 3                   # voluntary and involuntary switches per second, CPU split
perf sched record -- sleep 5 && perf sched latency | head        # scheduling delays (overhead: use briefly)
```

A `wait_ns` that is a large fraction of `run_ns` means the task spends much of its life waiting for CPU. That is saturation, regardless of what the average utilisation says.

**Quota throttling** differs from saturation, and the two are routinely confused:

| Aspect | Saturation | Quota throttling |
| --- | --- | --- |
| Meaning | All CPUs busy; runnable tasks wait | The cgroup used its quota for the period and is paused until the next period |
| Host CPU usage | High | Possibly low |
| Check | Run-queue length (`vmstat 1`), `uptime`, PSI | `cpu.stat`: `nr_throttled`, `throttled_usec` increasing |
| User symptom | Everything is slow | Latency spikes, especially p99, at regular intervals |
| Fix | Add capacity or reduce work | Raise or remove the CPU limit (keep requests), spread bursts |

```bash
cat /sys/fs/cgroup/<path>/cpu.max      # e.g. "50000 100000" = 0.5 CPU per 100 ms period
cat /sys/fs/cgroup/<path>/cpu.stat
# nr_periods 12000  nr_throttled 3400  throttled_usec 2210000000              (illustrative)
```

A service limited to 0.5 CPU that needs a 200 ms burst can use only 50 ms of it in a 100 ms period, then pauses for the remaining 50 ms; the requests that arrived during the pause wait. That is latency without errors, which is why throttling is routinely misdiagnosed as "the network is slow". A multi-threaded service is hit harder: eight busy threads can burn a 50 ms quota in about 6 ms of wall time and then stall for the remaining 94 ms of the period.

## Memory: page cache, reclaim, overcommit and the OOM killer

Linux treats free memory as wasted: it fills spare RAM with the **page cache** (file data), which is reclaimed when applications need memory. `free` therefore misleads; read `MemAvailable` in `/proc/meminfo`, an estimate of memory obtainable without swapping.

```bash
grep -E 'MemTotal|MemAvailable|^Cached|Dirty|Writeback|AnonPages|Slab|SReclaimable|Shmem|SwapTotal|SwapFree' /proc/meminfo
cat /proc/<pid>/smaps_rollup | grep -E 'Rss|Pss|Private|Anonymous|Swap'
vmstat -s | grep -E 'pages (paged|swapped)'
cat /proc/vmstat | grep -E 'pgmajfault|pgscan|pgsteal|allocstall|oom_kill|workingset_refault'
```

| Term | Meaning | Why it matters |
| --- | --- | --- |
| RSS | Pages of the process resident in RAM, including shared | Overcounts when processes share pages |
| PSS | RSS with shared pages divided among sharers | Best per-process attribution |
| Anonymous memory | Heap and stack, not backed by a file | Can only be freed by swapping or killing |
| Page cache | File-backed pages | Reclaimable when clean; dirty pages need writeback first |
| Slab | Kernel object caches | `SReclaimable` can be freed, `SUnreclaim` cannot |
| Working set | Pages a workload actively needs | If it exceeds available memory, refaults and stalls rise |

**Reclaim and pressure.** When free memory falls below thresholds, the kernel wakes `kswapd` to reclaim in the background; if allocation outpaces it, tasks perform **direct reclaim** and stall (`allocstall` counters rise). A workload whose working set barely fits experiences a fall in throughput long before the OOM killer acts, with high `workingset_refault` rates and non-zero PSI memory `some`/`full`. Swap changes the failure mode: a small amount of swap for cold anonymous pages helps; heavy swap activity (`si`/`so`) is a thrashing signal.

**Overcommit.** By default, Linux lets processes allocate more virtual memory than exists (heuristic overcommit, `vm.overcommit_memory=0`). A process pays when it *touches* pages. `fork` of a large process followed by writes copies pages lazily, so a 10 GiB process that forks can fail under strict accounting (`=2`) and succeed under heuristic mode. Strict mode makes failures happen at allocation time (`ENOMEM`), where applications can handle them, at the cost of reserving capacity that may never be used.

**The OOM killer.** When reclaim fails, the kernel selects a victim by `oom_score`, which is driven mainly by resident memory and adjusted by `oom_score_adj` (-1000 exempts a task; +1000 makes it first to die).

```bash
cat /proc/<pid>/oom_score /proc/<pid>/oom_score_adj
journalctl -k -b | grep -E 'Out of memory|oom-kill|Killed process'
# Out of memory: Killed process 4121 (python3) total-vm:..., anon-rss:..., file-rss:..., shmem-rss:...   (illustrative)
```

**Evidence: an OOM-kill with free memory on the host.** A container with a 512 MiB cgroup limit can be killed while the host has gigabytes free, because the limit is enforced per cgroup.

```bash
cat /sys/fs/cgroup/<path>/memory.max          # the limit, in bytes (cgroup v2)
cat /sys/fs/cgroup/<path>/memory.current      # current use
cat /sys/fs/cgroup/<path>/memory.events       # low, high, max, oom, oom_kill counters
cat /sys/fs/cgroup/<path>/memory.stat | grep -E '^(anon|file|kernel|slab|shmem|pgmajfault) '
journalctl -k | grep -i -E 'oom|killed process'
# Memory cgroup out of memory: Killed process 4121 (python3) ... constraint=CONSTRAINT_MEMCG   (illustrative)
free -h                                        # host shows plenty available
docker inspect <c> --format '{{.State.OOMKilled}} {{.HostConfig.Memory}}'
```

The tell-tale is `CONSTRAINT_MEMCG` in the kernel log with a non-zero `oom_kill` counter in `memory.events` while `free -h` looks healthy. In Kubernetes, the same event appears as `OOMKilled` with exit code 137 in the Pod's last state. Remember that a cgroup's `memory.current` includes **page cache** charged to the group; the kernel reclaims cache before killing, so a high number alone is not an emergency, but `memory.events` `high` and `max` counters that climb mean the group is working against its limit.

## cgroups and namespaces by hand

Containers are ordinary processes placed in a **cgroup** (a budget) and in **namespaces** (a private view). You can build the pieces yourself, which removes the mystery.

**Namespaces.** Each namespace type isolates one kind of resource: mount, PID, network, UTS (hostname), IPC, user and cgroup.

```bash
ls -l /proc/self/ns                           # namespace IDs of this shell
sudo unshare --pid --fork --mount-proc --uts bash -c 'hostname isolated; hostname; ps -e | head -3'
# isolated
#   PID TTY          TIME CMD
#     1 pts/0    00:00:00 bash                                                   (illustrative)
sudo lsns -t net                              # network namespaces on the host
sudo nsenter -t <pid> -n ss -ltnp             # run a host tool inside a process's network namespace
sudo nsenter -t <pid> -m -p ps -ef            # mount and PID namespaces of a container, from the host
```

`nsenter` is the expert's bridge: a container image may lack `ss` or `strace`, but the host has them, and `nsenter -t <pid> -n` lets the host's tools inspect the container's network view. The container's PID on the host is visible with `docker inspect -f '{{.State.PID}}' <c>` (or from the runtime).

**cgroup v2** is a single hierarchy under `/sys/fs/cgroup` with controllers enabled per subtree. Every process is in exactly one cgroup.

```bash
cat /proc/<pid>/cgroup                        # which cgroup is this process in?
cat /sys/fs/cgroup/cgroup.controllers         # available controllers
systemd-cgls --no-pager | head -20            # the tree as systemd sees it
systemd-cgtop -n 1                            # live CPU, memory and I/O per cgroup

sudo mkdir /sys/fs/cgroup/lab                 # a cgroup you create (needs privilege)
echo "+memory +cpu +io +pids" | sudo tee /sys/fs/cgroup/cgroup.subtree_control
echo 100M | sudo tee /sys/fs/cgroup/lab/memory.max
echo "20000 100000" | sudo tee /sys/fs/cgroup/lab/cpu.max       # 0.2 CPU
echo 32 | sudo tee /sys/fs/cgroup/lab/pids.max
echo $$ | sudo tee /sys/fs/cgroup/lab/cgroup.procs               # move this shell into it
```

The key interface files:

| File | Controls | Reading it |
| --- | --- | --- |
| `memory.max`, `memory.high` | Hard limit; soft limit that throttles and reclaims | `memory.events` counters show how often each was reached |
| `memory.swap.max` | Swap allowed for the group | `0` means no swap use |
| `cpu.max`, `cpu.weight` | Quota per period; relative share | `cpu.stat` shows throttling |
| `io.max`, `io.weight` | Bandwidth and IOPS limits; shares | `io.stat` per device |
| `pids.max` | Process or thread count | `pids.events` `max` shows fork failures |
| `cpuset.cpus`, `cpuset.mems` | Allowed CPUs and NUMA nodes | Pinning for latency-sensitive work |

A service restarted by `systemd` gets the limits from its unit (`MemoryMax=`, `CPUQuota=`, `TasksMax=`, `IOWeight=`), and `systemctl show -p MemoryMax,CPUQuotaPerSecUSec,TasksMax <unit>` confirms what is live. A cgroup in v2 also has **pressure files** (`memory.pressure`, `cpu.pressure`, `io.pressure`) so that you can see saturation for one workload rather than for the whole host.

**What limits do not do.** CPU weights have no effect when CPUs are idle; memory limits do not limit *kernel* memory that the group causes (partly accounted); namespaces and cgroups are not a security boundary against a kernel flaw (see T-DEV-02 for the container view). A user namespace lets an unprivileged user act as root in a private view, which is a frequent ingredient of kernel exploit chains, so some hardened environments restrict it (`kernel.unprivileged_userns_clone` or `user.max_user_namespaces`).

## Storage and I/O

The path of a write is long: application buffer, system call, page cache, filesystem (journal, allocation), block layer (queues and scheduler), device driver, and finally the device or remote volume. Each layer has its own queue, and latency accumulates wherever a queue is full.

**Buffered I/O returns early.** A `write` normally returns once data is in the page cache (dirty). Writeback to disk happens later, governed by `vm.dirty_background_ratio`, `vm.dirty_ratio` and age timers. `fsync` forces data to stable storage and waits. Databases call it often, so their latency equals storage latency.

```bash
grep -E 'Dirty|Writeback' /proc/meminfo
sysctl vm.dirty_background_ratio vm.dirty_ratio vm.dirty_expire_centisecs
iostat -xz 1 3
# Device  r/s  w/s  rkB/s  wkB/s  r_await  w_await  aqu-sz  %util                (illustrative)
# nvme0n1 120  900  4800   72000   0.4      5.2      4.8    71
```

How to read `iostat -x`:

- **`r_await`, `w_await`**: average time for a request, including queueing, in milliseconds. Compare with what the device can do (fractions of a millisecond for local NVMe; a few milliseconds for network volumes; far more for spinning disks).
- **`aqu-sz`**: average queue length. Latency rises when a queue is deep relative to the device's parallelism.
- **`%util`**: how often the device had at least one request in flight. On a device that handles many requests in parallel (NVMe, cloud volumes), 100% does not mean saturated; look at `await` and the queue.
- **IOPS and throughput limits** on cloud volumes appear as a flat ceiling in `r/s + w/s` or in throughput while `await` climbs.

A **stall pattern**: throughput suddenly stops for one or two seconds, then catches up. Candidates: writeback storms (a large dirty-page burst forcing writers to block), journal commits on a slow device, a volume that exhausted burst credits, or a snapshot or backup process saturating the same device. `/proc/pressure/io` and `biolatency` (below) distinguish them.

```bash
cat /proc/pressure/io
iotop -oPa                                   # per-process I/O (needs privilege and a recent kernel)
pidstat -d 1 3                               # per-process kB read and written per second
sudo biolatency-bpfcc 1 5                    # histogram of block I/O latency (BCC tools; name varies by distribution)
findmnt -o TARGET,SOURCE,FSTYPE,OPTIONS /var/lib/orders
cat /sys/block/nvme0n1/queue/scheduler       # [none] mq-deadline kyber bfq
```

The I/O scheduler matters less than people hope: for fast devices `none` is usually right; `mq-deadline` bounds latency on slower ones. Read-ahead (`blockdev --getra`), filesystem mount options (`noatime`), alignment and volume type decide more than scheduler choice. Directly observed fsync latency is the number a database user feels:

```bash
sudo fio --name=fsync-test --directory=/var/lib/orders/tmp --rw=write --bs=4k --size=64m --fsync=1 --runtime=20 --time_based --output-format=normal
# run on a scratch volume or off-hours: it creates real load                      
```

Run synthetic tests only on non-production volumes or in agreed windows; they consume the same I/O budget as production traffic.

## Network stack limits that look like network problems

| Symptom | Check | Cause and response |
| --- | --- | --- |
| Intermittent failures at high rate, `nf_conntrack: table full, dropping packet` in the kernel log | `sysctl net.netfilter.nf_conntrack_count` versus `net.netfilter.nf_conntrack_max` | Connection tracking exhausted; raise the limit, shorten timeouts or avoid tracking for that traffic |
| `Cannot assign requested address` on outbound calls | `ss -s`; count of `TIME_WAIT`; `sysctl net.ipv4.ip_local_port_range` | Ephemeral-port exhaustion between one client and one destination; reuse connections, widen the range, spread destinations |
| Clients time out while the server is idle | `ss -ltn` Recv-Q on the listener; `nstat -az TcpExtListenOverflows TcpExtListenDrops` | Accept backlog full; fix slow accept loops or raise `somaxconn` and the application's backlog |
| Occasional 1-second or 3-second delays | `nstat -az TcpExtTCPTimeouts`, `ss -ti` retransmits | Retransmission timeouts after packet loss; examine the path and queue drops (`tc -s qdisc`, `ip -s link`) |
| One connection slow, others fine | `ss -ti dst <ip>`: `cwnd`, `rtt`, `retrans` | Loss or a small window on that path; check MTU and offload settings |
| Service slow only during bursts | `softnet_stat` drops: `awk '{print $1, $2}' /proc/net/softnet_stat` | CPU cannot process packets as fast as they arrive: spread interrupts (RSS/RPS) |

```bash
ss -tin dst 203.0.113.10 | head               # per-connection internals: rtt, cwnd, retrans, send queues
nstat -az | grep -E 'Retrans|ListenOverflows|ListenDrops|TCPTimeouts|TCPBacklogDrop'
tc -s qdisc show dev eth0                     # drops at the queueing discipline
ethtool -S eth0 | grep -i -E 'drop|miss|err'  # NIC counters
```

Distinguish the layers: **drops on the NIC or qdisc** are a host capacity or configuration issue; **retransmits** suggest loss somewhere on the path; **listen overflows** are an application accepting too slowly; **conntrack drops** are a kernel table limit. All can look like "the network is flaky" from the client. Wire-level analysis (`tcpdump`) belongs in T-CLD-02 and carries risk (see the diagnostics policy below).

## Profiling: `perf`, flame graphs and system metrics

When metrics say *where the pressure is*, profilers say *what code is responsible*. A sampling profiler interrupts the CPU at a fixed rate (for example 99 times a second, to avoid lock-step with timers), records the call stack and builds statistics.

```bash
sudo perf stat -p <pid> -- sleep 10           # counters: instructions, cycles, context switches, faults
sudo perf record -F 99 -g -p <pid> -- sleep 30   # sample on-CPU stacks of one process for 30 seconds
sudo perf report --stdio --no-children | head -40
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > orders-oncpu.svg   # FlameGraph scripts by Brendan Gregg
```

**Reading a flame graph.** The x-axis is *not* time; it is the alphabetical order of stack frames, with width proportional to the share of samples. The y-axis is stack depth. A wide box means that function (and its callees) was on the stack in a large fraction of samples. Look for the **widest plateaus at the top**: those are where CPU was actually spent. A tall narrow tower is deep but cheap.

| Pattern | Typical meaning | Next question |
| --- | --- | --- |
| Wide plateau in application function | Hot code path | Algorithm or data-structure change? |
| Wide `memcpy`, `malloc` or GC frames | Allocation churn or copying | Reduce allocations, tune the runtime's memory settings |
| Wide kernel frames (`tcp_sendmsg`, `futex`) | System-call or lock cost | Batching, connection reuse, lock contention |
| Many tiny equal towers | Many similar threads | Pool sizing, per-request overhead |
| Missing symbols (hex addresses) | No frame pointers or symbols | Build with frame pointers or install debug symbols; use DWARF unwinding at higher cost |

An **on-CPU** flame graph shows work. It cannot explain a service that is slow because it is *waiting*. For that you need an **off-CPU** view (where threads block, and for how long), which needs the scheduler tracepoints and is usually collected with eBPF (below), or a wall-clock profiler provided by the runtime. Asking "on-CPU or off-CPU?" up front avoids optimising code that is not the bottleneck: if `vmstat` shows idle CPU and the service is slow, an on-CPU profile will mislead.

**System metrics to interpret together.** A single number lies; patterns across metrics tell the story:

| Metrics together | Interpretation |
| --- | --- |
| Load high, CPU `id` high, `wa` high | Tasks blocked on storage; check `iostat` and PSI io |
| Load high, `us+sy` high, run queue above CPU count | CPU saturation; add capacity or reduce work |
| CPU low, latency high, `nr_throttled` rising | Quota throttling, not load |
| `MemAvailable` low, `pgmajfault` and refaults high, PSI memory `some` non-zero | Memory pressure; working set larger than RAM |
| `sy` high, `si` high on one CPU | Network interrupt processing bound to one core |
| `st` high on a VM | Noisy neighbour at the hypervisor; the guest cannot fix it |

## eBPF as a mental model

**eBPF** lets you load small, verified programs into the kernel and attach them to events: function entry and exit, tracepoints, system calls, network hooks. The kernel checks each program for safety (bounded loops, no invalid memory access) before running it, and programs communicate results through maps (counters, histograms) that user space reads. For a diagnostician, that means answering "how often, how long, for whom" **inside the kernel**, with low overhead and without modifying or restarting the target.

Think in three parts:

1. **Event source:** what to observe (`tracepoint:syscalls:sys_enter_openat`, a kprobe on a kernel function, a uprobe in a library, a scheduler tracepoint).
2. **In-kernel aggregation:** count, histogram or stack-sample inside the kernel, instead of copying every event to user space.
3. **Output:** a small summary, not a stream of millions of events.

```bash
# Who opens files, and which files? (rate is usually modest; check before running on a hot host)
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat { printf("%s %s\n", comm, str(args->filename)); }'

# Count system calls by process for 10 seconds
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); } interval:s:10 { exit(); }'

# Latency histogram of read() for one process
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_read /pid == 4121/ { @s[tid] = nsecs; }
                  tracepoint:syscalls:sys_exit_read /@s[tid]/ { @us = hist((nsecs - @s[tid]) / 1000); delete(@s[tid]); }'

# Off-CPU time by stack is available as a ready-made tool: offcputime-bpfcc -p <pid> 10
```

Ready-made tools (the BCC and bpftrace collections, packaged as `bcc-tools` or `bpfcc-tools`) cover the common questions: `execsnoop` (new processes), `opensnoop` (file opens), `biolatency` and `biosnoop` (block I/O), `tcplife` and `tcpretrans` (connections and retransmits), `runqlat` (run-queue latency histogram), `cachestat` (page-cache hit rate), `offcputime` and `profile` (stacks). Use them before writing your own.

**Costs and cautions.** eBPF programs add overhead proportional to event rate: tracing every `read` or packet on a busy host can slow it. Rate-limit by filtering on PID or cgroup, use `interval` to stop after a fixed time and test on a canary first. They need privilege (`CAP_BPF` and `CAP_PERFMON`, or root), expose kernel and process data, and may print file names, arguments or addresses that are sensitive. Kernel versions differ in available probes, so a tool that works on one fleet image may fail on another; record the tool version with the result. Where you set `kernel.unprivileged_bpf_disabled=1` (as in the Professional baseline), only privileged users can load programs.

## Hard incidents: a catalogue with the evidence that identifies each

For each case the pattern is the same: the **symptom**, the **wrong first guess**, the **discriminating evidence** and the **fix**.

| Case | Symptom | Wrong first guess | Discriminating evidence | Fix |
| --- | --- | --- | --- | --- |
| Container OOM with free host memory | Restarts, exit 137, host healthy | "The host is out of memory" | `memory.events` `oom_kill` > 0; kernel log `CONSTRAINT_MEMCG` | Raise the limit to measured peak plus headroom; fix leak |
| CFS throttling | p99 spikes at fixed intervals, CPU graphs low | "Network jitter" | `cpu.stat` `nr_throttled` rising; `throttled_usec` | Raise or remove the CPU limit; reduce thread count |
| Deleted-open file | `df` 100%, `du` small | "Disk leak in the application" | `lsof +L1` shows a deleted file held open | Reopen the log (signal) or restart; fix rotation |
| Inode exhaustion | `No space left on device` with free blocks | "Disk full" | `df -i` at 100% | Remove the producer of tiny files; add inodes by recreating the filesystem if needed |
| Ephemeral-port exhaustion | `Cannot assign requested address` to one destination | "The remote is down" | `ss -s` shows tens of thousands of `TIME_WAIT` to one address | Connection reuse and pooling; widen range |
| Conntrack table full | Random connection failures on a gateway or node | "Flaky provider network" | `nf_conntrack: table full` in `dmesg`; count near max | Raise max, shorten timeouts, bypass tracking |
| fsync stalls | Database latency spikes, CPU idle | "Slow queries" | `iostat` `w_await` high; `biolatency` tail; burst credits exhausted | Faster or provisioned volume; separate WAL |
| Run-queue delay from a noisy neighbour | Latency at random times, host busy with another cgroup | "Application regression" | `runqlat` tail; `cpu.pressure` `some` high for the cgroup | CPU weights, isolation or dedicated node |
| Clock step | TLS and token failures after a certain minute | "Certificate expired" | `chronyc tracking` shows a large offset; `journalctl` shows a time jump | Fix time sync, alert on drift, restart time-sensitive services |
| Thread or PID limit | `fork: Resource temporarily unavailable` | "Memory" | `pids.events` `max` or `TasksMax` reached; `ps -eLf \| wc -l` | Raise limit deliberately; find the leak or spawner |
| Memory fragmentation or THP stalls | Periodic multi-ms pauses | "Garbage collector" | `/proc/vmstat` `thp_*` and compaction counters rising; `perf` shows `compact_zone` | Set transparent huge pages to `madvise`; pre-reserve huge pages where needed |
| Shared-host disk filled by a single cgroup | One tenant's logs fill `/var` | "Disk undersized" | `du -x` and `systemd-cgls` identify the unit | Separate volumes, log rate limits |

**Worked case: p99 spikes every 100 ms.** A service on a 0.5 CPU limit shows p99 latency of 130 ms against a p50 of 8 ms, with spikes in clusters. Host CPU is 20%.

```bash
cat /sys/fs/cgroup/system.slice/orders-api.service/cpu.max
# 50000 100000
grep -E 'nr_periods|nr_throttled|throttled_usec' /sys/fs/cgroup/system.slice/orders-api.service/cpu.stat
# nr_periods 18000  nr_throttled 6400  throttled_usec 321000000              (illustrative)
```

About 36% of periods were throttled. A request arriving in the paused part of a period waits until the next one: up to 50 ms here, and more when several threads cluster. Raising `CPUQuota` to 200% (or removing the quota and keeping a share through `CPUWeight`) should collapse the p99 without any code change. Verify by watching `nr_throttled` stop growing and p99 fall; if p99 does not fall, the throttling was a symptom, not the cause, and the next measurement is `runqlat` and a profile.

**Worked case: "idle CPU, slow service".** Load average 12 on four cores, `us+sy` 8%, `wa` 55%.

```bash
iostat -xz 1 3        # w_await 40 ms, aqu-sz 25 on the data volume              (illustrative)
cat /proc/pressure/io # some avg10=63.2 full avg10=58.9
ps -eo state,pid,comm | awk '$1=="D"' | head
sudo biolatency-bpfcc 1 3      # histogram: tail at 16-64 ms
```

Tasks are blocked in `D` state waiting for the device. The next question is *who* issues the I/O (`pidstat -d`, `biosnoop`), and whether the volume is at its provisioned limit (compare IOPS and throughput with the volume's quota in the cloud console). A profile of CPU would show nothing useful, because the CPU is idle: this is the off-CPU case.

## Hardening decisions with residual risk

Run the scoring tools, then decide finding by finding:

```bash
systemd-analyze security orders-api.service     # exposure score and per-setting findings
sshd -T | grep -E 'permitrootlogin|passwordauthentication|x11forwarding'
```

| Finding | Accept / remediate / automate | Reasoning |
| --- | --- | --- |
| Service runs with a writable `/home` | Remediate: `ProtectHome=true` | No need for home access; low risk to apply |
| `PrivateNetwork=` not set | Accept | The service needs the network; record why |
| `PasswordAuthentication yes` | Automate: configuration management plus a drift check | A recurring, mechanical fix; residual risk is drift |
| Kernel module loading allowed | Accept with a compensating control | Needed by the platform; monitor changes |

Record owner, date and residual risk for each accepted finding. An unrecorded acceptance is indistinguishable from an oversight.

## Production diagnostics policy

Classify tools by cost and risk and decide in advance what needs approval:

| Class | Examples | Production policy |
| --- | --- | --- |
| Read-only, negligible cost | `ps`, `ss`, `df`, `journalctl`, `cat /proc/...` | Allowed |
| Sampling with modest overhead | `perf record -F 99 -g`, `pidstat`, `bpftrace` one-liners with short duration, filtered by PID or cgroup | Allowed with a time limit, an announcement and a record of the command |
| Potentially disruptive | `strace -f` on a busy process, heavy `tcpdump` to disk, `perf` at high frequency, `kill -STOP`, memory dumps containing secrets, `fio` on a live volume | Refuse without approval: they can slow the process, fill disks or expose sensitive data |

Record every non-trivial command in the incident timeline, with the reason, the start and stop times and where the output is stored, and treat captured output (stacks, file names, packets) as sensitive data with a retention limit.

## Tuning trade-offs

Every tunable moves cost from one place to another. Write the trade-off down before changing anything.

| Change | What it buys | What it costs or risks | When it is right |
| --- | --- | --- | --- |
| Raise or remove a CPU quota | Removes throttling latency | Noisy-neighbour exposure | Latency-sensitive service with a reserved share |
| Lower `vm.swappiness` | Keeps anonymous pages in RAM | Less page cache; earlier OOM on tight hosts | Databases with predictable memory |
| Disable swap entirely | No thrashing | OOM kills instead of slow degradation | When fast failure and restart is preferred |
| Transparent huge pages `always` | Fewer TLB misses | Compaction stalls, memory bloat | Large, long-lived heaps that were measured to benefit; otherwise `madvise` |
| Raise `nf_conntrack_max` | Fewer drops | Kernel memory use and longer lookups | Gateways with measured high connection counts |
| Raise `somaxconn` and backlog | Absorbs bursts | Hides slow accept loops | Burst-driven services after fixing the loop |
| Larger `vm.dirty_ratio` | Higher write throughput in bursts | Longer stalls at writeback and more data lost on crash | Tolerant batch workloads |
| `noatime` mounts | Fewer metadata writes | Tools that rely on access time break | Almost all servers |
| CPU pinning and `cpuset` | Predictable latency, cache locality | Stranded capacity, operational complexity | Few, well-understood critical workloads |
| Kernel live patching | Fewer reboots | An additional component to trust and test | Fleets where reboot windows are costly |

**A tuning protocol.** State the hypothesis and the metric that will confirm it; record baseline values; change one setting on one canary; measure for long enough to include a peak; keep, revert or iterate; put the final value in configuration management with the evidence in the commit message. A tuning change that nobody can explain will be removed by the next engineer, or worse, kept for cargo-cult reasons after the hardware changes.

## Fleet-scale operations

At scale you need a source of truth for hosts, automated provisioning, image pipelines with scanning, a patch cadence with staged rollout and fast replacement. Prefer ephemeral, replaceable infrastructure and keep stateful data on managed or separately protected storage. Define a maximum host age and enforce it.

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Fork storm or process exhaustion | Runaway spawner, `TasksMax` unset | Limits, supervision |
| Log flood fills the disk | Unbounded logging | Rotation, rate limits, separate volumes |
| Clock skew | NTP failure | Time-sync monitoring; TLS and token failures often follow |
| Entropy or DNS resolver failures | Slow start-ups, hangs | Local caching resolver, health checks |
| Noisy neighbour | Shared host without limits | cgroup limits, dedicated nodes for critical workloads |
| Kernel or distribution update surprise | Behaviour change | Canary hosts, staged rollout, rollback images |

**Fleet decisions.** An immutable-image strategy rebuilds and replaces hosts when patching; the trade-offs are build-pipeline cost and the need for stateless hosts. A patch-in-place strategy is cheaper to start but accumulates drift. Whatever the choice, define a maximum host age (for example 30 days), a canary group that receives updates first, a rollback image and an alert for hosts exceeding the age. Correlate incidents with fleet changes: the first question on a fleet-wide symptom is "what changed, and where did it change first?"

## Knowledge consolidation

- Every process is kernel objects plus a cgroup and namespaces; a container is the same thing with limits and a private view.
- Cost tiers (user code, system call, context switch, page fault, disk, network) tell you which layer a symptom belongs to.
- CPU has at least four problems that look alike: compute, saturation, throttling and steal. Measure run-queue delay and `cpu.stat`.
- `MemAvailable`, PSS, reclaim counters and PSI describe memory; the OOM killer is the last stage, and cgroup limits create OOMs the host never sees.
- Storage latency accumulates across queues; read `await` and queue size, not just `%util`; `fsync` makes storage latency application latency.
- Several kernel limits (conntrack, ports, backlog, descriptors, PIDs) fail as network or application errors; each has a counter that names it.
- On-CPU profiles show work; off-CPU views show waiting; decide which you need before profiling.
- eBPF answers "how often, how long, for whom" in the kernel; control cost by filtering and bounding duration, and treat output as sensitive.
- Tuning moves cost; record the trade-off, test on a canary and keep evidence.

## Exercises

**Exercise 1 — Throttle yourself.** Create a cgroup with `cpu.max` of `20000 100000`, run a CPU-bound loop inside it and show `top` (about 20% of one CPU), `cpu.stat` (`nr_throttled` rising) and a latency measurement of a small periodic task in the same cgroup. Then raise the quota and compare.

**Exercise 2 — Cause and read an OOM.** In a cgroup with `memory.max=100M` and `memory.swap.max=0`, run a program that allocates 200 MiB. Show `memory.events`, the kernel log line and the process's exit status. Explain why the host's `free -h` showed nothing unusual.

**Exercise 3 — Build a namespace.** Use `unshare` to create a PID and mount namespace, mount a fresh `/proc`, and show that `ps` sees one process. From the host, find the same process and compare its host PID with its PID inside. Use `nsenter` to run `ss` in the network namespace of a container.

**Exercise 4 — Profile and read a flame graph.** Run a small CPU-bound program with one hot function and one cold one. Record with `perf record -F 99 -g`, produce a flame graph and annotate which box is hot and what its width means. Repeat for a program that mostly sleeps and explain why the on-CPU graph is uninformative.

**Exercise 5 — Block I/O under load.** On a scratch volume, run a writer with `fio` or `dd` while measuring `iostat -x 1`, `/proc/pressure/io` and (if available) `biolatency`. Report `await`, `aqu-sz` and `%util`, and state whether the device was saturated or merely busy.

**Exercise 6 — Reproduce port exhaustion.** Open many short-lived connections from one client to one server address and port until you see `Cannot assign requested address`. Record `ss -s` and the port range, then fix it with connection reuse and show the difference.

**Exercise 7 — eBPF with a budget.** Write a `bpftrace` program that counts `openat` calls by process name for 10 seconds. Compare the target's request latency with and without the probe, and state the overhead you measured and your policy for production use.

**Exercise 8 — Diagnose a hard incident from evidence only.** Given only these outputs: `vmstat 1` shows `wa` 50 and `id` 45; `iostat` shows `w_await` 38 ms and `aqu-sz` 20; PSI `io full` is 55; `ps` shows five `D`-state processes; the application CPU profile is flat. State the diagnosis, the next two measurements and one fix.

**Solution notes.**

*Exercise 1.* The loop shows roughly 20% CPU in `top`, since the quota is 20 ms per 100 ms period. `nr_throttled` rises steadily and `throttled_usec` accumulates. A periodic task that must run for 5 ms may complete in 5 ms or wait up to about 80 ms depending on when the quota ran out; the latency distribution has a long tail that disappears when the quota is raised. Measure the p99, not the mean.

*Exercise 2.* The process should end by `SIGKILL` (status 137) when it exceeds 100 MiB; `memory.events` shows `max` and `oom_kill` counts incremented and the kernel log contains `CONSTRAINT_MEMCG`. The host has plenty available because only the cgroup's limit was hit.

*Exercise 3.* Inside the namespace the shell is PID 1 (or `ps` shows one or two processes); on the host the same process has a large PID. `lsns` links the namespace identifier; `nsenter -t <pid> -n ss -ltnp` shows the container's sockets with the host's `ss`.

*Exercise 4.* The hot function should be the widest box near the top; its width is a fraction of samples, not time on the x-axis. For the mostly-sleeping program, few samples land in user code because the process is off-CPU most of the time, so the graph tells you almost nothing about why it is slow; an off-CPU view or a wall-clock profile is needed.

*Exercise 5.* A device with `aqu-sz` much larger than its parallelism and `await` climbing is saturated; a high `%util` with a short queue and low `await` on a parallel device is only busy. Report the three numbers together.

*Exercise 6.* The error appears when the number of sockets in `TIME_WAIT` plus established to one destination approaches the port range. Reusing connections (keep-alive, a pool) lowers the rate of new sockets; widening `ip_local_port_range` only delays the failure.

*Exercise 7.* The overhead depends on event rate; a filter by PID or cgroup and a fixed `interval` keep it small. A defensible policy is "bounded duration, filtered, announced, recorded, canary first, with the output treated as sensitive".

*Exercise 8.* Diagnosis: tasks are blocked on storage, so the service is waiting for the volume (off-CPU), not computing. Next measurements: which process issues the I/O (`pidstat -d`, `biosnoop`) and whether the volume's provisioned IOPS or throughput limit has been reached (cloud metrics, burst credits). Fix: move or isolate the heavy writer, raise the volume's provisioned limits, or separate the latency-sensitive data onto its own volume.

## Mentoring prompts

Explain why a container can be OOM-killed while the host reports plenty of free memory. What is the difference between CPU saturation and CPU throttling in the symptoms users see, and which counters separate them? When is an on-CPU flame graph the wrong tool, and what would you collect instead? Why can `%util` of 100% on a cloud volume mean nothing, and what would you read instead? Which diagnostics would you refuse to run on a production host without approval, and why? Describe a tuning change you would refuse to make without a canary, a metric and a rollback, and say what trade-off it moves.

---
