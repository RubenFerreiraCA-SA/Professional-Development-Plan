# Chapter 5 — Infrastructure as Code and Terraform (D05)

*DevOps Engineering textbook · Chapter 5 of 8*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see the [D05 course detail](../../3%20Course%20Detail/3.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) (about 42–60 hours). |
| **Prerequisites** | [D03](D03%20Docker%20and%20Containerization.md), [D04](D04%20CICD%20and%20Build%20Automation.md), basic networking and IAM, and an **isolated cloud sandbox** you are allowed to bill and destroy. |

## How to study this chapter

Terraform is not “cloud YAML.” It is how a platform team offers **reproducible infrastructure as a product**: protected state, reviewable plans, versioned modules and recovery you have practised before production pressure.

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Where state, locking, replacements or cost can go wrong, this chapter **shows a working sequence first**, then asks you to reproduce it, then adds a harder challenge.

Examples use **HashiCorp Terraform** and the **AWS** provider. The design principles transfer to other clouds; translate deliberately and record differences in an ADR. This text teaches [D05 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md). The [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) D05 bar is: *a second engineer provisions an isolated environment from the modules without undocumented manual steps; state locking is visible; the app endpoint is reachable under the intended network and IAM controls.*

> **Safety and cost boundary:** Use a dedicated training AWS account (or org OU) with budgets and alerts. Prefer regions you understand. **Destroy sandbox resources you create.** Never point training Terraform at production accounts. State and plan files can contain secrets — never commit them or upload them as public CI artifacts. The layouts below deliberately avoid NAT Gateways (expensive continuous cost) by placing training tasks in public subnets with locked-down security groups; that is a **training trade-off**, not a production pattern (document it in your ADR).

### Learning outcomes

1. Explain providers, dependency graph, plan/apply, refresh, drift and resource lifecycle (including replacements).
2. Protect remote state with locking, access control, encryption and a recovery decision.
3. Ship versioned modules with validated inputs, clear outputs and an upgrade story.
4. Run two isolated environments from the same modules without cross-talk.
5. Provision network, IAM and a container runtime path for Harbour with safe defaults.
6. Gate changes with plan-on-PR and apply-from-trusted-context.
7. Recover from drift, lock contention and partial apply without folklore.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
cd "$HARBOUR_ROOT"
terraform version   # Terraform >= 1.9 required for this chapter
aws sts get-caller-identity
grep -n 'terraform\|\.tfstate\|.terraform' .gitignore || echo "Confirm D01 ignore rules still cover Terraform artifacts"
```

Confirm `.gitignore` still excludes `.terraform/`, `*.tfstate`, `*.tfstate.*`, `*.tfplan` (from D01). Keep `.terraform.lock.hcl` **committed**.

Set a short tag you will use on every resource, for example `Project=harbour-training` and `Owner=<you>`.

---

## Section 5.1 — Terraform change semantics (before the cloud bill)

### 5.1.1 Core model

| Concept | Meaning |
| --- | --- |
| **Provider** | Plugin that talks to an API (AWS, GitHub, …) |
| **Resource** | Object Terraform creates/updates/destroys |
| **Data source** | Read-only lookup |
| **State** | Terraform’s record of what it believes exists |
| **Plan** | Proposed transition from state+config → desired |
| **Apply** | Execute an approved plan |
| **Module** | Reusable configuration interface (inputs/outputs) |

Desired configuration is code. **State** is privileged data. A plan computed yesterday can be wrong if state or the live world moved — always re-plan in the apply context when required.

### 5.1.2 Worked example — tiny root, fmt, validate, plan (no apply yet)

```bash
cd "$HARBOUR_ROOT"
mkdir -p infra/sandbox-hello
cd infra/sandbox-hello
```

`versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = "harbour-training"
      Module  = "sandbox-hello"
    }
  }
}
```

`variables.tf`:

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region for the training sandbox."
}

variable "name_prefix" {
  type        = string
  description = "Short prefix for resource names (lowercase alphanumeric and hyphen)."
  default     = "harbour"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,16}$", var.name_prefix))
    error_message = "name_prefix must be 2-16 chars of [a-z0-9-]."
  }
}
```

`main.tf` — start with something **cheap and deletable** (an SSM parameter as a canary object):

```hcl
resource "aws_ssm_parameter" "training_marker" {
  name  = "/${var.name_prefix}/training/marker"
  type  = "String"
  value = "harbour-d05-sandbox"

  tags = {
    Purpose = "terraform-semantics-drill"
  }
}

output "marker_name" {
  value = aws_ssm_parameter.training_marker.name
}
```

`terraform.tfvars` (do **not** commit account-specific secrets; tfvars with only region is fine to commit or keep local):

```hcl
aws_region  = "eu-west-1"
name_prefix = "harbour"
```

```bash
terraform fmt -check -recursive || terraform fmt -recursive
terraform init
terraform validate
terraform plan -out="${RUNNER_TEMP:-/tmp}/harbour-hello.tfplan"
terraform show -no-color "${RUNNER_TEMP:-/tmp}/harbour-hello.tfplan" | head -n 80
```

**Expected:** plan wants to create one `aws_ssm_parameter`. The plan file stays **outside git** (temp path).

