# T-CLD-03-B — Beginner Foundations

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-b"></a>
#### T-CLD-03-B — Beginner Foundations

## Why this matters

Most people first meet the cloud as a web console with hundreds of services and a "Create" button next to each. That is the wrong place to start. Four questions decide whether the next six months go well: *who* may act in this account, *where* do the things you create live, *what* does each cost while it exists, and *who is responsible* when something goes wrong.

Teams that skip those questions do not notice at first. Then an access key committed to a public repository is found by an automated scanner within minutes, or a forgotten database runs for three months, or an auditor asks "who deleted this?" and nobody can answer. These are *foundation* problems: they come from what was or was not set up before the first workload arrived.

This Beginner section teaches the vocabulary and mental models you need before building: what "cloud" means, how responsibility is split, what regions and zones are, why capacity can grow and shrink, how metering turns design choices into a bill, and how to keep a training account safe. It assumes no cloud experience and uses a fictional service, `orders-api` (a small web API with a relational database); nothing depends on other course material.

Provider names differ, so this text uses neutral terms. Commands and prices are **illustrative**; check your provider's current documentation and price list.

## First principles: renting capacity through an API

Before the cloud, running a service meant buying servers, placing them in a room, connecting cables, and waiting weeks for each change. The costs were mostly paid up front (capital expenditure), and you had to guess your peak demand in advance.

A **cloud provider** operates enormous datacentres and rents slices of them to customers. Three ideas define the model:

1. **On demand.** You request a resource (a virtual server, a storage bucket, a database) and receive it in seconds or minutes, without talking to a person.
2. **Through an API.** Every action — console click, command-line call, infrastructure-as-code run — is ultimately an authenticated request to the provider's programming interface. That is why identity (who may call the API) is the most important control you have.
3. **Metered.** You pay for what you consume — hours, gigabytes, requests — not for what you might need someday.

An analogy, and its limit: renting from the cloud is like using electricity from the grid and paying for the units used. The analogy fails in one way: the grid will not let you leave ten thousand lights on and bill you a month later. The cloud will, because *it does exactly what the authenticated caller requests*.

### Why organisations choose the cloud

The benefits are speed (a test environment in minutes), elasticity (capacity follows demand), no hardware ownership, global reach, managed services and pay-for-use. Each has an honest limit: speed also delivers mistakes faster; elasticity only works if the application is built for it; managed services still need configuring and securing; and pay-for-use has no natural ceiling.

The cloud is not "someone else's computer, so someone else's problem". It is someone else's computer, *with a contract that splits the problem between you and them*. Understanding that split is the next topic.

## Service models: IaaS, PaaS, SaaS and in between

Cloud services are grouped by how much of the technology stack the provider operates for you. Picture the stack as layers, from the building up to the data your users see:

```text
Layer                                   Who runs it?
------------------------------------    --------------------------------------
Data and its access rules               You   (almost always)
Application code                        You   (except in SaaS)
Runtime / libraries                     You, or the provider (PaaS and above)
Operating system                        You, or the provider (PaaS and above)
Virtualisation / hypervisor             Provider
Servers, storage, network hardware      Provider
Buildings, power, cooling, guards       Provider
```

The service models draw the line at different heights:

| Model | You manage | Provider manages | Example |
| --- | --- | --- | --- |
| IaaS (infrastructure) | Operating system, runtime, application, data | Hardware, virtualisation | Virtual machines, block disks, virtual networks |
| PaaS (platform) | Application and data | Operating system, runtime, scaling | Managed application platforms, managed databases |
| SaaS (software) | Configuration, users and your data | Almost everything | Hosted email, hosted ticketing |
| Containers / serverless | Application packaging or functions | Underlying hosts | Container services, function platforms |

Moving up the stack removes operational *tasks*, not responsibility: with a managed database the provider patches the engine, but you still decide who can connect, whether data is encrypted and how long backups live. It also usually reduces control and portability; a convenient platform feature can become an expensive dependency (a trade-off revisited at Professional and Expert level).

### Three ways to run `orders-api`

On **virtual machines** you operate the operating system, the database engine, backups and the API. With a **container service plus a managed database** you operate the image, API configuration, schema and access; the provider runs hosts and engine patches. On a **platform that deploys code directly** you operate code and data only. None is "best"; each moves a different amount of daily work to the provider, and the skill is to choose deliberately and write down why.

## Shared responsibility: who patches, who configures, who answers

Every provider publishes a **shared responsibility model**. In one sentence: *the provider is responsible for the security **of** the cloud; you are responsible for security **in** the cloud.* The first covers the datacentre, hardware and the virtualisation layer. The second covers what you build and configure on top.

