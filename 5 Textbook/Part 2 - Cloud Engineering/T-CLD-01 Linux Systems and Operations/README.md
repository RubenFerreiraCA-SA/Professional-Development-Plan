# T-CLD-01 — Linux Systems and Operations

*Part 2 — Cloud Engineering*


Most cloud workloads run on Linux, in virtual machines or in containers. Diagnosing a service means connecting a process, its permissions, its sockets and its logs.

## Levels


- [Beginner Foundations](T-CLD-01-B%20Beginner.md#t-cld-01-b) — shell and terminal, files and paths, permissions, users and groups, processes and signals, environment, streams and pipes, packages, a fully guided safe terminal session, a first diagnosis.
- [Intermediate Practice](T-CLD-01-I%20Intermediate.md#t-cld-01-i) — ownership and access decisions, service accounts, systemd units and exit statuses, journald, storage and capacity, network tools by layer, cron and timers, a triage sequence, service-failure worked example.
- [Professional Engineering](T-CLD-01-P%20Professional.md#t-cld-01-p) — secure baselines, privilege separation, SSH and audit, monitoring and capacity, reliability, backup and restore drills, a performance method, runbooks, trade-offs.
- [Expert Depth](T-CLD-01-E%20Expert.md#t-cld-01-e) — kernel and user space, scheduling, memory and the OOM killer, cgroups and namespaces by hand, storage and network I/O, perf and flame graphs, eBPF mental models, hard incidents, tuning trade-offs, fleet operations.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
