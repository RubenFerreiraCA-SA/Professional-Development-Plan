# T-PLT-06-E — Expert Depth

*Chapter: [T-PLT-06 — Golden Paths, Templates and Developer Experience](README.md) · Part 4 — Platform Engineering*

<a id="t-plt-06-e"></a>
#### T-PLT-06-E — Expert Depth

## Why this level exists

A golden path that works for ten services and one platform team is a craft problem. A golden path that serves hundreds of services, across years, through reorganisations, three template generations and a changing technology stack, is a *systems* problem with an economy, a lifecycle and a politics. Experts are asked questions that no tutorial answers. Should we fund a second template or deprecate one? How do we move eighty services off a retired workflow without a freeze? When the path blocks a legitimate innovation, who decides? Are our developer-experience numbers telling the truth, or have teams learned to please them?

This level covers six areas: how to run an *independent trial* properly and read its evidence honestly; the *economics of adoption*; *path evolution and deprecation*; *migration* at fleet scale; *consistency and usability at scale*; and *exceptions and measurement without gaming*. It assumes the earlier levels: path specifications, templates, shared workflows, guardrails, identity, ownership, audit, time-to-first-success and the operating model of a platform as a product. Examples are illustrative and generic; figures are invented to show reasoning, not to be copied.

## Running an independent trial properly

**Who qualifies:** an engineer who has never used the platform and whom you do not coach; with prior knowledge of the underlying tools (Git, containers) but not your system. Prior exposure makes the result invalid.

**Setup the day before:** clean accounts, tool installs described as in the docs, access granted by the documented route, a planted safe failure for the investigation task, a recording method (with consent), and an author-only failure card (injection command, expected symptoms, expected diagnosis, expected recovery).

**Task cards:** four short tasks — create a service, make and promote a change, investigate a planted failure and recover, then answer a comprehension check. No hints on the cards.

**Observer rules — the hardest part:**

1. Say nothing except scripted prompts (start, end, "please think aloud").
2. If asked a question: "I can't help — what do the docs say?" and log it as a stuck point. If you then answer, it is an I2.
3. Never touch their keyboard.
4. Record timestamps as you go; do not reconstruct afterwards.
5. If a participant is blocked for more than fifteen minutes on a step, you may end the task as *FAIL (blocked)* — a valid, valuable result. Do not rescue and call it a pass.
6. Run the acceptance checks yourself rather than accepting the participant's word: service in the catalogue, status healthy, promotion recorded, recovery traceable to a pull request.
7. Debrief with three questions — what was most confusing, what would you remove, would you use it voluntarily — and capture verbatim quotes with consent.

**Results:**

| Result | Meaning | Action |
| --- | --- | --- |
| PASS | All tasks complete; no I2 or I3 interventions; findings recorded | Triage stuck points anyway |
| FAIL (intervention) | Undocumented help was needed | Convert each I2/I3 into a doc or product fix; recruit a *new* participant |
| FAIL (blocked) | Participant could not proceed | Same; the stuck point is the finding |
| INVALID | Prior platform knowledge or leaked author context | Discard the evidence and record why |

Use a *new* participant after a failure: a returning participant has learned the answers and you would measure recall. They may return later for a labelled "second service" speed measurement.

A session log shows what contemporaneous recording looks like:

```text
trial T-03   participant P7   observer O2   path: http-python v3   date: 2026-10-14
00:00  start, task card 1 and docs link handed over
00:06  reading entry doc; finds prerequisites table
00:11  stuck: `platform doctor` says "token expired"; searches docs for "token"  [stuck S1]
00:17  asks: "where do I get a new token?" -> O2: "I can't help; what do the docs say?"  [Q1 logged]
00:22  finds page via search "login"; page is under "Reference"  [findability defect F1]
00:25  doctor passes
00:31  scaffold run; PR opened
00:33  CI failing: policy message unreadable  [stuck S2, 9 min]
00:42  fixes name casing after reading rule id in docs
00:44  acceptance check 1 passes (catalogue entry present)
```

Notice what is *not* in it: advice, reassurance, or a hint. The two findings (token page unfindable, policy message unreadable) are product defects, not participant defects.

## Honest statistics

With one or two participants you can find *problems*, not estimate *rates*. Report counts and quotes, not percentages that imply precision. An LLM given only the docs and a terminal can expose ambiguous steps quickly; label it an *automated docs probe — not a trial* and never use it to satisfy a pass standard.

