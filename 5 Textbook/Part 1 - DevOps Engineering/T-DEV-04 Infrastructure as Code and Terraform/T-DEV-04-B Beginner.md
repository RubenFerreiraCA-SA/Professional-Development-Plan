# T-DEV-04-B — Beginner Foundations

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-b"></a>
#### T-DEV-04-B — Beginner Foundations

**Why code.** Clicking in a console creates resources nobody can reproduce, review or roll back. IaC makes infrastructure changes pull requests: diffable, reviewable, repeatable.

**Core concepts**

| Concept | Meaning |
| --- | --- |
| Provider | Plugin that talks to an API (a cloud, a Git host, a monitoring service). |
| Resource | An object Terraform creates, updates or destroys. |
| Data source | A read-only lookup of something that already exists. |
| State | Terraform's record of which real objects correspond to your configuration. |
| Plan | A proposed set of changes computed from configuration, state and reality. |
| Apply | Executing a reviewed plan. |
| Module | A reusable bundle of configuration with inputs and outputs. |

Desired configuration is code. **State is privileged data**: it can contain credential-like values even when the configuration does not.

**The workflow**

```bash
terraform fmt -check       # consistent formatting
terraform init             # download providers, configure backend
terraform validate         # syntax and internal consistency
terraform plan -out=tfplan # what would change?
terraform show tfplan      # read it carefully
terraform apply tfplan     # only after review
```

**A tiny configuration** (no cloud account needed — it uses a local provider):

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

**What to commit.** Commit `.tf` files and `.terraform.lock.hcl` (it pins provider versions). Never commit `*.tfstate`, `.terraform/` or variable files containing secrets.

**Declarative, not procedural.** A shell script says *how* to build something (run these commands in order). Terraform configuration says *what* should exist and works out the steps. Run it again with no changes and the plan is empty: that property is called *idempotence*, and it is what makes review and repeatability possible.

**Reading a plan, line by line.** Change `greeting` from `"hello"` to `"hi"` and run `terraform plan`:

```text
  # local_file.note must be replaced
-/+ resource "local_file" "note" {
      ~ content  = "hello" -> "hi" # forces replacement
      ~ id       = "aaf4c61..." -> (known after apply)
        # (1 unchanged attribute hidden)
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

`# forces replacement` is the line to find. For a `local_file`, replacement is trivial. For a database, changing a field that forces replacement would destroy data. The habit that prevents harm is to read the summary line first (`Plan: 1 to add, 0 to change, 1 to destroy`), then look at every `-` and `-/+`.

**State: what it is and what goes wrong without it.** State maps `local_file.note` in your configuration to the real object. If state is lost, Terraform believes nothing exists and proposes to create everything again, usually failing against what already exists. If state is edited carelessly, the mapping becomes wrong. Beginners usually keep state locally; teams keep it in a *remote backend* with locking so two people cannot apply at once. Because state can contain secrets, restrict access to it as strictly as to a credential store.

**Drift.** If someone changes a real resource outside Terraform, the actual world no longer matches state. `terraform plan` detects it by refreshing and shows the difference, offering to put things back. The practical rule: make changes through code, or accept that the next plan will propose reverting them.

```bash
echo "edited by hand" > note.txt     # change outside Terraform
terraform plan                       # shows the file will be updated to match configuration
```

**Variables, outputs and a first module.**

```hcl
variable "greeting" {
  type        = string
  description = "Text written to the note"
  default     = "hello"
}
output "path" { value = local_file.note.filename }
```

```bash
terraform plan -var 'greeting=hi'
TF_VAR_greeting=hi terraform plan
terraform output path
```

A *module* is a directory of `.tf` files called from another configuration with `module "notes" { source = "./modules/note" … }`. Use one when you repeat the same set of resources and want a single, tested definition.

**Command reference**

| Command | What it does | Changes anything real? |
| --- | --- | --- |
| `terraform fmt -check` | Verifies formatting | No |
| `terraform init` | Downloads providers, configures the backend | Only local files (`.terraform/`) |
| `terraform validate` | Checks syntax and consistency | No |
| `terraform plan -out=tfplan` | Computes and saves a plan | No |
| `terraform show tfplan` | Prints a saved plan | No |
| `terraform apply tfplan` | Executes exactly that plan | **Yes** |
| `terraform destroy` | Plans and applies removal of everything | **Yes** |

Applying a saved plan matters: it executes what was reviewed, not whatever the plan would be a minute later.

**Common mistakes**

- Committing `terraform.tfstate` or a `.tfvars` file holding secrets (add them to `.gitignore` before the first commit).
- Skipping `.terraform.lock.hcl`, which means provider versions can differ between machines.
- Running `apply` straight away without a saved plan and review.
- Editing resources in the console and then wondering why the next plan wants to change them back.
- Ignoring `-/+` because the example was harmless; the same symbol means data loss on a database.

**Exercise.** Run the example, change the content, read the plan, apply, then delete the file by hand and run `plan` again. Explain in a sentence why Terraform wants to recreate it.
