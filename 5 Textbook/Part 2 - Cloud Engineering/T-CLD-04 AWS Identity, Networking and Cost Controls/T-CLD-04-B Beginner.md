# T-CLD-04-B — Beginner Foundations

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-b"></a>
#### T-CLD-04-B — Beginner Foundations

**IAM vocabulary**

| Term | Meaning |
| --- | --- |
| Principal | An identity making a request (user, role, service) |
| Policy | A JSON document that allows or denies actions on resources |
| Role | An identity assumed temporarily, with its own permissions |
| User | A long-lived identity (prefer single sign-on and roles) |
| MFA | A second authentication factor |
| STS | Service that issues temporary credentials |

**Who am I?** The first command to run after configuring any profile:

```bash
aws sts get-caller-identity --profile demo
```

If the returned ARN is not the identity you expected, stop and fix credentials before doing anything else.

**A policy, read line by line**

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

`Effect` allows or denies; `Action` is the API operations; `Resource` is what they apply to. By default everything is denied; an explicit deny always wins.

**Never use the root user for daily work.** Give it MFA, no access keys, and use it only for account recovery tasks.

**Network basics in AWS.** A *VPC* is your private network with an address range (CIDR). *Subnets* divide it across AZs. An *internet gateway* gives public subnets a route to the internet. A *security group* is a stateful allow-list firewall on a resource. A *load balancer* receives traffic and forwards it to healthy targets.

**Cost first.** Create a budget with an email alert before building a network:

```bash
aws budgets create-budget --account-id <id> --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

**How a request is evaluated.** AWS evaluates every API call against all applicable policies. The beginner rule has three steps: (1) everything starts as denied; (2) an `Allow` in an applicable policy grants the action; (3) any matching `Deny` overrides every `Allow`. So there are three outcomes: allowed, *implicitly* denied (no statement matched) and *explicitly* denied (a `Deny` matched).

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

**Roles, users and temporary credentials.** A role has no password or permanent key. A person or service *assumes* it and STS issues credentials that expire. Long-lived access keys are easy to leak and hard to rotate, which is why people use single sign-on and services use roles. Check the ARN shape from `get-caller-identity`:

```text
arn:aws:iam::111122223333:user/alice                         # long-lived user
arn:aws:sts::111122223333:assumed-role/ops-readonly/alice    # temporary role session
arn:aws:iam::111122223333:root                               # root: stop!
```

```bash
aws configure list-profiles
aws sts get-caller-identity --profile demo
aws ecs list-clusters --profile demo          # allowed?
aws ecs stop-task --cluster orders --task x --profile demo   # expect AccessDenied
```

**How the network pieces fit.**

```text
VPC 10.0.0.0/16
  ├─ public subnet A 10.0.1.0/24 (AZ a) ─┐  route 0.0.0.0/0 → internet gateway
  ├─ public subnet B 10.0.2.0/24 (AZ b) ─┤  hosts the load balancer
  └─ private subnets (tasks)             └  security group: allow 8000 from the load balancer's group only
```

A subnet is "public" because its route table sends `0.0.0.0/0` to an internet gateway, not because of its name. A security group allows inbound traffic by rule, is stateful (replies are automatically allowed) and can reference another security group as a source, which is more precise than a CIDR. The `/16` and `/24` notation says how many bits are the network part: `/24` gives 256 addresses (AWS reserves five per subnet).

**Cost control first.** A budget alert does not stop spending; it tells you. Create it before building, and give it a threshold well below your tolerance. Also tag everything you create (`project=practice`) so it can be found and deleted.

**Common mistakes**

- Using `AdministratorAccess` "just to get started" and never narrowing it.
- Using `"Action": "*"` or `"Resource": "*"` without noticing.
- Confusing the profile you meant with the one the shell is using; always run `get-caller-identity`.
- Opening a security group to `0.0.0.0/0` on an administrative port to debug a connection problem.
- Creating resources in the wrong Region and then not finding them.

**Exercise.** Create an operator identity with permission only to list and describe resources, configure a profile, run `get-caller-identity`, then try an action it should not be allowed to do and read the `AccessDenied` message.
