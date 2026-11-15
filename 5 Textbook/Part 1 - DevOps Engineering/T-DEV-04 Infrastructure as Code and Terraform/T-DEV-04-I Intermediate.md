# T-DEV-04-I — Intermediate Practice

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-i"></a>
#### T-DEV-04-I — Intermediate Practice

## Why this level exists

At Beginner level one person runs one configuration on one laptop. Real work breaks every one of those assumptions. Several people change the same infrastructure. There are at least two environments that must resemble each other but not be identical. Some resources already exist and must be brought under management. Applies fail halfway. A colleague edits something in the console during an incident.

This level teaches the mechanics that make shared Terraform workable: richer variables and types, modules as interfaces, how the dependency graph decides ordering, remote state with locking, import and move operations that change *ownership* without changing infrastructure, environment layouts, drift decisions, and a method for reading failures. Pipeline design, policy and organisational controls belong to [T-DEV-04-P](T-DEV-04-P%20Professional.md#t-dev-04-p). If plans, state and `-/+` are not yet comfortable, revisit [T-DEV-04-B](T-DEV-04-B%20Beginner.md#t-dev-04-b) first.

## Variables, locals and outputs in depth

### Types and validation

Untyped variables push errors to apply time, when the cloud API rejects a value and you have a half-applied change. Type constraints and `validation` blocks move the error to plan time.

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment name."
  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be staging or prod."
  }
}

variable "instance_count" {
  type    = number
  default = 2
  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "instance_count must be between 1 and 10."
  }
}

variable "tags" {
  type    = map(string)
  default = {}
}

variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
}
```

Complex types (`list`, `map`, `set`, `object`, `tuple`) let a module accept structured input. Prefer `object` with explicit attributes over `any`: `any` disables checking, so errors reappear late. Optional attributes with defaults (`optional(string, "x")`) keep call sites small without losing the contract.

### Locals

Locals name an expression so you compute it once and reuse it; they are not inputs and cannot be overridden from outside.

```hcl
locals {
  name_prefix = "orders-${var.environment}"
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
  })
  private_subnets = { for k, s in var.subnets : k => s if startswith(k, "private-") }
}
```

Use locals to hold *derived* values and naming rules. If you find locals that merely rename a variable, delete them: indirection costs readers attention.

### Outputs as a contract

Outputs are what other code is allowed to depend on. Name them for the consumer's need, add a description, and mark secrets:

```hcl
output "vpc_id" {
  description = "Identifier of the network created by this module."
  value       = aws_vpc.main.id
}

output "database_password" {
  value     = random_password.db.result
  sensitive = true   # hides display; the value is still stored in state
}
```

Treat output names as a public API. Renaming one is a breaking change for everything that reads it.

## Expressions: `count`, `for_each` and dynamic blocks

To create several similar objects, Terraform offers two meta-arguments.

```hcl
# count: identity is the integer index
resource "local_file" "by_count" {
  count    = 3
  filename = "${path.module}/count-${count.index}.txt"
  content  = "item ${count.index}"
}

# for_each: identity is the key
resource "local_file" "by_key" {
  for_each = toset(["alpha", "beta", "gamma"])
  filename = "${path.module}/${each.key}.txt"
  content  = "item ${each.key}"
}
```

The difference bites when the list changes. With `count`, removing `"alpha"` from a list shifts every later item down one index, so Terraform proposes to *replace* all the shifted ones. With `for_each`, each object is tied to its key and only the removed key is destroyed. Default to `for_each` over a map or set of stable keys. Reserve `count` for "zero or one" (`count = var.enabled ? 1 : 0`) and genuinely interchangeable copies.

`for_each` keys must be known at plan time. A key derived from another resource's `id` (known only after apply) fails with an error such as "The `for_each` map includes keys derived from resource attributes that cannot be determined until apply". Derive keys from your own input instead, and use the unknown value only in the *values*.

A `dynamic` block generates repeated nested blocks from data:

```hcl
resource "aws_security_group" "web" {
  name   = "${local.name_prefix}-web"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidrs
    }
  }
}
```

Do not overuse it: a configuration with many nested `dynamic` blocks is hard to read, and the plan output becomes harder to review.

## Modules as interfaces

A module is an API for other engineers: required inputs, validated defaults, outputs and version constraints, not a pile of resources.

```text
modules/network/
  main.tf         # resources
  variables.tf    # inputs with types and validation
  outputs.tf      # the contract
  versions.tf     # required Terraform and provider versions
  README.md       # inputs, outputs, an example
  tests/          # terraform test files
