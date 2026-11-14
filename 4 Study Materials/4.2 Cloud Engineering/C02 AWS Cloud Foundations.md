# Chapter 2 — AWS Cloud Foundations (C02)

*Cloud Engineering textbook · Chapter 2 of 3*

| | Details |
| --- | --- |
| **Estimated study time** | Work at your own pace; see [C02 course detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C02%20AWS%20Cloud%20Foundations.md) (about 32–40 hours). |
| **Prerequisites** | [C01](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md); an **isolated training AWS account** you may bill and destroy; [D05](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) helpful if Harbour already has `infra/`. |

## How to study this chapter

C02 builds a **landing-zone foundation**: who you are in the account, how Harbour is reached on the network edge, which AWS services hold which pieces, and how cost is contained. The checklist bar is not “I clicked around the console” — it is *Harbour runs in the documented landing zone under least-privilege identities; the demo path does not rely on standing admin credentials.*

Work in order: **Concept → Worked example → Practice → Verify → Reflect**. Prefer the AWS CLI and short-lived credentials. If you already completed D05, **reuse and document** that stack — do not invent a second unmanaged parallel universe.

This text teaches [C02 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C02%20AWS%20Cloud%20Foundations.md).

> **Safety and cost boundary:** Training account (or org OU) only. Enable a **budget alarm before** creating networks or compute. Never put long-lived access keys in Git. Never use the root user for daily labs. Destroy or stop training resources when idle. Record every standing exception.

### Learning outcomes

1. Separate root, human IAM, and workload roles; enforce MFA expectations.  
2. Sketch and justify a minimal VPC edge for Harbour (public/private intent, SG allow-lists).  
3. Map Harbour API, data, DNS and logs onto foundational AWS services (link D05 where present).  
4. Prove budgets, tags and an idle/destroy policy.  
5. Operate the demo path with a **least-privilege** identity — not `AdministratorAccess` as the happy path.

### Before you begin

Install tooling and prepare docs **before** any profile-specific STS check. Profiles are created in §2.2; identity validation happens immediately after that.

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"
# AWS_PROFILE is set after §2.2 configures harbour-training / harbour-demo
cd "$HARBOUR_ROOT"
mkdir -p docs/cloud docs/runbooks docs/decisions

command -v aws >/dev/null || {
  echo "Install AWS CLI v2 first: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
  exit 1
}
aws --version

command -v terraform >/dev/null || echo "terraform optional until you reuse D05 outputs (§2.4)"
test -d "$HARBOUR_ROOT" || echo "Set HARBOUR_ROOT to your Harbour repo"
```

You need: a **training** AWS account (or OU) you may bill, console access to create IAM users/roles and a budget, and MFA ability on human users. Do **not** run labs as the root user.

---

## Section 2.1 — Account model and shared responsibility (AWS)

### 2.1.1 Root is break-glass, not a daily driver

| Identity | Use |
| --- | --- |
| Root | Account recovery, rare break-glass — MFA on, no access keys |
| Human IAM user or SSO role | Day-to-day lab work with MFA |
| Workload role | ECS task / EC2 instance / CI OIDC — no human long-lived keys |

**Reflect:** If your only way to “make Harbour work” is an admin access key on disk, the landing zone is not done.

### 2.1.2 Shared responsibility (refine C01)

| You own | AWS owns (examples) |
| --- | --- |
| IAM policies you attach, SG rules, data in buckets/DB | Hypervisor, data-centre physical security |
| Guest OS if you run EC2 | Managed service control plane (RDS/ECS control plane) |
| Application secrets handling | Compliance of the underlying cloud facilities |

---

## Section 2.2 — IAM hygiene and a least-privilege demo path

### 2.2.1 Worked example — training admin vs demo operator

Create (console or CLI) two human-usable principals in the **training** account:

| Principal | Purpose | Policy intent |
| --- | --- | --- |
| `harbour-training-admin` | Bootstrap / break-glass lab admin | Broad within **this account only**; MFA required |
| `harbour-demo-operator` | Checklist “demo path” identity | Read + invoke only what Harbour needs to **show** (describe, get logs, hit health via public URL) — **not** `iam:*`, **not** unrestricted `ec2:*` |

Exact managed-policy ARNs change; prefer **customer-managed** policies you can read. Example starting point for the demo operator (tighten to your real resource ARNs after D05 exists):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadHarbourContext",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ecs:Describe*",
        "ecs:List*",
        "elasticloadbalancing:Describe*",
        "logs:Describe*",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics",
        "tag:GetResources"
      ],
      "Resource": "*"
    }
  ]
}
```

