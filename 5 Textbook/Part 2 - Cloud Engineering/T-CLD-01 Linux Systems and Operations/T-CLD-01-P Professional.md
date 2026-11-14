# T-CLD-01-P — Professional Engineering

*Chapter: [T-CLD-01 — Linux Systems and Operations](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-01-p"></a>
#### T-CLD-01-P — Professional Engineering

**Hardening a host.**

- Disable password login for SSH; use keys or short-lived certificates; restrict users and source addresses; no direct root login.
- Run services under dedicated users with systemd sandboxing (`ProtectSystem`, `ProtectHome`, `PrivateTmp`, `NoNewPrivileges`, `CapabilityBoundingSet=`, `RestrictAddressFamilies=`).
- Keep the package set small; automate security updates or rebuild images regularly.
- Centralise logs off the host and protect their integrity; an attacker on a host can alter local logs.
- Use mandatory access control (SELinux or AppArmor) in enforcing mode where the distribution supports it, and read its denials rather than disabling it.

**Immutable over mutable.** Prefer building images or machine templates and replacing instances to patching them by hand. Configuration drift on long-lived hosts becomes an incident later. When you must log in, treat the host as disposable and record what you changed.

**Capacity and limits.** Set explicit resource limits in units (`MemoryMax`, `CPUQuota`, `TasksMax`), watch saturation (not just utilisation), and keep headroom. Know the ceilings for file descriptors, ephemeral ports and connection tracking.

**Backups and recovery on hosts.** Define what is backed up (data directories, not the whole machine), how often, where (off-host, access-controlled, encrypted) and prove restoration by restoring into a clean host. A backup nobody has restored is a hypothesis.

**Operational discipline.**

| Practice | Why |
| --- | --- |
| Change via code or runbook, not memory | Repeatability |
| Record *who* changed *what* and *when* on shared hosts | Auditability |
| Time-box and log privileged sessions | Accountability |
| Prefer read-only diagnosis first | Safety under pressure |
| Never run destructive commands on a host you cannot snapshot or rebuild | Recovery |

**Decision guide**

| Situation | Do | Don't |
| --- | --- | --- |
| Permission denied | Fix owner, group or mode precisely | `chmod 777` |
| Service flaps | Read the journal and exit codes | Blind restart loops |
| Disk full | Find the largest consumer, fix the cause | Delete random logs |
| Unknown process | Inspect `/proc`, `ss`, unit files | Kill it without knowing |
| Fleet drift | Rebuild from a template | Hand-edit servers |
