# T-DEV-05 — GitOps and Release Operations

*Part 1 — DevOps Engineering*


GitOps makes Git the source of truth for what should run, and a controller inside the environment continuously reconciles reality toward it. It replaces ad-hoc deployment commands with reviewed changes and an automatic, auditable loop. Understanding the loop explains safe releases, drift, rollbacks and many production incidents.

## Levels


- [Beginner Foundations](T-DEV-05-B%20Beginner.md#t-dev-05-b) — desired versus actual state, reconciliation, Git as audited desired state, what GitOps is and is not, push versus pull, an annotated controller flow, Kustomize overlays, a safe first change, common mistakes.
- [Intermediate Practice](T-DEV-05-I%20Intermediate.md#t-dev-05-i) — installing a Flux-type controller, sources and Kustomizations with Argo CD equivalents, Kustomize and Helm inputs, environments, promotion through Git, reading controller signals, drift and field ownership, failed syncs, safe rollback.
- [Professional Engineering](T-DEV-05-P%20Professional.md#t-dev-05-p) — repository ownership and access, promotion by digest with evidence, least-privilege controllers, secrets approaches, progressive delivery, health evidence, multi-environment operation, runbooks, and why `git revert` does not restore data.
- [Expert Depth](T-DEV-05-E%20Expert.md#t-dev-05-e) — reconciliation theory, controller trust, multi-cluster and fleet rollout, reconciliation failures in depth, complex rollouts, governance, state and data recovery, organisational operating models.

All examples use a neutral `orders-api` service; the chapter has no dependency on any other course material. Outputs marked *illustrative* show expected shapes, not measured results.
