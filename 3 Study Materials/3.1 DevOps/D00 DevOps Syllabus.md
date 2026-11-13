# DevOps Engineering Syllabus

*Estimated 120–150 Study Hours · Learning Objectives & Hands-On Lab Assignments*

## Modules and estimated study time

This approximately 120–150-hour curriculum follows the end-to-end DevOps lifecycle across seven modules (D01–D07) with indicative syllabus weightings. Learners progress through a continuous Final Project—starting with repository setup, packaging services with Docker, automating CI/CD pipelines, provisioning cloud infrastructure with Terraform, deploying via GitOps, and monitoring live production systems with Datadog.

| Code | Module | Estimated hours | Weight | Core milestone |
| --- | --- | ---: | --- | --- |
| D01 | [Repository Fundamentals](D01%20Repository%20Fundamentals.md) | 4–5 | 3% | Establish a secure, governed repository and protected contribution workflow. |
| D02 | [Advanced Git](D02%20Advanced%20Git.md) | 4–5 | 4% | Resolve conflicts, recover commits and diagnose regressions safely. |
| D03 | [Docker & Containerization](D03%20Docker%20and%20Containerization.md) | 24–30 | 20% | Package and run a multi-service app locally with Docker Compose. |
| D04 | [CI/CD & Build Automation](D04%20CICD%20and%20Build%20Automation.md) | 16–20 | 13% | Automate code testing, image scanning, and registry pushes. |
| D05 | [Infrastructure as Code & Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md) | 32–40 | 27% | Provision cloud networking and container clusters via code. |
| D06 | [GitOps, Automation & Operations](D06%20GitOps%20Automation%20and%20Operations.md) | 24–30 | 20% | Automate continuous cloud deployments, rollbacks, and scaling. |
| D07 | [Datadog & Observability](D07%20Datadog%20and%20Observability.md) | 16–20 | 13% | Monitor live system metrics, logs, APM traces, and alerts. |

## Contribution to the Final Project

The modules contribute to the [programme Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md) through one reusable application delivery example across Git, Docker, CI/CD, Terraform, GitOps and Datadog. Each lesson includes a hands-on lab that builds on earlier work. The [module companion pages](D01%20Repository%20Fundamentals.md) can be used to collect links to completed work; the lesson objectives and labs below remain the source of truth.

## Certifications

Completing these materials does **not** award a certification, and certifications are **optional**. Learners may independently pursue relevant external certifications if they choose.

## D01: Repository Fundamentals (4–5 hours | 3%)

### Lesson 1 (4–5 hours): Repository Architecture, Governance & Security

**Learning objectives**

- Design a repository separating application, infrastructure and deployment work, with ownership and contribution instructions.
- Configure authenticated remote access, least-privilege roles and appropriate ignore rules for credentials and generated files.
- Define branch protection, CODEOWNERS or equivalent, and pull/merge-request review requirements.
- Justify chosen repository architecture, review policy and practical limitations in a short ADR.

> **Hands-on lab:** Create the Final Project repository, add application/infrastructure/deployment boundaries, configure ignore rules and branch protection, then submit and review a change to a sensitive path. Verify enforcement where supported and document limitations.

**Detailed practical material:** [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md).

## D02: Advanced Git (4–5 hours | 4%)

### Lesson 2 (4–5 hours): Git Internals, Conflict Resolution & Recovery

**Learning objectives**

- Interpret commit graphs, refs, object relationships and merge bases.
- Explain when merge commits, squash merges, rebase or cherry-pick are appropriate.
- Resolve conflicting histories using two independent clones while protecting shared branches.
- Recover discarded local work with reflog and diagnose a regression with `git bisect`.

> **Hands-on lab:** Create divergent commits and a merge conflict in a disposable repository, compare integration strategies, recover an intentionally lost local commit and identify a first bad commit with `git bisect`. Explain the safe production recovery route.

**Detailed practical material:** [D02 — Advanced Git](D02%20Advanced%20Git.md).

## D03: Docker & Containerization (24–30 hours | 20%)

### Lesson 3 (8–10 hours): Container Fundamentals & Images

**Learning objectives**

- Contrast container architecture with traditional virtual machines.

- Run, inspect, and manage container lifecycles using the Docker CLI.

- Write optimized multi-stage Dockerfile builds that leverage layer caching and run as non-root users.

> **Hands-on lab:** Write a multi-stage Dockerfile for a sample web API that cuts image size by at least 50%, verified using docker history and docker inspect.

### Lesson 4 (8–10 hours): Container Networking & Storage

**Learning objectives**

- Persist application data across container restarts using Docker named volumes and bind mounts.

- Configure custom bridge networks so isolated containers communicate securely.

- Inject runtime configuration safely using environment variables and .env files.

> **Hands-on lab:** Connect a database container to the API over an isolated bridge network with a persistent volume, proving data survives container deletion without exposing database ports to the host.

### Lesson 5 (8–10 hours): Multi-Container Applications

**Learning objectives**

- Orchestrate multi-service stacks (frontend, API, database) using Docker Compose.

- Configure service dependencies, health checks, and port mappings.

- Publish versioned container images to a remote container registry.

> **Hands-on lab:** Combine a frontend, backend API, and database into a docker-compose.yml stack that boots cleanly with one command, then push tagged images to a remote registry.

