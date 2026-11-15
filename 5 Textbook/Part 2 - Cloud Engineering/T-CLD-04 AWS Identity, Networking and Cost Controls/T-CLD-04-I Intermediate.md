# T-CLD-04-I — Intermediate Practice

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-i"></a>
#### T-CLD-04-I — Intermediate Practice

## Why this matters

At Beginner level you learned to read a policy, tell a refusal from a timeout and set a budget. Real services have more moving parts: people assume roles into other accounts, containers carry their own identities, traffic flows through route tables, security groups and network ACLs in sequence, and a bill is a sum of a hundred small decisions. When something breaks, "add more permissions" or "open the port" is the wrong reflex. The Intermediate skill is to **predict the outcome from the model, then check the prediction with evidence**.

This section assumes the Beginner material: principals, policies, roles, ARNs, CIDR, subnets, security groups, budgets. The running example is a small `orders` service behind a load balancer. Account IDs (`111122223333`, `444455556666`), Regions and names are placeholders.

**Markers.** **[AWS-specific]** marks behaviour particular to this provider. **[Version-sensitive]** marks defaults, limits, console labels, prices and message wording that change over time; verify against current documentation. Outputs marked *illustrative* show shape, not measurement.

## First principles: what a request carries

Every AWS API call is an authenticated, signed request that carries four things the authorisation system looks at:

| Element | Example | Where it comes from |
| --- | --- | --- |
| Principal | `arn:aws:sts::111122223333:assumed-role/ops-readonly/alice` | The credentials used to sign |
| Action | `ecs:UpdateService` | The API operation |
| Resource | `arn:aws:ecs:eu-west-1:111122223333:service/orders/orders-api` | The target of the operation |
| Context | Source IP, time, MFA present, tags, requested Region, calling service | The request itself and the session |

A policy is a function over these four elements. Conditions in a statement test the context. That is why identical actions can be allowed from one session and refused from another: the context differed.

## IAM policy evaluation

At Beginner level the rule was "deny wins, otherwise allow, otherwise deny". The fuller picture adds layers that can only *limit*, not grant.

**Layers, in the order you should check them.**

| Layer | Grants permission? | Role in evaluation |
| --- | --- | --- |
| Explicit `Deny` in any applicable policy | No (always blocks) | Overrides everything |
| Organisation guardrails (service control policies) | No | Maximum available to accounts in the organisation |
| Permissions boundary on the principal | No | Maximum an identity's policies may grant |
| Session policy (passed when assuming a role) | No | Further narrows one session |
| Identity-based policies | Yes | What the principal may do |
| Resource-based policies | Yes | What the resource allows named principals |

A useful way to remember it: **grants come from identity and resource policies; every other layer is a ceiling.** For an action to be allowed, (a) nothing may explicitly deny it, (b) every ceiling that applies must permit it, and (c) at least one grant must cover it.