Only when you intend to spend/create:

```bash
terraform apply "${RUNNER_TEMP:-/tmp}/harbour-hello.tfplan"
aws ssm get-parameter --name "/harbour/training/marker" --query 'Parameter.Value' --output text
```

**Practice — reproduce:** Change the parameter value, plan again, explain whether Terraform proposes update-in-place or replacement.

**Challenge:** Add a `lifecycle { prevent_destroy = true }` temporarily, try destroy, observe the block, remove it, and destroy for real when finished with this sandbox folder.

**Verify:** You can explain why `terraform show` on a saved plan is not proof the live account still matches that plan an hour later.

**Reflect:** Where should Harbour store the mapping from Git commit → plan → apply identity for audit?

When finished with the hello stack:

```bash
terraform destroy -auto-approve
```

---

## Section 5.2 — Remote state, locking and bootstrap

### 5.2.1 Concept

Local state on a laptop is not a platform. Use an access-controlled **remote backend** with **locking**:

| Piece (AWS pattern) | Role |
| --- | --- |
| S3 bucket | State objects (versioning + encryption on) |
| DynamoDB table | Lock lease |
| IAM | Who may read/write which state keys |

`sensitive` outputs still often land in state. Treat state access like production secret access.

### 5.2.2 Worked example — complete bootstrap root

Chicken-and-egg: the backend must exist before environment roots use it. Keep a **separate** bootstrap root that you apply rarely. Every file below is required.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"
cd "$HARBOUR_ROOT"
mkdir -p infra/bootstrap
cd infra/bootstrap
```

`versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = "harbour-training"
      Module  = "bootstrap"
    }
  }
}
```

`variables.tf`:

```hcl
variable "aws_region" {
  type        = string
  description = "AWS region for state backend resources."
}

variable "name_prefix" {
  type        = string
  description = "Short prefix for bucket/table names (lowercase alphanumeric and hyphen)."
  default     = "harbour"

  validation {
    condition     = can(regex("^[a-z0-9-]{2,16}$", var.name_prefix))
    error_message = "name_prefix must be 2-16 chars of [a-z0-9-]."
  }
}
```

`terraform.tfvars`:

```hcl
aws_region  = "eu-west-1"
name_prefix = "harbour"
```

`main.tf`:

```hcl
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "tf_state" {
  bucket = "${var.name_prefix}-tfstate-${data.aws_caller_identity.current.account_id}"

  tags = {
    Purpose = "terraform-state"
  }
}

resource "aws_s3_bucket_versioning" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tf_state" {
  bucket = aws_s3_bucket.tf_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tf_state" {
  bucket                  = aws_s3_bucket.tf_state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "tf_locks" {
  name         = "${var.name_prefix}-tf-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Purpose = "terraform-lock"
  }
}

output "state_bucket" {
  value = aws_s3_bucket.tf_state.bucket
}

output "lock_table" {
  value = aws_dynamodb_table.tf_locks.name
}

output "aws_region" {
  value = var.aws_region
}

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}
```

```bash
terraform init
terraform plan -out=/tmp/harbour-bootstrap.tfplan
terraform apply /tmp/harbour-bootstrap.tfplan

export STATE_BUCKET="$(terraform output -raw state_bucket)"
export LOCK_TABLE="$(terraform output -raw lock_table)"
export AWS_REGION="$(terraform output -raw aws_region)"
export AWS_ACCOUNT_ID="$(terraform output -raw aws_account_id)"
echo "STATE_BUCKET=$STATE_BUCKET"
echo "LOCK_TABLE=$LOCK_TABLE"
echo "AWS_REGION=$AWS_REGION"
echo "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID"
```

Record those four values in your Progress Log. **Do not destroy bootstrap** while environments still use it.

### 5.2.3 Worked example — lock-drill root (deterministic contention)

Do **not** race two ordinary `plan` commands — they often finish too quickly. Use a dedicated root whose apply holds the lock for a known duration.

```bash
mkdir -p "$HARBOUR_ROOT/infra/lock-drill"
cd "$HARBOUR_ROOT/infra/lock-drill"
```

`versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }
  }

  backend "s3" {
    # filled by -backend-config on init (same bucket/table as bootstrap)
    key      = "harbour/lock-drill/terraform.tfstate"
    encrypt  = true
  }
}

provider "aws" {
  region = var.aws_region
}
```

`variables.tf`:

```hcl
variable "aws_region" {
  type = string
}
```

`main.tf`:

```hcl
resource "time_sleep" "hold_lock" {
  create_duration = "90s"
}
```

`terraform.tfvars`:

```hcl
aws_region = "eu-west-1"
```

**Terminal A** (holds the lock for ~90 seconds):

```bash
cd "$HARBOUR_ROOT/infra/lock-drill"
terraform init \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="dynamodb_table=${LOCK_TABLE}" \
  -backend-config="region=${AWS_REGION}"