Some rules of thumb for reading evidence:

| Situation | What you may claim | What you may not claim |
| --- | --- | --- |
| 3 of 5 participants hit the same stuck point | A recurring defect worth fixing | "60% of developers fail here" |
| Median time 52 min over 5 trials | An order-of-magnitude indication | "Average time is 52 min" as a target for the population |
| Survey: 80% of 20 respondents satisfied | The respondents who answered were mostly satisfied | That the platform's users are 80% satisfied (non-response, selection) |
| Time to first success fell from 74 to 52 | After fixes, one new participant was faster | A proven 30% improvement |
| Zero support tickets this month | Nothing was reported | Nothing was wrong |

Where a number must be compared over time, fix its definition first and keep a log of definition changes; otherwise a change in the number may only be a change in what you counted.

## Turning findings into changes

Convert each stuck point into a ranked backlog item with a source, an owner and a verification step; fix at least one severe finding and re-verify; keep the metric definitions fixed after the first trial (changes are logged) to avoid reinterpreting results.

```text
F1  token page unfindable        source: T-03 S1/F1   owner: docs lead    severity: high
    fix: link from `platform doctor` failure output; add to prerequisites
    verify: new participant reaches the page within 2 minutes (trial T-04)
F2  policy message unreadable    source: T-03 S2      owner: policy owner severity: high
    fix: message names rule, object, example and link
    verify: table test for message content; T-04 participant fixes without observer
```

Rank by *severity × reach*: how bad the stuck point is for a person, multiplied by how many people meet it. A rare disaster and a universal annoyance may both outrank a moderate problem on a path nobody uses.

## Adoption economics

A golden path is an investment with costs and returns. Experts reason about both.

### Costs and benefits

| Costs (the platform side) | Benefits (the developer and organisation side) |
| --- | --- |
| Building and testing templates, workflows, policy | Time saved per new service and per change |
| Maintaining versions, migrations, deprecations | Fewer incidents from copied-and-diverged configuration |
| Support, documentation, trials | Faster onboarding of new developers |
| The portal or API, if any | Consistent audit, security and cost evidence |
| The cost of *not* supporting a workload | Lower cognitive load, more attention for domain work |

A rough per-path calculation shows the shape of the argument. All numbers are invented:

```text
Path: http-python
  Services created per year:           40
  Time saved per service vs. manual:   6 hours (copying, debugging pipeline, access)
  Hours saved per year:                240
  Time saved per service per quarter on maintenance (shared fixes): 1.5 hours x 60 services x 4 = 360 hours
  Total benefit:                       ~600 engineer-hours / year

  Platform cost: 0.4 FTE maintenance (≈ 700 hours) + 0.1 FTE support (≈ 175 hours)
  Net:                                 negative on pure hours at 60 services
```

The calculation is deliberately sobering. At 60 services the path may not pay for itself in pure time. Break-even moves with service count, with incident cost avoided and with benefits that hours do not capture (security evidence, auditability, onboarding speed). The point is not to produce a number but to *know which assumptions your case depends on*.

### Adoption is a choice, so model it

Developers adopt a path when its *perceived* net value exceeds the cost of leaving. Four forces:

| Force | Pushes toward the path | Pushes away |
| --- | --- | --- |
| Time to value | Fast first success | Slow first success, long waits |
| Capability | Path supports what I need | Path lacks my language, datastore or workload |
| Autonomy | Escape hatch exists and is respectful | Mandate; fear of being stuck |
| Trust | Past fixes arrived; support responded | Past breakages, ignored requests |

Trust is the slowest force to build and the fastest to lose. One unannounced breaking change can cost a quarter of adoption.

### Mandates versus attraction

At some scale an organisation will mandate a path for reasons that are not about developer convenience: a security baseline, an audit requirement, a cost control. Be careful to separate two things:

- The *requirements* (build evidence, health endpoints, ownership metadata, image by digest) may be mandatory.
- The *path* (the particular implementation) should remain the easiest way to meet them, not the only permitted way.

Mandating the requirements while keeping the path attractive keeps feedback honest: if teams still prefer their own route to the requirements, the path has a defect.

### Choosing what to build next

Rank candidate work by value over cost, with explicit evidence:

| Candidate | Teams affected | Stuck-point severity | Cost | Evidence | Rank |
| --- | --- | --- | --- | --- | --- |
| Policy message rewrite | All | High | S | Two trials | 1 |
| Queue-consumer template | 6 teams forking | Medium | L | Gap issues | 2 |
| Portal catalogue view | Many | Low | XL | Opinion | 4 |
| Auto-upgrade PRs for v2 services | 14 services | Medium | M | Version report | 3 |

Expect "high value, small cost" items to be documentation and error messages, rarely new features.

## Path evolution and deprecation

A path that cannot change ossifies; a path that changes carelessly destroys trust. The discipline between those is a *lifecycle*.

### The lifecycle of a path version

```text
 proposed ─▶ preview ─▶ stable ─▶ maintenance ─▶ deprecated ─▶ removed
              (opt-in)  (default)  (fixes only)   (dated)      (unsupported)
```

| Stage | Promise | Typical duration |
| --- | --- | --- |
| Preview | May change; feedback wanted; not for critical services | 1–3 months |
| Stable | Supported, documented, default for new services | Until superseded |
| Maintenance | Security and critical fixes only; no new features | 6–12 months |
| Deprecated | Removal date announced; migration guide published | At least one full planning cycle |
| Removed | Template and shared workflow versions retired; services must have moved | Date announced at deprecation |

### Compatibility rules for shared logic

| Change | Class | Rule |
| --- | --- | --- |
| Bug fix, patch update | Compatible | Release freely; announce in the changelog |
| New optional input, new optional behaviour | Additive | Document; default preserves old behaviour |
| New enforced check | Behavioural | Warn-only period, per-service list, then enforce with exemptions |
| New required input, changed meaning, removed input | Breaking | New major version, both versions supported during the window |
| Security emergency | Exceptional | May break; communicate immediately and help affected teams the same day |

### The deprecation notice

A good notice answers six questions, in this order:

```text
DEPRECATION: http-python template v2
What:     v2 and shared workflow service-ci@v1 are deprecated.
Why:      v1 workflows cannot receive the supply-chain checks required by policy 7.
When:     deprecated 2026-08-01; support (fixes) ends 2027-02-01; removal 2027-05-01.
Who:      14 services (list attached; your team is listed if affected).
What to do: run `platform upgrade http-python --to 3` (opens a pull request); guide:
            docs/migrations/http-python-2-to-3.md. Expected effort: under 2 hours per service.
Help:     office hours Tuesdays 14:00; #platform-support; we will open the pull request for you on request.
```

A notice that says only "v2 is deprecated" shifts the discovery work onto every developer.

### Retiring something developers like

Sometimes a popular part of the path must go: a template for a language the organisation no longer supports, a workflow with an unfixable flaw. Questions to answer before deciding:

| Question | Why it matters |
| --- | --- |
| Who still uses it, and how much do they depend on it? | Real data from the version report, not recollection |
| What is the cost of keeping it? | Security patches, support load, test matrix growth |
| What replaces it, and is the replacement at least as good for those users? | Retirement without a better alternative is abandonment |
| What is the migration effort per service, and who pays it? | Dictates whether the platform offers to do the work |
| What is the risk if it stays? | Security exposure, unsupported dependencies |
| Is the deadline negotiable for a justified case? | Sets the exception process before it is needed |

## Migration at fleet scale

A migration is a project with a plan, owners and a finish line. Treat it so.

### Principles

1. **Automate the mechanical part.** If a change is the same in forty repositories, a bot should propose it. Humans review and merge; they do not retype.
2. **Make it safe to stop halfway.** Both old and new must work during the transition.
3. **Measure the fleet, not the anecdote.** A dashboard of how many services are on each version is the project's truth.
4. **Give teams a path to ask for help**, and offer to do the migration for those who cannot.
5. **Define done.** Done is removal, not "most services migrated".

### An upgrade pull request

```text
platform upgrade --service orders-api --template http-python --to 3
# 1. reads .golden-path.yaml (current version 2)
# 2. computes the template diff from v2 to v3, applied to the generated files only
# 3. leaves developer-owned files alone; reports conflicts instead of overwriting
# 4. opens a pull request: title, link to migration guide, list of changes, test results
# 5. updates the stamp to version 3 only when the pull request merges
```

