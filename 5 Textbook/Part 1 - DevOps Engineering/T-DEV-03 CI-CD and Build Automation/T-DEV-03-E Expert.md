# T-DEV-03-E — Expert Depth

*Chapter: [T-DEV-03 — CI/CD and Build Automation](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-03-e"></a>
#### T-DEV-03-E — Expert Depth

**Provenance and what it does not prove.** A provenance attestation states that *this digest was built by this workflow from this commit*. That is valuable for tracing and for policy ("only deploy artifacts built by the release workflow from the protected branch"). It does not prove the source is benign, and a compromised pipeline can sign anything. Verification should bind several facts together: the digest, the expected source repository, the approved workflow identity, and a required commit on the protected branch. A signature alone is not enough.

**Supply-chain frameworks.** Frameworks such as SLSA describe levels of build integrity: scripted builds, hosted builds with provenance, hardened and isolated builds. Use them as a ladder for planning and for conversation with auditors, not as a checkbox exercise. Climb where the risk is.

**Pipeline threat model (beyond forks).**

1. *Poisoned pipeline execution:* an attacker who can modify a workflow file in a branch that has access to secrets. Mitigate with branch-scoped secrets, environment approvals and owners on workflow paths.
2. *Cache poisoning:* a low-privilege job writes a cache entry that a privileged job later restores. Scope caches by trust level.
3. *Third-party action compromise:* pin by SHA and review updates.
4. *Self-hosted runner persistence:* one job leaves artifacts for the next. Prefer ephemeral runners.
5. *Artifact substitution between jobs:* verify digests when passing artifacts between jobs.
6. *Script injection through untrusted inputs:* never interpolate `${{ github.event.pull_request.title }}` and similar into shell commands; pass through environment variables.

**Flake economics and test strategy.** Treat the pipeline as a product with a latency budget. Track median and tail duration, flake rate per test, queue time and cost. Fast feedback comes from test selection, parallelism and caching; slow suites move to merge or nightly lanes provided a failure there still blocks release. Retry policy should be explicit, bounded and visible, never silent.

**Deployment strategies and the pipeline's role.** Whether CD pushes to the environment or only updates desired state that a reconciler applies (see T-DEV-05) is an architectural decision with security consequences: pushing requires pipeline credentials to production; pulling does not. Progressive strategies (rolling, blue/green, canary) need health signals; the pipeline or a controller must be able to act on them.

**Exceptions.** A critical vulnerability with no available fix needs a governed exception: who may approve, the compensating control, and an expiry date. Exceptions without owners and expiry become permanent policy by neglect.

**Verifying an attestation: what the policy must bind together.** A verifier that only checks "a valid signature exists" accepts anything signed by anyone with a certificate. A defensible policy states each fact it requires:

```bash
# Illustrative: verify provenance for an image before it may be promoted
gh attestation verify oci://registry.example.com/orders-api@sha256:3f1c...e9a0 \
  --repo example-org/orders-api \
  --signer-workflow example-org/orders-api/.github/workflows/release.yml \
  --source-ref refs/heads/main
# equivalent with cosign: cosign verify-attestation --type slsaprovenance \
#   --certificate-identity-regexp '^https://github.com/example-org/orders-api/\.github/workflows/release\.yml@refs/heads/main$' \
#   --certificate-oidc-issuer https://token.actions.githubusercontent.com <image>@sha256:<digest>
```

| Fact bound | Attack it blocks |
| --- | --- |
| The **digest** (not a tag) | Swapping the image after verification |
| The **source repository** | An attestation from a fork or an unrelated repository |
| The **workflow identity and path** | A workflow in the same repository that anyone could edit on a branch |
| The **ref** (protected branch) and required review on that commit | Building unreviewed code from a feature branch |

What remains unproven: the commit itself may contain a back-door that passed review, and a compromised build platform can issue valid attestations for malicious builds. Provenance narrows the question to "trust this workflow and this review process", which is auditable; it does not remove it.

**Placing a pipeline on the ladder (SLSA-style).** A practical assessment is a table, not a score:

| Rung (simplified) | What is true | Evidence to produce | Climb when |
| --- | --- | --- | --- |
| Scripted build | Build is code in version control, not manual steps | Workflow file in repository | Always; it is the floor |
| Hosted build with provenance | Build runs on a managed service that emits signed provenance | Verifiable attestation per release | You have external consumers or regulated deployments |
| Hardened, isolated build | Builds are ephemeral, isolated from each other, with no secret access for untrusted code | Runner configuration, ephemeral logs, network egress policy | A compromise of one build could reach production secrets, or auditors require it |

Justify each climb by the loss it prevents. A team deploying an internal admin tool does not need the same rung as one distributing software to customers.

**Threat model: mitigation and an evidence test for each threat.**

| Threat | Mitigation | Evidence test (prove the control, not the setting) |
| --- | --- | --- |
| Poisoned pipeline execution | Secrets only on protected-branch environments with approval; CODEOWNERS on `.github/workflows/`; untrusted PRs run without secrets | Open a PR from a fork that edits the workflow to print a secret; confirm it receives none and the job cannot deploy |
| Cache poisoning | Separate caches by trust level; never restore a PR-written cache in a release job | A PR job writes a marker to the cache; the release job must not find it |
| Third-party action compromise | Pin to full commit SHA; update through reviewed PRs; allow-list actions at organisation level | Try referencing an unlisted action or a floating tag; the run must be rejected |
| Self-hosted runner persistence | Ephemeral runners, one job per instance; no runners for public-fork workflows | Job A writes a file to the workspace; job B on the "same" runner must not see it |
| Artifact substitution | Record digests when uploading; verify before consuming; build once | Alter the stored artifact in a test; the consuming job must fail on digest mismatch |
| Script injection | Pass untrusted values through `env:` and quote them; lint for `${{ github.event.* }}` in `run:` | Open a PR titled `"; echo INJECTED #` and confirm no command is executed |

```yaml
# Vulnerable: title is expanded into the shell script
- run: echo "Building ${{ github.event.pull_request.title }}"
# Safer: value arrives as data, not code
- env: { TITLE: "${{ github.event.pull_request.title }}" }
  run: echo "Building $TITLE"
```

**The pipeline as a product: measures and arithmetic.** Define a service-level view: median and p95 duration from push to green, queue time, flake rate per test, cost per run, and developer-visible failure rate caused by infrastructure rather than code. Flakes compound: if a pipeline has 40 independent tests that each flake 1% of the time, a run fails spuriously about 33% of the time (1 − 0.99⁴⁰). Developers then retry reflexively and stop trusting red builds, which is the real cost.

| Policy choice | Benefit | Failure mode | Guard |
| --- | --- | --- | --- |
| Automatic retry of a failed test (bounded, visible) | Hides rare infrastructure noise | Masks a genuine race condition | Count retries; a test that needs retry more than N times per week is quarantined with an owner and deadline |
| Moving slow suites to a merge or nightly lane | Fast PR feedback | A failure arrives after merge | Failures in the lane block promotion and page the owner of the change |
| Test selection by changed paths | Speed | Missed cross-module dependencies | Periodic full run; selection rules reviewed against escaped defects |

**Push versus pull deployment: a decision frame.**

| Question | Push (pipeline applies to the environment) | Pull (controller reconciles from Git) |
| --- | --- | --- |
| Where do production credentials live? | In the CI system (large blast radius if it is compromised) | In the cluster; CI needs only write access to a config repository |
| How is drift handled? | Not detected until the next deploy | Continuously detected and corrected |
| Rollback | Re-run an old pipeline | Revert a commit; state is visible and reviewable |
| Cost of adoption | Low | Needs a controller, a repository layout and promotion discipline |

Choose pull when the environment is production-like and the risk of credential theft from CI matters; push is defensible for small, low-risk targets with strong environment protection. Progressive strategies need a signal: rolling updates need readiness; blue/green needs a switch plus rollback of traffic; canary needs metrics comparison (error rate, latency) and an automatic or documented abort threshold. If nobody defined the signal, "canary" is only a slow rolling update.

**Governed exception record (template).**

```text
Exception ID: SEC-2026-014        Owner: <named person>   Approver: <role>
Finding: critical CVE in base image; no fixed version released
Scope: orders-api staging and production      Expires: 2026-12-15 (renewal needs re-approval)
Compensating controls: WAF rule blocking exploit path; egress deny; alert on exploit signature
Exit criteria: patched image promoted, or component removed
Evidence required at expiry: scan report showing the finding closed
```

An exception that lacks an owner, a compensating control or an expiry is not an exception; it is a silent policy change.

**Failure modes of the pipeline programme itself**

- Controls exist as settings but are never exercised, so nobody knows if they work. Schedule the evidence tests above quarterly.
- Security gates are slow and noisy, so teams route around them; measure bypass attempts and false-positive rates.
- A single "release engineer" account or runner pool becomes a privileged choke point and a single point of compromise.
- Provenance is generated but nothing verifies it, giving the audit trail without the protection.

**Mentoring prompts.** Draw the trust boundary of your pipeline and mark every place untrusted data crosses it. Why is "build once, promote the digest" a security property and not just an efficiency one? What would you need to see to believe an attestation, and what could a compromised build system still do?

---