terraform apply -auto-approve
```

**Terminal B** (run within a few seconds of starting A):

```bash
cd "$HARBOUR_ROOT/infra/lock-drill"
terraform plan -lock-timeout=0s
```

**Expected:** Terminal B fails immediately with a state lock error (lock ID present). Do **not** `force-unlock` while A is still applying. After A finishes, B’s plan succeeds.

Destroy when done: `terraform destroy -auto-approve` in the lock-drill root.

**Practice — reproduce:** Capture the lock error text in your evidence notes.

**Challenge:** Write the recovery steps for a *stale* lock after a crashed CI runner (prove no apply is running, then unlock) — separate from “active apply in another terminal.”

**Verify:** Staging/prod will use the same bucket/table with **different state keys**; lock-drill proved locking works before you build expensive resources.

---

## Section 5.3 — Modules as platform APIs

### 5.3.1 Concept

A module is an **interface** for other engineers: required inputs, validated defaults, outputs, version constraints and upgrade notes — not a junk drawer of resources.

Harbour needs at least:

| Module | Responsibility |
| --- | --- |
| `modules/network` | VPC, subnets, routing for ALB + tasks |
| `modules/runtime` | Security groups, ALB, ECS cluster/service for Harbour API |

### 5.3.2 Worked example — network module with validation

```bash
mkdir -p "$HARBOUR_ROOT/infra/modules/network"
```

`infra/modules/network/variables.tf` — **include validation before writing tests**:

```hcl
variable "name_prefix" {
  type        = string
  description = "Lowercase name prefix for network resources."

  validation {
    condition     = can(regex("^[a-z0-9-]{2,24}$", var.name_prefix))
    error_message = "name_prefix must be 2-24 chars of [a-z0-9-] (uppercase rejected)."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.40.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "Use 2-3 AZs."
  }
}
```

`infra/modules/network/main.tf`:

```hcl
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${var.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
  tags   = { Name = "${var.name_prefix}-igw" }
}

resource "aws_subnet" "public" {
  for_each = {
    for idx in range(var.az_count) :
    idx => {
      az   = data.aws_availability_zones.available.names[idx]
      cidr = cidrsubnet(var.vpc_cidr, 4, idx)
    }
  }

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.value.az
  cidr_block              = each.value.cidr
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name_prefix}-public-${each.key}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }
  tags = { Name = "${var.name_prefix}-public-rt" }
}

resource "aws_route_table_association" "public" {
  for_each       = aws_subnet.public
  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}
```

`infra/modules/network/outputs.tf`:

```hcl
output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = [for s in aws_subnet.public : s.id]
}
```

### 5.3.3 Worked example — `terraform test` (fail first, then pass)

Write the test **before** you trust the validation. First demonstrate a broken module (no validation), then restore the validation block from 5.3.2.

`infra/modules/network/tests/name.tftest.hcl`:

```hcl
run "rejects_bad_prefix" {
  command = plan

  variables {
    name_prefix = "BAD"
    vpc_cidr    = "10.40.0.0/16"
  }

  expect_failures = [
    var.name_prefix,
  ]
}
```

**Step A — show the test failing for the right reason (optional teaching branch):** temporarily remove the `validation` block from `name_prefix`, run:

```bash
cd "$HARBOUR_ROOT/infra/modules/network"
terraform init
terraform test
```

**Expected without validation:** the run does **not** meet `expect_failures` (plan may proceed to provider errors or succeed incorrectly). That proves the test is asserting real validation.

**Step B — restore the validation block from 5.3.2**, then:

```bash
terraform test
```

**Expected:** `rejects_bad_prefix` passes because `BAD` is rejected by the variable validation.

**Practice — reproduce:** Extend the runtime module’s existing `allowed_cidrs` list variable so that any element equal to `0.0.0.0/0` is rejected (keep the “at least one CIDR” rule). Write a `terraform test` with `expect_failures` that sets `allowed_cidrs = ["0.0.0.0/0"]`. Show the test failing before the validation exists, then passing after you add it.

**Verify:** Another engineer can read module inputs and know invalid values fail before apply.

### 5.3.4 Worked example — runtime module (ALB + ECS Fargate)

```bash
mkdir -p "$HARBOUR_ROOT/infra/modules/runtime"
```

`infra/modules/runtime/variables.tf`:

```hcl
variable "name_prefix" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }

variable "container_image" {
  type        = string
  description = "Immutable image reference including digest."
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "allowed_cidrs" {
  type        = list(string)
  description = "CIDRs allowed to reach the ALB. Prefer your /32 for training."
  validation {
    condition     = length(var.allowed_cidrs) > 0
    error_message = "Provide at least one CIDR."
  }
  validation {
    condition     = alltrue([for c in var.allowed_cidrs : c != "0.0.0.0/0"])
    error_message = "allowed_cidrs must not include 0.0.0.0/0 in this training module."
  }
}
```

`infra/modules/runtime/main.tf`:

```hcl
data "aws_region" "current" {}

resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "tasks" {
  name_prefix = "${var.name_prefix}-tasks-"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "this" {
  name               = substr("${var.name_prefix}-alb", 0, 32)
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids
}

resource "aws_lb_target_group" "this" {
  name        = substr("${var.name_prefix}-tg", 0, 32)
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    matcher             = "200"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 15
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
}

resource "aws_iam_role" "execution" {
  name = "${var.name_prefix}-ecs-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${var.name_prefix}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.name_prefix}-api"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "harbour-api"
    image     = var.container_image
    essential = true
    portMappings = [{
      containerPort = var.container_port
      protocol      = "tcp"
    }]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.api.name
        awslogs-region        = data.aws_region.current.name
        awslogs-stream-prefix = "api"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:${var.container_port}/health')\" || exit 1"]
      interval    = 15
      timeout     = 5
      retries     = 3
      startPeriod = 20
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${var.name_prefix}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true # training: avoid NAT cost — document in ADR
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "harbour-api"
    container_port   = var.container_port
  }

  depends_on = [aws_lb_listener.http]
}
```

`infra/modules/runtime/outputs.tf`:

```hcl
output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "service_url" {
  value = "http://${aws_lb.this.dns_name}"
}

output "alb_security_group_id" {
  value = aws_security_group.alb.id
}
```

---

## Section 5.4 — Staged first deployment (registry → image → ECS)

### 5.4.1 Why staging is staged

ECS needs `container_image` at apply time. ECR must exist before you can push. **Do not** try to invent a digest before the registry exists. Use three explicit stages:

| Stage | What you apply | Result |
| --- | --- | --- |
| **A** | Network + ECR only (`enable_runtime = false`) | Registry URL |
| **B** | (no Terraform) Push image; resolve digest | `container_image` value |
| **C** | Enable runtime (`enable_runtime = true`) with that digest | Reachable `/health` |

### 5.4.2 Complete staging environment root

```bash
mkdir -p "$HARBOUR_ROOT/infra/envs/staging"
cd "$HARBOUR_ROOT/infra/envs/staging"
```

`versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    key     = "harbour/staging/terraform.tfstate"
    encrypt = true
    # bucket, region, dynamodb_table via -backend-config
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "harbour-training"
      Environment = "staging"
    }
  }
}
```

`variables.tf`:

```hcl
variable "aws_region" {
  type = string
}

variable "name_prefix" {
  type    = string
  default = "harbour"
}

variable "allowed_cidrs" {
  type        = list(string)
  description = "CIDRs allowed to reach the ALB (use your /32)."
}

variable "enable_runtime" {
  type        = bool
  description = "False for stage A (registry only). True for stage C (ECS/ALB)."
  default     = false
}

variable "container_image" {
  type        = string
  description = "ECR image@sha256 digest. Required when enable_runtime is true."
  default     = ""

  # Cross-variable validation requires Terraform >= 1.9 (matches required_version).
  validation {
    condition = (
      !var.enable_runtime || (
        var.container_image != "" && can(regex("@sha256:[0-9a-f]{64}$", var.container_image))
      )
    )
    error_message = "When enable_runtime is true, container_image must be a digest reference ending in @sha256:<64 hex>."
  }
}
```

`main.tf`:

```hcl
module "network" {
  source      = "../../modules/network"
  name_prefix = "${var.name_prefix}-stg"
  vpc_cidr    = "10.40.0.0/16"
}

resource "aws_ecr_repository" "harbour" {
  name                 = "${var.name_prefix}-stg-api"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true # training only
}

module "runtime" {
  count = var.enable_runtime ? 1 : 0

  source          = "../../modules/runtime"
  name_prefix     = "${var.name_prefix}-stg"
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.public_subnet_ids
  container_image = var.container_image
  allowed_cidrs   = var.allowed_cidrs
}

output "ecr_repository_url" {
  value = aws_ecr_repository.harbour.repository_url
}

output "alb_dns_name" {
  value = try(module.runtime[0].alb_dns_name, null)
}

output "service_url" {
  value = try(module.runtime[0].service_url, null)
}

output "alb_security_group_id" {
  value = try(module.runtime[0].alb_security_group_id, null)
}
```

`terraform.tfvars` for **stage A** (no runtime yet):

```hcl
aws_region      = "eu-west-1"
name_prefix     = "harbour"
allowed_cidrs   = ["203.0.113.10/32"] # REPLACE with your public IP /32
enable_runtime  = false
container_image = ""
```

### 5.4.3 Stage A — apply network + ECR

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
# Re-export if this is a new shell:
# source values recorded from bootstrap, or:
# export STATE_BUCKET=... LOCK_TABLE=... AWS_REGION=... AWS_ACCOUNT_ID=...

terraform init \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="dynamodb_table=${LOCK_TABLE}" \
  -backend-config="region=${AWS_REGION}"

terraform plan -out=/tmp/harbour-stg-a.tfplan
terraform apply /tmp/harbour-stg-a.tfplan

export ECR_REPO="$(terraform output -raw ecr_repository_url)"
echo "ECR_REPO=$ECR_REPO"
```

**Expected:** VPC/subnets/ECR exist; `alb_dns_name` is `null`; no ECS yet.

### 5.4.4 Stage B — obtain an image, publish to ECR, resolve digest

A clean clone does **not** include `harbour-api:local`. Obtain the image first (pick one path), then push.

**Option 1 — build from Chapter 3 (works offline once dependencies exist):**

```bash
cd "$HARBOUR_ROOT/app"
export HARBOUR_COMMIT="$(git rev-parse HEAD)"
docker build --build-arg HARBOUR_COMMIT="$HARBOUR_COMMIT" -t harbour-api:local .
export DIGEST_SRC="harbour-api:local"
```