| Layer | Typical owner |
| --- | --- |
| Physical datacentre and hypervisor | Provider |
| Guest operating-system patching on virtual machines | You |
| Managed database engine patches | Provider — but your schema, access and backups remain yours |
| Application code and the policies you write | You |
| Firewall and security-group rules you configure | You |
| Encryption setting on a storage bucket | You (the provider offers it; you must switch it on or verify it is on) |

A useful test for any incident: *did the provider fail to deliver what they promised, or did we configure something we should not have?* Most publicly reported cloud security incidents are the second kind: a public bucket, a leaked credential, an over-broad permission, a database exposed to the internet. Typical misreadings are "it is managed, so it is backed up" and "it is in the cloud, so it is always available"; each ends in data loss or an outage the provider did not cause.

## Regions and availability zones

The provider's infrastructure is arranged geographically.

- A **region** is a geographic area (for example, a metropolitan area or a country) containing several independent datacentre groups. Regions are far enough apart that one disaster is unlikely to affect two of them.
- An **availability zone (AZ)** is one or more physically separate datacentres *within* a region, with independent power, cooling and networking, connected to the others by fast links.

```text
Provider
├── Region A (e.g. a country)
│   ├── Zone A1   (datacentre group, own power and network)
│   ├── Zone A2
│   └── Zone A3
└── Region B
    ├── Zone B1
    ├── Zone B2
    └── Zone B3
```

What each boundary protects against:

| Failure | Single instance | Two zones in one region | Two regions |
| --- | --- | --- | --- |
| One server fails | Outage until replaced | Survives if another instance exists | Survives |
| One zone loses power or network | Outage if it was in that zone | Survives *if capacity and data are arranged to support it* | Survives |
| A whole region is unavailable | Outage | Outage | Survives *if designed and tested* |
| Your own bad deployment or a deleted database | Outage | Outage (replicated data replicates the mistake) | Outage unless backups or delayed copies exist |

The last row is the one beginners miss: **redundancy does not protect against your own mistakes.** If you delete a table, a replica deletes it a moment later. Backups, versioning and access control protect against mistakes; zones protect against infrastructure failures.

### Choosing a region

Consider latency to your users, data-residency law, whether the region offers the services you plan to use, price differences, and data-transfer cost between components. For a training account, pick one region close to you, write it down and stay there; resources scattered across regions are a classic source of forgotten cost.

### "Multi-AZ" is a design, not a checkbox

A **multi-AZ** deployment keeps working if one zone fails. That needs instances in more than one zone behind something that routes around failure; enough spare capacity that survivors can carry the whole load (two zones each at 80 % cannot absorb one failing); and data available in the surviving zone, such as a managed standby.

A diagram showing two zones while one instance runs is aspirational. Either fix the diagram or fix the infrastructure.

## Elasticity: capacity that follows demand

**Elasticity** means adding capacity when demand rises and removing it when demand falls. Compare a shop whose traffic peaks for two hours a day: the traditional approach buys servers for the peak and runs them all day; the elastic approach adds servers for the peak and removes them afterwards.

Illustrative arithmetic: suppose a server costs 0.10 per hour. The shop needs 10 servers for two hours and 2 servers the rest of the day.

```text
Fixed for the peak:   10 servers x 24 h x 0.10 = 24.00 per day
Elastic:              (10 x 2 h + 2 x 22 h) x 0.10 = (20 + 44) x 0.10 = 6.40 per day
```

