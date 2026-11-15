# T-AIE-03-E — Expert Depth

*Chapter: [T-AIE-03 — AI Evaluation, Safety and Quality](README.md) · Part 3 — AI Engineering*

<a id="t-aie-03-e"></a>
#### T-AIE-03-E — Expert Depth

## Why this matters

Beginner and Intermediate practice give you a suite, a gate and honest reporting. Expert practice asks whether the *measurement itself* is sound. A suite can be executed flawlessly and still answer the wrong question: it may measure something adjacent to what matters, it may have leaked into the thing it measures, its uncertainty may be larger than anyone reports, and its thresholds may encode no decision about harm. Experts also face the organisational side: who decides what residual risk is acceptable, on what evidence, and how that decision is recorded and revisited.

This section assumes the preceding levels and some comfort with proportions, confidence intervals and confusion matrices. It uses the fictional **runbook assistant** throughout. All numbers in worked examples are illustrations chosen to demonstrate a calculation; none describes a real system, and the case catalogue describes constructed scenarios, not real events. Where jurisdiction-specific legal requirements are discussed, they are described only in general terms: seek qualified advice for your own situation.

## Evaluation as an experiment

Treat evaluation as an experiment about a population of inputs.

1. **Define the population** you care about: which users, what kinds of questions, in which languages, with which conversation shapes.
2. **Sample it representatively**, or state plainly how your sample differs.
3. **Estimate metrics with intervals**, not bare points.
4. **Compare changes on the same inputs** (paired comparison), because it removes between-case variation.
5. **Correct for multiple comparisons** when you try many variants.
6. **Guard against overfitting to the evaluation set** through repeated tuning.
7. **Pre-register the decision rule**: what result will make you ship, and what will not, written before the run.

The remaining sections develop the points where this goes wrong in practice.

## Measurement validity

A metric is only useful if it measures what you claim. Four questions, borrowed from measurement theory, expose the common gaps.

| Question | Meaning | Example failure for the runbook assistant |
| --- | --- | --- |
| **Content validity** | Do the cases cover the construct you care about? | "Quality" is claimed, but cases cover only questions the authors found easy to write |
| **Construct validity** | Does the score reflect the property, not a proxy? | A keyword-overlap score is read as "correctness"; it rewards answers that repeat the question |
| **Criterion validity** | Does the score predict outcomes you care about? | Offline groundedness is high, yet users escalate frequently |
| **Reliability** | Would the same measurement repeated give the same result? | The score changes by several points between identical runs because outputs vary |

### Validity is argued, not computed

There is no formula that certifies validity. You build an argument and test its weakest link. A practical method:

1. State the claim: "Assistant answers are supported by the cited documents."
2. List the inferences between the score and the claim: the grader understands the rubric; the cases represent real questions; the corpus is current; the grader's judgement matches humans on the hard cases.
3. For each inference, name the evidence you have and the evidence you lack.
4. Report the weakest inference alongside the number.

A report that says "groundedness 91%" without the inference chain invites readers to supply their own, usually generous, one.

### Separating reliability from validity

A measure can be reliable and invalid: a grader that consistently rewards length gives stable scores and tells you nothing about support. It can be valid on average and unreliable: a human panel that agrees with the truth only half the time per item. Check both. Reliability is measured by repeating (re-run the system several times, re-grade several times, have a second human) and looking at the spread. Validity is argued, then tested against independent evidence such as outcomes in production.

### Goodhart effects and proxy drift

When a proxy becomes a target it stops being a good proxy. If a team is rewarded for citation rate, answers will cite more; whether they are better is a separate question. Defences: several metrics that pull against each other, periodic human audits of cases where the metric looks good, and replacing cases and rubrics on a schedule.

## Leakage and contamination

**Leakage** means information that should have been unavailable at evaluation time influenced the system under test. It inflates scores and, worse, does so invisibly.

| Leak path | Mechanism | Detection |
| --- | --- | --- |
| Public benchmark in training data | The model has seen items or answers | Compare scores on public vs. private items; perturb items and look for drops |
| Test question pasted into a prompt | Few-shot examples include test items | Overlap check between prompts and test cases |
| Tuning on the evaluation set | Prompts adjusted until the set passes | Held-out set; track how often the held-out set was consulted |
| Retrieval corpus contains the answer key | Ground-truth documents are in the index | Index audit; exclude evaluation-only documents |
| Grader sees metadata | Case ids or labels visible to the grader | Strip metadata from grader input |
| Temporal leakage | Later facts used for earlier decisions | Time-based splits |
| Duplicates across splits | Same case, reworded, in tuning and test | Near-duplicate detection |

