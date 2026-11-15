# T-PLT-06-I — Intermediate Practice

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-i"></a>
#### T-PLT-06-I — Intermediate Practice

## Why this matters

At Beginner level a golden path is a document and a template. At Intermediate level it becomes *software you maintain*. Scaffolds must validate input, templates must be tested, shared workflows must stay compatible with services already generated, documentation must stay true as the path changes, and feedback from developers must turn into fixes rather than into a growing pile of complaints.

Most golden-path failures at this level are not design failures. They are *maintenance* failures: the template that worked in March no longer generates a service that builds in September, because nobody generated one in between. This section teaches the habits that prevent that: a scaffold that fails early with a useful message, templates tested like code, workflows that fix many services at once, documentation with a clear owner, and a feedback loop that closes.

This section assumes the Beginner material: cognitive load, the path specification, the entry document and the clean-machine test. The running example is a platform that offers an `http-python` template and a command `new-service`. Nothing depends on any other course material.

## First principles: a template is a product artefact

A template that generates code is easy to write. A template that generates a service which *builds, passes policy, deploys, reports health, has a runbook and appears in the catalogue* is the golden path. The distance between the two is the work of this level.

Design rules:

- Generate only what a developer would otherwise copy and paste; keep generated files short and readable.
- Platform-owned logic lives *outside* the generated service (reusable workflows, shared base manifests) so fixes propagate; the generated code *calls* it.
- Everything generated is inspectable plain files. No hidden state.
- Fail early with helpful errors (naming rules, missing owner).
- Stamp what was generated: template name and version, so the platform can tell later who is behind.

The central trade-off is *copy versus reference*:

| Approach | Fixes propagate? | Developer can customise? | Risk |
| --- | --- | --- | --- |
| Copy everything into the service | No; every service must be fixed separately | Fully | Services diverge; old bugs live forever |
| Reference everything from the platform | Yes | Barely | Developers cannot see or change behaviour; magic |
| Copy the thin parts, reference the logic | Yes for logic | For configuration | Needs versioning and compatibility rules |

The third row is the usual answer: generate small, readable *glue* files, and keep the substantial logic in shared, versioned workflows and base manifests.

## Anatomy of a generated service

```text
services/<name>/
  app/                  # starter code with /health and /ready
  Dockerfile
  deploy/               # thin overlay referencing platform base manifests
  .github/workflows/    # calls the reusable platform workflow
  RUNBOOK.md            # starter runbook with the status command first
  README.md             # includes a "deviations from the golden path" section
  .golden-path.yaml     # template name and version stamp
catalog/<name>.yaml     # ownership and links, in a portal-compatible shape
```

The stamp file is small but valuable:

```yaml
# .golden-path.yaml  (generated; do not edit by hand)
template: http-python
version: 3
generated: 2026-09-12
parameters:
  name: orders-api
  owner: team-orders
  datastore: none
```

With it, the platform can answer "how many services are still on version 2?" with a query rather than a survey.

## The scaffolding command

A scaffold is a conversation with the developer. It should ask little, validate hard, and explain failures.

```bash
platform/bin/new-service --name orders-api --owner team-orders --language python
# validates: lowercase name pattern, owner exists, name not already in the catalogue
# writes files, runs the offline checker, prints next steps
```

What validation looks like inside the tool, in simplified form:

```bash
#!/usr/bin/env bash
set -euo pipefail

name="${1:?name required}"
owner="${2:?owner required}"

if ! [[ "$name" =~ ^[a-z][a-z0-9-]{2,30}$ ]]; then
  echo "ERROR: name '$name' must be lowercase letters, digits and hyphens," >&2
  echo "       start with a letter and be 3-31 characters. Example: orders-api" >&2
  exit 2
fi
if ! grep -q "^$owner\$" catalog/owners.txt; then
  echo "ERROR: owner '$owner' is not registered. Known owners: $(paste -sd, catalog/owners.txt)" >&2
  echo "       Ask in #platform-support to add a team." >&2
  exit 2
fi
if [[ -e "catalog/$name.yaml" ]]; then
  echo "ERROR: a service named '$name' already exists (see catalog/$name.yaml)." >&2
  exit 2
fi
```

