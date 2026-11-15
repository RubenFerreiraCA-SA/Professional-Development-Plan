# T-DEV-05-B — Beginner Foundations

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-b"></a>
#### T-DEV-05-B — Beginner Foundations

## Why this matters

Writing code and building an image are only the first half of delivering software. The second half is making a particular version run, in a particular place, with particular settings, and being able to answer afterwards three plain questions: *what is running, who decided it should run, and how do we undo it?*

Teams that answer them from memory and shell history fail predictably: someone runs `kubectl apply` from a laptop with an old file, someone hot-fixes in a web console and forgets, and a month later nobody can say why staging differs from production.

**GitOps** is a working method that removes that class of failure. Instead of people or pipelines *pushing* changes into an environment, the desired state of the environment is written down in a Git repository, and a small program running inside the environment continuously *pulls* that description and makes reality match it. Every change is then a commit: reviewed, attributed, timestamped, and reversible.

This Beginner section assumes you can use a terminal and have met Git (T-DEV-01) and containers (T-DEV-02). It uses a small neutral service called `orders-api`; installing a controller waits for the Intermediate section. By the end you should be able to explain the loop, read the files that drive it, and make one safe change on a practice cluster.

## First principles: desired state and actual state

Every system you operate has two descriptions that can disagree.

| Description | Question it answers | Where it lives |
| --- | --- | --- |
| **Desired state** | "What do we *want* to be running?" | A document someone wrote: a manifest, a configuration file |
| **Actual state** (also *live* state) | "What is running *right now*?" | The cluster, the servers, the cloud account |

When you set a thermostat to 21 °C, you state a desired condition. The room has an actual temperature. The thermostat does not execute a one-off "heat the room" command; it measures, compares, and switches the heater on or off, repeatedly, forever. That repeated measure–compare–act cycle is a **control loop**, and the part that runs it is a **controller**.

Kubernetes is built entirely from such loops. You tell it "three replicas of this container"; a controller notices there are two, starts a third, and keeps watching. If a node dies and a replica disappears, the same controller starts another without being asked. This is the **declarative** style: you state *the end result*, not the steps.

The contrast is the **imperative** style:

Declarative configuration states the result (`replicas: 3` in a manifest); imperative commands (`kubectl scale … --replicas=3`) leave no durable record of intent.

Kubernetes already reconciles *inside* the cluster: it makes running Pods match the Deployment object. GitOps adds one more loop *outside* that: it makes the objects in the cluster match the files in Git. So there are two nested loops:

```text
 Git repository  ──(GitOps controller: reconcile)──▶  Kubernetes API objects
 (files)                                               (Deployments, Services …)
                                                               │
                                       (Kubernetes controllers: reconcile)
                                                               ▼
                                                      Running Pods and containers
```

Almost every confusing situation in this chapter comes down to *which loop is acting, and what is it comparing?*

## Reconciliation, step by step

**Reconciliation** is one pass of the loop. A GitOps controller performs four actions, then waits and repeats:

1. **Fetch** the desired state: clone or fetch the Git repository and read the files at a chosen path and revision.
2. **Render** them into plain objects: apply Kustomize overlays or Helm templating until the result is ordinary Kubernetes YAML.
3. **Compare** the rendered objects with what the cluster API reports (the *diff*).
4. **Act** on differences: create missing objects, update changed ones, and optionally delete objects that were removed from Git (*prune*). Then check that the workload becomes healthy.

Three properties make the loop trustworthy, and each one is easy to lose:

- **Idempotent.** Running a pass twice does the same as running it once. If nothing differs, nothing happens.
- **Eventual.** The loop converges *over time*. After a merge there is a delay (the polling interval plus apply time), during which Git and reality disagree. That is normal, not a failure.
- **Continuous.** It does not stop after a deploy. If someone later changes the live object by hand, the next pass sees a difference. That difference is called **drift**.

