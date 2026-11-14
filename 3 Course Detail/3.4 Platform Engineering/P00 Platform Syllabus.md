# P00 — Platform Engineering Syllabus

**Estimated study time:** 168–210 hours  
**Scope:** Kubernetes workloads and operations, internal developer platforms, DevEx, and a defensible integrated Final Project.

Platform Engineering is the **destination discipline** of this pathway: turn Harbour’s delivery, cloud and optional AI capabilities into a product other developers can use safely without undocumented help from you.

## Discipline objectives

1. Run Harbour as sound Kubernetes workloads with probes, resources and packaging you can defend.  
2. Operate the cluster day-2: RBAC, quotas, policy, recovery and upgrade rehearsals with evidence.  
3. Design a golden path and self-service experience; prove it with an independent trial user.  
4. Integrate prior disciplines into one demonstrable IDP and defend trade-offs from ADRs.

## Modules

| Module | Focus | Estimated study time | Evidence of capability |
| --- | --- | ---: | --- |
| [P01 — Kubernetes and Cloud-Native Fundamentals](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md) | Workloads, probes, networking, packaging, recovery under the workload definition | 48–60 hours | Pod-kill recovery with configured probes; digest-addressed deploy |
| [P02 — Kubernetes Administration and Operations](P02%20Kubernetes%20Administration%20and%20Operations.md) | RBAC, quotas, policy, incidents, rebuild/upgrade drills | 48–60 hours | Day-2 runbook + unprivileged identity denied out-of-scope actions |
| [P03 — Internal Developer Platforms and DevEx](P03%20Internal%20Developer%20Platforms%20and%20DevEx.md) | Platform-as-product, golden path, self-service, usability trial | 32–40 hours | Independent trial user completes create → deliver → status → investigate |
| [P04 — Platform Architecture and Final Project](P04%20Platform%20Architecture%20and%20Final%20Project.md) | Integration, reliability, architecture defence, final demonstration | 40–50 hours | Required Final Project demonstration items + ADR defence |
| **Total** | **4 modules** | **168–210 hours** | **A usable, operable Internal Developer Platform** |

Hour ranges are **planning assumptions**. Completion is demonstrated capability, not calendar time.

## Curriculum progression

1. **P01** — Make Harbour a correct Kubernetes citizen (workloads, probes, packaging).  
2. **P02** — Make the cluster operable under least privilege and recoverable from day-2 faults.  
3. **P03** — Make the platform a product: golden path, docs and independent usability evidence.  
4. **P04** — Integrate and defend the whole pathway as one system.

**Relationship to earlier disciplines:** D06 introduced kind/GitOps lightly; P01–P02 own Kubernetes depth. Cloud owns AWS landing-zone and resilience judgement. AI remains optional. Do not treat a successful Deployment as proof of a usable IDP — that bar lives in P03–P04.

**Early product thinking (before P03):** From the start of the pathway, keep a short note of Harbour’s intended users, their jobs-to-be-done, the first golden path and how you will measure success. Implementation waits for P03; the *why* should not.

## Practical outcomes and Final Project

Track Harbour increments on the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) rows P01–P04. **End of Platform** milestone: another developer follows a golden path and can see health, controls and recovery without undocumented author assistance.

**Exit scenario (programme destination):** independent trial user creates a service from the golden path → reviewed change yields a trusted immutable artifact → self-service deploy to an approved environment → health visible and a failure recovered with documented path → at least one stateful recovery scenario exercised → architecture trade-offs defended from ADRs.

## Completion criteria

- Each module’s Practical Assessment at **Competent** or better.  
- Checklist P01–P04 acceptance criteria met (or honestly `Adapted:`).  
- Independent trial evidence for P03 (not a portal screenshot alone).  
- No real secrets in Git; training vs production boundaries written down.

## Learning content status

| Artifact | Status |
| --- | --- |
| This syllabus + module course-detail | Authored; remediations after audits through `fbd5030` — **awaiting re-review (not signed off)** |
| Textbook chapters | [P01](../../4%20Study%20Materials/4.4%20Platform%20Engineering/P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md)–[P04](../../4%20Study%20Materials/4.4%20Platform%20Engineering/P04%20Platform%20Architecture%20and%20Final%20Project.md) — remediation for policy/promotion equivalence, application-level stateful recovery, GitOps rebuild, status contracts |
| Clean-room lab certification | Separate QA workstream — not implied by authorship |
| Executable Harbour reference + Gate 5 user acceptance | Still required before full programme sign-off |

**Previous discipline:** [AI syllabus](../3.3%20AI%20Engineering/A00%20AI%20Syllabus.md) (optional) or [Cloud syllabus](../3.2%20Cloud%20Engineering/C00%20Cloud%20Syllabus.md) · **Next module:** [P01](P01%20Kubernetes%20and%20Cloud%20Native%20Fundamentals.md)
