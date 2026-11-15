# T-AIE-03-P — Professional Engineering

*Chapter: [T-AIE-03 — AI Evaluation, Safety and Quality](README.md) · Part 3 — AI Engineering*

<a id="t-aie-03-p"></a>
#### T-AIE-03-P — Professional Engineering

## Why this matters

At Intermediate level, an evaluation suite is something one engineer runs. At Professional level it becomes **part of how the organisation decides to release**. That raises different questions. Who owns the datasets? What exactly blocks a release, and who may override the block? Which risks are handled by evaluation, and which by controls that evaluation cannot replace? How do you keep a model grader honest over months? What do you write down so that a new colleague, an auditor or an incident responder can understand what was claimed and why?

This section assumes you can build and run the Beginner and Intermediate practices: cases with provenance, deterministic scoring, human review, intervals for small samples and a CI gate. It continues with the fictional **runbook assistant**, now treated as a feature with an owner, a release process and users who depend on it. Numbers in worked examples are illustrations chosen to show a calculation; none is a measurement of a real system.

## An evaluation strategy

An evaluation strategy is a short, versioned document that answers five questions.

1. **Define quality for this feature.** Name the dimensions that matter: correctness, groundedness, completeness, refusal accuracy (both directions), safety, tone, latency and cost. State which are *gating* (a failure blocks release) and which are *tracked* (reported, with trends).
2. **Build datasets.** A **golden set** (curated, small, stable), a **regression set** (past failures), an **adversarial set** (attacks) and a **held-out set** that is never used for tuning prompts or thresholds. Sample from real traffic with privacy controls.
3. **Automate.** Deterministic checks on every pull request; broader and model-graded evaluation nightly or before release.
4. **Gate releases** on thresholds per metric, with explicit rules for exceptions.
5. **Close the loop.** Feedback, incidents and red-team findings become cases.

The strategy is not bureaucracy for its own sake. It is the document you open when a release is contested, to see what the team agreed *before* the numbers arrived.

| Dimension | Gating or tracked | Method | Cadence |
| --- | --- | --- | --- |
| Refusal accuracy (mutations) | Gating, zero tolerance | Deterministic assertion | Every PR |
| Over-refusal on safe neighbours | Gating, threshold | Deterministic assertion | Every PR |
| Schema validity | Gating, zero tolerance | Deterministic assertion | Every PR |
| Citation provenance | Gating, threshold | Deterministic plus sampled human check | Every PR and weekly sample |
| Groundedness of claims | Gating on a calibrated grader | Model-graded with human audit | Nightly and pre-release |
| Helpfulness and tone | Tracked | Rubric, human sample | Pre-release |
| Latency, cost per request | Tracked, with budget alert | Telemetry | Continuous |

## Release gates

A **release gate** is a rule, decided in advance, that determines whether a candidate version may go to users. The three properties of a good gate are that it is **explicit** (a number or a condition), **automatic where possible** (so it cannot be skipped by accident), and **owned** (a named role may grant exceptions).

### Choosing thresholds

A threshold is a decision about risk, not a statistical fact. Different failure types deserve different rules.

| Failure type | Typical rule | Reason |
| --- | --- | --- |
| Mutation executed or secret disclosed in a test | Zero tolerance | A single occurrence demonstrates a gap in a control |
| Over-refusal of safe requests | Maximum rate, e.g. "no more than two safe neighbours refused" | Product cost, tolerable in small numbers |
| Groundedness | Minimum rate with lower-bound requirement | Statistical estimate; use the interval, not the point |
| Non-regression against the current release | No category may fall by more than a stated margin | Stops silent trade-offs |
| Minimum coverage | Total cases and per-category counts at least a floor | Prevents passing by deleting cases |

For rates, gate on the **lower end of the interval**, not the point estimate. If the policy is "groundedness at least 85%", a result of 27 of 30 (point estimate 90%, interval roughly 74% to 96%) does not demonstrate the requirement. Either the set must grow, or the policy must be stated honestly as "no evidence of failure yet at this size". Decide which before the first release, not after a failing run.

### A gate you can run

The policy is data, stored in the repository and reviewed like code.

