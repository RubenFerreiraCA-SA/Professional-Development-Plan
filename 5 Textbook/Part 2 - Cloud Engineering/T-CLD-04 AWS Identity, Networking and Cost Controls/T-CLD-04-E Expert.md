# T-CLD-04-E — Expert Depth

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-e"></a>
#### T-CLD-04-E — Expert Depth

**Identity architecture at scale.** Federate workforce identity from a central provider; map groups to permission sets per account; issue credentials of minutes to hours; and log every assumption of a role. For workloads outside the provider, use workload identity federation (OpenID Connect) with conditions on repository, branch and environment rather than shared secrets. Design a break-glass path whose use triggers alerts and automatic review.

**Privilege-escalation paths in IAM.** Principals that can create or modify policies, pass roles to services (`iam:PassRole`), update role trust policies, attach policies to themselves, create access keys for others or start compute with a privileged role can often escalate to administrator. Review these permissions as a class. Test with simulation and with dedicated analysis tooling, and restrict `PassRole` to named roles and services.

**Cross-account and resource-policy complexity.** Trust policies, resource policies, endpoint policies, service control policies and permission boundaries compose. Document the effective permission for critical paths and test them as code (policy tests in CI). Be wary of confused-deputy problems: when a service acts on your behalf, require conditions such as `aws:SourceArn` and `aws:SourceAccount`.

**Network design trade-offs**

| Choice | Benefit | Cost or risk |
| --- | --- | --- |
| Private subnets with NAT | No inbound exposure | NAT hourly and per-GB cost; single point of failure per AZ unless duplicated |
| Gateway or interface endpoints | Private path, lower NAT use | Endpoint cost, policy management |
| Transit gateway or peering | Hub-and-spoke connectivity | Complexity, route and CIDR planning, cost per attachment and GB |
| Shared VPC | Central control | Blast radius, ownership boundaries |
| Inspection firewalls | Central egress control | Latency, throughput limits, operational load |

Plan CIDR allocation across the whole organisation early; overlapping ranges prevent later connectivity.

**Cost forensics.** When a bill spikes: break down by service, usage type and tag; look at data-transfer lines; check for abandoned resources, runaway logs or an unexpectedly scaled service; correlate with deployment events. Prevent recurrence with a guardrail (quota, budget action, policy), not a memo.

**Failure modes**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Leaked access key | Key in source or logs | Short-lived credentials, secret scanning, rotation |
| Overbroad role | Wildcards copied from examples | Access analysis, boundaries, review |
| Accidentally public resource | Misconfigured policy or SG | Organisation-level deny, detective rules |
| Cost runaway | Autoscaling without caps, log floods | Quotas, budgets with actions, alerts |
| Lockout | Overly strict deny or lost MFA | Tested break-glass, staged policy rollout |

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

**Confused deputy, shown.** A third-party analytics service assumes a role in your account to read logs. Another customer of that service learns your role ARN and asks the service to read *your* logs on *their* behalf; the service holds valid access, so it succeeds. The fix is a condition that binds the trust to the right customer:

```json
{"Effect":"Allow","Principal":{"Service":"logs-analytics.example.com"},"Action":"sts:AssumeRole",
 "Condition":{"StringEquals":{"sts:ExternalId":"acct-7f3a91"},
              "ArnLike":{"aws:SourceArn":"arn:aws:analytics:eu-west-1:111122223333:*"}}}
```

For AWS service principals, use `aws:SourceArn` and `aws:SourceAccount`; for third parties, an external ID unique per customer.

**Detecting a role that gained more permissions than intended.** Compare the permissions a role *can* use against what it *did* use: access analysis tools report unused services and actions; CloudTrail shows `AttachRolePolicy`/`PutRolePolicy` events; a daily export of effective policies is diffed against the approved baseline in version control; alerts fire when a change touches IAM outside the pipeline. The preventive layer is a service control policy denying IAM mutation except by the infrastructure pipeline role.

**A non-overlapping CIDR plan for fifty accounts across three regions.**

```text
Organisation supernet:          10.0.0.0/8  (never use a smaller range, or you will run out)
Reserve:                        10.192.0.0/10   acquisitions / future
Region eu-west-1:               10.0.0.0/11     (2,097,152 addresses)
Region us-east-1:               10.32.0.0/11
Region ap-southeast-1:          10.64.0.0/11
Remaining:                      10.96.0.0/11 spare;  10.128.0.0/10 spare
Per account (within region):    /16 blocks  -> 10.0.0.0/16, 10.1.0.0/16 ... (each /11 holds 32 such /16s)
Per VPC:                        /16 split into /20 subnets per AZ and tier (public, private, data)
Registry:                       a single source of truth (IPAM service or a Git file) with an automated overlap check in CI
```

Fifty accounts across three regions means about 17 per region, which fits easily into 32 /16s. Verify with a script (`python3 -c 'import ipaddress; …'`) that no two allocations overlap and check on every change. Avoid ranges commonly used on-premises or by VPNs (`192.168.0.0/16` and `10.0.0.0/24` in home networks) because they conflict with remote access.

**Cost forensics, worked.** A bill rises 40% overnight. Steps: break down by service (data transfer and NAT often surprise), then usage type (for example `NatGateway-Bytes` or `DataTransfer-Out-Bytes`), then by tag or account, then by resource ID. Suppose NAT bytes rose 20×: find which instance or task moved large volumes through NAT (flow logs show the top talkers), and discover a new job pulling container images from the public registry on every start. The fix is a guardrail: add a gateway or interface endpoint, set a pull-through cache, and add a budget action or anomaly alert at a threshold. Record the cost per resolved cause so reviewers see the pattern, not an anecdote.

**Risk ranking for a design.**

| Risk | Likelihood | Impact | Rank | Control and owner |
| --- | --- | --- | --- | --- |
| Overbroad CI deployment role | Medium | High (account takeover) | 1 | Scope role, `PassRole` restriction; platform |
| Public storage exposure | Low with org policy; Medium without | High | 2 | SCP deny; detective rule |
| NAT or data-transfer cost runaway | Medium | Medium | 3 | Endpoints, budget alerts; service team |
| Lockout after policy change | Low | High | 4 | Tested break-glass; staged rollout |

Rank by likelihood × impact and revisit when a control is tested, not when it is configured.

**Mentoring prompts.** Explain `iam:PassRole` and why it is dangerous. How would you detect that a role has been granted more permissions than its owners intended? Design a CIDR plan for fifty accounts across three regions that will never overlap and can accommodate acquisitions.

---
