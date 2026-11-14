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
- Primary failure drill: <bad deploy rollback | task stop / unhealthy | AZ impairment note | restore-from-state>
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

Optional IaC refinements (pick what your ADR requires — not all at once):

| Refinement | Where | Verify |
| --- | --- | --- |
| Raise `desired_count` to 2 | staging `tfvars` / module variable | Two tasks; ALB still healthy |
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

Pick **one** primary drill for the Practical Assessment. Record: hypothesis → inject → observe → recover → evidence paths. Recovery steps must match ADR 0103.

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

### 3.3.2 Option A — bad deploy rollback (preferred if you have a prior task definition)

**ADR claim:** “A bad task definition is rolled back to the previous known-good revision without recreating the cluster.”

```bash
# Capture current (known-good) definition:
GOOD_TD="$(aws ecs describe-services --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)"
echo "GOOD_TD=$GOOD_TD" | tee "$HARBOUR_ROOT/docs/cloud/recovery/rollback-ids.txt"

# Inject: register a deliberately broken revision (wrong image tag or failing health command).
# Prefer doing this via Terraform variable change + apply, then revert the same way.
# CLI sketch (break-glass — log in console-exceptions if you use it):
# aws ecs register-task-definition ...  # broken
# aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --task-definition <broken>

observe "during-bad-deploy"

# Recover per ADR — roll forward to GOOD_TD (or terraform apply previous tfvars):
aws ecs update-service --profile "$AWS_PROFILE" --region "$AWS_REGION" \
  --cluster "$CLUSTER" --service "$SERVICE" \
  --task-definition "$GOOD_TD" \
  --force-new-deployment

# Wait until runningCount == desiredCount and health returns 200
for i in 1 2 3 4 5 6; do
  observe "rollback-wait-$i"
  sleep 20
done
```

If you use GitOps from D06, prefer **reverting the Git change** that produced the bad digest and showing sync/apply evidence — still attach the same observe log.

### 3.3.3 Option B — task stop / unhealthy target (scheduler recovery)

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

**Verify:** New task ARN ≠ stopped ARN; `/health` recovers; events show the replacement. If `desired_count=1`, this proves **self-healing**, not multi-instance HA — say so in the ADR.

### 3.3.4 Option C — AZ impairment (honest simulation)

True AZ failure is hard to inject safely. Acceptable training simulations:

- Scale so tasks only register in one subnet/AZ, then remove that subnet from the service temporarily **via Terraform**, observe ALB behaviour, restore.  
- Or document: “ALB spans AZs (`alb-azs.json`); with `desired_count=1` we do **not** claim AZ failure tolerance; drill deferred until count ≥ 2 and tasks spread.”

Do **not** claim Multi-AZ app HA without evidence of tasks (or data) surviving loss of one AZ.

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
# Plan only until you intend to tear down:
terraform -chdir="$TF_STAGING" plan -destroy \
  | tee "$HARBOUR_ROOT/docs/cloud/c03-destroy-plan-head.txt" | head -n 60
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

1. **ADR 0103** — compute, network, data, edge, observability, cost, **one** primary failure mode.  
2. **Verified** HA/backup/limit choices in `infra/` (or explicit “not claimed” with evidence files such as `ha-baseline.json`, `alb-azs.json`).  
3. **Recovery evidence** for the injected/simulated failure (`docs/cloud/recovery/`, observe log, before/after health).  
4. **Cost controls** updated (budget still valid; NAT/idle/teardown honesty).  
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
- Was recovery done the way the ADR said (not a different improvisation)?  
- Were Terraform paths `-chdir=…/infra/envs/staging`?  
- Is health evidence still on **http://** unless HTTPS was an explicit enhancement?  
- Would a second engineer find CLUSTER/SERVICE names and the recovery runbook without asking you?

### Example conclusion (evidence still required)

> ADR 0103: Fargate public-subnet training, ALB HTTP across two AZs, desired_count=2 claimed for task replacement HA (not full AZ proof). Stateless API; state bucket versioning noted. Primary drill: stop-task → ECS replace; observe.log shows health 000→200 in ~Ns. Plan/apply under `infra/envs/staging`. No console exceptions. Budget unchanged; teardown runbook linked. Demo health via demo-operator.

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
- [D05 Terraform](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · [D06 CD/GitOps](../4.1%20DevOps/D06%20Continuous%20Delivery%20and%20GitOps.md) · [C02](C02%20AWS%20Cloud%20Foundations.md) · [Cloud overview](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/CLOUD%20Overview.md)

**Previous chapter:** [Chapter 2 — AWS Cloud Foundations](C02%20AWS%20Cloud%20Foundations.md) · **Course detail:** [C03](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C03%20AWS%20Infrastructure%20and%20Architecture.md) · **Next:** [Platform Engineering](../../3%20Course%20Detail/3.4%20Platform%20Engineering/) (after Cloud milestone) · **Checklist:** [Final Project Checklist · C03](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
