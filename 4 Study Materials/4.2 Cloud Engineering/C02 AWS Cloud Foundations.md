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

```bash
export HARBOUR_ROOT="${HARBOUR_ROOT:-$HOME/harbour-platform}"
export AWS_PROFILE="${AWS_PROFILE:-harbour-training}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"
cd "$HARBOUR_ROOT"
mkdir -p docs/cloud docs/runbooks docs/decisions

aws --version
aws sts get-caller-identity --profile "$AWS_PROFILE" || {
  echo "Configure a training profile first (§2.2) — do not proceed as root"
  exit 1
}
```

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

### 2.2.2 Worked example — CLI profiles without committing keys

```bash
# Prefer aws configure sso if your org supports it.
# Otherwise: create access keys ONLY for harbour-training-admin temporarily,
# store in the shared credentials file — never in the Harbour repo.
aws configure --profile harbour-training
aws configure --profile harbour-demo

aws sts get-caller-identity --profile harbour-training
aws sts get-caller-identity --profile harbour-demo
```

Add to `.gitignore` if not already present: any local override files; never commit `~/.aws`. Document in `docs/cloud/iam-baseline.md` which profile is admin vs demo.

### 2.2.3 Worked example — MFA expectation

```bash
# Console: enable MFA on both human users. CLI check (IAM):
aws iam list-mfa-devices --user-name harbour-demo-operator --profile harbour-training
# Expect at least one device when MFA is configured (admin may need iam:ListMFADevices).
```

If MFA listing is denied to the demo user, verify MFA in the console as admin and record “MFA verified visually / by admin” — still do not skip MFA.

### 2.2.4 Practice — prove the happy path is not admin

```bash
export AWS_PROFILE=harbour-demo
aws sts get-caller-identity
# Attempt something admin-only; expect AccessDenied:
aws iam create-user --user-name should-fail 2>&1 | head -n 20
```

**Verify:** `docs/cloud/iam-baseline.md` states explicitly: *demo path uses `harbour-demo` / `harbour-demo-operator`; standing admin is not required for health checks and describe operations.*

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

If D05 `infra/` already has a VPC:

```bash
cd "$HARBOUR_ROOT/infra"  # adjust to your layout
terraform output 2>/dev/null | tee "$HARBOUR_ROOT/docs/cloud/vpc-outputs.txt" || true
```

Copy VPC ID, subnet IDs, SG IDs into `docs/cloud/network-baseline.md` with a diagram:

```text
[Client] --HTTPS--> [ALB SG] --HTTP--> [Task SG] --5432--> [DB SG or none]
```

If you have **no** VPC yet, create a **minimal** one (console or a small Terraform root) with:

- One VPC CIDR (e.g. `10.50.0.0/16`)  
- Two public subnets in different AZs (ALB requirement)  
- One SG for an HTTP/HTTPS entry and one for app tasks allowing only from the entry SG  
- **No** NAT Gateway unless you accept the cost in writing  

Do not open `0.0.0.0/0` to SSH on the app SG.

### 2.4.3 Worked example — security groups as allow-lists

```bash
export AWS_PROFILE=harbour-training
# Replace with your SG ids from outputs/docs:
aws ec2 describe-security-groups --group-ids "$ALB_SG" "$APP_SG" \
  --query 'SecurityGroups[].{Name:GroupName,Id:GroupId,Ingress:IpPermissions}' \
  --output json | tee docs/cloud/sg-ingress.json
```

**Practice — reproduce:** Using C01 hop language, write which SG corresponds to the “TCP port hop” for the client and for the task.

### 2.4.4 Worked example — C01 diagnostics against an AWS endpoint

Once Harbour (or a placeholder health target) is reachable via an ALB DNS name or public IP:

```bash
# Set explicitly, e.g. export HARBOUR_HEALTH_URL="https://YOUR-ALB-DNS/health"
test -n "${HARBOUR_HEALTH_URL:-}" || {
  echo "Set HARBOUR_HEALTH_URL to your ALB health URL, or skip until D05 apply"
  exit 1
}
curl -v --connect-timeout 5 --max-time 15 "$HARBOUR_HEALTH_URL" \
  2>&1 | tee docs/cloud/aws-health-curl.txt | tail -n 40

# DNS for the hostname in the URL:
python3 - <<'PY'
from urllib.parse import urlparse
import os, subprocess
host = urlparse(os.environ["HARBOUR_HEALTH_URL"]).hostname
print(host)
subprocess.run(["dig", "+short", host], check=False)
PY
```

Apply the C01 ordered checks: DNS → route (your laptop) → TLS → HTTP status. Record refused vs timeout vs 5xx vs ready/health split if applicable.

If you only have local Compose today, complete network **sketch + SG design** now and mark “AWS health curl” as blocked on D05 apply — still finish IAM and budget. Do not fake a public URL.

**Verify:** `network-baseline.md` matches reality (or honestly says “pending apply”).

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
# If Terraform-managed (preferred):
cd "$HARBOUR_ROOT/infra"   # your path
# AWS_PROFILE=harbour-training terraform plan -destroy
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

1. `docs/cloud/iam-baseline.md` — root vs admin vs **demo-operator**; MFA notes; explicit “no admin for happy path.”  
2. `docs/cloud/network-baseline.md` — diagram, VPC/SG summary (from D05 outputs or minimal VPC).  
3. `docs/cloud/services-map.md` — Harbour placement table.  
4. `docs/cloud/cost-guardrails.md` — budget + alert proof + idle/destroy policy.  
5. Evidence that **`harbour-demo` profile** can perform the documented demo checks (STS identity + describe and/or health curl) while **admin-only** actions fail.  
6. ADR 0102 committed.

### Rubric

| Dimension | Developing | Competent | Advanced |
| --- | --- | --- | --- |
| IAM | Single admin key | Demo operator + MFA + denied admin action | SSO / no long-lived keys |
| Network | Console doodle | Documented VPC/SG matching live IDs | C01 hops against ALB with evidence |
| Services | Vague “use ECS” | Map linked to real resources/outputs | No duplicate unmanaged stack |
| Cost | Ignored | Budget alert before spend | Tags + teardown drill executed |
| Demo path | Uses admin “because easier” | Happy path on least-privilege identity | Automation assumes demo role |

**Completion:** **Competent** on every row.

### Self-check

- Can you open the health URL (or describe the service) **without** the admin profile?  
- Is root unused for labs?  
- Would a second engineer find VPC/SG IDs from `docs/cloud/` alone?  
- Is there a budget alert you have actually received or can show configured?

### Example conclusion (evidence still required)

> Training account `…`, region `eu-west-1`. Profiles `harbour-training` (admin) and `harbour-demo` (read/describe). Demo `CreateUser` → AccessDenied. VPC/SG IDs from D05 outputs in `network-baseline.md`. Budget $20 @ 80% email configured before new subnets. Health curl via ALB as demo user documented. No admin keys in Git. Teardown runbook filed.

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
