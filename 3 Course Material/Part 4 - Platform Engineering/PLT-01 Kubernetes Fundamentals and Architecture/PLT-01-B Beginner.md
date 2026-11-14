# PROJECT PREREQUISITES — MANDATORY ENTRY GATE

Required project state: **PRJ-001 through PRJ-068**, with every step recorded **Completed** — or **Out of scope** only where your PDP excludes an entire optional track (Datadog `PRJ-025`–`PRJ-028`, AI `PRJ-049`–`PRJ-068`). Never mark a single step Out of scope on its own.

**This gate includes the optional ranges.** PRJ-001 through PRJ-068 is not a "core steps only" list. It contains the optional Datadog steps ([PRJ-025](../../../4%20Project%20Document/Project.md#prj-025)–[PRJ-028](../../../4%20Project%20Document/Project.md#prj-028)) and the optional AI steps ([PRJ-049](../../../4%20Project%20Document/Project.md#prj-049)–[PRJ-068](../../../4%20Project%20Document/Project.md#prj-068)). If your PDP keeps those tracks active, every one of those 24 steps must be recorded **Completed** before you start this module. If your PDP excludes an entire optional track, record every step in that track (all four Datadog steps, or all twenty AI steps) as **Out of scope**. Excluding some steps of a track, or skipping a step inside an active track, does not satisfy this gate.

If any required step is neither Completed nor part of a wholly excluded optional track, **STOP**. Open the independent [Project Document](../../../4%20Project%20Document/Project.md), complete the missing steps, record their completion, then return here. Do not begin this module until the gate is satisfied.

Exact tasks: see [PRJ-001 through PRJ-068](../../../4%20Project%20Document/Project.md#prj-001); the last required step is [PRJ-068](../../../4%20Project%20Document/Project.md#prj-068).

## MODULE PLT-01-B — KUBERNETES FUNDAMENTALS AND ARCHITECTURE — BEGINNER

### 1. Topic and Scope

**In scope for this level:** Recognition-level vocabulary and architecture. You name the control-plane components (kube-apiserver, etcd, kube-scheduler, kube-controller-manager) and node components (kubelet, container runtime, kube-proxy), distinguish Pod, ReplicaSet, Deployment, Service and Namespace, and use read-only `kubectl` commands on a practice cluster to find each piece. The guided first task is to delete a Deployment-managed Pod and explain why it returns.

**Out of scope:** Writing manifests from scratch, probe and resource tuning, RBAC, multi-node high-availability design, cluster trade-off analysis and any step-by-step Harbour mapping instructions (those are in the Project Document).

**Self-assessment fit:** Choose this level in [2.2 Topic Self Assessment](../../../2%20PDP%20Development/2.2%20Topic%20Self%20Assessment.md#plt-01--kubernetes-fundamentals-and-architecture) when this matches your current ability: *Identify cluster components and Kubernetes vocabulary.* Typical starting point: You can already say what a container is, but you cannot yet say which Kubernetes component does what.

### 2. Learning Objectives

1. Name the seven core components (kube-apiserver, etcd, kube-scheduler, kube-controller-manager, kubelet, container runtime, kube-proxy) and state each one's responsibility in one sentence.
2. Distinguish Pod, ReplicaSet, Deployment, Service and Namespace, and choose the right object to inspect for "where is my container running?" versus "how do clients reach it?".
3. Run read-only commands (`kubectl get nodes -o wide`, `kubectl get pods -A`, `kubectl describe node`, `kubectl api-resources`) and match each part of the output to a component in the architecture.
4. Explain desired state versus observed state using the example of deleting a Pod owned by a Deployment, and correct two misconceptions (for example "Kubernetes builds images" or "a Pod is durable").
5. Prepare the evidence needed for **PRJ-069**: a Harbour component map showing control-plane, node, workload and Service responsibilities, with the command or document that confirms each box.

### 3. Required Textbook Reading

Read the following section in the master textbook (independent of this PDP):

- [T-PLT-01-B — Kubernetes Fundamentals and Architecture — Beginner](../../../5%20Textbook/Master%20Textbook.md#t-plt-01-b) — Read the architecture picture, the core-objects table and the first-commands sequence before doing the exercise.

Optional enrichment: the "What Kubernetes does not do" and training-versus-production-cluster notes in the same chapter. Optional material is clearly marked in the textbook.

### 4. Knowledge Assessment

**Task:** Without notes, sketch a three-node kind cluster and narrate the path from `kubectl create deployment web --image=nginx:1.27 --replicas=2` to two running Pods, naming every component that acts. Then run three read-only commands on a practice cluster and annotate their output.

**Pass criteria:** All seven components are named with a correct responsibility; the narration orders API server, etcd, controller manager, scheduler and kubelet defensibly; at least one misconception is corrected; annotated command output is saved with a date; no cluster state was changed by the read-only commands.

Record the result in your Learning Progress Record. Passing the knowledge assessment does **not** by itself complete the module — the project assignment below is also required for a project-linked pathway.

### 5. Project Assignment — COMPLETE BEFORE MOVING ON

Complete **PRJ-069 — Map Kubernetes components** in the [Project Document](../../../4%20Project%20Document/Project.md#prj-069).

Evidence to record: a component map (diagram plus table), the read-only command transcripts you used to confirm each component, and a note stating whether the cluster was real or simulated. Follow the completion criteria on that project step, then mark the step completed in your progress record before opening the next module.
