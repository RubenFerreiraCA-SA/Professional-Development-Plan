# T-PLT-01-B — Beginner Foundations

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-b"></a>
#### T-PLT-01-B — Beginner Foundations

## Why this matters

Running one container on one machine is easy. Running forty services, each with several copies, on a dozen machines that can fail at any time, is a different problem. Somebody has to decide which machine runs which copy, notice when a copy dies, replace it, give the copies a stable address so other services can find them, roll out a new version without a gap, and do all of this at three in the morning without a human typing commands.

Kubernetes is a system that takes over that job. You do not tell it "start this container on that machine". You tell it *what you want to be true* ("two copies of this image, reachable under this name") and a set of programs works continuously to make reality match. That single idea — **declared desired state, continuously reconciled** — explains why a deleted Pod comes back and why a failing rollout stalls instead of breaking everything.

This Beginner section assumes you know what a container image is and have run a container (see T-DEV-02). It does **not** assume you have used Kubernetes. The examples use a fictional service called `orders-api`; registry names such as `registry.example.com` are placeholders. You will build a small practice cluster, deploy to it, break it on purpose and learn to read what it tells you.

## First principles: commands versus desired state

There are two ways to operate a fleet of programs.

| Style | You say | The system does | When it goes wrong |
| --- | --- | --- | --- |
| Imperative | "Start container X on machine 3" | Exactly that, once | Nobody notices when X dies; you must remember what you did |
| Declarative | "Two replicas of X should exist" | Compares what exists to what you declared and acts on the difference, repeatedly | The declaration was wrong, but it is *recorded and reviewable* |

Kubernetes is declarative at its core. Every object you create — a Deployment, a Service, a ConfigMap — is a **record of intent** stored in the cluster. Programs called **controllers** read those records, look at the real world, and act to close the gap. This loop never stops:

```text
        ┌──────────────────────────────────────────────┐
        │                                              │
   desired state (spec)  ──►  compare  ◄──  observed state (status)
                               │
                               ▼
                       act to reduce the difference
                               │
                               └───────── repeat forever
```

Two consequences matter immediately:

1. **You edit the record, not the world.** If you delete a container by hand, the controller recreates it, because the record still says it should exist. To remove something, you change or delete the *record*.
2. **The system is eventually consistent.** After you declare something, there is a short delay while controllers notice and act. A command that returns successfully has stored your intent; it has not necessarily produced the result yet.

## The architecture in one picture

A Kubernetes **cluster** is a set of machines (called **nodes**) managed together, plus a **control plane** — the programs that store state and make decisions.

```text
 kubectl / CI / controllers
          │
   ┌──────▼───────┐   etcd (the database of cluster state)
   │  API server  │◄──────────────┘
   └──┬────────┬──┘
      │        │
┌─────▼──┐  ┌──▼──────────────┐       Node (worker)
│Scheduler│  │Controller manager│     ┌────────────────────┐
└────────┘  └─────────────────┘      │ kubelet  + runtime │
                                      │  Pod  Pod  Pod     │
                                      └────────────────────┘
```

## Cluster components, one by one

Learn each component by the question it answers.

| Component | Where it runs | The question it answers |
| --- | --- | --- |
| **API server** (`kube-apiserver`) | Control plane | "How does anything read or change cluster state?" It is the only front door. It authenticates, authorises, validates and stores objects |
| **etcd** | Control plane | "Where is the state kept?" A consistent key-value database holding every object. Lose it without a backup and you lose the cluster's memory |
| **Scheduler** (`kube-scheduler`) | Control plane | "Which node should this new Pod run on?" It picks a node that has room and satisfies the Pod's constraints |
| **Controller manager** (`kube-controller-manager`) | Control plane | "Who makes reality match the declaration?" A bundle of controllers: Deployments, ReplicaSets, nodes, endpoints and many more |
| **Cloud controller manager** | Control plane, on cloud clusters | "How do cloud resources (load balancers, node records) map to cluster objects?" |
| **kubelet** | Every node | "How does a Pod specification become running containers on this machine?" It starts containers, runs probes and reports status |
| **Container runtime** | Every node | "What actually creates the containers?" For example `containerd` or CRI-O; the kubelet talks to it through a standard interface |
| **kube-proxy** (or an equivalent data plane) | Every node | "How does traffic to a Service address reach a Pod?" It programs the node's network rules |
| **DNS add-on** (CoreDNS) | Inside the cluster, as Pods | "How do I find a Service by name?" |
| **Network plugin** (CNI) | Every node | "How do Pods get IP addresses and reach each other across nodes?" |

