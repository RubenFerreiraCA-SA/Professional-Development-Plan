# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-058**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-058](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-03-P — AI EVALUATION, SAFETY AND QUALITY — PROFESSIONAL

### 1. Topic and Scope

**In scope for this level:** Designing evaluation gates and risk controls. You define quality dimensions for the feature, build golden, regression, adversarial and held-out datasets, set per-metric release thresholds with an exception rule, use model graders only with a calibrated rubric and human sampling, track over-refusal alongside under-refusal, and document intended use, limitations, owners and versions.

**Out of scope:** Measurement theory, contamination, red-teaming programmes and regulatory context (`AIE-03-E`), writing the individual deterministic cases (`AIE-03-I`), deployment pipelines and monitoring (`AIE-05`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Define the quality dimensions for `ops-assistant` (correctness, groundedness, refusal accuracy, safety, latency, cost) and a threshold for each.
2. Design the four datasets (golden, regression, adversarial, held-out), say who owns each, how each grows and which are never used for tuning.
3. Write release criteria that state which metrics must pass, how many cases are the minimum, and the exception process, with a rule that failing cases are never deleted to turn the gate green.
4. Specify a model-graded rubric with a rationale-then-score format, randomised pairwise positions and a human agreement sample, and say how uncertainty is reported for a small set.
5. Produce the safety-control table (pre-checks, output validation, tool allow-lists, limits, redaction, human escalation, kill switch) and the feature documentation page as the evidence for **PRJ-059**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-03-P — AI Evaluation, Safety and Quality — Professional](../../../5%20Textbook/Master%20Textbook.md#t-aie-03-p)

Read for: an evaluation strategy with golden, regression, adversarial and held-out sets, careful model-graded evaluation, safety controls beyond evaluation, over- and under-refusal, and documentation and accountability.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Write a release-and-safety criteria document for `ops-assistant`: quality definition, dataset plan, metric thresholds with rationale, exception rule, control table, over-refusal and under-refusal tracking, and the user-facing limitations. Then apply it: give a go or no-go on a candidate whose report shows one adversarial failure and a 2-point groundedness gain on 40 cases.

**Pass criteria:** The go/no-go decision follows the written criteria and is defensible (the adversarial failure blocks release; a 2-point gain on 40 cases is called noise); thresholds are numeric; the document states what the gate does not prove and names an owner.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-059 — Design release and safety criteria** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-059).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
