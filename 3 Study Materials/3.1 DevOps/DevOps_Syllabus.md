# DevOps Engineering Syllabus

*Estimated 120–150 Study Hours · Learning Objectives & Hands-On Lab Assignments*

## Program Structure & Weighting Overview

This approximately 120–150-hour curriculum follows the end-to-end DevOps lifecycle across six weighted modules (D01–D06). Learners progress through a continuous capstone project—starting with repository setup, packaging services with Docker, automating CI/CD pipelines, provisioning cloud infrastructure with Terraform, deploying via GitOps, and monitoring live production systems with Datadog.

| Code | Module Title | Estimated hours | Weight | Core Milestone |
| --- | --- | ---: | --- | --- |
| D01 | Git & Repository Foundations | 8–10 | 7% | Set up a structured, branch-protected project repository. |
| D02 | Docker & Containerization | 24–30 | 20% | Package and run a multi-service app locally with Docker Compose. |
| D03 | CI/CD & Build Automation | 16–20 | 13% | Automate code testing, image scanning, and registry pushes. |
| D04 | Infrastructure as Code & Terraform | 32–40 | 27% | Provision cloud networking and container clusters via code. |
| D05 | GitOps, Automation & Operations | 24–30 | 20% | Automate continuous cloud deployments, rollbacks, and scaling. |
| D06 | Datadog & Observability | 16–20 | 13% | Monitor live system metrics, logs, APM traces, and alerts. |

## D01: Git & Repository Foundations (8–10 hours | 7%)

### Lesson 1 (8–10 hours): Repository Setup & Version Control Workflows

**Learning objectives**

- Configure SSH keys and Git identity for secure remote repository authentication.

- Structure a multi-component DevOps repository (/app, /infra, /deploy) for clean separation of concerns.

- Write DevOps-specific .gitignore files to prevent secret leaks and exclude build artifacts.

- Practice feature branching, clean commit conventions, and pull request code reviews.

> **Hands-on lab:** Create the master capstone repository on GitHub or GitLab, configure branch protection on main, add a project README.md and .gitignore covering .env, Docker, and Terraform files, and merge a sample feature branch via pull request.

## D02: Docker & Containerization (24–30 hours | 20%)

### Lesson 2 (8–10 hours): Container Fundamentals & Images

**Learning objectives**

- Contrast container architecture with traditional virtual machines.

- Run, inspect, and manage container lifecycles using the Docker CLI.

- Write optimized multi-stage Dockerfile builds that leverage layer caching and run as non-root users.

> **Hands-on lab:** Write a multi-stage Dockerfile for a sample web API that cuts image size by at least 50%, verified using docker history and docker inspect.

### Lesson 3 (8–10 hours): Container Networking & Storage

**Learning objectives**

- Persist application data across container restarts using Docker named volumes and bind mounts.

- Configure custom bridge networks so isolated containers communicate securely.

- Inject runtime configuration safely using environment variables and .env files.

> **Hands-on lab:** Connect a database container to the API over an isolated bridge network with a persistent volume, proving data survives container deletion without exposing database ports to the host.

### Lesson 4 (8–10 hours): Multi-Container Applications

**Learning objectives**

- Orchestrate multi-service stacks (frontend, API, database) using Docker Compose.

- Configure service dependencies, health checks, and port mappings.

- Publish versioned container images to a remote container registry.

> **Hands-on lab:** Combine a frontend, backend API, and database into a docker-compose.yml stack that boots cleanly with one command, then push tagged images to a remote registry.

## D03: CI/CD & Build Automation (16–20 hours | 13%)

### Lesson 5 (8–10 hours): Continuous Integration Workflows

**Learning objectives**

- Configure automated pipeline triggers based on Git branches and pull requests.

- Execute automated linting, unit testing, and code quality checks in CI runners.

- Manage pipeline secrets, environment variables, and build artifacts securely.

> **Hands-on lab:** Build a CI pipeline (e.g., GitHub Actions or GitLab CI) that automatically lints and tests code on every pull request, blocking merges if automated checks fail.

### Lesson 6 (8–10 hours): Automated Image Builds & Delivery

**Learning objectives**

- Automate Docker image builds inside CI pipelines.

- Integrate container vulnerability scanning to catch security flaws before release.

- Implement semantic and Git-SHA tagging strategies for registry pushes.