**Same account versus cross-account.** Within one account, an allow in the identity policy *or* a suitable resource policy is generally enough. Across accounts, **both sides** must agree: the caller's identity policy must allow the action *and* the resource's policy (or the assumed role's trust, for role assumption) must allow the caller. This is why a cross-account request can fail with a perfectly good identity policy.

> **[AWS-specific / Version-sensitive]** Exact interactions (for example how a permissions boundary affects a resource policy that names an IAM user or role directly) have subtleties and exceptions that AWS refines over time. For any non-trivial case, confirm in the current policy-evaluation documentation rather than from memory.

**Worked example.** A role `orders-deployer` has an identity policy allowing `ecs:UpdateService` on `*`, a permissions boundary allowing only `ecs:Describe*`, `ecs:List*` and `logs:*`, and sits in an account whose organisation policy permits `ecs:*`.

| Action | Identity allow | Boundary | Organisation ceiling | Result |
| --- | --- | --- | --- | --- |
| `ecs:UpdateService` | Yes | **No** | Yes | Denied: the boundary does not include it |
| `ecs:DescribeServices` | No | Yes | Yes | Denied: the identity policy grants nothing |
| `logs:GetLogEvents` | Yes | Yes | **No** (organisation policy omits `logs`) | Denied by the organisation ceiling |

No single document shows the effective permission; it is an **intersection** of ceilings with a **union** of grants. This is the reason for the troubleshooting order below.

**Conditions.** A statement's `Condition` block restricts when it applies:

```json
{
  "Effect": "Allow",
  "Action": "ecs:UpdateService",
  "Resource": "arn:aws:ecs:eu-west-1:111122223333:service/orders/*",
  "Condition": {
    "Bool": {"aws:MultiFactorAuthPresent": "true"},
    "StringEquals": {"aws:RequestedRegion": "eu-west-1"}
  }
}
```

Common context keys: `aws:MultiFactorAuthPresent`, `aws:RequestedRegion`, `aws:PrincipalTag/<key>`, `aws:ResourceTag/<key>`, `aws:SourceVpce` (the VPC endpoint used), `aws:SourceIp`, `aws:PrincipalOrgID`. Two cautions. Conditions on a missing key evaluate false for `Allow` and surprisingly can fail to match a `Deny`; test both paths. And `aws:SourceIp` shows a private address, or is absent, when the request travels through a VPC endpoint or comes from another AWS service on your behalf, so IP conditions silently stop working there.

**Deny with `NotAction` or a negated condition.** A common guardrail pattern is "deny everything outside the approved Regions", which must exempt global services:

```json
{
  "Effect": "Deny",
  "NotAction": ["iam:*", "sts:*", "organizations:*", "route53:*", "cloudfront:*", "support:*"],
  "Resource": "*",
  "Condition": {"StringNotEquals": {"aws:RequestedRegion": ["eu-west-1", "eu-central-1"]}}
}
```

**[Version-sensitive]** The list of global services that must be exempted changes; copy it from current AWS guidance and test, because a wrong exemption either breaks login or leaves a Region open.

## Assuming a role

To assume a role, two conditions must both hold: the role's **trust policy** names the caller, and the caller's own **identity policy** allows `sts:AssumeRole` on that role (for same-account assumption, a trust policy that names the exact caller ARN can suffice; cross-account always needs both). STS returns temporary credentials: an access key, a secret and a **session token**.

A trust policy for a role in the account `444455556666` that engineers in `111122223333` may assume only with MFA:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::111122223333:root"},
    "Action": "sts:AssumeRole",
    "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}
  }]
}
```

Naming the account root as principal does **not** mean the root user: it delegates the decision to the other account's IAM, so that account's administrators decide which of *their* identities may assume it. Then in the caller's account:

```json
{"Effect": "Allow", "Action": "sts:AssumeRole",
 "Resource": "arn:aws:iam::444455556666:role/orders-readonly"}
```

**On the command line:**

```ini
# ~/.aws/config
[profile base]
sso_session = corp
sso_account_id = 111122223333
sso_role_name = Engineer
region = eu-west-1

[profile orders-readonly]
role_arn = arn:aws:iam::444455556666:role/orders-readonly
source_profile = base
role_session_name = alice
region = eu-west-1
```

```bash
aws sts get-caller-identity --profile orders-readonly
# illustrative: .../assumed-role/orders-readonly/alice in account 444455556666
```

The CLI performs the assumption for you and caches the credentials until they expire. Verify the account ID in the ARN every time you switch profile.

**Session facts to know.**

- Credentials are temporary: a default of one hour, up to the role's configured maximum. **[Version-sensitive]** Limits (including the one-hour cap when chaining roles) are adjustable by AWS.
- **Role chaining** (assuming a role from a role session) works but resets the maximum duration and loses the original login's session name unless you set it.
- A **session policy** supplied at assume time can only narrow permissions, never widen them.
- Every assumption is logged by CloudTrail with the caller's identity, so `role_session_name` should identify the human or system. Cultivate it; anonymous session names make audits slow.
- **External ID** is a shared secret condition (`sts:ExternalId`) used when a third party assumes a role in your account; it defends against the confused-deputy problem (a topic expanded at Expert level).

## Least privilege, iteratively

Least privilege is a process, not a document. A workable loop:

1. **Start narrow.** Grant read and the one write action the task needs, on named resources.
2. **Exercise the real workflow** (deploy, rollback, read logs) in a non-production account.
3. **Collect denials** from CloudTrail or error messages; decide for each whether it is a legitimate need.
4. **Add specific actions**, not families. Prefer `ecs:UpdateService` on one service ARN to `ecs:*`.
5. **Prove it** with simulation and a negative test.
6. **Review periodically** using what the role actually used.

The policy simulator checks the policy without side effects:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::111122223333:role/orders-deployer \
  --action-names ecs:UpdateService iam:CreateUser \
  --resource-arns arn:aws:ecs:eu-west-1:111122223333:service/orders/orders-api \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table
```

