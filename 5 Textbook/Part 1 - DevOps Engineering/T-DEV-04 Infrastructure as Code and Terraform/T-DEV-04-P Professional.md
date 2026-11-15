# T-DEV-04-P — Professional Engineering

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-p"></a>
#### T-DEV-04-P — Professional Engineering

## Why this level exists

Intermediate practice makes Terraform work for a team on a good day. Professional practice makes it *safe* on a bad one. Terraform with cloud credentials is a machine for changing production; whoever can influence its input (code, variables, modules, providers, state) can influence production. Everything in this level follows from that sentence: who can run it, what it may touch, what reviewers see, which checks must pass, how secrets are handled, how risky changes are staged, what cannot be undone, and who is accountable for each piece.

The level assumes remote state, modules and import/move are familiar ([T-DEV-04-I](T-DEV-04-I%20Intermediate.md#t-dev-04-i)). It does not require a particular CI product; the controls are described in terms any pipeline can implement. Organisation-scale partitioning, cross-account design and large migrations are in [T-DEV-04-E](T-DEV-04-E%20Expert.md#t-dev-04-e).

## State security and locking

State is a secret. It records every attribute the provider returned, including generated passwords, connection strings and private keys, and it is the authoritative map from code to production objects. Anyone who can write state can make Terraform believe things that are untrue; anyone who can read it can often read secrets.

Design the state backend as a security product:

| Control | Purpose | Example |
| --- | --- | --- |
| Encryption at rest | Disk or snapshot theft | Server-side encryption with a customer-managed key |
| Versioning | Recover from a bad write | Object versioning on the state bucket |
| Locking | One writer at a time | Native lock object, or the platform's lock |
| Narrow read access | State holds secrets | Only the plan and apply roles of *that* root |
| Narrow write access | State integrity | Only the apply role, never developers |
| Access logging | Detect misuse | Bucket access logs or data-event trails, reviewed |
| Deletion protection | Accidents | Bucket policy denying delete of the bucket and of object versions to everyone except a break-glass role |
| Separation by sensitivity | Limit blast radius | A distinct bucket (or at least prefix and role) for production |

An illustrative least-privilege policy for a role that applies one root (the state object and its sibling lock object):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListStateBucketPrefix",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::example-org-tfstate",
      "Condition": { "StringLike": { "s3:prefix": ["orders/prod/*"] } }
    },
    {
      "Sid": "ReadWriteThisStateOnly",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::example-org-tfstate/orders/prod/terraform.tfstate",
        "arn:aws:s3:::example-org-tfstate/orders/prod/terraform.tfstate.tflock"
      ]
    }
  ]
}
```

(The lock object is a sibling with a `.tflock` suffix. `DeleteObject` is needed on it because native locking creates and removes it. The *plan* role needs read on the state and write on the lock object, but no `PutObject` on the state itself.)

**Sensitive values.** `sensitive = true` on a variable or output hides it from CLI display; it does *not* remove it from state or from a saved plan file. Treat both as secret. Newer Terraform versions add *ephemeral* values and *write-only* attributes, which avoid persisting some secrets in state at all; adopt them where the provider supports them and verify what is actually stored rather than assuming.

**Recovery path.** Plan it before you need it:

1. Do not start by editing; take the lock or confirm no run is active, so nothing else writes.
2. List object versions of the state key; identify the last good version by timestamp and by the run that wrote it.
3. Restore by copying that version to be the current object (not by deleting the latest version blindly).
4. Run `terraform plan` and *read* it. State restored to an older point makes Terraform believe things that were created since never existed, so it may propose duplicates; import or reconcile before any apply.
5. Record the incident and the cause.

Drill this in a sandbox: corrupt a test state deliberately, restore it, reconcile. A recovery procedure never rehearsed is a hope.

**Lock discipline.** A lock error means someone or something is working. In order: read the `Who` and `Operation` in the message, check the pipeline for that run, wait for it, and only then consider `terraform force-unlock <ID>` — with a second person aware, because forcing a lock while an apply runs can corrupt state. Make pipelines serialise per root (one concurrency group per state), so locks rarely matter.

## Pipelines: plan in CI, apply from trust

Even a same-repository pull request can contain untrusted code. A Terraform configuration is executable: provider and module sources, `local-exec` provisioners, external data sources and the `external` provider all run arbitrary commands on the runner. So the pipeline must separate three lanes.

| Lane | Runs | Cloud access |
| --- | --- | --- |
| Untrusted validation | `fmt`, `validate`, module tests on every pull request | None — no credentials, no state read |
| Trusted plan | `plan` against remote state | Federated identity with a *plan* role, from a named trusted workflow and allowed refs |
| Trusted apply | Fresh plan then apply | Federated identity with an *apply* role, behind environment approval |

Never store long-lived access keys in the repository, and never let pull-request-authored workflow files freely assume roles that can read state. Scope the role's trust policy to the audience and subject (repository plus environment or branch); only add workflow-identity claims after verifying the token your provider actually issues.

An illustrative trust policy for an apply role, expressed in the cloud's own policy language, restricting the federated identity to one repository and one protected environment:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::111111111111:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:example-org/infra:environment:prod"
      }
    }
  }]
}
```