Elasticity only happens if the application supports it. It must be **stateless where it scales** (state belongs in a database, cache or object store, not in an instance's memory or disk); **new instances must start and configure themselves** without a person; and **something must decide when to scale** from a measurable signal such as request rate, with a limit that stops scaling from becoming an unbounded bill. The cheapest resource is also one that is turned off: a lab that runs only during working hours costs roughly a quarter of one that runs continuously.

## Metering: how design choices become a bill

Cloud billing is a long list of **meters**: each service counts something and multiplies it by a price. Understanding the *shape* of the meters is more useful than memorising prices.

| Meter type | Counted as | Examples | Beginner trap |
| --- | --- | --- | --- |
| Time | Hours or seconds a resource exists | Virtual machines, load balancers, database instances, NAT gateways | A stopped-looking thing that still exists may still be billed |
| Capacity | Gigabytes provisioned per month | Disks, snapshots, buckets | Provisioned disk is billed even if mostly empty |
| Requests | Number of API calls or operations | Object storage requests, function invocations, queue messages | A loop that retries forever has a bill |
| Data transfer | Gigabytes moved | Out to the internet, between zones or regions | Traffic *into* the provider is often free; traffic *out* usually is not |

Three habits help. Before creating a resource, ask "what is the meter?" and read the pricing page. Know which resources bill by time even when idle (load balancers, NAT gateways, managed databases, reserved addresses, provisioned disks, snapshots); they survive after a lab is "finished". And watch storage and data transfer weekly, because they grow silently.

> **Warning.** Billing data usually lags reality by hours, sometimes by a day. A budget alert is a smoke detector, not a firewall: it tells you spending is high, it does not stop the spending. Do not rely on it as the only control.

The surprising line items are usually the NAT gateway or load balancer: they do not look like "a server", yet they bill every hour they exist.

## Cost and identity: the two controls that matter first

Two things cause the majority of painful early-cloud stories: **spending you did not intend** and **access you did not intend**. They are connected: whoever holds your credentials can create spending.

### Identity in three sentences

- An **identity** is something that can authenticate to the provider: a person, or a program such as a build job or a running service.
- **Authentication** proves who it is; **authorisation** (permissions or policies) decides what it may do.
- The **root user** (the original account owner) can do everything and cannot be restricted by normal permission policies; it exists for recovery and a few rare tasks, not for daily work.

| Identity type | Use | Rule |
| --- | --- | --- |
| Root user | Account recovery and rare account-level tasks | Strong unique password, multi-factor authentication (MFA), no access keys, almost never used |
| Human user (via single sign-on role or individual user) | Day-to-day console and command-line work | MFA required; least privilege; one person per identity |
| Workload role | A service, function or build job calling the API | Short-lived credentials issued by the platform; never a long-lived key on disk |

### Credentials: the golden rules

1. **Never commit credentials to source control**, not even in "temporary" files. Scanners watch public repositories continuously and abuse exposed keys within minutes.
2. **Prefer short-lived credentials** (roles, tokens that expire in hours) over long-lived keys.
3. **Do not share logins**; the audit trail could not tell the people apart.
4. **Enable MFA on every human identity.**
5. **If a key is exposed, rotate it immediately.** Deleting the commit is not enough; history and forks keep the secret.

Obtain short-lived credentials through single sign-on rather than a key file, and run a "who am I" command (for example `provider-cli identity whoami`) before anything destructive. Many costly mistakes happen because someone was logged into the wrong account.

## A safe account mental model

Think of a cloud account as **a fenced plot with one front gate, a meter on the wall and a logbook at the door.**

| Part of the metaphor | Real thing | What you must set up |
| --- | --- | --- |
| The fence | Account (or subscription / project) boundary | One account for training, separate from anything important |
| The front gate | Identity and access management | MFA, no root use, roles instead of shared keys |
| The meter on the wall | Billing and budgets | Budget with alerts before the first resource |
| The logbook | Audit logging | Audit trail enabled, stored where you cannot easily delete it |
| Labels and demolition plan | Tags and teardown runbook | Owner and expiry tags; ordered teardown; a check that the bill goes quiet |

A training account is a good first account precisely because it has *nothing important in it*. If it goes wrong, the loss is a small bill and an afternoon. The same habits applied to a production account are what Intermediate and Professional levels teach.

### The first hour in a new account: a checklist

Do these in order before building anything.

```text
1. Secure the root user
   - Strong unique password stored in a password manager
   - MFA enabled (a hardware key or authenticator app)
   - Delete any root access keys; do not create them
   - Set a monitored recovery email and phone number
2. Create a day-to-day identity (not root)
   - A named human identity or a single sign-on role with only the permissions you need
   - MFA required on it
3. Set a budget with alerts at 50 %, 80 % and 100 % plus a forecast alert, sent to an address you read
4. Turn on audit logging
   - Record account activity to a store in the same account (or better, a separate one)
5. Choose one region and write it down
6. Decide your tags
   - Project, Owner, Environment, and an ExpiryDate for anything temporary
7. Write the teardown note
   - "Everything created here can be removed by <how>"
```

## Where would the service live? A placement table

When planning a service, writing a table that maps each component from "laptop" to "cloud" forces clarity:

| Component | Local development | Typical cloud shape |
| --- | --- | --- |
| API | Container on a laptop | Container service or virtual machines |
| Database | Container with a volume | Managed relational database |
| Edge | `localhost` port | Load balancer with TLS |
| Logs and secrets | Console, `.env` file | Central log service, secrets service |

A reference picture of a small, sensible shape for `orders-api`:

```text
Internet
   |
[ Load balancer ]  <- TLS certificate, security group allows 443 from anywhere
   |        |
[API zone A] [API zone B]   <- security group allows traffic only from the load balancer
   |        |
[ Managed database, primary in zone A, standby in zone B ]
        <- security group allows traffic only from the API instances
```

Notice what the diagram says about *access*: each layer accepts traffic only from the layer in front of it. The database has no route from the internet. Designing who can reach what is as much a foundation decision as choosing the region.

## What can go wrong: common beginner mistakes and how they look

| Mistake | How it looks | Prevention |
| --- | --- | --- |
| Using root for daily work | Everything works; there is no way to limit or trace it | Create a limited identity on day one |
| Access key in a repository | Unexpected resources in unexpected regions; a provider warning email | Short-lived credentials; secret scanning; rotate immediately |
| No budget alarm | A surprising invoice at month end | Budget and alerts before the first resource |
| Logged into the wrong account | A "delete" affects the wrong environment | `whoami` before destructive actions |
| Treating a managed service as maintenance-free | Backups never configured | Read the shared-responsibility notes per service |
| Forgetting idle resources | A load balancer or database runs for weeks | Expiry tags; teardown checklist |

## Knowledge consolidation

- The cloud is **on-demand, API-driven and metered**: whoever holds valid credentials can create cost and exposure.
- **IaaS, PaaS and SaaS** differ in how much of the stack the provider operates. Moving up removes tasks, not responsibility.
- **Shared responsibility:** the provider secures *the cloud*; you secure *what you put in it* — configuration, identity, data, access rules and backups.
- A **region** is a geographic area; an **availability zone** is an isolated datacentre group inside it. Multi-AZ needs instances, spare capacity and data in more than one zone.
- Redundancy protects against **infrastructure failure**, not against your own mistakes; backups and access control cover those.
- **Elasticity** saves money only if the application is stateless where it scales and something decides when to scale.
- **Meters** turn design into a bill. Ask "what is the meter?" before creating a resource, and know which things bill just by existing.
- **Identity first:** do not use root for daily work; use MFA; use short-lived credentials; never commit secrets.
- **Budget before resources.** An alert is a smoke detector, not a firewall.
- A **safe account** has a fence (account), a gate (identity), a meter (budget), a logbook (audit), labels (tags) and a demolition plan (teardown).

## Exercises

**Exercise 1 — Classify and assign.** For (a) hosted email, (b) a managed relational database, (c) a virtual machine and (d) a function triggered by a file upload, state whether it is closest to IaaS, PaaS, SaaS or serverless and name one thing *you* must still configure or secure. Then say who owns each: patching the physical host kernel, patching a VM's operating system, enabling bucket encryption, deciding who may delete a database, and the backup retention of a managed database.

**Exercise 2 — Draw it.** Draw a diagram of a small service in the cloud with a user, a load balancer, two application instances in two AZs and a database. Mark who is responsible for patching each box, and which boxes accept traffic from which others.

**Exercise 3 — Survive a zone.** Using your Exercise 2 diagram: if one zone fails, which boxes stop working? Does the system still serve users? If each application instance runs at 70 % CPU on its own, what happens to the survivor? What would you change?

**Exercise 4 — Elasticity arithmetic.** A service needs 8 instances for 3 hours a day and 2 instances for the other 21 hours. An instance costs 0.12 per hour. Compute the daily cost (a) with fixed capacity for the peak and (b) with elastic capacity. State two reasons the elastic number might not be achievable in practice.

**Exercise 5 — Read the meter.** Choose one service from a provider's pricing page (a managed database, load balancer or NAT gateway). List its meters, which of them accrue when nothing is being used, and the monthly cost of leaving a small instance running for 30 days. Label your numbers as taken from the pricing page on a given date.

**Solution notes.**

*Exercise 1.* (a) SaaS: users, sharing rules, retention. (b) PaaS: access, networking, backups, parameters, schema. (c) IaaS: OS, runtime and application security. (d) serverless: code, permissions, triggers, timeouts. Ownership: provider, you, you (the provider offers it; you enable or verify it), you, you. If you wrote "provider" for encryption or backup retention, re-read the shared-responsibility table: configuration choices are yours.

*Exercise 2.* A good diagram shows the load balancer in front, instances in separate zones and a database that accepts traffic only from the instances. The provider patches the physical layer and a managed engine; you patch instance operating systems (unless a platform hides them) and your application. Marks go for showing access direction, not only boxes.

*Exercise 3.* The failed zone's instance (and possibly the database primary) stops; the load balancer should route to the survivor and a managed standby should be promoted. If each instance already ran at 70 %, the survivor would need 140 % and will saturate. Fixes: more instances per zone, a lower steady utilisation target, or autoscaling within the surviving zone.

*Exercise 4.* Fixed: 8 × 24 × 0.12 = 23.04. Elastic: (8 × 3 + 2 × 21) × 0.12 = 7.92. Reasons it may not be achievable: instances take minutes to start while the peak arrives faster; state in memory prevents removal; zone redundancy needs a higher minimum; scaling signals lag; the database does not scale with the application tier.

*Exercise 5.* Answers depend on service and region. A correct answer lists the *idle* meters (instance hours, provisioned storage, hourly gateway charges), not just usage meters, and cites the date of the price list.
