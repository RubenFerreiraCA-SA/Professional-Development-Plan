# T-PLT-07-I — Intermediate Practice

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-i"></a>
#### T-PLT-07-I — Intermediate Practice

## Why this matters

At the Beginner level you followed one change across the seams and marked each as Proven, Claimed or Unknown. At this level you run the *normal lifecycle* as a repeatable practice: a service is onboarded, changed, deployed, monitored, rolled back when it misbehaves, and the lessons feed the next change. You also learn who is responsible at each stage and what the failure signals look like, so a problem can be routed to the right seam within minutes instead of hours.

The central skill is **walking a symptom backwards through the lifecycle** to the first stage whose evidence does not match. The supporting skills are writing a verification step that compares artefacts across stages, assigning responsibilities explicitly, and writing runbooks that someone other than the author can follow. The chapter uses a neutral `orders-api` service; it has no dependency on any other course material. Commands are illustrative: names, namespaces and URLs will differ in your environment.

## First principles: the lifecycle as a loop with one source of truth

The lifecycle has six stages and one loop-back:

```text
 onboard ──► change ──► deploy ──► monitor ──► (rollback) ──► feedback
    ▲                                                            │
    └────────────────────────────────────────────────────────────┘
```

Two principles keep it coherent.

1. **Git is the source of truth for desired state.** Every change to what runs, including a rollback, is a reviewed commit. The controller makes the cluster match Git; people do not edit the cluster. This is what makes the lifecycle *auditable* (the history explains what happened) and *recoverable* (an earlier commit describes a known-good state).
2. **Artefacts, not intentions, cross stage boundaries.** The build does not say "this is probably the version we want"; it publishes a digest and records the commit and the evidence. The promotion cites that digest. The verification step compares them. Each stage can distrust the previous one *cheaply*, because it can check a named artefact.

A useful phrase for the second principle is **verify, then trust**. The cost of checking an artefact at each boundary is small; the cost of discovering a mismatch in production is large.

## Stage 1 — Onboarding: from nothing to a service the platform knows

Onboarding turns an idea into a service that fits the platform. It is the first integration test, because it exercises seams before any code exists.

What happens, in order:

1. A developer runs the scaffold or template, which creates a repository, a pipeline definition, base manifests, a service entry for the catalogue and a documentation stub.
2. The scaffold opens a pull request for any platform-owned path (for example the desired-state entry). A platform reviewer approves; the wait is a *documented human gate* and you should record how long it took.
3. After merge, the catalogue lists the service with an owner, an on-call contact and a link to its runbook.
4. Identity for the service is created: a build identity allowed to push one image name, a workload identity allowed to read its own secrets, and an access group for the owning team.
5. The status command reports `UNKNOWN` or `DOWN`, because nothing has been promoted. It must **not** report `HEALTHY`.

```bash
# What a clean onboarding leaves behind (illustrative)
git -C orders-api log --oneline | head -3
platformctl catalogue get orders-api
platformctl status orders-api --env staging
```

```text
orders-api   owner=team-orders   tier=standard   runbook=docs/runbook.md
orders-api   staging   UNKNOWN   (no release promoted; no telemetry yet)
```

The last line matters. A new service that reports `HEALTHY` before anything runs means the status check inspects too little. Catch it here, when it costs one line of code.

**Onboarding failure signals**

| Signal | Likely seam | First check |
| --- | --- | --- |
| Scaffold completes but the first pipeline run fails | Template ↔ pipeline | Compare the generated pipeline with a known-good one |
| Generated manifests rejected at the first deploy | Template ↔ policy | Run the policy check locally against the generated manifests |
| Catalogue entry exists but has no owner | Template ↔ catalogue | Check the required fields in the scaffold |
| Status says `HEALTHY` with nothing deployed | Status ↔ reality | Read what the status actually queries |

## Stage 2 — Change and build: the trusted path to a digest

A change enters as a pull request. The repository enforces review and required checks. After merge, a trusted pipeline builds the image *once*, pushes it by digest and records evidence: commit SHA, builder identity, build time, and an attestation (a signed statement of how the image was built).

