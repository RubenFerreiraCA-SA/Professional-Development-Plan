# T-CLD-05 — AWS Infrastructure, Resilience and Architecture

*Part 2 — Cloud Engineering*


Architecture is the set of decisions that determine how a system behaves when things go wrong. This topic is about making resilience claims *measurable*: define the failure you design for, build it through code, test it and record what you did and did not prove.

## Levels


- [Beginner Foundations](T-CLD-05-B%20Beginner.md#t-cld-05-b) — failure domains, regions and AZs, compute, storage, load balancing, databases and auto scaling, a walked small topology, capacity for AZ loss, RTO and RPO with numbers, a first drill.
- [Intermediate Practice](T-CLD-05-I%20Intermediate.md#t-cld-05-i) — decision records, topologies, network dependencies, load-balancer health checks, scaling policies, state, backups and restores, managed services, infrastructure as code, drills and routine failure analysis.
- [Professional Engineering](T-CLD-05-P%20Professional.md#t-cld-05-p) — worked RTO and RPO budgets, failure domains and static stability, immutable releases, data protection layers, tested restores, recovery runbooks, reliability versus cost, fault-drill evidence.
- [Expert Depth](T-CLD-05-E%20Expert.md#t-cld-05-e) — availability mathematics and correlation, gray failures, overload and metastability, multi-region patterns, durability, data recovery limits, blast radius, game days, DR cases.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Items marked *Version-specific* describe AWS behaviour that can change; outputs and figures marked *illustrative* show expected shapes, not measured results.
