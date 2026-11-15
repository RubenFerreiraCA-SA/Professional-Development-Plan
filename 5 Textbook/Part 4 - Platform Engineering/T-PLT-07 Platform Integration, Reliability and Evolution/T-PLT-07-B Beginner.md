# T-PLT-07-B — Beginner Foundations

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-b"></a>
#### T-PLT-07-B — Beginner Foundations

## Why this matters

Most engineering teams reach a point where every individual practice works. The repository has review rules. CI builds an image. A Terraform folder creates the network. A controller applies manifests to a cluster. A dashboard exists. Yet a new developer still needs two weeks and six people's help to ship one small change, and when a release goes wrong nobody can say quickly which layer broke.

That gap is what *integration* means. Each tool was chosen and configured on its own; the places where one tool hands something to the next were never designed, tested or owned. Those handover points — **seams** — are where most real defects live, and they are invisible if you inspect components one at a time.

This Beginner section teaches you to see a platform as a chain of components joined by seams, to follow a single change across all of them, and to ask one habitual question at every step: *what evidence would show another person that this works?* It assumes you have met the individual pieces (a Git repository, a container image, a pipeline, a Kubernetes cluster) at a basic level, but each is explained again in a sentence when it first appears. It uses a fictional service called `orders-api`; nothing here depends on any other course material.

## First principles: a platform is a set of contracts

Start with the plainest definition. A **platform**, in this context, is the set of shared tools and agreed paths that lets product teams build, ship and run software without each team reinventing the mechanics. A platform is not a product you install. It is an arrangement: a few components, a few rules about what passes between them, and a few people who look after the arrangement.

Two ideas make that arrangement manageable.

1. **Each component does one job and produces one kind of output.** The repository holds reviewed source. The build produces an image. The registry stores images. The delivery system turns desired state into running state. Monitoring turns running state into signals.
2. **Components talk through a small number of named artefacts.** An *artefact* is something concrete that can be named, stored and compared: a commit hash, an image digest, a manifest in Git, a log line, a status value. When you can name what crosses a boundary, you can check it.

The set of artefacts and the promises about them is the **contract** at that seam. For example: "The build publishes an image and records its digest; the promotion step may only reference digests that appear in that record." If a component breaks its side of the contract, the next component fails in a confusing way, far from the real cause.

Analogy, and its limit: a platform is like a relay race, lost at the baton exchange. The analogy fails because a platform's batons are passed thousands of times a week by automated runners nobody watches, so a small flaw repeats until someone notices.

## The seven pieces and what each one does

Seven kinds of component recur in almost every platform. Learn them as *jobs*, not product names; the products change.

| Piece | Its job | What it takes in | What it hands on | A plain question to ask it |
| --- | --- | --- | --- | --- |
| Repository | Hold source and desired state, with review rules | A proposed change | A reviewed, recorded commit | Who approved this and what did the checks say? |
| Image build | Turn a commit into a runnable package, once | A commit | An image with a unique digest, plus evidence about how it was built | Which commit produced this image? |
| Registry | Store images and serve them to clusters | An image | The same image, by digest, on request | Is the image the cluster pulled the image the build made? |
| Infrastructure | Create the network, cluster, storage and accounts that everything else runs on | Reviewed infrastructure code | A running environment | Who is allowed to change this and how do we know what changed? |
| Delivery | Turn "what we want" in Git into "what runs" in the cluster | Desired state in Git | Running Pods and a sync status | Does the cluster match Git, and if not, why? |
| Identity | Decide who or what may do each step | A credential or a signed token | An allow or a deny, plus an audit record | Who is this, and for what exact action? |
| Monitoring | Observe what is running and report health | Logs, metrics, traces, status | A signal a person or alert can act on | Is it healthy right now, and how do I know? |

An eighth thing sits across all seven: the **developer experience** (documentation, templates, error messages, support). If the entry document is wrong, the seam between platform and person is broken.

## A plain architecture walkthrough

Here is the whole thing in one picture. Read it from top to bottom as one change travelling to production, then read the labels on the right to see which artefact crosses each line.

