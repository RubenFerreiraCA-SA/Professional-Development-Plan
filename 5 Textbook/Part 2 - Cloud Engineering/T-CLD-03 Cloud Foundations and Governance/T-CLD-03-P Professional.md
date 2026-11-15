# T-CLD-03-P — Professional Engineering

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-p"></a>
#### T-CLD-03-P — Professional Engineering

## Why this matters

At Intermediate level a foundation is a documented baseline that a small team can apply consistently. At Professional level the audience changes. There are many teams, some of whom you will never meet; an internal or external auditor who needs *evidence*, not assurances; a finance function that wants costs attributed to products; legal requirements about where data may live; and incidents in which the question "how far could this spread?" has a short deadline.

Professional practice is the engineering of **governance as a system**: organisation policy that is layered and testable, duties split so that no single person can both make and approve a risky change, controls that are mapped to the risks they address, cost allocation that survives shared resources, residency rules that are enforced rather than hoped for, evidence collected continuously, and incident boundaries designed *before* the incident. It also means accepting that every control costs something, and being able to say what.

This section assumes the Beginner and Intermediate material: shared responsibility, account layout, identity bootstrap, budgets, guardrails, audit logs, tags and a basic landing zone. The running example continues: `orders-api` has grown into several teams, two regions in one legal area, and a customer contract that requires auditable controls. Policy documents, commands and numbers are **illustrative**; verify against your provider's current documentation and your own legal advice.

## First principles: governance is control under delegation

Governance exists because you want many people to move quickly *without* asking permission for each action, yet you cannot allow every action. The only way to square this is **delegation within bounds**: central teams define the bounds; workload teams act freely inside them.

Three properties define a good governance design:

| Property | Meaning | Failure when absent |
| --- | --- | --- |
| **Least privilege by default** | Nobody has more power than their task needs | One compromised credential reaches everything |
| **Independent verification** | The party that performs a change is not the only party that can approve or inspect it | Errors and fraud go unseen |
| **Evidence by construction** | Running the system produces proof that controls work | Audits become projects; claims are unverifiable |

Two equations of cost are worth keeping in mind:

```text
Cost of a control = friction to legitimate users + operating effort + residual bypass risk
Value of a control = (probability of the harm) x (impact of the harm) x (share the control removes)
```

A control whose value is lower than its cost should not exist, however fashionable. A control whose value is high but which is easy to bypass has a lower real value than its description suggests.

## Organisation policy as a layered system

Organisation policy is a hierarchy: root, organisational units, accounts. Policies attach at any level and are **inherited downward**. The effective permission of an identity in an account is the intersection of what its role allows and what every policy above permits.

```text
Effective permission  =  identity policy  AND  permission boundary (if any)
                         AND  account-level controls
                         AND  organisational-unit policies (all levels)
                         AND  root policies
```

### Design rules for a policy tree

| Rule | Reason |
| --- | --- |
| Attach policies to organisational units, not individual accounts | Moves with the account; fewer exceptions to track |
| Keep a small number of composable policies | Overlap makes denials hard to explain |
| Separate *guardrails* (deny) from *grants* (allow) | Different owners, different review cadence |
| Give every policy an ID, owner, purpose, test and review date | Policies without owners rot |
| Version policies in a repository; deploy by pipeline | Review, rollback, and evidence of change |
| Test policies in a canary organisational unit first | A bad deny at the root can lock out an entire organisation |
| Keep an out-of-band recovery path for policy mistakes | Someone must be able to fix a self-inflicted lockout |

### The policy catalogue

A catalogue lists each organisation-level control with the information a reviewer needs:

```text
ID        SCP-004
Name      Deny disabling of audit logging
Scope     Root (all member accounts); management account is exempt by design
Effect    Deny cloudtrail:StopLogging, DeleteTrail, UpdateTrail, config:StopConfigurationRecorder
Owner     Security architecture (team: sec-arch)
Risk      R-12: loss of audit evidence after a compromise
Test      sandbox/tests/scp-004.sh attempts each action; expects AccessDenied; runs nightly
Exception Not available; request a redesign through the architecture board
Review    Quarterly; last reviewed 2026-09-30
```