### A crude reconciler you can read in one minute

The idea is simple enough to sketch in a shell. This is a *teaching toy*, not something to run against production:

```bash
# Toy reconciler (practice cluster only). Read it, do not deploy it.
while true; do
  git pull --ff-only --quiet                       # 1. fetch desired state
  kubectl kustomize deploy/orders-api/overlays/staging > /tmp/desired.yaml   # 2. render
  kubectl diff -f /tmp/desired.yaml || true        # 3. compare (exit code 1 means differences)
  kubectl apply -f /tmp/desired.yaml               # 4. act
  sleep 60
done
```

A real controller does the same four things and adds authentication, status, health checks, safe pruning, retries and protection against two writers. Those additions are what you pay for when you adopt Flux or Argo CD.

## Git as audited desired state

Why Git, of all places, to hold the desired state? Because the properties you want from a deployment record are the ones Git already has:

| You need | Git provides |
| --- | --- |
| A history of every change | Commits, forever, with parents |
| Who changed it and why | Author, committer, message, linked pull request |
| Review before it takes effect | Pull requests, required approvals, code owners |
| A way back | `git revert`, or checking out an earlier commit |
| Proof nothing was tampered with | Content-addressed objects; signed commits and tags |
| A shared, offline-friendly copy | Cloning |

The result is an **audit trail you did not have to build**. Months later, "who changed the replica count of `orders-api` in production on 3 March, and who approved it?" is `git log -p -- deploy/orders-api/overlays/prod`.

Git records *intent*, not what *happened*; combine commit history with controller events (which commit was applied, when, and whether it became healthy) for a complete trail.

## What GitOps is, and what it is not

The word is used loosely, so draw the boundary before you build.

| GitOps **is** | GitOps **is not** |
| --- | --- |
| Desired state stored declaratively and versioned | "We keep some YAML in a repository somewhere" |
| Changes made only by editing that state (a pull request) | A pipeline that runs `kubectl apply` after tests; that is automated *push*, which is useful but a different model |
| An agent pulling and continuously reconciling | A tool that deploys once and never looks again |
| Drift detected and reported, or corrected | A guarantee that nothing can ever change by hand |
| One reviewed change path for all environments | A replacement for CI: building, testing and scanning still happen elsewhere |
| A way to make rollback a normal operation | A way to roll back *data*; see the limits below |
| A pattern that works with Flux, Argo CD and others | The name of one product |

Two misunderstandings cause most early disappointment.

**"GitOps replaces my pipeline."** It does not. CI answers *"is this change good, and what artifact does it produce?"* GitOps answers *"which artifact should each environment run?"* A typical flow has both: CI builds `registry.example.com/orders-api@sha256:3f1c…`, then a reviewed change updates the desired state to mention that digest, and the controller applies it.

**"GitOps means everything is in Git."** Not everything can be. Plain-text passwords must not be committed (Professional covers safe approaches), databases hold *data* rather than configuration, and the controller itself must be installed once by something else.

## Push versus pull

| Model | Who changes the cluster | Credential location | Audit trail |
| --- | --- | --- | --- |
| Push (imperative or pipeline-driven) | A human or CI job runs `kubectl` or API calls from outside | Cluster credentials stored in CI or on laptops | Scattered across CI logs and shell history |
| Pull (GitOps) | A controller *inside* the environment reconciles toward Git | Only read access to Git is needed; no external party holds cluster-admin | Commits plus controller events |

The security consequence is significant: a build server holding production administrator credentials is an attractive target, whereas in a pull model nothing outside can change production directly. The attack surface shifts to *who can merge to the desired-state repository*; that is why its access rules deserve more care than application code's. Merging there *is* deploying.

## Key terms

