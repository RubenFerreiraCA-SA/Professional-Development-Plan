# T-CLD-04-E — Expert Depth

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-e"></a>
#### T-CLD-04-E — Expert Depth

## Why this level exists

At Professional level each control was chosen and justified for one service. At scale the interesting problems are **interactions**. A guardrail set in one place silently blocks a pipeline in another. A role that is harmless alone becomes administrator when combined with a permission to pass it to a service. Two networks that each work perfectly cannot be connected because their address ranges overlap. A cost allocation scheme that is perfect for tagged resources hides a third of the bill in "unallocated". An exception granted for a launch is still in force three years later.

Expert practice is the discipline of **reasoning about composition**: how organisational policies, resource policies, trust policies, endpoint policies and boundaries combine; how many networks, regions and on-premises sites route to one another; how costs flow to the teams that cause them; and how failures actually unfold. The test of expertise is not knowing more settings; it is being able to say *where a given request will be stopped, who will find out, and what it costs everyone to keep it that way*.

This section assumes Beginner, Intermediate and Professional material. Account IDs (`111122223333`, `444455556666`), organisation IDs, Regions and names are placeholders.

**Markers.** **[AWS-specific]** marks behaviour particular to this provider. **[Version-sensitive]** marks limits, defaults, prices, feature availability and message wording that change; verify before relying on them. Outputs and figures marked *illustrative* demonstrate shape and arithmetic, not measurement.

## Organisation boundaries

### The organisation as a tree of ceilings

An **organisation** groups accounts into **organisational units (OUs)**. Policies attached to the root, an OU or an account apply to everything below. Service control policies (SCPs) do **not grant** permissions; they define the maximum. Effective maximum for an account is the **intersection** of the policies along the path from the root to the account.

```text
Root                                   SCP: FullAWSAccess (default allow) + deny-region + deny-audit-tamper
├─ Security OU                         SCP: protect log archive and security tooling
│    ├─ log-archive
│    └─ security-tooling
├─ Infrastructure OU                   SCP: allow networking and shared services
│    ├─ network-hub
│    └─ shared-services
├─ Workloads OU
│    ├─ Prod OU                        SCP: deny changes outside pipeline roles; deny public exposure
│    │    └─ orders-prod
│    └─ NonProd OU                     SCP: deny expensive instance families; allow broader experimentation
│         └─ orders-dev
├─ Sandbox OU                          SCP: strict budget-linked limits; deny leaving the organisation
└─ Exceptions OU                       Accounts with documented, expiring deviations
```

Design principles for the tree:

- **Organise by policy needs, not by org chart.** Team reorganisations are frequent; the need for "production is stricter than development" persists. Put accounts where the ceiling should be the same.
- **Use few SCPs, attached high.** Debugging gets harder with each layer. Prefer a small number of understandable policies at the root and OU level to many per-account exceptions.
- **Keep the management account nearly empty.** SCPs do **not** apply to it, so any workload there is outside your guardrails. It should hold organisation control and billing and little else.
- **Delegate administration** of security and networking services to member accounts so the management account is rarely used.

> **[AWS-specific / Version-sensitive]** SCP details that matter in practice: they do not affect service-linked roles; they do affect the root user of member accounts; there are limits on policy size and on the number of policies per target; and an allow must exist at **every** level of the path (the default `FullAWSAccess` provides it). Newer resource-oriented policy types extend this approach to resource access and to certain service defaults. Limits and policy types evolve, so verify them in current documentation and re-test guardrails after changes.

### Allow-list and deny-list strategy

| Strategy | How it works | Strength | Cost |
| --- | --- | --- | --- |
| Deny-list | Keep default allow; deny specific dangerous actions | Easy to roll out; new services work | New risky services are allowed until you notice |
| Allow-list | Remove default allow; permit named services only | Strong containment | New services need a policy change; inheritance requires allow at every level |

A deny-list at the root with an allow-list in sensitive OUs is a common compromise.

### Guardrails as code, tested

An SCP that cannot be tested is a hazard. Treat the organisation's policies as software:

```text
policies/
  root/deny-region.json
  root/deny-audit-tamper.json
  prod/deny-nonpipeline-change.json
tests/
  cases.yaml        # expected decision per (principal, action, resource, context)
```

```yaml
# illustrative test case format
- name: pipeline may update the service in prod
  principal: arn:aws:iam::444455556666:role/orders-apply
  action: ecs:UpdateService
  expect: allowed
- name: human administrator may not stop logging
  principal: arn:aws:iam::444455556666:role/Admin
  action: cloudtrail:StopLogging
  expect: denied
- name: non-approved region denied
  principal: arn:aws:iam::444455556666:role/orders-apply
  action: ec2:RunInstances
  context: {aws:RequestedRegion: ap-south-1}
  expect: denied
```