Tracking:

```text
migration http-python 2→3                              day 0     day 30    day 60    day 90
  services on v2                                         14        9          4         1
  upgrade PRs open (waiting on team)                      0        6          3         1
  upgrade PRs merged                                      0        5          5         3
  blocked (needs exception or platform help)              0        1          1         1
  teams contacted individually                            0        4          3         1
```

The tail is the hard part. The last few services are usually the ones with an unusual reason: no active owner, a frozen release, a custom workflow. Plan for them explicitly; a migration that waits for "just those two" never ends.

### What goes wrong in migrations

| Failure | Mechanism | Defence |
| --- | --- | --- |
| The pull request overwrites developer changes | Upgrade tool regenerates whole files | Diff-based upgrades; conflicts reported, never overwritten |
| Migration stalls at 90% | The remaining services have no owner or no capacity | Ownership report; an executive-visible list; offer to do the work |
| New version breaks a service in production only | Offline checks passed, cluster behaviour differed | Canary adoption: a few services first; lab deployment tests |
| Developers ignore the pull request | Notification fatigue | One channel, a dated reminder, and a visible dashboard by team |
| Two versions of the shared workflow diverge in behaviour | Security fixes applied to one only | Backport policy; maintenance-stage rules |

## Fleet consistency

At hundreds of services, *consistency* is what turns a platform from a convenience into a leverage point for security, cost and reliability. It is also what drifts silently.

### Dimensions of consistency

| Dimension | Question | Instrument |
| --- | --- | --- |
| Template version | Which version is each service on? | Version stamp report |
| Shared workflow version | Which services call a deprecated workflow? | Repository scan for `uses:` references |
| Required files | Does every service have a runbook, ownership and health endpoints? | Catalogue conformance check |
| Policy exemptions | How many exist, who owns them, when do they expire? | Exemption register report |
| Observability | Does every service emit the standard signals and a dashboard? | Conformance query against telemetry |
| Deviations | Which services are off the path and why? | Deviation records collected from READMEs |

### A conformance scorecard, with a warning

A scorecard turns the dimensions into a per-service view:

```text
service        version  workflow  runbook  owner-confirmed  dashboard  exemptions
orders-api     v3       v2        yes      2026-09-30       yes        0
reports-batch  v2       v1        no       2025-12-01       no         1 (EX-0042)
quote-calc     v3       v2        yes      2026-10-02       yes        0
```

Warning: a scorecard displayed to executives with team rankings will be optimised for its own sake. Show it to *teams about their own services*, with guidance on how to improve; aggregate it for leaders without ranking individuals. Treat any score as a prompt for a conversation, not a verdict.

### Drift

Services drift from the path in small ways: a file edited by hand, a workflow reference pinned to an old version, a manifest overlay that stopped referencing the base. Detect it; do not assume it away.

```bash
# detect services whose workflow reference is behind (illustrative)
rg -n "platform-workflows/.*@v[0-9]+" --glob '*.yaml' -o services/ \
  | awk -F'@' '{print $NF}' | sort | uniq -c | sort -rn
```

Pair detection with a *response*: an automated pull request for the mechanical cases, a message to the owner for the rest, and a planned review of services that have been behind for more than a defined period.

## Usability at scale

What worked for twenty developers fails at five hundred in predictable ways.

| Scale effect | Symptom | Response |
| --- | --- | --- |
| More workloads than the path covers | A growing share of services are off-path | Prioritise new templates by gap issue count; consider a *composable* path (base plus add-ons) over many monolithic templates |
| Documentation grows beyond what anyone can search | Duplicate and contradictory pages | Page owners, review dates, a retirement process for pages |
| Support load scales faster than the team | Queues, slow answers | Self-serve diagnostics (`doctor`, `status`), better error messages, a "known issues" page, office hours instead of ad-hoc interrupts |
| Many portal plugins | Upgrade burden, inconsistent behaviour | A small curated set; each with an owner; a retirement rule |
| Different teams want different defaults | Template parameter explosion | Opinionated defaults; a *small* set of supported variations; the rest through documented deviations |
| Organisation spans regions and time zones | Support gaps, slow reviews | Documented response times by region; asynchronous channels; follow-the-sun for incidents |

### Composition over multiplication