**Option 2 — pull the digest you published in Chapter 4 (GHCR):**

```bash
# Replace owner/digest with your D04 release evidence
docker pull "ghcr.io/<owner-lowercase>/harbour-api@sha256:<digest-from-d04>"
export DIGEST_SRC="ghcr.io/<owner-lowercase>/harbour-api@sha256:<digest-from-d04>"
```

Then authenticate to **this account’s** ECR and push. Because the repository uses `image_tag_mutability = "IMMUTABLE"`, **do not reuse a tag that already exists** — choose a new tag per push (commit SHA is ideal):

```bash
export AWS_REGION="${AWS_REGION:-eu-west-1}"
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
export IMAGE_TAG="${HARBOUR_COMMIT:-$(git -C "$HARBOUR_ROOT" rev-parse HEAD)}"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker image inspect "$DIGEST_SRC" >/dev/null
docker tag "$DIGEST_SRC" "${ECR_REPO}:${IMAGE_TAG}"
docker push "${ECR_REPO}:${IMAGE_TAG}"

export CONTAINER_IMAGE="$(
  aws ecr describe-images \
    --repository-name "${ECR_REPO##*/}" \
    --image-ids imageTag="${IMAGE_TAG}" \
    --query 'imageDetails[0].imageDigest' \
    --output text \
    | awk -v repo="$ECR_REPO" '{print repo "@" $0}'
)"
echo "IMAGE_TAG=$IMAGE_TAG"
echo "CONTAINER_IMAGE=$CONTAINER_IMAGE"
```

**Immutable tags:** a second push of the same `${IMAGE_TAG}` will fail once that tag exists. For later exercises, use a new commit SHA tag, or `training-$(date +%Y%m%d%H%M%S)`, then update `container_image` to the new `@sha256:…` (the digest is what ECS pins; the tag is only a publish label).

**Expected:** `CONTAINER_IMAGE` looks like `…amazonaws.com/harbour-stg-api@sha256:` followed by 64 hex characters.

### 5.4.5 Stage C — enable runtime with that digest

Update `terraform.tfvars`:

```hcl
aws_region      = "eu-west-1"
name_prefix     = "harbour"
allowed_cidrs   = ["203.0.113.10/32"] # your /32
enable_runtime  = true
container_image = "REPLACE_WITH_CONTAINER_IMAGE_FROM_STAGE_B"
```

Or pass on the CLI without committing the digest if you prefer:

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
terraform plan \
  -var="enable_runtime=true" \
  -var="container_image=${CONTAINER_IMAGE}" \
  -out=/tmp/harbour-stg-c.tfplan
terraform apply /tmp/harbour-stg-c.tfplan
terraform output
curl -sS "http://$(terraform output -raw alb_dns_name)/health"
```

**Expected:** `/health` returns Harbour JSON once the task is healthy. If not: target health, security groups, image digest, CloudWatch logs — not “open `0.0.0.0/0`” as the first fix.

### 5.4.6 Prod isolation

Copy the staging root to `infra/envs/prod` with:

- backend key `harbour/prod/terraform.tfstate`
- different `vpc_cidr` (e.g. `10.50.0.0/16`)
- `name_prefix` / ECR name for prod

Plan prod after changing only staging and confirm prod’s plan is empty (or unrelated). Optionally apply prod later; destroy when idle.

**Practice — reproduce:** From a clean clone, run stages A→B→C using only `infra/README.md`.

**Challenge:** Add a `moved` block drill for a renamed resource without replacement.

**Verify:** Second engineer can provision staging; state keys remain isolated.

---

## Section 5.5 — Drift, failed apply and recovery

### 5.5.1 Worked example — benign drift

After stage C, tag the ALB security group out-of-band and inspect the plan. Prefer the module output when present:

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"

export SG_ID="$(terraform output -raw alb_security_group_id 2>/dev/null || true)"
if [[ -z "$SG_ID" || "$SG_ID" == "null" ]]; then
  export VPC_ID="$(aws ec2 describe-vpcs \
    --filters Name=tag:Name,Values=harbour-stg-vpc \
    --query 'Vpcs[0].VpcId' --output text)"
  echo "Staging VPC_ID=$VPC_ID"
  aws ec2 describe-security-groups \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --query 'SecurityGroups[].{Id:GroupId,Name:GroupName}' \
    --output table
  # Set SG_ID to the ALB security group id from the table (name starts with harbour-stg-alb-).
  export SG_ID="<alb-security-group-id>"
fi

echo "SG_ID=$SG_ID"
test -n "$SG_ID" && test "$SG_ID" != "None" && test "$SG_ID" != "null"

aws ec2 create-tags --resources "$SG_ID" --tags Key=DriftDrill,Value=yes
terraform plan
```

**Decide explicitly:** revert drift (apply Terraform), import/adopt, or accept temporary drift with a ticket. Record the decision.

### 5.5.2 Worked example — partial failure mindset

If apply fails mid-way:

1. Read the error and the resource address.
2. Inspect the live provider console/CLI for what actually exists.
3. Run a fresh `terraform plan` before blind re-apply.
4. Prefer fixing config over random `terraform state rm` unless you understand ownership.

