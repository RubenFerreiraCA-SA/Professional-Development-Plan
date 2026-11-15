# Further Reading and Reference Notes

These pointers are for deepening understanding and for checking version-specific details. Documentation changes; verify current behaviour before relying on a feature.

### How to use these references

- Treat vendor documentation as authoritative for *syntax and current behaviour*, and this book for *concepts, trade-offs and decision-making*.
- When a command in this book behaves differently on your platform, check the tool's version and its release notes first.
- Prefer primary sources (specifications, official docs, post-incident reviews) over summaries.

### Part I — DevOps Engineering

- **Git and repositories:** the *Pro Git* book (git-scm.com/book) for the object model, branching, rebasing and recovery; Git reference documentation for `gitignore`, `reflog`, `bisect`, `worktree`, `rerere` and `range-diff`; your hosting provider's documentation on protected branches, rulesets, code owners and secret scanning.
- **Containers:** Docker documentation (Dockerfile best practices, multi-stage builds, Compose); the Open Container Initiative specifications for images and runtimes; Linux man pages for `namespaces(7)`, `cgroups(7)` and `capabilities(7)`; Sigstore documentation for signing and verification; Syft, Grype and Trivy documentation for SBOM generation and scanning.
- **CI/CD:** your CI provider's security-hardening guide; documentation on reusable workflows and OpenID Connect federation; the SLSA specification for supply-chain integrity levels; the *Accelerate* research and DORA reports for delivery-performance measurement (as signals, not targets).
- **Infrastructure as code:** Terraform documentation (state, backends, modules, testing, `moved` and `import` blocks); the S3 backend page for current locking behaviour; provider documentation for version-specific resource behaviour; policy-as-code tool documentation.
- **GitOps:** the OpenGitOps principles; Flux and Argo CD documentation; Kustomize and Helm documentation; guidance on sealed secrets, SOPS and external secrets operators.
- **Observability and reliability:** the OpenTelemetry specification and semantic conventions; Prometheus documentation; the Google *Site Reliability Engineering* book and *The Site Reliability Workbook* (service level objectives and burn-rate alerting); *Observability Engineering*; blameless post-incident review practices.
- **Datadog:** official documentation on the Agent, unified service tagging, APM, log management, monitors, SLOs and the Terraform provider; pricing and cardinality guidance from your plan documentation.

### Part II — Cloud Engineering

- **Linux and networking:** man pages for `systemd.service`, `ss`, `ip`, `nft`, `journalctl`; *Systems Performance* by Brendan Gregg; the USE method; RFCs for DNS (1034, 1035) and TLS 1.3 (8446); OpenSSL documentation; your provider's networking guides.
- **Cloud foundations:** the provider's well-architected framework and landing-zone guidance; organisation-level policy documentation; shared-responsibility pages; FinOps Foundation material on cost management.
- **AWS identity and networking:** IAM documentation on policy evaluation logic, permission boundaries and `PassRole`; VPC, security group and endpoint documentation; the policy simulator; Budgets and Cost Explorer documentation. Verify service names and limits in current documentation.
- **Architecture and resilience:** the provider's reliability pillar; *Release It!* for stability patterns; chaos engineering principles; documentation for container services, load balancers and managed databases on backup, failover and multi-AZ behaviour.

### Part III — AI Engineering

- **Prompting and models:** your model provider's prompt-engineering and safety guides; documentation on structured outputs and function calling; model cards and deprecation schedules for any model you pin.
- **Retrieval:** documentation of the vector or search system you use; the original retrieval-augmented generation research papers; evaluations such as retrieval recall and groundedness measures.
- **Evaluation and safety:** the OWASP Top 10 for LLM applications; NIST AI Risk Management Framework; guidance on red-teaming; JSON Schema documentation for output validation.
- **Agents and tools:** provider and community documentation on tool use and agent patterns; the Model Context Protocol specification and its security guidance; threat-modelling resources for agentic systems.
- **LLMOps:** your observability stack's documentation for tracing and metrics; provider documentation on rate limits, token accounting and data retention; guidance on feature flags and progressive delivery.

### Part IV — Platform Engineering

- **Kubernetes:** the official Kubernetes documentation (concepts, tasks, API reference, version-skew and deprecation policies); *Kubernetes Patterns*; the CIS Kubernetes Benchmark; the Pod Security Standards; documentation of your network plugin for NetworkPolicy support; ValidatingAdmissionPolicy and CEL reference; Kyverno or Gatekeeper documentation.
- **Operations and recovery:** `etcd` documentation for snapshot and restore; the cluster-upgrade guides for your distribution; Velero or provider-specific backup documentation; incident-management frameworks.
- **Platform engineering and developer experience:** the CNCF Platforms White Paper and Platform Engineering Maturity Model; *Team Topologies*; the Diátaxis documentation framework; Backstage documentation (software catalogue and templates); DORA and SPACE frameworks for developer productivity (with their stated limitations).
- **Integration and architecture:** guidance on architecture decision records (Michael Nygard's original article); C4 model for architecture views; supply-chain attestation and verification tooling documentation.

### Version-sensitive topics to re-check

Before relying on a worked example in production, verify current official documentation for at least: Git hosting rulesets and CODEOWNERS enforcement; Dockerfile and BuildKit syntax; CI OIDC claim formats; Terraform backend locking; Flux/Argo APIs; OpenTelemetry semantic conventions; Datadog Agent and monitor query syntax; AWS IAM evaluation edge cases and VPC features; Kubernetes API deprecations, Pod Security and admission; model-provider structured-output and tool-calling APIs. Where a chapter marks a detail as version-specific or illustrative, treat that label as authoritative for the book’s intent.

### Reference notes carried through this book

1. **Setting is not enforcement.** Show a rejected action to prove a control exists; a settings screenshot proves only a setting.
2. **Digests, not tags,** identify what runs; record commit → build → digest → deployment.
3. **Untrusted code never holds privileged credentials;** trusted automation never runs untrusted code.
4. **State, secrets and data are separate recovery problems** from configuration; Git restores definitions, not data.
5. **Measure, then claim.** State what a drill proved and what it did not. Keep a limitations register.
6. **Models are untrusted components.** Enforce policy in code outside the model; keep capability minimal; evaluate continuously.
7. **Prefer one owner per resource** and one source of truth per concern.
8. **Platforms are products.** Their evidence is independent users succeeding, not the existence of tooling.