A common scaling trap is a template per combination: `http-python-postgres`, `http-python-redis`, `http-go-postgres` and so on. Combinations grow multiplicatively and each must be tested. A composed path separates a *base* from *add-ons*:

```text
base:     http-python (service skeleton, CI, deploy, status, runbook)
add-ons:  postgres (adds datastore config and migration job)
          queue-consumer (adds consumer deployment, scaling rule)
          scheduled-job (adds a cron definition)
Each add-on is tested alone and with the base, plus a small sampled set of pairs.
```

The trade-off: add-ons need clear boundaries and compatibility rules, but the test matrix grows additively rather than multiplicatively.

### Developer experience beyond the platform

Fast local feedback (build and test times), reliable CI, short review latency, clear ownership, low-friction access, trustworthy environments, and psychologically safe incident culture. The platform team may influence only some of these; knowing which are inside its remit matters for honest accountability.

| Factor | Platform influence | Others involved |
| --- | --- | --- |
| Build and test time | High (shared workflows, caching, runners) | Application teams (test design) |
| CI reliability | High | Dependency owners |
| Review latency | Low | Team norms, staffing |
| Access friction | High | Security, identity teams |
| Environment trustworthiness | High | Data and application teams |
| Incident culture | Medium (templates, blameless reviews) | Engineering leadership |

## Exceptions at scale

Exceptions are not failures of the system; they are the system's pressure valve. Without a good exception process, developers fork silently and the platform loses visibility.

### Design

| Element | Description |
| --- | --- |
| Request | A short form or pull request: what rule, what subject, why, what compensating control |
| Decision | By a named role, with a response target; some classes pre-approved |
| Expiry | Every exception has an end date; renewal requires review |
| Register | A data file or table listing all exceptions, owners, expiry |
| Signal | Each exception increments a gap counter on the relevant path feature |

### Classes

| Class | Example | Handling |
| --- | --- | --- |
| Pre-approved | Non-default resource sizes within a stated limit | Self-service; recorded |
| Standard review | A language the path does not support, requirements still met | Platform reviewer, recorded deviation |
| Security-relevant | Disable a policy rule for one service | Security approval, compensating control, short expiry |
| Permanent | A workload with a structural reason (hardware, regulation) | Executive-level acknowledgement; annual review; a plan to build path support if repeated |

### Reading the exceptions

A register is data. Ask it questions:

```text
Exceptions by rule (last 12 months)
  image-by-digest           9   (7 vendor images by tag; 2 legacy)   -> build a vendor-image mirror with digest pinning
  required-readiness-probe  5   (batch jobs)                         -> batch template missing; build it
  no-privileged             2   (a profiler, a legacy agent)         -> security review; likely keep as exceptions
```

Many exceptions to one rule say the *rule* or the *path* is wrong for a class of workload, not that nine teams are being difficult. Few exceptions to a rule may mean nobody asks; check by comparing with the deviation records and the repository scan.

## Measuring developer experience without gaming

Every measure used to judge people or teams becomes a target; every target changes behaviour. Goodhart's law is an engineering constraint here.

### Ways metrics get gamed

| Metric | Gaming behaviour | Effect |
| --- | --- | --- |
| Time to first deployment | Pre-approved access, scripted demos, pre-warmed accounts | The number improves; real new joiners are unchanged |
| Number of services on the path | Re-labelling existing services; creating trivial services | Adoption looks high; value does not follow |
| Support tickets closed | Closing quickly without resolving; splitting tickets | Throughput up; satisfaction down |
| Deployment frequency (DORA) | Many trivial deployments, config toggles | Frequency up; no extra value delivered |
| Change failure rate | Not recording failures; reclassifying incidents | Rate falls; hidden risk grows |
| Survey satisfaction | Surveying only happy users; pressure to respond positively | Score rises; truth hidden |
| Conformance score | Adding required files with empty content | Score up; no real runbook exists |

### Principles that reduce gaming

1. **Use measures as signals, not targets.** Say it explicitly to teams and leadership, and mean it.
2. **Pair measures that pull against each other.** Pair speed with quality (deployment frequency with change failure rate and time to restore); pair adoption with a retention check (still on the path after six months).
3. **Measure the system, not the individual.** Never use developer-experience data to rate people.
4. **Triangulate quantitative with qualitative.** Trials, interviews, free-text survey comments and support reading often explain what numbers cannot.
5. **Make definitions public and stable.** Changes are logged; comparisons across definition changes are marked.
6. **Audit the measure.** Occasionally check a sample by hand: open five "conformant" runbooks and read them.
7. **Retire a measure when it stops informing.** A metric that always reads "fine" and has not caused a decision in a year is overhead.