Expect `allowed` for the first and `implicitDeny` for the second. The simulator tells you what the *policies you gave it* imply; **check what it covers** (resource policies, organisation guardrails and real-time context may or may not be included in your tooling version) and treat it as a design check, not as proof of effective access. The proof is a real call that succeeds or is denied.

To see what a role has really used, use the service's last-accessed information and access analysis:

```bash
aws iam generate-service-last-accessed-details \
  --arn arn:aws:iam::111122223333:role/orders-deployer
# then: aws iam get-service-last-accessed-details --job-id <id>
```

> **[AWS-specific / Version-sensitive]** IAM Access Analyzer can additionally generate a candidate policy from CloudTrail activity and report unused access. Features, retention and pricing vary; use the output as a first draft to review, never as an automatic grant.

**Customer-managed versus AWS-managed policies.** AWS-managed policies (`ReadOnlyAccess`, `AdministratorAccess`) are convenient but usually broader than your need and change without your review. Prefer customer-managed policies you can version in source control for anything used daily.

## Two principals, two purposes

Create a *training administrator* (broad rights in the training account only, MFA required) and a *demo operator* (read-mostly: describe resources, read logs; no `iam:*`, no unrestricted `ec2:*`). If the demo needs one mutating action, add just that action on that resource ARN. Test denial with the simulator, not by creating real users.

## Workload identity

Services need identities too. In a container service there are two different roles:

| Role | Used by | Typical permissions |
| --- | --- | --- |
| Execution role | The platform, to start the task | Pull image, write logs, read startup secrets |
| Task role | Your application code | Exactly the APIs the code calls |

They are separate trust boundaries; neither should be broad. For virtual machines the equivalent is an **instance profile**; for functions an **execution role**. The code obtains short-lived credentials automatically from a local metadata endpoint, so there are no keys to leak. Record human operator, task role and execution role separately in your identity baseline, and check each with the simulator.

> **[AWS-specific]** Kubernetes on AWS has its own ways of mapping a pod to a role; the idea (workload identity with no static keys) is the same, the mechanism differs by platform and version.

## VPC routing

A packet leaving a resource is matched against its subnet's **route table**. The rule is **longest prefix match**: the most specific route wins.

```text
Route table: public-rt                     Route table: private-rt
Destination      Target                    Destination      Target
10.50.0.0/16     local                     10.50.0.0/16     local
0.0.0.0/0        igw-0abc...               0.0.0.0/0        nat-0def...   (optional, costs money)
                                           pl-s3...         vpce-0ghi...  (gateway endpoint for object storage)
```

Targets and what they do:

| Target | Purpose | Notes |
| --- | --- | --- |
| `local` | Traffic inside the VPC | Always present, cannot be removed |
| Internet gateway | Two-way internet access for resources with public addresses | No hourly charge |
| NAT gateway | Outbound-only internet for private resources | Hourly plus per-GB processing; lives in a public subnet; zonal |
| Gateway endpoint | Private path to certain services (object storage, a key-value database) | Route-table entry; no hourly charge |
| Interface endpoint | Private path to many services through network interfaces | Hourly per AZ plus per-GB |
| Peering or transit attachment | Reach another VPC | Needs non-overlapping CIDR on both sides |

Routing is **per subnet**, and it has two halves. The sender's subnet must have a route toward the destination, **and the reply must find its way back**. An asymmetric setup (a route out but none back) produces timeouts that look like firewall problems.

**What makes a subnet public, precisely.** All three of: a route `0.0.0.0/0 → internet gateway`; a public (or elastic) IPv4 address on the resource; and security group and NACL rules that allow the traffic. Remove any one and the resource is not reachable from the internet. **[Version-sensitive]** AWS now charges for public IPv4 addresses, which affects the "just give everything a public IP" shortcut.

## Security groups versus network ACLs

