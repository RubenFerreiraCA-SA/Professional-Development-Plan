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
terraform version   # Terraform >= 1.5 recommended
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
  required_version = ">= 1.5.0"
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

### 5.2.2 Worked example — bootstrap backend once

Chicken-and-egg: the backend must exist before environment roots use it. Keep a **separate** bootstrap root that you apply rarely.

```bash
cd "$HARBOUR_ROOT"
mkdir -p infra/bootstrap
cd infra/bootstrap
```

`versions.tf` / provider as in 5.1 (region variable). `main.tf`:

```hcl
resource "aws_s3_bucket" "tf_state" {
  bucket = "${var.name_prefix}-tfstate-${data.aws_caller_identity.current.account_id}"

  tags = {
    Purpose = "terraform-state"
  }
}

data "aws_caller_identity" "current" {}

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
```

```bash
terraform init
terraform plan -out=/tmp/harbour-bootstrap.tfplan
terraform apply /tmp/harbour-bootstrap.tfplan
terraform output
```

Record `state_bucket` and `lock_table` in your Progress Log. **Do not destroy bootstrap** while environments still use it.

### 5.2.3 Worked example — environment root with remote backend

```bash
mkdir -p "$HARBOUR_ROOT/infra/envs/staging"
cd "$HARBOUR_ROOT/infra/envs/staging"
```

`backend.tf` (fill bucket/table/region from bootstrap outputs):

```hcl
terraform {
  backend "s3" {
    bucket         = "REPLACE_STATE_BUCKET"
    key            = "harbour/staging/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "REPLACE_LOCK_TABLE"
    encrypt        = true
  }
}
```

Add provider `versions.tf` as before. Run:

```bash
terraform init
```

**Expected:** backend initialises; subsequent plans lock via DynamoDB.

### 5.2.4 Worked example — see locking (two terminals)

