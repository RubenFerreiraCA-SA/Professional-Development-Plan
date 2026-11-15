# T-CLD-01-I — Intermediate Practice

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-i"></a>
#### T-CLD-01-I — Intermediate Practice

## Why this matters

At the Beginner level you learned to look at a Linux host: who you are, what runs, what listens, what is full. At the Intermediate level you start to *operate* one. That means running a service under supervision, reading its logs by time and by failure, managing storage and ownership deliberately, scheduling recurring work, checking the network from the host's point of view, and following a repeatable diagnostic sequence instead of guessing.

The central skill is turning a vague report ("the API is down") into a short chain of verified facts: the unit is in state `failed`; its main process exited with status 203; the journal shows that the binary path is wrong; the path is wrong because a release symlink points at a deleted directory. Every step in that chain is a command with output you can quote.

Assumptions: you can complete the Beginner guided session, and you have a Linux host or virtual machine where you may use `sudo` (a disposable VM is ideal). The examples use the fictional `orders-api` service, which listens on port 8000 and keeps data in `/var/lib/orders`. Outputs marked *illustrative* show expected shapes, not measured results.

## Project layout used below

```text
/opt/orders/bin/orders-api          the program (owned by root, mode 0755)
/etc/orders/db.env                  secrets in KEY=value form (root:root, mode 0600; loaded by systemd)
/etc/orders/app.conf                non-secret settings (root:orders, mode 0644)
/var/lib/orders/                    writable data (orders:orders, mode 0750)
/var/log/orders/                    optional file logs (orders:orders, mode 0750)
/etc/systemd/system/orders-api.service
```

The pattern is deliberate: **code is owned by root and not writable by the service**, **configuration is readable by the service**, and **only the data directory is writable**. If an attacker takes over the service, they inherit that small set of rights.

## First principles: identity, ownership and the access decision

When a process opens a file, the kernel compares the process's identity (effective UID, effective GID and supplementary groups) with the file's owner, group and mode bits and picks **exactly one class**: if the UID matches the owner, the owner bits apply and nothing else is consulted; otherwise, if any of the process's groups matches the file's group, the group bits apply; otherwise the "others" bits apply. This is why a file with mode `060` can be unreadable to its owner and readable to the group.

Three more mechanisms change the picture:

| Mechanism | What it does | Where it matters |
| --- | --- | --- |
| `umask` | Subtracts bits from the mode of newly created files | A service creating files with `0644` when you wanted `0640` |
| Setgid on a directory (`chmod g+s`) | New files inherit the directory's group | Shared directories where a team or service group needs access |
| ACLs (`setfacl`, `getfacl`) | Add per-user or per-group entries beyond owner/group/others | One extra reader without changing the group |

```bash
umask                                   # typically 0022 for users, often 0077 for services
sudo install -d -o orders -g orders -m 0750 /var/lib/orders
sudo chmod g+s /var/lib/orders          # new files keep group "orders"
getfacl /var/lib/orders                 # shows ACL entries, if any
sudo setfacl -m u:backup:rx /var/lib/orders   # let a backup account read, without joining the group
```

An ACL appears as a `+` after the mode in `ls -l`. When permissions seem impossible ("the mode says it should work"), check for ACLs, for a missing `x` on a parent directory, and for a mandatory access control layer such as SELinux or AppArmor, whose denials are logged separately.

```bash
namei -l /var/lib/orders/orders.db       # every path component with owner and mode
sudo -u orders test -r /etc/orders/app.conf && echo "orders can read app.conf"
sudo -u orders test -w /var/lib/orders && echo "orders can write the data directory"
```

**Ownership repair, safely.** Before you run `chown -R`, list what will change and verify the scope:

```bash
find /var/lib/orders ! -user orders -o ! -group orders | head     # what would change?
sudo chown -R orders:orders /var/lib/orders
```

Never run `chown -R` or `chmod -R` against `/`, `/etc`, `/usr` or a variable that may be empty; permissions on system directories are not recoverable by guesswork. If you must repair a system path, restore it from the package manager (`dpkg --verify`, `rpm -V`) rather than inventing modes.

