# T-PLT-04-B — Beginner Foundations

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-b"></a>
#### T-PLT-04-B — Beginner Foundations

## Why this matters

Deploying an application to Kubernetes is the easy part. The hard part is a Tuesday afternoon when a service that worked yesterday returns errors and a colleague asks, "is it the cluster or is it us?" You have to answer with evidence, not a guess. Kubernetes offers many places for something to go wrong (images, scheduling, probes, networking, storage, quotas, nodes) and many places to look. Without a method, beginners restart everything and hope, or stare at one log file for an hour.

This section teaches a method: the vocabulary of **day two**, then a small, safe, read-only routine built on pod status, events, logs and `describe`. It explains what common status words mean, how scheduling and health problems appear as symptoms, which commands are safe on a shared cluster, and ends with a complete troubleshooting walkthrough.

You need `kubectl`, a practice cluster (kind or minikube is ideal) and the habit of writing down what you see. Examples use a neutral service `orders-api` in the namespace `orders-staging`. Outputs marked *illustrative* show the expected shape, not measured results; columns and wording vary by version and provider.

## What "day two" means

Day zero is design, day one is the first deployment, and **day two is everything afterwards**: access changes, capacity limits, incidents, patching, upgrades, backups and handover. A platform team is judged here, because day one only has to work once.

| Concern | The question a runbook must answer |
| --- | --- |
| Access | Who can change what, and how do I revoke it? |
| Fairness and capacity | What stops one namespace consuming the cluster? |
| Safety rails | What stops an unsafe workload being admitted? |
| Incidents | How do I get from symptom to cause quickly? |
| Maintenance | How do I take a node out without an outage? |
| Recovery | What do I restore, from where, in what order, how long? |
| Change | How do I move to the next Kubernetes version? |

The four levels of this chapter climb that list. The Beginner emphasis is **incidents**: reaching a cause from a symptom using read-only commands.

## First principles: failures are broken promises

Kubernetes works by **reconciliation**. You declare desired state ("three replicas of this image"); controllers compare it with observed state and act to close the gap. So almost every failure is a place where a controller *wants* to act and cannot. The useful question is "which step of the chain is stuck, and what does that step say?"

```text
Deployment -> ReplicaSet -> Pod -> scheduled to a Node -> image pulled
  -> container started -> probes pass -> Pod Ready -> listed as an Endpoint
  -> Service routes traffic -> client succeeds
```

Each arrow is a handoff that leaves evidence, usually an **event** or a **status condition**. Troubleshooting is walking the chain left to right until you find the first arrow that did not happen. Two rules follow:

1. **The first broken link matters; later symptoms do not.** A Service with no endpoints is a symptom; the cause may be three arrows upstream.
2. **Kubernetes tells you what it knows only if you ask in the right place.** A container's logs say nothing about why it was never scheduled; the scheduler's event does.

Analogy and limit: it is like tracing a parcel, where the last scan says where it stopped. The analogy fails because Kubernetes events *expire* (about an hour by default), so capture evidence while you can.

## The four sources of evidence

| Source | Command | Answers |
| --- | --- | --- |
| Status | `kubectl get pods` | What state does Kubernetes say this is in? |
| Describe | `kubectl describe pod <pod>` | Conditions, container states, last termination reason, **events** |
| Events | `kubectl get events` | What did controllers and the kubelet just try? |
| Logs | `kubectl logs <pod>` | What did the application itself say? |

Use them in that order; each narrows the question for the next. Do not read application logs before you know the container ever started.

### Status: the one-line summary

```bash
kubectl get pods -n orders-staging -o wide
```

```text
NAME                          READY   STATUS             RESTARTS      AGE   NODE
orders-api-7c9d8b6f5d-4kxqp   1/1     Running            0             2d    worker-1
orders-api-7c9d8b6f5d-m2v8z   0/1     CrashLoopBackOff   6 (45s ago)   9m    worker-2
orders-api-7c9d8b6f5d-q9t7l   0/1     Pending            0             9m    <none>
```

