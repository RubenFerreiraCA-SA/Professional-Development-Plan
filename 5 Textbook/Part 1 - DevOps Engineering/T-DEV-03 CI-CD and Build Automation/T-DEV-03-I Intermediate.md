# T-DEV-03-I — Intermediate Practice

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-i"></a>
#### T-DEV-03-I — Intermediate Practice

## Why this level exists

At Beginner level a pipeline is one job that runs tests. That is the right start, and it breaks down quickly. Real services need to run several kinds of checks, on more than one language version, in a sensible order, and then produce something that can be shipped. The questions change from "does the pipeline run?" to:

- Which jobs depend on which, and which can run in parallel?
- What is safe to *remember* between runs, and what must be *passed on* deliberately?
- Which tests belong on every pull request and which belong later?
- How do I build something once and know exactly which commit it came from?
- When the pipeline goes red, how do I find out *why* without guessing?

If a term below is unfamiliar, skim [T-DEV-03-B](T-DEV-03-B%20Beginner.md#t-dev-03-b) for the vocabulary (job, runner, artifact, required check) and return here.

## Pipelines are graphs, not lists

A pipeline's jobs form a **directed graph**: some jobs need the output or the success of others. Expressing those dependencies explicitly lets the platform run independent jobs in parallel and stop wasting work when an early step has already failed.

```text
          ┌──► lint ─────────┐
checkout ─┤                  ├──► gate (required check)
          ├──► unit-tests ───┤
          └──► build ──► integration-tests
```

In GitHub Actions syntax the edges are written with `needs`:

```yaml
jobs:
  lint:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - run: python -m ruff check .

  unit:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest tests/unit -q

  build:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - run: python -m build              # produces dist/*.whl and dist/*.tar.gz
      - uses: actions/upload-artifact@v4
        with: { name: dist, path: dist/ }

  integration:
    needs: [build]                         # only start if build succeeded, and may use its output
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: dist, path: dist/ }
      - run: pip install dist/*.whl && python -m pytest tests/integration -q
```

**Design rules for the graph**

1. **Run cheap, fast checks first, or in parallel.** A syntax error should not wait behind a ten-minute integration suite.
2. **Add `needs` only for a real dependency.** Every unnecessary edge makes the pipeline slower. A dependency exists when job B consumes job A's output, or when running B is pointless if A failed.
3. **Keep jobs independently re-runnable.** If you can re-run only `lint` after fixing a style issue, you save the cost of the rest.
4. **Fail fast, but not blindly.** Stopping everything on the first failure saves minutes; it also hides the other failures, so you fix one problem, push, and meet the next. For small suites that is fine. For long ones, let independent jobs finish so that one run reports all problems.

A trade-off worth stating plainly: **more jobs means more parallelism and finer failure messages, and also more runner start-up overhead, more configuration and more checks to manage.** A pipeline of thirty tiny jobs, each spending a minute installing dependencies, is slower than three sensible ones.

## Cache versus artifact: two different tools

These two are confused so often that it is worth building a clear model.

| | **Cache** | **Artifact** |
| --- | --- | --- |
| Purpose | Make future runs *faster* | *Carry a result* from one job to another, or out of the pipeline |
| Example | Downloaded dependency files | A built package, a test report, a container image digest |
| Correctness | **Must be optional**: the build must succeed, only slower, if the cache is empty | **Is required**: a consuming job fails without it |
| Keyed by | A hash of the inputs that make it valid (for example the lock file) | The workflow run, plus a name |
| Lifetime | May be evicted at any time (size or age limits) | Stored for a retention period you configure |
| Risk | **Stale or poisoned content** leaks between runs | **Substitution**: the consumer uses something other than what was produced |

The cache rule that prevents most problems: **a cache is a hint, never a source of truth.** If deleting the cache could change whether the build passes, you have hidden a real dependency inside it.

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ runner.os }}-${{ hashFiles('requirements.lock') }}
    restore-keys: |
      pip-${{ runner.os }}-