## Users and groups for services

Run each service as its own unprivileged user, with no login shell and no home directory unless it needs one:

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin orders
sudo install -d -o root -g orders -m 0750 /etc/orders
sudo install -o root -g root -m 0600 /dev/null /etc/orders/db.env
getent passwd orders
id orders
```

`--system` allocates a low UID and, on most distributions, no ageing. The `install` command creates the file and sets owner, group and mode in one step, avoiding the short window where a new secret file has the wrong mode. Give the service group read access to the configuration files the program opens itself, and nothing more. A file loaded through `EnvironmentFile=` is read by systemd as root, so it can stay `root:root` with mode `0600`.

For people, use named accounts, a group for administrators and `sudo` rules that record who did what; never share one account. `last`, `lastb` and `journalctl _COMM=sshd` show login history, which you will meet again at Professional level.

## systemd in depth

`systemd` is PID 1 on most distributions. It starts **units**. The unit types you use most are **service** (a process), **timer** (a schedule), **socket**, **mount** and **target** (a named group, such as `multi-user.target`).

```ini
[Unit]
Description=Orders API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=orders
Group=orders
WorkingDirectory=/var/lib/orders
EnvironmentFile=/etc/orders/db.env
ExecStart=/opt/orders/bin/orders-api --port 8000
Restart=on-failure
RestartSec=2
TimeoutStopSec=20
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/orders
PrivateTmp=true
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Read it as a contract:

| Setting | Meaning | Common mistake |
| --- | --- | --- |
| `After=` / `Wants=` | Ordering and soft dependency; `After` orders, `Wants` requests | Believing `After=` alone starts the dependency |
| `Type=simple` | The process in `ExecStart` is the service | Using `simple` for programs that fork into the background (use `forking` with a PID file, or better, a foreground mode) |
| `User=` / `Group=` | Identity of the service | Forgetting that data and config must be readable by it |
| `EnvironmentFile=` | Loads `KEY=value` lines into the environment; systemd reads the file as root before dropping privileges | Quoting, `export` and shell syntax do not apply; and the service user needs no read access to this file, only to files the program opens itself |
| `Restart=on-failure` | Restart after non-zero exit or signal, not after clean exit | Expecting a restart after `exit 0` (use `always`) |
| `ProtectSystem=strict` | Mounts most of the filesystem read-only for the service | Forgetting `ReadWritePaths=` for data and log directories |
| `LimitNOFILE` | Open-file limit for the process | Raising a limit in a shell and expecting the service to see it |

The standard working loop:

```bash
sudo systemctl daemon-reload                 # re-read unit files after editing
sudo systemctl enable --now orders-api       # start now and at boot
systemctl status orders-api --no-pager
systemctl cat orders-api                     # the unit as systemd sees it, including drop-ins
systemctl show orders-api -p MainPID -p ExecMainStatus -p NRestarts -p ActiveEnterTimestamp
sudo systemctl edit orders-api               # create a drop-in override without editing the vendor file
systemd-analyze verify /etc/systemd/system/orders-api.service
```

Prefer **drop-ins** (`systemctl edit`) over editing a packaged unit, so a package update does not overwrite your change. `systemd-analyze verify` catches typos before they cause an outage. `systemctl reload` is only meaningful if the unit defines `ExecReload=`; otherwise use `restart`.

**Reading status.** The status header has three facts: `Loaded:` (is the unit file found, enabled?), `Active:` (running, failed, inactive, or `activating (auto-restart)`) and `Main PID:` with the exit status of the last run.

```text
● orders-api.service - Orders API
     Loaded: loaded (/etc/systemd/system/orders-api.service; enabled; preset: enabled)
     Active: activating (auto-restart) (Result: exit-code) since Mon 2024-06-03 10:14:01 UTC; 1s ago
    Process: 4410 ExecStart=/opt/orders/bin/orders-api --port 8000 (code=exited, status=203/EXEC)
   Main PID: 4410 (code=exited, status=203/EXEC)    (illustrative)
```

