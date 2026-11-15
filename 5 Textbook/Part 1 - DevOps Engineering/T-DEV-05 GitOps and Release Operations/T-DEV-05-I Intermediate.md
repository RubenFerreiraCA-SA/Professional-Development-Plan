# T-DEV-05-I — Intermediate Practice

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-i"></a>
#### T-DEV-05-I — Intermediate Practice

## Why this matters

At Beginner level the controller was a diagram. Now you install one, point it at a repository, and meet the situations that make GitOps real work: a sync that fails at 17:55, a Deployment that keeps reverting your change, a release that must be undone *now*, and the question "is production actually running what Git says?"

This section teaches the daily skills: installing and configuring a controller, reading its status, feeding it Kustomize and Helm inputs, structuring environments, handling drift and failed syncs, promoting a version through Git, and rolling back safely. The examples use Flux, with the Argo CD equivalents mapped alongside, because the concepts are shared and the vocabulary is the only real difference. API versions shown were current when this text was written; confirm them on your cluster with `kubectl explain` or `kubectl api-resources` before copying.

Use an isolated practice cluster throughout. The commands are written for `kind`, but any disposable cluster works.

## Setting up a practice lab

```bash
kind create cluster --name gitops-lab
kubectl cluster-info --context kind-gitops-lab
flux check --pre                        # verifies versions and cluster access before installing
```

Install the controller by *bootstrapping*, which commits the controller's own manifests into your repository and then makes the controller reconcile itself from there:

```bash
export GITHUB_TOKEN=<a short-lived personal token with repository access>
flux bootstrap github \
  --owner=example-org --repository=orders-platform \
  --branch=main --path=clusters/lab --personal
flux check                               # all controllers should report ready
```

Bootstrap writes a `clusters/lab/flux-system/` directory (controller manifests, a `GitRepository` and a root `Kustomization`) and configures a Git credential, normally a deploy key. Two lessons follow.

First, **bootstrap and reconcile have different privileges.** Bootstrap needs write access *once* to commit configuration. Reconcile needs only to *read* the desired state, forever. After bootstrap, make sure the credential stored in the cluster is a read-only deploy key (unless you use image-update automation, which needs write access to one branch), and revoke the broad token you used. A controller that holds a write-capable administrator token can alter the very repository that governs it.

Second, **the controller is itself under GitOps.** Its version and settings are files in `clusters/lab/flux-system/`. Upgrading it is a pull request. Deleting that directory, and the `prune` setting that follows, can remove the controller; the lab is the place to learn that safely.

## The Flux objects, one by one

Flux is a set of cooperating controllers, each with its own resource. The two you write most often are a *source* and a *Kustomization*.

### Source: where the desired state comes from

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata: { name: orders-platform, namespace: flux-system }
spec:
  interval: 1m                          # how often to check for new commits
  url: ssh://git@github.com/example-org/orders-platform
  ref: { branch: main }
  secretRef: { name: flux-system }      # the read-only deploy key
```

The source controller fetches the repository, packages the content as an *artifact* tagged with the revision, and exposes it to the other controllers. It does not apply anything. A source failure (unreachable host, wrong branch, rejected key) therefore blocks everything downstream while leaving the last applied state running unchanged.

Sources come in several kinds, chosen by where your desired state or packaged inputs live:

| Source kind | Holds | Typical use |
| --- | --- | --- |
| `GitRepository` | Manifests, overlays, charts | Your own desired-state tree |
| `HelmRepository` | An index of packaged charts | Third-party software |
| `OCIRepository` / `HelmRepository` of type OCI | Manifests or charts stored as OCI artifacts in a registry | Immutable, signed, digest-addressable configuration |
| `Bucket` | Files in object storage | Special cases only |

An OCI source is worth knowing about: CI publishes a *rendered* configuration artifact to a registry, the controller pulls it by digest, and the desired state becomes as immutable as an image. Git remains the review and history system; the registry becomes the delivery channel.

### Kustomization: what to apply, and how to judge it

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: { name: orders-staging, namespace: flux-system }
spec:
  interval: 5m                          # how often to re-check live state against the artifact
  retryInterval: 1m                     # how soon to retry after a failure
  sourceRef: { kind: GitRepository, name: orders-platform }
  path: ./deploy/orders-api/overlays/staging
  prune: true                           # delete objects removed from Git
  wait: true                            # wait for applied objects to become ready
  timeout: 3m
  targetNamespace: orders-staging
  serviceAccountName: orders-staging-reconciler    # applies with these permissions, not cluster-admin
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: orders-api
      namespace: orders-staging
```

