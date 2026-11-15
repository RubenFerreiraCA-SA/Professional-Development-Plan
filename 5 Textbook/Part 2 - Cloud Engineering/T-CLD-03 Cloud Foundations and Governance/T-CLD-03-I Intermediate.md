# T-CLD-03-I — Intermediate Practice

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-i"></a>
#### T-CLD-03-I — Intermediate Practice

## Why this matters

At Beginner level you learned what the cloud is and how to keep a single training account safe by hand. Real work quickly outgrows that. There are several people, several environments, a bill that someone must explain each month, an auditor who asks who changed what, and a growing list of resources nobody remembers creating. A foundation that lived in one person's head stops working the day a second person joins.

Intermediate practice turns the Beginner checklist into **documented, repeatable decisions**: how accounts are laid out, how identity is bootstrapped without long-lived keys, how budgets and alerts are wired to a person who will act on them, which guardrails stop the worst mistakes, how audit logs are kept safe, how tags make ownership visible, how those pieces combine into a small landing zone, and how everything is torn down again. This section assumes the Beginner material: shared responsibility, regions and zones, metering, root versus daily identity.

The running example is the same fictional `orders-api` service, now with a development and a production environment and three engineers. Examples use neutral terms, with provider-specific names in parentheses where they help you search documentation. Policy snippets, commands and figures are **illustrative**; verify syntax and prices against your provider's current documentation.

## First principles: a foundation is a set of boundaries

A cloud *foundation* is whatever exists before the first workload and that every workload inherits. It does four jobs:

| Job | Question it answers | Mechanism |
| --- | --- | --- |
| Separate | What can one mistake or one compromise reach? | Account (subscription, project) boundaries |
| Authenticate and authorise | Who may act, and with what power? | Identity provider, roles, policies |
| Constrain | What must never happen, whoever asks? | Organisation-level guardrails |
| Record and attribute | What happened, who did it, who pays? | Audit logs, tags, billing views |

The governing principle is that **a boundary is only as strong as the thing that enforces it**. A rule written in a wiki is advice. A permission policy that denies the action is a boundary. A budget that emails a mailbox nobody reads is decoration. At Intermediate level the discipline is to ask of every control: *what enforces it, who is told when it fires, and how would we know if it had stopped working?*

## Organisation and account layout

An **account** is the strongest boundary most providers offer inside one organisation: separate permissions, separate quotas, separate billing line. Putting everything in one account means a mistake in a test script and a breach of production share the same blast radius.

### A small, defensible layout

For a team of up to a few dozen engineers, a layout like this is a reasonable start:

```text
Organisation (root of the hierarchy)
├── Management account          billing, organisation policy, account vending; NO workloads
├── Security / log archive      central audit logs, security tooling; very few humans
├── Shared services             DNS, container registry, CI runners, network hubs
├── Workloads: non-production
│   ├── orders-dev              developers have broad permissions here
│   └── orders-staging          close to production; fewer people
└── Workloads: production
    └── orders-prod             few human write permissions; changes via pipeline
```

| Account | Purpose | Who has human access |
| --- | --- | --- |
| Management | Create accounts, attach organisation policies, read consolidated billing | A very small group; break-glass only |
| Security / log archive | Store audit logs and findings where workload owners cannot alter them | Security team, read mostly |
| Shared services | Things many workloads consume | Platform team |
| Dev / staging | Build and test | Engineers, broadly |
| Production | Run the service | Few, read-mostly, via roles with MFA |

Why the **management account holds no workloads**: it sits above every guardrail. In many providers organisation policies do not apply to the management account itself, so anything running there is outside your safety net, and its compromise is a compromise of the whole organisation.

### Grouping accounts: organisational units

Accounts are grouped into **organisational units** (folders, management groups) so that policy can be attached once to a group. Group by *how an account should be governed*, not by who owns it today (teams reorganise; governance requirements change more slowly).

```text
Root
├── Security          (log archive, audit tooling)
├── Infrastructure    (shared services, network)
├── Workloads
│   ├── NonProd       (dev, staging: looser guardrails)
│   └── Prod          (production: strictest guardrails)
└── Sandbox           (individual experiments: budget-capped, auto-cleaned)
```

