# T-CLD-04-B — Beginner Foundations

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-b"></a>
#### T-CLD-04-B — Beginner Foundations

## Why this matters

A cloud account is a shared, internet-connected machine room that bills you by the second. Three questions decide whether your first experience of it is pleasant or painful. **Who is allowed to do what?** (identity and permissions). **Who can talk to what?** (network reachability). **What will it cost?** (spend visibility). Most beginner disasters are answers to one of these that nobody wrote down: an administrator key pasted into a public repository, a database reachable from the whole internet, a forgotten load balancer billing for a month.

This section builds the vocabulary and the first habits for Amazon Web Services (AWS). It assumes you can use a terminal and understand basic networking ideas (an IP address, a port, a firewall). It does not assume prior cloud experience. The examples use a fictional `orders` service and placeholder account IDs such as `111122223333`; replace them with your own, and never paste real identifiers into shared notes.

Two ideas run through the whole chapter and are worth stating now:

1. **Permission and reachability are different questions.** A person can be *permitted* to call an API and still be unable to reach the service because of the network. A server can be *reachable* on the network and still reject every request because the caller has no permission. When something fails, first decide which of the two kinds of failure you are looking at.
2. **Every control has a cost and a failure message.** Learn to read both.

**Markers used in this chapter.** Text tagged **[AWS-specific]** describes behaviour of this provider that other providers name or implement differently. Text tagged **[Version-sensitive]** describes console screens, default settings, limits, prices or CLI output that change over time; check current AWS documentation before relying on them. Outputs marked *illustrative* show the expected shape, not measured results.

## First principles: accounts, Regions and the shared-responsibility line

An **AWS account** is the basic container for resources and the boundary for billing. A **Region** (for example `eu-west-1`) is a geographic cluster of data centres; most resources live in exactly one Region, and you pay and are limited per Region. Inside a Region, **Availability Zones (AZs)** are separate facilities with independent power and networking. A resource in `eu-west-1a` and one in `eu-west-1b` can survive different failures.

Identity is **global within an account**; networks are **regional**; costs are **account-wide** but reported by Region and service.

The **shared-responsibility model** in one line: AWS secures the facilities and managed-service software; you secure what you configure (permissions, open ports, encryption, leftover resources).

> **[AWS-specific]** Other providers use different words (subscription, project, tenancy) for the account-like boundary and different names for the same ideas below. The concepts transfer; the nouns do not.

## IAM vocabulary

IAM (Identity and Access Management) is the service that answers "who is this, and may they do that?"

| Term | Meaning | Beginner mental model |
| --- | --- | --- |
| Principal | An identity making a request (person, role session, service) | The "who" in a request |
| Policy | A JSON document that allows or denies actions on resources | The rulebook |
| Action | One API operation, written `service:Operation` | A verb, such as `ecs:DescribeServices` |
| Resource | The thing an action applies to, named by an ARN | The noun |
| Role | An identity assumed temporarily, with its own permissions | A uniform you borrow for a while |
| User | A long-lived identity (prefer single sign-on and roles) | A permanent badge; easy to lose |
| MFA | A second authentication factor | A second lock on the door |
| STS | The service that issues temporary credentials | The desk that issues visitor passes |
| ARN | Amazon Resource Name, a unique identifier | A postal address for any object |

An ARN has a fixed shape:

```text
arn:aws:ecs:eu-west-1:111122223333:service/orders/orders-api
 |   |   |       |          |            |
 |   |   |       |          |            +-- resource type and name
 |   |   |       |          +--------------- account ID
 |   |   |       +-------------------------- Region (blank for global services)
 |   |   +---------------------------------- service
 |   +-------------------------------------- partition (aws, or aws-cn / aws-us-gov)
 +------------------------------------------ literal "arn"
```

You will read ARNs constantly: in policies, in error messages and in logs. The account ID segment in an error message tells you immediately whether you are looking at your account or somebody else's.

