# T-DEV-05-B — Beginner Foundations

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-b"></a>
#### T-DEV-05-B — Beginner Foundations

**Push versus pull.**

| Model | Who changes the cluster | Audit trail |
| --- | --- | --- |
| Imperative / push | A human or pipeline runs `kubectl` or API calls | Scattered across logs |
| GitOps / pull | A controller reconciles toward Git | Commits plus controller events |

CI still builds and publishes artifacts. GitOps declares *which* artifact each environment should run. CI should not need administrator access to the cluster just to deploy.

**Key terms**

| Term | Meaning |
| --- | --- |
| Desired state | What Git says should be running. |
| Live state | What is actually running. |
| Reconciliation | A loop that compares them and acts to converge. |
| Drift | Live state differs from desired state. |
| Prune | Delete live resources that were removed from desired state. |
| Self-heal | Automatically revert manual changes to match Git. |

**Who owns what.**

| System | Owns |
| --- | --- |
| Infrastructure as code | Cluster, networks, identity foundations |
| Git desired-state directory | Workload definitions (Deployments, Services, configuration) |
| GitOps controller (Flux, Argo CD) | Reconciling Git into chosen namespaces |
| Humans in an emergency | Break-glass changes, then returning ownership to Git |

**A first mental run.** You change `replicas: 2` to `replicas: 3` in a file and open a pull request. After review and merge, the controller notices a new commit, renders the manifests, compares with the cluster and creates the third replica. You never ran a deploy command. If someone scales to five by hand, the controller changes it back to three.

**Declarative configuration with overlays.** Kustomize keeps a shared base and small per-environment overlays:

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

```yaml
# overlays/staging/kustomization.yaml
resources: [../../base]
namespace: orders-staging
images:
  - name: orders-api
    newName: registry.example.com/orders-api
    digest: sha256:3f1c...e9a0
replicas:
  - name: orders-api
    count: 2
```

You can preview any overlay locally with `kubectl kustomize deploy/orders-api/overlays/staging` without touching a cluster.

**Exercise.** Render both overlays, diff the outputs and explain in your own words why the digest (not a tag) appears in the overlay.