```bash
# Verify the artefact before promoting it (illustrative)
DIGEST=$(jq -r .digest release-record.json)
COMMIT=$(jq -r .commit release-record.json)

# 1. The digest exists in the registry
docker manifest inspect "registry.example.com/orders-api@${DIGEST}" >/dev/null

# 2. The attestation verifies and names the expected source
cosign verify-attestation --type slsaprovenance \
  --certificate-identity-regexp '^https://ci.example.com/.+/orders-api' \
  --certificate-oidc-issuer https://ci.example.com \
  "registry.example.com/orders-api@${DIGEST}" \
  | jq -r '.payload' | base64 -d | jq -r '.predicate.invocation.configSource.digest.sha1'

# 3. That source commit is on the protected branch
git merge-base --is-ancestor "${COMMIT}" origin/main && echo "commit on main"
```

Three separate checks, three separate claims: the image exists, it was built by the trusted pipeline, and it came from reviewed code. A pipeline that only checks the first has a seam hole: any image in the registry could be promoted.

**Build failure signals**

| Signal | Likely seam | First check |
| --- | --- | --- |
| Digest recorded does not exist in the registry | CI ↔ registry | Did the push step fail silently or push a different name? |
| Attestation verification fails | CI ↔ verification | Did the builder identity or issuer string change? |
| Same commit yields different digests across runs | Build reproducibility | Compare timestamps and unpinned inputs |
| Image tag resolves to a different digest than recorded | Mutable tag | Promote by digest only |

## Stage 3 — Deploy: promotion, policy, reconciliation

**Promotion** is a pull request in the desired-state repository that changes only the digest for one environment. Two required checks guard it:

- `promotion-verify` runs the artefact verification above and checks that the diff touches nothing except the digest line.
- `policy` evaluates the rendered manifests against rules (non-root, resource limits, allowed registries, no `latest`).

```bash
# promotion-verify: the diff must change exactly one digest line
CHANGED=$(git diff --unified=0 origin/main...HEAD -- env/staging/orders-api/ | grep -E '^[+-][^+-]' | wc -l)
[ "$CHANGED" -eq 2 ] || { echo "promotion must change exactly one line (found $CHANGED changed lines)"; exit 1; }
git diff -U0 origin/main...HEAD | grep -q '^+.*image:.*@sha256:' || { echo "no digest change"; exit 1; }
```

After merge, the **controller** compares Git to the cluster and applies the difference. Admission policy in the cluster re-checks the rules, because CI checks can be bypassed by someone with the right permissions; admission is the last line.

The acceptance condition for a deploy is a three-way equality: **the running digest equals the promoted digest equals the attested digest.**

```bash
PROMOTED=$(yq '.spec.template.spec.containers[0].image' env/staging/orders-api/deployment.yaml | sed 's/.*@//')
RUNNING=$(kubectl -n orders get pod -l app=orders-api \
  -o jsonpath='{.items[0].status.containerStatuses[0].imageID}' | sed 's/.*@//')
ATTESTED=$(jq -r .digest release-record.json)
[ "$PROMOTED" = "$RUNNING" ] && [ "$RUNNING" = "$ATTESTED" ] && echo "three-way match" || echo "MISMATCH promoted=$PROMOTED running=$RUNNING attested=$ATTESTED"
```

Run this at the end of every deploy drill and put the output in the evidence file.

**Deploy failure signals**

| Signal | Likely seam | First check |
| --- | --- | --- |
| Promotion PR checks fail on the policy step | Template ↔ policy | Read the policy message; does it say how to fix it? |
| PR merged, controller shows `OutOfSync` | Git ↔ controller | Controller logs; a sync error such as a rejected manifest |
| Controller `Synced`, Pods `Pending` | Controller ↔ cluster | Events: quota, scheduling, image pull |
| Pods `ImagePullBackOff` | Registry ↔ cluster | Pull secret, registry name, digest existence |
| Pods Ready but running digest differs | Controller ↔ ownership | Something else (a human, another tool) is managing the Deployment |

## Stage 4 — Monitor: health that can say "I don't know"

Monitoring has two jobs in the lifecycle: tell you if a change *worked*, and tell you quickly if it *did not*. A deploy is not finished when the controller says `Synced`; it is finished when health signals confirm the new version is serving.

A minimal post-deploy check watches four things for a short window:

| Check | Why it matters | Example condition |
| --- | --- | --- |
| Readiness | New Pods accept traffic | All replicas Ready within 3 minutes |
| Error rate | The change did not break requests | 5-minute error rate no worse than the previous release plus a margin |
| Latency | The change did not slow the service | p95 within an agreed margin |
| Data freshness | The telemetry itself is current | Last metric point under 60 seconds old |