**Who am I?** The first command to run after configuring any profile:

```bash
aws sts get-caller-identity --profile demo
```

Illustrative output:

```json
{
  "UserId": "AROAEXAMPLEID:alice",
  "Account": "111122223333",
  "Arn": "arn:aws:sts::111122223333:assumed-role/ops-readonly/alice"
}
```

If the returned ARN is not the identity you expected, stop and fix credentials before doing anything else. Running a destructive command with the wrong profile is one of the most common beginner incidents, and this one command prevents it.

## Reading a policy line by line

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ecs:DescribeServices", "logs:GetLogEvents"],
    "Resource": "*"
  }]
}
```

- `Version` is the policy language version. The value `2012-10-17` is the current one and is required for modern features; copy it exactly.
- `Statement` is a list; each entry is an independent rule.
- `Effect` is `Allow` or `Deny`.
- `Action` is the API operations covered. Wildcards (`ecs:Describe*`) match families of operations.
- `Resource` is what the rule applies to. `"*"` means every resource, which is acceptable for read-only listing and a warning sign elsewhere.

By default everything is denied. An explicit deny always wins over any allow.

**Identity-based versus resource-based policies.** The policy above is *identity-based*: attached to a user or role. Some services also support *resource-based* policies attached to the thing being accessed (a bucket, a queue, a key); these name a `Principal`. A request can fail although your own policy looks right because the resource's policy has the final say about outsiders.

**Never use the root user for daily work.** The root user is the identity created with the account and has unrestricted power that no policy can reduce. Give it a strong unique password and MFA, create no access keys for it, and use it only for the small number of account-level tasks that require it (for example closing the account or changing the support plan).

## Users, roles and temporary credentials

A role has no password and no permanent key. A person or a service *assumes* it, and STS issues credentials that expire. Long-lived access keys are easy to leak (in a repository, a chat message, a screenshot) and hard to rotate across many places, which is why people use single sign-on and services use roles.

The ARN shape from `get-caller-identity` tells you which kind of identity you hold:

```text
arn:aws:iam::111122223333:user/alice                         # long-lived user
arn:aws:sts::111122223333:assumed-role/ops-readonly/alice    # temporary role session
arn:aws:iam::111122223333:root                               # root: stop!
```

A role has two separate documents, and mixing them up is the classic beginner confusion:

| Document | Question it answers | Attached to |
| --- | --- | --- |
| Trust policy | *Who may assume this role?* | The role itself |
| Permission policy | *What may a session of this role do?* | The role (as identity policies) |

A role with generous permissions that anyone can assume is dangerous; a role with a tight trust policy but no permissions is useless. You need both halves to be right.

**Single sign-on in practice.** Modern accounts give people access through a central identity provider rather than IAM users. The command-line workflow looks like this:

```bash
aws configure sso                       # one-time setup of a named profile
aws sso login --profile demo            # opens a browser; credentials last hours
aws sts get-caller-identity --profile demo
```

> **[AWS-specific / Version-sensitive]** AWS IAM Identity Center is the managed single-sign-on service; its menus, command names and session lengths change between releases. The principle (short-lived credentials obtained after interactive login) is stable.

## How a request is evaluated

AWS evaluates every API call against all applicable policies. The beginner rule has three steps: (1) everything starts as denied; (2) an `Allow` in an applicable policy grants the action; (3) any matching `Deny` overrides every `Allow`. So there are three outcomes: allowed, *implicitly* denied (no statement matched) and *explicitly* denied (a `Deny` matched).

**Worked example.** Consider two statements attached to an operator role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["ecs:Describe*", "ecs:List*", "logs:GetLogEvents"], "Resource": "*"},
    {"Effect": "Deny",  "Action": "ecs:StopTask", "Resource": "*"}
  ]
}
```