### Naming and the account register

Choose a naming convention before the second account exists, and record it:

```text
<organisation>-<workload>-<environment>      e.g.  acme-orders-prod
Root email aliases:  aws-acme-orders-prod@acme.example   (a monitored shared mailbox, never a person)
```

Keep an **account register** (a table in the repository or a configuration database): account ID, name, owner team, environment, data classification, creation date, budget, and the person accountable for its cost.

## Identity bootstrap

The Beginner rule was "no root for daily work, no long-lived keys". Bootstrapping means putting that in place so that the *first day* of a new account is already safe.

### The identity layers

| Identity | Use | Rules |
| --- | --- | --- |
| Root user | Account recovery and rare account-level tasks | MFA on, no access keys, credentials in a vault with two-person access, alert on any login |
| Break-glass role | Emergency access when the normal path fails | Separate from daily roles, strongly authenticated, alert on use, reviewed after every use |
| Human identity via single sign-on | Day-to-day console and command-line work | Federated from the organisation's directory; MFA; session length hours, not days |
| Workload role | Services and CI | Short-lived credentials issued by the platform; no human keys |

If the only way to make a service work is an administrator key on disk, the foundation is incomplete.

### Bootstrap order

The order matters because each step makes the next one safer:

```text
1. Secure the management account root user (MFA, vaulted credentials, shared mailbox).
2. Connect a single sign-on identity provider; create groups (Platform, Developers, Auditors).
3. Define permission sets (roles): ReadOnly, Developer, PlatformAdmin, Billing, BreakGlass.
4. Assign groups to accounts through permission sets, never users to accounts one by one.
5. Turn on organisation-wide audit logging to the log archive account.
6. Attach first-wave guardrails to the organisational units.
7. Only then create workload accounts and let teams in.
```

### Permission sets by example

A role named `Developer` in `orders-dev` and `ReadOnly` in `orders-prod` for the same group shows least privilege in practice. Here is a deliberately small, illustrative policy that lets a developer read logs and manage a few resource types in the non-production account, scoped by tag:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadAndLogs",
      "Effect": "Allow",
      "Action": ["logs:Get*", "logs:Describe*", "logs:FilterLogEvents", "cloudwatch:Get*", "cloudwatch:List*"],
      "Resource": "*"
    },
    {
      "Sid": "ManageOwnTaggedResources",
      "Effect": "Allow",
      "Action": ["ec2:StartInstances", "ec2:StopInstances", "ec2:RebootInstances"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:ResourceTag/Project": "orders" } }
    }
  ]
}
```

Read it as a sentence: *this identity may read logs and metrics anywhere in the account, and may start, stop or reboot machines whose `Project` tag is `orders`.* Everything not allowed is denied by default. Compare with the common shortcut:

```json
{ "Effect": "Allow", "Action": "*", "Resource": "*" }
```

That statement is "administrator", and it should exist for very few identities and for short periods.

### Testing what an identity can do

Do not trust a policy you have not tested. After assigning a permission set, sign in as that role and try both an allowed and a forbidden action:

```bash
# Illustrative: run as the Developer role in the non-production account
provider-cli identity whoami                          # confirm account and role
provider-cli compute instances stop --id i-0abc...    # allowed on tagged instance
provider-cli iam users create --name test-user        # expected: AccessDenied
```

The "expected denial" is as important as the success: it is the evidence that least privilege exists.

## Budgets and alerts

A budget is a number; an **alert** is a message; neither stops spending by itself. The foundation question is *who receives the message and what do they do within an hour?*

### Budget design

Create budgets before networks or compute, per account and, where useful, per project tag. Document:

| Item | Example |
| --- | --- |
| Monthly budget | 400 for `orders-dev`; 3,000 for `orders-prod` (illustrative) |
| Thresholds | 50 % actual, 80 % actual, 100 % forecast, 100 % actual |
| Notification | A team mailbox plus a chat channel, not a single person |
| Owner | A named person who is accountable for the account's cost |
| Idle policy | "Stop or destroy within N hours of finishing a lab" |
| Forbidden by default | Always-on NAT gateways in sandbox, public databases, unused load balancers |
| Review cadence | Weekly in the first month, then monthly |

Budgets track billing data, which lags usage by hours. Combine them with **anomaly detection** (alerts on unusual daily spend relative to history) and with technical limits: service quotas set lower than defaults in sandbox accounts, and instance-type allow-lists.

### What an alert runbook says

```text
Alert: orders-dev spend at 80 % of monthly budget on day 12.
1. Open the cost explorer grouped by service, then by tag Project and Owner.
2. Identify the top three increases versus the previous week.
3. For each: expected (planned load test)? If not, find the owner tag; message them.
4. If no owner tag: treat as unowned; snapshot if needed, stop, and open a ticket.
5. Record the finding in the account's cost log: cause, action, date.
```

An alert that nobody has rehearsed responding to is not yet a control.

## Guardrails

A **guardrail** is a rule applied above the workload, so that a team cannot violate it by mistake (preventive) or so that violations are noticed quickly (detective). The first guardrails should prevent the *worst, cheapest-to-prevent* mistakes.

### Preventive guardrails: organisation policies

Providers offer organisation-level deny policies (service control policies, organisation policies, Azure Policy, and similar). They set the **maximum** permissions an account can ever have, whatever local administrators grant. An illustrative deny that blocks unused regions and protects audit logging:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnapprovedRegions",
      "Effect": "Deny",
      "NotAction": ["iam:*", "organizations:*", "route53:*", "support:*", "cloudfront:*", "budgets:*"],
      "Resource": "*",
      "Condition": { "StringNotEquals": { "aws:RequestedRegion": ["eu-west-1", "eu-central-1"] } }
    },
    {
      "Sid": "ProtectAuditLogging",
      "Effect": "Deny",
      "Action": ["cloudtrail:StopLogging", "cloudtrail:DeleteTrail", "cloudtrail:UpdateTrail"],
      "Resource": "*"
    }
  ]
}
```