```

A module that validates at its boundary:

```hcl
variable "vpc_cidr" {
  type = string
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid CIDR block."
  }
}

variable "allowed_cidrs" {
  type = list(string)
  validation {
    condition     = !contains(var.allowed_cidrs, "0.0.0.0/0")
    error_message = "Do not open ingress to the whole internet."
  }
}
```

Calling it:

```hcl
module "network" {
  source = "../../modules/network"

  vpc_cidr      = "10.50.0.0/16"
  allowed_cidrs = ["10.0.0.0/8"]
  tags          = local.common_tags
}

resource "aws_instance" "app" {
  subnet_id = module.network.private_subnet_ids[0]
  # ...
}
```

Rules of thumb for deciding what belongs in a module:

- **Extract when you repeat.** Two uses with differences you can name are a good time. One use "for reuse later" is speculation.
- **Expose decisions, not every argument.** A module that re-exports every provider argument is a verbose alias, not an abstraction.
- **Keep a module's resources at one level of concern.** A module called `platform` that creates networks, databases and DNS cannot be versioned sensibly.
- **Version consumers' view.** A module sourced from a path changes under the caller's feet; one sourced from a tag or a registry version changes only when the caller upgrades.

```hcl
module "network" {
  source  = "git::https://git.example.org/platform/terraform-network.git?ref=v1.4.2"
}
```

## The dependency graph

Terraform builds a directed acyclic graph from references. `aws_instance.app` that mentions `aws_subnet.private.id` gains an *implicit dependency*: the subnet is created first and destroyed last. Everything not connected by edges may run in parallel (the default parallelism is 10 concurrent operations).

```bash
terraform graph | dot -Tsvg > graph.svg    # requires Graphviz
terraform plan -parallelism=5              # useful if the API rate-limits you
```

When no attribute reference exists but an ordering requirement does (for example a policy must be attached before a service starts), add an *explicit* dependency:

```hcl
resource "aws_ecs_service" "app" {
  # ...
  depends_on = [aws_iam_role_policy_attachment.execution]
}
```

Use `depends_on` sparingly. It makes the graph less precise: everything that depends on the target can only be planned after the target's changes are known, which can turn small plans into broad "known after apply" plans. Prefer a real attribute reference whenever one exists.

Two error classes come from the graph:

| Error | Meaning | Typical fix |
| --- | --- | --- |
| `Cycle: a, b` | Two resources depend on each other | Break the loop with a third resource (for example, a separate rule resource instead of an inline one) |
| `Invalid for_each argument` | Keys unknown until apply | Derive keys from input; split into two applies if necessary |

A deliberate exception to "never use `-target`": `terraform apply -target=addr` applies only a resource and its dependencies. Use it to recover from a bootstrap problem or a broken provider, never as a routine way to avoid a big plan. A targeted apply leaves the rest of the configuration unchecked, so follow it with a full `plan` that you expect to be empty or understandable.

## Remote state with locking

Local state on a laptop is not a platform. Use an access-controlled backend with locking so two people cannot apply at once. A common AWS pattern uses an object-storage bucket with versioning and encryption:

```hcl
terraform {
  backend "s3" {
    bucket       = "example-org-tfstate"
    key          = "orders/staging/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true      # native S3 locking (Terraform 1.10+)
  }
}
```

The older pattern used a separate DynamoDB table for locks; it is deprecated for the S3 backend, so keep it only while migrating (set both, upgrade every user and pipeline, then remove the table). IAM must allow reading and writing both the state key and the sibling lock object. Use a different `key` per environment.

Backend blocks cannot use variables or expressions. To keep one configuration reusable across environments, leave values out and supply them at init time:

```hcl
terraform {
  backend "s3" {}
}
```

```bash
terraform init \
  -backend-config="bucket=example-org-tfstate" \
  -backend-config="key=orders/staging/terraform.tfstate" \
  -backend-config="region=eu-west-1"