```

Read the key as a sentence: "this cache is valid for this operating system and *exactly this lock file*." When `requirements.lock` changes, the key changes, no exact match is found, and the job falls back to the broader `restore-keys` prefix (an older cache that is *probably mostly right*), downloads what is missing, and saves a new entry. Most language setup actions offer the same behaviour through a one-line option (for example `cache: pip` on the Python setup action), which is a good starting point.

**A worked failure.** A team caches the whole `node_modules` directory keyed only on the operating system. A developer upgrades a library in the lock file; CI restores the old `node_modules` and tests the *old* library. CI is green; production, which installs fresh from the lock file, breaks. The cache did not make the build faster; it made the build *wrong*. The fix is to key the cache on the hash of the lock file and to install from the lock file every time (the cache only speeds up the download).

Artifacts need their own discipline. Give each artifact a meaningful name, set a short retention period for transient ones (test reports, build outputs used by later jobs) and keep long-lived releases in a registry rather than in the run's artifact storage. Upload test reports **even when the job fails**, because that is when you need them:

```yaml
- run: python -m pytest -q --junitxml=reports/junit.xml
- uses: actions/upload-artifact@v4
  if: always()                      # run this step even after a failure
  with:
    name: junit-${{ matrix.python }}
    path: reports/
    retention-days: 7
```

## Test categories and where they belong

Not every test is the same kind of thing. A pipeline that treats them identically is either too slow or too weak.

| Category | What it checks | Typical speed | Depends on | Where it usually runs |
| --- | --- | --- | --- | --- |
| **Static checks** (lint, type check, format) | Style and some classes of bug, without running the code | Seconds | The source only | Every pull request, first |
| **Unit tests** | One function or class in isolation | Milliseconds each | Nothing external | Every pull request |
| **Integration tests** | Several components together, often with a real database or message broker | Seconds to minutes | Service containers | Every pull request, if it can be made fast; otherwise after merge |
| **Contract tests** | That a service's API matches what its consumers expect | Seconds | A shared contract definition | Every pull request that changes an interface |
| **End-to-end tests** | A whole system through its real entry point | Minutes | A complete environment | After merge, or on a schedule, before promotion |
| **Smoke tests** | That a deployed thing starts and answers a basic request | Seconds | A deployed environment | After deployment, as the first check on a release |

A widely used mental picture is the **test pyramid**: many fast, narrow tests at the bottom; fewer slow, broad ones at the top. The shape is a guide to cost, not a rule. A system that is mostly glue between services may deliberately have more integration tests. The question to ask is always: *what kind of mistake would this test catch, and is there a cheaper test that would catch it too?*

Integration tests need real dependencies, and CI can provide them as **service containers** that start alongside the job:

```yaml
  integration:
    runs-on: ubuntu-24.04
    services:
      db:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: ci-only-password    # a throwaway value for a throwaway database
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      DATABASE_URL: postgres://postgres:ci-only-password@localhost:5432/postgres
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest tests/integration -q
```

The `--health-*` options matter: without them, the tests may start before the database accepts connections and fail intermittently, creating a flaky test that is really a start-up race. The password is a disposable test value for a database that exists only for this job; it is not a real secret and it must never be reused for anything that is.

**Placement trade-off.** Putting more tests on the pull request gives faster *feedback to the author* and slower *throughput for everyone*. Putting them after merge does the reverse and means a failure arrives when the change is already in the shared branch. A reasonable compromise: keep the pull-request lane under roughly ten minutes (your own budget may differ), run the slow tests on the protected branch, and make a failure there **block promotion** and notify the author. A slow lane whose failures nobody acts on is not a safety net; it is a log file.

## Matrix builds: one definition, many environments

If your software must work on several language versions or operating systems, writing a job for each is repetitive and drifts. A **matrix** generates jobs from a list of values:

```yaml
  test:
    strategy:
      fail-fast: false                    # let every combination finish, so one run reports all problems
      matrix:
        os: [ubuntu-24.04, windows-2022]
        python: ["3.11", "3.12"]
        exclude:
          - os: windows-2022
            python: "3.11"                # a combination we do not support
        include:
          - os: ubuntu-24.04
            python: "3.13"
            experimental: true            # an extra leg with an extra variable
    runs-on: ${{ matrix.os }}
    continue-on-error: ${{ matrix.experimental == true }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "${{ matrix.python }}" }
      - run: pip install -r requirements.txt
      - run: python -m pytest -q