```json
{
  "min_total": 120,
  "categories": {
    "mutation_refusal": {"min_cases": 20, "max_failures": 0},
    "safe_neighbour":   {"min_cases": 20, "max_failures": 2},
    "injection":        {"min_cases": 15, "max_failures": 0},
    "grounded_answer":  {"min_cases": 40, "min_rate_lower_bound": 0.80},
    "schema":           {"min_cases": 120, "max_failures": 0}
  },
  "max_regression_points": 3.0
}
```

The gate reads a report that records counts per category, optionally a baseline report from the current release, and a file of approved exceptions.

```python
# release_gate.py — run: python release_gate.py policy.json report.json [baseline.json] [exceptions.json]
import json, sys
from datetime import date
from math import sqrt


def wilson_lower(passed, total, z=1.96):
    if total == 0:
        return 0.0
    p = passed / total
    d = 1 + z * z / total
    c = (p + z * z / (2 * total)) / d
    h = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / d
    return c - h


def active_exceptions(path, today):
    if not path:
        return {}
    out = {}
    for e in json.load(open(path)):
        if date.fromisoformat(e["expires"]) >= today:
            out[e["check"]] = e
    return out


def evaluate(policy, report, baseline=None, exceptions=None, today=None):
    today = today or date.today()
    exc = active_exceptions(exceptions, today)
    problems = []
    if report["total"] < policy["min_total"]:
        problems.append(f'total {report["total"]} below {policy["min_total"]}')
    for name, rule in policy["categories"].items():
        c = report["categories"].get(name, {"passed": 0, "total": 0})
        failures = c["total"] - c["passed"]
        found = []
        if c["total"] < rule["min_cases"]:
            found.append(f'{name}: {c["total"]} cases, need {rule["min_cases"]}')
        if "max_failures" in rule and failures > rule["max_failures"]:
            found.append(f'{name}: {failures} failures, allowed {rule["max_failures"]}')
        if "min_rate_lower_bound" in rule:
            lb = wilson_lower(c["passed"], c["total"])
            if lb < rule["min_rate_lower_bound"]:
                found.append(f'{name}: lower bound {lb:.3f} below {rule["min_rate_lower_bound"]}')
        if baseline and name in baseline["categories"] and c["total"]:
            b = baseline["categories"][name]
            drop = 100 * (b["passed"] / b["total"] - c["passed"] / c["total"])
            if drop > policy["max_regression_points"]:
                found.append(f"{name}: fell {drop:.1f} points versus baseline")
        if found and name in exc:
            print(f'EXCEPTION applied to {name} until {exc[name]["expires"]}: {exc[name]["reason"]}')
        else:
            problems.extend(found)
    return problems


if __name__ == "__main__":
    a = sys.argv[1:]
    policy, report = json.load(open(a[0])), json.load(open(a[1]))
    baseline = json.load(open(a[2])) if len(a) > 2 else None
    problems = evaluate(policy, report, baseline, a[3] if len(a) > 3 else None)
    for p in problems:
        print("BLOCK:", p)
    print("gate:", "FAIL" if problems else "PASS")
    sys.exit(1 if problems else 0)
```

Properties worth copying: coverage is a gate (so deleting cases cannot pass), the lower bound rather than the point estimate is used for rates, regressions are checked against the baseline release, and exceptions are looked up from a file with an **expiry date** so they lapse automatically.

### What a gate cannot do

A gate checks that *tested* behaviour met the policy. It says nothing about untested inputs, drift after release, or a threshold that was set wrongly. Pair it with monitoring (T-AIE-05) and with the limits statement in your documentation.

## Exceptions

Pressure to ship will produce requests to override a failing gate. Plan for it, because an ad-hoc exception culture erodes every gate.

An **exception record** contains:

| Field | Example |
| --- | --- |
| Check waived | `grounded_answer` lower bound |
| Reason | "Corpus update added 12 new documents; cases for them are in review" |
| Risk accepted | "Answers about the 12 new documents are unevaluated for this release" |
| Compensating control | "Feature flag off for those document sets; weekly sample review" |
| Approver | Named role, not the requester |
| Expiry | A date, not "until fixed" |
| Follow-up | Ticket reference |

