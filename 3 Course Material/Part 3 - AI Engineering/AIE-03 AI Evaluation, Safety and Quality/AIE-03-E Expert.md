# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-059**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-059](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-03-E — AI EVALUATION, SAFETY AND QUALITY — EXPERT

### 1. Topic and Scope

**In scope for this level:** Critiquing measurement validity, robustness and governance. You treat evaluation as an experiment with sampling, confidence intervals and paired comparisons, recognise contamination and Goodhart effects, understand judge biases (position, verbosity, self-preference), plan a red-team programme, design layered safety controls and ongoing drift assurance, and consider regulatory and fairness context.

**Out of scope:** Writing basic cases and runners (`AIE-03-B`, `AIE-03-I`), setting a first release gate (`AIE-03-P`), agent autonomy levels (`AIE-04-E`), gateway and cost operations (`AIE-05-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Audit an evaluation suite for blind spots (missing populations, languages, long inputs, multi-turn manipulation, unanswerable cases) and rank them by risk.
2. Estimate whether a 3-point improvement on 80 cases is real using a confidence interval or paired comparison, and state the sample size you would need.
3. Identify the biases of a model grader and design a calibration plan using pairwise comparison, multiple judges and human audit.
4. Draft a red-team taxonomy with severity, reproduction steps, fix and re-test tracking, separating attacks to automate from those left to humans.
5. Specify the drift monitors and canary cases that would reveal silent provider, corpus or behaviour change, and record the audit findings as **PRJ-060**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-03-E — AI Evaluation, Safety and Quality — Expert](../../../5%20Textbook/Master%20Textbook.md#t-aie-03-e)

Read for: measurement theory for AI evaluation, limits of automated judging, red-teaming programmes, layered safety architecture, drift and the failure catalogue.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Audit the evaluation set and report from your `ops-assistant` work (or the sample in the textbook). Deliver a blind-spot register (gap, why it matters, how to close, owner), a statistical note answering the "3 points on 80 cases" question, and an incident process for a harmful output from detection to new regression case. Answer the textbook mentoring prompt on evaluating an assistant whose correct answer is sometimes "escalate to a human".

**Pass criteria:** At least six distinct blind spots are justified; the statistical note names uncertainty and does not claim significance without support; the incident process covers disable, preserve evidence, add case, review and re-enable; claims are limited to what the evidence supports.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-060 — Audit evaluation blind spots** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-060).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