`status=203/EXEC` means systemd could not execute the file at all. That is a different class of problem from the program starting and then failing.

| Status in `systemctl status` | Meaning | First thing to check |
| --- | --- | --- |
| `203/EXEC` | `ExecStart` could not be executed | Path exists, is executable (`ls -l`), correct interpreter line; `noexec` mount |
| `200/CHDIR` | `WorkingDirectory` missing or not enterable | `namei -l` on the path as the service user |
| `217/USER` | `User=` does not exist | `getent passwd <user>` |
| `226/NAMESPACE` | Sandboxing could not set up mounts | A `ReadWritePaths=` path that does not exist |
| `1/FAILURE` (or other small code) | The program itself ran and exited | The journal: this is the program's own error |
| `signal=KILL` | Killed by `SIGKILL` | Out-of-memory killer, `TimeoutStopSec` expiry, or an operator |
| `start-limit-hit` | Too many restarts inside the burst window | Fix the cause, then `systemctl reset-failed` |

**Restart loops.** `Restart=on-failure` with `RestartSec=2` will restart a broken service every two seconds. systemd stops after `StartLimitBurst` (default 5) restarts in `StartLimitIntervalSec` (default 10 seconds) and marks the unit `failed` with `start-limit-hit`. The loop is a symptom; the fix is in the journal, not in a longer `RestartSec`.

**Dependencies.** `After=network-online.target` waits until the network is configured, but it does not prove that the database accepts connections. A service must still retry its dependencies; ordering is not readiness.

**Timers.** A timer unit replaces a cron entry with logging, dependency control and `Persistent=true` catch-up after downtime:

```ini
# /etc/systemd/system/orders-cleanup.timer
[Unit]
Description=Nightly orders cleanup

[Timer]
OnCalendar=*-*-* 02:30:00
RandomizedDelaySec=300
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
systemctl list-timers --all
systemd-analyze calendar "*-*-* 02:30:00"      # check what the schedule expression means
```

## journald: reading logs by time, unit and priority

`journald` collects output from services (stdout and stderr), the kernel and syslog. It stores structured entries that you filter, not just a text file.

```bash
journalctl -u orders-api -n 100 --no-pager
journalctl -u orders-api --since "2024-06-03 10:00" --until "2024-06-03 10:30"
journalctl -u orders-api -p warning..alert         # priority filter
journalctl -u orders-api -b                        # current boot only
journalctl -u orders-api -b -1                     # previous boot, useful after a crash or reboot
journalctl -k -b --no-pager | tail -50             # kernel messages (OOM kills, disk errors)
journalctl -u orders-api -o json-pretty -n 1       # structured fields available to filter on
journalctl _PID=4410 --no-pager                    # all messages from one PID
journalctl --disk-usage
```

Facts that save incidents:

- **Persistence.** If `/var/log/journal` does not exist, many systems keep the journal in memory only, so logs vanish at reboot. Set `Storage=persistent` in `/etc/systemd/journald.conf` (or create the directory) where you need logs across reboots, and limit growth with `SystemMaxUse=`.
- **Rate limits.** A noisy service can lose messages. Look for `Suppressed N messages` in the journal.
- **Time zones.** `journalctl` shows local time; use `--utc` when comparing with other systems.
- **Boundaries.** `journalctl -b -1` shows the previous boot; the last lines before a silent stop are often the best evidence.

```bash
sudo journalctl --vacuum-time=14d      # delete entries older than 14 days
sudo journalctl --vacuum-size=500M     # cap total size
```

Applications that also write plain files need **log rotation**. A typical `logrotate` rule:

```text
/var/log/orders/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 orders orders
    sharedscripts
    postrotate
        systemctl kill -s HUP orders-api.service
    endscript
}
```

```bash
sudo logrotate --debug /etc/logrotate.d/orders     # dry run: shows what would happen
```

