# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-073**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-073](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-073](../../../4%20Project%20Document/Project.md#prj-073).

## MODULE PLT-02-I — KUBERNETES WORKLOADS, CONFIGURATION AND PACKAGING — INTERMEDIATE

### 1. Topic and Scope

**In scope for this level:** Writing and operating routine workload configuration. You tune probes (`initialDelaySeconds`, `periodSeconds`, `failureThreshold`), set requests and limits, feed configuration through ConfigMaps and Secrets (`envFrom`, `valueFrom`, volumes), drive rolling updates, use `kubectl rollout status/history/undo`, and render the same service with `kubectl kustomize` and `helm template`.

**Out of scope:** Pure vocabulary (Beginner), production quality gates and ownership policy (Professional), StatefulSet, operator and templating-language critique (Expert), and the Harbour health-and-configuration steps (Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-02--kubernetes-workloads-configuration-and-packaging) when this matches your current ability: *Run and troubleshoot routine workloads.* Typical starting point: You can read manifests and now need to write them, change configuration safely and diagnose a failed rollout.

### 2. Learning Objectives

1. Write a Deployment with liveness, readiness and startup probes, choose sensible thresholds and show how a wrong readiness path leaves Pods running but not Ready.
2. Set CPU and memory requests and limits and explain the effect of each on scheduling, throttling and OOM kills.
3. Supply configuration through a ConfigMap and a Secret using both `envFrom` and a mounted volume, and show that a changed value requires a rollout or a generated-name pattern to take effect.
4. Run, pause and undo a rolling update (`kubectl rollout status`, `history`, `undo`) and read ReplicaSet counts to explain what happened.
5. Prepare the evidence needed for **PRJ-074**: probes, configuration, secrets handling and resource requests for Harbour, plus a recorded normal update.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-02-I — Kubernetes Workloads, Configuration and Packaging — Intermediate](../../../5%20Textbook/Master%20Textbook.md#t-plt-02-i) — Study choosing deliberately between tools, writing a good chart, overlay patterns, config-change rollouts, workload shapes and the autoscaling basics.

Optional enrichment: the Job and HorizontalPodAutoscaler examples in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Deploy a service with probes, a ConfigMap and a Secret to a practice cluster. Change one configuration value, observe the rollout, then break the readiness probe and recover with `kubectl rollout undo`, recording what each ReplicaSet looked like at each stage.

**Pass criteria:** Probes behave as designed; the configuration change is visibly rolled out; the broken update never took the service fully down and was rolled back; no real secret value appears in notes or manifests.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-074 — Manage configuration and health** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-074).

Evidence to record: manifests, a rollout transcript showing ReplicaSet changes, and a short note on how secrets were supplied. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
