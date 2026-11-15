# T-DEV-04-E — Expert Depth

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-e"></a>
#### T-DEV-04-E — Expert Depth

## Why this level exists

Professional practice makes a single Terraform root safe: scoped identities, reviewed plans, policy, contracts. Expert practice deals with what happens when there are hundreds of roots, dozens of accounts, several teams with different release rhythms, thousands of resources per environment, and a history of decisions that nobody can reverse casually. The problems change character. Plans take forty minutes. A shared module change touches two hundred states. A provider upgrade is a programme, not a pull request. Drift is no longer an anomaly but a steady background rate. A recovery involves more than one state and more than one account.

The skill is not knowing obscure flags. It is anticipating how accepted practices fail under scale, ownership boundaries and partial failure, and designing structures so that a failure is small, visible and recoverable. This level assumes the material in [T-DEV-04-I](T-DEV-04-I%20Intermediate.md#t-dev-04-i) and [T-DEV-04-P](T-DEV-04-P%20Professional.md#t-dev-04-p) is already clear: remote state, locking, `moved` and `import`, plan review, policy over plan JSON, module contracts.

## Thinking about a large estate

Treat the estate as a system with four dimensions, and decide each one deliberately:

| Dimension | Question | Typical answer |
| --- | --- | --- |
| **Identity boundary** | Which cloud accounts, subscriptions or projects exist, and who may act in each? | One per environment and per sensitivity tier; shared services separated |
| **Lifecycle boundary** | What changes at the same rate and with the same risk? | Foundation, network, data, runtime, application |
| **Ownership boundary** | Which team approves and is paged? | One owner per root; no root with two owners |
| **Failure boundary** | If this state is corrupt or this apply fails, what else stops? | Small and named |

A useful layering, from slowest-changing and highest-impact to fastest-changing and lowest-impact:

| Layer | Contents | Change rate | Blast radius | Typical owner |
| --- | --- | --- | --- | --- |
| 0 Bootstrap | State storage, pipeline identities, organisation structure | Rare | Everything | Platform security |
| 1 Foundation | Accounts, guardrail policies, identity federation, logging, key hierarchy | Rare | Whole estate | Platform |
| 2 Network | Address plans, routing, transit, DNS zones, firewalls | Occasional | Every workload in a region | Network |
| 3 Shared platform | Clusters, registries, shared data services, observability | Weekly | Many workloads | Platform |
| 4 Workload infra | A service's database, queues, roles | Daily | One service | Service team |
| 5 Application config | Records, flags, schedules | Constant | One feature | Service team |

Rules that follow:

- Dependencies point **downwards only**. Layer 4 may read layer 2's published outputs; layer 2 must never depend on layer 4. A cycle between layers means the boundary is wrong.
- A change in layer *n* is planned and applied in layer *n* alone. Cross-layer coordination happens through *published interfaces*, never through shared state.
- The cost of an extra layer is paid in coordination; the benefit is blast radius. Choose the number of layers by measuring incident impact, not by aesthetics.

## State partitioning

How big should a state be? There is no number, but there are forces.

| Force | Pushes toward smaller states | Pushes toward larger states |
| --- | --- | --- |
| Plan time | Refresh calls one API request per resource (or more) | Fewer plans to run |
| Blast radius | A bad apply or corrupt state affects fewer objects | |
| Lock contention | Fewer people queued behind one lock | |
| Access control | State read rights can be narrower | |
| Cross-resource references | | Direct references are simple and checked |
| Atomic change | | One apply can change two things consistently |
| Operational overhead | | Fewer pipelines, backends and dependencies to manage |

Practical thresholds experts use as *signals*, not rules: a plan that takes longer than a few minutes to refresh; more than a few hundred to a couple of thousand resources in one state; more than one team regularly waiting for the lock; or resources in one state that have different owners or very different change rates.

Partition axes, usually combined in this order: **environment** (never share), **account or region** (identity and failure boundary), **layer** (lifecycle), then **component or service** (ownership). A conventional state key then encodes all of it:

```text
<estate>/<account>/<region>/<layer>/<component>/terraform.tfstate
example/prod-eu/eu-west-1/network/transit/terraform.tfstate
example/prod-eu/eu-west-1/workloads/orders/terraform.tfstate
```

### Contracts between states

When roots are split, they need to exchange values. Options:

| Mechanism | Strength | Weakness |
| --- | --- | --- |
| `terraform_remote_state` | Easy; typed outputs | Reader needs read access to the writer's *entire* state (possibly secrets); couples to the writer's output names; fails if the writer's backend changes |
| Published parameters (a parameter store, a secrets or config service) read with ordinary data sources | Narrow, auditable access; decoupled from the writer's tooling | Another resource to manage; values can go stale |
| Data sources that look up by tag or name | No explicit publication; discovers reality | Fragile if naming is not guaranteed; ambiguous matches |
| A catalogue managed by a platform tool or registry | Central discovery, versioned | Another system |

Expert guidance: prefer a *published interface* over reading another state. Write the interface as a small module (`publish` and `consume` halves) with a version, so the writer can add values compatibly and the reader fails with a clear message when something is missing:

```hcl
# in the network root: publish
resource "aws_ssm_parameter" "private_subnets" {
  name  = "/platform/${var.environment}/network/private_subnet_ids"
  type  = "StringList"
  value = join(",", aws_subnet.private[*].id)
  tags  = local.common_tags
}

# in a workload root: consume
data "aws_ssm_parameter" "private_subnets" {
  name = "/platform/${var.environment}/network/private_subnet_ids"
}

locals {
  private_subnet_ids = split(",", data.aws_ssm_parameter.private_subnets.value)
}
```

Note the consequence: the consuming plan reads a value at plan time. If the published value is *changing* in the same release (for example a subnet replaced), the consumer's next plan shows downstream changes. Order your applies accordingly and make the dependency visible in the pipeline (consumers wait for producers), not implicit in people's heads.

## Cross-account and cross-provider design

Estate-scale Terraform almost always crosses an identity boundary: a workload account that needs a record in a central DNS account; a peering that has two sides in two accounts; an organisation-level policy applied to many accounts. Terraform expresses this with **provider configurations**, usually aliased:

```hcl
provider "aws" {
  region = "eu-west-1"
  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/terraform-apply-workload"
  }
}

provider "aws" {
  alias  = "dns"
  region = "eu-west-1"
  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/terraform-apply-dns-records"
  }
}

resource "aws_route53_record" "service" {
  provider = aws.dns
  zone_id  = var.central_zone_id
  name     = "orders.example.org"
  type     = "CNAME"
  ttl      = 60
  records  = [aws_lb.main.dns_name]
}
```

A module that needs more than one identity declares its aliases, and the caller wires them:

```hcl
# in the module: versions.tf
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws.requester, aws.accepter]
    }
  }
}

# in the root
module "peering" {
  source = "../../modules/peering"
  providers = {
    aws.requester = aws
    aws.accepter  = aws.peer_account
  }
}
```

Design consequences an expert watches for:

- **Role chains are privilege surfaces.** The pipeline's apply role in account A can assume a role in account B; that second role's trust policy must name *that* role (and ideally conditions such as an external identifier or session tags), not the whole account root. Review it like any trust policy: "who can become this?"
- **Providers are static.** Provider configurations cannot be created in loops over a dynamic list of accounts in the way resources can (`for_each` on provider blocks is not supported in Terraform; check your tool and version); creating the same thing in fifty accounts therefore means either generated code (one provider block per account), a wrapper tool, one root per account, or a purpose-built mechanism for organisation-wide baselines. Weigh these on the cost of diff review, plan time and the failure boundary of each.
- **Removing a provider block while its resources are in state is an error**, not a clean-up. Keep the provider configuration until the resources are removed from state by destroy or a `removed` block. This is the most common reason an account decommission fails.
- **Credential lifetime versus apply duration.** Assumed-role sessions have a maximum duration. A long apply against many resources can outlive its token and fail midway; split large applies or lengthen sessions deliberately, within policy.
- **Region-specific and global resources.** Some services are global but homed in one region (certain CDN or DNS-adjacent resources); put them in a root whose region is documented as authoritative for that service.
- **One provider, many contexts.** Providers other than the cloud (identity, monitoring, Git hosting, secrets) have their own credentials and rate limits. Treat each as a separate trust decision in the pipeline; a monitoring-provider token in the same job as an infrastructure-apply role means a compromise of one grants the other.

### Same pattern, different tool

The patterns in this chapter (state, plan, modules, drift, least-privilege automation) carry across Terraform, its community fork OpenTofu, and other declarative tools. Syntax and version-specific features differ and diverge over time (state encryption, provider-defined functions and others). Choose with a written decision, check the documentation of the exact version you run, and avoid assuming that a feature you used in one is present in the other.

## Large migrations

A large migration is a sequence of safe small ones with checkpoints. Three categories dominate.

### 1. Moving resources between states with no replacement

Splitting a root, merging roots, or handing a component to another team all require the same primitive: *the real object stays; ownership moves.* The safest declarative sequence uses import into the destination first, then a removal from the source that **does not destroy**:

```hcl
# Step 1 — destination root: adopt the object (apply, then require an empty plan)
import {
  to = aws_s3_bucket.reports
  id = "example-reports-prod"
}

resource "aws_s3_bucket" "reports" {
  bucket = "example-reports-prod"
}
```

```hcl
# Step 2 — source root: forget the object without deleting it
removed {
  from = aws_s3_bucket.reports
  lifecycle {
    destroy = false
  }
}
```

Run order and checks:

1. **Freeze** both roots: no unrelated applies (pipeline lock or change freeze) for the duration.
2. **Back up** both states (`terraform state pull`) and record the backend versions.
3. **Destination first.** Apply the import; confirm the destination plan is empty. For a brief period *both* states track the object; that is safe only while no one applies changes to it.
4. **Source second.** Apply the `removed` block; confirm the source plan is empty and the object still exists in reality.
5. **Verify** from outside Terraform (the object's identity and its dependents are unchanged).
6. **Clean up:** delete the `import` and `removed` blocks in follow-up commits once every environment has applied them.

For many resources, generate the blocks from a state listing rather than typing them (`terraform state list` over the source, filtered by prefix, rendered into import and removed blocks), and review the generated diff. For whole-state moves between backends, `terraform init -migrate-state` copies a state; `terraform state mv -state-out=...` moves individual addresses between local state files. Prefer the declarative flow when states are remote and reviewed.

**Danger signs:** any step where a plan proposes to *create* the thing you are importing (the mapping is wrong); an `import` block whose `id` format is not the one the provider documents for that type; applying the destination before the source is frozen.

### 2. Restructuring modules at scale

Changing the shape of a widely used module (splitting it, renaming internal resources, changing `count` to `for_each`) changes addresses in every consumer's state. Provide `moved` blocks *inside the module* so that each consumer migrates as it upgrades, with no action from them:

```hcl
# inside the module, version 2.0.0
moved {
  from = aws_security_group.this
  to   = aws_security_group.app
}

moved {
  from = aws_security_group_rule.ingress[0]
  to   = aws_vpc_security_group_ingress_rule.from_lb
}
```

Moves cannot express every change (a `count` to `for_each` conversion needs one `moved` per instance, and cross-type moves are limited to those the provider supports). When the move cannot be expressed, publish a migration recipe (explicit `terraform state mv` commands and a script to run them across a list of roots) and test it on a copy of a real consumer's state. The acceptance test is the same everywhere: **upgrade the module version, plan, observe zero resource changes.**

Roll a breaking module change out by *cohort*: pilot roots first, then non-production, then production in waves, with automated plans reporting "no changes" or "expected changes" for each root. Never merge a module major version and expect forty teams to cope from a changelog.

### 3. Provider and runtime upgrades

A major provider version change can alter defaults, rename arguments and change how an attribute is read. A systematic upgrade:

1. Read the upgrade guide; write down the changes that touch your usage.
2. Upgrade the lock file in a branch (`terraform init -upgrade`), commit it alone.
3. Run **plan in every root** using a plan-only job and collect the results into a table: roots with no changes, roots with expected changes, roots with surprises.
4. Fix surprises in code (or pin the older version in the roots that cannot move yet).
5. Merge, then apply in order of risk: sandbox, non-production, production in waves, observing each wave's plans after the apply.

A lock file records checksums for each platform you use. When developers and CI run different operating systems, generate hashes for all:

```bash
terraform providers lock \
  -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_arm64
```

Mirror providers and modules you rely on (a network mirror or an internal registry) so that an upstream outage or yanked release cannot stop an incident response.

## Policy and drift at scale

### Policy as a pipeline, not a script

At estate scale, policy has a lifecycle of its own: it is written, tested, versioned, rolled out in *advisory* mode, measured, then enforced. A rule that fails five hundred existing resources on day one will be disabled by the first angry team. Roll out in four stages:

| Stage | Behaviour | Exit criterion |
| --- | --- | --- |
| Observe | Rule runs and logs, never blocks | Violation inventory complete |
| Warn | Rule posts a visible warning on changes | Teams know and have a remediation path |
| Enforce for new | Blocks new violations; existing ones carry exceptions | Exception list shrinking |
| Enforce | Blocks all; exceptions expire | Exceptions near zero |

Test the policies like code: each rule has a failing and a passing fixture of real plan JSON, run on every policy change. Version the policy bundle and make the version used visible in each check run so a failure can be reproduced.

Complement plan-time policy with **runtime inventory policy**: the plan sees only what Terraform manages. Scan the cloud estate for resources that no state manages (orphans and console-created objects) and for settings that violate rules regardless of how they were created. That catches exactly the class of failure plan policy cannot see.

### Drift detection as a service

At scale, drift is expected; the goal is to know about it fast and to classify it.

```bash
# read-only drift detection for one root, suitable for a scheduled job
terraform init -input=false
terraform plan -input=false -lock=false -refresh-only -detailed-exitcode -out=drift.tfplan
rc=$?
case "$rc" in
  0) echo "no drift" ;;
  2) terraform show -json drift.tfplan > drift.json; echo "DRIFT: raise a ticket" ;;
  *) echo "ERROR: detection failed" ; exit 1 ;;
esac
```

(`-detailed-exitcode` returns 0 for no change, 1 for error and 2 for changes. `-lock=false` is acceptable for read-only detection but means the job can read state mid-write; decide deliberately, and use a read-only role.) Use a plan role that cannot change infrastructure.

Design points:

- **Distinguish drift from pending code changes.** A plain `plan` mixes both. `-refresh-only` isolates reality-versus-state; a plain plan on the default branch isolates "unapplied merged code".
- **Classify**: expected controller changes (autoscaling, rotating values), accidental manual changes, malicious changes, provider noise. Feed noise findings back into `ignore_changes` or code so that signal stays high.
- **Alert on a non-empty result, with an owner.** A dashboard nobody receives is not detection. Route to the root's owner (see Ownership in the Professional level).
- **Measure**: count of roots with drift, mean time to resolve, recurring drift sources. A root that drifts every week has a process problem.
- **Mind the cost.** Refreshing thousands of resources hourly can exhaust API rate limits and incur charges. Match frequency to risk (daily for production foundations; weekly for sandboxes) and stagger runs.

### Keeping plans fast

When plans are slow, partitioning is the durable fix. Mitigations in the meantime:

```bash
terraform plan -refresh=false -out=tfplan   # skips refresh: only valid when you know state is fresh
terraform plan -parallelism=20              # raise cautiously; rate limits will push back
terraform plan -target=module.service       # a diagnostic and recovery tool, not a workflow
```

Skipping refresh makes the plan trust state; combined with infrequent drift detection it can hide a change. Use it for fast previews and keep a full-refresh plan as the one that gates apply.

## Module ecosystems

Beyond a handful of modules, you operate a *product*, with consumers.

**Tiers.** Distinguish them explicitly:

| Tier | Purpose | Stability promise |
| --- | --- | --- |
| Primitives | Thin, opinionated wrappers over one resource family (a bucket with encryption, logging and block-public-access on) | Strict semver; very stable |
| Compositions | Combine primitives into a capability (a service with queue, database and role) | Semver; documented change notes |
| Blueprints / stacks | Complete environment layouts | Versioned; consumers copy or reference |

**Governance of the ecosystem.**

- **Catalogue and discovery.** An internal registry or a repository convention with a README, example, inputs, outputs and a support contact for every module.
- **Versioning.** Release immutable tags; consumers pin exact or pessimistic constraints. Publish deprecation notices with dates.
- **Compatibility matrix.** Record which Terraform and provider versions each module release supports and test against the lowest and highest.
- **Contribution model.** Decide who may change a primitive; changes to one affect every composition.
- **Automated consumer testing.** When a module changes, run the plans of its known consumers (or a representative sample) as part of the module's CI, and refuse the release if they unexpectedly change. This is the single most effective ecosystem control.
- **Dependency updates as a flow.** Use automated update proposals for module and provider versions, each with a plan summary, rather than one annual big-bang upgrade.
- **Retiring modules.** A module with no consumers and no owner should be archived; a module with consumers and no owner is an incident waiting for a Friday.

**Anti-patterns.**

| Anti-pattern | Why it hurts | Alternative |
| --- | --- | --- |
| The "god module" | Cannot be versioned sensibly; every change affects everyone | Split by lifecycle |
| Thin wrapper over every resource | Pure indirection; consumers learn two APIs | Use the provider directly; wrap only where policy is added |
| Deeply nested modules (module calling module calling module) | Addresses become long; moves become hard; plans become opaque | Prefer composition at the root |
| Module with provider blocks inside | Cannot be removed cleanly; credentials baked in | Pass providers from the root |
| Unpinned module sources | Plans change without a commit | Pin to tags or registry versions |
| Configuration via one giant `map(any)` | No validation; impossible to document | Typed objects with optional attributes |

## Identity design for automation

Separate roles for plan, apply and state administration. The plan role should not be able to change infrastructure. Scope apply to what a root manages. Review the trust policy as carefully as the infrastructure.

At estate scale, add:

- **A role per root (or per layer) per account**, not one administrator role everywhere. The compromise of a workload pipeline must not grant foundation access.
- **Permission boundaries or guardrail policies** at the account or organisation level that cap what *any* automation role may do (for example, deny disabling logging or deleting the state bucket), so a mistake in a role's policy cannot exceed the cap.
- **Break-glass access** that is separate, logged, alerting and tested, so that incident response does not require improvising permissions in the middle of an outage.
- **Pipeline identity as inventory.** Know every identity that can apply to production, who can change its trust policy, and how the answer is reviewed.
- **A review of the privilege escalation path**: can a role that may edit IAM policies (even "just for its own workload") grant itself more? Policy-as-code and boundaries close this.

## Replacement semantics and safe change

Understand which attribute changes force replacement (`# forces replacement` in the plan). For stateful or traffic-critical resources use `create_before_destroy`, blue/green constructs, or provider-specific in-place options. `ignore_changes` suppresses drift on chosen attributes — use sparingly and document, because it hides divergence.

Additional levers:

```hcl
resource "aws_launch_template" "app" {
  # ...
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  # ...
  lifecycle {
    replace_triggered_by = [aws_launch_template.app.id]   # replace the group when the template changes
    ignore_changes       = [desired_capacity]             # owned by the scaler
  }
}
```

```bash
terraform apply -replace=aws_instance.app   # force a controlled replacement of one object
```

`create_before_destroy` propagates to dependencies: if A is create-before-destroy, the things A depends on are forced to be also, which can surprise you with name-collision errors. Resources with unique names need a `name_prefix` or a random suffix so old and new can coexist.

## Provider and version governance

Pin provider and Terraform versions, review lock-file changes like dependency updates, and mirror providers for reproducible, offline-capable builds. Upgrades to a provider's major version can silently change defaults; rehearse in a copy of the environment.

Add: a published *supported versions* policy (which Terraform and provider versions are allowed, with an end date for each), a scheduled job that reports roots on unsupported versions, and a "version drift" dashboard. A state written by a newer Terraform version may be unreadable by an older one; do not let developers on a different version apply production.

## Complex recovery

Recovery gets hard when more than one thing is wrong at once. The method is the same: **stabilise, stop writes, assess, restore, verify, learn**, but the scenarios deserve rehearsal.

### Scenario A: corrupt or lost state for one root

1. Stop pipelines for that root (disable the job; confirm no active lock).
2. Take a copy of the *current* object even though it is bad, for forensics.
3. Restore the last good version (see versioning). If no good version exists, **rebuild state by import**: write the list of addresses and ids from the code and the cloud inventory, and import in dependency order.
4. Plan. Treat any proposed create of something that exists as a mapping mistake, and any proposed destroy as a stop sign.
5. Only when the plan is explainable, resume.

When reconstructing, generate the import list mechanically from a tag-based inventory of the real objects, and review it, rather than typing hundreds of ids.

### Scenario B: a failed apply leaves two roots inconsistent

The producer root has replaced a network object; the consumer root still references the old identifier and now fails. Order of operations: freeze consumers; confirm the producer's state matches reality; run the consumer plan and read the proposed changes; apply the consumer in a controlled order; unfreeze. The preventive design is the producer/consumer pipeline dependency from the partitioning section.

### Scenario C: state backend unavailable or compromised

Unavailable: you cannot plan, which also means you cannot apply, so nothing *new* gets worse; but incident response that depends on Terraform stops. Keep a documented manual path for the top few emergency changes (scale a service, block an address), and a replica or backup of the backend in another failure domain. Compromised: treat every secret that was ever in state as exposed and rotate; verify state integrity by comparing it with reality using a read-only plan; review recent writes in the backend's access logs.

### Scenario D: a pipeline identity is compromised

Revoke the trust policy first (deny all), then rotate anything the identity could read, review the audit trail for what it did, and compare reality to code with drift detection across every root it could reach. The recovery product is a list of changes found and reverted, not a statement that nothing happened.

### Scenario E: an accidental destroy

Stateful objects: do not recreate immediately if recovery from backup, snapshot or soft-delete is possible, because a new object with the same name can block or complicate restoration. Determine what the provider retains (deletion windows, final snapshots, versioned objects). Restore into a new identity if necessary, then **import it** and align code. Key and certificate deletions have waiting periods that may let you cancel the deletion: act within them.

### Scenario F: a lock that never clears

Check that the owning process is dead and not stalled; check the lock metadata; take a state backup; force-unlock with a second person's agreement; run a plan and read it. Then find out why it was orphaned (runner killed, network partition) and fix it (job timeouts, graceful cancellation).

### Preparing for recovery

| Preparation | Why |
| --- | --- |
| State versioning, replicated and access-logged | Restoration and forensics |
| An inventory of resources by tag, independent of state | Rebuilding state; finding orphans |
| Documented import order and a script to generate imports | Speed and fewer mistakes |
| Backups and tested restores of data stores | Terraform recreates shells, not data |
| A break-glass path and a rehearsed drill | People, not tools, fail under stress |
| Runbooks owned and reviewed | Recovery steps rot fastest |

## Scaling the organisation

Patterns:

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Many small roots by lifecycle (network, data, runtime) | Limited blast radius, faster plans | Cross-root dependencies via remote state or data lookups |
| Shared module registry | Reuse and consistency | Version coupling, slow change propagation |
| Workspaces | Quick environment copies | Easy to apply to the wrong one; shared backend configuration |
| Orchestration wrappers or a managed platform | Policy, drift detection, approvals | Another system to secure and operate |
| Generated roots (templates producing per-account configuration) | Uniform baselines across many accounts | Generated diffs are large; the generator becomes critical code |
| Self-service catalogue | Teams provision approved shapes without platform tickets | Needs strong contracts, quotas and cost controls |

Detect drift on a schedule (a read-only plan) and alert on non-empty plans rather than waiting for surprise.

Orchestration is a real decision. Wrapper tools and managed platforms can run many roots in dependency order, share variables and provide policy and approvals; they also become the highest-privilege system in the estate, since they hold the ability to apply everywhere. Evaluate them by threat model (what happens if this system is compromised?), not only by feature list.

**The social side.** Large estates fail from ownership ambiguity far more often than from technical limits. Publish the layering, who owns each root, how to request a change to shared layers, and the SLA for doing so. Without a path that is faster than "do it in the console", people will take the console.

## Cost and sustainability governance

Make cost visible at plan time (cost-estimation tooling), enforce tags and budgets as policy, set idle policies (scale to zero or destroy after N days) and track orphaned resources. Treat the teardown path as a tested feature.

At scale add: **allocation by tag** with a required cost-centre and owner; **per-account budgets** with alert routing to owners; **commitment planning** informed by the stable layers; **an orphan sweep** (resources with no matching state); and **environment lifecycle automation** for ephemeral stacks, with expiry tags that a job honours. Efficiency is a design property: right-sized defaults in modules save more than any later review.

## Failure catalogue

| Failure | Cause | Defence |
| --- | --- | --- |
| Corrupt or lost state | Manual edit, failed write | Versioning, locking, restore drills |
| Concurrent applies | No locking or forced unlock | Native locks, pipeline serialisation |
| Secret leakage via state or plan | Sensitive attributes stored | Restricted access, encryption, summaries |
| Unreviewed widening of access | Large diff, reviewer fatigue | Policy as code on plan output |
| Dependency cycle at bootstrap | Registry needed before runtime | Staged applies, explicit variables |
| Destroying shared foundations | Wrong directory or state | Prevent-destroy, separate state, approvals |
| Module release breaks many roots | No consumer testing | Consumer plan matrix; cohort rollout |
| Provider upgrade changes defaults | Major version semantics | Plan in every root before merge |
| Estate-wide credential exposure | One role can apply everywhere | Role per root/layer; boundaries; break-glass |
| Drift noise ignored | Alert fatigue | Classify; tune `ignore_changes`; owner routing |
| Partial migration | Import done, removal not | Run order; both-roots freeze; empty-plan gates |
| Orchestrator compromise | Central system holds all privilege | Threat-model it; segment; audit; limit scope |
| Expired temporary credentials mid-apply | Long applies | Split applies; sized sessions |
| Removed provider block with resources in state | Account decommission done out of order | Remove resources first; `removed` blocks |

## Adversarial and contested questions

Use these as design reviews, not trivia:

- When would you choose to split a root configuration, and what do you pay for that?
- How would you migrate a resource from one state to another with zero replacement and prove it?
- What is the difference between "the pipeline applied successfully" and "the infrastructure matches intent"?
- If an attacker can open a pull request but not merge it, what in your Terraform pipeline can they still execute? What if they can edit a module you consume at an unpinned reference?
- Which of your controls still hold if the state bucket's write role is compromised? What would you detect, and how?
- Is a managed orchestration platform a security improvement or a concentration of risk for your estate? What evidence would change your answer?
- How would you decommission an account whose resources are managed by three roots, two of which belong to other teams?
- Which part of your recovery plan has actually been executed in the last six months?

## Knowledge consolidation

- Scale changes the problem from "write correct Terraform" to "design boundaries so failures are small, visible and recoverable".
- Partition by environment, identity, lifecycle and ownership; exchange values through published interfaces, not through other teams' state.
- Cross-account work is provider aliasing plus trust-policy design; provider blocks are static and removing one with resources in state is an error.
- Large migrations are sequences of empty-plan-gated steps: import destination, forget source without destroying, verify, clean up.
- Module ecosystems need versioning, consumer testing and cohort rollouts, or one release becomes an estate-wide incident.
- Policy is a lifecycle (observe, warn, enforce); drift detection is a service with owners and classification.
- Recovery needs backups of data, an independent inventory, rehearsed procedures and break-glass; Terraform restores shells, not contents.
- Expert judgement includes knowing when *not* to restructure, upgrade or centralise.

## Exercises

**Exercise 1.** An estate has four environments, three regions and twenty services. Propose the state partitioning: the key scheme, the layers, the owners, and the interface mechanism between layers. Name one boundary you chose *not* to draw and the cost of that choice.

**Exercise 2.** A bucket must move from a root owned by team A to a root owned by team B with zero replacement and no outage. Write the ordered runbook, the exact declarative blocks for each side, the gates between steps and the abort condition at each.

**Exercise 3.** You maintain a shared module used by sixty roots. Design the release of a breaking change (an internal resource is renamed and a default changes): `moved` blocks, versioning, consumer testing, cohort waves, and the communications you send.

**Exercise 4.** Write a drift-detection design for 200 roots: schedule, identity, rate-limit mitigation, classification, routing, metrics and the first three tuning actions after a week of noise.

**Exercise 5 (challenge).** A pipeline role that could apply to every production account was used by an unknown party for 36 hours. Outline containment, scoping of the damage, recovery of integrity, and the structural changes that would have limited the impact.

**Exercise 6 (challenge).** The state for a networking root was overwritten with an older version. The plan now proposes to create three subnets that exist and delete a route table in use. Explain what happened, what you do first, how you reconcile, and what prevents recurrence.

**Solution notes.** Exercise 1: a good answer separates account, region, layer and component in the key, publishes interfaces through a narrow channel and states plainly that a coarser partition (for example, not splitting by service within a layer) trades lock contention for fewer pipelines. Exercise 2: destination import first with an empty-plan gate, then a `removed` block with `destroy = false` in the source; a plan that wants to create the bucket is the abort signal. Exercise 3: expect `moved` blocks inside the module, a major version, a consumer-plan matrix in CI and waves with automated "no changes" checks. Exercise 5: containment starts with denying the trust policy; scope using audit logs and read-only drift detection; integrity is restored by reverting each unauthorised change and rotating whatever was readable. Exercise 6: state restored to an earlier point; freeze, restore the correct version or import the missing objects, and do not apply the proposed destroy; prevention includes versioning with review of writes, restricted write access, and serialised pipelines.