Keep `docs/incidents/d05-recovery-log.md` with symptoms → cause → action → prevention.

### 5.5.3 Destroy discipline

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
terraform plan -destroy -out=/tmp/harbour-stg-destroy.tfplan
terraform show /tmp/harbour-stg-destroy.tfplan
terraform apply /tmp/harbour-stg-destroy.tfplan
```

Never destroy bootstrap while envs remain. Set budget alarms before leaving resources overnight.

**Practice:** Run the drift drill and attach plan snippets (redact account IDs if sharing).

**Verify:** You can explain blast radius of replacing the ALB versus replacing a task definition.

---

## Section 5.6 — Plan in CI, apply from trust

### 5.6.1 Concept (extends D04)

A pull request in your own repository can still contain **untrusted code**. Fork guards are necessary but not sufficient. Separate:

| Lane | What runs | Cloud access |
| --- | --- | --- |
| **Untrusted validation** | `fmt`, `validate`, module `terraform test` on every PR (including forks / same-repo feature branches) | **None** — no OIDC, no state read |
| **Trusted plan** | `terraform plan` against remote state | OIDC → **plan** role, only from a **named trusted workflow** on allowed refs |
| **Trusted apply** | Fresh plan + apply | OIDC → **apply** role, GitHub Environment protection |

Never paste long-lived AKIA keys into the repo. Never let PR-authored workflow files freely assume roles that can read state.

### 5.6.2 Worked example — IAM trust scoped to trusted workflows

Create two roles (plan / apply). **Do not** use `repo:OWNER/REPO:*` — that allows many refs and job identities to assume the role.

**Verified example A — ordinary trusted workflow (matches this chapter’s `harbour-terraform-plan.yml`)**

The plan job is a normal workflow job (not a `workflow_call` reusable workflow). Constrain IAM with the claims that job actually receives: typically `aud` and `sub` (branch and/or environment), plus GitHub Environment protection on the job.

Replace `AWS_ACCOUNT_ID`, `OWNER`, `REPO`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:OWNER/REPO:environment:staging-plan"
        }
      }
    }
  ]
}
```

Use `environment: staging-plan` on the plan job (as in §5.6.4) so `sub` carries the environment form. Alternatively trust `repo:OWNER/REPO:ref:refs/heads/main` if you only run plan on pushes to `main` without an environment. **Do not** add a `job_workflow_ref` condition to this ordinary-workflow example — GitHub defines that claim for jobs that use **reusable workflows**; requiring it here can cause `AssumeRoleWithWebIdentity` to fail when the claim is absent.

**Verified example B — reusable trusted workflow (optional hardening)**

If you refactor plan into a reusable workflow (`workflow_call`) and a thin caller on `main`, AWS can additionally constrain `token.actions.githubusercontent.com:job_workflow_ref` (see current AWS IAM docs for GitHub OIDC). Only after you:

1. Run a throwaway job that prints/decodes the OIDC token claims for **that** reusable-workflow architecture.
2. Confirm `job_workflow_ref` is present and note its exact value.
3. Add an IAM `StringEquals` condition on that claim (e.g. the reusable workflow ref you observed).

Until those three steps succeed, stay with example A.

**Alternative — GitHub subject-claim customisation**

GitHub org/repo settings can customise the OIDC `sub` format (for example to include workflow path). That changes what appears in `sub`; IAM must match **that** configured format via `token.actions.githubusercontent.com:sub`. This is a different mechanism from AWS’s `job_workflow_ref` condition key — configure one coherent pair (GitHub token shape ↔ IAM trust), and verify with a decoded token. Do not assume a custom `sub` string equals `job_workflow_ref`.

**Apply role trust:** narrower still — e.g. only `repo:OWNER/REPO:environment:staging` after required reviewers approve.

**Plan role** permissions (illustrative — review with IAM Access Analyzer):

- `s3:ListBucket`, `s3:GetObject` on the state bucket/prefix `harbour/staging/*`
- DynamoDB lock table items needed for plan
- Read-only describe/list for refresh
- **No** mutate/create/delete on compute/network; **no** deleting state objects

**Apply role:** plan permissions plus create/update/delete on training resources, scoped by prefix/tags where possible. Humans use a separate role; CI apply is not account admin.

Store ARNs as GitHub **Actions secrets** (`AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN`) — not in git.

**Operational split:** keep `harbour-terraform-validate.yml` (no `id-token`, no AWS) required on all PRs. Run `harbour-terraform-plan.yml` only after merge to `main`, or from a protected `staging-plan` environment that untrusted PR authors cannot satisfy. If you insist on PR plans for same-repo branches, treat state as sensitive data: use a disposable plan workspace, never the production state key, and accept that this is a weaker training compromise — document it in the ADR.

### 5.6.3 Worked example — untrusted validate (every PR, no AWS)

`.github/workflows/harbour-terraform-validate.yml` — **required check** for all PRs.

Do **not** add `paths:` filters on a required workflow (same lesson as D04 §4.3.4): a docs-only PR would skip the check and block merges. Always run; keep the job cheap (modules only, no AWS).

