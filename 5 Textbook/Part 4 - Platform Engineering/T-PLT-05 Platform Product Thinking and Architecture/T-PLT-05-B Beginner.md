# T-PLT-05-B — Beginner Foundations

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-b"></a>
#### T-PLT-05-B — Beginner Foundations

**A platform has customers.** A platform team that ships tools without studying users builds what engineers call a *ticket queue with extra steps*. Product thinking starts with four questions:

| Question | Platform answer |
| --- | --- |
| Who are the users? | Application developers who write services but are not specialists in Kubernetes, infrastructure code or observability |
| What job do they hire the platform for? | "Get a new service from idea to a running, observable, recoverable deployment this afternoon, without learning every underlying tool" |
| How do we know it works? | Measured by *their* outcomes (time, interventions, completion), not our activity (features shipped) |
| What will we *not* do? | Non-goals, written down, so scope does not drift into a commercial platform-as-a-service |

**Internal developer platform (IDP).** A set of self-service capabilities, defaults and guardrails that make the safe way the easy way to build, ship and run software. It is an *interface* (command line, repository template, portal, documentation) plus the automation behind it.

**Users and jobs-to-be-done.** Write real personas — people you could recruit. Use the form: **When** *(situation)*, **I want** *(motivation)*, **so I can** *(outcome)*.

| Persona | Job to be done | Fear |
| --- | --- | --- |
| Product developer | "When I start a new service, I want a safe default that deploys, so I can ship my feature instead of YAML." | Breaking production; asking "stupid" questions |
| On-call developer | "When my service misbehaves at 2 a.m., I want to see what is wrong and the first safe action without waking the platform team." | Opaque dashboards; missing runbooks |
| Reviewer or tech lead | "I want to approve a change knowing the platform already checked the basics." | Rubber-stamping unreviewable diffs |
| Platform engineer | "I want fewer interrupts and a platform that improves from evidence." | Becoming a human API |

A feature that serves no job is a candidate for deletion.

**A one-page product brief**

```markdown
# Platform product brief
## Users              - personas with real examples
## Jobs-to-be-done    - 3-5 statements in the form above
## Golden path        - one-paragraph summary and the approved interface (e.g. a CLI plus docs)
## Non-goals (v1)     - at least three
## Success metrics    - defined before measuring (see below)
## Known limitations  - honest list
```

**Metrics from the user's outcome**

| Metric | Definition | Trap |
| --- | --- | --- |
| Independent completion time | Minutes from task handed over to acceptance check passing, excluding documented waits | Rewarding speed that hides unsafe shortcuts |
| Intervention count | Times someone gave information not already in the docs | Counting only "big" hints |
| Stuck points | Moments a user paused beyond two minutes, backtracked or searched without progress | Treating them as user error |
| Time to first deploy | New service created to first healthy Pod | Ignoring second-service speed |
| Adoption | Services on the golden path divided by all services | Meaningful only when use is voluntary |

**Exercise.** Write the product brief for an imaginary platform in one page, naming two real people you could ask to try it.
