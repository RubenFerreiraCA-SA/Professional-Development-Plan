# Software Engineering — The Master Textbook

This is the **master table of contents** for one unified publication. The educational content lives in the part, chapter and level files linked below. The book remains independent of any programme, project or course.

## How to Read This Book

This book is a single, self-contained reference for modern software delivery and operations. It covers four disciplines — DevOps, cloud, AI engineering and platform engineering — as 24 topics. It stands on its own and does not depend on any other document, programme or project. Every example is neutral and fictional, and every command or configuration appears inside the text.

### Structure

The book has four parts and 24 topics. Topic identifiers are stable and are used for cross-references.

| Part | Discipline | Topics |
| --- | --- | --- |
| I | DevOps Engineering | T-DEV-01 to T-DEV-07 |
| II | Cloud Engineering | T-CLD-01 to T-CLD-05 |
| III | AI Engineering | T-AIE-01 to T-AIE-05 |
| IV | Platform Engineering | T-PLT-01 to T-PLT-07 |

Each topic has four levels. The suffix on the heading says which level you are reading.

| Suffix | Level | What you should be able to do after reading it |
| --- | --- | --- |
| **B** | Beginner Foundations | Name the concepts, explain the mental model and perform a guided first exercise. |
| **I** | Intermediate Practice | Do routine work independently, recognise common patterns and troubleshoot typical failures. |
| **P** | Professional Engineering | Design and operate reliably, with security, quality and decisions you can defend. |
| **E** | Expert Depth | Reason about trade-offs, failure modes, governance and organisational scale, and teach others. |

### Suggested reading paths

- **Complete newcomer:** read all **B** sections of a part in order, doing the guided examples and exercises, before touching any **I** section. Within DevOps, start with Git (T-DEV-01), then containers (T-DEV-02), then CI/CD (T-DEV-03). Within Cloud, Linux (T-CLD-01) and networking (T-CLD-02) unlock later AWS chapters. Within Platform, Kubernetes fundamentals (T-PLT-01) before workloads, security and operations.
- **Working engineer filling a gap:** go straight to the topic, read **I** and **P**, and use **B** only where a term is unfamiliar. Higher levels include short refreshers and cross-links; they do not require reading every earlier level first.
- **Senior engineer or reviewer:** read **P** and **E**. They contain decision tables, failure-mode catalogues, governance cases and mentoring prompts.
- **Cross-topic paths:** Git prepares containers and CI; Linux and networking support cloud identity and resilience; GitOps distinguishes desired state, deployed artifact, runtime state and data recovery; observability ideas recur in Datadog, Kubernetes operations and AI monitoring; AI chapters treat models as software components with evaluation and trust boundaries.
- **Reference use:** Professional sections include decision guides; the [Glossary](Glossary.md) defines recurring terms; [Further Reading](Further%20Reading%20and%20Reference%20Notes.md) points at primary docs for version-sensitive checks.

### Conventions

- Commands assume a POSIX shell (Linux or macOS). Use a disposable environment for anything marked destructive.
- Placeholders appear in angle brackets, for example `<registry>/<image>@sha256:<digest>`.
- The running example is a small fictional web service called `orders-api`, owned by an application team, with a platform team providing infrastructure. Nothing about it is special; swap in your own service.
- "Evidence" means something another person can check: a command output, a rejected change, a log line. A setting that exists is not the same as a control that is enforced. This distinction recurs throughout the book.
- Tool versions and managed-service features change. Where a detail is version-sensitive, the text says so; verify against current vendor documentation before relying on it.

### A note on safety

Use disposable accounts, clusters and repositories for practice. Never put real credentials, production data or confidential code in an exercise. Treat any cloud resource you create as a cost until you have destroyed it.

---

---

## Master table of contents

### Part I — [DevOps Engineering](Part%201%20-%20DevOps%20Engineering/README.md)

#### [T-DEV-01 — Repository Management and Git](Part%201%20-%20DevOps%20Engineering/T-DEV-01%20Repository%20Management%20and%20Git/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-B%20Beginner.md#t-dev-01-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-I%20Intermediate.md#t-dev-01-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-P%20Professional.md#t-dev-01-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-01%20Repository%20Management%20and%20Git/T-DEV-01-E%20Expert.md#t-dev-01-e)