| Term | Meaning |
| --- | --- |
| Desired state | What Git says should be running. |
| Live state | What is actually running. |
| Reconciliation | One pass (or the repeated process) of comparing and converging. |
| Drift | Live state differs from desired state, for example because someone edited a resource by hand. |
| Prune | Delete live resources that were removed from desired state. |
| Self-heal | Automatically revert manual changes so the live state matches Git again. |
| Overlay | A small per-environment set of changes on top of a shared base. |
| Source | Where the controller reads from: a Git repository, and optionally a chart repository or registry. |
| Digest | The content hash of an image (`sha256:…`); it names exactly one image. |
| Health check | A test that decides when a deployed object counts as "Ready". |

## An annotated controller flow

Here is one reconciliation as a timeline, using Flux's vocabulary. Argo CD differs in names, not in shape; the Intermediate and Professional sections map the two.

```text
 ┌─────────── Developer ───────────┐
 │ 1. Edit overlay, open pull request │
 │ 2. Review, approve, merge to main  │      (humans decide; Git records)
 └───────────────┬─────────────────┘
                 ▼
 ┌──────────── Source controller ─────────────┐
 │ 3. Poll Git every interval (e.g. 1 minute) │   "Is there a new commit?"
 │ 4. Fetch it, store as a versioned artifact │   Failure here = SOURCE problem
 └───────────────┬────────────────────────────┘     (network, credentials, branch name)
                 ▼
 ┌───────── Kustomize controller ─────────────┐
 │ 5. Render the overlay at spec.path         │   Failure here = BUILD problem
 │ 6. Dry-run and diff against the cluster    │     (YAML error, bad path, missing file)
 │ 7. Apply the differences                   │   Failure here = APPLY problem
 │ 8. Prune what was removed (if enabled)     │     (permissions, invalid object, immutable field)
 │ 9. Wait for health checks (e.g. Ready)     │   Failure here = HEALTH problem
 └───────────────┬────────────────────────────┘     (image won't pull, probes fail)
                 ▼
 ┌────────────── Status and events ───────────┐
 │ 10. Report: "Applied revision main@sha1:…" │   You read this to know what happened.
 │ 11. Wait one interval, then go to step 3   │   Repeated forever; drift is corrected here.
 └────────────────────────────────────────────┘
```

Learn to name the stage. "The deploy didn't work" is not a diagnosis; "the render succeeded but the health check never passed because the image could not be pulled" is.

## Who owns what

A cluster is changed by several systems. Confusion arises when two of them believe they own the same object.

| System | Owns |
| --- | --- |
| Infrastructure as code (T-DEV-04) | The cluster itself, networks, identity foundations |
| Git desired-state directory | Workload definitions: Deployments, Services, configuration |
| GitOps controller (Flux, Argo CD) | Reconciling those definitions into chosen namespaces |
| CI pipeline | Building, testing, publishing artifacts and proposing digest updates; *not* applying to the cluster |
| Humans in an emergency | Break-glass changes, then returning ownership to Git |

The rule: **one owner per object.** If both a pipeline's `kubectl apply` and a GitOps controller manage the same Deployment, they will overwrite each other, and the cluster will flip between two versions.

## A first mental run

You change `replicas: 2` to `replicas: 3` in a file and open a pull request. Colleagues review and merge. About a minute later the controller notices a new commit, renders the manifests, compares with the cluster and creates the third replica. You never ran a deploy command. The controller reports "applied revision `abc123`". If someone then scales to five by hand, the next pass sees five versus three and, if self-heal is on, changes it back to three; if self-heal is off, it reports drift and leaves it to a human.

## Declarative configuration with overlays

A real service runs in several environments (staging, production) that are *almost* the same. Copying the entire manifest set per environment invites divergence. **Kustomize** keeps one shared **base** and small per-environment **overlays**:

```text
deploy/orders-api/
  base/
    deployment.yaml
    service.yaml
    kustomization.yaml
  overlays/
    staging/kustomization.yaml
    prod/kustomization.yaml
```

The base describes the service once:

```yaml
# deploy/orders-api/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
spec:
  replicas: 1                        # overlays override this
  selector:
    matchLabels: { app: orders-api }
  template:
    metadata:
      labels: { app: orders-api }
    spec:
      containers:
        - name: orders-api
          image: orders-api          # placeholder name; overlays pin the real image
          ports: [{ containerPort: 8080 }]
          readinessProbe:            # decides when traffic may arrive, and when "Ready" is true
            httpGet: { path: /health, port: 8080 }
            periodSeconds: 5
```

```yaml
# deploy/orders-api/base/kustomization.yaml
resources:
  - deployment.yaml
  - service.yaml
```

Each overlay says only what differs:

```yaml
# deploy/orders-api/overlays/staging/kustomization.yaml
resources: [../../base]
namespace: orders-staging
images:
  - name: orders-api
    newName: registry.example.com/orders-api
    digest: sha256:3f1c...e9a0       # shortened here; real digests have 64 hex characters
replicas:
  - name: orders-api
    count: 2
```

Production's overlay has the same shape with `namespace: orders-prod`, `count: 4` and its own digest; the difference between environments is a few reviewable lines.

You can preview any overlay locally without touching a cluster:

```bash
kubectl kustomize deploy/orders-api/overlays/staging          # prints the rendered YAML
diff <(kubectl kustomize deploy/orders-api/overlays/staging) \
     <(kubectl kustomize deploy/orders-api/overlays/prod)     # exactly how the environments differ
```

*Why a digest and not a tag?* A tag is a movable label: the same commit of desired state could deploy different code on different days. A digest names exactly one image, so the file is the audit record (T-DEV-02 explains both).

## A safe first change

Make your first change on a **practice cluster** (for example one created with `kind create cluster --name gitops-lab`) and a repository you may freely break. Never practise on a shared environment. The sequence is the same one you will use professionally; only the stakes differ.

1. **State the intent in one sentence.** "Change `orders-api` in staging from two replicas to three."
2. **Save the current rendered output** so you know your starting point:

   ```bash
   kubectl kustomize deploy/orders-api/overlays/staging > /tmp/before.yaml
   grep -n 'replicas\|image:' /tmp/before.yaml
   ```

3. **Create a branch** and make the smallest possible edit, one value:

   ```bash
   git switch -c staging-replicas-3
   # edit deploy/orders-api/overlays/staging/kustomization.yaml: count: 3
   git diff                                   # the diff should be one line
   ```

4. **Render again and compare.** Confirm that *only* the intended difference appears:

   ```bash
   kubectl kustomize deploy/orders-api/overlays/staging > /tmp/after.yaml
   diff /tmp/before.yaml /tmp/after.yaml      # expect exactly: replicas: 2 -> replicas: 3
   ```

   (Later you will use `flux diff`, which compares your rendered files with the *live* cluster rather than with an earlier render.)
5. **Commit with a message that says why**, push, and open a pull request:

   ```bash
   git commit -am "orders-api staging: scale to 3 replicas to test headroom under load"
   git push -u origin staging-replicas-3
   ```

6. **Review and merge.** In a team, someone other than the author approves. The merge *is* the deployment decision.
7. **Watch the loop work.** With a controller installed (next section) you would run `flux get kustomizations` and `kubectl get deploy -n orders-staging` and watch the count go from 2 to 3. Without a controller installed yet, use `kubectl apply -k` once as an *explicit stand-in* and note that you did the controller's job by hand.
8. **Prove the result, do not assume it.** Check three things: the controller (or you) reports success; the live object shows three replicas; three Pods are Ready.

   ```bash
   kubectl -n orders-staging get deploy orders-api
   kubectl -n orders-staging get pods -l app=orders-api
   ```

9. **Know your undo before you start.** The undo is `git revert <the commit>` through another pull request, not a hand edit in the cluster.

Most steps happen *before* anything touches the cluster: mistakes are caught while they are still text.

