# T-CLD-01-P — Professional Engineering

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-p"></a>
#### T-CLD-01-P — Professional Engineering

## Why this matters

A host that works is not yet a host you can operate. Professional practice means a Linux machine whose configuration is deliberate and reviewable, whose privileges are separated, whose access leaves evidence, whose capacity is watched before it runs out, whose failures are survivable, whose data can be restored and whose problems are handled by documented procedures rather than memory at three in the morning.

This section assumes the Intermediate material: you can run a service under `systemd`, read the journal, reason about ownership and storage and follow a triage sequence. The focus now is on **baselines you can defend**, **privilege separation**, **SSH and audit**, **monitoring and capacity**, **reliability**, **backup and recovery**, **performance method** and **runbooks**. The examples continue with the neutral `orders-api` service (port 8000, data in `/var/lib/orders`, user `orders`). Outputs marked *illustrative* show expected shapes, not measured results. Commands that change a host are written for a disposable machine or a change window with a rollback path.

## First principles: what "production-ready" means for a single host

A production host has to satisfy five properties. Each later section serves one or more of them.

| Property | Question it answers | Mechanisms in this section |
| --- | --- | --- |
| Least privilege | What can an attacker or a mistake reach? | Dedicated users, sandboxed units, sudo rules, mandatory access control |
| Accountability | Who did what, when, from where? | Named accounts, SSH logging, `auditd`, central logs |
| Observability | Can we see trouble before users do? | Metrics, saturation signals, alerts tied to actions |
| Recoverability | Can we get back to a known good state? | Immutable images, backups, restore drills, runbooks |
| Predictability | Will it behave the same tomorrow? | Configuration as code, drift checks, pinned packages, staged updates |

Two principles recur. First, **treat hosts as replaceable**: the strongest recovery plan for a stateless host is to rebuild it from a template, so any manual change must be small, recorded and either automated or discarded. Second, **a control you cannot verify is a hope**: every baseline item below comes with a command that proves it is in effect.

## Secure baselines

A baseline is the written, versioned set of settings every host of a class must have. It is a configuration-management and review artefact, not a one-time checklist. Keep the baseline small enough that people understand it.

| Area | Baseline setting | Verification |
| --- | --- | --- |
| Accounts | Named user accounts; no shared logins; locked or absent passwords for service users | `getent passwd`, `passwd -S <user>`, `awk -F: '$2 == ""' /etc/shadow` (expect no output) |
| SSH | Keys or certificates only, no root login, restricted users | `sshd -T` |
| Packages | Minimal set; security updates automated or images rebuilt | `dpkg -l \| wc -l`, `apt list --upgradable` |
| Services | Only needed services enabled | `systemctl list-unit-files --state=enabled`, `ss -ltnp` |
| Filesystems | Separate or limited writable areas; `nodev,nosuid,noexec` where possible | `findmnt -o TARGET,OPTIONS` |
| Kernel | Conservative network and memory settings | `sysctl -a` compared with the baseline file |
| Time | Synchronised, with an alert on drift | `timedatectl`, `chronyc tracking` |
| Logging | Shipped off-host; journal persistent | `journalctl --disk-usage`, collector status |
| MAC | SELinux or AppArmor enforcing | `getenforce` or `aa-status` |

A sysctl baseline as a drop-in file, reviewed like code:

```ini
# /etc/sysctl.d/60-baseline.conf
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.unprivileged_bpf_disabled = 1
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
vm.swappiness = 10
```

```bash
sudo sysctl --system                         # apply all drop-ins
sysctl net.ipv4.tcp_syncookies kernel.kptr_restrict
```

Hardening can break functionality: a router or a container host needs settings (such as IP forwarding) that a plain server should not have. Record exceptions with their reason, in the baseline, not in someone's head.

**Verifying a baseline continuously.** Run a read-only audit (an assessment tool such as Lynis or OpenSCAP, or your own script) in CI against freshly built images and on a schedule against running hosts. Compare to the baseline and alert on drift, because the interesting question is not "was it hardened on day one?" but "is it still?"

```bash
sudo lynis audit system --quick              # example assessment tool; read its findings, do not apply them blindly
```

## Privilege separation