#### [T-DEV-02 — Containers and Docker](Part%201%20-%20DevOps%20Engineering/T-DEV-02%20Containers%20and%20Docker/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-02%20Containers%20and%20Docker/T-DEV-02-B%20Beginner.md#t-dev-02-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-02%20Containers%20and%20Docker/T-DEV-02-I%20Intermediate.md#t-dev-02-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-02%20Containers%20and%20Docker/T-DEV-02-P%20Professional.md#t-dev-02-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-02%20Containers%20and%20Docker/T-DEV-02-E%20Expert.md#t-dev-02-e)

#### [T-DEV-03 — CI/CD and Build Automation](Part%201%20-%20DevOps%20Engineering/T-DEV-03%20CI-CD%20and%20Build%20Automation/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-03%20CI-CD%20and%20Build%20Automation/T-DEV-03-B%20Beginner.md#t-dev-03-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-03%20CI-CD%20and%20Build%20Automation/T-DEV-03-I%20Intermediate.md#t-dev-03-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-03%20CI-CD%20and%20Build%20Automation/T-DEV-03-P%20Professional.md#t-dev-03-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-03%20CI-CD%20and%20Build%20Automation/T-DEV-03-E%20Expert.md#t-dev-03-e)

#### [T-DEV-04 — Infrastructure as Code and Terraform](Part%201%20-%20DevOps%20Engineering/T-DEV-04%20Infrastructure%20as%20Code%20and%20Terraform/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-04%20Infrastructure%20as%20Code%20and%20Terraform/T-DEV-04-B%20Beginner.md#t-dev-04-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-04%20Infrastructure%20as%20Code%20and%20Terraform/T-DEV-04-I%20Intermediate.md#t-dev-04-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-04%20Infrastructure%20as%20Code%20and%20Terraform/T-DEV-04-P%20Professional.md#t-dev-04-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-04%20Infrastructure%20as%20Code%20and%20Terraform/T-DEV-04-E%20Expert.md#t-dev-04-e)

#### [T-DEV-05 — GitOps and Release Operations](Part%201%20-%20DevOps%20Engineering/T-DEV-05%20GitOps%20and%20Release%20Operations/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-05%20GitOps%20and%20Release%20Operations/T-DEV-05-B%20Beginner.md#t-dev-05-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-05%20GitOps%20and%20Release%20Operations/T-DEV-05-I%20Intermediate.md#t-dev-05-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-05%20GitOps%20and%20Release%20Operations/T-DEV-05-P%20Professional.md#t-dev-05-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-05%20GitOps%20and%20Release%20Operations/T-DEV-05-E%20Expert.md#t-dev-05-e)

#### [T-DEV-06 — Observability and Reliability](Part%201%20-%20DevOps%20Engineering/T-DEV-06%20Observability%20and%20Reliability/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-06%20Observability%20and%20Reliability/T-DEV-06-B%20Beginner.md#t-dev-06-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-06%20Observability%20and%20Reliability/T-DEV-06-I%20Intermediate.md#t-dev-06-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-06%20Observability%20and%20Reliability/T-DEV-06-P%20Professional.md#t-dev-06-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-06%20Observability%20and%20Reliability/T-DEV-06-E%20Expert.md#t-dev-06-e)

#### [T-DEV-07 — Datadog Monitoring](Part%201%20-%20DevOps%20Engineering/T-DEV-07%20Datadog%20Monitoring/README.md)

