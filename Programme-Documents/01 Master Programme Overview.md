# Medium Term Professional Development Plan

# Certification-led professional development program for 
Ruben Ferreira – Upper Intermediate Front-end Developer

# Nov 2026 – March 2027(align with DVT FYE27)

# Executive overview

Purpose: transition from primarily front-end web engineering into cloud/platform engineering, supported by Python, TypeScript, infrastructure automation, Kubernetes, observability and AI-enabled developer tooling. The programme is a personal development proposal; it is not an accredited qualification or an approved DVT training plan.

| Parameter | Programme decision |
| --- | --- |
| Structure | Four 12-week teaching modules, each followed by one review/buffer week |
| Effort | Target 8–12 hours per week; adjust to workload and sustainability |
| Hard requirement | DVT PDP: Datadog Fundamentals certification, due 31 March 2027 |
| Internal target | First Datadog attempt: December 2026 |
| Outcomes | 10 proposed credential targets: 8 priority/optional and 2 stretch; practical capstone |
| Primary stack | Linux, Docker, AWS, Terraform, GitLab CI/CD, Kubernetes, Helm, GitOps, Backstage, observability |

# Why the pivot?

DVT competency presentation, 12 Nov 2026 (user-supplied transcript): Thean Hoogenboezem described softer growth in front-end, continued Angular relevance in enterprises, higher demand for full-stack/back-end skills, and cloud/platform engineering with DevOps as a growth area. Saurabh Agrawal described a broader AI-agent orchestration direction. These statements express DVT's internal framing and do not constitute a verified count of current vacancies.

Career hypothesis: existing Angular, TypeScript, Python, NestJS, GitLab, AWS/Firebase exposure and finance-domain experience provide an entry point. The largest gaps are Linux administration, networking, cloud identity, Infrastructure as Code, container orchestration and operational reliability.

# Learning model and success criteria

- Every topic must produce an artefact: repository, Terraform module, diagram, working system, runbook or incident report.

- Certification attempts are scheduled after readiness checks, not automatically on the calendar date.

- DVT placement discussions should begin after 12 weeks, then again after 24 and 36 weeks.

- Use low-cost local labs; clean up all cloud resources; configure billing budgets and alerts.

- Separate certificate evidence, practical evidence and manager sign-off in the physical binder.

# Four-module summary

| Module | Focus | Exit evidence |
| --- | --- | --- |
| 1 · Weeks 1–12 | Datadog, Linux, networks, Docker, AWS basics | Datadog credential + monitored containerised app |
| 2 · Weeks 13–24 | AWS, Terraform, identity, CI/CD | Automated and securely deployed cloud stack |
| 3 · Weeks 25–36 | Kubernetes, GitOps, Helm, self-service platform | Developer platform MVP with golden path |
| 4 · Weeks 37–48 | SRE, K8s admin, Backstage, security, AI ops | Defended production-oriented platform capstone |

# Certification roadmap

| Credential | Category | Target |
| --- | --- | --- |
| Datadog Fundamentals | Mandatory DVT PDP | 18 Dec 2026 |
| Datadog Log Management Fundamentals | Additional / optional | Jan–Feb 2027 |
| Datadog APM & Distributed Tracing Fundamentals | Additional / optional | Feb 2027 |
| AWS Certified Cloud Practitioner | Foundation target | Mar 2027 |
| HashiCorp Terraform Associate (004) | Core target | Apr 2027 |
| AWS Certified Solutions Architect – Associate | Core target | Jun 2027 |
| Kubernetes and Cloud Native Associate (KCNA) | Core target | Jul 2027 |
| Certified Cloud Native Platform Engineering Associate (CNPA) | Core target | Aug 2027 |
| Certified Kubernetes Administrator (CKA) | Stretch target | Oct–Nov 2027 |
| Certified Backstage Associate (CBA) | Stretch / verify availability | Oct–Nov 2027 |

Only Datadog Fundamentals is confirmed as a mandatory DVT objective. All other exams are proposed. Vendors may update names, prerequisites, prices and exams during 2027: verify official pages before registration.

