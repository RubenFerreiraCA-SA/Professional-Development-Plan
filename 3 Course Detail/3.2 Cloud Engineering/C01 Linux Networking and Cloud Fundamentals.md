# C01 — Linux, Networking and Cloud Fundamentals

| | Details |
| --- | --- |
| **Estimated study time** | 32–40 hours |
| **Prerequisites** | Comfortable with a terminal; Harbour app from DevOps D03 (or equivalent) runnable locally. No prior sysadmin certification required. |

## Objective

Build an **operations baseline** for how Harbour is reached and troubleshot: Linux host literacy, IP/DNS/routing/TLS fundamentals, cloud vocabulary, and a written connectivity runbook. A Platform Engineer who cannot explain the path from client to process will misdiagnose every later AWS and Kubernetes failure.

## Outcomes

1. Operate a Linux host safely for service debugging (processes, users, permissions, logs, packages).  
2. Explain and inspect IP addressing, ports, DNS, routes, firewalls and basic TLS.  
3. Map IaaS/PaaS/SaaS, regions/AZs and shared responsibility to Harbour’s deployment choices.  
4. Produce a Harbour reachability diagram and diagnostic command sequence.  
5. Given a planted connectivity failure, restore reachability using only that documentation.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Linux operator essentials | 8–10 |
| Networking and TLS path | 10–12 |
| Cloud concepts and shared responsibility | 4–6 |
| Harbour connectivity lab + runbook | 6–8 |
| Practical Assessment | 4–6 |
| **Total** | **32–40** |

## 1. Linux for operators

Work on a disposable Linux VM or container host (local VM, cloud free-tier instance, or WSL2 with noted differences):

- Processes, signals, `systemd` (or equivalent) status for a service.  
- Users, groups, file permissions, `sudo` blast radius.  
- Logs: journal/`/var/log`, correlation with application stdout.  
- Package installs without polluting a production-like image contract.  
- Disk/memory pressure symptoms vs application bugs.

**Lab:** Run Harbour (Compose or binary) on the host; show PID, listening sockets and where logs land.

## 2. Networking and TLS

- OSI/TCP mental model sufficient for debugging (not an academic stack quiz).  
- Interfaces, addresses, routes, `ss`/`curl`, DNS resolution order.  
- Ports, security groups/firewalld/iptables concepts, published vs internal Docker ports (link D03).  
- TLS: certificates, trust stores, SNI; distinguish “TCP up” from “TLS/auth OK.”  
- HTTP health vs readiness (link D03 `/health` vs `/ready`).

**Lab:** Trace a request from client → DNS → route → port → process. Break DNS **or** port **or** process (one at a time) and record symptoms.

## 3. Cloud concepts

- Regions, availability zones, blast radius.  
- Shared responsibility (customer vs provider).  
- IaaS vs PaaS vs managed data stores — where Harbour API, DB and load balancers sit.  
- Why D05’s training trade-offs (e.g. public subnet tasks) are not production defaults.

**Exercise:** One-page map: which Harbour components you own vs the provider in your current lab topology.

## 4. Harbour connectivity runbook

Create `docs/runbooks/harbour-connectivity.md` with:

- Path diagram (client → edge → service → dependency).  
- Ordered diagnostics (DNS, route, port, TLS, process, app health/ready).  
- Recovery actions that are reversible and documented.  
- Explicit “stop and escalate” conditions.

## Practical Assessment — restore reachability

**Scenario:** A colleague reports “Harbour is down.” You may use only your network/path notes and runbook (plus standard OS tools).

**Required evidence:**

1. Reachability diagram for your actual lab topology.  
2. Diagnostic command list with expected healthy output (Compose via `app/docker-compose.yml` / `-f` path).  
3. An **application** planted failure (e.g. stopped process or dependency) diagnosed without guess-and-reboot.  
4. A **network** planted failure (bind/publish or firewall) with command evidence that differs from (3) — e.g. refused vs timeout, listener absent vs present.  
5. Recovery records for both; residual risk.  
6. Short note linking symptoms to cloud shared-responsibility (what would change on AWS ELB/SG vs local Compose).

**Acceptance:** Another engineer can follow the runbook to restore a similar failure and can tell application failure from network failure using output alone. “I restarted Docker” without a diagnosis does not pass.

## Certifications (optional)

Linux Foundation or CompTIA-style networking/Linux exams may reinforce vocabulary; they are **not** required for module completion. Prefer practical evidence over exam scores.

## Further learning

- `man ss`, `man ip`, `man systemd`  
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)  
- Prior art: [D03](../3.1%20DevOps/D03%20Docker%20and%20Containerization.md) networking; DevOps bridge note in the [Course Outline](../../1%20Foundational%20Documents/1.2%20Course%20Outline.md)

**Textbook:** [Chapter 1 — Linux, Networking and Cloud Fundamentals](../../4%20Study%20Materials/4.2%20Cloud%20Engineering/C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md)

**Previous:** [Cloud syllabus](C00%20Cloud%20Syllabus.md) · **Next:** [C02 — AWS Cloud Foundations](C02%20AWS%20Cloud%20Foundations.md)