Use exact `StringEquals` on `sub`, not a wildcard `StringLike` that lets every branch or pull request assume the role. Check the claims your own CI actually issues rather than copying a subject format from a blog.

A skeleton of a pipeline's lanes, in generic shell form:

```bash
# lane 1: untrusted, no credentials
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
terraform test

# lane 2: trusted plan (federated plan role)
terraform init -input=false
terraform plan -input=false -lock-timeout=60s -out=tfplan
terraform show -json tfplan > plan.json

# lane 3: trusted apply, after approval
terraform init -input=false
terraform apply -input=false tfplan     # the exact plan that was approved
```

Notes: `-input=false` stops silent prompts hanging a runner; `-backend=false` lets validation run with no state access; a saved plan can only be applied by the same Terraform version, provider versions and (by default) against the same state serial, so a stale plan fails closed rather than doing something unreviewed.

## Review workflows

A reviewer cannot review what they cannot see. For Terraform changes, the artefact to review is the **plan**, not only the diff of `.tf` files: a three-line change to a module's default can replace forty resources.

Publish a *plan summary* (resources added, changed, destroyed, replacements, security-group widening) for reviewers rather than the raw plan, because raw plans can contain sensitive values. Redaction is not a security control; restrict who can read summaries.

A summary can be derived from the plan JSON:

```bash
terraform show -json tfplan | jq -r '
  .resource_changes[]
  | select(.change.actions != ["no-op"] and .change.actions != ["read"])
  | "\(.change.actions | join("+"))\t\(.address)"' | sort
```

An output such as this is a reviewable artefact:

```text
create          aws_cloudwatch_log_group.app
delete+create   aws_lb_listener.https
update          aws_security_group.web
```

The line `delete+create` is a replacement; the reviewer's question is "what does the world look like between the delete and the create?"

Reviewer checklist for an infrastructure change:

1. **Blast radius.** Which environments and which resources, by name? Is anything replaced?
2. **Stateful objects.** Does any database, volume, queue, bucket, key or DNS zone appear among updates, replacements or destroys?
3. **Access widening.** Does any ingress, role, trust policy or bucket policy become broader?
4. **Cost.** Does the change add always-on or per-request costs?
5. **Ordering and rollout.** Is the change safe if it applies halfway? Does it need staging (see "Safe migrations")?
6. **Rollback.** What would reverting mean? Is it possible (see "Rollback limits")?
7. **Evidence.** Which test, plan or policy output supports the claim that the change is safe?

Require that **the apply runs the plan that was reviewed, or a fresh plan that is compared with it**. A plan computed earlier may be stale if state or the live world moved. For production, apply the exact saved plan, and fail the job if the plan's summary hash differs from what was approved.

Review sizes matter. A pull request mixing a module upgrade, a provider upgrade and a resource change produces a plan nobody can attribute. Insist that dependency upgrades (lock-file changes, module version bumps) arrive on their own and produce a plan with *no* resource changes unless the upgrade intends them.

