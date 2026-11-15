# T-CLD-04-P — Professional Engineering

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-p"></a>
#### T-CLD-04-P — Professional Engineering

## Why this matters

A working cloud environment is a demo. A *professionally engineered* one has answered questions the demo never asked. Who can change production, how do they get that ability, and how would we know if they abused it? If a CI credential leaks, how far can it reach? If one workload is compromised, what can it talk to and what can it call? Where does outbound traffic go, and who can see it? What does this design cost per month, and who notices when that doubles?

Professional practice turns those questions into **explicit, reviewable, enforceable decisions**: an identity architecture with separate roles for separate duties, cross-account access that is conditional rather than trusting, network segmentation that follows data sensitivity, controlled egress, tamper-resistant audit logs, guardrails that make mistakes hard rather than discouraged, a cost model produced *before* building, and a written justification for each non-obvious policy. This section assumes the Beginner and Intermediate material: policy evaluation layers, role assumption, routing, security groups versus network ACLs, tags and budgets. The examples use the neutral `orders` service; account IDs, Regions and names are placeholders.

**Markers.** **[AWS-specific]** is behaviour particular to this provider. **[Version-sensitive]** is a default, limit, price, console label or message that changes over time; verify it. Numbers marked *illustrative* demonstrate arithmetic, not current prices.

A recurring theme: **each control reduces a specific risk and does not remove others.** Learn what each one does *not* do.

## First principles: what "production-grade" means here

Define four properties and test every design against them:

| Property | Question | Evidence |
| --- | --- | --- |
| Least authority | Can each identity do only what its job needs? | Policies, simulation, access analysis |
| Containment | If one thing is compromised, how far does it spread? | Account, network and role boundaries |
| Accountability | Can we reconstruct who did what, when, from where? | Immutable logs, session names |
| Affordability | Is the cost known, attributed and bounded? | Cost model, tags, budgets with owners |

Controls fall into three timing classes, and a mature design uses all three:

- **Preventive** controls stop the action (organisation policies, permission boundaries, network rules).
- **Detective** controls notice it afterwards (audit logs, configuration rules, anomaly detection).
- **Corrective** controls repair it (automatic remediation, break-glass procedures, teardown).

Prevention without detection fails silently; detection without prevention is a record of your losses.

## Identity architecture

**Humans.** Federate workforce identity from a central identity provider into the cloud through single sign-on. Map *groups* to *permission sets* per account; a person's access is then a function of group membership, reviewable in one place. Credentials last minutes to hours. No long-lived IAM users for people, except possibly one tightly controlled emergency identity (see break-glass).

**Workloads.** Every workload runs under a role of its own: a task role for containers, an instance profile for machines, an execution role for functions. Credentials come from the platform and expire. A role per workload per environment is more roles but a smaller blast radius; do not share a role between two services merely because they currently need the same thing.