### Frameworks as lenses

Frameworks such as DORA metrics (deployment frequency, lead time, change failure rate, time to restore) and developer-experience survey models (feedback loops, cognitive load, flow state) are lenses that suggest what to look at. Use them to ask better questions rather than to produce league tables. Combine quantitative signals with qualitative research.

A balanced set for a platform team might look like this:

| Question | Quantitative signal | Qualitative signal |
| --- | --- | --- |
| Can new developers succeed alone? | Independent completion time and intervention classes from trials | Debrief quotes |
| Is the path trusted? | Retention on the path after 6 months; share of fixes shipped within target | Interview themes; free-text comments |
| Is the platform healthy? | Template matrix pass rate; platform SLO attainment | Support-thread reading; incident reviews |
| Is the fleet consistent? | Version distribution; conformance with sampled audits | Deviation record themes |
| Is it improving delivery? | DORA-style measures, read alongside quality measures | Team retrospectives |

## Failure catalogue

| Failure | Mechanism | Defence |
| --- | --- | --- |
| Template rot | Not generated in CI | Scheduled generation and deployment tests |
| Docs drift | Steps change, docs do not | Docs tested in trials and by automated probes |
| Status that lies | Healthy reported for unpromoted or stale services | Explicit `UNKNOWN`; checks for freshness and drift |
| Author-blindness | The builder cannot see stuck points | Independent trials; rehearsal runs labelled as such |
| Path ossification | The golden path blocks innovation | Escape hatch, deviation process, periodic review |
| Support overload | Repeated questions | Convert to docs or fixes weekly; measure by category |
| Trust collapse | A breaking change without notice | Compatibility rules, warn-only first, dated notices |
| Metric capture | A measure becomes a target | Pairing, triangulation, audit samples |
| Forever migration | The last 10% never moves | Define done as removal; offer to do the work; dated exceptions |
| Template multiplication | One template per combination | Composed path with add-ons; sampled pair tests |

## Template architecture at scale

Versioned template sources, generated-service stamps (`golden path vN`) that allow measuring who is behind, automated upgrade pull requests for generated services, compatibility rules for the shared workflows (additive changes, deprecation windows), and golden-image or base-manifest releases with canary adoption. Avoid the "copy and diverge" trap by keeping shared logic referenced, not copied.

A canary release of a shared workflow or base manifest:

```text
release service-ci@v2.7.0
  step 1: tag v2.7.0-rc; the platform's own services and 3 volunteer teams pin to it   (week 0)
  step 2: monitor failure rate, duration, support reports against thresholds           (week 0-1)
  step 3: if healthy, move the v2 floating tag to v2.7.0                               (week 1)
  step 4: if not, withdraw rc and publish what failed; no one outside the canary hurt
```

The rule of thumb: the blast radius of a change to shared logic equals the number of services that reference it, so release it with the care of a change to a production dependency.

## Case catalogue

### Case 1 — The scaffold that passed every check

The template generation matrix was green for six months. Then new services started failing at first deploy. The matrix ran offline only; a base image used by the generated Dockerfile had been withdrawn upstream. The nightly lab deployment had been disabled to save runner cost and nobody noticed. Lesson: the checks that find runtime rot are the ones that run the runtime. Re-enable the nightly deployment, alert on its absence, and pin base images to digests refreshed by an update bot with tests.

### Case 2 — The deprecation that ended trust

A shared workflow's input was renamed in a minor release. Forty services failed on Monday morning. The platform team's changelog had an entry; nobody reads changelogs on Monday. After rollback and a review, the team introduced compatibility classes, a warn-only period for behavioural changes, and a deprecation calendar developers can subscribe to. Adoption dipped for two quarters. Lesson: trust is the slowest asset to rebuild; one breaking change dwarfs many fixes.

### Case 3 — The metric that improved while the experience worsened

The platform team reported time to first deployment falling from 90 to 25 minutes. A trial with an independent participant took 95 minutes. The improvement came from pre-provisioned access granted by the team at hiring; the metric was measured only on those people. Lesson: define the population and the start condition; run independent trials; compare population-level numbers to trial evidence.

