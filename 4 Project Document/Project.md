# Harbour Learning Project — Independent Project Guide

*This document is complete on its own. You do not need the course modules or the master textbook to follow these tasks, although each task assumes the skills named in its purpose.*

## What you are building

A small educational sample system — referred to here as **Harbour** — that demonstrates repository practice, containers, delivery, infrastructure concepts, observability, optional cloud and AI capabilities, and a lightweight internal developer platform experience. Harbour is a **learning project**, not a production-grade commercial platform.

You implement Harbour in **your own separate repository and environments**. This PDP repository contains only written instructions.

## Safety and cost

- Use disposable local environments where possible (containers, kind, sandboxes).
- Never commit real secrets, personal data or production credentials.
- Prefer mocks/simulations when paid cloud or SaaS would be disproportionate.
- Tear down trial resources when finished; record costs you actually incurred.

## Optional tracks

The full route includes all 96 steps. Your personal PDP may mark an entire optional track (for example Datadog or AI) **Out of scope**. Within every **active** route, steps remain mandatory and ordered. Do not casually skip individual steps.

## How to use this guide

1. Complete tasks in order for your active route.
2. Record evidence for each step.
3. When a course module gate points here, finish the listed prerequisites before returning to the module.

## Task ledger overview

| Task | Title |
| --- | --- |
| [PRJ-001](#prj-001) | Establish the training repository |
| [PRJ-002](#prj-002) | Demonstrate collaboration and a reviewed change |
| [PRJ-003](#prj-003) | Apply governance and recover a mistake |
| [PRJ-004](#prj-004) | Defend and improve the repository workflow |
| [PRJ-005](#prj-005) | Containerise the sample service |
| [PRJ-006](#prj-006) | Run the service with a dependency |
| [PRJ-007](#prj-007) | Harden and identify the application image |
| [PRJ-008](#prj-008) | Investigate failure and portability |
| [PRJ-009](#prj-009) | Document a repeatable build and local check |
| [PRJ-010](#prj-010) | Implement reviewed-change validation |
| [PRJ-011](#prj-011) | Produce a traceable release |
| [PRJ-012](#prj-012) | Evaluate supply-chain and promotion controls |
| [PRJ-013](#prj-013) | Describe infrastructure as configuration |
| [PRJ-014](#prj-014) | Separate environments and reuse configuration |
| [PRJ-015](#prj-015) | Demonstrate controlled infrastructure change |
| [PRJ-016](#prj-016) | Defend infrastructure lifecycle decisions |
| [PRJ-017](#prj-017) | Declare desired application state |
| [PRJ-018](#prj-018) | Observe reconciliation and drift |
| [PRJ-019](#prj-019) | Promote and recover an application revision |
| [PRJ-020](#prj-020) | Explain operational control boundaries |
| [PRJ-021](#prj-021) | Record meaningful service health signals |
| [PRJ-022](#prj-022) | Connect metrics, logs and traces |
| [PRJ-023](#prj-023) | Create an actionable alert and runbook |
| [PRJ-024](#prj-024) | Run an evidence-led incident review |
| [PRJ-025](#prj-025) | Onboard the sample service to Datadog |
| [PRJ-026](#prj-026) | Correlate operational evidence |
| [PRJ-027](#prj-027) | Build useful dashboards and monitors |
| [PRJ-028](#prj-028) | Publish a reusable onboarding method |
| [PRJ-029](#prj-029) | Inspect the service host |
| [PRJ-030](#prj-030) | Diagnose a system fault |
| [PRJ-031](#prj-031) | Write an operator checklist |
| [PRJ-032](#prj-032) | Evaluate operating-system hardening |
| [PRJ-033](#prj-033) | Draw the service network path |
| [PRJ-034](#prj-034) | Diagnose name resolution and connectivity |
| [PRJ-035](#prj-035) | Explain the security boundary |
| [PRJ-036](#prj-036) | Investigate complex reachability incidents |
| [PRJ-037](#prj-037) | Classify the training system's cloud needs |
| [PRJ-038](#prj-038) | Evaluate service and responsibility choices |
| [PRJ-039](#prj-039) | Create a governance and cost baseline |
| [PRJ-040](#prj-040) | Defend architecture constraints |
| [PRJ-041](#prj-041) | Establish AWS training guardrails |
| [PRJ-042](#prj-042) | Map the application access path |
| [PRJ-043](#prj-043) | Apply least privilege and change discipline |
| [PRJ-044](#prj-044) | Review security and financial risk |
| [PRJ-045](#prj-045) | Select a deployable AWS design |
| [PRJ-046](#prj-046) | Describe or provision an isolated environment |
| [PRJ-047](#prj-047) | Demonstrate one failure and recovery |
| [PRJ-048](#prj-048) | Evaluate resilience and teardown |
| [PRJ-049](#prj-049) | Define the AI use case |
| [PRJ-050](#prj-050) | Design and compare prompts |
| [PRJ-051](#prj-051) | Implement structured interaction constraints |
| [PRJ-052](#prj-052) | Critically analyse model limits |
| [PRJ-053](#prj-053) | Choose a reliable knowledge source |
| [PRJ-054](#prj-054) | Demonstrate retrieval and attribution |
| [PRJ-055](#prj-055) | Handle missing or conflicting evidence |
| [PRJ-056](#prj-056) | Evaluate retrieval architecture |
| [PRJ-057](#prj-057) | Define an AI quality rubric |
| [PRJ-058](#prj-058) | Run a small evaluation set |
| [PRJ-059](#prj-059) | Design release and safety criteria |
| [PRJ-060](#prj-060) | Audit evaluation blind spots |
| [PRJ-061](#prj-061) | List permitted tool actions |
| [PRJ-062](#prj-062) | Demonstrate a tool interaction |
| [PRJ-063](#prj-063) | Protect privileged actions |
| [PRJ-064](#prj-064) | Evaluate agent autonomy |
| [PRJ-065](#prj-065) | Version the AI configuration |
| [PRJ-066](#prj-066) | Describe a deployment and rollback |
| [PRJ-067](#prj-067) | Observe AI service quality |
| [PRJ-068](#prj-068) | Defend the AI operating model |
| [PRJ-069](#prj-069) | Map Kubernetes components |
| [PRJ-070](#prj-070) | Start a disposable learning cluster |
| [PRJ-071](#prj-071) | Choose an appropriate cluster configuration |
| [PRJ-072](#prj-072) | Critique cluster design trade-offs |
| [PRJ-073](#prj-073) | Describe the sample Kubernetes workload |
| [PRJ-074](#prj-074) | Manage configuration and health |
| [PRJ-075](#prj-075) | Demonstrate rollout and workload resilience |
| [PRJ-076](#prj-076) | Critique workload and packaging patterns |
| [PRJ-077](#prj-077) | Identify cluster access boundaries |
| [PRJ-078](#prj-078) | Apply a baseline access model |
| [PRJ-079](#prj-079) | Demonstrate a denied unsafe request |
| [PRJ-080](#prj-080) | Critique a policy framework |
| [PRJ-081](#prj-081) | Write a basic cluster health checklist |
| [PRJ-082](#prj-082) | Diagnose a routine workload outage |
| [PRJ-083](#prj-083) | Recover a stateful or operational failure |
| [PRJ-084](#prj-084) | Defend an operating and recovery strategy |
| [PRJ-085](#prj-085) | Identify platform users |
| [PRJ-086](#prj-086) | Define a platform service boundary |
| [PRJ-087](#prj-087) | Create a platform architecture decision |
| [PRJ-088](#prj-088) | Evaluate platform evolution |
| [PRJ-089](#prj-089) | Document the developer's first use |
| [PRJ-090](#prj-090) | Define reusable starter material |
| [PRJ-091](#prj-091) | Demonstrate self-service with guardrails |
| [PRJ-092](#prj-092) | Evaluate self-service effectiveness |
| [PRJ-093](#prj-093) | Describe the complete learning platform |
| [PRJ-094](#prj-094) | Demonstrate the end-to-end developer journey |
| [PRJ-095](#prj-095) | Present recovery and acceptance evidence |
| [PRJ-096](#prj-096) | Defend and hand over the platform |

---

## PRJ-001 — Establish the training repository

**Position:** Step 1 of 96 · Topic `DEV-01` (Repository Management and Git) · Level Beginner

**Prerequisites:** None — this is the first active step.

**Purpose:** Demonstrate beginner-level practical capability in Repository Management and Git.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Establish the training repository**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-001` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Establish the training repository** and explain what you did.

### Evidence (minimum)

Create the project repository, a useful README and a clean initial history; record the repository URL and initial commit.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-002 — Demonstrate collaboration and a reviewed change

**Position:** Step 2 of 96 · Topic `DEV-01` (Repository Management and Git) · Level Intermediate

**Prerequisites:** PRJ-001 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Repository Management and Git.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate collaboration and a reviewed change**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-002` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate collaboration and a reviewed change** and explain what you did.

### Evidence (minimum)

Create a branch, make a small deliberate change and show a pull request and review decision or a documented equivalent.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-003 — Apply governance and recover a mistake

**Position:** Step 3 of 96 · Topic `DEV-01` (Repository Management and Git) · Level Professional

**Prerequisites:** PRJ-002 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Repository Management and Git.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Apply governance and recover a mistake**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-003` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Apply governance and recover a mistake** and explain what you did.

### Evidence (minimum)

Document ownership and protected-change rules; use a disposable branch to recover a lost change or resolve a nontrivial conflict safely.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-004 — Defend and improve the repository workflow

**Position:** Step 4 of 96 · Topic `DEV-01` (Repository Management and Git) · Level Expert

**Prerequisites:** PRJ-003 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Repository Management and Git.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend and improve the repository workflow**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-004` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend and improve the repository workflow** and explain what you did.

### Evidence (minimum)

Compare merge/rebase/revert policies, demonstrate a regression diagnosis or history recovery, and defend trade-offs in an ADR.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-005 — Containerise the sample service

**Position:** Step 5 of 96 · Topic `DEV-02` (Containers and Docker) · Level Beginner

**Prerequisites:** PRJ-004 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Containers and Docker.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Containerise the sample service**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-005` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Containerise the sample service** and explain what you did.

### Evidence (minimum)

Write the sample service's container definition in a separate learner workspace and prove the service starts and answers a health request.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-006 — Run the service with a dependency

**Position:** Step 6 of 96 · Topic `DEV-02` (Containers and Docker) · Level Intermediate

**Prerequisites:** PRJ-005 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Containers and Docker.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Run the service with a dependency**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-006` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Run the service with a dependency** and explain what you did.

### Evidence (minimum)

Add a local data service and a composed runtime; show successful startup and a diagnosed connectivity failure.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-007 — Harden and identify the application image

**Position:** Step 7 of 96 · Topic `DEV-02` (Containers and Docker) · Level Professional

**Prerequisites:** PRJ-006 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Containers and Docker.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Harden and identify the application image**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-007` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Harden and identify the application image** and explain what you did.

### Evidence (minimum)

Apply image hygiene, non-root runtime principles, resource limits and an immutable image reference; record what changed and why.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-008 — Investigate failure and portability

**Position:** Step 8 of 96 · Topic `DEV-02` (Containers and Docker) · Level Expert

**Prerequisites:** PRJ-007 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Containers and Docker.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Investigate failure and portability**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-008` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Investigate failure and portability** and explain what you did.

### Evidence (minimum)

Inject a controlled startup, storage or networking problem; restore service and explain portability and security limits.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-009 — Document a repeatable build and local check

**Position:** Step 9 of 96 · Topic `DEV-03` (CI/CD and Build Automation) · Level Beginner

**Prerequisites:** PRJ-008 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in CI/CD and Build Automation.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Document a repeatable build and local check**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-009` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Document a repeatable build and local check** and explain what you did.

### Evidence (minimum)

Specify the build, a basic automated check and a reproducible command sequence for the sample service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-010 — Implement reviewed-change validation

**Position:** Step 10 of 96 · Topic `DEV-03` (CI/CD and Build Automation) · Level Intermediate

**Prerequisites:** PRJ-009 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in CI/CD and Build Automation.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Implement reviewed-change validation**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-010` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Implement reviewed-change validation** and explain what you did.

### Evidence (minimum)

In the learner's project repository, configure a pipeline that runs on a proposed change and demonstrate a deliberately failing check.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-011 — Produce a traceable release

**Position:** Step 11 of 96 · Topic `DEV-03` (CI/CD and Build Automation) · Level Professional

**Prerequisites:** PRJ-010 must be completed.

**Purpose:** Demonstrate professional-level practical capability in CI/CD and Build Automation.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Produce a traceable release**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-011` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Produce a traceable release** and explain what you did.

### Evidence (minimum)

Create a successful release with a recorded commit, image or package digest and a clear promotion hand-off.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-012 — Evaluate supply-chain and promotion controls

**Position:** Step 12 of 96 · Topic `DEV-03` (CI/CD and Build Automation) · Level Expert

**Prerequisites:** PRJ-011 must be completed.

**Purpose:** Demonstrate expert-level practical capability in CI/CD and Build Automation.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate supply-chain and promotion controls**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-012` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate supply-chain and promotion controls** and explain what you did.

### Evidence (minimum)

Demonstrate a rejected unsafe promotion and explain the chosen approval, provenance and rollback design.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-013 — Describe infrastructure as configuration

**Position:** Step 13 of 96 · Topic `DEV-04` (Infrastructure as Code and Terraform) · Level Beginner

**Prerequisites:** PRJ-012 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Infrastructure as Code and Terraform.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Describe infrastructure as configuration**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-013` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Describe infrastructure as configuration** and explain what you did.

### Evidence (minimum)

Create a small declarative infrastructure plan in a sandbox and explain resources, providers and state.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-014 — Separate environments and reuse configuration

**Position:** Step 14 of 96 · Topic `DEV-04` (Infrastructure as Code and Terraform) · Level Intermediate

**Prerequisites:** PRJ-013 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Infrastructure as Code and Terraform.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Separate environments and reuse configuration**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-014` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Separate environments and reuse configuration** and explain what you did.

### Evidence (minimum)

Define an isolated learning environment using a reusable module, including safe variable handling.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-015 — Demonstrate controlled infrastructure change

**Position:** Step 15 of 96 · Topic `DEV-04` (Infrastructure as Code and Terraform) · Level Professional

**Prerequisites:** PRJ-014 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Infrastructure as Code and Terraform.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate controlled infrastructure change**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-015` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate controlled infrastructure change** and explain what you did.

### Evidence (minimum)

Record a reviewed plan, state/locking approach and one deliberate drift or failure investigation.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-016 — Defend infrastructure lifecycle decisions

**Position:** Step 16 of 96 · Topic `DEV-04` (Infrastructure as Code and Terraform) · Level Expert

**Prerequisites:** PRJ-015 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Infrastructure as Code and Terraform.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend infrastructure lifecycle decisions**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-016` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend infrastructure lifecycle decisions** and explain what you did.

### Evidence (minimum)

Compare state, IAM and change-control alternatives, demonstrate safe teardown and document limits and costs.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-017 — Declare desired application state

**Position:** Step 17 of 96 · Topic `DEV-05` (GitOps and Release Operations) · Level Beginner

**Prerequisites:** PRJ-016 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in GitOps and Release Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Declare desired application state**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-017` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Declare desired application state** and explain what you did.

### Evidence (minimum)

Write the learner project's target deployment state as documents stored with version history.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-018 — Observe reconciliation and drift

**Position:** Step 18 of 96 · Topic `DEV-05` (GitOps and Release Operations) · Level Intermediate

**Prerequisites:** PRJ-017 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in GitOps and Release Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Observe reconciliation and drift**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-018` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Observe reconciliation and drift** and explain what you did.

### Evidence (minimum)

Use an appropriate training environment to apply/reconcile desired state and record observed versus desired configuration.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-019 — Promote and recover an application revision

**Position:** Step 19 of 96 · Topic `DEV-05` (GitOps and Release Operations) · Level Professional

**Prerequisites:** PRJ-018 must be completed.

**Purpose:** Demonstrate professional-level practical capability in GitOps and Release Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Promote and recover an application revision**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-019` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Promote and recover an application revision** and explain what you did.

### Evidence (minimum)

Demonstrate a reviewed promotion and an audited rollback without rebuilding the immutable release.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-020 — Explain operational control boundaries

**Position:** Step 20 of 96 · Topic `DEV-05` (GitOps and Release Operations) · Level Expert

**Prerequisites:** PRJ-019 must be completed.

**Purpose:** Demonstrate expert-level practical capability in GitOps and Release Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Explain operational control boundaries**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-020` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Explain operational control boundaries** and explain what you did.

### Evidence (minimum)

Evaluate drift correction, break-glass access, environment separation and recovery strategies in an ADR.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-021 — Record meaningful service health signals

**Position:** Step 21 of 96 · Topic `DEV-06` (Observability and Reliability) · Level Beginner

**Prerequisites:** PRJ-020 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Observability and Reliability.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Record meaningful service health signals**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-021` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Record meaningful service health signals** and explain what you did.

### Evidence (minimum)

Identify a user journey and emit or capture basic logs and one useful service metric.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-022 — Connect metrics, logs and traces

**Position:** Step 22 of 96 · Topic `DEV-06` (Observability and Reliability) · Level Intermediate

**Prerequisites:** PRJ-021 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Observability and Reliability.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Connect metrics, logs and traces**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-022` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Connect metrics, logs and traces** and explain what you did.

### Evidence (minimum)

Produce correlated telemetry or a documented simulation and identify the responsible component during a failure.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-023 — Create an actionable alert and runbook

**Position:** Step 23 of 96 · Topic `DEV-06` (Observability and Reliability) · Level Professional

**Prerequisites:** PRJ-022 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Observability and Reliability.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Create an actionable alert and runbook**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-023` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Create an actionable alert and runbook** and explain what you did.

### Evidence (minimum)

Define an SLI/SLO, alert rationale and response procedure for the learning service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-024 — Run an evidence-led incident review

**Position:** Step 24 of 96 · Topic `DEV-06` (Observability and Reliability) · Level Expert

**Prerequisites:** PRJ-023 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Observability and Reliability.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Run an evidence-led incident review**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-024` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Run an evidence-led incident review** and explain what you did.

### Evidence (minimum)

Inject a fault, diagnose it from telemetry, document uncertainty and improve alerting or instrumentation.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-025 — Onboard the sample service to Datadog

**Position:** Step 25 of 96 · Topic `DEV-07` (Datadog Monitoring) · Level Beginner

**Prerequisites:** PRJ-024 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Datadog Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Onboard the sample service to Datadog**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-025` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Onboard the sample service to Datadog** and explain what you did.

### Evidence (minimum)

In a disposable or authorised account, document agent connection and basic service visibility; provide a no-paid-account interpretation route if needed.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-026 — Correlate operational evidence

**Position:** Step 26 of 96 · Topic `DEV-07` (Datadog Monitoring) · Level Intermediate

**Prerequisites:** PRJ-025 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Datadog Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Correlate operational evidence**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-026` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Correlate operational evidence** and explain what you did.

### Evidence (minimum)

Show a query or view connecting service health, logs and APM traces, or an equivalent documented walk-through.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-027 — Build useful dashboards and monitors

**Position:** Step 27 of 96 · Topic `DEV-07` (Datadog Monitoring) · Level Professional

**Prerequisites:** PRJ-026 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Datadog Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Build useful dashboards and monitors**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-027` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Build useful dashboards and monitors** and explain what you did.

### Evidence (minimum)

Create a concise service dashboard and prove monitors distinguish app incidents from missing telemetry.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-028 — Publish a reusable onboarding method

**Position:** Step 28 of 96 · Topic `DEV-07` (Datadog Monitoring) · Level Expert

**Prerequisites:** PRJ-027 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Datadog Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Publish a reusable onboarding method**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-028` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Publish a reusable onboarding method** and explain what you did.

### Evidence (minimum)

Show how a second sample service would be instrumented and critically assess cost, cardinality, privacy and vendor lock-in.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-029 — Inspect the service host

**Position:** Step 29 of 96 · Topic `CLD-01` (Linux Systems and Operations) · Level Beginner

**Prerequisites:** PRJ-028 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Linux Systems and Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Inspect the service host**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-029` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Inspect the service host** and explain what you did.

### Evidence (minimum)

Record processes, permissions, users, logs and resource observations for a Linux training host.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-030 — Diagnose a system fault

**Position:** Step 30 of 96 · Topic `CLD-01` (Linux Systems and Operations) · Level Intermediate

**Prerequisites:** PRJ-029 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Linux Systems and Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Diagnose a system fault**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-030` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Diagnose a system fault** and explain what you did.

### Evidence (minimum)

Use terminal tools to identify a failed process, permission issue or resource exhaustion and restore a test service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-031 — Write an operator checklist

**Position:** Step 31 of 96 · Topic `CLD-01` (Linux Systems and Operations) · Level Professional

**Prerequisites:** PRJ-030 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Linux Systems and Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Write an operator checklist**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-031` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Write an operator checklist** and explain what you did.

### Evidence (minimum)

Document a repeatable startup, access and investigation procedure for the training environment.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-032 — Evaluate operating-system hardening

**Position:** Step 32 of 96 · Topic `CLD-01` (Linux Systems and Operations) · Level Expert

**Prerequisites:** PRJ-031 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Linux Systems and Operations.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate operating-system hardening**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-032` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate operating-system hardening** and explain what you did.

### Evidence (minimum)

Compare service isolation, privilege reduction, operational automation and response under a realistic scenario.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-033 — Draw the service network path

**Position:** Step 33 of 96 · Topic `CLD-02` (Networking, DNS and TLS) · Level Beginner

**Prerequisites:** PRJ-032 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Networking, DNS and TLS.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Draw the service network path**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-033` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Draw the service network path** and explain what you did.

### Evidence (minimum)

Document client, DNS, IP/port, routing and application endpoints for the training service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-034 — Diagnose name resolution and connectivity

**Position:** Step 34 of 96 · Topic `CLD-02` (Networking, DNS and TLS) · Level Intermediate

**Prerequisites:** PRJ-033 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Networking, DNS and TLS.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Diagnose name resolution and connectivity**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-034` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Diagnose name resolution and connectivity** and explain what you did.

### Evidence (minimum)

Produce a successful test and an intentional DNS or network failure diagnosis with evidence.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-035 — Explain the security boundary

**Position:** Step 35 of 96 · Topic `CLD-02` (Networking, DNS and TLS) · Level Professional

**Prerequisites:** PRJ-034 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Networking, DNS and TLS.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Explain the security boundary**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-035` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Explain the security boundary** and explain what you did.

### Evidence (minimum)

Describe and, where practical, configure TLS, firewall and least-exposure choices for a training endpoint.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-036 — Investigate complex reachability incidents

**Position:** Step 36 of 96 · Topic `CLD-02` (Networking, DNS and TLS) · Level Expert

**Prerequisites:** PRJ-035 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Networking, DNS and TLS.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Investigate complex reachability incidents**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-036` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Investigate complex reachability incidents** and explain what you did.

### Evidence (minimum)

Analyse a multi-layer connection problem, distinguish TLS/DNS/routing causes and document a robust triage method.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-037 — Classify the training system's cloud needs

**Position:** Step 37 of 96 · Topic `CLD-03` (Cloud Foundations and Governance) · Level Beginner

**Prerequisites:** PRJ-036 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Cloud Foundations and Governance.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Classify the training system's cloud needs**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-037` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Classify the training system's cloud needs** and explain what you did.

### Evidence (minimum)

Map the sample service to compute, storage, network and identity responsibilities.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-038 — Evaluate service and responsibility choices

**Position:** Step 38 of 96 · Topic `CLD-03` (Cloud Foundations and Governance) · Level Intermediate

**Prerequisites:** PRJ-037 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Cloud Foundations and Governance.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate service and responsibility choices**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-038` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate service and responsibility choices** and explain what you did.

### Evidence (minimum)

Compare two suitable hosting approaches with cost, support and security implications.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-039 — Create a governance and cost baseline

**Position:** Step 39 of 96 · Topic `CLD-03` (Cloud Foundations and Governance) · Level Professional

**Prerequisites:** PRJ-038 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Cloud Foundations and Governance.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Create a governance and cost baseline**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-039` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Create a governance and cost baseline** and explain what you did.

### Evidence (minimum)

Document ownership, billing guardrails, data classification and operating responsibilities.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-040 — Defend architecture constraints

**Position:** Step 40 of 96 · Topic `CLD-03` (Cloud Foundations and Governance) · Level Expert

**Prerequisites:** PRJ-039 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Cloud Foundations and Governance.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend architecture constraints**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-040` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend architecture constraints** and explain what you did.

### Evidence (minimum)

Produce a decision record weighing shared responsibility, portability, resilience and operational limits.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-041 — Establish AWS training guardrails

**Position:** Step 41 of 96 · Topic `CLD-04` (AWS Identity, Networking and Cost Controls) · Level Beginner

**Prerequisites:** PRJ-040 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in AWS Identity, Networking and Cost Controls.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Establish AWS training guardrails**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-041` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Establish AWS training guardrails** and explain what you did.

### Evidence (minimum)

Identify an authorised account, identity baseline and spending limit without storing secrets in educational materials.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-042 — Map the application access path

**Position:** Step 42 of 96 · Topic `CLD-04` (AWS Identity, Networking and Cost Controls) · Level Intermediate

**Prerequisites:** PRJ-041 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in AWS Identity, Networking and Cost Controls.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Map the application access path**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-042` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Map the application access path** and explain what you did.

### Evidence (minimum)

Document IAM roles and a VPC/network route suitable for the sample application.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-043 — Apply least privilege and change discipline

**Position:** Step 43 of 96 · Topic `CLD-04` (AWS Identity, Networking and Cost Controls) · Level Professional

**Prerequisites:** PRJ-042 must be completed.

**Purpose:** Demonstrate professional-level practical capability in AWS Identity, Networking and Cost Controls.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Apply least privilege and change discipline**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-043` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Apply least privilege and change discipline** and explain what you did.

### Evidence (minimum)

Demonstrate controlled access in a disposable environment, plus a rejected excessive permission or public exposure.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-044 — Review security and financial risk

**Position:** Step 44 of 96 · Topic `CLD-04` (AWS Identity, Networking and Cost Controls) · Level Expert

**Prerequisites:** PRJ-043 must be completed.

**Purpose:** Demonstrate expert-level practical capability in AWS Identity, Networking and Cost Controls.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Review security and financial risk**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-044` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Review security and financial risk** and explain what you did.

### Evidence (minimum)

Defend account isolation, private/public boundaries, monitoring, quotas and teardown choices.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-045 — Select a deployable AWS design

**Position:** Step 45 of 96 · Topic `CLD-05` (AWS Infrastructure, Resilience and Architecture) · Level Beginner

**Prerequisites:** PRJ-044 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in AWS Infrastructure, Resilience and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Select a deployable AWS design**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-045` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Select a deployable AWS design** and explain what you did.

### Evidence (minimum)

Draw a minimal architecture for the sample service with dependencies and cost assumptions.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-046 — Describe or provision an isolated environment

**Position:** Step 46 of 96 · Topic `CLD-05` (AWS Infrastructure, Resilience and Architecture) · Level Intermediate

**Prerequisites:** PRJ-045 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in AWS Infrastructure, Resilience and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Describe or provision an isolated environment**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-046` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Describe or provision an isolated environment** and explain what you did.

### Evidence (minimum)

Build a bounded learning deployment via documented steps, or use a transparent simulation if cloud spending is excluded.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-047 — Demonstrate one failure and recovery

**Position:** Step 47 of 96 · Topic `CLD-05` (AWS Infrastructure, Resilience and Architecture) · Level Professional

**Prerequisites:** PRJ-046 must be completed.

**Purpose:** Demonstrate professional-level practical capability in AWS Infrastructure, Resilience and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate one failure and recovery**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-047` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate one failure and recovery** and explain what you did.

### Evidence (minimum)

Record an injected or simulated incident and recovery evidence consistent with the architecture decision.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-048 — Evaluate resilience and teardown

**Position:** Step 48 of 96 · Topic `CLD-05` (AWS Infrastructure, Resilience and Architecture) · Level Expert

**Prerequisites:** PRJ-047 must be completed.

**Purpose:** Demonstrate expert-level practical capability in AWS Infrastructure, Resilience and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate resilience and teardown**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-048` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate resilience and teardown** and explain what you did.

### Evidence (minimum)

Compare recovery objectives, availability, capacity, cost and portability; remove trial resources safely.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-049 — Define the AI use case

**Position:** Step 49 of 96 · Topic `AIE-01` (LLM Fundamentals and Prompting) · Level Beginner

**Prerequisites:** PRJ-048 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in LLM Fundamentals and Prompting.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Define the AI use case**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-049` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Define the AI use case** and explain what you did.

### Evidence (minimum)

State a narrow, non-privileged assistant purpose and record expected inputs, outputs and known limitations.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-050 — Design and compare prompts

**Position:** Step 50 of 96 · Topic `AIE-01` (LLM Fundamentals and Prompting) · Level Intermediate

**Prerequisites:** PRJ-049 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in LLM Fundamentals and Prompting.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Design and compare prompts**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-050` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Design and compare prompts** and explain what you did.

### Evidence (minimum)

Create prompts and compare responses against a small explicit rubric, using a mock provider if needed.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-051 — Implement structured interaction constraints

**Position:** Step 51 of 96 · Topic `AIE-01` (LLM Fundamentals and Prompting) · Level Professional

**Prerequisites:** PRJ-050 must be completed.

**Purpose:** Demonstrate professional-level practical capability in LLM Fundamentals and Prompting.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Implement structured interaction constraints**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-051` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Implement structured interaction constraints** and explain what you did.

### Evidence (minimum)

Define output format, error behaviour and fallback rules for the assistant design.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-052 — Critically analyse model limits

**Position:** Step 52 of 96 · Topic `AIE-01` (LLM Fundamentals and Prompting) · Level Expert

**Prerequisites:** PRJ-051 must be completed.

**Purpose:** Demonstrate expert-level practical capability in LLM Fundamentals and Prompting.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Critically analyse model limits**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-052` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Critically analyse model limits** and explain what you did.

### Evidence (minimum)

Assess prompt robustness, context, hallucination, threat scenarios and how users are informed of uncertainty.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-053 — Choose a reliable knowledge source

**Position:** Step 53 of 96 · Topic `AIE-02` (Grounding, Retrieval and Knowledge Use) · Level Beginner

**Prerequisites:** PRJ-052 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Grounding, Retrieval and Knowledge Use.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Choose a reliable knowledge source**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-053` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Choose a reliable knowledge source** and explain what you did.

### Evidence (minimum)

Define a small permitted read-only reference source and its update policy.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-054 — Demonstrate retrieval and attribution

**Position:** Step 54 of 96 · Topic `AIE-02` (Grounding, Retrieval and Knowledge Use) · Level Intermediate

**Prerequisites:** PRJ-053 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Grounding, Retrieval and Knowledge Use.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate retrieval and attribution**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-054` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate retrieval and attribution** and explain what you did.

### Evidence (minimum)

Show how a question retrieves relevant material and presents grounded evidence with source references.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-055 — Handle missing or conflicting evidence

**Position:** Step 55 of 96 · Topic `AIE-02` (Grounding, Retrieval and Knowledge Use) · Level Professional

**Prerequisites:** PRJ-054 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Grounding, Retrieval and Knowledge Use.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Handle missing or conflicting evidence**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-055` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Handle missing or conflicting evidence** and explain what you did.

### Evidence (minimum)

Record refusal/fallback and citation behaviour for incomplete, stale or conflicting sources.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-056 — Evaluate retrieval architecture

**Position:** Step 56 of 96 · Topic `AIE-02` (Grounding, Retrieval and Knowledge Use) · Level Expert

**Prerequisites:** PRJ-055 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Grounding, Retrieval and Knowledge Use.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate retrieval architecture**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-056` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate retrieval architecture** and explain what you did.

### Evidence (minimum)

Compare retrieval quality, chunking, indexing, privacy, freshness and operational cost.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-057 — Define an AI quality rubric

**Position:** Step 57 of 96 · Topic `AIE-03` (AI Evaluation, Safety and Quality) · Level Beginner

**Prerequisites:** PRJ-056 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in AI Evaluation, Safety and Quality.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Define an AI quality rubric**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-057` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Define an AI quality rubric** and explain what you did.

### Evidence (minimum)

Create representative success and failure scenarios tied to the assistant's intended user task.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-058 — Run a small evaluation set

**Position:** Step 58 of 96 · Topic `AIE-03` (AI Evaluation, Safety and Quality) · Level Intermediate

**Prerequisites:** PRJ-057 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in AI Evaluation, Safety and Quality.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Run a small evaluation set**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-058` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Run a small evaluation set** and explain what you did.

### Evidence (minimum)

Compare candidate responses against expected answers and record failures without hiding them.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-059 — Design release and safety criteria

**Position:** Step 59 of 96 · Topic `AIE-03` (AI Evaluation, Safety and Quality) · Level Professional

**Prerequisites:** PRJ-058 must be completed.

**Purpose:** Demonstrate professional-level practical capability in AI Evaluation, Safety and Quality.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Design release and safety criteria**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-059` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Design release and safety criteria** and explain what you did.

### Evidence (minimum)

Set quality thresholds, misuse cases and human-review triggers appropriate to the limited assistant.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-060 — Audit evaluation blind spots

**Position:** Step 60 of 96 · Topic `AIE-03` (AI Evaluation, Safety and Quality) · Level Expert

**Prerequisites:** PRJ-059 must be completed.

**Purpose:** Demonstrate expert-level practical capability in AI Evaluation, Safety and Quality.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Audit evaluation blind spots**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-060` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Audit evaluation blind spots** and explain what you did.

### Evidence (minimum)

Evaluate distribution shift, prompt injection, data leakage, measurement bias and model change impacts.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-061 — List permitted tool actions

**Position:** Step 61 of 96 · Topic `AIE-04` (Agents, Tools and Orchestration) · Level Beginner

**Prerequisites:** PRJ-060 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Agents, Tools and Orchestration.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **List permitted tool actions**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-061` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **List permitted tool actions** and explain what you did.

### Evidence (minimum)

Document an assistant's read-only tools, inputs, outputs and boundaries.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-062 — Demonstrate a tool interaction

**Position:** Step 62 of 96 · Topic `AIE-04` (Agents, Tools and Orchestration) · Level Intermediate

**Prerequisites:** PRJ-061 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Agents, Tools and Orchestration.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate a tool interaction**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-062` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate a tool interaction** and explain what you did.

### Evidence (minimum)

Trace a plan-call-observe-answer cycle and show tool errors handled explicitly.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-063 — Protect privileged actions

**Position:** Step 63 of 96 · Topic `AIE-04` (Agents, Tools and Orchestration) · Level Professional

**Prerequisites:** PRJ-062 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Agents, Tools and Orchestration.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Protect privileged actions**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-063` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Protect privileged actions** and explain what you did.

### Evidence (minimum)

Document and demonstrate denial of an unauthorised mutating request, with an approval path if one is in scope.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-064 — Evaluate agent autonomy

**Position:** Step 64 of 96 · Topic `AIE-04` (Agents, Tools and Orchestration) · Level Expert

**Prerequisites:** PRJ-063 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Agents, Tools and Orchestration.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate agent autonomy**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-064` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate agent autonomy** and explain what you did.

### Evidence (minimum)

Critique tool composition, oversight, prompt injection, recovery and when not to use an agent.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-065 — Version the AI configuration

**Position:** Step 65 of 96 · Topic `AIE-05` (LLMOps, Deployment and Monitoring) · Level Beginner

**Prerequisites:** PRJ-064 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in LLMOps, Deployment and Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Version the AI configuration**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-065` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Version the AI configuration** and explain what you did.

### Evidence (minimum)

Record the selected model, prompt, tool contract and intended environment in the learner project.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-066 — Describe a deployment and rollback

**Position:** Step 66 of 96 · Topic `AIE-05` (LLMOps, Deployment and Monitoring) · Level Intermediate

**Prerequisites:** PRJ-065 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in LLMOps, Deployment and Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Describe a deployment and rollback**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-066` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Describe a deployment and rollback** and explain what you did.

### Evidence (minimum)

Show how a controlled feature is enabled, disabled or rolled back, even if the provider is mocked.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-067 — Observe AI service quality

**Position:** Step 67 of 96 · Topic `AIE-05` (LLMOps, Deployment and Monitoring) · Level Professional

**Prerequisites:** PRJ-066 must be completed.

**Purpose:** Demonstrate professional-level practical capability in LLMOps, Deployment and Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Observe AI service quality**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-067` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Observe AI service quality** and explain what you did.

### Evidence (minimum)

Record latency, errors, cost proxies and evaluation trends for a set of representative interactions.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-068 — Defend the AI operating model

**Position:** Step 68 of 96 · Topic `AIE-05` (LLMOps, Deployment and Monitoring) · Level Expert

**Prerequisites:** PRJ-067 must be completed.

**Purpose:** Demonstrate expert-level practical capability in LLMOps, Deployment and Monitoring.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend the AI operating model**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-068` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend the AI operating model** and explain what you did.

### Evidence (minimum)

Evaluate change management, kill switches, budgets, privacy, quality drift and platform integration.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-069 — Map Kubernetes components

**Position:** Step 69 of 96 · Topic `PLT-01` (Kubernetes Fundamentals and Architecture) · Level Beginner

**Prerequisites:** PRJ-068 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Kubernetes Fundamentals and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Map Kubernetes components**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-069` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Map Kubernetes components** and explain what you did.

### Evidence (minimum)

Describe the control plane, node, workload and service responsibilities for the sample platform.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-070 — Start a disposable learning cluster

**Position:** Step 70 of 96 · Topic `PLT-01` (Kubernetes Fundamentals and Architecture) · Level Intermediate

**Prerequisites:** PRJ-069 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Kubernetes Fundamentals and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Start a disposable learning cluster**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-070` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Start a disposable learning cluster** and explain what you did.

### Evidence (minimum)

Use a safe training environment to inspect cluster state and explain the basic resource lifecycle.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-071 — Choose an appropriate cluster configuration

**Position:** Step 71 of 96 · Topic `PLT-01` (Kubernetes Fundamentals and Architecture) · Level Professional

**Prerequisites:** PRJ-070 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Kubernetes Fundamentals and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Choose an appropriate cluster configuration**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-071` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Choose an appropriate cluster configuration** and explain what you did.

### Evidence (minimum)

Document deployment architecture and basic separation of environments for the sample service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-072 — Critique cluster design trade-offs

**Position:** Step 72 of 96 · Topic `PLT-01` (Kubernetes Fundamentals and Architecture) · Level Expert

**Prerequisites:** PRJ-071 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Kubernetes Fundamentals and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Critique cluster design trade-offs**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-072` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Critique cluster design trade-offs** and explain what you did.

### Evidence (minimum)

Assess scheduling, control-plane, security and scale constraints without requiring a production cluster.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-073 — Describe the sample Kubernetes workload

**Position:** Step 73 of 96 · Topic `PLT-02` (Kubernetes Workloads, Configuration and Packaging) · Level Beginner

**Prerequisites:** PRJ-072 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Kubernetes Workloads, Configuration and Packaging.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Describe the sample Kubernetes workload**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-073` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Describe the sample Kubernetes workload** and explain what you did.

### Evidence (minimum)

Create or document a Pod/Deployment/Service configuration appropriate to the training application.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-074 — Manage configuration and health

**Position:** Step 74 of 96 · Topic `PLT-02` (Kubernetes Workloads, Configuration and Packaging) · Level Intermediate

**Prerequisites:** PRJ-073 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Kubernetes Workloads, Configuration and Packaging.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Manage configuration and health**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-074` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Manage configuration and health** and explain what you did.

### Evidence (minimum)

Add appropriate probes, configuration, secrets handling and resource requests; show a normal update.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-075 — Demonstrate rollout and workload resilience

**Position:** Step 75 of 96 · Topic `PLT-02` (Kubernetes Workloads, Configuration and Packaging) · Level Professional

**Prerequisites:** PRJ-074 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Kubernetes Workloads, Configuration and Packaging.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate rollout and workload resilience**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-075` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate rollout and workload resilience** and explain what you did.

### Evidence (minimum)

Use version-controlled manifests to deploy and recover from a controlled failure.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-076 — Critique workload and packaging patterns

**Position:** Step 76 of 96 · Topic `PLT-02` (Kubernetes Workloads, Configuration and Packaging) · Level Expert

**Prerequisites:** PRJ-075 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Kubernetes Workloads, Configuration and Packaging.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Critique workload and packaging patterns**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-076` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Critique workload and packaging patterns** and explain what you did.

### Evidence (minimum)

Compare controllers, Helm, Kustomize, stateful workloads and maintenance trade-offs.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-077 — Identify cluster access boundaries

**Position:** Step 77 of 96 · Topic `PLT-03` (Kubernetes Security and Policy) · Level Beginner

**Prerequisites:** PRJ-076 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Kubernetes Security and Policy.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Identify cluster access boundaries**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-077` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Identify cluster access boundaries** and explain what you did.

### Evidence (minimum)

Map namespaces, identities and resource ownership for the sample platform.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-078 — Apply a baseline access model

**Position:** Step 78 of 96 · Topic `PLT-03` (Kubernetes Security and Policy) · Level Intermediate

**Prerequisites:** PRJ-077 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Kubernetes Security and Policy.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Apply a baseline access model**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-078` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Apply a baseline access model** and explain what you did.

### Evidence (minimum)

Document or demonstrate an appropriate role, quota or workload security restriction in a disposable namespace.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-079 — Demonstrate a denied unsafe request

**Position:** Step 79 of 96 · Topic `PLT-03` (Kubernetes Security and Policy) · Level Professional

**Prerequisites:** PRJ-078 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Kubernetes Security and Policy.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate a denied unsafe request**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-079` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate a denied unsafe request** and explain what you did.

### Evidence (minimum)

Record one access or admission-policy denial and explain why it happened.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-080 — Critique a policy framework

**Position:** Step 80 of 96 · Topic `PLT-03` (Kubernetes Security and Policy) · Level Expert

**Prerequisites:** PRJ-079 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Kubernetes Security and Policy.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Critique a policy framework**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-080` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Critique a policy framework** and explain what you did.

### Evidence (minimum)

Compare admission, NetworkPolicy, RBAC, tenancy, audit and policy maintenance risks.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-081 — Write a basic cluster health checklist

**Position:** Step 81 of 96 · Topic `PLT-04` (Kubernetes Operations, Incidents and Recovery) · Level Beginner

**Prerequisites:** PRJ-080 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Kubernetes Operations, Incidents and Recovery.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Write a basic cluster health checklist**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-081` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Write a basic cluster health checklist** and explain what you did.

### Evidence (minimum)

Identify workload readiness, events, logs and node state relevant to the sample platform.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-082 — Diagnose a routine workload outage

**Position:** Step 82 of 96 · Topic `PLT-04` (Kubernetes Operations, Incidents and Recovery) · Level Intermediate

**Prerequisites:** PRJ-081 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Kubernetes Operations, Incidents and Recovery.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Diagnose a routine workload outage**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-082` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Diagnose a routine workload outage** and explain what you did.

### Evidence (minimum)

Inject or simulate an unavailable Pod and demonstrate a structured diagnosis.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-083 — Recover a stateful or operational failure

**Position:** Step 83 of 96 · Topic `PLT-04` (Kubernetes Operations, Incidents and Recovery) · Level Professional

**Prerequisites:** PRJ-082 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Kubernetes Operations, Incidents and Recovery.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Recover a stateful or operational failure**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-083` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Recover a stateful or operational failure** and explain what you did.

### Evidence (minimum)

Document a bounded backup/restore or incident recovery scenario with explicit data-loss limitations.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-084 — Defend an operating and recovery strategy

**Position:** Step 84 of 96 · Topic `PLT-04` (Kubernetes Operations, Incidents and Recovery) · Level Expert

**Prerequisites:** PRJ-083 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Kubernetes Operations, Incidents and Recovery.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend an operating and recovery strategy**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-084` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend an operating and recovery strategy** and explain what you did.

### Evidence (minimum)

Evaluate day-two operations, upgrade paths, recovery objectives and failure-domain assumptions.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-085 — Identify platform users

**Position:** Step 85 of 96 · Topic `PLT-05` (Platform Product Thinking and Architecture) · Level Beginner

**Prerequisites:** PRJ-084 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Platform Product Thinking and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Identify platform users**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-085` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Identify platform users** and explain what you did.

### Evidence (minimum)

Write user personas and top developer problems for the independent training platform.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-086 — Define a platform service boundary

**Position:** Step 86 of 96 · Topic `PLT-05` (Platform Product Thinking and Architecture) · Level Intermediate

**Prerequisites:** PRJ-085 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Platform Product Thinking and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Define a platform service boundary**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-086` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Define a platform service boundary** and explain what you did.

### Evidence (minimum)

Choose a small platform offering and make ownership and support expectations explicit.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-087 — Create a platform architecture decision

**Position:** Step 87 of 96 · Topic `PLT-05` (Platform Product Thinking and Architecture) · Level Professional

**Prerequisites:** PRJ-086 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Platform Product Thinking and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Create a platform architecture decision**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-087` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Create a platform architecture decision** and explain what you did.

### Evidence (minimum)

Record the platform's product goal, constraints, initial components and measures of success.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-088 — Evaluate platform evolution

**Position:** Step 88 of 96 · Topic `PLT-05` (Platform Product Thinking and Architecture) · Level Expert

**Prerequisites:** PRJ-087 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Platform Product Thinking and Architecture.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate platform evolution**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-088` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate platform evolution** and explain what you did.

### Evidence (minimum)

Critique build-vs-buy, cognitive load, adoption, funding and boundaries with concrete trade-offs.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-089 — Document the developer's first use

**Position:** Step 89 of 96 · Topic `PLT-06` (Golden Paths, Templates and Developer Experience) · Level Beginner

**Prerequisites:** PRJ-088 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Golden Paths, Templates and Developer Experience.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Document the developer's first use**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-089` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Document the developer's first use** and explain what you did.

### Evidence (minimum)

Write a clear entry guide for creating or onboarding a sample service.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-090 — Define reusable starter material

**Position:** Step 90 of 96 · Topic `PLT-06` (Golden Paths, Templates and Developer Experience) · Level Intermediate

**Prerequisites:** PRJ-089 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Golden Paths, Templates and Developer Experience.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Define reusable starter material**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-090` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Define reusable starter material** and explain what you did.

### Evidence (minimum)

Specify a simple template, ownership metadata and a minimal happy-path workflow.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-091 — Demonstrate self-service with guardrails

**Position:** Step 91 of 96 · Topic `PLT-06` (Golden Paths, Templates and Developer Experience) · Level Professional

**Prerequisites:** PRJ-090 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Golden Paths, Templates and Developer Experience.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate self-service with guardrails**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-091` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate self-service with guardrails** and explain what you did.

### Evidence (minimum)

Have a second person follow the guide or perform a documented cold read; record errors and fixes.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-092 — Evaluate self-service effectiveness

**Position:** Step 92 of 96 · Topic `PLT-06` (Golden Paths, Templates and Developer Experience) · Level Expert

**Prerequisites:** PRJ-091 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Golden Paths, Templates and Developer Experience.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Evaluate self-service effectiveness**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-092` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Evaluate self-service effectiveness** and explain what you did.

### Evidence (minimum)

Critique feedback, discoverability, support burden and how to measure cognitive load.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-093 — Describe the complete learning platform

**Position:** Step 93 of 96 · Topic `PLT-07` (Platform Integration, Reliability and Evolution) · Level Beginner

**Prerequisites:** PRJ-092 must be completed.

**Purpose:** Demonstrate beginner-level practical capability in Platform Integration, Reliability and Evolution.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Describe the complete learning platform**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-093` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Describe the complete learning platform** and explain what you did.

### Evidence (minimum)

Produce a clear architecture map connecting code, build, infrastructure, deployment and telemetry.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-094 — Demonstrate the end-to-end developer journey

**Position:** Step 94 of 96 · Topic `PLT-07` (Platform Integration, Reliability and Evolution) · Level Intermediate

**Prerequisites:** PRJ-093 must be completed.

**Purpose:** Demonstrate intermediate-level practical capability in Platform Integration, Reliability and Evolution.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Demonstrate the end-to-end developer journey**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-094` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Demonstrate the end-to-end developer journey** and explain what you did.

### Evidence (minimum)

Follow the written path from a sample change to a reviewed release and observable deployment.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-095 — Present recovery and acceptance evidence

**Position:** Step 95 of 96 · Topic `PLT-07` (Platform Integration, Reliability and Evolution) · Level Professional

**Prerequisites:** PRJ-094 must be completed.

**Purpose:** Demonstrate professional-level practical capability in Platform Integration, Reliability and Evolution.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Present recovery and acceptance evidence**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-095` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Present recovery and acceptance evidence** and explain what you did.

### Evidence (minimum)

Perform or document a bounded failure/recovery scenario and the evidence a second developer would need.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## PRJ-096 — Defend and hand over the platform

**Position:** Step 96 of 96 · Topic `PLT-07` (Platform Integration, Reliability and Evolution) · Level Expert

**Prerequisites:** PRJ-095 must be completed.

**Purpose:** Demonstrate expert-level practical capability in Platform Integration, Reliability and Evolution.

### Work to perform

1. Confirm prerequisites are complete and your working environment is disposable and safe.
2. In your own learner project workspace (not this PDP repo), carry out the work described by: **Defend and hand over the platform**.
3. Keep changes reviewed or documented according to your project's collaboration rules.
4. Capture evidence listed below; note any simulation or limitation honestly.
5. Update your progress record with `PRJ-096` = Completed (or Out of scope only if the whole optional track was excluded in your PDP).

### Expected outcome

You can show a concrete result that matches the intent of **Defend and hand over the platform** and explain what you did.

### Evidence (minimum)

Provide a coherent architecture review, independent-user feedback, trade-off register and next-improvements roadmap.

### Completion criteria

- The evidence above exists and is linkable from your progress record.
- Assumptions, simulations and cost limits are written down.
- No secrets were committed to educational materials.

### Cost and safety

Prefer local/mocked approaches. If using cloud or paid SaaS, use authorised disposable accounts and tear down afterwards.

---

## Final demonstration and teardown

When active steps through PRJ-096 (or your adapted route's final step) are complete, prepare a short demonstration: architecture map, one failure/recovery story, evidence links, and teardown confirmation. Keep claims proportionate to what you actually ran.