**Pipelines.** A CI system should obtain cloud credentials through **OpenID Connect federation** with conditions on repository, branch and environment, not through stored access keys:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::111122223333:oidc-provider/token.actions.example.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {"token.actions.example.com:aud": "sts.amazonaws.com"},
      "StringLike":   {"token.actions.example.com:sub": "repo:example-org/orders:ref:refs/heads/main"}
    }
  }]
}
```

The `sub` condition is the security control: without it, any repository using the same identity provider could assume the role. Provider hostnames, claim formats and available claims differ between CI systems and change; **[Version-sensitive]** confirm the exact `sub` format against your CI vendor's documentation and test with a repository that must be *refused*.

**Separation of duties by role.** Separate roles for different intents, so that a compromise of one does not grant all:

| Role | Purpose | Who or what assumes it | Notable limits |
| --- | --- | --- | --- |
| `orders-readonly` | Observe and diagnose | Engineers, on-call | No mutating actions, no secret values |
| `orders-plan` | Compute infrastructure change | CI on pull requests | Read everything needed, write nothing |
| `orders-apply` | Execute approved change | CI on the protected branch | Scoped to the service's resources; no IAM mutation outside a boundary |
| `orders-audit` | Review configuration and logs | Security | Read-only across accounts, including log archives |
| `orders-breakglass` | Emergency administrator | Named people, with approval | MFA, alarms on use, short session |

The plan role seeing more than it writes is deliberate: pull requests from forks and feature branches run untrusted code, so they must hold only credentials that cannot change anything.

**Break-glass.** A tested emergency path exists for when the identity provider is down or a policy locks everyone out. Its properties: separate credentials stored offline with split custody; usable only with MFA; every use raises an alert to a person who did not use it; automatic review within a day; periodic rehearsal. An untested break-glass account is a belief, not a control.

**Permission boundaries for delegation.** When a team may create roles for its own workloads, give it a **boundary** policy that caps what those roles can ever receive, and require the boundary on every role it creates:

```json
{
  "Effect": "Allow",
  "Action": ["iam:CreateRole", "iam:AttachRolePolicy", "iam:PutRolePolicy"],
  "Resource": "arn:aws:iam::111122223333:role/orders-*",
  "Condition": {"StringEquals": {"iam:PermissionsBoundary": "arn:aws:iam::111122223333:policy/orders-boundary"}}
}
```

Without that condition, a delegated administrator can create an unbounded role and escape the cap. A deeper treatment of escalation paths appears at Expert level.

## Cross-account access

Multi-account structure is a primary security boundary: accounts isolate blast radius, billing and quotas. Typical separation: management (organisation control only, no workloads), log archive, security tooling, shared services (networking, registry), and one account per workload per environment.

Cross-account access has two patterns.

**Pattern 1 — assume a role in the target account.** The caller's identity policy allows `sts:AssumeRole` on the target role; the target's trust policy names the caller. Add conditions:

```json
{
  "Effect": "Allow",
  "Principal": {"AWS": "arn:aws:iam::111122223333:role/orders-apply"},
  "Action": "sts:AssumeRole",
  "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-exampleorgid"}}
}
```

Naming the specific role is safer than naming the account root; `aws:PrincipalOrgID` adds a second barrier if a role name is ever reused by an account outside your organisation.

**Pattern 2 — a resource policy grants directly.** A bucket, queue or key can name a principal in another account. The caller's own identity policy must also allow the action. For shared artefact buckets use an organisation condition rather than a list of account IDs that must be updated for every new account:

```json
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": ["s3:GetObject"],
  "Resource": "arn:aws:s3:::example-shared-artifacts/*",
  "Condition": {"StringEquals": {"aws:PrincipalOrgID": "o-exampleorgid"}}
}
```

`Principal: "*"` is acceptable here only because the condition narrows it to your organisation; reviewers must see the condition before approving.

**Choosing between patterns.** Use *assume role* when the caller needs a **broad, audited, time-limited identity** in the target (deployments, operations). Use *resource policies* when a **narrow data path** is wanted without an identity switch (reading a shared artefact, delivering logs). Mixing them blurs the audit trail: with a role, CloudTrail in the target account shows the assumed role; with a resource policy, the caller's own account holds the best record of who initiated it.

**Debugging cross-account denials:** check four things in order: caller's identity policy; target trust or resource policy; ceilings in *both* accounts (organisation policies, boundaries); and conditions (MFA, organisation ID, source). Remember encryption keys have their own policy: a cross-account object may be readable on the bucket and unreadable because the key policy does not allow the caller.

## Network segmentation

Segment by **sensitivity and function**, using layers that fail differently.

| Layer | Control | What it protects against |
| --- | --- | --- |
| Account | Separate account per environment and sensitivity | Credential compromise, quota exhaustion, blast radius |
| VPC | Separate VPC per environment; no default connectivity | Lateral movement across environments |
| Subnet tier | Public (edge only), private (workloads), data (no route to the internet) | Misrouted or accidental exposure |
| Security group | Reference groups, not CIDR ranges; no wide `0.0.0.0/0` | Lateral movement within a tier |
| Endpoint policy | Restrict what a private path may reach | Data exfiltration through a permitted path |
| Resource policy | Condition on `aws:SourceVpce` or organisation | Access from outside the intended network |

A typical three-tier layout per AZ, with subnets of `/20` from a `/16`:

```text
VPC 10.50.0.0/16 (orders-prod)
  public   10.50.0.0/20   (AZ a)  10.50.16.0/20 (AZ b)   load balancers, NAT gateways
  private  10.50.32.0/20  (AZ a)  10.50.48.0/20 (AZ b)   application tasks
  data     10.50.64.0/20  (AZ a)  10.50.80.0/20 (AZ b)   databases; route table has only `local` and endpoints