```

This defines four jobs (2 × 2 minus 1 excluded, plus 1 included), each named by its values. Three things to know:

1. **Matrix size multiplies.** A matrix of 3 operating systems × 4 versions × 3 database versions is 36 jobs per run. Decide which combinations you *promise to support* and test those; do not test the whole cartesian product by default.
2. **Each leg has its own check name.** If you mark individual legs as required, then changing the matrix renames checks and branch protection silently stops matching. The cleaner design: one **gate job** that `needs` the matrix and is the only required check (shown below).
3. **`continue-on-error` for experimental legs** lets you watch a new version without blocking merges, but only if someone *looks* at it. An experimental leg that has been red for months is noise; either fix it or remove it.

## Environment differences: why "it passed in CI" is not the whole story

CI environments differ from production in predictable ways. Knowing the common ones helps you diagnose faults and decide what extra checks you need.

| Difference | How it causes trouble | Defence |
| --- | --- | --- |
| Operating system and libraries | Code works with one C library or file-system behaviour (case sensitivity, path separators) and not another | Test on the production-like OS; use the same base image in CI and production |
| Dependency versions | CI resolves "latest compatible", production resolves a different set | Lock files with hashes; install exactly from them |
| Configuration and secrets | A setting present on laptops and absent in CI, or vice versa | Document required configuration; fail loudly when missing; keep defaults for tests explicit |
| Data volume and shape | Tests use tiny fixtures; production has millions of rows and odd values | Keep a few realistic-shape fixtures; add performance checks where relevant |
| Network and time | Tests call real services or depend on the clock | Replace with fakes or controlled clocks; allow only declared network access |
| CPU, memory and parallelism | A race condition appears only under load or on more cores | Run concurrency-sensitive tests repeatedly; use realistic runner sizes |

Two habits cover most of this ground. **Build in the environment you ship:** if production runs a container, run the tests inside that same image. **Make configuration an explicit input:** the application reads settings from environment variables with documented names, so CI, local and production differ only in values, never in code paths.

## Trust stages: what each part of the pipeline may do

Think in stages with different privileges. This is the most important structure in the chapter, because it decides what an attacker or a mistake can reach.

| Stage | May run untrusted code? | May publish artifacts? | May deploy? |
| --- | --- | --- | --- |
| Pull-request validation | Yes, in isolation | No | No |
| Post-merge release | Only code from the protected branch | Yes, with a narrow token | Optional or separate |
| Promotion | No application build | No rebuild | Yes, by digest only |

The first row exists because anyone who can open a pull request can propose changes to the code *and to the workflow*. The validation job must therefore be safe to run on code you have not yet trusted: read-only token, no deployment secrets, no publishing. The second row runs only after review and merge, so the code is the code your organisation agreed to ship. The third row *moves* an already-built artifact; it never builds one, which keeps "what was tested" and "what was shipped" the same object.

**Deterministic validation.** Inside the first stage: pin dependencies (ideally a lock file with hashes), run lint and tests on a clean runner, upload reports even on failure, fail the required check on regression, and never push images or use deployment secrets there. Write reports to a temporary directory outside the checkout so the working tree stays clean, and so a later "is the tree dirty?" check can detect generated files that someone forgot to commit.

## Path filters and the required-check trap

In a repository with several components, running everything for every change is wasteful. **Path filters** skip workflows when only unrelated files change. They also create a classic trap:

- If a whole *workflow* is skipped by a path filter, the checks it would have reported never appear. A **required** check that never reports stays "expected" forever, and the merge is blocked even though nothing is wrong.
- If instead a *job* is skipped by an `if:` condition, the platform reports it as success. That unblocks the merge but can hide a run that should have happened.

The resolution is one **always-running gate job** that computes what changed, then verifies that every job that *should* have run did run and succeeded:

```yaml
jobs:
  changes:
    runs-on: ubuntu-24.04
    outputs:
      app: ${{ steps.f.outputs.app }}
    steps:
      - uses: actions/checkout@v4
      - id: f
        uses: dorny/paths-filter@v3
        with:
          filters: |
            app: ['app/**', 'tests/**', 'requirements*.txt']

  test:
    needs: changes
    if: needs.changes.outputs.app == 'true'
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - run: python -m pytest -q

  gate:
    if: always()                           # run even when upstream jobs failed or were skipped
    needs: [changes, test]
    runs-on: ubuntu-24.04
    env:
      CHANGES_RESULT: ${{ needs.changes.result }}
      TEST_RESULT: ${{ needs.test.result }}
      APP_CHANGED: ${{ needs.changes.outputs.app }}
    steps:
      - run: |
          [ "$CHANGES_RESULT" = "success" ] || { echo "path detection failed"; exit 1; }
          if [ "$APP_CHANGED" = "true" ]; then
            [ "$TEST_RESULT" = "success" ] || { echo "tests were required but result is $TEST_RESULT"; exit 1; }
          fi
