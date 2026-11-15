# T-CLD-05-B — Beginner Foundations

*Chapter: [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-05-b"></a>
#### T-CLD-05-B — Beginner Foundations

## Why this matters

Every system that matters to someone will eventually be broken by something ordinary: a process crashes, a disk fills, a data centre loses power, a deployment ships a bug, an engineer deletes the wrong thing. None of these is exotic. Over a long enough period they are certain. The question a team can actually influence is not *whether* a failure happens but *what the user experiences when it does*, and how quickly the team can get back to normal.

That is what this chapter calls **architecture**: the set of decisions that determine how a system behaves when things go wrong. The cloud changes who owns which part of failure: the provider runs buildings, power, network and physical hosts; you decide how many copies run, where, where data lives and what happens when a piece disappears.

This Beginner section assumes you have seen a terminal and a cloud console but have not designed a resilient system. It uses a fictional service, `orders-api`, on AWS. You will learn the building blocks (compute, storage, load balancing, databases, auto scaling), the geography (regions and Availability Zones), and how to walk a small topology and say, component by component, what happens when each one fails.

**Conventions.** *Version-specific* marks a behaviour, default, limit or timing that AWS can change; verify it in current documentation. *Illustrative* marks a shape of result, not a measurement. Angle brackets such as `<arn>` are placeholders for values from your own practice account.

## First principles: failure and failure domains

A **failure domain** is the set of things that fail together. If two things share a failure domain, one event takes out both, so having two of them gives you less protection than it appears to.

| Failure domain | Example event | What it takes out |
| --- | --- | --- |
| Host (virtual machine or physical server) | Hardware fault, host maintenance | Everything on that host |
| Availability Zone (AZ) | Power or cooling problem, network fault in one data-centre group | Everything you placed in that AZ |
| Region | Rare regional service impairment | Everything placed in that region |
| Account | Compromised credentials, accidental mass deletion | Everything in that account, including backups stored beside it |
| Deployment | A bad release | Every copy running that release, in every AZ |

Redundancy only protects when the copies sit in *different* failure domains for *that* failure: two servers in one AZ survive a host fault but not an AZ fault. Some domains are invisible on a diagram: a shared release, database or certificate.

## AWS geography: regions and Availability Zones

A **Region** is a geographic area, such as one in Ireland or one in the eastern United States, that contains several isolated groups of data centres. Each isolated group is an **Availability Zone**. AZs within a region are separated enough that a local problem (a power fault, a flood of a single site) is unlikely to affect more than one, and connected by fast, low-latency private networking so that you can run one system across them.

Practical consequences:

- **Regions are independent by design.** Resources exist in another region only if you copy them.
- **AZs are your first and cheapest failure boundary.** Spreading a service across two or three AZs in one region is the standard way to survive the loss of one data-centre group.
- **AZ names can differ between accounts.** The label `eu-west-1a` in your account may point at a different physical zone from `eu-west-1a` in a colleague's. If you need to coordinate placement across accounts, use the AZ ID (for example `euw1-az1`), which is consistent. *Version-specific:* check how AWS currently documents AZ names and IDs.

Most resources have a **scope**, which tells you what a failure of each geography does to them:

| Resource | Scope | What this means for resilience |
| --- | --- | --- |
| Subnet | One AZ | A subnet lives in exactly one AZ; to use two AZs you need at least two subnets |
| EC2 instance (virtual server) | One AZ | Lost if its AZ is lost |
| EBS volume (block disk) | One AZ | Replicated inside the AZ, not across AZs; take snapshots for more |
| S3 bucket (object storage) | Region | Standard storage keeps data across multiple AZs; you pick the region |
| Load balancer | Nodes in the AZs you enable | Enable at least two AZs |
| RDS database | One AZ per instance, or two with Multi-AZ | Single-AZ means the AZ is a single point of failure |

*Version-specific:* replication behaviour per storage class and database engine changes over time; verify in current documentation.

## Building blocks

| Building block | Examples | Handles | Does not handle |
| --- | --- | --- | --- |
| Compute (instances, containers, functions) | EC2, ECS, Lambda | Replacement of a failed copy by a scheduler | A bug present in every copy |
| Block storage | EBS | Disk media faults inside one AZ | AZ loss, deletion, corruption |
| Object storage | S3 | Loss of a disk or AZ (standard classes) | Accidental deletion unless versioning or backup exists |
| Load balancer | ALB, NLB | Failure of some targets | Failure of all targets; a bug that returns 200 while broken |
| Database | RDS, Aurora, DynamoDB | Host failure (with Multi-AZ or managed replication) | A bad query that deletes data |

Each component is either **stateless** (holds nothing that must survive its loss) or **stateful**. Compute and load balancers should be stateless. Databases, object stores and queues are stateful. The most reliable rule in this chapter: **keep the compute stateless** (no uploads on local disk, no sessions only in memory), **and concentrate resilience effort on the few stateful pieces.**

**Compute.** An EC2 instance is a virtual server; an Auto Scaling group keeps a fleet of identical instances created from a launch template and replaces any that fail health checks. A container service such as ECS keeps a **desired count** of tasks running from a task definition; if one stops, the scheduler starts another. Lambda runs code per request and places it across AZs for you. In all three, instances, tasks and function environments are **disposable**: a design that needs one particular copy to survive will eventually fail.

**Storage.** EBS is a disk attached to one server in one AZ; snapshot it to get a copy elsewhere. S3 stores objects by name across a region and is not versioned by default, so an overwrite or delete is permanent unless versioning is on. EFS is a shared filesystem mountable from several AZs; it is not a database.

**Durability versus availability.** Durability is the chance data still exists later; availability is the chance you can reach it now. Durability against hardware failure says nothing about *you* deleting something, hence backups, versioning and separate accounts.

## Load balancing and health checks

A **load balancer** is the front door. It accepts connections from users, picks a healthy **target** (a task or instance), and forwards the request. Targets are grouped into a **target group**. The load balancer repeatedly sends a **health check** request to each target, for example `GET /health`, and only sends user traffic to targets that pass.

Four settings define how quickly a bad target is noticed and how quickly a good one is trusted. The names below are the ALB target-group settings:

| Setting | Meaning | Typical illustrative value |
| --- | --- | --- |
| Interval | Seconds between checks | 30 (shorter for faster detection, more load) |
| Timeout | Seconds to wait for a reply | 5 |
| Unhealthy threshold | Consecutive failures before a target is marked unhealthy | 2 to 3 |
| Healthy threshold | Consecutive passes before a target is marked healthy | 2 to 5 |

*Version-specific:* defaults and allowed ranges differ by load-balancer type and change over time. Read the current documentation for your type.

Detection time is roughly `interval × unhealthy threshold`. With an interval of 10 seconds and an unhealthy threshold of 3, a dead target keeps receiving a share of traffic for up to about 30 seconds. That window is part of your recovery time. The load balancer also has **connection draining** (*deregistration delay* on ALB): when a target is removed on purpose, in-flight requests get time to finish. *Version-specific:* the default delay has historically been several minutes; verify it.

A **health check endpoint** deserves care. A check that always returns 200 hides every problem. A check that calls the database and fails whenever the database is slow can make every target look unhealthy at once and turn a small blip into a total outage. The Intermediate section returns to this trade-off. For now: a health check should answer "should this target receive traffic now?" honestly but simply.

## Databases at a glance

| Option | Survives host failure? | Survives AZ failure? | Beginner note |
| --- | --- | --- | --- |
| Single-instance database | No | No | Fine for learning, not a resilient production answer |
| Multi-AZ managed database | Yes | Yes, after a failover pause | The standard first step for durable data |
| Read replica | Not by itself | Not by itself | Mostly for read scale; promotion is a separate step |
| Backup / snapshot | Restores afterwards | Restores afterwards | Protects against deletion and corruption; slow |

**Failover** keeps the service going by switching to a standby with almost the same data. **Backup** restores data to an earlier moment. Failover protects against a machine failing; backup protects against *you* making a mistake. Replication copies a mistake as faithfully as good data, so it does not replace backup.

## Auto scaling: healing and growing are different jobs

An Auto Scaling group has three numbers: **minimum**, **desired** and **maximum** capacity.

- *Healing* keeps the count at the desired number. If an instance dies, a replacement is launched. This is a resilience feature.
- *Scaling* changes the desired number in response to load, between minimum and maximum. This is a capacity feature.

A scaling policy such as "keep average CPU near 50%" increases the desired count when traffic rises and decreases it when traffic falls. Scaling takes minutes (start, pull, boot, pass health checks), so keep headroom for sudden spikes, and set a sensible maximum because a runaway scale-out is also a cost incident.

A group can span AZs, keeping instances balanced and replacing capacity in the remaining AZs if one is impaired, provided the maximum and quota allow it.

## Walk a small service topology

Here is the `orders-api` topology used throughout the chapter.

```text
                  Users
                    |
                    v
             DNS name (orders.example.com)
                    |
                    v
        Application Load Balancer (nodes in AZ-a and AZ-b)
              |                       |
              v                       v
      AZ-a: private subnet     AZ-b: private subnet
      +----------------+       +----------------+
      | orders-api     |       | orders-api     |   <- ECS service, desired count 2
      | task 1         |       | task 2         |
      +-------+--------+       +--------+-------+
              \                        /
               v                      v
        +-------------------------------------+
        | Managed database                     |
        | primary in AZ-a, standby in AZ-b     |
        +-------------------------------------+
              |
        Object storage (uploads, region-wide)
        Central logs and metrics (outside the tasks)
```

Walk a single request:

1. The user's device asks DNS for `orders.example.com` and receives the load balancer's addresses.
2. The request reaches a load-balancer node in AZ-a or AZ-b.
3. The load balancer picks a healthy task and forwards the request.
4. The task reads and writes the database over the private network.
5. The task stores an uploaded file in object storage and writes logs to the central log service.
6. The response travels back the same way.

Now fail each piece, one at a time, and write down what the user sees.

| What fails | What happens | Visible to the user? |
| --- | --- | --- |
| Task 1 crashes | The load balancer's health check fails; traffic goes to task 2; the scheduler starts a replacement task | Possibly a few failed requests during the detection window; then none |
| AZ-a loses power | Task 1, the AZ-a load-balancer node and the database primary are gone; the database fails over to AZ-b; the load balancer uses AZ-b only | A short database failover pause; reduced capacity afterwards |
| Database primary host fails | Failover to the standby | A brief write interruption; connections must reconnect |
| A bad release is deployed to both tasks | Both tasks run the bug | An outage or errors until rollback; nothing in this topology prevents it |
| Someone deletes rows in the database | The standby copied the deletion | Data loss until restored from backup |

The table is the real skill of this section. For any diagram, you should be able to take each box and each arrow and write the corresponding row. The boxes you cannot fill in are your unknowns.

## The self-healing test

The simplest drill is to stop a running task and watch the scheduler start a replacement while the load balancer routes around the gap. With one task, there will be a short outage, which teaches why one instance is not high availability.

```bash
aws ecs list-tasks --cluster orders --service-name orders-api
aws ecs stop-task --cluster orders --task <task-arn> --reason "resilience drill"
while true; do curl -s -o /dev/null -w '%{http_code}\n' https://orders.example.com/health; sleep 2; done
```

Run it only on a practice service you own. Watch `aws ecs describe-services` events and `aws elbv2 describe-target-health` in another terminal.

**Honest wording.** "ECS replaced the task in about 40 seconds with `desired_count` 1" is true; "the system is highly available" is not.

## Worked example: what each design tolerates

Suppose `orders-api` runs behind a load balancer across two AZs.

| Design | One task stops | One AZ is lost | Database host fails | A bad release goes out |
| --- | --- | --- | --- | --- |
| 1 task, 1 AZ, single-instance database | Outage until the scheduler starts a replacement (tens of seconds to minutes) | Full outage until recovery | Outage; data restored to the last backup (RPO applies) | Outage until rollback |
| 2 tasks across 2 AZs, single-instance database | No visible outage; the load balancer routes around the gap | Half capacity; service continues | Outage until recovery or restore | Both tasks run the bad code unless a rollout is gradual |
| 2 tasks across 2 AZs, database with a standby in another AZ | No visible outage | Continues after a brief database failover | Short interruption during failover | Needs rollout controls; replication does not protect against bad releases |

Each added component protects against a specific failure and nothing else. Replication does not protect against deleting rows; two tasks do not protect against shipping a bug.

## Capacity: what "survives an AZ" costs

Surviving an AZ loss means the remaining AZs can carry the *whole* load. That has a price, and it is easy to underestimate.

Suppose peak traffic needs 12 tasks.

| Layout | Tasks per AZ | Total tasks | Tasks left after losing one AZ | Enough for 12? |
| --- | --- | --- | --- | --- |
| 2 AZs, sized for peak in total | 6 and 6 | 12 | 6 | No: half capacity at peak |
| 2 AZs, each able to carry peak | 12 and 12 | 24 | 12 | Yes, at 100% extra capacity |
| 3 AZs, spread evenly, sized to survive one loss | 6, 6, 6 | 18 | 12 | Yes, at 50% extra capacity |

More AZs make AZ-loss tolerance cheaper in extra capacity. If you say "we survive an AZ outage", the follow-up question is: *at what load, and with how much spare capacity already running?* Prefer capacity that is already running; capacity you plan to start after a failure may be contended.

## RTO and RPO with a number attached

The **recovery time objective (RTO)** is how long you may be down; the **recovery point objective (RPO)** is how much recent data you may lose. For `orders-api`: an RTO of 30 minutes means the service must be back within half an hour of a major failure; RPO of 5 minutes means losing at most five minutes of orders is acceptable. Those two numbers drive spending. A 5-minute RPO needs frequent backups or replication; a 24-hour RPO is satisfied by a nightly snapshot.

Availability is stated as a percentage, but it is more intuitive as downtime per 30-day month (43,200 minutes):

| Availability | Downtime per 30 days |
| --- | --- |
| 99% | about 7 hours 12 minutes |
| 99.9% | about 43 minutes |
| 99.99% | about 4 minutes 19 seconds |

A target with a number can be tested; one without is a wish.

## Desired count one versus two

With `desired_count` 1, stopping the task leaves the load balancer with no healthy target, so users see 5xx errors. With 2, one target remains healthy and users are served throughout. Check the numbers with `aws ecs describe-services` and `aws elbv2 describe-target-health --target-group-arn <arn>`, and record what you observed, with timestamps, rather than what you expected.

A record of a drill can be this simple:

```text
Drill:        stop one orders-api task
Environment:  practice account, orders cluster
Hypothesis:   with desired count 2 across two AZs, users see no errors
Start:        10:02:10   stop-task issued
Observed:     10:02:12   target health: one target draining
              10:02:14   curl loop: all 200 (one failed request at 10:02:13)
              10:02:51   replacement task running, target healthy
Result:       one failed request; full capacity restored in 41 seconds (illustrative)
Not proven:   AZ loss, database failover, bad release
```

## Common mistakes

- Calling a deployment "highly available" because it uses a managed service. Ask which failures were actually tested.
- Placing both tasks in the same AZ (two copies, one failure domain) or storing uploads on a task's local disk.
- Having backups but never restoring one. An untested backup is a hope.
- Treating replication as backup. A deletion is replicated within seconds.

## Knowledge consolidation

- Redundancy helps only across different failure domains, and only for the failures it covers.
- Keep compute stateless; failover keeps service going, backup restores data, and neither replaces the other.
- A claim is true when a recorded test supports it.

## Exercises

**Exercise 1 — Label the diagram.** Draw users, load balancer, two AZs with a task in each, scheduler, database and log service. Colour stateless boxes one way and stateful boxes another, and write the failure each box protects against.

**Exercise 2 — Fail each box.** For your own diagram, produce a table like the one in the topology walk: component, what happens, what the user sees. 

**Exercise 3 — Capacity.** Your peak needs 9 tasks. Calculate the total tasks needed to survive the loss of one AZ with 2 AZs and with 3 AZs, and the extra capacity as a percentage.

**Exercise 4 — Run the drill.** In a practice environment, run the stop-task drill with desired count 1 and 2, record the HTTP status over time and write the difference in two sentences.

**Solution notes.**

*Exercise 1.* Stateless: load balancer nodes, tasks. Stateful: database, object storage, logs. Protection: tasks are replaced by the scheduler; load balancer nodes by AZ spread; the database by its standby; object storage by multi-AZ storage inside the region. A good diagram also marks what is *not* protected, such as deletion and bad releases.

*Exercise 2.* Every row should have an observable symptom; rows you cannot fill in are tests to schedule.

*Exercise 3.* For 9 tasks: with 2 AZs each AZ must hold 9, total 18, extra 100%. With 3 AZs each AZ holds 5 (rounding up 9 / 2 = 4.5), total 15 so that two AZs hold 10, extra about 67%. 

*Exercise 4.* With one task you should see a run of 5xx or connection errors until the replacement is healthy. With two, you should see zero or very few failures. If you saw failures with two, check whether both tasks were in the same AZ, whether the target group had registered both and the health-check timing.