*Illustrative.* **READY** `1/1` counts containers passing readiness; `0/1` means the Pod receives no Service traffic. **STATUS** is a summary computed by `kubectl`, richer than the formal *phase* (`Pending`, `Running`, `Succeeded`, `Failed`, `Unknown`): `CrashLoopBackOff` and `ImagePullBackOff` are container waiting reasons promoted into the column. **RESTARTS** rising with `Running` means a container keeps dying. **NODE** `<none>` means the Pod was never placed: a scheduling problem, with no container and so no logs.

### Describe: the Pod's biography

Read `describe` in a fixed order: **Node** (is it scheduled?); **Containers → State and Last State** (how did the previous instance end: reason, exit code, times); **Conditions** (`PodScheduled`, `Initialized`, `ContainersReady`, `Ready`; the first `False` is the stuck stage); **Volumes** and **Tolerations**; and **Events** at the bottom, in time order.

```text
Containers:
  api:
    State:          Waiting
      Reason:       CrashLoopBackOff
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Restart Count:  6
    Limits:
      memory:  16Mi
```

*Illustrative.* The kernel killed the container for exceeding a 16 MiB limit, and Kubernetes restarts it with growing delays. You have a cause without reading a log line.

### Events: what the control plane just tried

```bash
kubectl get events -n orders-staging --sort-by=.lastTimestamp
kubectl events -n orders-staging --for pod/orders-api-7c9d8b6f5d-q9t7l   # newer kubectl
```

Each event has a `Type` (`Normal` or `Warning`), a `Reason` and a `Message`. Start with warnings.

| Reason | Emitted by | Typical meaning |
| --- | --- | --- |
| `FailedScheduling` | Scheduler | No node fits (resources, taints, affinity, volume) |
| `ErrImagePull`, `BackOff` | Kubelet | Image pull failed; waiting before retrying |
| `Unhealthy` | Kubelet | A probe failed |
| `FailedMount` | Kubelet | A volume, ConfigMap or Secret could not be mounted |
| `FailedCreate` | ReplicaSet controller | Pods could not be created (often quota or admission) |

Events are **not a durable log**: copy the output into your notes. A missing event is not proof nothing happened, because the component that would have emitted it may never have run.

### Logs: the application's own voice

```bash
kubectl logs <pod> -n orders-staging                      # current container
kubectl logs <pod> -n orders-staging --previous           # the instance that just crashed
kubectl logs <pod> -n orders-staging -c api               # a named container
kubectl logs -n orders-staging -l app=orders-api --tail=50 --since=10m
```

`--previous` is the flag beginners forget: for a crash-looping container the current instance may have printed nothing yet. If you see `container "api" ... is waiting to start`, there are no logs because it never started; go back to `describe`. `kubectl logs` shows standard output and error only, and logs of a deleted Pod are gone unless a cluster log pipeline collected them.

## Reading statuses properly

| Status | Where the Pod is in the chain | First evidence |
| --- | --- | --- |
| `Pending` | Not scheduled, or scheduled but not started | Events: `FailedScheduling` or volume events |
| `ContainerCreating` (long) | Sandbox, image or volume not ready | Events: `FailedMount`, `FailedCreatePodSandBox` |
| `ErrImagePull` / `ImagePullBackOff` | Image cannot be fetched | `manifest unknown`, `unauthorized`, `no such host` |
| `CrashLoopBackOff` | Starts, exits, restarted with back-off | `Last State` exit code; `logs --previous` |
| `Running`, `0/1` Ready | Alive, readiness failing | `Unhealthy: Readiness probe failed` |
| `Init:0/1`, `Init:CrashLoopBackOff` | An init container has not finished | `logs -c <init-container>` |
| `CreateContainerConfigError` | A referenced ConfigMap or Secret key is missing | Event naming the object or key |
| `Evicted` | Node pressure forced the Pod out | `describe` message (memory, ephemeral storage) |
| `Terminating` (stuck) | Deletion not completed | Finalizers, unreachable node, ignored `SIGTERM` |
| `Unknown` | Control plane cannot reach the node | `kubectl get nodes` |

### Exit codes you will meet

| Code | Meaning | Common cause |
| --- | --- | --- |
| `0` | Success | A service exited cleanly: wrong command, or a one-shot task |
| `1` | Generic application error | Unhandled exception, failed config load; read the logs |
| `126` / `127` | Not executable / not found | Wrong `command`, path or image architecture |
| `137` | 128 + 9: `SIGKILL` | `OOMKilled`, or killed after the grace period expired |
| `143` | 128 + 15: `SIGTERM` | Normal shutdown on request |

