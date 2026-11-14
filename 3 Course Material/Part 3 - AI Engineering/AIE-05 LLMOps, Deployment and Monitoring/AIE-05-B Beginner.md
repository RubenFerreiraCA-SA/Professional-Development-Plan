# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-064**.

Each required step must be recorded **Completed** in your progress record. A step may be recorded **Out of scope** only when your personal PDP excludes an entire optional track that contains it (for example the Datadog track); individual steps may not be skipped. The AI track (PRJ-049–PRJ-068) is itself optional as a whole: if your PDP excludes it, do not start this module. If any required step is neither Completed nor covered by a whole-track exclusion, **STOP**, open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here.

Exact tasks: see [PRJ-001 through PRJ-064](../../../4%20Project%20Document/Project.md#prj-001).

## MODULE AIE-05-B — LLMOPS, DEPLOYMENT AND MONITORING — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Describing model serving, versioning and AI operations. You explain LLMOps as operating a feature whose behaviour depends on prompt, tool policy and model identifier; record a version bundle (bundle, prompt, tool policy, model id, git sha); distinguish recording a version from deploying it; expose AI state in a health response; and use one flag to disable the assistant without taking down the core service.

**Out of scope:** Serving behind an HTTP API, limits and telemetry (`AIE-05-I`), release gating and observability stack (`AIE-05-P`), gateways, self-hosting and cost engineering (`AIE-05-E`), and any implementation steps that belong only in the Project Document.

### 2. Learning Objectives

1. Explain how operating an LLM feature differs from running a training pipeline, and why "fine-tune a model" is not the first step.
2. Create a version file recording bundle, prompt, tool policy and model identifiers plus a commit or image digest.
3. Explain why changing a version file does not roll back code, and what second identity must be pinned.
4. Design a health response that reports `enabled`, bundle version and model id while the core service stays healthy when the AI is off.
5. Flip the disable flag, restart, confirm the endpoint and refusal message, and keep the before-and-after output as evidence for **PRJ-065**.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-AIE-05-B — LLMOps, Deployment and Monitoring — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-aie-05-b)

Read for: what LLMOps is for a feature, what to version, pinning metadata and artefact identity, the health endpoint reporting AI state and the single-flag stop button.

Optional enrichment: related sections in the same topic chapter, clearly marked optional in the textbook.

### 4. Knowledge Assessment

**Task:** Create `ai-version.txt` (or an equivalent plain version file) for the `ops-assistant` bundle and a health response that reports it. Disable the feature using one flag, show the health endpoint reporting `enabled: false`, show a request refused with a clear message, and show the core service health unaffected. Write three sentences on what the file does not guarantee.

**Pass criteria:** The version record includes an artefact identity, not just names; the disabled state is visible in health and in a refused request; core health stays ok; no real model keys appear in the file.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-065 — Version the AI configuration** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-065).

Evidence to record: follow the completion criteria on that project step. Mark the step **Completed** in your progress record before opening the next module.
