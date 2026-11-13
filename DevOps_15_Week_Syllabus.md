DevOps Engineering Syllabus

15-Week Curriculum Overview, Weekly Learning Objectives & Hands-On Lab Assignments

Program Structure & Weighting Overview

This 15-week curriculum follows the end-to-end DevOps lifecycle across six weighted modules (D01âD06). Learners progress through a continuous capstone projectâstarting with repository setup, packaging services with Docker, automating CI/CD pipelines, provisioning cloud infrastructure with Terraform, deploying via GitOps, and monitoring live production systems with Datadog.

Module Title

Duration

Schedule

Weight

Core Milestone

D01

Git & Repository Foundations

1 week

Week 1

7%

Set up a structured, branch-protected project repository.

D02

Docker & Containerization

3 weeks

Weeks 2â4

20%

Package and run a multi-service app locally with Docker Compose.

D03

CI/CD & Build Automation

2 weeks

Weeks 5â6

13%

Automate code testing, image scanning, and registry pushes.

D04

Infrastructure as Code & Terraform

4 weeks

Weeks 7â10

27%

Provision cloud networking and container clusters via code.

D05

GitOps, Automation & Operations

3 weeks

Weeks 11â13

20%

Automate continuous cloud deployments, rollbacks, and scaling.

D06

Datadog & Observability

2 weeks

Weeks 14â15

13%

Monitor live system metrics, logs, APM traces, and alerts.

D01: Git & Repository Foundations (Week 1 | 7%)

Week 1: Repository Setup & Version Control Workflows

Learning Objectives:

- Configure SSH keys and Git identity for secure remote repository authentication.

- Structure a multi-component DevOps repository (/app, /infra, /deploy) for clean separation of concerns.

- Write DevOps-specific .gitignore files to prevent secret leaks and exclude build artifacts.

- Practice feature branching, clean commit conventions, and pull request code reviews.

D02: Docker & Containerization (Weeks 2â4 | 20%)

Week 2: Container Fundamentals & Images

Learning Objectives:

- Contrast container architecture with traditional virtual machines.

- Run, inspect, and manage container lifecycles using the Docker CLI.

- Write optimized multi-stage Dockerfile builds that leverage layer caching and run as non-root users.

Week 3: Container Networking & Storage

Learning Objectives:

- Persist application data across container restarts using Docker named volumes and bind mounts.

- Configure custom bridge networks so isolated containers communicate securely.

- Inject runtime configuration safely using environment variables and .env files.

Week 4: Multi-Container Applications

Learning Objectives:

- Orchestrate multi-service stacks (frontend, API, database) using Docker Compose.

- Configure service dependencies, health checks, and port mappings.

- Publish versioned container images to a remote container registry.

D03: CI/CD & Build Automation (Weeks 5â6 | 13%)

Week 5: Continuous Integration Workflows

Learning Objectives:

- Configure automated pipeline triggers based on Git branches and pull requests.

- Execute automated linting, unit testing, and code quality checks in CI runners.

- Manage pipeline secrets, environment variables, and build artifacts securely.

Week 6: Automated Image Builds & Delivery

Learning Objectives:

- Automate Docker image builds inside CI pipelines.

- Integrate container vulnerability scanning to catch security flaws before release.

- Implement semantic and Git-SHA tagging strategies for registry pushes.

D04: Infrastructure as Code & Terraform (Weeks 7â10 | 27%)

Week 7: IaC Concepts & Terraform Basics

Learning Objectives:

- Understand declarative infrastructure principles and HashiCorp Configuration Language (HCL).

- Configure cloud provider authentication, resources, variables, and outputs.

- Execute the core Terraform lifecycle (init, plan, apply, and destroy).

Week 8: State Management & Team Workflows

Learning Objectives:

- Understand how Terraform tracks real-world resources using state files.

- Configure remote state backends with state locking to prevent team conflicts.

- Import existing cloud resources and detect or resolve configuration drift.

Week 9: Modular & Reusable Infrastructure

Learning Objectives:

- Refactor repetitive infrastructure code into reusable, parameterized Terraform modules.

- Use loops (for_each, count) and dynamic blocks to scale resource creation.

- Isolate multi-environment setups (dev, staging, prod) using workspaces or directory structures.

Week 10: Cloud Networking & Compute Provisioning

Learning Objectives:

- Provision core cloud networking components (VPCs, subnets, security groups, load balancers).

- Enforce least-privilege IAM roles and security policies via code.

- Deploy managed container hosting infrastructure (such as ECS, GKE, or EKS).

D05: GitOps, Automation & Operations (Weeks 11â13 | 20%)

Week 11: GitOps Principles & Pull-Based Delivery

Learning Objectives:

- Contrast push-based CI deployments with pull-based GitOps workflows.

- Structure deployment manifests for declarative cluster reconciliation.

- Deploy and configure a GitOps operator (such as ArgoCD or Flux).

Week 12: Release Strategies & Rollbacks

Learning Objectives:

- Implement zero-downtime release strategies including rolling updates and blue/green deployments.

- Automate image tag updates in Git repositories when new builds pass CI.

- Execute rapid rollbacks using Git commit history as the single source of truth.

Week 13: Day-Two Operations & Runbook Automation

Learning Objectives:

- Configure horizontal auto-scaling policies to handle fluctuating traffic loads.

- Automate routine operational tasks such as backups, certificate rotation, and cleanup jobs.

- Practice incident simulation and self-healing recovery workflows on live environments.

D06: Datadog & Observability (Weeks 14â15 | 13%)

Week 14: Metrics, Logs & Infrastructure Monitoring

Learning Objectives:

- Deploy the Datadog Agent across containerized and cloud environments.

- Configure centralized log collection, parsing pipelines, and live tailing.

- Build custom dashboards tracking system health, resource utilization, and container metrics.

Week 15: APM Tracing & Actionable Alerting

Learning Objectives:

- Instrument Application Performance Monitoring (APM) to trace requests across microservices.

- Define Service Level Objectives (SLOs) and meaningful monitors to reduce alert fatigue.

- Configure automated alert routing to incident channels (e.g., Slack or PagerDuty).