## Policy as code

Humans miss things in long plans. Machines should check the rules that never change. Run checks over the plan JSON (for example, with a policy engine such as Open Policy Agent via `conftest`, or a managed policy product) and treat a failing policy as a failing check.

```rego
package terraform.plan

import rego.v1

# deny security group rules that open ingress to the whole internet
deny contains msg if {
  some rc in input.resource_changes
  rc.type == "aws_vpc_security_group_ingress_rule"
  rc.change.after.cidr_ipv4 == "0.0.0.0/0"
  msg := sprintf("%s opens ingress to 0.0.0.0/0", [rc.address])
}

# deny deletion or replacement of stateful resources without an explicit exception
protected := {"aws_db_instance", "aws_s3_bucket", "aws_kms_key", "aws_dynamodb_table"}

deny contains msg if {
  some rc in input.resource_changes
  rc.type in protected
  "delete" in rc.change.actions
  msg := sprintf("%s would be destroyed or replaced", [rc.address])
}

# require owner tag on taggable resources being created or updated
deny contains msg if {
  some rc in input.resource_changes
  rc.change.after.tags
  not rc.change.after.tags.Owner
  msg := sprintf("%s has no Owner tag", [rc.address])
}
```

```bash
terraform show -json tfplan > plan.json
conftest test --policy policy/ plan.json
```

Check your rules against real plan JSON before trusting them: tags inherited from provider `default_tags` appear under `tags_all`, not `tags`, so a rule that reads only `tags` can fire falsely or miss; and attributes that are unknown until apply appear under `after_unknown`, not `after`. Write a failing sample plan for each rule and keep it in the policy tests.

Policy categories that earn their keep:

| Category | Example rule | Note |
| --- | --- | --- |
| Exposure | No public ingress, no public buckets or snapshots | Highest value, lowest false-positive rate |
| Encryption | Storage and queues encrypted with approved keys | Check the *after* values |
| Identity | No wildcard actions on wildcard resources; no new cross-account trust without approval | Needs exceptions and a named approver |
| Hygiene | Required tags, approved regions and instance families | Enables cost allocation and ownership |
| Destruction | No delete or replace of stateful types without a labelled exception | Pair with `prevent_destroy` |
| Provenance | Modules only from approved sources and pinned versions | Check configuration, not just plan |

Static analysis of configuration (tools that scan `.tf` for known misconfigurations) catches problems before a plan exists; plan-based policy sees computed values. Use both; they have different blind spots.

**Document known gaps honestly.** Policy only sees what the plan shows: it cannot see a role a human adds afterwards, a console change, a resource Terraform does not manage, or values unknown until apply (a key that is `(known after apply)` cannot be matched against a rule). Publish a list of what policy does *not* cover, so nobody mistakes "policy passed" for "safe".

**Exceptions.** Make them explicit, scoped, owned and expiring: an exception file in the repository that names the address, the rule, the approver and an expiry date, which the policy reads. Exceptions that never expire become the real policy.

## Module contracts

A module is a promise to its consumers. Write the promise down and test it.

Design rules:

- Small, focused modules with explicit inputs and outputs; avoid pass-through of every provider argument.
- Validate inputs (CIDRs, names, sizes) at the boundary; encode policy such as "no open ingress" in validation or in a policy check.
- Version modules (tags or a registry) and write upgrade notes. Consumers pin versions.
- Prefer composition over deep nesting; avoid `count`/`for_each` on resources whose identity may change without a `moved` block.
- Use `moved` blocks to rename or restructure without replacing resources.
- Add `lifecycle { prevent_destroy = true }` on stateful resources, with a documented way to remove it deliberately.
- Use `precondition` and `postcondition` to state assumptions where validation of a single variable is not enough.

```hcl
resource "aws_db_instance" "main" {
  # ...
  lifecycle {
    prevent_destroy = true

    precondition {
      condition     = var.environment != "prod" || var.multi_az
      error_message = "Production databases must be multi-AZ."
    }
  }
}
```

A contract has four parts, each testable:

| Part | What to state | How to check |
| --- | --- | --- |
| Inputs | Types, validation, defaults that are safe | `terraform test` with failing cases |
| Outputs | Names and meaning; which are sensitive | A test asserting each output exists |
| Behaviour | What it creates, what it never touches | Plan-based assertions; policy |
| Change policy | What counts as breaking; how upgrades are communicated | Semver rules; changelog; upgrade notes |

**What is a breaking change?** Removing or renaming an input or output; changing a default in a way that alters resources; changing a resource's identity (address) without a `moved` block; raising the required provider major version; tightening validation so that formerly valid input fails. A new optional input with a default that changes nothing is not breaking. Decide this *in the contributing guide*, not during an argument.

**Provider configuration.** Child modules should not declare `provider` blocks with credentials; the root passes providers in. Declare the requirement with `required_providers` and let the caller decide regions and identities.

## Secrets

The rule is that secret *values* should not enter Terraform at all if there is an alternative; where they must, treat each place they land as secret storage.

| Pattern | Use | Caveat |
| --- | --- | --- |
| Create the secret container in Terraform; set the value elsewhere | Preferred: Terraform owns the existence and permissions, a human or system rotates the value | The value never appears in code or plan |
| Generate in Terraform (`random_password`) and store in a secret manager | Acceptable for bootstrap | The value is in state; restrict state, consider rotation outside Terraform |
| Read at apply time via a data source | When another system owns the value | The value lands in state; the apply role needs read access |
| Pass as an environment variable (`TF_VAR_x`) from the CI secret store | Short-lived inputs | Shows up in plan files; never echo; `sensitive = true` |
| Commit encrypted values | Only with a reviewed, tested scheme | Key management becomes the problem |
| Commit in plain text | Never | Rotate immediately if it happens |

```hcl
resource "aws_secretsmanager_secret" "db" {
  name = "orders/${var.environment}/db"
}

# Deliberately NO aws_secretsmanager_secret_version resource here:
# the value is set by the rotation process or an operator, so it never
# appears in code, plan output or this configuration's state.

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db.arn   # consumers get the pointer, not the value
}
```

A pragmatic variant is to let the database manage its own master credential in the secret manager and have Terraform reference only the secret's identifier. Whatever you choose, check the *actual* state after apply (`terraform state pull | jq` on a throwaway copy) to see what was stored; do not rely on the documentation of "sensitive".