| Request | Outcome | Reason |
| --- | --- | --- |
| `ecs:DescribeServices` | Allowed | Matches the first `Allow`. |
| `ecs:ListTasks` | Allowed | Matches `ecs:List*`. |
| `ecs:StopTask` | Explicitly denied | The `Deny` wins even if some other policy allows it. |
| `ecs:UpdateService` | Implicitly denied | Nothing allows it. |
| `s3:GetObject` | Implicitly denied | Different service; no statement matches. |

A denied call returns an error such as `AccessDenied` or `UnauthorizedOperation` that names the principal and the action. Read it carefully: it tells you exactly which permission is missing.

Illustrative error:

```text
An error occurred (AccessDeniedException) when calling the UpdateService operation:
User: arn:aws:sts::111122223333:assumed-role/ops-readonly/alice is not authorized to
perform: ecs:UpdateService on resource: arn:aws:ecs:eu-west-1:111122223333:service/orders/orders-api
because no identity-based policy allows the ecs:UpdateService action
```

Parse it in four pieces: *who* (the assumed-role ARN), *what* (`ecs:UpdateService`), *on which resource* (the service ARN) and *why* (no identity-based policy allows it). The wording of the final clause is **[Version-sensitive]**: newer AWS services name the policy type that caused the denial (identity-based policy, service control policy, resource-based policy), while older ones return a shorter message. When the clause is missing, you must work out the cause yourself; the Intermediate section teaches how.

**The least-privilege habit.** Grant the smallest set of actions on the smallest set of resources that lets the job work. Each early denial is information about one more permission to consider and, if legitimate, to add deliberately. A broad administrator policy "to get started" almost never gets narrowed afterwards.

## Network basics in AWS

A **VPC** (Virtual Private Cloud) is your private network inside one Region, defined by an address range written in **CIDR** notation. **Subnets** divide the VPC's range and each lives in one AZ. An **internet gateway** (IGW) gives a subnet a path to and from the internet. A **security group** is a stateful allow-list firewall attached to a resource's network interface. A **load balancer** receives traffic and forwards it to healthy targets.

**Reading CIDR.** The number after the slash is how many leading bits are the *network* part. The rest are addresses you can hand out.

| CIDR | Addresses | Typical use |
| --- | --- | --- |
| `10.0.0.0/16` | 65,536 | A whole VPC |
| `10.0.1.0/24` | 256 | One subnet |
| `10.0.16.0/20` | 4,096 | A larger subnet (for example one tier in one AZ) |
| `10.0.1.0/28` | 16 | The smallest subnet AWS allows |

Quick arithmetic: addresses = 2^(32 − prefix). AWS reserves five addresses per subnet, so a `/24` provides 251 usable addresses. **[Version-sensitive]** VPC size limits (currently `/16` largest and `/28` smallest for IPv4) can change.

Ranges you choose for a VPC should come from the private address blocks `10.0.0.0/8`, `172.16.0.0/12` or `192.168.0.0/16`. Choose ranges that do not overlap with your office, your home router (often `192.168.0.0/24` or `192.168.1.0/24`) or other VPCs you may one day connect, because overlapping networks cannot be joined.

**How the pieces fit.**

```text
VPC 10.0.0.0/16
  ├─ public subnet A 10.0.1.0/24 (AZ a) ─┐  route 0.0.0.0/0 → internet gateway
  ├─ public subnet B 10.0.2.0/24 (AZ b) ─┤  hosts the load balancer
  └─ private subnets (tasks)             └  security group: allow 8000 from the load balancer's group only
```

A subnet is "public" because its **route table** sends `0.0.0.0/0` to an internet gateway, not because of its name. Every route table has an automatic `local` route so that anything inside the VPC can reach anything else inside the VPC at the network level; security groups then decide what is actually allowed.

A security group allows inbound traffic by rule, is **stateful** (replies to allowed traffic are automatically allowed) and can reference another security group as a source, which is more precise than a CIDR because it follows the members as they change address.

