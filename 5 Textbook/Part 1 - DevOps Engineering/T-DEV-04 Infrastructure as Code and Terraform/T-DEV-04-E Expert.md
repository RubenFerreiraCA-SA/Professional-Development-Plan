# T-DEV-04-E — Expert Depth

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-e"></a>
#### T-DEV-04-E — Expert Depth

**State surgery and recovery.** `terraform import` (and import blocks), `state mv`, `state rm` and `moved` blocks change the mapping between code and reality without touching infrastructure. They are powerful and dangerous: take a state backup first, run a plan expecting no changes afterwards, and prefer declarative `import` and `moved` blocks that go through review over imperative commands. Treat "plan is empty after the operation" as the acceptance test.

**Replacement semantics and safe change.** Understand which attribute changes force replacement (`# forces replacement` in the plan). For stateful or traffic-critical resources use `create_before_destroy`, blue/green constructs, or provider-specific in-place options. `ignore_changes` suppresses drift on chosen attributes — use sparingly and document, because it hides divergence.

**Provider and version governance.** Pin provider and Terraform versions, review lock-file changes like dependency updates, and mirror providers for reproducible, offline-capable builds. Upgrades to a provider's major version can silently change defaults; rehearse in a copy of the environment.

**Scaling the organisation.** Patterns:

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Many small roots by lifecycle (network, data, runtime) | Limited blast radius, faster plans | Cross-root dependencies via remote state or data lookups |
| Shared module registry | Reuse and consistency | Version coupling, slow change propagation |
| Workspaces | Quick environment copies | Easy to apply to the wrong one; shared backend configuration |
| Orchestration wrappers or a managed platform | Policy, drift detection, approvals | Another system to secure and operate |

Detect drift on a schedule (a read-only plan) and alert on non-empty plans rather than waiting for surprise.

**Identity design for automation.** Separate roles for plan, apply and state administration. The plan role should not be able to change infrastructure. Scope apply to what a root manages. Review the trust policy as carefully as the infrastructure.

**Cost and sustainability governance.** Make cost visible at plan time (cost-estimation tooling), enforce tags and budgets as policy, set idle policies (scale to zero or destroy after N days) and track orphaned resources. Treat the teardown path as a tested feature.

**Failure catalogue**

| Failure | Cause | Defence |
| --- | --- | --- |
| Corrupt or lost state | Manual edit, failed write | Versioning, locking, restore drills |
| Concurrent applies | No locking or forced unlock | Native locks, pipeline serialisation |
| Secret leakage via state or plan | Sensitive attributes stored | Restricted access, encryption, summaries |
| Unreviewed widening of access | Large diff, reviewer fatigue | Policy as code on plan output |
| Dependency cycle at bootstrap | Registry needed before runtime | Staged applies, explicit variables |
| Destroying shared foundations | Wrong directory or state | Prevent-destroy, separate state, approvals |

**Mentoring prompts.** When would you choose to split a root configuration, and what do you pay for that? How would you migrate a resource from one state to another with zero replacement and prove it? What is the difference between "the pipeline applied successfully" and "the infrastructure matches intent"?

---