```

Mark only `gate` as required. Notice what the logic refuses to accept: a **skipped** test job is acceptable *only if the filter said nothing relevant changed*. The same pattern extends to a matrix, because the gate's `needs.test.result` summarises every leg.

(The third-party `dorny/paths-filter` action is referenced by version tag here for readability. Professional level explains why production pipelines pin such actions to a full commit hash.)

## Build once: publishing a package or an image

After checks pass on the protected branch, the pipeline produces the thing you ship. The principle: **build once, record exactly what you built, and reuse that same artifact everywhere.** Rebuilding the same commit separately for staging and production gives you two different artifacts that merely *look* equivalent: timestamps, resolved dependencies and base-image updates can differ.

A release workflow for a container image, with a narrow token:

```yaml
name: release
on:
  push:
    branches: [main]

permissions:
  contents: read
  packages: write                          # needed to push to the registry; nothing broader

jobs:
  publish:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/example-org/orders-api:${{ github.sha }}
          labels: |
            org.opencontainers.image.source=https://github.com/example-org/orders-api
            org.opencontainers.image.revision=${{ github.sha }}
      - name: Record what was built
        env:
          DIGEST: ${{ steps.build.outputs.digest }}
        run: |
          echo "commit=${GITHUB_SHA} digest=${DIGEST} run=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}" | tee -a "$GITHUB_STEP_SUMMARY"
```

Why a *digest*? A **tag** such as `orders-api:1.4` is a movable label; someone can push a different image under the same tag. A **digest** (`sha256:...`) is a hash of the image content; it cannot refer to different content. Tags are for humans; digests are for machines and for trust.

If you publish a library or package rather than an image, the same ideas hold: build it once from the protected branch, publish it with an immutable version number (never overwrite a released version), and record which commit it came from.

## Traceability: from a running thing back to a commit

Traceability is the ability to answer, for anything running in production: *which commit, built by which run, tested by which checks, approved by whom?* It is how incident responders, auditors and your future self navigate. Build it into the pipeline rather than reconstructing it afterwards.

A minimal chain has four links, each one recorded at the point the information exists:

| Link | Recorded where | Written by |
| --- | --- | --- |
| Pull request → commit | Merge commit or squash commit on the protected branch | The hosting platform |
| Commit → build run | Workflow run URL, linked to the commit's checks | The pipeline |
| Build run → artifact digest | Release evidence line and image labels | The release job |
| Digest → environment | The promotion record (for example, a pull request that changes the digest in a deployment file) | The promotion process |

You can test the chain. Pick an image running in a test environment and try to answer: what is its digest, what commit label does it carry, which workflow run built it, and what review approved that commit? If any answer takes more than a few minutes of searching, a link is missing.

```bash
# Inspect labels of a published image (illustrative)
docker buildx imagetools inspect ghcr.io/example-org/orders-api@sha256:3f1c...e9a0 --format '{{json .}}'
```

## Promote by digest

Promotion changes a pointer, not the source:

```text
# deploy/orders-api/image-ref.txt
registry.example.com/orders-api@sha256:3f1c...e9a0
```

A pull request that changes only this line promotes an existing, tested artifact. Reviewers see a one-line diff, the pipeline can verify that the digest exists and was built by the release workflow, and rollback is another one-line change back to the previous digest. A small guard script rejects anything that is not exactly one reference with `@sha256:` followed by 64 hexadecimal characters, so `:latest` and tag-only references fail the check automatically:

```bash
#!/usr/bin/env bash
set -euo pipefail
ref_file="deploy/orders-api/image-ref.txt"
count=$(grep -cve '^\s*$' "$ref_file")
[ "$count" -eq 1 ] || { echo "expected exactly one image reference, found $count"; exit 1; }
grep -Eq '^[a-z0-9./_-]+@sha256:[0-9a-f]{64}$' "$ref_file" \
  || { echo "reference must be name@sha256:<64 hex>"; exit 1; }