```yaml
name: harbour-terraform-validate

on:
  pull_request:
  push:
    branches: ["main"]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.8"
      - name: Fmt and validate modules (no backend / no credentials)
        working-directory: infra/modules/network
        run: |
          terraform init -backend=false -input=false
          terraform fmt -check -recursive
          terraform validate
          terraform test
```

No `id-token: write`. No state. Safe for forks and same-repo PRs — this job only exercises local module validation. If you later add path-aware optimisation, use D04’s always-running **gate** job as the required check name, not the skipped test job.

### 5.6.4 Worked example — trusted plan (after merge / protected environment)

Run cloud plan only from a **trusted** context that matches the IAM trust you configured in §5.6.2 example A (typically `aud` + `sub` for environment/branch on an ordinary workflow).

`.github/workflows/harbour-terraform-plan.yml`:

```yaml
name: harbour-terraform-plan

on:
  push:
    branches: ["main"]
    paths:
      - "infra/**"
      - ".github/workflows/harbour-terraform-plan.yml"
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  plan-staging:
    runs-on: ubuntu-latest
    environment: staging-plan
    defaults:
      run:
        working-directory: infra/envs/staging
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.8"
      - name: Configure AWS credentials (plan role)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_PLAN_ROLE_ARN }}
          aws-region: eu-west-1
      - name: Terraform init
        run: |
          terraform init -input=false \
            -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}" \
            -backend-config="dynamodb_table=${{ secrets.TF_LOCK_TABLE }}" \
            -backend-config="region=eu-west-1"
      - name: Plan
        run: |
          terraform plan -input=false -no-color -out="${{ runner.temp }}/stg.tfplan"
          terraform show -no-color "${{ runner.temp }}/stg.tfplan" > "${{ runner.temp }}/stg.plan.txt"
      - name: Write allowlisted plan summary from JSON (addresses/actions only)
        run: |
          # Full plan binary stays on the runner (${{ runner.temp }}/stg.tfplan).
          # Reviewers get ONLY resource addresses + change actions — not attribute values.
          terraform show -json "${{ runner.temp }}/stg.tfplan" > "${{ runner.temp }}/stg.plan.json"
          python3 - <<'PY'
          import json, os, pathlib
          plan = json.loads(pathlib.Path(os.environ["RUNNER_TEMP"] + "/stg.plan.json").read_text())
          lines = [
              "# Harbour staging plan summary",
              "",
              f"- commit: {os.environ.get('GITHUB_SHA', '')}",
              f"- run: {os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
              "",
              "| Action | Address |",
              "| --- | --- |",
          ]
          for rc in plan.get("resource_changes", []) or []:
              actions = rc.get("change", {}).get("actions") or []
              # Skip no-ops
              if actions == ["no-op"]:
                  continue
              addr = rc.get("address", "")
              action = ",".join(actions)
              # Allowlist: never include rc["change"]["before"|"after"] attribute objects
              lines.append(f"| `{action}` | `{addr}` |")
          summary = "\n".join(lines) + "\n"
          out = pathlib.Path(os.environ["RUNNER_TEMP"]) / "stg.summary.md"
          out.write_text(summary)
          print(summary)
          PY
        env:
          RUNNER_TEMP: ${{ runner.temp }}
          GITHUB_SHA: ${{ github.sha }}
          GITHUB_SERVER_URL: ${{ github.server_url }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_RUN_ID: ${{ github.run_id }}
      - uses: actions/upload-artifact@v4
        with:
          name: harbour-stg-plan-summary-${{ github.sha }}
          path: ${{ runner.temp }}/stg.summary.md
          retention-days: 5
```

**Full plan vs summary:**

| Artifact | Where it lives | Contents | Exposure |
| --- | --- | --- | --- |
| `stg.tfplan` / `stg.plan.json` | Trusted runner only (`runner.temp`) | Complete planned values | Sensitive — do not publish |
| `stg.summary.md` | Private artifact for **intended reviewers only** | Allowlisted **addresses + actions** (no attribute values) | **Lower exposure**, not automatically safe to publish — addresses can still name accounts, projects or environments |

Keep summary artifacts in a private repo, short retention, and audience-limited. Do not treat “no attribute values” as licence to post summaries publicly. Grepping human `terraform show` text is avoided because it can leak attributes; the JSON allowlist is the deliberate lower-exposure path, still inside a restricted trust boundary.

**Apply workflow** (trusted only): separate file, `environment: staging` with required reviewers, OIDC **apply** role whose trust matches that environment, **fresh** `plan` then `apply` in the same job (never reuse a stale plan artifact across time/state changes).

### 5.6.5 Threat drill — public SG change

Propose a change that sets `allowed_cidrs = ["0.0.0.0/0"]` (should already fail module validation if you completed the practice in 5.3.3). If validation were absent, show:

1. Plan summary calling out SG ingress widening.
2. Human review rejecting it, **or**
3. Policy-as-code failing — document gaps honestly.

**Practice — reproduce:** From the **summary artifact** alone, a second person describes blast radius without needing the full plan text.

**Verify:** Untrusted PRs get validate-only; ordinary-workflow plan/apply OIDC uses `aud`/`sub` (and environment protection) without requiring `job_workflow_ref` unless you verified a reusable-workflow token; summaries stay private to intended reviewers.

---