## What can go wrong

| Mistake | Symptom | What to do |
| --- | --- | --- |
| Editing the live object by hand "just this once" | The controller reverts it, or reports drift | Make the change in Git; if truly urgent, follow the emergency routine in Intermediate |
| Wrong `path` or file name in the overlay | Controller reports a build failure, nothing applies | Run `kubectl kustomize <path>` locally first |
| Using a tag, then the tag moves | Different Pods run different code | Pin by digest |
| Committing a secret as plain text | The secret is now in history *permanently* | Rotate it; do not just delete the line (Professional covers safe approaches) |
| Two systems manage one object | The object keeps flipping | Decide one owner |

**Applied is not Ready.** "Applied" means objects were created or updated; "Ready" means your health checks passed. A Deployment can be applied and still crash-loop.

## Knowledge consolidation

- **Desired state** is what you declared; **actual state** is what runs. A **controller** repeatedly compares and converges them.
- GitOps adds a loop *outside* Kubernetes: it makes cluster objects match files in Git. Kubernetes' own controllers then make Pods match those objects.
- A reconciliation pass is **fetch, render, compare, act**, and then a health check. It is idempotent, eventual and continuous.
- Git gives you an audit trail of **intent**; controller events give you the record of **what happened**. Use both.
- GitOps is **not** a replacement for CI, **not** a promise that everything lives in Git, and **not** a tool name.
- **Pull** keeps cluster credentials inside the environment; the new thing to protect is write access to the desired-state repository.
- Kustomize **overlays** express small, reviewable differences between environments; **digests** make versions exact.
- One owner per object. Name the stage (source, build, apply, health) where a problem occurs.
- Rehearse the undo before making the change.

## Exercises

**Exercise 1 — Render and diff.** Create the `orders-api` directory layout above with a base and two overlays. Render both overlays with `kubectl kustomize`, diff the outputs and list every difference. Explain why the digest, not a tag, appears in each overlay.

**Exercise 2 — Classify a failure.** For each situation, name the stage (source, build, apply, health) and the first thing you would check: (a) the controller reports it cannot clone the repository; (b) the controller reports a YAML parse error; (c) the Deployment is applied but Pods show `ImagePullBackOff`; (d) the apply fails with "field is immutable".

**Exercise 3 — GitOps or not?** For each, decide whether it is GitOps and justify: (a) a CI job runs `kubectl apply -f deploy/` after tests pass; (b) a controller in the cluster watches a repository and applies it, with self-heal off and a drift report; (c) YAML is stored in Git but an engineer applies it manually each release; (d) a controller applies whatever is on a developer's laptop.

**Exercise 4 — Safe first change.** Following the nine-step sequence above on a practice cluster, change one value in the staging overlay, verify it, then revert it through Git. Record the two commit identifiers and the observed live state after each.

**Solution notes.**

*Exercise 1.* Expect differences in namespace, replica count and digest only. The digest is there because a tag can be re-pointed; the overlay should identify exactly one image so the file is a faithful record of what runs. If you find other differences, ask whether they belong in the base.

*Exercise 2.* (a) Source: check credentials, URL and network access from within the cluster. (b) Build: render locally with `kubectl kustomize` to reproduce the error. (c) Health: the apply succeeded; check events and the image reference, then registry credentials. (d) Apply: some fields (for example a Deployment's selector) cannot be changed in place; the fix is a deliberate replacement, not repeated retries.

*Exercise 3.* (a) Automated push, not GitOps, although a perfectly reasonable pipeline. (b) GitOps, with drift reported rather than corrected. (c) Not GitOps; the state is in Git but nothing continuously reconciles. (d) Not GitOps; the source of truth must be a shared, reviewed repository, not a private machine.

*Exercise 4.* The two commits are the change and its revert; the revert should restore the earlier value exactly. If the live state does not match what Git says after you expected convergence, work down the stages: source, render, apply, health.