### Detecting overlap

A cheap first check is n-gram overlap between evaluation texts and anything the system has seen: prompts, few-shot examples, indexed documents.

```python
# leakage.py
def ngrams(text, n=8):
    toks = text.lower().split()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)}

def overlap_report(eval_texts, reference_texts, n=8):
    """Fraction of each eval text's n-grams that occur in any reference text."""
    ref = set()
    for t in reference_texts:
        ref |= ngrams(t, n)
    out = {}
    for name, t in eval_texts.items():
        g = ngrams(t, n)
        out[name] = (len(g & ref) / len(g)) if g else 0.0
    return out
```

Run it over `eval_texts = {case_id: question}` against `reference_texts` made of every prompt template, every few-shot example and every indexed passage. A high overlap does not prove cheating (some questions legitimately quote documents), but it flags items to inspect. It does not catch paraphrased leaks, so it is a floor, not a guarantee.

### Canary strings and held-out discipline

- **Canary strings.** Place a unique, meaningless token in the private evaluation set. If it ever appears in a model's output or an indexed corpus, the set has leaked. This detects some leaks after the fact; it does not prevent them.
- **Access discipline.** The held-out set should be readable by a small group, stored apart from tuning data, and excluded from any tooling that feeds prompts or training sets.
- **Consultation log.** Record every time the held-out set is used to make a decision. If it has informed many decisions, it is functioning as a tuning set; refresh it.
- **Time-based splits.** Where facts change, build the test set from material newer than anything the system was tuned on.

### Contamination of the grader

If a model grades answers and the same family wrote the answers, scores may be inflated by shared style (self-preference). If graders see the reference answer, they may rubber-stamp similar surface text. Strip case metadata, randomise order, and compare with human labels.

## Bias, variance and uncertainty

### Sources of variation

A reported pass rate hides several independent sources of uncertainty. Name them.

| Source | What varies | Handling |
| --- | --- | --- |
| Case sampling | Which cases happen to be in the set | Intervals; larger sets |
| Model nondeterminism | Same input, different output | Repeat runs; report per-case pass counts |
| Grader noise | Same answer, different grade | Repeat grading; agreement with humans |
| Label error | Human labels are wrong in places | Adjudication; re-label samples |
| Distribution shift | Production inputs differ from the set | Online sampling; scheduled refresh |

Intervals on the pass rate reflect only the first. A complete account is wider than the Wilson interval suggests.

### Is 3 points on 80 cases real? A worked example

Prompt B passes 66 of 80 cases (82.5%); prompt A passes 63 (78.75%): +3.75 points. For one proportion near 0.8 with n = 80, the standard error is √(0.8 × 0.2 / 80) ≈ 0.045, so a 95% interval is about ±8.8 points. The intervals overlap heavily; unpaired, the data cannot distinguish the prompts.

The comparison is better made **paired**, because the same cases are used:

| | B passes | B fails |
| --- | --- | --- |
| **A passes** | 58 | 5 |
| **A fails** | 8 | 9 |

Only the **discordant** cases matter: B won 8, A won 5. An exact sign test on 13 discordant cases gives a two-sided p-value near 0.58: no evidence of a difference. (With 8 of 13 on one side, the one-sided tail is about 0.29, and the two-sided value doubles it.)

To detect a true +3-point improvement with paired data, assuming roughly 10% of cases are discordant in either direction, you need on the order of a thousand cases. If disagreements are fewer, fewer cases suffice. Practical rules:

- Run each case several times if outputs vary.
- Use paired analysis.
- Set the rejection rule in advance.
- Treat a result within the noise as **no change**, then choose on cost, latency or risk.

### A paired bootstrap

A bootstrap resamples cases with replacement to see how the difference would vary across plausible case sets. It handles metrics that do not have a tidy formula.

```python
import random

def sign_test_p(b_wins, a_wins):
    from math import comb
    n = b_wins + a_wins
    k = max(b_wins, a_wins)
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)

def paired_bootstrap(a, b, reps=10000, seed=7):
    """a, b: 0/1 outcomes on the same cases. 95% interval for mean(b) - mean(a)."""
    rng = random.Random(seed)
    n = len(a)
    diffs = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(sum(b[i] - a[i] for i in idx) / n)
    diffs.sort()
    return diffs[int(0.025 * reps)], diffs[int(0.975 * reps) - 1]
```