## Section 5.7 — Cost, teardown and documentation

### 5.7.1 Before you leave the sandbox running

- AWS Budgets / billing alarm for the training account
- Tags: `Project`, `Owner`, `Environment`
- Estimate: ALB hours + Fargate vCPU/GB + S3/DynamoDB (usually small) — **NAT would dominate**; you avoided it on purpose
- `infra/README.md`: bootstrap → lock-drill (optional) → staging stages A→B→C → curl health → destroy order

### 5.7.2 ADR

Write `docs/decisions/0005-harbour-infra.md` covering:

- Module boundaries (network vs runtime)
- State isolation (staging vs prod keys)
- Public-subnet tasks without NAT (training trade-off)
- Ingress CIDR policy
- Upgrade / replacement strategy
- Recovery (versioned state + lock table)

---

## Practical Assessment — Chapter 5 — infrastructure platform contract

Align with [D05 Course Detail](../../3%20Course%20Detail/3.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) and the Final Project Checklist D05 acceptance criterion.

### Required deliverables

1. **Two environments** (e.g. staging + prod) from versioned modules with explicit tfvars.
2. **Remote state** with locking; evidence from the **deterministic lock-drill** (`time_sleep` + `plan -lock-timeout=0s`); backup/recovery decision written down.
2b. **Staged staging deploy** (ECR → push/resolve digest → ECS) so `container_image` is never required before the registry exists.
3. **CI plan** on PR + **approved apply** from a trusted context with recorded identity/revision.
4. **Reachable Harbour endpoint** (or interim health-capable container) behind your network/IAM design.
5. **Drift or failed-apply recovery** notes with evidence.
6. **ADR** on modules, state, cost, risk and upgrades.
7. **Second-engineer test:** they provision or tear down one env using only repo docs.

### Evaluation rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| Change semantics | Can apply examples | Explains plan/replace/drift with evidence | Designs for safe replacements |
| State | Local state | Remote + lock + access story | Tested recovery from versioned state |
| Modules | Copied folders | Clear inputs/outputs/validation; two envs | Tests + versioning/upgrade notes |
| Security | Open SG for convenience | Least privilege, restricted ingress, documented trade-offs | Policy-as-code gates |
| Delivery | Manual only | Validate on PR; `aud`/`sub` (+ env) for ordinary plan/apply | Reusable-workflow `job_workflow_ref` only after token proof; restricted summaries |
| Operability | “It applied” | Second engineer succeeds from README | Cost alarms + destroy discipline |

**Completion standard:** **Competent** on every row. Success is not merely `terraform apply` exiting zero.

### Self-check

- Can a stranger create staging without your Slack help?
- Is state locked and not in git?
- Does prod plan stay clean when staging changes?
- Is the health endpoint reachable only as intended?
- Did you destroy what you no longer need?

### Example assessment conclusion (evidence still required)

> Bootstrap S3/DynamoDB backends host env state. Lock-drill proved contention. Staging used A→B→C (build/pull image, push unique immutable ECR tag, resolve digest, then ECS). `/health` serves Harbour behind an IP-restricted ALB. Every PR runs validate-only (no AWS); plan/apply use OIDC roles scoped to trusted workflow/ref/environment. Intended reviewers get a lower-exposure JSON address/action summary (still private); full plan files stay on the trusted runner. A second engineer completed staging from the README.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Understand a change | `plan` + `show`, check replacements | Blind `apply` |
| Share state | S3 + DynamoDB lock + IAM | Laptop `terraform.tfstate` in Dropbox |
| Isolate envs | Separate state keys + CIDR/name prefixes | One state for all worlds |
| Cut training cost | No NAT; tiny Fargate; destroy often | Always-on NAT + open ALB |
| CI | Validate on every PR (no AWS); plan via scoped OIDC | `repo:…:*` trust; PR code assuming plan role; “redaction = safe” |
| Drift | Fresh plan; decide revert/import/accept | Manual console forever |
| Lock error | Wait / find active apply | `force-unlock` by reflex |

## Glossary

| Term | Definition |
| --- | --- |
| State | Terraform’s mapping of config addresses to real IDs |
| Backend | Where state is stored |
| Lock | Mutual exclusion for state operations |
| Drift | Live resource differs from state/config |
| Replacement | Destroy+create instead of update-in-place |
| Module | Encapsulated Terraform configuration with an interface |
| Backend key | Object path separating env state files |
| OIDC apply | Short-lived cloud creds from CI identity |

## References

- [Terraform documentation](https://developer.hashicorp.com/terraform/docs)
- [Terraform state](https://developer.hashicorp.com/terraform/language/state)
- [Terraform modules](https://developer.hashicorp.com/terraform/language/modules)
- [Terraform testing](https://developer.hashicorp.com/terraform/language/tests)
- [AWS S3 backend](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [OWASP IaC Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Infrastructure_as_Code_Security_Cheat_Sheet.html)

**Previous chapter:** [Chapter 4 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md) · **Course detail:** [D05 — Infrastructure as Code and Terraform](../../3%20Course%20Detail/3.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · **Next chapter:** Chapter 6 — GitOps, Automation and Operations (not yet authored) · **Checklist:** [Final Project Checklist · D05](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
