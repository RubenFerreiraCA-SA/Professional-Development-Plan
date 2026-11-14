# Chapter 3 — AWS Infrastructure and Architecture (C03)

*Cloud Engineering textbook · Chapter 3 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [C03 course detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) (about 64–80 hours). |
| **Prerequisites** | [C02](C02%20AWS%20Cloud%20Foundations.md); Terraform literacy from [D05](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) strongly recommended. Landing zone + staging runtime already usable. |

## How to study this chapter

C03 turns the C02 landing zone into an **architecture you can defend**: multi-AZ intent (or honest single-AZ limits), failure injection with recovery that matches an ADR, backup/restore assumptions stated in code, and cost/limit controls that survive a peer review. The checklist bar is: *a documented failure mode is injected or simulated; recovery matches the ADR without unrecorded console snowflakes.*

Work in order: **Concept → ADR draft → IaC change → Verify under load/failure → Reflect**. Prefer Terraform under `infra/envs/staging`. Extend D05 — do **not** invent a parallel unmanaged stack. Every console click that changes production-shaped resources must appear in a written exception list.

This text teaches [C03 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md).

> **Safety and cost boundary:** Training account only. Confirm the C02 budget alarm still fires before adding Multi-AZ data stores, NAT Gateways or extra ALBs. Prefer failure drills that **scale, stop or roll back** over creating expensive permanent capacity. Destroy or idle when done. Record every standing exception.

### Learning outcomes

1. Produce an architecture ADR covering compute, network, data, edge and observability hooks.  
2. Justify HA, backup and limit choices with **verified** behaviour (not aspirational diagrams).  
3. Inject or simulate one documented failure mode and recover per the ADR.  
4. Keep cost controls and teardown paths explicit.  
5. Prefer IaC changes; document any break-glass console use.

### Before you begin

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"
export AWS_PROFILE="${AWS_PROFILE:-harbour-training}"
export TF_STAGING="$HARBOUR_ROOT/infra/envs/staging"
cd "$HARBOUR_ROOT"
mkdir -p docs/cloud docs/decisions docs/runbooks docs/cloud/recovery

command -v aws >/dev/null && command -v terraform >/dev/null || {
  echo "Need AWS CLI v2 + Terraform (reuse D05 toolchain)"
  exit 1
}
aws sts get-caller-identity --profile "$AWS_PROFILE"
test -d "$TF_STAGING" || {
  echo "Complete D05 staging (or C02 minimal VPC path) before C03"
  exit 1
}

# Reuse C02 naming defaults; verify exact names (not substring grep):
export CLUSTER="${CLUSTER:-harbour-stg-cluster}"
export SERVICE="${SERVICE:-harbour-stg-api}"
FOUND_SERVICE="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].serviceName' --output text)"
test "$FOUND_SERVICE" = "$SERVICE" || {
  echo "Set CLUSTER/SERVICE from list-clusters / list-services (exact names)"
  exit 1
}

SERVICE_URL="$(terraform -chdir="$TF_STAGING" output -raw service_url 2>/dev/null || true)"
case "${SERVICE_URL:-}" in
  http://*|https://*) ;;
  *)
    echo "No valid service_url. Finish D05 Stage C (runtime) before architecture drills."
    exit 1
    ;;
esac
export HARBOUR_HEALTH_URL="${SERVICE_URL%/}/health"
echo "Baseline health URL: $HARBOUR_HEALTH_URL"
```

You need: C02 demo vs admin separation still intact, D05 staging applied through Stage C, and permission to change Terraform + run controlled failure drills.

---

## Section 3.1 — Architecture decision (training vs production)

### 3.1.1 What the ADR must cover

Write `docs/decisions/0103-harbour-aws-architecture.md` **before** large IaC edits. Minimum sections:

| Area | Questions the ADR answers |
| --- | --- |
| Compute | ECS Fargate vs EC2; desired count; placement (public subnet vs private+NAT) |
| Network | VPC CIDR, public/private intent, SG allow-lists, ALB listener scheme (HTTP training vs HTTPS enhancement) |
| Data | Stateless API vs DB; backup/restore story; what “RPO/RTO” means for *this* training stack |
| Edge | ALB AZs, health checks, target registration |
| Observability | Logs group, metrics to watch during failure, where recovery evidence lands |
| Cost / limits | NAT honesty, idle policy, quotas that would bite a second engineer |
| Failure mode | **Exactly one** primary drill for the Practical Assessment (plus optional extras) |

### 3.1.2 Topology trade-offs (record, do not cargo-cult)

D05’s training baseline is deliberate:

```text
[Client] --HTTP--> [ALB in ≥2 public subnets / AZs]
                      |
                      +--HTTP--> [Fargate tasks in public subnets, assign_public_ip=true]
                                 (locked-down task SG; no NAT Gateway)