The rule `128 + n` means "killed by signal n". `137` alone does not prove memory: check the `Reason` field for `OOMKilled`.

## Scheduling symptoms

A `Pending` Pod with node `<none>` has not been placed. The scheduler **filters** out nodes that cannot run the Pod, then **scores** the rest. The event reports the filter:

```text
Warning  FailedScheduling  default-scheduler
  0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: },
  2 Insufficient memory.
```

*Illustrative.* Read it as arithmetic: three nodes considered; one excluded by a taint; two excluded because the Pod's memory **request** does not fit what remains. Scheduling uses **requests**, not live usage: a node 10% busy can be "full" if Pods on it request nearly all allocatable memory.

| Message contains | Meaning | Inspect |
| --- | --- | --- |
| `Insufficient cpu` / `memory` | Requests exceed free allocatable capacity | `describe node` → *Allocated resources* |
| `untolerated taint` | Node repels Pods lacking a toleration | Node taints; Pod tolerations |
| `didn't match ... node affinity/selector` | Selector excludes every node | Node labels versus selector |
| `volume node affinity conflict` | The volume lives in a zone with no suitable node | PV affinity versus node zones |
| `unbound immediate PersistentVolumeClaims` | The claim has no volume yet | `get pvc`; StorageClass events |
| `Too many pods` | Node reached its Pod-count limit | Node `pods` allocatable |

```bash
kubectl describe node worker-1 | sed -n '/Allocated resources/,/Events/p'
kubectl get pods -A -o wide --field-selector spec.nodeName=worker-1
```

A scheduling problem is rarely fixed by touching the Pod. Usually you reduce an unrealistic request (with evidence from real usage), free capacity, add a node, or correct a selector or toleration through the normal change route.

## Health symptoms: probes and what they cause

| Probe | Question | On failure |
| --- | --- | --- |
| Startup | Has the application finished starting? | Other probes wait; on timeout the container is restarted |
| Liveness | Is the process stuck beyond recovery? | The container is **restarted** |
| Readiness | Can it serve traffic right now? | The Pod is **removed from endpoints**; no restart |

```yaml
readinessProbe:
  httpGet: { path: /ready, port: 8080 }
  periodSeconds: 5
  failureThreshold: 3
livenessProbe:
  httpGet: { path: /health, port: 8080 }
  initialDelaySeconds: 20
  periodSeconds: 10
  failureThreshold: 3
```

| Symptom | Likely cause | Evidence |
| --- | --- | --- |
| `Running`, `0/1`, zero restarts | Readiness path wrong or dependency down | `Readiness probe failed: ... statuscode: 404` |
| Restarts climb, similar lifetimes | Liveness too strict or start-up too slow | `Liveness probe failed`; `Killing` |
| 503 though Pods are `Running` | No Ready Pods, so no endpoints | `get endpointslices` shows no addresses |

A liveness probe that checks the database is dangerous: when the database is down every replica restarts at once, turning a dependency outage into a restart storm. Keep liveness shallow ("not wedged") and readiness honest ("my dependencies work").

## Safe checks: what to run on a shared cluster

| Class | Examples | Rule |
| --- | --- | --- |
| Read-only | `get`, `describe`, `logs`, `events`, `top`, `auth can-i`, `diff` | Run freely in namespaces you own |
| Reversible, narrow | `rollout restart`, `rollout undo`, `scale` | After a hypothesis; announce it; one workload |
| Disruptive | `delete pod`, `drain`, `cordon` | Know the effect; ask if unsure |
| Destructive | `delete pvc`, `delete namespace`, editing finalizers | Never first; never on data without a restore path |