This is **read-mostly**. It must **not** include `AdministratorAccess`. If your demo needs one mutating action (e.g. scale a service), add that single action with a resource ARN — do not widen to `*`.

### 2.2.2 Worked example — configure CLI profiles, then validate STS

```bash
# Prefer aws configure sso if your org supports it.
# Otherwise: create access keys ONLY for harbour-training-admin / demo-operator,
# store in the shared credentials file — never in the Harbour repo.
aws configure --profile harbour-training
aws configure --profile harbour-demo

# Mandatory identity checks — run these immediately after configure:
aws sts get-caller-identity --profile harbour-training | tee docs/cloud/sts-training.json
aws sts get-caller-identity --profile harbour-demo | tee docs/cloud/sts-demo.json
```

Confirm the ARNs match the principals you created (training-admin vs demo-operator). If either call fails, fix credentials **before** budgets/VPC work.

```bash
export AWS_PROFILE=harbour-training   # default for bootstrap sections below
```

Add to `.gitignore` if not already present: any local override files; never commit `~/.aws`. Document in `docs/cloud/iam-baseline.md` which profile is admin vs demo.

### 2.2.3 Worked example — MFA expectation

```bash
# Console: enable MFA on both human users. CLI check (IAM) as training-admin:
aws iam list-mfa-devices --user-name harbour-demo-operator --profile harbour-training
# Expect at least one device when MFA is configured.
```

If MFA listing is denied, verify MFA in the console as admin and record “MFA verified visually / by admin” — still do not skip MFA.

### 2.2.4 Practice — prove the happy path is not admin (non-mutating)

Do **not** use `aws iam create-user` as the deny test. If the demo profile were accidentally overprivileged, that command could **create a real user**.

**Positive evidence** (demo may do these):

```bash
export AWS_PROFILE=harbour-demo
aws sts get-caller-identity
aws ec2 describe-vpcs --region "$AWS_REGION" --max-items 1 2>&1 | head -n 20
```

**Negative evidence** — prefer IAM policy simulation as **training-admin** evaluating the demo principal (no side effects):

```bash
export AWS_PROFILE=harbour-training
DEMO_ARN="$(aws sts get-caller-identity --profile harbour-demo --query Arn --output text)"
# If DEMO_ARN is an assumed-role ARN, use the role ARN as PolicySourceArn instead.
aws iam simulate-principal-policy \
  --policy-source-arn "$DEMO_ARN" \
  --action-names iam:CreateUser iam:CreateAccessKey ec2:DescribeVpcs \
  --output table | tee docs/cloud/iam-simulate-demo.txt
```

Expect `iam:CreateUser` / `iam:CreateAccessKey` → **implicitDeny** or **explicitDeny**, and `ec2:DescribeVpcs` → **allowed** (if your demo policy includes describe).

**Alternative negative check** (still non-mutating): as `harbour-demo`, run `aws iam list-users` and expect **AccessDenied** — never create/delete.

**Verify:** `docs/cloud/iam-baseline.md` records STS ARNs, simulation (or AccessDenied) output, and states explicitly: *demo path uses `harbour-demo`; standing admin is not required for health checks and describe operations.*

---

## Section 2.3 — Cost guardrails first (before VPC toys)

### 2.3.1 Worked example — budget + alert

Create a monthly budget (console **Billing → Budgets**, or CLI if enabled) with an alert at a low training threshold (e.g. $10 or $20). Email must be an address you monitor.

Minimum evidence if CLI Budgets is awkward: screenshot or export of budget + alert subscriber in `docs/cloud/cost-guardrails.md`.