```

| Choice | Training-friendly | Production-shaped | Cost / complexity |
| --- | --- | --- | --- |
| Tasks in public subnets + public IP | Matches D05; no NAT bill | Unusual; prefer private+NAT or VPC endpoints | NAT ≈ continuous spend |
| ALB across 2 AZs | Already in D05 network module | Required for serious HA | ALB hourly + LCU |
| `desired_count = 1` | Cheap; fine for labs | **Not** HA — one task death = outage until scheduler replaces | Extra tasks cost |
| RDS Multi-AZ | Optional enhancement | Common for durable data | Instance + storage + Multi-AZ premium |
| Single-AZ “it works on my laptop cloud” | Only if ADR **admits** the limit | Insufficient for prod SLOs | Cheap until the AZ blip |

**Reflect:** If your diagram shows “Multi-AZ HA” but `desired_count` is 1 and there is no data store, the diagram is aspirational. Fix the ADR or fix the infra.

### 3.1.3 Worked example — draft ADR skeleton

```markdown
# ADR 0103 — Harbour AWS architecture (training)

## Status
Proposed → Accepted (date)

## Context
C02 landing zone in account … region … Reuse D05 `infra/envs/staging`.

## Decision
- Compute: ECS Fargate, desired_count = N, public-subnet training placement (no NAT)
- Network: ALB HTTP listener (D05); HTTPS deferred / added as enhancement …
- Data: API is currently **stateless**; durable state is image digest + Terraform state (S3 versioned). DB Multi-AZ: out of scope / planned …
- Edge: ALB in public subnets across AZs …; target group health path `/health`
- Observability: CloudWatch Logs group …; alarm … (optional)
- Primary failure drill: <Option B task stop (standard) | Option A Terraform bad-deploy (advanced) | placement-config sim (not AZ outage) | restore-from-state>
- Cost: budget $…; no NAT; teardown runbook …