- **Check your context first:** `kubectl config current-context`. Many accidents are the right command on the wrong cluster; make production visibly different in your prompt.
- **Always pass `-n`;** do not rely on the default namespace.
- **Save before changing:** `kubectl get deployment orders-api -n orders-staging -o yaml > before.yaml`.
- **Ask what you may do:** `kubectl auth can-i delete pods -n orders-staging`. A "no" is information, not an obstacle.
- **Dry-run:** `kubectl apply --dry-run=server -f file.yaml` and `kubectl diff -f file.yaml`.
- **Fix through the source of truth.** If the cluster is managed from Git, a live edit will be reverted or will hide the defect.
- **Never paste secrets into tickets;** base64 is encoding, not protection.

A test client run inside the cluster is the fairest test of what other workloads see; `port-forward` from your laptop bypasses the Service and network policy:

```bash
kubectl run curl --rm -it --restart=Never -n orders-staging --image=curlimages/curl -- \
  curl -sS -m 3 -o /dev/null -w '%{http_code}\n' http://orders-api/health
```

## Maintenance vocabulary

| Action | Effect |
| --- | --- |
| `cordon` | Mark a node unschedulable; existing Pods stay |
| `drain` | Cordon, then evict Pods via the Eviction API (honours disruption budgets) |
| `uncordon` | Make the node schedulable again |
| `delete pod` | Direct deletion (does not honour budgets); a controller creates a replacement |

A **PodDisruptionBudget** (PDB) says how many replicas must stay available during *voluntary* disruptions such as drains. It does not protect against a node crashing. You will practise drains at the Intermediate level.

## Recovery sources, at a glance

| Layer | Recovery source |
| --- | --- |
| Workload definitions | Git |
| Cluster policies and access rules | Git |
| Cluster state (etcd) | Snapshot or provider backup |
| Persistent data | Application-level backup, snapshots, managed database |
| Secrets | Secret manager |
| Images | Registry |

If you cannot name the source for a layer, you have found a gap before it hurt you. Write it down; that is a successful finding.

## A troubleshooting walkthrough

The scenario: the team reports that `orders-api` in `orders-staging` returns 503 after a deployment. You have read-only access.

**Step 1 — State the symptom.** Before touching anything write: "Requests to `orders-api` in staging return 503 since about 08:30; the last deployment was 08:25." If you cannot say what "working" looks like, you cannot say when it is fixed. Confirm the cluster with `kubectl config current-context`.

**Step 2 — Look at the workload, outside in.**

```bash
kubectl get deployment,replicaset,pods -n orders-staging -l app=orders-api
```

```text
deployment.apps/orders-api   2/3   3   2   12d
replicaset.apps/orders-api-7c9d8b6f5d   2   2   2   12d
replicaset.apps/orders-api-84f6d5cc9    1   1   0   9m
pod/orders-api-7c9d8b6f5d-4kxqp   1/1   Running            0   2d
pod/orders-api-7c9d8b6f5d-q9t7l   1/1   Running            0   2d
pod/orders-api-84f6d5cc9-xv5rm    0/1   ImagePullBackOff   0   9m
```

*Illustrative (columns abbreviated).* A rolling update has stalled: the old ReplicaSet still has two Ready Pods, and the new one has a Pod that cannot pull its image. The rolling update protected you, since the old Pods keep serving.

**Step 3 — Describe the failing Pod.**

```bash
kubectl describe pod orders-api-84f6d5cc9-xv5rm -n orders-staging | sed -n '/Events/,$p'
```

```text
Normal   Scheduled  9m   default-scheduler  Assigned orders-staging/orders-api-84f6d5cc9-xv5rm to worker-2
Normal   Pulling    8m   kubelet            Pulling image "registry.example.com/orders-api@sha256:0000...0000"
Warning  Failed     8m   kubelet            Failed to pull image: ... manifest unknown
Normal   BackOff    4m   kubelet            Back-off pulling image
```

The Pod was scheduled (not a capacity problem) and the registry reports `manifest unknown` for the digest: the reference does not exist. That is a defect with a quoted evidence line.

**Step 4 — Check what changed.** `kubectl rollout history deployment/orders-api -n orders-staging` and, if the cluster is Git-managed, `git log -p -- deploy/orders-api` show who changed the reference and when.

**Step 5 — Test whether the cause explains the symptom.**

```bash
kubectl get endpointslices -n orders-staging -l kubernetes.io/service-name=orders-api
```

