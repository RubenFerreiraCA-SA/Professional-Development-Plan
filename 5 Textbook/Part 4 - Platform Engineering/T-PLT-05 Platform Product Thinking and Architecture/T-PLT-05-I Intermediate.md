# T-PLT-05-I — Intermediate Practice

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-i"></a>
#### T-PLT-05-I — Intermediate Practice

**Why a portal alone is not a platform.**

| What you installed | What it proves | What it does *not* prove |
| --- | --- | --- |
| A portal running | A web application is up | That anyone can create a deployable service |
| Templates configured | A form submits | That the output builds, passes policy, deploys and is observable |
| A catalogue populated | Entities exist | That owners, runbooks and status are correct |
| A beautiful documentation site | Pages exist | That a stranger can follow them without help |
| A positive internal demo | The author can drive it | Anything about independent use |

A portal, CLI, template or README is an *interface*. The evidence of a platform is a trial with a real, independent user (see T-PLT-06).

**The platform contract — who owns what**

| Concern | Platform owns | Developer owns |
| --- | --- | --- |
| Namespace, quota, deployer identity | Tenant manifest and policy | Chooses service name and owner |
| Build pipeline and signing | Reusable workflows | Code and tests |
| Deploy mechanism | GitOps | Decides when to promote |
| Probes, limits, security context defaults | The template | Tunes values within limits |
| Telemetry plumbing, dashboard template | The platform | Business metrics, keeps runbook current |
| First response to incidents | Support route and docs | Service-specific diagnosis and fixes |
| Data durability for stateful services | Patterns and guidance only | Backup choices and restore tests |

A contract nobody wrote down is an assumption.

**Choose the runtime scope and say so.** A platform usually has one primary runtime (for example Kubernetes with GitOps, or a managed container service) and records the decision: alternatives, cost, what is *not* claimed. Different pathways may exist for teams on other runtimes, adapted knowingly rather than silently.

**Architecture views as text that diffs in Git**

| View | Contents |
| --- | --- |
| Context | Users, the platform, external systems |
| Components and flows | Source repository, CI, registry, desired-state repository, controller, cluster, observability |
| Trust boundaries | Where untrusted code runs, where credentials live, who can change production-shaped state |
| Ownership table | Who owns each resource, which controller reconciles it, whether it may be pruned |

**Architecture decision records.** A minimum set for a platform: runtime and scope; platform boundary and golden-path contract; delivery trust model (review, CI, digest, provenance — and what provenance does *not* prove); deployment identity, tenancy and policy; state and data; observability, SLOs and runbook ownership; secrets and access; cost and operations. Each ADR states *context, decision, alternatives, consequences (good and bad), evidence link and revisit trigger*.

**The limitations register.** Keep one row per honest gap: *gap, impact, compensating control, would fix by*. Typical entries: the practice cluster is single-node; a read role is cluster-wide; secrets are base64 in etcd; recovery of data depends on a copy outside the cluster. Maintain it from the start, not the night before a demonstration.

**Exercise.** Write the ownership table and a limitations register with at least five honest entries for a platform you know.
