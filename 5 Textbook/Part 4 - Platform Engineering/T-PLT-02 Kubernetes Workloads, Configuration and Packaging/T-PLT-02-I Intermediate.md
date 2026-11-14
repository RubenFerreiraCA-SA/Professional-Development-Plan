# T-PLT-02-I — Intermediate Practice

*Chapter: [T-PLT-02 — Kubernetes Workloads, Configuration and Packaging](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-02-i"></a>
#### T-PLT-02-I — Intermediate Practice

**Choosing deliberately**

| Need | Prefer | Why |
| --- | --- | --- |
| Your own app with environment overlays | Kustomize | No templating logic; patches are plain YAML |
| Third-party software (controllers, databases) | Helm charts | Ecosystem distributes them; values expose supported options |
| A reusable, parameterised package for many teams | Helm or a higher-level template | Values schema, versioned releases |
| Both | Helm for vendors, Kustomize for ours; render Helm to YAML in CI if you need reviewable diffs | Avoid logic leaking into app config |

**Writing a good chart**

```yaml
# templates/deployment.yaml (excerpt)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "orders-api.fullname" . }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels: {{- include "orders-api.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels: {{- include "orders-api.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: api
          image: "{{ .Values.image.repository }}@{{ required "image.digest is required" .Values.image.digest }}"
          resources: {{- toYaml .Values.resources | nindent 12 }}
```

Practices: ship a `values.schema.json` to reject bad values early; require the image digest; keep secure defaults (non-root, read-only filesystem, no privilege escalation); use the checksum annotation so config changes roll Pods; keep templates shallow; test with `helm lint`, `helm template` and a policy check.

**Overlay patterns.** Use a base for everything shared; overlays for environment differences (replica counts, resource sizes, hostnames, image digest); strategic-merge patches or JSON patches for edits; generators for ConfigMaps with content hashes in names so changes trigger rollouts.

```yaml
configMapGenerator:
  - name: orders-config
    literals: [LOG_LEVEL=info, FEATURE_X=off]
```

**Config change triggers a rollout.** Change a literal, apply, and watch a new ReplicaSet roll out because the generated ConfigMap name (with hash) changed. Contrast with editing a plain ConfigMap in place, which does not restart Pods.

**Workload shapes in practice.** Write a Job that checks readiness and exits non-zero on failure (`backoffLimit: 1`, `ttlSecondsAfterFinished: 300`, `restartPolicy: Never`, same hardened security context). Write a CronJob with `concurrencyPolicy: Forbid`. Demonstrate that a StatefulSet's Pods keep stable names and volumes across restarts, and that a persistent volume claim outlives the Pod but not a lost node.

**Autoscaling basics.** A HorizontalPodAutoscaler scales replicas on metrics (CPU utilisation relative to requests by default). It needs a metrics source and correct requests; unknown metrics usually mean no metrics server. Demonstrate scale-out under controlled load, not only that the autoscaler object exists.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders-api }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: orders-api }
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } }
```

**Exercise.** Convert a service to a chart with a values schema, install it to two namespaces with different values, and demonstrate a config-triggered rollout.