CI runs these through a policy evaluation tool, then a **sandbox account** under the same OU path tests the real behaviour before promotion. The simulator alone is not enough: **check what your evaluation tooling includes** (organisation policies, boundaries, resource policies, context keys). A deny you can simulate but not observe is a hypothesis.

**Failure of the guardrail itself.** The most expensive guardrail failure is a policy that blocks the credentials needed to remove it. Mitigation: exempt a named, alarmed administrative role at the root using a condition on `aws:PrincipalArn`, store its use under split custody, and never attach a new SCP to the root without first attaching to a test OU.

### Delegated administration and the management account

Some organisation-wide services (audit analysis, threat detection, configuration aggregation, network management) can be administered from a designated member account. Delegating:

1. keeps the management account out of daily use;
2. limits who holds the broadest rights;
3. puts security tooling in an account governed by the Security OU.

The break-glass path to the management account must exist and be rehearsed, because it is the only identity above the guardrails.

## Complex IAM: escalation, trust chains and attributes

### Identity architecture at scale

Federate workforce identity from a central provider; map groups to permission sets per account; issue credentials of minutes to hours; and log every assumption of a role. For workloads outside the provider, use workload identity federation (OpenID Connect) with conditions on repository, branch and environment rather than shared secrets. Design a break-glass path whose use triggers alerts and automatic review.

At scale two forms of drift matter: **permission-set drift** (a role in one account differs from the template) and **group sprawl** (a group that nobody can explain). Counter with periodic reconciliation: generate the expected state from source control and diff it against the real state, and require a named owner on every group.

### Privilege-escalation paths in IAM

Principals that can create or modify policies, pass roles to services (`iam:PassRole`), update role trust policies, attach policies to themselves, create access keys for others or start compute with a privileged role can often escalate to administrator. Review these permissions as a class. Test with simulation and with dedicated analysis tooling, and restrict `PassRole` to named roles and services.

**A privilege-escalation path, step by step.** Consider a role `ci-deployer` allowed:

```json
{"Effect":"Allow","Action":["iam:PassRole","lambda:CreateFunction","lambda:InvokeFunction"],"Resource":"*"}
```

If any role in the account has broad permissions (for example `admin-role` trusted by Lambda), `ci-deployer` can create a function, pass `admin-role` to it, invoke it and act as administrator through the function's code. The user never held administrator rights directly. The fix is to restrict what may be passed and to whom:

```json
{"Effect":"Allow","Action":"iam:PassRole",
 "Resource":"arn:aws:iam::111122223333:role/orders-lambda-exec",
 "Condition":{"StringEquals":{"iam:PassedToService":"lambda.amazonaws.com"}}}
```

| Permission class | Why it escalates | Control |
| --- | --- | --- |
| `iam:PassRole` unrestricted | Run services with a stronger role | Name roles; add `iam:PassedToService` |
| `iam:CreatePolicyVersion`, `AttachRolePolicy`, `PutRolePolicy` | Rewrite own or others' permissions | Deny for non-IAM administrators; permission boundaries |
| `iam:UpdateAssumeRolePolicy` | Make a strong role assumable by yourself | Restrict; alert on change |
| `iam:CreateAccessKey` for other users | Impersonate them | Restrict to self; prefer no long-lived keys |
| `sts:AssumeRole` on `*` | Reach any role whose trust allows you | Narrow resources; review trust policies |
| Compute creation with an instance profile (`ec2:RunInstances` + `PassRole`) | Code on a host with a privileged role | Restrict profiles; guard metadata access |
| `iam:SetDefaultPolicyVersion` | Switch to an older, broader version of a policy | Restrict; keep few versions |
| Write access to a bucket holding deployment templates | Change what the pipeline deploys | Treat the artefact store as part of the trust boundary |

**Indirect escalation.** Escalation is not only IAM. Write access to anything that a more privileged principal **executes or trusts** is an escalation path: a build script run by the pipeline, a function triggered by an event the attacker controls, an image the deployment role pulls, a parameter that configures a privileged job. Draw the graph: *who can write what, and who runs it?* Edges, not nodes, are the risk.

**Finding paths systematically.** (1) Enumerate principals and their effective permissions; (2) mark "dangerous" actions; (3) build a directed graph where an edge means "can obtain the identity of"; (4) search for paths from low-privilege principals to high ones. Dedicated analysis tools do this; your job is to verify results and fix the root cause, not to acknowledge every finding.

### Trust chains and role chaining

When role A assumes role B, which assumes role C, you have a **chain**. Each hop applies its own trust policy and its own session policy. Concerns: the chain's **maximum session duration** is capped, which breaks long jobs; **auditing** requires correlating events across sessions through the session names and source identity; and the **blast radius** is the union of reachable roles. Keep chains short (hub-and-spoke, not mesh), and use **source identity** or consistent session names so one person's actions are traceable across hops.

