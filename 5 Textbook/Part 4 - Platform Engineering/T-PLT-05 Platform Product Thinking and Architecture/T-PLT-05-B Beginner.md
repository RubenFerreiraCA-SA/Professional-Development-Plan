# T-PLT-05-B — Beginner Foundations

*Chapter: [T-PLT-05 — Platform Product Thinking and Architecture](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-05-b"></a>
#### T-PLT-05-B — Beginner Foundations

## Why this matters

Most engineers meet a "platform" the same way: someone announces a new internal system, a link to a wiki arrives, and a month later half the teams are still doing things the old way. The announcement was not the failure. The failure happened earlier, when the people building the platform decided what to build without asking the people who would use it.

An internal platform exists for one reason: so that the engineers who build and run products can spend their attention on the product instead of on plumbing. If a team still has to learn five tools, write four hundred lines of configuration and ask three other teams for permission before the first line of business code reaches production, the platform has not done its job, however modern its parts are.

This Beginner section teaches the *product thinking* under every platform decision: platform versus tool pile, internal users and their jobs, cognitive load, golden paths and team boundaries. It assumes you can read a simple configuration file and have used version control, not that you know Kubernetes or a portal product. Names such as `orders-api`, the `checkout` team and the `payments` team are fictional.

A recurring theme: **a platform is judged by what its users can do without help, not by what its builders have installed.**

## First principles: a platform is a product, not a tool pile

Picture a company with forty product developers and four infrastructure engineers. Over two years they adopt a scheduler, a pipeline system, a secrets store, metrics, log search, a policy engine and a portal. Each tool is good; each has its own login, documentation and failure modes. A new developer needs most of them to ship a small service, and the four engineers answer "how do I…?" all day. That is a **tool pile**: capabilities that are available but not assembled into something a person can use to finish a task. A **platform** assembles a smaller number of them behind one documented, self-service path.

| Question | Tool pile | Platform |
| --- | --- | --- |
| What is offered? | Components, each with its own interface | A complete path with one coherent interface |
| Who must integrate the parts? | Every user, separately | The platform team, once |
| How does a user learn it? | By asking colleagues and reading each tool's manual | By following documented, tested guidance |
| How is it improved? | Whoever shouts loudest gets an answer | By watching where users get stuck |
| What does success look like? | The tools are running | Users complete tasks without help |
| What happens to feedback? | Becomes a ticket | Becomes input to a roadmap |

Three properties separate a platform from a pile.

1. **It is built for users.** There are named groups of people it serves, and the team can describe what each is trying to do.
2. **It is self-service.** The common case needs no conversation with the platform team. A human gate may exist, but only where a person's judgement is genuinely required, and it is designed, not accidental.
3. **It improves from evidence.** The team watches real people use it, measures outcomes and changes the platform because of what it learns.

If any of the three is missing, you probably have infrastructure with a friendly name.

**Internal developer platform (IDP).** A set of self-service capabilities, defaults and guardrails that make the safe way the easy way to build, ship and run software. It is an *interface* (a command line, a repository template, a portal, documentation) plus the automation behind it. The interface is what users touch; the automation is what makes the interface honest.

Analogy, and its limit: a platform is like an airport route: passengers follow signs, not runways. It fails because internal users can usually build their own route, and that freedom is information.

## Who are the users? Internal users are customers

An internal platform has customers even though no money changes hands. They pay with attention, with trust and with the decision to use the platform or work around it.

**Who the users are.** The most visible user is the *application developer*, the person who writes a service but is not a specialist in container scheduling, networking or observability tooling. They are not the only user. A platform also serves:

| User | What they do with the platform | What they need from it |
| --- | --- | --- |
| Product developer | Creates, changes and ships services | A safe default that deploys without learning the underlying tools |
| On-call developer | Responds when a service misbehaves | Visibility of what is wrong and a safe first action |
| Reviewer or tech lead | Approves changes | Confidence that the basics were already checked |
| Platform engineer | Builds and operates the platform | Fewer interruptions; evidence of what to improve next |

**Why customers who can decline matter.** A developer who builds their own deployment script is saying the offered path was slower, riskier or less clear. If the platform *forces* every team onto one path you lose that signal. Mandate only what safety requires and compete on experience for the rest.

**Jobs to be done.** To describe a user, avoid abstract titles and use the **job** they are trying to get done. A job statement has three parts: **When** *(a situation)*, **I want** *(a motivation)*, **so I can** *(an outcome)*.

| Persona | Job to be done | Fear |
| --- | --- | --- |
| Product developer | "When I start a new service, I want a safe default that deploys, so I can ship my feature instead of writing configuration." | Breaking production; asking a question that sounds basic |
| On-call developer | "When my service misbehaves at 2 a.m., I want to see what is wrong and the first safe action, so I can restore service without waking the platform team." | Opaque dashboards; missing runbooks |
| Reviewer or tech lead | "When I review a change, I want to know the platform already checked the basics, so I can focus on whether the change is right." | Rubber-stamping unreviewable diffs |
| Platform engineer | "When I plan my quarter, I want evidence of where users are stuck, so I can work on the highest-value problems." | Becoming a human API |

**Real people, not segments.** Write personas you could recruit: "Ana from the checkout team, who shipped two services" is someone you can ask on Thursday.

## Cognitive load: what the platform absorbs

People can hold only so many things in mind at once. Software teams have a limited budget for understanding, and every tool, process and rule spends some of it. Cognitive load thinking splits that spend into three kinds.

| Kind | Meaning | Example | What a platform should do |
| --- | --- | --- | --- |
| Intrinsic | Effort inherent to the problem | Understanding what an order is and how it is priced | Leave it with the team; it is their job |
| Extraneous | Effort caused by the environment, not the problem | Remembering which of three pipelines supports which language | Remove it; this is the platform's main target |
| Germane | Effort that builds useful understanding | Learning how a retry policy interacts with a payment timeout | Protect it; do not hide what teams need to learn |

The aim is not to hide everything. A platform that removes germane load produces teams that cannot reason about their own service, and teams that cannot reason about their service cannot operate it. The aim is to remove *extraneous* load: the plumbing that every team repeats and that adds no insight.

A practical test: for each step in a path, ask which kind of load it produces. Writing a container build file for the fiftieth time is extraneous; deciding how an order is cancelled is intrinsic; understanding why a service restarts under memory pressure is germane, and a good platform surfaces it.

## Golden paths

A **golden path** is a documented, supported, opinionated route for a common task, designed so that following it is the easiest way to get a good result. The name does not imply gold-plated; it implies *well lit*. Users can leave the path, but they do so knowingly and own the consequences.

A golden path for creating a service might look like this.

| Step | What the user does | What the platform does |
| --- | --- | --- |
| 1 | Runs one command or fills one form with a service name and owner | Creates a repository from a tested template |
| 2 | Writes business code | Provides a build pipeline, tests and a container image definition |
| 3 | Opens a pull request | Runs checks; reports results in plain language |
| 4 | Merges | Builds an image once, records its digest and promotes it by declared rules |
| 5 | Looks at the service | Shows health, logs and a starter dashboard from the first deploy |
| 6 | Responds to an incident | Links the alert to a runbook the template created |

A path is *golden* rather than merely documented when it is complete (a stranger finishes it without leaving the page), opinionated (few choices before first success), supported (someone is paged if the template breaks), optional but attractive (teams stay voluntarily) and honest about its limits.

**A golden path is not a cage.** If a team has a legitimate need the path does not cover, such as a latency-critical service, they need a documented way to step off that says what they now own. Without one they leave informally, and you lose their trust and their information.

## Team boundaries: where the platform team sits

A platform team does not work alone. It sits between the teams that build product features and the underlying infrastructure and services they use. One widely used vocabulary describes four kinds of team and three ways teams interact.

**Four team types**

| Type | Purpose | Example |
| --- | --- | --- |
| Stream-aligned | Delivers a continuous flow of change for a business area | The checkout team |
| Platform | Provides internal services that reduce load for stream-aligned teams | The platform team |
| Enabling | Helps other teams adopt new capabilities, then steps back | A team that coaches others on observability |
| Complicated-subsystem | Owns a part that needs deep specialist knowledge | A team owning a pricing engine |

The platform team exists to serve stream-aligned teams, and its success is measured by *their* flow.

**Three interaction modes**

| Mode | Meaning | Warning sign |
| --- | --- | --- |
| Collaboration | Two teams work closely for a limited time | It never ends |
| X-as-a-Service | One team provides something the other consumes with minimal interaction | Consumers must ask for help to use it |
| Facilitating | One team helps the other learn or adapt | The helper becomes a permanent dependency |

A healthy platform starts in **collaboration** (pairing with the first users), then moves toward **X-as-a-service** as the path matures.

**The human API.** If developers must message a platform engineer for every routine request, that engineer *is* the interface: a **ticket queue with extra steps**. Turn each repeated request into a self-service capability and keep a human only where judgement is needed.

**Ownership boundaries.** Write down who owns what: the platform owns the template, the shared pipeline, the runtime and the support route; the product team owns code, tests, release timing, diagnosis and business behaviour. A contract nobody wrote down is an assumption, and an incident is an expensive time to find the line.

## A one-page product brief

A product brief forces the team to answer the basic questions before building. It fits on one page.

```markdown
# Platform product brief

## Users
- Ana, product developer, checkout team (joined four months ago, shipped two services)
- Kofi, on-call developer, payments team

## Jobs-to-be-done
1. When I start a new service, I want a safe default that deploys, so I can ship my feature.
2. When my service fails at night, I want to see what is wrong and the first safe action.
3. When I review a change, I want to know the basics were checked.

## Golden path
One command creates a repository from a template with build, deploy and
observability wired in. Interface: a command line plus one documentation page.

## Non-goals (v1)
- Not a general-purpose application hosting product
- No support for stateful services in v1
- No bespoke pipelines for individual teams

## Success metrics
- Independent completion time for "create and deploy a service"
- Intervention count during that task
- Adoption of the golden path among new services

## Known limitations
- Single runtime; teams on other runtimes use a documented exit
- Support during business hours only
```

**Non-goals** are decisions *not* to do something, written down so scope does not drift; a brief with fewer than three is hiding decisions. **Success metrics** are defined *before* measuring. **Known limitations** are honest, because a platform that claims none will have them discovered in an incident.

## Metrics from the user's outcome

A platform team can easily measure its own activity: features shipped, tickets closed, tools adopted. None of these says whether users are better off. Measure *their* outcomes.

| Metric | Definition | Trap |
| --- | --- | --- |
| Independent completion time | Minutes from task handed over to the acceptance check passing, excluding documented waits | Rewarding speed that hides unsafe shortcuts |
| Intervention count | Times someone gave information not already in the documentation | Counting only "big" hints |
| Stuck points | Moments a user paused beyond two minutes, backtracked or searched without progress | Treating them as user error |
| Time to first deploy | From service creation to first healthy running instance | Ignoring second-service speed |
| Adoption | Services on the golden path divided by all services | Meaningful only when use is voluntary |

**Measure a person, not a demo.** The author can always drive the platform; the proof is someone who has never seen it succeeding without help. A fast completion time with a high intervention count means the platform was fast only because someone helped, so read metrics as a set.

## A first small experiment: the observed trial

You do not need a survey platform or a research budget to learn from users. A simple trial yields most of what a beginner team needs.

1. **Pick one task** from the brief, such as "create and deploy a new service".
2. **Find one person** who has not seen the platform and give them an hour.
3. **Write an acceptance check** in advance, for example: the service answers on its health endpoint and appears in the catalogue with an owner.
4. **Give them only the documentation**, ask them to think aloud and help only if they are blocked for several minutes.
5. **Record** every pause, question and backtrack, and the time to acceptance.
6. **Do not defend.** If they misread a sentence, the sentence is wrong. Fix the top stuck point and repeat with another person.

An example record:

```text
Task: create and deploy a new service
Participant: P1 (product developer, 8 months at company)
Acceptance check: health endpoint returns 200; service appears in catalogue with owner

00:00  Reads page; asks where to find the template command         (intervention 1)
00:07  Runs command; error: missing permission to create repository  (stuck point A)
00:19  Permission granted by platform engineer                      (intervention 2)
00:26  Edits service name; unsure what "owner" must contain         (stuck point B)
00:41  Opens pull request; checks pass
00:53  Merged; waits for deploy; unclear where to look               (stuck point C)
01:04  Finds health endpoint; check passes
Result: completed with 2 interventions; 3 stuck points; 64 minutes
```

Five or six such records beat any amount of opinion.

## What can go wrong: common mistakes and how they look

| Mistake | Symptom | Fix |
| --- | --- | --- |
| Building a portal first | A polished interface in front of a path that does not work | Trial the path with a real user before building any interface |
| Mandating before earning | Teams comply on paper and work around the platform | Mandate only what safety needs; compete on experience |
| Hiding too much | Teams cannot diagnose their own services | Surface what they must understand; hide only plumbing |
| No written non-goals | Every request becomes in scope | Write at least three non-goals and review them |
| Measuring activity | Dashboards green; developers unhappy | Measure users' outcomes |
| Human API | Platform engineers answer the same questions daily | Automate the request; document the answer |

## Knowledge consolidation

- A **platform** is a product with users, self-service interfaces and an improvement loop; a **tool pile** offers components without assembling them.
- Internal users are **customers who can decline**; mandate only what safety needs.
- Describe users with **named personas and jobs to be done** (*when / I want / so I can*), including fears.
- A platform removes **extraneous** cognitive load and protects **germane** load.
- A **golden path** is complete, opinionated, supported, optional but attractive and honest; it needs a documented step-off.
- Platform teams move from **collaboration** toward **X-as-a-service**; a team answering routine requests by hand is a **human API**.
- Write a **product brief**, define metrics on the **user's outcome** in advance, and prove them with an independent person.

## Exercises

**Exercise 1 — Tool pile or platform.** List every tool a new developer at an organisation you know must touch to ship a small service. Count them, count the logins and count the places to look when it fails. Decide whether you have a tool pile or a platform, and justify your answer using the three properties (built for users, self-service, improves from evidence).

**Exercise 2 — Write three jobs.** For three different users of a platform you know, write a job statement in the form *When / I want / so I can*, and add their fear. Name a real person for each, even if you only name the role.

**Exercise 3 — Classify the load.** Take an onboarding guide for a service and list ten steps. Mark each as intrinsic, extraneous or germane for a product developer. Identify two steps you would automate and one you would deliberately leave visible.

**Exercise 4 — Draw the golden path.** Describe, in six steps, the golden path for creating a service in a platform you know or imagine. For each step state what the user does and what the platform does. Then write the three conditions under which a team would be right to leave the path.

**Exercise 5 — The observed trial.** Run the observed trial in this section with one real person on any process you own (it need not be a platform). Record pauses, interventions and time to acceptance. List the first fix you would make.

**Exercise 6 — Product brief.** Write the product brief for an imaginary platform in one page, naming two real people you could ask to try it. Include at least three non-goals and three known limitations.

**Solution notes.**

*Exercise 1.* Typical honest counts are five to ten tools with separate access and several places to look in a failure. Name the weakest of the three properties; intervention frequency is quick evidence of "not self-service".

*Exercise 2.* Check each statement for situation, motivation and outcome. "I want a dashboard" names a feature, not a job.

*Exercise 3.* Typical extraneous steps: choosing between build options, copying pipeline files, requesting access in several systems. Typical germane step: understanding why a readiness check fails. Defend what you leave visible.

*Exercise 4.* Look for a path ending in an *observable* result. Good exit conditions: an unsupported runtime, a regulatory control, a measurable harm to a critical requirement. Each exit says who owns what afterwards.

*Exercise 5.* Expect the first participant to stall within ten minutes on something you consider obvious. Count your interventions honestly.

*Exercise 6.* Check that metrics are defined before measuring, non-goals exclude something people want, and limitations are uncomfortable rather than cosmetic.
