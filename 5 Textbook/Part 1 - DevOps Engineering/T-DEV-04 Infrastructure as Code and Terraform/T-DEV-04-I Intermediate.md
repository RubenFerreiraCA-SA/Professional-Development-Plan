# T-DEV-04-I — Intermediate Practice

*Chapter: [T-DEV-04 — Infrastructure as Code and Terraform](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-04-i"></a>
#### T-DEV-04-I — Intermediate Practice

**Remote state with locking.** Local state on a laptop is not a platform. Use an access-controlled backend with locking so two people cannot apply at once. A common AWS pattern uses an object-storage bucket with versioning and encryption:

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

Bootstrapping chicken-and-egg: the state bucket itself is created by a small separate configuration (with local state or a manually created bucket), documented and rarely changed. Never destroy it while environments still use it.

**Prove locking works** before expensive resources exist: start an apply that sleeps (a `time_sleep` resource), then run a second `plan -lock-timeout=0s` and observe the lock error. Do not reach for `force-unlock` by reflex; first find the active run.

**Variables, outputs and environments.** Pass environment differences through variables and `*.tfvars` files; keep one root configuration per environment (`envs/staging`, `envs/prod`) with separate state keys and, usually, separate network ranges and name prefixes. Plan prod after changing only staging; its plan should be empty.

**Modules as interfaces.** A module is an API for other engineers: required inputs, validated defaults, outputs and version constraints, not a pile of resources.

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

**Testing modules.** Use `terraform test` with deliberately failing cases first, then passing ones:

```hcl
# tests/network.tftest.hcl
run "rejects_open_ingress" {
  command = plan
  variables { allowed_cidrs = ["0.0.0.0/0"], vpc_cidr = "10.50.0.0/16" }
  expect_failures = [var.allowed_cidrs]
}
```

**Staged first deployment.** Some resources depend on others that must exist first (a container service needs an image, an image needs a registry). Use explicit stages: (A) apply network and registry with the runtime disabled; (B) outside Terraform, push an image and resolve its digest; (C) enable the runtime with that digest. A feature flag variable such as `enable_runtime` makes stages visible.

**Drift.** Drift is when real infrastructure differs from state or code. Tag a resource by hand, run `plan`, and read what Terraform wants to do. Decide explicitly: revert (apply), adopt (import or update code), or accept temporarily with a ticket. Record the decision.

**When apply fails halfway.** Read the error and the resource address; inspect what actually exists; run a fresh `plan` before applying again; prefer fixing code over `terraform state rm`, unless you understand ownership. Keep a short recovery log: symptom, cause, action, prevention.

**Exercise.** Create two environment roots using one module, show that their states are isolated, introduce a manual tag as drift, and write down which decision you made and why.