The catalogue is the answer to "why was I denied?" in under fifteen minutes and to an auditor's "show me the control for risk R-12".

## Separation of duties

**Separation of duties** (SoD) means no single identity can complete a sensitive process end to end. It is the oldest control in finance and it translates directly to cloud operations. Its purpose is not distrust; it is to make a single mistake, a single compromised credential or a single coerced person insufficient to cause severe harm.

### Where it applies in the cloud

| Process | Duty A | Duty B | Mechanism |
| --- | --- | --- | --- |
| Changing production infrastructure | Author proposes change | Reviewer approves; pipeline applies | Pull-request approval rules; humans lack direct write in production |
| Changing organisation policy | Policy author | Security reviewer; separate deploy role | Repository protection; deploy role not held by authors |
| Granting access | Requester | Approver and the system owner | Access-request workflow with approval; time-boxed grants |
| Deleting audit logs or changing retention | Platform admin | None: not permitted to anyone | Preventive deny; object lock |
| Approving a cost commitment | Engineer proposes | Finance approves | Purchase workflow outside the cloud console |
| Using break-glass | Operator | Second person confirms and later reviews | Two-person access to the vault; mandatory post-use review |

### Designing roles to enforce it

The usual structure splits permissions into families so that no role holds an incompatible pair:

| Role family | May | May not |
| --- | --- | --- |
| Author / developer | Write code and infrastructure definitions; deploy to non-production | Approve own changes; write directly in production |
| Pipeline | Apply approved changes in production using short-lived credentials | Be assumed by humans interactively |
| Operator | Read production, restart services within runbooks | Change policies or IAM |
| Security administrator | Manage guardrails and audit tooling | Deploy workloads; alter their own audit trail |
| Billing / finance | View and allocate cost | Create resources |
| Auditor | Read-only on everything, including logs | Change anything |

An illustrative condition that stops an identity from assigning itself more power (a **permission boundary** pattern):

```json
{
  "Sid": "DenyPrivilegeEscalation",
  "Effect": "Deny",
  "Action": [
    "iam:CreateUser", "iam:AttachUserPolicy", "iam:PutUserPolicy",
    "iam:CreatePolicyVersion", "iam:UpdateAssumeRolePolicy", "iam:PassRole"
  ],
  "Resource": "*",
  "Condition": { "StringNotEquals": { "aws:PrincipalTag/Team": "platform-iam" } }
}
```

Beware of **hidden paths around SoD**: the ability to pass a powerful role to a service you control, to edit the pipeline definition that holds production credentials, or to modify the repository's protection rules. When designing SoD, enumerate the paths to *production write* and to *audit-trail modification*, not only the obvious ones.

### The small-team caveat

In a team of three, strict SoD is impractical. The professional response is **compensating controls**: pipeline-only production writes with required peer review where possible, high-risk operations requiring an out-of-band approval, and detective monitoring with alerts on every privileged action. State the compensation explicitly so an auditor sees a decision, not an omission.

## Preventive controls, in depth: SCPs and their kin

Service control policies (and equivalents: Azure Policy with deny effects, organisation policy constraints) are the strongest preventive mechanism. They are also the easiest way to harm yourself, so understand their mechanics.

### Mechanics worth knowing

- They **never grant**; they bound what local policies can grant.
- They typically **do not apply to the management account**, and may not affect some service-linked or provider-managed actions.
- Evaluation: an explicit deny anywhere in the chain wins; an allow must exist at *every* level for allow-list style policies.
- Two strategies: **deny-list** (start permissive, deny specific actions: easier to adopt) and **allow-list** (start with nothing, allow specific services: stronger, harder to operate).
- A policy has a size limit and a limited number of attachments per target; this forces composability.
- Changes are fast and affect everyone immediately: a bad deny is an outage.