```text
 Developer
    │  edits code, opens a pull request
    ▼
 ┌─────────────────────────┐
 │ 1. REPOSITORY           │  review rules + required checks
 └──────────┬──────────────┘  ── artefact: merge commit SHA
            ▼
 ┌─────────────────────────┐
 │ 2. BUILD (CI)           │  runs tests, builds once, records evidence
 └──────────┬──────────────┘  ── artefact: image digest sha256:…
            ▼
 ┌─────────────────────────┐
 │ 3. REGISTRY             │  stores the image, addressed by digest
 └──────────┬──────────────┘  ── artefact: digest-addressed image
            ▼
 ┌─────────────────────────┐
 │ 4. PROMOTION            │  a pull request that changes only the digest
 └──────────┬──────────────┘  ── artefact: desired state in Git
            ▼
 ┌─────────────────────────┐
 │ 5. DELIVERY CONTROLLER  │  compares Git to the cluster and applies it
 └──────────┬──────────────┘  ── artefact: Pods running that digest
            ▼
 ┌─────────────────────────┐
 │ 6. CLUSTER (runtime)    │  runs Pods on infrastructure from step 0
 └──────────┬──────────────┘  ── artefact: logs, metrics, traces, status
            ▼
 ┌─────────────────────────┐
 │ 7. MONITORING           │  shows health; a person or alert reacts
 └──────────┬──────────────┘
            ▼
   feedback: a defect or an idea becomes the next change at step 1

 Across every box:  IDENTITY decides who may act, and records that they did.
 Underneath step 6: INFRASTRUCTURE created the cluster, network and storage.
```

Notice what the picture does *not* show: a person copying a file onto a server. Ordinary changes move through reviewed, recorded steps.

**Walking the picture with a real change.** A developer changes a validation message in `orders-api`. Merging the pull request produces a commit on `main`. A trusted pipeline runs the tests, builds an image once and prints its digest. A promotion pull request edits one line in the desired-state repository: the digest. The controller rolls Pods to the new image, and logs and metrics start arriving from them. If an alert fires, the response ends with another commit, a fix or a revert, through the same path.

## The artefacts that cross each boundary

Every boundary in the walkthrough has one artefact that you can name and show. If you can show it, the boundary is *proven*; if you cannot, it is a guess.

| Stage | What happens | Artefact that crosses the boundary | Proof you can show |
| --- | --- | --- | --- |
| Change | Branch and commit | Commit SHA | `git log -1 --format=%H` |
| Review | Pull request with required review and checks | Merge commit on `main` | Pull request page showing the approval and green checks |
| Build | Trusted pipeline builds once | Image digest `sha256:…` | Pipeline run URL and the digest it printed |
| Artefact | Image stored in the registry | Digest-addressed image | `docker manifest inspect` or a registry listing |
| Deploy | Promotion changes only the digest; controller applies it | Desired state in Git | Promotion diff and controller sync status |
| Run | Pods start from that digest | Running Pod | `kubectl get pod -o jsonpath='{.items[*].status.containerStatuses[*].imageID}'` |
| Observe | Telemetry shows health | Logs, metrics, traces | Dashboard link and a log line mentioning the new version |

If the digest in the registry differs from the one in the Pod, the seam between build and deploy is broken, no matter how good each stage looks on its own.

## Digests, tags and "which version is running?"

The single most useful artefact in the whole chain is the **image digest**: a long hexadecimal fingerprint of the image content, written `sha256:…`. A **tag** such as `1.4.2` or `latest` is only a label that someone can move to point at a different image later. A digest cannot be moved; if the content changes, the digest changes.

This matters for integration because every later stage wants to answer the question "is this the thing the earlier stage made?" With tags the answer can be "probably". With digests the answer is "yes, byte for byte". That is why the promotion step changes *only a digest*: the reviewer sees one line change and can check that line against the pipeline's record.

You can see the difference yourself:

```bash
# What a tag points at today (it may point somewhere else tomorrow)
docker pull orders-api:1.4.2
docker inspect --format '{{index .RepoDigests 0}}' orders-api:1.4.2

# What a cluster is actually running, by digest (illustrative output follows)
kubectl get pod -l app=orders-api \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].imageID}{"\n"}{end}'
```

```text
orders-api-6d9c8b7f5-x2k4p    registry.example.com/orders-api@sha256:3f1a…c92e
orders-api-6d9c8b7f5-q8w7m    registry.example.com/orders-api@sha256:3f1a…c92e
```

Both Pods report the same digest, and that digest can be compared with the one the pipeline printed. If one Pod showed a different digest, a rollout is half-finished or something has been changed outside the normal path.

## Who is talking to whom: identity in plain terms