The last row is the one most often missing. Without it, a service that stopped reporting looks like a service that stopped erroring.

**Status must be honest.** The status command should be able to return `UNKNOWN`, and its text should say which check could not be performed. Treat a status that has never returned `UNKNOWN` as untested.

**Monitor failure signals**

| Signal | Likely seam | First check |
| --- | --- | --- |
| Dashboard exists, no data for the new service | Template ↔ telemetry | Is the service exporting? Is the label or name what the dashboard queries? |
| Alerts never fire in a drill | Telemetry ↔ alerting | Query the alert expression directly during the drill |
| Logs missing for one Pod | Runtime ↔ log pipeline | Node-level log agent, Pod label selectors |
| Status `HEALTHY` while users complain | Status ↔ reality | Add a check that exercises a user path |

## Stage 5 — Rollback: recovery through Git

Rollback is not a different system; it is the normal deploy path pointed at an earlier known-good digest. Because every release is a commit, the safest rollback is a **revert of the promotion pull request**.

```bash
# Find the promotion that introduced the bad digest and revert it
git log --oneline -- env/staging/orders-api/deployment.yaml | head -5
git revert --no-edit <bad-promotion-sha>
git push origin HEAD:rollback/orders-api-staging
# open a pull request; the same checks run; merge; the controller reconciles
```

Two rules make rollback dependable.

- **Roll back to a digest that still exists.** Registry retention rules that delete older digests turn rollback into a rebuild. Check that every digest referenced in Git's recent history is retained.
- **Know what rollback cannot undo.** Reverting the Deployment does not reverse a database migration, a message already published or a cache already poisoned. A release that changes persistent state needs a separate rollback plan (and usually a forward-compatible migration so the old version still works).

**Break-glass versus normal path.** In a severe incident an operator may need to act on the cluster directly. Define this in advance: who may do it, how it is recorded, and — critically — how the change is *brought back into Git* afterwards. A direct fix that never returns to Git is drift waiting to be reverted by the controller at the worst moment.

**Rollback failure signals**

| Signal | Likely seam | First check |
| --- | --- | --- |
| Revert PR conflicts | Promotion hygiene | Were promotions merged out of order or batched? |
| Reverted digest cannot be pulled | Registry retention | Retention rule versus the release record |
| Rollback succeeds but errors continue | State, not code | Data migration, config or secret change in the same release |
| Controller reverts the operator's manual fix | Break-glass not reconciled | Commit the fix to Git first |

## Stage 6 — Feedback: turning what happened into the next change

Every deploy, drill, incident and support question is data about the platform. The lifecycle closes only if this data becomes work.

| Source | Example finding | Platform change |
| --- | --- | --- |
| A stuck new user | They could not find the digest after merge | The release summary prints it and the next command |
| A policy denial | The message did not say how to fix it | Add a documentation link to the message |
| A slow review | Platform reviewer wait was two days | Add a second reviewer or an automated check for low-risk changes |
| A rollback | The previous digest was gone | Fix retention; add a check that fails when it would delete a recent release |

Capture each as a backlog item with a severity, an owner and a **verification step** that shows the fix worked. "We told people" is not a fix; "the same drill now completes without that confusion" is.

## Responsibilities: who owns what

An unowned seam is where problems wait. Write responsibilities down before something breaks. The matrix below separates *who owns the component*, *who owns the seam* and *who must be told* — three things that are often confused.

| Stage / seam | Owns the component | Owns the seam | Must be told when it breaks |
| --- | --- | --- | --- |
| Repository rules | Platform | Platform | Service team |
| Pipeline | Platform (shared workflow) / service team (service pipeline file) | Platform | Service team, platform on-call |
| Build → registry | Platform | Platform | Service team |
| Registry retention | Platform | Platform with service team input | Service teams with rollback needs |
| Promotion → controller | Platform | Platform | Service team |
| Controller → cluster | Platform / cluster operations | Cluster operations | Platform on-call |
| Service manifests | Service team | Service team | Platform if template defect |
| Telemetry from the service | Service team | Platform (the pipeline of telemetry), service team (what is emitted) | Both |
| Status and catalogue | Platform | Platform | Service team |
| Runbooks | Service team (developer) / platform (operator) | Whoever last changed the system | On-call |

Two rules keep this useful: **every seam has exactly one named owner** (a shared owner is no owner), and **the owner must have the authority and the access to fix it**. A team accountable for a seam they cannot change will escalate every time.