Read the fields as a contract. `sourceRef` and `path` say *what*. `interval` says how quickly drift is noticed; `retryInterval` says how persistently failures are retried. `prune` controls deletion. `wait` and `healthChecks` define "success" as *healthy*, not merely *applied*. `serviceAccountName` limits the blast radius: the controller impersonates that account, so a mistake in this path cannot create objects the account may not create. Note the two timing knobs are independent from the Git `interval`: a new commit is noticed at the source interval, but live drift is re-checked at the Kustomization interval.

Create one Kustomization per environment so staging and production reconcile, fail and are suspended independently. Order them only when you mean to:

```yaml
spec:
  dependsOn:
    - name: platform-addons               # e.g. CRDs and controllers this workload needs
```

`dependsOn` makes one Kustomization wait until another is Ready. Use it for real prerequisites (custom resource definitions must exist before objects of that kind); do not use it as a poor man's promotion mechanism, because "staging healthy, therefore production may proceed" is a *release decision* and belongs in a reviewed change.

### Argo CD: the same ideas under other names

| Concept | Flux | Argo CD |
| --- | --- | --- |
| Where to read | `GitRepository` | `Application.spec.source.repoURL` and `targetRevision` |
| What to apply | `Kustomization.spec.path` | `Application.spec.source.path` |
| Where to apply | `targetNamespace` and cluster | `Application.spec.destination` |
| Permissions boundary | `serviceAccountName` | `AppProject` (allowed repositories, namespaces, kinds) |
| Delete removed objects | `prune: true` | `syncPolicy.automated.prune: true` |
| Revert manual change | Default for managed fields | `syncPolicy.automated.selfHeal: true` |
| Force a pass now | `flux reconcile …` | `argocd app sync <name>` |
| Pause | `flux suspend …` | Disable automated sync |
| Health result | Condition `Ready`, `healthChecks` | Health status plus sync status |

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: orders-staging, namespace: argocd }
spec:
  project: orders
  source:
    repoURL: https://github.com/example-org/orders-platform
    targetRevision: main
    path: deploy/orders-api/overlays/staging
  destination: { server: https://kubernetes.default.svc, namespace: orders-staging }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=false]
```

Argo CD reports two separate axes you should keep apart: **Sync** (does live match Git?) and **Health** (are the workloads working?). An application can be *Synced* and *Degraded* (matches Git, but broken), or *OutOfSync* and *Healthy* (works, but someone changed it). Flux folds both into one `Ready` condition with a message, so read the message.

## Feeding the controller: Kustomize and Helm inputs

The controller does not care how YAML is produced, only that rendering succeeds. Two producers dominate.

**Kustomize** transforms plain YAML by overlay and patch (see Beginner). The rule for production use is to keep patches *small and named*: a strategic-merge or JSON patch that changes one field is reviewable; a copy of the whole Deployment with two lines changed is not.

```yaml
# overlays/prod/kustomization.yaml (excerpt)
patches:
  - target: { kind: Deployment, name: orders-api }
    patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: 512Mi
```

**Helm** packages parameterised templates. With Flux you do not run `helm install`; you declare a release and let the Helm controller reconcile it:

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata: { name: ingress, namespace: platform }
spec:
  interval: 10m
  chart:
    spec:
      chart: ingress-nginx
      version: "4.x"                     # a range is convenient; an exact version is reproducible
      sourceRef: { kind: HelmRepository, name: ingress-nginx, namespace: flux-system }
  values:
    controller: { replicaCount: 2 }
  valuesFrom:
    - kind: ConfigMap
      name: ingress-values-prod          # environment-specific values live in their own object
  install: { remediation: { retries: 3 } }
  upgrade: { remediation: { retries: 3, remediateLastFailure: true } }
```

Four habits keep Helm manageable under GitOps:

1. **Pin chart versions exactly** in production, or you hand the upgrade decision to the chart publisher. If you want automatic updates, make them a pull request.
2. **Keep values small and in Git**; never hand-edit a release with `helm upgrade`, because the controller will reconcile it back and you will have a confusing divergence between release history and Git.
3. **Render before you merge**: `helm template` with your values, or `flux build`, produces what will be applied, so reviewers can read it.
4. **Understand failure remediation.** A failed Helm upgrade can roll itself back, leaving a release at its previous revision while Git says otherwise. Configure remediation explicitly and alert on it; "the controller quietly rolled back" is a valid outcome you must be able to see.

### Variable substitution and its limits

Flux can substitute `${variables}` into manifests (`postBuild.substitute` or `substituteFrom` a ConfigMap), which helps with per-cluster values such as domain names. Use it sparingly: every variable is an input the reviewer cannot see in the diff. Prefer overlays for structure and substitution for a few cluster-specific strings, and remember that an unset variable can silently render as an empty string unless you configure strictness.

## Environments

Several arrangements work, and the choice matters for review and drift:

| Arrangement | How it looks | Review experience | Risk |
| --- | --- | --- | --- |
| Directory per environment (one branch) | `overlays/staging`, `overlays/prod` | One diff shows both; easy to compare | Everyone with merge rights can touch production |
| Branch per environment | `staging` and `main` branches | Promotion is a merge | Branches drift; merges carry unrelated changes |
| Repository per environment | Separate repositories | Strong access separation | Harder to compare and to automate |

For most teams, **directory-per-environment on one branch, with code-owner rules on the production directory**, is the best start: environment differences are plain files, comparison is `diff`, and production approval is enforced by path ownership rather than by convention.

Keep environments *structurally* identical and *numerically* different. If staging has one Deployment and production has three Deployments, staging stops being a rehearsal. Review each overlay for what is allowed to differ (replicas, resources, hostnames, digest during promotion) and treat anything else as a smell.

## Promotion through Git

Promotion is not a deployment command; it is a reviewed change to desired state.

| Actor | May do |
| --- | --- |
| CI release job | Publish `image@sha256:…` plus evidence (tests, scan, provenance) |
| Bot or human | Open a pull request changing one overlay's digest |
| Reviewer | Approve staging; a code owner approves production |
| Controller | Pull and reconcile each environment |
| CI with cluster-admin | Not required, and a warning sign |

Promote the *same digest* from staging to production by changing only the digest line in the production overlay. Then verify both environments run it:

```bash
kubectl -n orders-staging get deploy orders-api -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
kubectl -n orders-prod    get deploy orders-api -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

If the strings differ, one of three things is true: the change has not reconciled yet, reconciliation failed, or someone changed a live object. The controller's status tells you which.

Never rebuild for production. A rebuilt image is a *different artifact* that happens to share a commit; the thing you tested is the thing you promote.

## Reading controller signals

A diagnosis starts by classifying the failure stage (see the Beginner flow):

```bash
flux get sources git                     # source stage: is the revision fetched?
flux get kustomizations                  # build, apply and health: is it Ready, and why not?
flux get helmreleases -A                 # Helm-managed workloads
flux events --for Kustomization/orders-staging
kubectl -n flux-system logs deploy/kustomize-controller --tail=50
flux tree kustomization orders-staging   # what objects this Kustomization owns
flux trace deployment/orders-api -n orders-staging   # which Git source and path produced this object
```

*Illustrative* shapes of what you will see:

```text
NAME             REVISION              SUSPENDED  READY  MESSAGE
orders-staging   main@sha1:9c3e1b7     False      True   Applied revision: main@sha1:9c3e1b7
orders-prod      main@sha1:9c3e1b7     False      False  Health check failed after 3m0s: Deployment orders-prod/orders-api status: 'InProgress'
```

Read the second line precisely. The revision *was applied* (the objects exist), and the failure is at the health stage: the new Pods did not become Ready within the timeout. The right next step is not "re-run the deploy" but `kubectl -n orders-prod describe deploy orders-api`, the Pod events and the logs.

`flux trace` answers a question beginners often ask in reverse: "this Deployment is wrong; where does it come from?" It follows the labels the controller adds to the object back to the Kustomization, the source and the revision.

To force an immediate pass instead of waiting for the interval:

```bash
flux reconcile kustomization orders-staging --with-source
```

and to see what *would* change before merging a pull request:

```bash
flux diff kustomization orders-staging --path ./deploy/orders-api/overlays/staging
```

`flux diff` compares your local rendering with the live cluster, which makes it the most useful pre-merge check.

## Drift

**Drift** is any difference between live objects and the desired state. Some drift is accidental (a console edit), some is *legitimate* (an autoscaler changing `replicas`). Distinguishing them is a core skill.

Observe the cause-and-effect yourself:

```bash
kubectl -n orders-staging scale deploy/orders-api --replicas=5
kubectl -n orders-staging get deploy orders-api -w     # watch it return to Git's value
```

With the controller running and the Kustomization interval at five minutes, the revert happens at the next reconciliation (or immediately with `flux reconcile`). In Argo CD with self-heal enabled, the application reports *OutOfSync* and is corrected; with self-heal off, it only reports.

### Legitimate drift and field ownership

Kubernetes tracks *which actor owns which field* (server-side apply, "managed fields"). Flux applies with field manager `kustomize-controller` and takes ownership of fields it declares. A field it does **not** declare can be owned by someone else without conflict. This is how an autoscaler can safely manage `replicas` only if Git does *not* declare `replicas`:

```bash
kubectl -n orders-staging get deploy orders-api -o yaml --show-managed-fields | less
```

If your overlay sets `replicas: 2` *and* a HorizontalPodAutoscaler also writes replicas, the controller and the autoscaler fight: every reconcile resets the count to two and the autoscaler raises it again. The fix is to **remove `replicas` from the Deployment in Git** and let the autoscaler own it. In Argo CD the equivalent is `ignoreDifferences` for `/spec/replicas`. The general rule: *for every field, exactly one writer*.

### Emergency changes: suspend, fix, commit, resume

During an incident you may need a live change that Git cannot yet carry. A silent console edit is wrong because the controller will undo it, or worse, because nobody will know. The explicit routine is:

```bash
flux suspend kustomization orders-prod         # 1. stop reconciling (record the time and the ticket)
kubectl -n orders-prod set image deploy/orders-api orders-api=registry.example.com/orders-api@sha256:<known-good>   # 2. the minimal live fix
# 3. verify recovery
# 4. commit the same change to Git through a pull request (expedited review is fine)
flux resume kustomization orders-prod          # 5. resume; the live state now matches Git
```

Suspension is an **explicit exception**: it needs an owner, a ticket and a time limit, and a suspended Kustomization should appear in monitoring. Flux shows `SUSPENDED True` in `flux get`; an alert on suspension longer than a few hours catches forgotten exceptions. If you resume *before* committing, the controller reverts your fix and the incident returns.

## Failed syncs

When reconciliation fails, work by stage. The controller retries on its own, so the question is whether retrying can ever succeed.

| Stage | Typical message | Likely cause | First action | Retrying alone helps? |
| --- | --- | --- | --- | --- |
| Source | `authentication required`, `couldn't find remote ref` | Revoked key, wrong branch or URL | `flux get sources git`; check the secret and the branch | Only if the outage was transient |
| Build | `kustomize build failed`, `no such file` | Wrong `path`, invalid YAML, missing resource | `kubectl kustomize <path>` locally | No; fix Git |
| Apply | `field is immutable`, `forbidden`, `no matches for kind` | Selector change, missing permission, missing CRD | Read the exact object in the message; check `dependsOn` and RBAC | No, unless a prerequisite appears |
| Health | `InProgress`, `Progressing` timeout | Bad image, failing probes, quota | `describe` and events on the workload | No; the workload is unhealthy |
| Prune | Deleted something unexpected | Ownership overlap | Restore from Git; fix ownership | Not applicable |

Three subtleties:

**A failed apply can leave a partially applied state.** The controller applies a set of objects; if the fifth fails, the first four may already be live. Read what changed, not just that something failed. For a risky change, make the set small.

**Health failure does not roll back by itself.** With plain Deployments, the Kubernetes rolling update keeps the *old* Pods serving while the new ones fail readiness, which is protective, but the Deployment object stays at the *new* spec. Git still says "new". Rolling back is a decision you make in Git.

**Immutable fields need a replacement.** Changing a Deployment's `spec.selector` or a Job's template fails because those fields cannot be updated in place. Flux can recreate objects with `force: true`, which deletes and re-creates them (with downtime). Use it knowingly, for one object, not as a blanket setting.

### Image pull paths

The commonest health failure is `ImagePullBackOff`. On a local `kind` cluster, `kind load docker-image` places an image on the nodes directly, which only works for the lab. For a registry the **kubelet** needs credentials: `imagePullSecrets` on the Pod or ServiceAccount, or node or workload identity. Your laptop's `docker login` does not transfer to the cluster. Pinning a digest in a private repository without those credentials produces `ImagePullBackOff` with `pull access denied` or `unauthorized` in the Pod events.

```bash
kubectl -n orders-staging describe pod -l app=orders-api | sed -n '/Events:/,$p'
```

## Safe rollback

Rollback in GitOps means **moving desired state back**, so that the controller moves live state back. The method is `git revert`:

1. **Record what you shipped.** For every release, note the commit SHA of the change that introduced it. (Pull request merge commits are convenient; the pull request page holds the evidence.)
2. **Revert exactly that commit** on the branch the controller watches:

   ```bash
   git switch main && git pull --ff-only
   git revert <release-commit-sha>             # for a squash or ordinary commit
   # for a merge commit: git revert -m 1 <merge-sha>
   git push                                    # or open an expedited pull request
   ```

3. **Let the controller reconcile**, or force a pass: `flux reconcile kustomization orders-prod --with-source`.
4. **Verify the live digest and health**, not merely that the push succeeded.

Why not `git revert HEAD`? Other changes may have landed since the release, and HEAD may not be the one that broke things. Why `revert` rather than `git reset` plus force-push? A revert is a *new* commit, so history stays append-only and the audit trail remains intact; rewriting a branch that a controller watches also confuses it and erases the record of what ran.

Alternatives and their traps:

| Tool | What it does | Trap |
| --- | --- | --- |
| `kubectl rollout undo` | Reverts the live Deployment to the previous ReplicaSet | The controller reverts your undo at the next pass, because Git still says "new" |
| `argocd app rollback` | Syncs to a previous deployed revision | Does not work with automated sync enabled; Git still disagrees |
| `helm rollback` | Restores a previous release revision | Same: Git still wins, and release history diverges |
| Point the controller at an older commit | Pins `ref` to a prior revision | Fast, but you have stopped following the branch; track it and restore it |

All of these are valid as *tactical* steps inside an emergency suspension, followed by a Git change. None replaces the Git change.

**What rollback cannot do.** Reverting manifests reverts *code and configuration*. It cannot reverse a database migration that already ran, nor un-send an email. T-DEV-05-P treats this limit in depth; for now, before rolling back, ask: "Did this release change data in a way the old version cannot read?"

## Troubleshooting guide

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Kustomization not Ready | Bad path, YAML or authentication | `flux get`; `kubectl kustomize` locally |
| Source never updates | Wrong branch, revoked key | `flux get sources git`; the secret |
| `ImagePullBackOff` | Missing image, private registry without credentials, wrong digest | Pod events; pull secrets |
| `CrashLoopBackOff` | Application or configuration error | Logs; are probes too aggressive? |
| Revision applied, workload unhealthy | The release is bad | `describe`, events, logs; then revert |
| Object keeps reverting | Self-heal or Flux overwriting a manual edit | Make the change in Git, or suspend explicitly |
| Replica count flaps | Two writers (Git and autoscaler) | Remove `replicas` from Git; check managed fields |
| Remains drifted | Reconciliation suspended | `flux get`; resume after committing |
| Prune deleted a shared object | Ownership mistake | Restore from Git; document owners |
| Autoscaler shows unknown metrics | No metrics server | `kubectl top`; install one |
| `no matches for kind` | CRD not installed yet | `dependsOn` a Kustomization that installs it |

## Knowledge consolidation

- **Bootstrap writes once; reconcile only reads.** Reduce the credential to read-only after bootstrap and revoke the broad token.
- A **source** fetches; a **Kustomization** applies and judges health. Each has its own interval and failure modes.
- Define success as **healthy**, with `wait` and `healthChecks`, not merely applied. Use a **service account** to limit the controller's reach.
- Kustomize patches stay small; Helm charts are pinned, values live in Git, and remediation is configured and alerted on.
- **Directory-per-environment** with path-based code owners is a strong default; keep environments structurally identical.
- **Promote the same digest** by pull request; never rebuild for production.
- Classify failures by stage: source, build, apply, health. Only some are fixed by retrying.
- **Drift** may be legitimate; give each field exactly one writer. Emergencies use an explicit suspend, fix, commit, resume routine.
- Roll back with `git revert <recorded sha>`; imperative undo commands are tactical and temporary.
- Rollback restores configuration, not data.

## Exercises

**Exercise 1 — Bootstrap and hand over.** Create a `kind` cluster and bootstrap a controller against a practice repository. Inspect the credential stored in the cluster, confirm it is read-only, and revoke the bootstrap token. Show the controller still reconciles a new commit afterwards.

**Exercise 2 — Two environments.** Create staging and production Kustomizations from the `orders-api` overlays. Give each a service account limited to its namespace. Promote one digest from staging to production by pull request, and verify both environments run it with the `jsonpath` commands above.

**Exercise 3 — Break a release on purpose.** Change the staging digest to one that does not exist. Diagnose from controller status, events and Pod events which *stage* failed. Record the exact messages. Then recover using `git revert` of the recorded commit and confirm Ready.

**Exercise 4 — Drift and ownership.** Scale a Deployment by hand and observe the revert. Then add a HorizontalPodAutoscaler while leaving `replicas` in the overlay, observe the flapping, and fix it by removing `replicas` from Git. Show the field ownership before and after.

**Exercise 5 — Emergency routine.** Simulate an incident: suspend production, apply a live fix, commit the same fix, resume. Run it twice, the second time resuming *before* committing, and describe the difference.

**Exercise 6 — Compare rollback tools.** For one broken release, try `kubectl rollout undo` while reconciliation is active, then `git revert`. Record what each did over the next two intervals.

**Solution notes.**

*Exercise 1.* Expect a secret in `flux-system` containing the deploy key; the key's GitHub setting should be read-only unless you enabled image automation. Reconciliation of a new commit after the token is revoked proves the credential split worked. Details of the key name vary with how you bootstrapped.

*Exercise 2.* A service account bound to a namespaced role should be unable to create a ClusterRole; try adding one to the path and read the `forbidden` error, which is the control working. Both `jsonpath` outputs should show the same `@sha256:` reference once reconciled.

*Exercise 3.* Source and build stages should be fine; apply succeeds; the health stage fails with a timeout, and the Pod events show `ErrImagePull` or `ImagePullBackOff`. Old Pods keep serving during the failure. After the revert and reconcile, the Kustomization returns to Ready at the previous digest.

*Exercise 4.* Managed fields show `kustomize-controller` owning `spec.replicas` before the autoscaler is added, and a second manager (the controller manager or HPA) writing it during the flapping. After removing `replicas` from Git, only the autoscaler writes it. Output formatting varies by version.

*Exercise 5.* In the first run the fix persists until the commit lands and resume causes no change. In the second, resuming first lets the controller revert the live fix to Git's value, so the incident recurs. The lesson is the order: Git first, then resume.

*Exercise 6.* `kubectl rollout undo` appears to work for a moment, then the controller reapplies the Git version at the next reconciliation (or you see drift reported if self-heal is off). `git revert` produces a durable change. Timing depends on your intervals; record them.