- [Beginner Foundations](Part%201%20-%20DevOps%20Engineering/T-DEV-07%20Datadog%20Monitoring/T-DEV-07-B%20Beginner.md#t-dev-07-b)
- [Intermediate Practice](Part%201%20-%20DevOps%20Engineering/T-DEV-07%20Datadog%20Monitoring/T-DEV-07-I%20Intermediate.md#t-dev-07-i)
- [Professional Engineering](Part%201%20-%20DevOps%20Engineering/T-DEV-07%20Datadog%20Monitoring/T-DEV-07-P%20Professional.md#t-dev-07-p)
- [Expert Depth](Part%201%20-%20DevOps%20Engineering/T-DEV-07%20Datadog%20Monitoring/T-DEV-07-E%20Expert.md#t-dev-07-e)

### Part II — [Cloud Engineering](Part%202%20-%20Cloud%20Engineering/README.md)

#### [T-CLD-01 — Linux Systems and Operations](Part%202%20-%20Cloud%20Engineering/T-CLD-01%20Linux%20Systems%20and%20Operations/README.md)

- [Beginner Foundations](Part%202%20-%20Cloud%20Engineering/T-CLD-01%20Linux%20Systems%20and%20Operations/T-CLD-01-B%20Beginner.md#t-cld-01-b)
- [Intermediate Practice](Part%202%20-%20Cloud%20Engineering/T-CLD-01%20Linux%20Systems%20and%20Operations/T-CLD-01-I%20Intermediate.md#t-cld-01-i)
- [Professional Engineering](Part%202%20-%20Cloud%20Engineering/T-CLD-01%20Linux%20Systems%20and%20Operations/T-CLD-01-P%20Professional.md#t-cld-01-p)
- [Expert Depth](Part%202%20-%20Cloud%20Engineering/T-CLD-01%20Linux%20Systems%20and%20Operations/T-CLD-01-E%20Expert.md#t-cld-01-e)

#### [T-CLD-02 — Networking, DNS and TLS](Part%202%20-%20Cloud%20Engineering/T-CLD-02%20Networking,%20DNS%20and%20TLS/README.md)

- [Beginner Foundations](Part%202%20-%20Cloud%20Engineering/T-CLD-02%20Networking,%20DNS%20and%20TLS/T-CLD-02-B%20Beginner.md#t-cld-02-b)
- [Intermediate Practice](Part%202%20-%20Cloud%20Engineering/T-CLD-02%20Networking,%20DNS%20and%20TLS/T-CLD-02-I%20Intermediate.md#t-cld-02-i)
- [Professional Engineering](Part%202%20-%20Cloud%20Engineering/T-CLD-02%20Networking,%20DNS%20and%20TLS/T-CLD-02-P%20Professional.md#t-cld-02-p)
- [Expert Depth](Part%202%20-%20Cloud%20Engineering/T-CLD-02%20Networking,%20DNS%20and%20TLS/T-CLD-02-E%20Expert.md#t-cld-02-e)

#### [T-CLD-03 — Cloud Foundations and Governance](Part%202%20-%20Cloud%20Engineering/T-CLD-03%20Cloud%20Foundations%20and%20Governance/README.md)

- [Beginner Foundations](Part%202%20-%20Cloud%20Engineering/T-CLD-03%20Cloud%20Foundations%20and%20Governance/T-CLD-03-B%20Beginner.md#t-cld-03-b)
- [Intermediate Practice](Part%202%20-%20Cloud%20Engineering/T-CLD-03%20Cloud%20Foundations%20and%20Governance/T-CLD-03-I%20Intermediate.md#t-cld-03-i)
- [Professional Engineering](Part%202%20-%20Cloud%20Engineering/T-CLD-03%20Cloud%20Foundations%20and%20Governance/T-CLD-03-P%20Professional.md#t-cld-03-p)
- [Expert Depth](Part%202%20-%20Cloud%20Engineering/T-CLD-03%20Cloud%20Foundations%20and%20Governance/T-CLD-03-E%20Expert.md#t-cld-03-e)

#### [T-CLD-04 — AWS Identity, Networking and Cost Controls](Part%202%20-%20Cloud%20Engineering/T-CLD-04%20AWS%20Identity,%20Networking%20and%20Cost%20Controls/README.md)

- [Beginner Foundations](Part%202%20-%20Cloud%20Engineering/T-CLD-04%20AWS%20Identity,%20Networking%20and%20Cost%20Controls/T-CLD-04-B%20Beginner.md#t-cld-04-b)
- [Intermediate Practice](Part%202%20-%20Cloud%20Engineering/T-CLD-04%20AWS%20Identity,%20Networking%20and%20Cost%20Controls/T-CLD-04-I%20Intermediate.md#t-cld-04-i)
- [Professional Engineering](Part%202%20-%20Cloud%20Engineering/T-CLD-04%20AWS%20Identity,%20Networking%20and%20Cost%20Controls/T-CLD-04-P%20Professional.md#t-cld-04-p)
- [Expert Depth](Part%202%20-%20Cloud%20Engineering/T-CLD-04%20AWS%20Identity,%20Networking%20and%20Cost%20Controls/T-CLD-04-E%20Expert.md#t-cld-04-e)

#### [T-CLD-05 — AWS Infrastructure, Resilience and Architecture](Part%202%20-%20Cloud%20Engineering/T-CLD-05%20AWS%20Infrastructure,%20Resilience%20and%20Architecture/README.md)

- [Beginner Foundations](Part%202%20-%20Cloud%20Engineering/T-CLD-05%20AWS%20Infrastructure,%20Resilience%20and%20Architecture/T-CLD-05-B%20Beginner.md#t-cld-05-b)
- [Intermediate Practice](Part%202%20-%20Cloud%20Engineering/T-CLD-05%20AWS%20Infrastructure,%20Resilience%20and%20Architecture/T-CLD-05-I%20Intermediate.md#t-cld-05-i)
- [Professional Engineering](Part%202%20-%20Cloud%20Engineering/T-CLD-05%20AWS%20Infrastructure,%20Resilience%20and%20Architecture/T-CLD-05-P%20Professional.md#t-cld-05-p)
- [Expert Depth](Part%202%20-%20Cloud%20Engineering/T-CLD-05%20AWS%20Infrastructure,%20Resilience%20and%20Architecture/T-CLD-05-E%20Expert.md#t-cld-05-e)

### Part III — [AI Engineering](Part%203%20-%20AI%20Engineering/README.md)

#### [T-AIE-01 — LLM Fundamentals and Prompting](Part%203%20-%20AI%20Engineering/T-AIE-01%20LLM%20Fundamentals%20and%20Prompting/README.md)

- [Beginner Foundations](Part%203%20-%20AI%20Engineering/T-AIE-01%20LLM%20Fundamentals%20and%20Prompting/T-AIE-01-B%20Beginner.md#t-aie-01-b)
- [Intermediate Practice](Part%203%20-%20AI%20Engineering/T-AIE-01%20LLM%20Fundamentals%20and%20Prompting/T-AIE-01-I%20Intermediate.md#t-aie-01-i)
- [Professional Engineering](Part%203%20-%20AI%20Engineering/T-AIE-01%20LLM%20Fundamentals%20and%20Prompting/T-AIE-01-P%20Professional.md#t-aie-01-p)
- [Expert Depth](Part%203%20-%20AI%20Engineering/T-AIE-01%20LLM%20Fundamentals%20and%20Prompting/T-AIE-01-E%20Expert.md#t-aie-01-e)

#### [T-AIE-02 — Grounding, Retrieval and Knowledge Use](Part%203%20-%20AI%20Engineering/T-AIE-02%20Grounding,%20Retrieval%20and%20Knowledge%20Use/README.md)

- [Beginner Foundations](Part%203%20-%20AI%20Engineering/T-AIE-02%20Grounding,%20Retrieval%20and%20Knowledge%20Use/T-AIE-02-B%20Beginner.md#t-aie-02-b)
- [Intermediate Practice](Part%203%20-%20AI%20Engineering/T-AIE-02%20Grounding,%20Retrieval%20and%20Knowledge%20Use/T-AIE-02-I%20Intermediate.md#t-aie-02-i)
- [Professional Engineering](Part%203%20-%20AI%20Engineering/T-AIE-02%20Grounding,%20Retrieval%20and%20Knowledge%20Use/T-AIE-02-P%20Professional.md#t-aie-02-p)
- [Expert Depth](Part%203%20-%20AI%20Engineering/T-AIE-02%20Grounding,%20Retrieval%20and%20Knowledge%20Use/T-AIE-02-E%20Expert.md#t-aie-02-e)

#### [T-AIE-03 — AI Evaluation, Safety and Quality](Part%203%20-%20AI%20Engineering/T-AIE-03%20AI%20Evaluation,%20Safety%20and%20Quality/README.md)

- [Beginner Foundations](Part%203%20-%20AI%20Engineering/T-AIE-03%20AI%20Evaluation,%20Safety%20and%20Quality/T-AIE-03-B%20Beginner.md#t-aie-03-b)
- [Intermediate Practice](Part%203%20-%20AI%20Engineering/T-AIE-03%20AI%20Evaluation,%20Safety%20and%20Quality/T-AIE-03-I%20Intermediate.md#t-aie-03-i)
- [Professional Engineering](Part%203%20-%20AI%20Engineering/T-AIE-03%20AI%20Evaluation,%20Safety%20and%20Quality/T-AIE-03-P%20Professional.md#t-aie-03-p)
- [Expert Depth](Part%203%20-%20AI%20Engineering/T-AIE-03%20AI%20Evaluation,%20Safety%20and%20Quality/T-AIE-03-E%20Expert.md#t-aie-03-e)

#### [T-AIE-04 — Agents, Tools and Orchestration](Part%203%20-%20AI%20Engineering/T-AIE-04%20Agents,%20Tools%20and%20Orchestration/README.md)

- [Beginner Foundations](Part%203%20-%20AI%20Engineering/T-AIE-04%20Agents,%20Tools%20and%20Orchestration/T-AIE-04-B%20Beginner.md#t-aie-04-b)
- [Intermediate Practice](Part%203%20-%20AI%20Engineering/T-AIE-04%20Agents,%20Tools%20and%20Orchestration/T-AIE-04-I%20Intermediate.md#t-aie-04-i)
- [Professional Engineering](Part%203%20-%20AI%20Engineering/T-AIE-04%20Agents,%20Tools%20and%20Orchestration/T-AIE-04-P%20Professional.md#t-aie-04-p)
- [Expert Depth](Part%203%20-%20AI%20Engineering/T-AIE-04%20Agents,%20Tools%20and%20Orchestration/T-AIE-04-E%20Expert.md#t-aie-04-e)

#### [T-AIE-05 — LLMOps, Deployment and Monitoring](Part%203%20-%20AI%20Engineering/T-AIE-05%20LLMOps,%20Deployment%20and%20Monitoring/README.md)

- [Beginner Foundations](Part%203%20-%20AI%20Engineering/T-AIE-05%20LLMOps,%20Deployment%20and%20Monitoring/T-AIE-05-B%20Beginner.md#t-aie-05-b)
- [Intermediate Practice](Part%203%20-%20AI%20Engineering/T-AIE-05%20LLMOps,%20Deployment%20and%20Monitoring/T-AIE-05-I%20Intermediate.md#t-aie-05-i)
- [Professional Engineering](Part%203%20-%20AI%20Engineering/T-AIE-05%20LLMOps,%20Deployment%20and%20Monitoring/T-AIE-05-P%20Professional.md#t-aie-05-p)
- [Expert Depth](Part%203%20-%20AI%20Engineering/T-AIE-05%20LLMOps,%20Deployment%20and%20Monitoring/T-AIE-05-E%20Expert.md#t-aie-05-e)

### Part IV — [Platform Engineering](Part%204%20-%20Platform%20Engineering/README.md)

#### [T-PLT-01 — Kubernetes Fundamentals and Architecture](Part%204%20-%20Platform%20Engineering/T-PLT-01%20Kubernetes%20Fundamentals%20and%20Architecture/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-01%20Kubernetes%20Fundamentals%20and%20Architecture/T-PLT-01-B%20Beginner.md#t-plt-01-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-01%20Kubernetes%20Fundamentals%20and%20Architecture/T-PLT-01-I%20Intermediate.md#t-plt-01-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-01%20Kubernetes%20Fundamentals%20and%20Architecture/T-PLT-01-P%20Professional.md#t-plt-01-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-01%20Kubernetes%20Fundamentals%20and%20Architecture/T-PLT-01-E%20Expert.md#t-plt-01-e)

#### [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](Part%204%20-%20Platform%20Engineering/T-PLT-02%20Kubernetes%20Workloads,%20Configuration%20and%20Packaging/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-02%20Kubernetes%20Workloads,%20Configuration%20and%20Packaging/T-PLT-02-B%20Beginner.md#t-plt-02-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-02%20Kubernetes%20Workloads,%20Configuration%20and%20Packaging/T-PLT-02-I%20Intermediate.md#t-plt-02-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-02%20Kubernetes%20Workloads,%20Configuration%20and%20Packaging/T-PLT-02-P%20Professional.md#t-plt-02-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-02%20Kubernetes%20Workloads,%20Configuration%20and%20Packaging/T-PLT-02-E%20Expert.md#t-plt-02-e)

#### [T-PLT-03 — Kubernetes Security and Policy](Part%204%20-%20Platform%20Engineering/T-PLT-03%20Kubernetes%20Security%20and%20Policy/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-03%20Kubernetes%20Security%20and%20Policy/T-PLT-03-B%20Beginner.md#t-plt-03-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-03%20Kubernetes%20Security%20and%20Policy/T-PLT-03-I%20Intermediate.md#t-plt-03-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-03%20Kubernetes%20Security%20and%20Policy/T-PLT-03-P%20Professional.md#t-plt-03-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-03%20Kubernetes%20Security%20and%20Policy/T-PLT-03-E%20Expert.md#t-plt-03-e)

#### [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](Part%204%20-%20Platform%20Engineering/T-PLT-04%20Kubernetes%20Operations,%20Incidents%20and%20Recovery/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-04%20Kubernetes%20Operations,%20Incidents%20and%20Recovery/T-PLT-04-B%20Beginner.md#t-plt-04-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-04%20Kubernetes%20Operations,%20Incidents%20and%20Recovery/T-PLT-04-I%20Intermediate.md#t-plt-04-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-04%20Kubernetes%20Operations,%20Incidents%20and%20Recovery/T-PLT-04-P%20Professional.md#t-plt-04-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-04%20Kubernetes%20Operations,%20Incidents%20and%20Recovery/T-PLT-04-E%20Expert.md#t-plt-04-e)

#### [T-PLT-05 — Platform Product Thinking and Architecture](Part%204%20-%20Platform%20Engineering/T-PLT-05%20Platform%20Product%20Thinking%20and%20Architecture/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-05%20Platform%20Product%20Thinking%20and%20Architecture/T-PLT-05-B%20Beginner.md#t-plt-05-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-05%20Platform%20Product%20Thinking%20and%20Architecture/T-PLT-05-I%20Intermediate.md#t-plt-05-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-05%20Platform%20Product%20Thinking%20and%20Architecture/T-PLT-05-P%20Professional.md#t-plt-05-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-05%20Platform%20Product%20Thinking%20and%20Architecture/T-PLT-05-E%20Expert.md#t-plt-05-e)

#### [T-PLT-06 — Golden Paths, Templates and Developer Experience](Part%204%20-%20Platform%20Engineering/T-PLT-06%20Golden%20Paths,%20Templates%20and%20Developer%20Experience/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-06%20Golden%20Paths,%20Templates%20and%20Developer%20Experience/T-PLT-06-B%20Beginner.md#t-plt-06-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-06%20Golden%20Paths,%20Templates%20and%20Developer%20Experience/T-PLT-06-I%20Intermediate.md#t-plt-06-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-06%20Golden%20Paths,%20Templates%20and%20Developer%20Experience/T-PLT-06-P%20Professional.md#t-plt-06-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-06%20Golden%20Paths,%20Templates%20and%20Developer%20Experience/T-PLT-06-E%20Expert.md#t-plt-06-e)

#### [T-PLT-07 — Platform Integration, Reliability and Evolution](Part%204%20-%20Platform%20Engineering/T-PLT-07%20Platform%20Integration,%20Reliability%20and%20Evolution/README.md)

- [Beginner Foundations](Part%204%20-%20Platform%20Engineering/T-PLT-07%20Platform%20Integration,%20Reliability%20and%20Evolution/T-PLT-07-B%20Beginner.md#t-plt-07-b)
- [Intermediate Practice](Part%204%20-%20Platform%20Engineering/T-PLT-07%20Platform%20Integration,%20Reliability%20and%20Evolution/T-PLT-07-I%20Intermediate.md#t-plt-07-i)
- [Professional Engineering](Part%204%20-%20Platform%20Engineering/T-PLT-07%20Platform%20Integration,%20Reliability%20and%20Evolution/T-PLT-07-P%20Professional.md#t-plt-07-p)
- [Expert Depth](Part%204%20-%20Platform%20Engineering/T-PLT-07%20Platform%20Integration,%20Reliability%20and%20Evolution/T-PLT-07-E%20Expert.md#t-plt-07-e)

### Reference

- [Glossary](Glossary.md)
- [Further Reading and Reference Notes](Further%20Reading%20and%20Reference%20Notes.md)