# Weekly syllabus

## Module 1 — Systems and observability

| Week | Focus | Evidence / exam |
| --- | --- | --- |
| 01  16 Nov | Datadog architecture, concepts, metrics and tags | Create Datadog account; read Fundamentals guide |
| 02  23 Nov | Datadog Agent, host monitoring, integration basics | Install Agent and verify telemetry |
| 03  30 Nov | Dashboards, monitors and Agent troubleshooting | Build dashboard; take practice assessment |
| 04  07 Dec | Datadog Fundamentals consolidation | Sit mandatory Datadog Fundamentals exam |
| 05  14 Dec | Linux essentials and services | Investigate failing Linux service |
| 06  21 Dec | Datadog log collection, parsing and pipelines | Collect and parse application logs |
| 07  28 Dec | Log queries, facets, analysis and troubleshooting | Take Log Management practice test |
| 08  04 Jan | Tracing concepts, HTTP and distributed applications | Trace multi-service request |
| 09  11 Jan | APM instrumentation with NestJS | Instrument API and record traces |
| 10  18 Jan | APM analysis, service maps and performance | Diagnose artificial latency |
| 11  25 Jan | AWS basics: identity, compute, storage, networking, cost | Design basic cloud architecture |
| 12  01 Feb | Observability integration and review | Demonstrate monitored Docker deployment |

Review / buffer week after module 1: consolidate portfolio evidence, catch up and assess readiness. No new mandatory topics.

## Module 2 — Cloud and infrastructure as code

| Week | Focus | Evidence / exam |
| --- | --- | --- |
| 13  15 Feb | APM exam preparation and cloud foundations | Optional Datadog APM exam |
| 14  22 Feb | AWS architecture, shared responsibility and billing | Study Cloud Practitioner objectives |
| 15  01 Mar | AWS IAM, VPC, EC2, S3, billing and exam review | Cloud Practitioner exam |
| 16  08 Mar | AWS ECS/Fargate, ECR and application deployment | Deploy sample container on AWS |
| 17  15 Mar | Terraform providers, resources, HCL and state | Provision first infrastructure stack |
| 18  22 Mar | Terraform variables, outputs, modules and lifecycle | Create reusable modules |
| 19  29 Mar | State locking, remote state, drift and HCP Terraform | Refactor and test Terraform stack |
| 20  05 Apr | CI/CD, secure pipelines and GitLab environments | Terraform Associate exam; pipeline demo |
| 21  12 Apr | AWS resilient architecture and networking patterns | Draw high-availability design |
| 22  19 Apr | AWS compute/database/storage selection | Architecture trade-off analysis |
| 23  26 Apr | Cost optimisation, security and performance | Solutions Architect practice tests |
| 24  03 May | Terraform/AWS integrated deployment | Demonstrate automated cloud environment |

Review / buffer week after module 2: consolidate portfolio evidence, catch up and assess readiness. No new mandatory topics.

## Module 3 — Cloud native and internal platforms

| Week | Focus | Evidence / exam |
| --- | --- | --- |
| 25  17 May | Cloud-native foundations and Kubernetes overview | AWS Solutions Architect - Associate exam |
| 26  24 May | Kubernetes control plane, pods and controllers | Start local cluster and deploy application |
| 27  31 May | Kubernetes Services, networking and core security | KCNA study and practical lab |
| 28  07 Jun | Orchestration, cloud-native observability and concepts | KCNA exam |
| 29  14 Jun | Kubernetes volumes, ConfigMaps, Secrets, probes | Multi-service local deployment |
| 30  21 Jun | Platform product model, self-service and golden paths | Write platform product requirements |
| 31  28 Jun | GitOps, CI/CD, platform APIs and provisioning | Configure GitOps workflow |
| 32  05 Jul | Developer experience, portals and service catalogues | Prototype golden-path template |
| 33  12 Jul | Platform governance, metrics, architecture and security | CNPA exam |
| 34  19 Jul | Helm charts and reusable deployment packaging | Publish working Helm chart |
| 35  26 Jul | Argo CD, reconciliation and delivery patterns | Reconcile from Git automatically |
| 36  02 Aug | Internal developer platform MVP assessment | Independent developer onboarding demo |

