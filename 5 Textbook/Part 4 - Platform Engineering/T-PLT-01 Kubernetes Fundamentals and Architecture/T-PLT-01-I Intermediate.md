# T-PLT-01-I — Intermediate Practice

*Chapter: [T-PLT-01 — Kubernetes Fundamentals and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-01-i"></a>
#### T-PLT-01-I — Intermediate Practice

**Declarative manifests.** Write YAML and apply it, rather than running imperative commands:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  labels: { app: orders-api }
spec:
  replicas: 2
  selector:
    matchLabels: { app: orders-api }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxUnavailable: 0, maxSurge: 1 }
  template:
    metadata:
      labels: { app: orders-api }
    spec:
      serviceAccountName: orders-api
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: api
          image: registry.example.com/orders-api@sha256:3f1c...e9a0
          ports: [{ containerPort: 8000 }]
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          resources:
            requests: { cpu: 100m, memory: 128Mi }
            limits:   { memory: 256Mi }
          startupProbe:   { httpGet: { path: /health, port: 8000 }, failureThreshold: 30, periodSeconds: 2 }
          readinessProbe: { httpGet: { path: /ready,  port: 8000 }, periodSeconds: 5 }
          livenessProbe:  { httpGet: { path: /health, port: 8000 }, periodSeconds: 10 }
---
apiVersion: v1
kind: Service
metadata: { name: orders-api }
spec:
  selector: { app: orders-api }
  ports: [{ port: 80, targetPort: 8000 }]
```

```bash
kubectl apply -f deploy.yaml
kubectl rollout status deployment/orders-api
kubectl describe deployment orders-api
kubectl rollout undo deployment/orders-api
kubectl get events --sort-by=.lastTimestamp
```

**Three probes, three questions**

| Probe | Question | Failure action |
| --- | --- | --- |
| `startupProbe` | Has it finished starting? | Kill the container if it never succeeds; disables the other probes until success |
| `readinessProbe` | Should it receive traffic now? | Remove from Service endpoints; no restart |
| `livenessProbe` | Is it wedged beyond self-recovery? | Restart the container |

The classic incident: a liveness probe that checks a dependency. The database blips, every replica fails liveness and restarts, and a small outage becomes a large one. **Liveness checks the process; readiness checks whether it should serve.**

**Probe design rules**

| Rule | Reason |
| --- | --- |
| Liveness is cheap and dependency-free | Avoid cascading restarts |
| Readiness may check critical dependencies — carefully | A shared dependency failure empties all endpoints |
| Use `startupProbe` instead of a huge `initialDelaySeconds` | Fast detection after start, tolerance for slow start |
| `timeoutSeconds` shorter than `periodSeconds` | Probes do not pile up |
| Avoid heavy `exec` probes | CPU cost at scale |

Break each probe deliberately, observe `kubectl get pods` and `describe` events for each failure, then restore.

**Requests, limits and quality of service**

| Setting | Used by | Effect |
| --- | --- | --- |
| `requests` | Scheduler, autoscaler, quotas | Capacity reserved for placement |
| `limits.memory` | Kernel control group | Exceeded: container is OOM-killed |
| `limits.cpu` | Kernel CPU quota | Exceeded: throttled (slow, not killed) |

Quality-of-service classes follow: `Guaranteed` (requests equal limits), `Burstable`, `BestEffort` (first evicted). Measure usage (`kubectl top pods`) before setting requests; too low causes overcommit, too high wastes capacity. Cause an OOM kill on purpose and read `Last State: OOMKilled` in `describe`.

**Configuration and secrets**

| Mechanism | Use for | Notes |
| --- | --- | --- |
| Environment literal | Tiny non-sensitive switches | Visible in `describe` |
| ConfigMap | Non-sensitive config | Env changes need a restart; mounted files update eventually |
| Secret | Credentials | Base64-encoded, not encrypted by default |
| Image build | Code and static assets only | Never environment-specific config or secrets |

A change to a ConfigMap does not restart Pods by itself; use a hash annotation or a tool that triggers a rollout.

**Services and DNS.** Every Pod has its own IP; Pod IPs are ephemeral; a Service gives a stable virtual address and DNS name (`orders-api.<namespace>.svc.cluster.local`) that load-balances across *ready* endpoints.

| Service type | Reachable from | Typical use |
| --- | --- | --- |
| `ClusterIP` | Inside the cluster | Default internal APIs |
| `NodePort` | Node address and port | Debugging, building block |
| `LoadBalancer` | A cloud load balancer | External exposure (needs a cloud controller) |
| `ExternalName` | DNS alias | Point at an external host |
| Headless (`clusterIP: None`) | DNS returns Pod addresses | StatefulSets, client-side discovery |

`kubectl port-forward` tunnels through the API server to one Pod; it bypasses the Service's load balancing and readiness behaviour, so a success there does not prove the Service works.

**Exercise.** Deploy the manifest, break readiness (wrong path) and liveness (failing endpoint) in turn, and record what each does to endpoints and restarts.
