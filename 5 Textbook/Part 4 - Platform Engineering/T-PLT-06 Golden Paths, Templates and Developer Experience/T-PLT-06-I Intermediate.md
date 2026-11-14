# T-PLT-06-I — Intermediate Practice

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-i"></a>
#### T-PLT-06-I — Intermediate Practice

**A template is a product artefact.** A template that generates code is easy. A template that generates a service which *builds, passes policy, deploys, reports health, has a runbook and appears in the catalogue* is the golden path. Design rules:

- Generate only what a developer would otherwise copy and paste; keep generated files short and readable.
- Platform-owned logic lives *outside* the generated service (reusable workflows, shared base manifests) so fixes propagate; the generated code *calls* it.
- Everything generated is inspectable plain files. No hidden state.
- Fail early with helpful errors (naming rules, missing owner).

**Layout of a generated service**

```text
services/<name>/
  app/                  # starter code with /health and /ready
  Dockerfile
  deploy/               # thin overlay referencing platform base manifests
  .github/workflows/    # calls the reusable platform workflow
  RUNBOOK.md            # starter runbook with the status command first
  README.md             # includes a "deviations from the golden path" section
catalog/<name>.yaml     # ownership and links, in a portal-compatible shape
```

**A scaffolding command with validation**

```bash
platform/bin/new-service --name orders-api --owner team-orders --language python
# validates: lowercase name pattern, owner exists, name not already in the catalogue
# writes files, runs the offline checker, prints next steps
```

**Test the template like software.** Split offline checks from cluster checks:

- *Offline (required PR check, no cluster credentials):* generate a service into a temporary directory, run formatters and linters, render manifests, evaluate policy against the rendered output, verify the catalogue entry and run the generated unit tests.
- *Cluster (disposable lab):* deploy the generated service, check readiness and a status command, then delete.

A template never generated in CI will rot.

**Safe self-service means guardrails, not freedom.** The limits are the product:

| Guardrail | Enforced by | Developer sees |
| --- | --- | --- |
| Naming and ownership rules | Scaffold plus a policy check | A clear error with the fix |
| Quota and defaults per namespace | Tenant manifest | "Quota exceeded: pods 6/6" |
| Digest-only images | Promotion tool, check, and admission policy | A rejection naming the rule |
| No administrator rights for developers | RBAC; a namespaced reconciler | Read-only status; changes by pull request |
| Review before change | Branch protection and code owners | Required reviewer and checks |
| Secrets never in Git | Secret scanning and a documented secret path | A blocked push or documented alternative |

Documented human gates are acceptable if they are *designed*: for example, creating a tenant namespace needs a platform reviewer; record the expected response time in the path.

**Promotion by pull request.** A promotion tool takes service, environment and digest, validates all three (environment allowed, digest well-formed and previously released), edits the overlay and opens a pull request. A policy check runs on the pull request and again at admission.

**Escape hatch and exceptions.** Teams will leave the path. Define a *deviation record* in the service README (what, why, who owns the consequence), an *exception expiry* (reviewed quarterly) and a *platform gap issue* for each deviation — every deviation is also a product signal.

**Exercise.** Generate a service from a template, deliberately delete its readiness probe and confirm the checker fails with a message a developer could act on.
