# D04 — CI/CD and Build Automation

| | Details |
| --- | --- |
| **Estimated study time** | 24–36 hours |
| **Prerequisites** | [D01 — Repository Fundamentals](D01%20Repository%20Fundamentals.md), [D02 — Advanced Git](D02%20Advanced%20Git.md) and [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md). Comfortable writing automated tests and using a remote Git hosting service. |

## Objective

Build a **trustworthy software delivery system** that converts an approved source change into a traceable, tested, policy-compliant artifact. Think like a Platform Engineer: pipelines are reusable services offered to development teams, with security boundaries, feedback quality, reliability and developer experience as first-class concerns.

Use GitHub Actions, GitLab CI or another comparable system. Choose one implementation and explain which design principles apply across providers.

## Outcomes

1. Design fast, deterministic CI that gives actionable feedback on pull/merge requests.
2. Separate validation, build, release and deployment responsibilities, and articulate the trust boundaries between them.
3. Use least-privilege identities, isolated runners and protected secrets without exposing credentials to untrusted changes.
4. Produce versioned container artifacts with build provenance, SBOMs, vulnerability scanning and traceable source identity.
5. Implement safe promotion across environments, artifact immutability, rollback evidence and operational controls.
6. Design reusable pipeline templates that avoid duplicated configuration while still allowing service-specific requirements.
7. Diagnose flaky tests, cache corruption, failed runners, non-repeatable builds and supply-chain issues.

## Learning and engineering activities

| Activity | Estimated hours |
| --- | ---: |
| CI architecture, tests and quality gates | 5–7 |
| Runner isolation, permissions, secrets and threat modelling | 4–6 |
| Artifact creation, scanning and provenance | 5–7 |
| Promotion workflows and reusable pipeline components | 4–6 |
| Failure injection and Practical Assessment | 6–10 |
| **Working estimate** | **24–36** |

These estimates follow the content rather than define it. Automating an existing, well-tested application may be faster; solving test reliability and provider restrictions may require more effort.

## 1. Design the delivery architecture

Start with the flow: **source change → validation → review → trusted integration → immutable release → environment promotion**.

Draw a diagram showing which steps execute:
- For untrusted pull/merge request code.
- After merge into a protected branch.
- Only when a release is approved or automatically promoted.

Determine where the source SHA, image digest, test report, approval and deployment record live.

**Design choices to defend:**
- Trunk-based development versus long-lived release branches.
- Merge queues and required checks versus unrestricted parallel merges.
- Running fast tests on each change, with slower integration/security suites at appropriate gates.
- Parallel jobs, cancellation of superseded work and targeted builds without skipping required security coverage.
- Whether CD pushes directly to a cluster or updates deployment configuration that a GitOps controller reconciles later in [D06](D06%20GitOps%20Automation%20and%20Operations.md).

**Exercise:** Create a test matrix (unit, integration, lint, type-check and container-based smoke tests). For each, specify trigger, expected duration, failure impact, and who owns remediation.

## 2. Build a reliable pull-request validation pipeline

Implement a validation pipeline for the Final Project application that:
1. Installs dependencies **from an immutable lockfile** using the language's deterministic install mode.
2. Runs formatting/linting, type checks (if applicable), unit tests and integration tests.
3. Publishes usable logs and test results even when some checks fail.
4. Runs in a clean environment and checks that generated artifacts do not silently modify the source tree.
5. Fails the merge gate on a deliberate test regression.

**Reliability drills:** force a failing dependency install, a flaky test and a timeout. Identify whether the failure is caused by source code, the test, cache corruption, a runner, or infrastructure. Avoid blanket retries that hide real regressions.

**Performance analysis:** measure clean-run versus cached-run duration; identify critical-path jobs and introduce caching only for verified, appropriate directories. Never treat caches as trusted build outputs or store credentials inside them.

## 3. Treat the CI platform as a privileged system

**Threat model:** an external contributor opens a pull request containing hostile code. What can that job read, write, publish or trigger?