A process holding a deleted log file open continues to write to it and the space is not freed. `lsof +L1` lists open files with link count zero, which finds this.

## Storage: devices, filesystems, mounts and capacity

Think of storage in layers, bottom to top: a **block device** (a disk or cloud volume), an optional **partition table** or logical volume, a **filesystem** (ext4, xfs), and a **mount point** in the directory tree.

```bash
lsblk -f                                  # devices, filesystems, labels, UUIDs and mount points
findmnt /var/lib/orders                   # which mount serves this path, with options
df -hT /var/lib/orders                    # size, used, available and filesystem type
df -i /var/lib/orders                     # inode usage
du -xh --max-depth=1 /var | sort -h | tail
sudo blkid                                # UUID of each filesystem
```

Why `df` and `du` disagree: `df` reports what the filesystem has allocated, including deleted-but-open files and reserved blocks; `du` adds up the files it can see. A large `df` and a small `du` usually means a deleted file is still held open (`lsof +L1`) or that a mount hides files underneath it.

**Mounting.** A persistent mount is listed in `/etc/fstab`. Use UUIDs, not device names, because names such as `/dev/sdb` can change between boots or after attaching another disk.

```text
# /etc/fstab (illustrative line)
UUID=3b1f0d7a-0000-4c1e-9a55-111122223333  /var/lib/orders  ext4  defaults,noatime,nofail  0  2
```

```bash
sudo mount -a                  # applies fstab; errors appear now rather than at the next boot
findmnt --verify               # checks fstab for mistakes
```

An erroneous `fstab` line can stop a machine booting into normal mode. Test with `mount -a` and keep a console or recovery path before rebooting. `nofail` lets boot continue if a non-critical volume is missing. `noexec` on a mount prevents running programs from it, which explains `203/EXEC` for a binary placed in `/tmp` or a hardened data volume.

**Capacity problems have more than one dimension:**

| Resource | Symptom | Check | Typical cause |
| --- | --- | --- | --- |
| Blocks | `No space left on device`, writes fail | `df -h` | Logs, core dumps, caches, data growth |
| Inodes | `No space left on device` with free blocks | `df -i` | Millions of tiny files, session or cache directories |
| Deleted-open files | `df` high, `du` low | `lsof +L1` | Rotated or deleted log held by a running process |
| I/O saturation | Slow, not full | `iostat -x 1`, `iotop` | Noisy neighbour, backup, runaway logger |

**Growing safely.** Observe (`lsblk`, `df`), snapshot, grow the volume at the provider, grow the partition (`growpart`), grow the filesystem (`resize2fs` for ext4, `xfs_growfs` for XFS), verify with `df -h` and record the change. Growing is usually online; shrinking is risky and not supported for XFS.

## Networking tools from the host

The question "is it the network?" has host-side answers you can collect before you involve anyone else.

```bash
ip -br addr                               # interfaces and addresses, one line each
ip route                                  # default gateway and routes
ip -s link show eth0                      # errors and drops on an interface
ss -ltnp                                  # what listens (TCP)
ss -tn state established | head           # current connections
ss -s                                     # socket totals by state
getent hosts db.internal                  # resolves like applications do (uses nsswitch)
dig +short db.internal                    # asks DNS directly
resolvectl status                         # which resolvers and domains are in use (systemd-resolved)
curl -sv --max-time 5 http://127.0.0.1:8000/health -o /dev/null
nc -vz db.internal 5432                   # TCP connect test (host and port)
```

Match the tool to the layer so that you can say *where* a request stops:

| Layer | Question | Tool | A "no" looks like |
| --- | --- | --- | --- |
| Address | Does the host have an address and a route? | `ip -br addr`, `ip route` | No default route; interface `DOWN` |
| Name | Does the name resolve, and to what? | `getent hosts`, `dig` | `NXDOMAIN`, timeout, or an unexpected address |
| Transport | Can a TCP connection open? | `nc -vz`, `curl -v` | `Connection refused` (nothing listening) vs timeout (blocked or unreachable) |
| Application | Does the service answer correctly? | `curl` with status and body | `5xx`, wrong body, TLS error |
| Local listener | Does the service listen where expected? | `ss -ltnp` | Bound to `127.0.0.1` only, or not at all |

