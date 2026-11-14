# T-DEV-04-P — Professional Engineering

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-p"></a>
#### T-DEV-04-P — Professional Engineering

**Plan in CI, apply from trust.** Even a same-repository pull request can contain untrusted code. Separate three lanes:

| Lane | Runs | Cloud access |
| --- | --- | --- |
| Untrusted validation | `fmt`, `validate`, module tests on every pull request | None — no credentials, no state read |
| Trusted plan | `plan` against remote state | Federated identity with a *plan* role, from a named trusted workflow and allowed refs |
| Trusted apply | Fresh plan then apply | Federated identity with an *apply* role, behind environment approval |

Never store long-lived access keys in the repository, and never let pull-request-authored workflow files freely assume roles that can read state. Scope the role's trust policy to the audience and subject (repository plus environment or branch); only add workflow-identity claims after verifying the token your provider actually issues.

Publish a *plan summary* (resources added, changed, destroyed, replacements, security-group widening) for reviewers rather than the raw plan, because raw plans can contain sensitive values. Redaction is not a security control; restrict who can read summaries.

**Always re-plan in the apply context.** A plan computed earlier may be stale if state or the live world moved. For production, apply the exact saved plan that was reviewed, or re-plan and compare.

**State is a secret.** Encrypt it, enable versioning (recovery from a bad write), restrict read access like production secrets and keep sensitive values out of outputs where possible (`sensitive = true` hides display, not storage). Plan the recovery path: list object versions, restore a previous version only with care and with the lock held.

**Module design rules**

- Small, focused modules with explicit inputs and outputs; avoid pass-through of every provider argument.
- Validate inputs (CIDRs, names, sizes) at the boundary; encode policy such as "no open ingress" in validation or in a policy check.
- Version modules (tags or a registry) and write upgrade notes. Consumers pin versions.
- Prefer composition over deep nesting; avoid `count`/`for_each` on resources whose identity may change without a `moved` block.
- Use `moved` blocks to rename or restructure without replacing resources.
- Add `lifecycle { prevent_destroy = true }` on stateful resources, with a documented way to remove it deliberately.

**Policy as code.** Run checks (for example static analysis or a policy engine) over the plan JSON: no public ingress, required tags, encrypted storage, approved regions. Treat a failing policy as a failing check. Document known gaps honestly.

**Cost, tags and teardown.** Set a budget alarm before leaving resources running. Tag everything with `Project`, `Owner`, `Environment`. Understand cost drivers: a NAT gateway or an always-on load balancer dominates a small environment. Write a teardown order — runtime, then network, never the bootstrap while environments exist — and rehearse it. Have a second engineer provision or destroy an environment using only the README.

**Blast radius thinking.** Replacing a load balancer and replacing a task definition are different events. Before approving a plan, name what will be replaced, what depends on it and what users will experience. Large root configurations increase blast radius; split by lifecycle and by owner.

**Decision guide**

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Understand a change | `plan`, `show`, look for replacements | Blind `apply` |
| Share state | Remote backend, native locking, IAM | A state file in a synced folder |
| Isolate environments | Separate state keys, ranges, prefixes | One state for everything |
| Run in CI | Validation with no cloud access; plan via scoped federation | Wildcard trust; PR code assuming a plan role |
| Handle drift | Fresh plan, then revert, import or accept | Console edits forever |
| Hit a lock error | Wait or find the active run | Reflexive `force-unlock` |