```json
[
  {
    "check": "grounded_answer",
    "reason": "New corpus segment not yet covered by cases",
    "risk": "Unevaluated answers for the new segment",
    "compensating_control": "Segment disabled by flag until cases land",
    "approver": "feature-owner",
    "expires": "2026-12-15",
    "ticket": "AIQ-482"
  }
]
```

Rules that keep exceptions honest:

1. **The requester is never the approver.**
2. **Exceptions expire.** The gate ignores an expired one, so the next release blocks again.
3. **Zero-tolerance safety checks have no routine exception route.** Waiving a mutation-refusal failure should require escalation above the feature owner, because the check protects people outside the team.
4. **Exceptions are counted and reviewed.** If the same check is waived release after release, the threshold is wrong or the product is not ready; either way, fix that, not the paperwork.

## Dataset ownership

Datasets are product assets. Without an owner they decay: cases go stale, labels disagree, sensitive data creeps in.

| Dataset | Owner role | Who may add | Who may remove or change expectation | Notes |
| --- | --- | --- | --- | --- |
| Golden set | Feature owner | Team members, by review | Feature owner with a recorded reason | Stable; reviewed each quarter |
| Regression set | On-call or incident owner | Anyone resolving an incident | Nobody; supersede with a note | Append-only |
| Adversarial set | Security reviewer | Team and red-team | Security reviewer | Handle with care; may hold attack text |
| Held-out set | Evaluation owner | Evaluation owner only | Evaluation owner | Access restricted so it cannot leak into tuning |
| Traffic-derived samples | Data protection owner | Through a documented pipeline | Retention policy | Redacted; consent and legal basis recorded |

### Practices

- **Version datasets** like code: a dataset has a version, and each report names the dataset version it ran.
- **Separate tuning from reporting.** Cases you iterate against become *training* cases for your prompt. Report final results on a held-out set that you looked at rarely, and refresh it when it has been consulted too often.
- **Sample real traffic with privacy controls.** Redact personal data and secrets *before* a human or a grader sees the text; limit access; set retention; record the basis for use. Do not copy production text into a public repository or an external grader without checking the terms that apply to it.
- **Review for leakage into prompts.** If a test question is pasted into a few-shot example, that test no longer measures generalisation.
- **Review labels.** Periodically re-label a sample; if the new labels disagree with old ones, the guide or the world has changed.

## Safety controls beyond evaluation

Evaluation estimates how often behaviour is acceptable on tested inputs. It does not *prevent* a bad outcome on an untested one. Controls do. Both are needed, and neither substitutes for the other.

| Control | Purpose | Evaluation's role |
| --- | --- | --- |
| Input pre-checks and classification | Block or route out-of-scope or abusive input | Measure false blocks and misses |
| Output validation and filtering | Enforce schema and policy before display | Test that bad outputs are caught |
| Tool allow-lists and approvals | Limit actions (see T-AIE-04) | Test that disallowed calls are refused |
| Rate and cost limits | Contain abuse and runaway cost | Test limits trigger |
| Redaction of secrets and personal data | Reduce leakage in prompts, logs and answers | Test with fake secrets |
| Human escalation | A route out when confidence is low or stakes are high | Measure missed and unnecessary escalations |
| Kill switch | One action to disable the feature (see T-AIE-05) | Rehearse it |

Two principles shape the design.

**Prefer controls outside the model.** A rule in the prompt ("never reveal the key") is a request to a probabilistic system. A control in code (the key is never placed in the prompt; the output scanner rejects key patterns; the tool is not on the allow-list) holds regardless of the model's behaviour. Use the prompt as a first layer and code as the one you rely on.

**Test that the control works, not only the model.** For an output scanner, the test is a set of fake secrets that must be blocked and a set of harmless strings that must not be.

```python
import re

SECRET_PATTERNS = [
    re.compile(r"\bSK-[A-Z0-9-]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

def leaks_secret(text):
    return any(p.search(text) for p in SECRET_PATTERNS)

assert leaks_secret("the key is SK-TRAINING-FAKE-0000")
assert leaks_secret("AKIAABCDEFGHIJKLMNOP")
assert not leaks_secret("The SKU is 12345 and the sky is clear")
```

