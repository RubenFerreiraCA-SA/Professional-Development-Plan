# T-AIE-03-E — Expert Depth

*Chapter: [T-AIE-03 — AI Evaluation, Safety and Quality](README.md) · Part 3 — AI Engineering*

<a id="t-aie-03-e"></a>
#### T-AIE-03-E — Expert Depth

**Measurement theory for AI evaluation.** Treat evaluation as an experiment. Define the population of inputs you care about; sample it representatively; estimate metrics with confidence intervals; test changes with paired comparisons on the same inputs; correct for multiple comparisons when you try many variants; and watch for overfitting to the evaluation set through repeated tuning. A benchmark that appears in training data inflates scores (contamination). Keep private held-out data.

**Limits of automated judging.** Model graders have position, verbosity and self-preference biases and can be fooled by confident wrong answers. Techniques: pairwise rather than absolute scoring, multiple judges with disagreement analysis, reference-guided judging, decomposing claims for verification against sources, and periodic human audits. For high-stakes cases, human review remains the standard.

**Red-teaming programme.** Structured adversarial testing by people who did not build the feature: taxonomy of attacks (direct and indirect prompt injection, jailbreaks, data exfiltration, tool abuse, denial of wallet, multi-turn manipulation), a tracker with severity, reproduction steps and fixes, and re-testing. Automate known attacks as regression cases; keep novel ones human-driven. Define what "acceptable residual risk" means with the business.

**Safety architecture.** Layered, independent controls so one failure is not catastrophic: capability limits (least privilege), isolation of untrusted content, input and output classifiers, policy engines outside the model, monitoring and anomaly detection, rate limits, human approval for impactful actions, audit trails and an incident process. Assume each layer fails sometimes and design for graceful failure.

**Drift and ongoing assurance.** Quality changes without code changes: provider model updates, corpus changes, user behaviour shifts. Run scheduled evaluations against production-like inputs, monitor online proxies (refusal rate, citation rate, escalation rate, user corrections), alert on shifts and keep canary cases that must always pass. Maintain a rollback for prompt, model and corpus versions.

**Regulatory and ethical context.** Depending on jurisdiction and use, requirements on transparency, human oversight, data protection, record keeping and risk classification may apply. Build the documentation, logging and review processes early; retrofitting is expensive. Consider fairness: evaluate across user groups and languages, and avoid using the model for decisions that need accountability without human review.

**Failure catalogue**

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Goodhart effect | Optimising to the metric degrades real quality | Multiple metrics, human audits, refresh data |
| Eval contamination | Test cases leak into prompts or training | Private held-out sets |
| Silent model update | Provider changes behaviour | Pinned versions, scheduled regression runs |
| Judge collapse | Grader rewards style over substance | Calibrated rubrics, human checks |
| False reassurance | Passing a narrow suite is read as "safe" | State scope of claims, widen coverage |

**Auditing an evaluation suite for blind spots.** Build a coverage matrix and look for empty cells.

| Dimension | Values to check | Typical gap | Risk if missing |
| --- | --- | --- | --- |
| Behaviour | Answer, refuse, abstain, escalate | No "escalate" cases | Wrong action in the highest-impact cases |
| Population | Languages, expertise levels, accessibility needs | English only | Quiet failure for whole user groups |
| Input shape | Long inputs, empty input, malformed text, pasted logs | Only tidy one-line questions | Failures at production inputs |
| Conversation | Multi-turn manipulation, topic switching, repeated pressure | Single-turn only | Safeguards erode over a conversation |
| Evidence | Missing, contradictory, stale sources | Always-clean sources | Overconfident answers |
| Adversarial | Injection in documents, tool abuse, secrets requests | A few jailbreak strings | Real attacks unexercised |

Rank empty cells by impact × likelihood in production, add cases for the top few, and write down the cells you chose not to cover. That statement bounds your claim.

**Is 3 points on 80 cases real? Worked example.** Prompt B passes 66 of 80 cases (82.5%), prompt A passes 63 (78.75%): +3.75 points. For one proportion near 0.8, the standard error with n = 80 is √(0.8 × 0.2 / 80) ≈ 0.045, so a 95% interval is about ±8.8 points. The intervals overlap heavily, so the data cannot distinguish the prompts. The comparison is better paired, because the same cases are used:

| | B passes | B fails |
| --- | --- | --- |
| **A passes** | 58 | 5 |
| **A fails** | 8 | 9 |

Only the discordant cases matter: B won 8, A won 5. A sign test on 13 discordant cases gives a p-value near 0.58: no evidence of a difference. To detect a true +3 point improvement with paired data, assuming roughly 10% of cases are discordant in either direction, you need on the order of a thousand or more cases; if the disagreements are fewer, fewer cases suffice. The practical rules: run each case several times if outputs vary, use paired analysis, set the rejection rule in advance, and treat a result within the noise as "no change", then choose on cost, latency or risk.

**Grader biases and a calibration plan.**

| Bias | Symptom | Check |
| --- | --- | --- |
| Verbosity | Longer answers get higher scores | Correlate score with length on a fixed-quality sample; length-control the rubric |
| Position | The first (or second) option in a pair wins more often | Swap order; require agreement across both orders |
| Self-preference | Judge prefers outputs from its own model family | Use a judge from a different family; compare with human labels |
| Confident-wrong | Fluent false answers score well | Reference-guided or claim-by-claim verification |

```text
Calibration protocol:
1. Humans label 150 cases (two labellers; compute agreement, e.g. Cohen's kappa; adjudicate disagreements).
2. Run the judge; compute agreement with the adjudicated labels per criterion.
3. Accept the judge for a criterion only if agreement meets a pre-set bar (e.g. >= 85%) and no bias test fails.
4. Audit 5% of judged results by humans every run; drop to manual review when agreement falls.
```

**Red-team tracker: minimum record.**

| Field | Example |
| --- | --- |
| ID, severity | RT-014, High (data exfiltration via crafted document) |
| Category | Indirect prompt injection |
| Reproduction | Exact input, document, model/prompt/bundle version, steps |
| Impact | The assistant sent retrieved text to an attacker-controlled URL |
| Fix | Output URL allow-list; document tagged as untrusted; tool call blocked |
| Re-test | Automated regression case RT-014 added; passes on version 1.4.2 |
| Status/owner/date | Closed, <owner>, date |

Automate attacks that are reproducible and cheap to detect (known jailbreak strings, injection templates, secret-pattern output), and keep creative, multi-step or social attacks with humans, rotating testers so the team does not share blind spots. Agree with the business what residual risk is acceptable, per severity, in writing.

**Designing the "escalate to a human" evaluation.** The correct answer is sometimes "I cannot decide this; here is who to ask". Include cases where escalation is correct (ambiguous policy, high-impact request) and cases where it is wrong (a simple documented question). Measure both error types: missed escalation (dangerous) and unnecessary escalation (cost and user annoyance). Report the confusion matrix, not one accuracy figure, and set separate thresholds.

**Drift monitoring plan.**

| Monitor | Cadence | Trigger |
| --- | --- | --- |
| Canary suite (20 stable, must-pass cases) | Every deploy and daily | Any failure pages the owner |
| Full evaluation on fresh production samples | Weekly | Drop > 3 points on any criterion |
| Online proxies: refusal rate, citation rate, escalation rate, schema failures | Continuous | Shift > 2 standard deviations from the 28-day baseline |
| Corpus change diff | On each index update | Large deletions or additions trigger a re-run |
| Provider notices | On subscription | Re-evaluate before the deprecation date |

**Incident process for a harmful output, end to end.** Detect (user report or monitor); triage severity within an hour; contain (disable the feature or the specific capability); preserve evidence (inputs, retrieved context, version bundle, logs, with restricted access); find the cause and reproduce it; fix and add a regression case; communicate to affected users where required; re-enable behind canary; hold a blameless review and update the red-team tracker and evaluation suite.

**Mentoring prompts.** Design an evaluation for an assistant whose correct answer is sometimes "escalate to a human". How would you estimate whether a 3-point improvement on 80 cases is real? What would an incident process for a harmful output look like end to end?

---
