# T-DEV-04-B — Beginner Foundations

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-b"></a>
#### T-DEV-04-B — Beginner Foundations

## Why this matters

Every running system sits on infrastructure: networks, servers, databases, queues, permissions, DNS records. Someone has to create those things, and later someone has to change them. If the creation happened by clicking through a console, the knowledge of *what exists and why* lives in a person's memory and a trail of audit events nobody reads. When that person leaves, or when the environment must be rebuilt after an incident, the team discovers it cannot reproduce what it depends on.

**Infrastructure as code (IaC)** replaces that with text files. The files describe the infrastructure; a tool reads them and makes the real world match. Because the description is text, it can live in version control, be reviewed in a pull request, be tested, and be applied the same way every time. The infrastructure change becomes an ordinary engineering change with a diff, a reviewer and a history.

**Terraform** is the most widely used tool for this. It is not the only one (there are cloud-specific tools, general-purpose-language tools and a community fork of Terraform), but the ideas it forces you to learn are universal: *desired state versus actual state, plans before changes, state as a record, modules as reusable interfaces, and drift when reality moves behind your back.* Learn those and every other tool becomes a dialect.

This level gets you from zero to a safe first workflow. It assumes you can use a terminal and have met Git (see [T-DEV-01-B](../T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-B%20Beginner.md#t-dev-01-b)). It does not assume any cloud experience: the first examples need no account at all.

## Imperative versus declarative

There are two ways to tell a machine how to arrive at a result.

**Imperative** (procedural) instructions say *how*: do step 1, then step 2, then step 3.

```bash
# imperative: a script that builds a storage bucket
aws s3api create-bucket --bucket example-notes-1234 --region eu-west-1 \
  --create-bucket-configuration LocationConstraint=eu-west-1
aws s3api put-bucket-tagging --bucket example-notes-1234 \
  --tagging 'TagSet=[{Key=Owner,Value=training}]'
```

Run that twice and the second run fails because the bucket already exists. Change the tag value and run it again and the script has no idea what to do about the old tag. To handle every case you must write the checking, branching and clean-up logic yourself, and that logic is where scripts rot.

**Declarative** instructions say *what the end result must look like*:

```hcl
resource "aws_s3_bucket" "notes" {
  bucket = "example-notes-1234"
  tags   = { Owner = "training" }
}
```

Terraform compares this description with what it knows exists, works out the difference, and performs only the steps required. Run it twice and the second run does nothing. Change the tag and it updates the tag. Delete the block and it removes the bucket. The property that "running it again with no changes does nothing" is called **idempotence**, and it is what makes reviewing and repeating safe.

| | Imperative script | Declarative configuration |
| --- | --- | --- |
| You write | Steps | Desired end state |
| Second run | May fail or duplicate | Does nothing if already correct |
| Removing something | You write the delete step | You delete the block |
| Review in a pull request | You review commands | You review the resulting shape |
| Risk | Hidden ordering and missing checks | Surprising replacements; state mistakes |

Declarative is not magic: the tool still performs imperative API calls underneath. You are moving the *planning* from your head into the tool.

## The three-way picture: code, state and reality

Hold this picture for the rest of the chapter. Terraform always reasons about three things:

1. **Configuration** — what your `.tf` files say should exist.
2. **State** — Terraform's own record of which real objects it created or adopted, and their last-known attributes.
3. **Reality** — what the provider's API actually reports right now.

`terraform plan` refreshes state from reality, compares it with configuration and shows the difference. Nearly every Terraform surprise is a mismatch between two of these three: code says one thing, state remembers another, reality holds a third. When something puzzling happens, ask which pair disagrees.

## Core concepts

| Concept | Meaning |
| --- | --- |
| Provider | Plugin that talks to an API (a cloud, a Git host, a monitoring service, even the local filesystem). |
| Resource | An object Terraform creates, updates or destroys. |
| Data source | A read-only lookup of something that already exists. |
| Variable | An input to a configuration; makes it reusable. |
| Output | A value a configuration publishes after apply. |
| Local | A named expression inside a configuration; avoids repetition. |
| State | Terraform's record of which real objects correspond to your configuration. |
| Plan | A proposed set of changes computed from configuration, state and reality. |
| Apply | Executing a plan. |
| Module | A reusable bundle of configuration with inputs and outputs. |
| Backend | Where state is stored (a local file, or a remote service with locking). |

Desired configuration is code. **State is privileged data**: it can contain credential-like values even when the configuration does not, because providers store whatever the API returned, including generated passwords.

## What a Terraform project looks like

A configuration is a directory of files ending in `.tf`. Terraform reads every `.tf` file in the directory as one unit, so the file names are for humans only. A common starting layout:

```text
my-first-iac/
  main.tf              # resources
  variables.tf         # input variables
  outputs.tf           # outputs
  versions.tf          # terraform block: required version, providers
  .terraform.lock.hcl  # provider version pins (commit this)
  .gitignore           # ignore state and local plugin cache
```

The language, HCL, has a handful of building blocks:

```hcl
# A block has a type, optional labels, and a body of arguments.
resource "local_file" "note" {        # type "resource"; labels: provider type, local name
  filename = "${path.module}/note.txt" # argument = expression
  content  = "hello"
}
```

- `resource "local_file" "note"` declares a resource of type `local_file`, named `note` inside this configuration. Its **address** is `local_file.note`; you will see that string in every plan.
- Expressions refer to other objects by address: `local_file.note.filename`. That reference also creates a **dependency**: Terraform knows it must create `note` before anything that uses its attributes.
- `"${...}"` inserts an expression into a string. `path.module` is the directory of the current configuration.
- `#` starts a comment.

Terraform builds a graph of resources from these references and creates independent resources in parallel, ordering dependent ones correctly. You rarely need to say "do this first" yourself.

## Providers: where the real work happens

Terraform itself knows nothing about clouds. **Providers** are separate plugins, downloaded by `terraform init`, that translate resource blocks into API calls. The `required_providers` block names them and constrains their versions:

```hcl
terraform {
  required_version = ">= 1.9"
  required_providers {
    local = { source = "hashicorp/local", version = "~> 2.5" }
  }
}
```

`~> 2.5` means "2.5 or newer, but below 3.0". Provider major versions can change behaviour, which is why the version is constrained and why `.terraform.lock.hcl` records the exact version and checksums chosen.

## The workflow

Five commands carry most daily work.

```bash
terraform fmt -check       # consistent formatting (omit -check to rewrite files)
terraform init             # download providers, configure the backend
terraform validate         # syntax and internal consistency; no API calls
terraform plan -out=tfplan # what would change?
terraform show tfplan      # read it carefully
terraform apply tfplan     # only after review
terraform destroy          # removal of everything this configuration manages
```

Treat `plan` as the point of the whole tool. The plan is the reviewable artefact; `apply` is merely its execution.

## A tiny first configuration (no cloud account needed)

This configuration writes a text file on your own machine using the `local` provider. It is a perfect first lab: it has the full lifecycle of a real resource, costs nothing and cannot damage anything beyond a file in your project folder.

```hcl
terraform {
  required_version = ">= 1.9"
  required_providers {
    local = { source = "hashicorp/local", version = "~> 2.5" }
  }
}

variable "greeting" {
  type    = string
  default = "hello"
}

resource "local_file" "note" {
  filename = "${path.module}/note.txt"
  content  = var.greeting
}

output "path" {
  value = local_file.note.filename
}
```

Run the workflow, then change `greeting` and run `plan` again. Read the symbols: `+` create, `~` update in place, `-` destroy, `-/+` replace. A replacement means the old object is destroyed — for a database or load balancer that matters enormously.

### Reading a plan, line by line

Change `greeting` from `"hello"` to `"hi"` and run `terraform plan`:

```text
  # local_file.note must be replaced
-/+ resource "local_file" "note" {
      ~ content  = "hello" -> "hi" # forces replacement
      ~ id       = "aaf4c61..." -> (known after apply)
        # (1 unchanged attribute hidden)
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

`# forces replacement` is the line to find. For a `local_file`, replacement is trivial. For a database, changing a field that forces replacement would destroy data. The habit that prevents harm is to read the summary line first (`Plan: 1 to add, 0 to change, 1 to destroy`), then look at every `-` and `-/+`. Also notice `(known after apply)`: some values only exist once the real object is created.

A healthy plan on an unchanged configuration says:

```text
No changes. Your infrastructure matches the configuration.
```

That empty plan is your baseline. Whenever you are unsure about the state of things, an empty plan is the strongest evidence you can have that code and reality agree.

## State: what it is and what goes wrong without it

State maps `local_file.note` in your configuration to the real object. If state is lost, Terraform believes nothing exists and proposes to create everything again, usually failing against what already exists. If state is edited carelessly, the mapping becomes wrong. Beginners usually keep state locally in `terraform.tfstate`; teams keep it in a *remote backend* with locking so two people cannot apply at once. Because state can contain secrets, restrict access to it as strictly as to a credential store.

Look at your own state without opening the file:

```bash
terraform state list                 # every address Terraform tracks
terraform state show local_file.note # attributes of one object
```

Do not edit the state file by hand. There are supported commands for the rare cases that need it; they are Intermediate and Expert material.

## Drift

If someone changes a real resource outside Terraform, reality no longer matches state. `terraform plan` detects it by refreshing and shows the difference, offering to put things back. The practical rule: make changes through code, or accept that the next plan will propose reverting them.

```bash
echo "edited by hand" > note.txt     # change outside Terraform
terraform plan                       # shows the file will be updated to match configuration
```

This is the friendliest possible demonstration of drift. In a cloud account the same effect happens when a colleague changes a firewall rule in the console: the next plan proposes to undo it, and if that rule was keeping an incident mitigated, applying blindly reintroduces the incident.

## Variables, outputs and locals

Variables make a configuration reusable; outputs expose results; locals name an intermediate value.

```hcl
variable "greeting" {
  type        = string
  description = "Text written to the note"
  default     = "hello"
}

locals {
  full_text = "${var.greeting}\n"
}

resource "local_file" "note" {
  filename = "${path.module}/note.txt"
  content  = local.full_text
}

output "path" {
  value = local_file.note.filename
}
```

There are several ways to supply a variable, from lowest to highest precedence: the default in the file, `TF_VAR_` environment variables, `terraform.tfvars` files, then `-var` flags.

```bash
terraform plan -var 'greeting=hi'
TF_VAR_greeting=hi terraform plan
terraform output path
```

Mark a variable `sensitive = true` if its value is a secret; Terraform then hides it from console output (it is still stored in state — hiding is not protection).

## A first module

A *module* is a directory of `.tf` files called from another configuration. Every configuration is already a module (the "root module"); the idea becomes useful when you repeat yourself.

```text
my-first-iac/
  main.tf
  modules/
    note/
      main.tf
      variables.tf
```

```hcl
# main.tf
module "welcome" {
  source   = "./modules/note"
  filename = "${path.module}/welcome.txt"
  text     = "welcome"
}

module "goodbye" {
  source   = "./modules/note"
  filename = "${path.module}/goodbye.txt"
  text     = "goodbye"
}
```

After adding a module call, run `terraform init` again: Terraform needs to register the module. Use a module when you repeat the same set of resources and want one tested definition; do not create one for a single resource "just in case".

## A first cloud example, with cost safeguards

When you are ready to touch a real cloud, do so deliberately. The local lab taught the workflow; this section adds the habits that keep a learning exercise from becoming an invoice. The example uses AWS because it is common; the safeguards apply to any provider.

**Before writing any code, set the safeguards:**

1. **Use a dedicated sandbox account or project**, not a shared or production one. A mistake then has a ceiling.
2. **Create a budget alert** in the provider's billing console (a few currency units, with email notification at 50 % and 80 %). A budget alerts you; it does not stop spending. It is a smoke detector, not a sprinkler.
3. **Use a single region** and note it. Resources forgotten in another region are the most common unpleasant surprise.
4. **Authenticate with short-lived credentials** (single sign-on or a temporary session), not a long-lived access key saved on disk.
5. **Choose resources that are free or nearly free while idle.** A storage bucket costs fractions of a cent when empty. A NAT gateway, a load balancer, a managed database or a running virtual machine does not; do not use them in a first example.
6. **Plan the teardown before the apply.** Know the exact command (`terraform destroy`) and verify afterwards that nothing remains.

A disposable configuration that follows these rules:

```hcl
terraform {
  required_version = ">= 1.9"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 6.0" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = {
      Project     = "iac-learning"
      Owner       = "your-name"
      Environment = "sandbox"
      Disposable  = "true"
    }
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "lab" {
  bucket        = "iac-learning-${random_id.suffix.hex}"
  force_destroy = true   # lets destroy remove a bucket that still has objects: ONLY for disposable labs
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket                  = aws_s3_bucket.lab.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_name" {
  value = aws_s3_bucket.lab.bucket
}
```

Notes on the choices:

- `default_tags` applies the same tags to every resource that supports them, so anything left behind is identifiable by `Disposable = true` and `Owner`.
- The random suffix exists because bucket names are global; without it your name probably collides with someone else's.
- The public access block is a safe default. Learning labs should not create public things by accident.
- `force_destroy = true` is a deliberate lab-only convenience. In real configurations it is dangerous because it deletes data; you will see why in the Professional level.

Run the full lifecycle, and **finish it**:

```bash
terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output bucket_name
terraform destroy
terraform state list      # should print nothing
```

Then confirm independently of Terraform that nothing remains, using the provider's own tooling or console and filtering by your tag. A successful `destroy` message is strong evidence, not proof: resources created by hand next to yours are not Terraform's to remove.

**A budget as code (optional).** Teams often define the alert with Terraform too. This resource is free for the first few budgets in many accounts, but check your provider's current pricing:

```hcl
resource "aws_budgets_budget" "lab" {
  name         = "iac-learning-monthly"
  budget_type  = "COST"
  limit_amount = "5"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["you@example.com"]
  }
}
```

Remember its limit: it notifies after spending reaches the threshold, and billing data lags. It is not a hard cap.

## What to commit

Commit `.tf` files and `.terraform.lock.hcl` (it pins provider versions). Never commit `*.tfstate`, `.terraform/` or variable files containing secrets. Create `.gitignore` before the first commit:

```text
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
crash.log
tfplan
```

(If you need a `.tfvars` file with non-secret defaults, commit it deliberately under a name such as `staging.tfvars` and exclude the others by pattern.)

## Command reference

| Command | What it does | Changes anything real? |
| --- | --- | --- |
| `terraform fmt -check` | Verifies formatting | No |
| `terraform init` | Downloads providers, configures the backend | Only local files (`.terraform/`) |
| `terraform validate` | Checks syntax and consistency | No |
| `terraform plan -out=tfplan` | Computes and saves a plan | No |
| `terraform show tfplan` | Prints a saved plan | No |
| `terraform apply tfplan` | Executes exactly that plan | **Yes** |
| `terraform output` | Prints output values | No |
| `terraform state list` | Lists tracked addresses | No |
| `terraform destroy` | Plans and applies removal of everything | **Yes** |

Applying a saved plan matters: it executes what was reviewed, not whatever the plan would be a minute later.

## When something goes wrong (beginner triage)

| Symptom | Likely meaning | First move |
| --- | --- | --- |
| `Error: Inconsistent dependency lock file` | Providers changed without a lock update | `terraform init` (or `-upgrade` deliberately) |
| `Error acquiring the state lock` | Another run is active, or one crashed | Wait; find the other run; do not force at once |
| `BucketAlreadyExists` or similar | Global name collision | Add a random suffix |
| Plan wants to replace something unexpected | A changed argument forces replacement | Find `# forces replacement`; reconsider the change |

## Common mistakes

- Committing `terraform.tfstate` or a `.tfvars` file holding secrets (add them to `.gitignore` before the first commit).
- Skipping `.terraform.lock.hcl`, which means provider versions can differ between machines.
- Running `apply` straight away without a saved plan and review.
- Editing resources in the console and then wondering why the next plan wants to change them back.
- Ignoring `-/+` because the example was harmless; the same symbol means data loss on a database.
- Learning on a shared or production account.

## Knowledge consolidation

- Infrastructure as code makes infrastructure changes reviewable, repeatable and recoverable.
- Declarative configuration states the desired end result; Terraform computes the steps and is idempotent.
- Terraform reasons about configuration, state and reality; most surprises are a disagreement between two of them.
- `plan` is the control point; read the summary line, then every `-` and `-/+`.
- State is sensitive data and must never be committed; teams keep it remotely with locking.
- Cost safety is designed in advance: sandbox account, budget alert, cheap resources, tags, a rehearsed destroy.

## Exercises

**Exercise 1 — Guided.** Run the local example. Change the content, read the plan, apply, then delete the file by hand and run `plan` again. Explain in a sentence why Terraform wants to recreate it.

**Exercise 2 — Read the plan.** Add a second `local_file` that uses `local_file.note.filename` in its content. Run `terraform graph` (or read the plan order) and explain which resource Terraform must create first, and how it knew.

**Exercise 3 — Drift.** Edit `note.txt` by hand and run `plan`. Decide in writing whether to revert (apply), adopt (change the code), or accept; give one reason for your choice.

**Exercise 4 (optional, needs a sandbox cloud account).** Create the budget alert first, then run the disposable bucket lifecycle, ending with `terraform destroy` and a manual check by tag. Record the real cost, even if it is zero.

**Solution notes.** Exercise 1: the file no longer exists, so reality disagrees with state; Terraform's plan restores the configured state. Exercise 2: the second resource references an attribute of the first, which creates a dependency edge; Terraform needs no explicit ordering. Exercise 3: any of the three is defensible if the reason is stated; reverting is usually the default, adopting is right if the hand edit was an improvement that belongs in code. Exercise 4: success is an empty `state list`, an empty tag-filtered inventory, and a recorded cost.