| Property | Security group | Network ACL |
| --- | --- | --- |
| Attached to | A network interface (resource) | A subnet |
| State | Stateful | Stateless |
| Rule types | Allow only | Allow and deny |
| Evaluation | All rules together | Numbered rules, lowest first, first match wins |
| Default | Inbound denied, outbound allowed | Default NACL allows all |
| Source | CIDR, prefix list or another security group | CIDR only |
| Typical use | Primary segmentation between tiers | Coarse subnet-level block or compliance guardrail |

Stateful means that if the inbound request is allowed, the response is allowed out regardless of outbound rules. Stateless means each direction is judged separately, so a NACL must allow the **return traffic on ephemeral ports** (high-numbered client ports; commonly 1024–65535, check the client operating systems in use) as well as the request.

```text
Client 203.0.113.9:50432  →  ALB :443     NACL inbound must allow tcp/443 from client
ALB :443  →  Client :50432                NACL outbound must allow tcp/1024-65535 to client
```

Practical rule: **use security groups for everything; use NACLs rarely, with a stated reason** such as explicitly blocking a known-bad CIDR. A misconfigured NACL is one of the hardest failures to find because the security groups all look correct.

**A security group chain in Terraform:**

```hcl
resource "aws_security_group" "alb" {
  name   = "orders-alb"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app" {
  name   = "orders-app"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]   # only the load balancer
  }
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

> **[Version-sensitive]** Resource and argument names follow the Terraform AWS provider at the time of writing; newer provider versions add separate rule resources and deprecate some inline forms. Pin the provider and read its changelog before upgrading.

The application group allows traffic only from the load-balancer group; there is no SSH rule. Restricting egress to `443` is stricter than the default and breaks anything needing other ports; document the decision.

## The VPC edge for a service

A minimal design: one VPC (for example `10.50.0.0/16`); two public subnets in different AZs for the load balancer; private subnets for tasks; one security group for the load balancer allowing HTTP/HTTPS from the internet; one for tasks allowing inbound *only from the load-balancer group*; no open SSH. How tasks reach the internet for image pulls and updates is a cost decision with three options:

| Option | Security | Cost | Failure behaviour |
| --- | --- | --- | --- |
| Tasks in public subnets with public IPs (lab only) | Weaker: each task has an internet-facing address | Lowest | No NAT to fail |
| Private subnets with one NAT gateway | Good | Hourly plus per-GB, and cross-AZ traffic for other zones | An AZ failure can cut egress for the rest |
| Private subnets plus endpoints for registry, logs and storage | Best for AWS-service traffic | Endpoint hourly cost per AZ | Endpoint policy and DNS must be right |

Training deployments sometimes use the first option to avoid NAT charges; that is a cost trade-off, not a production blueprint. Whatever you choose, write it down with the reason.

## Troubleshooting: a repeatable routine

Apply the diagnostics from Beginner level to the cloud endpoint, then go deeper only where the evidence points.

**1. Classify the failure.** Fast, named refusal (permission) or silence (network)?

**2. If permission:** read the error for principal, action, resource and the stated reason.

```bash
# Who am I, really?
aws sts get-caller-identity
# Decode the detailed authorization failure, where the service returns an encoded message:
aws sts decode-authorization-message --encoded-message <blob> --query DecodedMessage --output text
# Find the denied call in the audit trail (management events):
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateService \
  --max-results 5 --query 'Events[].[EventTime,Username]' --output table
```

Then check in order: **explicit deny anywhere → organisation guardrail → permissions boundary → session policy → identity policy → resource policy → conditions** (MFA, Region, tags, source). The first layer that fails is your cause.

**3. If network:** walk the path.

```text
name resolves?  →  route from source subnet?  →  route back?  →  NACL (both directions)?
  →  security group on destination (inbound) and source (outbound)?  →  something listening?
```

```bash
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0aaa \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId,NatGatewayId,State]' --output table
aws ec2 describe-security-groups --group-ids sg-0bbb \
  --query 'SecurityGroups[].IpPermissions' --output json
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-0aaa \
  --query 'NetworkAcls[].Entries' --output json
