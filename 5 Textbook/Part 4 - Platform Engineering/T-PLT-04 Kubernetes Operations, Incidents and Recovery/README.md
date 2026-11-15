# T-PLT-04 — Kubernetes Operations, Incidents and Recovery

*Part 4 — Platform Engineering*

Kubernetes is easy to deploy to and hard to operate. This chapter is about day two: finding out what is wrong with evidence, taking nodes out and putting them back, changing and upgrading safely, recovering from loss, and running incidents and reliability programmes at team and fleet scale.

## Levels


- [Beginner Foundations](T-PLT-04-B%20Beginner.md#t-plt-04-b) — what day two means, the status/describe/events/logs routine, reading Pod statuses and exit codes, scheduling and probe symptoms, safe checks on a shared cluster, maintenance vocabulary, recovery sources and a full troubleshooting walkthrough.
- [Intermediate Practice](T-PLT-04-I%20Intermediate.md#t-plt-04-i) — evidence-led diagnosis, a fault catalogue and blind drills, runbooks, debugging stalled rollouts, ephemeral debugging, node lifecycle (drain, failure, NotReady), configuration and certificate failures, capacity and quotas, namespace rebuild from Git and etcd snapshot awareness.
- [Professional Engineering](T-PLT-04-P%20Professional.md#t-plt-04-p) — recovery levels, cluster versus application failure, upgrade and change planning, backup and restore boundaries, incident command, resilience exercises, tested playbooks and the decision guide.
- [Expert Depth](T-PLT-04-E%20Expert.md#t-plt-04-e) — failure domains, control-plane and etcd operations, large-scale failure mechanisms, etcd and cluster recovery, fleet operations, rollout safety, upgrade strategies, reliability programmes, disaster-recovery design and platform-wide incident response.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