> **Hands-on lab:** Extend the CI workflow so merges to main automatically build, vulnerability-scan (e.g., with Trivy), and push production-ready container images to the registry.

## D04: Infrastructure as Code & Terraform (32–40 hours | 27%)

### Lesson 7 (8–10 hours): IaC Concepts & Terraform Basics

**Learning objectives**

- Understand declarative infrastructure principles and HashiCorp Configuration Language (HCL).

- Configure cloud provider authentication, resources, variables, and outputs.

- Execute the core Terraform lifecycle (init, plan, apply, and destroy).

> **Hands-on lab:** Provision a cloud storage bucket and basic compute instance via Terraform without hardcoding credentials.

### Lesson 8 (8–10 hours): State Management & Team Workflows

**Learning objectives**

- Understand how Terraform tracks real-world resources using state files.

- Configure remote state backends with state locking to prevent team conflicts.

- Import existing cloud resources and detect or resolve configuration drift.

> **Hands-on lab:** Migrate Terraform state to a remote backend, manually alter a resource in the cloud console to simulate drift, and use Terraform to detect and revert the drift.

### Lesson 9 (8–10 hours): Modular & Reusable Infrastructure

**Learning objectives**

- Refactor repetitive infrastructure code into reusable, parameterized Terraform modules.

- Use loops (for_each, count) and dynamic blocks to scale resource creation.

- Isolate multi-environment setups (dev, staging, prod) using workspaces or directory structures.

> **Hands-on lab:** Convert existing Terraform files into a reusable module and deploy separate dev and prod environments from the shared codebase.

### Lesson 10 (8–10 hours): Cloud Networking & Compute Provisioning

**Learning objectives**

- Provision core cloud networking components (VPCs, subnets, security groups, load balancers).

- Enforce least-privilege IAM roles and security policies via code.

- Deploy managed container hosting infrastructure (such as ECS, GKE, or EKS).

> **Hands-on lab:** Deploy a complete private cloud network and managed container cluster ready to host the capstone application.

## D05: GitOps, Automation & Operations (24–30 hours | 20%)

### Lesson 11 (8–10 hours): GitOps Principles & Pull-Based Delivery

**Learning objectives**

- Contrast push-based CI deployments with pull-based GitOps workflows.

- Structure deployment manifests for declarative cluster reconciliation.

- Deploy and configure a GitOps operator (such as ArgoCD or Flux).

> **Hands-on lab:** Install a GitOps operator on the cloud cluster and sync the capstone application live from the /deploy directory of the repository.

### Lesson 12 (8–10 hours): Release Strategies & Rollbacks

**Learning objectives**

- Implement zero-downtime release strategies including rolling updates and blue/green deployments.

- Automate image tag updates in Git repositories when new builds pass CI.

- Execute rapid rollbacks using Git commit history as the single source of truth.

> **Hands-on lab:** Automate image tag updates from CI to the GitOps configuration, deploy a broken image tag, and restore service health with a single git revert.

### Lesson 13 (8–10 hours): Day-Two Operations & Runbook Automation

**Learning objectives**

- Configure horizontal auto-scaling policies to handle fluctuating traffic loads.

- Automate routine operational tasks such as backups, certificate rotation, and cleanup jobs.

- Practice incident simulation and self-healing recovery workflows on live environments.

> **Hands-on lab:** Set up auto-scaling rules, run a load test to trigger scaling, and manually terminate a running container pod to verify self-healing without downtime.

## D06: Datadog & Observability (16–20 hours | 13%)

### Lesson 14 (8–10 hours): Metrics, Logs & Infrastructure Monitoring

**Learning objectives**

- Deploy the Datadog Agent across containerized and cloud environments.

- Configure centralized log collection, parsing pipelines, and live tailing.

- Build custom dashboards tracking system health, resource utilization, and container metrics.

> **Hands-on lab:** Deploy the Datadog Agent to the cluster and build a custom dashboard tracking CPU/memory metrics, container restarts, and filtered error logs.

### Lesson 15 (8–10 hours): APM Tracing & Actionable Alerting

**Learning objectives**

- Instrument Application Performance Monitoring (APM) to trace requests across microservices.

- Define Service Level Objectives (SLOs) and meaningful monitors to reduce alert fatigue.

- Configure automated alert routing to incident channels (e.g., Slack or PagerDuty).

> **Hands-on lab:** Instrument Datadog APM on the backend API to trace database queries and configure an alert monitor that fires a notification when error rates spike.