`docs/cloud/cost-guardrails.md` must include:

| Item | Your value |
| --- | --- |
| Monthly budget | |
| Alert threshold % | |
| Notify email | |
| Idle policy | Stop/destroy within N hours of finishing a lab |
| Forbidden-by-default | NAT Gateway “always on”, public RDS, unused ALBs |

### 2.3.2 Tagging convention

Require tags on training resources:

```text
project=harbour
env=training
owner=<your-handle>
```

```bash
# Example once a VPC exists:
aws ec2 describe-vpcs --profile harbour-training --region "$AWS_REGION" \
  --query 'Vpcs[].{Id:VpcId,Tags:Tags}' --output table
```

**Verify:** Budget evidence exists **before** you create a second subnet “just to try.”

---

## Section 2.4 — VPC edge for Harbour

### 2.4.1 Concept — enough network to reason

```text
Internet
  → IGW
  → Public subnet (ALB / bastion / training tasks — justify)
  → Private subnet (preferred for data plane — may need NAT for egress)
  → Security groups (stateful allow-lists)
```

**Training trade-off (D05):** tasks in public subnets **without NAT** reduce cost; that is not a production default. Document which pattern you use.

### 2.4.2 Worked example — sketch then implement (or import from D05)

D05’s staging root is **`infra/envs/staging`**, not `infra/`. Use `-chdir` (or `cd` there) so outputs resolve.

If D05 staging is applied:

```bash
export AWS_PROFILE=harbour-training
export TF_STAGING="$HARBOUR_ROOT/infra/envs/staging"
test -d "$TF_STAGING" || echo "No D05 staging env yet — use minimal VPC path below"

# Capture outputs with absolute evidence path:
terraform -chdir="$TF_STAGING" output | tee "$HARBOUR_ROOT/docs/cloud/vpc-outputs.txt"

# D05 runtime module exposes (names may be nested under module outputs — adjust):
#   service_url              → http://<alb-dns>   (HTTP listener — see §2.4.4)
#   alb_dns_name
#   alb_security_group_id
ALB_SG="$(terraform -chdir="$TF_STAGING" output -raw alb_security_group_id 2>/dev/null || true)"
SERVICE_URL="$(terraform -chdir="$TF_STAGING" output -raw service_url 2>/dev/null || true)"
ALB_DNS="$(terraform -chdir="$TF_STAGING" output -raw alb_dns_name 2>/dev/null || true)"

# Tasks SG may not be a root output in D05 — discover from the running service ENI/SG:
# (Set CLUSTER/SERVICE to your names, e.g. harbour-stg-cluster / harbour-stg-api)
APP_SG="$(aws ecs describe-services --profile harbour-training --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups[0]' \
  --output text 2>/dev/null || true)"

echo "ALB_SG=${ALB_SG}" | tee "$HARBOUR_ROOT/docs/cloud/sg-ids.txt"
echo "APP_SG=${APP_SG}" | tee -a "$HARBOUR_ROOT/docs/cloud/sg-ids.txt"
echo "SERVICE_URL=${SERVICE_URL}" | tee -a "$HARBOUR_ROOT/docs/cloud/sg-ids.txt"
```

If `alb_security_group_id` is nested (e.g. only on a module), run `terraform -chdir="$TF_STAGING" output` and copy the value into `ALB_SG` manually — still record the source. Prefer adding a root output later rather than guessing IDs.

Copy VPC ID, subnet IDs, SG IDs into `docs/cloud/network-baseline.md` with a diagram matching the **actual** listener scheme:

```text
[Client] --HTTP--> [ALB SG] --HTTP--> [Task SG]     # D05 training baseline
# Later (enhancement): [Client] --HTTPS--> [ALB TLS listener] --HTTP--> [Task SG]
```

If you have **no** VPC yet, create a **minimal** one (console or a small Terraform root under `infra/envs/staging`) with:

- One VPC CIDR (e.g. `10.50.0.0/16`)  
- Two public subnets in different AZs (ALB requirement)  
- One SG for an HTTP entry and one for app tasks allowing only from the entry SG  
- **No** NAT Gateway unless you accept the cost in writing  