Separate identities by purpose so that compromise of one does not give everything.

| Identity | Purpose | Rights |
| --- | --- | --- |
| Human administrator (named) | Interactive work | Login by key or certificate; `sudo` for defined commands; session logging |
| Service account | Runs one service | No login shell, no home, no password, no `sudo`; only its data directory is writable |
| Deploy identity | Installs releases | May write release directories and restart one unit; cannot read secrets |
| Backup identity | Reads data to back it up | Read-only access to data paths via ACL, no write, no shell |
| Break-glass account | Emergency access | Credentials sealed, use alerted, rotated after every use |

**Service separation in systemd.** The unit is where privilege boundaries become enforceable:

```ini
[Service]
User=orders
Group=orders
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
CapabilityBoundingSet=
AmbientCapabilities=
ReadWritePaths=/var/lib/orders
UMask=0027
```

An empty `CapabilityBoundingSet=` removes every Linux capability, so the process cannot, for instance, change the clock or bind ports below 1024. If a service legitimately needs one, grant exactly that (`AmbientCapabilities=CAP_NET_BIND_SERVICE`) and record why. `MemoryDenyWriteExecute=true` breaks runtimes that generate code at run time (some JIT-based ones), so test it and apply it per service.

```bash
systemd-analyze security orders-api.service            # exposure score and findings per setting
sudo systemd-run --pty -p User=orders -p ProtectSystem=strict /bin/sh -c 'touch /etc/x'   # expect a read-only error
```

Treat the exposure score as a conversation starter, not a target of zero: remaining findings are decisions to accept, remediate or automate, with an owner.

**sudo as policy.** Use specific commands, not blanket root, and use drop-ins so that package updates do not overwrite your policy:

```text
# /etc/sudoers.d/orders-deploy   (edit with: sudo visudo -f /etc/sudoers.d/orders-deploy)
Cmnd_Alias ORDERS_CTL = /usr/bin/systemctl restart orders-api, /usr/bin/systemctl status orders-api
%orders-deploy ALL=(root) NOPASSWD: ORDERS_CTL
Defaults:%orders-deploy log_output
Defaults logfile="/var/log/sudo.log"
```

```bash
sudo visudo -c                          # syntax check for all sudoers files
sudo -l -U alice                        # what can this user run?
```

Beware commands that permit shell escapes (`vi`, `less`, `find`, `tar`, many interpreters): allowing them under `sudo` is allowing root. Wildcards in sudo rules are also easy to abuse.

**Mandatory access control.** SELinux and AppArmor confine a process beyond file modes. When something is denied, read the denial instead of disabling the control:

```bash
getenforce                                 # Enforcing, Permissive or Disabled
sudo ausearch -m AVC,USER_AVC -ts recent   # SELinux denials
sudo aa-status                             # AppArmor profiles and their modes
journalctl -k | grep -i apparmor | tail
```

If you need an exception, create a narrow policy or boolean for the one action that is required, record the reason and test in permissive mode on a canary only. "Set it to disabled" is not a fix; it removes a layer for the whole host.

## SSH and audit

SSH is the main administrative door, so it needs both hardening and a record of its use.

```text
# /etc/ssh/sshd_config.d/10-baseline.conf
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AllowGroups ssh-users
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
LogLevel VERBOSE
```

```bash
sudo sshd -t                               # syntax check BEFORE reloading
sudo sshd -T | grep -E '^(permitrootlogin|passwordauthentication|allowgroups|maxauthtries)'
sudo systemctl reload ssh                  # unit is "sshd" on some distributions
# keep your current session open; test a second login from another terminal before closing it
```

**Never close your only session while changing SSH.** Open a second connection after each change. A configuration that locks you out of a remote host with no console access is a rebuild.

**Keys and certificates.** Per-person keys scatter across `authorized_keys` files and are hard to revoke. Short-lived **SSH certificates** signed by a certificate authority expire on their own and carry the principal (the allowed username) and a validity window:

```bash
ssh-keygen -s ca_key -I alice@example -n alice -V +8h alice_key.pub     # sign a key valid for 8 hours
ssh-keygen -L -f alice_key-cert.pub                                     # inspect a certificate
```