A control that is only believed, never tested, is an assumption.

### Quality trade-offs

Safety, helpfulness and cost pull against each other. An assistant that refuses too much is useless; one that never refuses is dangerous. Track **over-refusal** alongside **under-refusal**, and report both. Raising a threshold on one often moves the other, so look at them together on the same cases, as in a confusion matrix, rather than optimising one number.

## Model-grader calibration

A model grader is a measuring instrument. Instruments are calibrated before use and re-checked afterwards.

### Calibration procedure

1. **Define the criterion** as a yes/no question, with definitions and anchored examples. "Does every claim in the answer appear in the supplied passages?"
2. **Collect human labels.** At least two reviewers label a sample, disagreements are resolved by a third or by discussion, and agreement is measured (see Intermediate). If humans cannot agree, the grader has nothing to match.
3. **Choose the sample to include hard cases:** near-misses, long answers, answers with partial support, and answers that sound confident but cite the wrong passage.
4. **Run the grader and compare** per criterion, reporting agreement, false-pass rate (grader says pass, human says fail) and false-fail rate.
5. **Accept the grader for a criterion** only if agreement meets a bar fixed in advance *and* the false-pass rate is acceptable for the risk. For safety criteria a false pass is the dangerous error, so weigh it more heavily than overall accuracy.
6. **Version everything:** grader model identifier, prompt, settings, the calibration sample and the date.
7. **Re-audit on a schedule**, for example a small human-labelled sample from each scheduled run, and re-calibrate when the grader, rubric, system outputs or corpus change materially.

### Reading a calibration result

Illustrative confusion matrix for one criterion on 100 human-labelled answers:

|  | Human: supported | Human: not supported |
| --- | --- | --- |
| **Grader: supported** | 61 | 9 |
| **Grader: not supported** | 7 | 23 |

Overall agreement is 84 of 100. But the grader passed 9 answers that humans judged unsupported: 9 of 32 unsupported answers were waved through, a false-pass rate of about 28%. If this criterion gates a safety property, 84% overall agreement is the wrong number to quote; the 28% false-pass rate is the one that decides whether the grader may be used alone, used only as a pre-filter ahead of human review, or rejected.

### Practical rules

- Use a grader from a **different model family** than the system being judged where practicable.
- **Randomise** option order in pairwise comparisons, and run both orders.
- Ask for a **brief rationale, then a verdict**, and store both.
- Give the grader the **source passages** and ask for claim-by-claim support, rather than "is this good?"
- Keep a **human-only slice** that never goes through the grader, so you can detect grader drift.
- Report **uncertainty**: with small sets, differences of a few points are noise.

## Documentation and accountability

Write the documentation for the person who will be paged at night, the person who will audit a decision and the user who needs to know what the assistant can and cannot do.

### Feature documentation (a one-page record)

```text
Feature: Runbook assistant
Version: prompt 12 / model identifier <pinned> / corpus 2026-11-01 / dataset v34
Owner: <role>   Escalation contact: <role or channel>

Intended use
  Answer questions about operational runbooks, citing the passage used.
Out of scope
  Executing changes; legal, medical or HR questions; questions about systems
  not covered by the corpus.

Known limitations
  - May decline safe questions that resemble requests for changes.
  - Cannot answer about documents added after the corpus date.
  - Evaluated on 136 cases (see report), written by the team; not a sample of
    real traffic for categories marked "synthetic".

Evaluation (latest)
  Report: eval-2026-11-14.json   Gate: PASS   Exceptions: none active
  Human-audited grader agreement for groundedness: <fill from calibration>

Safety controls
  Output secret scanner; tool allow-list (read-only); rate limit; kill switch.

Data
  Corpus sources: <list>. Traffic samples: redacted; retention <period>.

Change history
  Link to release log, exception log and red-team tracker.
```

### Show limitations to users

State the main limits in the interface, in plain language: that answers come from a particular set of documents, that they may be incomplete, and where to go for something the assistant cannot do. Users who know the limits calibrate their trust; users who do not will over-rely.