The difference between **refused** and **timed out** is the single most useful network clue. Refused means the packet reached a machine that had no listener: the host is up and the port is closed. A timeout means silence: a firewall dropped it, the route is wrong or the target is down.

Host firewalls (`nft list ruleset`, `ufw status`) and cloud security groups are separate layers; report what you saw (a timeout from this source to this port), not "the firewall blocks us". Name resolution, TLS and cloud networking continue in T-CLD-02.

## Cron and scheduled work

`cron` runs commands on a schedule. A crontab line has five time fields and a command:

```text
# minute hour day-of-month month day-of-week  command
30 2 * * *   /opt/orders/bin/cleanup.sh >> /var/log/orders/cleanup.log 2>&1
*/5 * * * *  /opt/orders/bin/heartbeat.sh
```

```bash
crontab -l                  # your user's jobs
sudo crontab -u orders -l   # another user's jobs
ls /etc/cron.d /etc/cron.daily
grep CRON /var/log/syslog | tail          # Debian family; or: journalctl -u cron
```

Cron jobs fail for repeatable reasons:

| Failure | Why | Fix |
| --- | --- | --- |
| "Works in my shell, not in cron" | Cron runs with a minimal environment and a short `PATH` | Use absolute paths; set `PATH=` at the top of the crontab |
| Silent failure | Output is mailed or discarded | Redirect both streams to a log, or use a timer which logs to the journal |
| Overlap | A slow run is still going when the next starts | Use `flock -n /run/lock/cleanup.lock command` |
| Missed run | Machine was off at the scheduled time | A systemd timer with `Persistent=true` |

A scheduled job is production code: give it an owner, a log, a lock, an exit code that means something and an alert when it has not succeeded recently.

## Finding what a process is doing

```bash
ls -l /proc/<pid>/fd | head               # open files and sockets
tr ' ' ' ' < /proc/<pid>/cmdline; echo   # exact command line
grep -E 'State|VmRSS|Threads|Uid' /proc/<pid>/status
grep -i 'open files' /proc/<pid>/limits   # the limit the process really has, which may differ from your ulimit
sudo lsof -iTCP -sTCP:LISTEN -P -n        # which process owns each listening port
```

`strace -f -p <pid>` shows system calls but slows the process; use it briefly, on one PID, and record that you did.

## Resource pressure symptoms

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Writes fail, services crash | Disk or inode exhaustion | `df -h`, `df -i`, `du` |
| Process killed without an application log line | Out-of-memory killer | `journalctl -k \| grep -i -E 'oom\|killed process'` |
| High load, low CPU use | I/O wait or uninterruptible (`D`) tasks | `vmstat 1`, `iostat -x 1`, `ps -eo state,pid,cmd \| grep '^D'` |
| `Too many open files` | File-descriptor limit | `cat /proc/<pid>/limits`, unit `LimitNOFILE`, `ls /proc/<pid>/fd \| wc -l` |
| Service slow, CPU high | Busy loop or heavy work | `top -H -p <pid>`, `pidstat -u 1` |
| `Cannot allocate memory` while `free` shows memory | Process or cgroup limits | `MemoryMax=`, `ulimit -a`, `systemctl show -p MemoryMax` |
| Time-dependent failures (certificates, tokens) | Clock drift | `timedatectl`, `chronyc tracking` |

**Reading `vmstat 1`.** Columns `r` (runnable processes), `b` (blocked), `si`/`so` (swap in and out), `wa` (I/O wait) and `id` (idle) answer most first questions. A persistent `r` above the CPU count means CPU saturation. A high `wa` with idle CPU points to storage. Non-zero `si` and `so` means active swapping, which makes everything slow.

```bash
vmstat 1 5
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st   (illustrative)
```

## Package and update hygiene