### Common high-value controls

| Category | Example control | Type |
| --- | --- | --- |
| Evidence | Deny stopping audit logging; deny deleting log archives | Deny SCP |
| Boundary | Deny leaving the organisation; deny creating accounts outside vending | Deny SCP |
| Identity | Deny root-user actions in member accounts; deny creating long-lived access keys for human users | Deny SCP |
| Data | Deny disabling account-level public-access block; require encryption on storage | Deny + detective |
| Region | Deny use of unapproved regions (with a global-service exemption list) | Deny SCP |
| Network | Deny internet gateway creation in accounts that must be private | Deny SCP |
| Cost | Deny very expensive instance families outside approved accounts | Deny SCP |
| Tag | Deny resource creation without owner tag for selected services | Deny with condition |

### Safe rollout of a deny

```text
1. Write the policy and its test (a script that tries the forbidden action).
2. Run an inventory query: which existing resources or roles would this break?
3. Apply to a canary organisational unit with a known owner.
4. Monitor audit logs for denials (AccessDenied events matching the policy) for a week.
5. Contact owners of legitimate denials; fix or define exceptions.
6. Roll out to the next OU; repeat; finally the production OU.
7. Record the rollout, results and the date in the catalogue.
```

A useful audit-log query to find who would be affected before enforcement (illustrative pseudo-SQL for a log query engine):

```sql
SELECT useridentity.arn, eventname, count(*) AS calls
FROM audit_logs
WHERE eventsource = 'ec2.amazonaws.com'
  AND awsregion NOT IN ('eu-west-1', 'eu-central-1')
  AND eventtime > now() - interval '30' day
GROUP BY 1, 2
ORDER BY calls DESC;
```

If the query returns activity from a region you thought unused, you have found something to discuss *before* the deny turns it into an outage.

## Detective and corrective controls

Detective controls inspect configuration and activity: configuration rules, security-finding aggregators, anomaly detection on identity use, and flow-log analysis.

| Control | Detects | Typical response | Risk |
| --- | --- | --- | --- |
| Configuration rule: no public storage | Misconfiguration | Alert; auto-remediate in non-production | Remediation breaking legitimate hosting |
| Identity anomaly detection | Credential misuse | Page security; revoke sessions | False positives; alert fatigue |
| Unused-credential report | Stale keys and roles | Disable after notice | Breaking infrequent jobs |
| Drift detection (IaC plan vs reality) | Out-of-band change | Ticket or revert | Reverting an emergency fix |
| Findings aggregator | Provider-detected issues | Triage by severity and exposure | Noise |

**Corrective automation** (automatic remediation) should follow rules: scope to well-understood violations; test in non-production; log every action; include a kill switch; and exclude resources with an active, approved exception.

## Cost allocation

Cost allocation answers "who is responsible for this spend?" Without it, optimisation has no owner.

### Layers of attribution

| Layer | Mechanism | Strength | Weakness |
| --- | --- | --- | --- |
| Account | Each workload in its own account | Exact, automatic | Shared services remain unattributed |
| Tag | Required tags activated in billing | Flexible, cross-account | Depends on tag discipline; untagged remainder |
| Resource hierarchy | Folders/OUs mapped to business units | Rolls up cleanly | Coarse |
| Allocation rules | Proportional split of shared costs | Handles shared platform | Requires an agreed driver |
| Usage-based metering | Application-level counters (per tenant or request) | Closest to unit economics | Needs engineering effort |

### Allocating shared costs

Shared services (the network hub, logging, the container registry, a shared Kubernetes cluster) cost money and serve many teams. Choose an explicit rule and publish it:

| Shared cost | Candidate driver | Note |
| --- | --- | --- |
| Central logging | Gigabytes ingested per account | Rewards sensible log levels |
| Network hub | Data processed per attachment | Reflects use |
| Shared cluster | CPU and memory *requests* per namespace | Requests, not usage, drive capacity |
| Security tooling | Number of accounts, or flat split | Simplicity beats precision here |
| Support plan | Proportional to spend | Standard practice |