Two properties to remember about this kind of policy:

- It **limits** permissions; it never grants them. An action needs both an allow in the account and the absence of a deny from above.
- It does not apply to everything identically (the management account, and some service-linked roles, are usually exempt). Read the provider's rules for what is outside its reach.

### Detective guardrails

Detective controls watch configuration and alert when it drifts: an open security group, an unencrypted volume, a public bucket, a root login. They suit things that cannot be blocked without breaking legitimate use.

| Mechanism | Strength | Weakness |
| --- | --- | --- |
| Preventive deny | Cannot be bypassed locally | Can block legitimate work; needs an exception route |
| Detective rule | Flexible; catches what you did not predict | Depends on someone responding; the harm may already be done |
| Corrective automation | Fast | Can cause outages; scope and test it |

### A sensible first set

A small first wave of guardrails (and the reasons) is better than a long list nobody understands:

| Guardrail | Prevents |
| --- | --- |
| Deny stopping audit logging or deleting log archives | Loss of evidence after a compromise |
| Restrict permitted regions | Forgotten resources in unused regions; data-residency breaches |
| Deny leaving the organisation | An account escaping governance |
| Block public object storage (account-level setting) | Accidental data exposure |
| Deny root user actions in member accounts | Daily use of the most powerful identity |
| Require encryption on new storage volumes (detective at first) | Unencrypted data at rest |

Each guardrail should have a **test**: try the forbidden action in a sandbox and expect a denial. Keep the evidence.

## Audit logs

An **audit log** records API calls: who (identity), what (action), when, from where, and whether it succeeded. When something goes wrong, the audit log answers "who deleted this?" and "how did the attacker get in?"

### What to capture and where it goes

| Log | What it shows | Notes |
| --- | --- | --- |
| Management (control-plane) events | Creating, changing, deleting resources; sign-ins; policy changes | Enable in *every* account and *every* region |
| Data events | Reading or writing individual objects or records | High volume and cost; enable for sensitive stores only |
| Network flow logs | Who talked to whom | Useful for investigation; enable selectively |
| Application and operating-system logs | Your own software's behaviour | Different pipeline, same retention thinking |