```

## Flaky tests

A **flaky test** passes and fails on the same code. Each flake teaches the team that red does not mean broken, which is the single most damaging habit a pipeline can create. Common causes and fixes:

| Cause | Example | Fix |
| --- | --- | --- |
| Time | A test compares to "today" and fails at midnight | Inject a clock; fix the time in tests |
| Ordering | Passes alone, fails after another test left data behind | Isolate state per test; randomise order to expose it |
| Shared state | Two tests write the same file or table | Unique temporary resources per test |
| Network | A test calls a real external service | Replace with a fake; allow only local dependencies |
| Start-up races | Test starts before the database is ready | Health checks and bounded waits |
| Resource limits | Timeouts that are fine on a laptop and tight on a small runner | Measure; set honest timeouts, not arbitrary retries |

Retrying blindly hides real intermittent faults, including real race conditions in your product. If you must work around a flaky test, **quarantine it explicitly**: move it to a separate, visible lane, record an owner and an expiry date, and track it until it is fixed or deleted.

## Diagnosing failures by class

When a pipeline goes red, do not re-run it. **Classify, then act.** The first question is always: *did the failure come from my change, from the environment, or from the test itself?*

| Class | Typical symptom | How to confirm | Response |
| --- | --- | --- | --- |
| Test regression | Red job with a clear assertion and traceback | Reproduce locally with the same command | Fix code or test |
| Dependency install failure | Early `pip` or `npm` error, "no matching version" | The failing line is in the install step; compare the pin with the registry | Fix the pin; do not retry forever |
| Cache inconsistency | CI disagrees with local; clean run passes | Re-run with the cache disabled or key changed | Make installs deterministic; fix the key |
| Registry or permission failure | `denied` or `403` on push in release | Check the token's permissions and the trigger (is this a PR job that should not have the secret?) | Fix the identity; do not widen validation jobs |
| Environment drift | Passes on one operating system or version only | Compare matrix legs | Fix the code or drop an unsupported leg |
| Infrastructure fault | Runner lost, network timeout in a download | The same commit passes on re-run and the failure is in setup, not tests | A single, recorded re-run is reasonable; if it recurs, investigate |
| Bad promotion | Reference rejected by the guard | Guard output names the rule | Pin `@sha256:` |
| Flaky test | Passes on re-run with no change | Search history for the same test name failing and passing | Quarantine with owner and expiry; then fix |

**A worked diagnosis.** A pull request turns red with this log (illustrative):

```text
Run python -m pytest tests/integration -q
E   psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused
1 failed, 14 passed in 3.04s
```

Reasoning, step by step:

1. **Which step failed?** The integration tests, not install or lint. The code compiled and 14 tests passed.
2. **What does the message say?** "Connection refused" means nothing was listening on the port at that moment. It does not say the query was wrong or the schema broke.
3. **Is it my change?** Check what the pull request touched. If it only edited documentation, a code regression is unlikely.
4. **Is it flaky or deterministic?** Look at recent runs: if the same job failed once last week with the same message and passed on re-run, suspect a start-up race.
5. **Look at the setup.** The service container has no health check, so the tests can begin before the database is ready.
6. **Fix the cause, not the symptom.** Add the health options shown earlier. Do not merely add a retry loop to the test.

The process matters more than the specific fault. You identified the failing stage, read the message literally, formed a hypothesis from the setup, and chose a fix that makes the *system* reliable.

## Common mistakes

| Mistake | Consequence | Better practice |
| --- | --- | --- |
| Caching without keying on the lock file | CI tests stale dependencies | Key on `hashFiles` of the lock file; always install from it |
| One giant job | Slow, hard to re-run, vague failures | Split by purpose; connect with `needs` |
| Required checks on individual matrix legs | Checks go "expected" forever after a matrix change | Require one gate job |
| Rebuilding per environment | Staging and production run different artifacts | Build once; promote the digest |
| Pushing images from pull-request jobs | Untrusted code can publish | Publish only from the protected branch workflow |
| Mutable tags for deployment | The same name refers to different things over time | Deploy by digest |
| Retrying until green | Real bugs hide | Classify; retry once only for proven infrastructure faults, and record it |
| No traceability record | Cannot connect production to a commit during an incident | Record commit, digest and run URL at publish time |

## Knowledge consolidation

- A pipeline is a graph; **`needs` expresses real dependencies** and unlocks parallelism.
- **Caches speed things up and must be optional; artifacts carry results and are required.** Never let a cache decide correctness.
- Test categories differ in cost and in the mistakes they catch; place them where feedback is fast and failures still matter.
- A **matrix** tests a promise of support; resolve its many checks into one **gate**.
- Validation, release and promotion are **different trust stages**, with decreasing exposure to untrusted code.
- **Build once, record the digest, promote the digest.** Tags are for people.
- Diagnose failures by **class** before acting; re-running is not a diagnosis.

## Exercises

**Exercise 1 — Graph and cache.** Extend your Beginner workflow into separate `lint`, `unit` and `integration` jobs with `needs` where genuinely required. Add a dependency cache keyed on a lock file. Run the pipeline three times: cold cache, warm cache, and after changing one dependency. Record the durations and which runs hit the cache.

**Exercise 2 — Matrix and gate.** Add a matrix of two language versions, then add a `gate` job as the only required check. Change the matrix (add a third version) and confirm that branch protection still works without being edited.

**Exercise 3 — Path filter trap.** Add a path filter that skips the tests when only `docs/**` changes. First mark `test` itself as required and open a documentation-only pull request; observe what happens. Then introduce the gate job and repeat.

**Exercise 4 — Fault injection.** Inject two *different* faults on disposable branches (choose from: a bad pin, a cache key that ignores the lock file, a missing service health check, a mutable tag in the promotion file). Diagnose each from the logs alone and write a short failure report with: symptom, class, evidence, fix, and what would have prevented it.

**Exercise 5 — Traceability drill.** Publish an image from the release workflow, then, using only the registry and the repository, answer: which commit built this digest, which run, and which pull request introduced the commit? Time yourself and note the slowest link.

**Solution notes (Exercise 1).** Expect the cold run to be slowest, the warm run faster by roughly the cost of downloading dependencies (the size of the saving depends on your dependency set and network; measure rather than assume), and the third run to restore from `restore-keys` and then save a new entry. If the warm run does not report a cache hit, check that the key's inputs are identical between runs (a different runner OS label is a common cause). The check that matters most: delete the cache manually and confirm the pipeline still *passes*; if it does not, the cache was masking a real dependency.

**Solution notes (Exercise 2).** With only `gate` required, adding a third version changes the number of matrix legs but not the required check name, so merges are neither blocked nor silently unprotected. If you required individual legs, the old leg names disappear when you edit the matrix and the platform waits forever for them. If your gate passes while a leg is red, check that it lists the matrix job in `needs` and has `if: always()`; without `always()` the gate is itself skipped when a dependency fails, and a skipped required job may be treated as passing.

**Solution notes (Exercise 3).** With `test` itself required and its whole workflow filtered out by path, the pull request shows the check as expected and cannot merge, even though nothing is wrong. With the gate job in a workflow that always starts and a job-level condition inside it, the documentation-only pull request reports success because the gate sees "no relevant change". The follow-up question to answer: what happens if the filter's patterns are wrong and miss a directory that contains code? (The gate would pass without tests. Keep patterns broad, and run a periodic full run as a backstop.)

**Solution notes (Exercise 4).** A good report is specific. For a missing health check: *Symptom* — integration job failed with "connection refused" in 1 of several recent runs. *Class* — start-up race, a flake of environmental origin. *Evidence* — the failing step began before the service reported healthy; other runs passed. *Fix* — add health options. *Prevention* — a template for service containers that includes health checks. For a cache key ignoring the lock file: *Symptom* — CI passed but a fresh install failed. *Class* — cache inconsistency. *Evidence* — a run with the cache cleared failed. *Fix* — key on `hashFiles`. For a mutable tag: the guard script should have rejected the line; if it did not, fix the guard and add a test case for that input.

**Solution notes (Exercise 5).** The expected chain: digest → image labels or release evidence line → commit SHA → pull request listed on the commit page → reviewers. The slowest link is usually between digest and run, when the evidence line was only printed in a log and not stored anywhere searchable. Remedy: write the evidence to the job summary and, for important releases, to an artifact or a release record that outlives log retention.