Do not open `0.0.0.0/0` to SSH on the app SG.

### 2.4.3 Worked example — security groups as allow-lists

```bash
export AWS_PROFILE=harbour-training
test -n "$ALB_SG" && test -n "$APP_SG" || {
  echo "Set ALB_SG and APP_SG from §2.4.2 before describing"
  exit 1
}
aws ec2 describe-security-groups \
  --profile harbour-training \
  --region "$AWS_REGION" \
  --group-ids "$ALB_SG" "$APP_SG" \
  --query 'SecurityGroups[].{Name:GroupName,Id:GroupId,Ingress:IpPermissions}' \
  --output json > "$HARBOUR_ROOT/docs/cloud/sg-ingress.json"
```

**Practice — reproduce:** Using C01 hop language, write which SG corresponds to the “TCP port hop” for the client and for the task.

### 2.4.4 Worked example — C01 diagnostics against an AWS endpoint (HTTP first)

D05’s training ALB uses an **HTTP** listener (`service_url = http://…`). Do **not** assume HTTPS until you add a TLS listener and a valid certificate (links to C01 TLS lessons).

```bash
# Prefer Terraform output; HTTP is the D05 baseline:
export HARBOUR_HEALTH_URL="${SERVICE_URL}/health"
# e.g. http://harbour-xxxx.eu-west-1.elb.amazonaws.com/health
# Only use https://… after you have configured an HTTPS listener + cert (enhancement below).

test -n "${HARBOUR_HEALTH_URL:-}" || {
  echo "Set HARBOUR_HEALTH_URL from service_url, or skip until D05 Stage C apply"
  exit 1
}
curl -v --connect-timeout 5 --max-time 15 "$HARBOUR_HEALTH_URL" \
  2>&1 | tee "$HARBOUR_ROOT/docs/cloud/aws-health-curl.txt" | tail -n 40

python3 - <<'PY'
from urllib.parse import urlparse
import os, subprocess
host = urlparse(os.environ["HARBOUR_HEALTH_URL"]).hostname
print(host)
subprocess.run(["dig", "+short", host], check=False)
PY
```

Apply the C01 ordered checks: DNS → route (your laptop) → **HTTP** (or TLS if enhanced) → status. Record refused vs timeout vs 5xx vs ready/health split if applicable.

**HTTPS enhancement (optional, explicit):** add an HTTPS listener + ACM (or imported) certificate for a hostname you control; then set `HARBOUR_HEALTH_URL=https://<hostname>/health` and reuse C01 verify/mismatch drills against that edge. Until then, keep evidence on **HTTP** so it matches D05.

If you only have local Compose today, complete network **sketch + SG design** now and mark “AWS health curl” as blocked on D05 apply — still finish IAM and budget. Do not fake a public URL.

**Verify:** `network-baseline.md` matches reality (or honestly says “pending apply”); health URL scheme matches the listener you actually have.

---

## Section 2.5 — Foundational services map

### 2.5.1 Worked example — where Harbour lives

Fill `docs/cloud/services-map.md`:

| Concern | Local (DevOps) | AWS foundation (this chapter) | Notes / D05 resource |
| --- | --- | --- | --- |
| API process | Compose `api` | ECS Fargate / EC2 | |
| Image | Local/GHCR | ECR | |
| Data | Compose `db` unpublished | RDS or deferred | |
| Edge | localhost:8000 | ALB + SG | |
| DNS | none or /etc/hosts | Route 53 or ALB DNS | |
| Logs | `compose logs` | CloudWatch Logs | |
| Identity (workload) | n/a | Task role | |
| Identity (human demo) | n/a | `harbour-demo-operator` | |

**Rule:** Prefer linking existing Terraform addresses over recreating resources in the console.

### 2.5.2 Practice — demo operator can see what matters

```bash
export AWS_PROFILE=harbour-demo
aws ecs list-clusters --region "$AWS_REGION" 2>&1 | head
aws elbv2 describe-load-balancers --region "$AWS_REGION" 2>&1 | head
# Expect success for describe, or AccessDenied with a note to widen *read* only
```