Three habits are visible. Each message states the rule, *shows an example*, and tells the developer what to do next. Checks run before any file is written, so a failure leaves nothing half-created. Exit codes are distinct from success so that automation can react.

### Parameters: fewer is better

Every parameter is a decision the developer must make and the platform must support. Prefer a small set with safe defaults:

| Parameter | Keep? | Reason |
| --- | --- | --- |
| name, owner | Required | Identity and accountability |
| language | Yes, from a short list | Chooses the template |
| datastore | Optional, default none | Common variation |
| cpu and memory sizes | No; default per environment | A decision most developers cannot make well on day one |
| base image tag | No; platform sets and updates | Developers should not track image patches |

## Workflows: shared logic that fixes many services at once

A generated pipeline should be a few lines that call a shared workflow:

```yaml
# .github/workflows/ci.yaml  (generated)
name: ci
on: [pull_request, push]
jobs:
  build:
    uses: platform-org/platform-workflows/.github/workflows/service-ci.yaml@v2
    with:
      service: orders-api
      language: python
    secrets: inherit
```

The `@v2` reference is a *contract*. Rules for maintaining it:

| Change to the shared workflow | Allowed within v2? | How to handle |
| --- | --- | --- |
| Fix a bug, update a pinned tool patch version | Yes | Release; every service gets it on next run |
| Add an optional input with a safe default | Yes | Additive; document it |
| Add a new required input | No | New major version, migration guide, deprecation window |
| Remove an input or change meaning | No | New major version |
| Add a new check that can fail existing services | Careful | Announce, run in warn-only mode first, then enforce |

The *warn-only first* pattern prevents the platform from breaking everyone on a Tuesday morning:

```text
week 0   announce new check; run in warn-only mode; list services that would fail
week 2   open pull requests (or issues) against failing services
week 4   enforce; exceptions require a recorded deviation
```

### Promotion by pull request

A promotion tool takes service, environment and digest, validates all three (environment allowed, digest well-formed and previously released), edits the overlay and opens a pull request. A policy check runs on the pull request and again at admission.

```bash
platform promote --service orders-api --env staging --digest sha256:3f1c...e9a0
# validates: env in {staging, production}; digest matches ^sha256:[0-9a-f]{64}$;
#            digest was built by CI for this service; production requires prior staging
# edits deploy/overlays/staging/kustomization.yaml, opens a pull request
```

The developer sees a pull request with a diff. The audit record is the Git history. Rolling back is promoting an earlier digest, never editing live objects.

## Testing a template like software

A template never generated in CI will rot. Split checks by what they need.

**Offline checks** are a required pull-request check on the template repository. They need no cluster credentials:

1. Generate a service into a temporary directory with each supported parameter combination.
2. Run formatters and linters on the output.
3. Render manifests and evaluate policy against the rendered output.
4. Verify that the catalogue entry is valid and the stamp file exists.
5. Run the generated unit tests.

```bash
#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
for lang in python go; do
  for ds in none postgres; do
    out="$tmp/${lang}-${ds}"
    platform/bin/new-service --name "t-$lang-$ds" --owner team-test \
      --language "$lang" --datastore "$ds" --out "$out" --no-git
    (cd "$out" && make lint test)
    kustomize build "$out/deploy/overlays/staging" > "$out/rendered.yaml"
    conftest test "$out/rendered.yaml" --policy platform/policy/
    platform/bin/check-catalog "$out/catalog"
  done
done
echo "template matrix OK"
```

**Cluster checks** run on a schedule in a disposable lab: deploy the generated service, check readiness and the status command, then delete. They catch things offline checks cannot, such as an image that does not start or a probe that never succeeds.