An illustrative worked example:

```text
Monthly shared logging bill: 6,000
Ingested per account (GB):   orders 4,000 | payments 1,500 | internal-tools 500
Allocation by ingestion:     orders 4,000/6,000 x 6,000 = 4,000
                             payments 1,500             = 1,500
                             internal-tools 500         =   500
```

The point is not mathematical precision but **incentive**: teams that can reduce the driver (log volume) see the saving.

### Showback, chargeback and the metrics that matter

**Showback** shows teams their costs without moving money; **chargeback** transfers the cost to their budget. Start with showback; add chargeback when the allocation is trusted.

| Metric | Computation | Use |
| --- | --- | --- |
| Untagged / unallocated spend | Unattributed ÷ total | Governance health; target below a few percent |
| Unit cost | Attributable cost ÷ business unit (orders processed) | Trend and design comparison |
| Commitment coverage and utilisation | Committed share of steady usage; used share of commitment | Avoid on-demand overspend and unused commitments |
| Forecast accuracy | Forecast ÷ actual | Credibility with finance |
| Waste | Idle resources, oversized instances, orphaned storage | Prioritise cleanup |

### Cost drivers worth knowing

- Compute hours (and the difference between on-demand, committed and interruptible capacity).
- Load-balancer hours and capacity units; NAT gateway hours and per-gigabyte processing.
- Data transfer: out to the internet, between zones and between regions.
- Storage tier, snapshots, request counts and retrieval fees.
- Managed database instance class, replicas, provisioned IOPS and backup retention.
- Log ingestion and retention, which often rival compute in cost for chatty services.

Use commitments (savings plans, reservations) only for **stable baseload**, after measuring; commit conservatively and review utilisation monthly.

## Data residency and sovereignty

**Data residency** is where data is stored; **sovereignty** concerns which legal system can compel access to it. They are related and not the same: data stored in a local region may still be subject to foreign legal reach through the provider's jurisdiction. Residency is a technical control; sovereignty also needs a legal assessment.

### Residency as a control chain

A residency requirement ("customer data stays in the EU") is only met if *every* place data can go is controlled:

| Where data can leak across a boundary | Control |
| --- | --- |
| Resources created in an unapproved region | Region-deny policy with exemptions listed |
| Backups and snapshots copied elsewhere | Replication and copy rules restricted to approved regions |
| Logs and telemetry exported to a global service | Logging destinations in approved regions; scrub personal data |
| Support access by provider staff or your own contractors | Contractual terms; access approval workflow; session logging |
| Managed services that process data in other regions | Review per-service data-processing documentation |
| Global services with a single home region | Treat their metadata and configuration as potential residency exposure |
| Developer laptops and CI caches | Policy on exporting data; synthetic data in non-production |
| AI and analytics features that send data to other regions | Review service terms and region settings before enabling |

### Evidence for residency

```text
Claim:    All production customer data resides in eu-west-1 and eu-central-1.
Controls: SCP-007 (region deny), SCP-011 (restrict cross-region replication), key policy limiting key use to approved regions.
Evidence: Nightly inventory of storage and database resources by region (zero outside list);
          audit log search for CopyObject / CreateSnapshot to other regions (zero);
          list of exempted global services and the data classes they touch.
Residual: Provider support access (contractual); global control plane metadata.
```

Name the residual risk. An honest statement ("this is covered by contract and not by technical control") is better than silence.

## Evidence and compliance

Compliance means demonstrating that controls operate. The professional goal is **continuous evidence**: automated checks that produce time-stamped results, rather than screenshots gathered in the week before an audit.

### Mapping controls to frameworks

Do not build a control set per framework. Build one set of controls, then map:

| Our control | Risk | Framework requirements it supports (examples) |
| --- | --- | --- |
| SCP-004 audit logging protected | R-12 | Logging and monitoring; non-repudiation |
| Single sign-on with MFA | R-03 | Access control; authentication |
| Encryption at rest with customer-managed keys | R-08 | Data protection; key management |
| Access review each quarter | R-05 | Least privilege; periodic review |
| Change via reviewed pull request | R-14 | Change management; separation of duties |

### What good evidence looks like

| Property | Meaning |
| --- | --- |
| Time-stamped | Shows when it was true |
| Automatically produced | Not hand-assembled |
| Tamper-evident | Stored in a place the control owner cannot alter |
| Complete | Covers the whole population (every account), not a sample you chose |
| Reproducible | An auditor can re-run the query |
| Linked | Evidence ID is attached to a control and a risk |

An illustrative evidence record:

```text
Control:   CTL-AUD-02 Audit logging cannot be disabled
Check:     query lists accounts where the organisation trail is not active; expected zero
Run:       2026-11-14T02:00Z by evidence-pipeline (read-only role)
Result:    0 non-compliant of 14 accounts
Stored:    s3://evidence-archive/ctl-aud-02/2026-11-14.json (object lock, 7 years)
```

### Common audit traps

- **Compliance by screenshot**: evidence that cannot be reproduced.
- **Sampling bias**: the sample accounts are the clean ones.
- **Stale evidence**: the check ran at the audit and not since.
- **Control exists, test missing**: nobody proved the deny actually denies.
- **Exceptions untracked**: approved deviations live in email.

## Incident boundaries

An **incident boundary** is a pre-built limit on how far a compromise or mistake can spread, plus the ability to *cut it* quickly. Boundaries are designed in advance; during an incident there is no time.

### Blast-radius layers

| Boundary | Contains | Cut by |
| --- | --- | --- |
| Credential / session | One identity's actions | Revoke sessions; disable the identity |
| Resource / service | One workload | Isolate security group; stop the instance |
| Account | One workload's environment | Apply a quarantine policy; remove cross-account trust |
| Organisational unit | A group of accounts | Attach a deny-all policy at the OU |
| Organisation | Everything | Break-glass; provider support; pre-planned recovery |
| Region | Regional failure or restricted use | Region deny; failover plan |

### A quarantine toolkit

Prepare these before you need them:

```text
- A "quarantine" policy that denies all but read and forensic actions; attach to a compromised account or role by one command.
- A security-group "isolate" template that blocks all traffic and a procedure to snapshot an instance first.
- A "revoke sessions" procedure (deny policy with an issued-before condition) for roles whose credentials may be stolen.
- A forensics account with read access to snapshots and a write-only logging path.
- A communication tree: who declares an incident, who talks to the provider, who informs legal and customers.
```

The classic **revoke-sessions** deny uses a time condition so that sessions issued before the incident are dead while new ones work:

```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": { "DateLessThan": { "aws:TokenIssueTime": "2026-11-14T10:30:00Z" } }
}
```

### Cross-account trust is a boundary

Every cross-account role trust is a bridge. Inventory them. A compromised development account that can assume a role in production has defeated the account boundary. Prefer trust conditioned on external identifiers, source accounts and tags; review quarterly; alert on new trust relationships.

### Management plane protection

The management account and the log archive are crown jewels: very few humans, hardware-backed MFA, alerts on every login, no workloads, and a documented recovery path if they are locked out.

## Shared responsibility as a design input

Make a matrix for each chosen service: what the provider guarantees, what you must configure, what you must monitor and what you must prove to an auditor. Managed services remove patching but add configuration surface (public access settings, encryption options, backup retention).

| Service | Provider guarantees | You configure | You monitor | You prove |
| --- | --- | --- | --- | --- |
| Managed relational database | Engine patching, standby failover | Network access, encryption, backup retention, parameters | Replication lag, storage, failed logins | Backup restore tested; access reviewed |
| Object storage | Durability of stored objects | Public-access blocks, encryption, lifecycle, replication | Policy changes, unusual access | No public exposure; retention honoured |
| Virtual machines | Host and hypervisor | OS patching, hardening, agent install | Patch compliance, drift | Patch SLA met |
| Container platform | Control plane (managed offering) | Node pools, workload security, admission rules | Cluster health, image provenance | Policy enforcement results |