Send the organisation-wide trail to a bucket in the **log archive account**, with these properties:

```text
- Written by the audit service; workload accounts cannot delete or edit.
- Versioning on; object lock (write-once) for the retention period where available.
- Encryption with a key owned by the security account.
- Log file integrity validation enabled, so tampering is detectable.
- Retention set by a documented rule (for example 13 months hot, then archive).
- Alert if logging stops, if the trail is modified, or if the bucket policy changes.
```

### Reading a log entry

An abbreviated, illustrative event:

```json
{
  "eventTime": "2026-11-14T09:12:44Z",
  "eventName": "DeleteDBInstance",
  "userIdentity": { "type": "AssumedRole", "arn": "arn:aws:sts::111122223333:assumed-role/Developer/alice" },
  "sourceIPAddress": "203.0.113.17",
  "awsRegion": "eu-west-1",
  "requestParameters": { "dBInstanceIdentifier": "orders-dev-db" },
  "errorCode": null
}
```

Read it as: *at 09:12 UTC, Alice, using the Developer role, deleted the dev database, from this address, successfully.* Because roles are assumed from single sign-on, the log identifies the person even though the role is shared. That is why shared users and long-lived shared keys are a foundation defect: they destroy this attribution.

## Tagging

Tags are the cheapest metadata system the cloud provides. A tag is a key-value label on a resource.

### A minimal tag policy

| Tag | Purpose | Example |
| --- | --- | --- |
| `Project` | What it belongs to; drives cost reports and permissions | `orders` |
| `Owner` | A team or role mailbox that can answer for it | `team-orders` |
| `Environment` | Separates dev, staging, production | `dev` |
| `CostCenter` | Finance allocation (optional at first) | `cc-1234` |
| `ExpiryDate` | Temporary resources are deleted after this date | `2026-12-01` |

### Making tags enforceable

A tag policy that is merely requested decays within weeks. Combine three mechanisms:

1. **Create-time**: infrastructure-as-code applies default tags to every resource it makes (module-level or provider-level defaults).
2. **Policy**: a rule that denies creation of selected resource types without required tags, or a detective rule that reports non-compliance daily.
3. **Reporting**: a weekly report of untagged spend and of resources past `ExpiryDate`.

An illustrative fragment of infrastructure code:

```hcl
provider "aws" {
  region = "eu-west-1"
  default_tags {
    tags = {
      Project     = "orders"
      Owner       = "team-orders"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}
```

Tag keys are case-sensitive and cost-allocation tags typically must be *activated* in billing before they appear in cost reports; a tag added today does not retroactively label last month's spend. Plan for that gap.

## A small landing zone

A **landing zone** is the pre-configured, governed starting point into which new accounts are placed. At Intermediate level you do not need a large product; you need the *baseline* applied the same way every time.

### The baseline every new account receives

```text
Identity      Single sign-on assignments for standard groups; no local users
Logging       Organisation trail delivering to log archive; config recorder on
Guardrails    Inherited from the organisational unit
Budget        Account budget with the standard thresholds and a named owner
Tags          Default-tag configuration; tag policy attached
Network        (if the account needs one) a standard address range from a registry
Security      Account-level public-access blocks, default encryption, detective rules on
Contact       Billing, security and operations contacts set to shared mailboxes
```

### Foundational services map

| Concern | Local | Cloud foundation |
| --- | --- | --- |
| API process | Container | Container service or virtual machines |
| Image storage | Local registry | Managed container registry |
| Data | Database container | Managed database or deferred |
| Edge | localhost port | Load balancer plus security groups |
| DNS | hosts file | Managed DNS or load-balancer name |
| Logs | Console | Central log service |
| Workload identity | n/a | Task or instance role |
| Human demo access | n/a | A limited operator role |

Prefer linking existing infrastructure-as-code resources over recreating them in a console. A console-created resource is invisible to review, impossible to recreate exactly, and the usual source of drift.

### Vending an account (the process)

