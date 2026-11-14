# T-CLD-03-B — Beginner Foundations

*Chapter: [T-CLD-03 — Cloud Foundations and Governance](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-03-b"></a>
#### T-CLD-03-B — Beginner Foundations

**What "cloud" means.** Cloud providers rent computing, storage and networking on demand through APIs. You pay for use, and you configure — and must secure — what you create.

**Service models**

| Model | You manage | Provider manages | Example |
| --- | --- | --- | --- |
| IaaS | Operating system, runtime, application, data | Hardware, virtualisation | Virtual machines |
| PaaS | Application and data | Operating system, runtime, scaling | Managed application platforms |
| SaaS | Configuration and data | Almost everything | Hosted email |
| Containers / serverless | Application packaging or functions | Underlying hosts | Container services, functions |

**Shared responsibility.**

| Layer | Typical owner |
| --- | --- |
| Physical datacentre and hypervisor | Provider |
| Guest operating-system patching on virtual machines | You |
| Managed database engine patches | Provider — but your schema, access and backups remain yours |
| Application code and the policies you write | You |
| Firewall and security-group rules you configure | You |

**Regions and availability zones.** A *region* is a geographic area; an *availability zone* (AZ) is one or more isolated datacentres within it. A single-AZ deployment fails when that AZ fails; a multi-AZ design survives that failure if capacity and data are arranged to support it. A single-node deployment survives neither in any useful sense.

**Where would the service live?** A placement table forces clarity:

| Component | Local development | Typical cloud shape |
| --- | --- | --- |
| API | Container on a laptop | Container service or virtual machines |
| Database | Container with a volume | Managed relational database, or a container if justified |
| Edge | `localhost` port | Load balancer with TLS |
| Logs | Console output | Central log service |

**First safety rules.** Use a training account with a budget alarm *before* creating resources. Never use the root user for daily work. Never put access keys in source control. Tag resources and know how to delete them.

**Exercise.** Draw a diagram of a small service in the cloud with a user, a load balancer, two application instances in two AZs and a database. Mark who is responsible for patching each box.
