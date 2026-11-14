# T-PLT-01-B — Beginner Foundations

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-b"></a>
#### T-PLT-01-B — Beginner Foundations

**What cloud-native asks of an application.** "Cloud-native" does not mean "runs on Kubernetes". It is a set of operating assumptions that platforms like Kubernetes exploit:

| Property | What the platform assumes | Example |
| --- | --- | --- |
| Disposable processes | Any instance may be killed and replaced | Stateless service |
| Configuration from the environment | The same image runs everywhere; config is injected | `DATABASE_HOST` environment variable |
| Logs to standard output | The platform collects them | No log files managed by the app |
| Health endpoints | The platform can ask "alive?" and "ready?" separately | `/health` and `/ready` |
| Graceful shutdown | `SIGTERM` leads to a prompt, clean exit | Draining in-flight requests |
| Backing services by address | The database is a host name, not a local process | Connection string |

If one is false — for example, sessions kept in memory — Kubernetes will schedule the app happily and expose the flaw during the first rollout or node maintenance.

**Architecture in one picture.**

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

Key ideas:

- The **API server** is the only door to the cluster's stored state (etcd). Everything — `kubectl`, controllers, kubelets — reads and writes objects through it. That is why access control on the API is the central security control.
- **Controllers reconcile.** You declare `replicas: 2`; a controller sees one running Pod and creates another. There is no "start a container" command in the model, only desired state.
- **Pods** are the unit of scheduling: one or more containers sharing a network namespace and volumes.
- **Nodes** run the *kubelet*, which turns Pod specifications into running containers, runs probes and reports status.

**The core objects**

| Object | Owns | Why it exists |
| --- | --- | --- |
| Pod | Containers, volumes, network identity | Unit of scheduling; ephemeral |
| ReplicaSet | N identical Pods | Keeps the count |
| Deployment | ReplicaSets across versions | Rolling updates, rollback, history |
| Service | A stable address in front of Pods | Load-balances across ready Pods |
| Labels and selectors | Association | How controllers and Services find their Pods |

A bare Pod that dies stays dead. That is the point of a Deployment.

**First commands**

```bash
kubectl cluster-info
kubectl get nodes
kubectl create namespace practice
kubectl -n practice create deployment web --image=nginx:1.27 --replicas=2
kubectl -n practice get pods -o wide
kubectl -n practice delete pod <one-pod>      # watch it come back
kubectl -n practice expose deployment web --port 80
kubectl -n practice port-forward svc/web 8080:80
```

**What Kubernetes does not do**

| Common assumption | Reality |
| --- | --- |
| "It makes my app highly available" | It restarts and reschedules. Availability depends on replicas, spread, probes, disruption budgets and the failure domains beneath |
| "It backs up my data" | It does not. Persistent volume claims are storage claims, not backups |
| "It secures my app" | Defaults are permissive. Security is access control, admission policy, network policy and image hygiene |
| "It deploys safely" | A Deployment rolls out what you tell it. A bad image that passes its probe still ships |
| "It scales my database" | Stateful systems need their own replication design |

**Training cluster versus production cluster.** A one-machine practice cluster (for example `kind`) has a single control plane, node-local storage and no real load balancer. It teaches the model but proves nothing about production failover. Know which of your claims survive that gap.

**Exercise.** Create a three-node practice cluster, deploy two replicas, delete a Pod and describe what the Deployment did and which object noticed.