### Case 4 — The portal that nobody opened

A portal with a catalogue, scaffolder and documentation was built over a year. Usage was strong in the first month and dropped. The trial showed that developers' real stuck points were access and error messages, neither of which the portal addressed. The CLI, which had been neglected, was what developers used. Lesson: ask "would this remove a stuck point we observed?" before building the interface.

### Case 5 — The exception that became the standard

Nine teams used the same exception to leave the path because it lacked a batch template. Each recorded a deviation; nobody read the register. When it was read, nine forks of batch workflows were each slightly different, each with its own security gaps. A batch template was built and migration pull requests offered. Lesson: exceptions are data; read them on a schedule and let counts drive the roadmap.

### Case 6 — The owner who left

A production service had an owner field naming a group that had been disbanded eight months earlier. During an incident, the escalation went to an empty channel for forty minutes. Ownership checks against the identity provider were added, with weekly reports of unowned services and a rule blocking production promotion without a valid on-call route. Lesson: ownership is data with a half-life.

## Expert trade-offs

| Decision | Option A | Option B | Consider |
| --- | --- | --- | --- |
| One path or several | One opinionated path | Several for distinct workload classes | Usage data, gap issues, support capacity |
| Monolithic templates or composed | Fewer files, simpler first run | Add-ons, smaller matrix growth | Number of combinations in demand |
| Mandate requirements | Strong baseline, simpler audit | Voluntary, higher trust | Risk appetite, regulation |
| Pull-based or push-based upgrades | Teams choose timing | Platform pushes pull requests | Speed of security fixes versus autonomy |
| Portal investment | Discovery and onboarding UI | CLI and docs focus | Observed stuck points; capacity to maintain |
| Scorecards | Visible, motivating | Risk of gaming | Audience, ranking policy, audit samples |
| Support model | Open channel, quick answers | Ticketed, measured | Team size and scale |
| Breaking-change speed | Fast, simple code | Slow, preserved trust | Blast radius, security urgency |

## Knowledge consolidation

1. Why can three of five participants hitting the same problem justify a fix but not a percentage claim?
2. State the deprecation lifecycle and what the platform promises at each stage.
3. Why define "done" for a migration as removal?
4. What makes composed paths scale better than one template per combination?
5. Why would many exceptions to one rule indicate a platform issue rather than team behaviour?
6. Give three ways a time-to-first-deployment metric can be gamed and one control for each.
7. What is the blast radius of a change to a shared workflow, and how does a canary reduce it?

## Exercises

1. **Trial plan.** Plan a four-task independent trial for a platform you know. Specify participant qualification, setup the day before, planted failure, observer script and acceptance checks. Run it or rehearse it clearly labelled as a rehearsal.
2. **Deprecation notice.** Write a six-part notice for retiring one version of a shared workflow, including a timeline and a migration estimate per service.
3. **Migration dashboard.** Design the tracking report for retiring a template version across 60 services. Include states, owners, blocked cases and the definition of done.
4. **Adoption economics.** Build a one-page cost-benefit model for a path at 20, 60 and 200 services. List which assumptions you least trust and how you would measure them.
5. **Metric audit.** Choose three developer-experience metrics in use at an organisation and list two ways each could be gamed, one pairing measure each and one hand audit.
6. **Exception register.** Given twenty invented exceptions, group them by rule and workload class, and decide which should become path features, which stay exceptions and which indicate a wrong rule.
7. **Composition.** Redesign a set of six combination templates into a base plus add-ons. Define the test matrix and what you will not test.

## Mentoring prompts

- An I2 intervention occurred because the participant could not find the access request page. What are all the changes you could make, and which first? How do you tell the difference between a platform problem and a participant problem? How would you decide to retire part of the golden path?
- A leader asks for a ranking of teams by conformance score. What do you say, what do you offer instead, and what harm are you trying to prevent?
- Forty percent of services remain on a deprecated version after the removal date. List the questions you would ask about each remaining service before deciding what to do.
- Adoption of the path is flat while support requests fall. Give three explanations, two of which are bad news, and the evidence that would separate them.
- You can fund one of: a portal, a batch template, or auto-upgrade pull requests. Explain how you would choose with the evidence you already have and the evidence you would gather in two weeks.