Install from trusted repositories, record versions per host class, pin versions in images and update on a schedule. Check what would change (`apt list --upgradable`, `dnf check-update`) and detect modified package files (`dpkg --verify`, `rpm -V <package>`). After updating a library, restart the services that use it (`needrestart`, `dnf needs-restarting`): a running process keeps the old copy mapped.

## A Linux triage sequence

Use the same order every time, because order stops you from blaming a dependency before proving the host is healthy.

1. **What is the claim, and since when?** Write the symptom and the time. Find recent changes (deploys, package updates, config edits).
2. **Is the process running?** `systemctl status`, `systemctl show -p ExecMainStatus -p NRestarts`.
3. **If not, why did it exit?** `journalctl -u … -b -n 100`; classify: could not start (exec, user, namespace) or started and failed.
4. **Is it listening where expected?** `ss -ltnp`; compare address, port and PID.
5. **Can it read what it needs and write what it must?** `namei -l`, `sudo -u user test -r/-w`, ACLs and SELinux/AppArmor denials.
6. **Is the machine under pressure?** `df -h`, `df -i`, `free -h`, `vmstat 1 5`, `journalctl -k`.
7. **Is a dependency reachable?** Resolve, connect, then call (see the network table); hand deeper network analysis to T-CLD-02.
8. **Change one thing, verify, record.** Say what you changed, what you expected and what you saw.

## Worked example: a service flaps after a release

A release changes `/opt/orders/current` (a symlink) and the service begins restarting.

```bash
systemctl status orders-api --no-pager
#   Active: activating (auto-restart) (Result: exit-code)
#   Process: ... ExecStart=/opt/orders/current/bin/orders-api (code=exited, status=203/EXEC)   (illustrative)

journalctl -u orders-api -b -n 20 --no-pager
# systemd[1]: orders-api.service: Failed to execute /opt/orders/current/bin/orders-api: No such file or directory

ls -l /opt/orders/
# lrwxrwxrwx 1 root root 28 Jun  3 10:12 current -> /opt/orders/releases/2024-06-03
ls -l /opt/orders/releases/
# drwxr-xr-x 3 root root 4096 Jun  1 09:00 2024-06-01      (2024-06-03 is missing)
```

Read the chain: status 203 means exec failed; the journal says the file does not exist; the symlink points to a release directory that was never created. The correct fix is to repair the release (create or restore the directory, or point the symlink back at `2024-06-01`), then verify and only then restart:

```bash
sudo ln -sfn /opt/orders/releases/2024-06-01 /opt/orders/current
ls -l /opt/orders/current/bin/orders-api
sudo systemctl reset-failed orders-api
sudo systemctl restart orders-api
systemctl is-active orders-api && curl -fsS http://127.0.0.1:8000/health
```

The incident note records the symptom, the evidence lines, the change and the check that the service is healthy. The prevention is a deployment step that verifies the target exists before it switches the symlink.

## What can go wrong: a short catalogue

| Situation | What you see | Cause and response |
| --- | --- | --- |
| Unit works by hand, fails under systemd | `Permission denied` or `Read-only file system` | Sandboxing (`ProtectSystem=strict`) needs `ReadWritePaths=`; different `User=` |
| Disk 100% after log rotation | `df` high, `du` low | Process holds the deleted file; signal it to reopen logs, or restart |
| Database connection works from your shell, not the service | `Connection refused` or `Name or service not known` | Different environment, DNS search path or `PrivateNetwork`; test as the service user |
| Cron job did not run | Nothing in logs | Wrong user crontab, `%` unescaped, daemon stopped, or job ran with a minimal `PATH` |
| `sudo systemctl restart` makes it worse | New failure after restart | Restart before capturing evidence; always capture status and the last 100 journal lines first |

## Knowledge consolidation