On servers, `TrustedUserCAKeys /etc/ssh/ca.pub` accepts certificates from that CA. Protect the CA key as one of your most sensitive secrets.

**Reading SSH evidence.**

```bash
journalctl -u ssh --since "1 hour ago" | grep -E 'Accepted|Failed|Invalid'
last -a | head                              # successful logins
sudo lastb | head                           # failed logins (needs privilege)
who -a                                      # who is on right now
```

A public SSH port is attacked continuously; a pile of `Failed password` lines from unknown addresses is background noise, but `Accepted publickey` from an unexpected address or at an unexpected time is an incident trigger.

**auditd.** The Linux audit framework records security-relevant events in the kernel with user and session identity. Use it for evidence, not volume: log what you would want to see after an incident.

```text
# /etc/audit/rules.d/60-baseline.rules
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k privilege
-w /etc/sudoers.d/ -p wa -k privilege
-w /etc/ssh/sshd_config -p wa -k sshd
-w /etc/systemd/system/ -p wa -k units
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=-1 -k root-exec
```

```bash
sudo augenrules --load
sudo auditctl -l                           # active rules
sudo ausearch -k privilege -ts today | aureport -f -i      # who touched sudoers today
sudo aureport --auth --summary             # login summary
```

`auid` is the **login UID**: it stays the original user's ID even after `sudo`, so "root ran this" can be traced to the human who started the session. The `execve` rule above is high volume; enable it on bastions or sensitive hosts, estimate disk and CPU cost first, and ship the result off the host. Audit and journal data that remain only on the machine can be altered by whoever compromises it, so forward them to a central store that the host cannot rewrite.

## Monitoring and capacity

Monitor to answer three questions in order: **are users affected, is the host close to a limit, what changed?** Alerts that do not lead to an action are noise.

**The USE method** gives a short checklist per resource: **U**tilisation (how busy), **S**aturation (how much waiting) and **E**rrors.

| Resource | Utilisation | Saturation | Errors |
| --- | --- | --- | --- |
| CPU | `mpstat -P ALL 1`, `top` | Run-queue length (`vmstat r`), pressure `/proc/pressure/cpu` | Machine-check or throttling events in `dmesg` |
| Memory | `free -h` (available) | Swap activity (`vmstat si/so`), `/proc/pressure/memory` | OOM kills in `journalctl -k` |
| Disk | `iostat -x` (`%util`) | Average queue size and `await` | `dmesg` I/O errors, SMART or cloud volume status |
| Filesystem | `df -h`, `df -i` | Writes failing, inode shortage | `Read-only file system` remounts |
| Network | `sar -n DEV 1`, `ip -s link` | Socket backlog (`ss -ltn` Recv-Q), retransmits (`nstat`) | Interface drops and errors |
| File descriptors | `cat /proc/sys/fs/file-nr` | Per-process: `ls /proc/<pid>/fd \| wc -l` against limits | `Too many open files` in logs |

Pressure Stall Information (PSI) makes saturation directly visible on kernels that provide it:

```bash
cat /proc/pressure/memory
# some avg10=0.00 avg60=0.12 avg300=0.04 total=18423      (illustrative)
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

`some` is the share of time at least one task stalled waiting for the resource; `full` is when all non-idle tasks stalled. Sustained non-zero `full` memory pressure means the host is in real trouble even if utilisation graphs look modest.

**What to expose.** An agent such as `node_exporter` publishes host metrics for a time-series system. Choose a small set of alerts that map to actions:

```yaml
groups:
  - name: host
    rules:
      - alert: DiskWillFillIn4h
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/var/lib/orders"}[1h], 4*3600) < 0
        for: 15m
        annotations:
          action: "Runbook: disk-growth. Find the largest consumer before it fills."
      - alert: InodesLow
        expr: node_filesystem_files_free / node_filesystem_files < 0.10
        for: 10m
      - alert: MemoryPressureSustained
        expr: rate(node_pressure_memory_waiting_seconds_total[5m]) > 0.1
        for: 10m
      - alert: ClockDrift
        expr: abs(node_timex_offset_seconds) > 0.05
        for: 10m
      - alert: UnitFailed
        expr: node_systemd_unit_state{name="orders-api.service",state="failed"} == 1
        for: 1m