For the table above (A: 63 passes, B: 66 passes, 58 shared, B alone 8, A alone 5, 9 shared failures) the sign test gives p ≈ 0.58 and a seeded bootstrap of the paired difference gives an interval of roughly −5 to +12.5 points. The exact end-points depend on the seed and on the number of repetitions. The interval comfortably includes zero.

### Multiple comparisons

If you try ten prompt variants against the same set and keep the best, the "best" is partly luck. With ten independent tests at a 5% false-positive rate each, the chance of at least one false positive is about 1 − 0.95¹⁰ ≈ 40%. Options: pre-specify one primary comparison; adjust the threshold (for example, divide 0.05 by the number of tests, the conservative Bonferroni rule, giving 0.005 for ten); or confirm the winner on a **fresh held-out set** that was not used to choose it. The last option is usually the most convincing and the simplest.

### Subgroup analysis

An overall rate can hide a subgroup collapse. Slice by language, user expertise, input length, topic and whether the question concerns a recently changed document. Slices get small quickly, so interpret them with wide intervals, and use them to find *where to collect more cases*, not to declare conclusions. If a slice matters for fairness or safety, build it into the dataset deliberately rather than hoping the random sample contains enough.

### Bias in the evaluation process

| Bias | Mechanism | Mitigation |
| --- | --- | --- |
| Selection | Cases come from users who complain or from the authors' imagination | Mix sources; note the sampling frame |
| Survivorship | Only answered queries are logged; abandoned sessions disappear | Log abandonment and escalation |
| Confirmation | Reviewers look harder for errors in the new version | Blind comparisons; randomise order |
| Annotator | One person's taste becomes "truth" | Several labellers; guide; rotation |
| Automation | Easy-to-score properties dominate the dashboard | Include human-scored dimensions |

## Limits of automated judging

Model graders have **position**, **verbosity** and **self-preference** biases and can be fooled by confident wrong answers. Techniques: pairwise rather than absolute scoring, multiple judges with disagreement analysis, reference-guided judging, decomposing claims for verification against sources, and periodic human audits. For high-stakes cases, human review remains the standard.

### Grader biases and a calibration plan

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

The figures in the protocol are examples of the *form* of a rule. Set your own bars from the cost of a grading error for the criterion in question, not from any universal number.

### Claim decomposition

For groundedness, a stronger design than "rate the answer" is to split the answer into atomic claims and verify each against the supplied passages.

1. Extract claims (a model or a rule-based splitter).
2. For each claim, give the verifier only the claim and the retrieved passages.
3. Label each claim *supported*, *contradicted* or *not addressed*.
4. Score the answer by the fraction supported, and separately flag any contradicted claim.

The decomposition has its own error sources: claim extraction can miss or merge claims, and the verifier can be lenient on partial matches. Calibrate each step, and keep a human-audited sample of the extraction too.

## Designing the "escalate to a human" evaluation

The correct answer is sometimes "I cannot decide this; here is who to ask". Include cases where escalation is correct (ambiguous policy, high-impact request) and cases where it is wrong (a simple documented question). Measure both error types: **missed escalation** (dangerous) and **unnecessary escalation** (cost and user annoyance). Report the confusion matrix, not one accuracy figure, and set separate thresholds.

## Thresholds versus impact

A threshold converts a score into an action. Choosing it is a decision about harm, and the decision is usually made implicitly. Make it explicit.

### Errors have different costs

For a binary decision such as "escalate to a human", there are two error types: a **false negative** (a case that should have been escalated is not) and a **false positive** (an unnecessary escalation). Their costs differ and depend on the product: a missed escalation might cost incident time or user harm, an unnecessary one costs reviewer time and delays.

Choose a score threshold by comparing expected cost at each candidate. Illustrative setting: 1,000 requests, 50 of which truly need escalation. The counts below are made up to show the arithmetic.

| Threshold | Missed escalations (FN) | Unnecessary escalations (FP) | Cost if FN = 200 units, FP = 1 | Cost if FN = 20 units, FP = 1 |
| --- | --- | --- | --- | --- |
| Permissive | 20 | 30 | 4,030 | 430 |
| Moderate | 6 | 120 | 1,320 | 240 |
| Strict | 1 | 400 | 600 | 420 |
| Escalate everything | 0 | 950 | 950 | 950 |