Three points save beginners a great deal of confusion:

- **Components do not call each other directly.** The scheduler writes "this Pod belongs on node 2" into the API server; the kubelet on node 2, which is *watching* the API server, notices.
- **The API server is the single door.** That is why *access control on the API* is the central security control. If it is down, you cannot change anything, but running Pods keep running.
- **The control plane and the nodes are different failure domains.** With the control plane down, existing Pods generally keep running but nothing is rescheduled or updated. With a node down, its Pods are gone until the control plane reschedules them.

In a **managed** service the provider runs the control plane; in a **self-managed** cluster you do; in a small practice cluster one machine does both jobs. The *roles* stay the same.

## Pods, ReplicaSets, Deployments and Services

These four objects are the working vocabulary of Kubernetes.

| Object | Owns | Why it exists |
| --- | --- | --- |
| **Pod** | One or more containers, shared network identity, shared volumes | The unit of scheduling. Ephemeral: a Pod is never "repaired", only replaced |
| **ReplicaSet** | N identical Pods | Keeps the count right |
| **Deployment** | ReplicaSets across versions | Rolling updates, rollback and history for stateless services |
| **Service** | A stable virtual address and name in front of a set of Pods | Pods come and go and their IPs change; a Service does not |
| **Labels and selectors** | Association | The glue: controllers and Services find "their" Pods by matching labels |

**A Pod** can hold several containers that share a network namespace (they reach each other on `localhost`) and can share volumes. Usually there is one main container; extras are helpers such as a log shipper. Every Pod gets its own IP address, which lasts only as long as the Pod. **A bare Pod that dies stays dead**, which is why you rarely create Pods directly. **A ReplicaSet** says "keep three Pods matching this label" and makes another if one disappears.

**A Deployment** manages ReplicaSets. When you change the image, it creates a *new* ReplicaSet for the new version and gradually shifts Pods from the old one to the new one. The old ReplicaSet is kept (scaled to zero) so rollback is quick. You normally work with Deployments and let them create the ReplicaSets and Pods.

```text
Deployment orders-api
   └── ReplicaSet orders-api-7d9c5f   (current version, 2 replicas)
          ├── Pod orders-api-7d9c5f-abcde   (IP 10.244.1.5, on node worker-1)
          └── Pod orders-api-7d9c5f-fghij   (IP 10.244.2.7, on node worker-2)
   └── ReplicaSet orders-api-6b8d44   (previous version, 0 replicas, kept for rollback)
```

**A Service** gives the group of Pods a stable address:

```text
 client ──► Service orders-api (10.96.12.40:80, DNS: orders-api)
                  │ chooses among READY Pods that match the selector
                  ├──► Pod 10.244.1.5:8000
                  └──► Pod 10.244.2.7:8000
```

**Labels and selectors** deserve a careful look, because most "it does not work" problems at this level are a selector that does not match:

```yaml
# On the Pod template (what labels the Pods carry):
labels:
  app: orders-api
# On the Service (which Pods it selects):
selector:
  app: orders-api
```

If those two differ by even one character, the Service has no Pods behind it and no traffic arrives. Labels are free-form text pairs, not magic: Kubernetes matches them exactly.

## Namespaces: a way to divide one cluster

A **namespace** is a named partition inside a cluster. Most objects (Pods, Deployments, Services, ConfigMaps) live in exactly one namespace; names must be unique *within* a namespace, not across the cluster. Namespaces let different teams or environments share a cluster without name collisions, and they are the unit to which you later attach quotas and access rules.

| Fact | Meaning |
| --- | --- |
| `default` exists | Fine for experiments, a poor habit for anything shared |
| `kube-system` holds the cluster's own components | Look, do not touch |
| A namespace is not a security boundary by itself | It becomes one only with access control, network rules and quotas |

Always say which namespace you mean: `kubectl -n practice get pods`. Forgetting it is a classic source of "my Pods disappeared" (they are in another namespace).

## What cloud-native asks of an application

"Cloud-native" does not mean "runs on Kubernetes". It is a set of operating assumptions that platforms like Kubernetes exploit:

| Property | What the platform assumes | Example |
| --- | --- | --- |
| Disposable processes | Any instance may be killed and replaced | Stateless service |
| Logs to standard output | The platform collects them | No log files managed by the app |
| Health endpoints | The platform can ask "alive?" and "ready?" separately | `/health` and `/ready` |
| Graceful shutdown | `SIGTERM` leads to a prompt, clean exit | Draining in-flight requests |