## D04: CI/CD & Build Automation (16–20 hours | 13%)

### Lesson 6 (8–10 hours): Continuous Integration Workflows

**Learning objectives**

- Configure automated pipeline triggers based on Git branches and pull requests.

- Execute automated linting, unit testing, and code quality checks in CI runners.

- Manage pipeline secrets, environment variables, and build artifacts securely.

> **Hands-on lab:** Build a CI pipeline (e.g., GitHub Actions or GitLab CI) that automatically lints and tests code on every pull request, blocking merges if automated checks fail.

### Lesson 7 (8–10 hours): Automated Image Builds & Delivery

**Learning objectives**

- Automate Docker image builds inside CI pipelines.

- Integrate container vulnerability scanning to catch security flaws before release.

- Implement semantic and Git-SHA tagging strategies for registry pushes.

> **Hands-on lab:** Extend the CI workflow so merges to main automatically build, vulnerability-scan (e.g., with Trivy), and push production-ready container images to the registry.

## D05: Infrastructure as Code & Terraform (32–40 hours | 27%)

### Lesson 8 (8–10 hours): IaC Concepts & Terraform Basics

**Learning objectives**

- Understand declarative infrastructure principles and HashiCorp Configuration Language (HCL).

- Configure cloud provider authentication, resources, variables, and outputs.

- Execute the core Terraform lifecycle (init, plan, apply, and destroy).

> **Hands-on lab:** Provision a cloud storage bucket and basic compute instance via Terraform without hardcoding credentials.

### Lesson 9 (8–10 hours): State Management & Team Workflows

**Learning objectives**

- Understand how Terraform tracks real-world resources using state files.

- Configure remote state backends with state locking to prevent team conflicts.

- Import existing cloud resources and detect or resolve configuration drift.

> **Hands-on lab:** Migrate Terraform state to a remote backend, manually alter a resource in the cloud console to simulate drift, and use Terraform to detect and revert the drift.

### Lesson 10 (8–10 hours): Modular & Reusable Infrastructure

**Learning objectives**

- Refactor repetitive infrastructure code into reusable, parameterized Terraform modules.

- Use loops (for_each, count) and dynamic blocks to scale resource creation.

- Isolate multi-environment setups (dev, staging, prod) using workspaces or directory structures.

> **Hands-on lab:** Convert existing Terraform files into a reusable module and deploy separate dev and prod environments from the shared codebase.

### Lesson 11 (8–10 hours): Cloud Networking & Compute Provisioning

**Learning objectives**

- Provision core cloud networking components (VPCs, subnets, security groups, load balancers).

- Enforce least-privilege IAM roles and security policies via code.

- Deploy managed container hosting infrastructure (such as ECS, GKE, or EKS).

> **Hands-on lab:** Deploy a complete private cloud network and managed container cluster ready to host the Final Project application.

## D06: GitOps, Automation & Operations (24–30 hours | 20%)

### Lesson 12 (8–10 hours): GitOps Principles & Pull-Based Delivery

**Learning objectives**

- Contrast push-based CI deployments with pull-based GitOps workflows.

- Structure deployment manifests for declarative cluster reconciliation.

- Deploy and configure a GitOps operator (such as ArgoCD or Flux).

> **Hands-on lab:** Install a GitOps operator on the cloud cluster and sync the Final Project application live from the /deploy directory of the repository.

### Lesson 13 (8–10 hours): Release Strategies & Rollbacks

**Learning objectives**

- Implement zero-downtime release strategies including rolling updates and blue/green deployments.

- Automate image tag updates in Git repositories when new builds pass CI.

- Execute rapid rollbacks using Git commit history as the single source of truth.

> **Hands-on lab:** Automate image tag updates from CI to the GitOps configuration, deploy a broken image tag, and restore service health with a single git revert.

### Lesson 14 (8–10 hours): Day-Two Operations & Runbook Automation

**Learning objectives**

- Configure horizontal auto-scaling policies to handle fluctuating traffic loads.

- Automate routine operational tasks such as backups, certificate rotation, and cleanup jobs.

- Practice incident simulation and self-healing recovery workflows on live environments.

> **Hands-on lab:** Set up auto-scaling rules, run a load test to trigger scaling, and manually terminate a running container pod to verify self-healing without downtime.

## D07: Datadog & Observability (16–20 hours | 13%)

### Lesson 15 (8–10 hours): Metrics, Logs & Infrastructure Monitoring

**Learning objectives**

- Deploy the Datadog Agent across containerized and cloud environments.

- Configure centralized log collection, parsing pipelines, and live tailing.

- Build custom dashboards tracking system health, resource utilization, and container metrics.

> **Hands-on lab:** Deploy the Datadog Agent to the cluster and build a custom dashboard tracking CPU/memory metrics, container restarts, and filtered error logs.

### Lesson 16 (8–10 hours): APM Tracing & Actionable Alerting

**Learning objectives**

- Instrument Application Performance Monitoring (APM) to trace requests across microservices.

- Define Service Level Objectives (SLOs) and meaningful monitors to reduce alert fatigue.

- Configure automated alert routing to incident channels (e.g., Slack or PagerDuty).

> **Hands-on lab:** Instrument Datadog APM on the backend API to trace database queries and configure an alert monitor that fires a notification when error rates spike.