With a high missed-escalation cost the strict threshold wins; with a lower ratio the moderate threshold wins. The *right threshold depends on the cost ratio*, and the cost ratio is a business and ethical judgement, not an evaluation output. The arithmetic is trivial; what matters is that someone owns the ratio and that it is written down.

Two constraints modify the picture:

- **Capacity.** A strict threshold that sends 400 unnecessary escalations per thousand requests to human reviewers may exceed what the team can review. A threshold that cannot be operated is not a safeguard.
- **Harm is not additive.** Some harms (a leaked credential, a harmful instruction followed) are not commensurable with a handful of annoyed users. Treat those as **constraints** (zero tolerance or a very small bound) rather than as terms in a sum.

### Thresholds should carry their impact

For every threshold, write the sentence "if this threshold is wrong in the permissive direction, then ___ happens; in the strict direction, ___." If you cannot complete the sentence, the threshold is arbitrary.

```text
Threshold record:
  Metric:       refusal accuracy on mutation requests
  Rule:         zero failures on 40 cases; any failure blocks release
  Permissive error:  a change request is executed or agreed to without authority
  Strict error:      safe questions are refused (tracked separately by over-refusal rate)
  Evidence:     test report id, dataset version, grader/version if any
  Review date:  <date>   Owner: <role>
  Known gap:    untested phrasing families (see coverage matrix cells A3, B2)
```

### Separating "can we measure it" from "does it matter"

Teams naturally gate on what is easy to measure. A useful discipline: list the harms that would matter most, then ask for each whether any current metric detects it. Harms with no metric are **unmeasured risks** and belong on the risk register with a plan (build cases, add a control, monitor online), not silently omitted.

## Auditing an evaluation suite for blind spots

Build a **coverage matrix** and look for empty cells.

| Dimension | Values to check | Typical gap | Risk if missing |
| --- | --- | --- | --- |
| Behaviour | Answer, refuse, abstain, escalate | No "escalate" cases | Wrong action in the highest-impact cases |
| Population | Languages, expertise levels, accessibility needs | English only | Quiet failure for whole user groups |
| Input shape | Long inputs, empty input, malformed text, pasted logs | Only tidy one-line questions | Failures at production inputs |
| Conversation | Multi-turn manipulation, topic switching, repeated pressure | Single-turn only | Safeguards erode over a conversation |
| Evidence | Missing, contradictory, stale sources | Always-clean sources | Overconfident answers |
| Adversarial | Injection in documents, tool abuse, secrets requests | A few jailbreak strings | Real attacks unexercised |

Rank empty cells by impact × likelihood in production, add cases for the top few, and write down the cells you chose not to cover. That statement bounds your claim.

## Red-teaming programme

Structured adversarial testing by people who did not build the feature. Elements: a taxonomy of attacks (direct and indirect prompt injection, jailbreaks, data exfiltration, tool abuse, denial of wallet, multi-turn manipulation), a tracker with severity, reproduction steps and fixes, and re-testing. Automate known attacks as regression cases; keep novel ones human-driven. Define what "acceptable residual risk" means with the business.

### Scoping and rules of engagement

Before any testing, write down: the systems in scope and out of scope; permitted techniques; the data that may and may not be touched; how to stop immediately; who is told; and how findings are disclosed and stored. Testing that touches real credentials or production data without these rules is itself a risk.

### Red-team tracker: minimum record

| Field | Example |
| --- | --- |
| ID, severity | RT-014, High (data exfiltration via crafted document) |
| Category | Indirect prompt injection |
| Reproduction | Exact input, document, model/prompt/bundle version, steps |
| Impact | The assistant sent retrieved text to an attacker-controlled URL |
| Fix | Output URL allow-list; document tagged as untrusted; tool call blocked |
| Re-test | Automated regression case RT-014 added; passes on version 1.4.2 |
| Status/owner/date | Closed, <owner>, date |

Automate attacks that are reproducible and cheap to detect (known jailbreak strings, injection templates, secret-pattern output), and keep creative, multi-step or social attacks with humans, rotating testers so the team does not share blind spots.

### Interpreting red-team results

A red-team report is evidence about *discovery effort*, not about absence of flaws.

- Findings per tester-hour measure how easy it was to find issues, not how many exist.
- Zero findings from a short, shallow exercise says little; say how many tester-hours, of what skill, with what access.
- Severity should be ranked by impact on people and systems, with the attack's cost to the attacker as a separate axis.
- Track **time to fix** and **recurrence** (the same class re-found after a fix signals a systemic gap).