```

The `predict_linear` alert warns hours before a disk fills, which is more useful than "disk above 90%" for a volume that grows fast, and a fixed threshold fits a large slow-growing volume better. Use both for different volumes. The `action` annotation links the alert to a runbook; an alert without one is a question handed to whoever is on call.

**Capacity planning.** Capacity is a forecast, not a guess:

1. Pick the limiting resource for the service (CPU, memory, disk, descriptors, connections, ephemeral ports).
2. Record peak and typical usage and growth per week from metrics.
3. State **headroom** as a number: for example "peak CPU 55% of capacity, target at most 70%".
4. Convert growth to a date: `weeks_left = (capacity - peak) / weekly_growth`.
5. Record a review date and the action (resize, add node, reduce work).

```bash
# Example arithmetic with illustrative numbers: 400 GiB volume, 310 GiB used, growing 6 GiB per week.
# weeks to 85% (340 GiB): (340 - 310) / 6 = 5 weeks
awk 'BEGIN { used=310; cap=400; rate=6; limit=0.85*cap; printf "%.1f weeks to 85%%\n", (limit-used)/rate }'
```

Know the ceilings that are not shown on a dashboard until they are hit: `LimitNOFILE`, `TasksMax`, `net.core.somaxconn`, `nf_conntrack_max`, the ephemeral port range and, on cloud hosts, the instance's network and disk burst credits. A burstable volume that runs out of credits slows suddenly, and the symptom looks like application slowness.

## Reliability

**Supervision and restarts.** `Restart=on-failure` with a bounded start limit makes a service self-heal from transient faults without hiding a persistent one. Add a watchdog if the application can implement it, so that a hung (not crashed) process is restarted:

```ini
[Service]
Type=notify
WatchdogSec=30
Restart=on-failure
RestartSec=3
StartLimitIntervalSec=300
StartLimitBurst=5
TimeoutStartSec=60
TimeoutStopSec=30
```

`Type=notify` requires the program to signal readiness (`sd_notify`); `WatchdogSec` requires it to ping periodically. Without that support, use a health check at the load balancer or an external prober instead of inventing a restart rule.

**Graceful shutdown.** `systemd` sends `SIGTERM`, waits `TimeoutStopSec`, then sends `SIGKILL`. A service that ignores `SIGTERM` is killed mid-request every time you deploy. Verify the behaviour:

```bash
time sudo systemctl stop orders-api         # a long delay equals the timeout: SIGTERM is being ignored
journalctl -u orders-api -n 5 --no-pager    # look for "Stopping..." then a clean exit, not "State 'stop-sigterm' timed out"
```

**Failure containment.** Limit what one service can consume so that a runaway process does not take the host with it:

```ini
[Service]
MemoryHigh=900M
MemoryMax=1G
CPUQuota=150%
TasksMax=512
IOWeight=100
OOMPolicy=stop
```

`MemoryHigh` throttles and reclaims before the hard cap; `MemoryMax` is the kill line. Choose the limit from observed peaks plus headroom, not from the machine's size. Set `OOMScoreAdjust=` for critical system services (negative values make them less likely victims) and avoid giving applications a protected score.

**Reboots and updates.** Decide the policy rather than leaving it to chance: apply updates in a maintenance window or by replacement, restart services after library updates, reboot when the kernel changes (or use a live-patching service you have tested), and make sure each service comes back on its own. A **reboot test** (reboot a canary and check units, mounts and health) finds missing `enable`, wrong `fstab` entries and ordering mistakes before an unplanned reboot does.

```bash
systemctl --failed                         # after reboot: anything not running that should be?
systemd-analyze blame | head               # what slowed boot?
needrestart -r l                           # which services still use old libraries? (list only)
```

**Single points of failure.** For each host, write down what happens if it disappears. If the answer is "an outage until someone rebuilds it", the design needs a second instance, automatic replacement or a documented recovery time that the business accepts.

## Backup and recovery

A backup is only real once a restore has been demonstrated.

**Decide what to protect.** Back up **data and state** (`/var/lib/orders`, database dumps or snapshots, configuration that is not in version control, secrets in their own protected system), not the whole machine; the machine is rebuilt from code. Name two numbers per service and get them agreed:

| Term | Meaning | Example |
| --- | --- | --- |
| RPO (recovery point objective) | How much data you can afford to lose, measured in time | 15 minutes |
| RTO (recovery time objective) | How long recovery may take | 1 hour |

The numbers drive the design: a 15-minute RPO means frequent snapshots or log shipping; a 24-hour RPO allows nightly backups.

**Properties of a sound backup.**

- **Off-host and access-controlled:** a backup on the same disk, or one the compromised host can delete, is not protection against loss or ransomware. Use write-once or append-only targets, separate credentials and a different failure domain.
- **Encrypted** before leaving the host, with keys stored apart from the data.
- **Consistent:** a copy of a database taken mid-write can be unreadable. Use the database's own dump or snapshot tooling, or freeze the filesystem briefly.
- **Versioned and retained:** keep daily, weekly and monthly generations, so a corruption noticed late can still be undone.
- **Monitored:** alert when the last successful backup is older than expected.

```bash
# Illustrative: a deduplicating, encrypted backup tool (restic) to an off-host repository
export RESTIC_REPOSITORY=sftp:backup@backup.example.net:/srv/restic/orders
export RESTIC_PASSWORD_FILE=/etc/orders/restic.pass        # root:root, mode 0600
restic backup /var/lib/orders --tag nightly
restic snapshots --compact
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
restic check --read-data-subset=5%                          # verify a sample of stored data
```

**Filesystem snapshots** (LVM, ZFS, or a cloud volume snapshot) are fast and consistent at a point in time, but they live near the original; copy them to another location.

**The restore drill.** Run it on a schedule and write down the result.

```bash
# 1. Restore into a clean, empty location, never over live data
mkdir -p /restore/orders && restic restore latest --target /restore/orders
# 2. Compare against expectations: counts, checksums, and an application-level check
find /restore/orders -type f | wc -l
sha256sum /restore/orders/var/lib/orders/orders.db
# 3. Start a copy of the service against the restored data and call its health endpoint
# 4. Record: backup time, restore duration (measured RTO), data age (measured RPO), issues found
```

The measured restore duration is your real RTO. If it is longer than the agreed one, the plan is wrong, not the number.

**Destructive actions need a safety net.** Before a risky change, snapshot or back up first and confirm the snapshot exists. Never run a destructive command on a host you cannot snapshot or rebuild. Verify scope before a bulk deletion by listing first, and put sensitive volumes behind protection against accidental deletion.

## Performance: a method, not a bag of tricks

Tuning without measurement is superstition. Use a fixed order and change one thing at a time.

1. **Define the symptom in user terms:** slower p95 latency for `/orders`, lower throughput, higher error rate; and when it began.
2. **Check the resource picture (USE)** for CPU, memory, disk, network and descriptors, from the table above. Eliminate resources with low utilisation, no saturation and no errors.
3. **Find the consumer:** which process, which thread, which file or socket.
4. **Form one hypothesis and test it:** change one thing, measure, keep or revert.
5. **Record the baseline and result** so that the next engineer does not repeat the work.

```bash
uptime                                      # load averages: 1, 5 and 15 minutes
vmstat 1 5                                  # run queue, swap, I/O wait, CPU split
mpstat -P ALL 1 3                           # per-CPU: one hot CPU suggests a single-threaded bottleneck
pidstat -u -r -d 1 3                        # per process: CPU, memory, disk
iostat -xz 1 3                              # per device latency and queue depth
ss -s; nstat -az | grep -i -E 'retrans|overflow'
top -H -p <pid>                             # per-thread CPU for one process
```

Interpret **load average** carefully: on Linux it counts runnable tasks and tasks in uninterruptible sleep, so high load with idle CPU usually means I/O waits. Compare load with the number of CPUs (`nproc`), not with a fixed number.

| Observation | Probable meaning | Next step |
| --- | --- | --- |
| High `us` CPU in one process | Application compute | Profile the application |
| High `sy` CPU | Kernel work: system calls, networking, locks | `perf top`, check packet rate |
| High `wa`, idle CPU | Storage waits | `iostat -x`, check volume type and credits |
| `si/so` non-zero | Swapping | Find the memory consumer; fix limits or size |
| Steal time `st` high (virtual machines) | The hypervisor takes your CPU | Resize or move; not tunable in the guest |
| Load high, CPU idle, no I/O wait | Lock contention or blocked tasks | Thread dumps, `D`-state list |

**Safe tuning.** Prefer changing application settings and capacity to changing kernel parameters. When you do change a kernel setting, put it in a `sysctl.d` file with a comment naming the evidence, apply it to a canary and keep the old value in the commit message.

## Runbooks and operational discipline

A runbook is a short, tested procedure for a known situation. It lets someone who was not there when it was written act safely. A good one is:

- **Triggered by an alert or symptom** and linked from it.
- **Read-only first:** diagnosis steps before any change.
- **Explicit about risk:** each changing step names what it does and how to undo it.
- **Tested:** run during a game day, not first during an outage.
- **Owned and dated:** someone reviews it on a schedule and after every incident that used it.

```text
Runbook: orders-api unit failed
Trigger: UnitFailed alert for orders-api.service
Impact: orders cannot be created; reads may still work
Safe first checks (read-only):
  1. systemctl status orders-api --no-pager
  2. journalctl -u orders-api -b -n 100 --no-pager
  3. systemctl show orders-api -p ExecMainStatus -p NRestarts -p Result