| Check | Where | Frequency | Catches |
| --- | --- | --- | --- |
| Matrix generation + lint + unit tests | Pull request | Every change | Syntax, naming, broken starter code |
| Render + policy | Pull request | Every change | Manifest and policy drift |
| Deploy to lab, status check, delete | Scheduled | Nightly | Runtime failures, expired images, changed dependencies |
| Docs link check and command extraction | Pull request and nightly | Both | Dead links, commands that no longer run |

A nightly run matters because dependencies change without anyone touching the template: a base image is retired, a package yanked, an API deprecated.

## Safe self-service means guardrails, not freedom

The limits are the product. A developer can create and change things quickly *because* the platform makes dangerous things hard.

| Guardrail | Enforced by | Developer sees |
| --- | --- | --- |
| Naming and ownership rules | Scaffold plus a policy check | A clear error with the fix |
| Quota and defaults per namespace | Tenant manifest | "Quota exceeded: pods 6/6" |
| Digest-only images | Promotion tool, check, and admission policy | A rejection naming the rule |
| No administrator rights for developers | RBAC; a namespaced reconciler | Read-only status; changes by pull request |
| Review before change | Branch protection and code owners | Required reviewer and checks |
| Secrets never in Git | Secret scanning and a documented secret path | A blocked push or documented alternative |

Documented human gates are acceptable if they are *designed*: for example, creating a tenant namespace needs a platform reviewer; record the expected response time in the path.

A guardrail is useful only if its *message* helps. Compare:

```text
Bad:   Error: admission webhook "policy.platform" denied the request.
Good:  DENIED by rule 'image-by-digest': container 'app' uses tag 'latest'.
       Use a digest such as orders-api@sha256:<64 hex>. How: docs/how-to/promote.md
```

The second names the rule, the object and the fix, and links to a page. Writing such messages is real engineering effort, and it is where much of the developer experience lives.

## Documentation as part of the path

Documentation in a platform is code-adjacent: it can break. Treat it that way.

| Practice | How |
| --- | --- |
| Docs live beside the code that they describe | Same repository or a linked, versioned one |
| Commands are extracted and tested | A CI job runs fenced `bash` blocks marked as runnable in a lab |
| Links checked | Link-check job on pull request and nightly |
| One owner per page | Named in front matter; stale pages (no review in 6 months) are flagged |
| Four kinds kept separate | tutorial, how-to, reference, explanation |
| Errors documented beside the steps that cause them | Each how-to has a "If you see..." section |

A front-matter block that makes ownership checkable:

```yaml
---
title: Promote a release to staging
kind: how-to
owner: team-platform
last_reviewed: 2026-10-01
runnable: true
---
```

A simple freshness check turns the metadata into a signal:

```bash
# list pages not reviewed in 180 days
find docs -name '*.md' -print0 | xargs -0 awk '
  /^last_reviewed:/ { print FILENAME, $2 }' | sort -k2 | head -20
```

## The feedback loop

Developers will tell you what hurts, if telling you is cheap and visibly worthwhile. A closed loop looks like this:

```text
 developer hits a problem
        │  (support channel, issue label platform-gap, or trial finding)
        ▼
   triage weekly ──▶ categorise ──▶ is it a docs fix, a path fix or a gap?
        │                              │             │            │
        │                       fix docs within   fix path /   add to roadmap
        │                       the week          template     with a ranked reason
        ▼
   tell the reporter what changed ──▶ measure again
```

Practical rules:

- Use two labels: `platform-support` (a question) and `platform-gap` (the path does not fit). Both have a stated response target.
- Convert any question asked three times into a document or a fix within the week.
- Categorise support requests so that you can report "access: 14, template errors: 9, docs unclear: 7". The categories reveal what to fix first.
- Close the loop publicly: a short changelog entry "What we fixed this month, and who reported it".

