# T-PLT-06-B — Beginner Foundations

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-b"></a>
#### T-PLT-06-B — Beginner Foundations

## Why this matters

Imagine your first week on a team that runs its software on a shared platform. You have written code for years. Yet you cannot ship a one-line change, because you do not know which repository template to use, which pipeline to copy, how to ask for a namespace, where the dashboard lives, or who owns the thing you are about to break. Every one of those questions has an answer. The trouble is that the answers live in six places and three people's heads.

A platform team exists to remove that friction. The tools it builds are only half of the job: a build system, a cluster and a registry are all inert until a developer can use them without help. This chapter is about the other half. It covers the *paved road* a developer walks on day one, the *template* that creates their first service, the *documentation* that explains it, and the *promises* the platform makes in return for the developer's trust.

At Beginner level you will learn to describe a golden path precisely, classify the kinds of effort it should remove, write an entry document that survives a clean-machine test, and recognise the common ways first-service onboarding fails. Nothing here assumes a particular portal product, cloud or language. The examples use an imaginary `platform` command-line tool and a service called `orders-api`, but every idea transfers.

## First principles: effort has three kinds

Psychologists who study learning describe three kinds of mental effort, usually called **cognitive load**:

- *Intrinsic* load is the difficulty of the problem itself. Designing retries and idempotency for an order API is hard because ordering systems are hard. No tool removes it.
- *Extraneous* load is difficulty added by the way the task is presented or tooled. Copying a Dockerfile from three repositories and remembering twelve flags is extraneous. It teaches nothing about orders.
- *Germane* load is effort that builds understanding you will reuse. Seeing how a pipeline promotes an image teaches you what "release safety" means.

Platforms exist to cut extraneous load. A developer's limited attention should go to the domain, not to remembering syntax. The skill that matters is *classifying before fixing*:

| Frustration a new developer reports | Kind | Can the platform remove it? |
| --- | --- | --- |
| "I do not understand how retries and idempotency work for an order API." | Intrinsic | No. That is the domain problem; the platform may support learning. |
| "I copied a Dockerfile, a pipeline and Kubernetes YAML from three repositories and still got it wrong." | Extraneous | Yes. A template removes the copying. |
| "Seeing how the pipeline promotes images helped me understand release safety." | Germane | Keep it. Hide the plumbing, not the learning. |
| "I could not tell whether my deploy worked." | Extraneous | Yes. A status command gives a verdict. |
| "I did not know who had to approve my access." | Extraneous | Yes. Document the approver and the expected wait. |

Two failure directions follow. Remove germane load by hiding everything and you create magic that nobody can debug at 3 a.m. Leave extraneous load in place and you burn every developer's time, forever, for no learning in return.

## What a golden path is

A **golden path**, sometimes called a **paved road**, is the opinionated, supported, *easiest* way to do a common job. The word "easiest" is the point. A golden path wins because developers choose it, not because they are forced to.

| Property | Meaning |
| --- | --- |
| Opinionated | One default for language, packaging, deploy and observability |
| Complete | Covers create → build → deploy → operate, not just scaffolding |
| Supported | The platform team fixes it when it breaks |
| Optional but attractive | Leaving is allowed; then you own more (an *escape hatch*) |
| Understandable | Developers can see what the path did and why; no magic they cannot inspect |

A rough picture of the road and its exit:

```text
        idea
          │
          ▼
   ┌─────────────┐   create    ┌─────────┐   build   ┌─────────┐
   │  template   ├────────────▶│  repo   ├──────────▶│  image  │
   └─────────────┘             └─────────┘           └────┬────┘
                                                          │ promote
                       ┌──────────────────────────────────▼──────┐
   escape hatch  ─ ─ ─▶│ staging ─▶ production, with status,    │
   (you own more)      │ runbook, owner and dashboard attached  │
                       └─────────────────────────────────────────┘
```

### A golden path versus its neighbours

| Idea | What it is | Difference from a golden path |
| --- | --- | --- |
| Mandate | A rule you must follow | A golden path is chosen because it is easier, not forced |
| Template | A scaffold generated once | A path includes operating the service after creation |
| Cage | A path with no exit | A golden path has a documented escape hatch |
| Standard | A documented expectation | A path is the working implementation of the standard |
| Tutorial | A lesson with no production consequence | A path produces something real and supported |

An *escape hatch* example: a team needs a language the path does not support. They may leave the path, provided they meet the same requirements (build evidence, health endpoints, ownership metadata) and accept that they now own the pipeline maintenance. Leaving is a trade, not a transgression.

## What the path promises, and what it does not

A golden path is a two-sided agreement. Say it plainly in the first document a developer reads.

