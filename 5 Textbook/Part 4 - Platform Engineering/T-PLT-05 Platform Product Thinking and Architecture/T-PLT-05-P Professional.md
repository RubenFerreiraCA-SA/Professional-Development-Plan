# T-PLT-05-P — Professional Engineering

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-p"></a>
#### T-PLT-05-P — Professional Engineering

**An integrated outcome matrix.** Define the platform's promises as outcomes a user could verify, and map each to evidence:

| Outcome | Capabilities it integrates | Evidence |
| --- | --- | --- |
| 1. A developer creates a service | Template, repository governance, container build | The service exists with owner and runbook; review gate was required |
| 2. A reviewed change triggers a trusted build | Review and branch protection, CI, registry | Pull request, run, digest, attestation |
| 3. Self-service deployment under identity and policy | Infrastructure as code, GitOps, access control, templates | Tenant manifests, promotion pull request, policy denial transcript |
| 4. Health, failure and recovery are visible and rehearsed | Observability, Kubernetes, operations | Drill timelines, runbooks, status output |
| 5. An independent developer succeeds without help | Everything | An acceptance record |

Nothing counts as done without a link to evidence you can open. Optional capabilities (AI features, a specific monitoring vendor) are marked "not in scope" rather than half-delivered, with an equivalent bar recorded if a substitute is used.

**What "trusted" means — and does not.**

| Control | Claim it supports | What it does *not* prove |
| --- | --- | --- |
| Required review plus code owners | A second person saw the change | That the reviewer understood it |
| Required tests | Known regressions are blocked | The absence of bugs |
| Immutable digest | The same bytes run everywhere | That the bytes are safe |
| Provenance attestation | This digest was built by this workflow from this commit | That the source or workflow is benign; a compromised build system could sign anything |
| SBOM | You know the contents | That the contents are free of vulnerabilities |

**Promotion that verifies before it moves.** A promotion check binds *digest → expected source repository → approved workflow → required commit on the protected release branch*, and rejects on any mismatch. An attestation alone is not enough: the check must also compare the source commit against policy. The release process writes a small evidence record per digest so promotion can look up the allowed commit:

```json
{"commit": "9d2f...", "workflow": "release", "image": "registry.example.com/orders-api@sha256:3f1c...", "ref": "refs/heads/main", "event": "push"}
```

**One page shows the chain**: merge commit → run URL → digest → attestation commit → promotion pull request. Without a break in that chain, the artefact is traceable.

**Approved environments and identities**

| Question | Platform answer to record |
| --- | --- |
| Which environments can a developer promote to? | Staging by tool; production-shaped environments need a platform reviewer, not self-service |
| Who applies manifests? | A per-tenant reconciler identity with rights only inside its namespace |
| What can CI do? | Push images and attestations — no cluster credentials |
| What can a developer do in the cluster? | Read-only status; changes by pull request |

**Policy in two places.** Policy in CI (an offline evaluator, no credentials) gives fast feedback; policy at admission catches everything that bypassed CI. Use the *same* rules. Distinguish offline CI evaluation from live admission probes, which need a disposable cluster and show which layer (policy engine, Pod Security, RBAC) produced a denial.

**Secrets.** No secret lives in Git. For a demonstration database, an operator creates the credential out of band; record who creates it, how it rotates and the limitation of the environment (for example, base64 in etcd, unencrypted). Production-shaped options (an external secrets operator, sealed secrets or SOPS) are the next step.

**Stateful dependencies deliberately.** State is expensive to get wrong, so add it as an opt-in platform component, with a documented human gate. It must satisfy the tenant's restricted Pod Security and default-deny network policy (explicit allow rules for the application and database).

**Define health and recovery targets before injecting failures.**

| Signal | Where | Healthy |
| --- | --- | --- |
| Pod Ready and restarts | Status tool, `kubectl` | Ready; restarts stable |
| Readiness body | `/ready` | `database: query_ok` — an authenticated query, not a TCP connect |
| Application contract | Write then read an entry | The same entry returns |
| Service endpoints | `kubectl get endpoints` | Non-empty |
| Backup freshness | Newest successful job and off-cluster copy | Within target age |

Set targets (for example RTO ≤ 3 minutes to a working read-write path) and report both measured recovery time and *estimated recovery-point age* (incident time minus last completed backup).

**Decision guide**

| Need | Do | Avoid |
| --- | --- | --- |
| Describe the platform | Outcomes with evidence links | A feature list |
| Explain trust | A claims table with "does not prove" columns | "Signed, therefore secure" |
| Record decisions | ADRs with alternatives and revisit triggers | Slide-deck architecture |
| Be honest | A limitations register from day one | Discovering limits during the demonstration |
| Handle state | Opt-in component, explicit human gate, restore drill | Treating a volume as a backup |