Review / buffer week after module 3: consolidate portfolio evidence, catch up and assess readiness. No new mandatory topics.

## Module 4 — Advanced platform engineering

| Week | Focus | Evidence / exam |
| --- | --- | --- |
| 37  16 Aug | Kubernetes administration, nodes and components | CKA-style cluster labs |
| 38  23 Aug | Kubernetes DNS, networking and troubleshooting | Diagnose broken cluster networking |
| 39  30 Aug | Scheduling, storage, RBAC and workloads | Security + persistent volume exercise |
| 40  06 Sep | Kubernetes recovery, upgrades and timed troubleshooting | Full practice scenario |
| 41  13 Sep | SRE, SLIs/SLOs, incident response and on-call design | Create runbook and incident review |
| 42  20 Sep | Prometheus, Grafana and OpenTelemetry | Instrument, visualise and alert |
| 43  27 Sep | Backstage fundamentals, software catalogues | Register platform-managed applications |
| 44  04 Oct | Backstage templates, plugins and integrations | Create self-service template |
| 45  11 Oct | Backstage auth, deployment and lifecycle | Demonstrate secure portal |
| 46  18 Oct | AI-assisted operations, approval and safety controls | Build read-only incident assistant |
| 47  25 Oct | Platform capstone: integration, recovery and documentation | Dry-run technical evaluation |
| 48  01 Nov | Capstone defense and platform assessment | Demonstrate, document and defend architecture |

Review / buffer week after module 4: consolidate portfolio evidence, catch up and assess readiness. No new mandatory topics.

# Running capstone

Working title: Vulporex Developer Platform. Start with a NestJS + PostgreSQL Docker environment; deploy to AWS with Terraform and GitLab CI/CD; migrate an equivalent workflow into a local Kubernetes/GitOps environment; add a service catalogue, developer template, dashboards, policies and read-only AI-assisted diagnostics. The goal is repeatable onboarding, not an elaborate visual interface.

# Progress and assessment gates

| Gate | Evidence to show DVT |
| --- | --- |
| By 31 Mar 2027 | Datadog Fundamentals official certificate and PDP submission |
| Week 12 | Containerised service, monitoring dashboard, troubleshooting exercise |
| Week 24 | Terraform repository, automated pipeline, secure AWS deployment and rollback |
| Week 36 | Helm chart, GitOps, golden-path demonstration |
| Week 48 | Architecture, SLOs, security controls, incident runbooks and capstone demonstration |

# Cost and administrative policy

Keep a live budget. Exam fees are subject to currency exchange, tax, regional pricing, retakes and vendor changes. Confirm DVT reimbursement before purchasing. Known official examples checked 13 Nov 2026: Datadog certifications US$100 per attempt; Terraform Associate (004) US$70.50 plus applicable taxes. Do not treat earlier rough aggregate estimates as an approved budget.

# Official reference directory

Datadog certification: https://www.datadoghq.com/certification/overview/

Datadog learning paths: https://learn.datadoghq.com/pages/certification

AWS certification: https://aws.amazon.com/certification/

Terraform Associate (004): https://developer.hashicorp.com/certifications/terraform-associate

Linux Foundation certifications: https://training.linuxfoundation.org/certification/

Kubernetes tutorials: https://kubernetes.io/docs/tutorials/

Backstage documentation: https://backstage.io/docs/

CNCF platform engineering maturity model: https://tag-app-delivery.cncf.io/whitepapers/platform-eng-maturity-model/

# Programme decisions requiring confirmation

- [  ] DVT KPI weighting and evidence-submission process

- [  ] Reimbursement / exam voucher availability

- [  ] Whether DVT has platform-engineering competency matrix or mentor

- [  ] Internal placement requirements and targeted platform stack

- [  ] Future certification catalogues and examination availability
