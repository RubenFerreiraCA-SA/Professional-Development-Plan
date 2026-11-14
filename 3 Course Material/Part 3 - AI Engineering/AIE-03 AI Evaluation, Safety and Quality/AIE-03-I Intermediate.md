# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-057**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-057](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-03-I — AI EVALUATION, SAFETY AND QUALITY — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Constructing and running repeatable example-based evaluations. You combine deterministic assertions, reference comparison, rubric grading and human review appropriately; verify citation provenance; add adversarial and injection fixtures; cover safety categories; force the offline fake model for reproducibility; and gate on freshly produced counts (`failed == 0` and a minimum total) rather than a stale report.

**Out of scope:** Release thresholds per metric and held-out set strategy (`AIE-03-P`), calibration of model graders and statistics (`AIE-03-E`), live-model online metrics (`AIE-05`), any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Write at least eight evaluation cases that use deterministic assertions (refusal flag, empty citations, allowed values, forbidden strings) and run them with a runner that produces a JSON report.
2. Add a citation-provenance check proving the cited identifier was actually retrieved, and sabotage it to watch the suite fail.
3. Create an adversarial fixture with hostile instructions and a fake secret, assert that neither appears in the answer, and state what a mock-based defence cannot prove.
4. Map cases to the five safety categories (scope violation, injection, privacy, harmful content, overreliance) and identify any uncovered category.
5. Re-run the evaluation on current code, assert `failed == 0` and `total >= minimum`, and attach the fresh report as the evidence for **PRJ-058**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-03-I — AI Evaluation, Safety and Quality — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-aie-03-i)

Read for: types of evaluation, citation provenance, adversarial fixtures, safety categories, gating on current code with counts, and regression discipline.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Run an evaluation of at least eight cases against your offline `ops-assistant` using the deterministic fake model (force it even if a real key is set). Include one adversarial fixture and one provenance case. Then deliberately break refusal logic and the provenance check one at a time, show the report failing each time, restore the code and show a clean run.

**Pass criteria:** Reports show `total`, `failed` and per-case problems; both sabotage runs fail for the expected reason; the final run is generated freshly, not copied; the write-up notes that passing covers only the cases listed.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-058 — Run a small evaluation set** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-058).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