If a secret is committed or leaked through a plan artefact, the response is the same as for any leak: rotate first, then clean up (see [T-DEV-01-P](../T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-P%20Professional.md#t-dev-01-p)). Deleting the file or the CI log is not rotation.

## Safe migrations

Most Terraform incidents are not creation; they are *changing* something that already carries traffic or data. A migration plan has stages, each ending in an observable check.

**Pattern: expand, migrate, contract.**

1. **Expand.** Add the new thing alongside the old, with no consumer yet. The plan should show only creates.
2. **Migrate.** Move consumers (DNS weight, application config, a dependency's reference) in small steps, verifying each by a real signal, not by "apply succeeded".
3. **Contract.** Remove the old thing only after a soak period during which nothing used it. The plan should show only destroys of objects you can name.

**Rename or restructure with no replacement:** add a `moved` block, run `plan`, confirm it reports moves and **zero** creates and destroys, apply.

**Change something that forces replacement:** do not accept `-/+` on stateful objects. Options: create a new resource with a new identity, migrate data or traffic, then remove the old one; use `create_before_destroy` where names allow; or change a setting in place via a provider-specific path if one exists.

**Take over an existing object:** `import` block, then a plan showing no changes (see Intermediate). Do it in a branch, run it against staging first, and keep the block until every environment has applied it.

**Upgrade a provider major version:** read the upgrade guide, upgrade in a branch, run `terraform init -upgrade`, run `plan` in every environment, and require *no unexpected changes* before the upgrade merges. Defaults change between majors.

**Split a configuration:** see the cross-state moves in [T-DEV-04-E](T-DEV-04-E%20Expert.md#t-dev-04-e). The rule at this level: never split by `state rm` on one side and hope.

**Before every risky apply**, write down: the plan summary, the expected duration, the signal that shows it is going wrong, who can stop it, and what you will do if it halts halfway.

## Testing in text

Infrastructure tests are cheaper the earlier they run. Arrange them as a pyramid:

| Layer | Tool | Cost | What it catches |
| --- | --- | --- | --- |
| Format and syntax | `fmt -check`, `validate` | Seconds | Typos, broken references |
| Static analysis | Linters and security scanners over `.tf` | Seconds | Known misconfigurations, deprecated syntax |
| Plan-time unit tests | `terraform test` with `command = plan` and mock providers | Seconds | Validation rules, naming, tags, logic |
| Plan policy | Policy engine over plan JSON | Seconds | Exposure, destruction, hygiene |
| Apply tests in a sandbox | `terraform test` with `command = apply`, or a harness | Minutes, real money | Provider behaviour, permissions, ordering |
| Operational checks | Smoke test of the deployed result | Minutes | "Does it actually work?" |

A plan-time test with a mocked provider (no credentials, no cost):

```hcl
# tests/tags.tftest.hcl
mock_provider "aws" {}

run "owner_tag_is_required" {
  command = plan
  variables {
    environment = "staging"
    tags        = {}
  }
  expect_failures = [var.tags]
}

run "bucket_is_encrypted_and_private" {
  command = plan
  variables {
    environment = "staging"
    tags        = { Owner = "platform" }
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_policy == true
    error_message = "Bucket must block public policies."
  }
}
```

Exercise a negative test for every validation rule: a rule never seen failing is a rule that may not work. Add `check` blocks for assertions that should hold in a running environment (for example, an endpoint responds), which report as warnings during plan and apply rather than blocking.

**Testing a migration in text** means rehearsing it on a copy: restore a staging state into a scratch root, run the migration commit against it, and require the post-condition "plan is empty". Keep the rehearsal log with the change.

## Rollback limits

"We can just revert the commit" is only true for stateless things. Reverting code and applying produces a *new* forward change that tries to recreate the previous shape. What it cannot do:

| Object | Can revert restore it? | What actually happens |
| --- | --- | --- |
| Stateless config (a tag, a rule) | Yes | Restored |
| A destroyed database | No | A new empty database; data restored only from backups |
| A deleted encryption key | No | Key deletion has waiting periods; after them data is gone |
| A replaced resource with a generated address | No | New address, new endpoint; consumers still point at the old one |
| A rotated or deleted secret | No | New value; clients with the old one fail |
| A DNS change | Partly | Caches hold the old answer for the TTL, in both directions |
| Provider-side destroy protections | N/A | Some objects cannot be recreated under the same name for days |
| A schema or data migration | No | Needs its own reverse migration |

Therefore:

- Take and test backups and snapshots *before* risky changes; verify a restore, not just a snapshot's existence.
- Use `prevent_destroy` and deletion protection on stateful resources.
- Treat key deletion as a one-way door; use the shortest-reasonable wait only deliberately.
- Prefer forward fixes for partial failures: fix the code and re-apply. Only "revert" when you have worked out what the revert's plan will do.
- Keep the *previous* known-good plan or commit identified, so that rollback is a rehearsed apply of a known artefact and not a design exercise at 3 a.m.

## Cost, tags and teardown

Set a budget alarm before leaving resources running. Tag everything with `Project`, `Owner`, `Environment`. Understand cost drivers: a NAT gateway or an always-on load balancer dominates a small environment. Write a teardown order — runtime, then network, never the bootstrap while environments exist — and rehearse it. Have a second engineer provision or destroy an environment using only the README.

Enforce tags in two places: `default_tags` on the provider (so you do not rely on every author remembering), and a policy that rejects untagged taggable resources. Idle policy for non-production: scale to zero or destroy after a defined number of days, with a tag (`ExpiresOn`) that a scheduled job honours.

## Ownership

Every state, module, pipeline and policy needs a named owner, or it will rot.

| Artefact | Owner answers | Evidence |
| --- | --- | --- |
| Each root configuration | Who approves its plans? Who is paged when its apply fails? | CODEOWNERS entry; runbook link |
| Shared modules | Who triages issues and releases versions? | Maintainers file; release notes |
| State backend | Who handles recovery, key rotation and access review? | Quarterly access review record |
| Pipeline roles | Who reviews trust policy changes? | Review requirements on those files |
| Policy library | Who decides exceptions? | Exception file with approvers |
| Provider and Terraform versions | Who schedules upgrades? | Upgrade calendar |

Treat the trust policies, backend configuration, pipeline definitions and policy files as the most sensitive paths in the repository, and protect them with ownership rules and required reviews from a platform or security group (see [T-DEV-01-P](../T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-P%20Professional.md#t-dev-01-p)).

## Blast radius thinking

Replacing a load balancer and replacing a task definition are different events. Before approving a plan, name what will be replaced, what depends on it and what users will experience. Large root configurations increase blast radius; split by lifecycle and by owner. A good split follows rates of change and impact: the network changes rarely and breaks everything; an application's service changes daily and breaks one thing. Do not let them share a state.

## Decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Understand a change | `plan`, `show`, look for replacements | Blind `apply` |
| Share state | Remote backend, native locking, IAM | A state file in a synced folder |
| Isolate environments | Separate state keys, ranges, prefixes | One state for everything |
| Run in CI | Validation with no cloud access; plan via scoped federation | Wildcard trust; PR code assuming a plan role |
| Handle drift | Fresh plan, then revert, import or accept | Console edits forever |
| Hit a lock error | Wait or find the active run | Reflexive `force-unlock` |
| Rename a resource | `moved` block, plan shows no replacement | Rename and hope |
| Adopt an existing object | `import` block, empty plan afterwards | Pasting guessed attributes and applying |
| Store a secret | Container in Terraform, value elsewhere | Plain-text variables in the repository |
| Upgrade a provider | Own branch, plan in every environment | Bundling with feature changes |
| Remove something risky | Expand, migrate, contract | Deleting and watching |

## Knowledge consolidation

- Terraform with credentials is a production-change machine; control who and what can influence its input.
- State is a secret and an integrity-critical record: encrypt, version, lock, scope, log, and rehearse recovery.
- Separate untrusted validation, trusted plan and trusted apply; federate identities and scope trust exactly.
- Review the plan, not only the diff; apply what was reviewed.
- Policy as code catches the rules that never change, and its gaps must be documented.
- A module is a contract with inputs, outputs, behaviour and a change policy; test negative cases.
- Revert is not rollback for stateful, keyed or cached things; design with that in mind.
- Every artefact has a named owner; unowned trust policies are the most dangerous.

## Exercises

**Exercise 1.** Write a least-privilege access policy for the plan role and the apply role of one root: which actions on the state object, the lock object and the cloud resources it manages. State which role may read secrets in state and why.

**Exercise 2.** Write three policy rules (exposure, destruction, hygiene) as sentences, then as rules for a policy engine of your choice. Give one plan that should fail each and one that should pass. List two things your policy cannot see.

**Exercise 3.** Design a module contract for a storage module: inputs with validation, outputs, three negative tests, and a one-paragraph definition of what counts as a breaking change.

**Exercise 4.** Plan a migration of a database from one identity to another with no downtime using expand, migrate, contract. For each stage name the observable check and the abort condition.

**Exercise 5 (challenge).** A production apply failed halfway: the new load balancer exists, the old listener was destroyed, and the new target group is empty. Write the first five actions, say whether you revert or fix forward, and justify it using the rollback limits table.

**Solution notes.** Exercise 1: the plan role can read state and write only the lock object; only the apply role writes state; the secrets question should conclude that anything able to read state can read stored secrets, so both roles are privileged. Exercise 2: valid gaps include console changes, unknown-after-apply values and unmanaged resources. Exercise 4: checks should be real signals (error rate, replica lag, connection counts), not "apply succeeded". Exercise 5: stabilise first (restore traffic to a known good path), inspect what exists, run a fresh plan, and prefer forward fix when the revert would recreate objects with new addresses.