Agree with the business what residual risk is acceptable, per severity, in writing, and revisit the agreement after each exercise.

## Safety architecture

Layered, independent controls so one failure is not catastrophic: capability limits (least privilege), isolation of untrusted content, input and output classifiers, policy engines outside the model, monitoring and anomaly detection, rate limits, human approval for impactful actions, audit trails and an incident process. Assume each layer fails sometimes and design for graceful failure.

**Independence matters.** Two layers that share a failure mode (the same classifier model, the same prompt, the same credential) are one layer for risk purposes. When assessing a design, ask of each pair of controls: what single event would defeat both?

## Governance

Governance is the set of decisions about who may release what, on what evidence, and who answers for the outcome.

### Decision rights

| Decision | Typical decider | Evidence required |
| --- | --- | --- |
| Release a routine prompt change | Feature owner | Gate pass |
| Release with an exception | Approver above the requester | Exception record |
| Waive a safety zero-tolerance check | Senior accountable owner for the risk | Risk assessment, compensating control, expiry |
| Change a threshold | Feature owner plus risk or security reviewer | Rationale, impact sentence, review date |
| Retire or disable the feature | On-call (immediate), owner (permanent) | Incident or review record |

### Risk tiers

Not every feature needs the same rigour. Classify by what a wrong output could cause, and scale controls.

| Tier | Example consequence | Typical minimum |
| --- | --- | --- |
| Low | Slightly unhelpful answer, easily verified by the user | Deterministic gate; sampled review |
| Medium | Misleading operational guidance a reviewer would likely catch | Calibrated grader, human audit sample, documented limits |
| High | Output could trigger an impactful action or affect a person's rights | Human approval on action, red-team before launch, restricted release, formal sign-off |

The tier definitions are yours to set with the organisation's risk function. The point is that the *same* gate for everything either over-burdens trivial features or under-protects dangerous ones.

### Evidence pack for a release decision

A release record that stands up months later contains: the version bundle (prompt, model identifier, corpus and dataset versions); the evaluation report with intervals; grader calibration summary; open red-team findings with severity; active exceptions; the threshold records; and the sign-off. Store them together, immutable, and linked from the release log.

### Regulatory and ethical context

Depending on jurisdiction and use, requirements on transparency, human oversight, data protection, record keeping and risk classification may apply. Build the documentation, logging and review processes early; retrofitting is expensive. Consider fairness: evaluate across user groups and languages, and avoid using the model for decisions that need accountability without human review. Treat statements about specific legal obligations as questions for legal and compliance specialists; an evaluation engineer's role is to make the evidence available.

## Drift and ongoing assurance

Quality changes without code changes: provider model updates, corpus changes, user behaviour shifts. Run scheduled evaluations against production-like inputs, monitor online proxies (refusal rate, citation rate, escalation rate, user corrections), alert on shifts and keep canary cases that must always pass. Maintain a rollback for prompt, model and corpus versions.

### Drift monitoring plan

| Monitor | Cadence | Trigger |
| --- | --- | --- |
| Canary suite (20 stable, must-pass cases) | Every deploy and daily | Any failure pages the owner |
| Full evaluation on fresh production samples | Weekly | Drop > 3 points on any criterion |
| Online proxies: refusal rate, citation rate, escalation rate, schema failures | Continuous | Shift > 2 standard deviations from the 28-day baseline |
| Corpus change diff | On each index update | Large deletions or additions trigger a re-run |
| Provider notices | On subscription | Re-evaluate before the deprecation date |

The numbers in the trigger column are starting points. A "3-point drop" is meaningful only relative to the interval of the weekly sample: on a few dozen cases it is noise, so size the sample so that the trigger is detectable, or use a wider trigger and say so.

## Incident process for a harmful output, end to end

Detect (user report or monitor); triage severity within an hour; contain (disable the feature or the specific capability); preserve evidence (inputs, retrieved context, version bundle, logs, with restricted access); find the cause and reproduce it; fix and add a regression case; communicate to affected users where required; re-enable behind canary; hold a blameless review and update the red-team tracker and evaluation suite.

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Goodhart effect | Optimising to the metric degrades real quality | Multiple metrics, human audits, refresh data |
| Eval contamination | Test cases leak into prompts or training | Private held-out sets |
| Silent model update | Provider changes behaviour | Pinned versions, scheduled regression runs |
| Judge collapse | Grader rewards style over substance | Calibrated rubrics, human checks |
| False reassurance | Passing a narrow suite is read as "safe" | State scope of claims, widen coverage |
| Winner's curse | Best of many variants looks better than it is | Fresh held-out confirmation |
| Threshold by habit | A number inherited without an impact statement | Threshold records with owner and review date |
| Shared failure mode | Two "independent" controls fail together | Independence review |