## Placement decisions with trade-offs

Record why a component is run as virtual machines, containers, serverless or a managed service: operational burden, cost at your scale, portability, performance, compliance and team skills. A topology diagram that implies high availability while a single instance runs is aspirational; either fix the diagram or the infrastructure.

| Option | Strong when | Weak when |
| --- | --- | --- |
| Virtual machines | Need OS control; lift-and-shift; predictable load | Team cannot sustain patching |
| Containers on a managed platform | Many services; portability matters | Platform engineering is absent |
| Serverless functions | Spiky, event-driven load | Long-running, latency-critical or high steady throughput (cost) |
| Fully managed SaaS/PaaS | The capability is not a differentiator | Compliance, residency or lock-in constraints bite |

## Governance trade-offs

Every governance choice buys something and costs something. Naming the trade is the professional skill.

| Choice | Gain | Cost | Choose when |
| --- | --- | --- | --- |
| More accounts | Smaller blast radius, clean billing | Baseline overhead, cross-account plumbing | Vending is automated |
| Strict preventive denies | Strong assurance | Friction, exception volume | Harm is severe and irreversible |
| Detective-first | Low friction, learning | Harm may occur before response | Early adoption; ambiguous rules |
| Central platform team approvals | Consistency | Bottleneck, shadow IT | Few high-risk decisions only |
| Self-service with guardrails | Speed | Needs mature guardrails and tests | Most routine changes |
| Customer-managed encryption keys | Control, audit | Key operations burden; outage if mismanaged | Regulated data |
| Centralised egress | Visibility, filtering | Cost, single bottleneck | Regulated or high-risk networks |
| Commitment discounts | Lower unit price | Lock-in, forecasting risk | Stable baseload |

### Measuring the cost of a control

For each major control track: exception requests per month, median time to decision, number of denials per month that were *legitimate work*, and engineer-hours per month spent operating it. A control that generates mostly false denials needs redesign.

## Decision guide

| Question | Prefer | Because |
| --- | --- | --- |
| Where do human users authenticate? | Central single sign-on with MFA | Revocation and audit |
| How do services authenticate? | Roles with short-lived credentials | No long-lived keys to leak |
| How do we limit blast radius? | Separate accounts and guardrail policies | Hard boundaries |
| How do we avoid surprise bills? | Budgets, anomaly alerts, idle policy, tag enforcement | Early detection |
| How do we prove compliance? | Automated evidence from logs and configuration rules | Repeatable audits |
| Who may change production? | A reviewed pipeline, not individuals | Separation of duties, traceability |
| How do we roll out a deny? | Canary OU, log analysis, then widen | Avoid self-inflicted outages |
| How do we handle residency? | Region deny, replication limits, evidence queries, named residual risk | Control chain with proof |
| How do we allocate shared costs? | Published driver rules, showback first | Incentive and trust |

## Knowledge consolidation

- Governance is **delegation within bounds**: least privilege, independent verification, evidence by construction.
- Organisation policy is **layered and inherited**; effective permission is an intersection. Keep policies few, owned, tested, versioned and rolled out through canaries.
- **Separation of duties** prevents a single identity from completing a sensitive process; enumerate the hidden paths around it, and state compensating controls where teams are small.
- **SCPs and equivalents** bound permissions; they never grant, usually exempt the management account, and can cause outages: write tests, query logs for impact, roll out gradually.
- **Detective** controls find drift; **corrective** automation needs scope, tests, logging and a kill switch.
- **Cost allocation** layers accounts, tags, hierarchy and published shared-cost rules; start with showback and track unallocated spend and unit cost.
- **Residency** is a chain of controls across regions, backups, logs, support access and global services; evidence it and name the residual risk.
- **Evidence** should be continuous, automated, complete, tamper-evident and linked to controls and risks.
- **Incident boundaries** (session, resource, account, OU, organisation) are designed in advance with a quarantine toolkit and inventoried cross-account trust.
- Every control has a **cost**: measure exceptions, false denials and operating effort.

