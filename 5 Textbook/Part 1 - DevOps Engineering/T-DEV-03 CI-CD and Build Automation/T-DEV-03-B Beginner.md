# T-DEV-03-B — Beginner Foundations

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-b"></a>
#### T-DEV-03-B — Beginner Foundations

## Why this matters

Imagine a team of four people working on one service. Each person builds and tests on their own laptop. One has a newer language version than the others. One forgets to run the tests before sharing a change. One has a file on disk that was never committed, so the code works for them and nowhere else. On Friday afternoon someone builds the release by hand, on their own machine, following steps they half remember. On Monday something is broken in production and nobody can say with confidence which source code, built on which machine, with which dependency versions, is actually running.

None of those people did anything unusual. The problem is structural: **the steps that decide whether a change is acceptable depend on the memory and the machine of whoever happens to perform them.** Automation removes that dependence. A *pipeline* is a written-down, executable description of the steps — build, check, package — that runs the same way for every change, on a clean machine, and reports the result in a place where reviewers will see it.

This Beginner section assumes you can use Git and have opened a pull request (see [T-DEV-01-B](T-DEV-01-B%20Beginner.md#t-dev-01-b) if not). It does **not** assume you have ever written a pipeline. The examples use GitHub Actions syntax because it is widely used and easy to read, but every idea transfers to GitLab CI, Jenkins, Buildkite, CircleCI and others; only the file format changes.

## First principles: what problem does integration solve?

Software is rarely written in one piece by one person. Several people change the same codebase at once, each on a branch. *Integration* is the moment their changes meet. The longer changes stay apart, the more they drift, and the more painful and surprising the meeting becomes. Teams used to integrate rarely (weekly, monthly, before a release) and then spend days finding out which combination of changes broke things.

**Continuous integration** inverts that: integrate small changes often, and **check every integration automatically**. The word "continuous" does not mean "running every second". It means *every change is checked as it arrives, without anyone having to remember*.

A useful way to see why this works is to think about the cost of finding a bug:

| When a bug is found | What you still remember | Who is affected | Typical effort |
| --- | --- | --- | --- |
| Minutes after the commit, in the pull request | Everything — you just wrote it | Only you | Small: you know exactly where to look |
| Days later, after merge | Some of it | Anyone who pulled the branch | Medium: you must re-read your own change |
| Weeks later, in a release | Little | The release schedule | Large: many changes are suspects |
| In production | Almost nothing | Users | Largest: includes incident cost |

The table is a model, not a measurement. Its point is directional: **a pipeline moves the discovery of mistakes as early and as close to the author as possible.**

## CI, continuous delivery and continuous deployment are different things

Three phrases are often blurred together. Keeping them apart helps you reason about risk.

| Term | What is automated | What a human still decides | Typical output |
| --- | --- | --- | --- |
| **Continuous integration (CI)** | Build and test every proposed or merged change | Whether to merge | A pass/fail result on the change |
| **Continuous delivery** | Producing a release-ready, verified artifact after merge, and making it deployable at any time | *When* to release to production | A versioned artifact that is ready to ship |
| **Continuous deployment** | Releasing every verified change to production automatically | Nothing per release; humans design the gates in advance | Production updated after each passing merge |

The abbreviation "CD" is used for both the second and third rows, which is why conversations about it get confused. When someone says "we do CD", ask: *after the tests pass, does a person press a button, or does it ship by itself?*

Neither version is "more correct". Continuous deployment is only responsible when the automated checks, the rollout method and the ability to undo a release are trustworthy. Many teams reach continuous delivery first, with an approval step before production, and stay there for good reasons (regulatory approval, coordination with other teams, expensive failures). This chapter's Beginner level concentrates on CI, because CD without reliable CI just ships mistakes faster.

An analogy, and where it breaks: CI is like a quality inspector standing at the end of an assembly line who checks each item as it comes off. Delivery is putting the checked item in the warehouse, ready to ship. Deployment is shipping it to a customer. The analogy breaks because in software the inspector is a script that can run in minutes for the price of a few CPU seconds, so you can inspect *every* item, not a sample.

## Anatomy of a pipeline

Before reading any configuration file, learn the nouns. Each one answers a different question.

| Term | Question it answers | Meaning in practice |
| --- | --- | --- |
| **Commit** | What changed? | A recorded snapshot of the code, identified by a hash. Pipelines run *for* a specific commit. |
| **Event / trigger** | When does automation start? | Something that happened: a pull request was opened, a branch was pushed to, a tag was created, a schedule fired. |
| **Workflow / pipeline** | What is the whole process? | A definition (usually a file in the repository) of jobs to run when a trigger fires. |
| **Job** | What is one unit of work? | A group of steps that runs on one machine, for example "run the tests". Jobs may run in parallel or in order. |
| **Step** | What is one action? | A single command or reusable action inside a job, such as "install dependencies". |
| **Runner** | Where does it run? | The machine (often a short-lived virtual machine or container) that executes a job. |
| **Artifact** | What did it produce? | A file or image produced by a job: a test report, a package, a container image. |
| **Check / status** | What is the verdict? | A pass/fail signal attached to the commit that the hosting platform shows to reviewers. |
| **Required check** | What may block a merge? | A check that branch protection says must pass before the change can be merged. |

Two relationships matter most for beginners:

1. **The workflow file lives in the repository, so it is reviewed like code.** That is a feature (history, review, rollback) and a risk (a malicious change to the workflow is a change to your automation). Later levels return to this.
2. **A runner starts clean.** Nothing from your laptop is there: not your installed packages, not your uncommitted files, not your environment variables. If the pipeline passes on a clean runner, the build does not secretly depend on your laptop. If it fails there but passes locally, that is the pipeline *telling you something true* about hidden dependencies.

## A first pipeline, annotated

Here is a minimal pull-request validation workflow, with a comment on every decision that matters. Read it as a series of answers to the vocabulary above.

```yaml
# .github/workflows/validate.yml
name: validate                       # label shown in the checks list

on:                                  # WHEN: the trigger
  pull_request:                      #   run for every pull request that is opened or updated
    branches: [main]                 #   ...that targets main

permissions:                         # WHAT IT MAY DO: the token given to this workflow
  contents: read                     #   read the repository; nothing else, no writing

concurrency:                         # avoid wasted runs
  group: validate-${{ github.ref }}  #   one run per branch at a time
  cancel-in-progress: true           #   a newer push replaces the older, now-obsolete run

jobs:
  test:                              # a job named "test"; this name becomes the check name
    runs-on: ubuntu-24.04            # WHERE: a clean, pinned operating-system image
    timeout-minutes: 10              # a hung job should fail, not run for hours
    steps:
      - uses: actions/checkout@v4    # fetch the code at the commit under test
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"     # a specific version, not "whatever is installed"
      - run: pip install -r requirements.txt   # dependencies from a pinned list
      - run: python -m pytest -q     # the verdict: non-zero exit code means failure
```

Walk through it slowly.

**The trigger.** `pull_request` means the workflow runs for proposed changes, *before* they merge. That is the right moment: the cost of failure is a red mark on a review, not a broken main branch.

**The permission block.** Without it, the workflow gets whatever default your organisation configured, which might include write access. Writing `contents: read` states the intent in code: *this job inspects the repository; it does not change anything.* A validation job has no business publishing, deploying, or editing issues. Starting with the smallest possible permission and adding only what a job demonstrably needs is called **least privilege**, and it is the single most useful security habit in pipelines.

**The concurrency block.** If you push three commits in a minute, you want results for the third, not three parallel runs of which two are already obsolete. This saves runner time without changing what is checked.

**The timeout.** A job that waits forever for a network call blocks developers and costs money. A timeout converts "stuck" into "failed", which is an actionable state.

**Pinned runner and language version.** `ubuntu-24.04` rather than `ubuntu-latest` means the operating system does not change underneath you on a date you did not choose. Pinning has a cost — someone must update it deliberately — and a benefit: failures are caused by your changes, not by an unannounced platform upgrade.

**The verdict.** Each step either exits with status 0 (success) or non-zero (failure). The first failing step stops the job and marks the check red. Nothing more magical is happening. A test runner returns non-zero when a test fails; the pipeline faithfully reports that.

A note on `uses: actions/checkout@v4`. This line pulls a reusable step written by someone else, and `@v4` means "the latest version in the v4 line", which can change. For official actions maintained by the platform that trade-off is commonly accepted at beginner level. For third-party actions, Professional and Expert levels explain why teams pin to an exact commit hash instead.

## Make the code testable first

CI cannot check what has no checks. Before you automate, there must be something to run. A tiny service with a function and a health endpoint is enough:

```python
# app/pricing.py
def order_total(prices: list[float], discount_percent: float = 0.0) -> float:
    """Sum the prices, then apply a percentage discount."""
    subtotal = sum(prices)
    return round(subtotal * (1 - discount_percent / 100), 2)
```

```python
# tests/test_pricing.py
from app.pricing import order_total

def test_total_without_discount():
    assert order_total([10.0, 5.5]) == 15.5

def test_total_with_discount():
    assert order_total([100.0], discount_percent=10) == 90.0

def test_empty_order_is_zero():
    assert order_total([]) == 0.0
```

And a check for a web endpoint:

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

def test_health_ok():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
```

Run the tests locally *first*:

```bash
python -m pytest -q
```

If the tests do not pass on your laptop, wiring them into CI only moves the confusion to a web page. Local first; then automate.

Notice what a good beginner test is: **small, fast, deterministic, and checks one behaviour**. "Deterministic" means that running it twice on the same code gives the same answer. A test that depends on the current time, random numbers or a live network service is *non-deterministic* and will eventually fail for reasons that have nothing to do with your change. Those failures train people to ignore red builds, which defeats the whole purpose (the Intermediate level calls this a *flaky test*).

## A failing validation that blocks a merge

The most important thing to see once with your own eyes is **a red check stopping a bad change**. Follow this story on a practice repository.

**Step 1: a change that looks harmless.** A teammate "simplifies" the pricing function and accidentally applies the discount in the wrong direction:

```python
# app/pricing.py  (on branch feature/simplify-pricing)
def order_total(prices: list[float], discount_percent: float = 0.0) -> float:
    subtotal = sum(prices)
    return round(subtotal * (1 + discount_percent / 100), 2)   # sign error
```

The code is valid Python. It runs. A manual glance at the diff might not catch a `-` turned into a `+`. Reviewers are human and the diff is small.

**Step 2: the pipeline runs.** The pull request triggers `validate`. The job log shows the relevant failure (illustrative output):

```text
tests/test_pricing.py::test_total_with_discount FAILED

    def test_total_with_discount():
>       assert order_total([100.0], discount_percent=10) == 90.0
E       assert 110.0 == 90.0

1 failed, 3 passed in 0.12s
Error: Process completed with exit code 1.
```

Read the log from the bottom up: the last line says *which step failed* and with what exit code; the lines above say *what was expected, what was observed*. Here the test expected 90 and the code returned 110. The mistake is not a mystery; the log points at it.

**Step 3: the platform blocks the merge.** The pull request shows `test — failing`. If the `test` check has been marked **required** in branch protection (or a ruleset), the merge button is disabled with a message such as "Required status check is expected" or "Merging is blocked". The author fixes the sign, pushes, and the check re-runs on the new commit and turns green. Only then can the change merge.

**Step 4: what you have just proven.** Three separate things had to be true for this to work, and each can silently fail:

1. The test existed and covered the behaviour. (If it did not, the pipeline would be green and wrong.)
2. The workflow ran on the pull request. (A trigger typo would leave no check at all.)
3. The check was *required*. (If not required, a red mark is only advice and someone in a hurry can merge anyway.)

A pipeline is only as strong as the weakest of those links. That is why the exercise at the end of this section asks you to *break a test on purpose* and confirm the merge is blocked. A control you have never seen fail is a control you do not know works.

## What the pipeline cannot tell you

CI is powerful but narrow. Be clear about its limits so you do not over-trust a green tick.

- **Green means "the checks I wrote passed", not "the code is correct".** If no test describes a behaviour, no test can notice that it broke.
- **Green on a runner means "works on that runner".** Differences in operating system, data volume, network or configuration can still bite in production. Later levels handle environments and matrix builds.
- **A pipeline can only enforce rules it is told about.** It does not review design, judge readability or notice a missing feature.
- **A pipeline is code with privileges.** If someone can alter the workflow file and the platform runs that file with secrets, they can read those secrets. This is why validation jobs have *no* publishing credentials.

## Trade-offs you will meet immediately

| Decision | Leaning toward speed | Leaning toward thoroughness | A reasonable starting point |
| --- | --- | --- | --- |
| Which tests on every pull request | Only unit tests, under a few minutes | Everything, including slow end-to-end suites | Fast unit tests on each pull request; slower suites after merge or on a schedule, provided their failures still matter |
| Pinning versions | Floating versions: fewer updates to manage | Exact versions: identical builds, deliberate upgrades | Pin; schedule reviewed updates |
| Retrying failed jobs | Retry quickly: unblock people | Never retry: every failure is investigated | Retry never *silently*; fix flaky tests rather than hiding them |
| Strictness of required checks | Few required checks: easy merges | Many required checks: strong gate | Require the checks whose failure should truly stop a merge |

There is no single right answer. The aim of this table is for you to *make* those choices on purpose rather than inherit them by accident.

## Common mistakes and how they look

| Mistake | How it looks | What to do instead |
| --- | --- | --- |
| Tests pass locally, fail in CI | A missing file, a missing dependency, a different version | Treat CI as correct: make the dependency explicit in the pinned list or the repository |
| Re-running a failed job until it passes | Same commit, three runs, green on the third | Investigate the failure; if the test is flaky, fix or quarantine it openly |
| Giving the validation job a publishing token | A `REGISTRY_PASSWORD` secret available to pull-request jobs | Remove it; publish from a separate workflow that runs only on the protected branch |
| Forgetting to mark the check as required | Red check, but the merge button is still green | Add the job to branch protection's required checks |
| Check never starts | No status appears on the pull request | Look at the trigger, the file path (`.github/workflows/`) and the branch filter |
| Unpinned dependencies | Passes on Monday, fails on Tuesday with no code change | Use a lock file or a pinned requirements list |
| Secrets in the repository | A key printed in a log or committed to a file | Remove, rotate, and keep secrets in the platform's secret store |
| Very slow validation | Developers batch changes to avoid waiting | Split fast checks from slow ones; cache dependency downloads |

## Rules of thumb

1. **Install from pinned dependencies** so today's build matches yesterday's.
2. **Run in a clean environment**, never on a developer's machine.
3. **Keep fast tests on every pull request;** run slower suites later without letting their failures be ignored.
4. **A failing required check blocks merge;** do not "retry until green".
5. **Never give a validation job credentials to publish or deploy.**
6. **Read logs from the bottom up** and name the failure before changing anything.
7. **Prove each control once** by making it fail on purpose.

## Knowledge consolidation

- A pipeline replaces *someone's memory and machine* with a written, repeatable process on a clean runner.
- **CI** checks every change; **delivery** keeps a verified artifact ready to release; **deployment** actually releases it. They are different decisions with different risks.
- The vocabulary — commit, trigger, workflow, job, step, runner, artifact, check — maps onto concrete lines in a file and concrete objects in the platform.
- A red check is only a gate when it is **required**; a required check is only meaningful when the test behind it **tests something**.
- Permissions are part of the design: a validation workflow reads, it does not write.
- Green means "the checks I wrote passed", nothing more.

## Exercises

**Exercise 1 — Guided build.** Create a practice repository containing the `order_total` function, the three tests above and a `requirements.txt` that lists `pytest` with a pinned version. Add `.github/workflows/validate.yml` as shown. Open a pull request with a trivial documentation change and confirm that the `test` check runs and passes. Then mark `test` as a required check in branch protection.

**Exercise 2 — Prove the gate.** On a new branch, introduce the sign error from the example. Open a pull request. Record: (a) the exact line of the log that names the failing test, (b) what the expected and actual values were, (c) what the merge button shows. Fix the error, push and record what changed on the pull request without you doing anything else.

**Exercise 3 — Break it three other ways.** On disposable branches, cause each of these and write one sentence on how the pipeline presented it: (a) misspell a package name in `requirements.txt`; (b) change the trigger from `pull_request` to `push` only; (c) add a test that fails only on the second run (for example by writing to and reading from a temporary file in a way that depends on prior state). Which of the three produced *no* check at all, and why is that the most dangerous?

**Exercise 4 — Transfer.** Explain to a colleague, without notes, the difference between continuous integration, continuous delivery and continuous deployment, using a real service you know. Say which one that service has today and what it would take to reach the next.

**Solution notes (Exercise 1).** Expect a green `test` check under the pull request. If the check does not appear, the usual causes are: the file is not in `.github/workflows/`, the YAML is invalid (the Actions tab shows a parse error), or the target branch is not `main` and the `branches` filter excluded it. When marking the check required, note that the check name offered in the settings appears only *after* the job has run at least once; that is expected, not a bug.

**Solution notes (Exercise 2).** The log should show `assert 110.0 == 90.0`, which tells you the discount increased the total. The merge button will be disabled or flagged as blocked by a required status check. After you push a fix, the pipeline re-runs on the *new* commit automatically; the earlier red result is attached to the old commit and remains in the history, which is correct. If the merge button stayed enabled, the check was not marked required: return to branch protection.

**Solution notes (Exercise 3).** (a) A misspelled package fails very early, in the `pip install` step, with a "no matching distribution" style message; the fix is in the pin, not in retrying. (b) With the trigger changed to `push` only, the workflow runs on pushes to branches in the repository but not as a pull-request check, so **no check appears on the pull request**; it looks "clean" because nothing reported a failure. This is the most dangerous case because absence of a red mark is indistinguishable from success. If the check is required, the merge stays blocked with the check shown as "expected", which is a safe failure; if it is optional, the control silently vanishes. (c) A test that depends on state left by a previous run passes the first time and fails the next, which is the shape of a flaky test; the right response is to make the test independent (create its own temporary directory) rather than re-run it.

**Solution notes (Exercise 4).** A good answer names the human decision point. For example: "After merge, the pipeline builds and publishes an image, but a person approves the production rollout: that is continuous delivery. To reach continuous deployment we would need automated rollout health checks and a tested rollback, so that no person is needed to protect users."