```

The data tier's route table has no internet route at all: even if a security group were opened by mistake, there is no path out or in. That is **defence in depth**: two independent mistakes would be needed.

**Security group design rules.**

- One group per *role* of resource (load balancer, application, database), named for the role.
- Ingress from other groups, not from CIDR blocks, except the load balancer's public listener.
- Outbound rules are an explicit decision: unrestricted egress is the default and often unjustified for a database.
- No rule is created without a description that names the purpose and owner.
- Review for `0.0.0.0/0` and `::/0` on anything other than a public listener; also review the IPv6 side, which is easily forgotten.

```bash
# Find open ingress to the world (illustrative audit query)
aws ec2 describe-security-groups \
  --query "SecurityGroups[?IpPermissions[?IpRanges[?CidrIp=='0.0.0.0/0']]].[GroupId,GroupName]" \
  --output table
```

**Network security design**

| Layer | Control |
| --- | --- |
| Perimeter | Load balancer with TLS; web application firewall for HTTP workloads |
| Subnet | Public only for edge components; private for workloads and data |
| Instance or task | Security groups referencing other groups |
| Egress | NAT with restrictions, or private endpoints to managed services |
| Data | Encryption at rest and in transit, private endpoints, no public databases |
| Observability | Flow logs and load-balancer logs to a protected location |

## Egress control

Inbound exposure gets attention; **outbound** is where exfiltration and supply-chain callbacks happen. Decide egress per tier.

| Tier | Typical egress need | Control |
| --- | --- | --- |
| Public (load balancer) | Reach targets inside the VPC | Security group to the application group only |
| Application | Image registry, logs, secrets, a few third-party APIs | Endpoints for AWS services; NAT plus allow-listing for the rest |
| Data | Nothing | No internet route; endpoints only if required |

Options for outbound internet access from private subnets:

| Option | Strength | Weakness |
| --- | --- | --- |
| NAT gateway, open egress | Simple | No filtering; any destination |
| NAT with security-group port limits | Cheap, coarse | Controls ports, not destinations |
| NAT plus DNS filtering | Blocks known-bad names | Does not stop connections by raw IP |
| Egress proxy or inspection firewall | Allow-list by name or inspection | Cost, latency, an operated component |

**Endpoints are both a cost and a security control.** A gateway endpoint for object storage keeps that traffic off NAT and can carry a policy limiting which buckets are reachable; an interface endpoint does the same for other services. An endpoint policy that permits only your organisation's buckets blunts exfiltration to an attacker's bucket:

```json
{
  "Statement": [{
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": "*",
    "Condition": {"StringEquals": {"aws:ResourceOrgID": "o-exampleorgid"}}
  }]
}
```

**[Version-sensitive]** Available condition keys for endpoint policies differ by service and have expanded over time; check support for the keys you plan to use, and test that a bucket outside the organisation is actually refused.

**NAT resilience.** A NAT gateway is zonal. One NAT serving all AZs is cheaper but couples egress to one AZ and adds cross-AZ data charges for other zones. The professional pattern for production is one NAT per AZ, with each private route table pointing to its own zone's NAT; for non-production, accept one and state the risk.

## Logging and audit

You cannot investigate what you did not record. Minimum evidence set:

| Source | Records | Notes |
| --- | --- | --- |
| Control-plane audit trail (CloudTrail) | Every API call: who, what, when, from where | Enable an **organisation-wide** trail to a central, protected store |
| Network flow logs | Accepted and rejected flows per interface | Cost scales with traffic; choose scope and fields deliberately |
| Load-balancer access logs | Requests, status, latency | Needed to separate network from application failures |
| Configuration history | Resource configuration over time | Answers "what did this look like on Tuesday?" |
| Application logs | Application behaviour | Do not log secrets or full tokens |

**Make logs trustworthy.** Deliver them to a **separate log-archive account** that workload administrators cannot write to or delete from; enable integrity validation on the audit trail; restrict deletion with object lock or equivalent; encrypt with a key whose policy the workload account cannot change; alert on any attempt to stop logging.

```json
{
  "Effect": "Deny",
  "Action": ["cloudtrail:StopLogging", "cloudtrail:DeleteTrail", "cloudtrail:UpdateTrail"],
  "Resource": "*"
}
```

Attached as an organisation guardrail, this denies disabling the trail in member accounts. (Exempt a single named administrative role only if you can justify it.) **[AWS-specific / Version-sensitive]** Management-event history is available in each account for a limited retention period without a trail; data events (object-level activity) and extended retention need extra configuration and cost.

**Audit questions your logs must answer.** Who assumed this role and from which identity? When was this security group changed, and by what pipeline run? Which principal called this API from an unexpected network? Did anyone disable logging? Test the questions: run a quarterly drill where someone makes a benign change and an auditor reconstructs it from logs alone.

**Session names as a feature.** Setting a meaningful session name (user or pipeline run ID) at role assumption makes that reconstruction possible. A fleet of sessions named `session` makes the audit trail useless.

## Guardrails

A **guardrail** limits what can be done *regardless of what individual policies grant*. At the organisation level these are service control policies, which set the ceiling for member accounts; at the account level, permission boundaries; at the resource level, block-public-access switches and encryption defaults.

| Guardrail | Effect | Class |
| --- | --- | --- |
| Deny leaving or disabling audit logging | Protects evidence | Preventive |
| Deny use of unapproved Regions | Shrinks the attack and billing surface | Preventive |
| Deny creating access keys for human users | Pushes people to federation | Preventive |
| Block public access on object storage, account-wide | Stops accidental exposure | Preventive |
| Require tags at resource creation | Makes cost attribution reliable | Preventive |
| Detect publicly reachable resources and unused credentials | Finds what slipped through | Detective |
| Alert on use of the break-glass role | Makes emergency use visible | Detective |

A **tag-on-create** guardrail, which requires the `project` tag when creating a service:

```json
{
  "Effect": "Deny",
  "Action": ["ecs:CreateService", "ec2:RunInstances"],
  "Resource": "*",
  "Condition": {"Null": {"aws:RequestTag/project": "true"}}
}
```

**[AWS-specific / Version-sensitive]** Only some actions and services support tag-on-create conditions, and a few services require extra permissions to tag at creation. Test each guarded action, because a guardrail that denies a legitimate path with an unclear message becomes a source of workarounds.

**Roll out guardrails safely.** (1) Detect first: write the rule as a detective control and count violations. (2) Fix existing violations or document exceptions. (3) Apply the preventive control to a test organisational unit. (4) Promote gradually. (5) Keep a tested path to remove a guardrail quickly. A guardrail that locks out the deployment pipeline during an incident teaches the organisation to distrust guardrails.

**Guardrails do not replace review.** They stop classes of mistake; they do not judge whether a design is right. Pair them with design review and with the written decisions described below.

## Cost-aware infrastructure

Estimating cost **before** building is part of design. A model has four parts:

| Cost driver | Billed by | Example factors |
| --- | --- | --- |
| Compute | Time × size | Task CPU/memory, count, hours per month |
| Network appliances | Hours + data processed | Load balancer capacity units, NAT hours and GB, endpoints |
| Data transfer | GB | Out to the internet, between AZs, between Regions |
| Observability and storage | Ingestion, retention, requests | Log ingestion, metrics, snapshots |

**A worked estimate (illustrative rates; replace with current pricing).** Assume 730 hours per month, a NAT gateway at an illustrative 0.045 per hour plus 0.045 per GB processed, an interface endpoint at 0.01 per hour per AZ plus 0.01 per GB, and a gateway endpoint at no charge.

- **Design A — NAT only.** Two NAT gateways: 2 × 730 × 0.045 = 65.70. Data: 400 GB of image and package traffic × 0.045 = 18.00. Total about 83.70 per month.
- **Design B — NAT plus endpoints.** Keep two NAT gateways (65.70). Add a free gateway endpoint for object storage (most image layers come from it) and interface endpoints for two registry and logging APIs in two AZs: 2 × 2 × 730 × 0.01 = 29.20. Suppose the endpoints take 350 of the 400 GB away from NAT: NAT data 50 × 0.045 = 2.25; endpoint data 350 × 0.01 = 3.50. Total about 100.65 per month.

At this volume, the endpoints **cost more**; at 5 TB per month the arithmetic reverses (NAT data 5,000 × 0.045 = 225.00 versus a few tens of dollars through endpoints). The professional conclusion is not "always use endpoints" but "**compute the break-even and revisit when volume changes**". There may be security reasons for endpoints regardless of cost; if so, say that reason in the decision record.

**Hidden multipliers to model explicitly.**

- **Cross-AZ traffic**: load balancer to a target in another AZ, replication, and application chatter between zones.
- **Log ingestion**: verbose debug logging in production can cost more than the compute it describes.
- **NAT data processing**: container image pulls on every start, package downloads, telemetry.
- **Idle resources**: load balancers, NAT gateways, unattached volumes and addresses.

**Controls in operation.**

| Control | What it does | Limit |
| --- | --- | --- |
| Budget with alert | Warns at thresholds | Does not stop spend; lags billing |
| Budget action | Applies a restrictive policy automatically at a threshold | Needs careful design to avoid breaking production |
| Anomaly detection | Flags unusual spend patterns | Needs tuning; still after the fact |
| Tag-on-create enforcement | Makes attribution possible | Not all resources are taggable |
| Schedule for non-production | Stops compute outside working hours | Needs wake-up and state handling |
| Lifecycle rules | Expires logs, snapshots and images | Must respect audit retention |

Make teardown documented and **tested**; a teardown that leaves orphaned volumes and addresses is a standing charge.

## Justified policy decisions

Every non-obvious allow, deny or exception should have a short written justification that a future maintainer can evaluate. A lightweight record:

```text
Decision:    Allow orders-apply to update ECS services in orders-prod, scoped by resource ARN and tag.
Context:     Pipeline deploys on merge; humans have read-only access.
Risk:        A compromised pipeline can deploy arbitrary images to this service.
Mitigations: OIDC with branch-and-environment conditions; image digest allow-list; deploy audit alarm;
             boundary forbids IAM mutation.