## Exercises

**Exercise 1 — Policy catalogue.** Write catalogue entries for three organisation-level controls, including ID, scope, effect, owner, risk, test, exception route and review date.

**Exercise 2 — Separation of duties map.** For production infrastructure changes, access grants and policy changes, draw the path from "intent" to "applied", marking who performs each duty. Identify two hidden paths that would let one person bypass the separation, and the control that closes each.

**Exercise 3 — Safe deny rollout.** Plan the rollout of a new deny that blocks creation of internet gateways in a set of private accounts. Include the inventory query, canary selection, monitoring period, communication, rollback and success criteria.

**Exercise 4 — Cost allocation design.** An organisation has 12 accounts, a shared logging platform costing 9,000 per month and a shared network hub costing 5,000. Propose drivers for each, compute the allocation for three accounts using invented usage numbers, and describe what behaviour each driver encourages.

**Exercise 5 — Residency evidence.** For the claim "customer data is stored only in two approved regions", list at least six places data could leak across the boundary, the control for each, and the evidence query you would run nightly.

**Exercise 6 — Evidence pipeline.** Design an evidence record for one control: the check, its schedule, the identity that runs it, where results are stored, and who can alter them. Explain how it avoids "compliance by screenshot".

**Exercise 7 — Incident boundary drill.** Suppose a developer's session credentials were exposed at 10:30. Write the steps to contain the incident at credential, resource and account level, naming the policy or command for each and how you would verify containment from the audit log.

**Exercise 8 — Trade-off memo.** Write a one-page memo recommending either *account per team* or *account per environment* for an organisation of 40 engineers. State what you gain, what you pay, and what evidence would make you revisit the choice.

**Solution notes.**

*Exercise 1.* Good entries tie each control to a concrete risk and a test that tries the forbidden action. A control without an exception statement ("none, redesign through the board") is acceptable if stated; a control without an owner or test is not.

*Exercise 2.* Typical hidden paths: the ability to edit the pipeline definition that holds production credentials; the ability to change repository protection rules; the ability to pass a privileged role to a service one controls; and write access to the policy deployment role. Closures include protected branches, separate pipeline-edit approvals, passrole restrictions and alerting on changes to these objects.

*Exercise 3.* Look for an inventory of existing gateways in target accounts, a canary with a known owner, a week of denial monitoring, a named rollback (detach the policy) with a decision-maker, and a criterion such as "zero legitimate denials for seven days".

*Exercise 4.* Plausible drivers are gigabytes ingested for logging and data processed (or attachment count) for the network hub. State the incentives: teams reduce log volume or unnecessary cross-network traffic. A good answer notes the limit of the driver, for example that ingestion counts can punish teams for useful debug logging.

*Exercise 5.* Expect region policy, replication and snapshot copy restrictions, log destinations, support access, managed-service processing, global service metadata, backups, CI caches and analytics exports. The evidence queries should return counts of resources outside the approved list (expected zero) and be stored tamper-evidently.

*Exercise 6.* A strong record names a read-only identity running the check, a schedule, storage with object lock, a reproducible query, and a control owner who cannot alter results. It avoids screenshots because anyone can re-run the query and see the same result.

*Exercise 7.* Containment: disable the user or revoke sessions with an issued-before deny; isolate affected instances and snapshot first; apply a quarantine policy to the account if it spreads. Verify through audit logs that no new events from the exposed session appear after the cutoff, and review actions taken before it.

*Exercise 8.* Either answer can be defended. Look for explicit gains and costs (blast radius, baseline overhead, cost attribution, shared-service reach), the automation maturity assumed, and a measurable trigger for revisiting (for example vending time or exception counts).