| Property | Security group |
| --- | --- |
| Where it applies | The network interface of a resource |
| Rule types | Allow only; there is no deny rule |
| Default | Inbound denied, outbound allowed |
| State | Stateful: replies are automatic |
| Source | CIDR or another security group |

To make a subnet *private* you do not add a rule; you simply leave out the route to the internet gateway. Resources there can still reach other things in the VPC.

## Permission versus reachability: two questions

This is the single most useful diagnostic idea of the chapter. Suppose you call a service and it fails. Place the failure in one of two worlds.

| Question | World | Typical symptom | Where to look |
| --- | --- | --- | --- |
| Is the caller *allowed*? | Identity and permissions | A prompt answer: `AccessDenied`, `403`, `UnauthorizedOperation` | Policies, trust, conditions |
| Can the caller *reach* it? | Network | A silence: timeout; or `connection refused`; or DNS failure | Routes, security groups, listener, name resolution |

The telling difference is **speed and wording**. An authorisation failure is a fast, explicit refusal that names the principal. A network failure is typically slow (the packet is dropped and you wait for a timeout) or a bare "connection refused". If you see a precise message naming your identity, the network worked: you reached the service and it said no. If you see a hang, your request probably never arrived, and no amount of policy editing will help.

A short test ladder for a load-balanced service:

```bash
# 1. Does the name resolve?
dig +short orders-lb-123456.eu-west-1.elb.amazonaws.com

# 2. Is the TCP port reachable?
nc -vz orders-lb-123456.eu-west-1.elb.amazonaws.com 443

# 3. Does HTTP respond, and with what status?
curl -sS -o /dev/null -w '%{http_code}\n' https://orders-lb-123456.eu-west-1.elb.amazonaws.com/health
```

Step 1 failing means a name problem; step 2 timing out suggests a route or security-group problem ("refused" means nothing is listening); step 3 returning `502` or `503` means you reached the load balancer but it has no healthy target.

## Cost first

A budget alert does not stop spending; it tells you. Create it before building, and give it a threshold well below your tolerance:

```bash
aws budgets create-budget --account-id <id> --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

Two important facts for beginners. First, **billing data lags**: charges appear hours after the usage, so an alert is an early warning, not a real-time brake. Second, **some resources bill by the hour whether or not they are used**: load balancers, NAT gateways, databases and unattached public IPv4 addresses are the usual culprits. Free or low-cost experiments become expensive when something is left running.

Also tag everything you create (`project=practice`, `owner=your-name`, `expires=2026-12-01`) so it can be found and deleted. **[AWS-specific]** Cost reports can only group by a tag after the tag key has been activated for cost allocation in the billing settings, and the data then appears after a delay, so activate your standard tag keys on day one.

> **[Version-sensitive]** Prices, free-tier terms and which resources bill by the hour change frequently. Treat any number in this chapter as an example, and check the current pricing page before estimating.

Before ending a session, list instances, load balancers, NAT gateways and unattached addresses in every Region you used (`aws ec2 describe-nat-gateways`, `aws elbv2 describe-load-balancers`, `aws ec2 describe-addresses`). The "wrong Region" is where forgotten resources hide.

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Using `AdministratorAccess` "just to get started" and never narrowing it | Everything works, including mistakes | Start from read-only, add one permission at a time |
| `"Action": "*"` or `"Resource": "*"` copied from an example | A tiny script can delete anything | Replace with named actions and ARNs |
| Wrong profile active in the shell | Resources appear in an unexpected account | Run `get-caller-identity` first, every session |
| Security group open to `0.0.0.0/0` on an administrative port to debug | Constant scanning in the logs; possible compromise | Open to a single trusted address briefly, or use a managed session tool; close it |
| Resources created in the wrong Region | "It was there yesterday" | Set the Region in the profile; check all Regions before ending |
| Access key committed to a repository | Alerts from the provider; unexpected usage | Revoke the key at once, then remove it from history; use roles instead |
| Public subnet used "because it works" for databases | Database reachable from the internet | Private subnet, security group allowing only the application group |

## Knowledge consolidation

- **Identity answers "who and what may they do"; the network answers "who can reach what".** Diagnose which one failed before changing anything.
- Everything is **denied by default**; an explicit `Deny` beats any `Allow`.
- A **role** is assumed for a short time and has a *trust policy* (who may assume it) and *permission policies* (what it may do). Prefer roles and single sign-on to long-lived keys.
- Run `aws sts get-caller-identity` before anything else; read ARNs for account, role and session.
- The **root user** is for rare account-level tasks, with MFA and no access keys.
- A **VPC** is regional, a **subnet** is zonal, and a subnet is public only if its route table sends `0.0.0.0/0` to an internet gateway.
- **Security groups** are stateful allow-lists; reference other security groups rather than wide CIDR ranges.
- A `/24` has 256 addresses and 251 usable; plan non-overlapping CIDR ranges early.
- A **budget** warns you; it does not stop spending. Create it first, tag everything, and tear down.
- Treat numbers, console screens and default limits as **version-sensitive**; the principles are stable.

## Exercises

**Exercise 1 — Operator identity.** Create an operator identity with permission only to list and describe resources, configure a profile, run `get-caller-identity`, then try an action it should not be allowed to do and read the `AccessDenied` message. Copy the message and label who, what, resource and reason.

**Exercise 2 — Policy reading.** For the worked policy, predict the outcome for `ecs:DescribeTasks`, `ecs:RunTask` and `ecs:StopTask`. Then add a second `Allow` for `ecs:StopTask` and predict again.

**Exercise 3 — CIDR practice.** For `10.20.0.0/16` write four non-overlapping `/24` subnets across two AZs. State how many usable addresses each has. Explain why `10.20.5.0/24` and `10.20.5.128/25` cannot both exist as subnets.

**Exercise 4 — Timeout or refusal?** Describe, in a table, what you would see and conclude for: an unresolved name; a TCP timeout; a TCP refusal; an HTTP `403`; an HTTP `503`. For each, name the layer (name resolution, route or firewall, listener, permission, target health).

**Exercise 5 — Budget and teardown.** Create a monthly budget with two thresholds, tag a test resource with `project=practice`, then write and run a teardown checklist for every Region you used.

**Solution notes.**

*Exercise 1.* Expect the allowed list/describe call to succeed and a mutating call to return an explicit message naming the assumed-role ARN, the action and the resource. If the wording lacks the "because…" clause, that is normal for some services; the first three parts are still enough to decide what permission would be needed. If the operator can do something you did not intend, look for an attached managed policy that is broader than you expected.

*Exercise 2.* `ecs:DescribeTasks` is allowed; `ecs:RunTask` is implicitly denied; `ecs:StopTask` is explicitly denied. A second `Allow` for `ecs:StopTask` does **not** change that: the `Deny` still wins.

*Exercise 3.* One valid answer: `10.20.1.0/24` and `10.20.2.0/24` in AZ a, `10.20.3.0/24` and `10.20.4.0/24` in AZ b, each with 251 usable addresses. `10.20.5.128/25` lies inside `10.20.5.0/24`, so the ranges overlap and a VPC will reject the second subnet.

*Exercise 4.* Unresolved name: name resolution. TCP timeout: route, security group or other filtering. TCP refusal: reachable, but nothing listening on that port. HTTP `403`: reached the service; permission or an application-level rule. HTTP `503`: reached the load balancer; no healthy target. Your table should name the layer for each; a difference in phrasing is fine.

*Exercise 5.* The budget should exist and the tag should be visible on the resource. If the tag does not yet appear in cost reports, that is normal until the tag key is activated for cost allocation and a delay passes. Your teardown checklist should include instances, load balancers, NAT gateways, addresses, volumes and snapshots in each Region you touched.