- The kernel picks **one** permission class (owner, group or others); parents need `x`; ACLs and mandatory access control can add or remove access.
- Services run as their own users: code owned by root, config readable, data directory writable, nothing else.
- Unit files are contracts; `systemctl cat`, `show` and `systemd-analyze verify` show and check them. Statuses such as `203/EXEC` classify a failure before you read a log.
- `After=` orders; it does not guarantee readiness. Restart policies hide loops unless you read `NRestarts` and the journal.
- Journals can be filtered by unit, time, boot, priority and PID; confirm persistence if you need logs across reboots.
- Storage has layers (device, filesystem, mount); check blocks, inodes, deleted-open files and I/O separately.
- Refused means "no listener"; timed out means "no answer". State which layer fails.
- Cron needs absolute paths, logs, locks and alerts; timers are often a better fit.
- A triage sequence beats intuition: process, listener, logs, access, pressure, dependency, change one thing.

## Exercises

**Exercise 1 — Create the service.** Create the `orders` user, directories and unit above for a toy program (a shell script that logs a line every few seconds will do). Start it with `systemctl enable --now` and show `status`, `show -p MainPID -p NRestarts` and the last 20 journal lines.

**Exercise 2 — Break and fix permissions precisely.** Make the toy program open `/etc/orders/app.conf` itself at start-up. Set the file to `root:root` mode `0600`, restart and read the failure. Fix it with `root:orders` and `0640`, and prove the fix with `sudo -u orders test -r`. Then repeat with `db.env`, loaded through `EnvironmentFile=`, and explain why the same mode does not break the service.

**Exercise 3 — Provoke each exit class.** Change the unit three times: (a) wrong `ExecStart` path, (b) nonexistent `User=`, (c) a `ReadWritePaths=` directory that does not exist. Record the status code, the journal line and the one-sentence meaning of each.

**Exercise 4 — Disk full, three ways.** On a scratch loopback filesystem, (a) fill blocks, (b) exhaust inodes with many empty files, (c) delete a log that a background process holds open. Show the `df`, `df -i` and `lsof +L1` evidence and the fix for each.

**Exercise 5 — Cron versus timer.** Write a job that prints its environment, run it from cron, from a systemd timer and from your shell, and compare `PATH`. Add `flock -n` and show a second overlapping run being skipped.

**Exercise 6 — Triage a partner's fault.** Have a partner introduce one of: wrong ownership, full inode table, wrong bind address, a stopped dependency. Use the triage sequence and quote the line of output that identifies the cause.

**Solution notes.**

*Exercise 1.* `Active: active (running)` with a `Main PID`, `NRestarts=0` and the toy program's journal lines. If it fails with `203/EXEC`, check the interpreter line and the executable bit; if the service writes files, check `ReadWritePaths=`.

*Exercise 2.* With `root:root` and `0600` the program exits with its own `Permission denied`, visible in the journal. With `root:orders` and `0640` the group bit lets `orders` read it and others cannot. `db.env` still loads at `root:root 0600`, because systemd opens `EnvironmentFile=` as root before it switches to `User=orders`; keep such files tighter than the service group when the program does not read them directly. `chmod 777` would work and would let every local account modify the file.

*Exercise 3.* Expect `203/EXEC` for (a), `217/USER` for (b) and `226/NAMESPACE` for (c). The classification matters more than the exact text: the binary could not be executed, the identity does not exist, the sandbox could not be built.

*Exercise 4.* (a) `df -h` at 100%, with `du` naming the big directory. (b) `df -h` shows free space while `df -i` shows `IUse%` at 100%; fix the producer of small files. (c) `df` high and `du` low, and `lsof +L1` names the deleted file; signal the process to reopen its log or restart it.

*Exercise 5.* Cron's `PATH` is typically `/usr/bin:/bin`, so tools in `/usr/local/bin` are not found; a timer inherits the unit's environment, not your shell's. With `flock -n`, the second run exits at once with a non-zero status instead of overlapping.

*Exercise 6.* The strongest answers quote discriminating evidence: owner and mode from `ls -l`, `IUse%` from `df -i`, the bind address from `ss -ltnp`, the refused connection from `nc`. An answer that names a cause without a supporting line of output is a guess.