```text
Request  -> team lead files a request: workload, environment, owner, budget, data class
Review   -> platform team checks naming, owner and data class against the register
Create   -> automation creates the account inside the correct organisational unit
Baseline -> automation applies the baseline stack (identity, logging, budget, tags)
Verify   -> automated checks confirm every baseline item; register is updated
Handover -> the team receives access through single sign-on, with documentation
```

If creating an account takes two weeks and three tickets, teams will share accounts or create unmanaged ones. The speed of the official path is a *governance* property.

## An ADR for the landing zone

An **architecture decision record** captures a decision and its reasons, so a future reader can tell whether the reasons still hold. Record: accounts and organisation structure, identity approach, region(s), network ranges, logging destination, cost controls, teardown policy and the reason for each.

```text
ADR-007  Landing zone for orders (status: accepted, 2026-11-10)
Context   Three engineers, two environments, one region required by customer contract.
Decision  Five accounts (management, log-archive, shared, nonprod, prod); SSO with
          three permission sets; two approved regions; org trail to log-archive with
          object lock; first-wave guardrails (regions, logging, leave-org, public storage).
Because   Blast-radius separation at low cost; audit evidence outside workload control.
Rejected  Single account with tags only: no hard boundary for production.
Trade-off Extra overhead per account; mitigated by automated baseline.
Revisit   When teams exceed ten or a second customer region is required.
```

## Teardown

Cost control ends in deletion. A **teardown runbook** says how to remove everything you created, in the right order, and how to confirm the bill goes quiet.

### Ordering and protection

Remove from the outside in, and from the most dependent to the least:

```text
1. Stop traffic: DNS records, load balancers, public endpoints.
2. Remove runtime: services, instances, containers, functions, scheduled jobs.
3. Remove network attachments: NAT gateways, elastic addresses, endpoints.
4. Take and verify any final backups; delete data stores deliberately.
5. Remove the network itself (subnets, route tables, gateways).
6. Remove identity artefacts created for the workload (roles, keys, secrets).
7. NEVER remove while dependents exist: remote state, audit logs, budgets, SSO.
8. Verify: no resources by tag, cost explorer flat after 48 hours.
```

List what must not be deleted: budgets and alerts, MFA devices, audit logs and the state storage for your infrastructure code. Deleting a state bucket while resources exist leaves orphans you can no longer manage with tooling.

### Confirming the bill goes quiet

```text
Day 0   Run teardown; save the list of resources deleted.
Day 1   Query resources by tag Project=<name> in all enabled regions: expect none.
Day 2   Check cost by service and by day: hourly-billed items should be zero.
Day 7   Check storage, snapshots and data transfer lines for stragglers.
Day 30  Final bill review; close the cost log entry.
```

Common stragglers: snapshots and machine images, elastic IP addresses, load-balancer remnants, log groups with long retention, and resources in a region you tried once.

## What can go wrong: a short catalogue

| Problem | How it appears | Defence |
| --- | --- | --- |
| Everything in one account | Dev script deletes a production table | Account separation with guardrails |
| Management account used for workloads | Guardrails do not apply to it | Keep it workload-free |
| Shared admin login | Audit shows a role, not a person | Federated identity, one person per session |
| Budget alert to a dead mailbox | Surprise invoice | Team mailbox plus chat; test the alert |
| Guardrail without exception path | Teams request broad admin or create shadow accounts | Document a time-boxed exception route |
| Logs in the same account they audit | Attacker deletes logs | Central log archive with object lock |
| Tags requested but not enforced | Half of spend unattributed | Defaults in IaC, policy, weekly report |
| Console-built baseline | Cannot reproduce; drift | Baseline as code, reviewed |
| Teardown deletes state first | Orphaned resources | Ordered runbook; protect state and logs |

## Knowledge consolidation