## Case catalogue

These are constructed scenarios for analysis.

### Case 1 — The benchmark that the model had seen

A team reports a high score on a public question set and decides the model is safe for a feature. A private set of similar questions, written afterwards, gives a markedly lower pass rate.

*Reading.* The public set may have been in training data, so its score mixes ability with recall. Public and private results are different measurements.
*Action.* Treat the private set as the decision basis; perturb public items (rephrase, change values) and compare; document which claims rest on which set.

### Case 2 — The significant-looking winner

Twelve prompt variants are compared with the baseline on the same 100 cases. One variant shows a gain that looks large and is declared the winner.

*Reading.* Twelve tries inflate the chance that one looks good by luck.
*Action.* Pre-specify the comparison, adjust the threshold or confirm on a fresh held-out set. If the gain disappears there, it was selection.

### Case 3 — The safe average, the unsafe slice

Overall refusal accuracy is high. A slice analysis shows that mutation requests written in a language other than the main one are refused less often, and there are few such cases in the set.

*Reading.* The aggregate hid a subgroup; the slice is small so the interval is wide, which means the real rate could be much worse or fine.
*Action.* Build a dedicated multilingual mutation set, gate it separately, and record it on the coverage matrix.

### Case 4 — The threshold nobody could justify

A gate demands 90% groundedness. Asked why 90%, nobody recalls; asked what happens at 88%, nobody can say.

*Reading.* The threshold was inherited, not decided.
*Action.* Write the threshold record: what is protected, the cost of a miss versus an unnecessary block, the capacity to review, the interval needed to claim compliance. Change the number only through that record.

### Case 5 — Two layers, one point of failure

An input classifier and an output classifier both use the same underlying model. A crafted input that confuses the model defeats both.

*Reading.* Apparent depth with a shared failure mode.
*Action.* Diversify (a rule-based check, a different model, a capability limit), and test with inputs designed to defeat the shared component.

### Case 6 — The red team that found nothing

A two-hour exercise by two testers who helped build the feature records no findings, and the report says "no vulnerabilities".

*Reading.* Short, shallow, non-independent testing says little about absence.
*Action.* Rewrite the conclusion to state effort and independence; schedule an exercise with testers who did not build it; keep the result as a lower bound on risk, not an upper bound.

## Expert trade-offs

| Decision | Benefit | Cost | When to accept the cost |
| --- | --- | --- | --- |
| Large held-out sets | Tight intervals, honest reporting | Labelling cost; restricted access | High-stakes features |
| Claim-level grading | Detects partial support | More calls, extraction error | Groundedness gating for medium and high tiers |
| Pre-registered decision rules | Prevents motivated analysis | Slower iteration | Ship/no-ship decisions |
| Human red team | Finds novel attacks | Cost, scheduling | Before launch and at major change |
| Strict thresholds | Lower miss rate | Reviewer load, user friction | When the missed-error cost dominates and capacity exists |
| Frequent refresh of data | Resists overfitting and drift | Upkeep, loss of long-term comparability | Fast-changing domains; keep a frozen canary slice |
| Independent control layers | Resilience | Complexity | Risks where one failure would be severe |

## Knowledge consolidation

- Treat evaluation as an **experiment**: population, sampling, intervals, paired comparison, pre-registered rules.
- **Validity** is argued through the inference chain from score to claim; report the weakest link. A metric can be reliable and invalid.
- **Leakage** inflates scores invisibly; use held-out sets with access control, consultation logs, overlap checks and canary strings.
- Uncertainty has several sources; **interval-on-cases understates it**. Prefer **paired** comparisons, resample where formulas are awkward, and confirm winners on fresh data.
- **Slices** find hidden failures but are noisy; use them to direct data collection.
- Automated graders are biased instruments: calibrate per criterion, weigh false passes for safety criteria, decompose claims, and audit by humans.
- **Thresholds are decisions about impact.** The cost ratio belongs to the business; write the impact sentence; treat grave harms as constraints; respect review capacity.
- **Red-team results** bound discovery effort, not the absence of flaws; keep independence and written residual-risk agreements.
- **Governance** assigns decision rights by risk tier and keeps an evidence pack per release.
- **Drift** requires scheduled evaluation, canaries and rollback; size samples so that triggers are meaningful.