Terminal A:

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
# create a long-running apply later; for now start a plan that you pause with a deliberate hold:
terraform plan
# leave this shell open during apply of a real change when you have resources
```

Better drill once you have resources in Section 5.4:

1. Terminal A: `terraform apply` (or plan) that holds the lock.
2. Terminal B: `terraform plan` → expect a lock error naming the lock ID.
3. **Never** `force-unlock` while A is genuinely active. Only unlock stale locks after you prove no apply is running.

**Practice — reproduce:** Document the exact lock error text in your evidence notes.

**Challenge:** Enable bucket versioning recovery notes: how you would restore a previous state object after a bad apply *without* overwriting blindly (read AWS console/CLI object versions, compare, decide).

**Verify:** State for staging lives in S3 under the `harbour/staging/…` key; laptop has no long-term `terraform.tfstate` for that root (only local backend config).

---

## Section 5.3 — Modules as platform APIs

### 5.3.1 Concept

A module is an **interface** for other engineers: required inputs, validated defaults, outputs, version constraints and upgrade notes — not a junk drawer of resources.

Harbour needs at least:

| Module | Responsibility |
| --- | --- |
| `modules/network` | VPC, subnets, routing, basic flow for ALB + tasks |
| `modules/runtime` | Security groups, ALB, ECS cluster/service for Harbour API image |

### 5.3.2 Worked example — network module (training-sized)

```bash
mkdir -p "$HARBOUR_ROOT/infra/modules/network"
```

`infra/modules/network/variables.tf`:

```hcl
variable "name_prefix" {
  type = string
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

`infra/modules/network/main.tf` (abridged but complete enough to apply):

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

### 5.3.3 Worked example — runtime module (ALB + ECS Fargate public)

```bash
mkdir -p "$HARBOUR_ROOT/infra/modules/runtime"
```

`infra/modules/runtime/variables.tf`:

```hcl
variable "name_prefix" { type = string }

variable "vpc_id" { type = string }

variable "subnet_ids" {
  type = list(string)
}

variable "container_image" {
  type        = string
  description = "Immutable image reference including digest, e.g. ACCOUNT.dkr.ecr.REGION.amazonaws.com/repo@sha256:…"
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
  name               = "${var.name_prefix}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.subnet_ids
}

resource "aws_lb_target_group" "this" {
  name        = "${var.name_prefix}-tg"
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
    assign_public_ip = true # training: avoid NAT Gateway cost — document in ADR
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
```

**Image supply (working sequence):** create ECR in the env root (or a tiny module), push the D04 digest, pass the digest into `container_image`.

```hcl
# in envs/staging — beside the modules
resource "aws_ecr_repository" "harbour" {
  name                 = "${var.name_prefix}-stg-api"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true # training only
}

output "ecr_repository_url" {
  value = aws_ecr_repository.harbour.repository_url
}
```

```bash
# after terraform apply creates the repo:
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"
docker pull "ghcr.io/<owner>/harbour-api@sha256:<digest-from-d04>"   # or use local harbour-api:local
DIGEST_SRC="ghcr.io/<owner>/harbour-api@sha256:<digest-from-d04>"
ECR_REPO="$(terraform output -raw ecr_repository_url)"
docker tag "$DIGEST_SRC" "$ECR_REPO:training"
docker push "$ECR_REPO:training"
# resolve the pushed digest and set container_image = "$ECR_REPO@sha256:…"
```

If Harbour is not ready yet, temporarily set `container_image` to a public image that serves HTTP 200 on `/` and adjust the target-group health check path — then switch back to Harbour `@sha256:…` before assessment.

### 5.3.4 Worked example — `terraform test` for validation

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

Adjust to match your real validation blocks. Run from the module directory:

```bash
cd "$HARBOUR_ROOT/infra/modules/network"
terraform init
terraform test
```

**Practice — reproduce:** Add an input validation that rejects `0.0.0.0/0` for an `allowed_ingress_cidr` variable; prove `terraform test` or a plan failure catches it.

**Verify:** Another engineer can read module `README.md` files and know required inputs without asking you.

---

## Section 5.4 — Two environments, one module version

### 5.4.1 Layout

```text
infra/
  bootstrap/
  modules/
    network/
    runtime/
  envs/
    staging/
    prod/
  README.md
```

`infra/envs/staging/main.tf`:

```hcl
module "network" {
  source      = "../../modules/network"
  name_prefix = "${var.name_prefix}-stg"
  vpc_cidr    = "10.40.0.0/16"
}

module "runtime" {
  source          = "../../modules/runtime"
  name_prefix     = "${var.name_prefix}-stg"
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.public_subnet_ids
  container_image = var.container_image
  allowed_cidrs   = var.allowed_cidrs
}

output "alb_dns_name" {
  value = module.runtime.alb_dns_name
}

output "service_url" {
  value = module.runtime.service_url
}
```

Also define `variable "name_prefix"`, `variable "container_image"`, and `variable "allowed_cidrs"` in `variables.tf` for the env root. `prod` uses a **different state key** (`harbour/prod/terraform.tfstate`), different CIDR (e.g. `10.50.0.0/16`), and different `name_prefix` suffix. Same module source version.

### 5.4.2 Worked example — apply staging until the URL answers

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
terraform init
terraform plan -out=/tmp/harbour-stg.tfplan
terraform show -no-color /tmp/harbour-stg.tfplan | less
terraform apply /tmp/harbour-stg.tfplan
terraform output
curl -sS "http://$(terraform output -raw alb_dns_name)/health" || true
```

Use HTTPS listener only if you attach a certificate; for training, HTTP on an IP-restricted ALB is acceptable if documented.

**Expected:** `/health` returns Harbour’s JSON once the task is healthy. If not: check target health, security groups, image digest, CloudWatch logs — do not “fix with open `0.0.0.0/0`” as the first move.

### 5.4.3 Worked example — prove isolation

1. Apply staging.
2. Init/plan **prod** with different backend key (do not apply yet if cost-sensitive).
3. Change a staging-only tag; plan prod and show **no** unexpected staging resource addresses in the prod plan.
4. Optionally apply prod with `desired_count = 1` and tear it down when done.

**Practice — reproduce:** From a clean clone, provision staging using only `infra/README.md` (second-engineer test).

**Challenge:** Introduce a deliberate breaking module change (rename a resource without `moved`) in a branch; show a replacement plan and write the migration note you would require before merge.

**Verify:** Checklist acceptance — second engineer path works; locking still visible on concurrent plans.

---

## Section 5.5 — Drift, failed apply and recovery

### 5.5.1 Worked example — benign drift

```bash
# After staging exists — change a tag out-of-band:
PARAM_OR_SG_ID="..."   # pick a resource you understand
aws ec2 create-tags --resources "$SG_ID" --tags Key=DriftDrill,Value=yes
cd "$HARBOUR_ROOT/infra/envs/staging"
terraform plan
```

**Decide explicitly:** revert drift (apply Terraform), import/adopt, or accept temporary drift with a ticket. Record the decision.

### 5.5.2 Worked example — partial failure mindset

If apply fails mid-way:

1. Read the error and the resource address.
2. Inspect the live provider console/CLI for what actually exists.
3. `terraform refresh` / new plan (Terraform 1.x: just plan) before blind re-apply.
4. Prefer fixing config over random `terraform state rm` unless you understand ownership.

Keep `docs/incidents/d05-recovery-log.md` with symptoms → cause → action → prevention.

### 5.5.3 Destroy discipline

```bash
cd "$HARBOUR_ROOT/infra/envs/staging"
terraform plan -destroy -out=/tmp/harbour-stg-destroy.tfplan
terraform show /tmp/harbour-stg-destroy.tfplan
# only then:
terraform apply /tmp/harbour-stg-destroy.tfplan
```

Never destroy bootstrap while envs remain. Set budget alarms before leaving resources overnight.

**Practice:** Run the drift drill and attach plan snippets (redact account IDs if sharing).

**Verify:** You can explain blast radius of replacing the ALB versus replacing a task definition.

---

## Section 5.6 — Plan in CI, apply from trust

### 5.6.1 Concept (extends D04)

| Trigger | Terraform action | Credentials |
| --- | --- | --- |
| Pull request | `fmt`, `validate`, `test`, **plan** | Read-only / plan role |
| Protected main / environment approval | **apply** | Short-lived role (OIDC preferred) |

Never apply from fork PRs. Never paste long-lived AKIA keys into the repo.

### 5.6.2 Worked example — PR plan workflow (skeleton you can run)

`.github/workflows/harbour-terraform-plan.yml`:

```yaml
name: harbour-terraform-plan

on:
  pull_request:
    paths:
      - "infra/**"
      - ".github/workflows/harbour-terraform-plan.yml"

permissions:
  contents: read
  pull-requests: read
  id-token: write   # if using OIDC
  # For posting plan comments you may need pull-requests: write — prefer artifacts instead.

jobs:
  plan-staging:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra/envs/staging
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.9.8"
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_PLAN_ROLE_ARN }}
          aws-region: eu-west-1
      - run: terraform init -input=false
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - name: Plan
        run: |
          terraform plan -input=false -no-color -out="${{ runner.temp }}/stg.tfplan"
          terraform show -no-color "${{ runner.temp }}/stg.tfplan" > "${{ runner.temp }}/stg.plan.txt"
      - uses: actions/upload-artifact@v4
        with:
          name: harbour-stg-plan-${{ github.sha }}
          path: ${{ runner.temp }}/stg.plan.txt