If one is false — for example, sessions kept in memory — Kubernetes will schedule the app happily and expose the flaw during the first rollout or node maintenance.

## Reading an object: spec and status

Every Kubernetes object has the same two-part shape, and reading it fluently is the beginner's most valuable skill.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: practice
spec:            # what you WANT (you write this)
  replicas: 2
status:          # what IS (the system writes this)
  replicas: 2
  readyReplicas: 1
  availableReplicas: 1
```

`metadata` identifies the object. `spec` is the **desired state**; you own it. `status` is the **observed state**; controllers own it and you never write it. The gap between `spec.replicas: 2` and `status.readyReplicas: 1` is work a controller is doing or failing to do. **Diagnosis is reading that gap.**

## Inspecting a cluster with `kubectl`

`kubectl` is the command-line client for the API server. Five verbs cover most beginner work:

| Command | What it shows | Use it to |
| --- | --- | --- |
| `kubectl get <kind>` | A table of objects | See what exists and rough health |
| `kubectl get <kind> <name> -o yaml` | The full object, spec and status | See exactly what the system recorded |
| `kubectl describe <kind> <name>` | A readable summary plus recent **events** | Find out *why* something is not working |
| `kubectl logs <pod>` | The container's standard output | See what the application said |
| `kubectl explain <kind>.<field>` | Built-in documentation for a field | Look up a field without leaving the terminal |

```bash
kubectl get nodes
kubectl -n practice get deploy,rs,pods,svc
kubectl -n practice get pods -o wide
kubectl -n practice describe pod <pod-name>
kubectl -n practice logs <pod-name>
kubectl -n practice logs <pod-name> --previous      # logs of the last crashed container
kubectl -n practice get events --sort-by=.lastTimestamp
kubectl explain deployment.spec.strategy
```

**Events are the cluster talking.** The bottom of `kubectl describe pod` lists what the scheduler and kubelet did and why they refused to do something. Read events first; they expire after about an hour.

**Status words you will see on Pods**

| Status | Plain meaning |
| --- | --- |
| `Pending` | Accepted, but not running yet: not scheduled, or images still being pulled |
| `ContainerCreating` | Scheduled; the kubelet is pulling the image and setting up volumes |
| `Running` | At least one container is running (this does *not* mean it is ready or working) |
| `Completed` | Finished successfully (for run-to-completion workloads) |
| `CrashLoopBackOff` | The container keeps exiting; Kubernetes waits longer between restarts |
| `ImagePullBackOff` | The image cannot be pulled; Kubernetes retries with growing delays |
| `Terminating` | Being shut down |

The `READY` column (for example `1/2`) counts containers whose readiness checks pass. `Running` with `0/1` means the process exists but is not receiving traffic.

## The journey from `kubectl apply` to a running Pod

Follow one command through the system. This sequence is the most useful mental model in the chapter; later levels add precision to every step.

```bash
kubectl apply -f orders-api.yaml
```

| Step | Who | What happens |
| --- | --- | --- |
| 1 | `kubectl` | Reads the file and sends the object to the API server |
| 2 | API server | Checks who you are, whether you are allowed, and whether the object is valid; stores it in etcd |
| 3 | Deployment controller | Notices a new Deployment with no ReplicaSet and creates one |
| 4 | ReplicaSet controller | Notices it has zero Pods but wants two, and creates two Pod records (no node chosen yet) |
| 5 | Scheduler | Notices Pods with no node; picks a node for each and records the choice |
| 6 | Kubelet (on the chosen node) | Notices a Pod assigned to it; pulls the image and starts the containers |
| 7 | Kubelet | Runs the readiness check; when it passes, reports the Pod `Ready` |
| 8 | Endpoint machinery | Adds the ready Pod's IP to the list behind the Service |

At no point did one component call the next. Each one watched the stored state, did its own small job and wrote back its result. That is why the system is resilient: a restarted controller simply reads the current state and carries on.

**Now follow one request.** A client Pod calls `http://orders-api/health`: (1) cluster DNS resolves `orders-api` to the Service's stable address; (2) the client connects to it; (3) rules on the client's node, programmed by kube-proxy or the network plugin, pick one *ready* Pod behind the Service and forward the connection; (4) the Pod answers along the same path.

A Service is not a process listening somewhere. It is a stored record plus network rules on every node, so a Service with no ready Pods fails with connection errors rather than "the Service is down".

## Your first manifest, line by line