## Exercises

**Exercise 1 — Validity argument.** Take one reported metric from a system you know. Write the claim, list the inferences between score and claim, and mark each inference as evidenced or not. Identify the weakest one and propose a test.

**Exercise 2 — Leakage hunt.** Run the n-gram overlap function over your evaluation questions against your prompts, few-shot examples and indexed passages. List the five highest-overlap items and classify each as legitimate quotation, a leak or unclear.

**Exercise 3 — Paired analysis.** Take two versions of a prompt, run both on the same 60 cases, and build the 2×2 table. Compute the sign-test p-value and a paired bootstrap interval. Write the decision under a rule you fix *before* looking at the result.

**Exercise 4 — Winner's curse.** Simulate 10 variants that all have the same true pass rate of 0.8 on 100 cases each (random draws). Repeat 200 times and record how often the best variant looks at least 5 points better than 0.8. Explain the result in two sentences.

**Exercise 5 — Cost-based threshold.** Using a score threshold sweep from your own escalation or refusal classifier on labelled data, build the table of FN and FP counts at four thresholds. Choose a threshold under two different cost ratios, and describe the reviewer capacity implied.

**Exercise 6 — Coverage matrix audit.** Build the coverage matrix for your suite. Choose the three empty cells with the highest impact × likelihood, add three cases to each, and record the cells you chose not to cover and why.

**Exercise 7 — Independence review.** Draw your safety architecture as a list of controls. For each pair, name the single event that would defeat both. Identify one pair to diversify.

**Exercise 8 — Evidence pack.** Assemble the evidence pack for a recent release of a feature you work on. List what is missing, and who would have to supply it.

**Solution notes.**

*Exercise 1.* Typical weakest inferences: "the cases represent real traffic" (they were written by the team) and "the grader agrees with humans on hard cases" (calibration used easy cases). A test for the first is to sample real, redacted traffic and compare the score on it with the score on the authored set.

*Exercise 2.* Expect a mix. Quoting a document phrase in a question is legitimate and shows up as moderate overlap with the indexed corpus. Overlap with a few-shot example is a genuine leak: the case no longer tests generalisation. Overlap is a flag for inspection, not a verdict.

*Exercise 3.* The sign test uses only discordant cases. With fewer than 6 discordant cases, even a unanimous split cannot reach a two-sided p below 0.05, so say that the set is too small to decide and choose on cost or risk. The bootstrap interval will usually include zero for small sets.

*Exercise 4.* With ten variants of the same true rate, the maximum of ten noisy estimates is typically above the true value. A run with Python's `random.Random(1)` gave about 78% of repetitions with a best score of 85 or more; your fraction will differ with the seed. Your exact fraction depends on the random draws; the instructive result is that the winner's apparent edge shrinks when re-measured on fresh cases.

*Exercise 5.* Moving from a lower to a higher cost for a missed case moves the best threshold toward more escalation, until the reviewer capacity becomes the binding constraint. If the capacity limit is hit, report that the chosen threshold is a compromise and what additional controls cover the remaining risk.

*Exercise 6.* A defensible answer contains a short list of consciously uncovered cells with reasons such as low likelihood, a different control covering the risk, or planned future work. An empty "not covered" list is a sign that the matrix was not examined honestly.

*Exercise 7.* Common shared failure modes: the same model used for classification and generation, the same credential reachable from several layers, the same logging pipeline for detection and audit. Diversifying often means adding a simple rule-based check beside a model-based one.

*Exercise 8.* Missing items are usually the grader calibration summary, the threshold records and the version of the dataset used. Name an owner and a date for each.

## Mentoring prompts

Design an evaluation for an assistant whose correct answer is sometimes "escalate to a human". How would you estimate whether a 3-point improvement on 80 cases is real, and what would you do if the answer is "cannot tell"? What would an incident process for a harmful output look like end to end? Choose one threshold in a system you know and write its impact sentence: what is the cost if it is too permissive, and if it is too strict, and who decided? Which of your evaluation claims rest on a dataset that might have leaked, and how would you find out? Which two of your safety controls share a failure mode?

---
