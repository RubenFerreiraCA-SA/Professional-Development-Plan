# T-PLT-07-B — Beginner Foundations

*Chapter: [T-PLT-07 — Platform Integration, Reliability and Evolution](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-07-b"></a>
#### T-PLT-07-B — Beginner Foundations

**Putting the pieces together.** Individual practices — repository rules, containers, CI, infrastructure as code, GitOps, observability, Kubernetes, templates — each work alone. A *platform* works when a developer can use them as one path, and you can show with evidence that each part holds.

**The end-to-end path**

```text
create service (template)
   → pull request with required review and checks
   → trusted build produces an image digest plus evidence
   → promotion pull request changes only the digest
   → policy checks pass in CI and at admission
   → GitOps controller deploys it
   → status, logs, metrics and traces show health
   → a failure is detected, diagnosed and recovered by a runbook
```

**Integration debt compounds.** Fix one layer at a time: get the stateless path green end to end before adding state, extra environments or extra capabilities. The seams between components — not the components — are where most defects live.

**Evidence, not claims.** For each step ask: how would I show another person this works? A log line, a rejected change, a status command output, a timeline. Collect it as you go.

**A first integration checklist**

| Check | Evidence to keep |
| --- | --- |
| A service can be created by following the docs | The resulting repository and catalogue entry |
| A failing test blocks merge | The pull request with the red check |
| An image is built once and identified by digest | Run URL and digest |
| A promotion changes only a digest | The promotion pull request diff |
| The running Pod uses that digest | `kubectl` output showing the image ID |
| The service reports health | Status output |
| A planted failure is recoverable | Timeline and runbook version used |

**Worked example: one change through the whole path.** Suppose a developer changes a validation message in `orders-api`. Track the single artefact that crosses each boundary:

| Stage | What happens | Artefact that crosses the boundary | Proof you can show |
| --- | --- | --- | --- |
| Change | Branch and commit | Commit SHA | `git log -1 --format=%H` |
| Review | Pull request with required review and checks | Merge commit on `main` | Pull request page showing the approval and green checks |
| Build | Trusted pipeline builds once | Image digest `sha256:…` | Pipeline run URL and the digest it printed |
| Artefact | Image stored in the registry | Digest-addressed image | `docker manifest inspect` or registry listing |
| Deploy | Promotion changes only the digest; controller applies it | Desired state in Git | Promotion diff and controller sync status |
| Run | Pods start from that digest | Running Pod | `kubectl get pod -o jsonpath='{.items[*].status.containerStatuses[*].imageID}'` |
| Observe | Telemetry shows health | Logs, metrics, traces | Dashboard link and a log line mentioning the new version |

If the digest in the registry differs from the one in the Pod, then the seam between the build and deploy stages is broken, no matter how good each stage looks on its own.

**What "integration debt" looks like.** It is the accumulated cost of components that each work but were never connected end to end: a template that creates a repository the pipeline cannot build; a pipeline that publishes a tag the cluster never pulls; dashboards that exist but show no data for the new service. Typical sources: two teams each assume the other owns the seam, manual steps that nobody wrote down, and "temporary" workarounds that became permanent.

**Why stateless first.** A stateless service has one dependency chain to verify and can be restarted without consequences. Databases add backups, migrations, credentials and failure recovery. If you add them while the basic path is still red, every failure has many possible causes. Get the plain path green, record the evidence, then add one complication at a time.

**Applying the checklist.** For each row of the checklist assign one of three marks:

| Mark | Meaning |
| --- | --- |
| Proven | You have a command output, link or log line you can show someone now. |
| Claimed | You believe it works but have no evidence yet. |
| Unknown | You have not looked. |

The *weakest seam* is the first stage whose mark is not "Proven" and whose failure would stop everything after it. That is where the next hour of work belongs.

**Common mistakes**

- Declaring the path "done" because each team's component passed its own tests.
- Verifying by reading configuration instead of observing behaviour. The Pod's image ID, not the manifest, tells you what is running.
- Using mutable tags such as `latest`, which makes the artefact crossing the boundary ambiguous.
- Skipping the failure step. A path that has only been shown working has not been shown recoverable.
- Collecting evidence at the end from memory. Capture it while you do each step.

**Exercise 1.** Draw the path for your own service as seven boxes. Under each box write the artefact leaving it and one proof command. Mark each box Proven, Claimed or Unknown and circle the weakest seam.

**Exercise 2.** Walk the path with a small example service. For each step, write the one command or link that proves it.