| The platform promises | The developer agrees |
| --- | --- |
| The path works end to end today, and a failing path is a platform incident | To use the path unless they record why they left it |
| Fixes to shared logic reach your service without a rewrite | To keep ownership metadata and health endpoints accurate |
| Common questions have written answers | To search the docs, then ask in the support channel rather than a private message |
| Breaking changes come with notice and a migration guide | To act on deprecation notices before the stated date |
| Waits that exist (review, approval) are documented with expected times | To raise a gap when the path does not fit, not fork it silently |

What a golden path does **not** promise: that every workload fits, that it never changes, or that it removes the need to understand your own service. A promise you cannot keep is worse than silence, so the "Not covered" section of the path specification matters as much as the steps.

## The golden-path specification

A golden-path specification is a short document with a fixed shape:

```markdown
# Golden path: new HTTP service
## Prerequisites (one-time)  - tools with versions, access, who approves
## Steps                     - numbered, copy-pasteable, with expected output
## Done means                - acceptance checks (service in catalogue, status healthy, promotion recorded)
## Not covered (v1)          - stateful services, non-HTTP workloads, ...
## Escape hatch              - how to leave the path and what you then own
```

A filled-in excerpt:

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

The *measurable success condition* is what keeps the path honest. Without a number, "easy" is an opinion. Note what the number measures: time to a healthy deployment, for a person new to the platform. It does not measure how fast the author can do it.

## The first service: a guided journey

Follow a developer, Priya, through her first service. Each stage shows where onboarding usually breaks.

**Stage 1 — Arrive.** Priya opens the entry document. In ten seconds she must know whether the page is for her. A good opening reads: "This page takes you from nothing to a running `http-python` service in about an hour. It does not cover queues or batch jobs."

**Stage 2 — Prepare.** She checks her tools. Every tool has an exact version and a one-line verification command:

```bash
git --version          # expect: git version 2.40 or later
docker --version       # expect: Docker version 24 or later
platform --version     # expect: platform 1.x
platform doctor        # illustrative: checks login, network and permissions; prints PASS or a reason
```

A `doctor`-style command is worth building early. It turns a vague "it doesn't work" into a named missing prerequisite.

**Stage 3 — Get access.** Access is where silent waits live. The document states how to request it, who approves it and the expected wait. A documented wait of one working day is fine. An unwritten wait is a defect, because Priya cannot tell whether the request is stuck or merely slow.

**Stage 4 — Create.** One command creates the service from a template:

```bash
platform new service --name orders-api --template http-python --owner team-orders
# illustrative output:
#   validated name and owner
#   created repository orders-api from template http-python v3
#   opened pull request #1: "Add orders-api scaffold"
#   next: wait for the green check, then merge
```

**Stage 5 — Verify.** She merges and runs the status command from the document. The expected output is printed in the document so she can compare:

```text
$ platform status orders-api
SERVICE  orders-api   owner: team-orders
ENV      staging      status: HEALTHY   replicas: 2/2
```

**Stage 6 — Know what next.** The document ends with links: change the code, add a datastore, read the runbook, ask for help. A document that stops at "success" leaves her at a dead end.

The whole path is a loop of *do, see expected output, continue*. Whenever the real output differs from the expected output and the document says nothing, that is where beginners give up.

## Templates: what they do and where they stop

A **template** generates the starting files of a service so that nobody copies and pastes. A beginner-level template creates:

```text
orders-api/
  app/            starter code with /health and /ready endpoints
  Dockerfile
  deploy/         small files that reference shared platform manifests
  .github/workflows/   a few lines that call a shared pipeline
  RUNBOOK.md      first page of the operating guide
  README.md       what this service is, who owns it
```

Three beginner rules about templates:

1. **Keep generated files short.** If a developer cannot read every file in an afternoon, the template did too much.
2. **Keep the shared logic outside.** The generated pipeline *calls* a shared workflow instead of containing a copy. When the platform team fixes the shared workflow, every service benefits. A copied pipeline stays broken forever.
3. **Everything generated is a plain file.** No hidden state, no generator that must be re-run to understand the service.

A template is only the *start* of a path. The path continues into building, deploying and operating, which is why a template alone is not a golden path.

## Documentation that actually helps

Documentation is part of the product, not a courtesy. Four kinds of document serve four different needs:

| Kind | Reader's question | Example |
| --- | --- | --- |
| Tutorial | "Take me from zero to something working." | First service in an hour |
| How-to | "How do I do this specific thing?" | Roll back a release |
| Reference | "What exactly is the rule?" | Allowed environments, quotas |
| Explanation | "Why does it work this way?" | Why images are promoted by digest |