**Verify:** Services map committed; no secret values in the table.

### 2.5.3 Worked example — workload identity (ECS task role), not only humans

Least privilege applies to **running services**, not only the demo CLI profile. After D05 runtime exists:

```bash
export AWS_PROFILE=harbour-training
# CLUSTER / SERVICE from your staging names:
TASK_DEF="$(aws ecs describe-services --region "$AWS_REGION" \
  --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].taskDefinition' --output text)"
echo "task_definition=${TASK_DEF}"

TASK_ROLE_ARN="$(aws ecs describe-task-definition --region "$AWS_REGION" \
  --task-definition "$TASK_DEF" \
  --query 'taskDefinition.taskRoleArn' --output text)"
EXEC_ROLE_ARN="$(aws ecs describe-task-definition --region "$AWS_REGION" \
  --task-definition "$TASK_DEF" \
  --query 'taskDefinition.executionRoleArn' --output text)"
echo "taskRole=${TASK_ROLE_ARN}" | tee "$HARBOUR_ROOT/docs/cloud/workload-roles.txt"
echo "executionRole=${EXEC_ROLE_ARN}" | tee -a "$HARBOUR_ROOT/docs/cloud/workload-roles.txt"

# What can the task role do? (non-mutating simulation)
aws iam simulate-principal-policy \
  --policy-source-arn "$TASK_ROLE_ARN" \
  --action-names ecr:GetAuthorizationToken logs:PutLogEvents iam:CreateUser s3:ListAllMyBuckets \
  --output table | tee "$HARBOUR_ROOT/docs/cloud/iam-simulate-task-role.txt"
```

**Expected teaching outcome:**

| Role | Typical allow | Typical deny |
| --- | --- | --- |
| Execution role | Pull image, write logs (execution policy) | Broad IAM/admin |
| Task role | Only what the **app** needs (often minimal in D05 training) | `iam:CreateUser`, account-wide admin |

Record in `iam-baseline.md`: human demo-operator vs task role vs execution role — three different trust boundaries.

If runtime is not applied yet, write the intended role split from D05 module code (`aws_iam_role.task` / `execution`) and mark simulation as pending — do not skip the conceptual distinction.

**Verify:** Docs name which identity Harbour’s task assumes and cite simulation (or attached-policy list) evidence.

---

## Section 2.6 — Landing-zone ADR and destroy policy

### 2.6.1 ADR

`docs/decisions/0102-aws-landing-zone.md`:

```markdown
# ADR 0102 — Harbour AWS landing zone (training)

## Decision
- Account: …
- Region: …
- Human identities: training-admin (break-glass lab) + demo-operator (happy path)
- Network pattern: public-subnet training / private+NAT (pick one; justify cost)
- Reuse D05 infra: yes/no — paths …

## Consequences
- Demo must work as demo-operator
- Budget $… with alert …
- Destroy command / runbook: …
```

### 2.6.2 Worked example — idle and destroy

```bash
# If Terraform-managed (preferred) — D05 staging root:
# AWS_PROFILE=harbour-training terraform -chdir="$HARBOUR_ROOT/infra/envs/staging" plan -destroy
# Only destroy when you intend to; capture the plan in evidence if you run it

# Document the idle policy even if you keep a minimal always-on budget alarm only.
```

`docs/runbooks/aws-training-teardown.md`: ordered teardown, what not to delete (budget? MFA?), and how to confirm bill goes quiet.

---

## Section 2.7 — Troubleshooting field guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `InvalidClientTokenId` | Wrong keys/profile | `sts get-caller-identity` |
| AccessDenied on demo path | Policy too tight or wrong resource | Policy simulator; widen read-only carefully |
| AccessDenied expected on iam:CreateUser | Good — demo is not admin | Keep it that way |
| curl timeout to ALB | SG, subnet route, unhealthy targets | C01 hops; target group health |
| curl refused | Nothing listening / wrong port | Listener rules; ECS service |
| Surprise bill | NAT/ALB/idle ECS | Budgets; teardown runbook |