```

Or keep them in a file per environment (`backend/staging.hcl`) and run `terraform init -backend-config=backend/staging.hcl`. If you switch backends, `terraform init -migrate-state` copies existing state; `-reconfigure` ignores previous backend settings and does *not* migrate. Mixing them up is a classic way to appear to "lose" state.

**Bootstrapping chicken-and-egg:** the state bucket itself is created by a small separate configuration (with local state or a manually created bucket), documented and rarely changed. Never destroy it while environments still use it.

**Prove locking works** before expensive resources exist: start an apply that sleeps (a `time_sleep` resource), then run a second `plan -lock-timeout=0s` and observe the lock error. Do not reach for `force-unlock` by reflex; first find the active run.

```text
Error: Error acquiring the state lock
Lock Info:
  ID:        3c1f...
  Path:      example-org-tfstate/orders/staging/terraform.tfstate
  Operation: OperationTypeApply
  Who:       ci-runner@build-17
```

The `Who` and `Operation` lines tell you whom to ask. `terraform force-unlock <ID>` is for a lock left behind by a dead process, and only after you have confirmed no apply is running.

### Reading another configuration's outputs

When one configuration needs a value created by another (a network's subnet identifiers), there are two main options:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "example-org-tfstate"
    key    = "network/staging/terraform.tfstate"
    region = "eu-west-1"
  }
}

# usage
subnet_id = data.terraform_remote_state.network.outputs.private_subnet_ids[0]
```

The caller then needs *read access to the other state*, which may include secrets unrelated to the outputs it wants. A narrower contract is to publish only the needed values to a parameter store or tag, and read them with ordinary data sources. Intermediate rule: know that `terraform_remote_state` couples the reader to the writer's state layout and permissions; the Professional level discusses safer contracts.

## Environment layouts

You need staging and production to share *code* but never share *state*. Three common layouts:

| Layout | How | Strength | Weakness |
| --- | --- | --- | --- |
| One root per environment (`envs/staging`, `envs/prod`) calling shared modules | Directory per environment, separate backend key | Explicit; plans are isolated; easy to differ deliberately | Some duplication of root files |
| One root with `*.tfvars` per environment | `terraform apply -var-file=prod.tfvars` with a different backend config per environment | Minimal duplication | Easy to run with the wrong var-file or backend |
| Workspaces | `terraform workspace select prod` | Quick copies of a single configuration | Same backend and code; very easy to apply to the wrong workspace; hides differences |

A recommended intermediate layout:

```text
infra/
  modules/
    network/
    service/
  envs/
    staging/
      main.tf          # calls modules with staging values
      backend.hcl
      staging.tfvars
    prod/
      main.tf
      backend.hcl
      prod.tfvars
```

Pass environment differences through variables and `*.tfvars` files; keep separate state keys and, usually, separate network ranges and name prefixes. Plan prod after changing only staging; its plan should be empty. If it is not, you have found drift or an undeliberate dependency between them.