Mixing these in one page makes all four worse. A tutorial that stops to explain design history loses the learner; a reference page written as a story is slow to search.

Basic quality rules:

- Every command is copy-pasteable and shows expected output.
- No assumed working directory, cluster or account. State them.
- The error message you will see appears *next to* the step that causes it.
- Headings and link text are descriptive ("Request namespace access", not "click here").
- Meaning is never carried by colour alone.

## The entry document

The first document a developer reads decides whether they trust the rest. Keep it in this order and for these reasons:

| Order | Section | Why here |
| --- | --- | --- |
| 1 | Goal and outcome | The reader decides in 10 seconds whether this page is for them |
| 2 | Prerequisites with verification commands | Failures here are cheapest to fix before any real work |
| 3 | One command | An early quick win builds confidence |
| 4 | Expected output | Lets the reader know if they are on track |
| 5 | What next | Prevents a dead end after success |
| 6 | Where to get help | Gives the reader an exit when something breaks |

Also in the first thirty minutes: what the platform does for you (three sentences), what it will not do, how to obtain access and a "hello" smoke test.

## Test your own onboarding

On a clean account or container, follow the document verbatim. Every command you must improvise is a defect; fix the document, not your memory.

```bash
docker run --rm -it ubuntu:24.04 bash        # a clean environment
# follow the document verbatim; log each deviation:
#   step 3: needed `apt-get install curl` (undocumented prerequisite)
#   step 5: output differed from the document (version changed)
```

Keep the log in a table so it can become a backlog:

| Step | Deviation | Fix | Date |
| --- | --- | --- | --- |
| 3 | `curl` missing | Add to prerequisites with a verification command | 2026-11-02 |
| 5 | Output shows version 2, document says 1 | Update expected output; add version to check | 2026-11-02 |
| 7 | "Merge" step did not say which branch | Name the branch | 2026-11-03 |

Re-run after each fix. The test ends when no improvisation is needed. You cannot judge your own document well because you already know the answers, so the clean-machine test is a stand-in for a new reader. It is not a substitute for one, a point the Professional and Expert levels develop.

## How first-service onboarding fails

Onboarding fails in a handful of recognisable ways. Learn the symptoms so that you can read a complaint and know where to look.

| What the developer says | Likely cause | First fix |
| --- | --- | --- |
| "The command is not found." | Undocumented tool or wrong version | Add tool, version and verification command |
| "I was told to request access and heard nothing for two days." | Undocumented approval path or wait | Name the approver; state expected response time |
| "The scaffold created files I do not understand." | Template too large or unexplained | Shrink it; annotate generated files |
| "My pipeline failed and the error mentions a policy." | Rule not documented near the step | Put the error and fix beside the step |
| "It said success but nothing is running." | Status check lies or does not exist | Provide an honest status command |
| "I followed the document and my output was different." | Docs drifted from the path | Test docs against the path regularly |
| "I do not know who to ask." | No help route | Add an "I'm stuck" page with channel and response time |

Notice that most causes are *platform* defects. A beginner who fails is usually reporting a fault in the product, not their own ability.

## Common mistakes

- Writing the document from memory on a machine that already has everything installed.
- Documenting what the platform *can* do instead of the first task a developer actually has.
- Calling something a golden path while it is a mandate with no exit.
- Starting with a long architecture description before the reader has run anything.
- Stating "easy" without measuring how long a new person takes.
- Hiding the plumbing so completely that nobody can debug the service they own.
- Letting the template and the documentation drift apart.

## Knowledge consolidation

Check yourself before moving on.

1. Name the three kinds of cognitive load and give an example of each in a deployment task.
2. Why must a golden path include an escape hatch? What does a team gain and lose by using it?
3. List the five sections of a path specification. Which one protects against false promises?
4. Why is a copied pipeline worse than a pipeline that calls a shared workflow?
5. What distinguishes a tutorial from a how-to?
6. A new developer says "it worked but nothing is running." Which part of the platform probably misreports, and what should it say instead?

## Exercises

1. **Entry document.** Write the entry document for a platform you know. Run it on a clean machine and list every improvised step. Fix the document and run again.
2. **Classify.** Interview a colleague about their last three frustrations with tooling. Classify each as intrinsic, extraneous or germane, and say whether a platform could remove it.
3. **Specification.** Write a path specification for "a scheduled batch job" with a measurable success condition and a "Not covered" section.
4. **Failure reading.** Take the onboarding failures table and invent a fourth row from your own experience, including likely cause and first fix.
5. **Escape hatch.** Write a deviation note for a team that must use a language the path does not support. State what they own afterwards.
