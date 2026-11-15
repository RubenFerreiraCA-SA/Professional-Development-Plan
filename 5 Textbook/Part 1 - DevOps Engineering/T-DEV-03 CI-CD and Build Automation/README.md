# T-DEV-03 — CI/CD and Build Automation

*Part 1 — DevOps Engineering*

Continuous integration validates every change; continuous delivery moves a verified artifact toward production. The central design question is trust: which automation may run untrusted code, which may publish, and which may deploy.

Read **Beginner** if pipelines are new: it explains why automation exists, how CI differs from delivery and deployment, and walks through a safe first pipeline and a failing check that blocks a merge. Read **Intermediate** to design multi-stage pipelines: dependencies, caches versus artifacts, test categories, matrices, environment differences, publishing once and tracing an artifact back to a commit. Read **Professional** to treat the pipeline as a privileged system: immutable artifacts, approvals and promotion, short-lived cloud credentials, protected environments, deployment strategies, rollback and pipeline reliability. Read **Expert** for provenance, supply-chain threats, cache and runner attacks, economics of speed and flakiness, governed policy exceptions and trust-boundary cases. Higher levels point back to earlier ones; the chapter does not depend on any particular project repository.

## Levels

- [Beginner Foundations](T-DEV-03-B%20Beginner.md#t-dev-03-b)
- [Intermediate Practice](T-DEV-03-I%20Intermediate.md#t-dev-03-i)
- [Professional Engineering](T-DEV-03-P%20Professional.md#t-dev-03-p)
- [Expert Depth](T-DEV-03-E%20Expert.md#t-dev-03-e)