- A foundation **separates, authenticates, constrains and records**. A control is real only if something enforces it and someone is told when it fires.
- Use **multiple accounts** grouped into organisational units by governance need; keep the **management account workload-free**.
- **Bootstrap identity** before workloads: vaulted root with MFA, single sign-on, permission sets, break-glass, workload roles; no long-lived keys.
- **Test permissions** with both an allowed and a forbidden action; the denial is evidence.
- **Budgets** need thresholds, a named owner and a rehearsed response; they do not stop spending, so add anomaly detection and technical limits.
- **Preventive** guardrails (organisation deny policies) limit permissions; **detective** rules find drift; **corrective** automation is powerful and risky. Start with a few high-value, testable guardrails.
- **Audit logs** go to a protected archive in a separate account with write-once storage, integrity validation and alerts if logging stops.
- **Tags** work only if enforced at creation, by policy and by reporting; cost-allocation tags must be activated.
- A **landing zone** is a repeatable baseline plus a fast, automated way to vend accounts.
- **Teardown** is ordered, protects state and logs, and ends with verification that the bill is quiet.

## Exercises

**Exercise 1 — Account layout.** For a team with a public website, an internal admin tool, and a data-science sandbox, propose an account and organisational-unit layout. Justify each boundary in one sentence and state which account holds the audit logs.

**Exercise 2 — Identity baseline.** Write the identity baseline for a new training account: root-user handling, daily role, break-glass role and workload roles. For each, state the credential type, its lifetime and how you would detect misuse.

**Exercise 3 — Permission test.** Write a policy that lets a role start and stop only instances tagged `Project=orders` and read logs. List three actions it should *deny* and show how you would test each one.

**Exercise 4 — Budget and runbook.** Design a budget with thresholds and notification routes for a sandbox account, and write a half-page alert runbook. Include one technical limit (a quota or an allow-list) that works even if nobody reads the alert.

**Exercise 5 — First-wave guardrails.** Choose three organisation-level guardrails. For each, state what it prevents, how a legitimate user would request an exception, and how you would test that it works in a sandbox.

**Exercise 6 — Audit evidence.** Take one audit-log event (real or the example above) and answer: who, what, when, from where, did it succeed? Then state what you would need in place for the same question to be answerable if the attacker had tried to delete the log.

**Exercise 7 — Tag enforcement.** Write a tag policy with four required tags. Describe how each is applied at creation, how non-compliance is detected, and how you would report untagged spend weekly.

**Exercise 8 — Foundation documents.** Write the foundation documents for a training account: identity baseline, cost guardrails, services map and teardown runbook, each under one page.

**Solution notes.**

*Exercise 1.* A sound layout separates production from non-production, puts audit logs in a dedicated archive account, and isolates the sandbox with a hard budget. Whether the admin tool shares an account with the website depends on its data class and who administers it; the justification matters more than the exact answer.

*Exercise 2.* Root: strong password, MFA, vaulted, no keys, alert on any use. Daily: federated, MFA, session of hours. Break-glass: separate, strongly authenticated, alert and review on every use. Workload: platform-issued short-lived credentials. Misuse detection should name a log source and an alert, not only a hope.

*Exercise 3.* Expected denials include creating users, deleting databases and modifying audit logging. Test each by assuming the role and attempting the action; the evidence is an access-denied response and a matching audit event.

*Exercise 4.* A strong answer routes alerts to a shared channel as well as a mailbox, includes a forecast alert, and adds a technical limit such as reduced quotas or restricted instance types. If your only control is an email, you have a notification, not a limit.

*Exercise 5.* Look for guardrails tied to a concrete loss (evidence loss, data exposure, regional sprawl), an exception route with an owner and expiry, and a sandbox test that attempts the forbidden action and expects a denial.

*Exercise 6.* The example answers: Alice (via the Developer role), deleted `orders-dev-db`, at 09:12 UTC on 14 November 2026, from the given address, successfully. To survive log tampering you need a central archive in another account, write-once storage, integrity validation and an alert if logging stops.

*Exercise 7.* Look for create-time defaults in infrastructure code, policy that blocks or reports, and a scheduled report of untagged spend and expired resources. Note the delay before cost-allocation tags appear.

*Exercise 8.* Each document must be usable by a stranger: the identity baseline names every identity type; the cost guardrails give amounts, thresholds, recipients and an idle policy; the services map matches the placement table; the teardown runbook is ordered, protects state and logs, and ends with a verification step.