### Accountability

Name who decides, who approves exceptions, who maintains each dataset and who is contacted when the feature misbehaves. Keep decisions and their evidence (report, dataset version, exception record) together, so that "why did we release this?" has an answer months later.

## Case studies

The following are **illustrative scenarios** constructed to teach reasoning. They are not reports of real events.

### Case 1 — The green suite that missed the polite request

A team's suite contains twenty requests for changes, all phrased as commands ("Restart the cache node"). All pass. After a prompt rewrite aimed at friendlier tone, a user writes "Could you kindly restart the cache node for me?" and the assistant agrees.

*Analysis.* The suite measured one phrasing. The failure is a coverage gap, not a flaky model.
*Response.* Add the case to the regression set with its reason and source, add a family of rephrasings (politeness, questions, indirect speech) to the golden set, and add a coverage-by-phrasing line to the strategy document. The gate's per-category minimum now counts the larger set.
*Lesson.* A passing suite describes the cases you thought of.

### Case 2 — The grader that liked long answers

A nightly groundedness score rises over several weeks while human spot checks look unchanged. Investigation compares grader scores with answer length and finds that longer answers score higher regardless of support.

*Analysis.* Verbosity bias; the prompt changes had made answers longer, and the grader rewarded length.
*Response.* Add a length-matched slice to calibration, change the grader prompt to say that length is not a criterion, re-run calibration, and report the human-labelled sample next to the grader score from now on.
*Lesson.* A metric that moves while humans see no change is a signal to inspect the instrument.

### Case 3 — The exception that never expired

A gate failure on a new corpus segment is waived "until cases are written". No expiry is recorded. Two releases later the segment is still unevaluated and still live.

*Analysis.* The exception had no end, so the compensating control lapsed with the memory of why it existed.
*Response.* Require an expiry and a named approver in the record; have the gate read exceptions and ignore expired ones; review the active-exception list at each release meeting.
*Lesson.* Exceptions without expiry become policy.

### Case 4 — The tuning set that became the test set

A team tunes a prompt by reading failures on the 120-case golden set and adjusting until it reaches 95%. A later production sample, labelled by humans, shows a materially lower rate.

*Analysis.* Repeated tuning against the evaluated cases overfits the prompt to them. The 95% measures the cases the prompt was shaped around.
*Response.* Introduce a held-out set that the tuning team does not read, report both numbers, and refresh the held-out set after it has been consulted several times.
*Lesson.* Report on data you did not tune on.

### Case 5 — The control nobody tested

The prompt says "never output keys". A secrets scanner exists in the output path, but nobody has tested it with realistic fake keys, and a pattern was mistyped so it never matches the key format in use.

*Analysis.* A control believed to work but never exercised provides no assurance.
*Response.* Add fake-secret cases and a unit test for each pattern, run them in the gate, and add the scanner to the periodic control review.
*Lesson.* Test the control, not only the model.

## Professional trade-offs

| Decision | Benefit | Cost | When to accept the cost |
| --- | --- | --- | --- |
| Strict zero-tolerance safety gates | Confidence for the protected harm | Blocked releases; temptation to bypass | Harms that fall on people outside the team |
| Lower-bound gating on rates | Honest claims | Larger datasets needed | Any rate-based claim you will rely on |
| Model grader in the gate | Scales to free text | Calibration and drift upkeep | When a calibrated grader beats the cost of human review |
| Held-out set | Honest reporting | Lower availability for debugging | Anywhere prompts are tuned iteratively |
| Traffic-derived cases | Realism | Privacy work, retention, redaction | When synthetic cases miss real phrasing |
| Documentation of limits in the UI | Calibrated user trust | Product friction | User-facing assistants |
| Expiring exceptions | Prevents quiet erosion | Repeat approvals | Always |

## Decision guide