Every arrow in the walkthrough is an *actor* asking to do something, and not all actors are people: a developer opens and merges pull requests; the build pipeline pushes images; the delivery controller applies manifests; a running Pod reads its own credentials; an on-call person reads logs. Two beginner rules cover most of it. First, **give each actor only what its step needs**: the pipeline that publishes images does not need to modify the cluster, and the controller that modifies the cluster does not need to publish images. Second, **prefer short-lived credentials over long-lived passwords**, and keep secrets out of Git. For any step ask: *who or what is doing this, and could it do more than it needs to?*

## Where observability fits

Monitoring closes the loop. **Logs** (time-stamped text) say what an instance reported; **metrics** (numbers over time) show whether things are getting better or worse; **traces** (the path of one request) show where it spent its time. Add a plain **status command** that reports health, running version and last deploy time.

A signal is only useful if the *new* service actually reports. A common seam failure is a good dashboard that stays empty because the service never sent data, which looks identical to "everything is quiet". Make the status say `UNKNOWN` when there is no data, not `HEALTHY`.

## Integration debt compounds

Fix one layer at a time: get the stateless path green end to end before adding state, extra environments or extra capabilities. The seams between components — not the components — are where most defects live.

**What "integration debt" looks like.** It is the accumulated cost of components that each work but were never connected end to end: a template that creates a repository the pipeline cannot build; a pipeline that publishes a tag the cluster never pulls; dashboards that exist but show no data for the new service. Typical sources are two teams each assuming the other owns the seam, manual steps nobody wrote down, and "temporary" workarounds that became permanent.

Debt compounds because later work builds on top: each workaround for a missing digest record is another thing promotion, audit and rollback automation must carry.

**Why stateless first.** A stateless service has one dependency chain to verify and can be restarted without consequences. Databases add backups, migrations, credentials and failure recovery. If you add them while the basic path is still red, every failure has many possible causes. Get the plain path green, record the evidence, then add one complication at a time.

## Evidence, not claims

For each step ask: how would I show another person this works? A log line, a rejected change, a status output, a timeline. Collect it as you go. "The pipeline builds the image" is a claim; "run 4812 built it and printed this digest" is evidence for one build; "a pull request with a failing test could not be merged, here is the page" is evidence for a *control*. The last kind is the most valuable, because a platform is mostly defined by what it *prevents*.

## A first integration checklist

| Check | Evidence to keep |
| --- | --- |
| A service can be created by following the docs | The resulting repository and catalogue entry |
| A failing test blocks merge | The pull request with the red check |
| An image is built once and identified by digest | Run URL and digest |
| A promotion changes only a digest | The promotion pull request diff |
| The running Pod uses that digest | `kubectl` output showing the image ID |
| The service reports health | Status output |
| A planted failure is recoverable | Timeline and runbook version used |

**Applying the checklist.** For each row assign one of three marks:

| Mark | Meaning |
| --- | --- |
| Proven | You have a command output, link or log line you can show someone now. |
| Claimed | You believe it works but have no evidence yet. |
| Unknown | You have not looked. |

The *weakest seam* is the first stage whose mark is not "Proven" and whose failure would stop everything after it. That is where the next hour of work belongs.

## A guided walk: following one change with commands

Here is a minimal sequence you can run against a practice environment. Everything is illustrative; names and URLs will differ in yours. Keep a text file of what each command printed.

```bash
# 1. The commit: what exactly are we shipping?
git switch -c fix/validation-message
git commit -am "orders-api: clearer validation message"
git log -1 --format='commit=%H'

# 2. After merge and the pipeline run: what digest did the build print?
#    (copy it from the run output or the release summary)
DIGEST="sha256:3f1a...c92e"

# 3. Does the registry hold that exact digest?
docker manifest inspect "registry.example.com/orders-api@${DIGEST}" > /dev/null \
  && echo "registry: present"

# 4. Does the promotion diff touch only the digest line?
git diff --stat main...promote/orders-api-staging
git diff main...promote/orders-api-staging

# 5. Did the controller finish, and does the cluster match Git?
kubectl -n orders get deploy orders-api
kubectl -n orders rollout status deploy/orders-api --timeout=120s

# 6. What digest is the running Pod using?
kubectl -n orders get pod -l app=orders-api \
  -o jsonpath='{.items[*].status.containerStatuses[*].imageID}'
```

A healthy run ends with the digest from step 2 appearing, unchanged, in step 6. If it does not, work *backwards* from the Pod: was the promotion merged, did the controller sync, did the registry hold the image? The first stage whose answer does not match is the broken seam.

## A first failure, planted on purpose