## A troubleshooting routine: walk backwards from the symptom

When something is wrong, resist guessing. Start from what you can observe and move one stage back at a time, applying the same check: *does the artefact here match the artefact in the stage before?*

```text
Symptom: users see old behaviour after a deploy
  1. What digest is running?                    kubectl ... imageID
  2. Does that equal the promoted digest?       desired-state file in Git
       no  → controller not synced / something else owns the Deployment
       yes → continue
  3. Does the promoted digest equal the build's record?
       no  → promotion used the wrong digest
       yes → continue
  4. Does the build's commit contain the change?
       no  → the change was not merged / built from an old commit
       yes → the change is in the running digest; the bug is in the change or a cache
```

Each step has a yes/no answer and a command. This is faster than reading everything at once, and the result — "the first mismatch is between 2 and 3" — is also the sentence you put in the ticket.

## Integrated demonstration plan

Choose one runtime and record it. Then build and demonstrate each outcome in order, committing the evidence:

1. **Create:** run the scaffold on a branch, open a pull request, observe the required review (a platform-owned path triggers a platform reviewer — a documented human gate; record the wait). After merge the catalogue lists the service; the status command reports `UNKNOWN` or `DOWN` (nothing promoted), not a false `HEALTHY`.
2. **Reviewed change, trusted build:** open a pull request that breaks a test and show it unmergeable; fix and merge; record commit, run URL, digest and attestation; verify the artefact before promotion.
3. **Self-service deploy:** promote the verified digest to staging by pull request; the required `promotion-verify` and `policy` checks pass; the controller reconciles; confirm that the *running* image digest equals the promoted digest equals the attested digest.
4. **Health, failure, recovery:** kill a Pod; run a drill that breaks a release and recover through Git; if state is in scope, run a restore drill.
5. **Independent acceptance:** a person who did not build the platform does the path with no help.

**Acceptance tasks**

| Task | Standard |
| --- | --- |
| Create and deploy a service | Completed with no undocumented help |
| Make and promote a change | Review, build, promotion all via the documented path |
| Investigate and recover a planted failure | Recovery via the runbook and a pull request |
| Explain the controls | The participant states what blocked an unsafe action and why |

Record findings with severity, and treat any severe finding as a backlog item to fix and re-verify.

## Stateful drills (if state is in scope)

| Drill | Injection | Evidence |
| --- | --- | --- |
| S1 | Kill an application Pod | Timeline to Ready; client impact |
| S2 | Kill the database Pod | Data survived; time to `query_ok` |
| S3 | Logical damage (delete rows) | Restore from backup; compare fingerprints; recovery-point exposure |
| S4 (optional) | Rebuild: delete the volume and Pod, recreate empty, restore from an off-cluster copy | Counts match; total recovery time |

Fingerprint data before and after (row count and a checksum) so you can show what was and was not recovered:

```bash
psql "$DB_URL" -Atc "select count(*), md5(string_agg(id::text || status, ',' order by id)) from orders" \
  | tee evidence/orders-fingerprint-before.txt
```

**Backups that survive the cluster.** Copy a dump *out* of the cluster (not into Git) and test restoring from the copy. A backup that lives only in the cluster dies with it. A backup that has never been restored is a hope, not a control.

## Runbooks for someone who is not you

A developer runbook ("Not Ready and `database: unreachable` → status → documented first action") and an operator runbook (decision tree: Pod down versus data wrong; exact restore command; verification query; who approves; "do not delete the volume to fix this"). Record which runbook version was used in each drill. A usable runbook has a fixed shape:

```markdown
# Runbook: orders-api — new release is failing

**When to use:** status is DEGRADED within 15 minutes of a promotion.
**Who:** any member of team-orders. Escalate to platform on-call if step 4 fails.

1. Confirm: `platformctl status orders-api --env staging` — note version and error rate.
2. Identify the promotion: `git log -3 -- env/staging/orders-api/`.
3. Roll back: revert that promotion PR, merge, wait for `Synced`.
4. Verify: status returns HEALTHY and the three-way digest check matches.
5. Record: timeline in the incident note, and open a follow-up for the cause.

**Do not:** edit the Deployment with kubectl; delete the namespace; skip verification.
**Last tested:** 2026-11-02 by a person who did not write it. **Version:** 4.
```

