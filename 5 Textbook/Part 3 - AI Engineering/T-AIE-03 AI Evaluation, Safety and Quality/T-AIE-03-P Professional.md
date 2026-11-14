# T-AIE-03-P — Professional Engineering

*Chapter: [T-AIE-03 — AI Evaluation, Safety and Quality](README.md) · Part 3 — AI Engineering*

<a id="t-aie-03-p"></a>
#### T-AIE-03-P — Professional Engineering

**An evaluation strategy.**

1. *Define quality* for the feature: correctness, groundedness, completeness, refusal accuracy, safety, tone, latency, cost.
2. *Build datasets:* golden set (curated, small, stable), regression set (past failures), adversarial set (attacks), and a held-out set not used for tuning. Sample from real traffic with privacy controls.
3. *Automate:* deterministic checks on every pull request; broader and model-graded evaluation nightly or before release.
4. *Gate releases* on thresholds per metric, with explicit rules for exceptions.
5. *Close the loop:* feedback and incidents create cases.

**Model-graded evaluation done carefully.** Use a rubric with clear criteria, ask for a brief rationale then a score, randomise positions in pairwise comparisons, use a different model family than the one being judged where possible, and measure agreement with human labels on a sample. Report uncertainty; with small sets, differences of a few points are noise.

**Safety controls beyond evaluation**

| Control | Purpose |
| --- | --- |
| Input pre-checks and classification | Block or route out-of-scope or abusive input |
| Output validation and filtering | Enforce schema and policy before display |
| Tool allow-lists and approvals | Limit actions (see T-AIE-04) |
| Rate and cost limits | Contain abuse and runaway cost |
| Redaction of secrets and personal data | Reduce leakage in prompts, logs and answers |
| Human escalation | A route out when confidence is low or stakes are high |
| Kill switch | One action to disable the feature (see T-AIE-05) |

**Quality dimensions and trade-offs.** Safety, helpfulness and cost pull against each other. An assistant that refuses too much is useless; one that never refuses is dangerous. Track *over-refusal* (valid requests refused) alongside *under-refusal*.

**Documentation and accountability.** Maintain for each feature: intended use, scope, known limitations, evaluation results and dates, data sources, model and prompt versions, owner and escalation contact. Present limitations to users in the interface.

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Prove a change is safe | Evaluation on current code, thresholds | Spot checks |
| Catch regressions | Case from every incident | Deleting failing cases |
| Test safety | Adversarial and injection sets | Only happy paths |
| Use model graders | Rubric, calibration, human sampling | Treating scores as truth |
| Report honestly | State what a pass does not prove | "The model usually refuses" |