---

## Practical Assessment — Chapter 2 — landing zone without standing admin

Align with [C02 Course Detail](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C02%20AWS%20Cloud%20Foundations.md) and Final Project Checklist C02.

### Required deliverables

1. `docs/cloud/iam-baseline.md` — root vs admin vs **demo-operator** vs **ECS task/execution roles**; MFA notes; explicit “no admin for happy path.”  
2. Positive + negative human permission evidence (STS/describe allowed; simulate or non-mutating deny — **not** `create-user`).  
3. Workload role evidence (task role ARN + simulation or policy list).  
4. `docs/cloud/network-baseline.md` — diagram, VPC/SG IDs from `terraform -chdir=…/envs/staging` (or minimal VPC).  
5. `docs/cloud/services-map.md` — Harbour placement table.  
6. `docs/cloud/cost-guardrails.md` — budget + alert proof + idle/destroy policy.  
7. Health/demo check using **`http://`** D05 baseline URL unless HTTPS was explicitly added.  
8. ADR 0102 committed.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| IAM | Single admin key | Demo operator + MFA + non-mutating deny proof + task role noted | SSO; task-role simulation filed |
| Network | Console doodle | Documented VPC/SG matching live IDs | C01 hops against ALB with evidence |
| Services | Vague “use ECS” | Map linked to real resources/outputs | No duplicate unmanaged stack |
| Cost | Ignored | Budget alert before spend | Tags + teardown drill executed |
| Demo path | Uses admin “because easier” | Happy path on least-privilege identity | Automation assumes demo role |

**Completion:** **Competent** on every row.

### Self-check

- Did STS succeed only **after** profiles were configured (§2.2)?  
- Can you demo without admin, with non-mutating deny proof?  
- Do you know the ECS **task role** ARN and what it cannot do?  
- Is health evidence on **http://** unless you added TLS deliberately?  
- Were Terraform outputs read via `infra/envs/staging`?  
- Is there a budget alert before extra spend?

### Example conclusion (evidence still required)

> Training account `…`, region `eu-west-1`. Profiles configured then STS-validated. Demo: describe allowed; `simulate-principal-policy` denies `iam:CreateUser`. Task role ARN recorded; simulation shows no admin IAM. SG IDs from `terraform -chdir=infra/envs/staging` + ECS service query. Budget before spend. Health via `http://$ALB/health` (D05 HTTP listener). No admin keys in Git.

---

## Quick-reference decision guide

| You need to… | Start by… | Avoid… |
| --- | --- | --- |
| “Just try something” | Confirm budget alert exists | Untagged always-on NAT |
| Show Harbour to a peer | `AWS_PROFILE=harbour-demo` | Handing them root |
| Fix AccessDenied | Least privilege + specific ARN | `AdministratorAccess` for convenience |
| Debug reachability | C01 hops against ALB DNS | Restarting ECS first |
| Leave for the week | Teardown / scale-to-zero policy | Hoping the bill is fine |

## Glossary

| Term | Meaning |
| --- | --- |
| Landing zone | Account + identity + network + guardrails baseline |
| Break-glass | Rare highly privileged access with audit |
| Task role | Workload identity for AWS API calls from compute |
| Security group | Stateful allow-list firewall at the ENI |
| Standing admin | Privileged creds used as the normal daily/demo path |

## References

- [AWS IAM best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)  
- [VPC security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)  
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)  
- [D05 Terraform](../4.1%20DevOps/D05%20Infrastructure%20as%20Code%20and%20Terraform.md) · [C01](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) · [Cloud overview](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/CLOUD%20Overview.md)

**Previous chapter:** [Chapter 1 — Linux, Networking and Cloud Fundamentals](C01%20Linux%20Networking%20and%20Cloud%20Fundamentals.md) · **Course detail:** [C02](../../3%20Course%20Detail/3.2%20Cloud%20Engineering/C02%20AWS%20Cloud%20Foundations.md) · **Next chapter:** Chapter 3 — AWS Infrastructure and Architecture (not yet authored) · **Checklist:** [Final Project Checklist · C02](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md)