A summary table for the monthly review:

| Category | Count | Median time to resolve | Action |
| --- | --- | --- | --- |
| Access requests | 14 | 1.5 days | Document approver; add self-service for read access |
| Template generation errors | 9 | 2 hours | Add validation and clearer messages |
| Docs unclear | 7 | 1 day | Rewrite three pages; add expected output |
| Platform gap (no support) | 4 | n/a | Ranked on roadmap by number of teams affected |

## Onboarding failures and their diagnosis

When a new developer reports failure, work down a ladder instead of guessing.

| Question | If the answer is no | Likely fix |
| --- | --- | --- |
| Could they find the entry document? | Findability | Link from the places people start (team page, repo template) |
| Did every prerequisite check pass? | Environment | Better `doctor` command; document versions |
| Was access granted in the documented time? | Process | Name the approver; measure the wait |
| Did generation succeed with helpful messages? | Scaffold | Better validation and messages |
| Did CI pass on the generated service? | Template rot | Matrix test failed to cover this case |
| Did deploy succeed and status report correctly? | Platform or status | Fix path or status command |
| Could they find the runbook when something broke? | Operability | Put status command first; link in the portal |

Record each case in the same short form: *symptom, step, cause, fix, document or code changed*. After ten cases patterns appear, and that pattern is your roadmap.

## Escape hatches and deviations

Teams will leave the path. Make leaving visible and cheap to record, and make the cost clear.

- A **deviation record** in the service README: what was changed, why, and who owns the consequence.
- An **exception expiry**, reviewed quarterly. A deviation without an end date becomes permanent by default.
- A **platform gap issue** for each deviation. Every deviation is also a product signal.

```markdown
## Deviations from the golden path
| Date | Deviation | Reason | Owner | Review by | Gap issue |
| --- | --- | --- | --- | --- | --- |
| 2026-10-04 | Uses Rust, own Dockerfile and CI | Latency-critical parser | team-orders | 2027-01-04 | platform-gap#118 |
```

Even a deviation must meet the same *requirements* the path meets: health endpoints, ownership metadata, build evidence, a runbook. The path is the easy way to meet them; leaving means meeting them yourself.

## Common mistakes

- Generating a template that has never been built since it was written.
- Copying shared logic into services, so a single fix needs fifty pull requests.
- Adding a new check that fails existing services without a warn-only period.
- Error messages from policy engines passed through unreadable.
- Documentation with no owner and no review date.
- Treating each support question as one-off instead of a signal.
- Recording deviations without an expiry or a gap issue.
- Measuring only adoption and not whether the generated service works.

## Knowledge consolidation

1. Why is "copy the thin parts, reference the logic" usually better than copying everything or referencing everything?
2. What does the version stamp enable, and what question could you not answer without it?
3. Which template checks belong offline and which in a lab cluster? Why not do all of them in the cluster?
4. Describe the warn-only pattern and the failure it prevents.
5. Why must an error message state a rule, an example and a next step?
6. A question has been asked in support three times. What do you do this week?

## Exercises

1. **Scaffold validation.** Write a script that validates a service name, an owner and a duplicate, with messages that show an example and a next step. Test five bad inputs.
2. **Template matrix.** Write a CI job that generates every supported parameter combination into a temporary directory and runs lint, unit tests and a policy check. Break one combination on purpose and confirm the job fails with a clear message.
3. **Readiness probe.** Generate a service from a template, deliberately delete its readiness probe and confirm the checker fails with a message a developer could act on.
4. **Warn-only rollout.** Plan the rollout of a new required check across fifty services: weeks, communication, who is told and when it becomes enforced.
5. **Feedback review.** Take a month of support messages (real or invented), categorise them and propose the top three fixes with a reason for the order.
6. **Deviation record.** Write the deviation record for a team that cannot use the path's language and include expiry and gap issue.