```

Store plans under `${{ runner.temp }}` (same lesson as D04 JUnit): do not dirty the checkout; do not commit plans.

**Apply workflow** (trusted only): separate file, `environment: staging` with required reviewers, OIDC **apply** role narrower than human admin, `terraform apply -input=false "${{ runner.temp }}/…"` only after a **fresh** plan in that job when state may have changed.

### 5.6.3 Threat drill — public SG in a PR

Open a PR that changes `allowed_cidrs` to `["0.0.0.0/0"]`. Show:

1. Plan output calling out SG ingress change.
2. Human review rejecting it, **or**
3. A policy check (OPA/Conftest/Checkov) failing — if you lack automation, document the gap honestly.

**Practice — reproduce:** Post the plan artifact link on a PR and have a second person summarise blast radius from that artifact alone.

**Verify:** Untrusted PRs cannot apply; staging apply is auditable (who/what/when).

---

## Section 5.7 — Cost, teardown and documentation

### 5.7.1 Before you leave the sandbox running

- AWS Budgets / billing alarm for the training account
- Tags: `Project`, `Owner`, `Environment`
- Estimate: ALB hours + Fargate vCPU/GB + S3/DynamoDB (usually small) — **NAT would dominate**; you avoided it on purpose
- `infra/README.md`: bootstrap → staging apply → how to curl health → destroy order

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
2. **Remote state** with locking; evidence of a lock conflict; backup/recovery decision written down.
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
| Delivery | Manual only | Plan-in-CI, trusted apply | OIDC, environments, no stale plans |
| Operability | “It applied” | Second engineer succeeds from README | Cost alarms + destroy discipline |

**Completion standard:** **Competent** on every row. Success is not merely `terraform apply` exiting zero.

### Self-check

- Can a stranger create staging without your Slack help?
- Is state locked and not in git?
- Does prod plan stay clean when staging changes?
- Is the health endpoint reachable only as intended?
- Did you destroy what you no longer need?

### Example assessment conclusion (evidence still required)

> Bootstrap S3/DynamoDB backends host `harbour/staging` and `harbour/prod` state. Network and runtime modules deploy an IP-restricted ALB + Fargate service on public subnets (no NAT; ADR explains why). Staging `/health` serves Harbour from an ECR digest. PR plans upload artifacts from `runner.temp`; apply uses a reviewed GitHub Environment. A second engineer applied staging from the README. Drift drill and lock contention are logged.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Understand a change | `plan` + `show`, check replacements | Blind `apply` |
| Share state | S3 + DynamoDB lock + IAM | Laptop `terraform.tfstate` in Dropbox |
| Isolate envs | Separate state keys + CIDR/name prefixes | One state for all worlds |
| Cut training cost | No NAT; tiny Fargate; destroy often | Always-on NAT + open ALB |
| CI | Plan on PR to temp artifact | Committing plans; apply on fork PRs |
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
