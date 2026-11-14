# T-DEV-03-I — Intermediate Practice

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-i"></a>
#### T-DEV-03-I — Intermediate Practice

**Delivery stages and trust.** Think in three stages with different privileges:

| Stage | May run untrusted code? | May publish artifacts? | May deploy? |
| --- | --- | --- | --- |
| Pull-request validation | Yes, in isolation | No | No |
| Post-merge release | Only code from the protected branch | Yes, with a narrow token | Optional or separate |
| Promotion | No application build | No rebuild | Yes — by digest only |

**Deterministic validation.** Pin dependencies (ideally with a lock file and hashes), run lint and tests in a clean runner, upload reports even on failure, fail the required check on regression, and never push images or use deployment secrets in this job. Write reports to a temporary directory outside the checkout so the working tree stays clean.

**Path filters and required checks (the monorepo trap).** Path filters save minutes by skipping workflows when only unrelated files change. But a *required* check that never ran stays "pending" forever and blocks the merge, while a skipped job reported as success can hide a missing run. The resolution is a single always-running gate job that computes what changed and fails if any needed job failed or was skipped by mistake:

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
            app: ['app/**', 'requirements*.txt']
  test:
    needs: changes
    if: needs.changes.outputs.app == 'true'
    runs-on: ubuntu-24.04
    steps: [ { run: echo "run tests" } ]
  gate:
    if: always()
    needs: [changes, test]
    runs-on: ubuntu-24.04
    steps:
      - run: |
          [ "${{ needs.test.result }}" = "success" ] || [ "${{ needs.test.result }}" = "skipped" ]
```

Mark only `gate` as required.

**Release once.** After checks pass on the protected branch: build the image once, push it, record *commit SHA ↔ registry digest*, generate an SBOM and scan that digest. Do not rebuild the same commit separately for staging and production — each rebuild is a different artifact.

**Promote by digest.** Promotion changes a pointer, not the source:

```text
# deploy/orders-api/image-ref.txt
registry.example.com/orders-api@sha256:3f1c...e9a0
```

A pull request that only changes this line promotes an existing, verified artifact. A small guard script rejects anything that is not exactly one reference with `@sha256:` and 64 hex characters, so `:latest` and tag-only references fail review automatically.

**Flaky tests.** A test that sometimes fails destroys trust in the gate. Retrying blindly hides real intermittent faults; fix the nondeterminism (time, ordering, shared state, network) and quarantine explicitly, with an owner and an expiry, if you must.

**Troubleshooting by class**

| Fault | Typical symptom | Response |
| --- | --- | --- |
| Test regression | Red job with a clear traceback | Fix code or test |
| Dependency install failure | Early pip or npm error | Fix the pin; do not retry forever |
| Cache inconsistency | CI differs from local | Make installs deterministic; clear caches |
| Registry auth failure | Push denied in release | Fix the identity; ensure PR jobs lack the secret |
| Bad promotion | Tag without a digest | Guard script fails; pin `@sha256:` |

**Exercise.** Inject two different faults on disposable branches, diagnose each from logs alone and write a short failure report.