A path that has only been shown working has not been shown *recoverable*. Once the plain path is green, promote a digest whose image exits immediately. Pods fail to become Ready, the rollout stalls and the old Pods keep serving. Recover by reverting the promotion pull request, the same path used to deploy, and record a timeline.

```text
10:02  promotion PR merged (digest sha256:bad9…)
10:03  new Pods CrashLoopBackOff; old Pods still serving
10:09  engineer notices status DEGRADED
10:11  revert PR merged
10:12  controller reconciles to previous digest; Pods Ready
```

The numbers are illustrative. What matters is that you *have* a timeline and every action went through Git.

## What can go wrong: common mistakes and how they look

| Mistake | How it looks | First check |
| --- | --- | --- |
| Declaring the path "done" because each team's component passed its own tests | Everything is green, yet a new service cannot reach production | Walk the whole path with one new service |
| Verifying by reading configuration instead of observing behaviour | The manifest says one image; the cluster runs another | Compare the Pod's image ID, not the manifest |
| Using mutable tags such as `latest` | A rebuild changes behaviour with no change in Git | Record and compare digests |
| Skipping the failure step | The first real failure is also the first rehearsal | Plant one failure and recover through the runbook |
| A dashboard with no data treated as "quiet" | Silence during an outage | Make the status `UNKNOWN` without data |
| Two teams each assuming the other owns the seam | A recurring problem nobody fixes | Write down one owner per seam |

## Reading a status report honestly

A status that only says `OK` is weaker than one that names the version, shows how fresh its data is and can say `UNKNOWN`. When you build or review a status view, check those three properties.

## Knowledge consolidation

- A **platform** is components plus the **contracts** at the seams between them, plus people who own them. Most defects live at the seams.
- The recurring pieces are **repository, build, registry, infrastructure, delivery, identity and monitoring**, and the developer experience across them.
- Follow **one artefact** across each boundary: commit SHA, image digest, desired state, running Pod, telemetry.
- **Tags move; digests do not.** Promotion should change only a digest so reviewers can check it.
- Give each actor only the **permissions its step needs**, and keep secrets out of Git.
- **Silence is not health.** A status that cannot say `UNKNOWN` will say `HEALTHY` when it should not.
- Get the **stateless path green first**, then add state, environments and capabilities one at a time.
- Collect **evidence as you go**. The most valuable evidence shows something unsafe being stopped.
- A path shown working is not yet shown **recoverable**; plant a failure and recover through the normal path.

## Exercises

**Exercise 1 — Draw your path.** Draw the path for your own service (or a practice service) as seven boxes. Under each box write the artefact leaving it and one proof command. Mark each box Proven, Claimed or Unknown and circle the weakest seam.

**Exercise 2 — Walk the path.** Walk the path with a small example service. For each step, write the one command or link that proves it. Keep the real output in a text file.

**Exercise 3 — Name the owner.** For each of the six seams in the walkthrough (repository→build, build→registry, registry→promotion, promotion→controller, controller→cluster, cluster→monitoring) write one sentence: what is the contract, and who would you ask if it broke? Mark any seam where you cannot name an owner.

**Exercise 4 — Tag versus digest.** Pull a public image by a version tag, record its digest, pull it again by digest, and explain in three sentences why a promotion pull request should contain the digest rather than the tag.

**Exercise 5 — A silent dashboard.** Pick a dashboard or status view you use. Stop the data source (or look at it for a service that does not report) and record what the view shows. Write the change that would make it say `UNKNOWN`.

**Exercise 6 — Plan a failure.** Choose one planted failure from this section. Write down in advance what you expect to see at each stage, then run it and compare. Record one surprise.

**Solution notes.**

*Exercise 1.* Label each arrow with an artefact ("image digest", not "Docker"). The weakest seam is the *earliest* non-proven box whose failure blocks later ones, not simply the one that worries you most.

*Exercise 2.* Expect to improvise at least one step the documentation did not mention; each is an integration finding.

*Exercise 3.* Cluster→monitoring is often unowned. An unowned seam is a finding, not an error in the exercise.

*Exercise 4.* A tag can be re-pointed, so two clusters pulling "the same tag" could run different code. The digest lets a reviewer compare one line against the pipeline's record.

*Exercise 5.* Track the *freshness* of the data and show `UNKNOWN` beyond a threshold of a few reporting intervals.

*Exercise 6.* Surprises usually concern timing or the number of places you had to look; both inform the status view and the runbook.
