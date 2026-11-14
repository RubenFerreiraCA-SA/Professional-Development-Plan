# DevOps Exit Assessment — integrated Harbour check

*Optional but recommended after D01–D07 (and D08 if completing the full curriculum).*

Chapter Practical Assessments prove **individual** capabilities. This exit assessment asks a **second engineer** (or you, after a cooling-off period) to exercise the **accumulated** Harbour path: controlled release, failure investigation and recovery using only the project’s documentation and telemetry.

It does **not** replace chapter assessments or the [Final Project Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md). It strengthens the “End of DevOps” milestone.

## Baseline

| | |
| --- | --- |
| **Textbook baseline (documentation freeze)** | Git commit `69f54e0d2dc81d414c3f2c9bd47138015a8ba9ec` (2026-11-14) — eight chapters authored; see [DevOps textbook README](README.md) |
| **Lab reproducibility** | Not claimed by this freeze — run a clean-room Harbour build against the textbook and file defects against both docs and implementation |

## Scenario

A colleague must:

1. Accept or land a small, reviewed change to Harbour.  
2. Obtain a **trusted** image digest (CI/release path from D04).  
3. Deploy or promote that digest through the project’s declared path (GitOps desired state and/or the runtime you documented — ECS **or** kind; state which).  
4. Confirm the running artifact matches the digest.  
5. Investigate a planted or natural failure using telemetry and runbooks (D07; D08 if in scope).  
6. Recover to a known-good state with auditable history (Git revert / digest pin — not undocumented live edits).  
7. Distinguish **application failure** from **missing telemetry** if both drills are available.

## Evidence required

| ☐ | Evidence |
| --- | --- |
| ☐ | Commit SHA of the change and of any revert |
| ☐ | Image digest promoted / running |
| ☐ | Link or path to desired-state / deploy config used |
| ☐ | Investigation notes: symptom, ≥2 hypotheses, contradicting evidence, action |
| ☐ | Before/after health or SLI check |
| ☐ | (If D08) App fault vs Agent/collector blind-spot distinguished |

## Pass standard

Another engineer can repeat the release and recovery from the Harbour docs **without** pair-programming with the author. Screenshots without digests, SHAs and runbook steps do not pass.

## Relationship to Final Project

| Goal | Use |
| --- | --- |
| Full DevOps curriculum | Chapter assessments + this exit assessment + D08 (or documented curriculum deferral) |
| Final Project IDP acceptance | [Checklist](../../1%20Foundational%20Documents/1.5%20Final%20Project%20Checklist.md) End of DevOps (Final Project) rows; D08 may be `N/A` with equivalent ops proof |

**Syllabus:** [D00 — DevOps Syllabus](../../3%20Course%20Detail/3.1%20DevOps/D00%20DevOps%20Syllabus.md) · **Textbook:** [README](README.md)
