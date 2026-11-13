# D00 — DevOps Engineering Syllabus

The DevOps discipline develops the engineering capabilities needed to create **secure, repeatable and operable delivery services** for other developers. It is the foundation for later Cloud, AI and Platform Engineering work.

The eight modules below form a recommended progression, not a mandatory qualification or fixed-duration course. They are designed for developers who already have practical software engineering experience. **Each module owns its detailed learning activities and Practical Assessment**; this syllabus sets out the overall sequence, boundaries and expected outcomes.

## Modules

| Module | Focus | Estimated study time | Evidence of capability |
| --- | --- | ---: | --- |
| [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md) | Repository architecture, ownership, governance, access and source security | 6–9 hours | A governed, reviewable source repository with documented ownership and controls |
| [D02 — Advanced Git](D02%20Advanced%20Git.md) | Commit internals, history strategies, conflict resolution, recovery and bisect | 7–10 hours | Documented conflict resolution, recovery and regression investigation |
| [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md) | Container runtime, image engineering, networking, persistence and supply-chain security | 28–40 hours | Reproducible hardened images, a multi-service stack and failure evidence |
| [D04 — CI/CD and Build Automation](D04%20CICD%20and%20Build%20Automation.md) | Trusted pipelines, isolated runners, verification, provenance and artifact promotion | 24–36 hours | An auditable pipeline from reviewed source to immutable release |
| [D05 — Infrastructure as Code and Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md) | State, drift, modules, IAM, infrastructure architecture and policy | 42–60 hours | Reusable infrastructure deployed through controlled, reviewed changes |
| [D06 — GitOps, Automation and Operations](D06%20GitOps%20Automation%20and%20Operations.md) | Reconciliation, progressive delivery, rollbacks and day-two operations | 30–44 hours | A governed desired-state deployment with verified recovery |
| [D07 — Observability](D07%20Observability.md) | Vendor-neutral telemetry architecture, instrumentation, SLIs/SLOs and diagnostic reasoning | 18–28 hours | Instrumented services, meaningful objectives and reproducible incident investigation |
| [D08 — Datadog](D08%20Datadog.md) | Agent and APM setup, dashboards, alerting, incident response and reusable provider configuration | 24–36 hours | Operational Datadog monitoring and repeatable second-service onboarding |
| **Total** | **8 modules** | **179–263 hours** | **A working, traceable application delivery foundation** |

**How estimates were developed:** Study-time ranges were assigned **after reviewing the module content, exercises, lab dependencies and Practical Assessments**. They are planning estimates, not constraints. A developer with prior experience may demonstrate an outcome more quickly; unfamiliar providers, infrastructure issues or additional depth may take longer. Completion is determined by demonstrated capability.

## Curriculum progression

The learning is cumulative. Each module produces assets needed in later modules:

1. **D01 — Govern source changes.** Establish repository layout, code ownership, safe contribution paths and security rules.
2. **D02 — Understand and recover source history.** Diagnose conflicts and regressions without endangering the shared repository.
3. **D03 — Define the runtime contract.** Make the application reproducible, containerised, secure and diagnosable.
4. **D04 — Build an artifact you can trust.** Turn reviewed code into tested, traceable, immutable container releases.
5. **D05 — Provision the environment safely.** Use Terraform modules, state controls and reviewed infrastructure changes.
6. **D06 — Operate declared deployments.** Promote those exact release artifacts through GitOps, then test drift, rollback and resilience.
7. **D07 — Understand and design observability.** Instrument services with portable telemetry, define SLIs/SLOs and investigate failures using evidence.
8. **D08 — Operate Datadog.** Implement agents, APM, logs, dashboards, monitors and reusable onboarding for additional teams.

### Core lessons carried through the syllabus

The original teaching topics remain part of the pathway, but are now explored through the **more advanced module specifications** rather than duplicated beginner-level lessons in this overview.

| Module | Learning areas and original practical progression |
| --- | --- |
| D01 | Repository layout, remote access, ignore rules, protected default branch and a reviewed change |
| D02 | Git object model, merge/rebase choices, complex conflict resolution, reflog recovery and regression identification |
| D03 | Container images; networking and persistent storage; multi-service Compose application and published images |
| D04 | Pull-request validation; automated container builds, scanning and registry releases |
| D05 | Terraform resource lifecycle; state and drift; reusable modules; secure networking, IAM and container infrastructure |
| D06 | GitOps controller and declarative sync; release/rollback strategy; autoscaling and day-two recovery |
| D07 | Monitoring versus observability; metrics, structured logs, distributed traces, OpenTelemetry pipeline, service objectives, incident diagnosis and governance |
| D08 | Datadog Agent; infrastructure monitoring, APM and log correlation; dashboards, SLOs, actionable alerting, incident investigation and provider-specific operations |

## What a Platform Engineer must be able to demonstrate

Beyond simply knowing each technology, a developer should be able to **explain the system as a whole**:

- **Self-service:** Can another developer understand, use and extend the delivery workflow without specialist intervention?
- **Security:** Which identities can change source, publish artifacts, provision infrastructure or deploy code? How are secrets prevented from leaking?
- **Provenance:** Can a running workload be traced back to a reviewed change, passing checks and an immutable image?
- **Reliability:** Can a new release, failed dependency, drift event or resource limit be diagnosed and recovered from?
- **Operations:** Are health, error rate, latency and dependencies observable? Who is alerted and what should they do?
- **Governance:** Which policies are enforced automatically, which require human approval and which limitations remain?
- **Maintainability:** Are infrastructure modules, workflows, configuration and monitoring reusable rather than application-specific one-offs?

These are engineering outcomes. A screenshot, passing command or completed reading list is **not** sufficient evidence on its own.

## Practical Assessments and the Final Project

Each module provides a **Practical Assessment** appropriate to that subject. Collect links to the working repository, reviewed changes, build artifacts, infrastructure plans, deployment history, monitoring results, runbooks and architectural decisions.

The recommended [programme Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md) integrates those assets into one **Internal Developer Platform**. Track the module-by-module Harbour increments on the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md). This work is cumulative, not a separate project deferred until the end. Developers may substitute equivalent practical work consistent with their personal PDP.

Where a provider feature, paid service or external reviewer is unavailable, document the limitation and show a reasonable alternative. Do not claim an untested control was enforced.

## Scope and boundaries

D07 builds the vendor-neutral observability foundation; D08 applies it in Datadog. D03 introduces container runtime fundamentals, and D06 uses a **small, isolated Kubernetes environment** to practise GitOps. Deep Kubernetes administration, multi-cluster platform design, developer portals and organisation-wide platform operations are developed later in the Platform Engineering discipline. Cloud Engineering revisits networking, IAM and infrastructure at greater breadth. AI Engineering covers LLM and agent capabilities separately.

Avoid unnecessary complexity: a demonstrable secure delivery system is more valuable than a fragile collection of tools.

## Certifications

This framework **does not issue certifications**. Certifications are entirely optional and must be earned separately from the issuing organisation. Learners may map relevant external certification objectives into their own PDP, but practical capability remains the primary goal.

**Next:** [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md)