| Need | Do | Avoid |
| --- | --- | --- |
| Prove a change is safe | Evaluation on current code, per-category thresholds | Spot checks |
| Catch regressions | A case from every incident, with reason and source | Deleting failing cases |
| Test safety | Adversarial and injection sets plus tests of the controls | Only happy paths |
| Use model graders | Rubric, calibration, human sampling, versioning | Treating scores as truth |
| Gate rates | Lower bound and minimum cases | Point estimates on small sets |
| Waive a check | Record with approver, risk, control and expiry | Informal agreement |
| Report honestly | State what a pass does not prove | "The model usually refuses" |
| Keep datasets healthy | Named owners, versions, a held-out set | Shared folder nobody owns |

## Knowledge consolidation

- An **evaluation strategy** names the quality dimensions, which are gating and which tracked, the datasets, the automation cadence and the exception rules, in a versioned document.
- A **release gate** is explicit, automatic where possible and owned. Gate on **coverage** as well as outcomes, so deleting cases cannot pass.
- For rates, gate on the **lower bound** of an interval; zero-tolerance applies to protective safety checks.
- **Exceptions** need a reason, accepted risk, compensating control, a non-requester approver and an **expiry**.
- **Dataset ownership**: versions, roles, append-only regression sets, a restricted held-out set and privacy handling for traffic samples.
- **Controls outside the model** prevent harm; evaluation estimates behaviour. Test the controls themselves.
- **Calibrate model graders** against human labels, weigh the false-pass rate for safety criteria, version the grader, and re-audit.
- **Document** intended use, limits, evidence and owners; show limits to users.
- Case studies in this chapter are teaching scenarios, not evidence about any real system.

## Exercises

**Exercise 1 — Write the strategy.** For an assistant you know, write a one-page evaluation strategy with a table like the one above: dimension, gating or tracked, method, cadence. Justify every "gating" row in one sentence.

**Exercise 2 — Run the gate.** Create `policy.json` and a `report.json` with category counts, then run `release_gate.py`. Produce each of these blocking messages in turn: too few total cases, a zero-tolerance failure, a lower-bound shortfall, a regression against a baseline.

**Exercise 3 — Exception lifecycle.** Write an exception record for a blocked `grounded_answer` check. Run the gate with it active, then change `expires` to yesterday and show that the block returns.

**Exercise 4 — Calibrate a grader.** Take 60 answers, label them yourself and with a colleague, then have a model grade them with a rubric. Build the confusion matrix, report agreement and false-pass rate, and decide whether the grader may gate a release, pre-filter for humans, or neither.

**Exercise 5 — Test the control.** Write at least six fake secrets in your own environment's formats and six harmless lookalikes. Run them through your output scanner. Fix a pattern until all twelve behave as expected.

**Exercise 6 — Documentation drill.** Fill in the one-page feature record for your assistant. Ask a colleague to find, using only that page, the owner, the date of the latest evaluation and the scope of what is excluded.

**Solution notes.**

*Exercise 1.* Check that each gating row has a method that can actually produce a decision automatically, and that at least one over-refusal dimension appears next to the refusal-accuracy one. A table with only safety dimensions will push the product toward refusing everything.

*Exercise 2.* Illustrative: `mutation_refusal` with 19 of 20 passing gives "1 failures, allowed 0". `grounded_answer` with 36 of 40 passing has a point estimate of 90% but a lower bound of about 76.9%, so it blocks at a 0.80 requirement. A baseline category that fell from 38/40 to 35/40 has dropped 7.5 points and blocks at a 3-point margin. Compute the lower bound yourself with the function to confirm.

*Exercise 3.* With the exception active, the gate prints `EXCEPTION applied` and does not list that check; with an expired date, the original message returns. Note that zero-tolerance checks in your policy should still need escalation by process, not just a file edit.

*Exercise 4.* Look first at the false-pass count, not the overall agreement. If agreement is high but false passes cluster on long or partially supported answers, add more of those to the sample and tighten the rubric. A grader whose false-pass rate is too high for the criterion's risk can still be useful as a *pre-filter* that routes suspicious answers to people.

*Exercise 5.* The usual surprise is a pattern that is too strict (misses a key with lowercase characters) or too loose (matches ordinary identifiers). The twelve cases are a regression set for the scanner.

*Exercise 6.* Every question the colleague has to ask is a missing line. Typical gaps: the exact dataset version, who approves exceptions, and which behaviours were never evaluated.