Two addresses remain, from the old Pods, so the Service is still serving from the old version. The bad image is *a* defect but does not explain the customer's 503. Keep both hypotheses open and continue down the chain: probes and application logs of the old Pods, then upstream dependencies.

**Step 6 — Act narrowly and record.** Revert the bad reference through the normal route (a Git revert, or `kubectl rollout undo` on a practice cluster) and watch:

```bash
kubectl rollout status deployment/orders-api -n orders-staging --timeout=120s
```

Write the note: symptom and time; what you checked, in order; the quoted evidence; the action; the result; and what remains unexplained. A real defect is not necessarily *the* defect, and a good note shortens the next person's hour.

## What can go wrong: beginner mistakes

| Mistake | Why it hurts | Better |
| --- | --- | --- |
| Deleting a Pod to "fix" it | Hides evidence; the replacement fails the same way | Read `describe` and `--previous` first |
| Reading app logs for a Pending Pod | None exist | Read events |
| Blaming the cluster before the change | Most incidents follow a change | Ask what changed in the last hour |
| Wrong context | Production edits by accident | Check context; coloured prompt |
| `kubectl edit` on a Git-managed object | Reverted, or drift hides the defect | Change the source |
| Treating `Running` as healthy | Readiness and dependencies are separate | Check `READY`, endpoints, a real request |
| Not writing things down | Events expire; memory fades | Keep a timestamped note |

## Knowledge consolidation

- Day two is access, capacity, safety rails, incidents, maintenance, recovery and change; incidents come first.
- Failures are broken reconciliation promises: walk the chain and find the first broken link.
- Use **status, describe, events, logs**, in that order; *Last State* and events answer most questions.
- `Pending` with node `<none>` is scheduling, which uses **requests**. `CrashLoopBackOff` needs the exit code and `logs --previous`. `Running 0/1` is readiness.
- Exit `137` is `SIGKILL`; confirm `OOMKilled` before saying "memory".
- **Liveness restarts; readiness removes from endpoints.** Keep liveness shallow.
- Start read-only; check context; pass `-n`; save before changing; fix through the source of truth.
- A real defect is not necessarily the cause of the reported symptom; check the Service path from inside the cluster.

## Exercises

**Exercise 1 — Read a healthy Pod.** Deploy `orders-api` on a practice cluster. Run `get -o wide`, `describe`, `get events` and `logs`. For *Conditions*, *Last State* and *Events*, write one sentence on what each would look like if unhealthy.

**Exercise 2 — Three breakages.** Break the deployment three ways, one at a time: a non-existent digest, readiness path `/nope`, `limits.memory: 16Mi`. After each, record `STATUS`, `READY` and one quoted evidence line. Revert between runs.

**Exercise 3 — Schedule the impossible.** Request more memory than any node has. Quote the `FailedScheduling` event and write the arithmetic. Then lower the request.

**Exercise 4 — Service path.** Point the Service selector at a label no Pod has. Show with `get endpointslices` that Pods are healthy yet there are no endpoints; fix it and prove it with a request from a temporary Pod.

**Exercise 5 — Write an incident note.** Pick one breakage and write a five-line note (symptom and time; checks in order; evidence; action; result). Swap with a partner and check that you can reproduce their reasoning.

**Solution notes.**

*Exercise 1.* A healthy Pod shows `True` in all four conditions and only `Normal` events. Unhealthy variants show a `False` condition, a non-zero termination, or `Warning` events.

*Exercise 2.* A bad digest gives `ErrImagePull`, then `ImagePullBackOff`, with `manifest unknown` or similar and no logs. A bad readiness path gives `Running 0/1`, zero restarts and an `Unhealthy` event with a 404. A 16 MiB limit gives `OOMKilled`, exit `137` and `CrashLoopBackOff` if the process truly needs more; a tiny static server might survive, which is itself a finding about real need.

*Exercise 3.* Expect `Pending`, node `<none>` and `0/N nodes are available: N Insufficient memory`. The arithmetic shows the scheduler filtering on requests.

*Exercise 4.* The slice lists no addresses while Pods are `Ready`; restoring the selector repopulates it within seconds.

*Exercise 5.* A good note quotes the evidence verbatim, lists what was ruled out, and separates what was done from what is still unexplained. If your partner cannot follow it, add the missing step.
