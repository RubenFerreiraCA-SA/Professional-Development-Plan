# T-DEV-05-I — Intermediate Practice

*Chapter: [T-DEV-05 — GitOps and Release Operations](README.md) · Part 1 — DevOps Engineering*

<a id="t-dev-05-i"></a>
#### T-DEV-05-I — Intermediate Practice

**Installing a controller.** Use an isolated practice cluster (for example, `kind`). With Flux:

```bash
kind create cluster --name gitops-lab
flux check --pre
flux bootstrap github --owner=example-org --repository=orders-platform \
  --branch=main --path=clusters/lab --personal
```

Bootstrap writes controller manifests into the repository and configures a Git credential. After bootstrap, hand over from the broad bootstrap token to a read-only deploy key, then revoke the token. *Bootstrap* writes configuration once; *reconcile* only needs to read desired state forever.

**Pointing the controller at your configuration.**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata: { name: orders-staging, namespace: flux-system }
spec:
  interval: 1m
  sourceRef: { kind: GitRepository, name: flux-system }
  path: ./deploy/orders-api/overlays/staging
  prune: true
  wait: true
  timeout: 3m
```

Create one object per environment so staging and production reconcile independently.

**Read controller signals.** Distinguish *source failed* (Git unreachable or auth wrong), *build failed* (bad YAML or Kustomize error) and *health check failed* (workload not Ready):

```bash
flux get sources git
flux get kustomizations
kubectl -n flux-system logs deploy/kustomize-controller --tail=50
flux reconcile kustomization orders-staging --with-source
```

**Promotion through Git.** Promotion is a reviewed change to desired state:

| Actor | Allowed |
| --- | --- |
| CI release | Publish `image@sha256:…` plus evidence |
| Human or bot pull request | Update the overlay's `images:` entry to that digest |
| Controller | Pull and reconcile each environment |
| CI with cluster-admin | Not required |

Promote the *same digest* from staging to production by changing only the digest line in the production overlay, then verify both environments run it (`kubectl get deploy -o jsonpath='{..image}'`).

**Image pull paths.** With a local practice cluster, `kind load docker-image` places an image directly on nodes. For a private registry, the kubelet needs credentials (`imagePullSecrets` or a node/workload identity); your laptop's `docker login` does not transfer. Pinning a private digest without credentials produces `ImagePullBackOff`.

**Drift and self-heal.** Scale a Deployment by hand and watch the controller restore the Git value. A live image patch is temporary under active reconciliation: Git wins. For true emergencies, *suspend* reconciliation, make the fix, commit it to Git, then *resume*. Suspension is an explicit exception to ticket and time-box.

**Rollback by Git.** Record the SHA of the release commit that broke things, then `git revert <that-sha>` on the branch the controller watches and let it reconcile. Avoid a blind `git revert HEAD` after other merges have landed.

**Troubleshooting guide**

| Symptom | Likely cause | First check |
| --- | --- | --- |
| Kustomization not Ready | Bad path, YAML or auth | `flux get`; `kubectl kustomize` locally |
| `ImagePullBackOff` | Image missing on node, private registry, wrong digest | Events; pull credentials |
| `CrashLoopBackOff` | Application or configuration error | Logs; are probes too aggressive? |
| Remains drifted | Reconciliation suspended | `flux get`; resume |
| Prune deleted a shared object | Ownership mistake | Ownership list; restore from Git |
| Autoscaler shows unknown metrics | No metrics server | `kubectl top`; install it |

**Exercise.** Break a release deliberately (an unpullable digest), diagnose it from controller status, revert the recorded commit and confirm recovery.
