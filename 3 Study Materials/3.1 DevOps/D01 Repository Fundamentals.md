# D01 — Repository Fundamentals

| | Details |
| --- | --- |
| **Estimated study time** | 6–9 hours |
| **Prerequisites** | Confident everyday use of Git, pull/merge requests and a hosted source-control platform. |

## Objective

Design a **production-ready repository foundation** with clear ownership, safe contribution workflows and enforceable security controls. This module focuses on repository architecture and governance; [D02 — Advanced Git](D02%20Advanced%20Git.md) covers the deeper history, recovery and debugging techniques.

The repository becomes the starting point for the [programme Final Project](../../1%20Foundational%20Documents/1.4%20Final%20Project.md).

## Outcomes

1. Explain and defend a monorepo, multi-repo or separate deployment-repo strategy.
2. Establish clear ownership and boundaries between application, infrastructure and deployment code.
3. Configure and validate review, branch-protection and least-privilege policies where supported.
4. Apply secret-handling and source-control supply-chain safeguards.
5. Demonstrate a governed contribution and record any enforcement gaps.

## Suggested activities

| Activity | Estimated hours |
| --- | ---: |
| Repository architecture, structure and ownership | 1.5–2.5 |
| Governance, access and supply-chain controls | 2–3 |
| Practical Assessment and evidence | 2.5–3.5 |
| **Total** | **6–9** |

## 1. Repository architecture and code ownership

Create or refactor the ongoing Final Project repository:

```text
final-project/
├── app/                   # Application code and tests
├── infra/                 # Infrastructure as code
├── deploy/                # Deployment and GitOps configuration
├── docs/
│   └── decisions/         # Architecture decision records
├── .github/ or .gitlab/   # Hosting-specific automation/configuration
├── .gitignore
├── README.md
└── CONTRIBUTING.md
```

Keep the structure intentionally small; avoid creating empty directories without a reason. The same architecture can be implemented on GitHub or GitLab, with platform-specific controls clearly documented.

**Design exercise:** Decide whether the project should remain a monorepo, split into application/infrastructure repositories, or evolve into a separate deployment-config repository. Evaluate change coupling, permissions, ownership, release cadence, auditability and GitOps reconciliation. Record the decision in a one-page ADR with alternatives and trade-offs.

Define code ownership at least for `app/`, `infra/` and `deploy/`. On GitHub, an example `.github/CODEOWNERS` is:

```text
/app/       @your-org/app-maintainers
/infra/     @your-org/platform-maintainers
/deploy/    @your-org/platform-maintainers
```

Replace placeholders with real, eligible teams. A CODEOWNERS file alone does **not** enforce approvals; combine it with review rules and verify that the required reviewers can actually access the repository. For GitLab, use its supported code-owner syntax and approval settings.

**Repository hygiene:** Implement a suitable `.gitignore` for your chosen stack, excluding local secrets, build products and Terraform state while retaining intentional dependency lockfiles. Demonstrate `git check-ignore -v` and `git ls-files`. Discuss the limitations of `.gitignore` once a secret is already tracked.

## 2. Governance, identity and software supply-chain security

Treat the repository as a **security boundary**, not merely a storage location.

| Control | Design question / evidence |
| --- | --- |
| Permissions | Who may read, push, approve, administer and publish? Are service accounts scoped narrowly? |
| Protected default branch | Are direct pushes, force pushes and deletion restricted? Are bypasses audited or limited? |
| Reviews | Are independent approvals and code-owner reviews required for sensitive paths? |
| Automated checks | Which tests, scans and policies must pass before merge? D04 will build the actual CI pipeline. |
| Identity and provenance | Which authentication methods, MFA policies and commit/tag signing options are available? |
| Secrets | How are tokens issued, stored, rotated and prevented from entering history? |
| Dependencies and automation | Can untrusted pull requests access credentials? Are actions/runners/dependencies reviewed and pinned where appropriate? |
| Releases | How are tags protected and how can the team trace an artifact back to reviewed source? |

**Implement and demonstrate**, where supported by your hosting plan and permissions:

1. Protect `main`, disable force-pushing and deletion, and require changes through pull/merge requests.
2. Configure an approval rule and code-owner review for sensitive paths. Where a solo or private-repo plan cannot enforce this, document the gap rather than claiming it works.
3. Use a feature branch to propose a change in `infra/` or `deploy/`; capture the review and merge record.
4. Verify that an unauthorised direct update is rejected or document why enforcement cannot be tested.
5. Add a lightweight secret-detection safeguard, such as an approved local pre-commit scanner or repository-native secret scanning. **Use fabricated test strings only**; never plant real credentials for the exercise.

Review SSH keys, scoped tokens and signed commits/tags as options rather than mandatory setup steps. A valid signature proves possession of a key, not that the change is safe. Understand how compromised credentials, unsafe workflow triggers and excessive CI token permissions can undermine an otherwise protected repository.

## 3. Practical Assessment — repository governance

In a test repository (or an isolated Final Project repository):

1. Create the application/infrastructure/deployment structure with appropriate ignore rules, a contribution guide and a short ADR.
2. Define code owners and demonstrate the proposed approval workflow for a change to `infra/` or `deploy/`.
3. Configure protected-`main` rules and relevant access restrictions; verify enforcement where your platform allows it.
4. Demonstrate the secret-detection safeguard using non-sensitive test data.
5. Explain the risks, trade-offs and any provider-plan limits that prevent enforcement.

**Completion standard:** Another developer can understand how to contribute safely, who owns sensitive changes and why your controls were chosen.

## References

- [GitHub — Protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub — CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitLab — Protected branches](https://docs.gitlab.com/user/project/repository/branches/protected/)
- [Git documentation — gitignore](https://git-scm.com/docs/gitignore)

**Previous:** [DevOps Syllabus](D00%20DevOps%20Syllabus.md) · **Next:** [D02 — Advanced Git](D02%20Advanced%20Git.md)
