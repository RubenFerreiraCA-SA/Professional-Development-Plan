# T-PLT-06-B — Beginner Foundations

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-b"></a>
#### T-PLT-06-B — Beginner Foundations

**Cognitive load.** Three kinds exist: *intrinsic* (the problem is hard), *extraneous* (the tooling makes it harder than necessary) and *germane* (effort that builds useful understanding). Platforms exist to cut extraneous load. Developers should spend their effort on their domain, not on remembering twelve flags.

**A golden path** (or "paved road") is the opinionated, supported, *easiest* way to do a common job. It is not a cage:

| Property | Meaning |
| --- | --- |
| Opinionated | One default for language, packaging, deploy and observability |
| Complete | Covers create → build → deploy → operate, not just scaffolding |
| Supported | The platform team fixes it when it breaks |
| Optional but attractive | Leaving is allowed; then you own more (an escape hatch) |
| Understandable | Developers can see what the path did and why; no magic they cannot inspect |

**A golden-path specification** is a short document:

```markdown
# Golden path: new HTTP service
## Prerequisites (one-time)  - tools with versions, access, who approves
## Steps                     - numbered, copy-pasteable, with expected output
## Done means                - acceptance checks (service in catalogue, status healthy, promotion recorded)
## Not covered (v1)          - stateful services, non-HTTP workloads, ...
## Escape hatch              - how to leave the path and what you then own
```

**The first thirty minutes.** Onboarding is where platforms lose users. One entry document, in this order: what the platform does for you (three sentences) and what it will not do; a tool checklist with exact versions and a one-line verification command each; access — how to obtain it, who approves it and the expected wait (a documented wait is fine; an unwritten one is a defect); a "hello" smoke test; links to the golden path and the "I'm stuck" page.

**Test your own onboarding.** On a clean account or container, follow the document verbatim. Every command you must improvise is a defect; fix the document, not your memory.

**Classifying cognitive load: an example.** A new developer onboarding a service meets three frustrations:

| Frustration | Kind | Can the platform remove it? |
| --- | --- | --- |
| "I do not understand how retries and idempotency work for an order API." | Intrinsic | No. That is the domain problem; the platform may support learning. |
| "I had to copy a Dockerfile, a pipeline and Kubernetes YAML from three repositories and still got it wrong." | Extraneous | Yes. A template removes the copying. |
| "Seeing how the pipeline promotes images helped me understand release safety." | Germane | Keep it. Hide the plumbing, not the learning. |

The skill is classifying before fixing. Removing germane load by hiding everything creates magic nobody can debug; leaving extraneous load in place burns time.

**A golden path versus its neighbours**

| Idea | What it is | Difference from a golden path |
| --- | --- | --- |
| Mandate | A rule you must follow | A golden path is chosen because it is easier, not forced |
| Template | A scaffold generated once | A path includes operating the service after creation |
| Cage | A path with no exit | A golden path has a documented escape hatch |
| Standard | A documented expectation | A path is the working implementation of the standard |

An *escape hatch* example: a team needs a language the path does not support. They may leave the path, provided they meet the same requirements (build evidence, health endpoints, ownership metadata) and accept that they now own the pipeline maintenance.

**A filled-in specification (excerpt)**

```markdown
# Golden path: new HTTP service
Audience:  an application developer who has not used the platform before
Outcome:   a running service with CI, a deployed staging environment and a dashboard
Success:   median time from "start" to first healthy deployment <= 60 minutes,
           measured over the last five new services
## Steps
1. Run `platform new service --name orders-api --template http-python`.
2. Open the generated pull request; wait for the green check.
3. Merge. Open the status page and confirm "Healthy".
## Supported variations
language: python or go; datastore: none or managed Postgres
## Not covered (v1)
queues, batch jobs, GPU workloads
## Escape hatch
Document in the repository why you left; you own build and deploy maintenance.
```

The *measurable success condition* is what keeps the path honest. Without a number, "easy" is an opinion.

**Entry-document structure, with the reason for the order**

| Order | Section | Why here |
| --- | --- | --- |
| 1 | Goal and outcome | The reader decides in 10 seconds whether this page is for them |
| 2 | Prerequisites with verification commands | Failures here are cheapest to fix before any real work |
| 3 | One command | An early quick win builds confidence |
| 4 | Expected output | Lets the reader know if they are on track |
| 5 | What next | Prevents a dead end after success |
| 6 | Where to get help | Gives the reader an exit when something breaks |

**Running the clean-machine test.** Use a container or fresh account and keep a log:

```bash
docker run --rm -it ubuntu:24.04 bash        # a clean environment
# follow the document verbatim; log each deviation:
#   step 3: needed `apt-get install curl` (undocumented prerequisite)
#   step 5: output differed from the document (version changed)
```

Every deviation becomes a fix to the document or the path, with the date. Re-run after each fix; the test ends when no improvisation is needed.

**Common mistakes**

- Writing the document from memory on a machine that already has everything installed.
- Documenting what the platform *can* do instead of the first task a developer actually has.
- Calling something a golden path while it is a mandate with no exit.
- Starting with a long architecture description before the reader has run anything.
- Stating "easy" without measuring how long a new person takes.

**Exercise.** Write the entry document for a platform you know, run it on a clean machine, and list every improvised step.
