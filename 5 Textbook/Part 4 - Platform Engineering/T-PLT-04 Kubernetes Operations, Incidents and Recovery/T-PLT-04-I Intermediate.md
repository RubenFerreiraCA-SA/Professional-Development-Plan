# T-PLT-04-I — Intermediate Practice

*Chapter: [T-PLT-04 — Kubernetes Operations, Incidents and Recovery](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-04-i"></a>
#### T-PLT-04-I — Intermediate Practice

## Why this matters

At the Beginner level you learned to read one Pod. At the Intermediate level the problems stop being about a single Pod: a rollout stalls halfway, a node disappears, a certificate expires on a Sunday, a namespace hits its quota, and the person on call is not the person who built the service. What separates a calm response from a chaotic one is **practice and written procedure**: faults you have injected before, runbooks someone else can follow, and a habit of forming a hypothesis and testing it with evidence instead of trying commands until something changes.

This section builds that practice. It gives a fault catalogue to rehearse, a runbook format, the node lifecycle (cordon, drain, failure, replacement), a systematic way to debug deployments, the configuration and certificate failures that appear on every real cluster, capacity and quota diagnosis, a rebuild of a namespace from Git with a stopwatch, an awareness of etcd snapshots, and a discipline for evidence-led diagnosis. Examples use `orders-api` in `orders-staging` on a practice cluster you may break freely. Outputs marked *illustrative* show shapes, not measured results.

## First principles: diagnosis is hypothesis testing

An incident is a gap between what you believe about the system and what it is doing. Evidence-led diagnosis closes that gap in a loop:

```text
observe  ->  hypothesise  ->  predict  ->  test (cheapest, safest first)  ->  conclude  ->  act
```

The *predict* step is what makes it science rather than guessing: "if the cause is a missing ConfigMap key, then `describe` will show `CreateContainerConfigError` and the event will name the key." If the prediction fails, the hypothesis is wrong, which is progress. Three disciplines follow:

1. **Keep a short list of competing hypotheses**, not one favourite. Rank by likelihood and by cost of testing.
2. **Prefer tests that are read-only and that can discriminate**: a check whose result would differ between hypotheses.
3. **Change one thing at a time**, and record the time. Two simultaneous changes make the outcome unexplainable.

Most incidents also follow a change. The first question is always "what changed?": a deployment, a configuration edit, a certificate, a node pool, a policy, a version, or a dependency. Kubernetes records some of this for you.

```bash
kubectl rollout history deployment/orders-api -n orders-staging
kubectl get events -A --sort-by=.lastTimestamp | tail -30
kubectl get deployment orders-api -n orders-staging -o jsonpath='{.metadata.managedFields[*].manager}{"\n"}'
```

## A fault catalogue to practise on

| Fault | Injection | Symptom | Evidence | Fix |
| --- | --- | --- | --- | --- |
| Bad digest | Image `@sha256:000…` | `ImagePullBackOff`; rollout stalls; old Pods keep serving | `describe pod` events | Revert the commit |
| Bad readiness path | Probe `/nope` | `0/1 Ready`, no restarts, rollout stalls | `describe`, EndpointSlice | Revert |
| Memory limit too low | `limits.memory: 16Mi` | `OOMKilled`, `CrashLoopBackOff` | `describe` last state | Raise with evidence |
| Quota exhausted | Lower the CPU quota, restart | New Pods never created | `describe rs`, `exceeded quota` events | Fix the quota or right-size |
| Selector drift | Change the Service selector | Service has no endpoints, Pods healthy | `get endpointslices` | Revert |
| NetworkPolicy gap | Remove the DNS allow | Name-resolution timeouts, Pods Ready | DNS test from a Pod | Restore the policy |
| Admission denial | Tagged image via Git | Sync error; no new ReplicaSet | Controller status, API error | Use a digest |
| Missing config key | Rename a ConfigMap key | `CreateContainerConfigError` | Event naming the key | Restore the key |
| Port mismatch | `targetPort` ≠ app port | Endpoints present; connections refused | Test from a Pod | Align ports |

Run the *blind drill*: someone else injects a fault from this table; you diagnose using only the ladder and write a short incident note. Rotate roles. Add a row each time a drill reveals something new.

## Runbooks that others can follow

A runbook is a procedure written for someone tired, unfamiliar and under pressure. It should be short, tested and honest about its limits. A useful pattern is **symptom → first check → decision**:

```markdown
# Runbook: orders-api rollout stalled
**Applies to:** orders-staging, orders-production.   **Owner:** platform on-call.
**Last exercised:** 2026-10-02 by someone who did not write it.

## Symptom
`rollout status` does not complete; Deployment shows UP-TO-DATE ≠ READY.

## Safe checks (read-only)
1. `kubectl get rs,pods -n <ns> -l app=orders-api`
2. `kubectl describe pod <newest-pod>`: read Events and Last State.
3. `kubectl get events -n <ns> --sort-by=.lastTimestamp | tail -20`

## Decision
| Evidence                                   | Next step                        |
| ------------------------------------------ | -------------------------------- |
| ErrImagePull / manifest unknown            | Revert image reference (Git)     |
| Readiness probe failed, restarts 0         | Compare probe path with the app  |
| FailedScheduling / Insufficient            | See the capacity runbook         |
| exceeded quota                             | See the quota runbook            |

## Do not
- Delete the namespace, PVCs or finalizers.
- Edit live objects managed from Git.

## Escalate when
No cause within 20 minutes, or customer impact is rising.

## Record
Time, evidence lines, action, result.
```

Good runbooks name **who may do what**, state **how to undo** each action, link to the dashboards that matter, and include a "do not" section. Bad runbooks are essays, assume one person's memory, or rot: every runbook should record when it was last exercised.

## Debugging deployments and rollouts

A Deployment owns ReplicaSets, which own Pods. A rollout creates a new ReplicaSet and shifts replicas according to `maxSurge` and `maxUnavailable` (default 25% each, rounded). It is marked failed when it makes no progress for `progressDeadlineSeconds` (default 600 s); the Deployment gets the condition `Progressing=False, reason=ProgressDeadlineExceeded`, but **Kubernetes does not roll back automatically**.

```bash
kubectl rollout status deployment/orders-api -n orders-staging --timeout=120s
kubectl get deployment orders-api -n orders-staging -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
kubectl get rs -n orders-staging -l app=orders-api
kubectl describe rs <new-replicaset> -n orders-staging       # why Pods are not created
kubectl rollout undo deployment/orders-api -n orders-staging  # practice clusters; in production prefer Git
```

A decision path for a stalled rollout:

| Observation | Meaning | Next |
| --- | --- | --- |
| New ReplicaSet has 0 Pods and a `FailedCreate` event | Pods rejected at creation | Quota, admission webhook, Pod Security, missing ServiceAccount |
| New Pods `Pending` | Scheduling | `describe pod` events; capacity |
| New Pods `ImagePullBackOff` | Registry or reference | Event message; pull secret; digest exists |
| New Pods `CrashLoopBackOff` | Application fails | Exit code, `logs --previous`, configuration |
| New Pods `Running`, `0/1` | Readiness failing | Probe versus application; dependencies |
| New Pods Ready, old ones not terminating | `maxUnavailable`/PDB/grace period | `describe` old Pods; `terminationGracePeriodSeconds` |

Pay attention to the **rollout's safety property**: with a failing new version and default settings, old Pods remain and serve. A stalled rollout is usually *not* an outage; do not turn it into one by deleting the old ReplicaSet. Also check `minReadySeconds` (a Pod must stay Ready this long to count as available) and, where the rollout hangs on termination, whether the application handles `SIGTERM` within the grace period.

**Pod creation failures** appear on the ReplicaSet, not on a Pod, because the Pod never exists. That is why `describe rs` matters:

```text
Warning  FailedCreate  replicaset-controller
  Error creating: pods "orders-api-84f6d5cc9-" is forbidden: exceeded quota: staging-quota,
  requested: limits.cpu=500m, used: limits.cpu=3800m, limited: limits.cpu=4
```

*Illustrative.* The quota message gives the requested, used and limited values, enough to decide whether to right-size or ask for more.

## Ephemeral debugging

When the image has no shell, attach a temporary container to the Pod's namespaces rather than rebuilding the image:

```bash
kubectl debug -it pod/orders-api-7c9d8b6f5d-4kxqp -n orders-staging \
  --image=busybox:1.36 --target=api -- sh
kubectl debug pod/orders-api-7c9d8b6f5d-4kxqp -n orders-staging \
  --copy-to=orders-api-debug --container=api --image=registry.example.com/orders-api:debug
kubectl debug node/worker-2 -it --image=busybox:1.36        # node's filesystem appears at /host
```

| Technique | Use | Caution |
| --- | --- | --- |
| Ephemeral container (`--target`) | Inspect processes, network, DNS from inside the Pod | Needs RBAC for `pods/ephemeralcontainers`; cannot be removed until the Pod is |
| Pod copy (`--copy-to`) | Change command or image on a copy, leave the original serving | Copy has the same labels unless relabelled, so may receive traffic; relabel it |
| Node debug | Read kubelet logs, check disk | Privileged access; use only with authority; clean up the debug Pod |

Ephemeral containers need `pods/ephemeralcontainers` permission (deliberately not in a developer role), and under restricted Pod Security the debug container itself must satisfy the policy. Treat debug access as an audited, time-boxed privilege.

## Node lifecycle

A node moves through states you should be able to name: *joining → Ready → cordoned (unschedulable) → draining → removed*, plus the failure states *NotReady* and *Unknown*. Check conditions first:

```bash
kubectl get nodes -o wide
kubectl describe node worker-2 | sed -n '/Conditions/,/Addresses/p'
```

| Condition | Meaning when `True` |
| --- | --- |
| `Ready` | (when `False`/`Unknown`) kubelet not healthy or not reporting |
| `MemoryPressure` / `DiskPressure` / `PIDPressure` | Kubelet will evict Pods to protect the node |
| `NetworkUnavailable` | Network plugin has not configured the node |

### Planned removal: cordon and drain

```bash
kubectl cordon worker-2
kubectl drain worker-2 --ignore-daemonsets --delete-emptydir-data --timeout=120s
# ... maintenance ...
kubectl uncordon worker-2
```

Run a drain while a client loop measures availability:

```bash
while true; do curl -s -o /dev/null -w '%{http_code} %{time_total}\n' http://orders-api.example.internal/health; sleep 0.2; done
```

A PodDisruptionBudget that cannot be satisfied (for example `minAvailable: 1` with one replica) makes the drain fail with `Cannot evict pod as it would violate the pod's disruption budget`. The budget is doing its job, and a mis-sized one freezes every future upgrade. Check budgets *before* maintenance:

```bash
kubectl get pdb -A
```

*Illustrative:* a row with `ALLOWED DISRUPTIONS 0` means any eviction of that application will block. Fix the replicas or the budget through change control. `--disable-eviction` bypasses budgets by deleting Pods directly; treat it as an emergency override that needs a named approver.

Other drain blockers: Pods without a controller (need `--force`, and are then lost), local storage (`--delete-emptydir-data` loses it), and Pods that ignore termination signals and wait out the grace period.

### Node failure is not a drain

On abrupt node loss, the control plane marks the node `Unknown`, adds taints `node.kubernetes.io/unreachable` and `not-ready`, and Pods are evicted after their toleration period (**about five minutes by default**, the `tolerationSeconds: 300` added to Pods). PDBs do not apply, because this is involuntary disruption. Pods managed by a Deployment are replaced elsewhere; Pods with `ReadWriteOnce` volumes may wait further while the volume is detached from the dead node.

Observe it on a practice cluster by stopping the kubelet or the VM, record the time to detection, to rescheduling and to Ready, and compare with your target. If five minutes is too long for a service, tune toleration seconds on that workload and have enough replicas spread across nodes; do not depend on drain behaviour for failure.

### NotReady: a checklist

```bash
kubectl describe node worker-2                       # conditions and events
ssh worker-2 'systemctl status kubelet; journalctl -u kubelet -n 100 --no-pager'
ssh worker-2 'crictl ps -a | head; df -h /var/lib/kubelet; free -m'
```

| Finding | Likely cause | Action |
| --- | --- | --- |
| Kubelet stopped or crash-looping | Config error, certificate expired, runtime down | Read kubelet log; restart after fixing |
| `container runtime is down` | containerd stopped | Restart the runtime; check disk |
| `NetworkPluginNotReady` | CNI Pod not running on the node | Check CNI DaemonSet Pods |
| `DiskPressure` | Images, logs or ephemeral storage full | Free space; find the heavy Pods |
| Node unreachable by SSH too | Host or network failure | Replace the node (cattle, not pets) |

When a node cannot be repaired quickly, **replace it**: cordon, drain if possible, delete the Node object, and let the node pool or provider create a new one.

## Configuration and certificate failures

### ConfigMaps and Secrets

| Situation | Behaviour | Consequence |
| --- | --- | --- |
| ConfigMap or Secret missing, referenced by `env` or `volume` | Pod stuck `ContainerCreating` (volume) or `CreateContainerConfigError` (env) | Create the object or key |
| Referenced key missing, not marked `optional` | `CreateContainerConfigError` | Restore the key |
| Value changed, consumed as environment variable | **Not updated** in running containers | Restart the workload |
| Value changed, mounted as a volume | Updated after a delay (not with `subPath`) | Application must re-read it |
| Name or namespace wrong | Object "not found" | Compare namespaces; ConfigMaps are namespaced |

A frequent incident is "I changed the ConfigMap but nothing happened". Prove what the Pod actually sees, rather than what the manifest says:

```bash
kubectl exec -n orders-staging deploy/orders-api -- printenv | grep ORDERS_
kubectl exec -n orders-staging deploy/orders-api -- cat /etc/orders/config.yaml
```

A durable approach is to roll the workload when configuration changes (a hash of the ConfigMap in the Pod template annotations, or generated names in Kustomize), so the change is visible, reviewable and reversible.

### Certificates

Certificates expire, and expiry is a scheduled outage that looks like a surprise. On a kubeadm-style cluster the control-plane client and serving certificates last about a year by default and are renewed on upgrade; the CA lasts much longer. Kubelet client certificates normally rotate automatically; webhooks and ingress certificates have their own lifecycle.

```bash
kubeadm certs check-expiration                       # self-managed, kubeadm
openssl s_client -connect api.example.internal:6443 </dev/null 2>/dev/null | openssl x509 -noout -subject -enddate
kubectl get certificates -A                          # when cert-manager is installed
kubectl get csr
```

| Symptom | Possible certificate cause |
| --- | --- |
| `x509: certificate has expired or is not yet valid` from `kubectl` | API server certificate expired, or the client's clock is wrong |
| Nodes become `NotReady` together | Kubelet client certificate expired or could not rotate |
| Create/update calls fail with webhook TLS errors | Admission webhook serving certificate expired or CA bundle stale |
| Ingress serves a browser warning | Ingress certificate not renewed; challenge failing |

Remedy: renew, restart the affected components, verify. Prevent: alert on days-to-expiry (for example 30 and 7), automate renewal, and rehearse renewal on a non-production cluster. Check the *clock* before the certificate: skew produces "not yet valid".

## Capacity, quotas and resource symptoms

Capacity problems reach you as Pending Pods, throttled CPU, OOM kills or evictions. Distinguish four ideas:

| Concept | What it controls | Failure when wrong |
| --- | --- | --- |
| **Request** | Scheduling decision and guaranteed share | Too high: Pending and waste. Too low: noisy neighbours |
| **Limit (memory)** | Hard ceiling | Exceed it and the container is OOM-killed |
| **Limit (CPU)** | Throttling ceiling | Latency spikes with no restart: check throttling metrics |
| **Quota / LimitRange** | Namespace total and per-object defaults | New Pods rejected: `exceeded quota` |

Quality-of-service classes follow from requests and limits: `Guaranteed` (requests equal limits for all containers), `Burstable`, `BestEffort` (none set). Under node pressure the kubelet evicts BestEffort and over-request Burstable Pods first.

```bash
kubectl top nodes
kubectl top pods -n orders-staging --sort-by=memory
kubectl describe resourcequota -n orders-staging
kubectl describe node worker-1 | sed -n '/Allocated resources/,/Events/p'
kubectl get pods -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,QOS:.status.qosClass | sort -k3 | head
```

`kubectl top` requires a metrics source (metrics-server) and shows recent usage, not history; use your monitoring system for trends. Compare **requests, usage and allocatable**: if requests are far above usage everywhere, the cluster is "full but idle" (wasteful); if usage regularly approaches limits, you are heading for OOM kills or throttling.

A right-sizing rule: set the memory request near the typical working set plus margin, memory limit near the observed peak plus margin, and CPU request near typical use. Change them with evidence (a week of data, including peaks), through the normal route.

## Rebuild a namespace from Git with a stopwatch

Delete the namespace and restore from a single entry point that includes the guardrails (namespace, quota, policies) *before* workloads:

```bash
kubectl delete namespace orders-staging
time kubectl apply -k deploy/platform/staging
kubectl -n orders-staging rollout status deployment/orders-api
```

Order matters on a fresh cluster: namespace → quota and limits → network policies → workload. A first apply may fail because a custom resource's definition is not ready; repeat or sequence it. Record how long each stage took and what needed a human decision. Data does not come back with this procedure: persistent volumes and databases need their own restore, which you will design at the Professional level.

If a namespace is stuck in `Terminating`:

```bash
kubectl get namespace orders-staging -o jsonpath='{.status.conditions}' | jq .
kubectl get apiservices | grep -v True
```

A common cause is an unavailable aggregated API (for example a metrics API whose backing Pods are down) that prevents the namespace controller from listing content. Fix the cause. Removing finalizers by patching is a last resort that can leave orphaned resources.

## etcd snapshot (awareness)

On a cluster you control: `etcdctl snapshot save snapshot.db` with the appropriate endpoint and certificates, then `etcdutl snapshot status snapshot.db -w table`. Restores are delicate because they roll the *whole cluster state* back: Pods, Deployments, Secrets and claims created after the snapshot vanish from the cluster's view. On managed services the provider owns etcd; learn their guarantees and what *you* must back up (workload definitions in Git, persistent data, external dependencies).

## Evidence-led diagnosis: a worked example

A report: "orders-api is slow, and some requests fail, since the node maintenance last night." Follow the loop.

**Observe.** Error rate rose at 02:10; node `worker-2` was drained and uncordoned at 02:05.

**Hypotheses** (with test costs): (a) Pods rescheduled onto a node with a stricter network policy (cheap: compare nodes); (b) fewer replicas Ready than before (cheap: `get deploy`); (c) the node came back with a CPU-constrained instance type (cheap: `describe node`); (d) a dependency regressed (moderate: dependency dashboards).

**Tests.**

```bash
kubectl get deploy orders-api -n orders-staging                  # (b): 2/3 Ready?
kubectl get pods -n orders-staging -o wide -l app=orders-api     # placement
kubectl describe node worker-2 | grep -E 'cpu|memory|Taints'     # (c)
kubectl top pods -n orders-staging -l app=orders-api
```

*Illustrative result:* `2/3` available; the third Pod sits `Pending` with `Insufficient cpu` because `worker-2` is back with fewer allocatable CPUs than before maintenance; the two Ready Pods are CPU-throttled. Hypotheses (b) and (c) are confirmed together; (a) and (d) are not needed to explain the symptom.

**Conclude and act.** The node pool template changed during maintenance. Restore the instance size through change control; as a stopgap, lower the CPU request if usage evidence supports it. **Record** what you ruled out and why.

A discipline worth adopting: when you write "root cause", attach an evidence line to every link of the causal chain, and list anything you inferred rather than observed.

## What can go wrong: a short catalogue

| Failure | Why it happens | Prevention |
| --- | --- | --- |
| Drain hangs | PDB allows 0 disruptions; unmanaged Pod; local data | Review budgets before maintenance |
| Node failure takes minutes to recover | Default five-minute toleration; volume detach | Spread replicas; tune toleration; test |
| "Config change did nothing" | Env vars read at start; `subPath` mounts not refreshed | Roll workloads on config change |
| Webhook outage blocks all creates | `failurePolicy: Fail` and the webhook is down | Highly available webhooks; scoped rules |
| Stalled rollout turned into an outage | Old ReplicaSet deleted by hand | Revert through Git; leave old Pods running |
| Namespace stuck `Terminating` | Unavailable API or finalizer | Fix the API; finalizer patch as last resort |
| Rebuild fails in the wrong order | Workload applied before quota and policy | One entry point with ordered stages |
| Evidence lost | Events expired; Pods replaced | Capture output into the incident note early |

## Knowledge consolidation

- Diagnosis is a loop: observe, hypothesise, predict, test cheaply and read-only, change one thing, record.
- Ask "what changed?" first; keep competing hypotheses and tests that discriminate between them.
- A runbook is symptom → first check → decision, with "do not", escalation, undo and a last-exercised date.
- Rollouts do not roll back automatically; a stalled rollout normally leaves old Pods serving. Pod creation failures show on the **ReplicaSet**.
- Drain is voluntary and budget-respecting; node failure is involuntary, takes about five minutes by default, and ignores PDBs.
- Config changes reach environment variables only on restart; certificates expire on a calendar you can monitor.
- Requests drive scheduling, memory limits cause OOM kills, CPU limits cause throttling, quotas reject creation.
- A namespace rebuild proves definitions and ordering, not data.
- A snapshot restore rewinds everything; know whether your provider owns it.

## Exercises

**Exercise 1 — Blind drill.** Have a partner inject one fault from the catalogue without telling you. Using only the ladder, write an incident note: symptom, hypotheses, tests, evidence, conclusion. Score yourself on whether every claim has an evidence line.

**Exercise 2 — Drain with a failing PDB.** Set `minAvailable: 1` on a one-replica Deployment and drain its node while a client loop runs. Quote the refusal. Fix the budget or replicas and repeat; record client-visible errors and latency in both runs.

**Exercise 3 — Node loss.** On a practice cluster stop the kubelet on a worker. Record time to `NotReady`, to taint, to eviction, and to a Ready replacement Pod. Compare against the five-minute default and decide whether your service tolerates it.

**Exercise 4 — Config that did nothing.** Consume a value as an environment variable and as a mounted file. Change the ConfigMap, record what each Pod sees after one minute, then roll the Deployment and record again.

**Exercise 5 — Quota.** Lower the namespace CPU quota below current use and trigger a rollout. Find the exact message on the ReplicaSet and compute the smallest quota that would allow it.

**Exercise 6 — Rebuild.** Delete a practice namespace and restore from Git with a stopwatch. Record the duration per stage, what needed a human, and what was *not* restored.

**Exercise 7 — Write the runbook.** Turn Exercise 1's fault into a one-page runbook in the format above and have a colleague follow it cold; fix every point where they hesitated.

**Solution notes.**

*Exercise 1.* A strong note states two or three hypotheses, names the test that would discriminate, and quotes output. A weak note jumps to a fix. Look for claims you inferred but did not observe.

*Exercise 2.* Expect `Cannot evict pod as it would violate the pod's disruption budget`, with the drain retrying until the timeout. After fixing (for example two replicas and `minAvailable: 1`), the drain should complete with no or brief client errors; your measurement tells you which. Note that a PDB with replicas equal to `minAvailable` also blocks.

*Exercise 3.* Typical shape: node `Unknown` within about 40 seconds (the node-monitor grace period), taints applied then, Pods evicted after toleration seconds (about 300 s), replacements Ready some seconds later. Cloud and distribution defaults differ; record yours rather than copying these.

*Exercise 4.* Environment variables should be unchanged until restart; the mounted file should update after the kubelet sync delay unless mounted with `subPath`. After the roll both agree.

*Exercise 5.* The message gives `requested`, `used` and `limited`. The smallest workable quota is `used` plus the new requested amount, remembering that during a rolling update old and new Pods coexist, so surge counts.

*Exercise 6.* Illustrative expectation: namespace and quota apply in seconds; workload Ready depends on image pull. Typical omissions: persistent data, Secrets held outside Git, and any object created by hand. List them; each is a recovery gap.

*Exercise 7.* Hesitation points are the gaps. Common ones are missing namespace in commands, unclear authority to act, and no undo step.