Notice the three elements beyond the steps: *when to use it* (so it is not used wrongly), *do not* (the tempting wrong moves) and *last tested by whom* (so staleness is visible).

## What can go wrong: a short catalogue

| Failure | How it looks | Defence |
| --- | --- | --- |
| Promotion of an unverified digest | A digest with no attestation reaches staging | `promotion-verify` as a required check; admission re-check |
| Verification checks only the image, not its source | A build from an unreviewed branch is promoted | Verify the source commit is on the protected branch |
| Controller prunes something it should not | A resource owned by another tool disappears | Document ownership; exclude or annotate resources |
| Rollback target deleted by retention | Revert merges but Pods cannot pull | Retention keeps every digest in recent Git history |
| Break-glass fix never recorded | Controller reverts it or drift alarms fire | Commit to Git first, or immediately after |
| Status `HEALTHY` with stale data | Silent outage | Data freshness check returns `UNKNOWN` |
| Runbook assumes access developers lack | The reader stalls at step 2 | Split developer and operator runbooks; test with a newcomer |

## Knowledge consolidation

- The lifecycle is **onboard → change → deploy → monitor → rollback → feedback**, with Git as the single source of desired state.
- **Verify, then trust**: each boundary checks a named artefact — image exists, attested by the trusted builder, source on the protected branch.
- A successful deploy means a **three-way match**: running digest = promoted digest = attested digest.
- A deploy is finished when **health signals confirm it**, including a check that the telemetry itself is fresh.
- **Rollback is the normal path** pointed at an earlier commit; it needs retained digests and does not undo state changes.
- **Break-glass** is defined in advance and always returns to Git.
- Every seam has **one named owner** with authority to fix it.
- **Walk backwards** from the symptom; the first mismatch names the broken seam.
- Findings only count when they become **backlog items with a verification step**.
- Runbooks state *when*, *who*, *do not* and *last tested by whom*.

## Exercises

**Exercise 1 — Full lifecycle.** On a practice platform run the five demonstration steps in order. Keep an evidence file with the commit, run URL, digest, attestation output, promotion diff and the three-way match output.

**Exercise 2 — Write the verification.** Implement `promotion-verify` for your environment: check that the digest exists, that the attestation names the trusted builder and that the source commit is on the protected branch. Then write three *negative* tests (an unknown digest, an attestation from an untrusted identity, a commit from an unmerged branch) and show each is rejected.

**Exercise 3 — Rollback drill.** Promote a deliberately bad digest to staging, measure the time to first signal, and recover by reverting the promotion through Git. Record the timeline and the runbook version used.

**Exercise 4 — Retention check.** List the digests referenced in the last ten promotions and verify that each is still pullable. Write the rule or alert that would warn you before retention deletes one.

**Exercise 5 — Ownership matrix.** Fill in a responsibility matrix for your platform. Highlight every seam with no owner or two owners, and propose a resolution for each.

**Exercise 6 — Stateful drills.** Run drills S1 and S2, record the timelines and improve one runbook based on what confused you.

**Exercise 7 — Trace from a symptom.** A colleague plants a change that makes the service return a different response than expected. Using only the walking-backwards routine, find the first mismatched stage. Write the sentence you would put in the ticket.

**Solution notes.**

*Exercise 1.* The evidence file should let a stranger replay the path. If any item is a screenshot of a configuration rather than output of observed behaviour, replace it.

*Exercise 2.* Expected rejections: an unknown digest fails the registry check; an untrusted identity fails certificate matching; an unmerged-branch commit fails the ancestry check. If a negative test passes when it should fail, the check has a gap, which is the finding.

*Exercise 3.* Typical timings: seconds for the controller to apply, minutes before a human notices. The gap between "signal exists" and "someone knows" is the improvement target; consider an alert on a failing rollout.

*Exercise 4.* A common finding is a retention rule that counts age rather than reference. The fix is to retain anything referenced by a commit within a defined window, and to alert on rules that would delete it.

*Exercise 5.* Two owners usually means each assumes the other acts; zero owners usually means the seam fell between teams. Resolve with one name and the authority to change it.

*Exercise 6.* Expect S1 to recover in tens of seconds and S2 to take longer, and for the runbook to be missing the verification query. Record the recovery time you observed, not the one you expected.

*Exercise 7.* A strong ticket sentence reads like "Running digest equals the promoted digest, but the promoted digest was built from commit X, which does not contain the fix: the break is between merge and build." Precision about the stage is the skill.