Rejected:    Wildcard ecs:* on * (blast radius); long-lived deployment keys (leak risk).
Cost:        Pipeline cannot touch other services; new services need a policy change (review time).
Review:      Quarterly, or on any change to the pipeline's trust conditions.
Owner:       platform-team
```

Notice the pattern: *what we allow, what could go wrong, what limits it, what we turned down and why, who owns it, and when it is reviewed.* If you cannot fill in the "rejected" line you have not considered alternatives.

**Exceptions.** An exception is a decision with an expiry. Record scope, reason, compensating control, owner and end date. Exceptions without end dates become the policy.

## Evidence of control

Keep these artefacts and refresh them when infrastructure changes:

- **Identity baseline**: principals (human, workload, pipeline), their roles, and evidence of allowed and denied actions.
- **Network baseline**: identifiers taken from infrastructure outputs, not typed by hand.
- **Services map**: which service talks to which, on what port, through which control.
- **Budget and cost model**: current estimate and last review.
- **Audit-reconstruction drill**: the date and result.
- **Decision records** and the exception register.

A claim without evidence is a risk; "pending apply" is an honest status.

## Professional trade-offs

| Axis | One end | Other end | How to decide |
| --- | --- | --- | --- |
| Many accounts vs few | Strong isolation, overhead | Simplicity, shared blast radius | Isolation where compromise cost is high |
| Strict egress vs developer speed | Allow-list | Open | Strict for data and production tiers |
| NAT per AZ vs shared | Resilience | Lower cost | Production: per AZ; lab: shared, documented |
| Endpoints vs NAT | Private, controllable | Lower fixed cost at low volume | Break-even and security needs |
| Guardrail strictness vs flexibility | Deny by default | Detect only | Preventive for high-impact, detective for the rest |
| Fine-grained roles vs maintenance | Smaller blast radius | Fewer policies | Fine for production deploy paths |
| Log everything vs cost | Better forensics | Lower bill | Full audit logs; sampled or short-retention for noisy sources |

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Demo or operate daily | Limited operator role with MFA | Standing administrator |
| Allow a service to call an API | Task or instance role with specific actions | Long-lived access keys in environment variables |
| CI deploys | OIDC federation with branch conditions | Stored keys in CI variables |
| Cross-account deployment | Assume a named role with conditions | Trusting the whole account root unconditionally |
| Expose a service | Load balancer open; application group only from the load balancer | `0.0.0.0/0` on application or SSH |
| Private access to AWS services | Endpoints with policies | Open NAT for everything |
| Debug AccessDenied | Layer-by-layer check, simulator, logs | Adding `*` until it works |
| Protect audit evidence | Separate log account, immutable storage | Logs in the same account that admins control |
| Keep a bill small | Budget first, idle policy, tested teardown | Always-on NAT in a lab |

## Knowledge consolidation

- Design for **least authority, containment, accountability and affordability**; use preventive, detective and corrective controls together.
- **Humans** federate through single sign-on; **workloads** use platform roles; **pipelines** use OIDC with repository, branch and environment conditions.
- Separate roles for **read, plan, apply, audit and break-glass**; test the break-glass path.
- **Boundaries** cap delegated administrators, but only if creation of roles *requires* the boundary.
- **Cross-account** access uses assumed roles for broad audited identities and resource policies for narrow data paths; add organisation conditions.
- **Segment** by account, VPC, tier, security group and endpoint policy; the data tier should have no internet route at all.
- **Egress** deserves as much design as ingress; endpoints are both cost and security controls.
- **Logs** must be centralised, protected from the people they record, and tested by reconstruction drills.
- **Guardrails** set ceilings; roll them out detect-first and keep an escape route.
- **Model cost before building**; compute break-evens; watch cross-AZ, log and NAT multipliers.
- **Write the decision**: allowed, risked, limited, rejected, owned, reviewed.

## Exercises

**Exercise 1 — Role design.** For the `orders` service, write five roles (readonly, plan, apply, audit, break-glass) with trust policy, permission summary and the single most dangerous permission each holds. Explain what happens if the plan role is compromised versus the apply role.

**Exercise 2 — Pipeline trust.** Write an OIDC trust policy for one repository's main branch. List three ways the condition could be mistakenly widened and test, in a lab, that a different repository and a different branch are refused.

**Exercise 3 — Cross-account.** Design access so a deployment account can update services in a production account and a log archive receives logs from both. For each path, choose assume-role or resource policy and justify. List the policies each account needs.

**Exercise 4 — Segmentation review.** Given a VPC with a database in a public subnet reachable only through a security group, redesign it with tiers. State which two independent mistakes would be needed to expose the database after your change.

**Exercise 5 — Egress audit.** For a private application tier, list every outbound destination (use flow logs). Classify each as AWS service, third party or unknown. Propose endpoints or allow-lists for each and note what you would block.

**Exercise 6 — Guardrail rollout.** Choose one guardrail (Region restriction or tag-on-create). Write the detective version, the preventive version, the test plan, the escape route, and the communication to teams.

**Exercise 7 — Cost model.** Estimate monthly cost for the VPC edge in two designs (one NAT, NAT per AZ plus endpoints) using current pricing. Compute the break-even traffic for endpoints and state your decision.

**Exercise 8 — Decision record.** Write a decision record for one non-obvious policy in your lab, including a "rejected" alternative and a review date.

**Solution notes.**

*Exercise 1.* A good answer pairs each role with a trust condition (who and under what context) and names the dangerous permission (for the plan role: broad read access to configuration that may reveal secrets; for the apply role: the ability to deploy arbitrary images). A compromised plan role should reveal information but not change the environment; a compromised apply role can deploy code, which is why its trust is restricted to the protected branch and why deployments are alarmed.

*Exercise 2.* Ways to widen by mistake include a `StringLike` pattern of `repo:example-org/*`, omitting the `sub` condition, and allowing any `ref` when only `main` was intended. The refusal tests should return an assume-role denial; if they succeed, the condition does not apply as you thought.

*Exercise 3.* A typical answer: deployment uses assume-role into a named production role (broad, audited, time-limited); log delivery uses a resource policy on the archive bucket with an organisation condition (narrow data path); both need key-policy permissions if the logs are encrypted.

*Exercise 4.* After moving the database to a data subnet with no internet route, exposure would need both a route to an internet gateway added to its subnet *and* a security group opened to the world (plus a public address). Name those independent mistakes and the detective control that would find each.

*Exercise 5.* Expect surprises: telemetry endpoints, package mirrors and image pulls. Unknown destinations should be investigated before blocking; recording them as an exception with an owner is a valid interim step.

*Exercise 6.* The detective version is a query or rule that lists violations; the preventive version is a policy attached first to a test organisational unit. The escape route is a named role or a documented procedure to detach the policy. Teams should be told the exact error they will see.

*Exercise 7.* Results depend on current prices and your traffic; the deliverable is the formula, the break-even and the stated reason. If security requirements drive the choice, say so rather than disguising it as cost.

*Exercise 8.* Check the record includes the mitigation list, a rejected alternative that is genuinely different, an owner and a review date that is in the future.