## Consequences
- HA claim limited to: …
- RPO/RTO for training: …
- Console changes require exception entry in docs/cloud/console-exceptions.md
```

**Practice — decide:** Fill every `…` with values you can prove from Terraform outputs or AWS describe calls this week.

---

## Section 3.2 — Implement through code (extend D05)

### 3.2.1 Ground rules

1. Change `infra/modules/*` and `infra/envs/staging` — not a one-off console resource that Terraform will fight.  
2. `terraform plan` before `apply`; keep the plan summary in evidence.  
3. After apply, re-read outputs with `-chdir`:

```bash
terraform -chdir="$TF_STAGING" plan -out=/tmp/harbour-c03.tfplan
terraform -chdir="$TF_STAGING" show -no-color /tmp/harbour-c03.tfplan \
  | tee "$HARBOUR_ROOT/docs/cloud/c03-plan-summary.txt" | tail -n 80
# apply only when the plan matches the ADR
# terraform -chdir="$TF_STAGING" apply /tmp/harbour-c03.tfplan
```

### 3.2.2 Worked example — make HA claims measurable

At minimum, document current facts:

```bash
aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].{desired:desiredCount,running:runningCount,taskDef:taskDefinition,subnets:networkConfiguration.awsvpcConfiguration.subnets}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/ha-baseline.json"

aws elbv2 describe-load-balancers --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --query 'LoadBalancers[?contains(LoadBalancerName, `harbour`)].{Name:LoadBalancerName,AZs:AvailabilityZones,DNS:DNSName}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/alb-azs.json"
```

**Wire `desired_count` through the staging root (D05 gap).** The runtime module already accepts `desired_count`, but D05’s staging root does not declare or pass it. Add this before claiming multi-task HA:

```hcl
# infra/envs/staging — add alongside existing variables:
variable "desired_count" {
  type    = number
  default = 1
}

module "runtime" {
  count = var.enable_runtime ? 1 : 0

  source          = "../../modules/runtime"
  name_prefix     = "${var.name_prefix}-stg"
  vpc_id          = module.network.vpc_id
  subnet_ids      = module.network.public_subnet_ids
  container_image = var.container_image
  allowed_cidrs   = var.allowed_cidrs
  desired_count   = var.desired_count   # ← add this line (module already supports it)
}
```

Then raise count and verify placement:

```bash
# Keep other vars in terraform.tfvars; override count for this apply:
terraform -chdir="$TF_STAGING" plan \
  -var="desired_count=2" \
  -out=/tmp/harbour-desired-2.tfplan
terraform -chdir="$TF_STAGING" show -no-color /tmp/harbour-desired-2.tfplan \
  | tee "$HARBOUR_ROOT/docs/cloud/desired-count-plan.txt" | tail -n 40
terraform -chdir="$TF_STAGING" apply /tmp/harbour-desired-2.tfplan

aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].{desired:desiredCount,running:runningCount}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/ha-after-desired-2.json"

# Actual AZ placement — one describe-tasks call → one JSON array (valid document):
TASK_ARNS="$(aws ecs list-tasks --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --service-name "$SERVICE" --desired-status RUNNING \
  --query 'taskArns' --output text)"
test -n "$TASK_ARNS" && test "$TASK_ARNS" != "None" || {
  echo "No running tasks to describe"
  exit 1
}
# shellcheck disable=SC2086  # intentional word-split of ARN list for --tasks
aws ecs describe-tasks --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --tasks $TASK_ARNS \
  --query 'tasks[].{task:taskArn,az:availabilityZone,subnet:attachments[0].details[?name==`subnetId`].value|[0]}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/task-az-placement.json"
```

Persist `desired_count = 2` in `terraform.tfvars` (or your usual var file) if the ADR keeps that claim; otherwise plan/apply back to `1` when idle.

Other optional IaC refinements (pick what your ADR requires — not all at once):

| Refinement | Where | Verify |
| --- | --- | --- |
| Tighten task SG ingress to ALB SG only | runtime module | C01/C02 SG dump still matches |
| Add HTTPS listener + cert | runtime module + ACM | Then (and only then) use `https://` health URL |
| Add CloudWatch alarm on unhealthy hosts | staging or module | Alarm enters ALARM during drill |
| Private subnets + NAT | network module | **Cost ADR update first** |

### 3.2.3 Worked example — least-privilege task role stays true

Any new AWS API the app needs belongs on the **task role**, not the demo human profile. After IaC changes:

```bash
TASK_DEF="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)"
TASK_ROLE_ARN="$(aws ecs describe-task-definition --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --task-definition "$TASK_DEF" \
  --query 'taskDefinition.taskRoleArn' --output text)"
echo "taskRole=${TASK_ROLE_ARN}" | tee "$HARBOUR_ROOT/docs/cloud/workload-roles-c03.txt"

aws iam simulate-principal-policy \
  --profile "$AWS_PROFILE" \
  --policy-source-arn "$TASK_ROLE_ARN" \
  --action-names ecr:GetAuthorizationToken logs:PutLogEvents iam:CreateUser \
  --output table | tee "$HARBOUR_ROOT/docs/cloud/iam-simulate-task-role-c03.txt"
```

### 3.2.4 Practice — no snowflake checklist

Before leaving §3.2, run:

```bash
# Anything created only in console for "just this lab"?
# If yes → either import to Terraform or list in docs/cloud/console-exceptions.md
test -f "$HARBOUR_ROOT/docs/cloud/console-exceptions.md" \
  || echo "# Console exceptions (C03)" > "$HARBOUR_ROOT/docs/cloud/console-exceptions.md"
```

---

## Section 3.3 — Failure and recovery (match the ADR)

Pick **one** primary drill for the Practical Assessment. **Option B (task stop)** is the standard executable assessment. **Option A (bad deploy via Terraform)** is the advanced design exercise when you want deploy-rollback evidence without CLI drift. Record: hypothesis → inject → observe → recover → evidence paths. Recovery steps must match ADR 0103.

### 3.3.1 Shared observation helpers

```bash
observe() {
  local label="$1"
  {
    echo "=== $label $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    curl -sS -o /tmp/harbour-body.txt -w "http_code=%{http_code} time=%{time_total}\n" \
      --connect-timeout 5 --max-time 15 "$HARBOUR_HEALTH_URL" || echo "curl_failed=$?"
    aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
      --cluster "$CLUSTER" --services "$SERVICE" \
      --query 'services[0].{desired:desiredCount,running:runningCount,events:events[0:3]}' \
      --output json
  } | tee -a "$HARBOUR_ROOT/docs/cloud/recovery/observe.log"
}
observe "baseline-before-inject"
```

### 3.3.2 Option A — bad deploy rollback via Terraform (advanced)

**Role:** Advanced design exercise — fully executable, but longer than Option B. Do **not** recover with bare `aws ecs update-service` while Terraform still owns the task definition; that creates drift.

**ADR claim:** “A bad `container_image` digest is applied through Terraform, observed as a failed deploy, then reverted by re-applying the previous digest — no unmanaged CLI task-definition edits.”

```bash
# 1) Record the known-good digest from the running task definition (must be image@sha256:…):
TASK_DEF="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)"
GOOD_IMAGE="$(aws ecs describe-task-definition --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --task-definition "$TASK_DEF" \
  --query 'taskDefinition.containerDefinitions[0].image' --output text)"
case "$GOOD_IMAGE" in
  *@sha256:*) ;;
  *)
    echo "Expected digest reference from D05 Stage C; got: $GOOD_IMAGE"
    exit 1
    ;;
esac
# Preserve the known-good digest for the whole drill (do not overwrite this file):
umask 077
printf '%s\n' "$GOOD_IMAGE" > "$HARBOUR_ROOT/docs/cloud/recovery/good-image.txt"
echo "GOOD_IMAGE=$GOOD_IMAGE" | tee "$HARBOUR_ROOT/docs/cloud/recovery/rollback-ids.txt"
cp -a "$HARBOUR_ROOT/docs/cloud/recovery/good-image.txt" \
  "$HARBOUR_ROOT/docs/cloud/recovery/good-image.txt.bak"

# 2) Syntactically valid but non-pullable digest (fails ECS pulls / never becomes healthy):
ECR_REPO="${GOOD_IMAGE%@*}"
BAD_IMAGE="${ECR_REPO}@sha256:0000000000000000000000000000000000000000000000000000000000000001"
echo "BAD_IMAGE=$BAD_IMAGE" | tee -a "$HARBOUR_ROOT/docs/cloud/recovery/rollback-ids.txt"

# 3) Inject — plan + apply through staging (keep enable_runtime / allowed_cidrs from tfvars):
terraform -chdir="$TF_STAGING" plan \
  -var="enable_runtime=true" \
  -var="container_image=${BAD_IMAGE}" \
  -out=/tmp/harbour-bad-deploy.tfplan
terraform -chdir="$TF_STAGING" show -no-color /tmp/harbour-bad-deploy.tfplan \
  | tee "$HARBOUR_ROOT/docs/cloud/recovery/bad-deploy-plan.txt" | tail -n 60
terraform -chdir="$TF_STAGING" apply /tmp/harbour-bad-deploy.tfplan

observe "during-bad-deploy"
# Expect: tasks failing to start or never healthy; /health degraded or failing.
# Wait long enough to capture events (do not leave BAD_IMAGE applied overnight).
for i in 1 2 3 4; do
  observe "bad-deploy-wait-$i"
  sleep 20
done

# 3b) Safeguard — inspect ECS deployment / circuit-breaker state before Terraform recovery.
# If the service already rolled back (circuit breaker) or a deployment is still IN_PROGRESS,
# record it; then still drive recovery via Terraform so desired state matches GOOD_IMAGE.
aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].{taskDef:taskDefinition,deployments:deployments[*].{status:status,rollout:rolloutState,reason:rolloutStateReason,running:runningCount,failed:failedTasks,td:taskDefinition}}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/recovery/deploy-state-before-revert.json"

# 4) Recover — re-read the preserved digest; revert with another recorded plan/apply:
GOOD_IMAGE="$(cat "$HARBOUR_ROOT/docs/cloud/recovery/good-image.txt")"
test -n "$GOOD_IMAGE" || {
  echo "Missing preserved good-image.txt — abort recovery"
  exit 1
}
terraform -chdir="$TF_STAGING" plan \
  -var="enable_runtime=true" \
  -var="container_image=${GOOD_IMAGE}" \
  -out=/tmp/harbour-good-revert.tfplan
terraform -chdir="$TF_STAGING" show -no-color /tmp/harbour-good-revert.tfplan \
  | tee "$HARBOUR_ROOT/docs/cloud/recovery/good-revert-plan.txt" | tail -n 60
terraform -chdir="$TF_STAGING" apply /tmp/harbour-good-revert.tfplan

# Also restore container_image in terraform.tfvars (or your var file) so the next plain
# plan does not re-introduce BAD_IMAGE.
for i in 1 2 3 4 5 6; do
  observe "rollback-wait-$i"
  sleep 20
done

# 5) Final service/deployment status — /health alone is not enough:
aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].{taskDef:taskDefinition,desired:desiredCount,running:runningCount,deployments:deployments[*].{status:status,rollout:rolloutState,reason:rolloutStateReason,running:runningCount,td:taskDefinition}}' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/recovery/deploy-state-after-revert.json"

FINAL_IMAGE="$(aws ecs describe-task-definition --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --task-definition "$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
    --cluster "$CLUSTER" --services "$SERVICE" \
    --query 'services[0].taskDefinition' --output text)" \
  --query 'taskDefinition.containerDefinitions[0].image' --output text)"
echo "FINAL_IMAGE=$FINAL_IMAGE" | tee -a "$HARBOUR_ROOT/docs/cloud/recovery/rollback-ids.txt"
test "$FINAL_IMAGE" = "$GOOD_IMAGE" || {
  echo "Service image still != preserved GOOD_IMAGE — recovery incomplete"
  exit 1
}

# Executable assertions: deploy finished, capacity matches (not only image + curl):
PRIMARY_ROLLOUT="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].deployments[?status==`PRIMARY`]|[0].rolloutState' --output text)"
DESIRED="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].desiredCount' --output text)"
RUNNING="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].runningCount' --output text)"
echo "PRIMARY_ROLLOUT=$PRIMARY_ROLLOUT desired=$DESIRED running=$RUNNING" \
  | tee -a "$HARBOUR_ROOT/docs/cloud/recovery/rollback-ids.txt"
test "$PRIMARY_ROLLOUT" = "COMPLETED" || {
  echo "PRIMARY rolloutState is '$PRIMARY_ROLLOUT' (want COMPLETED) — wait or investigate"
  exit 1
}
test "$RUNNING" = "$DESIRED" || {
  echo "runningCount ($RUNNING) != desiredCount ($DESIRED) — recovery incomplete"
  exit 1
}
```

**Verify:** Observe log shows unhealthy/failed during inject; after revert you have HTTP 200 **and** the script assertions pass (`FINAL_IMAGE` = `GOOD_IMAGE`, PRIMARY `rolloutState` = `COMPLETED`, `runningCount` = `desiredCount`). File `good-image.txt`, both plan files, and both deploy-state snapshots. `terraform -chdir="$TF_STAGING" plan` (with restored tfvars) is empty or unrelated. If you use GitOps from [D06](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md), the same story is “bad digest commit → revert commit” with sync evidence — still attach the observe log and final deployment status.

### 3.3.3 Option B — task stop / unhealthy target (standard assessment)

**Role:** Standard executable Practical Assessment drill. Proves **self-healing** (ECS replaces the task). With `desired_count=1` this is **not** multi-instance HA — say so in the ADR.

**ADR claim:** “Stopping the running task(s) results in ECS replacing them; ALB returns healthy within RTO ….”

```bash
TASK_ARN="$(aws ecs list-tasks --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --service-name "$SERVICE" --desired-status RUNNING \
  --query 'taskArns[0]' --output text)"
test -n "$TASK_ARN" && test "$TASK_ARN" != "None" || {
  echo "No running task to stop"
  exit 1
}
echo "Stopping $TASK_ARN" | tee "$HARBOUR_ROOT/docs/cloud/recovery/task-stop.txt"
aws ecs stop-task --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --task "$TASK_ARN" \
  --reason "C03 failure drill — expect ECS to replace"

observe "immediately-after-stop"
for i in 1 2 3 4 5 6; do
  observe "replace-wait-$i"
  sleep 15
done
```

**Verify:** New task ARN ≠ stopped ARN; `/health` recovers; events show the replacement.

### 3.3.4 Option C — placement-configuration failure (not a true AZ outage)

**Label clearly:** this is a **placement-configuration failure simulation**, not an Availability Zone outage. Removing a subnet from the ECS service network configuration is **not** equivalent to AWS impairing an AZ. Do **not** use this drill to claim “Multi-AZ resilience verified.”

**What it can teach:** how Harbour behaves when the service can no longer place tasks in a subnet you removed on purpose, and how you restore that configuration via Terraform.

**Procedure (only if ADR names this drill and `desired_count` ≥ 1):**

```bash
# Record current subnet list from the service (or from module.network outputs):
aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/recovery/subnets-before.json"

# Via Terraform only: temporarily pass a single public subnet_id into module.runtime
# (or a temporary staging override), plan, apply, observe placement/health impact,
# then restore the full subnet list with another plan/apply. File both plans.
# Do not edit the service network config with the AWS CLI while Terraform owns it.
```

**Expected limitations (write these into the ADR):**

- Proves configuration/placement sensitivity, **not** AZ failure tolerance.  
- ALB may still span two AZs in `alb-azs.json` while tasks cannot — that is not app HA.  
- True AZ resilience remains an **unverified claim** until you have an appropriate test (and usually `desired_count` ≥ 2 with verified cross-AZ placement from §3.2.2).

With `desired_count=1`, the honest ADR line is: “ALB spans AZs; we do **not** claim AZ failure tolerance for the app.”

### 3.3.5 Option D — restore assumptions (stateless + state bucket)

Harbour’s D05 API is typically **stateless**. A valid ADR says:

| Asset | Protection | Restore drill |
| --- | --- | --- |
| App compute | ECS desired count + image digest in tfvars | Re-apply staging / roll task definition |
| Terraform state | S3 versioning + DynamoDB lock (D05 bootstrap) | List object versions; restore prior state **only** with care in training |
| Application DB | None unless you added RDS | If none: write “N/A — no durable app data” |

```bash
# Prove state-bucket versioning (bootstrap outputs from D05):
# aws s3api get-bucket-versioning --bucket "$STATE_BUCKET"
# Record result in docs/cloud/recovery/state-versioning.txt
```

Optional advanced path: add a minimal durable dependency (e.g. RDS single-AZ or DynamoDB table for a feature flag), document backup, then run a restore drill. Cost must be approved in the ADR first.

### 3.3.6 Worked example — recovery runbook stub

`docs/runbooks/harbour-aws-recovery.md`:

```markdown
# Harbour AWS recovery (training)

## Symptoms
- /health not 200, or ECS runningCount < desired

## Detect
1. curl -v $HARBOUR_HEALTH_URL
2. ecs describe-services events
3. target group health

## Recover (per ADR 0103 primary drill)
1. …
2. …
3. observe until healthy

## Escalate / stop
- Do not open 0.0.0.0/0 SSH “to debug”
- Do not use root
- Console changes → console-exceptions.md
```

---

## Section 3.4 — Cost, quotas and teardown

### 3.4.1 Worked example — quotas that bite

```bash
aws service-quotas list-service-quotas \
  --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --service-code ecs \
  --query 'Quotas[?contains(QuotaName, `Fargate`) || contains(QuotaName, `Tasks`)].{Name:QuotaName,Value:Value}' \
  --output table 2>/dev/null \
  | tee "$HARBOUR_ROOT/docs/cloud/ecs-quotas.txt" || echo "Quotas API optional — note manual console check"

aws budgets describe-budget \
  --profile "$AWS_PROFILE" \
  --account-id "$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)" \
  --budget-name harbour-training 2>/dev/null \
  | tee "$HARBOUR_ROOT/docs/cloud/budget-c03.txt" \
  || echo "Record your real budget name/evidence from C02"
```

Update `docs/cloud/cost-guardrails.md` with: NAT decision, ALB idle cost, Fargate task count, what you will destroy after assessment.

### 3.4.2 Worked example — destroy path still exists

```bash
# Plan only until you intend to tear down — capture the full plan first (avoid
# piping through head, which can SIGPIPE terraform and truncate evidence):
terraform -chdir="$TF_STAGING" plan -destroy \
  > "$HARBOUR_ROOT/docs/cloud/c03-destroy-plan.txt"
head -n 60 "$HARBOUR_ROOT/docs/cloud/c03-destroy-plan.txt"
```

Confirm `docs/runbooks/aws-training-teardown.md` (from C02) still lists order: runtime → network → (never bootstrap while envs exist).

### 3.4.3 Practice — idle policy one-liner

Add to the ADR consequences: “If unused > N days: scale desired_count to 0 **or** destroy staging; keep budget alarm.”

---

## Section 3.5 — Observability hooks for architecture

Architecture without signals is hope. Minimum for C03:

| Signal | Source | Use in drill |
| --- | --- | --- |
| HTTP health | `curl` to `HARBOUR_HEALTH_URL` | Pass/fail recovery |
| ECS events | `describe-services` | Why tasks stopped/started |
| Target health | `elbv2 describe-target-health` | Unhealthy vs draining |
| Logs | CloudWatch log group from task def | App-level errors during bad deploy |

```bash
TG_ARN="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].loadBalancers[0].targetGroupArn' --output text)"
aws elbv2 describe-target-health --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --output json | tee "$HARBOUR_ROOT/docs/cloud/recovery/target-health.json"
```

Optional: one CloudWatch alarm on `UnHealthyHostCount` or ECS `RunningTaskCount` — create via Terraform if you want it permanent.

---

## Section 3.6 — Console exceptions and snowflake ban

`docs/cloud/console-exceptions.md` template:

```markdown
# Console exceptions (C03)

| Date | Resource | Why console | Follow-up |
| --- | --- | --- | --- |
| | | | Imported to Terraform / destroyed / accepted temporary until … |
```

**Rule:** Empty table is excellent. A filled table with follow-up dates is acceptable. Unlisted console drift fails the assessment.

---

## Section 3.7 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Plan wants to replace ALB | Name/ARN drift or manual change | `console-exceptions`; refresh state |
| Rollback leaves unhealthy targets | Bad image still draining / wrong TG | Target health + ECS events |
| “Multi-AZ” but one AZ empty | desired_count=1 or subnet list truncated | `ha-baseline.json` |
| Destroy blocked | `prevent_destroy` or bootstrap dependency | D05 teardown order |
| Surprise bill after HA test | Left desired_count high / NAT added | Budget + scale to 0 |
| Health URL `/health` only | Empty `SERVICE_URL` | Re-run preflight `case` validation |

---

## Practical Assessment — Chapter 3 — recover per ADR

Align with [C03 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) and Final Project Checklist C03.

### Required deliverables

1. **ADR 0103** — compute, network, data, edge, observability, cost, **one** primary failure mode (Option B is the standard assessment; Option A if you complete the full Terraform bad-deploy loop).  
2. **Verified** HA/backup/limit choices in `infra/` (or explicit “not claimed” with evidence files such as `ha-baseline.json`, `alb-azs.json`, and task AZ placement if `desired_count` ≥ 2).  
3. **Recovery evidence** for the injected/simulated failure (`docs/cloud/recovery/`, observe log, before/after health). Placement-config drills must not be labelled as AZ outages.  
4. **Cost controls** updated (budget still valid; NAT/idle/teardown honesty; full destroy plan file if captured).  
5. **`console-exceptions.md`** — complete list (may be empty).  
6. Recovery runbook stub matching the ADR.  
7. Confirmation demo path still works as **least-privilege** identity from C02 (no standing admin required to show health).

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| ADR | Diagram only | Trade-offs + honest limits + primary drill named | Training vs prod table with cost numbers |
| IaC | Console-first changes | Plan/apply evidence under `infra/envs/staging` | Module change + test or validation |
| Failure drill | Restarted until fixed | Inject → observe → recover matches ADR | Second drill or alarm-backed detection |
| HA/backup claims | Copied from blog | Claims match `desired_count` / data reality | Measured RTO in observe log |
| Cost / snowflakes | Ignored | Budget + teardown + exception log | Destroy plan captured; exceptions empty |

**Completion:** **Competent** on every row.

### Self-check

- Does the ADR admit single-task / no-DB limits if that is reality?  
- If you raised `desired_count`, is it wired through the **staging root** and verified with task AZ placement?  
- Was recovery done the way the ADR said (Terraform revert for Option A — no CLI drift)?  
- Did you avoid calling a subnet-removal drill a “true AZ outage”?  
- Were Terraform paths `-chdir=…/infra/envs/staging`?  
- Is health evidence still on **http://** unless HTTPS was an explicit enhancement?  
- Would a second engineer find CLUSTER/SERVICE names and the recovery runbook without asking you?

### Example conclusion (evidence still required)

> ADR 0103: Fargate public-subnet training, ALB HTTP across two AZs, desired_count=2 wired via staging `var.desired_count` (task-az-placement.json shows spread — still not a live AZ-impairment test). Stateless API; state bucket versioning noted. Primary drill: Option B stop-task → ECS replace; observe.log shows health recover in ~Ns. No console exceptions. Full destroy plan filed (not executed). Demo health via demo-operator.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| Claim HA | Read `desiredCount` + ALB AZs | Drawing Multi-AZ boxes for one task |
| Change architecture | ADR paragraph → Terraform plan | Console “temporary” SG rule |
| Prove recovery | `observe` before/during/after | Only a green `/health` at the end |
| Add NAT / RDS | Cost line in ADR + budget check | Silent apply overnight |
| Leave for the week | Scale to 0 or destroy staging | Hoping Fargate is free |

## Glossary

| Term | Meaning |
| --- | --- |
| ADR | Architecture Decision Record — why this shape, with consequences |
| RPO / RTO | How much data you may lose / how long restore may take |
| Snowflake | Resource or change that exists only in console, not in IaC |
| Self-healing | Scheduler replaces failed tasks — not the same as Multi-AZ HA |
| Blast radius | How much of Harbour fails when one AZ, role or deploy goes wrong |

## References

- [AWS Well-Architected — Reliability](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)  
- [ECS best practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/intro.html)  
- [D05 Terraform](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · [D06 GitOps Automation and Operations](../4.1%20DevOps/D06%20GitOps%20Automation%20and%20Operations.md) · [C02](C02%20AWS%20Cloud%20Foundations.md) · [Cloud syllabus](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C00%20Cloud%20Syllabus.md)

**Previous chapter:** [Chapter 2 — AWS Cloud Foundations](C02%20AWS%20Cloud%20Foundations.md) · **Course detail:** [C03](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) · **Next (optional):** [AI syllabus](../../3%20Course%20Detail/3.3%20AI%20Engineering/A00%20AI%20Syllabus.md) · **Next:** [Platform syllabus](../../3%20Course%20Detail/3.4%20Platform%20Engineering/P00%20Platform%20Syllabus.md) (after Cloud milestone) · **Checklist:** [Final Project Checklist · C03](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