Classify:
  203/EXEC, 217/USER, 226/NAMESPACE -> unit or release problem: check path, user, ReadWritePaths
  1/FAILURE with "Permission denied" -> namei -l on the path as the service user
  signal=KILL -> journalctl -k | grep -i oom; compare MemoryMax with peak use
Change (one at a time, record each):
  - Fix cause; systemctl reset-failed orders-api; systemctl restart orders-api
Verify: curl -fsS http://127.0.0.1:8000/health ; check error rate for 10 minutes
Rollback: re-point /opt/orders/current at the previous release; restart
Escalate: if not resolved in 20 minutes, page the service owner
Owner: platform-team   Last tested: 2024-05-20
```

**Operational discipline.**

| Practice | Why |
| --- | --- |
| Change through code or a runbook, not memory | Repeatability |
| Record who changed what and when on shared hosts | Auditability |
| Time-box and log privileged sessions | Accountability |
| Read-only diagnosis first | Safety under pressure |
| One change at a time, with an expected result | Attributable outcomes |
| Never run destructive commands on a host you cannot snapshot or rebuild | Recovery |
| Write the incident timeline as you go | Reviews rely on facts, not recollection |

## Professional trade-offs

| Decision | Option A | Option B | How to choose |
| --- | --- | --- | --- |
| Patching | Replace hosts from fresh images | Patch in place | Replacement removes drift but needs stateless hosts and a build pipeline; patch-in-place is cheaper to start and accumulates risk |
| Hardening depth | Strict sandboxing and syscall filters | Baseline only | Strict profiles reduce blast radius and cost test time; apply them first to internet-facing services |
| Audit volume | Full command auditing | Targeted file and privilege rules | Full auditing is expensive and noisy; use it where the threat model demands it |
| SSH access | Certificates with a CA | Per-user keys | Certificates expire and revoke naturally; they need a CA operation you must protect |
| Backup frequency | Frequent, small | Nightly | Tighter RPO costs storage, I/O and monitoring effort |
| Alerts | Few, symptom-based | Many, cause-based | Cause alerts help diagnosis; symptom alerts protect people from noise |

## Decision guide

| Situation | Do | Don't |
| --- | --- | --- |
| Permission denied | Fix owner, group or mode precisely; verify as the service user | `chmod 777` |
| Service flaps | Read the journal and exit codes; check `NRestarts` | Blind restart loops |
| Disk full | Find the largest consumer (`du -x`), check deleted-open files, fix the cause | Delete random logs |
| Unknown process | Inspect `/proc`, `ss`, unit files; compare with the baseline | Kill it without knowing |
| Fleet drift | Rebuild from the template | Hand-edit servers |
| SELinux or AppArmor denial | Read the denial and write a narrow rule | Disable MAC |
| Need root access for a task | Grant a specific sudo command, log it | Share the root password |
| Backup exists | Restore it into a clean location and measure | Assume it works |
| Performance complaint | Measure with USE, find the consumer, change one thing | Tune kernel knobs at random |

## Knowledge consolidation

- A baseline is a versioned document with a verification command for every line; drift checks keep it true.
- Separate identities by purpose; make service units enforce least privilege with sandboxing and an empty capability set unless one is justified.
- Use sudo for specific commands, avoid shell escapes in sudo rules, and read MAC denials instead of disabling MAC.
- Harden SSH with `sshd -t`, a second session as safety net, short-lived certificates where practical and off-host logs.
- `auditd` records identity through `auid`; target rules at what you would want after an incident and ship results off the host.
- Monitor with USE, including saturation; alert on forecasts for disks and tie every alert to an action.
- Capacity is arithmetic on measured growth with a stated headroom and a review date.
- Reliability combines supervision, graceful shutdown, limits, update policy and reboot tests.
- A backup is proven by a timed restore into a clean place; RPO and RTO are measured, not promised.
- Performance work follows a method: symptom, resources, consumer, one hypothesis, record.
- Runbooks are read-only first, tested and owned.

## Exercises

**Exercise 1 — Baseline with verification.** Write a baseline for a host class with at least eight settings. For each, add the command that proves it. Run the commands on a test machine and record every deviation.

**Exercise 2 — Sandbox the service.** Take the `orders-api` unit, apply the hardening block above and run `systemd-analyze security`. Remove or relax the settings that break the toy program, justify each relaxation in a comment, and write down the final score and the findings you accepted.

**Exercise 3 — Safe SSH change.** On a disposable VM with console access, change `sshd` to the baseline above using a drop-in file. Show the `sshd -t` check, the second-session test and what `sshd -T` reports. Then deliberately set `AllowGroups` to a group you are not in, show the lockout from a new session, and recover using the console.

**Exercise 4 — Audit a sensitive file.** Add an `auditd` watch on a test file, change it as a normal user via `sudo`, and use `ausearch` to show `auid` (the human) and `uid` (root). Explain why this matters when several administrators share `sudo`.

**Exercise 5 — Forecast a disk.** From a week of `df` samples (generate them if needed), compute weeks to 85% and write the alert and action that would fire before then.

**Exercise 6 — Restore drill.** Back up a directory to a second location with a tool of your choice, delete the original, restore into a clean path, verify checksums, and record the measured time. State the RPO and RTO that your result supports.

**Exercise 7 — Write and test a runbook.** Write a runbook for "disk above 90% on /var/lib/orders". Ask a colleague who has not seen the host to follow it while you silently note every place they hesitated, and fix those lines.

**Solution notes.**

*Exercise 1.* Good baselines are short and each line is falsifiable. Typical deviations: an unused service listening on a port, a packaged default that allows password login, a time service not running. A baseline with no verification command is a wish.

*Exercise 2.* Frequent relaxations are `MemoryDenyWriteExecute` (for runtimes that generate code), `SystemCallFilter` (when a rare syscall is needed; widen the group, not the whole filter) and `RestrictAddressFamilies`. The exposure score should fall markedly from the default; the accepted findings, with reasons, are the deliverable.

*Exercise 3.* `sshd -t` catches syntax errors only; it does not catch a policy that excludes you. The second session proves your access. After the deliberate lockout, recovery needs a console or an out-of-band path, which is why the exercise requires one.

*Exercise 4.* `auid` is the original login identity, preserved across `sudo`; `uid` is the effective user, root. Without `auid`, "root edited sudoers" cannot be attributed to a person.

*Exercise 5.* The arithmetic is `(0.85 × capacity − used) / weekly growth`. A good alert uses a forecast over a short window and an action such as "identify the largest consumer and decide: prune, move or grow".

*Exercise 6.* Measured numbers vary. Credit the exercise only if the restore went to a clean location, checksums matched and the time was recorded; a restore over live data hides missing files.

*Exercise 7.* Typical fixes: replace "check the logs" with the exact command, add the expected output, and mark which step changes state and how to undo it.