> **[AWS-specific / Version-sensitive]** Session durations, chaining caps and the availability of source identity and session-tag features vary by service and change over time.

### Attribute-based access control (ABAC)

Instead of one policy per team, use tags on **principals** and **resources** and a single policy that compares them:

```json
{
  "Effect": "Allow",
  "Action": ["ecs:UpdateService", "ecs:DescribeServices"],
  "Resource": "*",
  "Condition": {"StringEquals": {"aws:ResourceTag/team": "${aws:PrincipalTag/team}"}}
}
```

A person tagged `team=orders` may update only services tagged `team=orders`. Benefits: fewer policies, automatic scaling with new resources. Risks: **tags become security controls**, so the ability to *change* tags is the ability to change access. Therefore: restrict who can tag and untag (`aws:TagKeys`, `aws:RequestTag`), protect the access-control tag keys with a guardrail, prevent principals from modifying their own tags, and audit tag changes. ABAC without tag governance is an escalation path with a friendly name.

### Cross-account and resource-policy complexity

Trust policies, resource policies, endpoint policies, service control policies and permission boundaries compose. Document the effective permission for critical paths and test them as code (policy tests in CI). Consider a read of an encrypted object from another account:

| Layer | Must permit |
| --- | --- |
| Caller's organisation ceiling | The action |
| Caller's boundary and session policy | The action |
| Caller's identity policy | Read on the object and decrypt with the key |
| Network path | VPC endpoint policy allows the bucket |
| Bucket policy | The caller or organisation |
| Key policy | The caller (or delegates to IAM in the key's account) |
| Target organisation ceiling (where applicable) | Access by outside or inside principals |

Seven independent places can each say no. A runbook that lists them in order saves hours, and a **negative test** (a principal that must be refused) is as important as a positive one.

**Confused deputy, shown.** A third-party analytics service assumes a role in your account to read logs. Another customer of that service learns your role ARN and asks the service to read *your* logs on *their* behalf; the service holds valid access, so it succeeds. The fix is a condition that binds the trust to the right customer:

```json
{"Effect":"Allow","Principal":{"Service":"logs-analytics.example.com"},"Action":"sts:AssumeRole",
 "Condition":{"StringEquals":{"sts:ExternalId":"acct-7f3a91"},
              "ArnLike":{"aws:SourceArn":"arn:aws:analytics:eu-west-1:111122223333:*"}}}
```

For AWS service principals, use `aws:SourceArn` and `aws:SourceAccount`; for third parties, an external ID unique per customer and not guessable. The principle: **when a service acts on your behalf, the resource must verify on whose behalf it acts.**

### Detecting a role that gained more permissions than intended

Compare the permissions a role *can* use against what it *did* use: access analysis tools report unused services and actions; CloudTrail shows `AttachRolePolicy`/`PutRolePolicy` events; a daily export of effective policies is diffed against the approved baseline in version control; alerts fire when a change touches IAM outside the pipeline. The preventive layer is a service control policy denying IAM mutation except by the infrastructure pipeline role.

```json
{
  "Effect": "Deny",
  "Action": ["iam:Put*Policy", "iam:Attach*Policy", "iam:Create*Policy*", "iam:UpdateAssumeRolePolicy", "iam:Delete*Policy*"],
  "Resource": "*",
  "Condition": {"ArnNotLike": {"aws:PrincipalArn": "arn:aws:iam::*:role/org-iam-pipeline"}}
}
```

Watch for wildcards that match more than you intend (`iam:Create*Policy*` also matches policy-version actions, which is desired here but should be confirmed), and for actions that a service performs on its own behalf through service-linked roles, which SCPs do not constrain.

## Multi-VPC networking

### Connectivity options

| Option | Model | Strengths | Limits and costs |
| --- | --- | --- | --- |
| VPC peering | One-to-one link | Simple, no hourly charge for the link, low latency | **Non-transitive**; no overlapping CIDR; mesh grows as n(n−1)/2; no edge-to-edge routing through a peer |
| Transit gateway | Regional hub with route tables | Transitive routing, central policy, scales to many VPCs and on-premises | Per-attachment hourly cost and per-GB; route-table design is the work |
| Private service endpoints (PrivateLink) | Consume one service privately | No routing between networks; works with overlapping CIDR; fine-grained exposure | Per-AZ endpoint cost; one service at a time; DNS design |
| Shared VPC subnets | Several accounts in one network | Central control, no cross-VPC traffic cost | Blast radius, ownership and quota boundaries, noisy-neighbour risk |
| Inter-Region links | Transit or peering across Regions | Disaster recovery, global footprint | Latency, per-GB cost, static routes may be required |

A rule of thumb that holds up: **use PrivateLink when you want to expose a service, routing when you want to join networks.** Joining networks creates a surface of everything-to-everything unless route tables and security groups say otherwise; exposing one service creates a surface of one port.

### Transit gateway as a segmentation tool

A transit gateway has **attachments** (VPCs, VPNs, links), **route tables**, **associations** (which table an attachment uses to *send*) and **propagations** (which table learns an attachment's CIDR so others can *reach* it). Segmentation is by table:

```text
Route table "prod":       learns prod VPCs + shared-services;           does NOT learn non-prod
Route table "nonprod":    learns non-prod VPCs + shared-services;       does NOT learn prod
Route table "shared":     learns every VPC (so shared services can answer everyone)
Attachment associations:  prod VPCs → prod;  non-prod VPCs → nonprod;  shared-services → shared
```

Prod and non-prod cannot route to one another even though both attach to the same hub. Test the **negative**: from a non-prod host, attempt a connection to a prod address and confirm it fails at routing, not merely at a security group. A route that exists but is blocked by a security group is one mistake from an incident.

**Centralised egress and inspection.** A hub VPC holding NAT and an inspection layer can serve every spoke:

```text
spoke VPC → transit gateway → egress VPC (inspection firewall → NAT gateway) → internet
```

Benefits: one place for egress policy and logging; fewer NAT gateways. Costs and hazards: all egress traffic pays per-GB charges at the transit gateway *and* at NAT; the inspection layer is a throughput bottleneck and a single point of failure per AZ; and **symmetric routing** is mandatory because stateful firewalls drop flows whose return path differs. **[AWS-specific]** Transit gateways have an *appliance mode* attachment setting that keeps both directions of a flow in the same AZ for an inspection VPC; leaving it off is a classic cause of intermittent drops that appear only for cross-AZ flows.

### Address planning

Overlapping ranges prevent later connectivity, so plan CIDR allocation across the whole organisation early, before the first VPC is built.

```text
Organisation supernet:      10.0.0.0/8
Reserve (acquisitions):     10.192.0.0/10      keep empty until needed
Region eu-west-1:           10.0.0.0/11        (2,097,152 addresses)
Region us-east-1:           10.32.0.0/11
Region ap-southeast-1:      10.64.0.0/11
Spare:                      10.96.0.0/11, 10.128.0.0/10
Per account (in region):    /16 blocks → 10.0.0.0/16, 10.1.0.0/16 … (each /11 holds 32 such /16s)
Per VPC:                    /16 split into /20 subnets per AZ and tier (public, private, data)
Registry:                   one source of truth (an IP address management service or a version-controlled file)
                            with an automated overlap check in CI
```

Fifty accounts across three Regions is about 17 per Region, which fits comfortably into 32 `/16` blocks. Verify with a script rather than by eye:

```bash
python3 - <<'PY'
import ipaddress, itertools
allocs = ["10.0.0.0/16", "10.1.0.0/16", "10.32.0.0/16", "10.64.0.0/16"]
nets = [ipaddress.ip_network(a) for a in allocs]
bad = [(a, b) for a, b in itertools.combinations(nets, 2) if a.overlaps(b)]
print("overlaps:", bad or "none")
PY
```

Avoid ranges commonly used on-premises or by VPNs (`192.168.0.0/16` and `10.0.0.0/24` in home networks) because they conflict with remote access. When an overlap already exists (an acquisition), your options are: renumber (cleanest, hardest), translate with NAT between the networks (works, breaks end-to-end identity and complicates logs), or **expose services through PrivateLink**, which does not require routing and therefore tolerates overlap.

**[Version-sensitive]** VPCs can have secondary CIDR blocks and now support very large IPv6 allocations; IPv6 reduces the planning problem but adds its own: security groups and route tables need an IPv6 side, and "egress-only" gateways replace NAT for outbound-only access.

### DNS in a multi-VPC world

Name resolution fails more quietly than routing. Questions to settle in the design: which private hosted zones are associated with which VPCs; how a name in one account's zone resolves from another account's VPC (zone association across accounts); how endpoint DNS names resolve to private addresses (the private-DNS setting on interface endpoints); and what happens when two VPCs define the same name. Decide **who owns the namespace** (for example one central zone per environment) and automate the associations.

## Hybrid networking

### Connecting to on-premises sites

| Option | Path | Properties | Considerations |
| --- | --- | --- | --- |
| Site-to-site VPN | Encrypted tunnels over the internet | Quick, inexpensive, two tunnels per connection for resilience | Bandwidth limits per tunnel (**[Version-sensitive]**), variable latency, dependent on the internet |
| Dedicated private link (Direct Connect) | Physical or partner circuit | Consistent latency and bandwidth, lower data-transfer cost | Lead time, cost, **not encrypted by default**, needs redundancy at two levels (circuits and locations) |
| Both | Private link primary, VPN backup | Resilient | Must test failover; route preference through BGP attributes |

**Routing mechanics.** Dynamic routing exchanges prefixes through BGP. Facts that matter: the more specific prefix wins; among equal prefixes, the local preference and path length decide; what you *advertise* on-premises is what they can reach, so advertise only what is needed; and **route limits** on the on-premises or cloud side can silently drop prefixes beyond a ceiling. Document the expected prefix set for each connection and alarm when it changes.

**Failure behaviours worth rehearsing.** (1) *Primary link fails*: do sessions fail over within the applications' tolerance? (2) *Both fail*: which services can run without on-premises, and which cannot? (3) *Asymmetric return*: traffic goes out over one path and returns over another, and a stateful firewall drops it. (4) *Overlap with the on-premises range*: some sites use the same private ranges as your VPCs. Plan for these before the first migration, not after.

**Hybrid DNS.** On-premises systems must resolve cloud names and cloud systems must resolve on-premises names. Managed resolver endpoints provide an inbound path (on-premises asks the cloud) and an outbound path (cloud asks on-premises) with forwarding rules. A frequent failure is a forwarding loop or a missing rule for a newly created private zone.

**Symptom: "small requests work, large ones hang."** The usual cause is an MTU mismatch combined with blocked path-MTU discovery, common on tunnels and encapsulated paths. Verify with progressively larger don't-fragment pings and adjust MSS clamping on the tunnel. **[Version-sensitive]** Supported MTU values differ by connection type; check current values.

```bash
# illustrative: find the largest unfragmented payload toward an on-premises host
ping -M do -s 1372 10.200.0.15
ping -M do -s 1472 10.200.0.15
```

**Security of the extended perimeter.** A hybrid link joins trust domains. Treat the on-premises network as **less trusted than your VPC data tier** by default: security groups should name specific on-premises prefixes and ports, not "everything from the corporate range". A compromise of an office laptop should not be a route to the database subnet.

## Enterprise cost allocation

### From invoice to team

An enterprise needs to answer, per team, product and environment: *what did it cost, why did it change, and what is the unit cost?* Four mechanisms combine:

| Mechanism | Allocates by | Strength | Weakness |
| --- | --- | --- | --- |
| Account structure | The account that incurred it | Unambiguous, free | Only as fine as your account design |
| Cost-allocation tags | Tag values on resources | Fine-grained | Needs coverage, discipline and activation; some costs untaggable |
| Cost categories / grouping rules | Rules over accounts, tags, services | Business-friendly views without changing resources | Rules must be maintained |
| Usage-level cost data export | Line items by resource and usage type | The raw material for everything else | Large; needs a query engine and modelling |

**Taxonomy.** Keep it small and governed: `product`, `team`, `environment`, `cost-centre`, `data-classification`. Define allowed values (an enumerated list), who may create new ones and how they are enforced. A tag taxonomy with fifty keys and free-text values yields fifty ways to be wrong.

**Coverage as a metric.** Measure **percentage of cost with valid allocation** per month, and report it by team. Set a target (for example above 95%) and give each team the list of its untagged resources. Remediate by enforcing tag-on-create for new resources, scheduled reconciliation for old ones, and *an explicit owner for the residue*.

### Shared costs

Some costs are not caused by one team: networking hubs, shared logging, the security tooling, the inspection firewall, support, enterprise discounts. Allocation methods:

| Method | How | Fairness | Complexity |
| --- | --- | --- | --- |
| Fixed split | Equal share among consumers | Crude | Low |
| Proportional to direct spend | Share follows each team's own spend | Reasonable default | Medium |
| Proportional to a usage driver | GB through the hub, number of attachments, log volume | Best incentive | High (needs a metric per shared service) |
| Central budget | Platform team absorbs | Simple; hides the cost | Low, but removes feedback |

A defensible approach: allocate shared costs **by the driver that most plausibly causes them** where that is measurable (for example NAT and transit GB by traffic per VPC), and fall back to proportional-to-spend otherwise. Publish the method; allocation disputes are cheaper to resolve before the first invoice than after.

**Discounts and commitments.** Commitment discounts (savings plans or reserved capacity) are bought centrally and apply across accounts according to rules. Decide whether benefits are shown to the team that benefited or pooled, because the answer changes the apparent unit cost of a service and therefore decisions. **[AWS-specific / Version-sensitive]** Sharing rules, discount types, term options and reporting views change; confirm current behaviour before building a chargeback model on them.

### Showback, chargeback and unit economics

- **Showback**: show teams their costs without billing them internally. Cheap to start, effective when teams care and leaders review.
- **Chargeback**: transfer cost to the team's budget. Stronger incentive; requires accuracy and a dispute process, otherwise it breeds tag-gaming.

The most useful number is the **unit cost**: cost per order, per thousand requests, per active user. A bill that rises 20% while traffic rises 40% is good news that raw spend hides. Pair the cost export with a business metric by month.

```text
Unit cost report (illustrative)
Month    Orders served    Direct cost    Allocated shared    Cost per 1,000 orders
2026-08  1,200,000        4,800          1,150               4.96
2026-09  1,500,000        5,300          1,300               4.40
```

### Cost forensics, worked

A bill rises 40% overnight. Steps: break down by service (data transfer and NAT often surprise), then usage type (for example `NatGateway-Bytes` or `DataTransfer-Out-Bytes`), then by tag or account, then by resource ID. Suppose NAT bytes rose 20×: find which instance or task moved large volumes through NAT (flow logs show the top talkers), and discover a new job pulling container images from the public registry on every start. The fix is a guardrail: add a gateway or interface endpoint, set a pull-through cache, and add a budget action or anomaly alert at a threshold. Record the cost per resolved cause so reviewers see the pattern, not an anecdote.

When the cause is not visible at account level, use a two-axis method: (1) **which dimension moved** (service, usage type, account, Region, tag) and (2) **what changed in the environment at that time** (deployments, new accounts, new integrations, scaling events). Billing data lags, so correlate with the deployment log and with flow or access logs, which are timely.

## Exceptions

An organisation without exceptions is either very small or not telling the truth. The goal is to make exceptions **visible, bounded and expiring**.

**Exception register fields.**

| Field | Example |
| --- | --- |
| Identifier | EXC-2026-014 |
| Control relaxed | Region guardrail: allow `ap-south-1` |
| Scope | Account `orders-data-eu`, role `orders-analytics` only |
| Reason | Data-residency partner requires processing in that Region |
| Compensating controls | Flow logs, budget cap, no internet egress |
| Approver and owner | Named people, not teams |
| Expiry | Date; renewal requires a new review |
| Detection | How we would notice use beyond the scope |

**Lifecycle.** Request → risk review → time-boxed approval → implementation *as code* (so it appears in version control) → monitoring → renewal or removal. Send reminders to the owner before expiry; **default to removal** if nobody renews. A register that is not wired to automation is a document that drifts.

**Where to place exceptions structurally.** Prefer an **Exceptions OU** or a narrowly scoped condition on a named principal over editing the shared policy. An edit to the root policy weakens the control for everyone; a scoped exception weakens it for one scope and is easy to find and remove.

**Break-glass is an exception with an alarm.** Its use should page someone and produce a review. Track frequency: frequent break-glass use means a guardrail is mis-designed or a routine task lacks a safe path.

## Failure patterns

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Leaked access key | Key in source or logs | Short-lived credentials, secret scanning, rotation |
| Overbroad role | Wildcards copied from examples | Access analysis, boundaries, review |
| Accidentally public resource | Misconfigured policy or SG | Organisation-level deny, detective rules |
| Cost runaway | Autoscaling without caps, log floods | Quotas, budgets with actions, alerts |
| Lockout | Overly strict deny or lost MFA | Tested break-glass, staged policy rollout |
| Guardrail locks out the pipeline | Deny without exemption for the deployment role | Exempt named role, test OU first |
| Overlapping CIDR | Late acquisition or ad hoc ranges | Registry, CI overlap check, PrivateLink fallback |
| Asymmetric inspection | Firewall sees only one direction | Symmetric routing, appliance mode |
| Tag-based access bypass | Principals can edit the tags that grant access | Guard tag keys, restrict `TagResource` |
| Log loss | Logs in the same account as the compromised role | Separate archive account, immutability |
| Silent route-limit drop | Prefix limit exceeded on a hybrid link | Alarm on prefix counts, summarise routes |
| Orphaned exception | Expired approval still in force | Expiry in code, default to removal |

**Case catalogue.**

*Case 1 — The deployer that could become administrator.* A pipeline role held `PassRole` on `*` and permission to create functions. A security review's graph analysis found a path to an administrator role. Fix: named roles, `iam:PassedToService`, boundary on the pipeline, and an alert on `CreateFunction` outside the pipeline. Lesson: reason about *combinations*, not single permissions.

*Case 2 — The guardrail that stopped the fix.* During an incident the team needed to detach a bad policy, but a new organisation policy denied IAM changes to everyone except a pipeline that was itself broken. Recovery required the management account's break-glass path. Fix: exempt a named, alarmed emergency role; stage SCPs through a test OU; rehearse removal.

*Case 3 — The NAT that nobody modelled.* A new batch job pulled several terabytes each night through NAT, adding a large monthly charge. Flow logs showed the job as top talker. Fix: a gateway endpoint for object storage, a registry cache, and a unit-cost dashboard that made the change visible within days instead of at invoice.

*Case 4 — The acquisition with the same ranges.* An acquired company used `10.0.0.0/16`, as did a production VPC. Renumbering was months of work. Short-term: expose three services through PrivateLink; medium-term: renumber the acquired network into the reserve block. Lesson: the reserve range exists for exactly this.

*Case 5 — The intermittent drops.* After centralising egress, some connections reset only when targets were in a different AZ. Cause: inspection appliance mode was off, so return traffic took a different AZ than the request. Fix: enable appliance mode for the inspection attachment and add a cross-AZ test to the change checklist.

## Risk ranking for a design

| Risk | Likelihood | Impact | Rank | Control and owner |
| --- | --- | --- | --- | --- |
| Overbroad CI deployment role | Medium | High (account takeover) | 1 | Scope role, `PassRole` restriction; platform |
| Public storage exposure | Low with org policy; Medium without | High | 2 | SCP deny; detective rule |
| NAT or data-transfer cost runaway | Medium | Medium | 3 | Endpoints, budget alerts; service team |
| Lockout after policy change | Low | High | 4 | Tested break-glass, staged rollout |

Rank by likelihood × impact and revisit when a control is tested, not when it is configured.

## Expert trade-offs

| Axis | One end | Other end | How an expert decides |
| --- | --- | --- | --- |
| Many accounts vs operational overhead | Strong isolation | Fewer things to manage | Automate account vending; isolate where compromise cost is high |
| Allow-list vs deny-list organisation policy | Containment | Agility | Allow-list for sensitive OUs, deny-list elsewhere |
| ABAC vs explicit role per team | Scales with tags | Auditable by reading policies | ABAC where tag governance is strong; roles where it is not |
| Transit hub vs PrivateLink | Everything routable | One service exposed | Join networks only when everything-to-everything is intended |
| Central egress vs local NAT | One control point | Fault isolation, lower transit cost | Central where inspection is required; local elsewhere |
| Chargeback vs showback | Incentive | Low friction | Chargeback only with trustworthy allocation |
| Encryption on private links vs performance | Confidentiality | Throughput | Encrypt links crossing shared facilities; document where you do not |
| Exceptions vs uniformity | Delivery | Consistency | Time-boxed, scoped, owned, automated expiry |

A useful expert habit is to **write the sentence before choosing**: "We accept *cost* to reduce *specific risk*, and we will know it failed when *observable signal*." If you cannot complete that sentence, the control is cargo cult.

## Knowledge consolidation

- The organisation is a **tree of ceilings**; effective permission is the intersection of every ceiling and the union of grants. SCPs do not grant, do not constrain the management account, and need an allow at every level.
- **Test guardrails as code** and never apply one to the root without a test OU and an exempt emergency path.
- **Escalation lives in combinations and in edges** (who can write what a stronger principal runs). `PassRole`, trust-policy edits and policy-version actions are the classic classes.
- **ABAC** turns tags into security controls; govern tagging as strictly as policy.
- **Cross-account reads** pass through many independent layers, including keys and endpoints; write the list down and test the negatives.
- Use **PrivateLink to expose** a service and **routing to join** networks; use transit route tables for segmentation and test that forbidden paths fail at routing.
- **Plan addresses for the whole organisation** with a registry, an overlap check and a reserve block; PrivateLink is the fallback for overlap.
- **Hybrid links** need redundancy at two levels, route and prefix monitoring, symmetric paths, hybrid DNS and MTU awareness.
- **Cost allocation** combines accounts, governed tags, rules and exports; measure coverage; allocate shared costs by driver; report unit cost.
- **Exceptions** are scoped, owned, monitored and expiring; place them structurally outside the shared policy.
- Every control has a cost and a failure signal; state both.

## Exercises

**Exercise 1 — Organisation design.** Design an OU tree for an organisation with production, non-production, a data-science group with relaxed limits, and an acquisition in progress. For each OU, state the SCP ceiling, who administers it and one guardrail you would not apply at the root, with the reason.

**Exercise 2 — Guardrail tests.** Write ten test cases (five allowed, five denied) for an organisation policy that restricts Regions and protects audit logging. Include one case that tests the emergency exemption and one that tests a global service.

**Exercise 3 — Escalation graph.** Given these roles: `ci-deployer` (PassRole `*`, CreateFunction), `lambda-admin` (trusted by Lambda, administrator), `readonly` (read everything, `sts:AssumeRole` on `*`), `build-runner` (write to an artefact bucket), `deploy-job` (reads the artefact bucket and applies templates as administrator). Draw the graph and list every escalation path to administrator. For each, name the control that removes it.

**Exercise 4 — ABAC safety.** Write an ABAC policy for team-scoped service updates and a second policy that protects the `team` tag from tampering. Show a sequence by which a user could escape the scope if the second policy were missing.

**Exercise 5 — Transit design.** Design transit route tables for prod, non-prod, shared services and an inspection VPC. State associations and propagations and the negative test for prod ↔ non-prod. Explain what changes if shared services need to reach both.

**Exercise 6 — Overlap response.** An acquired network uses `10.0.0.0/16`, as does your VPC. Provide three options with costs and risks, recommend one for each of the next 30 days and 12 months, and describe how you will verify no new overlaps appear.

**Exercise 7 — Hybrid failure drill.** Document expected behaviour for loss of a primary private link, loss of both links, and an asymmetric return path. For each, state the evidence you would collect and the decision a responder makes.

**Exercise 8 — Allocation model.** Given a monthly bill with 22% untagged cost, 12% shared networking and a commitment discount, design the allocation: coverage target, remediation plan, shared-cost driver, discount treatment and a unit-cost metric. State what you would not allocate and why.

**Exercise 9 — Exception lifecycle.** Write an exception record for allowing one extra Region for one role. Include compensating controls, the detection that would show out-of-scope use, the expiry mechanism in code and what happens if the owner leaves the company.

**Solution notes.**

*Exercise 1.* Strong answers attach few policies high and keep the acquisition in a segregated OU with a restrictive network posture until its identity and logging match standards. Relaxed limits for data science belong in a scoped OU or account, not at the root. Marks go for naming the *reason* a guardrail is not global (for example a Region deny at the root is fine; a deny on a service data science needs belongs lower).

*Exercise 2.* Cases should include: pipeline role performing an allowed action in an approved Region (allowed); the same role in a non-approved Region (denied); stopping the audit trail by an ordinary admin (denied); the emergency role stopping it (allowed but alarmed); an identity or organisation-management call in any Region (allowed, as a global service). If your global-service case is denied, your exemption list is wrong.

*Exercise 3.* Paths: `ci-deployer` → create a function with `lambda-admin` → administrator; `build-runner` → poison the artefact bucket → `deploy-job` applies it as administrator; `readonly` → `sts:AssumeRole` on `*` → any role whose trust names the account. Controls: named `PassRole` with `iam:PassedToService`; separate write and read trust for artefacts with integrity checks and review on the deploy job; narrow `AssumeRole` resources and review trust policies. The second path is the one most often missed because no IAM permission is involved.

*Exercise 4.* Without tag protection, a user with `TagResource` can tag a service `team=orders` (or change their own principal tag, where permitted) and then update it. The protecting policy denies changing the `team` tag except by an administrative role and denies principals modifying their own tags. Verify with a negative test.

*Exercise 5.* A typical solution: prod and non-prod attachments associate with separate tables; each propagates into the shared table and learns the shared-services CIDR; the inspection VPC association is for egress. If shared services must reach both, the shared table learns both, but prod and non-prod tables still do not learn each other. The negative test is a failed connection from non-prod to prod that fails at routing (no route) rather than at a security group.

*Exercise 6.* Options: renumber, NAT between, PrivateLink. 30 days: PrivateLink for the few required services; 12 months: renumber into the reserve. Verification is the registry plus an automated overlap check on every VPC creation. Note that NAT breaks identity and logging and should be a last resort.

*Exercise 7.* Primary loss: failover within application tolerance; evidence is BGP session state and path latency. Both lost: a list of services that continue (cloud-only) and those that fail; decision is the incident declaration and degrade plan. Asymmetric return: connections reset or hang for some flows; evidence is flow logs on both sides; decision is the routing preference change.

*Exercise 8.* Look for a coverage metric, remediation by tag-on-create plus reconciliation, a shared-cost driver (traffic or attachments) with a proportional fallback, an explicit statement on how commitment benefits are shown, and a unit-cost metric tied to a business measure. Items you may choose not to allocate (support, enterprise-wide tooling) should be listed with an owner.

*Exercise 9.* The record should have a scoped condition on a named principal, compensating controls (flow logs, budget cap), detection (an alert when the exception's Region is used by any other principal), expiry enforced by automation that removes the exception by default, and an ownership transfer step. If it relies on a person remembering, it fails the exercise.

## Mentoring prompts

Explain `iam:PassRole` and why it is dangerous. How would you detect that a role has been granted more permissions than its owners intended? Design a CIDR plan for fifty accounts across three regions that will never overlap and can accommodate acquisitions. Why can an SCP both be correct and still cause an outage, and what would you do before attaching one to the root? A team says "our tags are our access control": what do you ask them next? When would you refuse to put two networks on the same transit gateway? How would you explain to a finance leader why 22% of the bill is unallocated and what it will cost to fix? Pick one exception in your organisation and say what its expiry mechanism is.

---