Workspaces deserve a particular warning. They are fine for short-lived copies of one configuration (a developer's scratch copy), but using them for production versus staging means that a stale terminal tab and `terraform apply` is all it takes to change the wrong thing. Make the environment visible in the working directory and the backend key instead of in hidden CLI state.

## Staged first deployment

Some resources depend on others that must exist first (a container service needs an image, an image needs a registry). Use explicit stages: (A) apply network and registry with the runtime disabled; (B) outside Terraform, push an image and resolve its digest; (C) enable the runtime with that digest. A feature flag variable such as `enable_runtime` makes stages visible.

```hcl
variable "enable_runtime" {
  type    = bool
  default = false
}

variable "image_digest" {
  type    = string
  default = ""
  validation {
    condition     = var.image_digest == "" || can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "image_digest must be empty or a sha256 digest."
  }
}

resource "aws_ecs_service" "app" {
  count = var.enable_runtime ? 1 : 0
  # ...
}
```

Pin by digest rather than by a mutable tag so a plan describes exactly one image.

## Import and move: changing ownership without changing infrastructure

Two operations change Terraform's *mapping* between code and the real world while leaving the real world untouched.

### Importing something that already exists

Suppose a bucket was created by hand and should now be managed. Write the resource block, then declare an `import` block (Terraform 1.5+), which goes through plan and review like any other change:

```hcl
import {
  to = aws_s3_bucket.legacy
  id = "legacy-reports-bucket"
}

resource "aws_s3_bucket" "legacy" {
  bucket = "legacy-reports-bucket"
}
```

```bash
terraform plan                                  # shows: aws_s3_bucket.legacy will be imported
terraform plan -generate-config-out=generated.tf # draft code for resources you have not written
terraform apply
```

Treat generated configuration as a draft: it lists every attribute, including computed ones that should be removed. The acceptance test for any import is a **subsequent plan that proposes no changes**. If it proposes changes, your code differs from reality; decide which is right before applying.

After the import has been applied, delete the `import` block (it is harmless to keep but clutters the file) in a follow-up commit.

### Renaming or restructuring with `moved`

Renaming a resource address makes Terraform see "destroy the old one, create the new one". A `moved` block records that it is the same object:

```hcl
moved {
  from = aws_s3_bucket.logs
  to   = aws_s3_bucket.audit_logs
}

moved {
  from = aws_instance.app
  to   = module.compute.aws_instance.app
}
```

The plan then reports "has moved to" rather than destroy-and-create. Keep `moved` blocks in the configuration for as long as any consumer might still have the old addresses in state (for a shared module, a long time).

### Imperative equivalents

The older commands still exist and are sometimes necessary:

```bash
terraform state list
terraform state show aws_s3_bucket.logs
terraform state mv aws_s3_bucket.logs aws_s3_bucket.audit_logs
terraform state rm aws_s3_bucket.legacy      # forget it; do NOT destroy it
terraform import aws_s3_bucket.legacy legacy-reports-bucket
```

Prefer declarative blocks because they go through review and can be replayed on other environments; the imperative commands change state immediately and leave no trace in the repository. Whichever you use, **back up state first** (`terraform state pull > backup.tfstate`) and follow it with a plan expecting no changes.

`terraform state rm` deserves special care: it makes Terraform forget a resource, so the next plan proposes to create a duplicate, and the object keeps running, unmanaged. It is for handing ownership elsewhere, not for "making an error go away".

## Drift

Drift is when real infrastructure differs from state or code. Create it deliberately in a sandbox: tag a resource by hand, run `plan`, and read what Terraform wants to do.

Terraform offers a way to look at drift without proposing changes to configuration:

```bash
terraform plan -refresh-only      # shows only differences between state and reality
terraform apply -refresh-only     # records reality into state, changing nothing real
```

Decide explicitly, for each drifted item:

| Decision | Action | When |
| --- | --- | --- |
| **Revert** | Run a normal apply; Terraform restores the configured value | The manual change was unauthorised or accidental |
| **Adopt** | Change the code to match; then plan shows no changes | The manual change was right and should persist |
| **Accept temporarily** | `ignore_changes` or leave it with a ticket | A controller (autoscaler, operator) legitimately changes the value |

Record the decision and reason. `lifecycle { ignore_changes = [desired_count] }` is the right tool when something else *legitimately* owns an attribute (an autoscaler owning capacity). Used to silence an annoying diff, it hides real divergence.

## Testing modules

Use `terraform test` with deliberately failing cases first, then passing ones:

```hcl
# tests/network.tftest.hcl
run "rejects_open_ingress" {
  command = plan
  variables {
    allowed_cidrs = ["0.0.0.0/0"]
    vpc_cidr      = "10.50.0.0/16"
  }
  expect_failures = [var.allowed_cidrs]
}

run "accepts_private_ingress" {
  command = plan
  variables {
    allowed_cidrs = ["10.0.0.0/8"]
    vpc_cidr      = "10.50.0.0/16"
  }
  assert {
    condition     = aws_vpc.main.cidr_block == "10.50.0.0/16"
    error_message = "VPC CIDR was not propagated."
  }
}
```

```bash
terraform test
```

`command = plan` tests are fast and free; `command = apply` tests create real infrastructure and destroy it afterwards, which is slow and billable. Start with plan-time tests, add `mock_provider` blocks (Terraform 1.7+) when you need to exercise logic without credentials, and reserve real applies for a small number of critical paths in a sandbox account.

## When apply fails halfway

Terraform does not roll back. A failed apply leaves everything that succeeded in place and recorded in state, and stops at the first error in a dependency chain. Method:

1. **Read the error and the resource address.** The address says which resource; the message says what the provider API refused.
2. **Inspect what actually exists.** Use the provider's tooling or console. Some failures leave a half-created object that Terraform did not record.
3. **Run a fresh `plan` before applying again.** The plan now describes the remaining work; it is often shorter and easier to review than the original.
4. **Prefer fixing code** over `terraform state rm`, unless you understand ownership.
5. **Keep a short recovery log:** symptom, cause, action, prevention.

Common plan- and apply-time failure classes:

| Symptom | Likely cause | Move |
| --- | --- | --- |
| `Error: Invalid index` / `null value` | Output or attribute not available (count 0, unknown) | Check conditional resources; use `try()` or `one()` carefully |
| `AlreadyExists` on apply | Object exists outside state | Import it, or choose a different name |
| `AccessDenied` mid-apply | Role lacks one permission | Add the missing permission; re-plan; note it in the review |
| `DependencyViolation` on destroy | Something still references the object | Find the dependent object; it may be outside Terraform |
| Plan shows a replacement you did not expect | Immutable argument changed | Find `# forces replacement`; change the approach |
| `Provider configuration not present` | Resource in state, provider block removed | Restore the provider block until the resource is gone |
| Perpetual diff | Provider normalises a value differently | Match the normalised form; check provider issue list; last resort `ignore_changes` with a comment |

A useful debugging aid:

```bash
TF_LOG=debug terraform plan 2> debug.log   # verbose logs; may contain secrets, never commit or paste
terraform console                           # evaluate expressions against current state
```

## Lifecycle rules you should know exist

```hcl
resource "aws_db_instance" "main" {
  # ...
  lifecycle {
    prevent_destroy       = true               # plan errors if replacement or destroy is proposed
    create_before_destroy = false
    ignore_changes        = [password]         # something else rotates this
  }
}
```

`prevent_destroy` turns a data-loss accident into a plan-time error; it does not stop someone removing the whole block from code (then there is nothing to protect), so pair it with review. `create_before_destroy` creates the replacement first, which fits resources that must always exist, but name collisions can make it fail.

## Exercises

**Exercise 1.** Create two environment roots (`envs/staging`, `envs/prod`) using one module. Show that their states are isolated (different backend keys), that planning one never mentions the other, and that `terraform state list` differs where it should.

**Exercise 2.** Introduce drift: change a tag by hand. Run `plan` and `plan -refresh-only`. Write down which decision you made (revert, adopt, accept) and why.

**Exercise 3.** Rename a resource without using `moved` and observe the destroy-and-create plan; revert, then rename it again with a `moved` block and show that the plan reports a move.

**Exercise 4.** Using `local_file` resources, build the same three files with `count` and with `for_each`. Remove the first element from the input in both. Describe the difference between the two plans.

**Exercise 5 (challenge).** Create a resource by hand in a sandbox account, write the block and an `import` block, and reach a plan with no changes. Note every attribute you had to add or remove.

**Solution notes.** Exercise 3: without `moved` the plan shows `-` for the old address and `+` for the new; with it, "has moved to" and no replacement. Exercise 4: `count` renumbers and replaces the later items; `for_each` destroys only the removed key. Exercise 5 should end with `No changes`; if generated code was used, expect to delete read-only attributes such as ARNs and ids that are computed.