Evaluate:
- Hosted versus self-hosted runners and the risks of running untrusted pull requests on persistent machines.
- Read-only tokens for validation and narrowly scoped write tokens only for trusted release contexts.
- Avoiding privileged workflow triggers that execute attacker-controlled content with secrets (for example, careless use of `pull_request_target`).
- Secret masking limitations and exfiltration through process output, artifacts, caches or outbound network access.
- Federated identity/OIDC for short-lived cloud credentials instead of persistent cloud access keys.
- Reusable actions or components, pinned dependencies and update policy.
- Concurrency controls to stop colliding promotions to the same environment.

**Exercise:** Document a permission matrix for validation, artifact publication and deployment/promotion. Test that an untrusted validation job cannot publish a release or retrieve protected secrets. Use dummy credentials only.

## 4. Release artifacts, not mutable source branches

Extend the trusted branch pipeline to:

- Build the application once after successful checks, producing a versioned container image.
- Generate an SBOM, scan the exact release image and record a reasoned decision for severe findings.
- Record the image **digest** alongside the originating commit and pipeline run.
- Publish to a restricted registry with separate identities for write and read where possible.
- Consider attestation/signing that ties the artifact to the build process; document what level of provenance is actually verified.
- Make release artifacts immutable for promotion: **do not rebuild the same source separately for staging and production**.

**Security gate design:** define what blocks the release (for example, critical vulnerabilities with an available fix, failed tests, invalid signature), what requires explicit exception approval, and how exceptions expire. Scanner output alone is not a security policy.

**Evidence:** show that a tagged artifact can be resolved to a digest, that the digest matches the deployed/promotion reference, and that a source SHA traces back to an approved change.

## 5. Promotion, rollback and developer experience

Implement a simple `dev` → `test` or `staging` promotion process (local or inexpensive cloud environment is sufficient):

- Promotion must select **an existing artifact digest**.
- Capture the promotion decision, environment, operator or automation identity, and result.
- Preserve a prior known-good digest for rollback.
- If using GitOps, promote by a reviewed pull/merge request updating the desired-state manifest rather than manually changing the live cluster.
- Establish a rule for failed promotion: freeze, alert, roll back or reconcile, depending on the actual failure.
- Expose a concise pipeline failure summary and links to diagnostics for developers.

**Platform thinking exercise:** extract one reusable pipeline template or component and apply it to a second small service. Decide which choices are enforced centrally (security, provenance) and which are configurable (language, tests). Version the template and document how breaking changes reach consumers.

## Practical Assessment — trusted software supply chain

**Scenario:** Your platform team offers a delivery workflow for two application teams. One makes a legitimate change; the other submits untrusted code or a failing dependency. Demonstrate that the platform gives useful feedback and does not accidentally grant publication rights.

**Required demonstration:**

1. A working PR/MR pipeline with deterministic dependency installs, automated checks and a blocked merge when checks fail.
2. A trusted build that publishes an immutable image and retains commit SHA, image digest, vulnerability evidence and a dependency inventory.
3. A permission model showing that untrusted code cannot access deployment credentials or publish an artifact.
4. An environment promotion using the **same release digest**, with a documented rollback to an earlier digest.
5. A reusable pipeline component consumed by two sample services, with clear configuration and ownership.
6. A failure report distinguishing at least two types of fault (code/test/runner/cache/security/promotion) and the remediation.

**Acceptance:** Another developer can follow the pipeline's logs and artifacts to explain exactly **what code** was built, **which checks passed**, **who or what promoted it** and **what is running**. Publish only synthetic or non-sensitive evidence.

## Further study

- [GitHub Actions — Security hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [GitLab — CI/CD security](https://docs.gitlab.com/ci/security/)
- [SLSA framework](https://slsa.dev/)
- [OpenID Connect — GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [OCI image specification](https://github.com/opencontainers/image-spec)
- [Docker — Build attestations](https://docs.docker.com/build/metadata/attestations/)

**Previous:** [D03 — Docker and Containerization](D03%20Docker%20and%20Containerization.md) · **Next:** [D05 — Infrastructure as Code and Terraform](D05%20Infrastructure%20as%20Code%20and%20Terraform.md)