```

**Tools that shorten the search.** **[AWS-specific]** *Reachability Analyzer* evaluates a path between two endpoints from configuration and reports the first blocking component; it does not send packets, so it will not find a stopped application. *VPC Flow Logs* record accepted and rejected flows per network interface:

```text
# illustrative flow-log line: version account eni src dst srcport dstport proto packets bytes start end action status
2 111122223333 eni-0abc 203.0.113.9 10.50.1.12 50432 8000 6 4 240 1731650000 1731650060 REJECT OK
```

A `REJECT` tells you a security group or NACL dropped the packet but **not which one**. Combine with the configuration. An `ACCEPT` outbound with no inbound `ACCEPT` at the destination points to a route-back or destination-side problem.

**Typical causes mapped to symptoms:**

| Symptom | Likely cause | Check |
| --- | --- | --- |
| Timeout from the internet | Subnet lacks IGW route; no public IP; security group or NACL blocks | Route table, address, groups |
| Timeout from task to the internet | Private subnet with no NAT or endpoint | Route table of the task subnet |
| Works one way, fails on reply | Stateless NACL missing ephemeral-port rule | NACL outbound |
| `502`/`503` from load balancer | Targets unhealthy | Target-group health, security group between load balancer and task |
| `AccessDenied` only in one account | Boundary, guardrail or trust differs | Policy layers in that account |
| `AccessDenied` only from a pipeline | Pipeline role session lacks a tag or MFA condition | Conditions in the policy |

## Tags and budgets

**Tags** are key–value labels on resources. They serve three jobs: *cost attribution* (who owns this spend), *access control* (conditions on `aws:ResourceTag`) and *operations* (automation targets, expiry). Decide a small standard set and enforce it:

| Key | Example | Purpose |
| --- | --- | --- |
| `project` | `orders` | Cost grouping |
| `owner` | `team-orders` | Who to contact |
| `environment` | `training` | Policy and budget scope |
| `expires` | `2026-12-01` | Cleanup automation |

**[AWS-specific]** A tag key must be **activated as a cost-allocation tag** in billing settings before it appears in cost reports, and only data after activation is tagged. Not every resource type supports tags at creation, and some costs (data transfer, support) are not taggable at all; plan an "unallocated" bucket.

**Budgets.** A budget compares actual or forecast spend with a limit and sends notifications at thresholds. Scope it by tag, service or account to make an alert actionable.

```json
{
  "BudgetName": "training-monthly",
  "BudgetLimit": {"Amount": "50", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "CostFilters": {"TagKeyValue": ["user:environment$training"]}
}
```

**[Version-sensitive]** Filter syntax and the delay before data appears vary; test with a deliberately low threshold. Billing data lags by hours, so budgets detect trends, not spikes within the hour.

**Cost guardrails document**

| Item | Value |
| --- | --- |
| Monthly budget | e.g. a small fixed amount |
| Alert threshold | e.g. 50% and 80%, plus a forecast alert |
| Notification | A monitored mailbox or channel, not a personal inbox |
| Idle policy | Stop or destroy within N hours |
| Forbidden by default | Always-on NAT, public databases, unused load balancers |
| Owner | A named person who acts on the alert |

An alert nobody reads is a decoration. The document must name who acts and what they do.

## What can go wrong: a short catalogue

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Trust policy fixed but caller lacks `sts:AssumeRole` | `AccessDenied` on assume | Add the action on the role ARN to the caller |
| Using `"Principal": {"AWS": "*"}` in a trust policy | Anyone can assume, subject only to other checks | Name specific principals and conditions |
| IP condition with VPC endpoint traffic | Allow never matches | Use `aws:SourceVpce` or `aws:SourceVpc` |
| Missing return rule on a NACL | One-way connectivity | Add ephemeral-port rule or remove the NACL |
| Overlapping CIDR with another network | Cannot peer or route | Re-plan ranges before connecting |
| Cost tag not activated | Reports show "untagged" | Activate tag keys; tag at creation |

## Knowledge consolidation

- Evaluate a request as **explicit deny → ceilings → grants**: organisation guardrails, boundaries and session policies only limit; identity and resource policies grant.
- Across accounts, **both sides must allow**; within an account, one grant is generally enough. Verify subtle cases in current documentation.
- **Role assumption** needs a trust policy naming the caller and (cross-account) an identity permission to assume; sessions are temporary and logged with a session name you control.
- Least privilege is a **loop**: narrow, exercise, observe denials, add specifics, prove, review with usage data.
- The simulator checks policy logic; only a real call proves effective access.
- Workloads use **their own roles**: separate execution and task roles; no static keys.
- Routing is **longest prefix**, per subnet, with a way **back**. A public subnet needs route, address *and* permissive rules.
- **Security groups** are stateful allow-lists and the main tool; **NACLs** are stateless, ordered, rare, and need ephemeral-port return rules.
- Troubleshoot by **classifying** (refusal or silence), then walking the layers in a fixed order and gathering evidence at each step.
- **Tags** need activation to appear in cost reports; budgets warn on trends and need an owner.

## Exercises

**Exercise 1 — Evaluation table.** Write a table (as in the worked example) for a role with an identity allow for `s3:PutObject`, a boundary that allows only `s3:GetObject`, and an organisation guardrail that allows `s3:*`. Predict `GetObject`, `PutObject` and `DeleteObject`, then verify two predictions by simulation.

**Exercise 2 — Cross-account role.** In two accounts (or two roles in one account if only one is available), create a role with a trust policy that requires MFA, and a caller policy that allows `sts:AssumeRole` on it. Configure a CLI profile with `source_profile`, run `get-caller-identity` and read the ARN. Remove each half in turn and record the error.

**Exercise 3 — Least-privilege loop.** Take a deployment script, run it under a read-only role, and record each denial. Add only the actions needed, then run a negative test and the simulator. Write the final policy and one sentence per statement explaining why it exists.

**Exercise 4 — Route reading.** Given the two route tables above, state for three destinations (`10.50.7.4`, `203.0.113.5`, an object-storage address) which route is chosen and why. Then explain what changes if the `0.0.0.0/0` route is deleted from the private table.

**Exercise 5 — NACL trap.** In a lab VPC, add a NACL on the application subnet that allows inbound `tcp/8000` and outbound `tcp/8000` only. Test a connection, explain why it fails, and fix it. Decide whether you would keep the NACL at all.

**Exercise 6 — Flow-log reading.** Enable flow logs on one interface, generate an allowed and a blocked connection, and find both lines. Explain what the log can and cannot tell you about the cause.

**Exercise 7 — Cost guardrails.** Write the guardrails document for your lab: budget, thresholds, owner, idle policy, forbidden items. Create the budget and a tag-scoped variant, and note which cost lines are not attributable to a tag.

**Solution notes.**

*Exercise 1.* `GetObject`: identity allow is absent (only `PutObject` is granted), so it is denied even though the boundary permits it. `PutObject`: identity allows it but the boundary does not, so it is denied. `DeleteObject`: nothing grants it. If you predicted that *any* single allowed layer was enough, revisit the ceiling-versus-grant idea. Simulation output should show `implicitDeny` for all three; if your tooling reports otherwise, check whether it evaluates boundaries.

*Exercise 2.* Removing the trust policy produces an assume-role denial that names the role; removing the caller's permission produces a denial that names the caller. Both look similar, so read *who is not authorised to perform sts:AssumeRole on which resource*. If MFA is required and your session lacks it, expect a denial even when both halves are present.

*Exercise 3.* The first run typically shows several denials for read calls you did not anticipate (for example tag reads and describe calls). Judge each: add describe calls on specific resources if the workflow needs them; reject others and change the script. The final policy should contain resource ARNs rather than `*` for mutating actions.

*Exercise 4.* `10.50.7.4` uses `local` (most specific). `203.0.113.5` uses the default route (NAT or IGW). Object storage uses the prefix-list route to the endpoint, because the prefix list is more specific than `0.0.0.0/0`. Deleting the default route from the private table removes internet egress but leaves VPC-internal and endpoint paths.

*Exercise 5.* The request arrives, but the reply to the client's ephemeral port is blocked by the stateless outbound rule. Adding an outbound rule for ephemeral ports fixes it. A good answer notes that the security groups already provide the control and the NACL added fragility, so it should be removed unless it has a stated purpose.

*Exercise 6.* The blocked connection appears as `REJECT`; the allowed one as `ACCEPT`. The log does not say which rule rejected, nor does it show application-layer failures. It supports a hypothesis; configuration confirms it. Flow-log fields and delivery delay are **version-sensitive**, so verify against the current format.

*Exercise 7.* Tag-scoped budgets only see tagged resources; data transfer and some shared charges stay outside. Record that as accepted "unallocated" spend with an owner.