Write the desired state in a file instead of typing imperative commands. Files can be reviewed, stored in Git and re-applied.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  namespace: practice
  labels:
    app: orders-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orders-api          # which Pods this Deployment owns
  template:                    # the Pod blueprint
    metadata:
      labels:
        app: orders-api        # must match the selector above
    spec:
      containers:
        - name: api
          image: registry.example.com/orders-api:1.0.0
          ports:
            - containerPort: 8000
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: orders-api
  namespace: practice
spec:
  selector:
    app: orders-api            # matches the Pod labels
  ports:
    - port: 80                 # the Service's port
      targetPort: 8000         # the container's port
```

Reading it: `spec.selector.matchLabels` must match `spec.template.metadata.labels` (the API server rejects a mismatch); `template` is the Pod blueprint; without a `readinessProbe` a Pod counts as ready the moment its container starts; `port` is what clients use and `targetPort` is the container's port.

A note on images: `:1.0.0` is a tag, and tags can be moved. Pin a specific version and **never use `latest`**.

## A practice cluster with `kind`

You can run a real cluster on a laptop. `kind` ("Kubernetes in Docker") runs each node as a container.

```yaml
# kind-three-node.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
  - role: worker
```

```bash
kind create cluster --name practice --config kind-three-node.yaml
kubectl cluster-info --context kind-practice
kubectl get nodes -o wide
kubectl create namespace practice
```

Other tools (minikube, k3d, Docker Desktop's cluster) teach the same lessons.

**What a practice cluster does and does not teach**

| It teaches | It cannot prove |
| --- | --- |
| Objects, controllers, selectors, probes, events | Production failover: one machine hosts all the "nodes", so one power loss ends everything |
| Rolling updates and rollback | Zone failure behaviour: there are no real zones |
| Service discovery inside a cluster | Real load balancers and cloud integrations |
| Reading `describe` and logs | Real storage durability: volumes are on one host |

Know which of your claims survive that gap. A practice cluster that "survived" a Pod deletion proved only that the Deployment replaced a Pod.

## The first commands: a guided session

```bash
kubectl -n practice apply -f orders-api.yaml
kubectl -n practice rollout status deployment/orders-api
kubectl -n practice get pods -o wide
kubectl -n practice delete pod <one-pod-name>       # watch it come back
kubectl -n practice get pods --watch                # Ctrl-C to stop
kubectl -n practice scale deployment orders-api --replicas=3
kubectl -n practice port-forward svc/orders-api 8080:80
curl -s http://127.0.0.1:8080/health
```

What to observe:

1. After the delete, a *new* Pod with a different name and IP appears. The ReplicaSet controller saw fewer Pods than two. A Pod is replaced, not repaired.
2. After `scale`, a third Pod appears. You changed `spec.replicas`; the controller did the rest.
3. `port-forward` tunnels through the API server to one Pod. It does **not** test the Service's load balancing or readiness behaviour.

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | How to find it | Fix |
| --- | --- | --- | --- |
| Selector does not match Pod labels | Service exists but requests fail; no endpoints | `kubectl get endpoints orders-api` shows `<none>` | Make the Service selector match the labels |
| Wrong image name or tag | `ImagePullBackOff` | `describe pod` events: "not found" or "unauthorized" | Correct the image; add pull credentials if the registry is private |
| Application crashes at start | `CrashLoopBackOff` | `kubectl logs <pod> --previous` | Fix the error shown in the log |
| Readiness path is wrong | Pod `Running` but `0/1` Ready; rollout never completes | `describe pod`: "Readiness probe failed" | Correct path or port |
| Asking for more CPU or memory than any node has | `Pending` forever | `describe pod`: "Insufficient cpu/memory" | Lower the request or add capacity |
| Port confusion (`port` versus `targetPort`) | Connection refused through the Service, works by `port-forward` to the Pod | Compare Service `targetPort` to the container port | Fix `targetPort` |

**A first diagnostic routine.** When something does not work, do these in order and write down what you see:

1. `kubectl get pods -o wide` — which Pods, which status, which node?
2. `kubectl describe pod <name>` — read the **Events** at the bottom.
3. `kubectl logs <name>` (and `--previous` after a crash) — what did the application say?
4. `kubectl get endpoints <service>` — does the Service have addresses?
5. `kubectl get events --sort-by=.lastTimestamp` — what else happened recently?

## What Kubernetes does not do

| Common assumption | Reality |
| --- | --- |
| "It makes my app highly available" | It restarts and reschedules. Availability depends on replicas, spread, probes, disruption budgets and the failure domains beneath |
| "It backs up my data" | It does not. Persistent volume claims are storage claims, not backups |
| "It secures my app" | Defaults are permissive. Security is access control, admission policy, network policy and image hygiene |
| "It deploys safely" | A Deployment rolls out what you tell it. A bad image that passes its probe still ships |
| "It scales my database" | Stateful systems need their own replication design |
| "It fixes slow code" | More replicas multiply a problem as readily as they spread load |

## Knowledge consolidation

- Kubernetes is a **reconciliation system**: you declare desired state (`spec`), controllers observe reality (`status`) and act on the difference, continuously.
- The **API server** is the single door to cluster state, which etcd stores; the **scheduler** places Pods, **controllers** keep counts and versions right, and the **kubelet** makes containers happen on each node.
- Components communicate by **watching and writing state**, not by calling each other.
- A **Pod** is the ephemeral unit of scheduling; a **Deployment** manages ReplicaSets, which manage Pods; a **Service** gives a stable address to the *ready* Pods that match its selector.
- **Labels and selectors** are exact-match glue; a mismatch is the most common beginner fault.
- **Namespaces** partition names and later policy; always state which one you mean.
- Diagnose by reading **spec versus status**, then **events**, then **logs**.
- A practice cluster teaches the model; it **proves nothing** about production failover, zones or storage.

## Exercises

**Exercise 1 — Build the practice cluster.** Create the three-node `kind` cluster above. Run `kubectl get nodes -o wide` and `kubectl -n kube-system get pods -o wide`. List which components you can see as Pods and which you cannot, and explain the difference.

**Exercise 2 — Deploy and replace.** Apply the `orders-api` manifest (substitute an image you can pull, for example a small web server, and adjust the probe path to one it serves). Delete one Pod. Describe, in order, what the Deployment did and which object noticed, using `kubectl get events`.

**Exercise 3 — Break the selector.** Change the Service selector to `app: orders-apix`, apply, and run `kubectl get endpoints orders-api`. Fix it and watch the endpoints return. Write one sentence explaining why the Pods kept running throughout.

**Exercise 4 — Three failures, three signatures.** Deploy, one at a time, (a) a nonexistent image tag, (b) a request for `100` CPUs, (c) a wrong readiness path. For each, record the Pod status, the key line in `describe` events and the first command you used.

**Exercise 5 — Draw the journey.** From memory, draw the `kubectl apply` journey for a Deployment of two Pods, naming the component at each step and the stored object it wrote.

**Solution notes.**

*Exercise 1.* On `kind`, the control-plane components (API server, etcd, scheduler, controller manager) run as *static Pods* on the control-plane node, so they appear in `kube-system`; CoreDNS and the network plugin also appear. The kubelet and the container runtime are system processes on each node, not Pods, so you will not see them in `get pods`. That difference is a good first demonstration that "a component" and "a Pod" are not synonyms.

*Exercise 2.* A strong answer reads: the Pod was deleted; the ReplicaSet controller saw fewer Pods than `replicas`; it created a Pod record; the scheduler assigned a node; the kubelet pulled the image and started the container; the readiness probe passed and the Pod joined the Service endpoints. Events will show `Scheduled`, `Pulled`, `Created`, `Started`. Exact timings and names vary.

*Exercise 3.* `get endpoints` shows `<none>` while the selector is wrong, because no Pod carries `app: orders-apix`. The Pods kept running because the Service is only a routing record; changing it affects traffic, not the Pods' lifecycle.

*Exercise 4.* Expected: (a) `ErrImagePull` then `ImagePullBackOff`, events "manifest unknown" or "not found", first command `describe pod`; (b) `Pending`, event `0/3 nodes are available: 3 Insufficient cpu`; (c) `Running` but `0/1` Ready, event "Readiness probe failed: HTTP probe failed with statuscode: 404", and the Deployment rollout waits. Wording differs by version; the pattern is what to record.

*Exercise 5.* Check your drawing against the eight-step table. Marks go for the order and for showing that the scheduler and kubelet are driven by stored state rather than by direct calls.

## Mentoring prompts

Why does deleting a Pod managed by a Deployment not make the application smaller? What does it mean that `status` is "owned by the system", and what would go wrong if you edited it? A Service shows no endpoints while all Pods are `Running`: list the three most likely causes in the order you would check them. What can a three-node `kind` cluster tell you about production failover, and what must you refuse to claim?

---
